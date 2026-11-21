"""Conservative Salesforce DX dependency scanner.

Every reported edge is supported by an explicit static reference. Dynamic Apex,
Flow expressions and managed-package resolution are intentionally out of scope.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

from .models import Component, Reference, Snapshot

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_FILES = 20_000

_CLASS_CALL = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\s*\.")
_CLASS_NEW = re.compile(r"\bnew\s+([A-Za-z][A-Za-z0-9_]*)\s*\(")
_SOQL_OBJECT = re.compile(r"\bFROM\s+([A-Za-z][A-Za-z0-9_]*)\b", re.I)
_TRIGGER_OBJECT = re.compile(r"\btrigger\s+\w+\s+on\s+([A-Za-z][A-Za-z0-9_]*)\b", re.I)
_LWC_APEX = re.compile(r"@salesforce/apex/([A-Za-z][\w]*)\.[A-Za-z][\w]*")
_LWC_SCHEMA = re.compile(r"@salesforce/schema/([A-Za-z][\w]*(?:\.[A-Za-z][\w]*)?)")
_APEX_SCHEMA_FIELD = re.compile(r"\bSchema\.SObjectType\.([A-Za-z][\w]*)\.fields\.([A-Za-z][\w]*)")


def component_for_path(path: str) -> tuple[str, str, str] | None:
    """Return (id, kind, human name) from a relative source path."""
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    filename = parts[-1] if parts else ""
    if filename.endswith(".cls") and "classes" in parts:
        name = filename[:-4]
        return f"ApexClass:{name}", "ApexClass", name
    if filename.endswith(".trigger") and "triggers" in parts:
        name = filename[:-8]
        return f"ApexTrigger:{name}", "ApexTrigger", name
    if filename.endswith(".flow-meta.xml") and "flows" in parts:
        name = filename[:-14]
        return f"Flow:{name}", "Flow", name
    if filename.endswith(".permissionset-meta.xml") and "permissionsets" in parts:
        name = filename[:-23]
        return f"PermissionSet:{name}", "PermissionSet", name
    if "objects" in parts:
        pos = parts.index("objects")
        if len(parts) > pos + 2:
            obj = parts[pos + 1]
            if filename == f"{obj}.object-meta.xml":
                return f"CustomObject:{obj}", "CustomObject", obj
            if "fields" in parts[pos + 2:] and filename.endswith(".field-meta.xml"):
                name = f"{obj}.{filename[:-15]}"
                return f"CustomField:{name}", "CustomField", name
    if "lwc" in parts:
        pos = parts.index("lwc")
        if len(parts) > pos + 2 and filename.endswith((".js", ".html")) and not filename.endswith(".test.js"):
            name = parts[pos + 1]
            return f"LWC:{name}", "LWC", name
    return None


def _get_text(path: Path) -> str:
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("file exceeds 2 MiB safety limit")
    return path.read_text(encoding="utf-8")


def _local(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _find_child_text(element: ET.Element, tag: str) -> str | None:
    return next((x.text.strip() for x in element if _local(x) == tag and x.text and x.text.strip()), None)


def _xml_references(text: str, kind: str) -> list[tuple[str, str]]:
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("DTD and entity declarations are not accepted")
    tree = ET.fromstring(text)
    refs: list[tuple[str, str]] = []
    if kind == "Flow":
        for element in tree.iter():
            tag = _local(element)
            if tag in {"recordLookups", "recordCreates", "recordUpdates", "recordDeletes", "start"}:
                obj = _find_child_text(element, "object")
                if obj:
                    refs.append((f"CustomObject:{obj}", "flow-object"))
            if tag == "subflows":
                name = _find_child_text(element, "flowName")
                if name:
                    refs.append((f"Flow:{name}", "subflow"))
    elif kind == "PermissionSet":
        for element in tree.iter():
            tag = _local(element)
            if tag == "objectPermissions":
                obj = _find_child_text(element, "object")
                if obj:
                    refs.append((f"CustomObject:{obj}", "object-permission"))
            if tag == "fieldPermissions":
                fld = _find_child_text(element, "field")
                if fld:
                    refs.append((f"CustomField:{fld}", "field-permission"))
    return refs


def _mask_apex_noncode(text: str) -> str:
    """Mask Apex comments and strings while preserving offsets and newlines."""
    output = list(text)
    i = 0
    n = len(text)

    while i < n:
        start = i

        if text.startswith("//", i):
            end = text.find("\n", i + 2)
            i = n if end == -1 else end

        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2

        elif text[i] in ("'", '"'):
            quote = text[i]
            i += 1

            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                elif text[i] == quote:
                    if i + 1 < n and text[i + 1] == quote:
                        i += 2
                    else:
                        i += 1
                        break
                else:
                    i += 1

        else:
            i += 1
            continue

        for j in range(start, i):
            if text[j] != "\n":
                output[j] = " "

    return "".join(output)


def _code_references(text: str, kind: str) -> list[tuple[str, str, int]]:
    rules: list[tuple[re.Pattern[str], str, str]] = []
    if kind in {"ApexClass", "ApexTrigger"}:
        rules = [
            (_CLASS_CALL, "ApexClass", "apex-call"),
            (_CLASS_NEW, "ApexClass", "apex-new"),
            (_SOQL_OBJECT, "CustomObject", "soql-object"),
            (_TRIGGER_OBJECT, "CustomObject", "trigger-object"),
        ]
    elif kind == "LWC":
        rules = [(_LWC_APEX, "ApexClass", "lwc-apex"), (_LWC_SCHEMA, "schema", "lwc-schema")]

    code_text = (
        _mask_apex_noncode(text)
        if kind in {"ApexClass", "ApexTrigger"}
        else text
    )
    refs: list[tuple[str, str, int]] = []
    for pattern, target_kind, relation in rules:
        for match in pattern.finditer(code_text):
            name = match.group(1)
            line = text.count("\n", 0, match.start()) + 1
            if target_kind == "schema":
                if "." in name:
                    obj, _ = name.split(".", 1)
                    refs.extend([(f"CustomField:{name}", relation, line), (f"CustomObject:{obj}", "schema-object", line)])
                else:
                    refs.append((f"CustomObject:{name}", "schema-object", line))
            else:
                refs.append((f"{target_kind}:{name}", relation, line))
    if kind in {"ApexClass", "ApexTrigger"}:
        for match in _APEX_SCHEMA_FIELD.finditer(code_text):
            name = f"{match.group(1)}.{match.group(2)}"
            refs.append((f"CustomField:{name}", "apex-schema-field", text.count("\n", 0, match.start()) + 1))
    return refs


def scan(root: str | Path) -> Snapshot:
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    snapshot = Snapshot()
    file_index: list[tuple[str, Path, str]] = []
    by_component: dict[str, list[str]] = defaultdict(list)
    count = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or ".git" in path.relative_to(root).parts:
            continue
        count += 1
        if count > MAX_FILES:
            raise ValueError(f"project contains more than {MAX_FILES:,} files")
        rel = path.relative_to(root).as_posix()
        entry = component_for_path(rel)
        if entry is None:
            continue
        component_id, kind, name = entry
        by_component[component_id].append(rel)
        file_index.append((rel, path, kind))

    for component_id, paths in by_component.items():
        kind, name = component_id.split(":", 1)
        snapshot.components[component_id] = Component(component_id, kind, name, tuple(sorted(paths)))
    seen: set[tuple[str, str, str, str, int | None]] = set()
    for rel, path, kind in file_index:
        source = component_for_path(rel)[0]  # type: ignore[index]
        try:
            text = _get_text(path)
            raw_refs = (
                [(target, relation, None) for target, relation in _xml_references(text, kind)]
                if kind in {"Flow", "PermissionSet", "CustomField", "CustomObject"}
                else _code_references(text, kind)
            )
            for target, relation, line in raw_refs:
                if target == source or target not in snapshot.components:
                    continue
                key = (source, target, relation, rel, line)
                if key not in seen:
                    seen.add(key)
                    snapshot.references.append(Reference(source, target, relation, rel, line))
        except (OSError, UnicodeError, ET.ParseError, ValueError) as exc:
            snapshot.warnings.append(f"Skipped {rel}: {type(exc).__name__}: {exc}")
    snapshot.references.sort(key=lambda x: (x.source, x.target, x.relation, x.path, x.line or 0))
    return snapshot
