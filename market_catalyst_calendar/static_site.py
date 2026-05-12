"""Deterministic multi-page static site generation."""

from __future__ import annotations

import hashlib
from datetime import date
from html import escape
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urlparse

from .dashboard import html_dashboard
from .models import CatalystRecord, Dataset, sorted_records
from .render import records_json, source_pack_json, watchlist_json
from .scoring import score_record


SITE_VERSION = 1


def create_static_site(
    dataset: Dataset,
    output_dir: str,
    as_of: date,
    days: int,
    stale_after_days: int,
    fresh_after_days: int = 14,
) -> Dict[str, object]:
    """Write a deterministic no-JavaScript multi-page site and return its manifest."""

    destination = Path(output_dir)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"static-site output directory must be empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    records = sorted_records(dataset.records)
    upcoming = _upcoming_records(records, as_of, days)
    tickers = sorted({record.ticker for record in records})
    source_payload = source_pack_json(records, as_of, fresh_after_days)

    files: Dict[str, str] = {
        "index.html": _index_page(records, upcoming, tickers, as_of, days, stale_after_days),
        "dashboard.html": html_dashboard(records, as_of, days, stale_after_days, fresh_after_days),
        "sources.html": _sources_page(source_payload, as_of, fresh_after_days),
        "style.css": _style(),
    }
    for ticker in tickers:
        ticker_records = [record for record in records if record.ticker == ticker]
        files[f"tickers/{_ticker_slug(ticker)}.html"] = _ticker_page(ticker, ticker_records, as_of, days, stale_after_days)

    for relative_path, text in sorted(files.items()):
        _write_text(destination / relative_path, text)

    manifest = _manifest(destination, sorted(files), dataset, as_of, days, stale_after_days, fresh_after_days, tickers)
    _write_text(destination / "manifest.json", _json_like(manifest))
    return manifest


def _index_page(
    records: List[CatalystRecord],
    upcoming: List[CatalystRecord],
    tickers: List[str],
    as_of: date,
    days: int,
    stale_after_days: int,
) -> str:
    scored = records_json(upcoming, as_of)["records"]
    stale_count = sum(1 for record in records if score_record(record, as_of, stale_after_days=stale_after_days).review_state == "stale")
    watch_payload = watchlist_json(records, as_of, days, stale_after_days)
    cards = [
        ("Records", len(records), "total catalysts"),
        ("Upcoming", len(upcoming), f"next {days} days"),
        ("Tickers", len(tickers), "linked pages"),
        ("Stale", stale_count, "need review"),
        ("Watch Items", watch_payload["summary"]["item_count"], "open queue"),
    ]
    rows = []
    for item in scored:
        rows.append(
            _tr(
                [
                    _td(str(item["catalyst_score"]), "num strong"),
                    _td_raw(_link(str(item["ticker"]), f"tickers/{_ticker_slug(str(item['ticker']))}.html"), "ticker"),
                    _td(str(item["event_type"]).replace("_", " ")),
                    _td(str(item["window"])),
                    _td(str(item["urgency"]), f"pill {_pill_class(str(item['urgency']))}"),
                    _td(str(item["review_state"]), f"pill {_pill_class(str(item['review_state']))}"),
                ]
            )
        )
    ticker_links = ", ".join(_link(ticker, f"tickers/{_ticker_slug(ticker)}.html") for ticker in tickers)
    content = [
        _cards(cards),
        _section("Ticker Pages", "Each linked page preserves record details, scenarios, broker context, and evidence.", f'<p class="links">{ticker_links}</p>'),
        _section("Upcoming Catalysts", "Open catalysts in the forward site window.", _table(["Score", "Ticker", "Event", "Window", "Urgency", "Review"], rows)),
    ]
    return _page("Market Catalyst Site", "Index", as_of, "index", "\n".join(content))


