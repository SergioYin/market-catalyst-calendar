"""Deterministic quickstart receipt for finance-product boundaries."""

from __future__ import annotations

import hashlib
import shlex
import subprocess
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from . import __version__
from .models import CatalystRecord, Dataset
from .render import brief_markdown, records_json, risk_budget_json, source_pack_json


DEFAULT_INPUT = "examples/demo_records.json"
DEFAULT_AS_OF = date(2026, 5, 13)
DEFAULT_DAYS = 45
BOUNDARIES = [
    "No live data: the receipt reads only the local input file and does not fetch market, news, or broker data.",
    "No broker integration: commands do not place, route, recommend, or simulate trades with a broker.",
    "No investment advice: outputs are deterministic research fixtures and operational checks, not personalized recommendations.",
]
SOURCE_PACK_FRESH_AFTER_DAYS = 14
IMPORTANT_FIXTURES = [
    "examples/demo_records.json",
    "examples/upcoming.json",
    "examples/brief.md",
    "examples/risk_budget.json",
    "examples/source_pack.json",
    "examples/version_report.json",
]


def quickstart_receipt_json(dataset: Dataset, input_path: str, as_of: date, days: int, root: Path, repo: Path) -> Dict[str, object]:
    """Return a deterministic quickstart receipt for local demo workflows."""

    upcoming = _upcoming_records(dataset.records, as_of, days)
    artifact_specs = [
        (
            "upcoming.json",
            ["upcoming", "--input", input_path, "--as-of", as_of.isoformat(), "--days", str(days), "--format", "json"],
            _json_text(records_json(upcoming, as_of)),
        ),
        (
            "brief.md",
            ["brief", "--input", input_path, "--as-of", as_of.isoformat(), "--days", str(days)],
            brief_markdown(upcoming, as_of),
        ),
        (
            "risk_budget.json",
            ["risk-budget", "--input", input_path, "--as-of", as_of.isoformat(), "--days", str(days), "--format", "json"],
            _json_text(risk_budget_json(upcoming, as_of)),
        ),
        (
            "source_pack.json",
            [
                "source-pack",
                "--input",
                input_path,
                "--as-of",
                as_of.isoformat(),
                "--fresh-after-days",
                str(SOURCE_PACK_FRESH_AFTER_DAYS),
                "--format",
                "json",
            ],
            _json_text(source_pack_json(dataset.records, as_of, SOURCE_PACK_FRESH_AFTER_DAYS)),
        ),
    ]
    return {
        "schema_version": "quickstart-receipt/v1",
        "package": {
            "name": "market-catalyst-calendar",
            "version": __version__,
        },
        "release_context": _release_context(repo),
        "inputs": {
            "dataset_path": input_path,
            "dataset_sha256": _file_sha256(Path(input_path)),
            "record_count": len(dataset.records),
        },
        "parameters": {
            "as_of": as_of.isoformat(),
            "days": days,
        },
        "boundaries": BOUNDARIES,
        "rerun_commands": _rerun_commands(input_path, as_of, days),
        "artifacts": [
            {
                "name": name,
                "command": _command(command_args),
                "sha256": _sha256(text),
                "bytes": len(text.encode("utf-8")),
            }
            for name, command_args, text in artifact_specs
        ],
        "fixtures": _fixture_hashes(root, IMPORTANT_FIXTURES),
    }


def quickstart_receipt_markdown(payload: Dict[str, object]) -> str:
    package = payload["package"]
    inputs = payload["inputs"]
    params = payload["parameters"]
    release = payload["release_context"]
    lines = [
        "# Market Catalyst Quickstart Receipt",
        "",
        f"Package: `{package['name']}`",
        f"Version: `{package['version']}`",
        f"Input: `{inputs['dataset_path']}`",
        f"Input SHA-256: `{inputs['dataset_sha256']}`",
        f"Records: {inputs['record_count']}",
        f"As of: `{params['as_of']}`",
        f"Days: {params['days']}",
        "",
        "## Boundaries",
        "",
    ]
    for boundary in payload["boundaries"]:
        lines.append(f"- {boundary}")
    lines.extend(["", "## Release Context", ""])
    if release["available"]:
        lines.extend(
            [
                f"- Commit: `{release['commit']['short_hash']}`",
                f"- Commit date: `{release['commit']['date']}`",
                f"- Latest tag: `{release['latest_tag'] or 'none'}`",
                f"- Subject: {release['commit']['subject']}",
            ]
        )
    else:
        lines.append(f"- Unavailable: {release['detail']}")
    lines.extend(["", "## Exact Rerun Commands", ""])
    for command in payload["rerun_commands"]:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Artifact Hashes", "", "| Artifact | Bytes | SHA-256 | Command |", "| --- | ---: | --- | --- |"])
    for artifact in payload["artifacts"]:
        lines.append(
            f"| `{artifact['name']}` | {artifact['bytes']} | `{artifact['sha256']}` | `{artifact['command']}` |"
        )
    lines.extend(["", "## Fixture Hashes", "", "| Fixture | Present | Bytes | SHA-256 |", "| --- | --- | ---: | --- |"])
    for fixture in payload["fixtures"]:
        lines.append(
            f"| `{fixture['path']}` | {str(fixture['present']).lower()} | {fixture['bytes']} | `{fixture['sha256'] or ''}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _rerun_commands(input_path: str, as_of: date, days: int) -> List[str]:
    common = ["--input", input_path, "--as-of", as_of.isoformat()]
    return [
        _command(["validate", "--input", input_path]),
        _command(["upcoming", *common, "--days", str(days), "--format", "json"]),
        _command(["brief", *common, "--days", str(days)]),
        _command(["risk-budget", *common, "--days", str(days), "--format", "json"]),
        _command(["source-pack", *common, "--fresh-after-days", str(SOURCE_PACK_FRESH_AFTER_DAYS), "--format", "json"]),
        _command(["quickstart-receipt", "--input", input_path, "--as-of", as_of.isoformat(), "--days", str(days), "--format", "json"]),
    ]


def _command(args: Iterable[str]) -> str:
    return " ".join(shlex.quote(part) for part in ["python", "-m", "market_catalyst_calendar", *args])


def _upcoming_records(records: Iterable[CatalystRecord], as_of: date, days: int) -> List[CatalystRecord]:
    return [
        record
        for record in records
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]


def _json_text(data: object) -> str:
    import json

    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _fixture_hashes(root: Path, paths: Iterable[str]) -> List[Dict[str, object]]:
    fixtures = []
    for relative in paths:
        path = root / relative
        digest = _file_sha256(path)
        fixtures.append(
            {
                "path": relative,
                "present": digest is not None,
                "bytes": path.stat().st_size if path.is_file() else 0,
                "sha256": digest,
            }
        )
    return fixtures


def _file_sha256(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    return _sha256(path.read_text(encoding="utf-8"))


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _release_context(repo: Path) -> Dict[str, object]:
    commit = _git(repo, ["log", "-1", "--format=%H%x00%h%x00%cI%x00%s"])
    if commit is None:
        return {"available": False, "detail": "git metadata unavailable", "latest_tag": None, "commit": None}
    parts = commit.split("\x00")
    if len(parts) != 4:
        return {"available": False, "detail": "git commit output was not parseable", "latest_tag": None, "commit": None}
    return {
        "available": True,
        "latest_tag": _git(repo, ["describe", "--tags", "--abbrev=0"]),
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
