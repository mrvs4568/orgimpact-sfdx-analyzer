"""Human-readable release-review evidence output."""
from __future__ import annotations


def markdown_report(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# OrgImpact — Change Impact Review", "",
        "**Static analysis only — not a deploy authorization.**", "",
        f"- Components indexed: {summary['total_components']}",
        f"- Dependencies indexed: {summary['total_references']}",
        f"- Changed components: {summary['changed_components']}",
        f"- Other impacted components: {summary['impacted_components']}",
        f"- High-risk changes: {summary['high_risk_changes']}", "",
        "## Changed components", "",
    ]
    if not report["changes"]:
        lines.extend(["No recognizable metadata changes found.", ""])
    for item in report["changes"]:
        lines.extend([
            f"### `{item['id']}` — {item['risk_level'].upper()} ({item['risk_score']}/100)", "",
            f"- Operation: {item['status']}",
            f"- Paths: {', '.join(f'`{p}`' for p in item['paths'])}",
            f"- Direct dependents: {', '.join(f'`{p}`' for p in item['direct_dependents']) or 'None detected'}",
            f"- Transitive dependents: {', '.join(f'`{p}`' for p in item['indirect_dependents']) or 'None detected'}",
            "- Risk evidence:",
        ])
        lines.extend(f"  - {factor}" for factor in item["risk_factors"])
        lines.append("")
    lines.extend(["## Impact summary", ""])
    if not report["impacted"]:
        lines.append("No additional dependent components detected.")
    else:
        for item in report["impacted"]:
            lines.append(f"- `{item['id']}` (depth {item['min_depth']}; triggered by {', '.join(item['via'])})")
    lines.extend(["", "## Limitations and warnings", "", report["disclaimer"], ""])
    lines.extend(f"- {warning}" for warning in report["ignored_changes"] + report["warnings"])
    if not (report["ignored_changes"] or report["warnings"]):
        lines.append("- No scan warnings")
    return "\n".join(lines) + "\n"
