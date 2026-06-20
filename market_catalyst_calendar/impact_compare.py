"""Compare deterministic impact-brief snapshots."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List, Optional

from .impact_brief import BOUNDARY, BOUNDARY_NOTE, impact_brief_json
from .models import parse_dataset


CHANGE_FIELDS = (
    "ticker",
    "entity",
    "event_type",
    "window",
    "status",
    "confidence",
    "thesis_impact",
    "impact_label",
    "urgency",
    "review_state",
    "required_review_action",
    "portfolio_weight",
    "weighted_attention",
    "risk_budget",
    "max_loss",
    "sector",
    "theme",
    "thesis_id",
    "source_ref",
    "evidence_checked_at",
    "broker_view_count",
)


def impact_compare_json(
    base_raw: Dict[str, Any],
    current_raw: Dict[str, Any],
    as_of: Optional[date],
    days: int,
    stale_after_days: int,
) -> Dict[str, object]:
    """Return deltas between two static datasets or impact-brief JSON snapshots."""

    base = _normalize_snapshot(base_raw, as_of, days, stale_after_days)
    current = _normalize_snapshot(current_raw, as_of, days, stale_after_days)
    base_by_id = _items_by_id(base["records"])
    current_by_id = _items_by_id(current["records"])
    base_ids = set(base_by_id)
    current_ids = set(current_by_id)

    added = [current_by_id[item_id] for item_id in sorted(current_ids - base_ids)]
    removed = [base_by_id[item_id] for item_id in sorted(base_ids - current_ids)]
    changed = [
        _changed_item(base_by_id[item_id], current_by_id[item_id])
        for item_id in sorted(base_ids & current_ids)
    ]
    changed = [item for item in changed if _has_change(item)]
    attention_delta = sum(int(item["attention_score"]) for item in current["records"]) - sum(
        int(item["attention_score"]) for item in base["records"]
    )

    return {
        "schema_version": "impact-compare/v1",
        "as_of": (as_of.isoformat() if as_of else str(current["as_of"])),
        "base_as_of": base["as_of"],
        "current_as_of": current["as_of"],
        "base_input_type": base["input_type"],
        "current_input_type": current["input_type"],
        "days": days,
        "stale_after_days": stale_after_days,
        "boundary_note": BOUNDARY_NOTE,
        "boundary": dict(BOUNDARY),
        "added": [_item_summary(item) for item in _sort_items(added)],
        "removed": [_item_summary(item) for item in _sort_items(removed)],
        "changed": changed,
        "summary": {
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
            "attention_score_movement_count": sum(1 for item in changed if item["attention_score_change"]["delta"] != 0),
            "evidence_state_movement_count": sum(1 for item in changed if item["evidence_state_transition"] is not None),
            "impact_flag_change_count": sum(1 for item in changed if item["impact_flag_change"]["changed"]),
            "impact_label_change_count": sum(1 for item in changed if item["impact_label_transition"] is not None),
            "aggregate_attention_delta": attention_delta,
        },
    }


def impact_compare_markdown(
    base_raw: Dict[str, Any],
    current_raw: Dict[str, Any],
    as_of: Optional[date],
    days: int,
    stale_after_days: int,
) -> str:
    """Render impact-brief deltas as Markdown."""

    payload = impact_compare_json(base_raw, current_raw, as_of, days, stale_after_days)
    summary = payload["summary"]  # type: ignore[index]
    lines = [
        "# Market Catalyst Impact Compare",
        "",
        f"As of: {payload['as_of']}",
        f"Base snapshot: {payload['base_as_of']} ({payload['base_input_type']})",
        f"Current snapshot: {payload['current_as_of']} ({payload['current_input_type']})",
        f"Scope: impact-brief records within {payload['days']} days; stale after {payload['stale_after_days']} days.",
        "",
        f"Boundary: {payload['boundary_note']}",
        "",
        (
            "Summary: "
            f"{summary['added_count']} added, "
            f"{summary['removed_count']} removed, "
            f"{summary['changed_count']} changed, "
            f"{summary['attention_score_movement_count']} attention-score movements, "
            f"{summary['evidence_state_movement_count']} evidence-state movements, "
            f"{summary['impact_flag_change_count']} impact-flag changes."
        ),
        "",
    ]
    _append_item_table(lines, "Added Catalysts", payload["added"])  # type: ignore[arg-type]
    _append_item_table(lines, "Removed Catalysts", payload["removed"])  # type: ignore[arg-type]
    changed = payload["changed"]  # type: ignore[assignment]
    lines.extend(["## Changed Catalysts", ""])
    if not changed:
        lines.extend(["No changed catalysts.", ""])
    else:
        lines.extend(
            [
                "| ID | Ticker | Attention | Evidence | Impact Flags | Impact Label | Fields |",
                "| --- | --- | ---: | --- | --- | --- | --- |",
            ]
        )
        for item in changed:  # type: ignore[union-attr]
            flag_change = item["impact_flag_change"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(item["id"]),
                        str(item["ticker"]),
                        _format_delta(int(item["attention_score_change"]["delta"])),
                        _transition_label(item["evidence_state_transition"]),
                        f"+{len(flag_change['added_flags'])}/-{len(flag_change['removed_flags'])}",
                        _transition_label(item["impact_label_transition"]),
                        ", ".join(str(change["field"]) for change in item["field_changes"]) or "none",
                    ]
                )
                + " |"
            )
        lines.append("")
        for item in changed:  # type: ignore[union-attr]
            attention = item["attention_score_change"]
            catalyst = item["catalyst_score_change"]
            flags = item["impact_flag_change"]
            lines.extend(
                [
                    f"### {item['ticker']} - {item['id']}",
                    "",
                    f"- Attention score: {attention['from']} -> {attention['to']} ({_format_delta(int(attention['delta']))})",
                    f"- Catalyst score: {catalyst['from']} -> {catalyst['to']} ({_format_delta(int(catalyst['delta']))})",
                    f"- Evidence state: {_transition_label(item['evidence_state_transition'])}",
                    f"- Impact flags: added {', '.join(flags['added_flags']) or 'none'}; removed {', '.join(flags['removed_flags']) or 'none'}",
                    f"- Impact label: {_transition_label(item['impact_label_transition'])}",
                ]
            )
            if item["field_changes"]:
                lines.append(
                    "- Other fields: "
                    + "; ".join(
                        f"{change['field']} {change['from']} -> {change['to']}" for change in item["field_changes"]
                    )
                )
            lines.append("")
    return "\n".join(lines)


def _normalize_snapshot(raw: Dict[str, Any], as_of: Optional[date], days: int, stale_after_days: int) -> Dict[str, Any]:
    if raw.get("schema_version") == "impact-brief/v1":
        records = raw.get("records")
        if not isinstance(records, list):
            raise ValueError("impact-brief snapshot records must be a list")
        return {
            "as_of": str(raw.get("as_of", "missing")),
            "input_type": "impact-brief",
            "records": [_normalize_item(item) for item in records],
        }
    dataset = parse_dataset(raw)
    brief_as_of = as_of or dataset.as_of
    payload = impact_brief_json(dataset.records, brief_as_of, days, stale_after_days)
    return {
        "as_of": payload["as_of"],
        "input_type": "dataset",
        "records": [_normalize_item(item) for item in payload["records"]],  # type: ignore[arg-type]
    }


def _normalize_item(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("impact-brief records must be objects")
    if "id" not in raw:
        raise ValueError("impact-brief records must include id")
    item = dict(raw)
    item["impact_flags"] = sorted(str(flag) for flag in item.get("impact_flags", []))
    return item


def _items_by_id(items: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(item["id"]): item for item in items}


def _sort_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(items, key=lambda item: (str(item.get("window", "")), str(item.get("ticker", "")), str(item["id"])))


def _item_summary(item: Dict[str, Any]) -> Dict[str, object]:
    return {
        "id": item["id"],
        "ticker": item.get("ticker", ""),
        "entity": item.get("entity", ""),
        "event_type": item.get("event_type", ""),
        "window": item.get("window", ""),
        "attention_score": item.get("attention_score", 0),
        "catalyst_score": item.get("catalyst_score", 0),
        "evidence_state": item.get("evidence_state", "missing"),
        "impact_label": item.get("impact_label", "unknown thesis context"),
        "impact_flags": list(item.get("impact_flags", [])),
    }


def _changed_item(base: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, object]:
    return {
        "id": current["id"],
        "ticker": current.get("ticker", ""),
        "entity": current.get("entity", ""),
        "event_type": current.get("event_type", ""),
        "window": current.get("window", ""),
        "attention_score_change": _numeric_change(base, current, "attention_score"),
        "catalyst_score_change": _numeric_change(base, current, "catalyst_score"),
        "urgency_transition": _transition(base.get("urgency"), current.get("urgency")),
        "review_state_transition": _transition(base.get("review_state"), current.get("review_state")),
        "evidence_state_transition": _transition(base.get("evidence_state"), current.get("evidence_state")),
        "impact_label_transition": _transition(base.get("impact_label"), current.get("impact_label")),
        "thesis_impact_transition": _transition(base.get("thesis_impact"), current.get("thesis_impact")),
        "impact_flag_change": _flag_change(base, current),
        "field_changes": _field_changes(base, current),
    }


def _has_change(item: Dict[str, object]) -> bool:
    flag_change = item["impact_flag_change"]  # type: ignore[assignment]
    return bool(
        item["attention_score_change"]["delta"]  # type: ignore[index]
        or item["catalyst_score_change"]["delta"]  # type: ignore[index]
        or item["urgency_transition"]
        or item["review_state_transition"]
        or item["evidence_state_transition"]
        or item["impact_label_transition"]
        or item["thesis_impact_transition"]
        or flag_change["changed"]  # type: ignore[index]
        or item["field_changes"]
    )


def _numeric_change(base: Dict[str, Any], current: Dict[str, Any], field: str) -> Dict[str, object]:
    before = int(base.get(field, 0))
    after = int(current.get(field, 0))
    return {"from": before, "to": after, "delta": after - before}


def _flag_change(base: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, object]:
    before = set(str(flag) for flag in base.get("impact_flags", []))
    after = set(str(flag) for flag in current.get("impact_flags", []))
    added = sorted(after - before)
    removed = sorted(before - after)
    return {
        "added_flags": added,
        "removed_flags": removed,
        "unchanged_flags": sorted(before & after),
        "changed": bool(added or removed),
    }


def _field_changes(base: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, object]]:
    changes = []
    for field in CHANGE_FIELDS:
        before = _value(base.get(field))
        after = _value(current.get(field))
        if before != after:
            changes.append({"field": field, "from": before, "to": after})
    return changes


def _transition(before: object, after: object) -> Optional[Dict[str, object]]:
    before_value = _value(before)
    after_value = _value(after)
    if before_value == after_value:
        return None
    return {"from": before_value, "to": after_value}


def _value(value: object) -> object:
    return "missing" if value is None else value


def _append_item_table(lines: List[str], title: str, items: object) -> None:
    lines.extend([f"## {title}", ""])
    if not items:
        lines.extend([f"No {title.lower()}.", ""])
        return
    lines.extend(["| Attention | Ticker | Window | Event | Evidence | Flags | ID |", "| ---: | --- | --- | --- | --- | --- | --- |"])
    for item in items:  # type: ignore[union-attr]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["attention_score"]),
                    str(item["ticker"]),
                    str(item["window"]),
                    str(item["event_type"]).replace("_", " "),
                    str(item["evidence_state"]),
                    ", ".join(str(flag) for flag in item["impact_flags"]) or "none",
                    str(item["id"]),
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
