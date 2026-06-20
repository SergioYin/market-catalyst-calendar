"""Public-safe impact capture checklist generation."""

from __future__ import annotations

import hashlib
import shlex
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional


BOUNDARY_STATEMENTS = [
    "No live data: capture uses checked-in local fixtures only and does not fetch market, news, or broker data.",
    "No broker integration: capture commands do not place, route, recommend, or simulate trades with a broker.",
    "No predictions: captured artifacts preserve deterministic scenario context only and do not forecast outcomes.",
    "No investment advice: captured artifacts are deterministic public research examples, not personalized recommendations.",
    "No private data: capture targets exclude account identifiers, holdings, credentials, and personal data.",
]

BOUNDARY_FLAGS = {
    "broker_connectivity": False,
    "investment_advice": False,
    "live_data": False,
    "prediction": False,
    "private_data": False,
    "trade_recommendation": False,
}

CAPTURE_SPECS = [
    {
        "artifact": "impact-brief",
        "command_args": ["impact-brief", "--input", "examples/demo_records.json", "--as-of", "2026-05-13", "--days", "45"],
        "source_fixture": "examples/demo_records.json",
        "output_artifact_path": "examples/impact_brief.md",
        "capture_target": "public-safe screenshot or GIF of the Markdown impact brief boundary, summary, ranked catalysts, and scenario context",
    },
    {
        "artifact": "impact-dashboard",
        "command_args": ["impact-dashboard", "--input", "examples/demo_records.json", "--as-of", "2026-05-13", "--days", "45"],
        "source_fixture": "examples/demo_records.json",
        "output_artifact_path": "examples/impact_dashboard.md",
        "capture_target": "public-safe screenshot or GIF of the Markdown impact dashboard summary, evidence states, top attention table, and review queue",
    },
    {
        "artifact": "impact-compare",
        "command_args": [
            "impact-compare",
            "--base",
            "examples/demo_records.json",
            "--current",
            "examples/demo_records_updated.json",
            "--as-of",
            "2026-05-27",
            "--format",
            "markdown",
        ],
        "source_fixture": "examples/demo_records.json; examples/demo_records_updated.json",
        "output_artifact_path": "examples/impact_compare.md",
        "capture_target": "public-safe screenshot or GIF of the Markdown impact comparison summary, added/removed/changed rows, and impact movements",
    },
    {
        "artifact": "impact-artifact-receipt",
        "command_args": ["impact-artifact-receipt", "--root", ".", "--format", "markdown"],
        "source_fixture": "examples/demo_records.json; examples/demo_records_updated.json; checked-in impact examples",
        "output_artifact_path": "examples/impact_artifact_receipt.md",
        "capture_target": "public-safe screenshot or GIF of the Markdown impact artifact receipt boundaries, rerun commands, paths, bytes, and hashes",
    },
]


def impact_capture_checklist_json(root: Path, files: Optional[Mapping[str, str]] = None) -> Dict[str, object]:
    """Return a deterministic screenshot/GIF capture checklist for public impact artifacts."""

    display_root = str(root)
    root = root.resolve()
    checklist = []
    for spec in CAPTURE_SPECS:
        artifact_path = str(spec["output_artifact_path"])
        text = _read_text(root, artifact_path, files)
        source_fixture = str(spec["source_fixture"])
        checklist.append(
            {
                "artifact": spec["artifact"],
                "status": "ready" if text is not None else "missing",
                "render_command": _render_command(spec["command_args"], artifact_path),  # type: ignore[arg-type]
                "source_fixture": source_fixture,
                "output_artifact_path": artifact_path,
                "existing": {
                    "present": text is not None,
                    "bytes": len(text.encode("utf-8")) if text is not None else 0,
                    "sha256": _sha256(text) if text is not None else None,
                },
                "capture_target": spec["capture_target"],
                "boundaries": list(BOUNDARY_STATEMENTS),
            }
        )
    missing = [str(item["output_artifact_path"]) for item in checklist if item["status"] != "ready"]
    return {
        "schema_version": "impact-capture-checklist/v1",
        "root": display_root,
        "ok": not missing,
        "boundary": dict(BOUNDARY_FLAGS),
        "boundaries": list(BOUNDARY_STATEMENTS),
        "summary": {
            "item_count": len(checklist),
            "missing_count": len(missing),
            "total_bytes": sum(int(item["existing"]["bytes"]) for item in checklist),  # type: ignore[index]
        },
        "checklist": checklist,
        "missing": missing,
    }


def impact_capture_checklist_markdown(payload: Dict[str, object]) -> str:
    lines = [
        "# Market Catalyst Impact Capture Checklist",
        "",
        f"Status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"Root: `{payload['root']}`",
        f"Items: {payload['summary']['item_count']}",
        "",
        "## Boundaries",
        "",
    ]
    for boundary in payload["boundaries"]:
        lines.append(f"- {boundary}")
    lines.extend(
        [
            "",
            "## Checklist",
            "",
            "| Done | Artifact | Source fixture | Output artifact | Bytes | SHA-256 | Capture target | Render command |",
            "| --- | --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for item in payload["checklist"]:
        existing = item["existing"]
        lines.append(
            f"| [ ] | `{item['artifact']}` | `{item['source_fixture']}` | `{item['output_artifact_path']}` | "
            f"{existing['bytes']} | `{existing['sha256'] or ''}` | {_cell(str(item['capture_target']))} | "
            f"`{item['render_command']}` |"
        )
    if payload["missing"]:
        lines.extend(["", "## Missing", ""])
        for path in payload["missing"]:
            lines.append(f"- `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def _render_command(args: Iterable[str], output_path: str) -> str:
    command = " ".join(shlex.quote(part) for part in ["python", "-m", "market_catalyst_calendar", *args])
    return f"{command} > {shlex.quote(output_path)}"


def _read_text(root: Path, relative_path: str, files: Optional[Mapping[str, str]]) -> Optional[str]:
    if files is not None:
        return files.get(relative_path) or files.get(f"examples/{Path(relative_path).name}")
    path = root / relative_path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
