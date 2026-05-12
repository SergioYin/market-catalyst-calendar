# NVDA Catalyst Drilldown

As of: 2026-05-13
Scope: single-ticker dossier for the next 45 days; stale after 14 days.

| Metric | Value |
| --- | ---: |
| Records | 1 |
| Upcoming events | 1 |
| Broker views | 2 |
| Sources | 4 |
| Watch items | 1 |
| Decision memos | 1 |
| Post-event queue | 0 |

## Record Ledger

| Score | Window | Event | Status | Review | Impact | Thesis |
| ---: | --- | --- | --- | --- | --- | --- |
| 84 | 2026-06-02 | product launch | scheduled | current | positive | ai-infrastructure-capex |

## Upcoming Events

As of: 2026-05-13

| Score | Window | Ticker | Event | Status | Review | Impact |
| ---: | --- | --- | --- | --- | --- | --- |
| 84 | 2026-06-02 | NVDA | product launch | scheduled | current | positive |

### NVDA - NVIDIA Corporation

- Event: product launch (2026-06-02)
- Score: 84; urgency: medium; review: current
- Required action: monitor_date
- Thesis impact: positive
- Base scenario: Product roadmap details support existing accelerator growth expectations.
- Evidence: https://example.com/nvidia-computex-keynote, https://example.com/channel-check-gpu-supply

## Thesis Map

As of: 2026-05-13
Stale after: 14 days

| Thesis | Open Events | Highest Score | Stale | Records | Evidence References |
| --- | ---: | ---: | ---: | --- | --- |
| ai-infrastructure-capex | 1 | 84 | 0 | demo-nvda-computex-2026 | NVDA Computex keynote tracker, https://example.com/channel-check-gpu-supply, https://example.com/nvidia-computex-keynote |

## Broker Matrix

As of: 2026-05-13
Stale broker source after: 30 days

| Ticker | Thesis | Views | Target Avg | Target Range | Dispersion | Stale Sources | Linked Catalysts |
| --- | --- | ---: | ---: | --- | ---: | --- | --- |
| NVDA | ai-infrastructure-capex | 2 | 1202.50 | 1085.00-1320.00 | 235.00 | Metro Capital Markets | demo-nvda-computex-2026 |

### NVDA - ai-infrastructure-capex

| Institution | Rating | Target | As Of | Age | Caveat | Source |
| --- | --- | ---: | --- | ---: | --- | --- |
| Metro Capital Markets | hold | 1085.00 | 2026-04-05 | 38 | Older view predates the final Computex keynote agenda. | https://example.com/nvda-broker-metro |
| North Coast Securities | buy | 1320.00 | 2026-05-10 | 3 | Target assumes accelerator backlog converts into second-half revenue. | https://example.com/nvda-broker-north-coast |

## Risk Budget

As of: 2026-05-13

Total catalysts: 1
Aggregate risk budget: 60,000.00
Aggregate max loss: 52,000.00
Aggregate expected event loss: 32,323.20
Over-budget groups: 0
Over-budget catalysts: 0

| Ticker | Thesis | Urgency | Records | Budget | Max Loss | Expected Loss | Utilization | Flags |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| NVDA | ai-infrastructure-capex | medium | 1 | 60,000.00 | 52,000.00 | 32,323.20 | 0.87x | none |

## Watchlist

As of: 2026-05-13
Scope: open catalysts due or starting within 45 days; stale after 14 days.

| Priority | Due | Cadence | Ticker | Catalyst | Triggers | Thesis | Sources |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high (78) | 2026-05-26 | twice_weekly | NVDA | product_launch 2026-06-02 | Review by 2026-05-26 before catalyst window 2026-06-02.; Escalate if NVDA confirms, delays, cancels, or changes the product launch window.; Bull/base/bear evidence changes the linked thesis 'ai-infrastructure-capex'.; Position size, portfolio weight, or risk budget changes before the event. | ai-infrastructure-capex | NVDA Computex keynote tracker, https://example.com/nvidia-computex-keynote, https://example.com/channel-check-gpu-supply |

