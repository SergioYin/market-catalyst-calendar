# Example Fixtures

The files in this directory are deterministic fixtures generated from the built-in demo dataset. They are intentionally checked in so package users, downstream agents, and tests can inspect exact command output without running networked tools.

All examples use these stable dates:

- Dataset `as_of`: `2026-05-13`
- Updated snapshot `as_of`: `2026-05-27`
- Forward report window: `45` days unless the command says otherwise
- Post-event review date: `2026-06-25`

## Fixture Index

| Fixture | Command output | Purpose |
| --- | --- | --- |
| `demo_records.json` | `export-demo` | Canonical JSON input dataset with four records covering completed, stale, scheduled, and confirmed catalysts. |
| `presets.json` | preset config | Named preset workflow defaults for `days`, stale thresholds, quality profile, output directory, and report sequence. |
| `preset_run.json` | `run-preset` | Deterministic manifest from executing the `desk-packet` preset workflow packet. |
| `demo_records.csv` | `export-csv` | Spreadsheet-friendly dataset export with stable columns and encoded multi-value cells. |
| `imported_demo_records.json` | `import-csv` | JSON reconstructed from `demo_records.csv`; validates the CSV round trip. |
| `upcoming.json` | `upcoming` | Upcoming open catalysts in the 45-day window. |
| `stale.json` | `stale` | Records whose review state is stale as of the fixture date. |
| `brief.md` | `brief` | Human-readable Markdown brief for upcoming catalysts. |
| `exposure.json` | `exposure` | Portfolio-weight and notional exposure grouped by ticker, event type, and urgency. |
| `exposure.md` | `exposure --format markdown` | Markdown rendering of the exposure report. |
| `risk_budget.json` | `risk-budget` | Event risk grouped by ticker, thesis, and urgency with over-budget catalyst flags. |
| `risk_budget.md` | `risk-budget --format markdown` | Markdown rendering of the risk-budget workflow. |
| `sector_map.json` | `sector-map` | Sector/theme clusters with exposure, urgency, stale evidence, and broker dispersion. |
| `sector_map.md` | `sector-map --format markdown` | Markdown rendering of the sector-map workflow. |
| `review_plan.json` | `review-plan` | Machine-readable stale and high-urgency review checklist. |
| `review_plan.md` | `review-plan --format markdown` | Analyst checklist rendering of the review plan. |
| `thesis_map.json` | `thesis-map` | Catalyst grouping by `thesis_id`, including evidence references and stale counts. |
| `thesis_map.md` | `thesis-map --format markdown` | Markdown rendering of thesis coverage. |
| `scenario_matrix.json` | `scenario-matrix` | Bull/base/bear scenarios for upcoming catalysts. |
| `scenario_matrix.md` | `scenario-matrix --format markdown` | Markdown matrix of the same scenario set. |
| `evidence_audit.json` | `evidence-audit` | Evidence freshness, source-count, and source-concentration findings. |
| `evidence_audit.md` | `evidence-audit --format markdown` | Markdown audit packet for human review. |
| `quality_gate.json` | `quality-gate --profile public` | Public research dataset quality gate with fail/pass status, rule findings, and diagnostic codes. |
| `quality_gate.md` | `quality-gate --profile public --format markdown` | Markdown rendering of the same public research quality gate. |
| `doctor.json` | `doctor --profile public` | Read-only repair planner for validation and quality-gate failures, including diagnostics and suggested patch operations. |
| `doctor.md` | `doctor --profile public --format markdown` | Markdown repair checklist for analyst review. |
| `doctor_patch.json` | `doctor --profile public --format patch` | JSON Patch-style operation list only, for applying to a copy of the dataset. |
| `broker_matrix.json` | `broker-matrix` | Broker view dispersion, stale broker source flags, and linked catalysts. |
| `broker_matrix.md` | `broker-matrix --format markdown` | Markdown broker matrix and per-view details. |
| `source_pack.json` | `source-pack` | Deduplicated evidence and broker source inventory. |
| `source_pack.csv` | `source-pack --format csv` | CSV source inventory for external collection or review. |
| `source_pack.md` | `source-pack --format markdown` | Markdown source packet. |
| `watchlist.json` | `watchlist` | Prioritized watch items with due dates, cadence, triggers, and source refs. |
| `watchlist.md` | `watchlist --format markdown` | Markdown watch queue and trigger details. |
| `decision_log.json` | `decision-log` | Decision memo stubs for upcoming open catalysts. |
| `decision_log.md` | `decision-log --format markdown` | Markdown decision journal stubs. |
| `drilldown.json` | `drilldown --ticker NVDA` | Complete single-ticker dossier combining events, thesis, brokers, risk, watch items, source pack, post-event queue, and decision logs. |
| `drilldown.md` | `drilldown --ticker NVDA --format markdown` | Markdown rendering of the single-ticker drilldown dossier. |
| `command_cookbook.md` | `command-cookbook` | Field-aware Markdown command cookbook with selected report sequences and expected output files. |
| `tutorial.md` | `tutorial` | Notebooks-free Markdown tutorial with expected command output excerpts and learning checkpoints. |
| `agent_handoff.json` | `agent-handoff` | Machine-readable context pack for a downstream investment research agent with summary, risks, stale items, next commands, and source URLs. |
| `agent_handoff.md` | `agent-handoff --format markdown` | Analyst-readable rendering of the same research-agent handoff pack. |
| `taxonomy.json` | `taxonomy` | Machine-readable supported event types, statuses, review actions, quality rules, diagnostic codes, and command catalog. |
| `taxonomy.md` | `taxonomy --format markdown` | Analyst-readable rendering of the taxonomy and command catalog. |
| `fixture_gallery.json` | `fixture-gallery` | Machine-readable index of bundled fixtures with provenance, hashes, output types, and recommended use cases. |
| `fixture_gallery.md` | `fixture-gallery --format markdown` | Analyst-readable fixture gallery for selecting examples and regression fixtures. |
| `finalize_release.json` | `finalize-release --example` | Machine-readable release finalizer checklist combining audit, smoke, fixture, and changelog summaries. |
| `finalize_release.md` | `finalize-release --example --format markdown` | Markdown release checklist for final handoff review. |
| `post_event.json` | `post-event` | Outcome review queue after selected catalyst windows have passed. |
| `post_event.md` | `post-event --format markdown` | Markdown post-event review templates. |
| `demo_records_updated.json` | `export-demo --snapshot updated` | Second deterministic input dataset for snapshot comparison examples. |
| `compare.json` | `compare` | Machine-readable diff between the base and updated demo snapshots. |
| `compare.md` | `compare --format markdown` | Analyst-readable snapshot comparison report. |
| `merge.json` | `merge` | Merged base and updated demo datasets with provenance, conflicts, duplicate-ID diagnostics, and validation. |
| `dashboard.html` | `html-dashboard` | Static no-JavaScript dashboard for offline review. |
| `upcoming.ics` | `export-ics` | iCalendar export of upcoming catalysts. |

