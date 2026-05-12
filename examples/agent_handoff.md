# Agent Handoff Pack

As of: 2026-05-13
Dataset path in commands: `examples/demo_records.json`
Output directory in commands: `reports`

## Dataset Summary

| Metric | Value |
| --- | ---: |
| Records | 4 |
| Open records | 3 |
| Upcoming records | 3 |
| Stale review records | 1 |
| Stale evidence records | 1 |
| Missing evidence freshness | 1 |
| Source URLs | 11 |
| Broker views | 4 |

## Top Risks

| Rank | Ticker | Score | Window | Flags | Next action |
| ---: | --- | ---: | --- | --- | --- |
| 1 | PFE | 87 | 2026-05-20..2026-05-24 | stale_review, stale_evidence, over_budget, review_action:verify_source | Verify downside estimate, update risk budget, and escalate before the event window. |
| 2 | SPY | 83 | 2026-06-17 | missing_evidence_freshness, over_budget, review_action:monitor_date | Verify downside estimate, update risk budget, and escalate before the event window. |
| 3 | NVDA | 84 | 2026-06-02 | review_action:monitor_date | Complete required review action `monitor_date`. |

## Stale Items

| Ticker | Record | Review age | Evidence age | Action |
| --- | --- | ---: | ---: | --- |
| PFE | demo-pfe-fda-2026 | 15 | 15 | Verify downside estimate, update risk budget, and escalate before the event window. |
| SPY | demo-fomc-june-2026 | 5 | missing | Verify downside estimate, update risk budget, and escalate before the event window. |

## Commands To Run Next

```bash
mkdir -p reports
python -m market_catalyst_calendar validate --profile public --input examples/demo_records.json --as-of 2026-05-13 > reports/validate_public.json || test $? -eq 1
python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13 > reports/quality_gate.json || test $? -eq 1
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --fresh-after-days 14 > reports/source_pack.json
python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45 --stale-after-days 14 --format markdown > reports/review_plan.md
python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45 --stale-after-days 14 --format markdown > reports/decision_log.md
python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker PFE --days 45 --format markdown > reports/drilldown_pfe.md
python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker SPY --days 45 --format markdown > reports/drilldown_spy.md
python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45 --format markdown > reports/drilldown_nvda.md
```

## Source URLs

| Freshness | Type | Tickers | URL |
| --- | --- | --- | --- |
| missing | evidence | SPY | https://example.com/fomc-calendar |
| stale | evidence | PFE | https://example.com/fda-calendar |
| stale | broker | NVDA | https://example.com/nvda-broker-metro |
| stale | broker | PFE | https://example.com/pfe-broker-summit |
| stale | evidence | PFE | https://example.com/pfe-pipeline-update |
| fresh | evidence | NVDA | https://example.com/channel-check-gpu-supply |
| fresh | evidence | MSFT | https://example.com/msft-q3-earnings |
| fresh | broker | NVDA | https://example.com/nvda-broker-north-coast |
| fresh | evidence | NVDA | https://example.com/nvidia-computex-keynote |
| fresh | broker | PFE | https://example.com/pfe-broker-harbor |
| fresh | evidence | MSFT | https://ir.example.org/msft-q3-transcript |