### NVDA - NVIDIA Corporation

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

## Post-Event Queue

As of: 2026-05-13
Scope: completed catalysts plus events whose window ended at least 0 days ago and still need outcome review.

No catalysts need post-event outcome review.

## Source Pack

As of: 2026-05-13
Fresh after: 14 days

| Freshness | Uses | Type | Tickers | Thesis IDs | Checked | URL |
| --- | ---: | --- | --- | --- | --- | --- |
| stale | 1 | broker | NVDA | ai-infrastructure-capex | 2026-04-05 | https://example.com/nvda-broker-metro |
| fresh | 1 | evidence | NVDA | ai-infrastructure-capex | 2026-05-09 | https://example.com/channel-check-gpu-supply |
| fresh | 1 | broker | NVDA | ai-infrastructure-capex | 2026-05-10 | https://example.com/nvda-broker-north-coast |
| fresh | 1 | evidence | NVDA | ai-infrastructure-capex | 2026-05-09 | https://example.com/nvidia-computex-keynote |

## Decision Logs

As of: 2026-05-13
Scope: open catalysts due or starting within 45 days; stale after 14 days.

### NVDA - NVIDIA Corporation

- Memo id: decision-demo-nvda-computex-2026
- Decision owner: TBD
- Decision status: draft
- Prepared on: 2026-05-13

#### Thesis

- Thesis id: ai-infrastructure-capex
- Current impact: positive
- Working thesis: Product roadmap details support existing accelerator growth expectations.
- Decision question: Does the product launch change the thesis for NVDA?

#### Catalyst

- Catalyst id: demo-nvda-computex-2026
- Event: product_launch (2026-06-02)
- Status: scheduled; confidence: 0.74; score: 84
- Urgency: medium; review: current; required action: monitor_date

#### Evidence

- Source ref: NVDA Computex keynote tracker
- Evidence checked at: 2026-05-09
- Evidence URLs:
  - https://example.com/nvidia-computex-keynote
  - https://example.com/channel-check-gpu-supply

#### Scenarios

- bull: score 90; impact positive; date 2026-06-02; action none; note: Management confirms accelerated platform demand and shorter supply constraints.
- base: score 84; impact positive; date 2026-06-02; action monitor_date; note: Product roadmap details support existing accelerator growth expectations.
- bear: score 74; impact less_positive; date 2026-06-02; action none; note: Launch focuses on refresh timing without incremental demand signals.

#### Broker Context

- View count: 2; target range: 1085.00-1320.00; average target: 1202.50; stale views: 1
  - Metro Capital Markets hold 1085.00 as of 2026-04-05; caveat: Older view predates the final Computex keynote agenda.; source: https://example.com/nvda-broker-metro
  - North Coast Securities buy 1320.00 as of 2026-05-10; caveat: Target assumes accelerator backlog converts into second-half revenue.; source: https://example.com/nvda-broker-north-coast

#### Watchlist Triggers

- [review_due] Review by 2026-05-26 before catalyst window 2026-06-02. -> monitor_date
- [event_window] Escalate if NVDA confirms, delays, cancels, or changes the product launch window. -> update_status_and_history
- [thesis_link] Bull/base/bear evidence changes the linked thesis 'ai-infrastructure-capex'. -> update_thesis_reference
- [exposure_change] Position size, portfolio weight, or risk budget changes before the event. -> refresh_exposure_context

#### Decision Slots

- Pre-event decision: TBD
- Position action: TBD
- Risk limit or hedge: TBD
- Follow-up owner: TBD

#### Post-Event Review

- Review due: 2026-06-02
- Outcome: TBD
- Thesis update: TBD
- Evidence delta: TBD
- Scenario accuracy: TBD
- Next action: TBD
