---
name: ship-nurture
description: >
  End-to-end pipeline to build AND deploy a GHL nurture sequence from a doc.
  Use when the user gives an account name or location ID plus a sequence doc and
  wants it built + deployed with minimal questions. Triggers: "build and deploy
  this sequence for <account>", "ship this nurture to <location>", "set up this
  sequence in the account". Resolves the account, ensures access, analyzes the
  doc, builds the campaign, sets up custom values, deploys, self-heals known
  failures, verifies, and documents — asking only for truly unknowable inputs.
---

# Ship Nurture — account + doc → deployed workflows

Run the whole flow autonomously. Apply the defaults in
`references/build-defaults.md` so you do NOT ask questions that have a known
answer. Only stop for inputs only the user has (booking URL, FB form IDs, an
ambiguous business call). Everything is grounded in the live account.

All scripts run under the `Bash(python3 *)` allow rule (no prompts). Repo:
the GHL-Superspeed-V3-Better-Version project.

## Phase 0 — Resolve account + ensure access
1. **Resolve location ID.** If given a location ID, use it. If given a name,
   check memory `project_client_location_ids` and the `clients/` folder. If still
   unknown, ask once.
2. **Access check:** `python3 scripts/check_access.py <loc>`.
   - exit 0/1 (auth OK) → proceed (a "NOT READY" verdict just means custom
     values are missing — we create those in Phase 5).
   - exit 2 (auth failed) → the refresh-token path is broken for this location.
     Try: confirm `GHL_FIREBASE_REFRESH_TOKEN` is in env; for a non-DLF agency,
     the client's own refresh token must be passed (see memory
     `feedback_non_dlf_agency_deploy_auth`). `ghl-cli` only works for DLF-
     Marketplace sub-accounts. If you cannot get a working token yourself,
     ask the user for the location's Firebase refresh token — that is the ONE
     access thing worth asking about.

