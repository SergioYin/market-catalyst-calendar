# Market Catalyst Calendar Schema

This document is the offline contract for `market-catalyst-calendar` data and command output. The package uses only the Python standard library, reads JSON or CSV from files/stdin, and emits deterministic UTF-8 text.

## Dataset JSON

Top-level object:

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `as_of` | ISO date string | No | Dataset date. Defaults to `1970-01-01` when omitted. |
| `records` | array of record objects | Yes | Catalyst records. Must contain at least an array; validation may reject individual records. |

Record object:

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `id` | non-empty string | Yes | Stable unique record id within the dataset. |
| `ticker` | non-empty string | Yes | Uppercased by the parser; validation expects <=12 chars from `A-Z`, digits, `.`, or `-`. |
| `entity` | non-empty string | Yes | Company, security, index, or macro entity name. |
| `event_type` | enum string | Yes | One of `earnings`, `product_launch`, `regulatory_decision`, `clinical_trial`, `investor_day`, `macro_release`, `court_decision`, `capital_return`, `m_and_a`, `guidance_update`. |
| `date` | ISO date string | Conditionally | Single-day event date. Required when `window` is absent. |
| `window` | object | Conditionally | Multi-day event window. Required when `date` is absent. |
| `window.start` | ISO date string | With `window` | Inclusive start date. |
| `window.end` | ISO date string | With `window` | Inclusive end date, on or after `window.start`. |
| `confidence` | number | Yes | Decimal from `0` to `1`. |
| `position_size` | number or null | No | Non-negative notional exposure in the user's reporting currency. |
| `portfolio_weight` | number or null | No | Decimal from `0` to `1`; `0.05` means 5%. |
| `risk_budget` | number or null | No | Non-negative event risk budget in the user's reporting currency. |
| `max_loss` | number or null | No | Non-negative estimated maximum catalyst loss in the user's reporting currency. |
| `sector` | non-empty string or null | No | Broad sector, industry, or macro bucket used by `sector-map`. |
| `theme` | non-empty string or null | No | Cross-cutting catalyst theme used by `sector-map`. |
| `thesis_id` | non-empty string or null | No | Links the record to an external thesis. |
| `source_ref` | non-empty string or null | No | Human-readable source note or internal source reference. |
| `status` | enum string | Yes | One of `rumored`, `watching`, `scheduled`, `confirmed`, `completed`, `delayed`, `cancelled`. |
| `history` | array of history objects | No | Status history, sorted deterministically by date/status/note during parsing. Defaults to empty. |
| `thesis_impact` | enum string | Yes | One of `positive`, `negative`, `mixed`, `unknown`. |
| `evidence_urls` | array of strings | Yes | HTTP(S) source URLs. Validation requires at least one valid URL. |
| `scenario_notes` | object string->string | Yes | Must include `bull`, `base`, and `bear` keys for validation. |
| `required_review_action` | enum string | Yes | One of `verify_source`, `refresh_evidence`, `update_scenario`, `monitor_date`, `archive`, `none`. Open records cannot use `none`. |
| `last_reviewed` | ISO date string or null | No | Last analyst review date. Cannot be after top-level `as_of`. |
| `evidence_checked_at` | ISO date string or null | No | Date sources were last checked. Cannot be after top-level `as_of`. |
| `broker_views` | array of broker view objects | No | Optional broker or analyst snapshots. Defaults to empty. |
| `actual_outcome` | non-empty string or null | No | Post-event outcome note. |
| `outcome_recorded_at` | ISO date string or null | No | Requires `actual_outcome`, cannot be before the catalyst window starts, and cannot be after top-level `as_of`. |

History object:

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `date` | ISO date string | Yes | History entry date. Validation rejects future history after top-level `as_of`. |
| `status` | enum string | Yes | Same enum as record `status`. Latest history status should match current record status. |
| `note` | non-empty string | Yes | Analyst note for the status change. |

Broker view object:

| Field | Type | Required | Contract |
| --- | --- | --- | --- |
| `institution` | non-empty string | Yes | Broker or analyst institution. |
| `rating` | non-empty string | Yes | Rating label as recorded. |
| `target_price` | number | Yes | Non-negative target price. |
| `as_of` | ISO date string | Yes | View date. Validation rejects dates after top-level `as_of`. |
| `source_url` | string | Yes | HTTP(S) source URL. |
| `caveat` | non-empty string | Yes | Caveat or assumption attached to the view. |

