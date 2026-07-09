---
name: ghl-ops
description: Operate GoHighLevel for DLF client accounts — ghl CLI gotchas, SuperSpeed workflow engine, and the landing-page→tag funnel pattern. Use for any GHL task - creating contacts/tags/workflows, building landing pages that feed GHL, auditing accounts, or wiring form→tag→AI-setter automations.
---

# GHL Ops — tools, gotchas, and proven patterns

## Account map (verify against memory `closebot-account-map` — it wins on conflict)

| Client | GHL location ID |
|---|---|
| TVAAI (Houston) | jiR5qR3g4OrMRx6BmpF2 |
| MDW Aesthetics | zEpu0chRlGpqTiBg0D3n |
| Dr. Lead Flow (Christian's TEST acct) | W7BRJwzJCvFs9r0xZHrE |

NEVER trust location IDs hardcoded in `campaigns/*.py` — `2hP6rCb3COd2HUjD25w2` is Christian's, not a client's.

## ghl CLI (v2 public API) — the workhorse

Profiles in `~/.config/ghl/config.json` (`profiles.<name>.apiKey` = PIT token, plus `locationId`).

**BROKEN: global `--profile` and `--location` flags are ignored** — requests always use the default profile's location. Workaround:

```bash
ghl auth use tvaai          # switch default BEFORE the calls
# ... do work ...
ghl auth use dlf            # ALWAYS restore when done (dlf = MDW's location, misnamed)
```

Raw calls (body flag is `--data`, not `--body`):
```bash
ghl raw GET  "/locations/<LOC>/tags"
ghl raw POST /contacts/search --data '{"locationId":"<LOC>","query":"...","pageLimit":5}'
ghl raw POST /contacts/upsert --data '{"locationId":"<LOC>","firstName":"X","phone":"+1832...","tags":["atlas"],"source":"..."}'
ghl raw POST /contacts/<id>/tags --data '{"tags":["atlas"]}'
ghl raw DELETE /contacts/<id>
```
Pipe JSON to a scratchpad file before parsing — CLI sometimes prefixes non-JSON lines.

Scope notes: TVAAI PIT has everything EXCEPT `/payments/*` (403). Public v2 API cannot create workflows or forms.

## SuperSpeed engine (internal API) — workflow creation

`lib/engine.py` hits `backend.leadconnectorhq.com` (GHL internal API). Needs a **Firebase token**, NOT a PIT. Token sources, in order (see `TokenManager`):
1. MCP server `https://dlf-agency.skool-203.workers.dev` (Chrome extension deposits tokens there)
2. `GHL_FIREBASE_REFRESH_TOKEN` in project `.env` (auto-refresh via Firebase API)
3. `GHL_FIREBASE_TOKEN` env var, or CLI arg

Capabilities: create workflows + steps (56 verified action types in `VERIFIED_ACTIONS`) + triggers. Proven trigger types: `contact_tag` AND `appointment` (conditions: appointment.eventType/contactMode/appointment.status[/calendar.id], see campaigns/wrinklereset-nurture.py session, wf 1cc13412). Proven beyond the helpers: `remove_from_workflow` step (attributes `{type, workflow_id: [ids]}`). **Schema-copy technique for anything unproven:** GET a live workflow that already uses the step/trigger type (`/workflow/{loc}/list` → find by name → GET workflow / GET trigger?workflowId=) and clone its exact shape — never guess attribute schemas. Campaign-as-code pattern: see `campaigns/example-simple.py`. Tags used in triggers must be created at location level first (internal tags/create returns EMPTY body on success — "Expecting value" JSON error ≠ failure; verify via public GET /locations/{loc}/tags).

**MCP `ghl_workflow_builder_*` tools return "Access denied" (scope missing)** — don't burn time on them; use the engine or the CLI.

## Landing page → GHL tag funnel (the "atlas" pattern)

Proven build (see `atlas-landing/`): static page + Vercel serverless fn, no GHL form needed.

1. `<project>/public/index.html` — page with name+phone form, TCPA consent microcopy, on success redirect to the next funnel step (e.g. `tvaa.doctorleadflow.com/botoxoffer`).
2. `<project>/api/submit.js` — validates, then GHL `POST /contacts/upsert` with `tags:[...]` + explicit `POST /contacts/{id}/tags` (upsert alone can drop tags on existing contacts). Env: `GHL_PIT_TOKEN`, `GHL_LOCATION_ID`.
3. `vercel.json` rewrites: `/api/(.*)` → fn, `/(.*)` → `/public/index.html`.
4. TVAAI brand: bg #FCFAF4, badge #FDF3DC/#EADFC9, gold #C9A44A/#8A6D2A, text #2A211A/#6E6155, CTA green #34C759, system font stack.

### Vercel deploy gotchas
- Shell cwd RESETS between Bash calls — prefix EVERY vercel command with `cd <project-dir> &&`, else you link/deploy the repo root (uploads secrets!) or create rogue projects. THIS HAS HAPPENED — a bare `vercel deploy` from repo root auto-created a rogue `ghl-superspeed-v3` project. Verify the deployment name in the output matches the intended project every time.
- Rogue-project cleanup: `printf 'y\n' | vercel project rm <name>` (no `--yes` flag; `yes |` floods output with a redraw loop).
- Static files in `public/` are served at ROOT paths (`/styles.css`, `/areas/x.png`) — never reference them as `/public/...`.
- `vercel env add NAME production < file` per env (production/preview/development); pull token from ghl config via python, never echo it.
- The live URL is an **alias** from `vercel inspect <deployment-url>`, NOT `<project>.vercel.app` (that name may belong to someone else — atlas-landing.vercel.app is a squatter).
- After deploy: `vercel project ls` to confirm no rogue project.

### Verify end-to-end (always)
```bash
curl -s -X POST <alias>/api/submit -H "Content-Type: application/json" -d '{"firstName":"ClaudeTest","phone":"(832) 555-0142"}'
ghl raw POST /contacts/search --data '{"locationId":"<LOC>","query":"ClaudeTest","pageLimit":5}'   # check tags[]
ghl raw DELETE /contacts/<testId>
```
Watch for tags added by pre-existing automations (e.g. TVAAI adds `ai off` on new contacts) — flag conflicts with the AI-setter routing.
