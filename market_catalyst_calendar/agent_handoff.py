"""Investment research agent handoff pack rendering."""

from __future__ import annotations

import shlex
from collections import Counter
from datetime import date
from typing import Dict, Iterable, List, Sequence

from .models import CatalystRecord, Dataset, sorted_records
from .scoring import score_record


OPEN_STATUSES = {"rumored", "watching", "scheduled", "confirmed", "delayed"}


def agent_handoff_json(
    dataset: Dataset,
    as_of: date,
    dataset_path: str = "dataset.json",
    output_dir: str = "reports",
    days: int = 45,
    stale_after_days: int = 14,
    fresh_after_days: int = 14,
    top_limit: int = 5,
) -> Dict[str, object]:
    """Build a compact machine-readable context pack for a downstream agent."""

    records = sorted_records(dataset.records)
    upcoming = [record for record in records if _is_upcoming(record, as_of, days)]
    stale_items = _stale_items(records, as_of, stale_after_days, top_limit)
    top_risks = _top_risks(records, as_of, stale_after_days, fresh_after_days, top_limit)
    source_urls = _source_urls(records, as_of, fresh_after_days)
    commands = _commands_to_run_next(dataset_path, output_dir, as_of, days, stale_after_days, fresh_after_days, top_risks, stale_items)

    return {
        "schema_version": "agent-handoff/v1",
        "as_of": as_of.isoformat(),
        "generated_by": "market-catalyst-calendar agent-handoff",
        "handoff_objective": (
            "Refresh stale evidence, verify top catalyst risks, and prepare the next investment research packet "
            "without fetching or inventing sources inside this handoff."
        ),
        "parameters": {
            "dataset_path": dataset_path,
            "output_dir": output_dir,
            "days": days,
            "stale_after_days": stale_after_days,
            "fresh_after_days": fresh_after_days,
            "top_limit": top_limit,
        },
        "dataset_summary": _dataset_summary(records, upcoming, as_of, stale_after_days, fresh_after_days),
        "top_risks": top_risks,
        "stale_items": stale_items,
        "commands_to_run_next": commands,
        "source_urls": source_urls,
    }


def agent_handoff_markdown(
    dataset: Dataset,
    as_of: date,
    dataset_path: str = "dataset.json",
    output_dir: str = "reports",
    days: int = 45,
    stale_after_days: int = 14,
    fresh_after_days: int = 14,
    top_limit: int = 5,
) -> str:
    payload = agent_handoff_json(dataset, as_of, dataset_path, output_dir, days, stale_after_days, fresh_after_days, top_limit)
    summary = payload["dataset_summary"]  # type: ignore[index]
    lines = [
        "# Agent Handoff Pack",
        "",
        f"As of: {payload['as_of']}",
        f"Dataset path in commands: `{dataset_path}`",
        f"Output directory in commands: `{output_dir}`",
        "",
        "## Dataset Summary",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Records | {summary['record_count']} |",
        f"| Open records | {summary['open_record_count']} |",
        f"| Upcoming records | {summary['upcoming_record_count']} |",
        f"| Stale review records | {summary['stale_review_count']} |",
        f"| Stale evidence records | {summary['stale_evidence_count']} |",
        f"| Missing evidence freshness | {summary['missing_evidence_freshness_count']} |",
        f"| Source URLs | {summary['source_url_count']} |",
        f"| Broker views | {summary['broker_view_count']} |",
        "",
        "## Top Risks",
        "",
    ]
    top_risks = payload["top_risks"]  # type: ignore[index]
    if top_risks:
        lines.extend(
            [
                "| Rank | Ticker | Score | Window | Flags | Next action |",
                "| ---: | --- | ---: | --- | --- | --- |",
            ]
        )
        for item in top_risks:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(item["rank"]),
                        str(item["ticker"]),
                        str(item["catalyst_score"]),
                        str(item["window"]),
                        ", ".join(str(flag) for flag in item["risk_flags"]),
                        _markdown_cell(str(item["next_action"])),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No top risks selected.")

    lines.extend(["", "## Stale Items", ""])
    stale_items = payload["stale_items"]  # type: ignore[index]
    if stale_items:
        lines.extend(["| Ticker | Record | Review age | Evidence age | Action |", "| --- | --- | ---: | ---: | --- |"])
        for item in stale_items:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(item["ticker"]),
                        str(item["id"]),
                        str(item["review_age_days"]),
                        str(item["evidence_age_days"]),
                        _markdown_cell(str(item["next_action"])),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No stale items selected.")

    lines.extend(["", "## Commands To Run Next", "", "```bash", f"mkdir -p {shlex.quote(output_dir)}"])
    for command in payload["commands_to_run_next"]:  # type: ignore[index]
        lines.append(str(command["command"]))
    lines.extend(["```", "", "## Source URLs", ""])
    source_urls = payload["source_urls"]  # type: ignore[index]
    if source_urls:
        lines.extend(["| Freshness | Type | Tickers | URL |", "| --- | --- | --- | --- |"])
        for source in source_urls:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(source["freshness_state"]),
                        ", ".join(str(item) for item in source["source_types"]),
                        ", ".join(str(item) for item in source["tickers"]),
                        str(source["url"]),
                    ]
                )
                + " |"
            )
    else:
        lines.append("No source URLs recorded.")
    lines.append("")
    return "\n".join(lines)