## CSV Dataset

`export-csv` and `import-csv` use this stable column order:

```text
as_of,id,ticker,entity,event_type,window_start,window_end,confidence,position_size,portfolio_weight,risk_budget,max_loss,sector,theme,thesis_id,source_ref,status,thesis_impact,required_review_action,last_reviewed,evidence_checked_at,actual_outcome,outcome_recorded_at,evidence_urls,scenario_notes,history,broker_views
```

Required CSV columns are all columns except `position_size`, `portfolio_weight`, `risk_budget`, `max_loss`, `sector`, `theme`, `thesis_id`, `source_ref`, `evidence_checked_at`, `actual_outcome`, `outcome_recorded_at`, and `broker_views`.

All rows must share the same `as_of`. Equal `window_start` and `window_end` import as `date`; different values import as `window`. Multi-value cells percent-encode each component before joining:

| Column | Encoding |
| --- | --- |
| `evidence_urls` | URL-encoded values joined by ` | ` |
| `scenario_notes` | URL-encoded `key = value` pairs joined by ` | ` |
| `history` | URL-encoded `date = status = note` entries joined by ` | ` |
| `broker_views` | URL-encoded `institution = rating = target_price = as_of = source_url = caveat` entries joined by ` | ` |

## Common Output Rules

JSON output is pretty-printed with two-space indentation, sorted object keys, UTF-8 text, and a trailing newline. Markdown output is deterministic and ends with a trailing newline. Commands return `0` on success, `1` for validation/report failures where noted, and `2` for parse, filesystem, or argument value errors handled by the CLI.

`--input -` reads stdin. Omitted `--output` streams to stdout. `--as-of` overrides the dataset date for report calculations without mutating the input dataset.

## Command Contracts

`validate`

- Input: dataset JSON.
- Parameters: `--profile basic|public|strict`, optional `--as-of` for profile gates.
- Success: exit `0`, JSON object `{ "ok": true, "record_count": int }` for the default `basic` profile; profile-aware success also includes `profile` and `as_of`.
- Validation failure: exit `1`, JSON object with `ok: false`, string `errors`, and structured `diagnostics` containing stable codes such as `MCC-VAL-EVIDENCE-002`.
- Profiles: `basic` runs structural record validation; `public` adds publication quality-gate diagnostics; `strict` adds tighter release diagnostics for public datasets.

`upcoming`

- Input: dataset JSON.
- Parameters: `--as-of`, `--days`, `--format json|markdown`.
- Selection: open records whose window start is from `0` through `days` after `as_of`.
- JSON: `{ "as_of": date, "records": [record summary, ...] }`.
- Markdown: same record set rendered by the brief table with title `Market Catalyst Records`.

`stale`

- Input: dataset JSON.
- Parameters: `--as-of`, `--stale-after-days`, `--format json|markdown`.
- Selection: records whose scored `review_state` is `stale`.
- Output: same shape as `upcoming`.

`brief`

- Input: dataset JSON.
- Parameters: `--as-of`, `--days`.
- Selection: upcoming open records.
- Output: Markdown brief with summary table and per-record details.

Record summary objects emitted by `upcoming` and `stale` contain:

| Field | Type | Notes |
| --- | --- | --- |
| `as_of` | date | Top-level only. |
| `records[].id` | string | Catalyst id. |
| `records[].ticker` | string | Ticker. |
| `records[].entity` | string | Entity name. |
| `records[].event_type` | string | Event type. |
| `records[].window` | string | `YYYY-MM-DD` or `YYYY-MM-DD..YYYY-MM-DD`. |
| `records[].status` | string | Current status. |
| `records[].thesis_impact` | string | Directional impact. |
| `records[].evidence_urls` | array | Source URLs. |
| `records[].required_review_action` | string | Required action. |
| `records[].catalyst_score` | int | `0` to `100`. |
| `records[].urgency` | string | `overdue`, `high`, `medium`, `low`, or `closed`. |
| `records[].review_state` | string | `closed`, `stale`, `needs_review`, or `current`. |
| `records[].days_until` | int | Days from `as_of` to window start. |
| Optional fields | mixed | `position_size`, `portfolio_weight`, `risk_budget`, `max_loss`, `sector`, `theme`, `thesis_id`, `source_ref`, `evidence_checked_at`, `broker_views`, `actual_outcome`, `outcome_recorded_at` appear only when present. |

