"""Package and release status report."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from . import __version__
from .taxonomy import taxonomy_json


def version_report_json(root: Path, repo: Path) -> Dict[str, object]:
    """Return a deterministic package status report for release handoff."""

    root = root.resolve()
    repo = repo.resolve()
    taxonomy = taxonomy_json()
    fixture_count = _fixture_count(root)
    release_audit = _release_audit_status(root)
    return {
        "schema_version": "version-report/v1",
        "package": {
            "name": "market-catalyst-calendar",
            "version": __version__,
        },
        "summary": {
            "command_count": taxonomy["summary"]["command_count"],
            "fixture_count": fixture_count,
            "release_audit_status": release_audit["status"],
        },
        "command_count": taxonomy["summary"]["command_count"],
        "fixture_count": fixture_count,
        "release_audit": release_audit,
        "git": _git_status(repo),
    }


def version_report_markdown(payload: Dict[str, object]) -> str:
    package = payload["package"]
    release_audit = payload["release_audit"]
    git = payload["git"]
    lines = [
        "# Market Catalyst Version Report",
        "",
        f"Package: `{package['name']}`",
        f"Version: `{package['version']}`",
        f"Commands: {payload['command_count']}",
        f"Fixtures: {payload['fixture_count']}",
        f"Release audit: {str(release_audit['status']).upper()}",
        "",
        "## Git",
        "",
    ]
    if git["available"]:
        lines.extend(
            [
                f"- Latest tag: `{git['latest_tag'] or 'none'}`",
                f"- Commit: `{git['commit']['short_hash']}`",
                f"- Commit date: `{git['commit']['date']}`",
                f"- Subject: {git['commit']['subject']}",
            ]
        )
    else:
        lines.append(f"- Unavailable: {git['detail']}")
    if release_audit["blockers"]:
        lines.extend(["", "## Release Audit Blockers", ""])
        for blocker in release_audit["blockers"]:
            lines.append(f"- {blocker}")
    return "\n".join(lines).rstrip() + "\n"


def _fixture_count(root: Path) -> int:
    examples_dir = root / "examples"
    if not examples_dir.is_dir():
        return 0
    return sum(1 for path in examples_dir.iterdir() if path.is_file() and path.name not in {".gitkeep", "README.md"})


def _release_audit_status(root: Path) -> Dict[str, object]:
    """Return a non-recursive snapshot of release-audit readiness."""

    from .release_audit import RELEASE_AUDIT_SCHEMA_FIELDS, REQUIRED_COMMANDS, SKILL_PATH

    readme_text = _read_optional_text(root / "README.md")
    schema_text = _read_optional_text(root / "docs" / "SCHEMA.md")
    skill_path = root / SKILL_PATH
    skill_text = _read_optional_text(skill_path)
    workflow_files = _workflow_files(root)

    missing_commands = [command for command in REQUIRED_COMMANDS if not _mentions_command(readme_text, command)]
    missing_fields = [field for field in RELEASE_AUDIT_SCHEMA_FIELDS if f"`{field}`" not in schema_text]
    missing_skill = []
    if not skill_path.is_file():
        missing_skill.append(SKILL_PATH.as_posix())
    for command in ["release-audit", "finalize-release", "version-report"]:
        if command not in skill_text:
            missing_skill.append(f"{command} mention")

    blockers: List[str] = []
    if missing_commands:
        blockers.append(f"{len(missing_commands)} README command mentions missing")
    if missing_fields:
        blockers.append(f"{len(missing_fields)} schema release-audit field mentions missing")
    if missing_skill:
        blockers.append(f"{len(missing_skill)} agent skill mentions missing")
    if workflow_files:
        blockers.append(f"{len(workflow_files)} workflow files present")

    return {
        "status": "pass" if not blockers else "fail",
        "ok": not blockers,
        "checked_with": "version-report/nonrecursive-release-snapshot/v1",
        "detail": "release docs, skill, and workflow guardrails pass" if not blockers else "; ".join(blockers),
        "blockers": blockers,
        "missing_commands": missing_commands,
        "missing_schema_fields": missing_fields,
        "missing_skill_items": missing_skill,
        "workflow_files": workflow_files,
    }


def _git_status(repo: Path) -> Dict[str, object]:
    commit = _git(repo, ["log", "-1", "--format=%H%x00%h%x00%cI%x00%s"])
    if commit is None:
        return {"available": False, "detail": "git metadata unavailable", "latest_tag": None, "commit": None}
    parts = commit.split("\x00")
    if len(parts) != 4:
        return {"available": False, "detail": "git commit output was not parseable", "latest_tag": None, "commit": None}
    latest_tag = _git(repo, ["describe", "--tags", "--abbrev=0"])
    return {
        "available": True,
        "repo": repo.name,
        "latest_tag": latest_tag,
        "commit": {
            "hash": parts[0],
            "short_hash": parts[1],
            "date": parts[2],
            "subject": parts[3],
        },
    }


def _git(repo: Path, args: List[str]) -> Optional[str]:
    try:
        result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _workflow_files(root: Path) -> List[str]:
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in workflows.rglob("*") if path.is_file())


def _read_optional_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _mentions_command(text: str, command: str) -> bool:
    patterns = [
        f"market_catalyst_calendar {command}",
        f"market-catalyst-calendar {command}",
        f"`{command}`",
    ]
    return any(pattern in text for pattern in patterns)
