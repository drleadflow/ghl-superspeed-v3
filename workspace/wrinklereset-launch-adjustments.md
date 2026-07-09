# Wrinkle Reset Funnel — Launch Adjustments (turn off / adjust / verify)

2026-07-09 · Companion to the E2E master SOP + `wrinklereset-fallback-nurture.md`.
Everything below reflects what the SuperSpeed engine just built vs. what needs human action in GHL.

## ✅ Built & PUBLISHED this session (folder: Wrinkle Reset Funnel)

| Workflow | Link | State |
|---|---|---|
| SMS Tag Switch (Sophia Activation) — 2 triggers: "Claiming my" + any-reply-from-qualify, both with NOT-`ai off` filter → +sophia-live +claimed-wrinklereset +bridge-lead + opportunity (ENG: Engaged) | [1fa492b1](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/1fa492b1-9b6a-46f8-a0ba-f63a90a48a6e) | **published** |
| Appt Booked → Exit Nurture (any calendar, Requested+Confirmed → remove from nurture) | [1cc13412](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/1cc13412-a85c-49cc-aa16-8924b089a2b1) | **published** |
| 01.04.05: Medical Flag (PRIORITY) — full 6-step kill sequence cloned from Human Handover, re-arms by removing `medical_flag` | [c0f00de0](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/c0f00de0-e098-44e6-9aa9-43a43609d79a) | **published** |
| Qualify Nurture (No Text) — 12 steps | [6e3844d6](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/6e3844d6-5736-4923-9168-8c7b88ccae41) | **DRAFT — do not publish until §2 done** |

Tags created at location level: `wrinklereset-qualify`, `nurture | exhausted | wr founding`, `claimed-wrinklereset`, `bridge-lead`, `medical_flag`, `personal_contact`.

## 1 · REQUIRED adjustments — STATUS UPDATE 2026-07-09 PM (most done via API)