`exposure`

- JSON: `{ "as_of": date, "groups": [group, ...], "summary": object }`.
- Group fields: `ticker`, `event_type`, `urgency`, `record_count`, `portfolio_weight`, `position_size`, `weighted_exposure`, `weighted_position_exposure`, `records`.
- Summary fields: `group_count`, `record_count`, `portfolio_weight`, `position_size`, `weighted_exposure`, `weighted_position_exposure`.
- Markdown: exposure totals plus grouped table.

`risk-budget`

- Input: dataset JSON.
- Parameters: `--as-of`, `--days`, `--format json|markdown`.
- Selection: upcoming open records with `risk_budget` or `max_loss` present.
- Grouping: `ticker`, `thesis_id` (or `unmapped`), and scored `urgency`.
- JSON: `{ "as_of": date, "groups": [group, ...], "summary": object }`.
- Group fields: `ticker`, `thesis_id`, `urgency`, `record_count`, `risk_budget`, `max_loss`, `expected_event_loss`, `budget_remaining`, `budget_utilization`, `over_budget_record_count`, `missing_budget_count`, `missing_max_loss_count`, `flags`, `records`.
- Record fields: `id`, `ticker`, `entity`, `event_type`, `window`, `status`, `thesis_id`, `catalyst_score`, `urgency`, `confidence`, `risk_budget`, `max_loss`, `expected_event_loss`, `budget_remaining`, `budget_utilization`, `flags`.
- Summary fields: `group_count`, `record_count`, `risk_budget`, `max_loss`, `expected_event_loss`, `over_budget_group_count`, `over_budget_record_count`, `missing_budget_count`, `missing_max_loss_count`.
- Flags: `over_budget` when `max_loss > risk_budget`, `missing_budget` when max loss is present without a budget, and `missing_max_loss` when budget is present without a max-loss estimate.
- Markdown: risk-budget totals, grouped budget table, and flagged catalyst details.

`sector-map`

- Input: dataset JSON.
- Parameters: `--as-of`, `--stale-after-days`, `--format json|markdown`.
- Selection: records with `sector` or `theme` present. Missing one side is reported as `unmapped`.
- Grouping: `sector` and `theme`.
- JSON: `{ "as_of": date, "stale_after_days": int, "groups": [group, ...], "summary": object }`.
- Group fields: `sector`, `theme`, `record_count`, `open_event_count`, `highest_score`, `portfolio_weight`, `position_size`, `weighted_exposure`, `weighted_position_exposure`, `stale_evidence_count`, `missing_evidence_freshness_count`, `broker_view_count`, `broker_dispersion_max`, `broker_dispersion_avg`, `urgency_count`, `review_state_count`, `tickers`, `themes`, `records`.
- Record fields: `id`, `ticker`, `entity`, `event_type`, `window`, `status`, `sector`, `theme`, `thesis_id`, `catalyst_score`, `urgency`, `review_state`, `days_until`, `portfolio_weight`, `position_size`, `weighted_exposure`, `weighted_position_exposure`, `evidence_checked_at`, `evidence_age_days`, `evidence_state`, `broker_view_count`, `broker_dispersion`, `flags`.
- Summary fields: `group_count`, `record_count`, `open_event_count`, `stale_evidence_count`, `broker_view_count`, `portfolio_weight`, `weighted_exposure`, `highest_broker_dispersion`, `critical_record_count`.
- Flags: `missing_evidence` or `stale_evidence`, `urgent`, `stale_review`, and `broker_dispersion`.
- Markdown: sector/theme summary table plus flagged catalyst details.

`review-plan`

- JSON: `{ "as_of": date, "days": int, "stale_after_days": int, "records": [item, ...] }`.
- Item fields: `id`, `ticker`, `entity`, `event_type`, `window`, `status`, `catalyst_score`, `urgency`, `review_state`, `days_until`, `stale_days`, `selection_reasons`, `required_review_action`, `next_action`, `evidence_gap`, `scenario_update_prompt`, `evidence_urls`.
- Markdown: checklist grouped as one block per selected record.

`thesis-map`

- JSON: `{ "as_of": date, "stale_after_days": int, "groups": [group, ...], "summary": object }`.
- Group fields: `thesis_id`, `record_count`, `open_event_count`, `highest_score`, `stale_count`, `records`, `evidence_references`.
- Summary fields: `thesis_count`, `record_count`, `open_event_count`, `stale_count`.
- Markdown: thesis table.

