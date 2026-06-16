---
type: offer
client: prestige
name: "The Soft Reset"
offer_type: "Low-Ticket Frontend"
funnel_type: "Facebook Lead Form"
status: draft
price: 450
price_model: "per-unit-with-floor"
price_detail: "Jeuveau $10/unit, 30-unit minimum ($300 floor); offer wraps to $450 including consult + 2-week follow-up + $50 next-treatment credit"
deposit_required: true
deposit_amount: 50
no_show_fee: 0
no_show_fee_in_copy: false
has_deadline: true
deadline_date: ""
deadline_window: "14 days from form submit (per campaign .py — Notion has no hard calendar date)"
specialty: "Med Spa / Aesthetics"
age_range: "35-65"
gender: ["Female", "Male"]
income_level: "$100-200K"
geographic_radius: "Franklin, Brentwood, Nolensville, Thompson Station, Spring Hill, Nashville, Murfreesboro"
consult_handler: "Andrea Pryor NP"
consult_handler_resolved: "Andrea Pryor NP"
consult_length_minutes: 40
booking_link: "{{custom_values.booking_link}}"
booking_link_resolved: "https://aprestige.square.site/"
booking_surface: "Square (not native GHL calendar)"
custom_values_used:
  - "{{custom_values.booking_link}}"
  - "{{custom_values.text_message_name}}"
custom_value_ids:
  booking_link: "TBD — pull from GHL location 9uog1fOUDtxkSr4ZPx1i"
  text_message_name: "TBD — pull from GHL location 9uog1fOUDtxkSr4ZPx1i"
images_available: true
doctor_video: "Yes"
testimonials_available: true
uses_bot: "Not sure (treat as bot-fronted via text_message_name persona)"
payment_options: ["Pay in full", "Financing"]
financing_in_copy: false
monthly_budget: 0
target_cpl: 0
top_3_objections:
  - "Fear of looking frozen, overdone, or unnatural"
  - "Uncertainty about how much they need or what it will actually cost"
  - "Not fully trusting the provider or wanting to be sure they're in experienced hands"
biggest_pain_point: "They feel like they look more tired and aged than they feel. They're noticing lines and changes in their faces, but are hesitant to start Botox because they are afraid of looking frozen, overdone, and unnatural."
desired_outcome: "Look naturally refreshed, well-rested, and confident, while still looking like herself — natural, balanced, and not frozen."
core_promise: "Visibly smooth lines and achieve a refreshed confident look in days while maintaining natural expression"
why_yes: "The offer is designed to make new potential clients feel they're receiving a medically guided, personalized treatment plan — not just a one-time treatment."
buying_triggers:
  - "If you have been thinking about Botox but don't want to look frozen, this is for you."
  - "You're not tired — it's just starting to show on your face."
  - "The difference between natural results and overdone comes down to who you trust."
differentiators: "Personalized, medically guided neurotoxin approach focused on natural, balanced results — never overdone. Every treatment is customized based on facial anatomy, muscle movement, and long-term goals, not just units or trends. Unlike high-volume clinics, we prioritize precision, education, and trust. Patients feel confident and never rushed."
bonuses:
  - "Complimentary aesthetic consult ($150 value)"
  - "Personalized treatment plan for long-term and aging goals"
  - "$50 credit toward next treatment when 2-week follow-up is completed"
risk_reversal: "Treatment includes a follow-up assessment to ensure balanced and natural result."
guarantee: ""
limited_availability_angle: "Only a limited amount of new client appointments available"
similar_competitor_offers: "In Franklin and Brentwood, most med spas (Glow Medical Spa, NakedMD Med Spa Franklin, Bella Vi Spa & Aesthetics) offer Botox / neurotoxin priced per-unit at $11–$15/unit"
what_theyve_tried: ["Other clinics", "DIY/OTC"]
keyword: ""
keyword_model: "none — open reply CTA; replies route through global reply handler"
tag_prefix: "softreset-"
asset_folder_link: "https://drive.google.com/drive/folders/1qK4QF8LgBpMeO3gLfLJtnVBPwaHXOD2h"
notion_url: "https://www.notion.so/352728795ff0810bbd72f857c69c386b"
notion_offer_id: "352728795ff0810bbd72f857c69c386b"
notion_last_updated: "2026-05-04T17:07:18.621Z"
last_updated: 2026-05-08
---

# The Soft Reset

**Client:** [[clients/prestige/overview|A Prestige Aesthetics & Wellness]] · **Status:** Draft · **Type:** Low-Ticket Frontend · **Price:** $450
**Notion:** https://www.notion.so/352728795ff0810bbd72f857c69c386b
**Campaign file:** `campaigns/prestige-soft-reset-nurture.py` (authored 2026-05-05, not yet deployed)

## Core Promise

Visibly smooth lines and achieve a refreshed confident look in days while maintaining natural expression.

## What's Included

- Jeuveau (tox) at **$10/unit, 30-unit minimum** ($300 floor; package totals ~$450 with bonuses included)
- Complimentary aesthetic consult with Andrea Pryor NP (a $150 value) — plan comes before price
- Personalized treatment plan tied to long-term aging goals
- $50 deposit to hold the appointment, applied to the treatment
- 2-week follow-up assessment to fine-tune symmetry
- $50 credit toward next treatment when 2-week follow-up is completed

## Top 3 Objections

