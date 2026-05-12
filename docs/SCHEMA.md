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
as_of,id,ticker,entity,event_type,window_start,window_end,confidence,position_size,portfolio_weight,thesis_id,source_ref,status,thesis_impact,required_review_action,last_reviewed,evidence_checked_at,actual_outcome,outcome_recorded_at,evidence_urls,scenario_notes,history,broker_views
```

Required CSV columns are all columns except `position_size`, `portfolio_weight`, `thesis_id`, `source_ref`, `evidence_checked_at`, `actual_outcome`, `outcome_recorded_at`, and `broker_views`.

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
- Success: exit `0`, JSON object `{ "ok": true, "record_count": int }`.
- Validation failure: exit `1`, JSON object `{ "ok": false, "errors": [string, ...] }`.

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
| Optional fields | mixed | `position_size`, `portfolio_weight`, `thesis_id`, `source_ref`, `evidence_checked_at`, `broker_views`, `actual_outcome`, `outcome_recorded_at` appear only when present. |

`exposure`

- JSON: `{ "as_of": date, "groups": [group, ...], "summary": object }`.
- Group fields: `ticker`, `event_type`, `urgency`, `record_count`, `portfolio_weight`, `position_size`, `weighted_exposure`, `weighted_position_exposure`, `records`.
- Summary fields: `group_count`, `record_count`, `portfolio_weight`, `position_size`, `weighted_exposure`, `weighted_position_exposure`.
- Markdown: exposure totals plus grouped table.

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

`html-dashboard`

- Output: deterministic no-JavaScript HTML document.
- Parameters: `--as-of`, `--days`, `--stale-after-days`, optional `--output`.
- Contract: escapes dataset text before embedding it and includes score tables, exposure, thesis map, evidence audit, scenario matrix, and watchlist sections.

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
- Files: writes `dataset/dataset.json`, `dataset/dataset.csv`, all generated report fixtures, `reports/upcoming.ics`, and `manifest.json`.
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
