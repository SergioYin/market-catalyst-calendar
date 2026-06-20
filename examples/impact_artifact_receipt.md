# Market Catalyst Impact Artifact Receipt

Status: PASS
Root: `.`
Artifacts: 6

## Boundaries

- No live data: receipt evidence is limited to checked-in local fixtures and does not fetch market, news, or broker data.
- No broker integration: rerun commands do not place, route, recommend, or simulate trades with a broker.
- No prediction: artifacts summarize supplied catalyst records and do not forecast prices, returns, or outcomes.
- No investment advice: artifacts are deterministic public research examples, not personalized recommendations.

## Artifacts

| Artifact | Schema | Inputs | Output | Bytes | SHA-256 | Rerun |
| --- | --- | --- | --- | ---: | --- | --- |
| `impact_brief.json` | `impact-brief/v1` | `examples/demo_records.json` | `examples/impact_brief.json` | 4933 | `dd70eda12bdf42e33a1083b96b7b3848b25d312c1731b866bbbd57eed713607f` | `python -m market_catalyst_calendar impact-brief --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json > examples/impact_brief.json` |
| `impact_brief.md` | `impact-brief/markdown` | `examples/demo_records.json` | `examples/impact_brief.md` | 3522 | `90188731ad7ded160244fb18a7dca8dded8c119df87a8455532ad8f1bf3618f6` | `python -m market_catalyst_calendar impact-brief --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/impact_brief.md` |
| `impact_dashboard.json` | `impact-dashboard/v1` | `examples/demo_records.json` | `examples/impact_dashboard.json` | 3625 | `15b20ffab5185a0a581467630fdca920fc81ee4bef28a5444442caa4c38d25b0` | `python -m market_catalyst_calendar impact-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json > examples/impact_dashboard.json` |
| `impact_dashboard.md` | `impact-dashboard/markdown` | `examples/demo_records.json` | `examples/impact_dashboard.md` | 1354 | `2408f81c9d53b684313c49215357132b0e506abc9c0295df5ed48454b6b5ad58` | `python -m market_catalyst_calendar impact-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/impact_dashboard.md` |
| `impact_compare.json` | `impact-compare/v1` | `examples/demo_records.json`, `examples/demo_records_updated.json` | `examples/impact_compare.json` | 3897 | `7cabbf2036d42d7c2014de013af356d5fbaa03291d13c9c8367c83b3d2df3a96` | `python -m market_catalyst_calendar impact-compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 > examples/impact_compare.json` |
| `impact_compare.md` | `impact-compare/markdown` | `examples/demo_records.json`, `examples/demo_records_updated.json` | `examples/impact_compare.md` | 1990 | `3bcad5d758aecf1c8dacd64ef58549c2039bc92a5ce8a047ffb188b3467d1a26` | `python -m market_catalyst_calendar impact-compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 --format markdown > examples/impact_compare.md` |
