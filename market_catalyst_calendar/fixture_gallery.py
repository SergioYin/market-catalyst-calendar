"""Fixture gallery rendering."""

from __future__ import annotations

import hashlib
import shlex
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


FixtureCommand = Tuple[str, str, str, int]

OUTPUT_TYPES = {
    ".csv": "csv",
    ".html": "html",
    ".ics": "ics",
    ".json": "json",
    ".md": "markdown",
}

COMMAND_USE_CASES = {
    "agent-handoff": [
        "Hand compact context to a downstream research agent.",
        "Audit the exact commands and source URLs an agent should preserve.",
    ],
    "brief": [
        "Review a concise analyst packet for upcoming catalysts.",
        "Use as a Markdown snapshot in research notes or tickets.",
    ],
    "broker-matrix": [
        "Inspect broker view dispersion and stale broker-source flags.",
        "Compare sell-side assumptions against catalyst timing.",
    ],
    "command-cookbook": [
        "Show a field-aware report sequence for a dataset.",
        "Use as an analyst runbook for reproducing fixture outputs.",
    ],
    "compare": [
        "Review deterministic differences between base and updated snapshots.",
        "Test changed-status, changed-evidence, and score-delta consumers.",
    ],
    "decision-log": [
        "Create pre-event decision memo stubs without inventing conclusions.",
        "Seed human or agent decision journals.",
    ],
    "drilldown": [
        "Inspect a complete single-ticker dossier.",
        "Test composed reports that combine thesis, broker, risk, sources, and watch items.",
    ],
    "evidence-audit": [
        "Find stale, thin, or concentrated evidence metadata.",
        "Use before public handoff or source refresh work.",
    ],
    "finalize-release": [
        "Review one deterministic release checklist before handoff.",
        "Combine audit, smoke, fixture, and changelog status for release notes.",
    ],
    "export-csv": [
        "Validate spreadsheet-friendly export shape and encoded multi-value cells.",
        "Test CSV consumers against stable column order.",
    ],
    "export-demo": [
        "Start from a deterministic catalyst dataset.",
        "Smoke-test validation, scoring, and report commands.",
    ],
    "export-ics": [
        "Load upcoming catalysts into calendar tooling.",
        "Test deterministic iCalendar UID, date, and escaping behavior.",
    ],
    "exposure": [
        "Aggregate portfolio exposure for upcoming catalysts.",
        "Test weighted exposure calculations and grouped report rendering.",
    ],
    "html-dashboard": [
        "Review the static offline dashboard in a browser.",
        "Test escaped no-JavaScript HTML report generation.",
    ],
    "import-csv": [
        "Validate CSV round trips back into catalyst JSON.",
        "Test parser behavior for encoded multi-value cells.",
    ],
    "merge": [
        "Inspect deterministic multi-snapshot merge provenance and conflicts.",
        "Test downstream handling of validation diagnostics in merged datasets.",
    ],
    "post-event": [
        "Queue missing outcome capture after catalyst windows pass.",
        "Use as a post-event review template.",
    ],
    "quality-gate": [
        "Exercise public research quality diagnostics and nonzero exits.",
        "Use before publishing or handing off research fixtures.",
    ],
    "review-plan": [
        "List stale and high-urgency records needing analyst action.",
        "Use as a deterministic review checklist.",
    ],
    "risk-budget": [
        "Compare event max-loss estimates against risk budgets.",
        "Find over-budget catalysts before high-urgency events.",
    ],
    "scenario-matrix": [
        "Review bull/base/bear event scenarios for upcoming catalysts.",
        "Test scenario scores, dates, impacts, and Markdown tables.",
    ],
    "sector-map": [
        "Group catalyst exposure by sector and theme.",
        "Find concentration, stale evidence, and broker-dispersion clusters.",
    ],
    "source-pack": [
        "Export deduplicated evidence and broker source inventories.",
        "Use for source collection, audit, or downstream handoff.",
    ],
    "stale": [
        "List records whose review state is stale.",
        "Use to seed evidence refresh or analyst review queues.",
    ],
    "thesis-map": [
        "Group catalysts by investment thesis and source references.",
        "Find stale or sparse support for a thesis.",
    ],
    "upcoming": [
        "List open catalysts in a forward window.",
        "Test date-window filtering and deterministic score ordering.",
    ],
    "watchlist": [
        "Convert open catalysts into prioritized watch items.",
        "Use for trigger, due-date, and cadence workflows.",
    ],
}


