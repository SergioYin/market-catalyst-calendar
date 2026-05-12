"""Deterministic iCalendar export."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Iterable, List

from .models import CatalystRecord, sorted_records
from .scoring import score_record


PRODID = "-//market-catalyst-calendar//EN"


def records_to_ics(records: Iterable[CatalystRecord], as_of: date) -> str:
    """Render records as a deterministic all-day iCalendar feed."""

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Market Catalyst Calendar",
        f"X-MARKET-CATALYST-AS-OF:{_date_value(as_of)}",
    ]
    for record in sorted_records(records):
        lines.extend(_event_lines(record, as_of))
    lines.append("END:VCALENDAR")
    return "".join(_fold_line(line) for line in lines)


def _event_lines(record: CatalystRecord, as_of: date) -> List[str]:
    score = score_record(record, as_of)
    description = [
        f"Record: {record.record_id}",
        f"Entity: {record.entity}",
        f"Window: {record.window.label}",
        f"Status: {record.status}",
        f"Thesis impact: {record.thesis_impact}",
        f"Confidence: {record.confidence:.2f}",
        f"Catalyst score: {score.catalyst_score}",
        f"Urgency: {score.urgency}",
        f"Review: {score.review_state}",
        f"Required action: {record.required_review_action}",
        f"Base scenario: {record.scenario_notes.get('base', '')}",
    ]
    if record.source_ref:
        description.append(f"Source note: {record.source_ref}")
    if record.evidence_urls:
        description.append("Source URLs:")
        description.extend(f"- {url}" for url in record.evidence_urls)

    categories = [
        "market-catalyst",
        record.ticker,
        record.event_type,
        record.status,
        record.thesis_impact,
        score.urgency,
    ]
    if record.thesis_id:
        categories.append(record.thesis_id)

    lines = [
        "BEGIN:VEVENT",
        f"UID:{_uid(record)}",
        f"DTSTAMP:{_datetime_value(as_of)}",
        f"DTSTART;VALUE=DATE:{_date_value(record.window.start)}",
        f"DTEND;VALUE=DATE:{_date_value(record.window.end + timedelta(days=1))}",
        f"SUMMARY:{_escape_text(_summary(record))}",
        f"DESCRIPTION:{_escape_text(chr(10).join(description))}",
        "CATEGORIES:" + ",".join(_escape_text(category) for category in categories if category),
        f"STATUS:{_calendar_status(record.status)}",
    ]
    if record.evidence_urls:
        lines.append(f"URL:{_escape_uri(record.evidence_urls[0])}")
    lines.append("END:VEVENT")
    return lines


def _summary(record: CatalystRecord) -> str:
    event = record.event_type.replace("_", " ")
    return f"{record.ticker} {event}: {record.entity}"


def _uid(record: CatalystRecord) -> str:
    basis = "|".join(
        [
            record.record_id,
            record.ticker,
            record.event_type,
            record.window.start.isoformat(),
            record.window.end.isoformat(),
        ]
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]
    return f"{record.record_id}-{digest}@market-catalyst-calendar"


def _calendar_status(status: str) -> str:
    if status == "cancelled":
        return "CANCELLED"
    if status in {"confirmed", "scheduled", "completed"}:
        return "CONFIRMED"
    return "TENTATIVE"


def _date_value(value: date) -> str:
    return value.strftime("%Y%m%d")


def _datetime_value(value: date) -> str:
    return value.strftime("%Y%m%dT000000Z")


def _escape_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _escape_uri(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\r", "").replace("\n", "")


def _fold_line(line: str) -> str:
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line + "\r\n"

    chunks: List[str] = []
    current = ""
    current_bytes = 0
    limit = 75
    for char in line:
        char_bytes = len(char.encode("utf-8"))
        if current and current_bytes + char_bytes > limit:
            chunks.append(current)
            current = " " + char
            current_bytes = 1 + char_bytes
            limit = 75
        else:
            current += char
            current_bytes += char_bytes
    chunks.append(current)
    return "\r\n".join(chunks) + "\r\n"
