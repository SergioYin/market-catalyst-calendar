"""Snapshot comparison reports."""

from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, Optional, Tuple

from .models import CatalystRecord, Dataset, sorted_records
from .render import record_to_json
from .scoring import score_record


CORE_FIELDS = (
    "ticker",
    "entity",
    "event_type",
    "window",
    "confidence",
    "required_review_action",
    "last_reviewed",
    "evidence_checked_at",
    "position_size",
    "portfolio_weight",
    "risk_budget",
    "max_loss",
    "sector",
    "theme",
    "thesis_id",
    "source_ref",
    "actual_outcome",
    "outcome_recorded_at",
)


def compare_snapshots_json(
    base: Dataset,
    current: Dataset,
    as_of: date,
    stale_after_days: int,
) -> Dict[str, object]:
    base_by_id = _records_by_id(base.records)
    current_by_id = _records_by_id(current.records)
    base_ids = set(base_by_id)
    current_ids = set(current_by_id)

    added = [current_by_id[record_id] for record_id in sorted(current_ids - base_ids)]
    removed = [base_by_id[record_id] for record_id in sorted(base_ids - current_ids)]
    changed = [
        _changed_record(base_by_id[record_id], current_by_id[record_id], as_of, stale_after_days)
        for record_id in sorted(base_ids & current_ids)
    ]
    changed = [item for item in changed if _has_change(item)]

    return {
        "as_of": as_of.isoformat(),
        "base_as_of": base.as_of.isoformat(),
        "current_as_of": current.as_of.isoformat(),
        "stale_after_days": stale_after_days,
        "added": [_record_snapshot(record, as_of) for record in sorted_records(added)],
        "removed": [_record_snapshot(record, as_of) for record in sorted_records(removed)],
        "changed": changed,
        "summary": {
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
            "score_change_count": sum(1 for item in changed if item["score_change"]["delta"] != 0),
            "status_transition_count": sum(1 for item in changed if item["status_transition"] is not None),
            "evidence_change_count": sum(1 for item in changed if item["evidence_change"]["changed"]),
            "thesis_impact_change_count": sum(1 for item in changed if item["thesis_impact_change"] is not None),
        },
    }


def compare_snapshots_markdown(
    base: Dataset,
    current: Dataset,
    as_of: date,
    stale_after_days: int,
) -> str:
    payload = compare_snapshots_json(base, current, as_of, stale_after_days)
    summary = payload["summary"]  # type: ignore[index]
    lines = [
        "# Market Catalyst Snapshot Compare",
        "",
        f"As of: {payload['as_of']}",
        f"Base snapshot: {payload['base_as_of']}",
        f"Current snapshot: {payload['current_as_of']}",
        "",
        (
            "Summary: "
            f"{summary['added_count']} added, "
            f"{summary['removed_count']} removed, "
            f"{summary['changed_count']} changed, "
            f"{_count_label(int(summary['score_change_count']), 'score change')}, "
            f"{_count_label(int(summary['status_transition_count']), 'status transition')}, "
            f"{_count_label(int(summary['evidence_change_count']), 'evidence change')}, "
            f"{_count_label(int(summary['thesis_impact_change_count']), 'thesis-impact change')}."
        ),
        "",
    ]
    _append_record_table(lines, "Added Events", payload["added"])  # type: ignore[arg-type]
    _append_record_table(lines, "Removed Events", payload["removed"])  # type: ignore[arg-type]
    changed = payload["changed"]  # type: ignore[assignment]
    lines.extend(["## Changed Events", ""])
    if not changed:
        lines.extend(["No changed events.", ""])
    else:
        lines.extend(
            [
                "| ID | Ticker | Score Delta | Status | Evidence | Thesis Impact | Fields |",
                "| --- | --- | ---: | --- | --- | --- | --- |",
            ]
        )
        for item in changed:  # type: ignore[union-attr]
            status = item["status_transition"]
            thesis = item["thesis_impact_change"]
            evidence = item["evidence_change"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(item["id"]),
                        str(item["ticker"]),
                        _format_delta(int(item["score_change"]["delta"])),
                        _transition_label(status),
                        f"+{len(evidence['added_urls'])}/-{len(evidence['removed_urls'])}",
                        _transition_label(thesis),
                        ", ".join(str(change["field"]) for change in item["field_changes"]) or "none",
                    ]
                )
                + " |"
            )
        lines.append("")
        for item in changed:  # type: ignore[union-attr]
            lines.extend([f"### {item['ticker']} - {item['id']}", ""])
            score = item["score_change"]
            lines.append(
                f"- Score: {score['from']} -> {score['to']} ({_format_delta(int(score['delta']))}); "
                f"urgency {score['urgency_from']} -> {score['urgency_to']}; "
                f"review {score['review_state_from']} -> {score['review_state_to']}"
            )
            if item["status_transition"]:
                lines.append(f"- Status: {_transition_label(item['status_transition'])}")
            if item["thesis_impact_change"]:
                lines.append(f"- Thesis impact: {_transition_label(item['thesis_impact_change'])}")
            evidence = item["evidence_change"]
            if evidence["changed"]:
                lines.append(
                    "- Evidence: "
                    f"added {', '.join(evidence['added_urls']) or 'none'}; "
                    f"removed {', '.join(evidence['removed_urls']) or 'none'}; "
                    f"checked_at {_transition_label(evidence['checked_at_change'])}"
                )
            if item["field_changes"]:
                lines.append(
                    "- Other fields: "
                    + "; ".join(
                        f"{change['field']} {change['from']} -> {change['to']}" for change in item["field_changes"]
                    )
                )
            broker_changes = item["broker_view_changes"]
            broker_parts = []
            if broker_changes["added_views"]:
                broker_parts.append(
                    "added "
                    + ", ".join(str(view["institution"]) for view in broker_changes["added_views"])
                )
            if broker_changes["removed_views"]:
                broker_parts.append(
                    "removed "
                    + ", ".join(str(view["institution"]) for view in broker_changes["removed_views"])
                )
            if broker_changes["changed_views"]:
                broker_parts.append(
                    "changed "
                    + ", ".join(str(view["institution"]) for view in broker_changes["changed_views"])
                )
            if broker_parts:
                lines.append("- Broker views: " + "; ".join(broker_parts))
            lines.append("")
    return "\n".join(lines)


