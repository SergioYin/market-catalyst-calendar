"""Deterministic catalyst dataset merge workflow."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .models import Dataset, parse_dataset, validation_errors


@dataclass(frozen=True)
class MergeSource:
    index: int
    label: str
    as_of: date
    raw: Dict[str, Any]
    dataset: Dataset


def merge_datasets_json(
    raw_datasets: Sequence[Dict[str, Any]],
    labels: Sequence[str],
    as_of_override: Optional[date] = None,
    prefer_newer_status_history: bool = False,
) -> Dict[str, Any]:
    if len(raw_datasets) < 2:
        raise ValueError("merge requires at least two input datasets")
    if len(raw_datasets) != len(labels):
        raise ValueError("merge labels must match input datasets")

    sources = [
        MergeSource(index=index, label=labels[index], as_of=parse_dataset(raw).as_of, raw=raw, dataset=parse_dataset(raw))
        for index, raw in enumerate(raw_datasets)
    ]
    merged_as_of = as_of_override if as_of_override else max(source.as_of for source in sources)
    candidates_by_id = _record_candidates_by_id(sources)

    records: List[Dict[str, Any]] = []
    record_sources: Dict[str, List[str]] = {}
    chosen_sources: Dict[str, str] = {}
    status_history_sources: Dict[str, str] = {}
    conflicts: List[Dict[str, Any]] = []

    for record_id in sorted(candidates_by_id):
        candidates = candidates_by_id[record_id]
        chosen = _choose_candidate(candidates, prefer_status_history=False)
        merged_record = copy.deepcopy(chosen[2])
        status_history_candidate = chosen
        if prefer_newer_status_history:
            status_history_candidate = _choose_candidate(candidates, prefer_status_history=True)
            merged_record["status"] = copy.deepcopy(status_history_candidate[2].get("status"))
            merged_record["history"] = copy.deepcopy(status_history_candidate[2].get("history", []))

        records.append(merged_record)
        record_sources[record_id] = sorted(source.label for source, _, _ in candidates)
        chosen_sources[record_id] = chosen[0].label
        status_history_sources[record_id] = status_history_candidate[0].label

        differing_fields = _differing_fields([candidate[2] for candidate in candidates])
        if differing_fields:
            conflicts.append(
                {
                    "chosen_source": chosen[0].label,
                    "fields": differing_fields,
                    "id": record_id,
                    "source_count": len(candidates),
                    "sources": _candidate_summaries(candidates),
                    "status_history_source": status_history_candidate[0].label,
                }
            )

    result = {
        "as_of": merged_as_of.isoformat(),
        "merge": {
            "conflicts": conflicts,
            "duplicate_ids": _duplicate_id_diagnostics(sources),
            "prefer_newer_status_history": prefer_newer_status_history,
            "record_sources": record_sources,
            "chosen_sources": chosen_sources,
            "status_history_sources": status_history_sources,
            "sources": [
                {
                    "as_of": source.as_of.isoformat(),
                    "index": source.index,
                    "label": source.label,
                    "record_count": len(source.dataset.records),
                }
                for source in sources
            ],
            "summary": {
                "conflict_count": len(conflicts),
                "duplicate_id_count": sum(len(item["ids"]) for item in _duplicate_id_diagnostics(sources)),
                "input_count": len(sources),
                "merged_record_count": len(records),
                "source_record_count": sum(len(source.dataset.records) for source in sources),
            },
        },
        "records": _sort_raw_records(records, merged_as_of),
    }
    merged_dataset = parse_dataset(result)
    errors = validation_errors(merged_dataset)
    result["merge"]["validation"] = {"ok": not errors, "errors": errors}
    return result


def _record_candidates_by_id(
    sources: Iterable[MergeSource],
) -> Dict[str, List[Tuple[MergeSource, int, Dict[str, Any]]]]:
    candidates: Dict[str, List[Tuple[MergeSource, int, Dict[str, Any]]]] = {}
    for source in sources:
        records = source.raw.get("records")
        if not isinstance(records, list):
            continue
        for record_index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            record_id = record.get("id")
            if not isinstance(record_id, str):
                continue
            candidates.setdefault(record_id, []).append((source, record_index, record))
    return candidates


def _choose_candidate(
    candidates: Sequence[Tuple[MergeSource, int, Dict[str, Any]]],
    prefer_status_history: bool,
) -> Tuple[MergeSource, int, Dict[str, Any]]:
    if prefer_status_history:
        return max(candidates, key=lambda candidate: (_latest_history_date(candidate[2]), candidate[0].as_of, candidate[0].index, candidate[1]))
    return max(candidates, key=lambda candidate: (candidate[0].as_of, candidate[0].index, candidate[1]))


def _latest_history_date(record: Dict[str, Any]) -> date:
    latest = date.min
    history = record.get("history")
    if isinstance(history, list):
        for entry in history:
            if not isinstance(entry, dict) or not isinstance(entry.get("date"), str):
                continue
            try:
                latest = max(latest, date.fromisoformat(entry["date"]))
            except ValueError:
                continue
    return latest


def _differing_fields(records: Sequence[Dict[str, Any]]) -> List[str]:
    fields = sorted(set().union(*(record.keys() for record in records)))
    differing = []
    for field in fields:
        values = [_canonical_value(record.get(field)) for record in records]
        if len(set(values)) > 1:
            differing.append(field)
    return differing


def _canonical_value(value: Any) -> str:
    return repr(_normalize(value))


def _normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return value


def _candidate_summaries(candidates: Sequence[Tuple[MergeSource, int, Dict[str, Any]]]) -> List[Dict[str, Any]]:
    return [
        {
            "as_of": source.as_of.isoformat(),
            "input_index": source.index,
            "record_index": record_index,
            "source": source.label,
            "status": record.get("status"),
            "latest_history_date": _date_or_none(_latest_history_date(record)),
        }
        for source, record_index, record in candidates
    ]


def _date_or_none(value: date) -> Optional[str]:
    if value == date.min:
        return None
    return value.isoformat()


def _duplicate_id_diagnostics(sources: Iterable[MergeSource]) -> List[Dict[str, Any]]:
    diagnostics: List[Dict[str, Any]] = []
    for source in sources:
        seen: Dict[str, int] = {}
        duplicates: Dict[str, List[int]] = {}
        records = source.raw.get("records")
        if not isinstance(records, list):
            continue
        for index, record in enumerate(records):
            if not isinstance(record, dict) or not isinstance(record.get("id"), str):
                continue
            record_id = record["id"]
            if record_id in seen:
                duplicates.setdefault(record_id, [seen[record_id]]).append(index)
            else:
                seen[record_id] = index
        if duplicates:
            diagnostics.append(
                {
                    "ids": sorted(duplicates),
                    "record_indexes": {record_id: duplicates[record_id] for record_id in sorted(duplicates)},
                    "source": source.label,
                }
            )
    return diagnostics


def _sort_raw_records(records: Sequence[Dict[str, Any]], as_of: date) -> List[Dict[str, Any]]:
    dataset = parse_dataset({"as_of": as_of.isoformat(), "records": list(records)})
    order = {record.record_id: index for index, record in enumerate(sorted(dataset.records, key=lambda item: (item.window.start, item.ticker, item.record_id)))}
    return sorted((copy.deepcopy(record) for record in records), key=lambda record: order[str(record["id"])])
