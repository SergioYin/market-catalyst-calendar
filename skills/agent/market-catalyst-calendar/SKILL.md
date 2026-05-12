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
- Use `export-demo` to create a deterministic starter dataset or smoke-test the package.
- Use `export-csv` and `import-csv` when the user needs spreadsheet review or CSV round trips.
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
python -m market_catalyst_calendar export-csv --input examples/demo_records.json --output examples/demo_records.csv
python -m market_catalyst_calendar import-csv --input examples/demo_records.csv --output examples/imported_demo_records.json
python -m market_catalyst_calendar create-archive --input examples/demo_records.json --output-dir archive/demo --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar verify-archive archive/demo
```

## Input

Input is JSON with an `as_of` date and a `records` list. Each record should include ticker or entity, event type, date or window, confidence, status/history, thesis impact, evidence URLs, bull/base/bear scenario notes, required review action, and last reviewed date. Records can also include optional `position_size` and `portfolio_weight`; `portfolio_weight` is a decimal fraction from `0` to `1`.

## Output

Outputs are deterministic JSON, Markdown, CSV, or archive directories. JSON output sorts keys and records. Markdown briefs rank records by catalyst score, then event date, ticker, and record id. Exposure reports group upcoming open catalysts by ticker, event type, and urgency, then aggregate portfolio weight, notional position size, and confidence/score-weighted exposure. Review plans select stale open records plus high-urgency upcoming records, then provide per-record next actions, evidence gaps, and scenario update prompts. CSV exports sort rows by event window, ticker, and id, and percent-encode multi-value cell components before joining them with visible separators. Archives include canonical JSON, CSV, generated reports, and `manifest.json` entries with relative path, byte count, and SHA-256 hash; verification fails on missing, modified, or untracked files.

## Validation

Always validate input before producing a user-facing brief. Treat validation failures as blocking unless the user explicitly asks for a diagnostic report. Important checks include URL validity, scenario completeness, confidence range, status/history consistency, and required review action for open records.

## Safety

This tool organizes research records; it does not provide investment advice. Preserve source URLs, avoid inventing evidence, keep uncertainty visible through confidence and scenario notes, and label stale records that need review.

## Done Criteria

A task is done when the dataset validates, requested outputs are generated deterministically, archives verify when requested, stale or missing-review items are surfaced, exposure is aggregated when position or weight fields are relevant, and any limitations in evidence or confidence are clearly reported.
