---
type: offer
client: ritucci
name: "Free Consultation — Non-Surgical Joint Pain Relief"
offer_type: "Free Consult / Lead Gen"
funnel_type: "Lead Form"
status: draft
price: 0
price_model: "free"
deposit_required: false
deposit_amount: 0
no_show_fee: 0
no_show_fee_in_copy: false
has_deadline: false
deadline_date: ""
specialty: "Regenerative / Longevity"
age_range: "40-70"
gender: ["All"]
income_level: ""
geographic_radius: "30 miles Norwood MA (Greater Boston)"
consult_handler: "{{custom_values.text_message_name}}"
consult_handler_resolved: "Steven Ritucci Jr."
consult_length_minutes: 30
booking_link: "{{custom_values.booking_link}}"
booking_link_resolved: "TBD (Notion empty; likely calendly.com/stevenadelejanna/30min — verify)"
custom_values_used:
  - "{{custom_values.booking_link}}"
  - "{{custom_values.text_message_name}}"
custom_value_ids:
  booking_link: "TBD — pull from GHL location gasmmKGJL9bP7ruM49bh"
  text_message_name: "TBD — pull from GHL location gasmmKGJL9bP7ruM49bh"
images_available: false
doctor_video: "Yes"
testimonials_available: true
uses_bot: false
payment_options: []
monthly_budget: 1500
target_cpl: 25
target_cost_per_booked_call: 75
top_3_objections:
  - "Will this work?"
  - "Is it covered by insurance?"
  - "How is it different from cortisone shots?"
biggest_pain_point: "Chronic knee, hip, shoulder, or back pain — told surgery is the only option"
desired_outcome: "Eliminate or significantly reduce pain without surgery"
why_yes: "Nothing to lose — free consult with a real specialist who only does non-surgical care"
buying_triggers:
  - "Non-invasive"
  - "Board-certified MD"
  - "Proven regenerative track record"
differentiators: "Board-certified MD dedicated 100% to regenerative medicine — not a side offering"
bonuses: ""
risk_reversal: ""
guarantee: ""
keyword: "CONSULT"
asset_folder_link: "https://drive.google.com/drive/folders/1fREPrZ5_xLmcijfd3yV4_"
notion_url: "https://www.notion.so/34f728795ff081058d2cd23fff7d2184"
notion_offer_id: "34f728795ff081058d2cd23fff7d2184"
notion_last_updated: "2026-04-27T21:12:00.000Z"
last_updated: 2026-05-06
---

# Free Consultation — Non-Surgical Joint Pain Relief

**Client:** [[clients/ritucci/overview|Ritucci Regenerative Medicine]] · **Status:** Draft · **Type:** Free Consult / Lead Gen · **Price:** Free
**Notion:** https://www.notion.so/34f728795ff081058d2cd23fff7d2184

## Core Promise

Find out if you qualify for non-surgical pain relief — no surgery, no long-term medication.

## What's Included

- 30-min physician consultation with `{{custom_values.text_message_name}}`
- Imaging / history review on the call
- Candidacy assessment for the regenerative protocol
- Honest "yes / no" on whether you're a fit before any procedure conversation

## Top 3 Objections

1. Will this work?
2. Is it covered by insurance?
3. How is it different from cortisone shots?

## Bonuses / Risk Reversal

*(None set in Notion. Standard implicit risk reversal: it's free, you can hang up if you don't like it.)*

## Compliance Notes (Regenerative / orthobiologic mode)

- Same rules as the Ultra Regenerative Package: no "cures / heals / regrows / reverses"; candidacy-gated language; PRP / BMAC / A2M are minimally manipulated autologous biologics, not FDA-approved as drug therapies for these uses
- This is a **free consult** — no deposit, no no-show fee, no card on file. Don't borrow the Ultra offer's $100 no-show language here.
- Photos: none (`images_available: false`)
- Doctor video: **Yes** (per Notion — VSL + 3 video ads in the Drive folder; can use video drop-ins in this sequence, unlike the Ultra package which is still photo/video-blocked)
- Real testimonials only

