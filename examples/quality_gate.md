# Market Catalyst Quality Gate

Status: FAIL
Profile: public
As of: 2026-05-13
Minimum evidence URLs: 2
Maximum review age: 14 days
Maximum evidence age: 14 days
Maximum broker age: 30 days

Failed records: 4 of 4

| Severity | Code | Rule | Ticker | Record | Detail |
| --- | --- | --- | --- | --- | --- |
| critical | MCC-QG-SOURCE-001 | no_placeholder_urls | MSFT | demo-msft-earnings-2026 | evidence URL https://example.com/msft-q3-earnings is a placeholder host |
| high | MCC-QG-EVIDENCE-003 | minimum_evidence | PFE | demo-pfe-fda-2026 | evidence metadata is 15 days old; maximum is 14 |
| high | MCC-QG-REVIEW-002 | review_freshness | PFE | demo-pfe-fda-2026 | last review is 15 days old; maximum is 14 |
| critical | MCC-QG-SOURCE-001 | no_placeholder_urls | PFE | demo-pfe-fda-2026 | evidence URL https://example.com/fda-calendar is a placeholder host |
| critical | MCC-QG-SOURCE-001 | no_placeholder_urls | PFE | demo-pfe-fda-2026 | evidence URL https://example.com/pfe-pipeline-update is a placeholder host |
| critical | MCC-QG-SOURCE-002 | no_placeholder_urls | PFE | demo-pfe-fda-2026 | broker URL for Summit Research (https://example.com/pfe-broker-summit) is a placeholder host |
| critical | MCC-QG-SOURCE-002 | no_placeholder_urls | PFE | demo-pfe-fda-2026 | broker URL for Harbor Life Sciences (https://example.com/pfe-broker-harbor) is a placeholder host |
| medium | MCC-QG-BROKER-004 | broker_caveats | PFE | demo-pfe-fda-2026 | Summit Research broker view is 33 days old; maximum is 30 |
| critical | MCC-QG-SOURCE-001 | no_placeholder_urls | NVDA | demo-nvda-computex-2026 | evidence URL https://example.com/nvidia-computex-keynote is a placeholder host |
| critical | MCC-QG-SOURCE-001 | no_placeholder_urls | NVDA | demo-nvda-computex-2026 | evidence URL https://example.com/channel-check-gpu-supply is a placeholder host |
| critical | MCC-QG-SOURCE-002 | no_placeholder_urls | NVDA | demo-nvda-computex-2026 | broker URL for Metro Capital Markets (https://example.com/nvda-broker-metro) is a placeholder host |
| critical | MCC-QG-SOURCE-002 | no_placeholder_urls | NVDA | demo-nvda-computex-2026 | broker URL for North Coast Securities (https://example.com/nvda-broker-north-coast) is a placeholder host |
| medium | MCC-QG-BROKER-004 | broker_caveats | NVDA | demo-nvda-computex-2026 | Metro Capital Markets broker view is 38 days old; maximum is 30 |
| critical | MCC-QG-EVIDENCE-001 | minimum_evidence | SPY | demo-fomc-june-2026 | 1 evidence URLs present; 2 required |
| high | MCC-QG-EVIDENCE-002 | minimum_evidence | SPY | demo-fomc-june-2026 | evidence_checked_at is missing |
| critical | MCC-QG-SOURCE-001 | no_placeholder_urls | SPY | demo-fomc-june-2026 | evidence URL https://example.com/fomc-calendar is a placeholder host |

## MSFT - Microsoft Corporation

- Record: demo-msft-earnings-2026
- Window: 2026-05-06; status: completed
- Failed rules: no_placeholder_urls
- Next action: replace placeholder URLs with public source URLs.

## PFE - Pfizer Inc.

- Record: demo-pfe-fda-2026
- Window: 2026-05-20..2026-05-24; status: watching
- Failed rules: broker_caveats, minimum_evidence, no_placeholder_urls, review_freshness
- Next action: add independent evidence URLs and refresh evidence metadata; refresh analyst review date; replace placeholder URLs with public source URLs; refresh broker views and document explicit caveats.

## NVDA - NVIDIA Corporation

- Record: demo-nvda-computex-2026
- Window: 2026-06-02; status: scheduled
- Failed rules: broker_caveats, no_placeholder_urls
- Next action: replace placeholder URLs with public source URLs; refresh broker views and document explicit caveats.

## SPY - S&P 500 ETF Trust

- Record: demo-fomc-june-2026
- Window: 2026-06-17; status: confirmed
- Failed rules: minimum_evidence, no_placeholder_urls
- Next action: add independent evidence URLs and refresh evidence metadata; replace placeholder URLs with public source URLs.
