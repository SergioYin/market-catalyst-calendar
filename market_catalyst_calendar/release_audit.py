"""Offline release audit checks for the repository."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .demo_bundle import _bundle_files


REQUIRED_COMMANDS = [
    "validate",
    "upcoming",
    "stale",
    "brief",
    "exposure",
    "risk-budget",
    "sector-map",
    "review-plan",
    "thesis-map",
    "scenario-matrix",
    "evidence-audit",
    "quality-gate",
    "doctor",
    "broker-matrix",
    "source-pack",
    "watchlist",
    "decision-log",
    "drilldown",
    "command-cookbook",
    "tutorial",
    "agent-handoff",
    "run-preset",
    "taxonomy",
    "post-event",
    "export-demo",
    "export-preset-example",
    "demo-bundle",
    "fixture-gallery",
    "compare",
    "merge",
    "html-dashboard",
    "static-site",
    "export-csv",
    "export-ics",
    "import-csv",
    "create-archive",
    "verify-archive",
    "release-audit",
    "changelog",
    "smoke-matrix",
    "finalize-release",
]

RELEASE_AUDIT_SCHEMA_FIELDS = [
    "schema_version",
    "ok",
    "root",
    "checks",
    "summary",
    "id",
    "status",
    "detail",
    "expected_count",
    "checked_count",
    "missing",
    "extra",
    "mismatches",
    "required_commands",
    "missing_commands",
    "required_fields",
    "missing_fields",
    "workflow_files",
    "blockers",
    "components",
    "release_notes",
]

SKILL_PATH = Path("skills/agent/market-catalyst-calendar/SKILL.md")


def release_audit_json(root: Path) -> Dict[str, object]:
    """Return a deterministic release audit report for ``root``."""

    root = root.resolve()
    checks = [
        _examples_check(root),
        _readme_commands_check(root),
        _schema_fields_check(root),
        _skill_check(root),
        _workflow_files_check(root),
    ]
    passed = sum(1 for check in checks if check["status"] == "pass")
    failed = len(checks) - passed
    return {
        "schema_version": "release-audit/v1",
        "ok": failed == 0,
        "root": str(root),
        "checks": checks,
        "summary": {
            "check_count": len(checks),
            "failed_count": failed,
            "passed_count": passed,
        },
    }


def release_audit_markdown(report: Dict[str, object]) -> str:
    lines = [
        "# Market Catalyst Release Audit",
        "",
        f"Status: {'PASS' if report['ok'] else 'FAIL'}",
        f"Root: `{report['root']}`",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in report["checks"]:
        status = str(check["status"]).upper()
        lines.append(f"| {check['id']} | {status} | {_escape_table(str(check['detail']))} |")
    lines.append("")
    for check in report["checks"]:
        if check["status"] == "pass":
            continue
        lines.append(f"## {check['id']}")
        _append_items(lines, "Missing", check.get("missing", []))
        _append_items(lines, "Extra", check.get("extra", []))
        _append_items(lines, "Mismatches", check.get("mismatches", []))
        _append_items(lines, "Missing commands", check.get("missing_commands", []))
        _append_items(lines, "Missing fields", check.get("missing_fields", []))
        _append_items(lines, "Workflow files", check.get("workflow_files", []))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _examples_check(root: Path) -> Dict[str, object]:
    expected = {
        path.removeprefix("examples/"): text
        for path, text in _bundle_files().items()
        if path.startswith("examples/")
    }
    examples_dir = root / "examples"
    actual_paths = set()
    if examples_dir.is_dir():
        actual_paths = {
            path.relative_to(examples_dir).as_posix()
            for path in examples_dir.iterdir()
            if path.is_file() and path.name not in {".gitkeep", "README.md"}
        }
    expected_paths = set(expected)
    missing = sorted(expected_paths - actual_paths)
    extra = sorted(actual_paths - expected_paths)
    mismatches = []
    for relative_path in sorted(expected_paths & actual_paths):
        actual = (examples_dir / relative_path).read_bytes()
        if actual != expected[relative_path].encode("utf-8"):
            mismatches.append(relative_path)
    ok = not missing and not extra and not mismatches
    return {
        "id": "examples-regenerated",
        "status": "pass" if ok else "fail",
        "detail": (
            f"{len(expected_paths) - len(missing)} of {len(expected_paths)} expected fixtures match"
            if ok
            else f"{len(missing)} missing, {len(extra)} extra, {len(mismatches)} mismatched fixtures"
        ),
        "expected_count": len(expected_paths),
        "checked_count": len(actual_paths),
        "missing": missing,
        "extra": extra,
        "mismatches": mismatches,
    }


def _readme_commands_check(root: Path) -> Dict[str, object]:
    readme_path = root / "README.md"
    text = _read_optional_text(readme_path)
    missing = [command for command in REQUIRED_COMMANDS if not _mentions_command(text, command)]
    return {
        "id": "readme-required-commands",
        "status": "pass" if not missing else "fail",
        "detail": f"{len(REQUIRED_COMMANDS) - len(missing)} of {len(REQUIRED_COMMANDS)} required commands documented",
        "required_commands": REQUIRED_COMMANDS,
        "missing_commands": missing,
    }


def _schema_fields_check(root: Path) -> Dict[str, object]:
    schema_path = root / "docs" / "SCHEMA.md"
    text = _read_optional_text(schema_path)
    missing = [field for field in RELEASE_AUDIT_SCHEMA_FIELDS if f"`{field}`" not in text]
    return {
        "id": "schema-release-audit-fields",
        "status": "pass" if not missing else "fail",
        "detail": f"{len(RELEASE_AUDIT_SCHEMA_FIELDS) - len(missing)} of {len(RELEASE_AUDIT_SCHEMA_FIELDS)} release-audit fields documented",
        "required_fields": RELEASE_AUDIT_SCHEMA_FIELDS,
        "missing_fields": missing,
    }


def _skill_check(root: Path) -> Dict[str, object]:
    skill_path = root / SKILL_PATH
    text = _read_optional_text(skill_path)
    missing = []
    if not skill_path.is_file():
        missing.append(SKILL_PATH.as_posix())
    for command in ["release-audit", "finalize-release"]:
        if command not in text:
            missing.append(f"{command} mention")
    return {
        "id": "agent-skill",
        "status": "pass" if not missing else "fail",
        "detail": f"{SKILL_PATH.as_posix()} exists and documents release commands" if not missing else "skill file is missing or incomplete",
        "missing": missing,
    }


def _workflow_files_check(root: Path) -> Dict[str, object]:
    workflows = root / ".github" / "workflows"
    files = []
    if workflows.exists():
        files = sorted(path.relative_to(root).as_posix() for path in workflows.rglob("*") if path.is_file())
    return {
        "id": "no-workflow-files",
        "status": "pass" if not files else "fail",
        "detail": "no workflow files found" if not files else f"{len(files)} workflow files found",
        "workflow_files": files,
    }


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


def _append_items(lines: List[str], title: str, values: object) -> None:
    if not isinstance(values, list) or not values:
        return
    lines.append(f"{title}:")
    for value in values:
        lines.append(f"- `{value}`")


def _escape_table(text: str) -> str:
    return text.replace("|", "\\|")