`scenario-matrix`

- JSON: `{ "as_of": date, "stale_after_days": int, "records": [record, ...], "summary": object }`.
- Record fields: `id`, `ticker`, `entity`, `event_type`, `window`, `status`, `base_catalyst_score`, `review_state`, `scenarios`.
- Scenario fields: `scenario`, `date`, `score`, `impact`, `review_action`, `note`.
- Summary fields: `record_count`, `scenario_count`, `highest_scenario_score`, `review_action_count`.
- Markdown: one row per bull/base/bear scenario.

`evidence-audit`

- JSON: `{ "as_of": date, "fresh_after_days": int, "min_sources": int, "max_domain_share": number, "records": [flagged_record, ...], "summary": object }`.
- Flagged record fields: `id`, `ticker`, `entity`, `event_type`, `window`, `status`, `evidence_checked_at`, `evidence_age_days`, `evidence_url_count`, `evidence_urls`, `source_domains`, `source_domain_count`, `dominant_source_domain`, `dominant_source_share`, `flags`, `severity`, `next_action`.
- Summary fields: `record_count`, `flagged_record_count`, `flag_counts`, `severity_counts`.
- Markdown: flagged record table plus action notes.

`quality-gate`

- Input: dataset JSON.
- Parameters: `--profile basic|public|strict`, `--as-of`, optional threshold overrides `--min-evidence-urls`, `--max-review-age-days`, `--max-evidence-age-days`, `--max-broker-age-days`, and `--format json|markdown`.
- Exit status: `0` when the selected profile passes, `1` when JSON/Markdown diagnostics are produced but the selected profile fails.
- Profiles: `basic` checks required scenario presence and at least one evidence URL; `public` requires publication freshness, substantive scenarios, no placeholder URLs, and broker caveats; `strict` requires three evidence URLs, 7-day review/evidence freshness, 14-day broker freshness, broker coverage, and release metadata.
- JSON: `{ "as_of": date, "ok": bool, "policy": object, "records": [failing_record, ...], "summary": object }`.
- Issue fields: `code`, `rule`, `severity`, and `detail`.
- Summary fields: `record_count`, `failed_record_count`, `rule_counts`, and `severity_counts`.
- Markdown: status block plus a failing-record table with diagnostic codes and per-record next actions.

`export-preset-example`

- Input: built-in deterministic example config only; no dataset JSON is required.
- Parameters: optional `--output`.
- Output: presets JSON with top-level `defaults` and `presets` objects.

`run-preset`

- Input: presets JSON plus the dataset path named by the preset, unless `--input` overrides it.
- Parameters: required `--presets` and `--name`; optional `--input`, `--as-of`, and `--output-dir` overrides.
- Presets JSON: `{ "defaults": object, "presets": { name: preset } }`.
- Default fields: `days`, `stale_after_days`, `profile`, `output_dir`, optional `input`, optional `as_of`, and optional `workflows`.
- Preset fields: `input`, `as_of`, `days`, `stale_after_days`, `profile`, `output_dir`, and `workflows`; preset fields override defaults.
- Supported workflows: `validate`, `quality-gate`, `upcoming`, `stale`, `brief`, `exposure`, `exposure-markdown`, `risk-budget`, `risk-budget-markdown`, `sector-map`, `sector-map-markdown`, `review-plan`, `review-plan-markdown`, `thesis-map`, `thesis-map-markdown`, `scenario-matrix`, `scenario-matrix-markdown`, `evidence-audit`, `evidence-audit-markdown`, `broker-matrix`, `broker-matrix-markdown`, `source-pack`, `source-pack-csv`, `source-pack-markdown`, `watchlist`, `watchlist-markdown`, `decision-log`, `decision-log-markdown`, `agent-handoff`, `agent-handoff-markdown`, and `html-dashboard`.
- Output: writes each workflow artifact and `manifest.json` under `output_dir`, and prints the same manifest to stdout.
- JSON manifest: `{ "schema_version": "preset-run/v1", "ok": true, "preset": string, "input": string, "as_of": date, "parameters": object, "summary": object, "artifacts": [artifact, ...], "manifest": "manifest.json" }`.
- Parameters fields: `days`, `stale_after_days`, `profile`, and `output_dir`.
- Summary fields: `workflow_count`, `artifact_count`, `record_count`, and `report_failure_count`.
- Artifact fields: `workflow`, `path`, `command`, `exit_code`, `bytes`, and `sha256`.
- Exit status: `0` when the packet is generated. Individual report failures, such as a failing quality gate, are recorded in artifact `exit_code` and counted in `report_failure_count`.

