#!/usr/bin/env python3
"""Run the offline project selfcheck."""

from __future__ import annotations

import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_README = ROOT / "examples" / "README.md"


def run(args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def documented_example_commands() -> List[Tuple[List[str], Path, int]]:
    commands: List[Tuple[List[str], Path, int]] = []
    in_bash = False
    pending_fixture: Optional[Path] = None
    pending_exit_code = 0
    for line_number, raw_line in enumerate(EXAMPLES_README.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if line == "```bash":
            in_bash = True
            pending_fixture = None
            pending_exit_code = 0
            continue
        if in_bash and line == "```":
            if pending_fixture is not None:
                raise ValueError(f"{EXAMPLES_README}:{line_number}: fixture marker has no command")
            in_bash = False
            continue
        if not in_bash or not line:
            continue
        if line.startswith("# fixture:"):
            fixture = line.removeprefix("# fixture:").strip()
            if not fixture:
                raise ValueError(f"{EXAMPLES_README}:{line_number}: empty fixture marker")
            pending_fixture = ROOT / fixture
            pending_exit_code = 0
            continue
        if line.startswith("# exit-code:"):
            code = line.removeprefix("# exit-code:").strip()
            if not code.isdigit():
                raise ValueError(f"{EXAMPLES_README}:{line_number}: exit-code marker must be a non-negative integer")
            pending_exit_code = int(code)
            continue
        if line.startswith("#"):
            continue
        if pending_fixture is None:
            raise ValueError(f"{EXAMPLES_README}:{line_number}: documented command is missing a fixture marker")
        args = shlex.split(line)
        if args[:2] == ["python", "-m"]:
            args[0] = sys.executable
        commands.append((args, pending_fixture, pending_exit_code))
        pending_fixture = None
        pending_exit_code = 0
    return commands


def example_fixture_paths() -> List[Path]:
    return sorted(
        path
        for path in (ROOT / "examples").iterdir()
        if path.is_file() and path.name not in {".gitkeep", "README.md"}
    )


def validate_documented_examples() -> int:
    try:
        commands = documented_example_commands()
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    documented_paths = sorted(expected_path for _, expected_path, _ in commands)
    fixture_paths = example_fixture_paths()
    if documented_paths != fixture_paths:
        missing = sorted(path.relative_to(ROOT).as_posix() for path in set(fixture_paths) - set(documented_paths))
        extra = sorted(path.relative_to(ROOT).as_posix() for path in set(documented_paths) - set(fixture_paths))
        if missing:
            sys.stderr.write("examples missing documented commands: " + ", ".join(missing) + "\n")
        if extra:
            sys.stderr.write("documented commands reference missing fixtures: " + ", ".join(extra) + "\n")
        return 1
    for command, expected_path, expected_exit_code in commands:
        result = run(command)
        if result.returncode != expected_exit_code:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            sys.stderr.write(
                f"unexpected exit code for {' '.join(command)}: got {result.returncode}, expected {expected_exit_code}\n"
            )
            return result.returncode or 1
        expected = expected_path.read_text(encoding="utf-8")
        if result.stdout != expected:
            sys.stderr.write(f"output mismatch for {' '.join(command)}\n")
            return 1
    return 0


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
        quality_gate = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "quality-gate",
                "--input",
                str(demo_path),
                "--as-of",
                "2026-05-13",
            ]
        )
        if quality_gate.returncode != 1 or '"ok": false' not in quality_gate.stdout:
            sys.stderr.write(quality_gate.stdout)
            sys.stderr.write(quality_gate.stderr)
            return quality_gate.returncode or 1
        sector_map = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "sector-map",
                "--input",
                str(demo_path),
                "--as-of",
                "2026-05-13",
            ]
        )
        if sector_map.returncode != 0:
            sys.stderr.write(sector_map.stdout)
            sys.stderr.write(sector_map.stderr)
            return sector_map.returncode
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
        bundle_dir = Path(tmp) / "demo-bundle"
        demo_bundle = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "demo-bundle",
                "--output-dir",
                str(bundle_dir),
            ]
        )
        if demo_bundle.returncode != 0:
            sys.stderr.write(demo_bundle.stdout)
            sys.stderr.write(demo_bundle.stderr)
            return demo_bundle.returncode
        required_bundle_files = [
            bundle_dir / "README.md",
            bundle_dir / "quickstart-transcript.txt",
            bundle_dir / "manifest.json",
            bundle_dir / "examples" / "demo_records.json",
            bundle_dir / "examples" / "quality_gate.json",
            bundle_dir / "examples" / "dashboard.html",
        ]
        missing_bundle_files = [path.relative_to(bundle_dir).as_posix() for path in required_bundle_files if not path.is_file()]
        if missing_bundle_files:
            sys.stderr.write("demo bundle missing files: " + ", ".join(missing_bundle_files) + "\n")
            return 1
        documented_result = validate_documented_examples()
        if documented_result != 0:
            return documented_result
    print("selfcheck ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
