"""Deterministic release finalizer checklist."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from .fixture_gallery import fixture_gallery_json


def finalize_release_json(
    root: Path,
    repo: Path,
    since_tag: str,
    to_ref: str = "HEAD",
    include_merges: bool = False,
) -> Dict[str, object]:
    """Run release finalizer inputs and return a normalized checklist."""

    from .changelog import changelog_json
    from .demo_bundle import bundled_fixture_gallery_json
    from .release_audit import release_audit_json
    from .smoke_matrix import smoke_matrix_json

    root = root.resolve()
    repo = repo.resolve()
    release_audit = release_audit_json(root)
    smoke_matrix = smoke_matrix_json("json", include_finalize=False)
    gallery = bundled_fixture_gallery_json()
    changelog = changelog_json(repo, since_tag, to_ref, include_merges)
    return finalize_release_json_from_reports(
        root_label=_display_path(root),
        repo_label=_display_path(repo),
        release_audit=release_audit,
        smoke_matrix=smoke_matrix,
        fixture_gallery=gallery,
        changelog=changelog,
    )


def finalize_release_json_from_reports(
    root_label: str,
    repo_label: str,
    release_audit: Dict[str, object],
    smoke_matrix: Dict[str, object],
    fixture_gallery: Dict[str, object],
    changelog: Dict[str, object],
) -> Dict[str, object]:
    """Combine component reports into a stable release checklist payload."""

    release_ok = bool(release_audit["ok"])
    smoke_ok = bool(smoke_matrix["ok"])
    fixture_count = int(fixture_gallery["summary"]["fixture_count"])  # type: ignore[index]
    commit_count = int(changelog["commit_count"])
    checklist = [
        _check_item(
            "release-audit",
            release_ok,
            f"{release_audit['summary']['passed_count']} passed / {release_audit['summary']['check_count']} checks",
            _failed_release_checks(release_audit),
        ),
        _check_item(
            "smoke-matrix",
            smoke_ok,
            f"{smoke_matrix['summary']['passed_count']} passed / {smoke_matrix['summary']['command_count']} commands",
            _failed_smoke_commands(smoke_matrix),
        ),
        _check_item(
            "fixture-gallery",
            fixture_count > 0,
            f"{fixture_count} fixtures indexed",
            [],
        ),
        _check_item(
            "changelog",
            commit_count > 0,
            f"{commit_count} commits since {changelog['since_tag']}",
            [] if commit_count > 0 else ["no commits in release range"],
        ),
    ]
    blockers = sorted({blocker for item in checklist for blocker in item["blockers"]})
    return {
        "schema_version": "finalize-release/v1",
        "ok": all(item["ok"] for item in checklist),
        "root": root_label,
        "repo": repo_label,
        "range": changelog["range"],
        "since_tag": changelog["since_tag"],
        "to_ref": changelog["to_ref"],
        "checklist": checklist,
        "blockers": blockers,
        "components": {
            "release_audit": _release_audit_summary(release_audit),
            "smoke_matrix": _smoke_matrix_summary(smoke_matrix),
            "fixture_gallery": _fixture_gallery_summary(fixture_gallery),
            "changelog": _changelog_summary(changelog),
        },
        "release_notes": _release_notes_summary(changelog),
    }


def finalize_release_markdown(payload: Dict[str, object]) -> str:
    lines = [
        "# Market Catalyst Release Finalizer",
        "",
        f"Status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"Root: `{payload['root']}`",
        f"Repo: `{payload['repo']}`",
        f"Range: `{payload['range']}`",
        "",
        "## Checklist",
        "",
    ]
    for item in payload["checklist"]:
        marker = "x" if item["ok"] else " "
        lines.append(f"- [{marker}] `{item['id']}` - {item['detail']}")
        for blocker in item["blockers"]:
            lines.append(f"  - blocker: {blocker}")
    lines.extend(
        [
            "",
            "## Components",
            "",
            "| Component | Status | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for name in ["release_audit", "smoke_matrix", "fixture_gallery", "changelog"]:
        component = payload["components"][name]
        lines.append(f"| {name.replace('_', '-')} | {'PASS' if component['ok'] else 'FAIL'} | {_escape_table(component['detail'])} |")
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        for blocker in payload["blockers"]:
            lines.append(f"- {blocker}")
    lines.extend(["", "## Release Notes", ""])
    notes = payload["release_notes"]
    lines.append(f"- Commits: {notes['commit_count']}")
    lines.append(f"- Breaking changes: {notes['breaking_change_count']}")
    for category in notes["categories"]:
        lines.append(f"- {category['title']}: {category['commit_count']}")
    return "\n".join(lines).rstrip() + "\n"


def example_finalize_release_json(gallery: Dict[str, object]) -> Dict[str, object]:
    release_audit = {
        "schema_version": "release-audit/v1",
        "ok": True,
        "root": ".",
        "checks": [
            {"id": "examples-regenerated", "status": "pass", "detail": "all expected fixtures match"},
            {"id": "readme-required-commands", "status": "pass", "detail": "all required commands documented"},
            {"id": "schema-release-audit-fields", "status": "pass", "detail": "all release fields documented"},
            {"id": "agent-skill", "status": "pass", "detail": "skill file documents release commands"},
            {"id": "no-workflow-files", "status": "pass", "detail": "no workflow files found"},
        ],
        "summary": {"check_count": 5, "failed_count": 0, "passed_count": 5},
    }
    smoke_matrix = {
        "schema_version": "smoke-matrix/v1",
        "ok": True,
        "summary": {"command_count": 42, "failed_count": 0, "passed_count": 42},
        "commands": [
            {"command": "release-audit", "status": "pass", "detail": "ok"},
            {"command": "smoke-matrix", "status": "pass", "detail": "ok"},
            {"command": "fixture-gallery", "status": "pass", "detail": "ok"},
            {"command": "changelog", "status": "pass", "detail": "ok"},
        ],
    }
    changelog = {
        "schema_version": "changelog/v1",
        "repo": ".",
        "since_tag": "v2.9.0",
        "to_ref": "HEAD",
        "range": "v2.9.0..HEAD",
        "commit_count": 1,
        "breaking_change_count": 0,
        "categories": [
            {"id": "feat", "title": "Features", "commits": [{"short_hash": "example", "description": "add release finalizer"}]},
            {"id": "fix", "title": "Fixes", "commits": []},
        ],
    }
    return finalize_release_json_from_reports(".", ".", release_audit, smoke_matrix, gallery, changelog)


def fixture_gallery_json_from_bundle() -> Dict[str, object]:
    from .demo_bundle import _example_commands
    from .demo import DEMO_DATA, DEMO_UPDATED_DATA
    from .models import parse_dataset

    base = parse_dataset(DEMO_DATA)
    updated = parse_dataset(DEMO_UPDATED_DATA)
    commands = _example_commands(base, updated, include_finalize=False)
    files = {f"examples/{path}": output() for path, _, output, _ in commands}
    return fixture_gallery_json(
        files,
        [(path, command, files[f"examples/{path}"], exit_code) for path, command, _, exit_code in commands],
    )


def _release_audit_summary(report: Dict[str, object]) -> Dict[str, object]:
    failed = _failed_release_checks(report)
    return {
        "ok": report["ok"],
        "detail": f"{report['summary']['passed_count']} passed / {report['summary']['check_count']} checks",
        "failed_checks": failed,
    }


def _smoke_matrix_summary(report: Dict[str, object]) -> Dict[str, object]:
    failed = _failed_smoke_commands(report)
    return {
        "ok": report["ok"],
        "detail": f"{report['summary']['passed_count']} passed / {report['summary']['command_count']} commands",
        "failed_commands": failed,
    }


def _fixture_gallery_summary(report: Dict[str, object]) -> Dict[str, object]:
    counts = report["summary"]["output_type_counts"]  # type: ignore[index]
    return {
        "ok": int(report["summary"]["fixture_count"]) > 0,  # type: ignore[index]
        "detail": f"{report['summary']['fixture_count']} fixtures indexed",
        "output_type_counts": {key: counts[key] for key in sorted(counts)},
    }


def _changelog_summary(report: Dict[str, object]) -> Dict[str, object]:
    return {
        "ok": int(report["commit_count"]) > 0,
        "detail": f"{report['commit_count']} commits since {report['since_tag']}",
        "breaking_change_count": report["breaking_change_count"],
        "commit_count": report["commit_count"],
        "tags_in_range": report.get("tags_in_range", []),
    }


def _release_notes_summary(report: Dict[str, object]) -> Dict[str, object]:
    categories = []
    for category in report["categories"]:
        commits = category["commits"]
        if commits:
            categories.append(
                {
                    "id": category["id"],
                    "title": category["title"],
                    "commit_count": len(commits),
                    "commits": [
                        {
                            "description": commit["description"],
                            "references": commit.get("references", []),
                            "scope": commit.get("scope"),
                            "short_hash": commit["short_hash"],
                        }
                        for commit in commits
                    ],
                }
            )
    return {
        "breaking_change_count": report["breaking_change_count"],
        "categories": categories,
        "commit_count": report["commit_count"],
    }


def _check_item(identifier: str, ok: bool, detail: str, blockers: Iterable[str]) -> Dict[str, object]:
    return {"id": identifier, "ok": ok, "status": "pass" if ok else "fail", "detail": detail, "blockers": sorted(blockers)}


def _failed_release_checks(report: Dict[str, object]) -> List[str]:
    return [str(check["id"]) for check in report["checks"] if check["status"] != "pass"]


def _failed_smoke_commands(report: Dict[str, object]) -> List[str]:
    return [str(item["command"]) for item in report["commands"] if item["status"] != "pass"]


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd().resolve()).as_posix() or "."
    except ValueError:
        return str(path)


def _escape_table(text: str) -> str:
    return text.replace("|", "\\|")