def _records_by_id(records: Iterable[CatalystRecord]) -> Dict[str, CatalystRecord]:
    return {record.record_id: record for record in records}


def _record_snapshot(record: CatalystRecord, as_of: date) -> Dict[str, object]:
    payload = record_to_json(record, as_of)
    payload["confidence"] = record.confidence
    return payload


def _changed_record(
    base: CatalystRecord,
    current: CatalystRecord,
    as_of: date,
    stale_after_days: int,
) -> Dict[str, object]:
    base_score = score_record(base, as_of, stale_after_days)
    current_score = score_record(current, as_of, stale_after_days)
    return {
        "id": current.record_id,
        "ticker": current.ticker,
        "entity": current.entity,
        "event_type": current.event_type,
        "window": current.window.label,
        "score_change": {
            "from": base_score.catalyst_score,
            "to": current_score.catalyst_score,
            "delta": current_score.catalyst_score - base_score.catalyst_score,
            "urgency_from": base_score.urgency,
            "urgency_to": current_score.urgency,
            "review_state_from": base_score.review_state,
            "review_state_to": current_score.review_state,
        },
        "status_transition": _transition(base.status, current.status),
        "evidence_change": _evidence_change(base, current),
        "thesis_impact_change": _transition(base.thesis_impact, current.thesis_impact),
        "field_changes": _field_changes(base, current),
        "scenario_note_changes": _mapping_changes(base.scenario_notes, current.scenario_notes),
        "history_changes": _history_changes(base, current),
        "broker_view_changes": _broker_view_changes(base, current),
    }


def _has_change(item: Dict[str, object]) -> bool:
    score_change = item["score_change"]  # type: ignore[assignment]
    evidence_change = item["evidence_change"]  # type: ignore[assignment]
    history_changes = item["history_changes"]  # type: ignore[assignment]
    broker_view_changes = item["broker_view_changes"]  # type: ignore[assignment]
    return bool(
        score_change["delta"]  # type: ignore[index]
        or item["status_transition"]
        or evidence_change["changed"]  # type: ignore[index]
        or item["thesis_impact_change"]
        or item["field_changes"]
        or item["scenario_note_changes"]
        or history_changes["added_entries"]  # type: ignore[index]
        or history_changes["removed_entries"]  # type: ignore[index]
        or broker_view_changes["added_views"]  # type: ignore[index]
        or broker_view_changes["removed_views"]  # type: ignore[index]
        or broker_view_changes["changed_views"]  # type: ignore[index]
    )


def _transition(before: object, after: object) -> Optional[Dict[str, object]]:
    if before == after:
        return None
    return {"from": _value(before), "to": _value(after)}