def _dataset_summary(
    records: Sequence[CatalystRecord],
    upcoming: Sequence[CatalystRecord],
    as_of: date,
    stale_after_days: int,
    fresh_after_days: int,
) -> Dict[str, object]:
    status_counts = Counter(record.status for record in records)
    event_counts = Counter(record.event_type for record in records)
    urgency_counts = Counter(score_record(record, as_of, stale_after_days=stale_after_days).urgency for record in records)
    source_urls = {url for record in records for url in record.evidence_urls}
    source_urls.update(view.source_url for record in records for view in record.broker_views)
    return {
        "record_count": len(records),
        "open_record_count": sum(1 for record in records if record.status in OPEN_STATUSES),
        "upcoming_record_count": len(upcoming),
        "completed_or_cancelled_count": sum(1 for record in records if record.status in {"completed", "cancelled"}),
        "stale_review_count": sum(
            1 for record in records if score_record(record, as_of, stale_after_days=stale_after_days).review_state == "stale"
        ),
        "stale_evidence_count": sum(1 for record in records if _evidence_state(record, as_of, fresh_after_days) == "stale"),
        "missing_evidence_freshness_count": sum(1 for record in records if _evidence_state(record, as_of, fresh_after_days) == "missing"),
        "source_url_count": len(source_urls),
        "broker_view_count": sum(len(record.broker_views) for record in records),
        "status_counts": dict(sorted(status_counts.items())),
        "event_type_counts": dict(sorted(event_counts.items())),
        "urgency_counts": dict(sorted(urgency_counts.items())),
        "tickers": sorted({record.ticker for record in records}),
        "thesis_ids": sorted({record.thesis_id for record in records if record.thesis_id}),
    }


def _top_risks(
    records: Sequence[CatalystRecord],
    as_of: date,
    stale_after_days: int,
    fresh_after_days: int,
    limit: int,
) -> List[Dict[str, object]]:
    ranked = []
    for record in records:
        score = score_record(record, as_of, stale_after_days=stale_after_days)
        flags = _risk_flags(record, as_of, score.review_state, fresh_after_days)
        if not flags and score.urgency not in {"high", "overdue"}:
            continue
        priority = score.catalyst_score + (20 if "over_budget" in flags else 0) + (12 if "stale_evidence" in flags else 0) + (8 if "stale_review" in flags else 0)
        ranked.append((priority, record.window.start, record.ticker, record.record_id, record, score, flags))
    selected = sorted(ranked, key=lambda item: (-item[0], item[1], item[2], item[3]))[:limit]
    return [_risk_item(rank, record, score, flags) for rank, (_, _, _, _, record, score, flags) in enumerate(selected, start=1)]


def _risk_item(rank: int, record: CatalystRecord, score, flags: Sequence[str]) -> Dict[str, object]:
    expected_loss = (record.max_loss or 0.0) * record.confidence * score.catalyst_score / 100
    return {
        "rank": rank,
        "id": record.record_id,
        "ticker": record.ticker,
        "entity": record.entity,
        "event_type": record.event_type,
        "window": record.window.label,
        "status": record.status,
        "thesis_id": record.thesis_id or "unmapped",
        "catalyst_score": score.catalyst_score,
        "urgency": score.urgency,
        "review_state": score.review_state,
        "days_until": score.days_until,
        "confidence": record.confidence,
        "portfolio_weight": record.portfolio_weight,
        "risk_budget": record.risk_budget,
        "max_loss": record.max_loss,
        "expected_event_loss": round(expected_loss, 2),
        "risk_flags": list(flags),
        "next_action": _next_action(record, score.review_state, flags),
        "source_urls": list(record.evidence_urls) + [view.source_url for view in record.broker_views],
    }


