"""Static no-JavaScript HTML dashboard rendering."""

from __future__ import annotations

from datetime import date
from html import escape
from typing import Dict, Iterable, List

from .evidence import evidence_audit_json
from .models import CatalystRecord
from .render import (
    exposure_json,
    records_json,
    scenario_matrix_json,
    thesis_map_json,
    watchlist_json,
)


def html_dashboard(
    records: Iterable[CatalystRecord],
    as_of: date,
    days: int,
    stale_after_days: int,
    evidence_fresh_after_days: int = 14,
    evidence_min_sources: int = 2,
    evidence_max_domain_share: float = 0.67,
) -> str:
    """Render a deterministic, escaped, no-JavaScript HTML dashboard."""

    record_list = list(records)
    upcoming = [
        record
        for record in record_list
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]
    score_payload = records_json(upcoming, as_of)
    exposure_payload = exposure_json(upcoming, as_of)
    thesis_payload = thesis_map_json(record_list, as_of, stale_after_days)
    scenario_payload = scenario_matrix_json(upcoming, as_of, stale_after_days)
    evidence_payload = evidence_audit_json(
        record_list,
        as_of,
        evidence_fresh_after_days,
        evidence_min_sources,
        evidence_max_domain_share,
    )
    watchlist_payload = watchlist_json(record_list, as_of, days, stale_after_days)

    summary_cards = [
        ("Upcoming", len(score_payload["records"]), f"next {days} days"),
        ("Portfolio Weight", _percent(exposure_payload["summary"]["portfolio_weight"]), "upcoming exposure"),
        ("Weighted Exposure", _percent(exposure_payload["summary"]["weighted_exposure"]), "score adjusted"),
        ("Evidence Flags", evidence_payload["summary"]["flagged_record_count"], "records to audit"),
        ("Watch Items", watchlist_payload["summary"]["item_count"], "open catalysts"),
        ("Stale Thesis Links", thesis_payload["summary"]["stale_count"], "mapped records"),
    ]

    sections = [
        _score_table(score_payload["records"]),
        _exposure_summary(exposure_payload),
        _thesis_map(thesis_payload),
        _evidence_audit(evidence_payload),
        _scenario_matrix(scenario_payload),
        _watchlist(watchlist_payload),
    ]

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_h('Market Catalyst Dashboard')}</title>",
            _style(),
            "</head>",
            "<body>",
            '<main class="page">',
            '<header class="hero">',
            "<div>",
            "<p>Market Catalyst Calendar</p>",
            "<h1>Static Catalyst Dashboard</h1>",
            f"<span>As of {_h(as_of.isoformat())} - deterministic offline report - no JavaScript</span>",
            "</div>",
            "</header>",
            '<section class="cards" aria-label="Dashboard summary">',
            "".join(_card(label, value, note) for label, value, note in summary_cards),
            "</section>",
            *sections,
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def _score_table(records: List[Dict[str, object]]) -> str:
    rows = []
    for record in records:
        rows.append(
            _tr(
                [
                    _td(str(record["catalyst_score"]), "num strong"),
                    _td(str(record["ticker"]), "ticker"),
                    _td(str(record["event_type"]).replace("_", " ")),
                    _td(str(record["window"])),
                    _td(str(record["urgency"]), f"pill {_pill_class(str(record['urgency']))}"),
                    _td(str(record["review_state"]), f"pill {_pill_class(str(record['review_state']))}"),
                    _td(str(record["thesis_impact"])),
                ]
            )
        )
    return _section(
        "Score Tables",
        "Upcoming catalysts ranked by deterministic catalyst score.",
        _table(["Score", "Ticker", "Event", "Window", "Urgency", "Review", "Impact"], rows),
    )


