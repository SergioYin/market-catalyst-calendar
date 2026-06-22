"""Static visual evidence receipt generation."""

from __future__ import annotations

import hashlib
import shlex
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional


BOUNDARIES = [
    "Static-only: receipt evidence is limited to checked-in dashboard, report, and demo artifacts.",
    "Local fixtures only: regeneration commands use bundled example records.",
    "No live data: receipt generation does not fetch market, news, or broker data.",
    "No broker integration: artifacts do not connect to brokers.",
    "No orders: artifacts do not route orders, place orders, recommend trades, or simulate order execution.",
    "No personalized investment advice: artifacts are deterministic public research demos, not recommendations for any person or account.",
    "No private data: receipt targets use bundled demo fixtures and exclude account identifiers, credentials, and personal data.",
]

ARTIFACT_SPECS = [
    {
        "path": "examples/dashboard.html",
        "role": "static-html-dashboard",
        "route": "/examples/dashboard.html",
        "regeneration_args": [
            "html-dashboard",
            "--input",
            "examples/demo_records.json",
            "--as-of",
            "2026-05-13",
            "--days",
            "45",
        ],
        "capture_command": "open examples/dashboard.html",
    },
    {
        "path": "examples/impact_dashboard.md",
        "role": "markdown-impact-dashboard",
        "route": "/examples/impact_dashboard.md",
        "regeneration_args": [
            "impact-dashboard",
            "--input",
            "examples/demo_records.json",
            "--as-of",
            "2026-05-13",
            "--days",
            "45",
        ],
        "capture_command": "open examples/impact_dashboard.md",
    },
    {
        "path": "examples/impact_dashboard.json",
        "role": "machine-readable-impact-dashboard",
        "route": "/examples/impact_dashboard.json",
        "regeneration_args": [
            "impact-dashboard",
            "--input",
            "examples/demo_records.json",
            "--as-of",
            "2026-05-13",
            "--days",
            "45",
            "--format",
            "json",
        ],
        "capture_command": "python -m json.tool examples/impact_dashboard.json",
    },
    {
        "path": "examples/impact_brief.md",
        "role": "markdown-impact-report",
        "route": "/examples/impact_brief.md",
        "regeneration_args": [
            "impact-brief",
            "--input",
            "examples/demo_records.json",
            "--as-of",
            "2026-05-13",
            "--days",
            "45",
        ],
        "capture_command": "open examples/impact_brief.md",
    },
    {
        "path": "examples/agent_handoff.md",
        "role": "markdown-demo-handoff",
        "route": "/examples/agent_handoff.md",
        "regeneration_args": [
            "agent-handoff",
            "--input",
            "examples/demo_records.json",
            "--as-of",
            "2026-05-13",
            "--days",
            "45",
            "--format",
            "markdown",
        ],
        "capture_command": "open examples/agent_handoff.md",
    },
]


def visual_evidence_receipt_json(root: Path, files: Optional[Mapping[str, str]] = None) -> Dict[str, object]:
    """Return deterministic receipt evidence for curated static visual/demo artifacts."""

    artifacts = []
    for spec in ARTIFACT_SPECS:
        path = str(spec["path"])
        content = _read_bytes(root, path, files)
        artifacts.append(
            {
                "path": path,
                "present": content is not None,
                "bytes": len(content) if content is not None else 0,
                "sha256": hashlib.sha256(content).hexdigest() if content is not None else None,
                "role": spec["role"],
                "route": spec["route"],
                "regeneration_command": _regeneration_command(spec["regeneration_args"], path),  # type: ignore[arg-type]
                "capture_command": spec["capture_command"],
            }
        )
    missing = [str(item["path"]) for item in artifacts if not item["present"]]
    return {
        "schema_version": "visual-evidence-receipt/v1",
        "ok": not missing,
        "boundaries": BOUNDARIES,
        "summary": {
            "artifact_count": len(artifacts),
            "missing_count": len(missing),
            "total_bytes": sum(int(item["bytes"]) for item in artifacts),
        },
        "artifacts": artifacts,
        "missing": missing,
    }


def visual_evidence_receipt_markdown(payload: Dict[str, object]) -> str:
    lines = [
        "# Market Catalyst Visual Evidence Receipt",
        "",
        f"Status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"Artifacts: {payload['summary']['artifact_count']}",
        "",
        "## Boundaries",
        "",
    ]
    for boundary in payload["boundaries"]:
        lines.append(f"- {boundary}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "| Path | Role | Route | Bytes | SHA-256 | Regenerate | Capture |",
            "| --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for artifact in payload["artifacts"]:
        lines.append(
            f"| `{artifact['path']}` | `{artifact['role']}` | `{artifact['route']}` | "
            f"{artifact['bytes']} | `{artifact['sha256'] or ''}` | "
            f"`{artifact['regeneration_command']}` | `{artifact['capture_command']}` |"
        )
    if payload["missing"]:
        lines.extend(["", "## Missing", ""])
        for path in payload["missing"]:
            lines.append(f"- `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def _regeneration_command(args: Iterable[str], output_path: str) -> str:
    command = " ".join(shlex.quote(part) for part in ["python", "-m", "market_catalyst_calendar", *args])
    return f"{command} > {shlex.quote(output_path)}"


def _read_bytes(root: Path, relative_path: str, files: Optional[Mapping[str, str]]) -> Optional[bytes]:
    if files is not None:
        text = files.get(relative_path) or files.get(f"examples/{Path(relative_path).name}")
        return text.encode("utf-8") if text is not None else None
    path = root / relative_path
    if not path.is_file():
        return None
    return path.read_bytes()
