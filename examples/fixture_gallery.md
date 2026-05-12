# Market Catalyst Fixture Gallery

Bundled fixtures are deterministic outputs generated from the built-in demo datasets.
Hashes are SHA-256 digests of the exact fixture bytes.

## Summary

- Fixtures: 56
- csv: 2
- html: 1
- ics: 1
- json: 29
- markdown: 23

## Fixtures

| Fixture | Type | Exit | SHA-256 | Recommended use |
| --- | --- | ---: | --- | --- |
| `examples/demo_records.json` | json | 0 | `3a0b036503317688` | Start from a deterministic catalyst dataset. |
| `examples/presets.json` | json | 0 | `c66813f4d714ee66` | Inspect deterministic fixture output. |
| `examples/upcoming.json` | json | 0 | `bfefef8050a1e376` | List open catalysts in a forward window. |
| `examples/stale.json` | json | 0 | `a48095b11073803d` | List records whose review state is stale. |
| `examples/brief.md` | markdown | 0 | `dbf0252cacd2df04` | Review a concise analyst packet for upcoming catalysts. |
| `examples/exposure.json` | json | 0 | `5332b8522213a83d` | Aggregate portfolio exposure for upcoming catalysts. |
| `examples/exposure.md` | markdown | 0 | `b5d363ee9ced2aed` | Aggregate portfolio exposure for upcoming catalysts. |
| `examples/risk_budget.json` | json | 0 | `85e34e4316e593de` | Compare event max-loss estimates against risk budgets. |
| `examples/risk_budget.md` | markdown | 0 | `70559081dafa6bf9` | Compare event max-loss estimates against risk budgets. |
| `examples/sector_map.json` | json | 0 | `4f63e3091978a673` | Group catalyst exposure by sector and theme. |
| `examples/sector_map.md` | markdown | 0 | `463e6cd8911c92cf` | Group catalyst exposure by sector and theme. |
| `examples/review_plan.json` | json | 0 | `32da9b6ce6a5982c` | List stale and high-urgency records needing analyst action. |
| `examples/review_plan.md` | markdown | 0 | `94b566c91c858829` | List stale and high-urgency records needing analyst action. |
| `examples/thesis_map.json` | json | 0 | `21656c1ec3cb9673` | Group catalysts by investment thesis and source references. |
| `examples/thesis_map.md` | markdown | 0 | `2ba33fe8d536219e` | Group catalysts by investment thesis and source references. |
| `examples/scenario_matrix.json` | json | 0 | `51d449cf7c53483f` | Review bull/base/bear event scenarios for upcoming catalysts. |
| `examples/scenario_matrix.md` | markdown | 0 | `ca3f82dc602c911d` | Review bull/base/bear event scenarios for upcoming catalysts. |
| `examples/evidence_audit.json` | json | 0 | `977078f8ca4c1089` | Find stale, thin, or concentrated evidence metadata. |
| `examples/evidence_audit.md` | markdown | 0 | `070654151c93d676` | Find stale, thin, or concentrated evidence metadata. |
| `examples/quality_gate.json` | json | 1 | `eb2268844dd6602a` | Exercise public research quality diagnostics and nonzero exits. |
| `examples/quality_gate.md` | markdown | 1 | `44717b8d6ca70ae1` | Exercise public research quality diagnostics and nonzero exits. |
| `examples/doctor.json` | json | 0 | `1165debea9fecec0` | Inspect deterministic fixture output. |
| `examples/doctor.md` | markdown | 0 | `066999808460718e` | Inspect deterministic fixture output. |
| `examples/doctor_patch.json` | json | 0 | `30575d1933995014` | Inspect deterministic fixture output. |
| `examples/broker_matrix.json` | json | 0 | `c963e69b50181965` | Inspect broker view dispersion and stale broker-source flags. |
| `examples/broker_matrix.md` | markdown | 0 | `ae5ab28c6dc7707f` | Inspect broker view dispersion and stale broker-source flags. |
| `examples/source_pack.json` | json | 0 | `d4d4c6697765ed4d` | Export deduplicated evidence and broker source inventories. |
| `examples/source_pack.csv` | csv | 0 | `fc6634f680e27d20` | Export deduplicated evidence and broker source inventories. |
| `examples/source_pack.md` | markdown | 0 | `0cd02c8f70b1b8f3` | Export deduplicated evidence and broker source inventories. |
| `examples/watchlist.json` | json | 0 | `6ba1e1001eed110e` | Convert open catalysts into prioritized watch items. |
| `examples/watchlist.md` | markdown | 0 | `221c458506cac4df` | Convert open catalysts into prioritized watch items. |
| `examples/decision_log.json` | json | 0 | `51e52df0cf03f1c4` | Create pre-event decision memo stubs without inventing conclusions. |
| `examples/decision_log.md` | markdown | 0 | `857e24ea08ca100f` | Create pre-event decision memo stubs without inventing conclusions. |
| `examples/drilldown.json` | json | 0 | `17a2a1b2ed2504b9` | Inspect a complete single-ticker dossier. |
| `examples/drilldown.md` | markdown | 0 | `20b1838fbde5f48f` | Inspect a complete single-ticker dossier. |
| `examples/command_cookbook.md` | markdown | 0 | `3cc6c1ab23900cd9` | Show a field-aware report sequence for a dataset. |
| `examples/tutorial.md` | markdown | 0 | `ce1dfe39eb836ffc` | Inspect deterministic fixture output. |
| `examples/agent_handoff.json` | json | 0 | `2e12b696957c434e` | Hand compact context to a downstream research agent. |
| `examples/agent_handoff.md` | markdown | 0 | `b2a07d0943264d3e` | Hand compact context to a downstream research agent. |
| `examples/preset_run.json` | json | 0 | `dfa83b4934eecd9d` | Inspect deterministic fixture output. |
| `examples/taxonomy.json` | json | 0 | `ce04a98cc9ff7ba6` | Inspect deterministic fixture output. |
| `examples/taxonomy.md` | markdown | 0 | `9651ffcb9c7e121b` | Inspect deterministic fixture output. |
| `examples/version_report.json` | json | 0 | `c33dfa07c6d09559` | Inspect package version, command and fixture counts, release status, and local git refs. |
| `examples/version_report.md` | markdown | 0 | `40283fb7d0b292db` | Inspect package version, command and fixture counts, release status, and local git refs. |
| `examples/post_event.json` | json | 0 | `e763345775b25f8b` | Queue missing outcome capture after catalyst windows pass. |
| `examples/post_event.md` | markdown | 0 | `b593c05ac7b8cf01` | Queue missing outcome capture after catalyst windows pass. |
| `examples/demo_records_updated.json` | json | 0 | `e9ddd7b4752b62f4` | Start from a deterministic catalyst dataset. |
| `examples/compare.json` | json | 0 | `5b55087d78f9bc38` | Review deterministic differences between base and updated snapshots. |
| `examples/compare.md` | markdown | 0 | `ee0122d6f8eee39f` | Review deterministic differences between base and updated snapshots. |
| `examples/merge.json` | json | 0 | `9e397173ad5375e9` | Inspect deterministic multi-snapshot merge provenance and conflicts. |
| `examples/dashboard.html` | html | 0 | `a6c96ec8940e69af` | Review the static offline dashboard in a browser. |
| `examples/demo_records.csv` | csv | 0 | `dc5ec8f07bd31281` | Validate spreadsheet-friendly export shape and encoded multi-value cells. |
| `examples/upcoming.ics` | ics | 0 | `604533d3294ed317` | Load upcoming catalysts into calendar tooling. |
| `examples/imported_demo_records.json` | json | 0 | `65698120b5c74f32` | Validate CSV round trips back into catalyst JSON. |
| `examples/finalize_release.json` | json | 0 | `598bfcb43919823d` | Review one deterministic release checklist before handoff. |
| `examples/finalize_release.md` | markdown | 0 | `3fe6d07b3171bc8a` | Review one deterministic release checklist before handoff. |