def _exposure_summary(payload: Dict[str, object]) -> str:
    summary = payload["summary"]  # type: ignore[index]
    totals = _definition_grid(
        [
            ("Records", summary["record_count"]),
            ("Position Size", _money(summary["position_size"])),
            ("Portfolio Weight", _percent(summary["portfolio_weight"])),
            ("Weighted Position", _money(summary["weighted_position_exposure"])),
            ("Weighted Exposure", _percent(summary["weighted_exposure"])),
        ]
    )
    rows = []
    for group in payload["groups"]:  # type: ignore[index]
        rows.append(
            _tr(
                [
                    _td(str(group["ticker"]), "ticker"),
                    _td(str(group["event_type"]).replace("_", " ")),
                    _td(str(group["urgency"]), f"pill {_pill_class(str(group['urgency']))}"),
                    _td(str(group["record_count"]), "num"),
                    _td(_percent(group["portfolio_weight"]), "num"),
                    _td(_percent(group["weighted_exposure"]), "num strong"),
                    _td(_money(group["position_size"]), "num"),
                    _td(_money(group["weighted_position_exposure"]), "num strong"),
                ]
            )
        )
    return _section(
        "Exposure Summary",
        "Portfolio and notional exposure adjusted by confidence and catalyst score.",
        totals + _table(["Ticker", "Event", "Urgency", "Records", "Weight", "Weighted", "Position", "Weighted Position"], rows),
    )


def _thesis_map(payload: Dict[str, object]) -> str:
    rows = []
    for group in payload["groups"]:  # type: ignore[index]
        rows.append(
            _tr(
                [
                    _td(str(group["thesis_id"]), "wide"),
                    _td(str(group["open_event_count"]), "num"),
                    _td(str(group["highest_score"]), "num strong"),
                    _td(str(group["stale_count"]), "num"),
                    _td(", ".join(str(record_id) for record_id in group["records"]), "wide"),
                ]
            )
        )
    return _section(
        "Thesis Map",
        "Catalysts grouped by investment thesis with stale-link visibility.",
        _table(["Thesis", "Open", "Top Score", "Stale", "Records"], rows),
    )


def _evidence_audit(payload: Dict[str, object]) -> str:
    rows = []
    for item in payload["records"]:  # type: ignore[index]
        rows.append(
            _tr(
                [
                    _td(str(item["severity"]), f"pill {_pill_class(str(item['severity']))}"),
                    _td(str(item["ticker"]), "ticker"),
                    _td(str(item["id"]), "wide"),
                    _td(str(item["evidence_checked_at"] or "missing")),
                    _td(str(item["evidence_url_count"]), "num"),
                    _td(str(item["dominant_source_domain"] or "none")),
                    _td(", ".join(str(flag) for flag in item["flags"]), "wide"),
                    _td(str(item["next_action"]), "wide"),
                ]
            )
        )
    empty = "<p class=\"empty\">No evidence freshness or source concentration flags.</p>" if not rows else ""
    return _section(
        "Evidence Audit",
        "Offline checks for freshness metadata, source count, and domain concentration.",
        empty
        + _table(["Severity", "Ticker", "Record", "Checked", "Sources", "Dominant Domain", "Flags", "Next Action"], rows),
    )


def _scenario_matrix(payload: Dict[str, object]) -> str:
    rows = []
    for record in payload["records"]:  # type: ignore[index]
        for scenario in record["scenarios"]:
            rows.append(
                _tr(
                    [
                        _td(str(record["ticker"]), "ticker"),
                        _td(str(scenario["scenario"]).title()),
                        _td(str(scenario["score"]), "num strong"),
                        _td(str(scenario["date"])),
                        _td(str(scenario["impact"])),
                        _td(str(scenario["review_action"]), "wide"),
                        _td(str(scenario["note"]), "wide"),
                    ]
                )
            )
    return _section(
        "Scenario Matrix",
        "Bull, base, and bear paths with scenario-adjusted scores and review actions.",
        _table(["Ticker", "Scenario", "Score", "Date", "Impact", "Review Action", "Note"], rows),
    )


def _watchlist(payload: Dict[str, object]) -> str:
    rows = []
    for item in payload["items"]:  # type: ignore[index]
        rows.append(
            _tr(
                [
                    _td(str(item["priority"]), f"pill {_pill_class(str(item['priority']))}"),
                    _td(str(item["priority_score"]), "num strong"),
                    _td(str(item["due_date"])),
                    _td(str(item["review_cadence"])),
                    _td(str(item["ticker"]), "ticker"),
                    _td(str(item["event_type"]).replace("_", " ")),
                    _td("; ".join(str(trigger["condition"]) for trigger in item["trigger_conditions"]), "wide"),
                ]
            )
        )
    return _section(
        "Watchlist",
        "Prioritized review queue with due dates, cadence, and trigger conditions.",
        _table(["Priority", "Score", "Due", "Cadence", "Ticker", "Event", "Triggers"], rows),
    )


