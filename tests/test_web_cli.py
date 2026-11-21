import json
from pathlib import Path

from fastapi.testclient import TestClient

from orgimpact.cli import main
from orgimpact.web import create_app

BASE = Path(__file__).resolve().parents[1]
EXAMPLE = BASE / "examples" / "sfdx-project"
MANIFEST = BASE / "examples" / "change-manifest.json"


def test_cli_scan(capsys):
    assert main(["scan", "--root", str(EXAMPLE)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result["components"]) == 12


def test_cli_markdown_to_file(tmp_path):
    target = tmp_path / "report.md"
    code = main(["analyze", "--root", str(EXAMPLE), "--changes", str(MANIFEST), "--output", str(target)])
    assert code == 0
    assert "Change Impact Review" in target.read_text()


def test_api_snapshot_and_report():
    client = TestClient(create_app(EXAMPLE))
    assert client.get("/").status_code == 200
    assert "OrgImpact" in client.get("/").text
    assert client.get("/static/style.css").status_code == 200
    assert len(client.get("/api/snapshot").json()["components"]) == 12
    data = {"changes": json.loads(MANIFEST.read_text())}
    response = client.post("/api/analyze", json=data)
    assert response.status_code == 200
    assert response.json()["summary"]["changed_components"] == 2
    assert "AccountRiskService" in client.post("/api/export.md", json=data).text


def test_api_rejects_unsafe_path_and_unexpected_fields():
    client = TestClient(create_app(EXAMPLE))
    unsafe = client.post("/api/analyze", json={"changes": [{"path": "../../private", "status": "deleted"}]})
    assert unsafe.status_code == 422
    extra = client.post("/api/analyze", json={"changes": [], "root": "/private"})
    assert extra.status_code == 422
