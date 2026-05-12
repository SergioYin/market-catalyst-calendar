# Market Catalyst Calendar Agent Skill

## Triggers

Use this skill when a user wants to create, validate, rank, review, brief, or export a source-attributed market catalyst calendar for public equities, ETFs, macro instruments, or investment research workflows.

## Routing

- Use `python -m market_catalyst_calendar validate --profile basic` before trusting a dataset; use `--profile public` or `--profile strict` when the user needs release-grade diagnostics with stable codes.
- Use `upcoming` when the user asks what catalysts are in a forward window.
- Use `stale` when the user asks what needs review or evidence refresh.
- Use `brief` when the user wants a Markdown analyst-ready summary.
- Use `exposure` when the user asks which upcoming catalysts matter most to a portfolio or position book.
- Use `risk-budget` when the user asks whether catalyst max-loss estimates fit event risk budgets or wants over-budget catalysts grouped by ticker/thesis/urgency.
- Use `sector-map` when the user wants sector/theme clusters with exposure, urgency, stale evidence, and broker-dispersion context.
- Use `review-plan` when the user wants an actionable review checklist for stale records and high-urgency upcoming catalysts.
- Use `thesis-map` when the user wants catalysts grouped by investment thesis, with open event counts, stale counts, top score, and source references.
- Use `scenario-matrix` when the user wants bull/base/bear scenarios with scenario score, event date, impact, and review action.
- Use `evidence-audit` when the user wants evidence freshness, source count, or source concentration checks.
- Use `quality-gate --profile public` before publishing or handing off a public research dataset; use `--profile strict` for public release datasets that need three evidence URLs, 7-day review/evidence freshness, 14-day broker freshness, broker coverage, release metadata, and stable diagnostic codes.
- Use `doctor` when the user wants read-only repair suggestions for validation or quality-gate failures; use `--format patch` to emit only JSON Patch-style operations for review before applying to a copy.
- Use `broker-matrix` when the user wants broker or analyst views grouped by ticker/thesis with target-price dispersion, stale source flags, and linked catalysts.
- Use `source-pack` when the user wants a deduplicated evidence and broker source URL inventory with tickers, thesis ids, usage counts, freshness, and JSON/CSV/Markdown output.
- Use `watchlist` when the user wants catalysts converted into prioritized watch items with trigger conditions, due dates, review cadence, and thesis/source references.
- Use `decision-log` when the user wants deterministic catalyst decision memo stubs with thesis, catalyst, evidence, scenarios, broker context, watchlist triggers, decision slots, and post-event review slots.
- Use `drilldown --ticker` when the user wants a complete single-ticker dossier combining upcoming events, thesis map, broker matrix, risk budget, watchlist, post-event queue, source pack, and decision logs.
- Use `command-cookbook` when the user wants a deterministic analyst playbook of command sequences chosen from the dataset's available fields, with expected output files.
- Use `tutorial` when the user wants a notebooks-free Markdown walkthrough generated from demo data with expected command output excerpts and learning checkpoints.
- Use `agent-handoff` when the user wants a compact JSON or Markdown context pack for a downstream investment research agent, including dataset summary, top risks, stale items, commands to run next, and source URLs.
- Use `export-preset-example` to create a starter presets JSON file with default `days`, `stale_after_days`, `profile`, `output_dir`, and a named workflow list.
- Use `run-preset` when the user wants a named JSON-configured workflow packet generated deterministically into an output directory with a manifest.
- Use `taxonomy` when the user wants supported event types, statuses, review actions, quality rules, diagnostic codes, output-producing commands, or a complete command catalog in JSON or Markdown.
- Use `version-report` when the user wants package version, command count, checked-in fixture count, release readiness status, and latest local git tag/commit in JSON or Markdown.
- Use `fixture-gallery` when the user wants to inspect bundled example fixtures by command provenance, output type, hash, and recommended use case.
- Use `post-event` when the user wants overdue or completed catalysts that still need actual outcome capture and an outcome review template.
- Use `compare` when the user wants to diff two catalyst dataset snapshots and see added, removed, changed, score, status, evidence, or thesis-impact changes.
- Use `merge` when the user wants to combine multiple catalyst datasets into one validated JSON dataset with conflict diagnostics, duplicate-ID diagnostics, and source provenance.
- Use `html-dashboard` when the user wants a deterministic static no-JavaScript dashboard that combines score tables, exposure, thesis map, evidence audit, scenarios, and watchlist.
- Use `static-site` when the user wants a deterministic no-JavaScript site directory with an index, dashboard, source inventory, per-ticker pages, shared CSS, and a manifest.
- Use `export-demo` to create a deterministic starter dataset or smoke-test the package.
- Use `demo-bundle` when the user wants a portable tutorial packet containing every deterministic example output, a bundle README, manifest hashes, command provenance, and a quickstart transcript.
- Use `export-csv` and `import-csv` when the user needs spreadsheet review or CSV round trips.
- Use `export-ics` when the user needs upcoming catalysts in a calendar app or downstream calendar feed.
- Use `create-archive` when the user needs a portable handoff directory containing the dataset, generated reports, and a SHA-256 manifest.
- Use `verify-archive` before trusting or sharing an existing archive directory.
- Use `release-audit` before release handoff to verify checked-in examples, README command coverage, schema field docs, skill presence, and absence of workflow files.
- Use `changelog` when the user wants deterministic Markdown or JSON release notes from local git tags and commits without network calls.
- Use `smoke-matrix` when the user wants an offline pass/fail smoke report for every CLI command against demo data, including expected files and duration buckets.
- Use `finalize-release` when the user wants one deterministic release checklist that combines release-audit, smoke-matrix, fixture-gallery, and changelog.

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
python -m market_catalyst_calendar version-report --root . --repo .
python -m market_catalyst_calendar version-report --root . --repo . --format markdown
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

