"""Finance-specific scoring and review classification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .models import CatalystRecord


EVENT_WEIGHTS = {
    "earnings": 18,
    "product_launch": 16,
    "regulatory_decision": 23,
    "clinical_trial": 25,
    "investor_day": 14,
    "macro_release": 20,
    "court_decision": 22,
    "capital_return": 13,
    "m_and_a": 24,
    "guidance_update": 21,
}

STATUS_WEIGHTS = {
    "rumored": 6,
    "watching": 10,
    "scheduled": 14,
    "confirmed": 18,
    "completed": 2,
    "delayed": 8,
    "cancelled": 0,
}

IMPACT_WEIGHTS = {"positive": 11, "negative": 11, "mixed": 8, "unknown": 3}


@dataclass(frozen=True)
class Score:
    catalyst_score: int
    urgency: str
    review_state: str
    days_until: int
    stale_days: Optional[int]


def score_record(record: CatalystRecord, as_of: date, stale_after_days: int = 14) -> Score:
    days_until = (record.window.start - as_of).days
    proximity = _proximity_weight(days_until)
    evidence = min(12, len(record.evidence_urls) * 4)
    scenario_depth = min(6, sum(1 for value in record.scenario_notes.values() if len(value.strip()) >= 20) * 2)
    confidence = round(record.confidence * 20)
    raw = (
        EVENT_WEIGHTS.get(record.event_type, 8)
        + STATUS_WEIGHTS.get(record.status, 4)
        + IMPACT_WEIGHTS.get(record.thesis_impact, 3)
        + proximity
        + evidence
        + scenario_depth
        + confidence
    )
    if record.status in {"completed", "cancelled"}:
        raw = min(raw, 35)
    catalyst_score = max(0, min(100, int(raw)))
    stale_days = _stale_days(record, as_of, stale_after_days)
    return Score(
        catalyst_score=catalyst_score,
        urgency=_urgency(days_until, catalyst_score, record.status),
        review_state=_review_state(record, stale_days),
        days_until=days_until,
        stale_days=stale_days,
    )


def _proximity_weight(days_until: int) -> int:
    if days_until < 0:
        return 0
    if days_until <= 7:
        return 18
    if days_until <= 30:
        return 14
    if days_until <= 90:
        return 9
    return 3


def _urgency(days_until: int, catalyst_score: int, status: str) -> str:
    if status in {"completed", "cancelled"}:
        return "closed"
    if days_until < 0:
        return "overdue"
    if days_until <= 7 or catalyst_score >= 85:
        return "high"
    if days_until <= 30 or catalyst_score >= 65:
        return "medium"
    return "low"


def _stale_days(record: CatalystRecord, as_of: date, stale_after_days: int) -> Optional[int]:
    if record.status in {"completed", "cancelled"}:
        return None
    if not record.last_reviewed:
        return stale_after_days + 1
    age = (as_of - record.last_reviewed).days
    if age > stale_after_days:
        return age
    return None


def _review_state(record: CatalystRecord, stale_days: Optional[int]) -> str:
    if record.status in {"completed", "cancelled"}:
        return "closed"
    if stale_days is not None:
        return "stale"
    if record.required_review_action in {"verify_source", "refresh_evidence", "update_scenario"}:
        return "needs_review"
    return "current"
