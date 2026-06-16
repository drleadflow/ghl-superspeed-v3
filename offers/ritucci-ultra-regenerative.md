---
type: offer
client: ritucci
name: "Ultra Regenerative Package"
offer_type: "High-Ticket Package"
status: draft
price: null
price_model: "consult-determined"
deposit_required: false
deposit_amount: 0
no_show_fee: 100
no_show_fee_in_copy: false
has_deadline: false
deadline_date: ""
specialty: "Regenerative / Longevity"
age_range: "21–85"
gender: ["All"]
income_level: "$100-200K"
geographic_radius: "50 miles of clinic"
consult_handler: "{{custom_values.text_message_name}} or team member"
consult_handler_resolved: "Dr. Ritucci or team member"
consult_length_minutes: 15
booking_link: "{{custom_values.booking_link}}"
booking_link_resolved: "https://calendly.com/stevenadelejanna/30min"
custom_values_used:
  - "{{custom_values.booking_link}}"
  - "{{custom_values.text_message_name}}"
custom_value_ids:
  booking_link: "TBD — pull from GHL location gasmmKGJL9bP7ruM49bh"
  text_message_name: "TBD — pull from GHL location gasmmKGJL9bP7ruM49bh"
images_available: false
doctor_video: "Need to film"
testimonials_available: true
uses_bot: true
payment_options: ["Pay in full", "Payment plan", "Financing"]
monthly_budget: null
target_cpl: null
target_cost_per_booked_call: null
top_3_objections:
  - "It's expensive — I'm not sure it's worth it"
  - "What if it doesn't work for me?"
  - "I need time to think or discuss with my spouse"
biggest_pain_point: "Chronic joint pain that limits walking, stairs, and exercise — with the fear that surgery is the only option left after PT, cortisone, and medications gave only temporary or zero relief"
desired_outcome: "Get back to normal pain-free movement — walk, exercise, and stay active without surgery or repeated short-term treatments"
why_yes: "I want to avoid surgery if possible and finally fix this the right way — even if it costs more upfront"
buying_triggers:
  - "Told surgery may be the next step and want to avoid it"
  - "Pain is now interfering with daily life — sleep, walking, exercise"
  - "Previous treatments failed or only gave short-term relief"
differentiators: "Structured multi-phase regenerative protocol (not single-injection), customized per patient, ultrasound-guided by a double-board-certified physician, layering PRP + bone marrow concentrate + A2M + targeted shockwave for long-term outcomes"
bonuses: |
  - Priority scheduling (skip the waitlist)
  - Personalized recovery and activity plan to maximize results
  - Direct access to the clinical team for post-procedure questions
risk_reversal: "Every patient is evaluated for candidacy. If this approach isn't right for you, we'll tell you and discuss better alternatives before moving forward."
guarantee: "Plan adjusts based on response — if you're not progressing as expected, we re-tune the protocol or discuss alternatives so you're never stuck wasting time or money."
limited_availability_angle: "Limited regenerative cases per month due to procedure time and precision; most patients booked 2–4 weeks out, candidacy-dependent"
keyword: "MOVE"
notion_url: "https://www.notion.so/355728795ff081139b6ce2479ac60b1d"
notion_offer_id: "355728795ff081139b6ce2479ac60b1d"
notion_last_updated: "2026-05-03T15:39:00.000Z"
last_updated: 2026-05-06
---

# Ultra Regenerative Package

**Client:** [[clients/ritucci/overview|Ritucci Regenerative Medicine]] · **Status:** Draft · **Type:** High-Ticket Package · **Price:** Determined at consultation
**Notion:** https://www.notion.so/355728795ff081139b6ce2479ac60b1d

## Core Promise

Avoid surgery and get back to pain-free movement in 8–12 weeks using a personalized multi-therapy regenerative protocol — PRP, bone marrow concentrate, A2M, and targeted shockwave.

## What's Included

- Comprehensive evaluation plus ultrasound-guided diagnosis if indicated
- Multi-phase regenerative protocol (PRP, A2M, bone marrow concentrate)
- Targeted focused shockwave pre-treatment before every procedure
- All procedures performed under image guidance for precision
- Personalized treatment plan based on your specific joint and severity
- Follow-up visits to monitor progress and optimize results
- Access to financing options if needed

## Top 3 Objections

1. It's expensive — I'm not sure it's worth it
2. What if it doesn't work for me?
3. I need time to think or discuss with my spouse

## Bonuses / Risk Reversal

