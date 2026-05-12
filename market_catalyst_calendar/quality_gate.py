"""Public research dataset quality gate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
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
PROFILES = ("basic", "public", "strict")


@dataclass(frozen=True)
class QualityProfile:
    name: str
    min_evidence_urls: int
    max_review_age_days: Optional[int]
    max_evidence_age_days: Optional[int]
    max_broker_age_days: Optional[int]
    require_freshness_metadata: bool
    require_no_placeholder_urls: bool
    require_substantive_scenarios: bool
    require_broker_caveats: bool
    require_release_metadata: bool = False
    require_broker_views: bool = False
    min_scenario_note_chars: int = 24
    min_broker_caveat_chars: int = 24


QUALITY_PROFILES: Dict[str, QualityProfile] = {
    "basic": QualityProfile(
        name="basic",
        min_evidence_urls=1,
        max_review_age_days=None,
        max_evidence_age_days=None,
        max_broker_age_days=None,
        require_freshness_metadata=False,
        require_no_placeholder_urls=False,
        require_substantive_scenarios=False,
        require_broker_caveats=False,
    ),
    "public": QualityProfile(
        name="public",
        min_evidence_urls=2,
        max_review_age_days=14,
        max_evidence_age_days=14,
        max_broker_age_days=30,
        require_freshness_metadata=True,
        require_no_placeholder_urls=True,
        require_substantive_scenarios=True,
        require_broker_caveats=True,
    ),
    "strict": QualityProfile(
        name="strict",
        min_evidence_urls=3,
        max_review_age_days=7,
        max_evidence_age_days=7,
        max_broker_age_days=14,
        require_freshness_metadata=True,
        require_no_placeholder_urls=True,
        require_substantive_scenarios=True,
        require_broker_caveats=True,
        require_release_metadata=True,
        require_broker_views=True,
        min_scenario_note_chars=48,
        min_broker_caveat_chars=48,
    ),
}

DIAGNOSTIC_CODES = {
    ("minimum_evidence", "missing_url_count"): "MCC-QG-EVIDENCE-001",
    ("minimum_evidence", "missing_checked_at"): "MCC-QG-EVIDENCE-002",
    ("minimum_evidence", "stale_checked_at"): "MCC-QG-EVIDENCE-003",
    ("scenario_completeness", "missing_note"): "MCC-QG-SCENARIO-001",
    ("scenario_completeness", "placeholder_note"): "MCC-QG-SCENARIO-002",
    ("scenario_completeness", "thin_note"): "MCC-QG-SCENARIO-003",
    ("review_freshness", "missing_reviewed_at"): "MCC-QG-REVIEW-001",
    ("review_freshness", "stale_reviewed_at"): "MCC-QG-REVIEW-002",
    ("no_placeholder_urls", "placeholder_evidence_url"): "MCC-QG-SOURCE-001",
    ("no_placeholder_urls", "placeholder_broker_url"): "MCC-QG-SOURCE-002",
    ("broker_caveats", "missing_broker_views"): "MCC-QG-BROKER-001",
    ("broker_caveats", "thin_caveat"): "MCC-QG-BROKER-002",
    ("broker_caveats", "placeholder_caveat"): "MCC-QG-BROKER-003",
    ("broker_caveats", "stale_broker_view"): "MCC-QG-BROKER-004",
    ("release_metadata", "missing_sector"): "MCC-QG-RELEASE-001",
    ("release_metadata", "missing_theme"): "MCC-QG-RELEASE-002",
    ("release_metadata", "missing_thesis_id"): "MCC-QG-RELEASE-003",
    ("release_metadata", "missing_source_ref"): "MCC-QG-RELEASE-004",
}


def quality_gate_json(
    records: Iterable[CatalystRecord],
    as_of: date,
    min_evidence_urls: Optional[int],
    max_review_age_days: Optional[int],
    max_evidence_age_days: Optional[int],
    max_broker_age_days: Optional[int],
    profile: str = "public",
) -> Dict[str, object]:
    """Return deterministic pass/fail quality-gate output for public research data."""

    policy = quality_policy(
        profile,
        min_evidence_urls,
        max_review_age_days,
        max_evidence_age_days,
        max_broker_age_days,
    )
    items = [
        _record_gate(
            record,
            as_of,
            policy,
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
            "max_broker_age_days": policy.max_broker_age_days,
            "max_evidence_age_days": policy.max_evidence_age_days,
            "max_review_age_days": policy.max_review_age_days,
            "min_broker_caveat_chars": policy.min_broker_caveat_chars,
            "min_evidence_urls": policy.min_evidence_urls,
            "min_scenario_note_chars": policy.min_scenario_note_chars,
            "placeholder_hosts": sorted(PLACEHOLDER_HOSTS),
            "profile": policy.name,
            "require_broker_views": policy.require_broker_views,
            "require_release_metadata": policy.require_release_metadata,
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
    min_evidence_urls: Optional[int],
    max_review_age_days: Optional[int],
    max_evidence_age_days: Optional[int],
    max_broker_age_days: Optional[int],
    profile: str = "public",
) -> str:
    payload = quality_gate_json(
        records,
        as_of,
        min_evidence_urls,
        max_review_age_days,
        max_evidence_age_days,
        max_broker_age_days,
        profile,
    )
    summary = payload["summary"]
    status = "PASS" if payload["ok"] else "FAIL"
    policy = payload["policy"]
    lines = [
        "# Market Catalyst Quality Gate",
        "",
        f"Status: {status}",
        f"Profile: {policy['profile']}",  # type: ignore[index]
        f"As of: {as_of.isoformat()}",
        f"Minimum evidence URLs: {policy['min_evidence_urls']}",  # type: ignore[index]
        f"Maximum review age: {_age_label(policy['max_review_age_days'])}",  # type: ignore[index]
        f"Maximum evidence age: {_age_label(policy['max_evidence_age_days'])}",  # type: ignore[index]
        f"Maximum broker age: {_age_label(policy['max_broker_age_days'])}",  # type: ignore[index]
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
            "| Severity | Code | Rule | Ticker | Record | Detail |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in records_payload:  # type: ignore[assignment]
        for issue in item["issues"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(issue["severity"]),
                        str(issue["code"]),
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
    policy: QualityProfile,
) -> Dict[str, object]:
    issues: List[Dict[str, object]] = []
    _check_minimum_evidence(record, as_of, policy, issues)
    _check_scenario_completeness(record, policy, issues)
    _check_review_freshness(record, as_of, policy, issues)
    if policy.require_no_placeholder_urls:
        _check_placeholder_urls(record, issues)
    _check_broker_caveats(record, as_of, policy, issues)
    if policy.require_release_metadata:
        _check_release_metadata(record, issues)
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
    policy: QualityProfile,
    issues: List[Dict[str, object]],
) -> None:
    if len(record.evidence_urls) < policy.min_evidence_urls:
        _add_issue(
            issues,
            "minimum_evidence",
            "critical",
            "missing_url_count",
            f"{len(record.evidence_urls)} evidence URLs present; {policy.min_evidence_urls} required",
        )
    if not policy.require_freshness_metadata:
        return
    if record.evidence_checked_at is None:
        _add_issue(issues, "minimum_evidence", "high", "missing_checked_at", "evidence_checked_at is missing")
        return
    age_days = (as_of - record.evidence_checked_at).days
    if policy.max_evidence_age_days is not None and age_days > policy.max_evidence_age_days:
        _add_issue(
            issues,
            "minimum_evidence",
            "high",
            "stale_checked_at",
            f"evidence metadata is {age_days} days old; maximum is {policy.max_evidence_age_days}",
        )


def _check_scenario_completeness(record: CatalystRecord, policy: QualityProfile, issues: List[Dict[str, object]]) -> None:
    for scenario in REQUIRED_SCENARIOS:
        note = record.scenario_notes.get(scenario, "").strip()
        if not note:
            _add_issue(issues, "scenario_completeness", "critical", "missing_note", f"{scenario} scenario note is missing")
        elif policy.require_substantive_scenarios and _looks_placeholder_text(note):
            _add_issue(issues, "scenario_completeness", "high", "placeholder_note", f"{scenario} scenario note looks like a placeholder")
        elif policy.require_substantive_scenarios and len(note) < policy.min_scenario_note_chars:
            _add_issue(
                issues,
                "scenario_completeness",
                "medium",
                "thin_note",
                f"{scenario} scenario note has {len(note)} characters; minimum is {policy.min_scenario_note_chars}",
            )


def _check_review_freshness(
    record: CatalystRecord,
    as_of: date,
    policy: QualityProfile,
    issues: List[Dict[str, object]],
) -> None:
    if policy.max_review_age_days is None:
        return
    if record.last_reviewed is None:
        _add_issue(issues, "review_freshness", "high", "missing_reviewed_at", "last_reviewed is missing")
        return
    age_days = (as_of - record.last_reviewed).days
    if age_days > policy.max_review_age_days:
        _add_issue(
            issues,
            "review_freshness",
            "high",
            "stale_reviewed_at",
            f"last review is {age_days} days old; maximum is {policy.max_review_age_days}",
        )


def _check_placeholder_urls(record: CatalystRecord, issues: List[Dict[str, object]]) -> None:
    for url in record.evidence_urls:
        reason = _placeholder_url_reason(url)
        if reason:
            _add_issue(issues, "no_placeholder_urls", "critical", "placeholder_evidence_url", f"evidence URL {url} is {reason}")
    for view in record.broker_views:
        reason = _placeholder_url_reason(view.source_url)
        if reason:
            _add_issue(
                issues,
                "no_placeholder_urls",
                "critical",
                "placeholder_broker_url",
                f"broker URL for {view.institution} ({view.source_url}) is {reason}",
            )


def _check_broker_caveats(
    record: CatalystRecord,
    as_of: date,
    policy: QualityProfile,
    issues: List[Dict[str, object]],
) -> None:
    if policy.require_broker_views and not record.broker_views:
        _add_issue(issues, "broker_caveats", "high", "missing_broker_views", "at least one broker view is required")
    if not policy.require_broker_caveats:
        return
    for view in record.broker_views:
        caveat = view.caveat.strip()
        if len(caveat) < policy.min_broker_caveat_chars:
            _add_issue(
                issues,
                "broker_caveats",
                "high",
                "thin_caveat",
                f"{view.institution} caveat has {len(caveat)} characters; minimum is {policy.min_broker_caveat_chars}",
            )
        elif _looks_placeholder_text(caveat):
            _add_issue(issues, "broker_caveats", "high", "placeholder_caveat", f"{view.institution} caveat looks like a placeholder")
        age_days = (as_of - view.as_of).days
        if policy.max_broker_age_days is not None and age_days > policy.max_broker_age_days:
            _add_issue(
                issues,
                "broker_caveats",
                "medium",
                "stale_broker_view",
                f"{view.institution} broker view is {age_days} days old; maximum is {policy.max_broker_age_days}",
            )


def _check_release_metadata(record: CatalystRecord, issues: List[Dict[str, object]]) -> None:
    required_fields = [
        ("sector", record.sector, "missing_sector"),
        ("theme", record.theme, "missing_theme"),
        ("thesis_id", record.thesis_id, "missing_thesis_id"),
        ("source_ref", record.source_ref, "missing_source_ref"),
    ]
    for field, value, code_key in required_fields:
        if not value:
            _add_issue(issues, "release_metadata", "high", code_key, f"{field} is required for strict release datasets")


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


def quality_policy(
    profile: str,
    min_evidence_urls: Optional[int] = None,
    max_review_age_days: Optional[int] = None,
    max_evidence_age_days: Optional[int] = None,
    max_broker_age_days: Optional[int] = None,
) -> QualityProfile:
    if profile not in QUALITY_PROFILES:
        raise ValueError("--profile must be one of: basic, public, strict")
    base = QUALITY_PROFILES[profile]
    return QualityProfile(
        name=base.name,
        min_evidence_urls=base.min_evidence_urls if min_evidence_urls is None else min_evidence_urls,
        max_review_age_days=base.max_review_age_days if max_review_age_days is None else max_review_age_days,
        max_evidence_age_days=base.max_evidence_age_days if max_evidence_age_days is None else max_evidence_age_days,
        max_broker_age_days=base.max_broker_age_days if max_broker_age_days is None else max_broker_age_days,
        require_freshness_metadata=base.require_freshness_metadata,
        require_no_placeholder_urls=base.require_no_placeholder_urls,
        require_substantive_scenarios=base.require_substantive_scenarios,
        require_broker_caveats=base.require_broker_caveats,
        require_release_metadata=base.require_release_metadata,
        require_broker_views=base.require_broker_views,
        min_scenario_note_chars=base.min_scenario_note_chars,
        min_broker_caveat_chars=base.min_broker_caveat_chars,
    )


def _add_issue(issues: List[Dict[str, object]], rule: str, severity: str, code_key: str, detail: str) -> None:
    issues.append({"code": DIAGNOSTIC_CODES[(rule, code_key)], "detail": detail, "rule": rule, "severity": severity})


def _age_label(value: object) -> str:
    if value is None:
        return "not enforced"
    return f"{value} days"


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