## Command Provenance

### `examples/demo_records.json`

- Command: `python -m market_catalyst_calendar export-demo`
- Output type: `json`
- Bytes: 6771
- SHA-256: `3a0b0365033176885cfa9a2f5208d6a0770894a9c86949ba3c869db5aa3898f4`
- Recommended use cases:
  - Start from a deterministic catalyst dataset.
  - Smoke-test validation, scoring, and report commands.

### `examples/presets.json`

- Command: `python -m market_catalyst_calendar export-preset-example`
- Output type: `json`
- Bytes: 463
- SHA-256: `c66813f4d714ee66faa04396a4c06664662c5a08ef0636864bb7b013eab2261b`
- Recommended use cases:
  - Inspect deterministic fixture output.
  - Use as a stable regression fixture for downstream tooling.

### `examples/upcoming.json`

- Command: `python -m market_catalyst_calendar upcoming --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `json`
- Bytes: 3861
- SHA-256: `bfefef8050a1e37694d68339903282a1e1902bcd6c74473dec827e10b3e9dc1d`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - List open catalysts in a forward window.
  - Test date-window filtering and deterministic score ordering.

### `examples/stale.json`

- Command: `python -m market_catalyst_calendar stale --input examples/demo_records.json --as-of 2026-05-13`
- Output type: `json`
- Bytes: 1593
- SHA-256: `a48095b11073803d590858312d4847bb434410b8b498159c064e912a4d051c3e`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - List records whose review state is stale.
  - Use to seed evidence refresh or analyst review queues.

### `examples/brief.md`

- Command: `python -m market_catalyst_calendar brief --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `markdown`
- Bytes: 1371
- SHA-256: `dbf0252cacd2df04047953477b93fbc1fff0dd468eea831a044e08d778465579`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Review a concise analyst packet for upcoming catalysts.
  - Use as a Markdown snapshot in research notes or tickets.

