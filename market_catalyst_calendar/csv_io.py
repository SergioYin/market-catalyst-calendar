"""Deterministic CSV import/export for catalyst datasets."""

from __future__ import annotations

import csv
import io
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote, unquote

from .models import CatalystRecord, Dataset, parse_dataset, sorted_records


CSV_COLUMNS = [
    "as_of",
    "id",
    "ticker",
    "entity",
    "event_type",
    "window_start",
    "window_end",
    "confidence",
    "position_size",
    "portfolio_weight",
    "thesis_id",
    "source_ref",
    "status",
    "thesis_impact",
    "required_review_action",
    "last_reviewed",
    "evidence_checked_at",
    "actual_outcome",
    "outcome_recorded_at",
    "evidence_urls",
    "scenario_notes",
    "history",
    "broker_views",
]

REQUIRED_CSV_COLUMNS = [
    column
    for column in CSV_COLUMNS
    if column
    not in {
        "position_size",
        "portfolio_weight",
        "thesis_id",
        "source_ref",
        "evidence_checked_at",
        "actual_outcome",
        "outcome_recorded_at",
        "broker_views",
    }
]

ITEM_SEPARATOR = " | "
PART_SEPARATOR = " = "


def dataset_to_csv(dataset: Dataset) -> str:
    """Render a dataset as deterministic CSV."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for record in sorted_records(dataset.records):
        writer.writerow(_record_to_row(dataset.as_of.isoformat(), record))
    return output.getvalue()


def csv_to_dataset_json(text: str) -> Dict[str, object]:
    """Parse CSV text into the canonical JSON dataset shape."""
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV must include a header row")
    missing = [column for column in REQUIRED_CSV_COLUMNS if column not in reader.fieldnames]
    if missing:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing))

    as_of = None
    records: List[Dict[str, object]] = []
    for index, row in enumerate(reader, start=2):
        row_as_of = _required_cell(row, "as_of", index)
        if as_of is None:
            as_of = row_as_of
        elif row_as_of != as_of:
            raise ValueError(f"row {index}: as_of must match first row ({as_of})")
        records.append(_row_to_record(row, index))
    if as_of is None:
        raise ValueError("CSV must include at least one record row")

    raw = {"as_of": as_of, "records": records}
    parse_dataset(raw)
    return raw


def _record_to_row(as_of: str, record: CatalystRecord) -> Dict[str, str]:
    return {
        "as_of": as_of,
        "id": record.record_id,
        "ticker": record.ticker,
        "entity": record.entity,
        "event_type": record.event_type,
        "window_start": record.window.start.isoformat(),
        "window_end": record.window.end.isoformat(),
        "confidence": _format_confidence(record.confidence),
        "position_size": _format_optional_number(record.position_size),
        "portfolio_weight": _format_optional_number(record.portfolio_weight),
        "thesis_id": record.thesis_id or "",
        "source_ref": record.source_ref or "",
        "status": record.status,
        "thesis_impact": record.thesis_impact,
        "required_review_action": record.required_review_action,
        "last_reviewed": record.last_reviewed.isoformat() if record.last_reviewed else "",
        "evidence_checked_at": record.evidence_checked_at.isoformat() if record.evidence_checked_at else "",
        "actual_outcome": record.actual_outcome or "",
        "outcome_recorded_at": record.outcome_recorded_at.isoformat() if record.outcome_recorded_at else "",
        "evidence_urls": _join_items(record.evidence_urls),
        "scenario_notes": _join_pairs(sorted(record.scenario_notes.items())),
        "history": _join_history(record.history),
        "broker_views": _join_broker_views(record.broker_views),
    }


def _row_to_record(row: Dict[str, str], row_number: int) -> Dict[str, object]:
    window_start = _required_cell(row, "window_start", row_number)
    window_end = _required_cell(row, "window_end", row_number)
    record: Dict[str, object] = {
        "id": _required_cell(row, "id", row_number),
        "ticker": _required_cell(row, "ticker", row_number),
        "entity": _required_cell(row, "entity", row_number),
        "event_type": _required_cell(row, "event_type", row_number),
        "confidence": _parse_float(_required_cell(row, "confidence", row_number), row_number),
        "position_size": _parse_optional_float(row.get("position_size", ""), row_number, "position_size"),
        "portfolio_weight": _parse_optional_float(row.get("portfolio_weight", ""), row_number, "portfolio_weight"),
        "thesis_id": _optional_cell(row, "thesis_id"),
        "source_ref": _optional_cell(row, "source_ref"),
        "status": _required_cell(row, "status", row_number),
        "thesis_impact": _required_cell(row, "thesis_impact", row_number),
        "evidence_urls": _split_items(row.get("evidence_urls", "")),
        "scenario_notes": dict(_split_pairs(row.get("scenario_notes", ""), row_number, "scenario_notes")),
        "required_review_action": _required_cell(row, "required_review_action", row_number),
        "history": _split_history(row.get("history", ""), row_number),
        "broker_views": _split_broker_views(row.get("broker_views", ""), row_number),
    }
    if window_start == window_end:
        record["date"] = window_start
    else:
        record["window"] = {"start": window_start, "end": window_end}
    last_reviewed = (row.get("last_reviewed") or "").strip()
    if last_reviewed:
        record["last_reviewed"] = last_reviewed
    evidence_checked_at = (row.get("evidence_checked_at") or "").strip()
    if evidence_checked_at:
        record["evidence_checked_at"] = evidence_checked_at
    actual_outcome = (row.get("actual_outcome") or "").strip()
    if actual_outcome:
        record["actual_outcome"] = actual_outcome
    outcome_recorded_at = (row.get("outcome_recorded_at") or "").strip()
    if outcome_recorded_at:
        record["outcome_recorded_at"] = outcome_recorded_at
    return record


def _format_confidence(value: float) -> str:
    return f"{value:.12g}"


def _format_optional_number(value: Optional[float]) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def _encode(value: str) -> str:
    return quote(value, safe="")


def _decode(value: str) -> str:
    return unquote(value)


def _join_items(values: Iterable[str]) -> str:
    return ITEM_SEPARATOR.join(_encode(value) for value in values)


def _split_items(value: str) -> List[str]:
    if not value:
        return []
    return [_decode(part) for part in value.split(ITEM_SEPARATOR)]


def _join_pairs(values: Iterable[tuple[str, str]]) -> str:
    return ITEM_SEPARATOR.join(_encode(key) + PART_SEPARATOR + _encode(value) for key, value in values)


def _split_pairs(value: str, row_number: int, field: str) -> List[tuple[str, str]]:
    if not value:
        return []
    pairs: List[tuple[str, str]] = []
    for item in value.split(ITEM_SEPARATOR):
        parts = item.split(PART_SEPARATOR)
        if len(parts) != 2:
            raise ValueError(f"row {row_number}: malformed {field} item")
        pairs.append((_decode(parts[0]), _decode(parts[1])))
    return pairs


def _join_history(values) -> str:
    rows = []
    for entry in values:
        rows.append(
            PART_SEPARATOR.join(
                [
                    _encode(entry.date.isoformat()),
                    _encode(entry.status),
                    _encode(entry.note),
                ]
            )
        )
    return ITEM_SEPARATOR.join(rows)


def _split_history(value: str, row_number: int) -> List[Dict[str, str]]:
    if not value:
        return []
    entries = []
    for item in value.split(ITEM_SEPARATOR):
        parts = item.split(PART_SEPARATOR)
        if len(parts) != 3:
            raise ValueError(f"row {row_number}: malformed history item")
        entries.append({"date": _decode(parts[0]), "status": _decode(parts[1]), "note": _decode(parts[2])})
    return entries


def _join_broker_views(values) -> str:
    rows = []
    for view in values:
        rows.append(
            PART_SEPARATOR.join(
                [
                    _encode(view.institution),
                    _encode(view.rating),
                    _encode(f"{view.target_price:.12g}"),
                    _encode(view.as_of.isoformat()),
                    _encode(view.source_url),
                    _encode(view.caveat),
                ]
            )
        )
    return ITEM_SEPARATOR.join(rows)


def _split_broker_views(value: str, row_number: int) -> List[Dict[str, object]]:
    if not value:
        return []
    views: List[Dict[str, object]] = []
    for item in value.split(ITEM_SEPARATOR):
        parts = item.split(PART_SEPARATOR)
        if len(parts) != 6:
            raise ValueError(f"row {row_number}: malformed broker_views item")
        views.append(
            {
                "institution": _decode(parts[0]),
                "rating": _decode(parts[1]),
                "target_price": _parse_optional_float(_decode(parts[2]), row_number, "broker_views.target_price"),
                "as_of": _decode(parts[3]),
                "source_url": _decode(parts[4]),
                "caveat": _decode(parts[5]),
            }
        )
    return views


def _required_cell(row: Dict[str, str], column: str, row_number: int) -> str:
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(f"row {row_number}: {column} is required")
    return value


def _optional_cell(row: Dict[str, str], column: str) -> Optional[str]:
    value = (row.get(column) or "").strip()
    if not value:
        return None
    return value


def _parse_float(value: str, row_number: int) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"row {row_number}: confidence must be a number") from exc


def _parse_optional_float(value: str, row_number: int, column: str) -> Optional[float]:
    stripped = (value or "").strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError as exc:
        raise ValueError(f"row {row_number}: {column} must be a number") from exc
