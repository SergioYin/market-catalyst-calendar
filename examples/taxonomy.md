# Market Catalyst Taxonomy

Schema: `taxonomy/v1`
Commands: 41
Diagnostic codes: 35

## Event Types

- `capital_return`
- `clinical_trial`
- `court_decision`
- `earnings`
- `guidance_update`
- `investor_day`
- `m_and_a`
- `macro_release`
- `product_launch`
- `regulatory_decision`

## Statuses

- `cancelled`
- `completed`
- `confirmed`
- `delayed`
- `rumored`
- `scheduled`
- `watching`

## Review Actions

- `archive`
- `monitor_date`
- `none`
- `refresh_evidence`
- `update_scenario`
- `verify_source`

## Quality Rules

| Rule | Detail |
| --- | --- |
| broker_caveats | broker views must have substantive caveats and fresh source dates when required |
| minimum_evidence | records must meet evidence URL count and freshness metadata thresholds |
| no_placeholder_urls | evidence and broker URLs cannot use placeholder or sample hosts/terms |
| release_metadata | strict profile records must include sector, theme, thesis_id, and source_ref |
| review_freshness | last_reviewed must exist and fall within the profile freshness window |
| scenario_completeness | bull/base/bear notes must exist and be substantive |

## Diagnostic Codes

| Code | Source | Rule/Detail |
| --- | --- | --- |
| MCC-VAL-BROKER-001 | validate | broker view date is after dataset as_of |
| MCC-VAL-CONFIDENCE-001 | validate | confidence range or confirmed/completed confidence mismatch |
| MCC-VAL-DATE-001 | validate | last_reviewed is after dataset as_of |
| MCC-VAL-DATE-002 | validate | evidence_checked_at is after dataset as_of |
| MCC-VAL-DATE-003 | validate | outcome_recorded_at is after dataset as_of |
| MCC-VAL-DATE-004 | validate | outcome_recorded_at is before the event window starts |
| MCC-VAL-EVIDENCE-001 | validate | record has no evidence URLs |
| MCC-VAL-EVIDENCE-002 | validate | evidence URL is not valid http(s) |
| MCC-VAL-GENERAL-001 | validate | validation error without a more specific diagnostic |
| MCC-VAL-HISTORY-001 | validate | history contains a future update |
| MCC-VAL-HISTORY-002 | validate | latest history status does not match current status |
| MCC-VAL-IDENTITY-001 | validate | duplicate record id |
| MCC-VAL-IDENTITY-002 | validate | ticker or entity is missing |
| MCC-VAL-IDENTITY-003 | validate | ticker format is unsupported |
| MCC-VAL-OUTCOME-001 | validate | outcome_recorded_at is set without actual_outcome |
| MCC-VAL-REVIEW-001 | validate | open record has no required review action |
| MCC-VAL-SCENARIO-001 | validate | required bull/base/bear scenario note is missing |
| MCC-QG-BROKER-001 | quality-gate | broker_caveats |
| MCC-QG-BROKER-002 | quality-gate | broker_caveats |
| MCC-QG-BROKER-003 | quality-gate | broker_caveats |
| MCC-QG-BROKER-004 | quality-gate | broker_caveats |
| MCC-QG-EVIDENCE-001 | quality-gate | minimum_evidence |
| MCC-QG-EVIDENCE-002 | quality-gate | minimum_evidence |
| MCC-QG-EVIDENCE-003 | quality-gate | minimum_evidence |
| MCC-QG-RELEASE-001 | quality-gate | release_metadata |
| MCC-QG-RELEASE-002 | quality-gate | release_metadata |
| MCC-QG-RELEASE-003 | quality-gate | release_metadata |
| MCC-QG-RELEASE-004 | quality-gate | release_metadata |
| MCC-QG-REVIEW-001 | quality-gate | review_freshness |
| MCC-QG-REVIEW-002 | quality-gate | review_freshness |
| MCC-QG-SCENARIO-001 | quality-gate | scenario_completeness |
| MCC-QG-SCENARIO-002 | quality-gate | scenario_completeness |
| MCC-QG-SCENARIO-003 | quality-gate | scenario_completeness |
| MCC-QG-SOURCE-001 | quality-gate | no_placeholder_urls |
| MCC-QG-SOURCE-002 | quality-gate | no_placeholder_urls |

## Output Commands

| Command | Formats | Purpose |
| --- | --- | --- |
| changelog | json, markdown | render local release notes from commits |
| compare | json, markdown | compare two dataset snapshots |
| create-archive | directory | create portable report archive with hashes |
| demo-bundle | directory | write all demo outputs plus manifest and transcript |
| export-csv | csv | export dataset rows to CSV |
| export-demo | json | write the built-in demo dataset |
| export-ics | ics | export upcoming catalysts to iCalendar |
| export-preset-example | json | write starter preset configuration |
| finalize-release | json, markdown | combine release audit, smoke matrix, fixture gallery, and changelog into a checklist |
| fixture-gallery | json, markdown | list bundled fixture hashes and provenance |
| html-dashboard | html | render a static HTML dashboard |
| import-csv | json | import CSV rows as dataset JSON |
| merge | json | merge datasets with provenance and validation |
| run-preset | json, directory | execute named preset report packets |
| static-site | directory | write a multi-page static site |
| taxonomy | json, markdown | report supported event types, statuses, actions, rules, diagnostics, and commands |
| tutorial | markdown | render a notebooks-free tutorial |

## All Commands

| Command | Category | Formats |
| --- | --- | --- |
| agent-handoff | agent | json, markdown |
| brief | briefing | markdown |
| broker-matrix | broker | json, markdown |
| changelog | release | json, markdown |
| command-cookbook | operations | markdown |
| compare | dataset | json, markdown |
| create-archive | archive | directory |
| decision-log | decision | json, markdown |
| demo-bundle | fixture | directory |
| doctor | quality | json, markdown, patch |
| drilldown | dossier | json, markdown |
| evidence-audit | quality | json, markdown |
| export-csv | interchange | csv |
| export-demo | fixture | json |
| export-ics | interchange | ics |
| export-preset-example | fixture | json |
| exposure | portfolio | json, markdown |
| finalize-release | release | json, markdown |
| fixture-gallery | fixture | json, markdown |
| html-dashboard | site | html |
| import-csv | interchange | json |
| merge | dataset | json |
| post-event | review | json, markdown |
| quality-gate | quality | json, markdown |
| release-audit | release | json, markdown |
| review-plan | review | json, markdown |
| risk-budget | portfolio | json, markdown |
| run-preset | packet | json, directory |
| scenario-matrix | scenario | json, markdown |
| sector-map | taxonomy | json, markdown |
| smoke-matrix | release | json, markdown |
| source-pack | sources | json, csv, markdown |
| stale | review | json, markdown |
| static-site | site | directory |
| taxonomy | metadata | json, markdown |
| thesis-map | taxonomy | json, markdown |
| tutorial | learning | markdown |
| upcoming | calendar | json, markdown |
| validate | quality | json |
| verify-archive | archive | json |
| watchlist | review | json, markdown |
