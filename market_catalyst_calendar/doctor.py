"""Dataset doctor repair planning."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .models import Dataset, validation_errors
from .quality_gate import quality_gate_json


@dataclass(frozen=True)
class Repair:
    op: str
    path: str
    value: Any
    record_id: str
    diagnostic_codes: Tuple[str, ...]
    reason: str
    confidence: str = "medium"

    def patch_op(self) -> Dict[str, Any]:
        return {"op": self.op, "path": self.path, "value": self.value}

    def detail(self) -> Dict[str, Any]:
        payload = self.patch_op()
        payload.update(
            {
                "confidence": self.confidence,
                "diagnostic_codes": list(self.diagnostic_codes),
                "reason": self.reason,
                "record_id": self.record_id,
            }
        )
        return payload


def doctor_json(
    raw_dataset: Dict[str, Any],
    dataset: Dataset,
    as_of: date,
    profile: str = "public",
    min_evidence_urls: Optional[int] = None,
    max_review_age_days: Optional[int] = None,
    max_evidence_age_days: Optional[int] = None,
    max_broker_age_days: Optional[int] = None,
) -> Dict[str, Any]:
    """Return a deterministic read-only repair plan for validation and quality failures."""

    raw_records = _raw_records(raw_dataset)
    record_indexes = _record_indexes(raw_records)
    validation_diagnostics = _validation_diagnostics(validation_errors(dataset))
    gate = quality_gate_json(
        dataset.records,
        as_of,
        min_evidence_urls,
        max_review_age_days,
        max_evidence_age_days,
        max_broker_age_days,
        profile,
    )
    quality_diagnostics = _quality_diagnostics(gate)
    repairs = _dedupe_repairs(
        list(_validation_repairs(validation_diagnostics, raw_records, record_indexes, as_of))
        + list(_quality_repairs(gate, raw_records, record_indexes, as_of))
    )
    manual = _manual_actions(validation_diagnostics + quality_diagnostics, repairs)
    return {
        "schema_version": "doctor/v1",
        "as_of": as_of.isoformat(),
        "profile": profile,
        "ok": not validation_diagnostics and gate["ok"],
        "modifies_input": False,
        "summary": {
            "diagnostic_count": len(validation_diagnostics) + len(quality_diagnostics),
            "manual_action_count": len(manual),
            "record_count": len(dataset.records),
            "repair_count": len(repairs),
            "validation_error_count": len(validation_diagnostics),
            "quality_failure_count": int(gate["summary"]["failed_record_count"]),
        },
        "diagnostics": validation_diagnostics + quality_diagnostics,
        "repairs": [repair.detail() for repair in repairs],
        "patch": [repair.patch_op() for repair in repairs],
        "manual_actions": manual,
        "next_steps": [
            "Review suggested values before applying them; placeholder replacement URLs are deterministic prompts, not verified sources.",
            f"After editing a copy of the dataset, rerun validate --profile {profile} and quality-gate --profile {profile}.",
        ],
    }


def doctor_markdown(payload: Dict[str, Any]) -> str:
    """Render a human repair checklist from a doctor payload."""

    status = "PASS" if payload["ok"] else "NEEDS REPAIR"
    summary = payload["summary"]
    lines = [
        "# Market Catalyst Dataset Doctor",
        "",
        f"Status: {status}",
        f"Profile: {payload['profile']}",
        f"As of: {payload['as_of']}",
        "Read-only: yes",
        "",
        f"Diagnostics: {summary['diagnostic_count']}",
        f"Suggested patch operations: {summary['repair_count']}",
        f"Manual actions: {summary['manual_action_count']}",
        "",
    ]
    repairs = payload["repairs"]
    if repairs:
        lines.extend(["## Suggested Repairs", "", "| Code | Record | Operation | Path | Reason |", "| --- | --- | --- | --- | --- |"])
        for repair in repairs:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(", ".join(repair["diagnostic_codes"])),
                        _cell(repair["record_id"]),
                        _cell(repair["op"]),
                        _cell(repair["path"]),
                        _cell(repair["reason"]),
                    ]
                )
                + " |"
            )
        lines.append("")
    manual = payload["manual_actions"]
    if manual:
        lines.extend(["## Manual Review", ""])
        for item in manual:
            lines.append(f"- `{item['record_id']}` {item['code']}: {item['suggestion']}")
        lines.append("")
    lines.extend(["## Next Steps", ""])
    for step in payload["next_steps"]:
        lines.append(f"- {step}")
    return "\n".join(lines).rstrip() + "\n"


def _validation_repairs(
    diagnostics: List[Dict[str, Any]],
    raw_records: List[Dict[str, Any]],
    record_indexes: Dict[str, int],
    as_of: date,
) -> Iterable[Repair]:
    for diagnostic in diagnostics:
        record_id = diagnostic["record_id"]
        index = record_indexes.get(record_id)
        if index is None:
            continue
        raw = raw_records[index]
        code = diagnostic["code"]
        detail = diagnostic["detail"]
        prefix = f"/records/{index}"
        if code == "MCC-VAL-EVIDENCE-001":
            yield _add_evidence_url(index, record_id, len(raw.get("evidence_urls", [])), code)
        elif code == "MCC-VAL-EVIDENCE-002":
            bad_url = detail.rsplit(": ", 1)[-1]
            for url_index, url in enumerate(raw.get("evidence_urls", [])):
                if url == bad_url:
                    yield Repair("replace", f"{prefix}/evidence_urls/{url_index}", _source_url(record_id, "evidence", url_index + 1), record_id, (code,), "replace invalid evidence URL")
        elif code == "MCC-VAL-SCENARIO-001":
            for scenario in _missing_scenarios(detail):
                yield Repair("add", f"{prefix}/scenario_notes/{_escape_path(scenario)}", _scenario_note(raw, scenario), record_id, (code,), f"add missing {scenario} scenario note")
        elif code == "MCC-VAL-CONFIDENCE-001":
            yield Repair("replace", f"{prefix}/confidence", 0.6, record_id, (code,), "raise confirmed/completed confidence to minimum validation threshold")
        elif code == "MCC-VAL-REVIEW-001":
            yield Repair("replace", f"{prefix}/required_review_action", "refresh_evidence", record_id, (code,), "open records need an explicit review action")
        elif code in {"MCC-VAL-DATE-001", "MCC-VAL-DATE-002", "MCC-VAL-DATE-003"}:
            field = {"MCC-VAL-DATE-001": "last_reviewed", "MCC-VAL-DATE-002": "evidence_checked_at", "MCC-VAL-DATE-003": "outcome_recorded_at"}[code]
            yield Repair("replace", f"{prefix}/{field}", as_of.isoformat(), record_id, (code,), f"cap {field} at dataset as_of")
        elif code == "MCC-VAL-OUTCOME-001":
            yield Repair("add", f"{prefix}/actual_outcome", "TBD: record actual catalyst outcome before publishing.", record_id, (code,), "outcome_recorded_at requires outcome text")
        elif code == "MCC-VAL-HISTORY-002" and raw.get("status"):
            history = raw.get("history", [])
            if isinstance(history, list) and history:
                yield Repair("replace", f"{prefix}/history/{len(history) - 1}/status", raw["status"], record_id, (code,), "align latest history status with record status")


def _quality_repairs(
    gate: Dict[str, Any],
    raw_records: List[Dict[str, Any]],
    record_indexes: Dict[str, int],
    as_of: date,
) -> Iterable[Repair]:
    policy = gate["policy"]
    min_evidence = int(policy["min_evidence_urls"])
    for record in gate["records"]:
        record_id = str(record["id"])
        index = record_indexes.get(record_id)
        if index is None:
            continue
        raw = raw_records[index]
        prefix = f"/records/{index}"
        for issue in record["issues"]:
            code = str(issue["code"])
            detail = str(issue["detail"])
            if code == "MCC-QG-EVIDENCE-001":
                present = len(raw.get("evidence_urls", []))
                for offset in range(max(0, min_evidence - present)):
                    yield _add_evidence_url(index, record_id, present + offset, code)
            elif code in {"MCC-QG-EVIDENCE-002", "MCC-QG-EVIDENCE-003"}:
                op = "add" if "evidence_checked_at" not in raw else "replace"
                yield Repair(op, f"{prefix}/evidence_checked_at", as_of.isoformat(), record_id, (code,), "refresh evidence freshness metadata")
            elif code in {"MCC-QG-REVIEW-001", "MCC-QG-REVIEW-002"}:
                op = "add" if "last_reviewed" not in raw else "replace"
                yield Repair(op, f"{prefix}/last_reviewed", as_of.isoformat(), record_id, (code,), "refresh analyst review date")
            elif code in {"MCC-QG-SCENARIO-001", "MCC-QG-SCENARIO-002", "MCC-QG-SCENARIO-003"}:
                scenario = detail.split(" scenario note", 1)[0]
                scenario_notes = raw.get("scenario_notes", {})
                op = "replace" if isinstance(scenario_notes, dict) and scenario in scenario_notes else "add"
                yield Repair(op, f"{prefix}/scenario_notes/{_escape_path(scenario)}", _scenario_note(raw, scenario), record_id, (code,), f"write substantive {scenario} scenario note")
            elif code == "MCC-QG-SOURCE-001":
                for url_index, url in enumerate(raw.get("evidence_urls", [])):
                    if url in detail:
                        yield Repair("replace", f"{prefix}/evidence_urls/{url_index}", _source_url(record_id, "evidence", url_index + 1), record_id, (code,), "replace placeholder evidence URL with a real public source URL")
            elif code == "MCC-QG-SOURCE-002":
                for view_index, view in enumerate(raw.get("broker_views", [])):
                    if isinstance(view, dict) and view.get("source_url") and str(view["source_url"]) in detail:
                        yield Repair("replace", f"{prefix}/broker_views/{view_index}/source_url", _source_url(record_id, "broker", view_index + 1), record_id, (code,), "replace placeholder broker URL with a real public source URL")
            elif code == "MCC-QG-BROKER-001":
                yield Repair("add", f"{prefix}/broker_views/-", _broker_view(record_id, as_of), record_id, (code,), "add a broker view shell for strict review", "low")
            elif code in {"MCC-QG-BROKER-002", "MCC-QG-BROKER-003"}:
                for view_index, view in enumerate(raw.get("broker_views", [])):
                    if isinstance(view, dict) and str(view.get("institution", "")) in detail:
                        yield Repair("replace", f"{prefix}/broker_views/{view_index}/caveat", _broker_caveat(raw, view), record_id, (code,), "write a substantive broker caveat")
            elif code == "MCC-QG-BROKER-004":
                for view_index, view in enumerate(raw.get("broker_views", [])):
                    if isinstance(view, dict) and str(view.get("institution", "")) in detail:
                        yield Repair("replace", f"{prefix}/broker_views/{view_index}/as_of", as_of.isoformat(), record_id, (code,), "refresh broker view date after source review")
            elif code.startswith("MCC-QG-RELEASE-"):
                field = {
                    "MCC-QG-RELEASE-001": "sector",
                    "MCC-QG-RELEASE-002": "theme",
                    "MCC-QG-RELEASE-003": "thesis_id",
                    "MCC-QG-RELEASE-004": "source_ref",
                }[code]
                yield Repair("add", f"{prefix}/{field}", _release_value(raw, field), record_id, (code,), f"populate strict release metadata field {field}")


def _add_evidence_url(index: int, record_id: str, url_index: int, code: str) -> Repair:
    return Repair("add", f"/records/{index}/evidence_urls/-", _source_url(record_id, "evidence", url_index + 1), record_id, (code,), "add an independent evidence URL")


def _dedupe_repairs(repairs: Iterable[Repair]) -> List[Repair]:
    merged: Dict[Tuple[str, str], Repair] = {}
    for repair in repairs:
        key = (repair.op, repair.path)
        previous = merged.get(key)
        if previous is None:
            merged[key] = repair
        else:
            merged[key] = Repair(
                repair.op,
                repair.path,
                repair.value,
                repair.record_id,
                tuple(sorted(set(previous.diagnostic_codes + repair.diagnostic_codes))),
                previous.reason,
                previous.confidence if previous.confidence == repair.confidence else "medium",
            )
    return [merged[key] for key in sorted(merged, key=lambda item: (item[1], item[0]))]


def _manual_actions(diagnostics: List[Dict[str, Any]], repairs: List[Repair]) -> List[Dict[str, str]]:
    covered = {(code, repair.record_id) for repair in repairs for code in repair.diagnostic_codes}
    actions = []
    for diagnostic in diagnostics:
        key = (diagnostic["code"], diagnostic["record_id"])
        if key in covered:
            continue
        actions.append(
            {
                "code": diagnostic["code"],
                "detail": diagnostic["detail"],
                "record_id": diagnostic["record_id"],
                "suggestion": _manual_suggestion(diagnostic["code"]),
            }
        )
    return actions


def _manual_suggestion(code: str) -> str:
    suggestions = {
        "MCC-VAL-IDENTITY-001": "choose one canonical record id and merge or remove duplicate records manually",
        "MCC-VAL-IDENTITY-002": "fill ticker, entity, or both from the source material",
        "MCC-VAL-IDENTITY-003": "normalize ticker to an exchange-style symbol",
        "MCC-VAL-HISTORY-001": "remove or redraft future-dated history after checking the event timeline",
        "MCC-VAL-DATE-004": "move outcome_recorded_at to the event date or later after confirming the actual review date",
        "MCC-VAL-BROKER-001": "review the broker source date and keep it on or before dataset as_of",
    }
    return suggestions.get(code, "review the diagnostic and edit the source record manually")


def _validation_diagnostics(errors: List[str]) -> List[Dict[str, Any]]:
    diagnostics = []
    for error in errors:
        record_id, detail = _split_validation_error(error)
        diagnostics.append({"code": _validation_code(detail), "detail": detail, "record_id": record_id, "severity": "error", "source": "validate"})
    return diagnostics


def _quality_diagnostics(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "code": issue["code"],
            "detail": issue["detail"],
            "record_id": record["id"],
            "rule": issue["rule"],
            "severity": issue["severity"],
            "source": "quality-gate",
            "ticker": record["ticker"],
        }
        for record in payload["records"]
        for issue in record["issues"]
    ]


def _split_validation_error(error: str) -> Tuple[str, str]:
    if ": " not in error:
        return "", error
    return tuple(error.split(": ", 1))  # type: ignore[return-value]


def _validation_code(detail: str) -> str:
    checks = [
        ("duplicate id", "MCC-VAL-IDENTITY-001"),
        ("ticker or entity is required", "MCC-VAL-IDENTITY-002"),
        ("ticker should look like", "MCC-VAL-IDENTITY-003"),
        ("at least one evidence URL", "MCC-VAL-EVIDENCE-001"),
        ("invalid evidence URL", "MCC-VAL-EVIDENCE-002"),
        ("missing scenario notes", "MCC-VAL-SCENARIO-001"),
        ("confidence", "MCC-VAL-CONFIDENCE-001"),
        ("open records need", "MCC-VAL-REVIEW-001"),
        ("last_reviewed cannot be after as_of", "MCC-VAL-DATE-001"),
        ("evidence_checked_at cannot be after as_of", "MCC-VAL-DATE-002"),
        ("outcome_recorded_at cannot be after as_of", "MCC-VAL-DATE-003"),
        ("outcome_recorded_at cannot be before", "MCC-VAL-DATE-004"),
        ("outcome_recorded_at requires actual_outcome", "MCC-VAL-OUTCOME-001"),
        ("broker view from", "MCC-VAL-BROKER-001"),
        ("history cannot include future updates", "MCC-VAL-HISTORY-001"),
        ("latest history status should match current status", "MCC-VAL-HISTORY-002"),
    ]
    for needle, code in checks:
        if needle in detail:
            return code
    return "MCC-VAL-GENERAL-001"


def _raw_records(raw_dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = raw_dataset.get("records", [])
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _record_indexes(raw_records: List[Dict[str, Any]]) -> Dict[str, int]:
    indexes = {}
    for index, record in enumerate(raw_records):
        record_id = record.get("id")
        if isinstance(record_id, str) and record_id not in indexes:
            indexes[record_id] = index
    return indexes


def _source_url(record_id: str, source_type: str, index: int) -> str:
    return f"https://research.exampledata.com/{_slug(record_id)}/{source_type}-{index}"


def _scenario_note(raw: Dict[str, Any], scenario: str) -> str:
    ticker = raw.get("ticker") or raw.get("entity") or "this catalyst"
    if scenario == "bull":
        return f"{ticker} upside case: verified evidence shows the catalyst improves timing, demand, or regulatory probability."
    if scenario == "bear":
        return f"{ticker} downside case: verified evidence shows delay, weaker demand, or a more restrictive outcome."
    return f"{ticker} base case: verified evidence supports the current thesis with no material change to expected timing."


def _broker_view(record_id: str, as_of: date) -> Dict[str, Any]:
    return {
        "institution": "TBD Research",
        "rating": "tbd",
        "target_price": 0.0,
        "as_of": as_of.isoformat(),
        "source_url": _source_url(record_id, "broker", 1),
        "caveat": "Replace this shell with a verified broker view and document the assumptions that could change the thesis.",
    }


def _broker_caveat(raw: Dict[str, Any], view: Dict[str, Any]) -> str:
    ticker = raw.get("ticker") or raw.get("entity") or "the catalyst"
    institution = view.get("institution") or "broker"
    return f"{institution} view depends on verified source assumptions for {ticker}; refresh if timing, probability, or target inputs change."


def _release_value(raw: Dict[str, Any], field: str) -> str:
    ticker = str(raw.get("ticker") or raw.get("entity") or "record").lower()
    values = {
        "sector": "Unclassified",
        "theme": "Needs classification",
        "thesis_id": f"{_slug(ticker)}-thesis",
        "source_ref": f"{raw.get('id', ticker)} source pack",
    }
    return values[field]


def _missing_scenarios(detail: str) -> List[str]:
    if ": " not in detail:
        return []
    return [item.strip() for item in detail.split(": ", 1)[1].split(",") if item.strip()]


def _slug(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    return "-".join(part for part in "".join(chars).split("-") if part) or "record"


def _escape_path(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
