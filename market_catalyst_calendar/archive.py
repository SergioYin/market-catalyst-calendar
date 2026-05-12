"""Portable archive creation and verification."""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .csv_io import dataset_to_csv
from .dashboard import html_dashboard
from .evidence import evidence_audit_json, evidence_audit_markdown
from .ics import records_to_ics
from .io import dump_json, read_json
from .models import Dataset, parse_dataset, sorted_records, validation_errors
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


MANIFEST_NAME = "manifest.json"
ARCHIVE_VERSION = 1


def create_archive(
    input_path: Optional[str],
    output_dir: str,
    as_of_override: Optional[str] = None,
    days: int = 45,
    stale_after_days: int = 14,
) -> Dict[str, object]:
    """Create a deterministic archive directory and return its manifest."""

    destination = Path(output_dir)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"archive output directory must be empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    raw = read_json(input_path)
    dataset = parse_dataset(raw)
    errors = validation_errors(dataset)
    if errors:
        raise ValueError("dataset validation failed: " + "; ".join(errors))

    as_of = dataset.as_of if as_of_override is None else date.fromisoformat(as_of_override)
    upcoming = _upcoming_records(dataset, as_of, days)
    stale = [
        record
        for record in dataset.records
        if score_record(record, as_of, stale_after_days=stale_after_days).review_state == "stale"
    ]

    files = {
        "dataset/dataset.json": dump_json(raw),
        "dataset/dataset.csv": dataset_to_csv(dataset),
        "reports/upcoming.json": dump_json(records_json(upcoming, as_of)),
        "reports/stale.json": dump_json(records_json(stale, as_of)),
        "reports/brief.md": brief_markdown(upcoming, as_of),
        "reports/broker_matrix.json": dump_json(broker_matrix_json(dataset.records, as_of, 30)),
        "reports/broker_matrix.md": broker_matrix_markdown(dataset.records, as_of, 30),
        "reports/decision_log.json": dump_json(decision_log_json(dataset.records, as_of, days, stale_after_days)),
        "reports/decision_log.md": decision_log_markdown(dataset.records, as_of, days, stale_after_days),
        "reports/upcoming.ics": records_to_ics(upcoming, as_of),
        "reports/exposure.json": dump_json(exposure_json(upcoming, as_of)),
        "reports/exposure.md": exposure_markdown(upcoming, as_of),
        "reports/post_event.json": dump_json(post_event_json(dataset.records, as_of, 0)),
        "reports/post_event.md": post_event_markdown(dataset.records, as_of, 0),
        "reports/review_plan.json": dump_json(review_plan_json(dataset.records, as_of, days, stale_after_days)),
        "reports/review_plan.md": review_plan_markdown(dataset.records, as_of, days, stale_after_days),
        "reports/risk_budget.json": dump_json(risk_budget_json(upcoming, as_of)),
        "reports/risk_budget.md": risk_budget_markdown(upcoming, as_of),
        "reports/scenario_matrix.json": dump_json(scenario_matrix_json(upcoming, as_of, stale_after_days)),
        "reports/scenario_matrix.md": scenario_matrix_markdown(upcoming, as_of, stale_after_days),
        "reports/sector_map.json": dump_json(sector_map_json(dataset.records, as_of, stale_after_days)),
        "reports/sector_map.md": sector_map_markdown(dataset.records, as_of, stale_after_days),
        "reports/source_pack.csv": source_pack_csv(dataset.records, as_of, stale_after_days),
        "reports/source_pack.json": dump_json(source_pack_json(dataset.records, as_of, stale_after_days)),
        "reports/source_pack.md": source_pack_markdown(dataset.records, as_of, stale_after_days),
        "reports/thesis_map.json": dump_json(thesis_map_json(dataset.records, as_of, stale_after_days)),
        "reports/thesis_map.md": thesis_map_markdown(dataset.records, as_of, stale_after_days),
        "reports/watchlist.json": dump_json(watchlist_json(dataset.records, as_of, days, stale_after_days)),
        "reports/watchlist.md": watchlist_markdown(dataset.records, as_of, days, stale_after_days),
        "reports/evidence_audit.json": dump_json(evidence_audit_json(dataset.records, as_of, stale_after_days, 2, 0.67)),
        "reports/evidence_audit.md": evidence_audit_markdown(dataset.records, as_of, stale_after_days, 2, 0.67),
        "reports/dashboard.html": html_dashboard(dataset.records, as_of, days, stale_after_days),
    }
    for relative_path, text in sorted(files.items()):
        _write_text(destination / relative_path, text)

    manifest = _build_manifest(destination, sorted(files), dataset, as_of.isoformat(), days, stale_after_days)
    _write_text(destination / MANIFEST_NAME, dump_json(manifest))
    return manifest


