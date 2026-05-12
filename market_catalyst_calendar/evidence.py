"""Evidence freshness and source concentration audit."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlparse

from .models import CatalystRecord, sorted_records


def evidence_audit_json(
    records: Iterable[CatalystRecord],
    as_of: date,
    fresh_after_days: int,
    min_sources: int,
    max_domain_share: float,
) -> Dict[str, object]:
    """Return a deterministic evidence audit report for records with source quality flags."""

    items = [
        _audit_record(record, as_of, fresh_after_days, min_sources, max_domain_share)
        for record in sorted_records(records)
    ]
    flagged = [item for item in items if item["flags"]]
    counts = Counter(flag for item in flagged for flag in item["flags"])
    severity_counts = Counter(str(item["severity"]) for item in flagged)
    return {
        "as_of": as_of.isoformat(),
        "fresh_after_days": fresh_after_days,
        "max_domain_share": max_domain_share,
        "min_sources": min_sources,
        "records": flagged,
        "summary": {
            "flag_counts": dict(sorted(counts.items())),
            "flagged_record_count": len(flagged),
            "record_count": len(items),
            "severity_counts": dict(sorted(severity_counts.items())),
        },
    }


def evidence_audit_markdown(
    records: Iterable[CatalystRecord],
    as_of: date,
    fresh_after_days: int,
    min_sources: int,
    max_domain_share: float,
) -> str:
    payload = evidence_audit_json(records, as_of, fresh_after_days, min_sources, max_domain_share)
    summary = payload["summary"]
    lines = [
        "# Market Catalyst Evidence Audit",
        "",
        f"As of: {as_of.isoformat()}",
        f"Fresh after: {fresh_after_days} days",
        f"Minimum sources: {min_sources}",
        f"Maximum domain share: {max_domain_share:.2f}",
        "",
        f"Flagged records: {summary['flagged_record_count']} of {summary['record_count']}",  # type: ignore[index]
        "",
    ]
    records_payload = payload["records"]
    if not records_payload:
        lines.extend(["No evidence freshness or concentration flags.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Severity | Ticker | Record | Evidence Checked | Sources | Dominant Domain | Flags |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for item in records_payload:  # type: ignore[assignment]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["severity"]),
                    str(item["ticker"]),
                    str(item["id"]),
                    str(item["evidence_checked_at"] or "missing"),
                    str(item["evidence_url_count"]),
                    _dominant_label(item),
                    ", ".join(str(flag) for flag in item["flags"]),
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
                f"- Window: {item['window']}; event: {str(item['event_type']).replace('_', ' ')}; status: {item['status']}",
                f"- Evidence checked: {item['evidence_checked_at'] or 'missing'}",
                f"- Source domains: {', '.join(str(domain) for domain in item['source_domains']) or 'none'}",
                f"- Next action: {item['next_action']}",
                "",
            ]
        )
    return "\n".join(lines)


def _audit_record(
    record: CatalystRecord,
    as_of: date,
    fresh_after_days: int,
    min_sources: int,
    max_domain_share: float,
) -> Dict[str, object]:
    domains = [_source_domain(url) for url in record.evidence_urls]
    valid_domains = [domain for domain in domains if domain]
    domain_counts = Counter(valid_domains)
    dominant_domain: Optional[str] = None
    dominant_count = 0
    if domain_counts:
        dominant_domain, dominant_count = sorted(domain_counts.items(), key=lambda item: (-item[1], item[0]))[0]
    source_count = len(record.evidence_urls)
    dominant_share = dominant_count / source_count if source_count else 0.0

    flags: List[str] = []
    evidence_age_days: Optional[int] = None
    if record.evidence_checked_at is None:
        flags.append("missing_evidence_checked_at")
    else:
        evidence_age_days = (as_of - record.evidence_checked_at).days
        if evidence_age_days > fresh_after_days:
            flags.append("stale_evidence_metadata")
    if source_count == 0:
        flags.append("missing_evidence_urls")
    elif source_count < min_sources:
        flags.append("thin_source_count")
    if source_count >= min_sources and dominant_share > max_domain_share:
        flags.append("source_concentration")

    return {
        "dominant_source_domain": dominant_domain,
        "dominant_source_share": round(dominant_share, 4),
        "entity": record.entity,
        "event_type": record.event_type,
        "evidence_age_days": evidence_age_days,
        "evidence_checked_at": record.evidence_checked_at.isoformat() if record.evidence_checked_at else None,
        "evidence_url_count": source_count,
        "evidence_urls": list(record.evidence_urls),
        "flags": flags,
        "id": record.record_id,
        "next_action": _next_action(flags, evidence_age_days, min_sources, fresh_after_days),
        "severity": _severity(flags),
        "source_domain_count": len(domain_counts),
        "source_domains": sorted(domain_counts),
        "status": record.status,
        "ticker": record.ticker,
        "window": record.window.label,
    }


def _source_domain(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return hostname.lower()[4:] if hostname.lower().startswith("www.") else hostname.lower()


def _severity(flags: List[str]) -> str:
    if "missing_evidence_urls" in flags:
        return "critical"
    if "missing_evidence_checked_at" in flags or "stale_evidence_metadata" in flags:
        return "high" if len(flags) > 1 else "medium"
    if flags:
        return "low"
    return "none"


def _next_action(flags: List[str], evidence_age_days: Optional[int], min_sources: int, fresh_after_days: int) -> str:
    if not flags:
        return "No evidence audit action is required."
    actions = []
    if "missing_evidence_checked_at" in flags:
        actions.append("record the date evidence was last checked")
    if "stale_evidence_metadata" in flags:
        actions.append(f"refresh source review; evidence age is {evidence_age_days} days versus {fresh_after_days} allowed")
    if "missing_evidence_urls" in flags:
        actions.append("add source URLs before relying on the record")
    if "thin_source_count" in flags:
        actions.append(f"add independent sources until at least {min_sources} URLs support the record")
    if "source_concentration" in flags:
        actions.append("add sources from independent domains or document why one domain is authoritative")
    return "; ".join(actions) + "."


def _dominant_label(item: Dict[str, object]) -> str:
    domain = item["dominant_source_domain"]
    if not domain:
        return "none"
    return f"{domain} ({float(item['dominant_source_share']):.2f})"
