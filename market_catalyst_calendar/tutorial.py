"""Notebook-free Markdown tutorial rendering."""

from __future__ import annotations

import shlex
from datetime import date
from typing import Dict, List

from .compare import compare_snapshots_markdown
from .demo import DEMO_DATA, DEMO_UPDATED_DATA
from .io import dump_json
from .models import Dataset, parse_dataset, sorted_records
from .quality_gate import quality_gate_json
from .render import (
    drilldown_markdown,
    records_json,
    risk_budget_markdown,
    source_pack_csv,
)
from .scoring import score_record


DEFAULT_AS_OF = date(2026, 5, 13)
UPDATED_AS_OF = date(2026, 5, 27)
DEFAULT_DAYS = 45
DEFAULT_STALE_AFTER_DAYS = 14


def tutorial_markdown(
    as_of: date = DEFAULT_AS_OF,
    days: int = DEFAULT_DAYS,
    dataset_path: str = "examples/demo_records.json",
) -> str:
    """Render a deterministic tutorial based on the built-in demo data."""

    base = parse_dataset(DEMO_DATA)
    updated = parse_dataset(DEMO_UPDATED_DATA)
    upcoming = _upcoming_records(base, as_of, days)
    dataset_arg = shlex.quote(dataset_path)
    updated_arg = shlex.quote(_updated_dataset_path(dataset_path))

    lines: List[str] = [
        "# Market Catalyst Calendar Tutorial",
        "",
        "This is a notebooks-free walkthrough generated from the built-in demo dataset. It is deterministic, offline, and designed to be run from a shell with only the Python standard library.",
        "",
        "## Tutorial Parameters",
        "",
        "| Parameter | Value |",
        "| --- | --- |",
        f"| Demo dataset date | {base.as_of.isoformat()} |",
        f"| Report as-of date | {as_of.isoformat()} |",
        f"| Forward window | {days} days |",
        f"| Demo records | {len(base.records)} |",
        f"| Dataset path used in commands | `{dataset_path}` |",
        "",
    ]

    _append_step(
        lines,
        1,
        "Create the Demo Dataset",
        "Start by materializing the canonical input JSON. The rest of the tutorial assumes this file path.",
        f"python -m market_catalyst_calendar export-demo > {dataset_arg}",
        _dataset_excerpt(base),
        "You can identify the dataset date, four record ids, and the mix of completed, watching, scheduled, and confirmed records.",
    )
    _append_step(
        lines,
        2,
        "Validate the Record Shape",
        "Run the structural validator before trusting any report output.",
        f"python -m market_catalyst_calendar validate --input {dataset_arg}",
        dump_json({"ok": True, "record_count": len(base.records)}).rstrip(),
        "Validation passes with `ok: true`; any schema or record consistency issue should block downstream briefing work.",
        language="json",
    )
    _append_step(
        lines,
        3,
        "Rank the Forward Catalyst Queue",
        "List upcoming open catalysts in the forward window and inspect the scores that drive later reports.",
        f"python -m market_catalyst_calendar upcoming --input {dataset_arg} --as-of {as_of.isoformat()} --days {days}",
        _upcoming_excerpt(upcoming, as_of),
        "The highest-priority item is PFE because it is near term, high confidence, and tied to a regulatory decision.",
        language="json",
    )
    _append_step(
        lines,
        4,
        "Observe a Publication Quality Failure",
        "The demo data intentionally uses placeholder URLs, so the public quality gate exits with status 1 while still producing useful diagnostics.",
        f"python -m market_catalyst_calendar quality-gate --profile public --input {dataset_arg} --as-of {as_of.isoformat()}",
        _quality_gate_excerpt(base, as_of),
        "The nonzero exit is expected here; the learning target is recognizing blocking diagnostic codes before handoff.",
        expected_exit=1,
        language="json",
    )
    _append_step(
        lines,
        5,
        "Connect Catalysts to Risk",
        "Use the risk-budget report to translate event records into over-budget and expected-loss review items.",
        f"python -m market_catalyst_calendar risk-budget --input {dataset_arg} --as-of {as_of.isoformat()} --days {days} --format markdown",
        _first_lines(risk_budget_markdown(upcoming, as_of), 12),
        "Two upcoming catalysts are over budget; that is the prompt for position sizing or thesis review before the event window.",
        language="markdown",
    )
    _append_step(
        lines,
        6,
        "Prepare a Source Collection List",
        "Export a deduplicated source inventory that another analyst or offline agent can work through.",
        f"python -m market_catalyst_calendar source-pack --input {dataset_arg} --as-of {as_of.isoformat()} --format csv",
        _first_lines(source_pack_csv(base.records, as_of, DEFAULT_STALE_AFTER_DAYS), 5),
        "Each source row preserves URL, usage, linked tickers, record ids, and freshness state without fetching the network.",
        language="csv",
    )
    _append_step(
        lines,
        7,
        "Drill Into One Ticker",
        "Compose a single-name dossier when a record needs focused review.",
        f"python -m market_catalyst_calendar drilldown --input {dataset_arg} --as-of {as_of.isoformat()} --ticker NVDA --days {days} --format markdown",
        _heading_excerpt(
            drilldown_markdown(
                base.records,
                as_of,
                "NVDA",
                days,
                DEFAULT_STALE_AFTER_DAYS,
                DEFAULT_STALE_AFTER_DAYS,
                30,
                0,
            )
        ),
        "The dossier combines record ledger, upcoming events, thesis map, broker matrix, risk budget, watchlist, source pack, and decision logs for one ticker.",
        language="markdown",
    )
    _append_step(
        lines,
        8,
        "Compare a Later Snapshot",
        "Generate the updated demo snapshot and compare it with the base dataset to see status, evidence, and thesis-impact changes.",
        (
            f"python -m market_catalyst_calendar export-demo --snapshot updated > {updated_arg}\n"
            f"python -m market_catalyst_calendar compare --base {dataset_arg} --current {updated_arg} --as-of {UPDATED_AS_OF.isoformat()} --format markdown"
        ),
        _first_lines(compare_snapshots_markdown(base, updated, UPDATED_AS_OF, DEFAULT_STALE_AFTER_DAYS), 14),
        "Snapshot comparison separates added, removed, and changed records so dataset refreshes can be reviewed without losing provenance.",
        language="markdown",
    )

    lines.extend(
        [
            "## Completion Checklist",
            "",
            "- [ ] Demo data was exported and validated.",
            "- [ ] Upcoming catalyst priority was checked against event timing and score.",
            "- [ ] Public quality-gate failures were treated as expected tutorial diagnostics, not ignored production failures.",
            "- [ ] Risk-budget and source-pack outputs were reviewed for handoff-ready context.",
            "- [ ] Single-ticker drilldown and snapshot compare were used to move from daily queue to deeper review.",
            "",
        ]
    )
    return "\n".join(lines)


