import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from market_catalyst_calendar.csv_io import CSV_COLUMNS, csv_to_dataset_json, dataset_to_csv
from market_catalyst_calendar.demo import DEMO_DATA, DEMO_UPDATED_DATA
from market_catalyst_calendar.models import parse_dataset, validation_errors
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

    def test_validate_stdin(self):
        result = self.run_cli("validate", input_data=json.dumps(DEMO_DATA))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"ok": True, "record_count": 4})

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
        by_id = {record["id"]: record for record in payload["records"]}
        self.assertEqual(
            by_id["demo-fomc-june-2026"]["failed_rules"],
            ["minimum_evidence", "no_placeholder_urls"],
        )
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
        self.assertIn("| critical | no_placeholder_urls | PFE | demo-pfe-fda-2026 | evidence URL https://example.com/fda-calendar is a placeholder host |", result.stdout)
        self.assertIn("- Failed rules: broker_caveats, minimum_evidence, no_placeholder_urls, review_freshness", result.stdout)

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
            self.assertEqual(json.loads(create_result.stdout)["file_count"], 32)

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
            self.assertEqual(payload["file_count"], 41)
            self.assertEqual(payload["manifest"], "manifest.json")

            manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["bundle_version"], 1)
            self.assertEqual(manifest["dataset"]["record_count"], 4)
            self.assertEqual(manifest["parameters"]["as_of"], "2026-05-13")
            self.assertEqual(len(manifest["files"]), 41)

            paths = [item["path"] for item in manifest["files"]]
            self.assertIn("README.md", paths)
            self.assertIn("quickstart-transcript.txt", paths)
            self.assertIn("examples/demo_records.json", paths)
            self.assertIn("examples/quality_gate.json", paths)
            self.assertIn("examples/dashboard.html", paths)

            selfcheck = load_selfcheck_module()
            documented = {f"examples/{path.name}" for _, path, _ in selfcheck.documented_example_commands()}
            bundled_examples = {path for path in paths if path.startswith("examples/")}
            self.assertEqual(bundled_examples, documented)

            quality_entry = next(item for item in manifest["files"] if item["path"] == "examples/quality_gate.json")
            self.assertEqual(quality_entry["exit_code"], 1)
            self.assertEqual(
                quality_entry["command"],
                "quality-gate --input examples/demo_records.json --as-of 2026-05-13",
            )

            demo_json = (bundle_dir / "examples" / "demo_records.json").read_text(encoding="utf-8")
            self.assertEqual(json.loads(demo_json), json.loads(json.dumps(DEMO_DATA)))
            transcript = (bundle_dir / "quickstart-transcript.txt").read_text(encoding="utf-8")
            self.assertIn("$ python -m market_catalyst_calendar demo-bundle --output-dir demo-bundle", transcript)
            self.assertIn("# exit code: 1", transcript)

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
