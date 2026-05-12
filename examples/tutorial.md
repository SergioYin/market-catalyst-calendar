# Market Catalyst Calendar Tutorial

This is a notebooks-free walkthrough generated from the built-in demo dataset. It is deterministic, offline, and designed to be run from a shell with only the Python standard library.

## Tutorial Parameters

| Parameter | Value |
| --- | --- |
| Demo dataset date | 2026-05-13 |
| Report as-of date | 2026-05-13 |
| Forward window | 45 days |
| Demo records | 4 |
| Dataset path used in commands | `examples/demo_records.json` |

## 1. Create the Demo Dataset

Start by materializing the canonical input JSON. The rest of the tutorial assumes this file path.

Command:

```bash
python -m market_catalyst_calendar export-demo > examples/demo_records.json
```

Expected exit code: `0`

Expected output excerpt:

```text
{
  "as_of": "2026-05-13",
  "record_count": 4,
  "record_ids": [
    "demo-msft-earnings-2026",
    "demo-pfe-fda-2026",
    "demo-nvda-computex-2026",
    "demo-fomc-june-2026"
  ],
  "status_counts": {
    "completed": 1,
    "confirmed": 1,
    "scheduled": 1,
    "watching": 1
  }
}
```

Learning checkpoint: You can identify the dataset date, four record ids, and the mix of completed, watching, scheduled, and confirmed records.

## 2. Validate the Record Shape

Run the structural validator before trusting any report output.

Command:

```bash
python -m market_catalyst_calendar validate --input examples/demo_records.json
```

Expected exit code: `0`

Expected output excerpt:

```json
{
  "ok": true,
  "record_count": 4
}
```

Learning checkpoint: Validation passes with `ok: true`; any schema or record consistency issue should block downstream briefing work.

## 3. Rank the Forward Catalyst Queue

List upcoming open catalysts in the forward window and inspect the scores that drive later reports.

Command:

```bash
python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45
```

Expected exit code: `0`

Expected output excerpt:

```json
{
  "as_of": "2026-05-13",
  "records": [
    {
      "catalyst_score": 87,
      "days_until": 7,
      "id": "demo-pfe-fda-2026",
      "ticker": "PFE",
      "urgency": "high",
      "window": "2026-05-20..2026-05-24"
    },
    {
      "catalyst_score": 84,
      "days_until": 20,
      "id": "demo-nvda-computex-2026",
      "ticker": "NVDA",
      "urgency": "medium",
      "window": "2026-06-02"
    },
    {
      "catalyst_score": 83,
      "days_until": 35,
      "id": "demo-fomc-june-2026",
      "ticker": "SPY",
      "urgency": "medium",
      "window": "2026-06-17"
    }
  ]
}
```

Learning checkpoint: The highest-priority item is PFE because it is near term, high confidence, and tied to a regulatory decision.

## 4. Observe a Publication Quality Failure

The demo data intentionally uses placeholder URLs, so the public quality gate exits with status 1 while still producing useful diagnostics.

Command:

```bash
python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13
```

Expected exit code: `1`

Expected output excerpt:

```json
{
  "failed_record_count": 4,
  "first_record": {
    "failed_rules": [
      "no_placeholder_urls"
    ],
    "id": "demo-msft-earnings-2026",
    "issue_codes": [
      "MCC-QG-SOURCE-001"
    ],
    "ticker": "MSFT"
  },
  "ok": false
}
```

Learning checkpoint: The nonzero exit is expected here; the learning target is recognizing blocking diagnostic codes before handoff.

## 5. Connect Catalysts to Risk

Use the risk-budget report to translate event records into over-budget and expected-loss review items.

Command:

```bash
python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown
```

Expected exit code: `0`

Expected output excerpt:

```markdown
# Market Catalyst Risk Budget

As of: 2026-05-13

Total catalysts: 3
Aggregate risk budget: 160,000.00
Aggregate max loss: 174,000.00
Aggregate expected event loss: 118,484.40
Over-budget groups: 2
Over-budget catalysts: 2

| Ticker | Thesis | Urgency | Records | Budget | Max Loss | Expected Loss | Utilization | Flags |
...
```

Learning checkpoint: Two upcoming catalysts are over budget; that is the prompt for position sizing or thesis review before the event window.

## 6. Prepare a Source Collection List

Export a deduplicated source inventory that another analyst or offline agent can work through.

Command:

```bash
python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format csv
```

Expected exit code: `0`

Expected output excerpt:

```csv
url,source_types,usage_count,tickers,thesis_ids,record_ids,evidence_checked_at,freshness_age_days,freshness_state,broker_institutions,broker_as_of_dates
https://example.com/fomc-calendar,evidence,1,SPY,rates-duration-risk,demo-fomc-june-2026,missing,missing,missing,,
https://example.com/fda-calendar,evidence,1,PFE,pharma-pipeline-reset,demo-pfe-fda-2026,2026-04-28,15,stale,,
https://example.com/nvda-broker-metro,broker,1,NVDA,ai-infrastructure-capex,demo-nvda-computex-2026,2026-04-05,38,stale,Metro Capital Markets,2026-04-05
https://example.com/pfe-broker-summit,broker,1,PFE,pharma-pipeline-reset,demo-pfe-fda-2026,2026-04-10,33,stale,Summit Research,2026-04-10
...
```

Learning checkpoint: Each source row preserves URL, usage, linked tickers, record ids, and freshness state without fetching the network.

## 7. Drill Into One Ticker

Compose a single-name dossier when a record needs focused review.

Command:

```bash
python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45 --format markdown
```

Expected exit code: `0`

Expected output excerpt:

```markdown
# NVDA Catalyst Drilldown
## Record Ledger
## Upcoming Events
### NVDA - NVIDIA Corporation
## Thesis Map
## Broker Matrix
### NVDA - ai-infrastructure-capex
## Risk Budget
## Watchlist
### NVDA - NVIDIA Corporation
```

Learning checkpoint: The dossier combines record ledger, upcoming events, thesis map, broker matrix, risk budget, watchlist, source pack, and decision logs for one ticker.

## 8. Compare a Later Snapshot

Generate the updated demo snapshot and compare it with the base dataset to see status, evidence, and thesis-impact changes.

Command:

```bash
python -m market_catalyst_calendar export-demo --snapshot updated > examples/demo_records_updated.json
python -m market_catalyst_calendar compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 --format markdown
```

Expected exit code: `0`

Expected output excerpt:

```markdown
# Market Catalyst Snapshot Compare

As of: 2026-05-27
Base snapshot: 2026-05-13
Current snapshot: 2026-05-27

Summary: 1 added, 1 removed, 2 changed, 2 score changes, 2 status transitions, 2 evidence changes, 1 thesis-impact change.

## Added Events

| Score | Window | Ticker | Event | Status | Impact | ID |
| ---: | --- | --- | --- | --- | --- | --- |
| 75 | 2026-06-12 | AMZN | product launch | watching | mixed | demo-amzn-kuiper-2026 |

...
```

Learning checkpoint: Snapshot comparison separates added, removed, and changed records so dataset refreshes can be reviewed without losing provenance.

## Completion Checklist

- [ ] Demo data was exported and validated.
- [ ] Upcoming catalyst priority was checked against event timing and score.
- [ ] Public quality-gate failures were treated as expected tutorial diagnostics, not ignored production failures.
- [ ] Risk-budget and source-pack outputs were reviewed for handoff-ready context.
- [ ] Single-ticker drilldown and snapshot compare were used to move from daily queue to deeper review.