## Documented Commands

`scripts/selfcheck.py` executes the commands below and compares stdout with the fixture named by each `# fixture:` marker. Keep this block in sync when adding, removing, or regenerating examples.

```bash
# fixture: examples/demo_records.json
python -m market_catalyst_calendar export-demo
# fixture: examples/presets.json
python -m market_catalyst_calendar export-preset-example
# fixture: examples/preset_run.json
python -m market_catalyst_calendar run-preset --presets examples/presets.json --name desk-packet
# fixture: examples/upcoming.json
python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/stale.json
python -m market_catalyst_calendar stale --input examples/demo_records.json --as-of 2026-05-13
# fixture: examples/brief.md
python -m market_catalyst_calendar brief --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/exposure.json
python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/exposure.md
python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
# fixture: examples/risk_budget.json
python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/risk_budget.md
python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
# fixture: examples/sector_map.json
python -m market_catalyst_calendar sector-map --input examples/demo_records.json --as-of 2026-05-13
# fixture: examples/sector_map.md
python -m market_catalyst_calendar sector-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown
# fixture: examples/review_plan.json
python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/review_plan.md
python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
# fixture: examples/thesis_map.json
python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13
# fixture: examples/thesis_map.md
python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown
# fixture: examples/scenario_matrix.json
python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/scenario_matrix.md
python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
# fixture: examples/evidence_audit.json
python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13
# fixture: examples/evidence_audit.md
python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13 --format markdown
# fixture: examples/quality_gate.json
# exit-code: 1
python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13
# fixture: examples/quality_gate.md
# exit-code: 1
python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13 --format markdown
# fixture: examples/doctor.json
python -m market_catalyst_calendar doctor --profile public --input examples/demo_records.json --as-of 2026-05-13
# fixture: examples/doctor.md
python -m market_catalyst_calendar doctor --profile public --input examples/demo_records.json --as-of 2026-05-13 --format markdown
# fixture: examples/doctor_patch.json
python -m market_catalyst_calendar doctor --profile public --input examples/demo_records.json --as-of 2026-05-13 --format patch
# fixture: examples/broker_matrix.json
python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13
# fixture: examples/broker_matrix.md
python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13 --format markdown
# fixture: examples/source_pack.json
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13
# fixture: examples/source_pack.csv
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format csv
# fixture: examples/source_pack.md
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format markdown
# fixture: examples/watchlist.json
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/watchlist.md
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
# fixture: examples/decision_log.json
python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/decision_log.md
python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
# fixture: examples/drilldown.json
python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45
# fixture: examples/drilldown.md
python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45 --format markdown
# fixture: examples/command_cookbook.md
python -m market_catalyst_calendar command-cookbook --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/tutorial.md
python -m market_catalyst_calendar tutorial --as-of 2026-05-13 --days 45 --dataset-path examples/demo_records.json
# fixture: examples/agent_handoff.json
python -m market_catalyst_calendar agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/agent_handoff.md
python -m market_catalyst_calendar agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
# fixture: examples/taxonomy.json
python -m market_catalyst_calendar taxonomy
# fixture: examples/taxonomy.md
python -m market_catalyst_calendar taxonomy --format markdown
# fixture: examples/fixture_gallery.json
python -m market_catalyst_calendar fixture-gallery
# fixture: examples/fixture_gallery.md
python -m market_catalyst_calendar fixture-gallery --format markdown
# fixture: examples/finalize_release.json
python -m market_catalyst_calendar finalize-release --example
# fixture: examples/finalize_release.md
python -m market_catalyst_calendar finalize-release --example --format markdown
# fixture: examples/post_event.json
python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-06-25
# fixture: examples/post_event.md
python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-06-25 --format markdown
# fixture: examples/demo_records_updated.json
python -m market_catalyst_calendar export-demo --snapshot updated
# fixture: examples/compare.json
python -m market_catalyst_calendar compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27
# fixture: examples/compare.md
python -m market_catalyst_calendar compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 --format markdown
# fixture: examples/merge.json
python -m market_catalyst_calendar merge examples/demo_records.json examples/demo_records_updated.json --as-of 2026-05-27
# fixture: examples/dashboard.html
python -m market_catalyst_calendar html-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/demo_records.csv
python -m market_catalyst_calendar export-csv --input examples/demo_records.json
# fixture: examples/upcoming.ics
python -m market_catalyst_calendar export-ics --input examples/demo_records.json --as-of 2026-05-13 --days 45
# fixture: examples/imported_demo_records.json
python -m market_catalyst_calendar import-csv --input examples/demo_records.csv
```

Archive output is not checked in because it duplicates these generated files and includes a directory-specific manifest. Run `create-archive` when you need a portable handoff directory.

Static-site output is not checked in because it is a generated directory with ticker pages and a site-specific manifest. Run `python -m market_catalyst_calendar static-site --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output-dir site` when you need a browsable no-JavaScript packet.

Demo bundle output is also not checked in. Run `python -m market_catalyst_calendar demo-bundle --output-dir demo-bundle` when you need a deterministic tutorial directory containing every example output, a bundle README, a quickstart transcript, and a manifest with hashes and command provenance.