def verify_archive(archive_dir: str) -> Dict[str, object]:
    """Verify manifest entries and return a deterministic verification report."""

    root = Path(archive_dir)
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        return _verification_report(root, False, [f"missing {MANIFEST_NAME}"], [], [])

    manifest = read_json(str(manifest_path))
    errors: List[str] = []
    if manifest.get("archive_version") != ARCHIVE_VERSION:
        errors.append(f"unsupported archive_version: {manifest.get('archive_version')}")
    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, list):
        errors.append("manifest.files must be a list")
        return _verification_report(root, False, errors, [], [])

    checked: List[str] = []
    expected_paths = set()
    for index, item in enumerate(manifest_files):
        if not isinstance(item, dict):
            errors.append(f"files[{index}] must be an object")
            continue
        relative_path = item.get("path")
        expected_sha = item.get("sha256")
        expected_bytes = item.get("bytes")
        if not isinstance(relative_path, str) or not isinstance(expected_sha, str) or not isinstance(expected_bytes, int):
            errors.append(f"files[{index}] must include path, bytes, and sha256")
            continue
        if Path(relative_path).is_absolute() or ".." in Path(relative_path).parts:
            errors.append(f"unsafe manifest path: {relative_path}")
            continue
        expected_paths.add(relative_path)
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing file: {relative_path}")
            continue
        digest, byte_count = _hash_file(path)
        checked.append(relative_path)
        if byte_count != expected_bytes:
            errors.append(f"byte count mismatch: {relative_path}")
        if digest != expected_sha:
            errors.append(f"sha256 mismatch: {relative_path}")

    actual_paths = set(_archive_files(root))
    extra = sorted(actual_paths - expected_paths)
    for relative_path in extra:
        errors.append(f"untracked file: {relative_path}")

    return _verification_report(root, not errors, errors, sorted(checked), extra)


def _build_manifest(
    root: Path,
    relative_paths: Iterable[str],
    dataset: Dataset,
    as_of: str,
    days: int,
    stale_after_days: int,
) -> Dict[str, object]:
    files = []
    for relative_path in relative_paths:
        digest, byte_count = _hash_file(root / relative_path)
        files.append({"bytes": byte_count, "path": relative_path, "sha256": digest})
    return {
        "archive_version": ARCHIVE_VERSION,
        "as_of": as_of,
        "dataset": {
            "record_count": len(dataset.records),
            "record_ids": [record.record_id for record in sorted_records(dataset.records)],
        },
        "files": files,
        "parameters": {
            "days": days,
            "evidence_fresh_after_days": stale_after_days,
            "evidence_max_domain_share": 0.67,
            "evidence_min_sources": 2,
            "broker_stale_after_days": 30,
            "stale_after_days": stale_after_days,
        },
    }


def _upcoming_records(dataset: Dataset, as_of: date, days: int):
    return [
        record
        for record in dataset.records
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]


def _archive_files(root: Path) -> List[str]:
    if not root.is_dir():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() != MANIFEST_NAME
    )


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


def _verification_report(
    root: Path,
    ok: bool,
    errors: List[str],
    checked_files: List[str],
    extra_files: List[str],
) -> Dict[str, object]:
    return {
        "archive_dir": str(root),
        "checked_files": checked_files,
        "errors": sorted(errors),
        "extra_files": extra_files,
        "ok": ok,
    }
