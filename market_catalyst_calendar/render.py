"""Markdown and JSON rendering."""

from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List

from .models import CatalystRecord, sorted_records
from .scoring import Score, score_record


def record_to_json(record: CatalystRecord, as_of: date) -> Dict[str, object]:
    score = score_record(record, as_of)
    payload: Dict[str, object] = {
        "catalyst_score": score.catalyst_score,
        "days_until": score.days_until,
        "entity": record.entity,
        "event_type": record.event_type,
        "evidence_urls": list(record.evidence_urls),
        "id": record.record_id,
        "required_review_action": record.required_review_action,
        "review_state": score.review_state,
        "status": record.status,
        "thesis_impact": record.thesis_impact,
        "ticker": record.ticker,
        "urgency": score.urgency,
        "window": record.window.label,
    }
    if record.position_size is not None:
        payload["position_size"] = record.position_size
    if record.portfolio_weight is not None:
        payload["portfolio_weight"] = record.portfolio_weight
    return payload


def records_json(records: Iterable[CatalystRecord], as_of: date) -> Dict[str, object]:
    return {
        "as_of": as_of.isoformat(),
        "records": [record_to_json(record, as_of) for record in sorted_records(records)],
    }


def brief_markdown(records: Iterable[CatalystRecord], as_of: date, title: str = "Market Catalyst Brief") -> str:
    ordered = sorted(
        records,
        key=lambda record: (-score_record(record, as_of).catalyst_score, record.window.start, record.ticker, record.record_id),
    )
    lines: List[str] = [f"# {title}", "", f"As of: {as_of.isoformat()}", ""]
    if not ordered:
        lines.extend(["No matching catalysts.", ""])
        return "\n".join(lines)
    lines.extend(["| Score | Window | Ticker | Event | Status | Review | Impact |", "| ---: | --- | --- | --- | --- | --- | --- |"])
    for record in ordered:
        score = score_record(record, as_of)
        lines.append(
            "| "
            + " | ".join(
                [
                    str(score.catalyst_score),
                    record.window.label,
                    record.ticker,
                    record.event_type.replace("_", " "),
                    record.status,
                    score.review_state,
                    record.thesis_impact,
                ]
            )
            + " |"
        )
    lines.append("")
    for record in ordered:
        score = score_record(record, as_of)
        lines.extend(
            [
                f"## {record.ticker} - {record.entity}",
                "",
                f"- Event: {record.event_type.replace('_', ' ')} ({record.window.label})",
                f"- Score: {score.catalyst_score}; urgency: {score.urgency}; review: {score.review_state}",
                f"- Required action: {record.required_review_action}",
                f"- Thesis impact: {record.thesis_impact}",
                f"- Base scenario: {record.scenario_notes.get('base', '')}",
                f"- Evidence: {', '.join(record.evidence_urls)}",
                "",
            ]
        )
    return "\n".join(lines)


def exposure_json(records: Iterable[CatalystRecord], as_of: date) -> Dict[str, object]:
    groups = _exposure_groups(records, as_of)
    return {
        "as_of": as_of.isoformat(),
        "groups": groups,
        "summary": _exposure_summary(groups),
    }


