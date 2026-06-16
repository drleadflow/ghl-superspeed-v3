# Native Automation Engine — Brainstorm In Progress (PAUSED 2026-05-11)

Status: **paused mid-brainstorm**, pick up with the `superpowers:brainstorming` skill (or `/gsd-resume-work`). Not yet a finished spec — no implementation has started.

## The goal (in the user's words)

> "Onboarding, Native Sites, All APIs. So the MCP turned to a CLI. That is the future but right now here, needs to stay what we have for right now. I want complete native automation capabilities. Have not finished that yet."

So: the long-term vision is consolidating the ~15 scattered GHL repos and turning the `dlf-ghl-mcp-server` into a CLI — **but that is explicitly future, not now**. The near-term work is **finishing the native automation engine** (`lib/engine.py` in this repo — the thing that builds GHL workflows via the internal `backend.leadconnectorhq.com` API) so it can express the full range of GHL automations natively, instead of falling back to the GHL UI.

"Complete" = parity with GHL's workflow builder is the **eventual goal**; the user will provide a priority list of "main items" later. So: build a pragmatic subset first, but design for parity and keep a living checklist.

## What the engine does natively today (as of 2026-05-11)

- **Triggers (3):** `facebook_lead_gen`, `customer_reply` (replied-to-workflow + optional keyword), `contact_tag` (legacy `tag` string still works). Set via `wf_def["trigger"] = {"type": ...}`.
- **Actions (~6):** send SMS, send email, wait (time-based only), `update_contact_field` (needs the per-location custom-field UUID, not the slug), `webhook`, `chatgpt` (Conversation-AI simple-prompt).
- **Structure:** folders, linear ordered step lists, single trigger per workflow. No if/else branches, no goals, no wait-for-event/condition.
- **Location resources:** tag creation; custom values (via `lib/a2p_values.py` — fetch/create/update, needs `version: 2021-07-28` header).
- `engine.py` is **969 lines doing ~8 jobs** (auth, HTTP, email-HTML, step builders, workflow assembly, triggers, folders, deploy) — the "file too large = doing too much" smell.

## Gaps the user flagged as biting most (= Phase-1 priority — all four selected)

1. **If/else branching** inside a workflow.
2. **Opportunity / pipeline actions** — create opportunity, move stage, update status/value, assign owner.
3. **Appointment + form triggers** — appointment booked/confirmed/cancelled/no-show/status-changed; native GHL form/survey submitted.
4. **Tag + workflow + task actions** — add/remove tag, add-to / remove-from another workflow, create task, internal notification (email/SMS to staff), set DnD.

User added: "Honestly a lot needs to be done since I have not gone through quite yet" — i.e. the full gap hasn't been audited. The capability map (below) IS that audit.

## Recommended approach (Approach "A" — tentatively agreed, not finalized)

**Modular registry + capability map + waves:**

- Split `engine.py` into `lib/ghl/`:
  - `client.py` — `TokenManager` + `GHLClient` (auth, HTTP, retry). Pure transport. (Already has the `extra_headers=` hook added 2026-05-11.)
  - `actions/<type>.py` — one small module per action type; each exports a builder fn returning the action JSON; registered in an `ACTIONS` registry.
  - `triggers/<type>.py` — one small module per trigger type; builder + filter/condition schema; registered in `TRIGGERS`.
  - `workflow.py` — assembles a workflow from a declarative spec (trigger(s) + ordered steps, including branches).
  - `deploy.py` — orchestration: create folder, create/update workflows, wire triggers, capture IDs, idempotency.
  - `custom_values.py` / `custom_fields.py` / `tags.py` — location-level resources (move `a2p_values.py` logic under here, or have it import from here).
  - `format.py` — `dm_email()` and the email-HTML helpers.
- **`lib/engine.py` becomes a thin compat shim** re-exporting the public names → existing `campaigns/*.py` keep working untouched ("stays what we have for now").
- **`references/ghl-automation-capabilities.md`** (new) — single source of truth: every GHL trigger + action, with status (built / planned / punted), the real internal-API JSON shape, and quirks. The parity checklist; the user's "main items" list slots into it.
- **Hard rule:** before implementing any action/trigger, capture its **real** JSON shape — GET an existing hand-built workflow that contains it, or sniff the GHL UI with the `watch-browser` skill. Never guess. (Lesson from `update_contact_field needs UUID` and the `version` header 401.)
- **Each action/trigger module** gets a unit test (builder → expected dict) and ideally one integration test deploying a throwaway workflow to a sandbox location and reading it back (extend `tests/live_test_render.py`).
- **Waves:** Phase 1 = the refactor + capability map + the 4 flagged categories. Wave 2+ driven by the user's "main items" list. Each wave = its own spec → plan → implement cycle.

Rejected: **B** (keep appending to `engine.py` — file rots). Deferred: **C** (declarative YAML campaign-spec DSL that compiles to GHL JSON — nice eventually, but needs the action/trigger builders underneath first).

## Open questions (where the brainstorm stopped)

1. **Is the refactor its own phase, or bundled with the Phase-1 capabilities?** (Last question asked; unanswered.)
2. The user's promised priority list of "main items" — needed to plan Wave 2.
3. Shape-discovery logistics: does the user already have GHL location(s) with hand-built workflows containing if/else + opportunity + appointment-trigger examples we can GET and copy, or do we need a sniffing pass first?

## Resume checklist

- Re-invoke `superpowers:brainstorming` (or `/gsd-resume-work`).
- Resolve open question #1, then move to "present design sections" → write the real spec at `docs/superpowers/specs/YYYY-MM-DD-native-automation-engine-phase1-design.md` → `superpowers:writing-plans`.
- Memory pointer: `project_native_automation_engine_brainstorm.md` in this project's memory dir.
