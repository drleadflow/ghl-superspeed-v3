---
type: campaign-index
last_updated: 2026-05-05
---

# Campaign Index

Each row links a `*.py` file in this folder to the services and offers it serves.

| File | Purpose | Services | Offers | Deployed To |
|------|---------|----------|--------|-------------|
| `campaigns/example-simple.py` | Reference example | — | — | — |
| `campaigns/ppp-webinar.py` | PPP webinar funnel | — | — | — |
| `campaigns/iv-wellness-nurture.py` | IV Wellness nurture sequence | [[services/boost-drip]], [[services/focus-drip]], [[services/immunity-drip]], [[services/recover-drip]], [[services/myers-drip]], [[services/nad-250mg]], [[services/nad-500mg]], [[services/wellness-check]] | [[offers/iv-first-visit]], [[offers/iv-signature-3]], [[offers/iv-six-pack]], [[offers/iv-nad-starter]] | [[clients/iv-wellness/overview\|IV Wellness]] |

## How to document a campaign

1. Add or update its row above
2. Link `Services` and `Offers` cells with wikilinks: `[[services/<slug>]]`, `[[offers/<slug>]]`
3. Note which clients it's been deployed to (kept short — full per-client notes go in `clients/<name>/campaigns.md`)
