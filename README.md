# Market Catalyst Calendar

`market-catalyst-calendar` is a stdlib-only Python CLI for maintaining source-attributed market catalyst records: earnings, product launches, regulatory decisions, macro releases, and other events that can change an investment thesis.

The v0.1 MVP is designed for offline agent and analyst workflows. It validates catalyst records, applies public research quality gates, suggests read-only repair plans with a dataset doctor, ranks upcoming events with finance-specific scoring, flags stale review items, audits evidence freshness and source diversity, aggregates portfolio exposure and event risk budgets, maps catalysts by sector/theme and investment thesis, reports supported taxonomy values and diagnostic codes, summarizes broker views, exports source packs, converts catalysts into prioritized watchlists, emits decision memo stubs, renders single-ticker drilldown dossiers, creates downstream research-agent handoff packs, executes named preset report packets from JSON config, compares and merges dataset snapshots, queues post-event outcome reviews, renders Markdown briefs, a static HTML dashboard, and a multi-page static site, exports calendar and CSV files, exports deterministic demo datasets and demo bundles, lists fixture hashes and provenance, and packages portable archives with hash verification.

## Install

```bash
python -m pip install .
```

No runtime dependencies are required beyond the Python standard library.

## Commands

```bash
python -m market_catalyst_calendar export-demo --output examples/demo_records.json
python -m market_catalyst_calendar validate --profile basic --input examples/demo_records.json
python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar stale --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar brief --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar sector-map --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar sector-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar validate --profile public --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar quality-gate --profile strict --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar doctor --profile public --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar doctor --profile public --input examples/demo_records.json --as-of 2026-05-13 --format patch
python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format csv
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45
python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45 --format markdown
python -m market_catalyst_calendar command-cookbook --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar tutorial --as-of 2026-05-13 --days 45 --dataset-path examples/demo_records.json
python -m market_catalyst_calendar agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar export-preset-example --output examples/presets.json
python -m market_catalyst_calendar run-preset --presets examples/presets.json --name desk-packet
python -m market_catalyst_calendar taxonomy
python -m market_catalyst_calendar taxonomy --format markdown
python -m market_catalyst_calendar fixture-gallery
python -m market_catalyst_calendar fixture-gallery --format markdown
python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-06-25
python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-06-25 --format markdown
python -m market_catalyst_calendar export-demo --snapshot updated --output examples/demo_records_updated.json
python -m market_catalyst_calendar demo-bundle --output-dir demo-bundle
python -m market_catalyst_calendar compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27
python -m market_catalyst_calendar compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 --format markdown
python -m market_catalyst_calendar merge examples/demo_records.json examples/demo_records_updated.json --as-of 2026-05-27 --output examples/merge.json
python -m market_catalyst_calendar html-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output examples/dashboard.html
python -m market_catalyst_calendar static-site --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output-dir site
python -m market_catalyst_calendar export-csv --input examples/demo_records.json --output examples/demo_records.csv
python -m market_catalyst_calendar export-ics --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output examples/upcoming.ics
python -m market_catalyst_calendar import-csv --input examples/demo_records.csv --output examples/imported_demo_records.json
python -m market_catalyst_calendar create-archive --input examples/demo_records.json --output-dir archive/demo --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar verify-archive archive/demo
python -m market_catalyst_calendar release-audit --root . --format markdown
python -m market_catalyst_calendar changelog --since-tag v0.1.0 --format markdown
python -m market_catalyst_calendar smoke-matrix --format markdown
python -m market_catalyst_calendar finalize-release --root . --repo . --since-tag v0.1.0 --format markdown
```

The installed script exposes the same interface:

```bash
market-catalyst-calendar brief --input examples/demo_records.json --as-of 2026-05-13
```

## Record Shape

Each record includes:

- `ticker` and `entity`
- `event_type`
- `date` or `window`
- `confidence`
- `status` and `history`
- `thesis_impact`
- `evidence_urls`
- `scenario_notes` for bull, base, and bear cases
- `required_review_action`
- `last_reviewed`
- optional `evidence_checked_at`
- optional `position_size` and `portfolio_weight`
- optional `risk_budget` and `max_loss`
- optional `sector` and `theme`
- optional `thesis_id` and `source_ref`
- optional `broker_views`, each with `institution`, `rating`, `target_price`, `as_of`, `source_url`, and `caveat`
- optional `actual_outcome` and `outcome_recorded_at`