## Input

Input is JSON with an `as_of` date and a `records` list. Each record should include ticker or entity, event type, date or window, confidence, status/history, thesis impact, evidence URLs, bull/base/bear scenario notes, required review action, and last reviewed date. Records can also include optional `evidence_checked_at`, `position_size`, `portfolio_weight`, `risk_budget`, `max_loss`, `sector`, `theme`, `thesis_id`, `source_ref`, `broker_views`, `actual_outcome`, and `outcome_recorded_at`; `portfolio_weight` is a decimal fraction from `0` to `1`, while `position_size`, `risk_budget`, and `max_loss` are non-negative notional values. Each broker view includes `institution`, `rating`, `target_price`, `as_of`, `source_url`, and `caveat`. Post-event outcome dates cannot be after dataset `as_of`, cannot be before the event window starts, and require `actual_outcome`.

## Output

Outputs are deterministic JSON, Markdown, static HTML, static site directories, CSV, ICS, archive directories, preset packet directories, or demo bundle directories. JSON output sorts keys and records. Markdown briefs rank records by catalyst score, then event date, ticker, and record id. Exposure reports group upcoming open catalysts by ticker, event type, and urgency, then aggregate portfolio weight, notional position size, and confidence/score-weighted exposure. Risk-budget reports group upcoming open catalysts by ticker, thesis, and urgency, compare `max_loss` with `risk_budget`, calculate expected event loss, and flag over-budget or incomplete risk data. Sector maps group records by optional `sector`/`theme`, then surface exposure, urgency mix, stale or missing evidence freshness, and broker target-price dispersion. Review plans select stale open records plus high-urgency upcoming records, then provide per-record next actions, evidence gaps, and scenario update prompts. Thesis maps group records with `thesis_id`, count open and stale events, surface the highest catalyst score, and list source references from `source_ref` and evidence URLs. Scenario matrices filter to upcoming open catalysts, then render bull/base/bear rows with scenario-adjusted score, scenario date, impact, review action, and note. Evidence audits flag missing or stale `evidence_checked_at`, fewer than `--min-sources` evidence URLs, and dominant source domains above `--max-domain-share`. Quality gates return fail/pass JSON or Markdown, include stable diagnostic codes, and exit nonzero when the selected profile fails for evidence minimums, scenario completeness, review freshness, placeholder URLs, broker caveats, or strict release metadata. Doctor reports are read-only and return diagnostics, repair explanations, manual actions, and JSON Patch-style operations for validation and quality-gate failures; `--format patch` emits only the operation list. Broker matrices group `broker_views` by ticker/thesis, calculate target-price dispersion and rating counts, flag stale broker sources, and link views back to catalyst records. Source packs deduplicate evidence URLs and broker `source_url` values, preserve linked tickers/thesis ids/record ids, count usage, and report freshness from `evidence_checked_at` and broker `as_of` dates in JSON, CSV, or Markdown. Watchlists convert open catalysts into priority-scored items with trigger conditions, due dates, due state, review cadence, thesis/source refs, evidence URLs, and scenario refs. Decision logs emit per-catalyst memo stubs with thesis context, catalyst status, evidence, scenarios, broker context, watchlist triggers, blank decision slots, and post-event review slots. Drilldowns filter to one ticker and compose upcoming events, thesis map, broker matrix, risk budget, watchlist, post-event queue, source pack, and decision logs into one dossier. Command cookbooks render Markdown playbooks that inspect available optional fields, select the relevant command sequences, and list expected output files for each step. Tutorials render notebooks-free Markdown walkthroughs from demo data with expected command output excerpts, expected exit codes, and learning checkpoints. Agent handoffs render JSON or Markdown context packs with dataset summary, top risks, stale items, next commands, and source URLs for downstream investment research agents. Preset runs read JSON config defaults for days, stale thresholds, quality profile, and output directory, then write named workflow artifacts plus a manifest with stable hashes and report exit codes. Taxonomy reports render supported event types, statuses, review actions, quality rules, validation and quality-gate diagnostic codes, output-producing commands, and the full command catalog in JSON or Markdown. Version reports render package version, command count, checked-in fixture count, release readiness status, and latest local git tag/commit in JSON or Markdown. Fixture galleries render JSON or Markdown indexes of bundled examples with command provenance, expected exit codes, output types, byte counts, SHA-256 hashes, input fixture references, and recommended use cases. Post-event reports select completed or overdue catalysts missing outcome fields and render outcome review templates. Compare reports match two datasets by record id and show added/removed events, score deltas, status transitions, evidence URL changes, thesis-impact changes, scenario-note changes, and history changes in JSON or Markdown. Merge reports emit a reusable merged JSON dataset plus source provenance, chosen-source maps, conflict fields, duplicate-ID diagnostics, and validation results; `--prefer-newer-status-history` can source `status`/`history` from the newest history entry while keeping the deterministic record winner for other fields. HTML dashboards combine score tables, exposure summary, risk budget, sector map, thesis map, evidence audit, scenario matrix, and watchlist in one no-JavaScript document with escaped dynamic text. Static sites write an index, dashboard, source inventory, per-ticker pages, shared CSS, and a manifest with hashes into an empty output directory. CSV exports sort rows by event window, ticker, and id, and percent-encode multi-value cell components before joining them with visible separators. ICS exports upcoming open catalysts as all-day iCalendar events with stable UIDs, deterministic `DTSTAMP`, escaped text, categories, exclusive `DTEND`, and source URL notes. Archives include canonical JSON, CSV, ICS, generated reports, and `manifest.json` entries with relative path, byte count, and SHA-256 hash; verification fails on missing, modified, or untracked files. Demo bundles include every example output under `examples/`, a bundle-local README, `quickstart-transcript.txt`, and `manifest.json` with command provenance and expected exit codes. Release audits return JSON or Markdown checks for regenerated examples, README required commands, schema fields, skill presence, and workflow-file absence. Changelogs render local git release notes from `--since-tag` through `--to-ref`, grouped by conventional-commit category with scopes, breaking changes, references, tags, and exact SHAs. Smoke matrices return JSON or Markdown pass/fail reports for every command, expected output files, expected exits, and coarse duration buckets.

