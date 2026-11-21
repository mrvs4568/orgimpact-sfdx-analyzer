"""Deterministic, explainable change impact analysis."""
from __future__ import annotations

import json
import subprocess
from collections import defaultdict, deque
from pathlib import Path, PurePosixPath

from .models import Change, Snapshot
from .scanner import component_for_path

_BASE_RISK = {
    "ApexClass": 30, "ApexTrigger": 60, "Flow": 50, "CustomObject": 55,
    "CustomField": 40, "LWC": 20, "PermissionSet": 45,
}
_STATUS_RISK = {"added": 5, "modified": 10, "deleted": 25}


def _validated_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("change path must be a relative POSIX path")
    parts = PurePosixPath(value).parts
    if value.startswith("/") or not parts or any(p in {"..", "."} for p in parts):
        raise ValueError(f"invalid change path: {value!r}")
    return PurePosixPath(value).as_posix()


def parse_changes(raw: object) -> list[Change]:
    if not isinstance(raw, list) or len(raw) > 1000:
        raise ValueError("changes must be a list of at most 1,000 items")
    changes: list[Change] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or set(item) != {"path", "status"}:
            raise ValueError("each change must contain only path and status")
        path = _validated_path(item["path"])
        status = item["status"]
        if not isinstance(status, str) or status not in _STATUS_RISK:
            raise ValueError(f"invalid status for {path}: {status!r}")
        if path in seen:
            raise ValueError(f"duplicate change path: {path}")
        seen.add(path)
        changes.append(Change(path=path, status=status))
    return changes


def read_manifest(filename: str | Path) -> list[Change]:
    payload = Path(filename).read_text(encoding="utf-8")
    if len(payload) > 200_000:
        raise ValueError("manifest exceeds 200 kB")
    return parse_changes(json.loads(payload))


def git_changes(root: str | Path, base_ref: str) -> list[Change]:
    """Committed changes from merge base to HEAD; uncommitted files are excluded."""
    if not base_ref or base_ref.startswith("-") or len(base_ref) > 200 or any(c in base_ref for c in " \t\r\n\x00"):
        raise ValueError("invalid base ref")
    base = Path(root).resolve(strict=True)
    cmd = ["git", "-C", str(base), "diff", "--no-renames", "--name-status", "-z", f"{base_ref}...HEAD", "--"]
    result = subprocess.run(cmd, capture_output=True, check=False, timeout=25)
    if result.returncode:
        raise ValueError("git diff failed: " + result.stderr.decode("utf-8", errors="replace").strip()[:300])
    fields = result.stdout.decode("utf-8", errors="strict").split("\x00")
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) % 2:
        raise ValueError("invalid git diff output")
    statuses = {"A": "added", "M": "modified", "D": "deleted", "T": "modified"}
    items: list[dict[str, str]] = []
    for i in range(0, len(fields), 2):
        status, path = fields[i : i + 2]
        if status not in statuses:
            raise ValueError(f"unsupported git file status: {status!r}")
        items.append({"status": statuses[status], "path": path})
    return parse_changes(items)


def analyze(snapshot: Snapshot, changes: list[Change]) -> dict:
    """Calculate reverse reachability for every changed component with shortest path depth."""
    reverse: dict[str, set[str]] = defaultdict(set)
    for edge in snapshot.references:
        reverse[edge.target].add(edge.source)

    grouped: dict[str, dict] = {}
    ignored: list[str] = []
    for change in changes:
        item = component_for_path(change.path)
        if item is None:
            ignored.append(f"No recognized component type: {change.path}")
            continue
        component_id, kind, name = item
        if component_id not in snapshot.components and change.status != "deleted":
            ignored.append(f"Changed component not found in snapshot: {change.path}")
            continue
        if component_id in grouped:
            prev = grouped[component_id]
            if prev["status"] != change.status:
                raise ValueError(f"conflicting statuses for component {component_id}")
            prev["paths"].append(change.path)
        else:
            grouped[component_id] = {
                "id": component_id, "kind": kind, "name": name,
                "status": change.status, "paths": [change.path],
            }

    impacts: dict[str, dict] = {}
    detailed: list[dict] = []
    for component_id, entry in sorted(grouped.items()):
        levels: dict[str, int] = {}
        todo = deque([(component_id, 0)])
        visited = {component_id}
        while todo:
            current, depth = todo.popleft()
            for dependent in sorted(reverse[current]):
                if dependent not in visited:
                    visited.add(dependent)
                    levels[dependent] = depth + 1
                    todo.append((dependent, depth + 1))
        direct = sorted(name for name, depth in levels.items() if depth == 1)
        indirect = sorted(name for name, depth in levels.items() if depth > 1)
        score = min(100, _BASE_RISK[entry["kind"]] + _STATUS_RISK[entry["status"]] + 8 * len(direct) + 3 * len(indirect))
        risk = "high" if score >= 70 else "medium" if score >= 40 else "low"
        detailed.append({
            **entry, "paths": sorted(entry["paths"]), "risk_score": score,
            "risk_level": risk, "direct_dependents": direct,
            "indirect_dependents": indirect,
            "risk_factors": [
                f"Base exposure for {entry['kind']}: {_BASE_RISK[entry['kind']]}",
                f"Change operation {entry['status']}: +{_STATUS_RISK[entry['status']]}",
                f"Direct consumers ({len(direct)}): +{8 * len(direct)}",
                f"Transitive consumers ({len(indirect)}): +{3 * len(indirect)}",
                "Score capped at 100; heuristic, not a deployment safety guarantee",
            ],
        })
        for dependent, depth in levels.items():
            if dependent in grouped:
                continue
            impact = impacts.setdefault(dependent, {"id": dependent, "via": [], "min_depth": depth})
            impact["via"].append(component_id)
            impact["min_depth"] = min(impact["min_depth"], depth)

    impacted = [dict(item, via=sorted(item["via"])) for item in sorted(impacts.values(), key=lambda x: x["id"])]
    return {
        "summary": {
            "total_components": len(snapshot.components),
            "total_references": len(snapshot.references),
            "changed_components": len(detailed),
            "impacted_components": len(impacted),
            "high_risk_changes": sum(c["risk_level"] == "high" for c in detailed),
        },
        "changes": detailed,
        "impacted": impacted,
        "ignored_changes": ignored,
        "warnings": list(snapshot.warnings),
        "disclaimer": "Read-only static analysis. Dynamic dependencies, permissions and deployment validation require separate review.",
    }