def _stale_items(records: Sequence[CatalystRecord], as_of: date, stale_after_days: int, limit: int) -> List[Dict[str, object]]:
    stale = []
    for record in records:
        score = score_record(record, as_of, stale_after_days=stale_after_days)
        review_age = (as_of - record.last_reviewed).days if record.last_reviewed else "missing"
        evidence_age = (as_of - record.evidence_checked_at).days if record.evidence_checked_at else "missing"
        if score.review_state != "stale" and evidence_age != "missing" and int(evidence_age) <= stale_after_days:
            continue
        stale.append((score.review_state != "stale", record.window.start, record.ticker, record.record_id, record, score, review_age, evidence_age))
    selected = sorted(stale, key=lambda item: (item[0], item[1], item[2], item[3]))[:limit]
    return [
        {
            "id": record.record_id,
            "ticker": record.ticker,
            "entity": record.entity,
            "event_type": record.event_type,
            "window": record.window.label,
            "status": record.status,
            "review_state": score.review_state,
            "review_age_days": review_age,
            "evidence_age_days": evidence_age,
            "required_review_action": record.required_review_action,
            "next_action": _next_action(record, score.review_state, _risk_flags(record, as_of, score.review_state, stale_after_days)),
            "evidence_urls": list(record.evidence_urls),
        }
        for _, _, _, _, record, score, review_age, evidence_age in selected
    ]


def _source_urls(records: Sequence[CatalystRecord], as_of: date, fresh_after_days: int) -> List[Dict[str, object]]:
    sources: Dict[str, Dict[str, object]] = {}
    for record in records:
        for url in record.evidence_urls:
            source = _source_entry(sources, url)
            _source_add_record(source, record, "evidence")
            if record.evidence_checked_at:
                source["freshness_dates"].append(record.evidence_checked_at)  # type: ignore[union-attr]
        for view in record.broker_views:
            source = _source_entry(sources, view.source_url)
            _source_add_record(source, record, "broker")
            source["broker_institutions"].add(view.institution)  # type: ignore[union-attr]
            source["freshness_dates"].append(view.as_of)  # type: ignore[union-attr]

    normalized = []
    for source in sources.values():
        dates = source["freshness_dates"]  # type: ignore[assignment]
        latest = max(dates) if dates else None
        age = (as_of - latest).days if latest else None
        if age is None:
            state = "missing"
        elif age > fresh_after_days:
            state = "stale"
        else:
            state = "fresh"
        normalized.append(
            {
                "url": source["url"],
                "source_types": sorted(source["source_types"]),  # type: ignore[arg-type]
                "tickers": sorted(source["tickers"]),  # type: ignore[arg-type]
                "record_ids": sorted(source["record_ids"]),  # type: ignore[arg-type]
                "thesis_ids": sorted(source["thesis_ids"]),  # type: ignore[arg-type]
                "freshness_state": state,
                "freshness_age_days": age if age is not None else "missing",
                "latest_checked_at": latest.isoformat() if latest else "missing",
                "broker_institutions": sorted(source["broker_institutions"]),  # type: ignore[arg-type]
            }
        )
    return sorted(normalized, key=lambda source: ({"missing": 0, "stale": 1, "fresh": 2}[str(source["freshness_state"])], str(source["url"])))