### `examples/exposure.json`

- Command: `python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `json`
- Bytes: 1238
- SHA-256: `5332b8522213a83d77db4280e8a9cc8a28fce7e252ba4e9ef59c71c32b096d76`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Aggregate portfolio exposure for upcoming catalysts.
  - Test weighted exposure calculations and grouped report rendering.

### `examples/exposure.md`

- Command: `python -m market_catalyst_calendar exposure --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown`
- Output type: `markdown`
- Bytes: 603
- SHA-256: `b5d363ee9ced2aedfff8f69bb5b9134f7b7bf17629f5872f611125a8c17c3581`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Aggregate portfolio exposure for upcoming catalysts.
  - Test weighted exposure calculations and grouped report rendering.

### `examples/risk_budget.json`

- Command: `python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `json`
- Bytes: 3572
- SHA-256: `85e34e4316e593de2f863ccb2d680bbdcad7606846256ff3645f26c35a985f5d`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Compare event max-loss estimates against risk budgets.
  - Find over-budget catalysts before high-urgency events.

### `examples/risk_budget.md`

- Command: `python -m market_catalyst_calendar risk-budget --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown`
- Output type: `markdown`
- Bytes: 926
- SHA-256: `70559081dafa6bf925e7f88a75727b385969f27775945044bdbd8573fc873b56`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Compare event max-loss estimates against risk budgets.
  - Find over-budget catalysts before high-urgency events.

### `examples/sector_map.json`

- Command: `python -m market_catalyst_calendar sector-map --input examples/demo_records.json --as-of 2026-05-13`
- Output type: `json`
- Bytes: 6896
- SHA-256: `4f63e3091978a673c5de14e5b1229e3708455f72bf594798609cd217181cb9fe`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Group catalyst exposure by sector and theme.
  - Find concentration, stale evidence, and broker-dispersion clusters.

### `examples/sector_map.md`

- Command: `python -m market_catalyst_calendar sector-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown`
- Output type: `markdown`
- Bytes: 1304
- SHA-256: `463e6cd8911c92cfff957cbc360eea772f7bf09263a1549d5596e47b7ddadb11`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Group catalyst exposure by sector and theme.
  - Find concentration, stale evidence, and broker-dispersion clusters.

### `examples/review_plan.json`

- Command: `python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `json`
- Bytes: 1229
- SHA-256: `32da9b6ce6a5982c55add00f735934d5e788a78c68db703289541dc9d7048b02`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - List stale and high-urgency records needing analyst action.
  - Use as a deterministic review checklist.

### `examples/review_plan.md`

- Command: `python -m market_catalyst_calendar review-plan --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown`
- Output type: `markdown`
- Bytes: 807
- SHA-256: `94b566c91c858829bb3f9f7b7775aac24532bd7fd692911b9198681e83843e7f`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - List stale and high-urgency records needing analyst action.
  - Use as a deterministic review checklist.

### `examples/thesis_map.json`

- Command: `python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13`
- Output type: `json`
- Bytes: 1332
- SHA-256: `21656c1ec3cb9673d8353718e1a80a3d8c269d83a8ee6e34146cfd95d45adcc9`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Group catalysts by investment thesis and source references.
  - Find stale or sparse support for a thesis.

### `examples/thesis_map.md`

- Command: `python -m market_catalyst_calendar thesis-map --input examples/demo_records.json --as-of 2026-05-13 --format markdown`
- Output type: `markdown`
- Bytes: 670
- SHA-256: `2ba33fe8d536219e77c994d833bba294c3e4a2341de92b0d03afd6e96675fc3f`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Group catalysts by investment thesis and source references.
  - Find stale or sparse support for a thesis.

### `examples/scenario_matrix.json`

- Command: `python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `json`
- Bytes: 3689
- SHA-256: `51d449cf7c53483f19dd9beb8798662a98103dad8cc8701d982bfbafea9b7f59`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Review bull/base/bear event scenarios for upcoming catalysts.
  - Test scenario scores, dates, impacts, and Markdown tables.