def _append_step(
    lines: List[str],
    number: int,
    title: str,
    goal: str,
    command: str,
    excerpt: str,
    checkpoint: str,
    expected_exit: int = 0,
    language: str = "text",
) -> None:
    lines.extend(
        [
            f"## {number}. {title}",
            "",
            goal,
            "",
            "Command:",
            "",
            "```bash",
            command,
            "```",
            "",
            f"Expected exit code: `{expected_exit}`",
            "",
            "Expected output excerpt:",
            "",
            f"```{language}",
            excerpt.rstrip(),
            "```",
            "",
            f"Learning checkpoint: {checkpoint}",
            "",
        ]
    )


def _dataset_excerpt(dataset: Dataset) -> str:
    status_counts: Dict[str, int] = {}
    for record in dataset.records:
        status_counts[record.status] = status_counts.get(record.status, 0) + 1
    record_ids = [record.record_id for record in sorted_records(dataset.records)]
    return dump_json(
        {
            "as_of": dataset.as_of.isoformat(),
            "record_count": len(dataset.records),
            "record_ids": record_ids,
            "status_counts": dict(sorted(status_counts.items())),
        }
    ).rstrip()


def _upcoming_excerpt(records, as_of: date) -> str:
    payload = records_json(records, as_of)
    excerpt = {
        "as_of": payload["as_of"],
        "records": [
            {
                "catalyst_score": record["catalyst_score"],
                "days_until": record["days_until"],
                "id": record["id"],
                "ticker": record["ticker"],
                "urgency": record["urgency"],
                "window": record["window"],
            }
            for record in payload["records"]
        ],
    }
    return dump_json(excerpt).rstrip()


def _quality_gate_excerpt(dataset: Dataset, as_of: date) -> str:
    payload = quality_gate_json(dataset.records, as_of, 2, 14, 14, 30)
    first = payload["records"][0]
    excerpt = {
        "ok": payload["ok"],
        "failed_record_count": payload["summary"]["failed_record_count"],
        "first_record": {
            "failed_rules": first["failed_rules"],
            "id": first["id"],
            "issue_codes": [issue["code"] for issue in first["issues"]],
            "ticker": first["ticker"],
        },
    }
    return dump_json(excerpt).rstrip()


def _first_lines(text: str, count: int) -> str:
    lines = text.rstrip().splitlines()
    excerpt = lines[:count]
    if len(lines) > count:
        excerpt.append("...")
    return "\n".join(excerpt)


def _heading_excerpt(text: str) -> str:
    headings = [line for line in text.splitlines() if line.startswith("#")][:10]
    return "\n".join(headings)


def _upcoming_records(dataset: Dataset, as_of: date, days: int):
    return [
        record
        for record in dataset.records
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]


def _updated_dataset_path(dataset_path: str) -> str:
    if dataset_path.endswith(".json"):
        return dataset_path[:-5] + "_updated.json"
    return dataset_path + ".updated.json"
