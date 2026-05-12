# Market Catalyst Calendar

`market-catalyst-calendar` is a stdlib-only Python CLI for maintaining source-attributed market catalyst records: earnings, product launches, regulatory decisions, macro releases, and other events that can change an investment thesis.

The v0.1 MVP is designed for offline agent and analyst workflows. It validates catalyst records, ranks upcoming events with finance-specific scoring, flags stale review items, aggregates portfolio exposure, renders Markdown briefs, exports a deterministic demo dataset, and packages portable archives with hash verification.

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
python -m market_catalyst_calendar export-csv --input examples/demo_records.json --output examples/demo_records.csv
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
- optional `position_size` and `portfolio_weight`

Validation checks schema shape, URL quality, scenario completeness, status/history consistency, confidence ranges, and review-action hygiene for open items.

`portfolio_weight` is a decimal fraction from `0` to `1`, so `0.05` means 5% of the portfolio. `position_size` is a non-negative notional value in the user's own reporting currency. Both fields are optional, which allows catalyst records to exist before a portfolio view is attached.

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

## CSV Workflow

`export-csv` writes the full catalyst dataset to a deterministic spreadsheet-friendly CSV. Rows are sorted by event window, ticker, and id; columns are stable; and `confidence` is formatted without unnecessary trailing noise.

`import-csv` reads that CSV back into the same JSON dataset shape used by `validate`, `upcoming`, `stale`, and `brief`. The CSV includes `window_start` and `window_end`; equal values import as a single `date`, while different values import as a `window`.

Multi-value cells use safe encoded separators:

- `evidence_urls`: URL-encoded values joined by ` | `
- `scenario_notes`: URL-encoded `key = value` pairs joined by ` | `
- `history`: URL-encoded `date = status = note` entries joined by ` | `

Because each component is percent-encoded before joining, commas, newlines, pipes, equals signs, and URL query strings survive a CSV round trip.

## Archive Workflow

`create-archive` writes a portable directory for handoff, review, or offline retention. The output directory must be empty. The archive contains:

- `dataset/dataset.json`: canonical JSON copy of the input dataset
- `dataset/dataset.csv`: deterministic CSV export for spreadsheet review
- `reports/upcoming.json` and `reports/stale.json`
- `reports/brief.md`
- `reports/exposure.json` and `reports/exposure.md`
- `reports/review_plan.json` and `reports/review_plan.md`
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
- Optional rich terminal output while preserving deterministic JSON and Markdown modes

## License

MIT
