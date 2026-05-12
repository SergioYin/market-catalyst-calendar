"""Deterministic demo bundle generation."""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

from .agent_handoff import agent_handoff_json, agent_handoff_markdown
from .command_cookbook import command_cookbook_markdown
from .compare import compare_snapshots_json, compare_snapshots_markdown
from .csv_io import csv_to_dataset_json, dataset_to_csv
from .dashboard import html_dashboard
from .demo import DEMO_DATA, DEMO_UPDATED_DATA
from .doctor import doctor_json, doctor_markdown
from .evidence import evidence_audit_json, evidence_audit_markdown
from .finalize_release import example_finalize_release_json, finalize_release_markdown
from .fixture_gallery import fixture_gallery_json, fixture_gallery_markdown
from .ics import records_to_ics
from .io import dump_json
from .merge import merge_datasets_json
from .models import CatalystRecord, Dataset, parse_dataset, sorted_records
from .presets import run_preset_config
from .quality_gate import quality_gate_json, quality_gate_markdown
from .render import (
    brief_markdown,
    broker_matrix_json,
    broker_matrix_markdown,
    decision_log_json,
    decision_log_markdown,
    drilldown_json,
    drilldown_markdown,
    exposure_json,
    exposure_markdown,
    post_event_json,
    post_event_markdown,
    records_json,
    review_plan_json,
    review_plan_markdown,
    risk_budget_json,
    risk_budget_markdown,
    scenario_matrix_json,
    scenario_matrix_markdown,
    sector_map_json,
    sector_map_markdown,
    source_pack_csv,
    source_pack_json,
    source_pack_markdown,
    thesis_map_json,
    thesis_map_markdown,
    watchlist_json,
    watchlist_markdown,
)
from .scoring import score_record
from .taxonomy import taxonomy_json, taxonomy_markdown
from .tutorial import tutorial_markdown
from .version_report import version_report_json, version_report_markdown


BUNDLE_VERSION = 1
DEFAULT_AS_OF = date(2026, 5, 13)
UPDATED_AS_OF = date(2026, 5, 27)
POST_EVENT_AS_OF = date(2026, 6, 25)
DEFAULT_DAYS = 45
DEFAULT_STALE_AFTER_DAYS = 14
EXAMPLE_PRESETS = {
    "defaults": {
        "days": DEFAULT_DAYS,
        "output_dir": "/tmp/market-catalyst-calendar-preset-example",
        "profile": "public",
        "stale_after_days": DEFAULT_STALE_AFTER_DAYS,
    },
    "presets": {
        "desk-packet": {
            "as_of": DEFAULT_AS_OF.isoformat(),
            "input": "examples/demo_records.json",
            "workflows": [
                "validate",
                "quality-gate",
                "upcoming",
                "review-plan",
                "source-pack",
                "watchlist",
                "agent-handoff",
            ],
        }
    },
}

CommandSpec = Tuple[str, str, Callable[[], str], int]


def create_demo_bundle(output_dir: str) -> Dict[str, object]:
    """Write a deterministic bundle containing all example outputs and docs."""

    destination = Path(output_dir)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"demo bundle output directory must be empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    files = _bundle_files()
    for relative_path, text in sorted(files.items()):
        _write_text(destination / relative_path, text)

    manifest = _build_manifest(destination, sorted(files))
    _write_text(destination / "manifest.json", dump_json(manifest))
    return manifest


def _bundle_files() -> Dict[str, str]:
    base = parse_dataset(DEMO_DATA)
    updated = parse_dataset(DEMO_UPDATED_DATA)
    commands = _example_commands(base, updated)

    files = {f"examples/{path}": output() for path, _, output, _ in commands}
    gallery = fixture_gallery_json(
        files,
        [(path, command, files[f"examples/{path}"], exit_code) for path, command, _, exit_code in commands],
    )
    files["examples/fixture_gallery.json"] = dump_json(gallery)
    files["examples/fixture_gallery.md"] = fixture_gallery_markdown(gallery)
    files["README.md"] = _bundle_readme(commands)
    files["quickstart-transcript.txt"] = _quickstart_transcript(commands)
    return files