Validation checks schema shape, URL quality, scenario completeness, status/history consistency, confidence ranges, and review-action hygiene for open items.

`portfolio_weight` is a decimal fraction from `0` to `1`, so `0.05` means 5% of the portfolio. `position_size`, `risk_budget`, and `max_loss` are non-negative notional values in the user's own reporting currency. All four fields are optional, which allows catalyst records to exist before a portfolio or risk view is attached.

`evidence_checked_at` is separate from `last_reviewed`: use it for the date sources were last checked, even when the thesis notes or status did not change.

`broker_views` are record-level analyst or broker snapshots. They are optional and offline: the CLI validates their source URLs and dates, but it does not fetch reports or infer missing target prices.

## Preset Workflow

`run-preset` executes a named workflow packet from a presets JSON file. Defaults can set `days`, `stale_after_days`, `profile`, and `output_dir`; each preset can override those values and list the workflows to write. The command writes deterministic artifacts plus `manifest.json` into the selected output directory and prints the same manifest to stdout.

```bash
python -m market_catalyst_calendar export-preset-example --output examples/presets.json
python -m market_catalyst_calendar run-preset --presets examples/presets.json --name desk-packet
```

Supported preset workflow ids include `validate`, `quality-gate`, `upcoming`, `stale`, `brief`, `exposure`, `risk-budget`, `sector-map`, `review-plan`, `thesis-map`, `scenario-matrix`, `evidence-audit`, `broker-matrix`, `source-pack`, `watchlist`, `decision-log`, `agent-handoff`, and `html-dashboard`, with `*-markdown`, `source-pack-csv`, and `source-pack-markdown` variants where applicable. Report failures such as a failing public quality gate are captured in the manifest artifact `exit_code` and do not prevent the packet from being generated.

`sector` and `theme` are optional taxonomy fields. Use `sector` for the broad business or macro bucket and `theme` for the cross-cutting catalyst exposure, such as AI infrastructure, pipeline reset, or rates duration.

`actual_outcome` and `outcome_recorded_at` are optional post-event fields. Use them after the catalyst window closes to capture what actually happened and when that outcome was recorded. `outcome_recorded_at` cannot be after dataset `as_of`, cannot be before the event window starts, and requires `actual_outcome`.

## Exposure Workflow

`exposure` filters to upcoming open catalysts in the requested look-ahead window, groups them by `ticker`, `event_type`, and scored `urgency`, then reports aggregate exposure in JSON or Markdown.

Weighted exposure adjusts each record's portfolio weight and notional position by both confidence and catalyst score:

```text
weighted exposure = portfolio_weight * confidence * catalyst_score / 100
weighted position exposure = position_size * confidence * catalyst_score / 100
```

This keeps low-confidence or low-priority catalysts visible while preventing them from counting the same as high-confidence near-term events.

## Risk Budget Workflow

`risk-budget` filters to upcoming open catalysts in the requested look-ahead window, groups records by `ticker`, `thesis_id`, and scored `urgency`, then compares `max_loss` estimates with explicit `risk_budget` limits.

JSON and Markdown outputs include:

- group-level budget, max loss, score/confidence-adjusted expected event loss, budget utilization, and remaining budget
- record-level catalyst score, confidence, budget, max loss, expected event loss, and flags
- `over_budget` flags when `max_loss` exceeds `risk_budget`
- `missing_budget` or `missing_max_loss` flags when only one side of the risk pair is present

Expected event loss is a prioritization metric:

```text
expected event loss = max_loss * confidence * catalyst_score / 100
```

Use `risk-budget` before high-urgency events to find catalysts whose stated downside exceeds the allowed risk budget.

## Taxonomy Workflow

`taxonomy` reports the supported offline vocabulary and command surface in JSON or Markdown. It includes event types, statuses, thesis impact values, required review actions, required scenarios, quality profiles, quality rules, validation and quality-gate diagnostic codes, every CLI command, and the subset of commands that can write artifacts with `--output`, `--output-dir`, or directory-producing behavior.

