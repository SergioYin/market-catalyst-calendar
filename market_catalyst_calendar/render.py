"""Markdown and JSON rendering."""

from __future__ import annotations

import csv
from io import StringIO
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
    if record.actual_outcome is not None:
        payload["actual_outcome"] = record.actual_outcome
    if record.outcome_recorded_at is not None:
        payload["outcome_recorded_at"] = record.outcome_recorded_at.isoformat()
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


def source_pack_json(records: Iterable[CatalystRecord], as_of: date, fresh_after_days: int) -> Dict[str, object]:
    sources = _source_pack_sources(records, as_of, fresh_after_days)
    return {
        "as_of": as_of.isoformat(),
        "fresh_after_days": fresh_after_days,
        "sources": sources,
        "summary": {
            "source_count": len(sources),
            "evidence_source_count": sum(1 for source in sources if "evidence" in source["source_types"]),
            "broker_source_count": sum(1 for source in sources if "broker" in source["source_types"]),
            "stale_source_count": sum(1 for source in sources if source["freshness_state"] == "stale"),
            "missing_freshness_count": sum(1 for source in sources if source["freshness_state"] == "missing"),
            "usage_count": sum(int(source["usage_count"]) for source in sources),
        },
    }


def source_pack_csv(records: Iterable[CatalystRecord], as_of: date, fresh_after_days: int) -> str:
    output = StringIO()
    columns = [
        "url",
        "source_types",
        "usage_count",
        "tickers",
        "thesis_ids",
        "record_ids",
        "evidence_checked_at",
        "freshness_age_days",
        "freshness_state",
        "broker_institutions",
        "broker_as_of_dates",
    ]
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for source in _source_pack_sources(records, as_of, fresh_after_days):
        writer.writerow(
            {
                "url": source["url"],
                "source_types": ";".join(str(item) for item in source["source_types"]),
                "usage_count": source["usage_count"],
                "tickers": ";".join(str(item) for item in source["tickers"]),
                "thesis_ids": ";".join(str(item) for item in source["thesis_ids"]),
                "record_ids": ";".join(str(item) for item in source["record_ids"]),
                "evidence_checked_at": source["evidence_checked_at"],
                "freshness_age_days": source["freshness_age_days"],
                "freshness_state": source["freshness_state"],
                "broker_institutions": ";".join(str(item) for item in source["broker_institutions"]),
                "broker_as_of_dates": ";".join(str(item) for item in source["broker_as_of_dates"]),
            }
        )
    return output.getvalue()


