---
type: offer
client: prestige
name: "GLP-1 Weight Loss Consultation — Perimenopausal Women"
offer_type: "Lead-Gen / Candidacy Assessment"
funnel_type: "Lead Form"
status: draft
price: 0
price_model: "consult-determined"
price_detail: "Consultation-based; protocol pricing determined at consult, never quoted in copy"
deposit_required: false
deposit_amount: 0
no_show_fee: 0
no_show_fee_in_copy: false
has_deadline: false
deadline_date: ""
specialty: "Med Spa / Aesthetics (women's health / weight loss vertical)"
age_range: "40-60"
gender: ["Female"]
income_level: "$100-200K"
geographic_radius: "25 miles Franklin TN"
consult_handler: "Andrea Pryor NP"
consult_handler_resolved: "Andrea Pryor NP"
consult_length_minutes: 0
booking_link: "{{custom_values.booking_link}}"
booking_link_resolved: "TBD — empty in Notion; confirm whether GLP-1 shares the Square booking surface (`aprestige.square.site`) or gets its own calendar"
booking_surface: "TBD"
custom_values_used:
  - "{{custom_values.booking_link}}"
  - "{{custom_values.text_message_name}}"
custom_value_ids:
  booking_link: "TBD — pull from GHL location 9uog1fOUDtxkSr4ZPx1i"
  text_message_name: "TBD — pull from GHL location 9uog1fOUDtxkSr4ZPx1i"
images_available: false
doctor_video: "Need to film"
testimonials_available: false
uses_bot: false
payment_options: []
financing_in_copy: false
monthly_budget: 1500
target_cpl: 35
target_cost_per_booked_call: 0
top_3_objections:
  - "Is it safe?"
  - "Will it work at my age?"
  - "What does it cost long-term?"
biggest_pain_point: "Menopause weight gain that won't respond to diet and exercise"
desired_outcome: "Sustainable weight loss while addressing hormonal symptoms"
core_promise: "Lose weight sustainably with physician-supervised GLP-1 therapy — designed for perimenopausal women"
why_yes: "Finally a provider who understands the hormonal complexity of midlife weight gain"
buying_triggers:
  - "Women's health specialization"
  - "GLP-1 plus HRT combined (root cause, not just symptom)"
  - "Personalized care, not a template protocol"
differentiators: "Combines GLP-1 with HRT evaluation — addresses root cause not just symptom. Andrea Pryor NP specializes in perimenopausal weight gain and screens hormonal context, current meds, labs, and history before prescribing anything. Patients won't be talked into a script."
bonuses: ""
risk_reversal: ""
guarantee: ""
limited_availability_angle: ""
similar_competitor_offers: ""
what_theyve_tried: []
keyword: ""
keyword_model: "none — open reply CTA; replies route through global reply handler"
tag_prefix: "glp1peri-"
asset_folder_link: ""
notion_url: "https://www.notion.so/34f728795ff081e3824ed71b084b2128"
notion_offer_id: "34f728795ff081e3824ed71b084b2128"
notion_last_updated: "2026-05-04T19:30:30.936Z"
last_updated: 2026-05-08
---

# GLP-1 Weight Loss Consultation — Perimenopausal Women

**Client:** [[clients/prestige/overview|A Prestige Aesthetics & Wellness]] · **Status:** Draft · **Type:** Lead Form / Candidacy Assessment · **Price:** Consult-determined
**Notion:** https://www.notion.so/34f728795ff081e3824ed71b084b2128
**Campaign file:** `campaigns/prestige-glp1-perimenopausal-nurture.py` (authored 2026-05-05, not yet deployed)
**Foundation phase:** No ads live yet. ~1,200 contacts in the location ready for reactivation (per Notion page body).

## Core Promise

Lose weight sustainably with physician-supervised GLP-1 therapy — designed for perimenopausal women.

## What's Included

- NP consultation with Andrea Pryor (perimenopausal weight gain is her specialty)
- GLP-1 candidacy assessment — honest yes/no on whether GLP-1 is the right call
- Personalized protocol (not one-size-fits-all)
- Hormone evaluation included — because perimenopausal weight gain and hormones are usually connected

## Top 3 Objections

1. Is it safe?
2. Will it work at my age?
3. What does it cost long-term?

## Bonuses / Risk Reversal

