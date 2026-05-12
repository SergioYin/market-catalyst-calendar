# Market Catalyst Calendar Agent Skill

## Triggers

Use this skill when a user wants to create, validate, rank, review, brief, or export a source-attributed market catalyst calendar for public equities, ETFs, macro instruments, or investment research workflows.

## Routing

- Use `python -m market_catalyst_calendar validate` before trusting a dataset.
- Use `upcoming` when the user asks what catalysts are in a forward window.
- Use `stale` when the user asks what needs review or evidence refresh.
- Use `brief` when the user wants a Markdown analyst-ready summary.
- Use `exposure` when the user asks which upcoming catalysts matter most to a portfolio or position book.
- Use `review-plan` when the user wants an actionable review checklist for stale records and high-urgency upcoming catalysts.
- Use `thesis-map` when the user wants catalysts grouped by investment thesis, with open event counts, stale counts, top score, and source references.
- Use `scenario-matrix` when the user wants bull/base/bear scenarios with scenario score, event date, impact, and review action.
- Use `evidence-audit` when the user wants evidence freshness, source count, or source concentration checks.
- Use `broker-matrix` when the user wants broker or analyst views grouped by ticker/thesis with target-price dispersion, stale source flags, and linked catalysts.
- Use `watchlist` when the user wants catalysts converted into prioritized watch items with trigger conditions, due dates, review cadence, and thesis/source references.
- Use `html-dashboard` when the user wants a deterministic static no-JavaScript dashboard that combines score tables, exposure, thesis map, evidence audit, scenarios, and watchlist.
- Use `export-demo` to create a deterministic starter dataset or smoke-test the package.
- Use `export-csv` and `import-csv` when the user needs spreadsheet review or CSV round trips.
- Use `export-ics` when the user needs upcoming catalysts in a calendar app or downstream calendar feed.
- Use `create-archive` when the user needs a portable handoff directory containing the dataset, generated reports, and a SHA-256 manifest.
- Use `verify-archive` before trusting or sharing an existing archive directory.

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
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
python -m market_catalyst_calendar html-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output examples/dashboard.html
python -m market_catalyst_calendar export-csv --input examples/demo_records.json --output examples/demo_records.csv
python -m market_catalyst_calendar export-ics --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output examples/upcoming.ics
python -m market_catalyst_calendar import-csv --input examples/demo_records.csv --output examples/imported_demo_records.json
python -m market_catalyst_calendar create-archive --input examples/demo_records.json --output-dir archive/demo --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar verify-archive archive/demo
```

## Input

Input is JSON with an `as_of` date and a `records` list. Each record should include ticker or entity, event type, date or window, confidence, status/history, thesis impact, evidence URLs, bull/base/bear scenario notes, required review action, and last reviewed date. Records can also include optional `evidence_checked_at`, `position_size`, `portfolio_weight`, `thesis_id`, `source_ref`, and `broker_views`; `portfolio_weight` is a decimal fraction from `0` to `1`. Each broker view includes `institution`, `rating`, `target_price`, `as_of`, `source_url`, and `caveat`.

## Output

Outputs are deterministic JSON, Markdown, static HTML, CSV, ICS, or archive directories. JSON output sorts keys and records. Markdown briefs rank records by catalyst score, then event date, ticker, and record id. Exposure reports group upcoming open catalysts by ticker, event type, and urgency, then aggregate portfolio weight, notional position size, and confidence/score-weighted exposure. Review plans select stale open records plus high-urgency upcoming records, then provide per-record next actions, evidence gaps, and scenario update prompts. Thesis maps group records with `thesis_id`, count open and stale events, surface the highest catalyst score, and list source references from `source_ref` and evidence URLs. Scenario matrices filter to upcoming open catalysts, then render bull/base/bear rows with scenario-adjusted score, scenario date, impact, review action, and note. Evidence audits flag missing or stale `evidence_checked_at`, fewer than `--min-sources` evidence URLs, and dominant source domains above `--max-domain-share`. Broker matrices group `broker_views` by ticker/thesis, calculate target-price dispersion and rating counts, flag stale broker sources, and link views back to catalyst records. Watchlists convert open catalysts into priority-scored items with trigger conditions, due dates, due state, review cadence, thesis/source refs, evidence URLs, and scenario refs. HTML dashboards combine score tables, exposure summary, thesis map, evidence audit, scenario matrix, and watchlist in one no-JavaScript document with escaped dynamic text. CSV exports sort rows by event window, ticker, and id, and percent-encode multi-value cell components before joining them with visible separators. ICS exports upcoming open catalysts as all-day iCalendar events with stable UIDs, deterministic `DTSTAMP`, escaped text, categories, exclusive `DTEND`, and source URL notes. Archives include canonical JSON, CSV, ICS, generated reports, and `manifest.json` entries with relative path, byte count, and SHA-256 hash; verification fails on missing, modified, or untracked files.

## Validation

Always validate input before producing a user-facing brief. Treat validation failures as blocking unless the user explicitly asks for a diagnostic report. Important checks include URL validity, scenario completeness, confidence range, status/history consistency, and required review action for open records.

## Safety

This tool organizes research records; it does not provide investment advice. Preserve source URLs, avoid inventing evidence, keep uncertainty visible through confidence and scenario notes, and label stale records that need review.

## Done Criteria

A task is done when the dataset validates, requested outputs are generated deterministically, HTML dashboards escape dataset text and require no JavaScript, calendar exports preserve source links and escaped text when requested, archives verify when requested, stale or missing-review items are surfaced, evidence freshness and source diversity are audited when requested, exposure is aggregated when position or weight fields are relevant, thesis links are grouped when `thesis_id` is present, broker views are summarized when `broker_views` is present, watchlists include priority, triggers, due dates, cadence, and source/thesis links when requested, scenario matrices show bull/base/bear implications when requested, and any limitations in evidence or confidence are clearly reported.
