# Market Catalyst Visual Evidence Receipt

Status: PASS
Artifacts: 5

## Boundaries

- Static-only: receipt evidence is limited to checked-in dashboard, report, and demo artifacts.
- Local fixtures only: regeneration commands use bundled example records.
- No live data: receipt generation does not fetch market, news, or broker data.
- No broker integration: artifacts do not connect to brokers.
- No orders: artifacts do not route orders, place orders, recommend trades, or simulate order execution.
- No personalized investment advice: artifacts are deterministic public research demos, not recommendations for any person or account.
- No private data: receipt targets use bundled demo fixtures and exclude account identifiers, credentials, and personal data.

## Artifacts

| Path | Role | Route | Bytes | SHA-256 | Regenerate | Capture |
| --- | --- | --- | ---: | --- | --- | --- |
| `examples/dashboard.html` | `static-html-dashboard` | `/examples/dashboard.html` | 15597 | `a6c96ec8940e69aff13338b7ba954d96fb2963d4fbd4d53e26cba492c2fd2ed4` | `python -m market_catalyst_calendar html-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/dashboard.html` | `open examples/dashboard.html` |
| `examples/impact_dashboard.md` | `markdown-impact-dashboard` | `/examples/impact_dashboard.md` | 1354 | `2408f81c9d53b684313c49215357132b0e506abc9c0295df5ed48454b6b5ad58` | `python -m market_catalyst_calendar impact-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/impact_dashboard.md` | `open examples/impact_dashboard.md` |
| `examples/impact_dashboard.json` | `machine-readable-impact-dashboard` | `/examples/impact_dashboard.json` | 3625 | `15b20ffab5185a0a581467630fdca920fc81ee4bef28a5444442caa4c38d25b0` | `python -m market_catalyst_calendar impact-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format json > examples/impact_dashboard.json` | `python -m json.tool examples/impact_dashboard.json` |
| `examples/impact_brief.md` | `markdown-impact-report` | `/examples/impact_brief.md` | 3522 | `90188731ad7ded160244fb18a7dca8dded8c119df87a8455532ad8f1bf3618f6` | `python -m market_catalyst_calendar impact-brief --input examples/demo_records.json --as-of 2026-05-13 --days 45 > examples/impact_brief.md` | `open examples/impact_brief.md` |
| `examples/agent_handoff.md` | `markdown-demo-handoff` | `/examples/agent_handoff.md` | 3581 | `b2a07d0943264d3ec26c0d596026de155148e5dd7fa332a1ff1a1f53ce53b069` | `python -m market_catalyst_calendar agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown > examples/agent_handoff.md` | `open examples/agent_handoff.md` |
