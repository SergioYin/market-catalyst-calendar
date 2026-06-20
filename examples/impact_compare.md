# Market Catalyst Impact Compare

As of: 2026-05-27
Base snapshot: 2026-05-27 (dataset)
Current snapshot: 2026-05-27 (dataset)
Scope: impact-brief records within 45 days; stale after 14 days.

Boundary: Offline deterministic research brief from supplied dataset only. No live data, broker connectivity, predictions, investment advice, or trade recommendations.

Summary: 1 added, 1 removed, 1 changed, 1 attention-score movements, 1 evidence-state movements, 1 impact-flag changes.

## Added Catalysts

| Attention | Ticker | Window | Event | Evidence | Flags | ID |
| ---: | --- | --- | --- | --- | --- | --- |
| 81 | AMZN | 2026-06-12 | product launch | fresh | over_budget | demo-amzn-kuiper-2026 |

## Removed Catalysts

| Attention | Ticker | Window | Event | Evidence | Flags | ID |
| ---: | --- | --- | --- | --- | --- | --- |
| 100 | SPY | 2026-06-17 | macro release | missing | missing_evidence_freshness, over_budget, stale_review | demo-fomc-june-2026 |

## Changed Catalysts

| ID | Ticker | Attention | Evidence | Impact Flags | Impact Label | Fields |
| --- | --- | ---: | --- | --- | --- | --- |
| demo-nvda-computex-2026 | NVDA | -3 | stale -> fresh | +0/-1 | none | status, confidence, review_state, required_review_action, portfolio_weight, weighted_attention, risk_budget, max_loss, source_ref, evidence_checked_at |

### NVDA - demo-nvda-computex-2026

- Attention score: 96 -> 93 (-3)
- Catalyst score: 88 -> 93 (+5)
- Evidence state: stale -> fresh
- Impact flags: added none; removed stale_review
- Impact label: none
- Other fields: status scheduled -> confirmed; confidence 0.74 -> 0.81; review_state stale -> needs_review; required_review_action monitor_date -> update_scenario; portfolio_weight 0.0825 -> 0.091; weighted_attention 0.053724 -> 0.06855; risk_budget 60000.0 -> 62000.0; max_loss 52000.0 -> 56000.0; source_ref NVDA Computex keynote tracker -> NVDA Computex keynote tracker refreshed after agenda update; evidence_checked_at 2026-05-09 -> 2026-05-27
