"""Deterministic command cookbook rendering."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Sequence

from .models import CatalystRecord, Dataset, sorted_records
from .scoring import score_record


@dataclass(frozen=True)
class CookbookCommand:
    command: str
    outputs: Sequence[str]
    note: str


@dataclass(frozen=True)
class CookbookRecipe:
    recipe_id: str
    title: str
    reason: str
    commands: Sequence[CookbookCommand]


def command_cookbook_markdown(
    dataset: Dataset,
    as_of: date,
    dataset_path: str = "dataset.json",
    output_dir: str = "reports",
    days: int = 45,
    stale_after_days: int = 14,
) -> str:
    """Render a field-aware analyst playbook with command sequences."""

    records = sorted_records(dataset.records)
    selected = _selected_recipes(records, as_of, dataset_path, output_dir, days, stale_after_days)
    skipped = _skipped_recipes(records)
    profile = _profile(records, as_of, days, stale_after_days)

    lines: List[str] = [
        "# Market Catalyst Command Cookbook",
        "",
        f"As of: {as_of.isoformat()}",
        f"Dataset path in commands: `{dataset_path}`",
        f"Output directory in commands: `{output_dir}`",
        "",
        "## Dataset Profile",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in profile:
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Field-Driven Selection",
            "",
            "| Section | Decision | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for recipe in selected:
        lines.append(f"| {recipe.title} | selected | {_markdown_cell(recipe.reason)} |")
    for title, reason in skipped:
        lines.append(f"| {title} | skipped | {_markdown_cell(reason)} |")

    lines.extend(["", "## Analyst Playbook", ""])
    for index, recipe in enumerate(selected, start=1):
        lines.extend(
            [
                f"### {index}. {recipe.title}",
                "",
                f"Why: {recipe.reason}",
                "",
                "Expected output files:",
            ]
        )
        outputs = _recipe_outputs(recipe)
        for output in outputs:
            lines.append(f"- `{output}`")
        lines.extend(["", "Commands:", "", "```bash", f"mkdir -p {shlex.quote(output_dir)}"])
        for command in recipe.commands:
            lines.append(command.command)
        lines.extend(["```", ""])
        for command in recipe.commands:
            if command.note:
                joined_outputs = ", ".join(f"`{output}`" for output in command.outputs)
                lines.append(f"- {joined_outputs}: {command.note}")
        lines.append("")
    return "\n".join(lines)


def _selected_recipes(
    records: Sequence[CatalystRecord],
    as_of: date,
    dataset_path: str,
    output_dir: str,
    days: int,
    stale_after_days: int,
) -> List[CookbookRecipe]:
    dataset = shlex.quote(dataset_path)
    out = _OutputPaths(output_dir)
    recipes = [
        CookbookRecipe(
            "intake",
            "Intake And Freshness Gate",
            "Every dataset should validate before downstream reports are trusted; quality-gate is included because it exposes publication blockers.",
            [
                _cmd(f"python -m market_catalyst_calendar validate --input {dataset}", [out.path("validate.json")], "Schema and record consistency check; exit nonzero if the dataset is invalid."),
                _cmd(
                    f"python -m market_catalyst_calendar quality-gate --profile public --input {dataset} --as-of {as_of.isoformat()} > {out.qpath('quality_gate.json')} || test $? -eq 1",
                    [out.path("quality_gate.json")],
                    "Public-research gate. Exit code 1 is expected when the gate finds blocking issues, so the shell guard preserves the playbook run.",
                    already_redirected=True,
                ),
                _cmd(f"python -m market_catalyst_calendar evidence-audit --input {dataset} --as-of {as_of.isoformat()} --format markdown", [out.path("evidence_audit.md")], "Evidence freshness, source-count, and source-concentration review."),
            ],
        ),
        CookbookRecipe(
            "core",
            "Core Catalyst Briefing",
            "Upcoming, stale, brief, and review-plan outputs create the minimum daily analyst packet.",
            [
                _cmd(f"python -m market_catalyst_calendar upcoming --input {dataset} --as-of {as_of.isoformat()} --days {days}", [out.path("upcoming.json")], "Machine-readable forward catalyst queue."),
                _cmd(f"python -m market_catalyst_calendar stale --input {dataset} --as-of {as_of.isoformat()} --format markdown", [out.path("stale.md")], "Human-readable list of records whose review state is stale."),
                _cmd(f"python -m market_catalyst_calendar brief --input {dataset} --as-of {as_of.isoformat()} --days {days}", [out.path("brief.md")], "Ranked Markdown brief for the forward window."),
                _cmd(f"python -m market_catalyst_calendar review-plan --input {dataset} --as-of {as_of.isoformat()} --days {days} --format markdown", [out.path("review_plan.md")], "Step-by-step checklist for stale and high-urgency records."),
            ],
        ),
        CookbookRecipe(
            "sources",
            "Source Handoff Packet",
            "Evidence URLs are present, so the cookbook includes a source inventory for audit or collection work.",
            [
                _cmd(f"python -m market_catalyst_calendar source-pack --input {dataset} --as-of {as_of.isoformat()}", [out.path("source_pack.json")], "Deduplicated source inventory for automation."),
                _cmd(f"python -m market_catalyst_calendar source-pack --input {dataset} --as-of {as_of.isoformat()} --format csv", [out.path("source_pack.csv")], "Spreadsheet-ready source collection list."),
                _cmd(f"python -m market_catalyst_calendar source-pack --input {dataset} --as-of {as_of.isoformat()} --format markdown", [out.path("source_pack.md")], "Analyst-readable source packet."),
            ],
        ),
    ]
    if _has_position_fields(records):
        recipes.append(
            CookbookRecipe(
                "exposure",
                "Portfolio Exposure Pass",
                "At least one record has `portfolio_weight` or `position_size`, so exposure aggregation is useful.",
                [
                    _cmd(f"python -m market_catalyst_calendar exposure --input {dataset} --as-of {as_of.isoformat()} --days {days}", [out.path("exposure.json")], "Grouped exposure data by ticker, event type, and urgency."),
                    _cmd(f"python -m market_catalyst_calendar exposure --input {dataset} --as-of {as_of.isoformat()} --days {days} --format markdown", [out.path("exposure.md")], "Markdown exposure table for review packets."),
                ],
            )
        )
    if _has_risk_budget_fields(records):
        recipes.append(
            CookbookRecipe(
                "risk",
                "Risk Budget Pass",
                "At least one record has `risk_budget` or `max_loss`, so event loss should be checked against budget.",
                [
                    _cmd(f"python -m market_catalyst_calendar risk-budget --input {dataset} --as-of {as_of.isoformat()} --days {days}", [out.path("risk_budget.json")], "Risk-budget calculations and flags for downstream automation."),
                    _cmd(f"python -m market_catalyst_calendar risk-budget --input {dataset} --as-of {as_of.isoformat()} --days {days} --format markdown", [out.path("risk_budget.md")], "Markdown risk table with over-budget details."),
                ],
            )
        )
    if _has_sector_theme_fields(records):
        recipes.append(
            CookbookRecipe(
                "sector",
                "Sector And Theme Map",
                "At least one record has `sector` or `theme`, so concentration should be reviewed above the single-name level.",
                [
                    _cmd(f"python -m market_catalyst_calendar sector-map --input {dataset} --as-of {as_of.isoformat()}", [out.path("sector_map.json")], "Sector/theme group data with exposure and evidence flags."),
                    _cmd(f"python -m market_catalyst_calendar sector-map --input {dataset} --as-of {as_of.isoformat()} --format markdown", [out.path("sector_map.md")], "Markdown sector/theme concentration view."),
                ],
            )
        )
    if _has_thesis_fields(records):
        recipes.append(
            CookbookRecipe(
                "thesis",
                "Thesis Coverage Pass",
                "At least one record has `thesis_id` or `source_ref`, so thesis-level coverage and decision stubs are relevant.",
                [
                    _cmd(f"python -m market_catalyst_calendar thesis-map --input {dataset} --as-of {as_of.isoformat()} --format markdown", [out.path("thesis_map.md")], "Thesis grouping with source references."),
                    _cmd(f"python -m market_catalyst_calendar watchlist --input {dataset} --as-of {as_of.isoformat()} --days {days} --format markdown", [out.path("watchlist.md")], "Prioritized watch queue with thesis/source triggers."),
                    _cmd(f"python -m market_catalyst_calendar decision-log --input {dataset} --as-of {as_of.isoformat()} --days {days} --format markdown", [out.path("decision_log.md")], "Decision memo stubs tied back to catalyst and thesis context."),
                ],
            )
        )
    if _has_broker_views(records):
        recipes.append(
            CookbookRecipe(
                "broker",
                "Broker View Matrix",
                "At least one record has `broker_views`, so target dispersion and stale broker sources should be summarized.",
                [
                    _cmd(f"python -m market_catalyst_calendar broker-matrix --input {dataset} --as-of {as_of.isoformat()}", [out.path("broker_matrix.json")], "Broker matrix data with target-price dispersion."),
                    _cmd(f"python -m market_catalyst_calendar broker-matrix --input {dataset} --as-of {as_of.isoformat()} --format markdown", [out.path("broker_matrix.md")], "Analyst-readable broker view matrix."),
                ],
            )
        )
    if _has_scenarios(records):
        recipes.append(
            CookbookRecipe(
                "scenarios",
                "Scenario Matrix Pass",
                "Bull/base/bear scenario notes are available, so event scenarios can be rendered directly.",
                [
                    _cmd(f"python -m market_catalyst_calendar scenario-matrix --input {dataset} --as-of {as_of.isoformat()} --days {days}", [out.path("scenario_matrix.json")], "Scenario rows for automation."),
                    _cmd(f"python -m market_catalyst_calendar scenario-matrix --input {dataset} --as-of {as_of.isoformat()} --days {days} --format markdown", [out.path("scenario_matrix.md")], "Markdown scenario matrix for analyst review."),
                ],
            )
        )
    if _has_post_event_candidates(records, as_of):
        recipes.append(
            CookbookRecipe(
                "post-event",
                "Post-Event Closeout",
                "At least one catalyst is completed, past its event window, or has outcome metadata, so outcome capture should be queued.",
                [
                    _cmd(f"python -m market_catalyst_calendar post-event --input {dataset} --as-of {as_of.isoformat()}", [out.path("post_event.json")], "Machine-readable outcome-review queue."),
                    _cmd(f"python -m market_catalyst_calendar post-event --input {dataset} --as-of {as_of.isoformat()} --format markdown", [out.path("post_event.md")], "Markdown post-event review templates."),
                ],
            )
        )
    recipes.append(
        CookbookRecipe(
            "exports",
            "Portable Outputs",
            "CSV, calendar, dashboard, and archive outputs are useful for handoff even when no optional fields are present.",
            [
                _cmd(f"python -m market_catalyst_calendar export-csv --input {dataset} --output {out.qpath('dataset.csv')}", [out.path("dataset.csv")], "Spreadsheet-friendly full dataset export.", already_redirected=True),
                _cmd(f"python -m market_catalyst_calendar export-ics --input {dataset} --as-of {as_of.isoformat()} --days {days} --output {out.qpath('upcoming.ics')}", [out.path("upcoming.ics")], "Calendar feed for upcoming open catalysts.", already_redirected=True),
                _cmd(f"python -m market_catalyst_calendar html-dashboard --input {dataset} --as-of {as_of.isoformat()} --days {days} --output {out.qpath('dashboard.html')}", [out.path("dashboard.html")], "Static no-JavaScript dashboard.", already_redirected=True),
                _cmd(f"python -m market_catalyst_calendar create-archive --input {dataset} --output-dir {out.qpath('archive')} --as-of {as_of.isoformat()} --days {days}", [out.path("archive/manifest.json")], "Portable archive directory with manifest hashes.", already_redirected=True),
                _cmd(f"python -m market_catalyst_calendar verify-archive {out.qpath('archive')}", [out.path("archive_verification.json")], "Archive verification report."),
            ],
        )
    )
    return recipes


def _skipped_recipes(records: Sequence[CatalystRecord]) -> List[tuple[str, str]]:
    skipped: List[tuple[str, str]] = []
    if not _has_position_fields(records):
        skipped.append(("Portfolio Exposure Pass", "No `portfolio_weight` or `position_size` fields are populated."))
    if not _has_risk_budget_fields(records):
        skipped.append(("Risk Budget Pass", "No `risk_budget` or `max_loss` fields are populated."))
    if not _has_sector_theme_fields(records):
        skipped.append(("Sector And Theme Map", "No `sector` or `theme` fields are populated."))
    if not _has_thesis_fields(records):
        skipped.append(("Thesis Coverage Pass", "No `thesis_id` or `source_ref` fields are populated."))
    if not _has_broker_views(records):
        skipped.append(("Broker View Matrix", "No `broker_views` are populated."))
    if not _has_scenarios(records):
        skipped.append(("Scenario Matrix Pass", "No record has complete bull/base/bear scenario notes."))
    return skipped


def _profile(records: Sequence[CatalystRecord], as_of: date, days: int, stale_after_days: int) -> List[tuple[str, object]]:
    upcoming_count = sum(1 for record in records if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days)
    stale_count = sum(1 for record in records if score_record(record, as_of, stale_after_days=stale_after_days).review_state == "stale")
    completed_or_past = sum(1 for record in records if record.status == "completed" or record.window.end <= as_of)
    return [
        ("records", len(records)),
        ("upcoming open records", upcoming_count),
        ("stale records", stale_count),
        ("completed or past-window records", completed_or_past),
        ("records with portfolio exposure", sum(1 for record in records if record.portfolio_weight is not None or record.position_size is not None)),
        ("records with risk budget fields", sum(1 for record in records if record.risk_budget is not None or record.max_loss is not None)),
        ("records with sector/theme", sum(1 for record in records if record.sector or record.theme)),
        ("records with thesis links", sum(1 for record in records if record.thesis_id or record.source_ref)),
        ("broker views", sum(len(record.broker_views) for record in records)),
    ]


def _cmd(command: str, outputs: Sequence[str], note: str, already_redirected: bool = False) -> CookbookCommand:
    if already_redirected:
        return CookbookCommand(command=command, outputs=outputs, note=note)
    if len(outputs) != 1:
        raise ValueError("redirected cookbook commands must have one output")
    return CookbookCommand(command=f"{command} > {shlex.quote(outputs[0])}", outputs=outputs, note=note)


def _recipe_outputs(recipe: CookbookRecipe) -> List[str]:
    return sorted({output for command in recipe.commands for output in command.outputs})


def _has_position_fields(records: Sequence[CatalystRecord]) -> bool:
    return any(record.portfolio_weight is not None or record.position_size is not None for record in records)


def _has_risk_budget_fields(records: Sequence[CatalystRecord]) -> bool:
    return any(record.risk_budget is not None or record.max_loss is not None for record in records)


def _has_sector_theme_fields(records: Sequence[CatalystRecord]) -> bool:
    return any(record.sector or record.theme for record in records)


def _has_thesis_fields(records: Sequence[CatalystRecord]) -> bool:
    return any(record.thesis_id or record.source_ref for record in records)


def _has_broker_views(records: Sequence[CatalystRecord]) -> bool:
    return any(record.broker_views for record in records)


def _has_scenarios(records: Sequence[CatalystRecord]) -> bool:
    required = {"bull", "base", "bear"}
    return any(required.issubset(record.scenario_notes) for record in records)


def _has_post_event_candidates(records: Sequence[CatalystRecord], as_of: date) -> bool:
    return any(
        record.status == "completed"
        or record.window.end <= as_of
        or record.actual_outcome is not None
        or record.outcome_recorded_at is not None
        for record in records
    )


def _markdown_cell(value: str) -> str:
    return value.replace("\n", " ").replace("|", "\\|")


class _OutputPaths:
    def __init__(self, output_dir: str) -> None:
        self.output_dir = output_dir.rstrip("/") or "."

    def path(self, name: str) -> str:
        if self.output_dir == ".":
            return name
        return f"{self.output_dir}/{name}"

    def qpath(self, name: str) -> str:
        return shlex.quote(self.path(name))
