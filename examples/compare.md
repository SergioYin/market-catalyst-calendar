# Market Catalyst Snapshot Compare

As of: 2026-05-27
Base snapshot: 2026-05-13
Current snapshot: 2026-05-27

Summary: 1 added, 1 removed, 2 changed, 2 score changes, 2 status transitions, 2 evidence changes, 1 thesis-impact change.

## Added Events

| Score | Window | Ticker | Event | Status | Impact | ID |
| ---: | --- | --- | --- | --- | --- | --- |
| 75 | 2026-06-12 | AMZN | product launch | watching | mixed | demo-amzn-kuiper-2026 |

## Removed Events

| Score | Window | Ticker | Event | Status | Impact | ID |
| ---: | --- | --- | --- | --- | --- | --- |
| 88 | 2026-06-17 | SPY | macro release | confirmed | mixed | demo-fomc-june-2026 |

## Changed Events

| ID | Ticker | Score Delta | Status | Evidence | Thesis Impact | Fields |
| --- | --- | ---: | --- | --- | --- | --- |
| demo-nvda-computex-2026 | NVDA | +5 | scheduled -> confirmed | +1/-1 | none | confidence, required_review_action, last_reviewed, evidence_checked_at, position_size, portfolio_weight, risk_budget, max_loss, source_ref |
| demo-pfe-fda-2026 | PFE | -34 | watching -> completed | +1/-1 | mixed -> positive | confidence, required_review_action, last_reviewed, evidence_checked_at, position_size, portfolio_weight, max_loss, source_ref, actual_outcome, outcome_recorded_at |

### NVDA - demo-nvda-computex-2026

- Score: 88 -> 93 (+5); urgency high -> high; review stale -> needs_review
- Status: scheduled -> confirmed
- Evidence: added https://example.com/nvidia-computex-agenda-update; removed https://example.com/channel-check-gpu-supply; checked_at 2026-05-09 -> 2026-05-27
- Other fields: confidence 0.74 -> 0.81; required_review_action monitor_date -> update_scenario; last_reviewed 2026-05-09 -> 2026-05-27; evidence_checked_at 2026-05-09 -> 2026-05-27; position_size 125000.0 -> 135000.0; portfolio_weight 0.0825 -> 0.091; risk_budget 60000.0 -> 62000.0; max_loss 52000.0 -> 56000.0; source_ref NVDA Computex keynote tracker -> NVDA Computex keynote tracker refreshed after agenda update
- Broker views: changed North Coast Securities

### PFE - demo-pfe-fda-2026

- Score: 69 -> 35 (-34); urgency overdue -> closed; review stale -> closed
- Status: watching -> completed
- Thesis impact: mixed -> positive
- Evidence: added https://example.com/pfe-label-update; removed https://example.com/pfe-pipeline-update; checked_at 2026-04-28 -> 2026-05-24
- Other fields: confidence 0.68 -> 0.76; required_review_action verify_source -> archive; last_reviewed 2026-04-28 -> 2026-05-24; evidence_checked_at 2026-04-28 -> 2026-05-24; position_size 48000.0 -> 42000.0; portfolio_weight 0.031 -> 0.026; max_loss 32000.0 -> 18000.0; source_ref FDA calendar and PFE pipeline note -> FDA calendar, label note, and PFE pipeline update; actual_outcome missing -> Approval arrived inside the expected decision window with label language better than the base case.; outcome_recorded_at missing -> 2026-05-24
- Broker views: changed Harbor Life Sciences
