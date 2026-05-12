# Market Catalyst Calendar

`market-catalyst-calendar` is a stdlib-only Python CLI for maintaining source-attributed market catalyst records: earnings, product launches, regulatory decisions, macro releases, and other events that can change an investment thesis.

The v0.1 MVP is designed for offline agent and analyst workflows. It validates catalyst records, ranks upcoming events with finance-specific scoring, flags stale review items, audits evidence freshness and source diversity, aggregates portfolio exposure, maps catalysts back to investment theses, summarizes broker views, exports source packs, converts catalysts into prioritized watchlists, emits decision memo stubs, queues post-event outcome reviews, renders Markdown briefs and a static HTML dashboard, exports calendar and CSV files, exports a deterministic demo dataset, and packages portable archives with hash verification.

## Install

```bash
python -m pip install .
```

No runtime dependencies are required beyond the Python standard library.

## Commands

```bash
python -m market_catalyst_calendar export-demo --output examples/demo_records.json
python -m market_catalyst_calendar validate --input examples/demo_records.json
python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar stale --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar brief --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format csv
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format markdown
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-06-25
python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-06-25 --format markdown
python -m market_catalyst_calendar html-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output examples/dashboard.html
python -m market_catalyst_calendar export-csv --input examples/demo_records.json --output examples/demo_records.csv
python -m market_catalyst_calendar export-ics --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output examples/upcoming.ics
python -m market_catalyst_calendar import-csv --input examples/demo_records.csv --output examples/imported_demo_records.json
python -m market_catalyst_calendar create-archive --input examples/demo_records.json --output-dir archive/demo --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar verify-archive archive/demo
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
- optional `thesis_id` and `source_ref`
- optional `broker_views`, each with `institution`, `rating`, `target_price`, `as_of`, `source_url`, and `caveat`
- optional `actual_outcome` and `outcome_recorded_at`

Validation checks schema shape, URL quality, scenario completeness, status/history consistency, confidence ranges, and review-action hygiene for open items.

`portfolio_weight` is a decimal fraction from `0` to `1`, so `0.05` means 5% of the portfolio. `position_size` is a non-negative notional value in the user's own reporting currency. Both fields are optional, which allows catalyst records to exist before a portfolio view is attached.

`evidence_checked_at` is separate from `last_reviewed`: use it for the date sources were last checked, even when the thesis notes or status did not change.

`broker_views` are record-level analyst or broker snapshots. They are optional and offline: the CLI validates their source URLs and dates, but it does not fetch reports or infer missing target prices.

`actual_outcome` and `outcome_recorded_at` are optional post-event fields. Use them after the catalyst window closes to capture what actually happened and when that outcome was recorded. `outcome_recorded_at` cannot be after dataset `as_of`, cannot be before the event window starts, and requires `actual_outcome`.

## Exposure Workflow

`exposure` filters to upcoming open catalysts in the requested look-ahead window, groups them by `ticker`, `event_type`, and scored `urgency`, then reports aggregate exposure in JSON or Markdown.

Weighted exposure adjusts each record's portfolio weight and notional position by both confidence and catalyst score:

```text
weighted exposure = portfolio_weight * confidence * catalyst_score / 100
weighted position exposure = position_size * confidence * catalyst_score / 100
```

This keeps low-confidence or low-priority catalysts visible while preventing them from counting the same as high-confidence near-term events.

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

## Post-Event Workflow

`post-event` lists catalysts that need outcome review after the event window has passed. It selects non-cancelled records whose `actual_outcome` or `outcome_recorded_at` is still missing when the record is already `completed` or when the review due date has passed. The review due date is the event window end plus `--review-after-days` (default `0`).

JSON and Markdown outputs include, per catalyst:

- event status, window, score, review due date, and days since the window ended
- outcome state and recorded-at state
- existing `actual_outcome` and `outcome_recorded_at` values when present, otherwise `TBD`
- thesis id, base scenario, source reference, and evidence URLs
- an outcome review template with slots for actual outcome, scenario accuracy, thesis impact after event, evidence delta, position or risk action, follow-up action, and source update need

Use it after events occur to close the loop between pre-event scenarios and what actually happened without inventing conclusions.

## HTML Dashboard Workflow

`html-dashboard` renders a deterministic, no-JavaScript HTML file for offline review. It safely escapes dataset text before writing it into the document.

The dashboard includes:

- score tables for upcoming catalysts
- exposure summary cards and grouped exposure rows
- thesis map
- evidence audit
- bull/base/bear scenario matrix
- prioritized watchlist

Use `--output` to write a portable `.html` artifact, or omit it to stream the HTML to stdout.

## CSV Workflow

`export-csv` writes the full catalyst dataset to a deterministic spreadsheet-friendly CSV. Rows are sorted by event window, ticker, and id; columns are stable; optional `thesis_id` and `source_ref` are preserved; and `confidence` is formatted without unnecessary trailing noise.

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
- `reports/post_event.json` and `reports/post_event.md`
- `reports/dashboard.html`
- `reports/exposure.json` and `reports/exposure.md`
- `reports/review_plan.json` and `reports/review_plan.md`
- `reports/scenario_matrix.json` and `reports/scenario_matrix.md`
- `reports/thesis_map.json` and `reports/thesis_map.md`
- `reports/evidence_audit.json` and `reports/evidence_audit.md`
- `manifest.json`: archive metadata plus byte counts and SHA-256 hashes for every archived file

`verify-archive` reads `manifest.json`, recomputes hashes and byte counts, and fails if any archived file is missing, changed, or untracked. This makes the directory portable without requiring a zip format or non-stdlib tooling.

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
- `post_event.json`: generated post-event outcome review queue
- `post_event.md`: generated Markdown post-event outcome review template
- `dashboard.html`: generated static no-JavaScript HTML dashboard
- `thesis_map.json`: generated thesis grouping data
- `thesis_map.md`: generated Markdown thesis map
- `upcoming.ics`: generated iCalendar export for upcoming catalysts
- `demo_records.csv`: deterministic CSV export
- `imported_demo_records.json`: JSON imported back from CSV

Archive output is intentionally not checked in because it duplicates the generated examples. Use the commands above to create a fresh archive when needed.

## Selfcheck

```bash
python scripts/selfcheck.py
```

The selfcheck runs unit tests, exports demo data to a temporary directory, validates it, creates and verifies an archive, and verifies deterministic command output against checked-in examples.

## Roadmap

- Per-sector event presets and scoring calibration
- Watchlist filters and portfolio exposure tags
- Evidence freshness checks using external fetchers kept outside the core stdlib package
- Optional thesis metadata catalogs while preserving record-level `thesis_id` links

## License

MIT