`taxonomy`

- Input: built-in package metadata only; no dataset JSON is required.
- Parameters: optional `--format json|markdown` and `--output`.
- JSON: `{ "schema_version": "taxonomy/v1", "event_types": [string, ...], "statuses": [string, ...], "review_actions": [string, ...], "quality_rules": [rule, ...], "diagnostic_codes": [code, ...], "output_commands": [string, ...], "commands": [command, ...], "summary": object }`.
- Rule fields: `id` and `detail`.
- Diagnostic code fields: `code`, `source`, `detail`, and optional `rule`.
- Command fields: `id`, `category`, `formats`, `inputs`, `purpose`, and `writes_files`.
- Summary fields: `command_count`, `diagnostic_code_count`, `event_type_count`, `output_command_count`, and `quality_rule_count`.
- Markdown: sections for event types, statuses, review actions, quality rules, diagnostic codes, output commands, and the full command catalog.

`version-report`

- Input: repository files and local git metadata only; no dataset JSON or network access is used.
- Parameters: optional `--root`, `--repo`, `--format json|markdown`, and `--output`.
- Exit status: `0` when the non-recursive release status passes, `1` when README command coverage, schema field coverage, agent skill mentions, or workflow-file checks fail.
- JSON: `{ "schema_version": "version-report/v1", "package": object, "summary": object, "command_count": int, "fixture_count": int, "release_audit": object, "git": object }`.
- Package fields: `name` and `version`.
- Summary fields: `command_count`, `fixture_count`, and `release_audit_status`.
- Release-audit fields: `status`, `ok`, `checked_with`, `detail`, `blockers`, `missing_commands`, `missing_schema_fields`, `missing_skill_items`, and `workflow_files`.
- Git fields: `available`, `repo`, `latest_tag`, `commit`, and `detail` when unavailable.
- Commit fields: `hash`, `short_hash`, `date`, and `subject`.
- Markdown: package/version summary, command and fixture counts, release audit status, git tag/commit details, and blockers when present.

`release-audit`

- Input: repository files only; no dataset JSON is required.
- Parameters: optional `--root` and `--format json|markdown`.
- Exit status: `0` when all release checks pass, `1` when any checked artifact is stale, missing, undocumented, incomplete, or a workflow file is present.
- Checks: regenerated `examples/` fixtures, README command coverage, schema field coverage, skill presence, and absence of `.github/workflows` files.
- JSON: `{ "schema_version": "release-audit/v1", "ok": bool, "root": string, "checks": [check, ...], "summary": object }`.
- Top-level fields: `schema_version`, `ok`, `root`, `checks`, and `summary`.
- Check fields: `id`, `status`, `detail`, `expected_count`, `checked_count`, `missing`, `extra`, `mismatches`, `required_commands`, `missing_commands`, `required_fields`, `missing_fields`, and `workflow_files` as applicable to the check.
- Summary fields: `check_count`, `passed_count`, and `failed_count`.
- Markdown: status block, check table, and failure detail lists.

`changelog`

- Input: local git repository only; no dataset JSON or network access is used.
- Parameters: required `--since-tag`, optional `--repo`, `--to-ref`, `--include-merges`, `--format json|markdown`, and `--output`.
- Range: `since_tag..to_ref`, where the starting tag is excluded and the ending ref is included. Merge commits are excluded unless `--include-merges` is set.
- JSON: `{ "schema_version": "changelog/v1", "repo": string, "since_tag": string, "to_ref": string, "from_sha": string, "to_sha": string, "range": string, "include_merges": bool, "commit_count": int, "tag_count": int, "tags_in_range": [string, ...], "tags_on_target": [string, ...], "breaking_change_count": int, "breaking_changes": [commit, ...], "categories": [category, ...], "commits": [commit, ...] }`.
- Commit fields: `hash`, `short_hash`, `date`, `author`, `subject`, `type`, `scope`, `description`, `category`, `breaking`, and `references`.
- Category fields: `id`, `title`, and `commits`.
- Conventional commit types are grouped into `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`, `revert`, and `other`.
- Markdown: release-note header with range, from/to SHAs, commit count, optional target tags, breaking changes, and non-empty category sections.

