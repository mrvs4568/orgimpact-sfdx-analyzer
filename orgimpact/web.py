"""Local-only read-only dashboard API; never accepts arbitrary filesystem paths."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from .analyzer import analyze, parse_changes
from .render import markdown_report
from .scanner import scan


class ChangeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(min_length=1, max_length=2000)
    status: str


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    changes: list[ChangeInput] = Field(max_length=1000)


def create_app(root: str | Path) -> FastAPI:
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    assets = Path(__file__).parent / "static"
    app = FastAPI(title="OrgImpact", version="0.1.0", docs_url="/api/docs", redoc_url=None)

    @app.get("/")
    def index():
        return FileResponse(assets / "index.html")

    @app.get("/static/style.css")
    def style():
        return FileResponse(assets / "style.css", media_type="text/css")

    @app.get("/static/app.js")
    def script():
        return FileResponse(assets / "app.js", media_type="text/javascript")

    @app.get("/api/snapshot")
    def snapshot():
        return scan(root).as_dict()

    def build_report(data: AnalysisRequest) -> dict:
        try:
            changes = parse_changes([item.model_dump() for item in data.changes])
            return analyze(scan(root), changes)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/analyze")
    def run_analysis(data: AnalysisRequest):
        return build_report(data)

    @app.post("/api/export.md", response_class=PlainTextResponse)
    def export(data: AnalysisRequest):
        return PlainTextResponse(markdown_report(build_report(data)), media_type="text/markdown")

    return app