### `examples/scenario_matrix.md`

- Command: `python -m market_catalyst_calendar scenario-matrix --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown`
- Output type: `markdown`
- Bytes: 1365
- SHA-256: `ca3f82dc602c911d615d071318d188bcfe40eb1af433b40702939c1ffe76f646`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Review bull/base/bear event scenarios for upcoming catalysts.
  - Test scenario scores, dates, impacts, and Markdown tables.

### `examples/evidence_audit.json`

- Command: `python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13`
- Output type: `json`
- Bytes: 2953
- SHA-256: `977078f8ca4c10897b912ec28d53e2f89cf96d08ad2de9352bdd69ad816761f9`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Find stale, thin, or concentrated evidence metadata.
  - Use before public handoff or source refresh work.

### `examples/evidence_audit.md`

- Command: `python -m market_catalyst_calendar evidence-audit --input examples/demo_records.json --as-of 2026-05-13 --format markdown`
- Output type: `markdown`
- Bytes: 1563
- SHA-256: `070654151c93d67666332040e6bf87c436e6413e5bb0fbfb2dbfb25a9e981e61`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Find stale, thin, or concentrated evidence metadata.
  - Use before public handoff or source refresh work.

### `examples/quality_gate.json`

- Command: `python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13`
- Output type: `json`
- Bytes: 6316
- SHA-256: `eb2268844dd6602a793cd1c7b3e62c976811ca66c52074f2a47e95e7429a33c0`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Exercise public research quality diagnostics and nonzero exits.
  - Use before publishing or handing off research fixtures.

### `examples/quality_gate.md`

- Command: `python -m market_catalyst_calendar quality-gate --profile public --input examples/demo_records.json --as-of 2026-05-13 --format markdown`
- Output type: `markdown`
- Bytes: 3928
- SHA-256: `44717b8d6ca70ae186846bc2f0d786c59a819ce525ee9047c83ecc2f2b960f00`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Exercise public research quality diagnostics and nonzero exits.
  - Use before publishing or handing off research fixtures.

### `examples/doctor.json`

- Command: `python -m market_catalyst_calendar doctor --profile public --input examples/demo_records.json --as-of 2026-05-13`
- Output type: `json`
- Bytes: 13526
- SHA-256: `1165debea9fecec0dcca1a9aab206e5bdd9d6d4fb402e79126e2ab90764795ae`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Inspect deterministic fixture output.
  - Use as a stable regression fixture for downstream tooling.

### `examples/doctor.md`

- Command: `python -m market_catalyst_calendar doctor --profile public --input examples/demo_records.json --as-of 2026-05-13 --format markdown`
- Output type: `markdown`
- Bytes: 2787
- SHA-256: `066999808460718e37def8ba12322a383945b820c2ba089c7a37dd79ba313d39`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Inspect deterministic fixture output.
  - Use as a stable regression fixture for downstream tooling.

### `examples/doctor_patch.json`

- Command: `python -m market_catalyst_calendar doctor --profile public --input examples/demo_records.json --as-of 2026-05-13 --format patch`
- Output type: `json`
- Bytes: 2206
- SHA-256: `30575d19339950140042623c1f648656b20e52033b3e358f43d1d448fa60cca2`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Inspect deterministic fixture output.
  - Use as a stable regression fixture for downstream tooling.

### `examples/broker_matrix.json`

- Command: `python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13`
- Output type: `json`
- Bytes: 3671
- SHA-256: `c963e69b50181965736ba8935018ce0c38c4a08eac7efbfff3bf8c6d97f7bf08`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Inspect broker view dispersion and stale broker-source flags.
  - Compare sell-side assumptions against catalyst timing.

### `examples/broker_matrix.md`