## Validation

Always validate input before producing a user-facing brief. Treat validation failures as blocking unless the user explicitly asks for a diagnostic report. Use `basic` for internal drafting, `public` before handoff, and `strict` for release datasets. Important checks include URL validity, scenario completeness, confidence range, status/history consistency, required review action for open records, evidence freshness, placeholder URLs, broker caveats, and release metadata.

## Safety

This tool organizes research records; it does not provide investment advice. Preserve source URLs, avoid inventing evidence, keep uncertainty visible through confidence and scenario notes, and label stale records that need review.

## Done Criteria

A task is done when the dataset validates, requested outputs are generated deterministically, HTML dashboards and static-site pages escape dataset text and require no JavaScript, static sites include index/dashboard/source/ticker pages plus a hashed manifest when requested, calendar exports preserve source links and escaped text when requested, archives verify when requested, preset runs write every configured artifact plus `manifest.json` with stable hashes and report exit codes when requested, demo bundles include all example outputs plus README/transcript/manifest when requested, fixture galleries include bundled fixture hashes, command provenance, output types, and recommended use cases when requested, taxonomy reports include supported event types, statuses, review actions, quality rules, diagnostic codes, output-producing commands, and command catalog when requested, version reports include package version, command count, fixture count, release status, and local git tag/commit when requested, smoke matrices check every command and report pass/fail, expected exits, expected files, and duration buckets when requested, release finalizers combine release-audit, smoke-matrix, fixture-gallery, and changelog into one checklist when requested, command cookbooks select sections from the dataset's available fields and list step-by-step commands with expected output files when requested, agent handoffs include dataset summary, top risks, stale items, commands to run next, and source URLs when requested, single-ticker drilldowns include events, thesis, brokers, risk, watchlist, post-event queue, source pack, and decision logs when requested, stale or missing-review items are surfaced, evidence freshness and source diversity are audited when requested, public research quality gates fail or pass explicitly when requested, doctor reports suggest read-only repairs and patch-style operations without mutating input when requested, source packs deduplicate evidence and broker URLs with usage and freshness context when requested, exposure is aggregated when position or weight fields are relevant, risk-budget reports flag over-budget catalysts when `risk_budget` or `max_loss` is present, sector/theme links are grouped when `sector` or `theme` is present, thesis links are grouped when `thesis_id` is present, broker views are summarized when `broker_views` is present, watchlists include priority, triggers, due dates, cadence, and source/thesis links when requested, decision logs include memo stubs and post-event review slots when requested, post-event reports queue missing `actual_outcome` or `outcome_recorded_at` fields when requested, compare reports identify added/removed/changed records and score/status/evidence/thesis-impact changes when requested, merge reports produce one valid merged dataset with provenance/conflict/duplicate diagnostics when requested, changelog reports summarize local git commits since the requested tag without network calls when requested, scenario matrices show bull/base/bear implications when requested, and any limitations in evidence or confidence are clearly reported.