def _evidence_change(base: CatalystRecord, current: CatalystRecord) -> Dict[str, object]:
    before = set(base.evidence_urls)
    after = set(current.evidence_urls)
    checked_at_change = _transition(base.evidence_checked_at, current.evidence_checked_at)
    added = sorted(after - before)
    removed = sorted(before - after)
    return {
        "added_urls": added,
        "removed_urls": removed,
        "unchanged_urls": sorted(before & after),
        "checked_at_change": checked_at_change,
        "changed": bool(added or removed or checked_at_change),
    }


def _field_changes(base: CatalystRecord, current: CatalystRecord) -> List[Dict[str, object]]:
    changes = []
    for field in CORE_FIELDS:
        before = _field_value(base, field)
        after = _field_value(current, field)
        if before != after:
            changes.append({"field": field, "from": before, "to": after})
    return changes


def _field_value(record: CatalystRecord, field: str) -> object:
    if field == "window":
        return record.window.label
    value = getattr(record, field)
    return _value(value)


def _mapping_changes(before: Dict[str, str], after: Dict[str, str]) -> List[Dict[str, object]]:
    changes = []
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            changes.append({"key": key, "from": before.get(key, "missing"), "to": after.get(key, "missing")})
    return changes


def _history_changes(base: CatalystRecord, current: CatalystRecord) -> Dict[str, object]:
    before = [_history_key(entry) for entry in base.history]
    after = [_history_key(entry) for entry in current.history]
    before_set = set(before)
    after_set = set(after)
    return {
        "added_entries": [_history_payload(entry) for entry in after if entry not in before_set],
        "removed_entries": [_history_payload(entry) for entry in before if entry not in after_set],
    }


def _broker_view_changes(base: CatalystRecord, current: CatalystRecord) -> Dict[str, object]:
    before = {_broker_view_key(view): view for view in base.broker_views}
    after = {_broker_view_key(view): view for view in current.broker_views}
    added = [after[key] for key in sorted(set(after) - set(before))]
    removed = [before[key] for key in sorted(set(before) - set(after))]
    changed = []
    for key in sorted(set(before) & set(after)):
        field_changes = []
        for field in ("rating", "target_price", "as_of", "caveat"):
            before_value = _value(getattr(before[key], field))
            after_value = _value(getattr(after[key], field))
            if before_value != after_value:
                field_changes.append({"field": field, "from": before_value, "to": after_value})
        if field_changes:
            changed.append(
                {
                    "institution": key[0],
                    "source_url": key[1],
                    "field_changes": field_changes,
                }
            )
    return {
        "added_views": [_broker_view_payload(view) for view in added],
        "removed_views": [_broker_view_payload(view) for view in removed],
        "changed_views": changed,
    }


def _history_key(entry) -> Tuple[str, str, str]:
    return (entry.date.isoformat(), entry.status, entry.note)


def _history_payload(entry: Tuple[str, str, str]) -> Dict[str, str]:
    return {"date": entry[0], "status": entry[1], "note": entry[2]}


def _broker_view_key(view) -> Tuple[str, str]:
    return (view.institution, view.source_url)


def _broker_view_payload(view) -> Dict[str, object]:
    return {
        "institution": view.institution,
        "rating": view.rating,
        "target_price": view.target_price,
        "as_of": view.as_of.isoformat(),
        "source_url": view.source_url,
        "caveat": view.caveat,
    }


def _value(value: object) -> object:
    if hasattr(value, "isoformat"):
        return value.isoformat()  # type: ignore[no-any-return, union-attr]
    return "missing" if value is None else value


def _append_record_table(lines: List[str], title: str, records: object) -> None:
    lines.extend([f"## {title}", ""])
    if not records:
        lines.extend([f"No {title.lower()}.", ""])
        return
    lines.extend(["| Score | Window | Ticker | Event | Status | Impact | ID |", "| ---: | --- | --- | --- | --- | --- | --- |"])
    for record in records:  # type: ignore[union-attr]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(record["catalyst_score"]),
                    str(record["window"]),
                    str(record["ticker"]),
                    str(record["event_type"]).replace("_", " "),
                    str(record["status"]),
                    str(record["thesis_impact"]),
                    str(record["id"]),
                ]
            )
            + " |"
        )
    lines.append("")


def _transition_label(change: object) -> str:
    if not change:
        return "none"
    return f"{change['from']} -> {change['to']}"  # type: ignore[index]


def _format_delta(value: int) -> str:
    if value > 0:
        return f"+{value}"
    return str(value)


def _count_label(count: int, label: str) -> str:
    suffix = "" if count == 1 else "s"
    return f"{count} {label}{suffix}"