- Command: `python -m market_catalyst_calendar broker-matrix --input examples/demo_records.json --as-of 2026-05-13 --format markdown`
- Output type: `markdown`
- Bytes: 1457
- SHA-256: `ae5ab28c6dc7707f976db64c2927338ab2f16a0ce1f1a43c02ca9a3c6cd386ff`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Inspect broker view dispersion and stale broker-source flags.
  - Compare sell-side assumptions against catalyst timing.

### `examples/source_pack.json`

- Command: `python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13`
- Output type: `json`
- Bytes: 6402
- SHA-256: `d4d4c6697765ed4d183d659db740c82fb4634590c14f9efc389ffd889909cc94`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Export deduplicated evidence and broker source inventories.
  - Use for source collection, audit, or downstream handoff.

### `examples/source_pack.csv`

- Command: `python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format csv`
- Output type: `csv`
- Bytes: 1566
- SHA-256: `fc6634f680e27d20fd3636b82b27c9434527ce681bc5c4014b3d2b55bf50e9e7`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Export deduplicated evidence and broker source inventories.
  - Use for source collection, audit, or downstream handoff.

### `examples/source_pack.md`

- Command: `python -m market_catalyst_calendar source-pack --input examples/demo_records.json --as-of 2026-05-13 --format markdown`
- Output type: `markdown`
- Bytes: 1363
- SHA-256: `0cd02c8f70b1b8f321057fd8806bbf35c5b24ebd1b77d202b85c15aff8e848ec`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Export deduplicated evidence and broker source inventories.
  - Use for source collection, audit, or downstream handoff.

### `examples/watchlist.json`

- Command: `python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `json`
- Bytes: 6836
- SHA-256: `6ba1e1001eed110e3ce901d1b67f5c60b32faf3abee35a1adda1545167d1f289`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Convert open catalysts into prioritized watch items.
  - Use for trigger, due-date, and cadence workflows.

### `examples/watchlist.md`

- Command: `python -m market_catalyst_calendar watchlist --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown`
- Output type: `markdown`
- Bytes: 4704
- SHA-256: `221c458506cac4df580078a3dc43da1a8ded52a0f4bcb6323e99500e77904fe0`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Convert open catalysts into prioritized watch items.
  - Use for trigger, due-date, and cadence workflows.

### `examples/decision_log.json`

- Command: `python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `json`
- Bytes: 12444
- SHA-256: `51e52df0cf03f1c409658a7f739eaee41cb5ec3e4f07d5bb2012de4b63fa5125`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Create pre-event decision memo stubs without inventing conclusions.
  - Seed human or agent decision journals.

### `examples/decision_log.md`

- Command: `python -m market_catalyst_calendar decision-log --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown`
- Output type: `markdown`
- Bytes: 7315
- SHA-256: `857e24ea08ca100f2acdf12dc25b96e90eb9fb6cdb31f49b34b6771c9baf8296`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Create pre-event decision memo stubs without inventing conclusions.
  - Seed human or agent decision journals.

### `examples/drilldown.json`

- Command: `python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45`
- Output type: `json`
- Bytes: 19498
- SHA-256: `17a2a1b2ed2504b9f5e491bc0b7a340fcd0cab43fbc56ed59ff4c4dab473eced`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Inspect a complete single-ticker dossier.
  - Test composed reports that combine thesis, broker, risk, sources, and watch items.

### `examples/drilldown.md`

- Command: `python -m market_catalyst_calendar drilldown --input examples/demo_records.json --as-of 2026-05-13 --ticker NVDA --days 45 --format markdown`
- Output type: `markdown`
- Bytes: 7870
- SHA-256: `20b1838fbde5f48fb54ec0e2f952c1115152faa6e0e329fd389bff7d0cabf422`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Inspect a complete single-ticker dossier.
  - Test composed reports that combine thesis, broker, risk, sources, and watch items.

### `examples/command_cookbook.md`

