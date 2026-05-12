import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from market_catalyst_calendar.csv_io import CSV_COLUMNS, csv_to_dataset_json, dataset_to_csv
from market_catalyst_calendar.demo import DEMO_DATA, DEMO_UPDATED_DATA
from market_catalyst_calendar.demo_bundle import _bundle_files
from market_catalyst_calendar.models import parse_dataset, validation_errors
from market_catalyst_calendar.release_audit import RELEASE_AUDIT_SCHEMA_FIELDS, REQUIRED_COMMANDS
from market_catalyst_calendar.scoring import score_record


ROOT = Path(__file__).resolve().parents[1]


def load_selfcheck_module():
    spec = importlib.util.spec_from_file_location("selfcheck", ROOT / "scripts" / "selfcheck.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load scripts/selfcheck.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModelTests(unittest.TestCase):
    def test_demo_validates(self):
        dataset = parse_dataset(DEMO_DATA)
        self.assertEqual(validation_errors(dataset), [])
        self.assertEqual(len(dataset.records), 4)

    def test_scoring_prioritizes_near_regulatory_event(self):
        dataset = parse_dataset(DEMO_DATA)
        scores = {record.record_id: score_record(record, dataset.as_of).catalyst_score for record in dataset.records}
        self.assertGreater(scores["demo-pfe-fda-2026"], scores["demo-nvda-computex-2026"])

    def test_csv_round_trip_preserves_safe_separator_content(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["evidence_urls"] = [
            "https://example.com/research?case=bull|base&note=a=b",
            "https://example.com/channel-check,gpu-supply",
        ]
        raw["records"][0]["scenario_notes"]["bull"] = "Demand holds | upside = faster ramps\nWatch hyperscaler orders."
        raw["records"][0]["history"][0]["note"] = "Added after channel checks | needs = review."
        raw["records"][0]["broker_views"][0]["caveat"] = "Target assumes backlog | revenue = visible\nNeeds follow-up."
        raw["records"][0]["actual_outcome"] = "Keynote confirmed the next platform ramp | demand = intact."
        raw["records"][0]["outcome_recorded_at"] = "2026-06-03"

        imported = csv_to_dataset_json(dataset_to_csv(parse_dataset(raw)))

        first = next(record for record in imported["records"] if record["id"] == "demo-nvda-computex-2026")
        self.assertEqual(first["evidence_urls"], raw["records"][0]["evidence_urls"])
        self.assertEqual(first["scenario_notes"]["bull"], raw["records"][0]["scenario_notes"]["bull"])
        self.assertEqual(first["history"][0]["note"], raw["records"][0]["history"][0]["note"])
        self.assertEqual(first["position_size"], raw["records"][0]["position_size"])
        self.assertEqual(first["portfolio_weight"], raw["records"][0]["portfolio_weight"])
        self.assertEqual(first["risk_budget"], raw["records"][0]["risk_budget"])
        self.assertEqual(first["max_loss"], raw["records"][0]["max_loss"])
        self.assertEqual(first["sector"], raw["records"][0]["sector"])
        self.assertEqual(first["theme"], raw["records"][0]["theme"])
        self.assertEqual(first["thesis_id"], raw["records"][0]["thesis_id"])
        self.assertEqual(first["source_ref"], raw["records"][0]["source_ref"])
        self.assertEqual(first["evidence_checked_at"], raw["records"][0]["evidence_checked_at"])
        self.assertEqual(first["broker_views"][1]["caveat"], raw["records"][0]["broker_views"][0]["caveat"])
        self.assertEqual(first["actual_outcome"], raw["records"][0]["actual_outcome"])
        self.assertEqual(first["outcome_recorded_at"], raw["records"][0]["outcome_recorded_at"])

    def test_csv_import_accepts_missing_optional_exposure_columns(self):
        csv_text = dataset_to_csv(parse_dataset(DEMO_DATA))
        lines = csv_text.splitlines()
        indexes = [
            CSV_COLUMNS.index("position_size"),
            CSV_COLUMNS.index("portfolio_weight"),
            CSV_COLUMNS.index("risk_budget"),
            CSV_COLUMNS.index("max_loss"),
            CSV_COLUMNS.index("sector"),
            CSV_COLUMNS.index("theme"),
            CSV_COLUMNS.index("thesis_id"),
            CSV_COLUMNS.index("source_ref"),
            CSV_COLUMNS.index("evidence_checked_at"),
            CSV_COLUMNS.index("actual_outcome"),
            CSV_COLUMNS.index("outcome_recorded_at"),
        ]
        filtered = []
        for line in lines:
            columns = line.split(",")
            filtered.append(",".join(value for index, value in enumerate(columns) if index not in indexes))

        imported = csv_to_dataset_json("\n".join(filtered) + "\n")

        first = next(record for record in imported["records"] if record["id"] == "demo-pfe-fda-2026")
        self.assertIsNone(first["position_size"])
        self.assertIsNone(first["portfolio_weight"])
        self.assertIsNone(first["risk_budget"])
        self.assertIsNone(first["max_loss"])
        self.assertIsNone(first["sector"])
        self.assertIsNone(first["theme"])
        self.assertIsNone(first["thesis_id"])
        self.assertIsNone(first["source_ref"])
        self.assertNotIn("evidence_checked_at", first)
        self.assertNotIn("actual_outcome", first)
        self.assertNotIn("outcome_recorded_at", first)

    def test_portfolio_weight_must_be_decimal_weight(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["portfolio_weight"] = 8.25
        with self.assertRaisesRegex(ValueError, "portfolio_weight must be between 0 and 1"):
            parse_dataset(raw)

    def test_broker_view_source_url_must_be_valid(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["broker_views"][0]["source_url"] = "not-a-url"
        with self.assertRaisesRegex(ValueError, "source_url must be an http"):
            parse_dataset(raw)

    def test_outcome_recorded_at_requires_actual_outcome(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["as_of"] = "2026-06-03"
        raw["records"][0]["outcome_recorded_at"] = "2026-06-03"
        dataset = parse_dataset(raw)
        self.assertIn("outcome_recorded_at requires actual_outcome", validation_errors(dataset)[0])

    def test_updated_demo_validates(self):
        dataset = parse_dataset(DEMO_UPDATED_DATA)
        self.assertEqual(validation_errors(dataset), [])
        self.assertEqual(len(dataset.records), 4)


class CliTests(unittest.TestCase):
    def run_cli(self, *args, input_data=None):
        return subprocess.run(
            [sys.executable, "-m", "market_catalyst_calendar", *args],
            input=input_data,
            text=True,
            capture_output=True,
            check=False,
        )

    def git(self, repo, *args, env=None):
        merged_env = os.environ.copy()
        merged_env.update(
            {
                "GIT_AUTHOR_NAME": "Test Author",
                "GIT_AUTHOR_EMAIL": "test@example.com",
                "GIT_COMMITTER_NAME": "Test Author",
                "GIT_COMMITTER_EMAIL": "test@example.com",
                "GIT_AUTHOR_DATE": "2026-05-13T12:00:00+00:00",
                "GIT_COMMITTER_DATE": "2026-05-13T12:00:00+00:00",
            }
        )
        if env:
            merged_env.update(env)
        return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True, env=merged_env)

    def write_file(self, repo, name, text):
        path = Path(repo) / name
        path.write_text(text, encoding="utf-8")
        return path

    def make_changelog_repo(self):
        tmp = tempfile.TemporaryDirectory()
        repo = Path(tmp.name)
        self.git(repo, "init")
        self.write_file(repo, "notes.txt", "base\n")
        self.git(repo, "add", "notes.txt")
        self.git(repo, "commit", "-m", "chore: initial release")
        self.git(repo, "tag", "v0.1.0")
        self.write_file(repo, "notes.txt", "base\nfeature\n")
        self.git(repo, "add", "notes.txt")
        self.git(repo, "commit", "-m", "feat(cli): add catalyst digest #12")
        self.write_file(repo, "notes.txt", "base\nfeature\nfix\n")
        self.git(repo, "add", "notes.txt")
        self.git(repo, "commit", "-m", "fix!: tighten evidence parsing", "-m", "BREAKING CHANGE: invalid URLs now fail validation.")
        return tmp, repo

    def test_validate_stdin(self):
        result = self.run_cli("validate", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True, "record_count": 4})

    def test_changelog_json_groups_commits_since_tag(self):
        tmp, repo = self.make_changelog_repo()
        with tmp:
            result = self.run_cli("changelog", "--repo", str(repo), "--since-tag", "v0.1.0", "--format", "json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "changelog/v1")
        self.assertEqual(payload["since_tag"], "v0.1.0")
        self.assertEqual(payload["commit_count"], 2)
        self.assertEqual(payload["breaking_change_count"], 1)
        self.assertEqual([commit["category"] for commit in payload["commits"]], ["feat", "fix"])
        self.assertEqual(payload["commits"][0]["scope"], "cli")
        self.assertEqual(payload["commits"][0]["references"], ["#12"])
        self.assertEqual(payload["categories"][0]["title"], "Features")
        self.assertEqual(payload["categories"][0]["commits"][0]["description"], "add catalyst digest #12")

    def test_changelog_markdown_is_deterministic_release_notes(self):
        tmp, repo = self.make_changelog_repo()
        with tmp:
            result = self.run_cli("changelog", "--repo", str(repo), "--since-tag", "v0.1.0")
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Release Notes\n", result.stdout)
        self.assertIn("Range: `v0.1.0..HEAD`", result.stdout)
        self.assertIn("## Breaking Changes", result.stdout)
        self.assertIn("add catalyst digest #12 (cli) #12", result.stdout)
        self.assertIn("tighten evidence parsing BREAKING", result.stdout)

    def test_validate_public_profile_includes_quality_diagnostic_codes(self):
        result = self.run_cli("validate", "--profile", "public", "--as-of", "2026-05-13", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["profile"], "public")
        self.assertEqual(payload["quality_gate"]["summary"]["failed_record_count"], 4)
        codes = {item["code"] for item in payload["diagnostics"]}
        self.assertIn("MCC-QG-EVIDENCE-001", codes)
        self.assertIn("MCC-QG-SOURCE-001", codes)

    def test_validate_strict_profile_adds_release_metadata_diagnostics(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["source_ref"] = None
        result = self.run_cli("validate", "--profile", "strict", "--as-of", "2026-05-13", input_data=json.dumps(raw))
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["profile"], "strict")
        diagnostics = [item for item in payload["diagnostics"] if item["source"] == "quality-gate"]
        self.assertIn("MCC-QG-RELEASE-004", {item["code"] for item in diagnostics})
        self.assertIn("MCC-QG-BROKER-001", {item["code"] for item in diagnostics})

    def test_taxonomy_json_reports_domain_rules_diagnostics_and_commands(self):
        result = self.run_cli("taxonomy")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "taxonomy/v1")
        self.assertIn("regulatory_decision", payload["event_types"])
        self.assertIn("scheduled", payload["statuses"])
        self.assertIn("verify_source", payload["review_actions"])
        self.assertIn("minimum_evidence", {rule["id"] for rule in payload["quality_rules"]})
        self.assertIn("MCC-QG-EVIDENCE-001", {item["code"] for item in payload["diagnostic_codes"]})
        self.assertIn("MCC-VAL-SCENARIO-001", {item["code"] for item in payload["diagnostic_codes"]})
        self.assertIn("taxonomy", {command["id"] for command in payload["commands"]})
        self.assertIn("demo-bundle", payload["output_commands"])

    def test_taxonomy_markdown_renders_catalog_sections(self):
        result = self.run_cli("taxonomy", "--format", "markdown")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Taxonomy", result.stdout)
        self.assertIn("## Diagnostic Codes", result.stdout)
        self.assertIn("| taxonomy | json, markdown |", result.stdout)

    def test_version_report_json_includes_release_and_git_snapshot(self):
        result = self.run_cli("version-report", "--root", str(ROOT), "--repo", str(ROOT))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "version-report/v1")
        self.assertEqual(payload["package"]["version"], "0.1.0")
        self.assertEqual(payload["command_count"], payload["summary"]["command_count"])
        self.assertGreaterEqual(payload["command_count"], len(REQUIRED_COMMANDS))
        self.assertEqual(payload["fixture_count"], payload["summary"]["fixture_count"])
        self.assertEqual(payload["release_audit"]["status"], "pass")
        self.assertEqual(payload["summary"]["release_audit_status"], "pass")
        self.assertIn("available", payload["git"])
        if payload["git"]["available"]:
            self.assertIn("short_hash", payload["git"]["commit"])

    def test_version_report_markdown_renders_summary(self):
        result = self.run_cli("version-report", "--root", str(ROOT), "--repo", str(ROOT), "--format", "markdown")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Version Report", result.stdout)
        self.assertIn("Version: `0.1.0`", result.stdout)
        self.assertIn("Release audit: PASS", result.stdout)

    def test_upcoming_json_is_deterministic(self):
        result = self.run_cli("upcoming", "--as-of", "2026-05-13", "--days", "10", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([record["id"] for record in payload["records"]], ["demo-pfe-fda-2026"])
        self.assertEqual(payload["records"][0]["portfolio_weight"], 0.031)

    def test_exposure_json_groups_upcoming_weighted_exposure(self):
        result = self.run_cli("exposure", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["group_count"], 3)
        self.assertEqual(payload["summary"]["record_count"], 3)
        self.assertEqual(payload["summary"]["portfolio_weight"], 0.3335)
        self.assertEqual(payload["summary"]["weighted_exposure"], 0.233962)
        self.assertEqual(payload["summary"]["weighted_position_exposure"], 106096.8)
        self.assertEqual(payload["groups"][0]["ticker"], "SPY")
        self.assertEqual(payload["groups"][0]["event_type"], "macro_release")
        self.assertEqual(payload["groups"][0]["urgency"], "medium")

    def test_exposure_markdown_renders_table(self):
        result = self.run_cli("exposure", "--as-of", "2026-05-13", "--days", "10", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Exposure", result.stdout)
        self.assertIn("| PFE | regulatory decision | high | 1 | 3.10% | 1.83% | 48,000.00 | 28,396.80 |", result.stdout)

    def test_risk_budget_json_flags_over_budget_catalysts(self):
        result = self.run_cli("risk-budget", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["summary"],
            {
                "expected_event_loss": 118484.4,
                "group_count": 3,
                "max_loss": 174000.0,
                "missing_budget_count": 0,
                "missing_max_loss_count": 0,
                "over_budget_group_count": 2,
                "over_budget_record_count": 2,
                "record_count": 3,
                "risk_budget": 160000.0,
            },
        )
        self.assertEqual([group["ticker"] for group in payload["groups"]], ["SPY", "PFE", "NVDA"])
        self.assertEqual(payload["groups"][0]["thesis_id"], "rates-duration-risk")
        self.assertEqual(payload["groups"][0]["urgency"], "medium")
        self.assertEqual(payload["groups"][0]["flags"], ["over_budget"])
        self.assertEqual(payload["groups"][1]["records"][0]["id"], "demo-pfe-fda-2026")
        self.assertEqual(payload["groups"][1]["records"][0]["budget_remaining"], -7000.0)
        self.assertEqual(payload["groups"][2]["flags"], [])

    def test_risk_budget_markdown_renders_summary_and_flags(self):
        result = self.run_cli(
            "risk-budget",
            "--as-of",
            "2026-05-13",
            "--days",
            "45",
            "--format",
            "markdown",
            input_data=json.dumps(DEMO_DATA),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Risk Budget", result.stdout)
        self.assertIn("Over-budget catalysts: 2", result.stdout)
        self.assertIn("| PFE | pharma-pipeline-reset | high | 1 | 25,000.00 | 32,000.00 | 18,931.20 | 1.28x | over_budget |", result.stdout)
        self.assertIn("- demo-fomc-june-2026: max loss 90,000.00 vs budget 75,000.00; flags: over_budget", result.stdout)

    def test_sector_map_json_groups_sector_theme_exposure_and_dispersion(self):
        result = self.run_cli("sector-map", "--as-of", "2026-05-13", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["group_count"], 4)
        self.assertEqual(payload["summary"]["record_count"], 4)
        self.assertEqual(payload["summary"]["open_event_count"], 3)
        self.assertEqual(payload["summary"]["stale_evidence_count"], 2)
        self.assertEqual(payload["summary"]["broker_view_count"], 4)
        self.assertEqual(payload["summary"]["portfolio_weight"], 0.3335)
        first = next(group for group in payload["groups"] if group["sector"] == "Health Care")
        self.assertEqual(first["sector"], "Health Care")
        self.assertEqual(first["theme"], "Pipeline reset")
        self.assertEqual(first["highest_score"], 87)
        self.assertEqual(first["urgency_count"], {"high": 1})
        self.assertEqual(first["stale_evidence_count"], 1)
        self.assertEqual(first["broker_dispersion_max"], 8.0)
        self.assertEqual(first["records"][0]["flags"], ["stale_evidence", "urgent", "stale_review", "broker_dispersion"])

    def test_sector_map_markdown_renders_groups_and_flags(self):
        result = self.run_cli("sector-map", "--as-of", "2026-05-13", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Sector Map", result.stdout)
        self.assertIn("| Health Care | Pipeline reset | 1 | 87 | high:1 | 3.10% | 1.83% | 1 | 8.00 | PFE |", result.stdout)
        self.assertIn("- PFE demo-pfe-fda-2026: urgency high; review stale; evidence stale; broker dispersion 8.00;", result.stdout)

    def test_review_plan_json_includes_actions_gaps_and_prompts(self):
        result = self.run_cli("review-plan", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["as_of"], "2026-05-13")
        self.assertEqual(payload["days"], 45)
        self.assertEqual(payload["stale_after_days"], 14)
        self.assertEqual([record["id"] for record in payload["records"]], ["demo-pfe-fda-2026"])
        record = payload["records"][0]
        self.assertEqual(record["selection_reasons"], ["stale", "high_urgency_upcoming"])
        self.assertEqual(record["stale_days"], 15)
        self.assertIn("Verify the primary source", record["next_action"])
        self.assertIn("confirm whether any source changed", record["evidence_gap"])
        self.assertIn("Current base case", record["scenario_update_prompt"])

    def test_review_plan_includes_stale_non_high_urgency_record(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["last_reviewed"] = "2026-04-20"
        result = self.run_cli("review-plan", "--as-of", "2026-05-13", "--days", "10", input_data=json.dumps(raw))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual([record["id"] for record in payload["records"]], ["demo-pfe-fda-2026", "demo-nvda-computex-2026"])
        self.assertEqual(payload["records"][1]["selection_reasons"], ["stale"])

    def test_review_plan_markdown_renders_checklist(self):
        result = self.run_cli(
            "review-plan",
            "--as-of",
            "2026-05-13",
            "--days",
            "45",
            "--format",
            "markdown",
            input_data=json.dumps(DEMO_DATA),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Review Plan", result.stdout)
        self.assertIn("- [ ] **PFE - Pfizer Inc.** (demo-pfe-fda-2026)", result.stdout)
        self.assertIn("Evidence gap: verify the source", result.stdout)

    def test_thesis_map_json_groups_scores_stale_and_evidence_refs(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][2]["thesis_id"] = raw["records"][0]["thesis_id"]
        result = self.run_cli("thesis-map", "--as-of", "2026-05-13", input_data=json.dumps(raw))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"], {"open_event_count": 3, "record_count": 3, "stale_count": 1, "thesis_count": 2})
        first = payload["groups"][0]
        self.assertEqual(first["thesis_id"], "ai-infrastructure-capex")
        self.assertEqual(first["open_event_count"], 2)
        self.assertEqual(first["stale_count"], 1)
        self.assertEqual(first["highest_score"], 87)
        self.assertEqual(first["records"], ["demo-nvda-computex-2026", "demo-pfe-fda-2026"])
        self.assertIn("NVDA Computex keynote tracker", first["evidence_references"])
        self.assertIn("https://example.com/fda-calendar", first["evidence_references"])

    def test_thesis_map_markdown_renders_table(self):
        result = self.run_cli("thesis-map", "--as-of", "2026-05-13", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Thesis Map", result.stdout)
        self.assertIn("| pharma-pipeline-reset | 1 | 87 | 1 | demo-pfe-fda-2026 |", result.stdout)

    def test_scenario_matrix_json_renders_bull_base_bear(self):
        result = self.run_cli("scenario-matrix", "--as-of", "2026-05-13", "--days", "10", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"], {"highest_scenario_score": 91, "record_count": 1, "review_action_count": 3, "scenario_count": 3})
        record = payload["records"][0]
        self.assertEqual(record["id"], "demo-pfe-fda-2026")
        self.assertEqual(record["base_catalyst_score"], 87)
        self.assertEqual([scenario["scenario"] for scenario in record["scenarios"]], ["bull", "base", "bear"])
        self.assertEqual([scenario["score"] for scenario in record["scenarios"]], [91, 87, 79])
        self.assertEqual([scenario["date"] for scenario in record["scenarios"]], ["2026-05-20", "2026-05-20..2026-05-24", "2026-05-24"])
        self.assertEqual([scenario["impact"] for scenario in record["scenarios"]], ["positive", "mixed", "negative"])
        self.assertEqual(record["scenarios"][0]["review_action"], "verify_source:bull:stale")

    def test_scenario_matrix_markdown_renders_table(self):
        result = self.run_cli(
            "scenario-matrix",
            "--as-of",
            "2026-05-13",
            "--days",
            "10",
            "--format",
            "markdown",
            input_data=json.dumps(DEMO_DATA),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Scenario Matrix", result.stdout)
        self.assertIn("| PFE | 2026-05-20 | bull | 91 | positive | verify_source:bull:stale |", result.stdout)

    def test_evidence_audit_json_flags_freshness_thin_sources_and_concentration(self):
        result = self.run_cli("evidence-audit", "--as-of", "2026-05-13", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["record_count"], 4)
        self.assertEqual(payload["summary"]["flagged_record_count"], 3)
        self.assertEqual(
            payload["summary"]["flag_counts"],
            {
                "missing_evidence_checked_at": 1,
                "source_concentration": 2,
                "stale_evidence_metadata": 1,
                "thin_source_count": 1,
            },
        )
        by_id = {record["id"]: record for record in payload["records"]}
        self.assertEqual(by_id["demo-pfe-fda-2026"]["evidence_age_days"], 15)
        self.assertEqual(by_id["demo-pfe-fda-2026"]["flags"], ["stale_evidence_metadata", "source_concentration"])
        self.assertEqual(by_id["demo-fomc-june-2026"]["flags"], ["missing_evidence_checked_at", "thin_source_count"])
        self.assertEqual(by_id["demo-nvda-computex-2026"]["dominant_source_domain"], "example.com")

    def test_evidence_audit_markdown_renders_detail(self):
        result = self.run_cli(
            "evidence-audit",
            "--as-of",
            "2026-05-13",
            "--format",
            "markdown",
            input_data=json.dumps(DEMO_DATA),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Evidence Audit", result.stdout)
        self.assertIn("| high | PFE | demo-pfe-fda-2026 | 2026-04-28 | 2 | example.com (1.00) |", result.stdout)
        self.assertIn("record the date evidence was last checked", result.stdout)

    def test_quality_gate_json_fails_public_dataset_rules(self):
        result = self.run_cli("quality-gate", "--as-of", "2026-05-13", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["summary"]["record_count"], 4)
        self.assertEqual(payload["summary"]["failed_record_count"], 4)
        self.assertEqual(payload["summary"]["rule_counts"]["no_placeholder_urls"], 10)
        self.assertEqual(payload["summary"]["rule_counts"]["minimum_evidence"], 3)
        self.assertEqual(payload["summary"]["rule_counts"]["broker_caveats"], 2)
        self.assertEqual(payload["policy"]["profile"], "public")
        by_id = {record["id"]: record for record in payload["records"]}
        self.assertEqual(
            by_id["demo-fomc-june-2026"]["failed_rules"],
            ["minimum_evidence", "no_placeholder_urls"],
        )
        self.assertEqual(by_id["demo-fomc-june-2026"]["issues"][0]["code"], "MCC-QG-EVIDENCE-001")
        self.assertIn("replace placeholder URLs", by_id["demo-pfe-fda-2026"]["next_action"])

    def test_quality_gate_markdown_renders_failures(self):
        result = self.run_cli(
            "quality-gate",
            "--as-of",
            "2026-05-13",
            "--format",
            "markdown",
            input_data=json.dumps(DEMO_DATA),
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("# Market Catalyst Quality Gate", result.stdout)
        self.assertIn("Status: FAIL", result.stdout)
        self.assertIn("| critical | MCC-QG-SOURCE-001 | no_placeholder_urls | PFE | demo-pfe-fda-2026 | evidence URL https://example.com/fda-calendar is a placeholder host |", result.stdout)
        self.assertIn("- Failed rules: broker_caveats, minimum_evidence, no_placeholder_urls, review_freshness", result.stdout)

    def test_quality_gate_strict_profile_applies_tighter_defaults(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        for record in raw["records"]:
            record["evidence_urls"] = [
                f"https://sources.exampledata.com/{record['id']}/primary",
                f"https://filings.exampledata.com/{record['id']}/filing",
            ]
            record["evidence_checked_at"] = "2026-05-10"
            record["last_reviewed"] = "2026-05-10"
            record["source_ref"] = record.get("source_ref") or f"{record['id']}-source"
        result = self.run_cli("quality-gate", "--profile", "strict", "--as-of", "2026-05-13", input_data=json.dumps(raw))
        self.assertEqual(result.returncode, 1, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["policy"]["profile"], "strict")
        self.assertEqual(payload["policy"]["min_evidence_urls"], 3)
        codes = {issue["code"] for record in payload["records"] for issue in record["issues"]}
        self.assertIn("MCC-QG-EVIDENCE-001", codes)
        self.assertIn("MCC-QG-BROKER-001", codes)

    def test_quality_gate_passes_when_public_rules_are_met(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        replacements = {
            "https://example.com/nvidia-computex-keynote": "https://investor.nvidia.com/events/computex-2026-keynote",
            "https://example.com/channel-check-gpu-supply": "https://www.nvidia.com/en-us/data-center/supply-update",
            "https://example.com/nvda-broker-north-coast": "https://research.northcoastmarkets.com/reports/nvda-2026-05-10",
            "https://example.com/nvda-broker-metro": "https://research.metrocapitalmarkets.com/reports/nvda-2026-05-10",
            "https://example.com/msft-q3-earnings": "https://www.microsoft.com/en-us/investor/earnings/fy-2026-q3",
            "https://ir.example.org/msft-q3-transcript": "https://www.sec.gov/Archives/edgar/data/msft-q3-transcript",
            "https://example.com/fda-calendar": "https://www.fda.gov/advisory-committees/pfe-review-calendar",
            "https://example.com/pfe-pipeline-update": "https://www.pfizer.com/news/press-release/pipeline-update",
            "https://example.com/pfe-broker-harbor": "https://research.harborlifesciences.com/reports/pfe-2026-05-01",
            "https://example.com/pfe-broker-summit": "https://research.summitsecurities.com/reports/pfe-2026-05-01",
            "https://example.com/fomc-calendar": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
        }
        for record in raw["records"]:
            record["evidence_urls"] = [replacements[url] for url in record["evidence_urls"]]
            if record["id"] == "demo-fomc-june-2026":
                record["evidence_urls"].append("https://www.federalreserve.gov/newsevents/pressreleases/monetary20260513a.htm")
                record["evidence_checked_at"] = "2026-05-13"
            if record["id"] == "demo-pfe-fda-2026":
                record["last_reviewed"] = "2026-05-01"
                record["evidence_checked_at"] = "2026-05-01"
            for view in record.get("broker_views", []):
                view["source_url"] = replacements[view["source_url"]]
                if view["as_of"] < "2026-04-14":
                    view["as_of"] = "2026-05-01"

        result = self.run_cli("quality-gate", "--as-of", "2026-05-13", input_data=json.dumps(raw))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["records"], [])
        self.assertEqual(payload["summary"]["failed_record_count"], 0)

    def test_doctor_json_suggests_read_only_repairs_for_public_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo.json"
            original = json.dumps(DEMO_DATA)
            path.write_text(original, encoding="utf-8")

            result = self.run_cli("doctor", "--input", str(path), "--as-of", "2026-05-13")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_text(encoding="utf-8"), original)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "doctor/v1")
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["modifies_input"])
        self.assertGreater(payload["summary"]["repair_count"], 0)
        self.assertIn("patch", payload)
        repairs = {(repair["record_id"], tuple(repair["diagnostic_codes"]), repair["path"]) for repair in payload["repairs"]}
        self.assertIn(("demo-fomc-june-2026", ("MCC-QG-EVIDENCE-001",), "/records/3/evidence_urls/-"), repairs)
        self.assertTrue(any(repair["path"] == "/records/2/last_reviewed" for repair in payload["repairs"]))
        self.assertTrue(any(repair["path"] == "/records/0/evidence_urls/0" for repair in payload["repairs"]))

    def test_doctor_patch_format_emits_json_patch_style_operations(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["scenario_notes"].pop("bear")

        result = self.run_cli("doctor", "--format", "patch", "--as-of", "2026-05-13", input_data=json.dumps(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        patch = json.loads(result.stdout)
        self.assertIsInstance(patch, list)
        self.assertIn({"op": "add", "path": "/records/0/scenario_notes/bear", "value": "NVDA downside case: verified evidence shows delay, weaker demand, or a more restrictive outcome."}, patch)

    def test_doctor_markdown_renders_repair_checklist(self):
        result = self.run_cli("doctor", "--format", "markdown", "--as-of", "2026-05-13", input_data=json.dumps(DEMO_DATA))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Dataset Doctor", result.stdout)
        self.assertIn("Read-only: yes", result.stdout)
        self.assertIn("MCC-QG-SOURCE-001", result.stdout)

    def test_broker_matrix_json_groups_dispersion_staleness_and_catalysts(self):
        result = self.run_cli("broker-matrix", "--as-of", "2026-05-13", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"], {"group_count": 2, "linked_catalyst_count": 2, "stale_view_count": 2, "view_count": 4})
        first = payload["groups"][0]
        self.assertEqual(first["ticker"], "NVDA")
        self.assertEqual(first["thesis_id"], "ai-infrastructure-capex")
        self.assertEqual(first["target_price_min"], 1085.0)
        self.assertEqual(first["target_price_max"], 1320.0)
        self.assertEqual(first["target_price_avg"], 1202.5)
        self.assertEqual(first["target_price_dispersion"], 235.0)
        self.assertEqual(first["stale_sources"][0]["institution"], "Metro Capital Markets")
        self.assertEqual(first["linked_catalysts"][0]["id"], "demo-nvda-computex-2026")
        self.assertEqual(first["rating_count"], {"buy": 1, "hold": 1})

    def test_broker_matrix_markdown_renders_summary_and_details(self):
        result = self.run_cli("broker-matrix", "--as-of", "2026-05-13", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Broker Matrix", result.stdout)
        self.assertIn("| NVDA | ai-infrastructure-capex | 2 | 1202.50 | 1085.00-1320.00 | 235.00 | Metro Capital Markets | demo-nvda-computex-2026 |", result.stdout)
        self.assertIn("| Metro Capital Markets | hold | 1085.00 | 2026-04-05 | 38 | Older view predates", result.stdout)

    def test_source_pack_json_deduplicates_evidence_and_broker_urls(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["evidence_urls"].append("https://example.com/pfe-broker-harbor")
        result = self.run_cli("source-pack", "--as-of", "2026-05-13", input_data=json.dumps(raw))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["source_count"], 11)
        self.assertEqual(payload["summary"]["usage_count"], 12)
        self.assertEqual(payload["summary"]["broker_source_count"], 4)
        self.assertEqual(payload["summary"]["evidence_source_count"], 8)
        by_url = {source["url"]: source for source in payload["sources"]}
        combined = by_url["https://example.com/pfe-broker-harbor"]
        self.assertEqual(combined["source_types"], ["broker", "evidence"])
        self.assertEqual(combined["usage_count"], 2)
        self.assertEqual(combined["tickers"], ["NVDA", "PFE"])
        self.assertEqual(combined["thesis_ids"], ["ai-infrastructure-capex", "pharma-pipeline-reset"])
        self.assertEqual(combined["evidence_checked_at"], "2026-05-09")
        self.assertEqual(combined["freshness_state"], "fresh")

    def test_source_pack_csv_and_markdown_render_source_inventory(self):
        csv_result = self.run_cli("source-pack", "--as-of", "2026-05-13", "--format", "csv", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(csv_result.returncode, 0, csv_result.stderr)
        self.assertTrue(csv_result.stdout.startswith("url,source_types,usage_count,tickers,thesis_ids,record_ids,evidence_checked_at"))
        self.assertIn("https://example.com/fomc-calendar,evidence,1,SPY,rates-duration-risk,demo-fomc-june-2026,missing,missing,missing", csv_result.stdout)
        md_result = self.run_cli("source-pack", "--as-of", "2026-05-13", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(md_result.returncode, 0, md_result.stderr)
        self.assertIn("# Market Catalyst Source Pack", md_result.stdout)
        self.assertIn("| stale | 1 | broker | NVDA | ai-infrastructure-capex | 2026-04-05 | https://example.com/nvda-broker-metro |", md_result.stdout)

    def test_watchlist_json_prioritizes_due_items_with_triggers_and_refs(self):
        result = self.run_cli("watchlist", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"], {"critical_count": 1, "due_now_count": 1, "high_count": 2, "item_count": 3, "low_count": 0, "medium_count": 0})
        self.assertEqual([item["catalyst_id"] for item in payload["items"]], ["demo-pfe-fda-2026", "demo-fomc-june-2026", "demo-nvda-computex-2026"])
        first = payload["items"][0]
        self.assertEqual(first["watch_id"], "watch-demo-pfe-fda-2026")
        self.assertEqual(first["priority"], "critical")
        self.assertEqual(first["priority_score"], 100)
        self.assertEqual(first["due_date"], "2026-05-13")
        self.assertEqual(first["review_cadence"], "daily_until_resolved")
        self.assertEqual(first["thesis_id"], "pharma-pipeline-reset")
        self.assertIn("FDA calendar and PFE pipeline note", first["source_refs"])
        self.assertIn("https://example.com/fda-calendar", first["evidence_urls"])
        self.assertEqual(
            [trigger["type"] for trigger in first["trigger_conditions"]],
            ["review_due", "event_window", "stale_review", "source_check", "thesis_link", "exposure_change"],
        )

    def test_watchlist_markdown_renders_table_and_trigger_details(self):
        result = self.run_cli("watchlist", "--as-of", "2026-05-13", "--days", "45", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Watchlist", result.stdout)
        self.assertIn("| critical (100) | 2026-05-13 | daily_until_resolved | PFE | regulatory_decision 2026-05-20..2026-05-24 |", result.stdout)
        self.assertIn("| high (78) | 2026-05-26 | twice_weekly | NVDA | product_launch 2026-06-02 |", result.stdout)
        self.assertIn("- Watch item: watch-demo-pfe-fda-2026", result.stdout)
        self.assertIn("Bull/base/bear evidence changes the linked thesis 'pharma-pipeline-reset'. -> update_thesis_reference", result.stdout)

    def test_decision_log_json_builds_memo_stubs_with_context(self):
        result = self.run_cli("decision-log", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"], {"broker_context_count": 2, "memo_count": 3, "stale_memo_count": 1, "trigger_count": 14})
        self.assertEqual([memo["memo_id"] for memo in payload["memos"]], ["decision-demo-pfe-fda-2026", "decision-demo-fomc-june-2026", "decision-demo-nvda-computex-2026"])
        first = payload["memos"][0]
        self.assertEqual(first["decision_status"], "draft")
        self.assertEqual(first["thesis"]["thesis_id"], "pharma-pipeline-reset")
        self.assertEqual(first["catalyst"]["review_state"], "stale")
        self.assertEqual([scenario["scenario"] for scenario in first["scenarios"]], ["bull", "base", "bear"])
        self.assertEqual(first["broker_context"]["target_price_range"], "31.00-39.00")
        self.assertEqual(first["watchlist_triggers"][0]["type"], "review_due")
        self.assertEqual(first["decision_slots"]["pre_event_decision"], "TBD")
        self.assertEqual(first["post_event_review"]["review_due"], "2026-05-24")

    def test_decision_log_markdown_renders_memo_sections(self):
        result = self.run_cli("decision-log", "--as-of", "2026-05-13", "--days", "10", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Decision Log", result.stdout)
        self.assertIn("## PFE - Pfizer Inc.", result.stdout)
        self.assertIn("### Broker Context", result.stdout)
        self.assertIn("- Pre-event decision: TBD", result.stdout)
        self.assertIn("- Review due: 2026-05-24", result.stdout)
        self.assertNotIn("## NVDA - NVIDIA Corporation", result.stdout)

    def test_drilldown_json_combines_single_ticker_dossier_sections(self):
        result = self.run_cli("drilldown", "--ticker", "nvda", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["ticker"], "NVDA")
        self.assertEqual(
            payload["summary"],
            {
                "broker_view_count": 2,
                "decision_memo_count": 1,
                "latest_window_end": "2026-06-02",
                "post_event_queue_count": 0,
                "record_count": 1,
                "source_count": 4,
                "upcoming_event_count": 1,
                "watch_item_count": 1,
            },
        )
        self.assertEqual(payload["records"][0]["id"], "demo-nvda-computex-2026")
        self.assertEqual(payload["dossier"]["thesis_map"]["summary"]["thesis_count"], 1)
        self.assertEqual(payload["dossier"]["broker_matrix"]["summary"]["stale_view_count"], 1)
        self.assertEqual(payload["dossier"]["risk_budget"]["summary"]["risk_budget"], 60000.0)
        self.assertEqual(payload["dossier"]["watchlist"]["items"][0]["priority"], "high")
        self.assertEqual(payload["dossier"]["decision_logs"]["memos"][0]["memo_id"], "decision-demo-nvda-computex-2026")
        self.assertEqual(payload["dossier"]["source_pack"]["summary"]["source_count"], 4)

    def test_drilldown_markdown_renders_complete_single_ticker_packet(self):
        result = self.run_cli("drilldown", "--ticker", "PFE", "--as-of", "2026-05-13", "--days", "45", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# PFE Catalyst Drilldown", result.stdout)
        self.assertIn("## Record Ledger", result.stdout)
        self.assertIn("## Upcoming Events", result.stdout)
        self.assertIn("## Thesis Map", result.stdout)
        self.assertIn("## Broker Matrix", result.stdout)
        self.assertIn("## Risk Budget", result.stdout)
        self.assertIn("## Watchlist", result.stdout)
        self.assertIn("## Post-Event Queue", result.stdout)
        self.assertIn("## Source Pack", result.stdout)
        self.assertIn("## Decision Logs", result.stdout)
        self.assertIn("### PFE - Pfizer Inc.", result.stdout)
        self.assertNotIn("NVIDIA Corporation", result.stdout)

    def test_command_cookbook_selects_field_driven_playbook_sections(self):
        result = self.run_cli("command-cookbook", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Command Cookbook", result.stdout)
        self.assertIn("Dataset path in commands: `dataset.json`", result.stdout)
        self.assertIn("| Portfolio Exposure Pass | selected | At least one record has `portfolio_weight` or `position_size`", result.stdout)
        self.assertIn("| Risk Budget Pass | selected | At least one record has `risk_budget` or `max_loss`", result.stdout)
        self.assertIn("| Sector And Theme Map | selected | At least one record has `sector` or `theme`", result.stdout)
        self.assertIn("| Broker View Matrix | selected | At least one record has `broker_views`", result.stdout)
        self.assertIn("python -m market_catalyst_calendar quality-gate --profile public --input dataset.json --as-of 2026-05-13 > reports/quality_gate.json || test $? -eq 1", result.stdout)
        self.assertIn("python -m market_catalyst_calendar risk-budget --input dataset.json --as-of 2026-05-13 --days 45 --format markdown > reports/risk_budget.md", result.stdout)
        self.assertIn("- `reports/archive/manifest.json`", result.stdout)

    def test_command_cookbook_skips_absent_optional_field_workflows(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        for record in raw["records"]:
            for key in ["position_size", "portfolio_weight", "risk_budget", "max_loss", "sector", "theme", "thesis_id", "source_ref", "broker_views"]:
                record.pop(key, None)
        result = self.run_cli("command-cookbook", "--as-of", "2026-05-13", "--dataset-path", "research/catalysts.json", "--output-dir", "out", input_data=json.dumps(raw))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dataset path in commands: `research/catalysts.json`", result.stdout)
        self.assertIn("| Portfolio Exposure Pass | skipped | No `portfolio_weight` or `position_size` fields are populated. |", result.stdout)
        self.assertIn("| Risk Budget Pass | skipped | No `risk_budget` or `max_loss` fields are populated. |", result.stdout)
        self.assertIn("| Broker View Matrix | skipped | No `broker_views` are populated. |", result.stdout)
        self.assertNotIn("risk-budget --input research/catalysts.json", result.stdout)
        self.assertIn("python -m market_catalyst_calendar upcoming --input research/catalysts.json --as-of 2026-05-13 --days 45 > out/upcoming.json", result.stdout)

    def test_tutorial_markdown_renders_demo_workflow_with_checkpoints(self):
        result = self.run_cli("tutorial", "--as-of", "2026-05-13", "--days", "45", "--dataset-path", "examples/demo_records.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Calendar Tutorial", result.stdout)
        self.assertIn("notebooks-free walkthrough", result.stdout)
        self.assertIn("python -m market_catalyst_calendar export-demo > examples/demo_records.json", result.stdout)
        self.assertIn("Expected exit code: `1`", result.stdout)
        self.assertIn('"issue_codes": [', result.stdout)
        self.assertIn("MCC-QG-SOURCE-001", result.stdout)
        self.assertIn("Learning checkpoint: Two upcoming catalysts are over budget", result.stdout)
        self.assertIn("- [ ] Single-ticker drilldown and snapshot compare", result.stdout)

    def test_tutorial_can_write_markdown_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "tutorial.md"
            result = self.run_cli("tutorial", "--output", str(output))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            text = output.read_text(encoding="utf-8")
        self.assertIn("# Market Catalyst Calendar Tutorial", text)
        self.assertIn("Expected output excerpt:", text)

    def test_agent_handoff_json_creates_machine_readable_research_context(self):
        result = self.run_cli("agent-handoff", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "agent-handoff/v1")
        self.assertEqual(payload["dataset_summary"]["record_count"], 4)
        self.assertEqual(payload["dataset_summary"]["upcoming_record_count"], 3)
        self.assertEqual(payload["dataset_summary"]["stale_review_count"], 1)
        self.assertEqual([item["ticker"] for item in payload["top_risks"]], ["PFE", "SPY", "NVDA"])
        self.assertIn("over_budget", payload["top_risks"][0]["risk_flags"])
        self.assertEqual([item["ticker"] for item in payload["stale_items"]], ["PFE", "SPY"])
        self.assertEqual(payload["source_urls"][0]["freshness_state"], "missing")
        self.assertIn("source-pack", [command["id"] for command in payload["commands_to_run_next"]])
        self.assertIn("drilldown-PFE", [command["id"] for command in payload["commands_to_run_next"]])

    def test_agent_handoff_markdown_renders_command_packet(self):
        result = self.run_cli(
            "agent-handoff",
            "--as-of",
            "2026-05-13",
            "--dataset-path",
            "research/catalysts.json",
            "--output-dir",
            "handoff",
            "--format",
            "markdown",
            input_data=json.dumps(DEMO_DATA),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Agent Handoff Pack", result.stdout)
        self.assertIn("Dataset path in commands: `research/catalysts.json`", result.stdout)
        self.assertIn("| 1 | PFE | 87 | 2026-05-20..2026-05-24 | stale_review, stale_evidence, over_budget", result.stdout)
        self.assertIn("python -m market_catalyst_calendar source-pack --input research/catalysts.json --as-of 2026-05-13 --fresh-after-days 14 > handoff/source_pack.json", result.stdout)

    def test_run_preset_executes_named_workflows_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset_path = root / "demo.json"
            output_dir = root / "packet"
            presets_path = root / "presets.json"
            dataset_path.write_text(json.dumps(DEMO_DATA), encoding="utf-8")
            presets_path.write_text(
                json.dumps(
                    {
                        "defaults": {
                            "days": 10,
                            "output_dir": str(output_dir),
                            "profile": "public",
                            "stale_after_days": 14,
                        },
                        "presets": {
                            "desk-packet": {
                                "as_of": "2026-05-13",
                                "input": str(dataset_path),
                                "workflows": ["validate", "quality-gate", "upcoming", "review-plan", "agent-handoff"],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            first = self.run_cli("run-preset", "--presets", str(presets_path), "--name", "desk-packet")
            second = self.run_cli("run-preset", "--presets", str(presets_path), "--name", "desk-packet")

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stdout, second.stdout)
            payload = json.loads(first.stdout)
            self.assertEqual(payload["schema_version"], "preset-run/v1")
            self.assertEqual(payload["parameters"]["days"], 10)
            self.assertEqual(payload["parameters"]["profile"], "public")
            self.assertEqual(payload["summary"]["workflow_count"], 5)
            self.assertEqual(payload["summary"]["report_failure_count"], 1)
            self.assertEqual([artifact["workflow"] for artifact in payload["artifacts"]], ["validate", "quality-gate", "upcoming", "review-plan", "agent-handoff"])
            self.assertEqual(next(artifact for artifact in payload["artifacts"] if artifact["workflow"] == "quality-gate")["exit_code"], 1)
            self.assertTrue((output_dir / "manifest.json").is_file())
            self.assertTrue((output_dir / "quality_gate.json").is_file())
            upcoming = json.loads((output_dir / "upcoming.json").read_text(encoding="utf-8"))
            self.assertEqual([record["id"] for record in upcoming["records"]], ["demo-pfe-fda-2026"])

    def test_post_event_json_lists_overdue_items_with_templates(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["actual_outcome"] = "Management confirmed faster platform cadence."
        raw["records"][0]["outcome_recorded_at"] = "2026-06-03"
        result = self.run_cli("post-event", "--as-of", "2026-06-25", input_data=json.dumps(raw))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["summary"],
            {
                "completed_count": 0,
                "item_count": 2,
                "missing_outcome_count": 2,
                "missing_recorded_at_count": 2,
                "overdue_count": 2,
            },
        )
        self.assertEqual([item["id"] for item in payload["items"]], ["demo-pfe-fda-2026", "demo-fomc-june-2026"])
        self.assertEqual(payload["items"][0]["review_due"], "2026-05-24")
        self.assertEqual(payload["items"][0]["outcome_review_template"]["outcome_recorded_at"], "2026-06-25")
        self.assertTrue(payload["items"][0]["outcome_review_template"]["source_update_needed"])

    def test_post_event_markdown_renders_outcome_review_template(self):
        result = self.run_cli("post-event", "--as-of", "2026-06-25", "--format", "markdown", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Post-Event Review", result.stdout)
        self.assertIn("| overdue | 2026-05-24 | PFE | regulatory_decision 2026-05-20..2026-05-24 |", result.stdout)
        self.assertIn("### Outcome Review Template", result.stdout)
        self.assertIn("- Actual outcome: TBD", result.stdout)

    def test_compare_json_reports_snapshot_deltas(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            current = Path(tmp) / "current.json"
            base.write_text(json.dumps(DEMO_DATA), encoding="utf-8")
            current.write_text(json.dumps(DEMO_UPDATED_DATA), encoding="utf-8")

            result = self.run_cli("compare", "--base", str(base), "--current", str(current), "--as-of", "2026-05-27")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["summary"],
            {
                "added_count": 1,
                "changed_count": 2,
                "evidence_change_count": 2,
                "removed_count": 1,
                "score_change_count": 2,
                "status_transition_count": 2,
                "thesis_impact_change_count": 1,
            },
        )
        self.assertEqual(payload["added"][0]["id"], "demo-amzn-kuiper-2026")
        self.assertEqual(payload["removed"][0]["id"], "demo-fomc-june-2026")
        by_id = {record["id"]: record for record in payload["changed"]}
        self.assertEqual(by_id["demo-nvda-computex-2026"]["status_transition"], {"from": "scheduled", "to": "confirmed"})
        self.assertEqual(by_id["demo-nvda-computex-2026"]["score_change"]["delta"], 5)
        self.assertEqual(by_id["demo-nvda-computex-2026"]["broker_view_changes"]["changed_views"][0]["institution"], "North Coast Securities")
        self.assertEqual(by_id["demo-pfe-fda-2026"]["thesis_impact_change"], {"from": "mixed", "to": "positive"})
        self.assertEqual(by_id["demo-pfe-fda-2026"]["evidence_change"]["added_urls"], ["https://example.com/pfe-label-update"])

    def test_compare_markdown_renders_added_removed_and_changed_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.json"
            current = Path(tmp) / "current.json"
            base.write_text(json.dumps(DEMO_DATA), encoding="utf-8")
            current.write_text(json.dumps(DEMO_UPDATED_DATA), encoding="utf-8")

            result = self.run_cli(
                "compare",
                "--base",
                str(base),
                "--current",
                str(current),
                "--as-of",
                "2026-05-27",
                "--format",
                "markdown",
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Snapshot Compare", result.stdout)
        self.assertIn("## Added Events", result.stdout)
        self.assertIn("demo-amzn-kuiper-2026", result.stdout)
        self.assertIn("| demo-pfe-fda-2026 | PFE | -34 | watching -> completed | +1/-1 | mixed -> positive |", result.stdout)
        self.assertIn("- Broker views: changed Harbor Life Sciences", result.stdout)

    def test_merge_json_combines_sources_conflicts_and_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp) / "left.json"
            right = Path(tmp) / "right.json"
            left.write_text(json.dumps(DEMO_DATA), encoding="utf-8")
            right.write_text(json.dumps(DEMO_UPDATED_DATA), encoding="utf-8")

            result = self.run_cli("merge", str(left), str(right), "--as-of", "2026-05-27")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["as_of"], "2026-05-27")
        self.assertEqual(payload["merge"]["validation"], {"errors": [], "ok": True})
        self.assertEqual(payload["merge"]["summary"]["merged_record_count"], 5)
        self.assertEqual(payload["merge"]["summary"]["conflict_count"], 2)
        self.assertEqual(payload["merge"]["record_sources"]["demo-pfe-fda-2026"], ["left.json", "right.json"])
        self.assertEqual(payload["merge"]["chosen_sources"]["demo-pfe-fda-2026"], "right.json")
        self.assertEqual([record["id"] for record in payload["records"]][0], "demo-msft-earnings-2026")
        merged_by_id = {record["id"]: record for record in payload["records"]}
        self.assertEqual(merged_by_id["demo-amzn-kuiper-2026"]["status"], "watching")
        self.assertEqual(merged_by_id["demo-pfe-fda-2026"]["status"], "completed")

    def test_merge_reports_duplicate_ids_without_emitting_duplicates(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"].append(json.loads(json.dumps(raw["records"][0])))
        with tempfile.TemporaryDirectory() as tmp:
            duplicate = Path(tmp) / "duplicate.json"
            updated = Path(tmp) / "updated.json"
            duplicate.write_text(json.dumps(raw), encoding="utf-8")
            updated.write_text(json.dumps(DEMO_UPDATED_DATA), encoding="utf-8")

            result = self.run_cli("merge", str(duplicate), str(updated), "--as-of", "2026-05-27")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["merge"]["duplicate_ids"][0]["ids"], ["demo-nvda-computex-2026"])
        self.assertEqual(payload["merge"]["duplicate_ids"][0]["record_indexes"]["demo-nvda-computex-2026"], [0, 4])
        ids = [record["id"] for record in payload["records"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_merge_can_prefer_newer_status_history_independently(self):
        main = json.loads(json.dumps(DEMO_DATA))
        branch = json.loads(json.dumps(DEMO_DATA))
        main["as_of"] = "2026-06-01"
        main["records"] = [main["records"][0]]
        main["records"][0]["confidence"] = 0.9
        branch["as_of"] = "2026-05-30"
        branch["records"] = [branch["records"][0]]
        branch["records"][0]["status"] = "confirmed"
        branch["records"][0]["history"].append(
            {
                "date": "2026-05-30",
                "status": "confirmed",
                "note": "Status confirmed in branch before the main dataset refresh.",
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            main_path = Path(tmp) / "main.json"
            branch_path = Path(tmp) / "branch.json"
            main_path.write_text(json.dumps(main), encoding="utf-8")
            branch_path.write_text(json.dumps(branch), encoding="utf-8")

            result = self.run_cli("merge", str(main_path), str(branch_path), "--prefer-newer-status-history")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        record = payload["records"][0]
        self.assertEqual(record["confidence"], 0.9)
        self.assertEqual(record["status"], "confirmed")
        self.assertEqual(record["history"][-1]["date"], "2026-05-30")
        self.assertEqual(payload["merge"]["chosen_sources"]["demo-nvda-computex-2026"], "main.json")
        self.assertEqual(payload["merge"]["status_history_sources"]["demo-nvda-computex-2026"], "branch.json")

    def test_export_demo_updated_snapshot(self):
        result = self.run_cli("export-demo", "--snapshot", "updated")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["as_of"], "2026-05-27")
        self.assertEqual(payload["records"][-1]["id"], "demo-amzn-kuiper-2026")

    def test_html_dashboard_renders_static_workflow_and_escapes_html(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["entity"] = 'NVIDIA <script>alert("x")</script>'
        raw["records"][0]["scenario_notes"]["base"] = "Roadmap <b>expands</b> & supply holds."
        raw["records"][0]["source_ref"] = "Keynote <tracker>"

        result = self.run_cli("html-dashboard", "--as-of", "2026-05-13", "--days", "45", input_data=json.dumps(raw))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("<!doctype html>\n"))
        self.assertIn("<h2>Score Tables</h2>", result.stdout)
        self.assertIn("<h2>Exposure Summary</h2>", result.stdout)
        self.assertIn("<h2>Sector Map</h2>", result.stdout)
        self.assertIn("<h2>Thesis Map</h2>", result.stdout)
        self.assertIn("<h2>Evidence Audit</h2>", result.stdout)
        self.assertIn("<h2>Scenario Matrix</h2>", result.stdout)
        self.assertIn("<h2>Watchlist</h2>", result.stdout)
        self.assertIn("Roadmap &lt;b&gt;expands&lt;/b&gt; &amp; supply holds.", result.stdout)
        self.assertNotIn("<script>alert", result.stdout)
        self.assertNotIn("<b>expands</b>", result.stdout)

    def test_static_site_writes_multi_page_no_js_directory(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["entity"] = 'NVIDIA <script>alert("x")</script>'
        raw["records"][0]["scenario_notes"]["base"] = "Roadmap <b>expands</b> & supply holds."

        with tempfile.TemporaryDirectory() as tmp:
            site_dir = Path(tmp) / "site"
            result = self.run_cli(
                "static-site",
                "--as-of",
                "2026-05-13",
                "--days",
                "45",
                "--output-dir",
                str(site_dir),
                input_data=json.dumps(raw),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["ok"], True)
            self.assertEqual(payload["file_count"], 9)
            expected = [
                "index.html",
                "dashboard.html",
                "sources.html",
                "style.css",
                "manifest.json",
                "tickers/msft.html",
                "tickers/nvda.html",
                "tickers/pfe.html",
                "tickers/spy.html",
            ]
            for relative_path in expected:
                self.assertTrue((site_dir / relative_path).is_file(), relative_path)
            index = (site_dir / "index.html").read_text(encoding="utf-8")
            nvda = (site_dir / "tickers" / "nvda.html").read_text(encoding="utf-8")
            sources = (site_dir / "sources.html").read_text(encoding="utf-8")
            manifest = json.loads((site_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn('href="tickers/nvda.html"', index)
        self.assertIn('href="../index.html"', nvda)
        self.assertIn("Roadmap &lt;b&gt;expands&lt;/b&gt; &amp; supply holds.", nvda)
        self.assertNotIn("<script>alert", nvda)
        self.assertIn("Source Inventory", sources)
        self.assertEqual(manifest["site_version"], 1)
        self.assertEqual(manifest["dataset"]["tickers"], ["MSFT", "NVDA", "PFE", "SPY"])
        self.assertEqual([item["path"] for item in manifest["files"]][0], "dashboard.html")

    def test_invalid_record_fails_validation(self):
        bad = dict(DEMO_DATA)
        bad["records"] = [dict(DEMO_DATA["records"][0], evidence_urls=[])]
        result = self.run_cli("validate", input_data=json.dumps(bad))
        self.assertEqual(result.returncode, 1)
        self.assertIn("at least one evidence URL", result.stdout)

    def test_export_csv_is_deterministic(self):
        result = self.run_cli("export-csv", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0].split(","), CSV_COLUMNS)
        self.assertIn("demo-msft-earnings-2026", lines[1])
        self.assertIn("demo-pfe-fda-2026", lines[2])
        self.assertIn("demo-nvda-computex-2026", lines[3])
        self.assertIn("demo-fomc-june-2026", lines[4])

    def test_export_ics_is_deterministic_and_escaped(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["entity"] = "NVIDIA, Corp; AI"
        raw["records"][0]["source_ref"] = "Keynote tracker\nsource"
        raw["records"][0]["scenario_notes"]["base"] = "Roadmap, supply; and demand\nstay aligned."

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "upcoming.ics"
            result = self.run_cli(
                "export-ics",
                "--as-of",
                "2026-05-13",
                "--days",
                "45",
                "--output",
                str(output),
                input_data=json.dumps(raw),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(encoding="utf-8", newline="") as handle:
                text = handle.read()
        unfolded = text.replace("\r\n ", "")
        self.assertTrue(text.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"))
        self.assertTrue(text.endswith("END:VCALENDAR\r\n"))
        self.assertEqual(text.count("BEGIN:VEVENT"), 3)
        self.assertIn("UID:demo-pfe-fda-2026-717aff837e76b0a92b6b@market-catalyst-calendar\r\n", text)
        self.assertIn("DTSTAMP:20260513T000000Z\r\n", text)
        self.assertIn("DTSTART;VALUE=DATE:20260520\r\nDTEND;VALUE=DATE:20260525\r\n", text)
        self.assertIn("CATEGORIES:market-catalyst,PFE,regulatory_decision,watching,mixed,high,pharma-pipeline-reset\r\n", unfolded)
        self.assertIn("URL:https://example.com/fda-calendar\r\n", text)
        self.assertIn("SUMMARY:NVDA product launch: NVIDIA\\, Corp\\; AI\r\n", text)
        self.assertIn("Base scenario: Roadmap\\, supply\\; and demand\\nstay aligned.", unfolded)
        self.assertIn("Source note: Keynote tracker\\nsource", unfolded)

    def test_import_csv_outputs_json_dataset(self):
        csv_result = self.run_cli("export-csv", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(csv_result.returncode, 0, csv_result.stderr)
        json_result = self.run_cli("import-csv", input_data=csv_result.stdout)
        self.assertEqual(json_result.returncode, 0, json_result.stderr)
        payload = json.loads(json_result.stdout)
        self.assertEqual(payload["as_of"], "2026-05-13")
        self.assertEqual(
            [record["id"] for record in payload["records"]],
            ["demo-msft-earnings-2026", "demo-pfe-fda-2026", "demo-nvda-computex-2026", "demo-fomc-june-2026"],
        )
        self.assertEqual(validation_errors(parse_dataset(payload)), [])

    def test_create_archive_writes_reports_manifest_and_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_path = Path(tmp) / "demo_records.json"
            archive_dir = Path(tmp) / "archive"
            dataset_path.write_text(json.dumps(DEMO_DATA), encoding="utf-8")

            create_result = self.run_cli(
                "create-archive",
                "--input",
                str(dataset_path),
                "--output-dir",
                str(archive_dir),
                "--as-of",
                "2026-05-13",
                "--days",
                "45",
            )
            self.assertEqual(create_result.returncode, 0, create_result.stderr)
            self.assertEqual(json.loads(create_result.stdout)["file_count"], 33)

            manifest = json.loads((archive_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["archive_version"], 1)
            self.assertEqual(manifest["dataset"]["record_count"], 4)
            self.assertEqual(
                [item["path"] for item in manifest["files"]],
                [
                    "dataset/dataset.csv",
                    "dataset/dataset.json",
                    "reports/brief.md",
                    "reports/broker_matrix.json",
                    "reports/broker_matrix.md",
                    "reports/command_cookbook.md",
                    "reports/dashboard.html",
                    "reports/decision_log.json",
                    "reports/decision_log.md",
                    "reports/evidence_audit.json",
                    "reports/evidence_audit.md",
                    "reports/exposure.json",
                    "reports/exposure.md",
                    "reports/post_event.json",
                    "reports/post_event.md",
                    "reports/review_plan.json",
                    "reports/review_plan.md",
                    "reports/risk_budget.json",
                    "reports/risk_budget.md",
                    "reports/scenario_matrix.json",
                    "reports/scenario_matrix.md",
                    "reports/sector_map.json",
                    "reports/sector_map.md",
                    "reports/source_pack.csv",
                    "reports/source_pack.json",
                    "reports/source_pack.md",
                    "reports/stale.json",
                    "reports/thesis_map.json",
                    "reports/thesis_map.md",
                    "reports/upcoming.ics",
                    "reports/upcoming.json",
                    "reports/watchlist.json",
                    "reports/watchlist.md",
                ],
            )

            verify_result = self.run_cli("verify-archive", str(archive_dir))
            self.assertEqual(verify_result.returncode, 0, verify_result.stderr)
            verify_payload = json.loads(verify_result.stdout)
            self.assertTrue(verify_payload["ok"])
            self.assertEqual(verify_payload["errors"], [])

    def test_verify_archive_fails_on_changed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_path = Path(tmp) / "demo_records.json"
            archive_dir = Path(tmp) / "archive"
            dataset_path.write_text(json.dumps(DEMO_DATA), encoding="utf-8")

            create_result = self.run_cli("create-archive", "--input", str(dataset_path), "--output-dir", str(archive_dir))
            self.assertEqual(create_result.returncode, 0, create_result.stderr)
            (archive_dir / "reports" / "brief.md").write_text("changed\n", encoding="utf-8")

            verify_result = self.run_cli("verify-archive", str(archive_dir))
            self.assertEqual(verify_result.returncode, 1)
            payload = json.loads(verify_result.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("sha256 mismatch: reports/brief.md", payload["errors"])

    def test_demo_bundle_writes_every_example_with_manifest_and_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp) / "demo-bundle"

            result = self.run_cli("demo-bundle", "--output-dir", str(bundle_dir))

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["file_count"], 60)
            self.assertEqual(payload["manifest"], "manifest.json")

            manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["bundle_version"], 1)
            self.assertEqual(manifest["dataset"]["record_count"], 4)
            self.assertEqual(manifest["parameters"]["as_of"], "2026-05-13")
            self.assertEqual(len(manifest["files"]), 60)

            paths = [item["path"] for item in manifest["files"]]
            self.assertIn("README.md", paths)
            self.assertIn("quickstart-transcript.txt", paths)
            self.assertIn("examples/demo_records.json", paths)
            self.assertIn("examples/presets.json", paths)
            self.assertIn("examples/preset_run.json", paths)
            self.assertIn("examples/quality_gate.json", paths)
            self.assertIn("examples/doctor.json", paths)
            self.assertIn("examples/doctor.md", paths)
            self.assertIn("examples/doctor_patch.json", paths)
            self.assertIn("examples/command_cookbook.md", paths)
            self.assertIn("examples/agent_handoff.json", paths)
            self.assertIn("examples/agent_handoff.md", paths)
            self.assertIn("examples/taxonomy.json", paths)
            self.assertIn("examples/taxonomy.md", paths)
            self.assertIn("examples/version_report.json", paths)
            self.assertIn("examples/version_report.md", paths)
            self.assertIn("examples/fixture_gallery.json", paths)
            self.assertIn("examples/fixture_gallery.md", paths)
            self.assertIn("examples/finalize_release.json", paths)
            self.assertIn("examples/finalize_release.md", paths)
            self.assertIn("examples/drilldown.json", paths)
            self.assertIn("examples/drilldown.md", paths)
            self.assertIn("examples/tutorial.md", paths)
            self.assertIn("examples/dashboard.html", paths)

            selfcheck = load_selfcheck_module()
            documented = {f"examples/{path.name}" for _, path, _ in selfcheck.documented_example_commands()}
            bundled_examples = {path for path in paths if path.startswith("examples/")}
            self.assertEqual(bundled_examples, documented)

            quality_entry = next(item for item in manifest["files"] if item["path"] == "examples/quality_gate.json")
            self.assertEqual(quality_entry["exit_code"], 1)
            self.assertEqual(
                quality_entry["command"],
                "quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13",
            )

            demo_json = (bundle_dir / "examples" / "demo_records.json").read_text(encoding="utf-8")
            self.assertEqual(json.loads(demo_json), json.loads(json.dumps(DEMO_DATA)))
            transcript = (bundle_dir / "quickstart-transcript.txt").read_text(encoding="utf-8")
            self.assertIn("$ python -m market_catalyst_calendar demo-bundle --output-dir demo-bundle", transcript)
            self.assertIn("# exit code: 1", transcript)

    def test_fixture_gallery_json_lists_hashes_provenance_and_use_cases(self):
        result = self.run_cli("fixture-gallery")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "fixture-gallery/v1")
        self.assertEqual(payload["summary"]["fixture_count"], 56)
        self.assertEqual(payload["summary"]["output_type_counts"]["json"], 29)
        quality = next(item for item in payload["fixtures"] if item["path"] == "examples/quality_gate.json")
        self.assertEqual(quality["exit_code"], 1)
        self.assertEqual(
            quality["command"],
            "python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13",
        )
        self.assertEqual(quality["output_type"], "json")
        self.assertEqual(len(quality["sha256"]), 64)
        self.assertIn("examples/demo_records.json", quality["input_fixtures"])
        self.assertIn("quality diagnostics", quality["recommended_use_cases"][0])

    def test_fixture_gallery_markdown_renders_command_provenance(self):
        result = self.run_cli("fixture-gallery", "--format", "markdown")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Fixture Gallery", result.stdout)
        self.assertIn("| `examples/demo_records.json` | json | 0 |", result.stdout)
        self.assertIn("### `examples/quality_gate.json`", result.stdout)
        self.assertIn("Command: `python -m market_catalyst_calendar quality-gate --profile public", result.stdout)

    def test_demo_bundle_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"

            first_result = self.run_cli("demo-bundle", "--output-dir", str(first))
            second_result = self.run_cli("demo-bundle", "--output-dir", str(second))

            self.assertEqual(first_result.returncode, 0, first_result.stderr)
            self.assertEqual(second_result.returncode, 0, second_result.stderr)
            first_manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
            second_manifest = json.loads((second / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(first_manifest, second_manifest)

    def test_demo_bundle_rejects_non_empty_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp) / "demo-bundle"
            bundle_dir.mkdir()
            (bundle_dir / "existing.txt").write_text("keep\n", encoding="utf-8")

            result = self.run_cli("demo-bundle", "--output-dir", str(bundle_dir))

            self.assertEqual(result.returncode, 2)
            self.assertIn("demo bundle output directory must be empty", result.stderr)

    def test_release_audit_json_passes_for_checked_in_release_artifacts(self):
        result = self.run_cli("release-audit", "--root", str(ROOT))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["schema_version"], "release-audit/v1")
        self.assertEqual(payload["summary"], {"check_count": 5, "failed_count": 0, "passed_count": 5})
        checks = {check["id"]: check for check in payload["checks"]}
        self.assertEqual(checks["examples-regenerated"]["expected_count"], 58)
        self.assertEqual(checks["examples-regenerated"]["mismatches"], [])
        self.assertEqual(checks["readme-required-commands"]["missing_commands"], [])
        self.assertEqual(checks["schema-release-audit-fields"]["missing_fields"], [])
        self.assertEqual(checks["no-workflow-files"]["workflow_files"], [])

    def test_smoke_matrix_json_runs_all_commands_with_expected_files(self):
        result = self.run_cli("smoke-matrix")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["schema_version"], "smoke-matrix/v1")
        self.assertGreaterEqual(payload["summary"]["command_count"], len(REQUIRED_COMMANDS))
        self.assertEqual(payload["summary"]["failed_count"], 0)
        by_command = {item["command"]: item for item in payload["commands"]}
        self.assertIn("smoke-matrix", by_command)
        self.assertIn("finalize-release", by_command)
        self.assertEqual(by_command["quality-gate"]["expected_exit_code"], 1)
        self.assertEqual(by_command["html-dashboard"]["expected_files"], ["dashboard.html"])
        self.assertEqual(by_command["demo-bundle"]["expected_files"], ["demo-bundle/manifest.json"])
        self.assertIn(by_command["validate"]["duration_bucket"], {"lt_250ms", "lt_1s", "lt_5s", "gte_5s"})

    def test_smoke_matrix_markdown_renders_pass_table(self):
        result = self.run_cli("smoke-matrix", "--format", "markdown")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Smoke Matrix", result.stdout)
        self.assertIn("Status: PASS", result.stdout)
        self.assertIn("| smoke-matrix | PASS | 0 | 0 | stdout |", result.stdout)
        self.assertIn("| finalize-release | PASS | 0 | 0 | stdout |", result.stdout)

    def test_finalize_release_json_combines_release_inputs(self):
        tmp, repo = self.make_changelog_repo()
        with tmp:
            result = self.run_cli("finalize-release", "--root", str(ROOT), "--repo", str(repo), "--since-tag", "v0.1.0")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["schema_version"], "finalize-release/v1")
        self.assertEqual([item["id"] for item in payload["checklist"]], ["release-audit", "smoke-matrix", "fixture-gallery", "changelog"])
        self.assertEqual(payload["components"]["release_audit"]["failed_checks"], [])
        self.assertEqual(payload["components"]["smoke_matrix"]["failed_commands"], [])
        self.assertEqual(payload["components"]["fixture_gallery"]["output_type_counts"]["json"], 29)
        self.assertEqual(payload["components"]["changelog"]["commit_count"], 2)
        self.assertEqual(payload["release_notes"]["categories"][0]["id"], "feat")

    def test_finalize_release_markdown_renders_checklist(self):
        result = self.run_cli("finalize-release", "--example", "--format", "markdown")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Release Finalizer", result.stdout)
        self.assertIn("- [x] `release-audit` - 5 passed / 5 checks", result.stdout)
        self.assertIn("| fixture-gallery | PASS | 56 fixtures indexed |", result.stdout)

    def test_release_audit_markdown_renders_pass_table(self):
        result = self.run_cli("release-audit", "--root", str(ROOT), "--format", "markdown")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Market Catalyst Release Audit", result.stdout)
        self.assertIn("Status: PASS", result.stdout)
        self.assertIn("| examples-regenerated | PASS | 58 of 58 expected fixtures match |", result.stdout)
        self.assertIn("| no-workflow-files | PASS | no workflow files found |", result.stdout)

    def test_release_audit_fails_when_workflow_files_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_root = Path(tmp)
            for relative_path, text in _bundle_files().items():
                if relative_path.startswith("examples/"):
                    path = audit_root / relative_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(text.encode("utf-8"))
            readme_commands = "\n".join(f"python -m market_catalyst_calendar {command}" for command in REQUIRED_COMMANDS)
            (audit_root / "README.md").write_text(readme_commands, encoding="utf-8")
            schema_text = "\n".join(f"`{field}`" for field in RELEASE_AUDIT_SCHEMA_FIELDS)
            (audit_root / "docs").mkdir()
            (audit_root / "docs" / "SCHEMA.md").write_text(schema_text, encoding="utf-8")
            skill = audit_root / "skills" / "agent" / "market-catalyst-calendar" / "SKILL.md"
            skill.parent.mkdir(parents=True, exist_ok=True)
            skill.write_text("release-audit\nfinalize-release\n", encoding="utf-8")
            workflow = audit_root / ".github" / "workflows" / "release.yml"
            workflow.parent.mkdir(parents=True, exist_ok=True)
            workflow.write_text("name: release\n", encoding="utf-8")

            result = self.run_cli("release-audit", "--root", str(audit_root))

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        check = next(item for item in payload["checks"] if item["id"] == "no-workflow-files")
        self.assertEqual(check["workflow_files"], [".github/workflows/release.yml"])


class SelfcheckDocumentationTests(unittest.TestCase):
    def test_examples_readme_documents_every_fixture_command(self):
        selfcheck = load_selfcheck_module()
        documented = {expected_path for _, expected_path, _ in selfcheck.documented_example_commands()}
        fixtures = set(selfcheck.example_fixture_paths())
        self.assertEqual(documented, fixtures)

    def test_documented_example_commands_use_module_entrypoint(self):
        selfcheck = load_selfcheck_module()
        commands = [command for command, _, _ in selfcheck.documented_example_commands()]
        self.assertTrue(commands)
        for command in commands:
            self.assertEqual(command[:3], [sys.executable, "-m", "market_catalyst_calendar"])


if __name__ == "__main__":
    unittest.main()
