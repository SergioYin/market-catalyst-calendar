#!/usr/bin/env python3
"""Run the offline project selfcheck."""

from __future__ import annotations

import shlex
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_README = ROOT / "examples" / "README.md"


def run(args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def run_git(repo: Path, args: List[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "Selfcheck",
        "GIT_AUTHOR_EMAIL": "selfcheck@example.com",
        "GIT_COMMITTER_NAME": "Selfcheck",
        "GIT_COMMITTER_EMAIL": "selfcheck@example.com",
        "GIT_AUTHOR_DATE": "2026-05-13T12:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-05-13T12:00:00+00:00",
    })
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False, env=env)


def check_changelog_command(tmp: Path) -> int:
    repo = tmp / "changelog-repo"
    repo.mkdir()
    for args in [
        ["init"],
        ["config", "user.name", "Selfcheck"],
        ["config", "user.email", "selfcheck@example.com"],
    ]:
        result = run_git(repo, args)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode
    notes = repo / "notes.txt"
    notes.write_text("base\n", encoding="utf-8")
    for args in [["add", "notes.txt"], ["commit", "-m", "chore: initial release"], ["tag", "v0.1.0"]]:
        result = run_git(repo, args)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode
    notes.write_text("base\nfeature\n", encoding="utf-8")
    for args in [["add", "notes.txt"], ["commit", "-m", "feat(cli): add changelog notes #7"]]:
        result = run_git(repo, args)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode
    changelog = run(
        [
            sys.executable,
            "-m",
            "market_catalyst_calendar",
            "changelog",
            "--repo",
            str(repo),
            "--since-tag",
            "v0.1.0",
            "--format",
            "json",
        ]
    )
    if changelog.returncode != 0 or '"schema_version": "changelog/v1"' not in changelog.stdout or '"commit_count": 1' not in changelog.stdout:
        sys.stderr.write(changelog.stdout)
        sys.stderr.write(changelog.stderr)
        return changelog.returncode or 1
    changelog_markdown = run(
        [
            sys.executable,
            "-m",
            "market_catalyst_calendar",
            "changelog",
            "--repo",
            str(repo),
            "--since-tag",
            "v0.1.0",
        ]
    )
    if changelog_markdown.returncode != 0 or "# Release Notes" not in changelog_markdown.stdout:
        sys.stderr.write(changelog_markdown.stdout)
        sys.stderr.write(changelog_markdown.stderr)
        return changelog_markdown.returncode or 1
    return 0


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
        tmp_path = Path(tmp)
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
        validate_public = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "validate",
                "--profile",
                "public",
                "--input",
                str(demo_path),
                "--as-of",
                "2026-05-13",
            ]
        )
        if validate_public.returncode != 1 or '"MCC-QG-EVIDENCE-001"' not in validate_public.stdout:
            sys.stderr.write(validate_public.stdout)
            sys.stderr.write(validate_public.stderr)
            return validate_public.returncode or 1
        quality_gate = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "quality-gate",
                "--profile",
                "public",
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
        doctor = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "doctor",
                "--profile",
                "public",
                "--input",
                str(demo_path),
                "--as-of",
                "2026-05-13",
            ]
        )
        if doctor.returncode != 0 or '"schema_version": "doctor/v1"' not in doctor.stdout or '"modifies_input": false' not in doctor.stdout:
            sys.stderr.write(doctor.stdout)
            sys.stderr.write(doctor.stderr)
            return doctor.returncode or 1
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
        cookbook = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "command-cookbook",
                "--input",
                str(demo_path),
                "--as-of",
                "2026-05-13",
            ]
        )
        if cookbook.returncode != 0 or "# Market Catalyst Command Cookbook" not in cookbook.stdout:
            sys.stderr.write(cookbook.stdout)
            sys.stderr.write(cookbook.stderr)
            return cookbook.returncode or 1
        tutorial = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "tutorial",
                "--as-of",
                "2026-05-13",
                "--days",
                "45",
                "--dataset-path",
                "examples/demo_records.json",
            ]
        )
        if tutorial.returncode != 0 or "# Market Catalyst Calendar Tutorial" not in tutorial.stdout or "Learning checkpoint:" not in tutorial.stdout:
            sys.stderr.write(tutorial.stdout)
            sys.stderr.write(tutorial.stderr)
            return tutorial.returncode or 1
        drilldown = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "drilldown",
                "--input",
                str(demo_path),
                "--as-of",
                "2026-05-13",
                "--ticker",
                "NVDA",
                "--days",
                "45",
            ]
        )
        if drilldown.returncode != 0 or '"ticker": "NVDA"' not in drilldown.stdout or '"decision_logs"' not in drilldown.stdout:
            sys.stderr.write(drilldown.stdout)
            sys.stderr.write(drilldown.stderr)
            return drilldown.returncode or 1
        presets_path = Path(tmp) / "presets.json"
        preset_dir = Path(tmp) / "preset-packet"
        export_presets = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "export-preset-example",
                "--output",
                str(presets_path),
            ]
        )
        if export_presets.returncode != 0:
            sys.stderr.write(export_presets.stdout)
            sys.stderr.write(export_presets.stderr)
            return export_presets.returncode
        preset_run = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "run-preset",
                "--presets",
                str(presets_path),
                "--name",
                "desk-packet",
                "--input",
                str(demo_path),
                "--as-of",
                "2026-05-13",
                "--output-dir",
                str(preset_dir),
            ]
        )
        required_preset_files = [
            preset_dir / "manifest.json",
            preset_dir / "quality_gate.json",
            preset_dir / "upcoming.json",
            preset_dir / "agent_handoff.json",
        ]
        missing_preset_files = [path.relative_to(preset_dir).as_posix() for path in required_preset_files if not path.is_file()]
        if preset_run.returncode != 0 or '"schema_version": "preset-run/v1"' not in preset_run.stdout or missing_preset_files:
            sys.stderr.write(preset_run.stdout)
            sys.stderr.write(preset_run.stderr)
            if missing_preset_files:
                sys.stderr.write("preset run missing files: " + ", ".join(missing_preset_files) + "\n")
            return preset_run.returncode or 1
        taxonomy = run([sys.executable, "-m", "market_catalyst_calendar", "taxonomy"])
        if taxonomy.returncode != 0 or '"schema_version": "taxonomy/v1"' not in taxonomy.stdout or '"quality_rules"' not in taxonomy.stdout:
            sys.stderr.write(taxonomy.stdout)
            sys.stderr.write(taxonomy.stderr)
            return taxonomy.returncode or 1
        site_dir = Path(tmp) / "site"
        static_site = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "static-site",
                "--input",
                str(demo_path),
                "--output-dir",
                str(site_dir),
                "--as-of",
                "2026-05-13",
                "--days",
                "45",
            ]
        )
        required_site_files = [
            site_dir / "index.html",
            site_dir / "dashboard.html",
            site_dir / "sources.html",
            site_dir / "style.css",
            site_dir / "manifest.json",
            site_dir / "tickers" / "nvda.html",
        ]
        missing_site_files = [path.relative_to(site_dir).as_posix() for path in required_site_files if not path.is_file()]
        if static_site.returncode != 0 or missing_site_files:
            sys.stderr.write(static_site.stdout)
            sys.stderr.write(static_site.stderr)
            if missing_site_files:
                sys.stderr.write("static site missing files: " + ", ".join(missing_site_files) + "\n")
            return static_site.returncode or 1
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
            bundle_dir / "examples" / "doctor.json",
            bundle_dir / "examples" / "doctor.md",
            bundle_dir / "examples" / "doctor_patch.json",
            bundle_dir / "examples" / "command_cookbook.md",
            bundle_dir / "examples" / "agent_handoff.json",
            bundle_dir / "examples" / "agent_handoff.md",
            bundle_dir / "examples" / "fixture_gallery.json",
            bundle_dir / "examples" / "fixture_gallery.md",
            bundle_dir / "examples" / "finalize_release.json",
            bundle_dir / "examples" / "finalize_release.md",
            bundle_dir / "examples" / "drilldown.json",
            bundle_dir / "examples" / "drilldown.md",
            bundle_dir / "examples" / "tutorial.md",
            bundle_dir / "examples" / "dashboard.html",
        ]
        missing_bundle_files = [path.relative_to(bundle_dir).as_posix() for path in required_bundle_files if not path.is_file()]
        if missing_bundle_files:
            sys.stderr.write("demo bundle missing files: " + ", ".join(missing_bundle_files) + "\n")
            return 1
        fixture_gallery = run([sys.executable, "-m", "market_catalyst_calendar", "fixture-gallery"])
        if fixture_gallery.returncode != 0 or '"schema_version": "fixture-gallery/v1"' not in fixture_gallery.stdout:
            sys.stderr.write(fixture_gallery.stdout)
            sys.stderr.write(fixture_gallery.stderr)
            return fixture_gallery.returncode or 1
        smoke_matrix = run([sys.executable, "-m", "market_catalyst_calendar", "smoke-matrix"])
        if smoke_matrix.returncode != 0 or '"schema_version": "smoke-matrix/v1"' not in smoke_matrix.stdout or '"ok": true' not in smoke_matrix.stdout:
            sys.stderr.write(smoke_matrix.stdout)
            sys.stderr.write(smoke_matrix.stderr)
            return smoke_matrix.returncode or 1
        documented_result = validate_documented_examples()
        if documented_result != 0:
            return documented_result
        release_audit = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "release-audit",
                "--root",
                str(ROOT),
            ]
        )
        if release_audit.returncode != 0 or '"ok": true' not in release_audit.stdout:
            sys.stderr.write(release_audit.stdout)
            sys.stderr.write(release_audit.stderr)
            return release_audit.returncode or 1
        changelog_result = check_changelog_command(tmp_path)
        if changelog_result != 0:
            return changelog_result
        finalize_release = run(
            [
                sys.executable,
                "-m",
                "market_catalyst_calendar",
                "finalize-release",
                "--root",
                str(ROOT),
                "--repo",
                str(tmp_path / "changelog-repo"),
                "--since-tag",
                "v0.1.0",
            ]
        )
        if finalize_release.returncode != 0 or '"schema_version": "finalize-release/v1"' not in finalize_release.stdout or '"ok": true' not in finalize_release.stdout:
            sys.stderr.write(finalize_release.stdout)
            sys.stderr.write(finalize_release.stderr)
            return finalize_release.returncode or 1
    print("selfcheck ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
