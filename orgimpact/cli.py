"""Command-line entry point for scan, analyze and local web UI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .analyzer import analyze, git_changes, read_manifest
from .render import markdown_report
from .scanner import scan


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orgimpact", description="Offline Salesforce metadata impact analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    scan_cmd = sub.add_parser("scan", help="Index metadata and print the dependency graph as JSON")
    scan_cmd.add_argument("--root", type=Path, required=True)
    analyze_cmd = sub.add_parser("analyze", help="Evaluate changed metadata and impacted consumers")
    analyze_cmd.add_argument("--root", type=Path, required=True)
    source = analyze_cmd.add_mutually_exclusive_group(required=True)
    source.add_argument("--changes", type=Path, help="JSON array of {path,status} records")
    source.add_argument("--git-base", help="Compare committed changes between merge base and HEAD")
    analyze_cmd.add_argument("--format", choices=["json", "md"], default="md")
    analyze_cmd.add_argument("--output", type=Path, help="Write report to a local file")
    web_cmd = sub.add_parser("serve", help="Start local read-only web dashboard")
    web_cmd.add_argument("--root", type=Path, required=True)
    web_cmd.add_argument("--host", default="127.0.0.1")
    web_cmd.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        if args.command == "serve":
            try:
                import uvicorn
                from .web import create_app
            except ImportError as exc:
                raise ValueError("web dependencies missing: pip install -e '.[web]'") from exc
            if args.host != "127.0.0.1":
                print("WARNING: non-loopback binding exposes metadata names to your network", file=sys.stderr)
            uvicorn.run(create_app(args.root), host=args.host, port=args.port)
            return 0
        snapshot = scan(args.root)
        if args.command == "scan":
            content = json.dumps(snapshot.as_dict(), indent=2)
        else:
            changes = read_manifest(args.changes) if args.changes is not None else git_changes(args.root, args.git_base)
            result = analyze(snapshot, changes)
            content = json.dumps(result, indent=2) if args.format == "json" else markdown_report(result)
        if getattr(args, "output", None) is not None:
            args.output.write_text(content + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")
            print(f"Wrote report: {args.output}")
        else:
            print(content)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"orgimpact: {exc}", file=sys.stderr)
        return 2
