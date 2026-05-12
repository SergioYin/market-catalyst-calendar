import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from market_catalyst_calendar.csv_io import CSV_COLUMNS, csv_to_dataset_json, dataset_to_csv
from market_catalyst_calendar.demo import DEMO_DATA
from market_catalyst_calendar.models import parse_dataset, validation_errors
from market_catalyst_calendar.scoring import score_record


class ModelTests(unittest.TestCase):
    def test_demo_validates(self):
        dataset = parse_dataset(DEMO_DATA)
        self.assertEqual(validation_errors(dataset), [])
        self.assertEqual(len(dataset.records), 3)

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

        imported = csv_to_dataset_json(dataset_to_csv(parse_dataset(raw)))

        first = next(record for record in imported["records"] if record["id"] == "demo-nvda-computex-2026")
        self.assertEqual(first["evidence_urls"], raw["records"][0]["evidence_urls"])
        self.assertEqual(first["scenario_notes"]["bull"], raw["records"][0]["scenario_notes"]["bull"])
        self.assertEqual(first["history"][0]["note"], raw["records"][0]["history"][0]["note"])
        self.assertEqual(first["position_size"], raw["records"][0]["position_size"])
        self.assertEqual(first["portfolio_weight"], raw["records"][0]["portfolio_weight"])
        self.assertEqual(first["thesis_id"], raw["records"][0]["thesis_id"])
        self.assertEqual(first["source_ref"], raw["records"][0]["source_ref"])
        self.assertEqual(first["evidence_checked_at"], raw["records"][0]["evidence_checked_at"])
        self.assertEqual(first["broker_views"][1]["caveat"], raw["records"][0]["broker_views"][0]["caveat"])

    def test_csv_import_accepts_missing_optional_exposure_columns(self):
        csv_text = dataset_to_csv(parse_dataset(DEMO_DATA))
        lines = csv_text.splitlines()
        indexes = [
            CSV_COLUMNS.index("position_size"),
            CSV_COLUMNS.index("portfolio_weight"),
            CSV_COLUMNS.index("thesis_id"),
            CSV_COLUMNS.index("source_ref"),
            CSV_COLUMNS.index("evidence_checked_at"),
        ]
        filtered = []
        for line in lines:
            columns = line.split(",")
            filtered.append(",".join(value for index, value in enumerate(columns) if index not in indexes))

        imported = csv_to_dataset_json("\n".join(filtered) + "\n")

        first = next(record for record in imported["records"] if record["id"] == "demo-pfe-fda-2026")
        self.assertIsNone(first["position_size"])
        self.assertIsNone(first["portfolio_weight"])
        self.assertIsNone(first["thesis_id"])
        self.assertIsNone(first["source_ref"])
        self.assertNotIn("evidence_checked_at", first)

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
        self.assertEqual(json.loads(result.stdout), {"ok": True, "record_count": 3})

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
        raw["records"][1]["thesis_id"] = raw["records"][0]["thesis_id"]
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
        self.assertEqual(payload["summary"]["record_count"], 3)
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
        self.assertIn("demo-pfe-fda-2026", lines[1])
        self.assertIn("demo-nvda-computex-2026", lines[2])
        self.assertIn("demo-fomc-june-2026", lines[3])

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
        self.assertEqual([record["id"] for record in payload["records"]], ["demo-pfe-fda-2026", "demo-nvda-computex-2026", "demo-fomc-june-2026"])
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
            self.assertEqual(json.loads(create_result.stdout)["file_count"], 21)

            manifest = json.loads((archive_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["archive_version"], 1)
            self.assertEqual(manifest["dataset"]["record_count"], 3)
            self.assertEqual(
                [item["path"] for item in manifest["files"]],
                [
                    "dataset/dataset.csv",
                    "dataset/dataset.json",
                    "reports/brief.md",
                    "reports/broker_matrix.json",
                    "reports/broker_matrix.md",
                    "reports/dashboard.html",
                    "reports/evidence_audit.json",
                    "reports/evidence_audit.md",
                    "reports/exposure.json",
                    "reports/exposure.md",
                    "reports/review_plan.json",
                    "reports/review_plan.md",
                    "reports/scenario_matrix.json",
                    "reports/scenario_matrix.md",
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


if __name__ == "__main__":
    unittest.main()
