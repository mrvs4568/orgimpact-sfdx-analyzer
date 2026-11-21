import json
from pathlib import Path

import pytest

from orgimpact.analyzer import analyze, parse_changes, read_manifest
from orgimpact.render import markdown_report
from orgimpact.scanner import scan

BASE = Path(__file__).resolve().parents[1]
EXAMPLE = BASE / "examples" / "sfdx-project"


def test_impact_is_transitive_and_explainable():
    result = analyze(scan(EXAMPLE), read_manifest(BASE / "examples" / "change-manifest.json"))
    assert result["summary"]["changed_components"] == 2
    assert result["summary"]["impacted_components"] >= 3
    changed = {item["id"]: item for item in result["changes"]}
    field = changed["CustomField:Account.Health_Score__c"]
    assert "LWC:accountHealth" in field["direct_dependents"]
    assert "PermissionSet:Account_Viewer" in field["direct_dependents"]
    service = changed["ApexClass:AccountRiskService"]
    assert "ApexTrigger:AccountRiskTrigger" in service["direct_dependents"]
    assert "LWC:accountHealth" in service["indirect_dependents"]
    assert any(item["id"] == "LWC:accountHealth" for item in result["impacted"])
    assert "Score capped at 100" in " ".join(service["risk_factors"])


def test_markdown_report_contains_evidence():
    report = analyze(scan(EXAMPLE), read_manifest(BASE / "examples" / "change-manifest.json"))
    md = markdown_report(report)
    assert "AccountRiskService" in md
    assert "Dynamic dependencies" in md
    assert "not a deploy authorization" in md


@pytest.mark.parametrize("payload", [
    [{"path": "../secrets", "status": "modified"}],
    [{"path": "/root/password", "status": "deleted"}],
    [{"path": "foo\\bar.cls", "status": "modified"}],
    [{"path": "a.cls", "status": "renamed"}],
    [{"path": "a.cls", "status": "modified", "extra": 2}],
    [{"path": "a.cls", "status": "modified"}, {"path": "a.cls", "status": "added"}],
    {"changes": []},
    [{"path": "file.cls", "status": ["modified"]}],
])
def test_manifest_rejects_invalid_payload(payload):
    with pytest.raises(ValueError):
        parse_changes(payload)


def test_deleted_metadata_is_still_considered():
    changes = parse_changes([{"path": "force-app/main/default/classes/OldService.cls", "status": "deleted"}])
    report = analyze(scan(EXAMPLE), changes)
    assert report["summary"]["changed_components"] == 1
    assert report["changes"][0]["risk_score"] == 55


def test_unknown_files_are_reported_not_silently_classified():
    changes = parse_changes([{"path": "README.md", "status": "modified"}])
    report = analyze(scan(EXAMPLE), changes)
    assert report["summary"]["changed_components"] == 0
    assert len(report["ignored_changes"]) == 1


def test_conflicting_component_change_status_rejected():
    changes = parse_changes([
        {"path": "force-app/main/default/lwc/accountHealth/accountHealth.js", "status": "added"},
        {"path": "force-app/main/default/lwc/accountHealth/accountHealth.html", "status": "modified"},
    ])
    with pytest.raises(ValueError, match="conflicting statuses"):
        analyze(scan(EXAMPLE), changes)


def test_json_report_roundtrip():
    report = analyze(scan(EXAMPLE), read_manifest(BASE / "examples" / "change-manifest.json"))
    assert json.loads(json.dumps(report))["summary"]["total_components"] == 12


def test_object_change_reaches_subflow_and_high_risk():
    change = read_manifest(BASE / "examples" / "high-impact-manifest.json")
    report = analyze(scan(EXAMPLE), change)
    obj = report["changes"][0]
    assert obj["id"] == "CustomObject:Account"
    assert obj["risk_level"] == "high"
    assert "Flow:Account_Review" in obj["direct_dependents"]
    assert "Flow:Account_Followup" in obj["indirect_dependents"]