Use it when building downstream agents, docs, or fixtures that need stable enum values and diagnostic-code mappings without importing internal modules:

```bash
python -m market_catalyst_calendar taxonomy
python -m market_catalyst_calendar taxonomy --format markdown
```

## Sector Map Workflow

`sector-map` groups records with `sector` or `theme` context and reports which sector/theme clusters combine catalyst exposure, urgency, stale evidence, and broker-view dispersion.

JSON and Markdown outputs include:

- sector, theme, open record count, highest catalyst score, urgency/review-state counts, and linked tickers
- aggregate portfolio weight, notional position, and confidence/score-weighted exposure for open records
- stale or missing evidence freshness counts using `--stale-after-days`
- broker view count plus maximum and average target-price dispersion within the group
- per-record flags for stale or missing evidence, high urgency, stale review, and broker dispersion

Use it when sector or thematic concentration matters more than single-name ordering, especially before refreshing a research packet or risk review.

## Review Plan Workflow

`review-plan` creates a deterministic checklist for records that need analyst attention. It selects any open record that is stale after `--stale-after-days` plus any open upcoming record scored as `high` urgency within `--days`.

JSON and Markdown outputs include, per record:

- selection reasons (`stale`, `high_urgency_upcoming`, or both)
- catalyst score, urgency, review state, days until, and stale days when applicable
- next action derived from the required review action and urgency/staleness
- evidence gap prompt that calls out missing, stale, or unverified support
- scenario update prompt for refreshing bull/base/bear cases

Use JSON when feeding another agent or script, and Markdown when running an analyst review checklist.

## Thesis Map Workflow

`thesis-map` groups catalyst records that include `thesis_id`. It reports each thesis's total records, open event count, highest catalyst score, stale open record count, source-linked record ids, and evidence references gathered from `source_ref` plus `evidence_urls`.

Use it when you need to see whether a thesis is supported by current upcoming events or has stale evidence before changing portfolio positioning. Records without `thesis_id` remain valid but are excluded from the thesis map.

## Scenario Matrix Workflow

`scenario-matrix` filters to upcoming open catalysts in the requested look-ahead window, then renders every record as bull, base, and bear event scenarios. JSON and Markdown outputs include each scenario's score, event date, directional impact, review action, and scenario note.

Scenario scores start from the deterministic catalyst score and apply a small bull/base/bear adjustment based on thesis impact and confidence. Date windows are expanded into scenario-specific dates: bull uses the start of the window, base keeps the full window, and bear uses the end of the window. Review actions preserve the record's required action and add scenario/staleness context where needed, which makes the matrix suitable for analyst review queues or downstream agents.

## Evidence Audit Workflow

`evidence-audit` flags records whose evidence metadata needs attention. It does not fetch the web; it audits the dataset fields offline.

The JSON and Markdown reports include records with any of these flags:

- `missing_evidence_checked_at`: no evidence freshness timestamp is present
- `stale_evidence_metadata`: `evidence_checked_at` is older than `--fresh-after-days`
- `thin_source_count`: fewer than `--min-sources` evidence URLs are present
- `source_concentration`: one source domain exceeds `--max-domain-share`

Defaults are `--fresh-after-days 14`, `--min-sources 2`, and `--max-domain-share 0.67`. Use Markdown for analyst review and JSON for downstream automation.

## Quality Gate Workflow

`validate` and `quality-gate` both support `--profile basic|public|strict`. `validate` defaults to `basic` for structural checks, while `quality-gate` defaults to `public` for publication readiness. `public` matches the checked-in release gate; `strict` tightens freshness windows, requires three evidence URLs, requires broker coverage, and requires release metadata fields (`sector`, `theme`, `thesis_id`, and `source_ref`). Both profile-aware commands emit stable diagnostic codes such as `MCC-QG-EVIDENCE-001` for downstream automation.

`quality-gate` applies stricter product rules for datasets intended to be used as public research inputs. It is offline and deterministic, but unlike basic `validate` it exits with status `1` when any record fails the selected gate.

The JSON and Markdown reports include only failing records and cover:

