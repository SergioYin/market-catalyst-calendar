# Release Notes

## Unreleased

- Added `impact-brief`, an offline deterministic public-finance CLI workflow with Markdown and JSON output.
- Added `impact-dashboard`, a static non-advisory impact panel that summarizes datasets or impact-brief JSON snapshots into horizon, evidence-state counts, impact flags, top attention catalysts, and review queue.
- Added `impact-compare`, an offline deterministic impact-brief delta workflow for static datasets or generated impact-brief JSON snapshots.
- Added `impact-artifact-receipt`, an offline receipt for impact example artifacts with rerun commands, fixture paths, output paths, byte sizes, SHA-256 hashes, schema labels, and fixed finance boundaries.
- Added `impact-receipt-compare`, a deterministic JSON/Markdown comparator for release-to-release impact artifact receipt drift.
- Added `impact-capture-checklist`, a deterministic JSON/Markdown release-evidence checklist for public-safe screenshot/GIF capture of impact brief, dashboard, compare, and artifact receipt examples.
- Added `visual-evidence-receipt`, a static visual/demo artifact receipt with relative paths, byte sizes, SHA-256 hashes, roles, routes, regeneration commands, capture commands, and explicit static-only/local-fixtures/no-live-data/no-broker/no-orders/no-advice/no-private-data boundaries.
- The workflow uses checked-in visual/demo artifacts and bundled demo fixtures, and explicitly excludes live data, broker connectivity, orders, personalized investment advice, private account data, and trade recommendations.
- Added impact-brief tests, schema docs, README usage, and deterministic example fixtures.
