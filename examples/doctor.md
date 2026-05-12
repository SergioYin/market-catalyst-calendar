# Market Catalyst Dataset Doctor

Status: NEEDS REPAIR
Profile: public
As of: 2026-05-13
Read-only: yes

Diagnostics: 16
Suggested patch operations: 16
Manual actions: 0

## Suggested Repairs

| Code | Record | Operation | Path | Reason |
| --- | --- | --- | --- | --- |
| MCC-QG-SOURCE-002 | demo-nvda-computex-2026 | replace | /records/0/broker_views/0/source_url | replace placeholder broker URL with a real public source URL |
| MCC-QG-BROKER-004 | demo-nvda-computex-2026 | replace | /records/0/broker_views/1/as_of | refresh broker view date after source review |
| MCC-QG-SOURCE-002 | demo-nvda-computex-2026 | replace | /records/0/broker_views/1/source_url | replace placeholder broker URL with a real public source URL |
| MCC-QG-SOURCE-001 | demo-nvda-computex-2026 | replace | /records/0/evidence_urls/0 | replace placeholder evidence URL with a real public source URL |
| MCC-QG-SOURCE-001 | demo-nvda-computex-2026 | replace | /records/0/evidence_urls/1 | replace placeholder evidence URL with a real public source URL |
| MCC-QG-SOURCE-001 | demo-msft-earnings-2026 | replace | /records/1/evidence_urls/0 | replace placeholder evidence URL with a real public source URL |
| MCC-QG-SOURCE-002 | demo-pfe-fda-2026 | replace | /records/2/broker_views/0/source_url | replace placeholder broker URL with a real public source URL |
| MCC-QG-BROKER-004 | demo-pfe-fda-2026 | replace | /records/2/broker_views/1/as_of | refresh broker view date after source review |
| MCC-QG-SOURCE-002 | demo-pfe-fda-2026 | replace | /records/2/broker_views/1/source_url | replace placeholder broker URL with a real public source URL |
| MCC-QG-EVIDENCE-003 | demo-pfe-fda-2026 | replace | /records/2/evidence_checked_at | refresh evidence freshness metadata |
| MCC-QG-SOURCE-001 | demo-pfe-fda-2026 | replace | /records/2/evidence_urls/0 | replace placeholder evidence URL with a real public source URL |
| MCC-QG-SOURCE-001 | demo-pfe-fda-2026 | replace | /records/2/evidence_urls/1 | replace placeholder evidence URL with a real public source URL |
| MCC-QG-REVIEW-002 | demo-pfe-fda-2026 | replace | /records/2/last_reviewed | refresh analyst review date |
| MCC-QG-EVIDENCE-002 | demo-fomc-june-2026 | add | /records/3/evidence_checked_at | refresh evidence freshness metadata |
| MCC-QG-EVIDENCE-001 | demo-fomc-june-2026 | add | /records/3/evidence_urls/- | add an independent evidence URL |
| MCC-QG-SOURCE-001 | demo-fomc-june-2026 | replace | /records/3/evidence_urls/0 | replace placeholder evidence URL with a real public source URL |

## Next Steps

- Review suggested values before applying them; placeholder replacement URLs are deterministic prompts, not verified sources.
- After editing a copy of the dataset, rerun validate --profile public and quality-gate --profile public.
