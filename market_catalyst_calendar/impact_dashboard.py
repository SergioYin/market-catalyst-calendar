"""Static impact dashboard summaries from datasets or impact briefs."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Optional

from .impact_brief import BOUNDARY, BOUNDARY_NOTE, impact_brief_json
from .models import parse_dataset


def impact_dashboard_json(
    raw: Dict[str, Any],
    as_of: Optional[date],
    days: int,
    stale_after_days: int,
    top_limit: int,
) -> Dict[str, object]:
    """Return a compact static impact dashboard summary."""

    brief, input_type = _normalize_impact_brief(raw, as_of, days, stale_after_days)
    records = [_normalize_record(record) for record in brief["records"]]
    evidence_counts = _counts(str(record.get("evidence_state", "unknown")) for record in records)
    flag_counts = _counts(flag for record in records for flag in record["impact_flags"])
    review_queue = [
        _review_item(record)
        for record in records
        if record.get("review_state") in {"stale", "needs_review"}
        or str(record.get("required_review_action", "none")) != "none"
        or "missing_evidence_freshness" in record["impact_flags"]
    ]
    review_queue.sort(key=lambda item: (-_int_field(item, "attention_score"), _int_field(item, "days_until"), str(item["ticker"]), str(item["id"])))

    return {
        "schema_version": "impact-dashboard/v1",
        "input_type": input_type,
        "as_of": str(brief.get("as_of", "missing")),
        "horizon": {
            "as_of": str(brief.get("as_of", "missing")),
            "days": int(brief.get("days", days)),
            "stale_after_days": int(brief.get("stale_after_days", stale_after_days)),
        },
        "boundary_note": BOUNDARY_NOTE,
        "boundary": dict(BOUNDARY),
        "summary": {
            "total_upcoming_items": len(records),
            "evidence_state_counts": evidence_counts,
            "impact_flag_counts": flag_counts,
            "review_queue_count": len(review_queue),
            "top_attention_count": min(top_limit, len(records)),
        },
        "top_attention_catalysts": [_attention_item(record) for record in _top_attention(records, top_limit)],
        "review_queue": review_queue,
    }


def impact_dashboard_markdown(
    raw: Dict[str, Any],
    as_of: Optional[date],
    days: int,
    stale_after_days: int,
    top_limit: int,
) -> str:
    """Render a static impact dashboard panel as Markdown."""

    payload = impact_dashboard_json(raw, as_of, days, stale_after_days, top_limit)
    summary = payload["summary"]  # type: ignore[index]
    horizon = payload["horizon"]  # type: ignore[index]
    lines = [
        "# Market Catalyst Impact Dashboard",
        "",
        f"As of: {payload['as_of']}",
        f"Horizon: {horizon['days']} days; stale after {horizon['stale_after_days']} days.",
        f"Input: {payload['input_type']}",
        "",
        f"Boundary: {payload['boundary_note']}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Total upcoming items | {summary['total_upcoming_items']} |",
        f"| Review queue | {summary['review_queue_count']} |",
        f"| Top attention catalysts | {summary['top_attention_count']} |",
        "",
        "## Evidence State Counts",
        "",
    ]
    _append_counts(lines, summary["evidence_state_counts"])  # type: ignore[index]
    lines.extend(["## Impact Flag Counts", ""])
    _append_counts(lines, summary["impact_flag_counts"])  # type: ignore[index]
    lines.extend(
        [
            "## Top Attention Catalysts",
            "",
            "| Attention | Ticker | Window | Event | Evidence | Flags |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["top_attention_catalysts"]:  # type: ignore[index]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["attention_score"]),
                    _markdown_cell(str(item["ticker"])),
                    _markdown_cell(str(item["window"])),
                    _markdown_cell(str(item["event_type"]).replace("_", " ")),
                    _markdown_cell(str(item["evidence_state"])),
                    _markdown_cell(", ".join(str(flag) for flag in item["impact_flags"]) or "none"),
                ]
            )
            + " |"
        )
    if not payload["top_attention_catalysts"]:  # type: ignore[index]
        lines.append("|  | none |  |  |  |  |")
    lines.extend(
        [
            "",
            "## Review Queue",
            "",
            "| Attention | Ticker | Review | Action | Reason |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for item in payload["review_queue"]:  # type: ignore[index]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["attention_score"]),
                    _markdown_cell(str(item["ticker"])),
                    _markdown_cell(str(item["review_state"])),
                    _markdown_cell(str(item["required_review_action"])),
                    _markdown_cell(", ".join(str(reason) for reason in item["reasons"]) or "none"),
                ]
            )
            + " |"
        )
    if not payload["review_queue"]:  # type: ignore[index]
        lines.append("|  | none |  |  |  |")
    return "\n".join(lines).rstrip() + "\n"


def _normalize_impact_brief(
    raw: Dict[str, Any],
    as_of: Optional[date],
    days: int,
    stale_after_days: int,
) -> tuple[Dict[str, Any], str]:
    if raw.get("schema_version") == "impact-brief/v1":
        records = raw.get("records")
        if not isinstance(records, list):
            raise ValueError("impact-brief records must be a list")
        brief = dict(raw)
        brief["records"] = records
        return brief, "impact-brief"
    dataset = parse_dataset(raw)
    brief_as_of = as_of or dataset.as_of
    return impact_brief_json(dataset.records, brief_as_of, days, stale_after_days), "dataset"


def _normalize_record(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("impact-brief records must be objects")
    item = dict(raw)
    flags = item.get("impact_flags", [])
    if not isinstance(flags, list):
        raise ValueError("impact-brief record impact_flags must be a list")
    item["impact_flags"] = sorted(str(flag) for flag in flags)
    return item


def _counts(values: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _top_attention(records: List[Dict[str, Any]], top_limit: int) -> List[Dict[str, Any]]:
    ranked = sorted(
        records,
        key=lambda record: (
            -_int_field(record, "attention_score"),
            _int_field(record, "days_until"),
            str(record.get("ticker", "")),
            str(record.get("id", "")),
        ),
    )
    return ranked[:top_limit]


def _attention_item(record: Dict[str, Any]) -> Dict[str, object]:
    return {
        "id": record.get("id"),
        "ticker": record.get("ticker"),
        "entity": record.get("entity"),
        "event_type": record.get("event_type"),
        "window": record.get("window"),
        "attention_score": _int_field(record, "attention_score"),
        "catalyst_score": _int_field(record, "catalyst_score"),
        "urgency": record.get("urgency"),
        "review_state": record.get("review_state"),
        "evidence_state": record.get("evidence_state", "unknown"),
        "impact_flags": record["impact_flags"],
    }


def _review_item(record: Dict[str, Any]) -> Dict[str, object]:
    reasons = []
    if record.get("review_state") in {"stale", "needs_review"}:
        reasons.append(str(record.get("review_state")))
    if "missing_evidence_freshness" in record["impact_flags"]:
        reasons.append("missing_evidence_freshness")
    if str(record.get("required_review_action", "none")) != "none":
        reasons.append(str(record.get("required_review_action")))
    return {
        "id": record.get("id"),
        "ticker": record.get("ticker"),
        "entity": record.get("entity"),
        "window": record.get("window"),
        "attention_score": _int_field(record, "attention_score"),
        "days_until": _int_field(record, "days_until"),
        "review_state": record.get("review_state"),
        "required_review_action": record.get("required_review_action"),
        "evidence_state": record.get("evidence_state", "unknown"),
        "impact_flags": record["impact_flags"],
        "reasons": reasons,
    }


def _append_counts(lines: List[str], counts: object) -> None:
    if not counts:
        lines.extend(["No counts.", ""])
        return
    lines.extend(["| State | Count |", "| --- | ---: |"])
    for key, value in counts.items():  # type: ignore[union-attr]
        lines.append(f"| {_markdown_cell(str(key))} | {value} |")
    lines.append("")


def _int_field(record: Dict[str, Any], field: str) -> int:
    value = record.get(field, 0)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"impact-brief record {field} must be an integer") from exc


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