- `minimum_evidence`: at least `--min-evidence-urls` URLs plus fresh `evidence_checked_at`
- `scenario_completeness`: substantive bull, base, and bear notes
- `review_freshness`: `last_reviewed` within `--max-review-age-days`
- `no_placeholder_urls`: no `example.*`, `.example`, localhost, sample, dummy, TODO, or TBD URLs in evidence or broker sources
- `broker_caveats`: broker views have substantive caveats and are no older than `--max-broker-age-days`

Profile defaults are one evidence URL for `basic`; two evidence URLs, 14 days for review/evidence freshness, and 30 days for broker views for `public`; and three evidence URLs, 7 days for review/evidence freshness, 14 days for broker views, broker coverage, and release metadata for `strict`. The numeric thresholds can still be overridden with `--min-evidence-urls`, `--max-review-age-days`, `--max-evidence-age-days`, and `--max-broker-age-days`.

## Doctor Workflow

`doctor` is a read-only dataset repair planner. It runs structural validation plus the selected quality profile, then suggests deterministic repairs for issues such as missing evidence URLs, invalid or placeholder URLs, stale freshness metadata, missing scenario notes, stale reviews, thin broker caveats, missing strict metadata, and outcome-field mismatches.

The command never modifies the input file. Use JSON for full diagnostics and Markdown for analyst review. Use `--format patch` when you only want the JSON Patch-style operation list to apply to a copy of the dataset after reviewing replacement URLs and shell values.

## Broker Matrix Workflow

`broker-matrix` groups optional `broker_views` by `ticker` and `thesis_id` and reports target-price dispersion, rating counts, stale source flags, and linked catalyst records.

The JSON and Markdown reports include:

- target price minimum, maximum, average, and dispersion
- rating counts across institutions
- stale broker sources older than `--stale-after-days` (default `30`)
- linked catalyst id, event type, window, status, urgency, review state, and catalyst score
- per-view source URL and caveat text

Use it to compare outside sell-side assumptions against catalyst timing without turning broker targets into investment advice.

## Source Pack Workflow

`source-pack` exports a deduplicated inventory of every evidence URL and broker source URL in the dataset. It does not fetch sources; it preserves the dataset's source links with enough context for handoff, audit, or downstream collection.

JSON, CSV, and Markdown outputs include:

- unique URL and source type (`evidence`, `broker`, or both)
- usage count across records and broker views
- linked tickers, thesis ids, and catalyst record ids
- latest freshness date from `evidence_checked_at` or broker `as_of`
- freshness age and state using `--fresh-after-days` (default `14`)
- broker institutions and broker source dates when applicable

Use JSON for automation, CSV for external source-collection work, and Markdown for analyst review packets.

## Release Audit Workflow

`release-audit` runs the offline release checks that keep the repository self-contained. It compares checked-in files under `examples/` with regenerated deterministic demo outputs, confirms the agent skill exists, checks that this README mentions the required commands, checks that `docs/SCHEMA.md` documents release-audit output fields, and fails if files exist under `.github/workflows`.

The command emits JSON by default and Markdown with `--format markdown`. It exits `0` when every check passes and `1` when any release artifact is missing, stale, undocumented, or backed by a workflow file.

## Changelog Workflow

`changelog` summarizes local git commits after a tag into deterministic release notes without network calls. It shells out only to the local `git` executable, reads tags and commits from `--repo`, excludes merge commits by default, and writes Markdown by default or JSON with `--format json`.

Use `--since-tag` to name the excluded starting tag, `--to-ref` to choose the included ending ref (default `HEAD`), and `--include-merges` when merge commits should appear. The JSON output groups commits by conventional-commit type, extracts scopes, breaking-change markers, and `#123` references, and includes the exact from/to SHAs plus tags reachable in the range.

## Smoke Matrix Workflow

`smoke-matrix` runs an internal offline smoke check for every CLI command against deterministic demo data. It creates a temporary demo workspace, executes stdout and file-writing commands, accepts expected nonzero exits such as the public `quality-gate` failure, verifies expected output files, and includes a probe check for `smoke-matrix` itself without recursively running the full matrix.

The JSON and Markdown reports include pass/fail status, actual and expected exit codes, expected files, and coarse duration buckets such as `lt_250ms`, `lt_1s`, `lt_5s`, and `gte_5s`. Only bucket labels are reported, so output remains stable enough for automated checks while still surfacing slow smoke cases.

