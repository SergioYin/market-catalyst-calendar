# Market Catalyst Impact Receipt Compare

Schema: `impact-receipt-compare/v1`
Status: PASS
Base: `examples/impact_artifact_receipt.json`
Current: `examples/impact_artifact_receipt.json`

Summary: 0 added, 0 removed, 0 changed, 6 unchanged; boundaries match.

## Limitations

- Static receipt comparison only: inputs are existing local JSON receipts and no market, news, or broker data is fetched.
- Non-advisory evidence: output reports artifact drift and does not recommend trades, positions, or investment actions.
- Hash-based artifact drift: changed entries are based on receipt metadata such as schema labels, bytes, hashes, and rerun commands.

## Boundary Check

| Check | Result |
| --- | --- |
| base receipt ok | True |
| current receipt ok | True |
| boundary text match | True |

## Added Artifacts

No added artifacts.


## Removed Artifacts

No removed artifacts.


## Changed Artifacts

No changed artifacts.


## Unchanged Artifacts

| Artifact | Schema | Bytes | SHA-256 | Rerun |
| --- | --- | ---: | --- | --- |
| examples/impact_brief.json | impact-brief/v1 | 4933 | dd70eda12bdf42e33a1083b96b7b3848b25d312c1731b866bbbd57eed713607f | python -m market_catalyst_calendar impact-brief --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json > examples/impact_brief.json |
| examples/impact_brief.md | impact-brief/markdown | 3522 | 90188731ad7ded160244fb18a7dca8dded8c119df87a8455532ad8f1bf3618f6 | python -m market_catalyst_calendar impact-brief --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/impact_brief.md |
| examples/impact_compare.json | impact-compare/v1 | 3897 | 7cabbf2036d42d7c2014de013af356d5fbaa03291d13c9c8367c83b3d2df3a96 | python -m market_catalyst_calendar impact-compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 > examples/impact_compare.json |
| examples/impact_compare.md | impact-compare/markdown | 1990 | 3bcad5d758aecf1c8dacd64ef58549c2039bc92a5ce8a047ffb188b3467d1a26 | python -m market_catalyst_calendar impact-compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 --format markdown > examples/impact_compare.md |
| examples/impact_dashboard.json | impact-dashboard/v1 | 3625 | 15b20ffab5185a0a581467630fdca920fc81ee4bef28a5444442caa4c38d25b0 | python -m market_catalyst_calendar impact-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json > examples/impact_dashboard.json |
| examples/impact_dashboard.md | impact-dashboard/markdown | 1354 | 2408f81c9d53b684313c49215357132b0e506abc9c0295df5ed48454b6b5ad58 | python -m market_catalyst_calendar impact-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/impact_dashboard.md |