def _ticker_page(ticker: str, records: List[CatalystRecord], as_of: date, days: int, stale_after_days: int) -> str:
    rows = []
    for record in records:
        score = score_record(record, as_of, stale_after_days=stale_after_days)
        rows.append(
            _tr(
                [
                    _td(str(score.catalyst_score), "num strong"),
                    _td(record.record_id, "wide"),
                    _td(record.entity, "wide"),
                    _td(record.event_type.replace("_", " ")),
                    _td(record.window.label),
                    _td(record.status),
                    _td(score.urgency, f"pill {_pill_class(score.urgency)}"),
                    _td(score.review_state, f"pill {_pill_class(score.review_state)}"),
                ]
            )
        )
    scenario_rows = []
    source_items = []
    broker_rows = []
    for record in records:
        for name in ["bull", "base", "bear"]:
            scenario_rows.append(_tr([_td(record.record_id, "wide"), _td(name), _td(record.scenario_notes.get(name, ""), "wide")]))
        for url in record.evidence_urls:
            source_items.append(f'<li>{_safe_external_link(url)} <span>{_h(record.record_id)}</span></li>')
        for view in record.broker_views:
            broker_rows.append(
                _tr(
                    [
                        _td(view.institution, "wide"),
                        _td(view.rating),
                        _td(f"{view.target_price:.2f}", "num"),
                        _td(view.as_of.isoformat()),
                        _td_raw(_safe_external_link(view.source_url), "wide"),
                        _td(view.caveat, "wide"),
                    ]
                )
            )
    content = "\n".join(
        [
            _cards(
                [
                    ("Records", len(records), ticker),
                    ("Upcoming", sum(1 for record in records if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days), f"next {days} days"),
                    ("Broker Views", sum(len(record.broker_views) for record in records), "recorded"),
                    ("Sources", sum(len(record.evidence_urls) for record in records), "evidence URLs"),
                ]
            ),
            _section("Record Ledger", "Catalysts for this ticker.", _table(["Score", "ID", "Entity", "Event", "Window", "Status", "Urgency", "Review"], rows)),
            _section("Scenario Notes", "Bull, base, and bear notes are copied from the dataset.", _table(["Record", "Case", "Note"], scenario_rows)),
            _section("Broker Views", "Optional analyst snapshots attached to this ticker.", _table(["Institution", "Rating", "Target", "As Of", "Source", "Caveat"], broker_rows)),
            _section("Evidence Links", "Source URLs used by this ticker.", "<ul>" + "".join(source_items) + "</ul>" if source_items else '<p class="empty">No evidence URLs.</p>'),
        ]
    )
    return _page(f"{ticker} Catalyst Page", ticker, as_of, "ticker", content)


def _sources_page(payload: Dict[str, object], as_of: date, fresh_after_days: int) -> str:
    rows = []
    for source in payload["sources"]:  # type: ignore[index]
        rows.append(
            _tr(
                [
                    _td(str(source["freshness_state"]), f"pill {_pill_class(str(source['freshness_state']))}"),
                    _td(str(source["usage_count"]), "num"),
                    _td(", ".join(str(item) for item in source["source_types"])),
                    _td(", ".join(str(item) for item in source["tickers"]), "ticker"),
                    _td(str(source["evidence_checked_at"])),
                    _td_raw(_safe_external_link(str(source["url"])), "wide"),
                ]
            )
        )
    summary = payload["summary"]  # type: ignore[index]
    content = "\n".join(
        [
            _cards(
                [
                    ("Sources", summary["source_count"], "deduped URLs"),
                    ("Evidence", summary["evidence_source_count"], "source URLs"),
                    ("Broker", summary["broker_source_count"], "source URLs"),
                    ("Fresh Window", fresh_after_days, "days"),
                ]
            ),
            _section("Source Inventory", "Evidence and broker source URLs deduplicated across the dataset.", _table(["Freshness", "Uses", "Types", "Tickers", "Checked", "URL"], rows)),
        ]
    )
    return _page("Market Catalyst Sources", "Sources", as_of, "sources", content)


def _page(title: str, heading: str, as_of: date, active: str, content: str) -> str:
    root_prefix = "../" if active == "ticker" else ""
    nav = [
        ("Index", f"{root_prefix}index.html", "index"),
        ("Dashboard", f"{root_prefix}dashboard.html", "dashboard"),
        ("Sources", f"{root_prefix}sources.html", "sources"),
    ]
    links = "".join(
        f'<a class="{"active" if key == active else ""}" href="{_h(href)}">{_h(label)}</a>'
        for label, href, key in nav
    )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_h(title)}</title>",
            f'<link rel="stylesheet" href="{_h(root_prefix)}style.css">',
            "</head>",
            "<body>",
            '<main class="page">',
            '<header class="hero">',
            f"<nav>{links}</nav>",
            "<p>Market Catalyst Calendar</p>",
            f"<h1>{_h(heading)}</h1>",
            f"<span>As of {_h(as_of.isoformat())} - static no-JavaScript site</span>",
            "</header>",
            content,
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def _cards(items: List[tuple[str, object, str]]) -> str:
    return '<section class="cards" aria-label="Summary">' + "".join(
        f'<article class="card"><span>{_h(label)}</span><strong>{_h(str(value))}</strong><small>{_h(note)}</small></article>'
        for label, value, note in items
    ) + "</section>"


