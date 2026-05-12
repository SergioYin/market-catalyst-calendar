"""Built-in deterministic demo dataset."""

DEMO_DATA = {
    "as_of": "2026-05-13",
    "records": [
        {
            "id": "demo-nvda-computex-2026",
            "ticker": "NVDA",
            "entity": "NVIDIA Corporation",
            "event_type": "product_launch",
            "date": "2026-06-02",
            "confidence": 0.74,
            "position_size": 125000,
            "portfolio_weight": 0.0825,
            "thesis_id": "ai-infrastructure-capex",
            "source_ref": "NVDA Computex keynote tracker",
            "status": "scheduled",
            "history": [
                {
                    "date": "2026-05-01",
                    "status": "scheduled",
                    "note": "Conference keynote timing added to calendar.",
                }
            ],
            "thesis_impact": "positive",
            "evidence_urls": [
                "https://example.com/nvidia-computex-keynote",
                "https://example.com/channel-check-gpu-supply",
            ],
            "scenario_notes": {
                "bull": "Management confirms accelerated platform demand and shorter supply constraints.",
                "base": "Product roadmap details support existing accelerator growth expectations.",
                "bear": "Launch focuses on refresh timing without incremental demand signals.",
            },
            "required_review_action": "monitor_date",
            "last_reviewed": "2026-05-09",
            "evidence_checked_at": "2026-05-09",
            "broker_views": [
                {
                    "institution": "North Coast Securities",
                    "rating": "buy",
                    "target_price": 1320.0,
                    "as_of": "2026-05-10",
                    "source_url": "https://example.com/nvda-broker-north-coast",
                    "caveat": "Target assumes accelerator backlog converts into second-half revenue.",
                },
                {
                    "institution": "Metro Capital Markets",
                    "rating": "hold",
                    "target_price": 1085.0,
                    "as_of": "2026-04-05",
                    "source_url": "https://example.com/nvda-broker-metro",
                    "caveat": "Older view predates the final Computex keynote agenda.",
                },
            ],
        },
        {
            "id": "demo-pfe-fda-2026",
            "ticker": "PFE",
            "entity": "Pfizer Inc.",
            "event_type": "regulatory_decision",
            "window": {"start": "2026-05-20", "end": "2026-05-24"},
            "confidence": 0.68,
            "position_size": 48000,
            "portfolio_weight": 0.031,
            "thesis_id": "pharma-pipeline-reset",
            "source_ref": "FDA calendar and PFE pipeline note",
            "status": "watching",
            "history": [
                {
                    "date": "2026-04-28",
                    "status": "watching",
                    "note": "Regulatory decision window estimated from public review timeline.",
                }
            ],
            "thesis_impact": "mixed",
            "evidence_urls": [
                "https://example.com/fda-calendar",
                "https://example.com/pfe-pipeline-update",
            ],
            "scenario_notes": {
                "bull": "Approval expands pipeline credibility and supports forward revenue mix.",
                "base": "Decision is mostly expected but clarifies launch timing.",
                "bear": "Delay or restrictive label pressures near-term sentiment.",
            },
            "required_review_action": "verify_source",
            "last_reviewed": "2026-04-28",
            "evidence_checked_at": "2026-04-28",
            "broker_views": [
                {
                    "institution": "Harbor Life Sciences",
                    "rating": "market perform",
                    "target_price": 31.0,
                    "as_of": "2026-05-01",
                    "source_url": "https://example.com/pfe-broker-harbor",
                    "caveat": "View depends on label breadth and launch timing after the decision window.",
                },
                {
                    "institution": "Summit Research",
                    "rating": "outperform",
                    "target_price": 39.0,
                    "as_of": "2026-04-10",
                    "source_url": "https://example.com/pfe-broker-summit",
                    "caveat": "Model gives partial credit for approval but not a restrictive label.",
                },
            ],
        },
        {
            "id": "demo-fomc-june-2026",
            "ticker": "SPY",
            "entity": "S&P 500 ETF Trust",
            "event_type": "macro_release",
            "date": "2026-06-17",
            "confidence": 0.9,
            "portfolio_weight": 0.22,
            "thesis_id": "rates-duration-risk",
            "source_ref": "FOMC public calendar",
            "status": "confirmed",
            "history": [
                {
                    "date": "2026-05-08",
                    "status": "confirmed",
                    "note": "FOMC date confirmed from public central bank calendar.",
                }
            ],
            "thesis_impact": "mixed",
            "evidence_urls": ["https://example.com/fomc-calendar"],
            "scenario_notes": {
                "bull": "Policy language indicates lower real-rate pressure for duration assets.",
                "base": "Statement broadly matches market-implied policy path.",
                "bear": "Inflation language reprices yields higher and weighs on multiples.",
            },
            "required_review_action": "monitor_date",
            "last_reviewed": "2026-05-08",
        },
    ],
}