def _commands_to_run_next(
    dataset_path: str,
    output_dir: str,
    as_of: date,
    days: int,
    stale_after_days: int,
    fresh_after_days: int,
    top_risks: Sequence[Dict[str, object]],
    stale_items: Sequence[Dict[str, object]],
) -> List[Dict[str, object]]:
    dataset = shlex.quote(dataset_path)
    out = _OutputPaths(output_dir)
    commands = [
        _command("validate-public", f"python -m market_catalyst_calendar validate --profile public --input {dataset} --as-of {as_of.isoformat()} > {out.qpath('validate_public.json')} || test $? -eq 1", out.path("validate_public.json"), "Refresh release diagnostics before trusting the handoff."),
        _command("quality-gate", f"python -m market_catalyst_calendar quality-gate --profile public --input {dataset} --as-of {as_of.isoformat()} > {out.qpath('quality_gate.json')} || test $? -eq 1", out.path("quality_gate.json"), "Collect blocking publication and evidence issues."),
        _command("source-pack", f"python -m market_catalyst_calendar source-pack --input {dataset} --as-of {as_of.isoformat()} --fresh-after-days {fresh_after_days} > {out.qpath('source_pack.json')}", out.path("source_pack.json"), "Give the research agent the deduplicated URL collection queue."),
        _command("review-plan", f"python -m market_catalyst_calendar review-plan --input {dataset} --as-of {as_of.isoformat()} --days {days} --stale-after-days {stale_after_days} --format markdown > {out.qpath('review_plan.md')}", out.path("review_plan.md"), "Turn stale and high-urgency catalysts into analyst actions."),
        _command("decision-log", f"python -m market_catalyst_calendar decision-log --input {dataset} --as-of {as_of.isoformat()} --days {days} --stale-after-days {stale_after_days} --format markdown > {out.qpath('decision_log.md')}", out.path("decision_log.md"), "Prepare decision memo stubs for the forward window."),
    ]
    tickers = []
    for item in list(top_risks) + list(stale_items):
        ticker = str(item["ticker"])
        if ticker not in tickers:
            tickers.append(ticker)
    for ticker in tickers[:3]:
        safe_ticker = shlex.quote(ticker)
        lower = ticker.lower().replace("/", "_")
        commands.append(
            _command(
                f"drilldown-{ticker}",
                f"python -m market_catalyst_calendar drilldown --input {dataset} --as-of {as_of.isoformat()} --ticker {safe_ticker} --days {days} --format markdown > {out.qpath(f'drilldown_{lower}.md')}",
                out.path(f"drilldown_{lower}.md"),
                "Create a single-name dossier for one of the handoff priorities.",
            )
        )
    return commands


def _command(command_id: str, command: str, output_path: str, reason: str) -> Dict[str, object]:
    return {"id": command_id, "command": command, "output_path": output_path, "reason": reason}


def _risk_flags(record: CatalystRecord, as_of: date, review_state: str, fresh_after_days: int) -> List[str]:
    flags = []
    evidence_state = _evidence_state(record, as_of, fresh_after_days)
    if review_state == "stale":
        flags.append("stale_review")
    if evidence_state == "stale":
        flags.append("stale_evidence")
    if evidence_state == "missing":
        flags.append("missing_evidence_freshness")
    if record.risk_budget is not None and record.max_loss is not None and record.max_loss > record.risk_budget:
        flags.append("over_budget")
    if record.risk_budget is None and record.max_loss is not None:
        flags.append("missing_risk_budget")
    if record.required_review_action != "none":
        flags.append(f"review_action:{record.required_review_action}")
    return flags


def _next_action(record: CatalystRecord, review_state: str, flags: Sequence[str]) -> str:
    if "over_budget" in flags:
        return "Verify downside estimate, update risk budget, and escalate before the event window."
    if "missing_evidence_freshness" in flags or "stale_evidence" in flags:
        return "Re-check evidence URLs, update evidence_checked_at, and refresh scenario notes."
    if review_state == "stale":
        return f"Refresh analyst review and resolve required action `{record.required_review_action}`."
    if record.required_review_action != "none":
        return f"Complete required review action `{record.required_review_action}`."
    return "Monitor event timing and preserve source links."


def _evidence_state(record: CatalystRecord, as_of: date, fresh_after_days: int) -> str:
    if record.evidence_checked_at is None:
        return "missing"
    return "stale" if (as_of - record.evidence_checked_at).days > fresh_after_days else "fresh"


def _is_upcoming(record: CatalystRecord, as_of: date, days: int) -> bool:
    return record.status in OPEN_STATUSES and 0 <= (record.window.start - as_of).days <= days


def _source_entry(sources: Dict[str, Dict[str, object]], url: str) -> Dict[str, object]:
    return sources.setdefault(
        url,
        {
            "url": url,
            "source_types": set(),
            "tickers": set(),
            "record_ids": set(),
            "thesis_ids": set(),
            "freshness_dates": [],
            "broker_institutions": set(),
        },
    )


def _source_add_record(source: Dict[str, object], record: CatalystRecord, source_type: str) -> None:
    source["source_types"].add(source_type)  # type: ignore[union-attr]
    source["tickers"].add(record.ticker)  # type: ignore[union-attr]
    source["record_ids"].add(record.record_id)  # type: ignore[union-attr]
    source["thesis_ids"].add(record.thesis_id or "unmapped")  # type: ignore[union-attr]


def _markdown_cell(value: str) -> str:
    return value.replace("\n", " ").replace("|", "\\|")


class _OutputPaths:
    def __init__(self, output_dir: str) -> None:
        self.output_dir = output_dir.rstrip("/") or "."

    def path(self, name: str) -> str:
        return f"{self.output_dir}/{name}" if self.output_dir != "." else name

    def qpath(self, name: str) -> str:
        return shlex.quote(self.path(name))