`finalize-release`

- Input: repository files, built-in fixture metadata, internal smoke checks, and local git history; no network access is used.
- Parameters: required `--since-tag` unless using the hidden fixture-only `--example`, optional `--root`, `--repo`, `--to-ref`, `--include-merges`, `--format json|markdown`, and `--output`.
- Exit status: `0` when release audit, smoke matrix, fixture gallery, and changelog checks all pass; `1` when any checklist item fails.
- JSON: `{ "schema_version": "finalize-release/v1", "ok": bool, "root": string, "repo": string, "range": string, "since_tag": string, "to_ref": string, "checklist": [item, ...], "blockers": [string, ...], "components": object, "release_notes": object }`.
- Checklist item fields: `id`, `ok`, `status`, `detail`, and `blockers`.
- Top-level finalizer fields include `blockers`, `components`, and `release_notes`.
- Component fields: `release_audit`, `smoke_matrix`, `fixture_gallery`, and `changelog`; each includes `ok` and deterministic summary fields.
- `release_notes` fields: `commit_count`, `breaking_change_count`, and non-empty changelog `categories` with compact commit references.
- Markdown: status block, checklist, component table, optional blockers, and release-note counts.

`broker-matrix`

- JSON: `{ "as_of": date, "stale_after_days": int, "groups": [group, ...], "summary": object }`.
- Group fields: `ticker`, `thesis_id`, `view_count`, `rating_count`, `target_price_min`, `target_price_max`, `target_price_avg`, `target_price_dispersion`, `stale_sources`, `linked_catalysts`, `views`.
- View fields: `institution`, `rating`, `target_price`, `as_of`, `age_days`, `source_url`, `caveat`, `stale_source`.
- Summary fields: `group_count`, `view_count`, `stale_view_count`, `linked_catalyst_count`.
- Markdown: group summary table plus per-view details.

`source-pack`

- JSON: `{ "as_of": date, "fresh_after_days": int, "sources": [source, ...], "summary": object }`.
- Source fields: `url`, `source_types`, `usage_count`, `tickers`, `thesis_ids`, `record_ids`, `evidence_checked_at`, `freshness_age_days`, `freshness_state`, `broker_institutions`, `broker_as_of_dates`.
- Summary fields: `source_count`, `evidence_source_count`, `broker_source_count`, `stale_source_count`, `missing_freshness_count`, `usage_count`.
- CSV: same source inventory with stable columns `url,source_types,usage_count,tickers,thesis_ids,record_ids,evidence_checked_at,freshness_age_days,freshness_state,broker_institutions,broker_as_of_dates`.
- Markdown: source inventory table.

`tutorial`

- Input: built-in demo data only; no dataset JSON is required.
- Parameters: optional `--as-of`, `--days`, `--dataset-path`, and `--output`.
- Output: deterministic Markdown tutorial.
- Contract: the tutorial is notebooks-free and includes command blocks, expected exit codes, expected command output excerpts derived from demo data, and learning checkpoints. It covers demo export, validation, upcoming catalysts, public quality-gate diagnostics, risk budget, source pack, single-ticker drilldown, and snapshot compare.

`agent-handoff`

- JSON: `{ "schema_version": "agent-handoff/v1", "as_of": date, "generated_by": string, "handoff_objective": string, "parameters": object, "dataset_summary": object, "top_risks": [risk, ...], "stale_items": [item, ...], "commands_to_run_next": [command, ...], "source_urls": [source, ...] }`.
- Parameters: `--days`, `--stale-after-days`, `--fresh-after-days`, `--top-limit`, `--dataset-path`, `--output-dir`, and `--format json|markdown`.
- Dataset summary fields: `record_count`, `open_record_count`, `upcoming_record_count`, `completed_or_cancelled_count`, `stale_review_count`, `stale_evidence_count`, `missing_evidence_freshness_count`, `source_url_count`, `broker_view_count`, `status_counts`, `event_type_counts`, `urgency_counts`, `tickers`, and `thesis_ids`.
- Risk fields: `rank`, `id`, `ticker`, `entity`, `event_type`, `window`, `status`, `thesis_id`, `catalyst_score`, `urgency`, `review_state`, `days_until`, `confidence`, `portfolio_weight`, `risk_budget`, `max_loss`, `expected_event_loss`, `risk_flags`, `next_action`, and `source_urls`.
- Stale item fields: `id`, `ticker`, `entity`, `event_type`, `window`, `status`, `review_state`, `review_age_days`, `evidence_age_days`, `required_review_action`, `next_action`, and `evidence_urls`.
- Command fields: `id`, `command`, `output_path`, and `reason`.
- Source URL fields: `url`, `source_types`, `tickers`, `record_ids`, `thesis_ids`, `freshness_state`, `freshness_age_days`, `latest_checked_at`, and `broker_institutions`.
- Markdown: context summary, top-risk table, stale item table, command block, and source URL table.

