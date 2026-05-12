"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

from .archive import create_archive, verify_archive
from .csv_io import csv_to_dataset_json, dataset_to_csv
from .dashboard import html_dashboard
from .demo import DEMO_DATA
from .evidence import evidence_audit_json, evidence_audit_markdown
from .ics import records_to_ics
from .io import dump_json, load_dataset, read_text
from .models import CatalystRecord, Dataset, parse_dataset, validation_errors
from .render import (
    brief_markdown,
    broker_matrix_json,
    broker_matrix_markdown,
    decision_log_json,
    decision_log_markdown,
    exposure_json,
    exposure_markdown,
    post_event_json,
    post_event_markdown,
    records_json,
    review_plan_json,
    review_plan_markdown,
    scenario_matrix_json,
    scenario_matrix_markdown,
    source_pack_csv,
    source_pack_json,
    source_pack_markdown,
    thesis_map_json,
    thesis_map_markdown,
    watchlist_json,
    watchlist_markdown,
)
from .scoring import score_record


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

    post_event = subparsers.add_parser("post-event", help="render post-event outcome review templates")
    add_input(post_event)
    add_as_of(post_event)
    post_event.add_argument("--review-after-days", type=int, default=0, help="days after event window end before outcome review is due")
    post_event.add_argument("--format", choices=["json", "markdown"], default="json")
    post_event.set_defaults(func=cmd_post_event)

    html = subparsers.add_parser("html-dashboard", help="render a deterministic static HTML dashboard")
    add_input(html)
    add_as_of(html)
    html.add_argument("--days", type=int, default=45, help="look-ahead window in days")
    html.add_argument("--stale-after-days", type=int, default=14)
    html.add_argument("--output", "-o", help="output HTML path; stdout when omitted")
    html.set_defaults(func=cmd_html_dashboard)

    demo = subparsers.add_parser("export-demo", help="write the built-in demo dataset")
    demo.add_argument("--output", "-o", help="output path; stdout when omitted")
    demo.set_defaults(func=cmd_export_demo)

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
    return parser


def add_input(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--input", "-i", default="-", help="input JSON path; defaults to stdin")


def add_as_of(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--as-of", help="ISO date override; defaults to dataset as_of")


def cmd_validate(args: argparse.Namespace) -> int:
    dataset = load_dataset(args.input)
    errors = validation_errors(dataset)
    if errors:
        print(dump_json({"ok": False, "errors": errors}), end="")
        return 1
    print(dump_json({"ok": True, "record_count": len(dataset.records)}), end="")
    return 0


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
    text = dump_json(DEMO_DATA)
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
