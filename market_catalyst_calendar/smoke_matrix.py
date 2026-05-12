"""Internal smoke matrix for every CLI command."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List

from .csv_io import dataset_to_csv
from .demo import DEMO_DATA, DEMO_UPDATED_DATA
from .io import dump_json
from .models import parse_dataset


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AS_OF = "2026-05-13"
UPDATED_AS_OF = "2026-05-27"
POST_EVENT_AS_OF = "2026-06-25"


@dataclass(frozen=True)
class SmokeCase:
    command: str
    args: List[str]
    expected_exit_code: int = 0
    expected_files: List[str] = field(default_factory=lambda: ["stdout"])
    required_stdout: str = ""
    setup_archive: bool = False
    setup_changelog_repo: bool = False


def smoke_matrix_json(fmt: str = "json", include_finalize: bool = True) -> Dict[str, object]:
    """Run smoke checks against built-in demo fixtures and return a report."""

    with tempfile.TemporaryDirectory(prefix="mcc-smoke-") as tmp:
        work = Path(tmp)
        context = _write_demo_workspace(work)
        results = [_run_case(case, context) for case in _smoke_cases(include_finalize)]
    failed = sum(1 for result in results if result["status"] != "pass")
    return {
        "schema_version": "smoke-matrix/v1",
        "ok": failed == 0,
        "format": fmt,
        "summary": {
            "command_count": len(results),
            "failed_count": failed,
            "passed_count": len(results) - failed,
        },
        "commands": results,
    }


def smoke_matrix_markdown(report: Dict[str, object]) -> str:
    lines = [
        "# Market Catalyst Smoke Matrix",
        "",
        f"Status: {'PASS' if report['ok'] else 'FAIL'}",
        f"Commands: {report['summary']['passed_count']} passed / {report['summary']['command_count']} checked",
        "",
        "| Command | Status | Exit | Expected | Files | Duration |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["commands"]:
        files = ", ".join(item["expected_files"])
        lines.append(
            f"| {item['command']} | {str(item['status']).upper()} | {item['exit_code']} | "
            f"{item['expected_exit_code']} | {files} | {item['duration_bucket']} |"
        )
    failed = [item for item in report["commands"] if item["status"] != "pass"]
    if failed:
        lines.append("")
        lines.append("## Failures")
        for item in failed:
            lines.append(f"- `{item['command']}`: {item['detail']}")
    return "\n".join(lines).rstrip() + "\n"


def smoke_probe_json() -> Dict[str, object]:
    return {"ok": True, "schema_version": "smoke-probe/v1"}


def _write_demo_workspace(work: Path) -> Dict[str, Path]:
    base = work / "demo_records.json"
    updated = work / "demo_records_updated.json"
    csv_path = work / "demo_records.csv"
    presets = work / "presets.json"
    base.write_text(dump_json(DEMO_DATA), encoding="utf-8")
    updated.write_text(dump_json(DEMO_UPDATED_DATA), encoding="utf-8")
    csv_path.write_text(dataset_to_csv(parse_dataset(DEMO_DATA)), encoding="utf-8")
    presets.write_text(
        dump_json(
            {
                "defaults": {
                    "days": 45,
                    "output_dir": str(work / "preset-packet"),
                    "profile": "public",
                    "stale_after_days": 14,
                },
                "presets": {
                    "desk-packet": {
                        "as_of": DEFAULT_AS_OF,
                        "input": str(base),
                        "workflows": ["validate", "quality-gate", "upcoming", "review-plan", "agent-handoff"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return {
        "work": work,
        "base": base,
        "updated": updated,
        "csv": csv_path,
        "presets": presets,
        "archive": work / "archive",
        "bundle": work / "demo-bundle",
        "changelog_repo": work / "changelog-repo",
        "root": ROOT,
        "site": work / "site",
        "preset_packet": work / "preset-packet",
    }


def _run_case(case: SmokeCase, context: Dict[str, Path]) -> Dict[str, object]:
    if case.setup_archive:
        _create_archive_fixture(context)
    if case.setup_changelog_repo:
        _create_changelog_repo(context["changelog_repo"])
    args = [_resolve_arg(arg, context) for arg in case.args]
    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-m", "market_catalyst_calendar", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.monotonic() - start
    missing = _missing_expected_files(case.expected_files, context)
    stdout_missing = bool(case.required_stdout and case.required_stdout not in result.stdout)
    status = "pass"
    detail = "ok"
    if result.returncode != case.expected_exit_code:
        status = "fail"
        detail = f"exit code {result.returncode}, expected {case.expected_exit_code}"
    elif missing:
        status = "fail"
        detail = "missing expected files: " + ", ".join(missing)
    elif stdout_missing:
        status = "fail"
        detail = f"stdout did not contain {case.required_stdout!r}"
    return {
        "command": case.command,
        "args": case.args,
        "status": status,
        "detail": detail,
        "exit_code": result.returncode,
        "expected_exit_code": case.expected_exit_code,
        "expected_files": case.expected_files,
        "duration_bucket": _duration_bucket(elapsed),
    }


def _smoke_cases(include_finalize: bool = True) -> List[SmokeCase]:
    base = "{base}"
    updated = "{updated}"
    csv_path = "{csv}"
    presets = "{presets}"
    archive = "{archive}"
    bundle = "{bundle}"
    changelog_repo = "{changelog_repo}"
    cases = [
        SmokeCase("validate", ["validate", "--input", base], required_stdout='"ok": true'),
        SmokeCase("upcoming", ["upcoming", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"]),
        SmokeCase("stale", ["stale", "--input", base, "--as-of", DEFAULT_AS_OF]),
        SmokeCase("brief", ["brief", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"], required_stdout="# Market Catalyst Brief"),
        SmokeCase("exposure", ["exposure", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"]),
        SmokeCase("exposure markdown", ["exposure", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--format", "markdown"], required_stdout="# Market Catalyst Exposure"),
        SmokeCase("risk-budget", ["risk-budget", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"]),
        SmokeCase("risk-budget markdown", ["risk-budget", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--format", "markdown"], required_stdout="# Market Catalyst Risk Budget"),
        SmokeCase("sector-map", ["sector-map", "--input", base, "--as-of", DEFAULT_AS_OF]),
        SmokeCase("sector-map markdown", ["sector-map", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "markdown"], required_stdout="# Market Catalyst Sector Map"),
        SmokeCase("review-plan", ["review-plan", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"]),
        SmokeCase("review-plan markdown", ["review-plan", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--format", "markdown"], required_stdout="# Market Catalyst Review Plan"),
        SmokeCase("thesis-map", ["thesis-map", "--input", base, "--as-of", DEFAULT_AS_OF]),
        SmokeCase("thesis-map markdown", ["thesis-map", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "markdown"], required_stdout="# Market Catalyst Thesis Map"),
        SmokeCase("scenario-matrix", ["scenario-matrix", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"]),
        SmokeCase("scenario-matrix markdown", ["scenario-matrix", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--format", "markdown"], required_stdout="# Market Catalyst Scenario Matrix"),
        SmokeCase("evidence-audit", ["evidence-audit", "--input", base, "--as-of", DEFAULT_AS_OF]),
        SmokeCase("evidence-audit markdown", ["evidence-audit", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "markdown"], required_stdout="# Market Catalyst Evidence Audit"),
        SmokeCase("quality-gate", ["quality-gate", "--profile", "public", "--input", base, "--as-of", DEFAULT_AS_OF], expected_exit_code=1, required_stdout='"ok": false'),
        SmokeCase("quality-gate markdown", ["quality-gate", "--profile", "public", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "markdown"], expected_exit_code=1, required_stdout="# Market Catalyst Quality Gate"),
        SmokeCase("doctor", ["doctor", "--profile", "public", "--input", base, "--as-of", DEFAULT_AS_OF], required_stdout='"schema_version": "doctor/v1"'),
        SmokeCase("doctor markdown", ["doctor", "--profile", "public", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "markdown"], required_stdout="# Market Catalyst Dataset Doctor"),
        SmokeCase("doctor patch", ["doctor", "--profile", "public", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "patch"], required_stdout='"op":'),
        SmokeCase("broker-matrix", ["broker-matrix", "--input", base, "--as-of", DEFAULT_AS_OF]),
        SmokeCase("broker-matrix markdown", ["broker-matrix", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "markdown"], required_stdout="# Market Catalyst Broker Matrix"),
        SmokeCase("source-pack", ["source-pack", "--input", base, "--as-of", DEFAULT_AS_OF]),
        SmokeCase("source-pack csv", ["source-pack", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "csv"], required_stdout="url,source_types"),
        SmokeCase("source-pack markdown", ["source-pack", "--input", base, "--as-of", DEFAULT_AS_OF, "--format", "markdown"], required_stdout="# Market Catalyst Source Pack"),
        SmokeCase("watchlist", ["watchlist", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"]),
        SmokeCase("watchlist markdown", ["watchlist", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--format", "markdown"], required_stdout="# Market Catalyst Watchlist"),
        SmokeCase("decision-log", ["decision-log", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"]),
        SmokeCase("decision-log markdown", ["decision-log", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--format", "markdown"], required_stdout="# Market Catalyst Decision Log"),
        SmokeCase("drilldown", ["drilldown", "--input", base, "--as-of", DEFAULT_AS_OF, "--ticker", "NVDA", "--days", "45"]),
        SmokeCase("drilldown markdown", ["drilldown", "--input", base, "--as-of", DEFAULT_AS_OF, "--ticker", "NVDA", "--days", "45", "--format", "markdown"], required_stdout="# NVDA Catalyst Drilldown"),
        SmokeCase("command-cookbook", ["command-cookbook", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"], required_stdout="# Market Catalyst Command Cookbook"),
        SmokeCase("tutorial", ["tutorial", "--as-of", DEFAULT_AS_OF, "--days", "45", "--dataset-path", "examples/demo_records.json"], required_stdout="# Market Catalyst Calendar Tutorial"),
        SmokeCase("agent-handoff", ["agent-handoff", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45"]),
        SmokeCase("agent-handoff markdown", ["agent-handoff", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--format", "markdown"], required_stdout="# Agent Handoff Pack"),
        SmokeCase("run-preset", ["run-preset", "--presets", presets, "--name", "desk-packet"], expected_files=["preset-packet/manifest.json", "preset-packet/upcoming.json"], required_stdout='"schema_version": "preset-run/v1"'),
        SmokeCase("taxonomy", ["taxonomy"], required_stdout='"schema_version": "taxonomy/v1"'),
        SmokeCase("taxonomy markdown", ["taxonomy", "--format", "markdown"], required_stdout="# Market Catalyst Taxonomy"),
        SmokeCase("version-report", ["version-report", "--root", "{root}", "--repo", "{root}"], required_stdout='"schema_version": "version-report/v1"'),
        SmokeCase("version-report markdown", ["version-report", "--root", "{root}", "--repo", "{root}", "--format", "markdown"], required_stdout="# Market Catalyst Version Report"),
        SmokeCase("post-event", ["post-event", "--input", base, "--as-of", POST_EVENT_AS_OF]),
        SmokeCase("post-event markdown", ["post-event", "--input", base, "--as-of", POST_EVENT_AS_OF, "--format", "markdown"], required_stdout="# Market Catalyst Post-Event Review"),
        SmokeCase("compare", ["compare", "--base", base, "--current", updated, "--as-of", UPDATED_AS_OF]),
        SmokeCase("compare markdown", ["compare", "--base", base, "--current", updated, "--as-of", UPDATED_AS_OF, "--format", "markdown"], required_stdout="# Market Catalyst Snapshot Compare"),
        SmokeCase("merge", ["merge", base, updated, "--as-of", UPDATED_AS_OF, "--output", "{work}/merge.json"], expected_files=["merge.json"]),
        SmokeCase("html-dashboard", ["html-dashboard", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--output", "{work}/dashboard.html"], expected_files=["dashboard.html"]),
        SmokeCase("static-site", ["static-site", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--output-dir", "{site}"], expected_files=["site/index.html", "site/sources.html", "site/dashboard.html", "site/manifest.json"]),
        SmokeCase("export-demo", ["export-demo", "--output", "{work}/exported_demo.json"], expected_files=["exported_demo.json"]),
        SmokeCase("export-demo updated", ["export-demo", "--snapshot", "updated", "--output", "{work}/exported_demo_updated.json"], expected_files=["exported_demo_updated.json"]),
        SmokeCase("export-preset-example", ["export-preset-example", "--output", "{work}/exported_presets.json"], expected_files=["exported_presets.json"]),
        SmokeCase("demo-bundle", ["demo-bundle", "--output-dir", bundle], expected_files=["demo-bundle/manifest.json"]),
        SmokeCase("fixture-gallery", ["fixture-gallery"], required_stdout='"schema_version": "fixture-gallery/v1"'),
        SmokeCase("fixture-gallery markdown", ["fixture-gallery", "--format", "markdown"], required_stdout="# Market Catalyst Fixture Gallery"),
        SmokeCase("export-csv", ["export-csv", "--input", base, "--output", "{work}/exported_demo.csv"], expected_files=["exported_demo.csv"]),
        SmokeCase("export-ics", ["export-ics", "--input", base, "--as-of", DEFAULT_AS_OF, "--days", "45", "--output", "{work}/upcoming.ics"], expected_files=["upcoming.ics"]),
        SmokeCase("import-csv", ["import-csv", "--input", csv_path, "--output", "{work}/imported_demo.json"], expected_files=["imported_demo.json"]),
        SmokeCase("create-archive", ["create-archive", "--input", base, "--output-dir", archive, "--as-of", DEFAULT_AS_OF, "--days", "45"], expected_files=["archive/manifest.json"]),
        SmokeCase("verify-archive", ["verify-archive", archive], setup_archive=True),
        SmokeCase("release-audit", ["release-audit", "--root", "{root}"]),
        SmokeCase("release-audit markdown", ["release-audit", "--root", "{root}", "--format", "markdown"], required_stdout="# Market Catalyst Release Audit"),
        SmokeCase("changelog", ["changelog", "--repo", changelog_repo, "--since-tag", "v0.1.0", "--format", "json"], setup_changelog_repo=True, required_stdout='"schema_version": "changelog/v1"'),
        SmokeCase("changelog markdown", ["changelog", "--repo", changelog_repo, "--since-tag", "v0.1.0", "--format", "markdown"], setup_changelog_repo=True, required_stdout="# Release Notes"),
        SmokeCase("smoke-matrix", ["smoke-matrix", "--probe"], required_stdout='"schema_version": "smoke-probe/v1"'),
    ]
    if include_finalize:
        cases.append(
            SmokeCase(
                "finalize-release",
                ["finalize-release", "--root", "{root}", "--repo", changelog_repo, "--since-tag", "v0.1.0"],
                setup_changelog_repo=True,
                required_stdout='"schema_version": "finalize-release/v1"',
            )
        )
    return cases


def _resolve_arg(arg: str, context: Dict[str, Path]) -> str:
    resolved = arg
    for key, value in context.items():
        resolved = resolved.replace("{" + key + "}", str(value))
    return resolved


def _missing_expected_files(expected_files: Iterable[str], context: Dict[str, Path]) -> List[str]:
    missing = []
    work = context["work"]
    for expected in expected_files:
        if expected == "stdout":
            continue
        if not (work / expected).is_file():
            missing.append(expected)
    return missing


def _duration_bucket(elapsed: float) -> str:
    if elapsed < 0.25:
        return "lt_250ms"
    if elapsed < 1:
        return "lt_1s"
    if elapsed < 5:
        return "lt_5s"
    return "gte_5s"


def _create_archive_fixture(context: Dict[str, Path]) -> None:
    archive = context["archive"]
    if (archive / "manifest.json").is_file():
        return
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "market_catalyst_calendar",
            "create-archive",
            "--input",
            str(context["base"]),
            "--output-dir",
            str(archive),
            "--as-of",
            DEFAULT_AS_OF,
            "--days",
            "45",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def _create_changelog_repo(repo: Path) -> None:
    if (repo / ".git").is_dir():
        return
    repo.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "Smoke Matrix",
            "GIT_AUTHOR_EMAIL": "smoke@example.com",
            "GIT_COMMITTER_NAME": "Smoke Matrix",
            "GIT_COMMITTER_EMAIL": "smoke@example.com",
            "GIT_AUTHOR_DATE": "2026-05-13T12:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-05-13T12:00:00+00:00",
        }
    )
    for args in (
        ["init"],
        ["config", "user.name", "Smoke Matrix"],
        ["config", "user.email", "smoke@example.com"],
    ):
        _run_git(repo, args, env)
    notes = repo / "notes.txt"
    notes.write_text("base\n", encoding="utf-8")
    _run_git(repo, ["add", "notes.txt"], env)
    _run_git(repo, ["commit", "-m", "chore: initial release"], env)
    _run_git(repo, ["tag", "v0.1.0"], env)
    notes.write_text("base\nfeature\n", encoding="utf-8")
    _run_git(repo, ["add", "notes.txt"], env)
    _run_git(repo, ["commit", "-m", "feat(cli): add smoke matrix #31"], env)


def _run_git(repo: Path, args: List[str], env: Dict[str, str]) -> None:
    result = subprocess.run(["git", *args], cwd=repo, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