## Phase 1 — Ingest + analyze the doc
Read the sequence doc the user gives. Produce a quick analysis (don't belabor):
- List every `{{custom_values.*}}` and `{{contact.*}}` merge field used.
- Catch broken merge fields + body typos (fix them in the build).
- Flag stale/hardcoded dates (today vs any deadline) → route to `offer_deadline`.
- Note the keyword (if any) and check it's free: `python3 scripts/inventory.py <loc> --json` and grep workflow names.
- Compliance scan for the niche (see defaults).

## Phase 2 — Discover (live, read-only)
- **Pipeline + stages:** `python3 scripts/ghl_pipelines.py <loc>` → pick the
  FlowBot pipeline; capture Engagement (new lead) + Connected/Qualification
  (replied) stage IDs.
- **FB lead form (WF-01 entry):** WF-01's standard trigger is the Facebook lead
  form. Get the page/form IDs from the workflow's advanced-canvas trigger UI, or
  ask the user once. If unknown, ship the `<prefix>-lead` tag-trigger fallback
  and note the UI step.
- **Action schemas:** already captured in `references/engine-schemas.md`. If you
  hit an unknown action type, reverse-engineer it:
  `python3 scripts/dump_workflows.py <loc> --out-dir /tmp/dump` then grep the
  JSON for that type.

## Phase 3 — Decide (apply defaults, minimize questions)
Apply `references/build-defaults.md`. Batch any genuinely-unknowable inputs into
ONE question set (typically only: booking_link URL, persona name if not Ashley,
deadline value or leave-empty, FB page/form IDs). Do not re-ask things the doc
or defaults already answer.

## Phase 4 — Build the campaign .py
Model on `campaigns/prestige-metabolic-reset-nurture.py` (canonical template):
- Local step-builders for `internal_create_opportunity`, `assign_user`,
  `internal_notification` (copy from `references/engine-schemas.md`).
- Emails as plain text via `email_step` (bare `[CTA]` line auto-links to
  `booking_link`; one-enter spacing; `- ` bullets). Convert doc CTAs to `[Label]`.
- Standard 4 workflows (see defaults). Use `link_steps([...])` — LINEAR only.
- Pipeline/stage IDs + `ANDREA_USER_ID`-style user id as top constants.
- Parse-check: `python3 -c "import ast; ast.parse(open('campaigns/<f>.py').read())"`.

## Phase 5 — Account setup
Create + populate location custom values:
`python3 scripts/set_custom_values.py <loc> text_message_name=Ashley booking_link=<url> offer_name="<name>"`
(Leave `offer_deadline` per the user's call.)

## Phase 6 — Deploy (with self-heal)
**PREFLIGHT FIRST (cheap insurance):** `python3 scripts/preflight_campaign.py campaigns/<file>.py`.
It must exit 0. This catches the deploy-breakers *statically* — `internal_update_opportunity`
(corrupted-type), `customer_reply` without a workflow filter, em dashes in copy —
BEFORE a bad action type zeroes the whole step batch and leaves you a failed
folder to clean up. One rejected action saves 0 steps across ALL workflows, so
this 1-second check saves a full cleanup + redeploy cycle.

Then `python3 campaigns/<file>.py` (env auto-loads; the file forces
`prefer_refresh_token`).
Then ALWAYS verify (Phase 7). If the deploy reports STEPS FAILED, 0-step
workflows, or missing triggers, FIX and redeploy clean:
1. **Find the failed folder's ID** first: `python3 scripts/inventory.py <loc>` (or
   the deploy output). A failed redeploy leaves a folder with the SAME name as
   any prior build, so delete by ID, not name:
   `python3 scripts/cleanup_deploy.py <loc> --folder-id <id>`.
   `--folder` ABORTS on a duplicate-name match (guard added after it once deleted
   a live v1 folder); `--folder-id` is the safe path.
2. fix the code (see the known failures in `references/engine-schemas.md` —
   esp. update_opportunity→create-upsert, customer_reply needs a workflow filter),
   re-run preflight,
3. re-run the deploy.
Re-running WITHOUT cleanup creates duplicates — never do that.

## Phase 7 — Verify (mandatory)
`python3 scripts/deploy_verify.py <loc> --folder "<folder name>"` → require
`ALL GOOD: True` (every workflow has steps + a LINKED trigger). Don't report
success until this passes.

## Phase 8 — Document + memory
- Write `clients/<client>/<offer>-build-log.md` + `<offer>-setup.md` (deploy
  status, WF IDs, go-live steps).
- Update memory: a `project_<client>_<offer>` file (deployed IDs) and any NEW
  gotcha. Add the index line to `MEMORY.md`.
- List remaining go-live UI steps (FB form tag, email footer, deadline value).

## Gotchas
- **`internal_update_opportunity` is rejected by the save API** — use
  `internal_create_opportunity` at the target stage (it upserts). See schemas.
- **`customer_reply` triggers REQUIRE a workflow filter** (`source_wf_key`);
  keyword-only silently produces NO trigger.
- **Builder wires LINEAR chains only** — no `if_else`/`find_opportunity`/
  `workflow_split` forks. Design linear; defer forks to the UI/v2.
- **Re-deploy duplicates** — always `cleanup_deploy.py` first, and delete by
  `--folder-id` not `--folder` (two folders can share a name; name-match would
  delete the wrong/live one — guard added 2026-06-04 after a real incident).
- **A bad action type zeroes the whole deploy** (atomic step-batch save) — run
  `preflight_campaign.py` before deploying to catch it statically.
- **Auth:** a stale `GHL_FIREBASE_TOKEN` id-token beats the refresh token unless
  `prefer_refresh_token=True`. The deploy file and `_ghl.py` already force it.
- **`validate_campaign` warns** on internal_*_opportunity ("unverified type") —
  benign; those types are real on the account.
- **Custom values are global** — a per-contact rolling deadline can't be one;
  use a per-cohort value or leave to the UI.

## Files
- `references/build-defaults.md` — the decision defaults (persona, triggers,
  workflow structure, compliance) that let this run without back-and-forth.
- `references/engine-schemas.md` — exact action JSON + step-builder snippets +
  the known save-API failures.
- Repo scripts used: `check_access.py`, `inventory.py`, `ghl_pipelines.py`,
  `set_custom_values.py`, `preflight_campaign.py` (PRE-deploy static gate),
  `deploy_verify.py` (POST-deploy gate), `cleanup_deploy.py`,
  `dump_workflows.py`.
