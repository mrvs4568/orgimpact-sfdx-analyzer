from pathlib import Path
import subprocess

import pytest

from orgimpact.analyzer import git_changes


def run_git(directory: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(directory), *args], check=True, text=True, capture_output=True)
    return result.stdout.strip()


def test_git_changes_from_merge_base(tmp_path: Path):
    run_git(tmp_path, "init", "-b", "main")
    run_git(tmp_path, "config", "user.name", "CI Test")
    run_git(tmp_path, "config", "user.email", "ci@example.invalid")
    sub = tmp_path / "force-app" / "main" / "default" / "classes"
    sub.mkdir(parents=True)
    apex = sub / "MyService.cls"
    apex.write_text("public class MyService {}\n")
    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "initial")
    run_git(tmp_path, "checkout", "-b", "change-score")
    apex.write_text("public class MyService { public void change() {} }\n")
    new = sub / "Another Service.cls"
    new.write_text("public class AnotherService {}\n")
    run_git(tmp_path, "add", ".")
    run_git(tmp_path, "commit", "-m", "change")
    changes = git_changes(tmp_path, "main")
    assert {(c.status, c.path) for c in changes} == {
        ("modified", "force-app/main/default/classes/MyService.cls"),
        ("added", "force-app/main/default/classes/Another Service.cls"),
    }


def test_git_ref_rejects_options(tmp_path: Path):
    with pytest.raises(ValueError, match="invalid base ref"):
        git_changes(tmp_path, "--exec=bad")
