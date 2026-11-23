from pathlib import Path

import pytest

from orgimpact.scanner import component_for_path, scan

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sfdx-project"


def test_component_naming():
    assert component_for_path("force-app/main/default/flows/Account_Review.flow-meta.xml")[0] == "Flow:Account_Review"
    assert component_for_path("force-app/main/default/objects/Account/fields/Health_Score__c.field-meta.xml")[0] == "CustomField:Account.Health_Score__c"
    assert component_for_path("force-app/main/default/permissionsets/Account_Viewer.permissionset-meta.xml")[0] == "PermissionSet:Account_Viewer"
    assert component_for_path("force-app/main/default/lwc/accountHealth/accountHealth.test.js") is None


def test_scan_finds_real_static_relationships():
    result = scan(EXAMPLE)
    assert len(result.components) == 12
    assert not result.warnings
    edges = {(e.source, e.target) for e in result.references}
    assert ("LWC:accountHealth", "ApexClass:AccountRiskController") in edges
    assert ("LWC:accountHealth", "CustomField:Account.Health_Score__c") in edges
    assert ("ApexClass:AccountRiskController", "ApexClass:AccountRiskService") in edges
    assert ("ApexTrigger:AccountRiskTrigger", "ApexClass:AccountRiskService") in edges
    assert ("ApexTrigger:AccountRiskTrigger", "CustomObject:Account") in edges
    assert ("Flow:Account_Review", "CustomObject:Account") in edges
    assert ("Flow:Account_Followup", "Flow:Account_Review") in edges
    assert ("PermissionSet:Account_Viewer", "CustomField:Account.Health_Score__c") in edges
    assert ("ApexClass:AccountRiskService", "CustomField:Account.Review_Status__c") in edges


def test_xml_parse_warning_does_not_abort(tmp_path: Path):
    target = tmp_path / "flows" / "Broken.flow-meta.xml"
    target.parent.mkdir()
    target.write_text("<Flow><recordLookups>", encoding="utf-8")
    result = scan(tmp_path)
    assert "Flow:Broken" in result.components
    assert len(result.warnings) == 1
    assert "Broken.flow-meta.xml" in result.warnings[0]


def test_external_entities_blocked(tmp_path: Path):
    target = tmp_path / "flows" / "Unsafe.flow-meta.xml"
    target.parent.mkdir()
    target.write_text('<!DOCTYPE x [ <!ENTITY e SYSTEM "file:///etc/passwd"> ]><Flow>&e;</Flow>')
    result = scan(tmp_path)
    assert len(result.warnings) == 1
    assert "DTD" in result.warnings[0]


def test_symlink_file_is_not_scanned(tmp_path: Path):
    external = tmp_path / "secret.cls"
    external.write_text("secret")
    target = tmp_path / "classes"
    target.mkdir()
    (target / "Linked.cls").symlink_to(external)
    result = scan(tmp_path)
    assert "ApexClass:Linked" not in result.components


@pytest.mark.parametrize("body", [
    "// TargetService.run();",
    "/* TargetService.run(); */",
    "/* Start comment\nTargetService.run();\nEnd comment */",
    "String message = 'TargetService.run()';",
    "String message = 'new TargetService()';",
])
def test_apex_ignores_comments_and_string_literals(tmp_path: Path, body: str):
    classes = tmp_path / "classes"
    classes.mkdir()

    (classes / "TargetService.cls").write_text(
        "public class TargetService {}",
        encoding="utf-8",
    )

    (classes / "SourceClass.cls").write_text(
        "public class SourceClass {\n"
        "  public void check() {\n"
        f"    {body}\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )

    result = scan(tmp_path)

    assert not any(
        edge.source == "ApexClass:SourceClass"
        and edge.target == "ApexClass:TargetService"
        for edge in result.references
    )


def test_apex_real_reference_preserves_line_number(tmp_path: Path):
    classes = tmp_path / "classes"
    classes.mkdir()

    (classes / "TargetService.cls").write_text(
        "public class TargetService {}",
        encoding="utf-8",
    )

    (classes / "SourceClass.cls").write_text(
        "public class SourceClass {\n"
        "  /* TargetService.run();\n"
        "     TargetService.run(); */\n"
        "  String message = 'TargetService.run();';\n"
        "  public void check() { TargetService.run(); }\n"
        "}\n",
        encoding="utf-8",
    )

    result = scan(tmp_path)

    references = [
        edge for edge in result.references
        if edge.source == "ApexClass:SourceClass"
        and edge.target == "ApexClass:TargetService"
    ]

    assert len(references) == 1
    assert references[0].line == 5


def test_apex_qualified_field_reference_detection(tmp_path: Path):
    field = (
        tmp_path / "objects" / "Account" / "fields"
        / "Health_Score__c.field-meta.xml"
    )
    field.parent.mkdir(parents=True)
    field.write_text("<CustomField/>", encoding="utf-8")

    classes = tmp_path / "classes"
    classes.mkdir()

    (classes / "SourceClass.cls").write_text(
        "public class SourceClass {\n"
        "  // Account.Health_Score__c\n"
        "  String message = 'Account.Health_Score__c';\n"
        "  /* Account.Health_Score__c */\n"
        "  Object fieldRef = Account.Health_Score__c;\n"
        "  Object other = record.Health_Score__c;\n"
        "  Object missing = Account.Unknown__c;\n"
        "}\n",
        encoding="utf-8",
    )

    result = scan(tmp_path)

    references = [
        edge for edge in result.references
        if edge.source == "ApexClass:SourceClass"
        and edge.target == "CustomField:Account.Health_Score__c"
    ]

    assert [(edge.relation, edge.line) for edge in references] == [
        ("apex-field", 5)
    ]
