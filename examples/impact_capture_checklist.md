# Market Catalyst Impact Capture Checklist

Status: PASS
Root: `.`
Items: 4

## Boundaries

- No live data: capture uses checked-in local fixtures only and does not fetch market, news, or broker data.
- No broker integration: capture commands do not place, route, recommend, or simulate trades with a broker.
- No predictions: captured artifacts preserve deterministic scenario context only and do not forecast outcomes.
- No investment advice: captured artifacts are deterministic public research examples, not personalized recommendations.
- No private data: capture targets exclude account identifiers, holdings, credentials, and personal data.

## Checklist

| Done | Artifact | Source fixture | Output artifact | Bytes | SHA-256 | Capture target | Render command |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| [ ] | `impact-brief` | `examples/demo_records.json` | `examples/impact_brief.md` | 3522 | `90188731ad7ded160244fb18a7dca8dded8c119df87a8455532ad8f1bf3618f6` | public-safe screenshot or GIF of the Markdown impact brief boundary, summary, ranked catalysts, and scenario context | `python -m market_catalyst_calendar impact-brief --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/impact_brief.md` |
| [ ] | `impact-dashboard` | `examples/demo_records.json` | `examples/impact_dashboard.md` | 1354 | `2408f81c9d53b684313c49215357132b0e506abc9c0295df5ed48454b6b5ad58` | public-safe screenshot or GIF of the Markdown impact dashboard summary, evidence states, top attention table, and review queue | `python -m market_catalyst_calendar impact-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/impact_dashboard.md` |
| [ ] | `impact-compare` | `examples/demo_records.json; examples/demo_records_updated.json` | `examples/impact_compare.md` | 1990 | `3bcad5d758aecf1c8dacd64ef58549c2039bc92a5ce8a047ffb188b3467d1a26` | public-safe screenshot or GIF of the Markdown impact comparison summary, added/removed/changed rows, and impact movements | `python -m market_catalyst_calendar impact-compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 --format markdown > examples/impact_compare.md` |
| [ ] | `impact-artifact-receipt` | `examples/demo_records.json; examples/demo_records_updated.json; checked-in impact examples` | `examples/impact_artifact_receipt.md` | 2886 | `03725b56be7b183a861970c86692905d5bcc53b8e0002205a248e37d955eed76` | public-safe screenshot or GIF of the Markdown impact artifact receipt boundaries, rerun commands, paths, bytes, and hashes | `python -m market_catalyst_calendar impact-artifact-receipt --root . --format markdown > examples/impact_artifact_receipt.md` |