def _section(title: str, description: str, content: str) -> str:
    return f'<section class="panel"><h2>{_h(title)}</h2><p>{_h(description)}</p>{content}</section>'


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


def _td_raw(value: str, class_name: str = "") -> str:
    class_attr = f' class="{_h(class_name)}"' if class_name else ""
    return f"<td{class_attr}>{value}</td>"


def _link(label: str, href: str) -> str:
    return f'<a href="{_h(href)}">{_h(label)}</a>'


def _safe_external_link(url: str) -> str:
    parsed = urlparse(url)
    label = parsed.netloc + parsed.path
    if len(label) > 88:
        label = label[:85] + "..."
    return f'<a href="{_h(url)}" rel="noreferrer">{_h(label or url)}</a>'


def _h(value: str) -> str:
    return escape(value, quote=True)


def _pill_class(value: str) -> str:
    normalized = value.lower().replace("_", "-")
    if normalized in {"critical", "high", "stale", "missing"}:
        return "bad"
    if normalized in {"medium", "due-now", "mixed"}:
        return "warn"
    if normalized in {"low", "fresh", "positive", "current"}:
        return "good"
    return "neutral"


def _ticker_slug(ticker: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in ticker).strip("-") or "ticker"


def _upcoming_records(records: Iterable[CatalystRecord], as_of: date, days: int) -> List[CatalystRecord]:
    return [
        record
        for record in records
        if record.status not in {"completed", "cancelled"} and 0 <= (record.window.start - as_of).days <= days
    ]


def _manifest(
    root: Path,
    relative_paths: List[str],
    dataset: Dataset,
    as_of: date,
    days: int,
    stale_after_days: int,
    fresh_after_days: int,
    tickers: List[str],
) -> Dict[str, object]:
    files = []
    for relative_path in relative_paths:
        digest, byte_count = _hash_file(root / relative_path)
        files.append({"bytes": byte_count, "path": relative_path, "sha256": digest})
    return {
        "site_version": SITE_VERSION,
        "as_of": as_of.isoformat(),
        "dataset": {
            "record_count": len(dataset.records),
            "record_ids": [record.record_id for record in sorted_records(dataset.records)],
            "tickers": tickers,
        },
        "files": files,
        "parameters": {
            "days": days,
            "fresh_after_days": fresh_after_days,
            "stale_after_days": stale_after_days,
        },
    }


def _hash_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    data = path.read_bytes()
    digest.update(data)
    return digest.hexdigest(), len(data)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _json_like(payload: Dict[str, object]) -> str:
    import json

    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _style() -> str:
    return """\
:root{color-scheme:light;--ink:#18212f;--muted:#607085;--line:#d8e0e8;--panel:#ffffff;--bg:#f5f7fa;--brand:#245c73;--accent:#7b4b20;--good:#276749;--warn:#8a5a00;--bad:#a32626;--neutral:#4b5563}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:var(--brand);font-weight:700;text-decoration:none}
a:hover{text-decoration:underline}
.page{max-width:1160px;margin:0 auto;padding:28px 20px 44px}
.hero{border-bottom:3px solid var(--brand);padding:10px 0 22px;margin-bottom:18px}
.hero nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}
.hero nav a{border:1px solid var(--line);border-radius:6px;padding:6px 9px;background:#fff}
.hero nav a.active{background:var(--brand);border-color:var(--brand);color:#fff}
.hero p{margin:0 0 6px;color:var(--accent);font-weight:700;text-transform:uppercase;font-size:12px}
.hero h1{margin:0;font-size:30px;line-height:1.12;letter-spacing:0}
.hero span{display:block;margin-top:8px;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:18px 0 20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px;min-height:88px}
.card span,.card small{display:block;color:var(--muted)}
.card strong{display:block;font-size:24px;margin:7px 0;color:var(--brand)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:16px;margin-top:14px}
.panel h2{font-size:20px;margin:0 0 4px;letter-spacing:0}
.panel>p{margin:0 0 12px;color:var(--muted)}
.links{line-height:1.9}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:6px}
table{width:100%;border-collapse:collapse;min-width:760px}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{background:#edf2f7;color:#334155;font-size:12px;text-transform:uppercase}
tr:last-child td{border-bottom:0}
ul{margin:0;padding-left:20px}
li{margin:7px 0}
li span{color:var(--muted)}
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
@media (max-width:900px){.cards{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:560px){.page{padding:18px 12px 30px}.cards{grid-template-columns:1fr}.hero h1{font-size:25px}}
"""