def _section(title: str, description: str, content: str) -> str:
    return (
        '<section class="panel">'
        f"<h2>{_h(title)}</h2>"
        f"<p>{_h(description)}</p>"
        f"{content}"
        "</section>"
    )


def _card(label: str, value: object, note: str) -> str:
    return f'<article class="card"><span>{_h(label)}</span><strong>{_h(str(value))}</strong><small>{_h(note)}</small></article>'


def _definition_grid(items: List[tuple[str, object]]) -> str:
    cells = []
    for label, value in items:
        cells.append(f"<div><dt>{_h(label)}</dt><dd>{_h(str(value))}</dd></div>")
    return '<dl class="metrics">' + "".join(cells) + "</dl>"


def _table(headers: List[str], rows: List[str]) -> str:
    if not rows:
        return '<p class="empty">No matching records.</p>'
    thead = "".join(f"<th>{_h(header)}</th>" for header in headers)
    return f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def _tr(cells: List[str]) -> str:
    return "<tr>" + "".join(cells) + "</tr>"


def _td(value: str, class_name: str = "") -> str:
    class_attr = f' class="{_h(class_name)}"' if class_name else ""
    return f"<td{class_attr}>{_h(value)}</td>"


def _h(value: str) -> str:
    return escape(value, quote=True)


def _percent(value: object) -> str:
    return f"{float(value) * 100:.2f}%"


def _money(value: object) -> str:
    return f"{float(value):,.2f}"


def _pill_class(value: str) -> str:
    normalized = value.lower().replace("_", "-")
    if normalized in {"critical", "high", "stale"}:
        return "bad"
    if normalized in {"medium", "due-now", "mixed"}:
        return "warn"
    if normalized in {"low", "fresh", "positive"}:
        return "good"
    return "neutral"


def _style() -> str:
    return """<style>
:root{color-scheme:light;--ink:#17202a;--muted:#5f6b7a;--line:#d9e0e8;--panel:#ffffff;--bg:#f5f7fa;--brand:#245c73;--accent:#7b4b20;--good:#276749;--warn:#8a5a00;--bad:#a32626;--neutral:#4b5563}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.page{max-width:1180px;margin:0 auto;padding:28px 20px 44px}
.hero{border-bottom:3px solid var(--brand);padding:10px 0 22px;margin-bottom:18px}
.hero p{margin:0 0 6px;color:var(--accent);font-weight:700;text-transform:uppercase;font-size:12px}
.hero h1{margin:0;font-size:32px;line-height:1.1;letter-spacing:0}
.hero span{display:block;margin-top:8px;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin:18px 0 20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px;min-height:92px}
.card span,.card small{display:block;color:var(--muted)}
.card strong{display:block;font-size:24px;margin:7px 0;color:var(--brand)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:16px;margin-top:14px}
.panel h2{font-size:20px;margin:0 0 4px;letter-spacing:0}
.panel>p{margin:0 0 12px;color:var(--muted)}
.metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin:0 0 14px}
.metrics div{border:1px solid var(--line);border-radius:6px;padding:10px}
.metrics dt{color:var(--muted);font-size:12px}
.metrics dd{margin:4px 0 0;font-size:18px;font-weight:700}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:6px}
table{width:100%;border-collapse:collapse;min-width:760px}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{background:#edf2f7;color:#334155;font-size:12px;text-transform:uppercase}
tr:last-child td{border-bottom:0}
.num{text-align:right;font-variant-numeric:tabular-nums}
.strong{font-weight:700}
.ticker{font-weight:800;color:var(--brand)}
.wide{min-width:180px}
.pill{font-weight:700}
.pill.good{color:var(--good)}
.pill.warn{color:var(--warn)}
.pill.bad{color:var(--bad)}
.pill.neutral{color:var(--neutral)}
.empty{color:var(--muted);font-style:italic}
@media (max-width:900px){.cards{grid-template-columns:repeat(3,minmax(0,1fr))}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:560px){.page{padding:18px 12px 30px}.cards,.metrics{grid-template-columns:1fr}.hero h1{font-size:26px}}
</style>"""