def source_pack_markdown(records: Iterable[CatalystRecord], as_of: date, fresh_after_days: int) -> str:
    payload = source_pack_json(records, as_of, fresh_after_days)
    lines = [
        "# Market Catalyst Source Pack",
        "",
        f"As of: {as_of.isoformat()}",
        f"Fresh after: {fresh_after_days} days",
        "",
    ]
    if not payload["sources"]:
        lines.extend(["No source URLs recorded.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Freshness | Uses | Type | Tickers | Thesis IDs | Checked | URL |",
            "| --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for source in payload["sources"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(source["freshness_state"]),
                    str(source["usage_count"]),
                    ", ".join(str(item) for item in source["source_types"]),
                    ", ".join(str(item) for item in source["tickers"]),
                    ", ".join(str(item) for item in source["thesis_ids"]),
                    str(source["evidence_checked_at"]),
                    str(source["url"]),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def decision_log_json(
    records: Iterable[CatalystRecord],
    as_of: date,
    days: int,
    stale_after_days: int,
) -> Dict[str, object]:
    memos = [_decision_memo(record, as_of, stale_after_days) for record in _decision_log_records(records, as_of, days, stale_after_days)]
    return {
        "as_of": as_of.isoformat(),
        "days": days,
        "stale_after_days": stale_after_days,
        "memos": memos,
        "summary": {
            "memo_count": len(memos),
            "broker_context_count": sum(1 for memo in memos if memo["broker_context"]["view_count"]),
            "stale_memo_count": sum(1 for memo in memos if memo["catalyst"]["review_state"] == "stale"),
            "trigger_count": sum(len(memo["watchlist_triggers"]) for memo in memos),
        },
    }


def decision_log_markdown(
    records: Iterable[CatalystRecord],
    as_of: date,
    days: int,
    stale_after_days: int,
) -> str:
    payload = decision_log_json(records, as_of, days, stale_after_days)
    lines = [
        "# Market Catalyst Decision Log",
        "",
        f"As of: {as_of.isoformat()}",
        f"Scope: open catalysts due or starting within {days} days; stale after {stale_after_days} days.",
        "",
    ]
    if not payload["memos"]:
        lines.extend(["No catalyst decision memos.", ""])
        return "\n".join(lines)

    for memo in payload["memos"]:
        thesis = memo["thesis"]  # type: ignore[index]
        catalyst = memo["catalyst"]  # type: ignore[index]
        evidence = memo["evidence"]  # type: ignore[index]
        broker = memo["broker_context"]  # type: ignore[index]
        review = memo["post_event_review"]  # type: ignore[index]
        lines.extend(
            [
                f"## {memo['ticker']} - {memo['entity']}",
                "",
                f"- Memo id: {memo['memo_id']}",
                f"- Decision owner: {memo['decision_owner']}",
                f"- Decision status: {memo['decision_status']}",
                f"- Prepared on: {memo['prepared_on']}",
                "",
                "### Thesis",
                "",
                f"- Thesis id: {thesis['thesis_id']}",
                f"- Current impact: {thesis['impact']}",
                f"- Working thesis: {thesis['working_thesis']}",
                f"- Decision question: {thesis['decision_question']}",
                "",
                "### Catalyst",
                "",
                f"- Catalyst id: {catalyst['id']}",
                f"- Event: {catalyst['event_type']} ({catalyst['window']})",
                f"- Status: {catalyst['status']}; confidence: {catalyst['confidence']}; score: {catalyst['catalyst_score']}",
                f"- Urgency: {catalyst['urgency']}; review: {catalyst['review_state']}; required action: {catalyst['required_review_action']}",
                "",
                "### Evidence",
                "",
                f"- Source ref: {evidence['source_ref']}",
                f"- Evidence checked at: {evidence['evidence_checked_at']}",
                "- Evidence URLs:",
            ]
        )
        for url in evidence["urls"]:  # type: ignore[index]
            lines.append(f"  - {url}")
        lines.extend(["", "### Scenarios", ""])
        for scenario in memo["scenarios"]:  # type: ignore[index]
            lines.append(
                f"- {scenario['scenario']}: score {scenario['score']}; impact {scenario['impact']}; date {scenario['date']}; action {scenario['review_action']}; note: {_markdown_cell(str(scenario['note']))}"
            )
        lines.extend(["", "### Broker Context", ""])
        average_target = "none" if broker["target_price_avg"] is None else _format_price(float(broker["target_price_avg"]))
        lines.append(
            f"- View count: {broker['view_count']}; target range: {broker['target_price_range']}; average target: {average_target}; stale views: {broker['stale_view_count']}"
        )
        for view in broker["views"]:  # type: ignore[index]
            lines.append(
                f"  - {view['institution']} {view['rating']} {_format_price(float(view['target_price']))} as of {view['as_of']}; caveat: {_markdown_cell(str(view['caveat']))}; source: {view['source_url']}"
            )
        if not broker["views"]:  # type: ignore[index]
            lines.append("  - No broker views recorded.")
        lines.extend(["", "### Watchlist Triggers", ""])
        for trigger in memo["watchlist_triggers"]:  # type: ignore[index]
            lines.append(f"- [{trigger['type']}] {trigger['condition']} -> {trigger['action']}")
        lines.extend(
            [
                "",
                "### Decision Slots",
                "",
                "- Pre-event decision: TBD",
                "- Position action: TBD",
                "- Risk limit or hedge: TBD",
                "- Follow-up owner: TBD",
                "",
                "### Post-Event Review",
                "",
                f"- Review due: {review['review_due']}",
                f"- Outcome: {review['outcome']}",
                f"- Thesis update: {review['thesis_update']}",
                f"- Evidence delta: {review['evidence_delta']}",
                f"- Scenario accuracy: {review['scenario_accuracy']}",
                f"- Next action: {review['next_action']}",
                "",
            ]
        )
    return "\n".join(lines)


def post_event_json(
    records: Iterable[CatalystRecord],
    as_of: date,
    review_after_days: int,
) -> Dict[str, object]:
    items = [_post_event_item(record, as_of, review_after_days) for record in _post_event_records(records, as_of, review_after_days)]
    return {
        "as_of": as_of.isoformat(),
        "review_after_days": review_after_days,
        "items": items,
        "summary": {
            "item_count": len(items),
            "completed_count": sum(1 for item in items if item["status"] == "completed"),
            "overdue_count": sum(1 for item in items if item["post_event_state"] == "overdue"),
            "missing_outcome_count": sum(1 for item in items if item["outcome_state"] == "missing_outcome"),
            "missing_recorded_at_count": sum(1 for item in items if item["recorded_at_state"] == "missing_recorded_at"),
        },
    }


def post_event_markdown(
    records: Iterable[CatalystRecord],
    as_of: date,
    review_after_days: int,
) -> str:
    payload = post_event_json(records, as_of, review_after_days)
    lines = [
        "# Market Catalyst Post-Event Review",
        "",
        f"As of: {as_of.isoformat()}",
        f"Scope: completed catalysts plus events whose window ended at least {review_after_days} days ago and still need outcome review.",
        "",
    ]
    if not payload["items"]:
        lines.extend(["No catalysts need post-event outcome review.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| State | Due | Ticker | Catalyst | Status | Outcome | Recorded At |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["items"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["post_event_state"]),
                    str(item["review_due"]),
                    str(item["ticker"]),
                    f"{item['event_type']} {item['window']}",
                    str(item["status"]),
                    _markdown_cell(str(item["actual_outcome"])),
                    str(item["outcome_recorded_at"]),
                ]
            )
            + " |"
        )
    lines.append("")
    for item in payload["items"]:
        template = item["outcome_review_template"]  # type: ignore[index]
        lines.extend(
            [
                f"## {item['ticker']} - {item['entity']}",
                "",
                f"- Catalyst id: {item['id']}",
                f"- Review state: {item['post_event_state']}; due: {item['review_due']}; days since window end: {item['days_since_window_end']}",
                f"- Status: {item['status']}; recorded outcome: {item['actual_outcome']}; recorded at: {item['outcome_recorded_at']}",
                f"- Thesis id: {item['thesis_id']}; pre-event base case: {_markdown_cell(str(item['base_scenario']))}",
                "",
                "### Outcome Review Template",
                "",
                f"- Actual outcome: {template['actual_outcome']}",
                f"- Outcome recorded at: {template['outcome_recorded_at']}",
                f"- Thesis impact after event: {template['thesis_impact_after_event']}",
                f"- Scenario accuracy: {_format_template_mapping(template['scenario_accuracy'])}",
                f"- Evidence delta: {template['evidence_delta']}",
                f"- Position or risk action: {template['position_or_risk_action']}",
                f"- Follow-up action: {template['follow_up_action']}",
                f"- Source update needed: {template['source_update_needed']}",
                "",
            ]
        )
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


def _decision_log_records(records: Iterable[CatalystRecord], as_of: date, days: int, stale_after_days: int) -> List[CatalystRecord]:
    return _watchlist_records(records, as_of, days, stale_after_days)


def _post_event_records(records: Iterable[CatalystRecord], as_of: date, review_after_days: int) -> List[CatalystRecord]:
    selected = []
    for record in records:
        if record.status == "cancelled":
            continue
        review_due = record.window.end + timedelta(days=review_after_days)
        has_review_gap = record.actual_outcome is None or record.outcome_recorded_at is None
        if has_review_gap and (record.status == "completed" or review_due <= as_of):
            selected.append(record)
    return sorted(selected, key=lambda record: _post_event_sort_key(record, as_of, review_after_days))


def _post_event_sort_key(record: CatalystRecord, as_of: date, review_after_days: int) -> tuple[object, ...]:
    review_due = record.window.end + timedelta(days=review_after_days)
    completed_rank = 0 if record.status == "completed" else 1
    overdue_days = max(0, (as_of - review_due).days)
    return (completed_rank, -overdue_days, review_due, record.window.end, record.ticker, record.record_id)


def _post_event_item(record: CatalystRecord, as_of: date, review_after_days: int) -> Dict[str, object]:
    score = score_record(record, as_of)
    review_due = record.window.end + timedelta(days=review_after_days)
    days_since_end = (as_of - record.window.end).days
    return {
        "id": record.record_id,
        "ticker": record.ticker,
        "entity": record.entity,
        "event_type": record.event_type,
        "window": record.window.label,
        "status": record.status,
        "confidence": record.confidence,
        "catalyst_score": score.catalyst_score,
        "review_due": review_due.isoformat(),
        "days_since_window_end": days_since_end,
        "post_event_state": "overdue" if review_due <= as_of else "completed_pending_review",
        "outcome_state": "recorded" if record.actual_outcome is not None else "missing_outcome",
        "recorded_at_state": "recorded" if record.outcome_recorded_at is not None else "missing_recorded_at",
        "actual_outcome": record.actual_outcome or "TBD",
        "outcome_recorded_at": record.outcome_recorded_at.isoformat() if record.outcome_recorded_at else "TBD",
        "required_review_action": record.required_review_action,
        "thesis_id": record.thesis_id or "unmapped",
        "thesis_impact": record.thesis_impact,
        "base_scenario": record.scenario_notes.get("base", ""),
        "evidence_urls": list(record.evidence_urls),
        "source_ref": record.source_ref or "none",
        "outcome_review_template": _outcome_review_template(record, as_of),
    }


def _outcome_review_template(record: CatalystRecord, as_of: date) -> Dict[str, object]:
    return {
        "actual_outcome": record.actual_outcome or "TBD",
        "outcome_recorded_at": record.outcome_recorded_at.isoformat() if record.outcome_recorded_at else as_of.isoformat(),
        "thesis_impact_after_event": "TBD",
        "scenario_accuracy": {
            "best_matching_scenario": "TBD",
            "bull_case_hit": "TBD",
            "base_case_hit": "TBD",
            "bear_case_hit": "TBD",
            "miss_reason": "TBD",
        },
        "evidence_delta": "TBD",
        "position_or_risk_action": "TBD",
        "follow_up_action": "TBD",
        "source_update_needed": record.required_review_action in {"verify_source", "refresh_evidence"},
    }


def _format_template_mapping(value: object) -> str:
    if not isinstance(value, dict):
        return str(value)
    return "; ".join(f"{str(key).replace('_', ' ')}: {value[key]}" for key in sorted(value))


def _decision_memo(record: CatalystRecord, as_of: date, stale_after_days: int) -> Dict[str, object]:
    score = score_record(record, as_of, stale_after_days=stale_after_days)
    scenario_record = _scenario_matrix_record(record, as_of, stale_after_days)
    watch_item = _watchlist_item(record, as_of, stale_after_days)
    return {
        "memo_id": f"decision-{record.record_id}",
        "prepared_on": as_of.isoformat(),
        "decision_owner": "TBD",
        "decision_status": "draft",
        "ticker": record.ticker,
        "entity": record.entity,
        "thesis": {
            "thesis_id": record.thesis_id or "unmapped",
            "impact": record.thesis_impact,
            "working_thesis": record.scenario_notes.get("base", ""),
            "decision_question": f"Does the {record.event_type.replace('_', ' ')} change the thesis for {record.ticker}?",
        },
        "catalyst": {
            "id": record.record_id,
            "event_type": record.event_type,
            "window": record.window.label,
            "status": record.status,
            "confidence": record.confidence,
            "catalyst_score": score.catalyst_score,
            "days_until": score.days_until,
            "urgency": score.urgency,
            "review_state": score.review_state,
            "required_review_action": record.required_review_action,
        },
        "evidence": {
            "source_ref": record.source_ref or "none",
            "evidence_checked_at": record.evidence_checked_at.isoformat() if record.evidence_checked_at else "missing",
            "urls": list(record.evidence_urls),
            "last_reviewed": record.last_reviewed.isoformat() if record.last_reviewed else "missing",
        },
        "scenarios": scenario_record["scenarios"],
        "broker_context": _decision_broker_context(record, as_of, stale_after_days),
        "watchlist_triggers": watch_item["trigger_conditions"],
        "decision_slots": {
            "pre_event_decision": "TBD",
            "position_action": "TBD",
            "risk_limit_or_hedge": "TBD",
            "follow_up_owner": "TBD",
        },
        "post_event_review": {
            "review_due": record.window.end.isoformat(),
            "outcome": "TBD",
            "thesis_update": "TBD",
            "evidence_delta": "TBD",
            "scenario_accuracy": "TBD",
            "next_action": "TBD",
        },
    }


def _decision_broker_context(record: CatalystRecord, as_of: date, stale_after_days: int) -> Dict[str, object]:
    views = [
        {
            "age_days": (as_of - view.as_of).days,
            "as_of": view.as_of.isoformat(),
            "caveat": view.caveat,
            "institution": view.institution,
            "rating": view.rating,
            "source_url": view.source_url,
            "stale_source": (as_of - view.as_of).days > stale_after_days,
            "target_price": view.target_price,
        }
        for view in record.broker_views
    ]
    views = sorted(views, key=lambda view: (str(view["institution"]), str(view["as_of"]), str(view["rating"]), float(view["target_price"])))
    targets = [float(view["target_price"]) for view in views]
    return {
        "target_price_avg": round(sum(targets) / len(targets), 2) if targets else None,
        "target_price_range": f"{_format_price(min(targets))}-{_format_price(max(targets))}" if targets else "none",
        "stale_view_count": sum(1 for view in views if view["stale_source"]),
        "view_count": len(views),
        "views": views,
    }


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


def _source_pack_sources(records: Iterable[CatalystRecord], as_of: date, fresh_after_days: int) -> List[Dict[str, object]]:
    sources: Dict[str, Dict[str, object]] = {}
    for record in records:
        thesis_id = record.thesis_id or "unmapped"
        for url in record.evidence_urls:
            source = _source_pack_entry(sources, url)
            _source_pack_add_record(source, record, thesis_id, "evidence")
            checked = record.evidence_checked_at
            if checked is not None:
                source["evidence_checked_dates"].add(checked.isoformat())  # type: ignore[union-attr]
                source["freshness_dates"].append(checked)  # type: ignore[union-attr]
        for view in record.broker_views:
            source = _source_pack_entry(sources, view.source_url)
            _source_pack_add_record(source, record, thesis_id, "broker")
            source["broker_institutions"].add(view.institution)  # type: ignore[union-attr]
            source["broker_as_of_dates"].add(view.as_of.isoformat())  # type: ignore[union-attr]
            source["freshness_dates"].append(view.as_of)  # type: ignore[union-attr]

    normalized = []
    for source in sources.values():
        freshness_dates = source["freshness_dates"]  # type: ignore[assignment]
        latest = max(freshness_dates) if freshness_dates else None
        age_days = (as_of - latest).days if latest is not None else None
        if age_days is None:
            freshness_state = "missing"
        elif age_days > fresh_after_days:
            freshness_state = "stale"
        else:
            freshness_state = "fresh"
        normalized.append(
            {
                "broker_as_of_dates": sorted(source["broker_as_of_dates"]),  # type: ignore[arg-type]
                "broker_institutions": sorted(source["broker_institutions"]),  # type: ignore[arg-type]
                "evidence_checked_at": latest.isoformat() if latest is not None else "missing",
                "evidence_checked_dates": sorted(source["evidence_checked_dates"]),  # type: ignore[arg-type]
                "freshness_age_days": age_days if age_days is not None else "missing",
                "freshness_state": freshness_state,
                "record_ids": sorted(source["record_ids"]),  # type: ignore[arg-type]
                "source_types": sorted(source["source_types"]),  # type: ignore[arg-type]
                "thesis_ids": sorted(source["thesis_ids"]),  # type: ignore[arg-type]
                "tickers": sorted(source["tickers"]),  # type: ignore[arg-type]
                "url": source["url"],
                "usage_count": source["usage_count"],
            }
        )
    return sorted(
        normalized,
        key=lambda source: (
            {"missing": 0, "stale": 1, "fresh": 2}.get(str(source["freshness_state"]), 3),
            -int(source["usage_count"]),
            str(source["url"]),
        ),
    )


def _source_pack_entry(sources: Dict[str, Dict[str, object]], url: str) -> Dict[str, object]:
    return sources.setdefault(
        url,
        {
            "broker_as_of_dates": set(),
            "broker_institutions": set(),
            "evidence_checked_dates": set(),
            "freshness_dates": [],
            "record_ids": set(),
            "source_types": set(),
            "thesis_ids": set(),
            "tickers": set(),
            "url": url,
            "usage_count": 0,
        },
    )


def _source_pack_add_record(source: Dict[str, object], record: CatalystRecord, thesis_id: str, source_type: str) -> None:
    source["usage_count"] = int(source["usage_count"]) + 1
    source["record_ids"].add(record.record_id)  # type: ignore[union-attr]
    source["source_types"].add(source_type)  # type: ignore[union-attr]
    source["thesis_ids"].add(thesis_id)  # type: ignore[union-attr]
    source["tickers"].add(record.ticker)  # type: ignore[union-attr]


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