1. Fear of looking frozen, overdone, or unnatural
2. Uncertainty about how much they need or what it will actually cost
3. Not fully trusting the provider or wanting to be sure they're in experienced hands

## Bonuses / Risk Reversal

- $150-value complimentary consult
- Personalized treatment plan
- $50 next-treatment credit on follow-up completion
- **Risk reversal:** Treatment includes a follow-up assessment to ensure balanced, natural result

## Compliance Notes (Aesthetics / Neurotoxin mode)

- Approved language: **"softens / smooths / supports a refreshed look / patients often describe a more rested look"**
- Banned: "erases / freezes / removes wrinkles permanently / guarantees / fixes"
- Banned: "100%" anywhere in body copy
- No em dashes anywhere in body copy (workflow names + code/file docstrings only)
- `{{custom_values.text_message_name}}` is the **bot persona, NOT Andrea**. SMS sender must remain a distinct front-desk persona that hands off to Andrea Pryor NP.
- No before/after photos in SMS (text-only). Email + ad creative may use them (`images_available: true`).
- **No financing / Care Credit references in body copy** (even though `Payment Options` includes Financing — that's a back-office option, not a front-line message).
- Real testimonials only.

## Sequence Variables (for /build-sequence)

- **OFFER_NAME:** The Soft Reset
- **TREATMENT_TYPE:** Low-ticket frontend Jeuveau (neurotoxin) offer for women in their late 30s through mid 50s in Franklin TN who have been thinking about Botox but are stuck on the "what if I look frozen" wall. Andrea Pryor NP is the on-site injector. Differentiation = precision and a plan-before-price consult, not unit-pricing competition with the high-volume Franklin/Brentwood clinics.
- **TOP_3_OBJECTIONS:**
  1. Fear of looking frozen, overdone, or unnatural
  2. Uncertainty about how much they need or what it will actually cost
  3. Not fully trusting the provider — wanting to be sure they're in experienced hands
- **WHAT_IT_DOESNT_DO:**
  - Not a permanent fix — Jeuveau wears off
  - Not "more is better" — overdoing it is the failure mode
  - Not a high-volume punch-card practice — Andrea won't quote units before assessing the face
- **HONEST_FLAW:** Results take a few days to set. The 2-week follow-up exists because the first read isn't always perfect — symmetry sometimes needs a small touch-up, and Andrea would rather see you back at 2 weeks than rush a single visit. That's the trade for natural results.
- **QUICK_WIN_TIPS:**
  1. Bring photos of yourself from a few years ago — helps Andrea see the movement pattern she's working with
  2. Note which expressions bother you most (forehead lines when surprised? "11s" between brows? crow's feet?) — units get placed by intent, not coverage
  3. Don't wear makeup that hides the area you want treated — she needs to see the muscle movement
- **DEADLINE_MATH:** *Has Deadline = Yes (per Notion). No hard calendar date.* → Use **clean 14-day window from form submit** for D5 deposit-deadline copy. Sequence = 28 touchpoints (full timeline including D5 deadline email).
- **KEYWORD:** *None.* Campaign uses an open reply CTA in the D14 email and SMS. Inbound replies route through the global reply handler (WF-02) which alerts the front desk via internal email. No keyword trigger to maintain, no per-offer keyword to pick.

## Booking Mechanics (internal)

- **$50 deposit** to hold the appointment, applied to the treatment
- **Funnel type:** Facebook lead form (per campaign .py docstring)
- **Consult length:** 40 min · **Handler:** Andrea Pryor NP
- **Booking link:** `{{custom_values.booking_link}}` (resolves to `https://aprestige.square.site/` — Square, not GHL native calendar)
- **Custom-value IDs** for both `booking_link` and `text_message_name` still TBD — pull from GHL location `9uog1fOUDtxkSr4ZPx1i`
- **Always use the token in copy.** Never hardcode the Square URL or the bot persona name in workflows, SMS, or email — both resolve at send time
- **Asset folder:** https://drive.google.com/drive/folders/1qK4QF8LgBpMeO3gLfLJtnVBPwaHXOD2h (doctor video + before/afters available)

## Audience

- Age range: 35–65
- Gender: Female + Male
- Geographic: Franklin, Brentwood, Nolensville, Thompson Station, Spring Hill, Nashville, Murfreesboro
- Income: $100–200K
- Specialty fit: Aesthetics / first-time-or-shopping neurotoxin

## Economics

- *(Not specified in Notion for this offer — Page 2 GLP-1 has $1500 monthly / $35 CPL but Soft Reset has no figures; ask client before launch)*

## Funnel Position

This is the **low-ticket frontend** for the location — designed to convert hesitant first-timers (and second-timers shopping for a new injector) into Andrea's chair. Once a Soft Reset client completes the 2-week follow-up, the implicit upsell path is into long-term aesthetic services (other neurotoxins, fillers, packages). Currently no defined back-end offer in vault — that's a gap to surface in `clients/prestige/issues.md` if/when one is built.

## Linked Services

- *(TBD — Jeuveau / neurotoxin service entry; aesthetic consult; see `clients/prestige/services.md`)*

## Linked Campaigns

- `campaigns/prestige-soft-reset-nurture.py` — exists 2026-05-05 (full polished copy, not yet deployed). Re-running `/build-sequence prestige-soft-reset` would clobber it; back up first.
