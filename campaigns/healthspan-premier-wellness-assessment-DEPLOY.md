# Deploy Runbook — Healthspan By Design · Premier Wellness Assessment (PWA) Nurture

**Status:** DRAFT, NOT DEPLOYED. Files authored + verified 2026-06-01. Copy is compliance-clean (see notes below).
**When you sit down with this, it's a ~5-minute job: clear 3 gates, run one command.**

## What's here

| File | What it is |
|---|---|
| `campaigns/healthspan-premier-wellness-assessment-nurture.py` | The campaign. 2 workflows, 41 steps, 18 contact-facing sends (7 emails + 11 SMS) across 28 days. Parses clean, `main()` aborts on the USER_ID placeholder so it can't deploy half-cocked. |
| `offers/healthspan-premier-wellness-assessment.md` | The offer spec (frontmatter + body + compliance notes + sequence variables). Source of truth for the copy. |

## The offer (one-liner)

$1,500 high-ticket preventive/longevity assessment. 100+ biomarkers + mobile phlebotomy + 60-min consult with **Dr. Joel Wussow MD** + written PWA report. Guarantee: *find ≥3 modifiable risks or the $1,500 is fully refunded.* Fee credited 100% toward Annual Concierge if they enroll within 30 days. Audience: 30–65, $200K+, FL/NY/AZ/TX, Attia/Huberman crowd. Notion: https://www.notion.so/368728795ff08187bd8bdbfb896e4daa

## Target

- **LOCATION_ID:** `EnmtjE3RhgP6s0oIn1GV` (Healthspan By Design LLC sub-account — created via dlf-onboarding 2026-06-01)
- **COMPANY_ID:** `R1HWQKyMMoj4PJ5mAYed` (DLF agency)

---

## Deploy gates — clear all 3, then run

### Gate 1 — Resolve USER_ID
The campaign needs a real user_id from the new location (currently the literal placeholder `TODO_RESOLVE_AT_DEPLOY` on line ~83, which makes `main()` abort).

Pull a user on the location (any of):
- `ghl-cli` (token-light): list users for `EnmtjE3RhgP6s0oIn1GV` and grab an id.
- GHL API with the agency PIT: `GET https://services.leadconnectorhq.com/users/?locationId=EnmtjE3RhgP6s0oIn1GV` (header `Version: 2021-07-28`).
- GHL UI: Settings → My Staff on the sub-account.

Then replace line ~83:
```python
USER_ID = "<the real 20-char user id>"
```

### Gate 2 — Refresh the GHL Firebase token
The v3 engine deploys through GHL's internal Firebase API, not OAuth. The token expires fast.
- Easiest: run the **`ghl-firebase-refresh`** skill (Playwright login to app.gohighlevel.com → extracts the JWT + refresh token).
- Or set `GHL_FIREBASE_REFRESH_TOKEN` in this repo's `.env` (see repo README "Get a Firebase Token"). The runner reads it automatically.

### Gate 3 — Confirm the two custom values exist on the location
The copy uses `{{custom_values.booking_link}}` and `{{custom_values.text_message_name}}`, resolved at send time. Both must exist on `EnmtjE3RhgP6s0oIn1GV` (Settings → Custom Values), or sends go out with empty tokens.
- **`text_message_name`** — the front-desk/concierge persona name (this offer has Uses Bot = No, so it's a patient coordinator who hands off to Dr. Wussow). Pick a name, set the value.
- **`booking_link`** — ⚠️ **NOT SET YET.** No booking link/funnel exists for this offer. Decide the destination (consult booking calendar vs lead-magnet page), create it, then set this custom value. The nurture's CTAs are dead until this is filled.

### Run it
```bash
cd ~/Desktop/GITHUB/GHL-Superspeed-V3-Better-Version
python3 campaigns/healthspan-premier-wellness-assessment-nurture.py
```
Expected: auth OK, then "All 41 steps saved!" Builds a folder "Premier Wellness Assessment" with both workflows.

### Post-deploy (GHL UI, manual — same as every v3 campaign)
1. **WF-01 trigger:** the engine ships a tag trigger `pwa-lead`. Either swap it to a Facebook Form Submission trigger, or set the lead form to add the `pwa-lead` tag on submit.
2. **WF-02 trigger:** set "Customer Replied" filtered to `replied to workflow = 01. PWA — Master Sequence` (needs WF-01's id, captured after deploy).
3. Publish both workflows (engine builds them in draft).
4. Send yourself a test contact through it before going live.

---

## Compliance notes (medical/longevity — already baked into the copy, keep it this way on edits)
- Educational / modality-stating ONLY. Never diagnostic, never symptom-to-diagnosis, never personal-attribute ("as a man with low T…").
- No outcome/cure promises. The ONLY guarantee allowed is the literal refund line, stated verbatim.
- "100%" only in the literal "credited 100% toward…" bonus. No em dashes in body copy.
- Joel's own framing (from Slack 2026-06-01): ApoB/Lp(a) are *supporting* markers inside the cardiovascular pillar, not the headline. 3 pillars = cardiovascular (PREVENT 10/30-yr) · metabolic (LPIR, 8yr early) · hormones (timing-dependent).

## If Joel wants to review first
Send him the 7 email subject lines + bodies from the `.py` (lines ~90–305). Edit copy in the `.py` directly, keep the compliance rules above, re-run `python3 -c "import ast; ast.parse(open('campaigns/healthspan-premier-wellness-assessment-nurture.py').read())"` to confirm it still parses, then deploy.

## Provenance
Offer sourced from Notion (above) + the "Booked & Busy Playbook" Google Doc (belief-shift framework) Emeka sent Joel 2026-06-01. Confirmed in Slack `#healthspanbydesign-dr-joel-wussow` (C0B4QF3D1D1). Notion flag "28 Day Nurture Sequence Built" was NO at authoring time — flip it to YES after deploy.
