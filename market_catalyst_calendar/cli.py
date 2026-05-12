"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

from .agent_handoff import agent_handoff_json, agent_handoff_markdown
from .archive import create_archive, verify_archive
from .changelog import changelog_json, changelog_markdown
from .command_cookbook import command_cookbook_markdown
from .compare import compare_snapshots_json, compare_snapshots_markdown
from .csv_io import csv_to_dataset_json, dataset_to_csv
from .dashboard import html_dashboard
from .demo import DEMO_DATA, DEMO_UPDATED_DATA
from .demo_bundle import bundled_fixture_gallery_json, bundled_fixture_gallery_markdown, create_demo_bundle
from .evidence import evidence_audit_json, evidence_audit_markdown
from .ics import records_to_ics
from .io import dump_json, load_dataset, read_json, read_text
from .merge import merge_datasets_json
from .models import CatalystRecord, Dataset, parse_dataset, validation_errors
from .quality_gate import PROFILES, quality_gate_json, quality_gate_markdown
from .release_audit import release_audit_json, release_audit_markdown
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
from .smoke_matrix import smoke_matrix_json, smoke_matrix_markdown, smoke_probe_json


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="market-catalyst-calendar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate catalyst JSON")
    add_input(validate)
    add_as_of(validate)
    validate.add_argument("--profile", choices=PROFILES, default="basic", help="validation depth; default: basic")
    validate.set_defaults(func=cmd_validate)

    upcoming = subparsers.add_parser("upcoming", help="list upcoming catalysts")
    add_input(upcoming)
    add_as_of(upcoming)
    upcoming.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    upcoming.add_argument("--format", choices=["json", "markdown"], default="json")
    upcoming.set_defaults(func=cmd_upcoming)

    stale = subparsers.add_parser("stale", help="list catalysts that need review")
    add_input(stale)
    add_as_of(stale)
    stale.add_argument("--stale-after-days", type=int, default=14)
    stale.add_argument("--format", choices=["json", "markdown"], default="json")
    stale.set_defaults(func=cmd_stale)

    brief = subparsers.add_parser("brief", help="render a Markdown catalyst brief")
    add_input(brief)
    add_as_of(brief)
    brief.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    brief.set_defaults(func=cmd_brief)

    exposure = subparsers.add_parser("exposure", help="aggregate upcoming catalyst exposure")
    add_input(exposure)
    add_as_of(exposure)
    exposure.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    exposure.add_argument("--format", choices=["json", "markdown"], default="json")
    exposure.set_defaults(func=cmd_exposure)

    risk_budget = subparsers.add_parser("risk-budget", help="summarize event risk against catalyst budgets")
    add_input(risk_budget)
    add_as_of(risk_budget)
    risk_budget.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    risk_budget.add_argument("--format", choices=["json", "markdown"], default="json")
    risk_budget.set_defaults(func=cmd_risk_budget)

    sector_map = subparsers.add_parser("sector-map", help="group catalysts by sector and theme context")
    add_input(sector_map)
    add_as_of(sector_map)
    sector_map.add_argument("--stale-after-days", type=int, default=14)
    sector_map.add_argument("--format", choices=["json", "markdown"], default="json")
    sector_map.set_defaults(func=cmd_sector_map)

    review_plan = subparsers.add_parser("review-plan", help="create a stale and high-urgency review checklist")
    add_input(review_plan)
    add_as_of(review_plan)
    review_plan.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    review_plan.add_argument("--stale-after-days", type=int, default=14)
    review_plan.add_argument("--format", choices=["json", "markdown"], default="json")
    review_plan.set_defaults(func=cmd_review_plan)

    thesis_map = subparsers.add_parser("thesis-map", help="group catalysts by investment thesis")
    add_input(thesis_map)
    add_as_of(thesis_map)
    thesis_map.add_argument("--stale-after-days", type=int, default=14)
    thesis_map.add_argument("--format", choices=["json", "markdown"], default="json")
    thesis_map.set_defaults(func=cmd_thesis_map)

    scenario_matrix = subparsers.add_parser("scenario-matrix", help="render bull/base/bear event scenarios")
    add_input(scenario_matrix)
    add_as_of(scenario_matrix)
    scenario_matrix.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    scenario_matrix.add_argument("--stale-after-days", type=int, default=14)
    scenario_matrix.add_argument("--format", choices=["json", "markdown"], default="json")
    scenario_matrix.set_defaults(func=cmd_scenario_matrix)

    evidence_audit = subparsers.add_parser("evidence-audit", help="audit evidence freshness and source diversity")
    add_input(evidence_audit)
    add_as_of(evidence_audit)
    evidence_audit.add_argument("--fresh-after-days", type=int, default=14)
    evidence_audit.add_argument("--min-sources", type=int, default=2)
    evidence_audit.add_argument("--max-domain-share", type=float, default=0.67)
    evidence_audit.add_argument("--format", choices=["json", "markdown"], default="json")
    evidence_audit.set_defaults(func=cmd_evidence_audit)

    quality_gate = subparsers.add_parser("quality-gate", help="apply public research dataset quality gates")
    add_input(quality_gate)
    add_as_of(quality_gate)
    quality_gate.add_argument("--profile", choices=PROFILES, default="public", help="quality gate profile; default: public")
    quality_gate.add_argument("--min-evidence-urls", type=int)
    quality_gate.add_argument("--max-review-age-days", type=int)
    quality_gate.add_argument("--max-evidence-age-days", type=int)
    quality_gate.add_argument("--max-broker-age-days", type=int)
    quality_gate.add_argument("--format", choices=["json", "markdown"], default="json")
    quality_gate.set_defaults(func=cmd_quality_gate)

    broker_matrix = subparsers.add_parser("broker-matrix", help="summarize broker views by ticker and thesis")
    add_input(broker_matrix)
    add_as_of(broker_matrix)
    broker_matrix.add_argument("--stale-after-days", type=int, default=30)
    broker_matrix.add_argument("--format", choices=["json", "markdown"], default="json")
    broker_matrix.set_defaults(func=cmd_broker_matrix)

    source_pack = subparsers.add_parser("source-pack", help="export unique evidence and broker source URLs")
    add_input(source_pack)
    add_as_of(source_pack)
    source_pack.add_argument("--fresh-after-days", type=int, default=14)
    source_pack.add_argument("--format", choices=["json", "csv", "markdown"], default="json")
    source_pack.set_defaults(func=cmd_source_pack)

    watchlist = subparsers.add_parser("watchlist", help="convert catalysts into prioritized watch items")
    add_input(watchlist)
    add_as_of(watchlist)
    watchlist.add_argument("--days", type=int, default=90, help="look-ahead window in days")
    watchlist.add_argument("--stale-after-days", type=int, default=14)
    watchlist.add_argument("--format", choices=["json", "markdown"], default="json")
    watchlist.set_defaults(func=cmd_watchlist)

    decision_log = subparsers.add_parser("decision-log", help="emit decision memo stubs per catalyst")
    add_input(decision_log)
    add_as_of(decision_log)
    decision_log.add_argument("--days", type=int, default=90, help="look-ahead window in days")
    decision_log.add_argument("--stale-after-days", type=int, default=14)
    decision_log.add_argument("--format", choices=["json", "markdown"], default="json")
    decision_log.set_defaults(func=cmd_decision_log)

    drilldown = subparsers.add_parser("drilldown", help="render a complete single-ticker catalyst dossier")
    add_input(drilldown)
    add_as_of(drilldown)
    drilldown.add_argument("--ticker", required=True, help="ticker symbol to drill into")
    drilldown.add_argument("--days", type=int, default=90, help="look-ahead window in days")
    drilldown.add_argument("--stale-after-days", type=int, default=14)
    drilldown.add_argument("--fresh-after-days", type=int, default=14)
    drilldown.add_argument("--broker-stale-after-days", type=int, default=30)
    drilldown.add_argument("--review-after-days", type=int, default=0)
    drilldown.add_argument("--format", choices=["json", "markdown"], default="json")
    drilldown.set_defaults(func=cmd_drilldown)

    command_cookbook = subparsers.add_parser("command-cookbook", help="render a field-aware command cookbook Markdown playbook")
    add_input(command_cookbook)
    add_as_of(command_cookbook)
    command_cookbook.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    command_cookbook.add_argument("--stale-after-days", type=int, default=14)
    command_cookbook.add_argument("--dataset-path", help="dataset path to show in generated commands; defaults to --input or dataset.json for stdin")
    command_cookbook.add_argument("--output-dir", default="reports", help="output directory to show in generated commands")
    command_cookbook.set_defaults(func=cmd_command_cookbook)

    agent_handoff = subparsers.add_parser("agent-handoff", help="create a machine-readable research-agent context pack")
    add_input(agent_handoff)
    add_as_of(agent_handoff)
    agent_handoff.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    agent_handoff.add_argument("--stale-after-days", type=int, default=14)
    agent_handoff.add_argument("--fresh-after-days", type=int, default=14)
    agent_handoff.add_argument("--top-limit", type=int, default=5, help="maximum top risks and stale items to include")
    agent_handoff.add_argument("--dataset-path", help="dataset path to show in generated commands; defaults to --input or dataset.json for stdin")
    agent_handoff.add_argument("--output-dir", default="reports", help="output directory to show in generated commands")
    agent_handoff.add_argument("--format", choices=["json", "markdown"], default="json")
    agent_handoff.set_defaults(func=cmd_agent_handoff)

    post_event = subparsers.add_parser("post-event", help="render post-event outcome review templates")
    add_input(post_event)
    add_as_of(post_event)
    post_event.add_argument("--review-after-days", type=int, default=0, help="days after event window end before outcome review is due")
    post_event.add_argument("--format", choices=["json", "markdown"], default="json")
    post_event.set_defaults(func=cmd_post_event)

    compare = subparsers.add_parser("compare", help="compare two catalyst dataset snapshots")
    compare.add_argument("--base", required=True, help="older dataset JSON path")
    compare.add_argument("--current", required=True, help="newer dataset JSON path")
    add_as_of(compare)
    compare.add_argument("--stale-after-days", type=int, default=14)
    compare.add_argument("--format", choices=["json", "markdown"], default="json")
    compare.add_argument("--output", "-o", help="output path; stdout when omitted")
    compare.set_defaults(func=cmd_compare)

    merge = subparsers.add_parser("merge", help="merge multiple catalyst datasets with deterministic conflict handling")
    merge.add_argument("inputs", nargs="+", help="input dataset JSON paths; use '-' for stdin")
    merge.add_argument("--as-of", help="merged dataset as_of; defaults to latest input as_of")
    merge.add_argument(
        "--prefer-newer-status-history",
        action="store_true",
        help="when records conflict, take status/history from the record with the newest history entry",
    )
    merge.add_argument("--output", "-o", help="output JSON path; stdout when omitted")
    merge.set_defaults(func=cmd_merge)

    html = subparsers.add_parser("html-dashboard", help="render a deterministic static HTML dashboard")
    add_input(html)
    add_as_of(html)
    html.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    html.add_argument("--stale-after-days", type=int, default=14)
    html.add_argument("--output", "-o", help="output HTML path; stdout when omitted")
    html.set_defaults(func=cmd_html_dashboard)

    demo = subparsers.add_parser("export-demo", help="write the built-in demo dataset")
    demo.add_argument("--snapshot", choices=["base", "updated"], default="base", help="demo snapshot to export")
    demo.add_argument("--output", "-o", help="output path; stdout when omitted")
    demo.set_defaults(func=cmd_export_demo)

    demo_bundle = subparsers.add_parser("demo-bundle", help="write a deterministic directory with every demo output")
    demo_bundle.add_argument("--output-dir", "-o", required=True, help="empty output directory for bundle files")
    demo_bundle.set_defaults(func=cmd_demo_bundle)

    fixture_gallery = subparsers.add_parser("fixture-gallery", help="list bundled fixture hashes, provenance, and use cases")
    fixture_gallery.add_argument("--format", choices=["json", "markdown"], default="json")
    fixture_gallery.add_argument("--output", "-o", help="output path; stdout when omitted")
    fixture_gallery.set_defaults(func=cmd_fixture_gallery)

    export_csv = subparsers.add_parser("export-csv", help="export catalyst JSON to deterministic CSV")
    add_input(export_csv)
    export_csv.add_argument("--output", "-o", help="output CSV path; stdout when omitted")
    export_csv.set_defaults(func=cmd_export_csv)

    export_ics = subparsers.add_parser("export-ics", help="export upcoming catalysts to deterministic iCalendar")
    add_input(export_ics)
    add_as_of(export_ics)
    export_ics.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    export_ics.add_argument("--output", "-o", help="output ICS path; stdout when omitted")
    export_ics.set_defaults(func=cmd_export_ics)

    import_csv = subparsers.add_parser("import-csv", help="import CSV into catalyst JSON")
    import_csv.add_argument("--input", "-i", default="-", help="input CSV path; defaults to stdin")
    import_csv.add_argument("--output", "-o", help="output JSON path; stdout when omitted")
    import_csv.set_defaults(func=cmd_import_csv)

    create_archive_parser = subparsers.add_parser("create-archive", help="create a portable archive directory")
    add_input(create_archive_parser)
    add_as_of(create_archive_parser)
    create_archive_parser.add_argument("--output-dir", "-o", required=True, help="empty output directory for archive files")
    create_archive_parser.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    create_archive_parser.add_argument("--stale-after-days", type=int, default=14)
    create_archive_parser.set_defaults(func=cmd_create_archive)

    verify_archive_parser = subparsers.add_parser("verify-archive", help="verify archive manifest hashes")
    verify_archive_parser.add_argument("archive_dir", help="archive directory containing manifest.json")
    verify_archive_parser.set_defaults(func=cmd_verify_archive)

    release_audit = subparsers.add_parser("release-audit", help="audit checked-in release artifacts")
    release_audit.add_argument("--root", default=".", help="repository root to audit; defaults to current directory")
    release_audit.add_argument("--format", choices=["json", "markdown"], default="json")
    release_audit.set_defaults(func=cmd_release_audit)

    changelog = subparsers.add_parser("changelog", help="summarize local git commits since a tag")
    changelog.add_argument("--repo", default=".", help="git repository root; defaults to current directory")
    changelog.add_argument("--since-tag", required=True, help="starting tag, excluded from the release notes")
    changelog.add_argument("--to-ref", default="HEAD", help="ending ref, included in the release notes; default: HEAD")
    changelog.add_argument("--include-merges", action="store_true", help="include merge commits; default excludes them")
    changelog.add_argument("--format", choices=["json", "markdown"], default="markdown")
    changelog.add_argument("--output", "-o", help="output path; stdout when omitted")
    changelog.set_defaults(func=cmd_changelog)

    smoke_matrix = subparsers.add_parser("smoke-matrix", help="run internal smoke checks for every command")
    smoke_matrix.add_argument("--format", choices=["json", "markdown"], default="json")
    smoke_matrix.add_argument("--probe", action="store_true", help=argparse.SUPPRESS)
    smoke_matrix.set_defaults(func=cmd_smoke_matrix)
    return parser


