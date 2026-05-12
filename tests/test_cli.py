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

        imported = csv_to_dataset_json(dataset_to_csv(parse_dataset(raw)))

        first = next(record for record in imported["records"] if record["id"] == "demo-nvda-computex-2026")
        self.assertEqual(first["evidence_urls"], raw["records"][0]["evidence_urls"])
        self.assertEqual(first["scenario_notes"]["bull"], raw["records"][0]["scenario_notes"]["bull"])
        self.assertEqual(first["history"][0]["note"], raw["records"][0]["history"][0]["note"])
        self.assertEqual(first["position_size"], raw["records"][0]["position_size"])
        self.assertEqual(first["portfolio_weight"], raw["records"][0]["portfolio_weight"])

    def test_csv_import_accepts_missing_optional_exposure_columns(self):
        csv_text = dataset_to_csv(parse_dataset(DEMO_DATA))
        lines = csv_text.splitlines()
        indexes = [CSV_COLUMNS.index("position_size"), CSV_COLUMNS.index("portfolio_weight")]
        filtered = []
        for line in lines:
            columns = line.split(",")
            filtered.append(",".join(value for index, value in enumerate(columns) if index not in indexes))

        imported = csv_to_dataset_json("\n".join(filtered) + "\n")

        first = next(record for record in imported["records"] if record["id"] == "demo-pfe-fda-2026")
        self.assertIsNone(first["position_size"])
        self.assertIsNone(first["portfolio_weight"])

    def test_portfolio_weight_must_be_decimal_weight(self):
        raw = json.loads(json.dumps(DEMO_DATA))
        raw["records"][0]["portfolio_weight"] = 8.25
        with self.assertRaisesRegex(ValueError, "portfolio_weight must be between 0 and 1"):
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
            self.assertEqual(json.loads(create_result.stdout)["file_count"], 9)

            manifest = json.loads((archive_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["archive_version"], 1)
            self.assertEqual(manifest["dataset"]["record_count"], 3)
            self.assertEqual(
                [item["path"] for item in manifest["files"]],
                [
                    "dataset/dataset.csv",
                    "dataset/dataset.json",
                    "reports/brief.md",
                    "reports/exposure.json",
                    "reports/exposure.md",
                    "reports/review_plan.json",
                    "reports/review_plan.md",
                    "reports/stale.json",
                    "reports/upcoming.json",
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