- [x] ~~Inbound Botox Flow tag swap~~ **DONE via API** — now adds `wrinklereset-qualify` and maps `source` → Contact Source.
- [x] ~~Nurture: Stop on Response~~ **DONE via API** (`stopOnResponse: true`)
- [x] ~~Nurture: day-4 call task step~~ **DONE via API** (13 steps now, incl. task with the after-call tagging instruction)
- [x] ~~Nurture publish~~ **DONE via API** — published
- [x] **medical_flag trigger verified FIRING** behaviorally (test contact tagged → kill sequence added `ai off`). Note: trigger `active:false` in the API is meaningless — live production triggers read the same. Behavioral test is the only truth.
- [ ] **Nurture — remaining UI-only items (before real traffic, not blocking tests):**
  - Goal Event: Tag Added `sophia-live` → End this workflow (no `workflow_goal` example exists in the account to schema-copy — UI only)
  - Ringless-VM step after the first "Wait 1 Days" (needs recorded audio)
  - SMS send window 9:00 AM–8:00 PM (evening form fills currently get SMS #1 at night)
  - Per-SMS-step skip-if `sophia-live`/`ai off` conditions
- [ ] **Medical Flag notifications rewording** (cloned Human Handover copy → 🚨 MEDICAL PRIORITY) — still open
- [ ] ⚠️ **New finding:** the cloned kill sequence (and its Human Handover source) does NOT contain the "remove all activation tags" step the Tag SOP documents as step 2 — `sophia-live` stayed on the escalated test contact. The bot filter's NOT-`ai off` still silences the bot, so it's safe, but the Tag SOP and reality disagree. Either add remove-tag steps to both workflows or amend the Tag SOP.
- [ ] **Medical Flag workflow — reword notifications** ([c0f00de0](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/c0f00de0-e098-44e6-9aa9-43a43609d79a)): steps were cloned from Human Handover — edit the two Internal Notification steps + Slack message to say **"🚨 MEDICAL PRIORITY"** and confirm recipients/channel are right.

## 2 · TURN OFF / keep off (double-messaging & conflict risks)

- [ ] **Parallel "Wrinkle Reset Membership v3" suite** — Master Sequence ([f19e6216](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/f19e6216-1c3f-4efe-935e-1a2b1d1fc04d), facebook_lead_gen trigger), Reply Handler (de7cb4fa), WRINKLE Keyword Recapture (de3890a5), Global Reply Handler (178109e2), RESET Keyword Recovery (5e1ce085). All triggers currently INACTIVE — **keep them off**. Two systems now target this offer; this funnel (tag switch + nurture + Sophia) is the owner. If the v3 suite ever goes live alongside it, leads get double-messaged.
- [ ] **"6. AI Off → Notify Client" ×3 duplicates** — all inactive; delete or archive to stop future confusion.
- [ ] **Duplicate "01.04.04: Human Handover"** (bb2c8f81, inactive) — 01.04.03 is the live one; archive the duplicate.
- [ ] **Meta "Campaign 2"** ($186/wk, zero leads — from the July 8 handoff) — pause if still running.

## 3 · TURN ON / publish (escalation rail gaps)

- [ ] **01.04.01++. TAG ADDED "AI OFF"** ([1a59e8a4](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/1a59e8a4-53fe-4c41-b614-8bb1e7ae5c19)) — the manual-mute handler is in DRAFT with inactive trigger. Publish it (it removes Flowbot assignment etc. when someone manually tags `ai off`).
- Escalation rail status (verified via trigger scan): `not_interested` ✅ active · `human_handover` ✅ active (01.04.03) · `ai_booking_error` ✅ active · `ai_aggression` ✅ active · `medical_flag` ✅ NOW built+published · `personal_contact` — ❌ no workflow found; per Tag SOP it's notify-only, build a simple notify workflow or accept silent tagging.

## 4 · Standardize & audit

- [ ] **Mute-tag spelling:** the LIVE system uses **`ai off` (with a space)** — CloseBot-era filters and this session's NOT-filters all check `ai off`. The Tag SOP documents `ai_off` (underscore) and both tags exist in the location. Standardize on `ai off`, update the Tag SOP, and audit any workflow referencing `ai_off`. (The kill-sequence step named "AI Off | AI_OFF" appears to add both — leave until audited.)
- [ ] **Sophia (CloseBot):** update KB + claim fast-path to the $9/unit founding-membership terms (KB still knows $199) · confirm source filter = has `sophia-live` AND NOT `ai off`, SMS channel · quiet hours SMS+Email only 9PM–7AM.
- [ ] **`ai off` auto-stamper — narrowed down:** confirmed live (fresh API-created test contact got `ai off` within minutes, 2026-07-09 PM). NOT a GHL workflow — all contact_created workflows checked, none add it. Most likely the EXTERNAL "TVAAI Platform" (fed by the published "TVAAI Platform - Lead Webhook" custom_webhook on contact_created) tags `ai off` back via API on lead ingest. Ask whoever runs that platform to exclude funnel leads (or stop stamping entirely per the Tag SOP rule). Until fixed: any API-imported contact arrives muted.

## 5 · Verification pass (after §1 done — ask Claude to run it)

1. Live form submit → contact + `wrinklereset-qualify` + nurture enrolled (after publish)
2. Reply "hold my spot" → sophia-live + claimed-wrinklereset + bridge-lead + ENG:Engaged opportunity + nurture ENDED + Sophia responds with $9/unit terms
3. Text "Hi TVAAI! Claiming my $9/unit Wrinkle Reset founding membership" from a fresh contact (no form) → same activation (Trigger A path)
4. `ai off` guard: tag a test contact `ai off`, text in → NO activation
5. Book a test appointment for an enrolled contact → removed from nurture (WF#4)
6. Unpublish Tag Switch temporarily, reply from enrolled contact → nurture still stops (Stop on Response)
7. Tag a test contact `medical_flag` → kill sequence runs, notifications arrive, tag removed at end
8. Delete all test contacts