## Finalize Release Workflow

`finalize-release` runs `release-audit`, `smoke-matrix`, `fixture-gallery`, and `changelog`, then normalizes their results into one deterministic release checklist. Use it as the final local handoff artifact before tagging or publishing.

Provide `--since-tag` for the excluded starting tag. The command emits JSON by default, Markdown with `--format markdown`, and exits `1` if any release audit check, smoke command, fixture index, or changelog requirement blocks the release.

## Watchlist Workflow

`watchlist` converts open catalysts into prioritized watch items for a forward window. It keeps the original catalyst links intact while adding workflow fields an analyst or downstream agent can act on.

JSON and Markdown outputs include:

- watch id, catalyst id, ticker, entity, event type, status, and event window
- priority score and band derived from catalyst score, urgency, stale state, exposure, and required action
- trigger conditions for review due dates, event window changes, stale review, source checks, thesis changes, and exposure changes
- due date, due state, and review cadence
- `thesis_id`, `source_ref`, source refs, evidence URLs, and bull/base/bear scenario refs

Use Markdown for a human watch queue and JSON when passing watch items into another offline agent or ticketing script.

## Decision Log Workflow

`decision-log` emits deterministic decision memo stubs for open catalysts in the requested forward window. It is designed for pre-event decision capture and post-event review without inventing conclusions.

JSON and Markdown outputs include, per catalyst:

- thesis context with `thesis_id`, current impact, working thesis, and decision question
- catalyst status, confidence, score, urgency, review state, and required action
- source reference, evidence freshness date, last review date, and evidence URLs
- bull/base/bear scenarios with scenario score, date, impact, review action, and note
- broker context with per-view caveats, stale flags, and target-price range when `broker_views` are present
- watchlist triggers reused from the watchlist workflow
- blank decision slots and post-event review slots marked `TBD`

Use Markdown when maintaining an analyst decision journal, and JSON when passing memo stubs to another offline process.

## Ticker Drilldown Workflow

`drilldown --ticker` renders a complete single-ticker dossier by filtering the dataset to one symbol and composing the existing analyst reports into one JSON or Markdown packet.

The dossier includes:

- a ticker record ledger and upcoming event section
- thesis map, broker matrix, and risk-budget context for the selected ticker
- watchlist items and decision-log memo stubs for open catalysts in the forward window
- post-event outcome queue for completed or overdue events
- deduplicated source pack for evidence and broker URLs

Use JSON when handing the dossier to another offline process, and Markdown when preparing a single-name research packet. The command is deterministic and offline; it does not fetch sources or infer missing evidence.

## Command Cookbook Workflow

`command-cookbook` renders a deterministic Markdown analyst playbook from the dataset. It profiles available fields, selects the relevant report sequences, and writes step-by-step shell commands with expected output files.

The cookbook always includes validation, quality-gate, evidence audit, core briefing, source-pack, and portable export sections. It conditionally adds:

- exposure commands when `portfolio_weight` or `position_size` is present
- risk-budget commands when `risk_budget` or `max_loss` is present
- sector/theme commands when `sector` or `theme` is present
- thesis, watchlist, and decision-log commands when `thesis_id` or `source_ref` is present
- broker-matrix commands when `broker_views` is present
- scenario-matrix commands when complete bull/base/bear scenario notes are present
- post-event closeout commands when a catalyst is completed, past its event window, or has outcome metadata

Use `--dataset-path` and `--output-dir` to control the paths shown in the generated command blocks without changing the input file being read.

## Tutorial Workflow

`tutorial` renders a notebooks-free Markdown walkthrough from the built-in demo data. It shows a shell-first learning path with expected command output excerpts, expected exit codes, and learning checkpoints for export, validation, upcoming catalysts, quality gates, risk budget, source pack, drilldown, and snapshot compare.

Use `--dataset-path` to control the path shown in commands, `--as-of` and `--days` to control report excerpts, and `--output` to write the tutorial to a Markdown file.

## Agent Handoff Workflow

`agent-handoff` creates a compact context pack for a downstream investment research agent. It is deterministic and offline: it summarizes the dataset, ranks top risks, lists stale items, preserves source URLs, and emits commands the next agent should run.

