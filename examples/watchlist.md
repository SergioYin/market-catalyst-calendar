# Market Catalyst Watchlist

As of: 2026-05-13
Scope: open catalysts due or starting within 45 days; stale after 14 days.

| Priority | Due | Cadence | Ticker | Catalyst | Triggers | Thesis | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| critical (100) | 2026-05-13 | daily_until_resolved | PFE | regulatory_decision 2026-05-20..2026-05-24 | Review by 2026-05-13 before catalyst window 2026-05-20..2026-05-24.; Escalate if PFE confirms, delays, cancels, or changes the regulatory decision window.; Last review is stale by 15 days as of 2026-05-13.; Primary evidence changes, disappears, conflicts with another source, or lacks a dated update.; Bull/base/bear evidence changes the linked thesis 'pharma-pipeline-reset'.; Position size, portfolio weight, or risk budget changes before the event. | pharma-pipeline-reset | FDA calendar and PFE pipeline note, https://example.com/fda-calendar, https://example.com/pfe-pipeline-update |
| high (79) | 2026-06-10 | weekly | SPY | macro_release 2026-06-17 | Review by 2026-06-10 before catalyst window 2026-06-17.; Escalate if SPY confirms, delays, cancels, or changes the macro release window.; Bull/base/bear evidence changes the linked thesis 'rates-duration-risk'.; Position size, portfolio weight, or risk budget changes before the event. | rates-duration-risk | FOMC public calendar, https://example.com/fomc-calendar |
| high (78) | 2026-05-26 | twice_weekly | NVDA | product_launch 2026-06-02 | Review by 2026-05-26 before catalyst window 2026-06-02.; Escalate if NVDA confirms, delays, cancels, or changes the product launch window.; Bull/base/bear evidence changes the linked thesis 'ai-infrastructure-capex'.; Position size, portfolio weight, or risk budget changes before the event. | ai-infrastructure-capex | NVDA Computex keynote tracker, https://example.com/nvidia-computex-keynote, https://example.com/channel-check-gpu-supply |

## PFE - Pfizer Inc.

- Watch item: watch-demo-pfe-fda-2026
- Catalyst: demo-pfe-fda-2026 (regulatory_decision, 2026-05-20..2026-05-24)
- Priority: critical (100); urgency: high; review: stale
- Due: 2026-05-13 (due_now); cadence: daily_until_resolved
- Required action: verify_source
- Thesis ref: pharma-pipeline-reset; source ref: FDA calendar and PFE pipeline note
- Evidence links: https://example.com/fda-calendar, https://example.com/pfe-pipeline-update
- Trigger conditions:
  - Review by 2026-05-13 before catalyst window 2026-05-20..2026-05-24. -> verify_source
  - Escalate if PFE confirms, delays, cancels, or changes the regulatory decision window. -> update_status_and_history
  - Last review is stale by 15 days as of 2026-05-13. -> refresh_review_notes
  - Primary evidence changes, disappears, conflicts with another source, or lacks a dated update. -> verify_source
  - Bull/base/bear evidence changes the linked thesis 'pharma-pipeline-reset'. -> update_thesis_reference
  - Position size, portfolio weight, or risk budget changes before the event. -> refresh_exposure_context

## SPY - S&P 500 ETF Trust

- Watch item: watch-demo-fomc-june-2026
- Catalyst: demo-fomc-june-2026 (macro_release, 2026-06-17)
- Priority: high (79); urgency: medium; review: current
- Due: 2026-06-10 (scheduled); cadence: weekly
- Required action: monitor_date
- Thesis ref: rates-duration-risk; source ref: FOMC public calendar
- Evidence links: https://example.com/fomc-calendar
- Trigger conditions:
  - Review by 2026-06-10 before catalyst window 2026-06-17. -> monitor_date
  - Escalate if SPY confirms, delays, cancels, or changes the macro release window. -> update_status_and_history
  - Bull/base/bear evidence changes the linked thesis 'rates-duration-risk'. -> update_thesis_reference
  - Position size, portfolio weight, or risk budget changes before the event. -> refresh_exposure_context

## NVDA - NVIDIA Corporation

- Watch item: watch-demo-nvda-computex-2026
- Catalyst: demo-nvda-computex-2026 (product_launch, 2026-06-02)
- Priority: high (78); urgency: medium; review: current
- Due: 2026-05-26 (scheduled); cadence: twice_weekly
- Required action: monitor_date
- Thesis ref: ai-infrastructure-capex; source ref: NVDA Computex keynote tracker
- Evidence links: https://example.com/nvidia-computex-keynote, https://example.com/channel-check-gpu-supply
- Trigger conditions:
  - Review by 2026-05-26 before catalyst window 2026-06-02. -> monitor_date
  - Escalate if NVDA confirms, delays, cancels, or changes the product launch window. -> update_status_and_history
  - Bull/base/bear evidence changes the linked thesis 'ai-infrastructure-capex'. -> update_thesis_reference
  - Position size, portfolio weight, or risk budget changes before the event. -> refresh_exposure_context
