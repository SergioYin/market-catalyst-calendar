"""Canonical fixture comparisons for generated examples."""

from __future__ import annotations

import json
import re
from typing import Any, Dict


VOLATILE_FIXTURES = {
    "quickstart_receipt.json",
    "quickstart_receipt.md",
    "version_report.json",
    "version_report.md",
}
VOLATILE_GALLERY_PATHS = {f"examples/{path}" for path in VOLATILE_FIXTURES}


def canonical_fixture_text(relative_path: str, text: str) -> str:
    """Return text normalized for fields that cannot be stable across commits."""

    if relative_path == "version_report.json":
        return _canonical_json(text, _normalize_version_report)
    if relative_path == "quickstart_receipt.json":
        return _canonical_json(text, _normalize_quickstart_receipt)
    if relative_path == "fixture_gallery.json":
        return _canonical_json(text, _normalize_fixture_gallery)
    if relative_path == "version_report.md":
        return _normalize_version_report_markdown(text)
    if relative_path == "quickstart_receipt.md":
        return _normalize_quickstart_receipt_markdown(text)
    if relative_path == "fixture_gallery.md":
        return _normalize_fixture_gallery_markdown(text)
    return text


def fixtures_match(relative_path: str, actual: str, expected: str) -> bool:
    try:
        return canonical_fixture_text(relative_path, actual) == canonical_fixture_text(relative_path, expected)
    except (TypeError, ValueError, json.JSONDecodeError):
        return False


def _canonical_json(text: str, normalizer: Any) -> str:
    payload = json.loads(text)
    normalizer(payload)
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _normalize_version_report(payload: Dict[str, Any]) -> None:
    _normalize_release_context(payload.get("git"))


def _normalize_quickstart_receipt(payload: Dict[str, Any]) -> None:
    _normalize_release_context(payload.get("release_context"))
    fixtures = payload.get("fixtures")
    if isinstance(fixtures, list):
        for fixture in fixtures:
            if not isinstance(fixture, dict) or fixture.get("path") not in VOLATILE_GALLERY_PATHS:
                continue
            if "bytes" in fixture:
                fixture["bytes"] = 0
            if "sha256" in fixture:
                fixture["sha256"] = "<volatile-fixture-sha256>"


def _normalize_release_context(value: Any) -> None:
    if not isinstance(value, dict):
        return
    if "latest_tag" in value:
        value["latest_tag"] = "<git-tag>"
    commit = value.get("commit")
    if isinstance(commit, dict):
        for key in ("hash", "short_hash", "date", "subject"):
            if key in commit:
                commit[key] = f"<git-commit-{key}>"


def _normalize_fixture_gallery(payload: Dict[str, Any]) -> None:
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        return
    for fixture in fixtures:
        if not isinstance(fixture, dict) or fixture.get("path") not in VOLATILE_GALLERY_PATHS:
            continue
        if "bytes" in fixture:
            fixture["bytes"] = 0
        if "sha256" in fixture:
            fixture["sha256"] = "<volatile-fixture-sha256>"


def _normalize_version_report_markdown(text: str) -> str:
    replacements = {
        r"^- Latest tag: `.*`$": "- Latest tag: `<git-tag>`",
        r"^- Commit: `.*`$": "- Commit: `<git-commit-short_hash>`",
        r"^- Commit date: `.*`$": "- Commit date: `<git-commit-date>`",
        r"^- Subject: .*$": "- Subject: <git-commit-subject>",
    }
    return _replace_lines(text, replacements)


def _normalize_quickstart_receipt_markdown(text: str) -> str:
    replacements = {
        r"^- Latest tag: `.*`$": "- Latest tag: `<git-tag>`",
        r"^- Commit: `.*`$": "- Commit: `<git-commit-short_hash>`",
        r"^- Commit date: `.*`$": "- Commit date: `<git-commit-date>`",
        r"^- Subject: .*$": "- Subject: <git-commit-subject>",
    }
    return _replace_lines(text, replacements)


def _normalize_fixture_gallery_markdown(text: str) -> str:
    lines = []
    current_fixture = ""
    for line in text.splitlines():
        heading = re.fullmatch(r"### `(examples/[^`]+)`", line)
        if heading:
            current_fixture = heading.group(1)
            lines.append(line)
            continue
        row = re.fullmatch(r"(\| `)(examples/[^`]+)(` \| [^|]+ \| )\d+( \| `)[0-9a-f]{16}(` \| .*)", line)
        if row and row.group(2) in VOLATILE_GALLERY_PATHS:
            lines.append(f"{row.group(1)}{row.group(2)}{row.group(3)}0{row.group(4)}<volatile-sha>{row.group(5)}")
            continue
        if current_fixture in VOLATILE_GALLERY_PATHS:
            if line.startswith("- Bytes: "):
                lines.append("- Bytes: 0")
                continue
            if re.fullmatch(r"- SHA-256: `[0-9a-f]{64}`", line):
                lines.append("- SHA-256: `<volatile-fixture-sha256>`")
                continue
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _replace_lines(text: str, replacements: Dict[str, str]) -> str:
    lines = []
    for line in text.splitlines():
        for pattern, replacement in replacements.items():
            if re.match(pattern, line):
                line = replacement
                break
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