## Sequence Variables (for /build-sequence)

- **OFFER_NAME:** Free Consultation — Non-Surgical Joint Pain Relief
- **TREATMENT_TYPE:** Free 30-min physician consult to determine candidacy for non-surgical regenerative joint-pain relief. Imaging / history review on the call, board-certified MD (`{{custom_values.text_message_name}}`) — not a salesperson. The free consult is the front door to the Ultra Regenerative Package or a single-procedure path, depending on what the eval finds.
- **TOP_3_OBJECTIONS:**
  1. Will this work?
  2. Is it covered by insurance?
  3. How is it different from cortisone shots?
- **WHAT_IT_DOESNT_DO:**
  - Not a treatment — it's a candidacy review
  - Not a guarantee of candidacy; about 1 in 4 callers find out they're not a fit
  - Not a same-day procedure
  - Insurance does not cover the protocols this gates into
- **HONEST_FLAW:** It's 30 minutes — not enough time to fully diagnose anything in person. We do imaging review and history on the call so we can tell you whether the protocol is even worth booking. About 1 in 4 callers find out they're not a candidate. Better to know now than $1,700 in.
- **QUICK_WIN_TIPS:**
  1. Have your imaging (X-ray / MRI) ready — even a phone photo of the report helps
  2. Write down what's gotten worse in the last 90 days vs. baseline
  3. List what you've already tried (PT, cortisone, NSAIDs, other clinics) and how long it gave you relief
  4. Block the full 30 min — questions matter more than the imaging
- **DEADLINE_MATH:** *No deadline (`Has Deadline=No`).* → Skip Day 5 loss-framed deadline email; sequence = 27 touchpoints.
- **KEYWORD:** CONSULT *(intentionally different from Ultra's `MOVE` so the global reply-handler can route by funnel: CONSULT → free-consult nurture, MOVE → Ultra package nurture.)*

## Booking Mechanics (internal)

- **Free** — no deposit, no card on file, no no-show fee
- **Funnel type:** Lead Form (per Notion)
- **Consult length:** 30 min · **Handler:** `{{custom_values.text_message_name}}` (resolved value: Steven Ritucci Jr.)
- **Booking link:** `{{custom_values.booking_link}}` (resolved value: *empty in Notion* — TBD; Ultra offer uses `calendly.com/stevenadelejanna/30min` but the slug name doesn't obviously match "Steven Ritucci Jr." — verify before launch)
- **Custom-value IDs** for both `booking_link` and `text_message_name` still TBD — pull from GHL location `gasmmKGJL9bP7ruM49bh` once the location is set up, then plug them into the workflow tokens
- **Always use the token in copy.** Never hardcode the calendly URL or doctor name in workflows, SMS, or email — both resolve at send time via custom values
- **Asset folder:** https://drive.google.com/drive/folders/1fREPrZ5_xLmcijfd3yV4_ (3 video ads + VSL — usable in the sequence)

## Audience

- Age range: 40–70 (tighter than Ultra's 21–85 — qualified-buyer bracket)
- Gender: All
- Geographic: 30 miles Norwood MA (Greater Boston) — note this offer's radius is tighter than Ultra's 50 mi; per-offer adjustment
- Specialty fit: Regenerative / Longevity

## Economics

- Monthly budget: $1,500
- Target CPL: $25
- Target cost / booked call: $75

## Funnel Position

This is the **front-door lead-gen offer**. Leads come in here, get qualified on the consult, and roll forward into the Ultra Regenerative Package nurture if they're a candidate. The two offers should share the location and contact records but live on different keywords (`CONSULT` vs `MOVE`) so the reply handler can route correctly.

## Linked Services

*(Same TBD service catalog as the Ultra package — eval / imaging review is the only delivery surface here; the protocol-side services live on the Ultra offer.)*

## Linked Campaigns

- (Run `/build-sequence ritucci-free-consult` to generate)
