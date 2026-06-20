# Market Catalyst Impact Dashboard

As of: 2026-05-13
Horizon: 45 days; stale after 14 days.
Input: dataset

Boundary: Offline deterministic research brief from supplied dataset only. No live data, broker connectivity, predictions, investment advice, or trade recommendations.

| Metric | Value |
| --- | ---: |
| Total upcoming items | 3 |
| Review queue | 3 |
| Top attention catalysts | 3 |

## Evidence State Counts

| State | Count |
| --- | ---: |
| fresh | 1 |
| missing | 1 |
| stale | 1 |

## Impact Flag Counts

| State | Count |
| --- | ---: |
| broker_context | 2 |
| missing_evidence_freshness | 1 |
| over_budget | 2 |
| stale_review | 1 |

## Top Attention Catalysts

| Attention | Ticker | Window | Event | Evidence | Flags |
| ---: | --- | --- | --- | --- | --- |
| 100 | PFE | 2026-05-20..2026-05-24 | regulatory decision | stale | broker_context, over_budget, stale_review |
| 89 | SPY | 2026-06-17 | macro release | missing | missing_evidence_freshness, over_budget |
| 84 | NVDA | 2026-06-02 | product launch | fresh | broker_context |

## Review Queue

| Attention | Ticker | Review | Action | Reason |
| ---: | --- | --- | --- | --- |
| 100 | PFE | stale | verify_source | stale, verify_source |
| 89 | SPY | current | monitor_date | missing_evidence_freshness, monitor_date |
| 84 | NVDA | current | monitor_date | monitor_date |
