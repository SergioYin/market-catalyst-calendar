"""Deterministic catalyst impact briefs from static dataset records."""

from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List

from .models import CatalystRecord
from .scoring import score_record


BOUNDARY_NOTE = (
    "Offline deterministic research brief from supplied dataset only. "
    "No live data, broker connectivity, predictions, investment advice, or trade recommendations."
)
BOUNDARY = {
    "source_basis": "supplied_dataset_only",
    "live_data": False,
    "broker_connectivity": False,
    "prediction": False,
    "investment_advice": False,
    "trade_recommendation": False,
}


def impact_brief_json(records: Iterable[CatalystRecord], as_of: date, days: int, stale_after_days: int) -> Dict[str, object]:
    """Return a deterministic public-finance impact brief payload."""

    selected = _impact_records(records, as_of, days, stale_after_days)
    items = [_impact_item(record, as_of, stale_after_days) for record in selected]
    return {
        "schema_version": "impact-brief/v1",
        "as_of": as_of.isoformat(),
        "days": days,
        "stale_after_days": stale_after_days,
        "boundary_note": BOUNDARY_NOTE,
        "boundary": dict(BOUNDARY),
        "summary": {
            "record_count": len(items),
            "high_urgency_count": sum(1 for item in items if item["urgency"] == "high"),
            "stale_review_count": sum(1 for item in items if item["review_state"] == "stale"),
            "over_budget_count": sum(1 for item in items if "over_budget" in item["impact_flags"]),
            "missing_risk_context_count": sum(1 for item in items if "missing_risk_context" in item["impact_flags"]),
            "aggregate_portfolio_weight": round(sum(float(item["portfolio_weight"]) for item in items), 6),
            "aggregate_weighted_attention": round(sum(float(item["weighted_attention"]) for item in items), 6),
        },
        "records": items,
    }


def impact_brief_markdown(records: Iterable[CatalystRecord], as_of: date, days: int, stale_after_days: int) -> str:
    """Render a deterministic Markdown catalyst impact brief."""

    payload = impact_brief_json(records, as_of, days, stale_after_days)
    summary = payload["summary"]  # type: ignore[index]
    lines = [
        "# Market Catalyst Impact Brief",
        "",
        f"As of: {payload['as_of']}",
        f"Scope: open catalysts starting within {days} days; stale after {stale_after_days} days.",
        "",
        f"Boundary: {payload['boundary_note']}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Records | {summary['record_count']} |",
        f"| High urgency | {summary['high_urgency_count']} |",
        f"| Stale review | {summary['stale_review_count']} |",
        f"| Over budget | {summary['over_budget_count']} |",
        f"| Missing risk context | {summary['missing_risk_context_count']} |",
        f"| Aggregate portfolio weight | {_format_percent(float(summary['aggregate_portfolio_weight']))} |",
        f"| Aggregate weighted attention | {_format_percent(float(summary['aggregate_weighted_attention']))} |",
        "",
    ]
    if not payload["records"]:
        lines.extend(["No open catalysts match the requested impact-brief window.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Attention | Ticker | Window | Event | Impact | Flags | Base Case |",
            "| ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["records"]:  # type: ignore[index]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["attention_score"]),
                    str(item["ticker"]),
                    str(item["window"]),
                    str(item["event_type"]).replace("_", " "),
                    str(item["impact_label"]),
                    ", ".join(str(flag) for flag in item["impact_flags"]) or "none",
                    _markdown_cell(str(item["scenarios"]["base"])),  # type: ignore[index]
                ]
            )
            + " |"
        )
    lines.append("")

    for item in payload["records"]:  # type: ignore[index]
        lines.extend(
            [
                f"## {item['ticker']} - {item['entity']}",
                "",
                f"- Catalyst id: {item['id']}",
                f"- Event: {str(item['event_type']).replace('_', ' ')} ({item['window']}); status: {item['status']}",
                f"- Attention score: {item['attention_score']}; catalyst score: {item['catalyst_score']}; urgency: {item['urgency']}; review: {item['review_state']}",
                f"- Impact label: {item['impact_label']}; thesis impact: {item['thesis_impact']}; confidence: {item['confidence']}",
                f"- Exposure context: weight {_format_percent(float(item['portfolio_weight']))}; weighted attention {_format_percent(float(item['weighted_attention']))}; risk budget {_format_money(float(item['risk_budget']))}; max loss {_format_money(float(item['max_loss']))}",
                f"- Evidence state: {item['evidence_state']}; source ref: {item['source_ref']}",
                f"- Required review action: {item['required_review_action']}",
                f"- Bull: {_markdown_cell(str(item['scenarios']['bull']))}",  # type: ignore[index]
                f"- Base: {_markdown_cell(str(item['scenarios']['base']))}",  # type: ignore[index]
                f"- Bear: {_markdown_cell(str(item['scenarios']['bear']))}",  # type: ignore[index]
                f"- Evidence URLs: {', '.join(str(url) for url in item['evidence_urls'])}",
                "",
            ]
        )
    return "\n".join(lines)


