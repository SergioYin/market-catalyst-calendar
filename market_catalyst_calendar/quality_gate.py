"""Public research dataset quality gate."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .models import CatalystRecord, sorted_records


REQUIRED_SCENARIOS = ("bull", "base", "bear")
PLACEHOLDER_HOSTS = {
    "example.com",
    "example.net",
    "example.org",
    "localhost",
}
PLACEHOLDER_TERMS = ("placeholder", "sample", "dummy", "todo", "tbd")


def quality_gate_json(
    records: Iterable[CatalystRecord],
    as_of: date,
    min_evidence_urls: int,
    max_review_age_days: int,
    max_evidence_age_days: int,
    max_broker_age_days: int,
) -> Dict[str, object]:
    """Return deterministic pass/fail quality-gate output for public research data."""

    items = [
        _record_gate(
            record,
            as_of,
            min_evidence_urls,
            max_review_age_days,
            max_evidence_age_days,
            max_broker_age_days,
        )
        for record in sorted_records(records)
    ]
    failing = [item for item in items if item["status"] == "fail"]
    rule_counts = Counter(issue["rule"] for item in items for issue in item["issues"])  # type: ignore[index]
    severity_counts = Counter(issue["severity"] for item in items for issue in item["issues"])  # type: ignore[index]
    return {
        "as_of": as_of.isoformat(),
        "ok": not failing,
        "policy": {
            "max_broker_age_days": max_broker_age_days,
            "max_evidence_age_days": max_evidence_age_days,
            "max_review_age_days": max_review_age_days,
            "min_evidence_urls": min_evidence_urls,
            "placeholder_hosts": sorted(PLACEHOLDER_HOSTS),
            "required_scenarios": list(REQUIRED_SCENARIOS),
        },
        "records": failing,
        "summary": {
            "failed_record_count": len(failing),
            "record_count": len(items),
            "rule_counts": dict(sorted(rule_counts.items())),
            "severity_counts": dict(sorted(severity_counts.items())),
        },
    }


def quality_gate_markdown(
    records: Iterable[CatalystRecord],
    as_of: date,
    min_evidence_urls: int,
    max_review_age_days: int,
    max_evidence_age_days: int,
    max_broker_age_days: int,
) -> str:
    payload = quality_gate_json(
        records,
        as_of,
        min_evidence_urls,
        max_review_age_days,
        max_evidence_age_days,
        max_broker_age_days,
    )
    summary = payload["summary"]
    status = "PASS" if payload["ok"] else "FAIL"
    lines = [
        "# Market Catalyst Quality Gate",
        "",
        f"Status: {status}",
        f"As of: {as_of.isoformat()}",
        f"Minimum evidence URLs: {min_evidence_urls}",
        f"Maximum review age: {max_review_age_days} days",
        f"Maximum evidence age: {max_evidence_age_days} days",
        f"Maximum broker age: {max_broker_age_days} days",
        "",
        f"Failed records: {summary['failed_record_count']} of {summary['record_count']}",  # type: ignore[index]
        "",
    ]
    records_payload = payload["records"]
    if not records_payload:
        lines.extend(["All records passed the public research quality gate.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Severity | Rule | Ticker | Record | Detail |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in records_payload:  # type: ignore[assignment]
        for issue in item["issues"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(issue["severity"]),
                        str(issue["rule"]),
                        str(item["ticker"]),
                        str(item["id"]),
                        _markdown_cell(str(issue["detail"])),
                    ]
                )
                + " |"
            )
    lines.append("")
    for item in records_payload:  # type: ignore[assignment]
        lines.extend(
            [
                f"## {item['ticker']} - {item['entity']}",
                "",
                f"- Record: {item['id']}",
                f"- Window: {item['window']}; status: {item['record_status']}",
                f"- Failed rules: {', '.join(str(rule) for rule in item['failed_rules'])}",
                f"- Next action: {item['next_action']}",
                "",
            ]
        )
    return "\n".join(lines)


def _record_gate(
    record: CatalystRecord,
    as_of: date,
    min_evidence_urls: int,
    max_review_age_days: int,
    max_evidence_age_days: int,
    max_broker_age_days: int,
) -> Dict[str, object]:
    issues: List[Dict[str, object]] = []
    _check_minimum_evidence(record, as_of, min_evidence_urls, max_evidence_age_days, issues)
    _check_scenario_completeness(record, issues)
    _check_review_freshness(record, as_of, max_review_age_days, issues)
    _check_placeholder_urls(record, issues)
    _check_broker_caveats(record, as_of, max_broker_age_days, issues)
    failed_rules = sorted({str(issue["rule"]) for issue in issues})
    return {
        "entity": record.entity,
        "failed_rules": failed_rules,
        "id": record.record_id,
        "issues": issues,
        "next_action": _next_action(failed_rules),
        "status": "fail" if issues else "pass",
        "ticker": record.ticker,
        "window": record.window.label,
        "record_status": record.status,
    }


def _check_minimum_evidence(
    record: CatalystRecord,
    as_of: date,
    min_evidence_urls: int,
    max_evidence_age_days: int,
    issues: List[Dict[str, object]],
) -> None:
    if len(record.evidence_urls) < min_evidence_urls:
        _add_issue(
            issues,
            "minimum_evidence",
            "critical",
            f"{len(record.evidence_urls)} evidence URLs present; {min_evidence_urls} required",
        )
    if record.evidence_checked_at is None:
        _add_issue(issues, "minimum_evidence", "high", "evidence_checked_at is missing")
        return
    age_days = (as_of - record.evidence_checked_at).days
    if age_days > max_evidence_age_days:
        _add_issue(
            issues,
            "minimum_evidence",
            "high",
            f"evidence metadata is {age_days} days old; maximum is {max_evidence_age_days}",
        )


def _check_scenario_completeness(record: CatalystRecord, issues: List[Dict[str, object]]) -> None:
    for scenario in REQUIRED_SCENARIOS:
        note = record.scenario_notes.get(scenario, "").strip()
        if not note:
            _add_issue(issues, "scenario_completeness", "critical", f"{scenario} scenario note is missing")
        elif _looks_placeholder_text(note):
            _add_issue(issues, "scenario_completeness", "high", f"{scenario} scenario note looks like a placeholder")
        elif len(note) < 24:
            _add_issue(issues, "scenario_completeness", "medium", f"{scenario} scenario note is too thin for public research")


def _check_review_freshness(
    record: CatalystRecord,
    as_of: date,
    max_review_age_days: int,
    issues: List[Dict[str, object]],
) -> None:
    if record.last_reviewed is None:
        _add_issue(issues, "review_freshness", "high", "last_reviewed is missing")
        return
    age_days = (as_of - record.last_reviewed).days
    if age_days > max_review_age_days:
        _add_issue(
            issues,
            "review_freshness",
            "high",
            f"last review is {age_days} days old; maximum is {max_review_age_days}",
        )


def _check_placeholder_urls(record: CatalystRecord, issues: List[Dict[str, object]]) -> None:
    for url in record.evidence_urls:
        reason = _placeholder_url_reason(url)
        if reason:
            _add_issue(issues, "no_placeholder_urls", "critical", f"evidence URL {url} is {reason}")
    for view in record.broker_views:
        reason = _placeholder_url_reason(view.source_url)
        if reason:
            _add_issue(
                issues,
                "no_placeholder_urls",
                "critical",
                f"broker URL for {view.institution} ({view.source_url}) is {reason}",
            )


def _check_broker_caveats(
    record: CatalystRecord,
    as_of: date,
    max_broker_age_days: int,
    issues: List[Dict[str, object]],
) -> None:
    for view in record.broker_views:
        caveat = view.caveat.strip()
        if len(caveat) < 24:
            _add_issue(issues, "broker_caveats", "high", f"{view.institution} caveat is too thin")
        elif _looks_placeholder_text(caveat):
            _add_issue(issues, "broker_caveats", "high", f"{view.institution} caveat looks like a placeholder")
        age_days = (as_of - view.as_of).days
        if age_days > max_broker_age_days:
            _add_issue(
                issues,
                "broker_caveats",
                "medium",
                f"{view.institution} broker view is {age_days} days old; maximum is {max_broker_age_days}",
            )


def _placeholder_url_reason(url: str) -> Optional[str]:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if hostname in PLACEHOLDER_HOSTS or hostname.endswith(".example"):
        return "a placeholder host"
    lowered = url.lower()
    if any(term in lowered for term in PLACEHOLDER_TERMS):
        return "a placeholder URL"
    return None


def _looks_placeholder_text(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in PLACEHOLDER_TERMS)


def _add_issue(issues: List[Dict[str, object]], rule: str, severity: str, detail: str) -> None:
    issues.append({"detail": detail, "rule": rule, "severity": severity})


def _next_action(failed_rules: List[str]) -> str:
    if not failed_rules:
        return "No quality-gate action is required."
    actions = []
    if "minimum_evidence" in failed_rules:
        actions.append("add independent evidence URLs and refresh evidence metadata")
    if "scenario_completeness" in failed_rules:
        actions.append("complete substantive bull/base/bear scenario notes")
    if "review_freshness" in failed_rules:
        actions.append("refresh analyst review date")
    if "no_placeholder_urls" in failed_rules:
        actions.append("replace placeholder URLs with public source URLs")
    if "broker_caveats" in failed_rules:
        actions.append("refresh broker views and document explicit caveats")
    return "; ".join(actions) + "."


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
