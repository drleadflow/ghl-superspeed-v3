# Wrinkle Reset — Fallback Nurture Workflow Spec (form leads who never text)

Built 2026-07-09. Companion to the E2E master SOP:
https://app.notion.com/p/398728795ff081619e17d61e9ccca577

**Offer context:** Wrinkle Reset Membership (founding) — $9/unit Allergan Botox, $4/unit Dysport, $9/mo, no contract, 50 founding spots, Houston only. Membership billing starts at first visit; only pre-visit charge is the $29 appointment deposit (credited). The old "$199 special / 7 spots" copy is RETIRED — purge from KB and claim page.

## Piece 1 — Workflow #2 "tag switch" (MODIFY)
- Trigger A (existing): inbound SMS contains `Claiming my`
- Trigger B (ADD): inbound SMS AND contact has tag `wrinklereset-qualify` ← any-reply activation
- **Filter on BOTH triggers: contact does NOT have tag `ai_off`** — `wrinklereset-qualify` is permanent, so without this filter an escalated lead who texts again re-summons the bot
- Actions: +`sophia-live` +`claimed-wrinklereset` +`bridge-lead` + opportunity (FlowBot Pipeline → ENG: Engaged)

## Piece 2 — Workflow #1 "form webhook" (MODIFY)
- Add Tag step: `wrinklereset-qualify`
- Create/Update Contact: map `source` → Contact Source

## Piece 3 — Workflow #3 "Wrinkle Reset — Qualify Nurture (No Text)" (NEW)
Trigger: Contact Tag Added → `wrinklereset-qualify`
Settings: **Stop on Response = ON** · Goal Event = Tag Added `sophia-live` → END workflow · SMS window 9AM–8PM contact TZ · no re-entry
**Every send step: skip if contact has `sophia-live` OR `ai_off`** (covers the form+claim-text race inside the first 5 minutes, and manually muted contacts).

| # | Timing | Day | Step | Copy |
|---|---|---|---|---|
| 1 | +5 min | d0 | SMS | Hey, is this {{contact.first_name}}? It's Sophia with TVAAI — your Wrinkle Reset request just came through and I've got one of the 50 founding spots with your name on it 🙂 Want me to hold it? Just reply "hold my spot" |
| 2 | +4 hrs | d0 | SMS | No pressure {{contact.first_name}} — I just don't want you paying $560 for your next 40 units when it could be $360 here. Same Allergan Botox, $9/unit as a founding member. Reply "hold my spot" and it's yours. |
| 3 | +1 day | d1 | Ringless VM (~20s) | "Hi {{contact.first_name}}, this is Sophia from The Vitality and Aesthetics Institute here in Houston. You checked out our nine-dollar-a-unit Wrinkle Reset membership and I'm holding a founding spot for you. No need to call back — just text us back at this number and I'll get you booked. Talk soon!" |
| 4 | +1 day | d2 | SMS | Quick one {{contact.first_name}} — the founding spots are going to Houston ladies done paying $14/unit at the "luxury" places. Yours is held through this week only. Text me back and I'll lock in your $9/unit before they're gone ✨ |
| 5 | +2 days | d4 | Task | Call {{contact.first_name}} {{contact.phone}} — WR form lead, never texted in. Opened with $9/unit founding offer. Reached & interested → have them text "claiming my spot", or book directly + manual tags. **AFTER THE CALL: add tag `sophia-live` (interested/booked) or `not_interested` — either one removes them from this nurture. Do not skip this.** |
| 6 | +3 days | d7 | SMS | Hey {{contact.first_name}} — still want the $9/unit founding spot? I don't want to keep blowing up your phone, so just reply "yes please" or "no thanks" and I'll take care of it either way 🙂 |
| 7 | +1 day | d8 | Tag | ADD `Nurture \| Exhausted \| WR Founding`. Do NOT remove `wrinklereset-qualify` (it powers any-reply activation forever). End. |

## Reply suppression — layered defense (a replier must NEVER get another nurture text)

Any single layer failing is survivable; each catches a different bypass:

| Layer | Mechanism | Catches |
|---|---|---|
| 0 | **Stop on Response** (Workflow #3 setting) | ANY reply — works even if Workflow #2 is unpublished/broken. The tag-independent backstop. |
| 1 | Goal Event `sophia-live` → end | Normal path: reply → Trigger B → tag → exit (even mid-wait) |
| 2 | Per-step skip-if `sophia-live` / `ai_off` | Send-vs-reply race in the same minute; manually muted contacts |
| 3 | **Appointment exit** — companion workflow: Appointment Booked (calendar HkwVKBTfqoj2bdyPqtC5) → Remove From Workflow #3 | Leads who convert by PHONE or book on book.tvaai.com — they never send an SMS, so layers 0–2 all miss them |
| 4 | Call-task outcome tagging (step 5 copy) | Day-4 human-call conversions |
| 5 | **Weekly leak audit**: any contact tagged `Nurture \| Exhausted \| WR Founding` that HAS inbound messages = a layer failed. Expected count: zero. | Silent breakage of any layer above |

GHL DND (STOP replies) suppresses sends natively — no extra handling needed.

## Reply flow
Any reply → Trigger B → `sophia-live` → goal event ends nurture → Sophia handles.
- Phrase asks ("hold my spot", "yes please") mitigate the CloseBot single-word first-message bug (~4%); bug self-recovers on the lead's second message.
- "no thanks" (invited by SMS #6) still trips Trigger B — Sophia's `not_interested` scenario catches it and closes gracefully; keywords widened to include polite declines. If Engaged-opportunity pollution from opt-outs becomes noticeable, add a Trigger B negative-phrase filter.
- SMS number = the number Sophia monitors (+1 832 230-2418) — NOT the clinic line (832 962-4455) shown on the landing page.

## Tag SOP registrations required (done in Tag SOP v2, 2026-07-09)
- `wrinklereset-qualify` — Lead Source class; form submitted, not yet texted; **permanent** (powers any-reply activation)
- `Nurture | Exhausted | WR Founding` — human-workflow class; nurture completed without a reply

## Verification after build
1. Submit the live form with a test contact → confirm `wrinklereset-qualify` + nurture enrollment
2. Wait for SMS #1 → reply "hold my spot" → confirm `sophia-live` added, nurture ENDED (goal event), Sophia responds **with founding-membership terms (not $199)**
3. Reply "no thanks" from a third test contact → confirm `not_interested` fires + graceful close, no further nurture
4. Second test contact: no reply → confirm SMS #2 timing + quiet-hours behavior
5. Escalation guard: add `ai_off` to a test contact with `wrinklereset-qualify`, text in → confirm Trigger B does NOT fire
6. **Stop-on-response backstop:** UNPUBLISH Workflow #2 temporarily, reply from a nurture-enrolled test contact → confirm the nurture still stops (layer 0). Republish Workflow #2.
7. **Phone-booking exit:** book a test appointment on the calendar for an enrolled contact (no SMS) → confirm removal from Workflow #3 (layer 3)
8. Delete test contacts
