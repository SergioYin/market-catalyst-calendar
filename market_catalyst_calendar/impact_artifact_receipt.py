"""Impact artifact receipt generation."""

from __future__ import annotations

import hashlib
import shlex
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional


BOUNDARIES = [
    "No live data: receipt evidence is limited to checked-in local fixtures and does not fetch market, news, or broker data.",
    "No broker integration: rerun commands do not place, route, recommend, or simulate trades with a broker.",
    "No prediction: artifacts summarize supplied catalyst records and do not forecast prices, returns, or outcomes.",
    "No investment advice: artifacts are deterministic public research examples, not personalized recommendations.",
]

ARTIFACT_SPECS = [
    {
        "name": "impact_brief.json",
        "command_args": ["impact-brief", "--input", "examples/demo_records.json", "--as-of", "2026-05-13", "--days", "45", "--format", "json"],
        "inputs": ["examples/demo_records.json"],
        "output_path": "examples/impact_brief.json",
        "schema_label": "impact-brief/v1",
        "format": "json",
    },
    {
        "name": "impact_brief.md",
        "command_args": ["impact-brief", "--input", "examples/demo_records.json", "--as-of", "2026-05-13", "--days", "45"],
        "inputs": ["examples/demo_records.json"],
        "output_path": "examples/impact_brief.md",
        "schema_label": "impact-brief/markdown",
        "format": "markdown",
    },
    {
        "name": "impact_dashboard.json",
        "command_args": ["impact-dashboard", "--input", "examples/demo_records.json", "--as-of", "2026-05-13", "--days", "45", "--format", "json"],
        "inputs": ["examples/demo_records.json"],
        "output_path": "examples/impact_dashboard.json",
        "schema_label": "impact-dashboard/v1",
        "format": "json",
    },
    {
        "name": "impact_dashboard.md",
        "command_args": ["impact-dashboard", "--input", "examples/demo_records.json", "--as-of", "2026-05-13", "--days", "45"],
        "inputs": ["examples/demo_records.json"],
        "output_path": "examples/impact_dashboard.md",
        "schema_label": "impact-dashboard/markdown",
        "format": "markdown",
    },
    {
        "name": "impact_compare.json",
        "command_args": [
            "impact-compare",
            "--base",
            "examples/demo_records.json",
            "--current",
            "examples/demo_records_updated.json",
            "--as-of",
            "2026-05-27",
        ],
        "inputs": ["examples/demo_records.json", "examples/demo_records_updated.json"],
        "output_path": "examples/impact_compare.json",
        "schema_label": "impact-compare/v1",
        "format": "json",
    },
    {
        "name": "impact_compare.md",
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
        "inputs": ["examples/demo_records.json", "examples/demo_records_updated.json"],
        "output_path": "examples/impact_compare.md",
        "schema_label": "impact-compare/markdown",
        "format": "markdown",
    },
]


def impact_artifact_receipt_json(root: Path, files: Optional[Mapping[str, str]] = None) -> Dict[str, object]:
    """Return receipt evidence for checked-in impact example artifacts."""

    display_root = str(root)
    root = root.resolve()
    artifacts = []
    for spec in ARTIFACT_SPECS:
        output_path = str(spec["output_path"])
        text = _read_text(root, output_path, files)
        artifacts.append(
            {
                "name": spec["name"],
                "format": spec["format"],
                "schema_label": spec["schema_label"],
                "inputs": [
                    {
                        "path": input_path,
                        "present": _exists(root, input_path, files),
                        "bytes": _byte_count(root, input_path, files),
                        "sha256": _sha256_or_none(root, input_path, files),
                    }
                    for input_path in spec["inputs"]  # type: ignore[index]
                ],
                "output_path": output_path,
                "present": text is not None,
                "bytes": len(text.encode("utf-8")) if text is not None else 0,
                "sha256": _sha256(text) if text is not None else None,
                "rerun_command": _rerun_command(spec["command_args"], output_path),  # type: ignore[arg-type]
            }
        )
    missing = [str(item["output_path"]) for item in artifacts if not item["present"]]
    missing.extend(
        str(input_item["path"])
        for item in artifacts
        for input_item in item["inputs"]  # type: ignore[union-attr]
        if not input_item["present"]
    )
    return {
        "schema_version": "impact-artifact-receipt/v1",
        "root": display_root,
        "ok": not missing,
        "boundaries": BOUNDARIES,
        "summary": {
            "artifact_count": len(artifacts),
            "missing_count": len(missing),
            "total_bytes": sum(int(item["bytes"]) for item in artifacts),
        },
        "artifacts": artifacts,
        "missing": sorted(set(missing)),
    }


def impact_artifact_receipt_markdown(payload: Dict[str, object]) -> str:
    lines = [
        "# Market Catalyst Impact Artifact Receipt",
        "",
        f"Status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"Root: `{payload['root']}`",
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
            "| Artifact | Schema | Inputs | Output | Bytes | SHA-256 | Rerun |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for artifact in payload["artifacts"]:
        inputs = ", ".join(f"`{item['path']}`" for item in artifact["inputs"])
        lines.append(
            f"| `{artifact['name']}` | `{artifact['schema_label']}` | {inputs} | "
            f"`{artifact['output_path']}` | {artifact['bytes']} | `{artifact['sha256'] or ''}` | "
            f"`{artifact['rerun_command']}` |"
        )
    if payload["missing"]:
        lines.extend(["", "## Missing", ""])
        for path in payload["missing"]:
            lines.append(f"- `{path}`")
    return "\n".join(lines).rstrip() + "\n"


def _rerun_command(args: Iterable[str], output_path: str) -> str:
    command = " ".join(shlex.quote(part) for part in ["python", "-m", "market_catalyst_calendar", *args])
    return f"{command} > {shlex.quote(output_path)}"


def _read_text(root: Path, relative_path: str, files: Optional[Mapping[str, str]]) -> Optional[str]:
    if files is not None:
        return files.get(relative_path) or files.get(f"examples/{Path(relative_path).name}")
    path = root / relative_path
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _exists(root: Path, relative_path: str, files: Optional[Mapping[str, str]]) -> bool:
    return _read_text(root, relative_path, files) is not None


def _byte_count(root: Path, relative_path: str, files: Optional[Mapping[str, str]]) -> int:
    text = _read_text(root, relative_path, files)
    return len(text.encode("utf-8")) if text is not None else 0


def _sha256_or_none(root: Path, relative_path: str, files: Optional[Mapping[str, str]]) -> Optional[str]:
    text = _read_text(root, relative_path, files)
    return _sha256(text) if text is not None else None


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
