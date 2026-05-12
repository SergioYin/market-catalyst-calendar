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


def documented_example_commands() -> List[Tuple[List[str], Path]]:
    commands: List[Tuple[List[str], Path]] = []
    in_bash = False
    pending_fixture: Optional[Path] = None
    for line_number, raw_line in enumerate(EXAMPLES_README.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if line == "```bash":
            in_bash = True
            pending_fixture = None
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
            continue
        if line.startswith("#"):
            continue
        if pending_fixture is None:
            raise ValueError(f"{EXAMPLES_README}:{line_number}: documented command is missing a fixture marker")
        args = shlex.split(line)
        if args[:2] == ["python", "-m"]:
            args[0] = sys.executable
        commands.append((args, pending_fixture))
        pending_fixture = None
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
    documented_paths = sorted(expected_path for _, expected_path in commands)
    fixture_paths = example_fixture_paths()
    if documented_paths != fixture_paths:
        missing = sorted(path.relative_to(ROOT).as_posix() for path in set(fixture_paths) - set(documented_paths))
        extra = sorted(path.relative_to(ROOT).as_posix() for path in set(documented_paths) - set(fixture_paths))
        if missing:
            sys.stderr.write("examples missing documented commands: " + ", ".join(missing) + "\n")
        if extra:
            sys.stderr.write("documented commands reference missing fixtures: " + ", ".join(extra) + "\n")
        return 1
    for command, expected_path in commands:
        result = run(command)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode
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
        documented_result = validate_documented_examples()
        if documented_result != 0:
            return documented_result
    print("selfcheck ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