- **Bonuses:**
  - Priority scheduling (skip the waitlist)
  - Personalized recovery and activity plan
  - Direct access to the clinical team for post-procedure questions
- **Risk reversal:** Full candidacy evaluation; if this isn't right for you, we tell you up front and discuss alternatives.
- **Guarantee:** Plan re-tunes based on response — no one stays stuck on a protocol that isn't working.

## Compliance Notes (Regenerative / orthobiologic mode)

- No "cures / heals / regrows / reverses" claims — frame as "supports regeneration", "may help reduce pain", "designed to improve function"
- Candidacy-gated language: "if you're a candidate", "depending on evaluation" — never universal promises
- PRP / BMAC / A2M are minimally manipulated autologous biologics — not FDA-approved as drug therapies for these uses; do not imply otherwise
- No before/after photos until filmed (`images_available: false`)
- No doctor video until filmed (`doctor_video: Need to film`)
- Real testimonials only; composite/example patients must be unnamed
- **Internal-only:** $100 no-show fee on card-on-file. Do NOT surface in ad copy, SMS, or email body. Reserved for booking-confirmation flow only if the client decides to disclose.

## Sequence Variables (for /build-sequence)

- **OFFER_NAME:** Ultra Regenerative Package
- **TREATMENT_TYPE:** Multi-phase regenerative protocol for chronic joint pain — PRP, A2M, bone marrow concentrate, and targeted shockwave, ultrasound-guided by a double-board-certified physician. 8–12 week timeline. Surgery alternative for candidates told their next step is surgical.
- **TOP_3_OBJECTIONS:**
  1. It's expensive — I'm not sure it's worth it
  2. What if it doesn't work for me?
  3. I need time to think or discuss with my spouse
- **WHAT_IT_DOESNT_DO:**
  - Not a one-shot fix — outcomes come from the multi-phase protocol, not a single injection
  - Won't regrow severe end-stage cartilage; severe candidates are redirected at evaluation
  - Not insurance-covered (pay in full / payment plan / financing)
- **HONEST_FLAW:** Bone marrow aspiration is harvested from your hip with local anesthesia. The aspiration itself is brief, but you'll feel pressure, and the site is sore for 2–3 days. Most patients are back to desk work the next day, but you're not running stairs that weekend.
- **QUICK_WIN_TIPS:**
  1. Bring imaging (X-ray / MRI) if you have it — speeds up candidacy review
  2. Hydrate well the 48 hours before — better blood draw, better PRP yield
  3. Skip NSAIDs (ibuprofen, Aleve) for 7 days before; they blunt the regenerative response
  4. Plan a 2–3 day light schedule after the procedure
- **DEADLINE_MATH:** *No deadline on this offer (`Has Deadline=No`).* → Skip Day 5 loss-framed deadline email. Generated sequence will be 27 touchpoints.
- **KEYWORD:** MOVE

## Pricing & Booking Mechanics (internal)

- **No published price** — pricing always determined at consultation; never quote a number in ads, SMS, or email
- **No deposit required** — card on file only at booking
- **No-show fee:** $100 (card on file). Internal policy. Do not include in any prospect-facing copy.
- **Payment options at consult:** Pay in full · Payment plan · Financing
- **Consult length:** 15 min · **Handler:** `{{custom_values.text_message_name}}` or team member (resolved value: Dr. Ritucci)
- **Booking link:** `{{custom_values.booking_link}}` (resolved value: `https://calendly.com/stevenadelejanna/30min`; custom-value ID still TBD — pull from GHL location `gasmmKGJL9bP7ruM49bh`)
- **Always use the token in copy.** Never hardcode the literal calendly URL or the doctor's name in workflows, SMS, or email — both resolve at send time via custom values.

## Audience

- Age range: 21–85 (qualified bracket: chronic joint pain w/ failed prior treatment)
- Income: $100–200K
- Gender: All
- Geographic: 50-mile radius of clinic
- Specialty fit: Regenerative / Longevity
- What they've tried: DIY/OTC, other clinics, medications

## Competitor Landscape

Many clinics offer single-injection PRP at $1,700–$2,500 per session — one-off, no structured plan, often inconsistent results, and don't combine shockwave on top. Ultra Regenerative Package is positioned as the structured-protocol alternative.

## Linked Services

*(Service catalog for Ritucci not yet populated. Candidates: PRP injection, A2M injection, bone marrow concentrate / BMAC, focused shockwave, ultrasound-guided evaluation. Promote to `services/` once a service is reusable across clients.)*

## Linked Campaigns

- (Run `/build-sequence ritucci-ultra-regenerative` to generate)