JSON and Markdown outputs include:

- `dataset_summary` with record counts, open/upcoming counts, stale review and evidence counts, source URL count, broker view count, status/event/urgency counts, tickers, and thesis ids
- `top_risks` ranked by catalyst score plus over-budget, stale evidence, stale review, missing freshness, and required-action flags
- `stale_items` with review age, evidence age, required action, and evidence URLs
- `commands_to_run_next` for validation, quality gate, source pack, review plan, decision log, and priority ticker drilldowns
- `source_urls` with evidence/broker type, linked tickers, record ids, thesis ids, freshness state, latest checked date, and broker institutions

Use JSON when handing work to another agent or script, and Markdown when attaching context to a human review note. Use `--dataset-path` and `--output-dir` to control generated command paths without changing the input file being read.

## Post-Event Workflow

`post-event` lists catalysts that need outcome review after the event window has passed. It selects non-cancelled records whose `actual_outcome` or `outcome_recorded_at` is still missing when the record is already `completed` or when the review due date has passed. The review due date is the event window end plus `--review-after-days` (default `0`).

JSON and Markdown outputs include, per catalyst:

- event status, window, score, review due date, and days since the window ended
- outcome state and recorded-at state
- existing `actual_outcome` and `outcome_recorded_at` values when present, otherwise `TBD`
- thesis id, base scenario, source reference, and evidence URLs
- an outcome review template with slots for actual outcome, scenario accuracy, thesis impact after event, evidence delta, position or risk action, follow-up action, and source update need

Use it after events occur to close the loop between pre-event scenarios and what actually happened without inventing conclusions.

## Compare Snapshots Workflow

`compare` reads an older `--base` dataset and a newer `--current` dataset, matches records by stable `id`, scores both snapshots with the same `--as-of`, and reports what changed in JSON or Markdown.

The report includes:

- added and removed catalyst events
- changed events with score deltas, urgency/review-state changes, and field changes
- status transitions such as `watching -> completed`
- evidence URL additions/removals plus `evidence_checked_at` changes
- thesis-impact changes such as `mixed -> positive`
- scenario-note, history entry, and broker-view changes

Use it when reviewing a refreshed research packet or checking what changed between archived datasets. `create-archive` remains a single-snapshot package; run `compare` separately when you have both the old and current dataset files.

## Merge Workflow

`merge` reads two or more catalyst datasets, combines records by stable `id`, and writes a reusable JSON dataset. The output keeps a top-level `merge` diagnostic block with input source labels, per-record provenance, conflict fields, chosen source, status/history source, duplicate-ID diagnostics, and validation results.

Conflict resolution is deterministic: by default, the record from the newest dataset `as_of` wins, with later input order as a tie-breaker. `--prefer-newer-status-history` keeps that record-level winner for other fields but takes `status` and `history` from the candidate with the newest history entry. The command exits `1` if the merged dataset fails validation, while still printing JSON diagnostics.

## HTML Dashboard Workflow

`html-dashboard` renders a deterministic, no-JavaScript HTML file for offline review. It safely escapes dataset text before writing it into the document.

The dashboard includes:

- score tables for upcoming catalysts
- exposure summary cards and grouped exposure rows
- risk-budget breach table
- sector map
- thesis map
- evidence audit
- bull/base/bear scenario matrix
- prioritized watchlist

Use `--output` to write a portable `.html` artifact, or omit it to stream the HTML to stdout.

## Static Site Workflow

`static-site` writes a deterministic, no-JavaScript site directory from one dataset. It requires an empty `--output-dir` and prints a JSON summary with the site directory, index path, manifest path, and file count.

The site includes:

- `index.html` with summary cards, ticker links, and upcoming catalysts
- `dashboard.html` with the full static dashboard report
- `sources.html` with a deduplicated evidence and broker source inventory
- one `tickers/<ticker>.html` page per ticker with record ledger, scenarios, broker views, and evidence links
- `style.css` and `manifest.json` with relative paths, byte counts, and SHA-256 hashes

Use it when an analyst or downstream agent needs a small browsable packet instead of one long HTML file.

## CSV Workflow