def exposure_markdown(records: Iterable[CatalystRecord], as_of: date) -> str:
    groups = _exposure_groups(records, as_of)
    summary = _exposure_summary(groups)
    lines = [
        "# Market Catalyst Exposure",
        "",
        f"As of: {as_of.isoformat()}",
        "",
        f"Total catalysts: {summary['record_count']}",
        f"Aggregate portfolio weight: {_format_percent(summary['portfolio_weight'])}",
        f"Aggregate weighted exposure: {_format_percent(summary['weighted_exposure'])}",
        f"Aggregate position size: {_format_money(summary['position_size'])}",
        f"Aggregate weighted position size: {_format_money(summary['weighted_position_exposure'])}",
        "",
    ]
    if not groups:
        lines.extend(["No upcoming catalyst exposure.", ""])
        return "\n".join(lines)
    lines.extend(
        [
            "| Ticker | Event | Urgency | Records | Weight | Weighted Exposure | Position | Weighted Position |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for group in groups:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(group["ticker"]),
                    str(group["event_type"]).replace("_", " "),
                    str(group["urgency"]),
                    str(group["record_count"]),
                    _format_percent(float(group["portfolio_weight"])),
                    _format_percent(float(group["weighted_exposure"])),
                    _format_money(float(group["position_size"])),
                    _format_money(float(group["weighted_position_exposure"])),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def review_plan_json(
    records: Iterable[CatalystRecord],
    as_of: date,
    days: int,
    stale_after_days: int,
) -> Dict[str, object]:
    return {
        "as_of": as_of.isoformat(),
        "days": days,
        "stale_after_days": stale_after_days,
        "records": [
            _review_plan_item(record, as_of, days, stale_after_days)
            for record in _review_plan_records(records, as_of, days, stale_after_days)
        ],
    }


def review_plan_markdown(
    records: Iterable[CatalystRecord],
    as_of: date,
    days: int,
    stale_after_days: int,
) -> str:
    ordered = _review_plan_records(records, as_of, days, stale_after_days)
    lines = [
        "# Market Catalyst Review Plan",
        "",
        f"As of: {as_of.isoformat()}",
        f"Scope: stale records after {stale_after_days} days plus high-urgency catalysts in the next {days} days.",
        "",
    ]
    if not ordered:
        lines.extend(["No stale or high-urgency upcoming catalysts.", ""])
        return "\n".join(lines)

    for record in ordered:
        item = _review_plan_item(record, as_of, days, stale_after_days)
        lines.extend(
            [
                f"- [ ] **{record.ticker} - {record.entity}** ({record.record_id})",
                f"  - Window: {record.window.label}; event: {record.event_type.replace('_', ' ')}",
                f"  - Score: {item['catalyst_score']}; urgency: {item['urgency']}; review: {item['review_state']}",
                f"  - Reason: {', '.join(str(reason) for reason in item['selection_reasons'])}",
                f"  - Next action: {item['next_action']}",
                f"  - Evidence gap: {item['evidence_gap']}",
                f"  - Scenario update prompt: {item['scenario_update_prompt']}",
                "",
            ]
        )
    return "\n".join(lines)


def _exposure_groups(records: Iterable[CatalystRecord], as_of: date) -> List[Dict[str, object]]:
    groups: Dict[tuple[str, str, str], Dict[str, object]] = {}
    for record in records:
        score = score_record(record, as_of)
        key = (record.ticker, record.event_type, score.urgency)
        group = groups.setdefault(
            key,
            {
                "ticker": record.ticker,
                "event_type": record.event_type,
                "urgency": score.urgency,
                "record_count": 0,
                "portfolio_weight": 0.0,
                "position_size": 0.0,
                "weighted_exposure": 0.0,
                "weighted_position_exposure": 0.0,
                "records": [],
            },
        )
        portfolio_weight = record.portfolio_weight or 0.0
        position_size = record.position_size or 0.0
        event_weight = record.confidence * score.catalyst_score / 100
        group["record_count"] = int(group["record_count"]) + 1
        group["portfolio_weight"] = float(group["portfolio_weight"]) + portfolio_weight
        group["position_size"] = float(group["position_size"]) + position_size
        group["weighted_exposure"] = float(group["weighted_exposure"]) + portfolio_weight * event_weight
        group["weighted_position_exposure"] = float(group["weighted_position_exposure"]) + position_size * event_weight
        group["records"].append(record.record_id)  # type: ignore[union-attr]

    ordered = sorted(
        groups.values(),
        key=lambda group: (
            -float(group["weighted_exposure"]),
            -float(group["weighted_position_exposure"]),
            str(group["ticker"]),
            str(group["event_type"]),
            str(group["urgency"]),
        ),
    )
    for group in ordered:
        group["portfolio_weight"] = round(float(group["portfolio_weight"]), 6)
        group["position_size"] = round(float(group["position_size"]), 2)
        group["weighted_exposure"] = round(float(group["weighted_exposure"]), 6)
        group["weighted_position_exposure"] = round(float(group["weighted_position_exposure"]), 2)
        group["records"] = sorted(group["records"])  # type: ignore[arg-type]
    return ordered


def _review_plan_records(
    records: Iterable[CatalystRecord],
    as_of: date,
    days: int,
    stale_after_days: int,
) -> List[CatalystRecord]:
    selected = []
    for record in records:
        score = score_record(record, as_of, stale_after_days=stale_after_days)
        if _review_plan_reasons(record, score, days):
            selected.append(record)
    return sorted(
        selected,
        key=lambda record: _review_plan_sort_key(record, as_of, stale_after_days),
    )


def _review_plan_item(
    record: CatalystRecord,
    as_of: date,
    days: int,
    stale_after_days: int,
) -> Dict[str, object]:
    score = score_record(record, as_of, stale_after_days=stale_after_days)
    payload: Dict[str, object] = {
        "catalyst_score": score.catalyst_score,
        "days_until": score.days_until,
        "entity": record.entity,
        "event_type": record.event_type,
        "evidence_gap": _evidence_gap(record, score),
        "evidence_urls": list(record.evidence_urls),
        "id": record.record_id,
        "next_action": _next_action(record, score),
        "required_review_action": record.required_review_action,
        "review_state": score.review_state,
        "scenario_update_prompt": _scenario_update_prompt(record, score),
        "selection_reasons": _review_plan_reasons(record, score, days),
        "status": record.status,
        "ticker": record.ticker,
        "urgency": score.urgency,
        "window": record.window.label,
    }
    if score.stale_days is not None:
        payload["stale_days"] = score.stale_days
    if record.last_reviewed is not None:
        payload["last_reviewed"] = record.last_reviewed.isoformat()
    return payload


def _review_plan_reasons(record: CatalystRecord, score: Score, days: int) -> List[str]:
    if record.status in {"completed", "cancelled"}:
        return []
    reasons = []
    if score.review_state == "stale":
        reasons.append("stale")
    if score.urgency == "high" and 0 <= score.days_until <= days:
        reasons.append("high_urgency_upcoming")
    return reasons


def _review_plan_sort_key(record: CatalystRecord, as_of: date, stale_after_days: int) -> tuple[object, ...]:
    score = score_record(record, as_of, stale_after_days=stale_after_days)
    stale_rank = 0 if score.review_state == "stale" else 1
    urgency_rank = {"high": 0, "overdue": 1, "medium": 2, "low": 3, "closed": 4}.get(score.urgency, 5)
    stale_days = score.stale_days if score.stale_days is not None else -1
    return (
        stale_rank,
        urgency_rank,
        -stale_days,
        -score.catalyst_score,
        score.days_until,
        record.window.start,
        record.ticker,
        record.record_id,
    )


def _next_action(record: CatalystRecord, score: Score) -> str:
    action_labels = {
        "verify_source": "Verify the primary source and confirm the event window before updating status.",
        "refresh_evidence": "Refresh evidence with a newer primary source or dated secondary source.",
        "update_scenario": "Update bull, base, and bear scenarios using the latest evidence.",
        "monitor_date": "Check whether the event date or window has changed and update history.",
        "archive": "Archive the record if the catalyst is no longer actionable.",
        "none": "Confirm that no review action is needed and keep the record current.",
    }
    if score.review_state == "stale":
        return f"Stale by {score.stale_days} days. {action_labels[record.required_review_action]}"
    if score.urgency == "high":
        return f"High urgency in {score.days_until} days. {action_labels[record.required_review_action]}"
    return action_labels[record.required_review_action]


def _evidence_gap(record: CatalystRecord, score: Score) -> str:
    gaps = []
    if len(record.evidence_urls) < 2:
        gaps.append("add another independent source")
    if record.required_review_action == "verify_source":
        gaps.append("verify the source that anchors the event date/window")
    if record.required_review_action == "refresh_evidence":
        gaps.append("replace stale evidence with a current dated source")
    if score.review_state == "stale":
        gaps.append("confirm whether any source changed since last review")
    if not gaps:
        return "No structural evidence gap; confirm sources still support the current scenario."
    return "; ".join(gaps) + "."


def _scenario_update_prompt(record: CatalystRecord, score: Score) -> str:
    base = record.scenario_notes.get("base", "").strip()
    prompt = (
        f"Revise bull/base/bear cases for {record.ticker} {record.event_type.replace('_', ' ')} "
        f"after checking evidence; preserve thesis impact '{record.thesis_impact}' or explain a change."
    )
    if base:
        return f"{prompt} Current base case: {base}"
    if score.urgency == "high":
        return f"{prompt} Add a base case before the high-urgency window opens."
    return prompt


def _exposure_summary(groups: Iterable[Dict[str, object]]) -> Dict[str, object]:
    group_list = list(groups)
    return {
        "group_count": len(group_list),
        "record_count": sum(int(group["record_count"]) for group in group_list),
        "portfolio_weight": round(sum(float(group["portfolio_weight"]) for group in group_list), 6),
        "position_size": round(sum(float(group["position_size"]) for group in group_list), 2),
        "weighted_exposure": round(sum(float(group["weighted_exposure"]) for group in group_list), 6),
        "weighted_position_exposure": round(sum(float(group["weighted_position_exposure"]) for group in group_list), 2),
    }


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _format_money(value: float) -> str:
    return f"{value:,.2f}"
