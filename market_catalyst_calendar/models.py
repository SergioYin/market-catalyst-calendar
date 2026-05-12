"""Domain model and validation for catalyst records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse


EVENT_TYPES = {
    "earnings",
    "product_launch",
    "regulatory_decision",
    "clinical_trial",
    "investor_day",
    "macro_release",
    "court_decision",
    "capital_return",
    "m_and_a",
    "guidance_update",
}

STATUSES = {"rumored", "watching", "scheduled", "confirmed", "completed", "delayed", "cancelled"}
IMPACTS = {"positive", "negative", "mixed", "unknown"}
REVIEW_ACTIONS = {"verify_source", "refresh_evidence", "update_scenario", "monitor_date", "archive", "none"}


@dataclass(frozen=True)
class EventWindow:
    start: date
    end: date

    @property
    def label(self) -> str:
        if self.start == self.end:
            return self.start.isoformat()
        return f"{self.start.isoformat()}..{self.end.isoformat()}"


@dataclass(frozen=True)
class HistoryEntry:
    date: date
    status: str
    note: str


@dataclass(frozen=True)
class BrokerView:
    institution: str
    rating: str
    target_price: float
    as_of: date
    source_url: str
    caveat: str


@dataclass(frozen=True)
class CatalystRecord:
    record_id: str
    ticker: str
    entity: str
    event_type: str
    window: EventWindow
    confidence: float
    status: str
    history: Tuple[HistoryEntry, ...]
    thesis_impact: str
    evidence_urls: Tuple[str, ...]
    scenario_notes: Dict[str, str]
    required_review_action: str
    last_reviewed: Optional[date]
    position_size: Optional[float]
    portfolio_weight: Optional[float]
    thesis_id: Optional[str]
    source_ref: Optional[str]
    evidence_checked_at: Optional[date]
    broker_views: Tuple[BrokerView, ...]


@dataclass(frozen=True)
class Dataset:
    as_of: date
    records: Tuple[CatalystRecord, ...]


def parse_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date string") from exc


def parse_window(raw: Dict[str, Any]) -> EventWindow:
    if "date" in raw:
        start = parse_date(raw["date"], "date")
        return EventWindow(start=start, end=start)
    if "window" not in raw or not isinstance(raw["window"], dict):
        raise ValueError("record must include date or window")
    window = raw["window"]
    start = parse_date(window.get("start"), "window.start")
    end = parse_date(window.get("end"), "window.end")
    if end < start:
        raise ValueError("window.end must be on or after window.start")
    return EventWindow(start=start, end=end)


def parse_history(raw: Any) -> Tuple[HistoryEntry, ...]:
    if raw is None:
        return tuple()
    if not isinstance(raw, list):
        raise ValueError("history must be a list")
    entries: List[HistoryEntry] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"history[{index}] must be an object")
        status = _required_str(item, "status", f"history[{index}]")
        if status not in STATUSES:
            raise ValueError(f"history[{index}].status has unsupported value: {status}")
        entries.append(
            HistoryEntry(
                date=parse_date(item.get("date"), f"history[{index}].date"),
                status=status,
                note=_required_str(item, "note", f"history[{index}]"),
            )
        )
    return tuple(sorted(entries, key=lambda entry: (entry.date, entry.status, entry.note)))


def parse_broker_views(raw: Any) -> Tuple[BrokerView, ...]:
    if raw is None:
        return tuple()
    if not isinstance(raw, list):
        raise ValueError("broker_views must be a list")
    views: List[BrokerView] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"broker_views[{index}] must be an object")
        target_price = item.get("target_price")
        if not isinstance(target_price, (int, float)) or isinstance(target_price, bool):
            raise ValueError(f"broker_views[{index}].target_price must be a non-negative number")
        target_price = float(target_price)
        if target_price < 0:
            raise ValueError(f"broker_views[{index}].target_price must be non-negative")
        source_url = _required_str(item, "source_url", f"broker_views[{index}]")
        if not _valid_url(source_url):
            raise ValueError(f"broker_views[{index}].source_url must be an http(s) URL")
        views.append(
            BrokerView(
                institution=_required_str(item, "institution", f"broker_views[{index}]"),
                rating=_required_str(item, "rating", f"broker_views[{index}]"),
                target_price=target_price,
                as_of=parse_date(item.get("as_of"), f"broker_views[{index}].as_of"),
                source_url=source_url,
                caveat=_required_str(item, "caveat", f"broker_views[{index}]"),
            )
        )
    return tuple(sorted(views, key=lambda view: (view.as_of, view.institution, view.rating, view.target_price, view.source_url)))


def parse_record(raw: Dict[str, Any]) -> CatalystRecord:
    if not isinstance(raw, dict):
        raise ValueError("record must be an object")
    event_type = _required_str(raw, "event_type", "record")
    if event_type not in EVENT_TYPES:
        raise ValueError(f"event_type has unsupported value: {event_type}")
    status = _required_str(raw, "status", "record")
    if status not in STATUSES:
        raise ValueError(f"status has unsupported value: {status}")
    thesis_impact = _required_str(raw, "thesis_impact", "record")
    if thesis_impact not in IMPACTS:
        raise ValueError(f"thesis_impact has unsupported value: {thesis_impact}")
    required_review_action = _required_str(raw, "required_review_action", "record")
    if required_review_action not in REVIEW_ACTIONS:
        raise ValueError(f"required_review_action has unsupported value: {required_review_action}")
    confidence = raw.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        raise ValueError("confidence must be a number between 0 and 1")
    confidence = float(confidence)
    if confidence < 0 or confidence > 1:
        raise ValueError("confidence must be between 0 and 1")
    evidence_urls = raw.get("evidence_urls")
    if not isinstance(evidence_urls, list) or not all(isinstance(url, str) for url in evidence_urls):
        raise ValueError("evidence_urls must be a list of strings")
    scenario_notes = raw.get("scenario_notes")
    if not isinstance(scenario_notes, dict):
        raise ValueError("scenario_notes must be an object")
    normalized_notes = {str(key): str(value) for key, value in scenario_notes.items()}
    last_reviewed = raw.get("last_reviewed")
    evidence_checked_at = raw.get("evidence_checked_at")
    position_size = _optional_nonnegative_float(raw, "position_size")
    portfolio_weight = _optional_nonnegative_float(raw, "portfolio_weight")
    if portfolio_weight is not None and portfolio_weight > 1:
        raise ValueError("portfolio_weight must be between 0 and 1")
    return CatalystRecord(
        record_id=_required_str(raw, "id", "record"),
        ticker=_required_str(raw, "ticker", "record").upper(),
        entity=_required_str(raw, "entity", "record"),
        event_type=event_type,
        window=parse_window(raw),
        confidence=confidence,
        status=status,
        history=parse_history(raw.get("history", [])),
        thesis_impact=thesis_impact,
        evidence_urls=tuple(evidence_urls),
        scenario_notes=normalized_notes,
        required_review_action=required_review_action,
        last_reviewed=parse_date(last_reviewed, "last_reviewed") if last_reviewed else None,
        position_size=position_size,
        portfolio_weight=portfolio_weight,
        thesis_id=_optional_str(raw, "thesis_id"),
        source_ref=_optional_str(raw, "source_ref"),
        evidence_checked_at=parse_date(evidence_checked_at, "evidence_checked_at") if evidence_checked_at else None,
        broker_views=parse_broker_views(raw.get("broker_views")),
    )


def parse_dataset(raw: Dict[str, Any]) -> Dataset:
    if not isinstance(raw, dict):
        raise ValueError("dataset must be an object")
    as_of_raw = raw.get("as_of", "1970-01-01")
    records_raw = raw.get("records")
    if not isinstance(records_raw, list):
        raise ValueError("records must be a list")
    records = tuple(parse_record(record) for record in records_raw)
    return Dataset(as_of=parse_date(as_of_raw, "as_of"), records=records)


def validation_errors(dataset: Dataset) -> List[str]:
    errors: List[str] = []
    seen_ids = set()
    for record in dataset.records:
        prefix = f"{record.record_id}: "
        if record.record_id in seen_ids:
            errors.append(prefix + "duplicate id")
        seen_ids.add(record.record_id)
        if not record.ticker and not record.entity:
            errors.append(prefix + "ticker or entity is required")
        if record.ticker and not _looks_like_ticker(record.ticker):
            errors.append(prefix + "ticker should look like an exchange ticker or symbol")
        if not record.evidence_urls:
            errors.append(prefix + "at least one evidence URL is required")
        for url in record.evidence_urls:
            if not _valid_url(url):
                errors.append(prefix + f"invalid evidence URL: {url}")
        missing_scenarios = sorted({"bull", "base", "bear"} - set(record.scenario_notes))
        if missing_scenarios:
            errors.append(prefix + "missing scenario notes: " + ", ".join(missing_scenarios))
        if record.status in {"confirmed", "completed"} and record.confidence < 0.6:
            errors.append(prefix + "confirmed/completed records should have confidence >= 0.60")
        if record.required_review_action == "none" and record.status not in {"confirmed", "completed", "cancelled"}:
            errors.append(prefix + "open records need a required review action")
        if record.last_reviewed and record.last_reviewed > dataset.as_of:
            errors.append(prefix + "last_reviewed cannot be after as_of")
        if record.evidence_checked_at and record.evidence_checked_at > dataset.as_of:
            errors.append(prefix + "evidence_checked_at cannot be after as_of")
        for view in record.broker_views:
            if view.as_of > dataset.as_of:
                errors.append(prefix + f"broker view from {view.institution} cannot be after as_of")
        if record.history:
            latest = max(record.history, key=lambda entry: entry.date)
            if latest.date > dataset.as_of:
                errors.append(prefix + "history cannot include future updates")
            if latest.status != record.status:
                errors.append(prefix + "latest history status should match current status")
    return sorted(errors)


def sorted_records(records: Iterable[CatalystRecord]) -> List[CatalystRecord]:
    return sorted(records, key=lambda record: (record.window.start, record.ticker, record.record_id))


def _required_str(raw: Dict[str, Any], key: str, owner: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner}.{key} must be a non-empty string")
    return value.strip()


def _optional_nonnegative_float(raw: Dict[str, Any], key: str) -> Optional[float]:
    value = raw.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{key} must be a non-negative number")
    parsed = float(value)
    if parsed < 0:
        raise ValueError(f"{key} must be non-negative")
    return parsed


def _optional_str(raw: Dict[str, Any], key: str) -> Optional[str]:
    value = raw.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string when provided")
    return value.strip()


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _looks_like_ticker(value: str) -> bool:
    if len(value) > 12:
        return False
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
    return all(char in allowed for char in value)