`export-csv` writes the full catalyst dataset to a deterministic spreadsheet-friendly CSV. Rows are sorted by event window, ticker, and id; columns are stable; optional `sector`, `theme`, `thesis_id`, and `source_ref` are preserved; and `confidence` is formatted without unnecessary trailing noise.

`import-csv` reads that CSV back into the same JSON dataset shape used by `validate`, `upcoming`, `stale`, and `brief`. The CSV includes `window_start` and `window_end`; equal values import as a single `date`, while different values import as a `window`.

Multi-value cells use safe encoded separators:

- `evidence_urls`: URL-encoded values joined by ` | `
- `scenario_notes`: URL-encoded `key = value` pairs joined by ` | `
- `history`: URL-encoded `date = status = note` entries joined by ` | `
- `broker_views`: URL-encoded `institution = rating = target_price = as_of = source_url = caveat` entries joined by ` | `

Because each component is percent-encoded before joining, commas, newlines, pipes, equals signs, and URL query strings survive a CSV round trip.

## Calendar Workflow

`export-ics` writes upcoming open catalysts in the requested look-ahead window to a deterministic iCalendar 2.0 file. Events are all-day entries sorted by event window, ticker, and id. Date windows use inclusive catalyst dates in the source data and the iCalendar-standard exclusive `DTEND`, so a `2026-05-20..2026-05-24` catalyst exports as `DTSTART;VALUE=DATE:20260520` and `DTEND;VALUE=DATE:20260525`.

Each event includes a stable UID derived from the catalyst id and event window, deterministic `DTSTAMP` based on `--as-of`, escaped `SUMMARY` and `DESCRIPTION` text, categories for ticker/event/status/impact/urgency/thesis, and source notes with evidence URLs. The first evidence URL is also emitted as the event `URL`.

## Archive Workflow

`create-archive` writes a portable directory for handoff, review, or offline retention. The output directory must be empty. The archive contains:

- `dataset/dataset.json`: canonical JSON copy of the input dataset
- `dataset/dataset.csv`: deterministic CSV export for spreadsheet review
- `reports/upcoming.json` and `reports/stale.json`
- `reports/upcoming.ics`
- `reports/brief.md`
- `reports/broker_matrix.json` and `reports/broker_matrix.md`
- `reports/source_pack.json`, `reports/source_pack.csv`, and `reports/source_pack.md`
- `reports/watchlist.json` and `reports/watchlist.md`
- `reports/decision_log.json` and `reports/decision_log.md`
- `reports/command_cookbook.md`
- `reports/post_event.json` and `reports/post_event.md`
- `reports/dashboard.html`
- `reports/exposure.json` and `reports/exposure.md`
- `reports/risk_budget.json` and `reports/risk_budget.md`
- `reports/sector_map.json` and `reports/sector_map.md`
- `reports/review_plan.json` and `reports/review_plan.md`
- `reports/scenario_matrix.json` and `reports/scenario_matrix.md`
- `reports/thesis_map.json` and `reports/thesis_map.md`
- `reports/evidence_audit.json` and `reports/evidence_audit.md`
- `manifest.json`: archive metadata plus byte counts and SHA-256 hashes for every archived file

`verify-archive` reads `manifest.json`, recomputes hashes and byte counts, and fails if any archived file is missing, changed, or untracked. This makes the directory portable without requiring a zip format or non-stdlib tooling.

## Demo Bundle Workflow

`demo-bundle` writes an empty output directory containing a complete deterministic demo packet generated from the built-in base and updated snapshots. It is meant for first-run evaluation, downstream agent fixtures, and offline review without relying on networked tools.

The bundle contains:

- `examples/`: every documented example output, including demo datasets, report JSON, Markdown reports, CSV, ICS, HTML dashboard, compare output, and merge output
- `README.md`: bundle-local quickstart and a command index for each generated example
- `quickstart-transcript.txt`: deterministic terminal transcript for validating, listing upcoming events, and observing the expected nonzero quality-gate result
- `manifest.json`: bundle metadata plus relative file paths, byte counts, SHA-256 hashes, command provenance, and expected exit codes

Unlike `create-archive`, which packages one caller-supplied dataset snapshot, `demo-bundle` always uses the built-in demo data and includes every example output in the same shape as the checked-in `examples/` fixtures.

