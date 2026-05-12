#!/usr/bin/env python3
"""Run the offline project selfcheck."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def main() -> int:
    checks = [
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    ]
    for command in checks:
        result = run(command)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode

    with tempfile.TemporaryDirectory() as tmp:
        demo_path = Path(tmp) / "demo_records.json"
        export = run([sys.executable, "-m", "market_catalyst_calendar", "export-demo", "--output", str(demo_path)])
        if export.returncode != 0:
            sys.stderr.write(export.stderr)
            return export.returncode
        validate = run([sys.executable, "-m", "market_catalyst_calendar", "validate", "--input", str(demo_path)])
        if validate.returncode != 0:
            sys.stderr.write(validate.stdout)
            sys.stderr.write(validate.stderr)
            return validate.returncode
        archive_dir = Path(tmp) / "archive"
        create_archive = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "create-archive",
                "--input",
                str(demo_path),
                "--output-dir",
                str(archive_dir),
                "--as-of",
                "2026-05-13",
                "--days",
                "45",
            ]
        )
        if create_archive.returncode != 0:
            sys.stderr.write(create_archive.stdout)
            sys.stderr.write(create_archive.stderr)
            return create_archive.returncode
        verify_archive = run([sys.executable, "-m", "market_catalyst_calendar", "verify-archive", str(archive_dir)])
        if verify_archive.returncode != 0:
            sys.stderr.write(verify_archive.stdout)
            sys.stderr.write(verify_archive.stderr)
            return verify_archive.returncode
        comparisons = [
            (
                [sys.executable, "-m", "market_catalyst_calendar", "upcoming", "--input", str(demo_path), "--as-of", "2026-05-13", "--days", "45"],
                ROOT / "examples" / "upcoming.json",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "stale", "--input", str(demo_path), "--as-of", "2026-05-13"],
                ROOT / "examples" / "stale.json",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "brief", "--input", str(demo_path), "--as-of", "2026-05-13", "--days", "45"],
                ROOT / "examples" / "brief.md",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "exposure", "--input", str(demo_path), "--as-of", "2026-05-13", "--days", "45"],
                ROOT / "examples" / "exposure.json",
            ),
            (
                [
                    sys.executable,
                    "-m",
                    "market_catalyst_calendar",
                    "exposure",
                    "--input",
                    str(demo_path),
                    "--as-of",
                    "2026-05-13",
                    "--days",
                    "45",
                    "--format",
                    "markdown",
                ],
                ROOT / "examples" / "exposure.md",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "review-plan", "--input", str(demo_path), "--as-of", "2026-05-13", "--days", "45"],
                ROOT / "examples" / "review_plan.json",
            ),
            (
                [
                    sys.executable,
                    "-m",
                    "market_catalyst_calendar",
                    "review-plan",
                    "--input",
                    str(demo_path),
                    "--as-of",
                    "2026-05-13",
                    "--days",
                    "45",
                    "--format",
                    "markdown",
                ],
                ROOT / "examples" / "review_plan.md",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "scenario-matrix", "--input", str(demo_path), "--as-of", "2026-05-13", "--days", "45"],
                ROOT / "examples" / "scenario_matrix.json",
            ),
            (
                [
                    sys.executable,
                    "-m",
                    "market_catalyst_calendar",
                    "scenario-matrix",
                    "--input",
                    str(demo_path),
                    "--as-of",
                    "2026-05-13",
                    "--days",
                    "45",
                    "--format",
                    "markdown",
                ],
                ROOT / "examples" / "scenario_matrix.md",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "evidence-audit", "--input", str(demo_path), "--as-of", "2026-05-13"],
                ROOT / "examples" / "evidence_audit.json",
            ),
            (
                [
                    sys.executable,
                    "-m",
                    "market_catalyst_calendar",
                    "evidence-audit",
                    "--input",
                    str(demo_path),
                    "--as-of",
                    "2026-05-13",
                    "--format",
                    "markdown",
                ],
                ROOT / "examples" / "evidence_audit.md",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "thesis-map", "--input", str(demo_path), "--as-of", "2026-05-13"],
                ROOT / "examples" / "thesis_map.json",
            ),
            (
                [
                    sys.executable,
                    "-m",
                    "market_catalyst_calendar",
                    "thesis-map",
                    "--input",
                    str(demo_path),
                    "--as-of",
                    "2026-05-13",
                    "--format",
                    "markdown",
                ],
                ROOT / "examples" / "thesis_map.md",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "export-csv", "--input", str(demo_path)],
                ROOT / "examples" / "demo_records.csv",
            ),
            (
                [
                    sys.executable,
                    "-m",
                    "market_catalyst_calendar",
                    "export-ics",
                    "--input",
                    str(demo_path),
                    "--as-of",
                    "2026-05-13",
                    "--days",
                    "45",
                ],
                ROOT / "examples" / "upcoming.ics",
            ),
            (
                [sys.executable, "-m", "market_catalyst_calendar", "import-csv", "--input", str(ROOT / "examples" / "demo_records.csv")],
                ROOT / "examples" / "imported_demo_records.json",
            ),
        ]
        for command, expected_path in comparisons:
            result = run(command)
            if result.returncode != 0:
                sys.stderr.write(result.stderr)
                return result.returncode
            expected = expected_path.read_text(encoding="utf-8")
            if result.stdout != expected:
                sys.stderr.write(f"output mismatch for {' '.join(command)}\n")
                return 1
    print("selfcheck ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
