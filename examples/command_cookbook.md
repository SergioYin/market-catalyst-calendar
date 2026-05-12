# Market Catalyst Command Cookbook

As of: 2026-05-13
Dataset path in commands: `examples/demo_records.json`
Output directory in commands: `reports`

## Dataset Profile

| Metric | Value |
| --- | ---: |
| records | 4 |
| upcoming open records | 3 |
| stale records | 1 |
| completed or past-window records | 1 |
| records with portfolio exposure | 4 |
| records with risk budget fields | 4 |
| records with sector/theme | 4 |
| records with thesis links | 4 |
| broker views | 4 |

## Field-Driven Selection

| Section | Decision | Reason |
| --- | --- | --- |
| Intake And Freshness Gate | selected | Every dataset should validate before downstream reports are trusted; quality-gate is included because it exposes publication blockers. |
| Core Catalyst Briefing | selected | Upcoming, stale, brief, and review-plan outputs create the minimum daily analyst packet. |
| Source Handoff Packet | selected | Evidence URLs are present, so the cookbook includes a source inventory for audit or collection work. |
| Portfolio Exposure Pass | selected | At least one record has `portfolio_weight` or `position_size`, so exposure aggregation is useful. |
| Risk Budget Pass | selected | At least one record has `risk_budget` or `max_loss`, so event loss should be checked against budget. |
| Sector And Theme Map | selected | At least one record has `sector` or `theme`, so concentration should be reviewed above the single-name level. |
| Thesis Coverage Pass | selected | At least one record has `thesis_id` or `source_ref`, so thesis-level coverage and decision stubs are relevant. |
| Broker View Matrix | selected | At least one record has `broker_views`, so target dispersion and stale broker sources should be summarized. |
| Scenario Matrix Pass | selected | Bull/base/bear scenario notes are available, so event scenarios can be rendered directly. |
| Post-Event Closeout | selected | At least one catalyst is completed, past its event window, or has outcome metadata, so outcome capture should be queued. |
| Portable Outputs | selected | CSV, calendar, dashboard, and archive outputs are useful for handoff even when no optional fields are present. |

## Analyst Playbook

### 1. Intake And Freshness Gate

Why: Every dataset should validate before downstream reports are trusted; quality-gate is included because it exposes publication blockers.

Expected output files:
- `reports/evidence_audit.md`
- `reports/quality_gate.json`
- `reports/validate.json`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar validate --input examples/demo_records.json > reports/validate.json
python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13 > reports/quality_gate.json || test $? -eq 1
python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13 --format markdown > reports/evidence_audit.md
```

- `reports/validate.json`: Schema and record consistency check; exit nonzero if the dataset is invalid.
- `reports/quality_gate.json`: Public-research gate. Exit code 1 is expected when the gate finds blocking issues, so the shell guard preserves the playbook run.
- `reports/evidence_audit.md`: Evidence freshness, source-count, and source-concentration review.

### 2. Core Catalyst Briefing

Why: Upcoming, stale, brief, and review-plan outputs create the minimum daily analyst packet.

Expected output files:
- `reports/brief.md`
- `reports/review_plan.md`
- `reports/stale.md`
- `reports/upcoming.json`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45 > reports/upcoming.json
python -m market_catalyst_calendar stale --input examples/demo_records.json --as-of 2026-05-13 --format markdown > reports/stale.md
python -m market_catalyst_calendar brief --input examples/demo_records.json --as-of 2026-05-13 --days 45 > reports/brief.md
python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown > reports/review_plan.md
```

- `reports/upcoming.json`: Machine-readable forward catalyst queue.
- `reports/stale.md`: Human-readable list of records whose review state is stale.
- `reports/brief.md`: Ranked Markdown brief for the forward window.
- `reports/review_plan.md`: Step-by-step checklist for stale and high-urgency records.

### 3. Source Handoff Packet

Why: Evidence URLs are present, so the cookbook includes a source inventory for audit or collection work.

Expected output files:
- `reports/source_pack.csv`
- `reports/source_pack.json`
- `reports/source_pack.md`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 > reports/source_pack.json
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format csv > reports/source_pack.csv
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format markdown > reports/source_pack.md
```

- `reports/source_pack.json`: Deduplicated source inventory for automation.
- `reports/source_pack.csv`: Spreadsheet-ready source collection list.
- `reports/source_pack.md`: Analyst-readable source packet.

### 4. Portfolio Exposure Pass

Why: At least one record has `portfolio_weight` or `position_size`, so exposure aggregation is useful.

Expected output files:
- `reports/exposure.json`
- `reports/exposure.md`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45 > reports/exposure.json
python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown > reports/exposure.md
```