## Fixture Gallery Workflow

`fixture-gallery` lists the bundled deterministic example fixtures with their command provenance, expected exit code, output type, byte count, SHA-256 hash, input fixture references, and recommended use cases. It emits JSON by default and Markdown with `--format markdown`.

Use it when choosing a regression fixture, auditing checked-in examples, or handing another agent a compact map of which fixture demonstrates which workflow.

## Scoring

The CLI is more than a JSON formatter. Each record receives a deterministic `catalyst_score` based on event type, status, thesis impact, proximity, confidence, evidence depth, and scenario-note depth. Review state is derived from status, required action, and stale review age.

## Examples

Checked-in examples live in `examples/`:

- `demo_records.json`: deterministic demo input
- `upcoming.json`: generated upcoming output
- `stale.json`: generated stale-review output
- `brief.md`: generated Markdown brief
- `exposure.json`: generated exposure aggregation
- `exposure.md`: generated Markdown exposure table
- `risk_budget.json`: generated event risk-budget aggregation
- `risk_budget.md`: generated Markdown risk-budget workflow
- `sector_map.json`: generated sector/theme map with exposure, stale evidence, and broker dispersion
- `sector_map.md`: generated Markdown sector-map workflow
- `review_plan.json`: generated review checklist data
- `review_plan.md`: generated Markdown review checklist
- `scenario_matrix.json`: generated bull/base/bear scenario matrix
- `scenario_matrix.md`: generated Markdown scenario matrix
- `evidence_audit.json`: generated evidence freshness and diversity audit
- `evidence_audit.md`: generated Markdown evidence audit
- `broker_matrix.json`: generated broker view dispersion and linkage matrix
- `broker_matrix.md`: generated Markdown broker matrix
- `source_pack.json`: generated unique evidence and broker source inventory
- `source_pack.csv`: generated CSV source inventory
- `source_pack.md`: generated Markdown source pack
- `watchlist.json`: generated prioritized watch item workflow
- `watchlist.md`: generated Markdown watchlist
- `decision_log.json`: generated decision memo stubs
- `decision_log.md`: generated Markdown decision log
- `drilldown.json`: generated complete single-ticker dossier
- `drilldown.md`: generated Markdown single-ticker dossier
- `command_cookbook.md`: generated field-aware analyst command cookbook
- `tutorial.md`: generated notebooks-free tutorial with command output excerpts and learning checkpoints
- `agent_handoff.json`: generated downstream research-agent context pack
- `agent_handoff.md`: generated Markdown research-agent handoff
- `fixture_gallery.json`: generated fixture index with hashes, provenance, output types, and use cases
- `fixture_gallery.md`: generated Markdown fixture gallery
- `post_event.json`: generated post-event outcome review queue
- `post_event.md`: generated Markdown post-event outcome review template
- `demo_records_updated.json`: deterministic second snapshot for compare examples
- `compare.json`: generated snapshot comparison data
- `compare.md`: generated Markdown snapshot comparison report
- `merge.json`: generated merged dataset with provenance, conflict diagnostics, and validation
- `dashboard.html`: generated static no-JavaScript HTML dashboard
- `thesis_map.json`: generated thesis grouping data
- `thesis_map.md`: generated Markdown thesis map
- `upcoming.ics`: generated iCalendar export for upcoming catalysts
- `demo_records.csv`: deterministic CSV export
- `imported_demo_records.json`: JSON imported back from CSV

Archive output is intentionally not checked in because it duplicates the generated examples. Use the commands above to create a fresh archive when needed.
Demo bundle output is also intentionally not checked in; regenerate it with `demo-bundle` when you need a portable tutorial packet.

## Selfcheck

```bash
python scripts/selfcheck.py
```

The selfcheck runs unit tests, exports demo data to a temporary directory, validates it, creates and verifies an archive, creates a demo bundle, checks the fixture gallery, runs the smoke matrix, and verifies deterministic command output against checked-in examples.

## Roadmap

- Per-sector event presets and scoring calibration
- Watchlist filters and portfolio exposure tags
- Evidence freshness checks using external fetchers kept outside the core stdlib package
- Optional thesis metadata catalogs while preserving record-level `thesis_id` links

## License

MIT
