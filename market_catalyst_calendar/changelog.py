"""Deterministic release notes from local git history."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


CATEGORY_ORDER = [
    ("feat", "Features"),
    ("fix", "Fixes"),
    ("perf", "Performance"),
    ("refactor", "Refactors"),
    ("docs", "Documentation"),
    ("test", "Tests"),
    ("build", "Build"),
    ("ci", "CI"),
    ("chore", "Chores"),
    ("revert", "Reverts"),
    ("other", "Other Changes"),
]
CATEGORY_IDS = {item[0] for item in CATEGORY_ORDER}

CONVENTIONAL_RE = re.compile(r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<description>.+)$")
ISSUE_RE = re.compile(r"(?<![\w/])#(?P<number>[0-9]+)\b")


def changelog_json(repo: Path, since_tag: str, to_ref: str = "HEAD", include_merges: bool = False) -> Dict[str, object]:
    """Return deterministic release notes for commits after ``since_tag`` through ``to_ref``."""

    repo = repo.resolve()
    _git(repo, "rev-parse", "--is-inside-work-tree")
    from_sha = _git(repo, "rev-parse", f"{since_tag}^{{commit}}")
    to_sha = _git(repo, "rev-parse", f"{to_ref}^{{commit}}")
    range_spec = f"{since_tag}..{to_ref}"
    log_args = ["log", "--reverse", "--date=short", "--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%s%x1f%b%x1e"]
    if not include_merges:
        log_args.append("--no-merges")
    raw_log = _git_raw(repo, *log_args, range_spec)
    commits = [_parse_commit(chunk) for chunk in raw_log.split("\x1e") if chunk.strip()]
    categories = []
    for category_id, title in CATEGORY_ORDER:
        items = [commit for commit in commits if commit["category"] == category_id]
        categories.append({"id": category_id, "title": title, "commits": items})
    breaking_changes = [commit for commit in commits if commit["breaking"]]
    tags_on_target = _git_lines(repo, "tag", "--points-at", to_sha)
    tags_in_range = _git_lines(repo, "tag", "--merged", to_sha, "--no-merged", since_tag)
    return {
        "schema_version": "changelog/v1",
        "repo": str(repo),
        "since_tag": since_tag,
        "to_ref": to_ref,
        "from_sha": from_sha,
        "to_sha": to_sha,
        "range": range_spec,
        "include_merges": include_merges,
        "commit_count": len(commits),
        "tag_count": len(tags_in_range),
        "tags_in_range": tags_in_range,
        "tags_on_target": tags_on_target,
        "breaking_change_count": len(breaking_changes),
        "breaking_changes": breaking_changes,
        "categories": categories,
        "commits": commits,
    }


def changelog_markdown(payload: Dict[str, object]) -> str:
    """Render a changelog payload as deterministic Markdown."""

    lines = [
        "# Release Notes",
        "",
        f"Range: `{payload['range']}`",
        f"From: `{_short(str(payload['from_sha']))}`",
        f"To: `{_short(str(payload['to_sha']))}`",
        f"Commits: {payload['commit_count']}",
    ]
    tags_on_target = payload["tags_on_target"]
    if tags_on_target:
        lines.append("Tags on target: " + ", ".join(f"`{tag}`" for tag in tags_on_target))
    lines.append("")
    if payload["breaking_changes"]:
        lines.extend(["## Breaking Changes", ""])
        for commit in payload["breaking_changes"]:
            lines.append(_commit_bullet(commit))
        lines.append("")
    for category in payload["categories"]:
        commits = category["commits"]
        if not commits:
            continue
        lines.extend([f"## {category['title']}", ""])
        for commit in commits:
            lines.append(_commit_bullet(commit))
        lines.append("")
    if not payload["commits"]:
        lines.extend(["## Changes", "", "No commits found in range.", ""])
    return "\n".join(lines).rstrip() + "\n"


def _parse_commit(chunk: str) -> Dict[str, object]:
    fields = chunk.strip("\n").split("\x1f", 5)
    if len(fields) < 6:
        raise ValueError("git log output was incomplete")
    full_hash, short_hash, commit_date, author, subject, body = fields
    conventional = CONVENTIONAL_RE.match(subject)
    commit_type: Optional[str] = None
    scope: Optional[str] = None
    description = subject.strip()
    subject_breaking = False
    if conventional:
        commit_type = conventional.group("type").lower()
        scope = conventional.group("scope")
        subject_breaking = bool(conventional.group("breaking"))
        description = conventional.group("description").strip()
    body_breaking = "BREAKING CHANGE:" in body or "BREAKING-CHANGE:" in body
    category = commit_type if commit_type in CATEGORY_IDS else "other"
    return {
        "hash": full_hash,
        "short_hash": short_hash,
        "date": commit_date,
        "author": author,
        "subject": subject.strip(),
        "type": commit_type,
        "scope": scope,
        "description": description,
        "category": category,
        "breaking": subject_breaking or body_breaking,
        "references": sorted({f"#{match.group('number')}" for match in ISSUE_RE.finditer(subject + "\n" + body)}),
    }


def _commit_bullet(commit: Dict[str, object]) -> str:
    scope = f" ({commit['scope']})" if commit["scope"] else ""
    refs = f" {' '.join(commit['references'])}" if commit["references"] else ""
    breaking = " BREAKING" if commit["breaking"] else ""
    return f"- `{commit['short_hash']}` {commit['date']}: {commit['description']}{scope}{refs}{breaking}"


def _short(value: str) -> str:
    return value[:12]


def _git_lines(repo: Path, *args: str) -> List[str]:
    output = _git(repo, *args)
    return sorted(line for line in output.splitlines() if line)


def _git(repo: Path, *args: str) -> str:
    return _git_raw(repo, *args).strip()


def _git_raw(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ValueError(detail)
    return result.stdout