- `reports/exposure.json`: Grouped exposure data by ticker, event type, and urgency.
- `reports/exposure.md`: Markdown exposure table for review packets.

### 5. Risk Budget Pass

Why: At least one record has `risk_budget` or `max_loss`, so event loss should be checked against budget.

Expected output files:
- `reports/risk_budget.json`
- `reports/risk_budget.md`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 > reports/risk_budget.json
python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown > reports/risk_budget.md
```

- `reports/risk_budget.json`: Risk-budget calculations and flags for downstream automation.
- `reports/risk_budget.md`: Markdown risk table with over-budget details.

### 6. Sector And Theme Map

Why: At least one record has `sector` or `theme`, so concentration should be reviewed above the single-name level.

Expected output files:
- `reports/sector_map.json`
- `reports/sector_map.md`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar sector-map --input examples/demo_records.json --as-of 2026-05-13 > reports/sector_map.json
python -m market_catalyst_calendar sector-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown > reports/sector_map.md
```

- `reports/sector_map.json`: Sector/theme group data with exposure and evidence flags.
- `reports/sector_map.md`: Markdown sector/theme concentration view.

### 7. Thesis Coverage Pass

Why: At least one record has `thesis_id` or `source_ref`, so thesis-level coverage and decision stubs are relevant.

Expected output files:
- `reports/decision_log.md`
- `reports/thesis_map.md`
- `reports/watchlist.md`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown > reports/thesis_map.md
python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown > reports/watchlist.md
python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown > reports/decision_log.md
```

- `reports/thesis_map.md`: Thesis grouping with source references.
- `reports/watchlist.md`: Prioritized watch queue with thesis/source triggers.
- `reports/decision_log.md`: Decision memo stubs tied back to catalyst and thesis context.

### 8. Broker View Matrix

Why: At least one record has `broker_views`, so target dispersion and stale broker sources should be summarized.

Expected output files:
- `reports/broker_matrix.json`
- `reports/broker_matrix.md`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13 > reports/broker_matrix.json
python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13 --format markdown > reports/broker_matrix.md
```

- `reports/broker_matrix.json`: Broker matrix data with target-price dispersion.
- `reports/broker_matrix.md`: Analyst-readable broker view matrix.

### 9. Scenario Matrix Pass

Why: Bull/base/bear scenario notes are available, so event scenarios can be rendered directly.

Expected output files:
- `reports/scenario_matrix.json`
- `reports/scenario_matrix.md`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45 > reports/scenario_matrix.json
python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown > reports/scenario_matrix.md
```

- `reports/scenario_matrix.json`: Scenario rows for automation.
- `reports/scenario_matrix.md`: Markdown scenario matrix for analyst review.

### 10. Post-Event Closeout

Why: At least one catalyst is completed, past its event window, or has outcome metadata, so outcome capture should be queued.

Expected output files:
- `reports/post_event.json`
- `reports/post_event.md`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-05-13 > reports/post_event.json
python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-05-13 --format markdown > reports/post_event.md
```

- `reports/post_event.json`: Machine-readable outcome-review queue.
- `reports/post_event.md`: Markdown post-event review templates.

### 11. Portable Outputs

Why: CSV, calendar, dashboard, and archive outputs are useful for handoff even when no optional fields are present.

Expected output files:
- `reports/archive/manifest.json`
- `reports/archive_verification.json`
- `reports/dashboard.html`
- `reports/dataset.csv`
- `reports/upcoming.ics`

Commands:

```bash
mkdir -p reports
python -m market_catalyst_calendar export-csv --input examples/demo_records.json --output reports/dataset.csv
python -m market_catalyst_calendar export-ics --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output reports/upcoming.ics
python -m market_catalyst_calendar html-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 --output reports/dashboard.html
python -m market_catalyst_calendar create-archive --input examples/demo_records.json --output-dir reports/archive --as-of 2026-05-13 --days 45
python -m market_catalyst_calendar verify-archive reports/archive > reports/archive_verification.json
```

- `reports/dataset.csv`: Spreadsheet-friendly full dataset export.
- `reports/upcoming.ics`: Calendar feed for upcoming open catalysts.
- `reports/dashboard.html`: Static no-JavaScript dashboard.
- `reports/archive/manifest.json`: Portable archive directory with manifest hashes.
- `reports/archive_verification.json`: Archive verification report.