- Command: `python -m market_catalyst_calendar command-cookbook --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `markdown`
- Bytes: 11808
- SHA-256: `3cc6c1ab23900cd9baa6bd91348cffe2952ae212ed32db98deb155e4b303d53e`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Show a field-aware report sequence for a dataset.
  - Use as an analyst runbook for reproducing fixture outputs.

### `examples/tutorial.md`

- Command: `python -m market_catalyst_calendar tutorial --as-of 2026-05-13 --days 45 --dataset-path examples/demo_records.json`
- Output type: `markdown`
- Bytes: 7707
- SHA-256: `ce1dfe39eb836ffcdb8a27615ea8abf77e7cb19717dc581bec4b8b75cd062d6e`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Inspect deterministic fixture output.
  - Use as a stable regression fixture for downstream tooling.

### `examples/agent_handoff.json`

- Command: `python -m market_catalyst_calendar agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `json`
- Bytes: 13009
- SHA-256: `2e12b696957c434e40f1bb0310b49a112601e47a7879dca51c548f4350c98e42`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Hand compact context to a downstream research agent.
  - Audit the exact commands and source URLs an agent should preserve.

### `examples/agent_handoff.md`

- Command: `python -m market_catalyst_calendar agent-handoff --input examples/demo_records.json --as-of 2026-05-13 --days 45 --format markdown`
- Output type: `markdown`
- Bytes: 3581
- SHA-256: `b2a07d0943264d3ec26c0d596026de155148e5dd7fa332a1ff1a1f53ce53b069`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Hand compact context to a downstream research agent.
  - Audit the exact commands and source URLs an agent should preserve.

### `examples/preset_run.json`

- Command: `python -m market_catalyst_calendar run-preset --presets examples/presets.json --name desk-packet`
- Output type: `json`
- Bytes: 2974
- SHA-256: `dfa83b4934eecd9dd4aa1767e556797dcbec91a54b31ce3200f8d55028fef736`
- Input fixtures: `examples/presets.json`
- Recommended use cases:
  - Inspect deterministic fixture output.
  - Use as a stable regression fixture for downstream tooling.

### `examples/taxonomy.json`

- Command: `python -m market_catalyst_calendar taxonomy`
- Output type: `json`
- Bytes: 19511
- SHA-256: `ce04a98cc9ff7ba6e4301a167f0743f0d73a8ede55dcf460243246cdfabd2e5d`
- Recommended use cases:
  - Inspect deterministic fixture output.
  - Use as a stable regression fixture for downstream tooling.

### `examples/taxonomy.md`

- Command: `python -m market_catalyst_calendar taxonomy --format markdown`
- Output type: `markdown`
- Bytes: 6748
- SHA-256: `9651ffcb9c7e121b9958a7f9234f11e7c7871a430120606baaac34f5b9746451`
- Recommended use cases:
  - Inspect deterministic fixture output.
  - Use as a stable regression fixture for downstream tooling.

### `examples/version_report.json`

- Command: `python -m market_catalyst_calendar version-report --root . --repo .`
- Output type: `json`
- Bytes: 944
- SHA-256: `c33dfa07c6d0955925ac48407a54fcd7bcd002194407181282aab5be2f83dd8c`
- Recommended use cases:
  - Inspect package version, command and fixture counts, release status, and local git refs.
  - Use as a compact release handoff snapshot before tagging.

### `examples/version_report.md`

- Command: `python -m market_catalyst_calendar version-report --root . --repo . --format markdown`
- Output type: `markdown`
- Bytes: 277
- SHA-256: `40283fb7d0b292db27aa7b12db40ac38d13e84eb1d754e79622036aaf3479bb3`
- Recommended use cases:
  - Inspect package version, command and fixture counts, release status, and local git refs.
  - Use as a compact release handoff snapshot before tagging.

### `examples/post_event.json`

- Command: `python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-06-25`
- Output type: `json`
- Bytes: 4548
- SHA-256: `e763345775b25f8baa945fcd93adec052a50df48d14a45f15cd50f9317101a8e`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Queue missing outcome capture after catalyst windows pass.
  - Use as a post-event review template.

### `examples/post_event.md`

- Command: `python -m market_catalyst_calendar post-event --input examples/demo_records.json --as-of 2026-06-25 --format markdown`
- Output type: `markdown`
- Bytes: 2532
- SHA-256: `b593c05ac7b8cf018b24309e9fc1936b0ed9d010b00326af72d54d6759c9acd5`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Queue missing outcome capture after catalyst windows pass.
  - Use as a post-event review template.

### `examples/demo_records_updated.json`

- Command: `python -m market_catalyst_calendar export-demo --snapshot updated`
- Output type: `json`
- Bytes: 7564
- SHA-256: `e9ddd7b4752b62f47e9a9c953e3c7ef8e21a49c08e276575a51222454497f967`
- Recommended use cases:
  - Start from a deterministic catalyst dataset.
  - Smoke-test validation, scoring, and report commands.

