"""Markdown and JSON rendering."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, Iterable, List

from .models import CatalystRecord, sorted_records
from .scoring import Score, score_record


SCENARIO_ORDER = ("bull", "base", "bear")


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
    if record.thesis_id is not None:
        payload["thesis_id"] = record.thesis_id
    if record.source_ref is not None:
        payload["source_ref"] = record.source_ref
    if record.evidence_checked_at is not None:
        payload["evidence_checked_at"] = record.evidence_checked_at.isoformat()
    if record.broker_views:
        payload["broker_views"] = [
            {
                "as_of": view.as_of.isoformat(),
                "caveat": view.caveat,
                "institution": view.institution,
                "rating": view.rating,
                "source_url": view.source_url,
                "target_price": view.target_price,
            }
            for view in record.broker_views
        ]
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


def thesis_map_json(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> Dict[str, object]:
    groups = _thesis_groups(records, as_of, stale_after_days)
    return {
        "as_of": as_of.isoformat(),
        "stale_after_days": stale_after_days,
        "groups": groups,
        "summary": {
            "thesis_count": len(groups),
            "record_count": sum(int(group["record_count"]) for group in groups),
            "open_event_count": sum(int(group["open_event_count"]) for group in groups),
            "stale_count": sum(int(group["stale_count"]) for group in groups),
        },
    }


def thesis_map_markdown(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> str:
    groups = _thesis_groups(records, as_of, stale_after_days)
    lines = [
        "# Market Catalyst Thesis Map",
        "",
        f"As of: {as_of.isoformat()}",
        f"Stale after: {stale_after_days} days",
        "",
    ]
    if not groups:
        lines.extend(["No catalysts with thesis_id.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Thesis | Open Events | Highest Score | Stale | Records | Evidence References |",
            "| --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for group in groups:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(group["thesis_id"]),
                    str(group["open_event_count"]),
                    str(group["highest_score"]),
                    str(group["stale_count"]),
                    ", ".join(str(record_id) for record_id in group["records"]),
                    ", ".join(str(ref) for ref in group["evidence_references"]),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def scenario_matrix_json(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> Dict[str, object]:
    matrix = [_scenario_matrix_record(record, as_of, stale_after_days) for record in sorted_records(records)]
    return {
        "as_of": as_of.isoformat(),
        "stale_after_days": stale_after_days,
        "records": matrix,
        "summary": {
            "record_count": len(matrix),
            "scenario_count": sum(len(record["scenarios"]) for record in matrix),
            "highest_scenario_score": max(
                (int(scenario["score"]) for record in matrix for scenario in record["scenarios"]),
                default=0,
            ),
            "review_action_count": sum(
                1
                for record in matrix
                for scenario in record["scenarios"]
                if scenario["review_action"] != "none"
            ),
        },
    }


def scenario_matrix_markdown(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> str:
    payload = scenario_matrix_json(records, as_of, stale_after_days)
    lines = [
        "# Market Catalyst Scenario Matrix",
        "",
        f"As of: {as_of.isoformat()}",
        f"Stale after: {stale_after_days} days",
        "",
    ]
    if not payload["records"]:
        lines.extend(["No matching catalyst scenarios.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Ticker | Event Date | Scenario | Score | Impact | Review Action | Note |",
            "| --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    for record in payload["records"]:
        for scenario in record["scenarios"]:  # type: ignore[index]
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(record["ticker"]),
                        str(scenario["date"]),
                        str(scenario["scenario"]),
                        str(scenario["score"]),
                        str(scenario["impact"]),
                        str(scenario["review_action"]),
                        _markdown_cell(str(scenario["note"])),
                    ]
                )
                + " |"
            )
    lines.append("")
    return "\n".join(lines)


def broker_matrix_json(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> Dict[str, object]:
    groups = _broker_groups(records, as_of, stale_after_days)
    return {
        "as_of": as_of.isoformat(),
        "stale_after_days": stale_after_days,
        "groups": groups,
        "summary": {
            "group_count": len(groups),
            "view_count": sum(int(group["view_count"]) for group in groups),
            "stale_view_count": sum(len(group["stale_sources"]) for group in groups),
            "linked_catalyst_count": sum(len(group["linked_catalysts"]) for group in groups),
        },
    }


def broker_matrix_markdown(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> str:
    payload = broker_matrix_json(records, as_of, stale_after_days)
    lines = [
        "# Market Catalyst Broker Matrix",
        "",
        f"As of: {as_of.isoformat()}",
        f"Stale broker source after: {stale_after_days} days",
        "",
    ]
    if not payload["groups"]:
        lines.extend(["No broker views recorded.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Ticker | Thesis | Views | Target Avg | Target Range | Dispersion | Stale Sources | Linked Catalysts |",
            "| --- | --- | ---: | ---: | --- | ---: | --- | --- |",
        ]
    )
    for group in payload["groups"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(group["ticker"]),
                    str(group["thesis_id"]),
                    str(group["view_count"]),
                    _format_price(float(group["target_price_avg"])),
                    _format_target_range(group),
                    _format_price(float(group["target_price_dispersion"])),
                    ", ".join(str(item["institution"]) for item in group["stale_sources"]) or "none",
                    ", ".join(str(item["id"]) for item in group["linked_catalysts"]) or "none",
                ]
            )
            + " |"
        )
    lines.append("")
    for group in payload["groups"]:
        lines.extend([f"## {group['ticker']} - {group['thesis_id']}", ""])
        lines.extend(["| Institution | Rating | Target | As Of | Age | Caveat | Source |", "| --- | --- | ---: | --- | ---: | --- | --- |"])
        for view in group["views"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(view["institution"]),
                        str(view["rating"]),
                        _format_price(float(view["target_price"])),
                        str(view["as_of"]),
                        str(view["age_days"]),
                        _markdown_cell(str(view["caveat"])),
                        str(view["source_url"]),
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


def watchlist_json(
    records: Iterable[CatalystRecord],
    as_of: date,
    days: int,
    stale_after_days: int,
) -> Dict[str, object]:
    items = [_watchlist_item(record, as_of, stale_after_days) for record in _watchlist_records(records, as_of, days, stale_after_days)]
    return {
        "as_of": as_of.isoformat(),
        "days": days,
        "stale_after_days": stale_after_days,
        "items": items,
        "summary": {
            "item_count": len(items),
            "critical_count": sum(1 for item in items if item["priority"] == "critical"),
            "high_count": sum(1 for item in items if item["priority"] == "high"),
            "medium_count": sum(1 for item in items if item["priority"] == "medium"),
            "low_count": sum(1 for item in items if item["priority"] == "low"),
            "due_now_count": sum(1 for item in items if item["due_state"] == "due_now"),
        },
    }


def watchlist_markdown(
    records: Iterable[CatalystRecord],
    as_of: date,
    days: int,
    stale_after_days: int,
) -> str:
    payload = watchlist_json(records, as_of, days, stale_after_days)
    lines = [
        "# Market Catalyst Watchlist",
        "",
        f"As of: {as_of.isoformat()}",
        f"Scope: open catalysts due or starting within {days} days; stale after {stale_after_days} days.",
        "",
    ]
    if not payload["items"]:
        lines.extend(["No catalyst watch items.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Priority | Due | Cadence | Ticker | Catalyst | Triggers | Thesis | Sources |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["items"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"{item['priority']} ({item['priority_score']})",
                    str(item["due_date"]),
                    str(item["review_cadence"]),
                    str(item["ticker"]),
                    f"{item['event_type']} {item['window']}",
                    _markdown_cell("; ".join(str(trigger["condition"]) for trigger in item["trigger_conditions"])),
                    str(item["thesis_id"]),
                    _markdown_cell(", ".join(str(source) for source in item["source_refs"])),
                ]
            )
            + " |"
        )
    lines.append("")
    for item in payload["items"]:
        lines.extend(
            [
                f"## {item['ticker']} - {item['entity']}",
                "",
                f"- Watch item: {item['watch_id']}",
                f"- Catalyst: {item['catalyst_id']} ({item['event_type']}, {item['window']})",
                f"- Priority: {item['priority']} ({item['priority_score']}); urgency: {item['urgency']}; review: {item['review_state']}",
                f"- Due: {item['due_date']} ({item['due_state']}); cadence: {item['review_cadence']}",
                f"- Required action: {item['required_review_action']}",
                f"- Thesis ref: {item['thesis_id']}; source ref: {item['source_ref']}",
                f"- Evidence links: {', '.join(str(url) for url in item['evidence_urls'])}",
                "- Trigger conditions:",
            ]
        )
        for trigger in item["trigger_conditions"]:
            lines.append(f"  - {trigger['condition']} -> {trigger['action']}")
        lines.append("")
    return "\n".join(lines)


def _watchlist_records(records: Iterable[CatalystRecord], as_of: date, days: int, stale_after_days: int) -> List[CatalystRecord]:
    selected = []
    for record in records:
        if record.status in {"completed", "cancelled"}:
            continue
        days_until = (record.window.start - as_of).days
        if days_until <= days:
            selected.append(record)
    return sorted(selected, key=lambda record: _watchlist_sort_key(record, as_of, stale_after_days))


def _watchlist_sort_key(record: CatalystRecord, as_of: date, stale_after_days: int) -> tuple[object, ...]:
    score = score_record(record, as_of, stale_after_days=stale_after_days)
    priority_score = _watchlist_priority_score(record, score)
    return (-priority_score, _watchlist_due_date(record, as_of, score), record.window.start, record.ticker, record.record_id)


def _watchlist_item(record: CatalystRecord, as_of: date, stale_after_days: int) -> Dict[str, object]:
    score = score_record(record, as_of, stale_after_days=stale_after_days)
    due_date = _watchlist_due_date(record, as_of, score)
    source_refs = []
    if record.source_ref is not None:
        source_refs.append(record.source_ref)
    source_refs.extend(record.evidence_urls)
    priority_score = _watchlist_priority_score(record, score)
    return {
        "watch_id": f"watch-{record.record_id}",
        "catalyst_id": record.record_id,
        "ticker": record.ticker,
        "entity": record.entity,
        "event_type": record.event_type,
        "window": record.window.label,
        "status": record.status,
        "catalyst_score": score.catalyst_score,
        "priority_score": priority_score,
        "priority": _watchlist_priority(priority_score),
        "urgency": score.urgency,
        "review_state": score.review_state,
        "days_until": score.days_until,
        "due_date": due_date.isoformat(),
        "due_state": "due_now" if due_date <= as_of else "scheduled",
        "review_cadence": _watchlist_cadence(score, due_date, as_of),
        "trigger_conditions": _watchlist_triggers(record, as_of, score, due_date),
        "required_review_action": record.required_review_action,
        "thesis_id": record.thesis_id or "unmapped",
        "source_ref": record.source_ref or "none",
        "source_refs": source_refs,
        "evidence_urls": list(record.evidence_urls),
        "scenario_refs": {
            "bull": record.scenario_notes.get("bull", ""),
            "base": record.scenario_notes.get("base", ""),
            "bear": record.scenario_notes.get("bear", ""),
        },
    }


def _watchlist_priority_score(record: CatalystRecord, score: Score) -> int:
    base_score = round(score.catalyst_score * 0.75)
    stale_boost = 12 if score.review_state == "stale" else 0
    urgency_boost = {"overdue": 18, "high": 14, "medium": 7, "low": 0, "closed": 0}.get(score.urgency, 0)
    exposure_boost = min(10, round((record.portfolio_weight or 0.0) * 100))
    action_boost = 6 if record.required_review_action in {"verify_source", "refresh_evidence", "update_scenario"} else 0
    return max(0, min(100, base_score + stale_boost + urgency_boost + exposure_boost + action_boost))


def _watchlist_priority(priority_score: int) -> str:
    if priority_score >= 90:
        return "critical"
    if priority_score >= 75:
        return "high"
    if priority_score >= 55:
        return "medium"
    return "low"


def _watchlist_due_date(record: CatalystRecord, as_of: date, score: Score) -> date:
    if score.review_state == "stale" or score.days_until <= 0:
        return as_of
    if score.urgency == "high":
        return max(as_of, record.window.start - timedelta(days=3))
    if score.urgency == "medium":
        return max(as_of, record.window.start - timedelta(days=7))
    return max(as_of, record.window.start - timedelta(days=14))


def _watchlist_cadence(score: Score, due_date: date, as_of: date) -> str:
    if due_date <= as_of or score.urgency in {"overdue", "high"}:
        return "daily_until_resolved"
    if score.days_until <= 30:
        return "twice_weekly"
    if score.days_until <= 90:
        return "weekly"
    return "monthly"


def _watchlist_triggers(record: CatalystRecord, as_of: date, score: Score, due_date: date) -> List[Dict[str, object]]:
    triggers: List[Dict[str, object]] = [
        {
            "type": "review_due",
            "condition": f"Review by {due_date.isoformat()} before catalyst window {record.window.label}.",
            "action": record.required_review_action,
        },
        {
            "type": "event_window",
            "condition": f"Escalate if {record.ticker} confirms, delays, cancels, or changes the {record.event_type.replace('_', ' ')} window.",
            "action": "update_status_and_history",
        },
    ]
    if score.review_state == "stale":
        triggers.append(
            {
                "type": "stale_review",
                "condition": f"Last review is stale by {score.stale_days} days as of {as_of.isoformat()}.",
                "action": "refresh_review_notes",
            }
        )
    if record.required_review_action in {"verify_source", "refresh_evidence"}:
        triggers.append(
            {
                "type": "source_check",
                "condition": "Primary evidence changes, disappears, conflicts with another source, or lacks a dated update.",
                "action": record.required_review_action,
            }
        )
    if record.thesis_id is not None:
        triggers.append(
            {
                "type": "thesis_link",
                "condition": f"Bull/base/bear evidence changes the linked thesis '{record.thesis_id}'.",
                "action": "update_thesis_reference",
            }
        )
    if record.portfolio_weight is not None or record.position_size is not None:
        triggers.append(
            {
                "type": "exposure_change",
                "condition": "Position size, portfolio weight, or risk budget changes before the event.",
                "action": "refresh_exposure_context",
            }
        )
    return triggers


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


def _broker_groups(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> List[Dict[str, object]]:
    groups: Dict[tuple[str, str], Dict[str, object]] = {}
    for record in records:
        if not record.broker_views:
            continue
        thesis_id = record.thesis_id or "unmapped"
        key = (record.ticker, thesis_id)
        group = groups.setdefault(
            key,
            {
                "ticker": record.ticker,
                "thesis_id": thesis_id,
                "views": [],
                "linked_catalysts": {},
            },
        )
        score = score_record(record, as_of, stale_after_days=stale_after_days)
        group["linked_catalysts"][record.record_id] = {  # type: ignore[index]
            "catalyst_score": score.catalyst_score,
            "days_until": score.days_until,
            "event_type": record.event_type,
            "id": record.record_id,
            "review_state": score.review_state,
            "status": record.status,
            "urgency": score.urgency,
            "window": record.window.label,
        }
        for view in record.broker_views:
            age_days = (as_of - view.as_of).days
            group["views"].append(  # type: ignore[union-attr]
                {
                    "age_days": age_days,
                    "as_of": view.as_of.isoformat(),
                    "caveat": view.caveat,
                    "institution": view.institution,
                    "rating": view.rating,
                    "source_url": view.source_url,
                    "stale_source": age_days > stale_after_days,
                    "target_price": view.target_price,
                }
            )

    normalized = []
    for group in groups.values():
        views = sorted(
            group["views"],  # type: ignore[arg-type]
            key=lambda view: (str(view["institution"]), str(view["as_of"]), str(view["rating"]), float(view["target_price"])),
        )
        targets = [float(view["target_price"]) for view in views]
        target_min = min(targets)
        target_max = max(targets)
        target_avg = sum(targets) / len(targets)
        ratings = sorted(set(str(view["rating"]) for view in views))
        linked = sorted(
            group["linked_catalysts"].values(),  # type: ignore[union-attr]
            key=lambda item: (-int(item["catalyst_score"]), str(item["window"]), str(item["id"])),
        )
        normalized.append(
            {
                "linked_catalysts": linked,
                "rating_count": {rating: sum(1 for view in views if view["rating"] == rating) for rating in ratings},
                "ratings": ratings,
                "stale_sources": [
                    {
                        "age_days": view["age_days"],
                        "as_of": view["as_of"],
                        "institution": view["institution"],
                        "source_url": view["source_url"],
                    }
                    for view in views
                    if view["stale_source"]
                ],
                "target_price_avg": round(target_avg, 2),
                "target_price_dispersion": round(target_max - target_min, 2),
                "target_price_max": round(target_max, 2),
                "target_price_min": round(target_min, 2),
                "thesis_id": group["thesis_id"],
                "ticker": group["ticker"],
                "view_count": len(views),
                "views": views,
            }
        )
    return sorted(
        normalized,
        key=lambda group: (
            -float(group["target_price_dispersion"]),
            -len(group["stale_sources"]),
            str(group["ticker"]),
            str(group["thesis_id"]),
        ),
    )


def _scenario_matrix_record(record: CatalystRecord, as_of: date, stale_after_days: int) -> Dict[str, object]:
    score = score_record(record, as_of, stale_after_days=stale_after_days)
    return {
        "base_catalyst_score": score.catalyst_score,
        "days_until": score.days_until,
        "entity": record.entity,
        "event_type": record.event_type,
        "id": record.record_id,
        "review_state": score.review_state,
        "scenarios": [_scenario_item(record, score, scenario) for scenario in SCENARIO_ORDER],
        "status": record.status,
        "ticker": record.ticker,
        "urgency": score.urgency,
        "window": record.window.label,
    }


def _scenario_item(record: CatalystRecord, score: Score, scenario: str) -> Dict[str, object]:
    scenario_score = max(0, min(100, score.catalyst_score + _scenario_score_adjustment(record, scenario)))
    return {
        "date": _scenario_date(record, scenario),
        "impact": _scenario_impact(record, scenario),
        "note": record.scenario_notes.get(scenario, ""),
        "review_action": _scenario_review_action(record, score, scenario),
        "scenario": scenario,
        "score": scenario_score,
    }


def _scenario_score_adjustment(record: CatalystRecord, scenario: str) -> int:
    if scenario == "base":
        return 0
    impact_bias = {
        "positive": 6,
        "mixed": 4,
        "negative": 6,
        "unknown": 2,
    }.get(record.thesis_impact, 2)
    confidence_bias = 3 if record.confidence >= 0.75 else 0
    if scenario == "bull":
        return impact_bias + confidence_bias
    return -(impact_bias + confidence_bias + 4)


def _scenario_date(record: CatalystRecord, scenario: str) -> str:
    if record.window.start == record.window.end:
        return record.window.start.isoformat()
    if scenario == "bull":
        return record.window.start.isoformat()
    if scenario == "bear":
        return record.window.end.isoformat()
    return record.window.label


def _scenario_impact(record: CatalystRecord, scenario: str) -> str:
    if scenario == "base":
        return record.thesis_impact
    if scenario == "bull":
        if record.thesis_impact == "negative":
            return "less_negative"
        if record.thesis_impact == "unknown":
            return "positive_if_confirmed"
        return "positive"
    if record.thesis_impact == "positive":
        return "less_positive"
    if record.thesis_impact == "unknown":
        return "negative_if_disconfirmed"
    return "negative"


def _scenario_review_action(record: CatalystRecord, score: Score, scenario: str) -> str:
    if record.status in {"completed", "cancelled"}:
        return "none"
    if score.review_state == "stale":
        return f"{record.required_review_action}:{scenario}:stale"
    if scenario != "base" and record.required_review_action in {"update_scenario", "refresh_evidence", "verify_source"}:
        return f"{record.required_review_action}:{scenario}"
    if scenario == "base":
        return record.required_review_action
    return "monitor_date" if score.urgency in {"high", "overdue"} else "none"


def _thesis_groups(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> List[Dict[str, object]]:
    groups: Dict[str, Dict[str, object]] = {}
    for record in records:
        if record.thesis_id is None:
            continue
        score = score_record(record, as_of, stale_after_days=stale_after_days)
        group = groups.setdefault(
            record.thesis_id,
            {
                "thesis_id": record.thesis_id,
                "record_count": 0,
                "open_event_count": 0,
                "highest_score": 0,
                "stale_count": 0,
                "records": [],
                "evidence_references": [],
            },
        )
        is_open = record.status not in {"completed", "cancelled"}
        group["record_count"] = int(group["record_count"]) + 1
        if is_open:
            group["open_event_count"] = int(group["open_event_count"]) + 1
        group["highest_score"] = max(int(group["highest_score"]), score.catalyst_score)
        if is_open and score.review_state == "stale":
            group["stale_count"] = int(group["stale_count"]) + 1
        group["records"].append(record.record_id)  # type: ignore[union-attr]
        references = group["evidence_references"]
        if record.source_ref is not None:
            references.append(record.source_ref)  # type: ignore[union-attr]
        references.extend(record.evidence_urls)  # type: ignore[union-attr]

    ordered = sorted(
        groups.values(),
        key=lambda group: (
            -int(group["open_event_count"]),
            -int(group["highest_score"]),
            str(group["thesis_id"]),
        ),
    )
    for group in ordered:
        group["records"] = sorted(group["records"])  # type: ignore[arg-type]
        group["evidence_references"] = sorted(set(group["evidence_references"]))  # type: ignore[arg-type]
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


def _format_price(value: float) -> str:
    return f"{value:.2f}"


def _format_target_range(group: Dict[str, object]) -> str:
    return f"{_format_price(float(group['target_price_min']))}-{_format_price(float(group['target_price_max']))}"


def _markdown_cell(value: str) -> str:
    return value.replace("\n", " ").replace("|", "\\|")