def add_input(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", "-i", default="-", help="input JSON path; defaults to stdin")


def add_as_of(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--as-of", help="ISO date override; defaults to dataset as_of")


def cmd_validate(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    errors = validation_errors(dataset)
    diagnostics = _validation_diagnostics(errors)
    if args.profile == "basic":
        if errors:
            print(dump_json({"ok": False, "errors": errors, "diagnostics": diagnostics, "profile": args.profile}), end="")
            return 1
        print(dump_json({"ok": True, "record_count": len(dataset.records)}), end="")
        return 0

    as_of = resolve_as_of(dataset, args.as_of)
    gate = quality_gate_json(dataset.records, as_of, None, None, None, None, args.profile)
    gate_diagnostics = _quality_gate_diagnostics(gate)
    diagnostics.extend(gate_diagnostics)
    if diagnostics:
        print(
            dump_json(
                {
                    "as_of": as_of.isoformat(),
                    "diagnostics": diagnostics,
                    "errors": errors,
                    "ok": False,
                    "profile": args.profile,
                    "quality_gate": {
                        "ok": gate["ok"],
                        "summary": gate["summary"],
                    },
                    "record_count": len(dataset.records),
                }
            ),
            end="",
        )
        return 1
    print(dump_json({"as_of": as_of.isoformat(), "ok": True, "profile": args.profile, "record_count": len(dataset.records)}), end="")
    return 0


def _validation_diagnostics(errors: List[str]) -> List[dict]:
    diagnostics = []
    for error in errors:
        record_id, detail = _split_validation_error(error)
        diagnostics.append(
            {
                "code": _validation_code(detail),
                "detail": detail,
                "record_id": record_id,
                "severity": "error",
                "source": "validate",
            }
        )
    return diagnostics


def _quality_gate_diagnostics(payload: dict) -> List[dict]:
    diagnostics = []
    for record in payload["records"]:
        for issue in record["issues"]:
            diagnostics.append(
                {
                    "code": issue["code"],
                    "detail": issue["detail"],
                    "record_id": record["id"],
                    "rule": issue["rule"],
                    "severity": issue["severity"],
                    "source": "quality-gate",
                    "ticker": record["ticker"],
                }
            )
    return diagnostics


def _split_validation_error(error: str) -> tuple[str, str]:
    if ": " not in error:
        return "", error
    record_id, detail = error.split(": ", 1)
    return record_id, detail


def _validation_code(detail: str) -> str:
    checks = [
        ("duplicate id", "MCC-VAL-IDENTITY-001"),
        ("ticker or entity is required", "MCC-VAL-IDENTITY-002"),
        ("ticker should look like", "MCC-VAL-IDENTITY-003"),
        ("at least one evidence URL", "MCC-VAL-EVIDENCE-001"),
        ("invalid evidence URL", "MCC-VAL-EVIDENCE-002"),
        ("missing scenario notes", "MCC-VAL-SCENARIO-001"),
        ("confidence", "MCC-VAL-CONFIDENCE-001"),
        ("open records need", "MCC-VAL-REVIEW-001"),
        ("last_reviewed cannot be after as_of", "MCC-VAL-DATE-001"),
        ("evidence_checked_at cannot be after as_of", "MCC-VAL-DATE-002"),
        ("outcome_recorded_at cannot be after as_of", "MCC-VAL-DATE-003"),
        ("outcome_recorded_at cannot be before", "MCC-VAL-DATE-004"),
        ("outcome_recorded_at requires actual_outcome", "MCC-VAL-OUTCOME-001"),
        ("broker view from", "MCC-VAL-BROKER-001"),
        ("history cannot include future updates", "MCC-VAL-HISTORY-001"),
        ("latest history status should match current status", "MCC-VAL-HISTORY-002"),
    ]
    for needle, code in checks:
        if needle in detail:
            return code
    return "MCC-VAL-GENERAL-001"


def cmd_upcoming(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    records = upcoming_records(dataset.records, as_of, args.days)
    write_records(records, as_of, args.format)
    return 0


def cmd_stale(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    records = [
        record
        for record in dataset.records
        if score_record(record, as_of, stale_after_days=args.stale_after_days).review_state == "stale"
    ]
    write_records(records, as_of, args.format)
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    records = upcoming_records(dataset.records, as_of, args.days)
    print(brief_markdown(records, as_of), end="")
    return 0


def cmd_exposure(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    records = upcoming_records(dataset.records, as_of, args.days)
    if args.format == "json":
        print(dump_json(exposure_json(records, as_of)), end="")
    else:
        print(exposure_markdown(records, as_of), end="")
    return 0


def cmd_risk_budget(args: argparse.Namespace) -> int:
    if args.days < 0:
        raise ValueError("--days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    records = upcoming_records(dataset.records, as_of, args.days)
    if args.format == "json":
        print(dump_json(risk_budget_json(records, as_of)), end="")
    else:
        print(risk_budget_markdown(records, as_of), end="")
    return 0


def cmd_sector_map(args: argparse.Namespace) -> int:
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(sector_map_json(dataset.records, as_of, args.stale_after_days)), end="")
    else:
        print(sector_map_markdown(dataset.records, as_of, args.stale_after_days), end="")
    return 0


def cmd_review_plan(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(review_plan_json(dataset.records, as_of, args.days, args.stale_after_days)), end="")
    else:
        print(review_plan_markdown(dataset.records, as_of, args.days, args.stale_after_days), end="")
    return 0


def cmd_thesis_map(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(thesis_map_json(dataset.records, as_of, args.stale_after_days)), end="")
    else:
        print(thesis_map_markdown(dataset.records, as_of, args.stale_after_days), end="")
    return 0


def cmd_scenario_matrix(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    records = upcoming_records(dataset.records, as_of, args.days)
    if args.format == "json":
        print(dump_json(scenario_matrix_json(records, as_of, args.stale_after_days)), end="")
    else:
        print(scenario_matrix_markdown(records, as_of, args.stale_after_days), end="")
    return 0


def cmd_evidence_audit(args: argparse.Namespace) -> int:
    if args.fresh_after_days < 0:
        raise ValueError("--fresh-after-days must be non-negative")
    if args.min_sources < 1:
        raise ValueError("--min-sources must be at least 1")
    if args.max_domain_share <= 0 or args.max_domain_share > 1:
        raise ValueError("--max-domain-share must be greater than 0 and at most 1")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(evidence_audit_json(dataset.records, as_of, args.fresh_after_days, args.min_sources, args.max_domain_share)), end="")
    else:
        print(evidence_audit_markdown(dataset.records, as_of, args.fresh_after_days, args.min_sources, args.max_domain_share), end="")
    return 0


def cmd_quality_gate(args: argparse.Namespace) -> int:
    if args.min_evidence_urls is not None and args.min_evidence_urls < 1:
        raise ValueError("--min-evidence-urls must be at least 1")
    if args.max_review_age_days is not None and args.max_review_age_days < 0:
        raise ValueError("--max-review-age-days must be non-negative")
    if args.max_evidence_age_days is not None and args.max_evidence_age_days < 0:
        raise ValueError("--max-evidence-age-days must be non-negative")
    if args.max_broker_age_days is not None and args.max_broker_age_days < 0:
        raise ValueError("--max-broker-age-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        payload = quality_gate_json(
            dataset.records,
            as_of,
            args.min_evidence_urls,
            args.max_review_age_days,
            args.max_evidence_age_days,
            args.max_broker_age_days,
            args.profile,
        )
        print(dump_json(payload), end="")
    else:
        payload = quality_gate_json(
            dataset.records,
            as_of,
            args.min_evidence_urls,
            args.max_review_age_days,
            args.max_evidence_age_days,
            args.max_broker_age_days,
            args.profile,
        )
        print(
            quality_gate_markdown(
                dataset.records,
                as_of,
                args.min_evidence_urls,
                args.max_review_age_days,
                args.max_evidence_age_days,
                args.max_broker_age_days,
                args.profile,
            ),
            end="",
        )
    return 0 if payload["ok"] else 1


def cmd_broker_matrix(args: argparse.Namespace) -> int:
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(broker_matrix_json(dataset.records, as_of, args.stale_after_days)), end="")
    else:
        print(broker_matrix_markdown(dataset.records, as_of, args.stale_after_days), end="")
    return 0


def cmd_source_pack(args: argparse.Namespace) -> int:
    if args.fresh_after_days < 0:
        raise ValueError("--fresh-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(source_pack_json(dataset.records, as_of, args.fresh_after_days)), end="")
    elif args.format == "csv":
        print(source_pack_csv(dataset.records, as_of, args.fresh_after_days), end="")
    else:
        print(source_pack_markdown(dataset.records, as_of, args.fresh_after_days), end="")
    return 0


def cmd_watchlist(args: argparse.Namespace) -> int:
    if args.days < 0:
        raise ValueError("--days must be non-negative")
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(watchlist_json(dataset.records, as_of, args.days, args.stale_after_days)), end="")
    else:
        print(watchlist_markdown(dataset.records, as_of, args.days, args.stale_after_days), end="")
    return 0


def cmd_decision_log(args: argparse.Namespace) -> int:
    if args.days < 0:
        raise ValueError("--days must be non-negative")
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(decision_log_json(dataset.records, as_of, args.days, args.stale_after_days)), end="")
    else:
        print(decision_log_markdown(dataset.records, as_of, args.days, args.stale_after_days), end="")
    return 0


def cmd_drilldown(args: argparse.Namespace) -> int:
    if args.days < 0:
        raise ValueError("--days must be non-negative")
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    if args.fresh_after_days < 0:
        raise ValueError("--fresh-after-days must be non-negative")
    if args.broker_stale_after_days < 0:
        raise ValueError("--broker-stale-after-days must be non-negative")
    if args.review_after_days < 0:
        raise ValueError("--review-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(
            dump_json(
                drilldown_json(
                    dataset.records,
                    as_of,
                    args.ticker,
                    args.days,
                    args.stale_after_days,
                    args.fresh_after_days,
                    args.broker_stale_after_days,
                    args.review_after_days,
                )
            ),
            end="",
        )
    else:
        print(
            drilldown_markdown(
                dataset.records,
                as_of,
                args.ticker,
                args.days,
                args.stale_after_days,
                args.fresh_after_days,
                args.broker_stale_after_days,
                args.review_after_days,
            ),
            end="",
        )
    return 0


def cmd_command_cookbook(args: argparse.Namespace) -> int:
    if args.days < 0:
        raise ValueError("--days must be non-negative")
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    dataset_path = args.dataset_path or ("dataset.json" if args.input == "-" else args.input)
    print(command_cookbook_markdown(dataset, as_of, dataset_path, args.output_dir, args.days, args.stale_after_days), end="")
    return 0


def cmd_agent_handoff(args: argparse.Namespace) -> int:
    if args.days < 0:
        raise ValueError("--days must be non-negative")
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    if args.fresh_after_days < 0:
        raise ValueError("--fresh-after-days must be non-negative")
    if args.top_limit < 1:
        raise ValueError("--top-limit must be at least 1")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    dataset_path = args.dataset_path or ("dataset.json" if args.input == "-" else args.input)
    if args.format == "json":
        print(
            dump_json(
                agent_handoff_json(
                    dataset,
                    as_of,
                    dataset_path,
                    args.output_dir,
                    args.days,
                    args.stale_after_days,
                    args.fresh_after_days,
                    args.top_limit,
                )
            ),
            end="",
        )
    else:
        print(
            agent_handoff_markdown(
                dataset,
                as_of,
                dataset_path,
                args.output_dir,
                args.days,
                args.stale_after_days,
                args.fresh_after_days,
                args.top_limit,
            ),
            end="",
        )
    return 0


def cmd_post_event(args: argparse.Namespace) -> int:
    if args.review_after_days < 0:
        raise ValueError("--review-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    if args.format == "json":
        print(dump_json(post_event_json(dataset.records, as_of, args.review_after_days)), end="")
    else:
        print(post_event_markdown(dataset.records, as_of, args.review_after_days), end="")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    base = load_dataset(args.base)
    current = load_dataset(args.current)
    as_of = date.fromisoformat(args.as_of) if args.as_of else current.as_of
    if args.format == "json":
        text = dump_json(compare_snapshots_json(base, current, as_of, args.stale_after_days))
    else:
        text = compare_snapshots_markdown(base, current, as_of, args.stale_after_days)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    if len(args.inputs) < 2:
        raise ValueError("merge requires at least two input datasets")
    raw_datasets = [read_json(path) for path in args.inputs]
    labels = [_source_label(path, index) for index, path in enumerate(args.inputs)]
    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    payload = merge_datasets_json(raw_datasets, labels, as_of, args.prefer_newer_status_history)
    text = dump_json(payload)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if payload["merge"]["validation"]["ok"] else 1


def cmd_html_dashboard(args: argparse.Namespace) -> int:
    if args.days < 0:
        raise ValueError("--days must be non-negative")
    if args.stale_after_days < 0:
        raise ValueError("--stale-after-days must be non-negative")
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    text = html_dashboard(dataset.records, as_of, args.days, args.stale_after_days)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_export_demo(args: argparse.Namespace) -> int:
    data = DEMO_DATA if args.snapshot == "base" else DEMO_UPDATED_DATA
    text = dump_json(data)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_demo_bundle(args: argparse.Namespace) -> int:
    manifest = create_demo_bundle(args.output_dir)
    print(
        dump_json(
            {
                "bundle_dir": args.output_dir,
                "file_count": len(manifest["files"]),
                "manifest": "manifest.json",
                "ok": True,
            }
        ),
        end="",
    )
    return 0


def cmd_fixture_gallery(args: argparse.Namespace) -> int:
    text = dump_json(bundled_fixture_gallery_json()) if args.format == "json" else bundled_fixture_gallery_markdown()
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_export_csv(args: argparse.Namespace) -> int:
    text = dataset_to_csv(load_dataset(args.input))
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_export_ics(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    as_of = resolve_as_of(dataset, args.as_of)
    records = upcoming_records(dataset.records, as_of, args.days)
    text = records_to_ics(records, as_of)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8", newline="")
    else:
        print(text, end="")
    return 0


def cmd_import_csv(args: argparse.Namespace) -> int:
    text = dump_json(csv_to_dataset_json(read_text(args.input)))
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_create_archive(args: argparse.Namespace) -> int:
    manifest = create_archive(args.input, args.output_dir, args.as_of, args.days, args.stale_after_days)
    print(
        dump_json(
            {
                "archive_dir": args.output_dir,
                "file_count": len(manifest["files"]),
                "manifest": "manifest.json",
                "ok": True,
            }
        ),
        end="",
    )
    return 0


def cmd_verify_archive(args: argparse.Namespace) -> int:
    report = verify_archive(args.archive_dir)
    print(dump_json(report), end="")
    return 0 if report["ok"] else 1


def cmd_release_audit(args: argparse.Namespace) -> int:
    report = release_audit_json(Path(args.root))
    if args.format == "json":
        print(dump_json(report), end="")
    else:
        print(release_audit_markdown(report), end="")
    return 0 if report["ok"] else 1


def cmd_changelog(args: argparse.Namespace) -> int:
    payload = changelog_json(Path(args.repo), args.since_tag, args.to_ref, args.include_merges)
    text = dump_json(payload) if args.format == "json" else changelog_markdown(payload)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_smoke_matrix(args: argparse.Namespace) -> int:
    if args.probe:
        print(dump_json(smoke_probe_json()), end="")
        return 0
    report = smoke_matrix_json(args.format)
    if args.format == "json":
        print(dump_json(report), end="")
    else:
        print(smoke_matrix_markdown(report), end="")
    return 0 if report["ok"] else 1


def write_records(records: Iterable[CatalystRecord], as_of: date, fmt: str) -> None:
    if fmt == "json":
        print(dump_json(records_json(records, as_of)), end="")
    else:
        print(brief_markdown(records, as_of, title="Market Catalyst Records"), end="")


def resolve_as_of(dataset: Dataset, override: Optional[str]) -> date:
    if override:
        return date.fromisoformat(override)
    return dataset.as_of


def upcoming_records(records: Iterable[CatalystRecord], as_of: date, days: int) -> List[CatalystRecord]:
    return [
        record
        for record in records
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]


def _source_label(path: str, index: int) -> str:
    if path == "-":
        return f"stdin-{index}"
    return Path(path).name