*(None set in Notion. Implicit risk reversal: Andrea reviews full medical history, current meds, labs, and hormone picture before prescribing anything. If GLP-1 is not a fit, she tells you and you don't get a script.)*

## Compliance Notes (GLP-1 / weight-loss mode)

- Approved language: **"supports / helps with / patients often describe"**
- Banned: "treats / cures / fixes" anywhere in body copy
- **Acknowledge perimenopausal hormonal context — never just weight.** This is the entire differentiator; copy that frames it as "weight loss" without the hormonal frame loses the audience.
- No em dashes anywhere in body copy
- `{{custom_values.text_message_name}}` is the **bot persona, NOT Andrea**. SMS sender must remain a distinct front-desk persona that hands off to Andrea Pryor NP.
- **No before/after photos** at any point (`images_available: false`) — no photo MMS, no email image proof
- **No doctor-video drop-ins** until filmed (`doctor_video: Need to film`) — the campaign cannot rely on a VSL or ad-style video module yet
- No financing / Care Credit references in body copy
- Real testimonials only — and currently `testimonials_available: false`, so no testimonial quotes until provided by the client

## Sequence Variables (for /build-sequence)

- **OFFER_NAME:** GLP-1 Weight Loss Consultation — Perimenopausal Women
- **TREATMENT_TYPE:** NP-led GLP-1 candidacy + hormone evaluation for women 40–60 in perimenopause/menopause whose weight gain has stopped responding to diet and exercise. Andrea Pryor NP screens current meds, labs, hormone picture, and full history before prescribing. Honest no-script-if-it's-not-a-fit policy is a major buying trigger.
- **TOP_3_OBJECTIONS:**
  1. Is it safe?
  2. Will it work at my age?
  3. What does it cost long-term?
- **WHAT_IT_DOESNT_DO:**
  - Not a guarantee of a script — about a meaningful share of consults end with "you're not a candidate today"
  - Not a same-day prescription — labs and hormone review come first
  - Not a weight-only program — hormone evaluation is the integrated half
  - Not insurance-covered (most GLP-1 weight-loss use cases are not covered; assume out-of-pocket)
- **HONEST_FLAW:** GLP-1 is not a forever fix. Maintenance matters. Andrea is candid that the long-term cost question (objection #3) is the most important one to think about before booking — the consult helps you see whether the math works for you, not whether you "qualify."
- **QUICK_WIN_TIPS:**
  1. Bring a list of perimenopausal symptoms (sleep, mood, hot flashes, energy, weight) — Andrea uses the symptom picture to decide if hormone eval should happen before, during, or after the GLP-1 conversation
  2. Bring current meds (especially anything for thyroid, HRT, antidepressants, GERD)
  3. Bring recent labs if available — saves a draw and speeds the candidacy call
  4. Be honest about what you've already tried — diet history matters for protocol design
- **DEADLINE_MATH:** *Has Deadline = No (per Notion).* → **Skip Day 5 loss-framed deadline email.** Sequence = 27 touchpoints. Mirror Ritucci Free Consult shape (also `Has Deadline=No`).
- **KEYWORD:** *None.* Campaign uses an open reply CTA in the D14 email and SMS. Inbound replies route through the global reply handler (WF-02) which alerts the front desk via internal email. Front desk reads each reply and responds in-channel — no keyword classification needed.

## Booking Mechanics (internal)

- **No deposit, no card on file** (per Notion `Deposit Required: No`)
- **Funnel type:** Lead Form (per Notion)
- **Consult length:** TBD (not set in Notion — recommend matching Soft Reset's 40 min, or shorter if framed as a candidacy call)
- **Handler:** Andrea Pryor NP
- **Booking link:** `{{custom_values.booking_link}}` — Notion field is empty. Confirm whether GLP-1 shares the Square surface or gets its own calendar before any traffic.
- **Custom-value IDs** for both `booking_link` and `text_message_name` still TBD — pull from GHL location `9uog1fOUDtxkSr4ZPx1i`
- **Asset folder:** *(empty in Notion — no Drive folder linked)*

## Audience

- Age range: 40–60 (tighter than Soft Reset's 35–65 — perimenopausal core)
- Gender: Female only
- Geographic: 25 miles of Franklin TN (tighter than Soft Reset's broader metro spread)
- Income: $100–200K
- Specialty fit: women's health / weight loss / hormonal medicine

## Economics

- Monthly budget: $1,500
- Target CPL: $35
- Target cost / booked call: TBD

## Funnel Position

**Lead-gen / candidacy front door.** Same location as Soft Reset but a parallel funnel — perimenopausal women interested in GLP-1 + hormone work, not aesthetic clients. The implicit upsell path is into a longer-term GLP-1 + HRT program post-consult, but the program structure is not yet defined in vault — surface as a gap in `clients/prestige/issues.md` once the long-term protocol is decided.

Reactivation context: ~1,200 existing contacts in the location are reactivation-ready. The female-only / perimenopausal audience here is a narrower slice of that list than Soft Reset's gender-mixed 35–65 cohort. Expect different reactivation segments per offer; do not blast both campaigns to the full list simultaneously without segmentation.

## Linked Services

- *(TBD — GLP-1 weight-loss program service entry + hormone evaluation service entry; see `clients/prestige/services.md`)*

## Linked Campaigns

- `campaigns/prestige-glp1-perimenopausal-nurture.py` — exists 2026-05-05 (full polished copy, not yet deployed). Re-running `/build-sequence prestige-glp1-perimenopausal` would clobber it; back up first.
