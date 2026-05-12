"""Preset workflow execution for deterministic report packets."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence

from .agent_handoff import agent_handoff_json, agent_handoff_markdown
from .dashboard import html_dashboard
from .evidence import evidence_audit_json, evidence_audit_markdown
from .io import dump_json, load_dataset, read_json
from .models import CatalystRecord, Dataset, validation_errors
from .quality_gate import PROFILES, quality_gate_json, quality_gate_markdown
from .render import (
    brief_markdown,
    broker_matrix_json,
    broker_matrix_markdown,
    decision_log_json,
    decision_log_markdown,
    exposure_json,
    exposure_markdown,
    records_json,
    review_plan_json,
    review_plan_markdown,
    risk_budget_json,
    risk_budget_markdown,
    scenario_matrix_json,
    scenario_matrix_markdown,
    sector_map_json,
    sector_map_markdown,
    source_pack_csv,
    source_pack_json,
    source_pack_markdown,
    thesis_map_json,
    thesis_map_markdown,
    watchlist_json,
    watchlist_markdown,
)
from .scoring import score_record


DEFAULT_WORKFLOWS = [
    "validate",
    "quality-gate",
    "upcoming",
    "stale",
    "brief",
    "review-plan",
    "source-pack",
    "watchlist",
    "agent-handoff",
]


@dataclass(frozen=True)
class PresetRun:
    name: str
    input_path: str
    as_of: date
    days: int
    stale_after_days: int
    profile: str
    output_dir: Path
    workflows: List[str]


@dataclass(frozen=True)
class WorkflowResult:
    id: str
    path: str
    command: str
    exit_code: int
    bytes: int
    sha256: str


def run_preset(
    presets_path: str,
    name: str,
    input_override: Optional[str] = None,
    as_of_override: Optional[str] = None,
    output_dir_override: Optional[str] = None,
) -> Dict[str, object]:
    """Execute a named preset and return a deterministic manifest payload."""

    config = read_json(presets_path)
    return run_preset_config(config, name, input_override, as_of_override, output_dir_override, write_files=True)


def run_preset_config(
    config: Mapping[str, object],
    name: str,
    input_override: Optional[str] = None,
    as_of_override: Optional[str] = None,
    output_dir_override: Optional[str] = None,
    write_files: bool = True,
    dataset_override: Optional[Dataset] = None,
) -> Dict[str, object]:
    """Execute or render a preset manifest from an already-loaded config."""

    preset = _resolve_preset(config, name, input_override, as_of_override, output_dir_override)
    if preset.days < 0:
        raise ValueError("preset days must be non-negative")
    if preset.stale_after_days < 0:
        raise ValueError("preset stale_after_days must be non-negative")
    if preset.profile not in PROFILES:
        raise ValueError(f"preset profile must be one of: {', '.join(PROFILES)}")

    dataset = dataset_override or load_dataset(preset.input_path)
    if write_files:
        preset.output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for workflow in preset.workflows:
        result = _run_workflow(workflow, preset, dataset)
        if write_files:
            _write_text(preset.output_dir / result.path, result.text)
        digest, byte_count = _hash_bytes(result.text.encode("utf-8"))
        results.append(
            WorkflowResult(
                id=workflow,
                path=result.path,
                command=result.command,
                exit_code=result.exit_code,
                bytes=byte_count,
                sha256=digest,
            )
        )

    manifest = _manifest(preset, dataset, results)
    if write_files:
        _write_text(preset.output_dir / "manifest.json", dump_json(manifest))
    return manifest


@dataclass(frozen=True)
class _RenderedWorkflow:
    text: str
    path: str
    command: str
    exit_code: int = 0


def _resolve_preset(
    config: Mapping[str, object],
    name: str,
    input_override: Optional[str],
    as_of_override: Optional[str],
    output_dir_override: Optional[str],
) -> PresetRun:
    presets = config.get("presets")
    if not isinstance(presets, Mapping):
        raise ValueError("presets JSON must contain a presets object")
    raw = presets.get(name)
    if not isinstance(raw, Mapping):
        raise ValueError(f"preset not found: {name}")
    defaults = config.get("defaults", {})
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, Mapping):
        raise ValueError("presets defaults must be an object")

    input_path = input_override or _string_value(raw, "input") or _string_value(defaults, "input")
    if not input_path:
        raise ValueError(f"preset {name} requires input")
    as_of_value = as_of_override or _string_value(raw, "as_of") or _string_value(defaults, "as_of")
    if not as_of_value:
        raise ValueError(f"preset {name} requires as_of")
    output_dir = output_dir_override or _string_value(raw, "output_dir") or _string_value(defaults, "output_dir") or "reports"
    days = _int_value(raw, "days", _int_value(defaults, "days", 45))
    stale_after_days = _int_value(raw, "stale_after_days", _int_value(defaults, "stale_after_days", 14))
    profile = _string_value(raw, "profile") or _string_value(defaults, "profile") or "public"
    workflows = _workflows(raw.get("workflows", defaults.get("workflows", DEFAULT_WORKFLOWS)))
    return PresetRun(
        name=name,
        input_path=input_path,
        as_of=date.fromisoformat(as_of_value),
        days=days,
        stale_after_days=stale_after_days,
        profile=profile,
        output_dir=Path(output_dir),
        workflows=workflows,
    )


def _run_workflow(workflow: str, preset: PresetRun, dataset: Dataset) -> _RenderedWorkflow:
    upcoming = _upcoming_records(dataset.records, preset.as_of, preset.days)
    stale = _stale_records(dataset.records, preset.as_of, preset.stale_after_days)
    command_prefix = f"python -m market_catalyst_calendar {workflow} --input {preset.input_path} --as-of {preset.as_of.isoformat()}"

    workflow_map: Dict[str, Callable[[], _RenderedWorkflow]] = {
        "validate": lambda: _validate_workflow(preset, dataset),
        "quality-gate": lambda: _quality_gate_workflow(preset, dataset),
        "upcoming": lambda: _RenderedWorkflow(dump_json(records_json(upcoming, preset.as_of)), "upcoming.json", f"{command_prefix} --days {preset.days}"),
        "stale": lambda: _RenderedWorkflow(dump_json(records_json(stale, preset.as_of)), "stale.json", f"{command_prefix} --stale-after-days {preset.stale_after_days}"),
        "brief": lambda: _RenderedWorkflow(brief_markdown(upcoming, preset.as_of), "brief.md", f"{command_prefix} --days {preset.days}"),
        "exposure": lambda: _RenderedWorkflow(dump_json(exposure_json(upcoming, preset.as_of)), "exposure.json", f"{command_prefix} --days {preset.days}"),
        "exposure-markdown": lambda: _RenderedWorkflow(exposure_markdown(upcoming, preset.as_of), "exposure.md", f"{command_prefix} --days {preset.days} --format markdown"),
        "risk-budget": lambda: _RenderedWorkflow(dump_json(risk_budget_json(upcoming, preset.as_of)), "risk_budget.json", f"{command_prefix} --days {preset.days}"),
        "risk-budget-markdown": lambda: _RenderedWorkflow(risk_budget_markdown(upcoming, preset.as_of), "risk_budget.md", f"{command_prefix} --days {preset.days} --format markdown"),
        "sector-map": lambda: _RenderedWorkflow(dump_json(sector_map_json(dataset.records, preset.as_of, preset.stale_after_days)), "sector_map.json", f"{command_prefix} --stale-after-days {preset.stale_after_days}"),
        "sector-map-markdown": lambda: _RenderedWorkflow(sector_map_markdown(dataset.records, preset.as_of, preset.stale_after_days), "sector_map.md", f"{command_prefix} --stale-after-days {preset.stale_after_days} --format markdown"),
        "review-plan": lambda: _RenderedWorkflow(dump_json(review_plan_json(dataset.records, preset.as_of, preset.days, preset.stale_after_days)), "review_plan.json", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days}"),
        "review-plan-markdown": lambda: _RenderedWorkflow(review_plan_markdown(dataset.records, preset.as_of, preset.days, preset.stale_after_days), "review_plan.md", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days} --format markdown"),
        "thesis-map": lambda: _RenderedWorkflow(dump_json(thesis_map_json(dataset.records, preset.as_of, preset.stale_after_days)), "thesis_map.json", f"{command_prefix} --stale-after-days {preset.stale_after_days}"),
        "thesis-map-markdown": lambda: _RenderedWorkflow(thesis_map_markdown(dataset.records, preset.as_of, preset.stale_after_days), "thesis_map.md", f"{command_prefix} --stale-after-days {preset.stale_after_days} --format markdown"),
        "scenario-matrix": lambda: _RenderedWorkflow(dump_json(scenario_matrix_json(upcoming, preset.as_of, preset.stale_after_days)), "scenario_matrix.json", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days}"),
        "scenario-matrix-markdown": lambda: _RenderedWorkflow(scenario_matrix_markdown(upcoming, preset.as_of, preset.stale_after_days), "scenario_matrix.md", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days} --format markdown"),
        "evidence-audit": lambda: _RenderedWorkflow(dump_json(evidence_audit_json(dataset.records, preset.as_of, preset.stale_after_days, 2, 0.67)), "evidence_audit.json", f"{command_prefix} --fresh-after-days {preset.stale_after_days}"),
        "evidence-audit-markdown": lambda: _RenderedWorkflow(evidence_audit_markdown(dataset.records, preset.as_of, preset.stale_after_days, 2, 0.67), "evidence_audit.md", f"{command_prefix} --fresh-after-days {preset.stale_after_days} --format markdown"),
        "broker-matrix": lambda: _RenderedWorkflow(dump_json(broker_matrix_json(dataset.records, preset.as_of, 30)), "broker_matrix.json", f"{command_prefix} --stale-after-days 30"),
        "broker-matrix-markdown": lambda: _RenderedWorkflow(broker_matrix_markdown(dataset.records, preset.as_of, 30), "broker_matrix.md", f"{command_prefix} --stale-after-days 30 --format markdown"),
        "source-pack": lambda: _RenderedWorkflow(dump_json(source_pack_json(dataset.records, preset.as_of, preset.stale_after_days)), "source_pack.json", f"{command_prefix} --fresh-after-days {preset.stale_after_days}"),
        "source-pack-csv": lambda: _RenderedWorkflow(source_pack_csv(dataset.records, preset.as_of, preset.stale_after_days), "source_pack.csv", f"{command_prefix} --fresh-after-days {preset.stale_after_days} --format csv"),
        "source-pack-markdown": lambda: _RenderedWorkflow(source_pack_markdown(dataset.records, preset.as_of, preset.stale_after_days), "source_pack.md", f"{command_prefix} --fresh-after-days {preset.stale_after_days} --format markdown"),
        "watchlist": lambda: _RenderedWorkflow(dump_json(watchlist_json(dataset.records, preset.as_of, preset.days, preset.stale_after_days)), "watchlist.json", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days}"),
        "watchlist-markdown": lambda: _RenderedWorkflow(watchlist_markdown(dataset.records, preset.as_of, preset.days, preset.stale_after_days), "watchlist.md", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days} --format markdown"),
        "decision-log": lambda: _RenderedWorkflow(dump_json(decision_log_json(dataset.records, preset.as_of, preset.days, preset.stale_after_days)), "decision_log.json", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days}"),
        "decision-log-markdown": lambda: _RenderedWorkflow(decision_log_markdown(dataset.records, preset.as_of, preset.days, preset.stale_after_days), "decision_log.md", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days} --format markdown"),
        "agent-handoff": lambda: _RenderedWorkflow(dump_json(agent_handoff_json(dataset, preset.as_of, preset.input_path, preset.output_dir.as_posix(), preset.days, preset.stale_after_days, preset.stale_after_days, 5)), "agent_handoff.json", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days} --fresh-after-days {preset.stale_after_days} --output-dir {preset.output_dir.as_posix()}"),
        "agent-handoff-markdown": lambda: _RenderedWorkflow(agent_handoff_markdown(dataset, preset.as_of, preset.input_path, preset.output_dir.as_posix(), preset.days, preset.stale_after_days, preset.stale_after_days, 5), "agent_handoff.md", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days} --fresh-after-days {preset.stale_after_days} --output-dir {preset.output_dir.as_posix()} --format markdown"),
        "html-dashboard": lambda: _RenderedWorkflow(html_dashboard(dataset.records, preset.as_of, preset.days, preset.stale_after_days), "dashboard.html", f"{command_prefix} --days {preset.days} --stale-after-days {preset.stale_after_days}"),
    }
    if workflow not in workflow_map:
        raise ValueError(f"unsupported preset workflow: {workflow}")
    return workflow_map[workflow]()


def _validate_workflow(preset: PresetRun, dataset: Dataset) -> _RenderedWorkflow:
    errors = validation_errors(dataset)
    payload = {"ok": not errors, "record_count": len(dataset.records)}
    if errors:
        payload["errors"] = errors
    return _RenderedWorkflow(
        dump_json(payload),
        "validate.json",
        f"python -m market_catalyst_calendar validate --profile basic --input {preset.input_path}",
        0 if not errors else 1,
    )


def _quality_gate_workflow(preset: PresetRun, dataset: Dataset) -> _RenderedWorkflow:
    payload = quality_gate_json(dataset.records, preset.as_of, None, None, None, None, preset.profile)
    return _RenderedWorkflow(
        dump_json(payload),
        "quality_gate.json",
        f"python -m market_catalyst_calendar quality-gate --profile {preset.profile} --input {preset.input_path} --as-of {preset.as_of.isoformat()}",
        0 if payload["ok"] else 1,
    )


def _manifest(preset: PresetRun, dataset: Dataset, results: Sequence[WorkflowResult]) -> Dict[str, object]:
    return {
        "schema_version": "preset-run/v1",
        "ok": True,
        "preset": preset.name,
        "input": preset.input_path,
        "as_of": preset.as_of.isoformat(),
        "parameters": {
            "days": preset.days,
            "output_dir": preset.output_dir.as_posix(),
            "profile": preset.profile,
            "stale_after_days": preset.stale_after_days,
        },
        "summary": {
            "artifact_count": len(results) + 1,
            "record_count": len(dataset.records),
            "report_failure_count": sum(1 for result in results if result.exit_code != 0),
            "workflow_count": len(results),
        },
        "artifacts": [
            {
                "bytes": result.bytes,
                "command": result.command,
                "exit_code": result.exit_code,
                "path": result.path,
                "sha256": result.sha256,
                "workflow": result.id,
            }
            for result in results
        ],
        "manifest": "manifest.json",
    }


def _upcoming_records(records: Iterable[CatalystRecord], as_of: date, days: int) -> List[CatalystRecord]:
    return [
        record
        for record in records
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]


def _stale_records(records: Iterable[CatalystRecord], as_of: date, stale_after_days: int) -> List[CatalystRecord]:
    return [
        record
        for record in records
        if score_record(record, as_of, stale_after_days=stale_after_days).review_state == "stale"
    ]


def _workflows(value: object) -> List[str]:
    if not isinstance(value, list) or not value:
        raise ValueError("preset workflows must be a non-empty array")
    workflows = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError("preset workflows must contain non-empty strings")
        workflows.append(item)
    return workflows


def _string_value(mapping: Mapping[str, object], key: str) -> Optional[str]:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"preset {key} must be a non-empty string")
    return value


def _int_value(mapping: Mapping[str, object], key: str, default: int) -> int:
    value = mapping.get(key)
    if value is None:
        return default
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"preset {key} must be an integer")
    return value


def _hash_bytes(data: bytes) -> tuple[str, int]:
    return hashlib.sha256(data).hexdigest(), len(data)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
