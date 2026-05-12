"""Supported taxonomy and command catalog reports."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .models import EVENT_TYPES, IMPACTS, REVIEW_ACTIONS, STATUSES
from .quality_gate import DIAGNOSTIC_CODES, PROFILES, QUALITY_PROFILES, REQUIRED_SCENARIOS


VALIDATION_DIAGNOSTIC_CODES = {
    "MCC-VAL-BROKER-001": "broker view date is after dataset as_of",
    "MCC-VAL-CONFIDENCE-001": "confidence range or confirmed/completed confidence mismatch",
    "MCC-VAL-DATE-001": "last_reviewed is after dataset as_of",
    "MCC-VAL-DATE-002": "evidence_checked_at is after dataset as_of",
    "MCC-VAL-DATE-003": "outcome_recorded_at is after dataset as_of",
    "MCC-VAL-DATE-004": "outcome_recorded_at is before the event window starts",
    "MCC-VAL-EVIDENCE-001": "record has no evidence URLs",
    "MCC-VAL-EVIDENCE-002": "evidence URL is not valid http(s)",
    "MCC-VAL-GENERAL-001": "validation error without a more specific diagnostic",
    "MCC-VAL-HISTORY-001": "history contains a future update",
    "MCC-VAL-HISTORY-002": "latest history status does not match current status",
    "MCC-VAL-IDENTITY-001": "duplicate record id",
    "MCC-VAL-IDENTITY-002": "ticker or entity is missing",
    "MCC-VAL-IDENTITY-003": "ticker format is unsupported",
    "MCC-VAL-OUTCOME-001": "outcome_recorded_at is set without actual_outcome",
    "MCC-VAL-REVIEW-001": "open record has no required review action",
    "MCC-VAL-SCENARIO-001": "required bull/base/bear scenario note is missing",
}

QUALITY_RULES = {
    "broker_caveats": "broker views must have substantive caveats and fresh source dates when required",
    "minimum_evidence": "records must meet evidence URL count and freshness metadata thresholds",
    "no_placeholder_urls": "evidence and broker URLs cannot use placeholder or sample hosts/terms",
    "release_metadata": "strict profile records must include sector, theme, thesis_id, and source_ref",
    "review_freshness": "last_reviewed must exist and fall within the profile freshness window",
    "scenario_completeness": "bull/base/bear notes must exist and be substantive",
}

COMMAND_CATALOG = [
    {
        "id": "validate",
        "category": "quality",
        "formats": ["json"],
        "inputs": ["dataset"],
        "purpose": "validate schema and optional quality profile diagnostics",
        "writes_files": False,
    },
    {"id": "upcoming", "category": "calendar", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "list upcoming open catalysts", "writes_files": False},
    {"id": "stale", "category": "review", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "list catalysts whose review state is stale", "writes_files": False},
    {"id": "brief", "category": "briefing", "formats": ["markdown"], "inputs": ["dataset"], "purpose": "render an analyst catalyst brief", "writes_files": False},
    {"id": "exposure", "category": "portfolio", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "aggregate portfolio exposure by ticker/event/urgency", "writes_files": False},
    {"id": "risk-budget", "category": "portfolio", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "compare event max loss with risk budgets", "writes_files": False},
    {"id": "sector-map", "category": "taxonomy", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "group catalysts by sector and theme", "writes_files": False},
    {"id": "review-plan", "category": "review", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "create review actions for stale and high-urgency catalysts", "writes_files": False},
    {"id": "thesis-map", "category": "taxonomy", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "group catalysts by thesis id and evidence references", "writes_files": False},
    {"id": "scenario-matrix", "category": "scenario", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "render bull/base/bear event scenarios", "writes_files": False},
    {"id": "evidence-audit", "category": "quality", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "audit evidence freshness, source count, and concentration", "writes_files": False},
    {"id": "quality-gate", "category": "quality", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "apply publication quality rules and diagnostic codes", "writes_files": False},
    {"id": "doctor", "category": "quality", "formats": ["json", "markdown", "patch"], "inputs": ["dataset"], "purpose": "suggest read-only repairs for validation and quality failures", "writes_files": False},
    {"id": "broker-matrix", "category": "broker", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "summarize broker views and target dispersion", "writes_files": False},
    {"id": "source-pack", "category": "sources", "formats": ["json", "csv", "markdown"], "inputs": ["dataset"], "purpose": "deduplicate source URLs for collection and review", "writes_files": False},
    {"id": "watchlist", "category": "review", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "convert open catalysts into watch items", "writes_files": False},
    {"id": "decision-log", "category": "decision", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "emit decision memo stubs", "writes_files": False},
    {"id": "drilldown", "category": "dossier", "formats": ["json", "markdown"], "inputs": ["dataset", "ticker"], "purpose": "compose a single-ticker catalyst dossier", "writes_files": False},
    {"id": "command-cookbook", "category": "operations", "formats": ["markdown"], "inputs": ["dataset"], "purpose": "render field-aware command playbooks", "writes_files": False},
    {"id": "tutorial", "category": "learning", "formats": ["markdown"], "inputs": ["demo data"], "purpose": "render a notebooks-free tutorial", "writes_files": True},
    {"id": "agent-handoff", "category": "agent", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "create downstream research-agent context packs", "writes_files": False},
    {"id": "run-preset", "category": "packet", "formats": ["json", "directory"], "inputs": ["presets", "dataset"], "purpose": "execute named preset report packets", "writes_files": True},
    {"id": "taxonomy", "category": "metadata", "formats": ["json", "markdown"], "inputs": [], "purpose": "report supported event types, statuses, actions, rules, diagnostics, and commands", "writes_files": True},
    {"id": "post-event", "category": "review", "formats": ["json", "markdown"], "inputs": ["dataset"], "purpose": "queue missing post-event outcome reviews", "writes_files": False},
    {"id": "export-demo", "category": "fixture", "formats": ["json"], "inputs": [], "purpose": "write the built-in demo dataset", "writes_files": True},
    {"id": "export-preset-example", "category": "fixture", "formats": ["json"], "inputs": [], "purpose": "write starter preset configuration", "writes_files": True},
    {"id": "demo-bundle", "category": "fixture", "formats": ["directory"], "inputs": [], "purpose": "write all demo outputs plus manifest and transcript", "writes_files": True},
    {"id": "fixture-gallery", "category": "fixture", "formats": ["json", "markdown"], "inputs": [], "purpose": "list bundled fixture hashes and provenance", "writes_files": True},
    {"id": "compare", "category": "dataset", "formats": ["json", "markdown"], "inputs": ["base dataset", "current dataset"], "purpose": "compare two dataset snapshots", "writes_files": True},
    {"id": "merge", "category": "dataset", "formats": ["json"], "inputs": ["datasets"], "purpose": "merge datasets with provenance and validation", "writes_files": True},
    {"id": "html-dashboard", "category": "site", "formats": ["html"], "inputs": ["dataset"], "purpose": "render a static HTML dashboard", "writes_files": True},
    {"id": "static-site", "category": "site", "formats": ["directory"], "inputs": ["dataset"], "purpose": "write a multi-page static site", "writes_files": True},
    {"id": "export-csv", "category": "interchange", "formats": ["csv"], "inputs": ["dataset"], "purpose": "export dataset rows to CSV", "writes_files": True},
    {"id": "export-ics", "category": "interchange", "formats": ["ics"], "inputs": ["dataset"], "purpose": "export upcoming catalysts to iCalendar", "writes_files": True},
    {"id": "import-csv", "category": "interchange", "formats": ["json"], "inputs": ["csv"], "purpose": "import CSV rows as dataset JSON", "writes_files": True},
    {"id": "create-archive", "category": "archive", "formats": ["directory"], "inputs": ["dataset"], "purpose": "create portable report archive with hashes", "writes_files": True},
    {"id": "verify-archive", "category": "archive", "formats": ["json"], "inputs": ["archive directory"], "purpose": "verify archive hashes and file inventory", "writes_files": False},
    {"id": "release-audit", "category": "release", "formats": ["json", "markdown"], "inputs": ["repo"], "purpose": "audit release examples, docs, skill, and workflows", "writes_files": False},
    {"id": "changelog", "category": "release", "formats": ["json", "markdown"], "inputs": ["git repo"], "purpose": "render local release notes from commits", "writes_files": True},
    {"id": "smoke-matrix", "category": "release", "formats": ["json", "markdown"], "inputs": ["demo data"], "purpose": "run offline smoke checks for CLI commands", "writes_files": False},
    {"id": "finalize-release", "category": "release", "formats": ["json", "markdown"], "inputs": ["repo", "git repo"], "purpose": "combine release audit, smoke matrix, fixture gallery, and changelog into a checklist", "writes_files": True},
]


def taxonomy_json() -> Dict[str, object]:
    """Return deterministic supported taxonomy and command metadata."""

    diagnostic_codes = [
        {"code": code, "source": "validate", "detail": detail}
        for code, detail in sorted(VALIDATION_DIAGNOSTIC_CODES.items())
    ]
    diagnostic_codes.extend(
        {
            "code": code,
            "detail": f"{rule}.{reason}",
            "rule": rule,
            "source": "quality-gate",
        }
        for (rule, reason), code in sorted(DIAGNOSTIC_CODES.items(), key=lambda item: item[1])
    )
    profiles = [
        {
            "max_broker_age_days": profile.max_broker_age_days,
            "max_evidence_age_days": profile.max_evidence_age_days,
            "max_review_age_days": profile.max_review_age_days,
            "min_broker_caveat_chars": profile.min_broker_caveat_chars,
            "min_evidence_urls": profile.min_evidence_urls,
            "min_scenario_note_chars": profile.min_scenario_note_chars,
            "name": profile.name,
            "require_broker_views": profile.require_broker_views,
            "require_release_metadata": profile.require_release_metadata,
        }
        for profile in (QUALITY_PROFILES[name] for name in PROFILES)
    ]
    return {
        "schema_version": "taxonomy/v1",
        "diagnostic_codes": diagnostic_codes,
        "event_types": _values(EVENT_TYPES),
        "impact_values": _values(IMPACTS),
        "output_commands": sorted(command["id"] for command in COMMAND_CATALOG if command["writes_files"]),
        "quality_profiles": profiles,
        "quality_rules": [{"id": rule, "detail": detail} for rule, detail in sorted(QUALITY_RULES.items())],
        "required_scenarios": list(REQUIRED_SCENARIOS),
        "review_actions": _values(REVIEW_ACTIONS),
        "statuses": _values(STATUSES),
        "summary": {
            "command_count": len(COMMAND_CATALOG),
            "diagnostic_code_count": len(diagnostic_codes),
            "event_type_count": len(EVENT_TYPES),
            "output_command_count": sum(1 for command in COMMAND_CATALOG if command["writes_files"]),
            "quality_rule_count": len(QUALITY_RULES),
        },
        "commands": sorted(COMMAND_CATALOG, key=lambda command: str(command["id"])),
    }


def taxonomy_markdown() -> str:
    payload = taxonomy_json()
    lines = [
        "# Market Catalyst Taxonomy",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Commands: {payload['summary']['command_count']}",
        f"Diagnostic codes: {payload['summary']['diagnostic_code_count']}",
        "",
    ]
    _append_values(lines, "Event Types", payload["event_types"])
    _append_values(lines, "Statuses", payload["statuses"])
    _append_values(lines, "Review Actions", payload["review_actions"])
    _append_table(lines, "Quality Rules", ["Rule", "Detail"], ((item["id"], item["detail"]) for item in payload["quality_rules"]))
    _append_table(
        lines,
        "Diagnostic Codes",
        ["Code", "Source", "Rule/Detail"],
        (
            (
                item["code"],
                item["source"],
                item.get("rule", item["detail"]),
            )
            for item in payload["diagnostic_codes"]
        ),
    )
    _append_table(
        lines,
        "Output Commands",
        ["Command", "Formats", "Purpose"],
        (
            (
                command["id"],
                ", ".join(command["formats"]),
                command["purpose"],
            )
            for command in payload["commands"]
            if command["id"] in payload["output_commands"]
        ),
    )
    _append_table(
        lines,
        "All Commands",
        ["Command", "Category", "Formats"],
        ((command["id"], command["category"], ", ".join(command["formats"])) for command in payload["commands"]),
    )
    return "\n".join(lines).rstrip() + "\n"


def _values(values: Iterable[str]) -> List[str]:
    return sorted(values)


def _append_values(lines: List[str], title: str, values: object) -> None:
    lines.extend([f"## {title}", ""])
    for value in values:  # type: ignore[assignment]
        lines.append(f"- `{value}`")
    lines.append("")


def _append_table(lines: List[str], title: str, headers: List[str], rows: Iterable[tuple[object, ...]]) -> None:
    lines.extend([f"## {title}", "", "| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"])
    for row in rows:
        lines.append("| " + " | ".join(_cell(str(value)) for value in row) + " |")
    lines.append("")


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
