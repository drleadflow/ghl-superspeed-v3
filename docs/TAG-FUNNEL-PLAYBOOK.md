# Tag Funnel Playbook — Repeatable Client Funnel System

The complete, repeatable system for launching a **landing page → tag → SMS → AI setter** funnel
for any GHL client. Built and battle-tested on TVAAI "Wrinkle Reset" (July 2026).

**📊 Visual map (every box clickable → live page/workflow):**
https://healthproceo-diagrams.vercel.app/?diagram=e2e-funnel-system

## The system in one line

Ad → landing page (2-field qualify form) → GHL webhook creates tagged contact → claim page →
**lead texts first** → tag workflow flips the AI setter on → bot books schedule-first/fee-last →
payment link → booked. Non-texters get a nurture; escalations go to humans.

**Why lead-texts-first:** business-initiated SMS lands in Unknown Senders (measured: 38% reply,
9.7h median). Lead-initiated threads live in their real inbox — 87.5% of booked leads replied
vs 28% of non-booked.

## Documentation map (read in this order)

| Doc | What it covers |
|---|---|
| [E2E Master SOP (Notion)](https://app.notion.com/p/398728795ff081619e17d61e9ccca577) | THE source of truth — phases, owners, canonical tag flow |
| [Launch Checklist (Notion)](https://app.notion.com/p/398728795ff08157bf54c8b27423d7c2) | TVAAI current state: what's live, what to adjust/turn off |
| [Page-build SOP (Notion)](https://app.notion.com/p/398728795ff0815488edd40a48dec519) | How the operator pastes pages into GHL + QA |
| `workspace/wrinklereset-fallback-nurture.md` | Nurture spec incl. 6-layer reply-suppression defense |
| `workspace/wrinklereset-launch-adjustments.md` | Detailed adjust/turn-off list with findings |
| [Tag SOP (Notion)](https://app.notion.com/p/397728795ff08127bd49df2e521cbd51) | Every tag, naming rules, kill sequence |
| [CloseBot SOP (Notion)](https://app.notion.com/p/397728795ff08115a0b5c2c9a84e2594) | Building the AI setter (Phase 4) |

## What's in this repo

```
atlas-landing/            The pages (TVAAI reference build)
  public/index.html         Landing page (Vercel-hosted copy)
  public/styles.css/app.js  Styles + calculator/form logic
  public/areas/*.png        Calculator icons  ·  hero-bg.jpg  ·  qr-claim.png
  api/submit.js             Fallback serverless form handler (webhook-first is preferred)
  ghl-paste/landing-page.html   ← single-file paste for GHL (form posts to webhook)
  ghl-paste/claim-page.html     ← single-file paste for GHL (tap-to-text + QR)
campaigns/wrinklereset-nurture.py   Engine builder for the nurture workflow
lib/engine.py             SuperSpeed engine (internal API, see main README)
diagrams/e2e-funnel-system.excalidraw   The system map source
.claude/skills/ghl-ops/   Claude Code skill: CLI gotchas, schema-copy technique, deploy rules
```

Claude Code users also have the user-level `~/.claude/skills/ghl-tag-funnel/` skill —
tell Claude *"use the ghl-tag-funnel skill for [client]"* with the intake inputs and it
builds pages + workflows + verification end-to-end.

## The live TVAAI reference build

| Piece | Link | What it does / why it exists |
|---|---|---|
| Landing page | [tvaa.doctorleadflow.com/wrinklereset](https://tvaa.doctorleadflow.com/wrinklereset) | Converts cold traffic with concrete offer math + 2-field qualify form |
| Claim page | [tvaa.doctorleadflow.com/botoxoffer](https://tvaa.doctorleadflow.com/botoxoffer) | One job: get the lead to hit SEND on the prefilled text (tap-to-text mobile, QR desktop) |
| Vercel project | atlas-landing → [atlas-landing-eight.vercel.app](https://atlas-landing-eight.vercel.app) | Hosts images, QR, fallback API — **must stay up** |
| WF: Inbound Botox Flow | [open](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/c9bbbbfe-41ee-40ad-9b83-00fe941bc645) | Form webhook → creates contact + `wrinklereset-qualify` + source. Why: no secrets in page code; the tag powers nurture + any-reply activation |
| WF: SMS Tag Switch | [open](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/1fa492b1-9b6a-46f8-a0ba-f63a90a48a6e) | Inbound SMS ("Claiming my" OR any reply from qualify lead, never `ai off`) → `sophia-live` + `claimed-wrinklereset` + `bridge-lead` + ENG:Engaged opportunity. Why: THE on/off switch — rollback = unpublish this one workflow |
| WF: Qualify Nurture | [open](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/6e3844d6-5736-4923-9168-8c7b88ccae41) | 6 touches / 7 days for form leads who never text ("is this you?" → math → VM → deadline → call task → takeaway). Why: recovers the majority who drop at the SMS step. Exits: any reply, `sophia-live`, appointment |
| WF: Appt Booked → Exit Nurture | [open](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/1cc13412-a85c-49cc-aa16-8924b089a2b1) | Any appointment (any calendar) removes the lead from the nurture. Why: phone/website bookings never send an SMS — without this, booked patients keep getting texts |
| WF: Medical Flag (PRIORITY) | [open](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/c0f00de0-e098-44e6-9aa9-43a43609d79a) | `medical_flag` → kill sequence (mute bot, notify team email/SMS/Slack, re-arm). Why: the bot never answers medical questions |
| WF: AI OFF handler | [open](https://app.gohighlevel.com/v2/location/jiR5qR3g4OrMRx6BmpF2/automation/workflow/1a59e8a4-53fe-4c41-b614-8bb1e7ae5c19) | Manual-mute handler (was in draft — publish per checklist) |
| Sophia (CloseBot) | bot_P7OFBVD8RPDNK96U | Books schedule-first/fee-last on calendar HkwVKBTfqoj2bdyPqtC5 |

## The canonical tag flow (memorize this)

| Event | Tags applied | By |
|---|---|---|
| Form submit | `wrinklereset-qualify` (permanent) | Inbound Botox Flow |
| Lead texts in / replies | `sophia-live` + `claimed-wrinklereset` + `bridge-lead` | SMS Tag Switch |
| Bot escalates | `medical_flag` / `human_handover` / `ai_booking_error` / `not_interested` → kill sequence adds `ai off` | Sophia → escalation WFs |
| Nurture completes unanswered | `nurture \| exhausted \| wr founding` | Qualify Nurture |

`atlas` = Sophia's TEST tag only. `ai off` (WITH a space — not `ai_off`) = bot muted.

## Cloning this for a new client (< 1 day)

1. **Intake** per the Master SOP Phase 0 (offer math, assets, SMS number, calendar, prefills)
2. **Pages**: Claude + `ghl-tag-funnel` skill → new Vercel project + 2 GHL-paste files
3. **Workflows**: copy `campaigns/wrinklereset-nurture.py`, change location/tags/copy, run it;
   Tag Switch + Appt Exit + Medical Flag were engine-built too — the schema-copy technique in
   `.claude/skills/ghl-ops/SKILL.md` reproduces any of them
4. **Bot**: clone Sophia per the CloseBot SOP (duplicate + fill 6 job-flow variables)
5. **Verify behaviorally** — never trust trigger `active` flags; tag a test contact and watch
   what happens (the engine README + skill document this)