def _impact_records(records: Iterable[CatalystRecord], as_of: date, days: int, stale_after_days: int) -> List[CatalystRecord]:
    selected = [
        record
        for record in records
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]
    return sorted(selected, key=lambda record: _impact_sort_key(record, as_of, stale_after_days))


def _impact_sort_key(record: CatalystRecord, as_of: date, stale_after_days: int) -> tuple[object, ...]:
    item = _impact_item(record, as_of, stale_after_days)
    return (-int(item["attention_score"]), record.window.start, record.ticker, record.record_id)


def _impact_item(record: CatalystRecord, as_of: date, stale_after_days: int) -> Dict[str, object]:
    score = score_record(record, as_of, stale_after_days=stale_after_days)
    flags = _impact_flags(record, score.review_state)
    portfolio_weight = record.portfolio_weight or 0.0
    weighted_attention = portfolio_weight * record.confidence * score.catalyst_score / 100
    attention_score = min(
        100,
        round(score.catalyst_score + (8 if score.review_state == "stale" else 0) + (6 if "over_budget" in flags else 0)),
    )
    return {
        "id": record.record_id,
        "ticker": record.ticker,
        "entity": record.entity,
        "event_type": record.event_type,
        "window": record.window.label,
        "status": record.status,
        "confidence": record.confidence,
        "thesis_impact": record.thesis_impact,
        "impact_label": _impact_label(record),
        "catalyst_score": score.catalyst_score,
        "attention_score": attention_score,
        "days_until": score.days_until,
        "urgency": score.urgency,
        "review_state": score.review_state,
        "required_review_action": record.required_review_action,
        "portfolio_weight": portfolio_weight,
        "weighted_attention": round(weighted_attention, 6),
        "risk_budget": record.risk_budget or 0.0,
        "max_loss": record.max_loss or 0.0,
        "sector": record.sector or "unmapped",
        "theme": record.theme or "unmapped",
        "thesis_id": record.thesis_id or "unmapped",
        "source_ref": record.source_ref or "none",
        "evidence_state": _evidence_state(record, as_of, stale_after_days),
        "evidence_checked_at": record.evidence_checked_at.isoformat() if record.evidence_checked_at else "missing",
        "evidence_urls": list(record.evidence_urls),
        "broker_view_count": len(record.broker_views),
        "impact_flags": flags,
        "scenarios": {
            "bull": _scenario_note(record, "bull"),
            "base": _scenario_note(record, "base"),
            "bear": _scenario_note(record, "bear"),
        },
    }


def _impact_flags(record: CatalystRecord, review_state: str) -> List[str]:
    flags = []
    if review_state == "stale":
        flags.append("stale_review")
    if record.evidence_checked_at is None:
        flags.append("missing_evidence_freshness")
    if record.risk_budget is None or record.max_loss is None:
        flags.append("missing_risk_context")
    elif record.max_loss > record.risk_budget:
        flags.append("over_budget")
    if record.broker_views:
        flags.append("broker_context")
    return flags


def _impact_label(record: CatalystRecord) -> str:
    if record.thesis_impact == "positive":
        return "positive thesis context"
    if record.thesis_impact == "negative":
        return "negative thesis context"
    if record.thesis_impact == "mixed":
        return "mixed thesis context"
    return "unknown thesis context"


def _evidence_state(record: CatalystRecord, as_of: date, stale_after_days: int) -> str:
    if not record.evidence_urls:
        return "missing"
    if record.evidence_checked_at is None:
        return "missing"
    if (as_of - record.evidence_checked_at).days > stale_after_days:
        return "stale"
    return "fresh"


def _scenario_note(record: CatalystRecord, scenario: str) -> str:
    note = record.scenario_notes.get(scenario, "").strip()
    if note:
        return note
    return "Not supplied in the static dataset."


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _format_money(value: float) -> str:
    return f"{value:,.2f}"


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