def fixture_gallery_json(files: Dict[str, str], commands: Iterable[FixtureCommand]) -> Dict[str, object]:
    fixtures = []
    output_type_counts: Dict[str, int] = {}
    for path, command, text, exit_code in commands:
        relative_path = f"examples/{path}"
        output_type = _output_type(relative_path)
        output_type_counts[output_type] = output_type_counts.get(output_type, 0) + 1
        content = files[relative_path]
        fixtures.append(
            {
                "path": relative_path,
                "command": f"python -m market_catalyst_calendar {command}",
                "command_args": shlex.split(command),
                "exit_code": exit_code,
                "output_type": output_type,
                "bytes": len(content.encode("utf-8")),
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "input_fixtures": _input_fixtures(command, relative_path),
                "recommended_use_cases": _recommended_use_cases(command, relative_path),
            }
        )
    return {
        "schema_version": "fixture-gallery/v1",
        "summary": {
            "fixture_count": len(fixtures),
            "output_type_counts": {key: output_type_counts[key] for key in sorted(output_type_counts)},
        },
        "fixtures": fixtures,
    }


def fixture_gallery_markdown(payload: Dict[str, object]) -> str:
    lines = [
        "# Market Catalyst Fixture Gallery",
        "",
        "Bundled fixtures are deterministic outputs generated from the built-in demo datasets.",
        "Hashes are SHA-256 digests of the exact fixture bytes.",
        "",
        "## Summary",
        "",
        f"- Fixtures: {payload['summary']['fixture_count']}",
    ]
    counts = payload["summary"]["output_type_counts"]
    for output_type in sorted(counts):
        lines.append(f"- {output_type}: {counts[output_type]}")
    lines.extend(
        [
            "",
            "## Fixtures",
            "",
            "| Fixture | Type | Exit | SHA-256 | Recommended use |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for fixture in payload["fixtures"]:
        use_case = str(fixture["recommended_use_cases"][0])
        lines.append(
            "| "
            f"`{fixture['path']}` | "
            f"{fixture['output_type']} | "
            f"{fixture['exit_code']} | "
            f"`{str(fixture['sha256'])[:16]}` | "
            f"{_escape_table(use_case)} |"
        )
    lines.extend(["", "## Command Provenance", ""])
    for fixture in payload["fixtures"]:
        lines.append(f"### `{fixture['path']}`")
        lines.append("")
        lines.append(f"- Command: `{fixture['command']}`")
        lines.append(f"- Output type: `{fixture['output_type']}`")
        lines.append(f"- Bytes: {fixture['bytes']}")
        lines.append(f"- SHA-256: `{fixture['sha256']}`")
        if fixture["input_fixtures"]:
            inputs = ", ".join(f"`{path}`" for path in fixture["input_fixtures"])
            lines.append(f"- Input fixtures: {inputs}")
        lines.append("- Recommended use cases:")
        for use_case in fixture["recommended_use_cases"]:
            lines.append(f"  - {use_case}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _output_type(path: str) -> str:
    return OUTPUT_TYPES.get(Path(path).suffix, "text")


def _input_fixtures(command: str, output_path: str) -> List[str]:
    inputs = []
    for token in shlex.split(command):
        if token.startswith("examples/") and token != output_path and token not in inputs:
            inputs.append(token)
    return inputs


def _recommended_use_cases(command: str, path: str) -> List[str]:
    args = shlex.split(command)
    command_name = args[0] if args else Path(path).stem
    use_cases = COMMAND_USE_CASES.get(command_name)
    if use_cases is not None:
        return use_cases
    return [
        "Inspect deterministic fixture output.",
        "Use as a stable regression fixture for downstream tooling.",
    ]


def _escape_table(text: str) -> str:
    return text.replace("|", "\\|")