def bundled_fixture_gallery_json() -> Dict[str, object]:
    base = parse_dataset(DEMO_DATA)
    updated = parse_dataset(DEMO_UPDATED_DATA)
    commands = _example_commands(base, updated)
    files = {f"examples/{path}": output() for path, _, output, _ in commands}
    return fixture_gallery_json(
        files,
        [(path, command, files[f"examples/{path}"], exit_code) for path, command, _, exit_code in commands],
    )


def bundled_fixture_gallery_markdown() -> str:
    return fixture_gallery_markdown(bundled_fixture_gallery_json())


def _example_commands(base: Dataset, updated: Dataset, include_finalize: bool = True) -> List[CommandSpec]:
    as_of = DEFAULT_AS_OF
    updated_as_of = UPDATED_AS_OF
    post_event_as_of = POST_EVENT_AS_OF
    upcoming = _upcoming_records(base.records, as_of, DEFAULT_DAYS)
    stale = _stale_records(base.records, as_of, DEFAULT_STALE_AFTER_DAYS)
    csv_text = dataset_to_csv(base)

    commands = [
        ("demo_records.json", "export-demo", lambda: dump_json(DEMO_DATA), 0),
        ("presets.json", "export-preset-example", lambda: dump_json(EXAMPLE_PRESETS), 0),
        (
            "upcoming.json",
            "upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: dump_json(records_json(upcoming, as_of)),
            0,
        ),
        (
            "stale.json",
            "stale --input examples/demo_records.json --as-of 2026-05-13",
            lambda: dump_json(records_json(stale, as_of)),
            0,
        ),
        (
            "brief.md",
            "brief --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: brief_markdown(upcoming, as_of),
            0,
        ),
        (
            "exposure.json",
            "exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: dump_json(exposure_json(upcoming, as_of)),
            0,
        ),
        (
            "exposure.md",
            "exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown",
            lambda: exposure_markdown(upcoming, as_of),
            0,
        ),
        (
            "risk_budget.json",
            "risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: dump_json(risk_budget_json(upcoming, as_of)),
            0,
        ),
        (
            "risk_budget.md",
            "risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown",
            lambda: risk_budget_markdown(upcoming, as_of),
            0,
        ),
        (
            "sector_map.json",
            "sector-map --input examples/demo_records.json --as-of 2026-05-13",
            lambda: dump_json(sector_map_json(base.records, as_of, DEFAULT_STALE_AFTER_DAYS)),
            0,
        ),
        (
            "sector_map.md",
            "sector-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown",
            lambda: sector_map_markdown(base.records, as_of, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "review_plan.json",
            "review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: dump_json(review_plan_json(base.records, as_of, DEFAULT_DAYS, DEFAULT_STALE_AFTER_DAYS)),
            0,
        ),
        (
            "review_plan.md",
            "review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown",
            lambda: review_plan_markdown(base.records, as_of, DEFAULT_DAYS, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "thesis_map.json",
            "thesis-map --input examples/demo_records.json --as-of 2026-05-13",
            lambda: dump_json(thesis_map_json(base.records, as_of, DEFAULT_STALE_AFTER_DAYS)),
            0,
        ),
        (
            "thesis_map.md",
            "thesis-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown",
            lambda: thesis_map_markdown(base.records, as_of, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "scenario_matrix.json",
            "scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: dump_json(scenario_matrix_json(upcoming, as_of, DEFAULT_STALE_AFTER_DAYS)),
            0,
        ),
        (
            "scenario_matrix.md",
            "scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown",
            lambda: scenario_matrix_markdown(upcoming, as_of, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "evidence_audit.json",
            "evidence-audit --input examples/demo_records.json --as-of 2026-05-13",
            lambda: dump_json(evidence_audit_json(base.records, as_of, DEFAULT_STALE_AFTER_DAYS, 2, 0.67)),
            0,
        ),
        (
            "evidence_audit.md",
            "evidence-audit --input examples/demo_records.json --as-of 2026-05-13 --format markdown",
            lambda: evidence_audit_markdown(base.records, as_of, DEFAULT_STALE_AFTER_DAYS, 2, 0.67),
            0,
        ),
        (
            "quality_gate.json",
            "quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13",
            lambda: dump_json(quality_gate_json(base.records, as_of, 2, 14, 14, 30)),
            1,
        ),
        (
            "quality_gate.md",
            "quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13 --format markdown",
            lambda: quality_gate_markdown(base.records, as_of, 2, 14, 14, 30),
            1,
        ),
        (
            "doctor.json",
            "doctor --profile public --input examples/demo_records.json --as-of 2026-05-13",
            lambda: dump_json(doctor_json(DEMO_DATA, base, as_of, "public")),
            0,
        ),
        (
            "doctor.md",
            "doctor --profile public --input examples/demo_records.json --as-of 2026-05-13 --format markdown",
            lambda: doctor_markdown(doctor_json(DEMO_DATA, base, as_of, "public")),
            0,
        ),
        (
            "doctor_patch.json",
            "doctor --profile public --input examples/demo_records.json --as-of 2026-05-13 --format patch",
            lambda: dump_json(doctor_json(DEMO_DATA, base, as_of, "public")["patch"]),
            0,
        ),
        (
            "broker_matrix.json",
            "broker-matrix --input examples/demo_records.json --as-of 2026-05-13",
            lambda: dump_json(broker_matrix_json(base.records, as_of, 30)),
            0,
        ),
        (
            "broker_matrix.md",
            "broker-matrix --input examples/demo_records.json --as-of 2026-05-13 --format markdown",
            lambda: broker_matrix_markdown(base.records, as_of, 30),
            0,
        ),
        (
            "source_pack.json",
            "source-pack --input examples/demo_records.json --as-of 2026-05-13",
            lambda: dump_json(source_pack_json(base.records, as_of, DEFAULT_STALE_AFTER_DAYS)),
            0,
        ),
        (
            "source_pack.csv",
            "source-pack --input examples/demo_records.json --as-of 2026-05-13 --format csv",
            lambda: source_pack_csv(base.records, as_of, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "source_pack.md",
            "source-pack --input examples/demo_records.json --as-of 2026-05-13 --format markdown",
            lambda: source_pack_markdown(base.records, as_of, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "watchlist.json",
            "watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: dump_json(watchlist_json(base.records, as_of, DEFAULT_DAYS, DEFAULT_STALE_AFTER_DAYS)),
            0,
        ),
        (
            "watchlist.md",
            "watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown",
            lambda: watchlist_markdown(base.records, as_of, DEFAULT_DAYS, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "decision_log.json",
            "decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: dump_json(decision_log_json(base.records, as_of, DEFAULT_DAYS, DEFAULT_STALE_AFTER_DAYS)),
            0,
        ),
        (
            "decision_log.md",
            "decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown",
            lambda: decision_log_markdown(base.records, as_of, DEFAULT_DAYS, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "drilldown.json",
            "drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45",
            lambda: dump_json(
                drilldown_json(
                    base.records,
                    as_of,
                    "NVDA",
                    DEFAULT_DAYS,
                    DEFAULT_STALE_AFTER_DAYS,
                    DEFAULT_STALE_AFTER_DAYS,
                    30,
                    0,
                )
            ),
            0,
        ),
        (
            "drilldown.md",
            "drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45 --format markdown",
            lambda: drilldown_markdown(
                base.records,
                as_of,
                "NVDA",
                DEFAULT_DAYS,
                DEFAULT_STALE_AFTER_DAYS,
                DEFAULT_STALE_AFTER_DAYS,
                30,
                0,
            ),
            0,
        ),
        (
            "command_cookbook.md",
            "command-cookbook --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: command_cookbook_markdown(base, as_of, "examples/demo_records.json", "reports", DEFAULT_DAYS, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "tutorial.md",
            "tutorial --as-of 2026-05-13 --days 45 --dataset-path examples/demo_records.json",
            lambda: tutorial_markdown(as_of, DEFAULT_DAYS, "examples/demo_records.json"),
            0,
        ),
        (
            "agent_handoff.json",
            "agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: dump_json(
                agent_handoff_json(
                    base,
                    as_of,
                    "examples/demo_records.json",
                    "reports",
                    DEFAULT_DAYS,
                    DEFAULT_STALE_AFTER_DAYS,
                    DEFAULT_STALE_AFTER_DAYS,
                    5,
                )
            ),
            0,
        ),
        (
            "agent_handoff.md",
            "agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown",
            lambda: agent_handoff_markdown(
                base,
                as_of,
                "examples/demo_records.json",
                "reports",
                DEFAULT_DAYS,
                DEFAULT_STALE_AFTER_DAYS,
                DEFAULT_STALE_AFTER_DAYS,
                5,
            ),
            0,
        ),
        (
            "preset_run.json",
            "run-preset --presets examples/presets.json --name desk-packet",
            lambda: dump_json(run_preset_config(EXAMPLE_PRESETS, "desk-packet", write_files=False, dataset_override=base)),
            0,
        ),
        ("taxonomy.json", "taxonomy", lambda: dump_json(taxonomy_json()), 0),
        ("taxonomy.md", "taxonomy --format markdown", taxonomy_markdown, 0),
        (
            "version_report.json",
            "version-report --root . --repo .",
            lambda: dump_json(version_report_json(Path("."), Path("."))),
            0,
        ),
        (
            "version_report.md",
            "version-report --root . --repo . --format markdown",
            lambda: version_report_markdown(version_report_json(Path("."), Path("."))),
            0,
        ),
        (
            "post_event.json",
            "post-event --input examples/demo_records.json --as-of 2026-06-25",
            lambda: dump_json(post_event_json(base.records, post_event_as_of, 0)),
            0,
        ),
        (
            "post_event.md",
            "post-event --input examples/demo_records.json --as-of 2026-06-25 --format markdown",
            lambda: post_event_markdown(base.records, post_event_as_of, 0),
            0,
        ),
        ("demo_records_updated.json", "export-demo --snapshot updated", lambda: dump_json(DEMO_UPDATED_DATA), 0),
        (
            "compare.json",
            "compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27",
            lambda: dump_json(compare_snapshots_json(base, updated, updated_as_of, DEFAULT_STALE_AFTER_DAYS)),
            0,
        ),
        (
            "compare.md",
            "compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 --format markdown",
            lambda: compare_snapshots_markdown(base, updated, updated_as_of, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        (
            "merge.json",
            "merge examples/demo_records.json examples/demo_records_updated.json --as-of 2026-05-27",
            lambda: dump_json(merge_datasets_json([DEMO_DATA, DEMO_UPDATED_DATA], ["demo_records.json", "demo_records_updated.json"], updated_as_of, False)),
            0,
        ),
        (
            "dashboard.html",
            "html-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: html_dashboard(base.records, as_of, DEFAULT_DAYS, DEFAULT_STALE_AFTER_DAYS),
            0,
        ),
        ("demo_records.csv", "export-csv --input examples/demo_records.json", lambda: csv_text, 0),
        (
            "upcoming.ics",
            "export-ics --input examples/demo_records.json --as-of 2026-05-13 --days 45",
            lambda: records_to_ics(upcoming, as_of),
            0,
        ),
        (
            "imported_demo_records.json",
            "import-csv --input examples/demo_records.csv",
            lambda: dump_json(csv_to_dataset_json(csv_text)),
            0,
        ),
    ]
    if include_finalize:
        gallery = fixture_gallery_json(
            {f"examples/{path}": output() for path, _, output, _ in commands},
            [
                (path, command, output(), exit_code)
                for path, command, output, exit_code in _example_commands(base, updated, include_finalize=False)
            ],
        )
        gallery["summary"]["fixture_count"] = int(gallery["summary"]["fixture_count"]) + 2
        gallery["summary"]["output_type_counts"]["json"] = int(gallery["summary"]["output_type_counts"]["json"]) + 1
        gallery["summary"]["output_type_counts"]["markdown"] = int(gallery["summary"]["output_type_counts"]["markdown"]) + 1
        commands.extend(
            [
                (
                    "finalize_release.json",
                    "finalize-release --example",
                    lambda: dump_json(example_finalize_release_json(gallery)),
                    0,
                ),
                (
                    "finalize_release.md",
                    "finalize-release --example --format markdown",
                    lambda: finalize_release_markdown(example_finalize_release_json(gallery)),
                    0,
                ),
            ]
        )
    return commands


def _bundle_readme(commands: Iterable[CommandSpec]) -> str:
    lines = [
        "# Market Catalyst Calendar Demo Bundle",
        "",
        "This directory is generated by `python -m market_catalyst_calendar demo-bundle`.",
        "It is deterministic and stdlib-only: every file can be regenerated from the built-in demo datasets.",
        "",
        "## Contents",
        "",
        "- `examples/`: every documented example output, including JSON, Markdown, CSV, ICS, and HTML fixtures.",
        "- `quickstart-transcript.txt`: a short deterministic terminal transcript for first-run validation.",
        "- `manifest.json`: relative file paths, byte counts, SHA-256 hashes, command provenance, and bundle parameters.",
        "",
        "## Quickstart",
        "",
        "```bash",
        "python -m market_catalyst_calendar validate --input examples/demo_records.json",
        "python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45",
        "python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13",
        "```",
        "",
        "## Example Outputs",
        "",
        "| File | Command | Exit |",
        "| --- | --- | --- |",
    ]
    for path, command, _, exit_code in commands:
        lines.append(f"| `examples/{path}` | `python -m market_catalyst_calendar {command}` | {exit_code} |")
    lines.append("| `examples/fixture_gallery.json` | `python -m market_catalyst_calendar fixture-gallery` | 0 |")
    lines.append("| `examples/fixture_gallery.md` | `python -m market_catalyst_calendar fixture-gallery --format markdown` | 0 |")
    lines.append("")
    return "\n".join(lines)


def _quickstart_transcript(commands: List[CommandSpec]) -> str:
    outputs = {path: output() for path, _, output, _ in commands}
    validate_payload = {"ok": True, "record_count": len(parse_dataset(DEMO_DATA).records)}
    quality_payload = quality_gate_json(parse_dataset(DEMO_DATA).records, DEFAULT_AS_OF, 2, 14, 14, 30)
    bundle_payload = {
        "bundle_dir": "demo-bundle",
        "file_count": len(commands) + 4,
        "manifest": "manifest.json",
        "ok": True,
    }
    lines = [
        "$ python -m market_catalyst_calendar demo-bundle --output-dir demo-bundle",
        dump_json(bundle_payload).rstrip(),
        "$ cd demo-bundle",
        "$ python -m market_catalyst_calendar validate --input examples/demo_records.json",
        dump_json(validate_payload).rstrip(),
        "$ python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45",
        outputs["upcoming.json"].rstrip(),
        "$ python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13",
        dump_json(quality_payload).rstrip(),
        "# exit code: 1",
    ]
    return "\n".join(lines) + "\n"


def _build_manifest(root: Path, relative_paths: Iterable[str]) -> Dict[str, object]:
    command_map = {f"examples/{path}": {"command": command, "exit_code": exit_code} for path, command, _, exit_code in _example_commands(parse_dataset(DEMO_DATA), parse_dataset(DEMO_UPDATED_DATA))}
    files = []
    for relative_path in relative_paths:
        digest, byte_count = _hash_file(root / relative_path)
        item = {"bytes": byte_count, "path": relative_path, "sha256": digest}
        if relative_path in command_map:
            item.update(command_map[relative_path])
        files.append(item)
    return {
        "bundle_version": BUNDLE_VERSION,
        "dataset": {
            "as_of": DEFAULT_AS_OF.isoformat(),
            "record_count": len(parse_dataset(DEMO_DATA).records),
            "record_ids": [record.record_id for record in sorted_records(parse_dataset(DEMO_DATA).records)],
            "updated_as_of": UPDATED_AS_OF.isoformat(),
            "updated_record_count": len(parse_dataset(DEMO_UPDATED_DATA).records),
        },
        "files": files,
        "parameters": {
            "as_of": DEFAULT_AS_OF.isoformat(),
            "days": DEFAULT_DAYS,
            "post_event_as_of": POST_EVENT_AS_OF.isoformat(),
            "stale_after_days": DEFAULT_STALE_AFTER_DAYS,
        },
    }


def _upcoming_records(records: Iterable[CatalystRecord], as_of: date, days: int) -> List[CatalystRecord]:
    return [
        record
        for record in records
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]


def _stale_records(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> List[CatalystRecord]:
    return [
        record
        for record in records
        if score_record(record, as_of, stale_after_days=stale_after_days).review_state == "stale"
    ]


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            byte_count += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), byte_count


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