`watchlist`

- JSON: `{ "as_of": date, "days": int, "stale_after_days": int, "items": [item, ...], "summary": object }`.
- Item fields: `watch_id`, `catalyst_id`, `ticker`, `entity`, `event_type`, `window`, `status`, `catalyst_score`, `priority_score`, `priority`, `urgency`, `review_state`, `days_until`, `due_date`, `due_state`, `review_cadence`, `trigger_conditions`, `required_review_action`, `thesis_id`, `source_ref`, `source_refs`, `evidence_urls`, `scenario_refs`.
- Trigger fields: `type`, `condition`, `action`.
- Summary fields: `item_count`, `critical_count`, `high_count`, `medium_count`, `low_count`, `due_now_count`.
- Markdown: watch queue table plus per-item trigger details.

`decision-log`

- JSON: `{ "as_of": date, "days": int, "stale_after_days": int, "memos": [memo, ...], "summary": object }`.
- Memo fields: `memo_id`, `prepared_on`, `decision_owner`, `decision_status`, `ticker`, `entity`, `thesis`, `catalyst`, `evidence`, `scenarios`, `broker_context`, `watchlist_triggers`, `decision_slots`, `post_event_review`.
- Summary fields: `memo_count`, `broker_context_count`, `stale_memo_count`, `trigger_count`.
- Markdown: one decision memo stub per catalyst.

`post-event`

- JSON: `{ "as_of": date, "review_after_days": int, "items": [item, ...], "summary": object }`.
- Item fields: `id`, `ticker`, `entity`, `event_type`, `window`, `status`, `confidence`, `catalyst_score`, `review_due`, `days_since_window_end`, `post_event_state`, `outcome_state`, `recorded_at_state`, `actual_outcome`, `outcome_recorded_at`, `required_review_action`, `thesis_id`, `thesis_impact`, `base_scenario`, `evidence_urls`, `source_ref`, `outcome_review_template`.
- Template fields: `actual_outcome`, `outcome_recorded_at`, `thesis_impact_after_event`, `scenario_accuracy`, `evidence_delta`, `position_or_risk_action`, `follow_up_action`, `source_update_needed`.
- Summary fields: `item_count`, `completed_count`, `overdue_count`, `missing_outcome_count`, `missing_recorded_at_count`.
- Markdown: outcome review queue plus templates.

`compare`

- Inputs: `--base` older dataset JSON path and `--current` newer dataset JSON path.
- Parameters: `--as-of`, `--stale-after-days`, `--format json|markdown`, optional `--output`.
- Matching: records are matched by stable `id`; unmatched current records are added events and unmatched base records are removed events.
- Scoring: base and current records are scored with the same `as_of` and `stale_after_days`.
- JSON: `{ "as_of": date, "base_as_of": date, "current_as_of": date, "stale_after_days": int, "added": [record summary, ...], "removed": [record summary, ...], "changed": [change, ...], "summary": object }`.
- Changed event fields: `id`, `ticker`, `entity`, `event_type`, `window`, `score_change`, `status_transition`, `evidence_change`, `thesis_impact_change`, `field_changes`, `scenario_note_changes`, `history_changes`, `broker_view_changes`.
- Score change fields: `from`, `to`, `delta`, `urgency_from`, `urgency_to`, `review_state_from`, `review_state_to`.
- Evidence change fields: `added_urls`, `removed_urls`, `unchanged_urls`, `checked_at_change`, `changed`.
- Broker view change fields: `added_views`, `removed_views`, `changed_views`; changed views are matched by `institution` and `source_url`.
- Summary fields: `added_count`, `removed_count`, `changed_count`, `score_change_count`, `status_transition_count`, `evidence_change_count`, `thesis_impact_change_count`.
- Markdown: added/removed tables plus changed-event summary and details.