### `examples/compare.json`

- Command: `python -m market_catalyst_calendar compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27`
- Output type: `json`
- Bytes: 9757
- SHA-256: `5b55087d78f9bc38b9158cb541049939b2f2e7abdec891e3778c20bad76d27d0`
- Input fixtures: `examples/demo_records.json`, `examples/demo_records_updated.json`
- Recommended use cases:
  - Review deterministic differences between base and updated snapshots.
  - Test changed-status, changed-evidence, and score-delta consumers.

### `examples/compare.md`

- Command: `python -m market_catalyst_calendar compare --base examples/demo_records.json --current examples/demo_records_updated.json --as-of 2026-05-27 --format markdown`
- Output type: `markdown`
- Bytes: 2930
- SHA-256: `ee0122d6f8eee39fcac5e19eeba52f9701ec3addafa23b5d0e1b631ca091b7ba`
- Input fixtures: `examples/demo_records.json`, `examples/demo_records_updated.json`
- Recommended use cases:
  - Review deterministic differences between base and updated snapshots.
  - Test changed-status, changed-evidence, and score-delta consumers.

### `examples/merge.json`

- Command: `python -m market_catalyst_calendar merge examples/demo_records.json examples/demo_records_updated.json --as-of 2026-05-27`
- Output type: `json`
- Bytes: 12790
- SHA-256: `9e397173ad5375e9a83296db9d435dce63bce20b8433e9811745443a0e3ecd68`
- Input fixtures: `examples/demo_records.json`, `examples/demo_records_updated.json`
- Recommended use cases:
  - Inspect deterministic multi-snapshot merge provenance and conflicts.
  - Test downstream handling of validation diagnostics in merged datasets.

### `examples/dashboard.html`

- Command: `python -m market_catalyst_calendar html-dashboard --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `html`
- Bytes: 15597
- SHA-256: `a6c96ec8940e69aff13338b7ba954d96fb2963d4fbd4d53e26cba492c2fd2ed4`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Review the static offline dashboard in a browser.
  - Test escaped no-JavaScript HTML report generation.

### `examples/demo_records.csv`

- Command: `python -m market_catalyst_calendar export-csv --input examples/demo_records.json`
- Output type: `csv`
- Bytes: 4080
- SHA-256: `dc5ec8f07bd3128143b33181056d54bc9ef7bb60d98ec30ccc7b9a1ec7c91a6a`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Validate spreadsheet-friendly export shape and encoded multi-value cells.
  - Test CSV consumers against stable column order.

### `examples/upcoming.ics`

- Command: `python -m market_catalyst_calendar export-ics --input examples/demo_records.json --as-of 2026-05-13 --days 45`
- Output type: `ics`
- Bytes: 2710
- SHA-256: `604533d3294ed3170974d146c8c61c27ab93638d7f9967773a8d7c8d3768ae24`
- Input fixtures: `examples/demo_records.json`
- Recommended use cases:
  - Load upcoming catalysts into calendar tooling.
  - Test deterministic iCalendar UID, date, and escaping behavior.

### `examples/imported_demo_records.json`

- Command: `python -m market_catalyst_calendar import-csv --input examples/demo_records.csv`
- Output type: `json`
- Bytes: 6899
- SHA-256: `65698120b5c74f32e7d0d3c303459d06f214f5e4cf1c1ecc9787dd6c554f0be5`
- Input fixtures: `examples/demo_records.csv`
- Recommended use cases:
  - Validate CSV round trips back into catalyst JSON.
  - Test parser behavior for encoded multi-value cells.

### `examples/finalize_release.json`

- Command: `python -m market_catalyst_calendar finalize-release --example`
- Output type: `json`
- Bytes: 1831
- SHA-256: `598bfcb43919823d977490838af54b2bf72c5cf622a3a3555a354e14089eea58`
- Recommended use cases:
  - Review one deterministic release checklist before handoff.
  - Combine audit, smoke, fixture, and changelog status for release notes.

### `examples/finalize_release.md`

- Command: `python -m market_catalyst_calendar finalize-release --example --format markdown`
- Output type: `markdown`
- Bytes: 615
- SHA-256: `3fe6d07b3171bc8a1911c099f37ebaebceb710e94639a0cf5220474911ff72e9`
- Recommended use cases:
  - Review one deterministic release checklist before handoff.
  - Combine audit, smoke, fixture, and changelog status for release notes.
