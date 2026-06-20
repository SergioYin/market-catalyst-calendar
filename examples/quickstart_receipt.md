# Market Catalyst Quickstart Receipt

Package: `market-catalyst-calendar`
Version: `0.1.0`
Input: `examples/demo_records.json`
Input SHA-256: `3a0b0365033176885cfa9a2f5208d6a0770894a9c86949ba3c869db5aa3898f4`
Records: 4
As of: `2026-05-13`
Days: 45

## Boundaries

- No live data: the receipt reads only the local input file and does not fetch market, news, or broker data.
- No broker integration: commands do not place, route, recommend, or simulate trades with a broker.
- No investment advice: outputs are deterministic research fixtures and operational checks, not personalized recommendations.

## Release Context

- Commit: `dc09a7a`
- Commit date: `2026-06-21T02:19:08+08:00`
- Latest tag: `v4.0.0`
- Subject: feat: add catalyst impact dashboard panel

## Exact Rerun Commands

- `python -m market_catalyst_calendar validate --input examples/demo_records.json`
- `python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json`
- `python -m market_catalyst_calendar brief --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- `python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json`
- `python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --fresh-after-days 14 --format json`
- `python -m market_catalyst_calendar quickstart-receipt --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json`

## Artifact Hashes

| Artifact | Bytes | SHA-256 | Command |
| --- | ---: | --- | --- |
| `upcoming.json` | 3861 | `bfefef8050a1e37694d68339903282a1e1902bcd6c74473dec827e10b3e9dc1d` | `python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json` |
| `brief.md` | 1371 | `dbf0252cacd2df04047953477b93fbc1fff0dd468eea831a044e08d778465579` | `python -m market_catalyst_calendar brief --input examples/demo_records.json --as-of 2026-05-13 --days 45` |
| `risk_budget.json` | 3572 | `85e34e4316e593de2f863ccb2d680bbdcad7606846256ff3645f26c35a985f5d` | `python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json` |
| `source_pack.json` | 6402 | `d4d4c6697765ed4d183d659db740c82fb4634590c14f9efc389ffd889909cc94` | `python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --fresh-after-days 14 --format json` |

## Fixture Hashes

| Fixture | Present | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `examples/demo_records.json` | true | 6771 | `3a0b0365033176885cfa9a2f5208d6a0770894a9c86949ba3c869db5aa3898f4` |
| `examples/upcoming.json` | true | 3861 | `bfefef8050a1e37694d68339903282a1e1902bcd6c74473dec827e10b3e9dc1d` |
| `examples/brief.md` | true | 1371 | `dbf0252cacd2df04047953477b93fbc1fff0dd468eea831a044e08d778465579` |
| `examples/risk_budget.json` | true | 3572 | `85e34e4316e593de2f863ccb2d680bbdcad7606846256ff3645f26c35a985f5d` |
| `examples/source_pack.json` | true | 6402 | `d4d4c6697765ed4d183d659db740c82fb4634590c14f9efc389ffd889909cc94` |
| `examples/version_report.json` | true | 948 | `39098724260fda74ceed14cd596dec17ab0c94b8c6e2af55c0ec9a409aa92b2b` |