`merge`

- Inputs: two or more dataset JSON paths as positional arguments.
- Parameters: optional `--as-of`, optional `--prefer-newer-status-history`, optional `--output`.
- Matching: records are grouped by stable `id`; merged output contains at most one record per id.
- Conflict handling: by default the candidate from the newest input dataset `as_of` wins, with later input order and later record index as deterministic tie-breakers.
- Status/history override: `--prefer-newer-status-history` keeps the normal winning record for all other fields, but takes `status` and `history` from the candidate whose latest history entry is newest.
- JSON: canonical dataset shape plus top-level `merge` diagnostics: `{ "as_of": date, "records": [record, ...], "merge": object }`.
- Merge diagnostics fields: `sources`, `record_sources`, `chosen_sources`, `status_history_sources`, `conflicts`, `duplicate_ids`, `prefer_newer_status_history`, `summary`, `validation`.
- Conflict fields: `id`, `fields`, `sources`, `source_count`, `chosen_source`, `status_history_source`.
- Duplicate-ID diagnostics report repeated ids within an input source and their original record indexes.
- Validation fields: `ok` and `errors`, using the same validation rules as `validate`.
- Exit status: `0` when the merged dataset validates, `1` when JSON diagnostics are produced but validation fails, and `2` for parse/filesystem/argument errors.

`html-dashboard`

- Output: deterministic no-JavaScript HTML document.
- Parameters: `--as-of`, `--days`, `--stale-after-days`, optional `--output`.
- Contract: escapes dataset text before embedding it and includes score tables, exposure, thesis map, evidence audit, scenario matrix, and watchlist sections.

`static-site`

- Input: dataset JSON.
- Parameters: required `--output-dir`, optional `--as-of`, `--days`, `--stale-after-days`, and `--fresh-after-days`.
- Output: JSON summary to stdout plus a deterministic no-JavaScript site directory.
- Files: `index.html`, `dashboard.html`, `sources.html`, `style.css`, `manifest.json`, and one `tickers/<ticker>.html` page for each ticker in the dataset.
- Contract: `--output-dir` must be empty; dynamic dataset text is escaped; `manifest.json` includes `site_version`, `as_of`, dataset record ids and tickers, parameters, and per-file `path`, `bytes`, and `sha256`.

`export-demo`

- Output: canonical demo dataset JSON.
- Optional `--output` writes the same text to a file.

`export-csv`

- Input: dataset JSON.
- Output: deterministic CSV dataset using the CSV schema above.
- Optional `--output` writes the same text to a file.

`import-csv`

- Input: CSV dataset.
- Output: canonical JSON dataset shape.
- Optional `--output` writes the same text to a file.

`export-ics`

- Input: dataset JSON.
- Selection: upcoming open records.
- Output: deterministic iCalendar 2.0 text with all-day `VEVENT` entries, stable UIDs, deterministic `DTSTAMP` from `--as-of`, escaped summary/description/category text, and first evidence URL as `URL`.
- Optional `--output` writes the same text to a file with calendar line endings preserved.

`create-archive`

- Input: dataset JSON.
- Parameters: `--output-dir`, `--as-of`, `--days`, `--stale-after-days`.
- Files: writes `dataset/dataset.json`, `dataset/dataset.csv`, all generated report fixtures including risk-budget and sector-map reports, `reports/upcoming.ics`, and `manifest.json`.
- Stdout: `{ "archive_dir": string, "file_count": int, "manifest": "manifest.json", "ok": true }`.
- The output directory must be empty when it already exists.

Archive manifest:

- Top-level fields: `archive_version`, `as_of`, `dataset`, `files`, `parameters`.
- `dataset`: `record_count`, `record_ids`.
- `files[]`: `path`, `bytes`, `sha256`.
- `parameters`: `days`, `stale_after_days`, `evidence_fresh_after_days`, `evidence_min_sources`, `evidence_max_domain_share`, `broker_stale_after_days`.

`verify-archive`

- Input: archive directory containing `manifest.json`.
- Success: exit `0`, JSON report `{ "ok": true, "archive_dir": string, "checked_files": [path, ...], "extra_files": [], "errors": [] }`.
- Failure: exit `1`, same report shape with `ok: false` and errors such as missing file, byte count mismatch, SHA-256 mismatch, untracked file, or unsupported archive version.
