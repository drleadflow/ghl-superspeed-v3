---
type: offer
client: iv-wellness
name: "NAD+ IV Therapy — Anti-Aging & Energy Reset"
offer_type: "IV Therapy"
status: active
price: 399
deposit_required: false
has_deadline: false
deadline_date: ""
specialty: "Regenerative / Longevity"
age_range: "35-60"
gender: ["All"]
income_level: "$100-200K"
geographic_radius: "20 miles Cincinnati OH"
consult_handler: "Alicia Logeman"
booking_link: ""
images_available: false
doctor_video: "Need to film"
uses_bot: false
monthly_budget: 1500
target_cpl: 30
target_cost_per_booked_call: 90
top_3_objections:
  - "Is it safe?"
  - "How is this different from B12 shots?"
  - "Will I really feel the difference?"
biggest_pain_point: "Chronic fatigue, brain fog, feeling older than you are, poor recovery — NAD levels decline 50% by age 50"
desired_outcome: "Lasting energy boost, mental clarity, improved mood and cellular repair — noticeable within 24-48 hours"
why_yes: "NAD+ is the gold standard of anti-aging IV therapy — and it comes to your door with a licensed RN"
buying_triggers:
  - "Longevity/biohacking trend"
  - "No clinic visit needed"
  - "Dramatic energy results"
differentiators: "Mobile service + licensed RN + free add-on push — concierge longevity medicine at home pricing"
bonuses: "Free add-on: B12 or Glutathione push with first NAD+ session"
risk_reversal: "Full wellness assessment before every session — your RN confirms candidacy"
guarantee: ""
keyword: "RESET"
notion_url: "https://www.notion.so/34f728795ff081bb90a3cb80465ab0f5"
notion_offer_id: "34f728795ff081bb90a3cb80465ab0f5"
notion_last_updated: "2026-04-27T21:24:10.964Z"
last_updated: 2026-05-05
---

# NAD+ IV Therapy — Anti-Aging & Energy Reset

**Client:** [[clients/iv-wellness/overview|IV-Wellness]] · **Status:** Live · **Type:** IV Therapy · **Price:** $399
**Notion:** https://www.notion.so/34f728795ff081bb90a3cb80465ab0f5

## Core Promise

Restore cellular energy, sharpen your mind and slow aging at the source — NAD+ delivered straight to your bloodstream at home.

## What's Included

- NAD+ IV infusion (250mg–500mg dose range)
- RN-administered at your home or office
- 90–120 min session
- Pre-session wellness assessment
- **Bonus:** Free B12 or Glutathione push with first session

## Top 3 Objections

1. Is it safe?
2. How is this different from B12 shots?
3. Will I really feel the difference?

## Bonuses / Risk Reversal

- **Bonuses:** Free B12 or Glutathione push with first NAD+ session
- **Risk reversal:** Full wellness assessment before every session — your RN confirms candidacy
- **Guarantee:** *(none stated)*

## Compliance Notes (IV strict mode)

- Use "supports / complements / helps with" — never "cures / treats / fixes"
- No specific health-outcome claims (no "fixes fatigue", no "reverses aging")
- No before/after photos (none exist for IV)
- D0 T+1 SMS is text-only, NOT MMS
- Pratfall flaw must be operational (not clinical)
- See `lib/prompts/iv-adjustments.md` for the full ruleset applied at sequence build time

## Sequence Variables (for /build-sequence)

- **OFFER_NAME:** NAD+ IV Therapy — Anti-Aging & Energy Reset
- **TREATMENT_TYPE:** NAD+ IV infusion (250-500mg) delivered by a licensed RN at your home or office in Cincinnati. 90-120 min session including wellness assessment. Supports cellular energy, mental clarity, and longevity goals.
- **TOP_3_OBJECTIONS:**
  1. Is it safe?
  2. How is this different from B12 shots?
  3. Will I really feel the difference?
- **WHAT_IT_DOESNT_DO:**
  - Won't replace sleep, nutrition, or movement
  - Won't reverse genetic aging — supports the cellular machinery, doesn't rewind biology
  - Single sessions help, but the protocol works best as 3-4 sessions in the first month
- **HONEST_FLAW:** NAD+ at full dose burns. Like, your chest feels warm and your face flushes for the first 20 minutes. We slow the drip way down at the start, but anyone who tells you it's totally comfortable is lying. The rest of the session is fine.
- **QUICK_WIN_TIPS:**
  1. Hydrate hard the day before — 80-100oz water
  2. Eat a real meal 1 hr before, no fasting
  3. Block the full 2 hours, don't try to squeeze it between meetings
  4. Skip caffeine that morning — NAD+ is the energy lift, you don't need to stack
- **DEADLINE_MATH:** *No deadline on this offer (`Has Deadline=No`).* → Skip V2 Day 5 loss-framed deadline email. Generated sequence will be 27 touchpoints, not 28.
- **KEYWORD:** RESET

## Notion Notes

> NAD+ is the #1 IV therapy search term for the 35-60 longevity crowd. Premium, scientific, trending.
> Cincinnati mobile NAD+ market: $350-$600. $399 is aggressive entry pricing that drives volume while maintaining premium perception.
> Free B12 or Glutathione add-on costs Alicia ~$0 in product but gives massive perceived value.

## Audience

- Age range: 35-60
- Income: $100-200K
- Gender: All
- Geographic: 20 miles Cincinnati OH
- Specialty fit: Regenerative / Longevity

## Linked Services

*(IV-Wellness service catalog needs reconciliation against the canonical 14 formulas in Notion — see `clients/iv-wellness/issues.md`. NAD+ specifically corresponds to existing `[[services/nad-250mg]]` and `[[services/nad-500mg]]`.)*

## Linked Campaigns

- (Run `/build-sequence iv-wellness-nad-iv-therapy` to generate)
