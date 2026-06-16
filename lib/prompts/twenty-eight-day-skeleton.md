# 28-Day Nurture Sequence — Orchestration Skeleton

> Source of truth for the structural wrap that turns Master Copy Prompt output into a deployable GHL campaign.
> Used by `/build-sequence`. Modeled on the DPN system (Amazing Skin Care, v3.1).

## Three artifacts produced per offer

1. **`campaigns/<client>-<offer>-nurture.py`** — engine-deployable. Contains automated workflows only (SMS, email, wait, tag steps). All manual steps are excluded (front desk calls, voicemail drops can't be automated).
2. **`clients/<client>/<offer>-manual-touchpoints.md`** — front desk runbook. Manual calls, voicemail script, Hail Mary SMS template. Printed and used by ops.
3. **`clients/<client>/<offer>-ai-bot-prompt.md`** — paste into GHL Conversation AI. The 7-branch setter system tied to specific automated SMS triggers.
4. **`clients/<client>/<offer>-sequence-qa.md`** — QA report from the gate, surface any flags before deploy.

## Touchpoint Timeline (every day, every channel, every owner)

The DPN reference deployed 30 distinct touchpoints across 28 days. Same skeleton for any offer; per-offer adjustments live in `iv-adjustments.md` (or future `<niche>-adjustments.md`).

### Day 0 — Form submit through first hour

| Time | Channel | Owner | Goes Where |
|------|---------|-------|------------|
| T+0 sec | SMS confirmation | CRM auto | `.py` |
| T+1 min | SMS or MMS qualifying question | CRM auto | `.py` (no MMS for IV — text only) |
| T+2 min | Internal alert if no reply | CRM auto | `.py` |
| T+5 min | Double-dial call | Front desk | `manual-touchpoints.md` |
| T+6 min | Voicemail drop if unanswered | Front desk | `manual-touchpoints.md` (script + GHL pre-record) |
| Live | Call script | Front desk | `manual-touchpoints.md` |

### Days 1–14 — Active nurture (Doc 1 sequence flows here)

| Day / Time | Channel | Owner | Source | Goes Where |
|------------|---------|-------|--------|------------|
| D1 10am | Email 1 (welcome + qualifier) | CRM auto | Doc 1 [1] | `.py` |
| D1 10:15am | SMS (echo qualifier) | CRM auto | Doc 1 [2] | `.py` |
| D2 morning | Manual call | Front desk | — | `manual-touchpoints.md` |
| D2 10am | Email 2 (objections + Zeigarnik open) | CRM auto | Doc 1 [3] | `.py` |
| D2 5pm | SMS (reciprocity hook → AI bot) | CRM auto | new | `.py` + bot Branch 2 |
| D2 afternoon | Manual SMS check-in | Front desk | — | `manual-touchpoints.md` |
| D3 10am | Email 3 (quick wins, no sell) | CRM auto | Doc 1 [4] | `.py` |
| D3 10am | SMS (pattern interrupt) | CRM auto | new | `.py` + bot Branch 3 |
| D3 afternoon | Manual call | Front desk | — | `manual-touchpoints.md` |
| D4 10am | Email 4A or 4B (branched social proof) | CRM auto | Doc 1 [5][6] | `.py` |
| D4 5pm | SMS (escalated personalization → AI bot) | CRM auto | Doc 1 [7] | `.py` + bot Branch 4 |
| D5 morning | Hail Mary SMS | Front desk | — | `manual-touchpoints.md` |
| D5 5pm | SMS (curiosity gap → AI bot) | CRM auto | new | `.py` + bot Branch 5 |
| D7 | Pipeline move → Long-Term Nurture | CRM auto | — | `.py` (tag-driven) |
| D7 10am | Email 5A or 5B (Zeigarnik close) | CRM auto | Doc 1 [8] | `.py` |
| D7 10am | SMS (direct question) | CRM auto | new | `.py` |
| D10 10am | Email 6 (logic + cost of inaction) | CRM auto | new | `.py` |
| D12 10am | SMS (objection surfacer → AI bot) | CRM auto | new | `.py` + bot Branch 6 |
| D14 9am | Email 7 (peak-end + keyword) | CRM auto | Doc 1 [9] | `.py` |
| D14 10am | SMS (last call + keyword plant) | CRM auto | new | `.py` |

### Days 15–28 — Dormancy + breakup

| Day | Action | Goes Where |
|-----|--------|------------|
| D28 10am | Breakup SMS → AI bot Branch 7 | `.py` |
| D28 end | Apply `<offer>-nurture-complete` tag, move to Ghost pipeline | `.py` |

### Always-on (separate workflows)

| Workflow | Trigger | Goes Where |
|----------|---------|------------|
| WF Keyword Recovery | Inbound SMS contains KEYWORD any time after D14 | `.py` |
| WF Global Reply Handler | Any inbound reply not matching a keyword | `.py` |

## Tags emitted

```
<offer>-lead              # Form submitted
<offer>-first-timer       # Branch tag from qualifier reply
<offer>-curious           # IV-specific: wellness-curious branch
<offer>-symptom-driven    # IV-specific: symptom-driven branch
<offer>-opened-d1         # Email open
<offer>-opened-d2         # Email open
<offer>-replied           # Substantive inbound reply
<offer>-booked            # Appointment confirmed
<offer>-returning-lead    # Texted KEYWORD after D14
<offer>-nurture-complete  # End of 28-day cycle
```

Replace `<offer>` with the offer slug at generation time (e.g., `firstdrip-lead`).

## Workflow structure mapped to engine

The `.py` campaign defines THREE workflows:

```python
CAMPAIGN = {
    "01-master": {
        "name": "01. <Offer> — Master Sequence",
        "tag": "<offer>-lead",          # Triggered on form-submit tag
        "templates": link_steps([ ... 28 days of automated steps ... ]),
    },
    "02-keyword-recovery": {
        "name": "02. <Offer> — Keyword Recovery",
        "tag": "<offer>-keyword-trigger",  # Fired by inbound SMS keyword filter (set up separately)
        "templates": link_steps([ ... ]),
    },
    "03-reply-handler": {
        "name": "03. <Offer> — Global Reply Handler",
        "tag": "<offer>-replied",
        "templates": link_steps([ ... ]),
    },
}
```

## AI Bot Prompt Skeleton

The bot prompt mirrors the DPN structure (Sections 1–3 of Doc 2). For each new offer:

- **Identity:** name = `{{custom_values.text_message_name}}`, location = `{{location.name}}`, specialty = `<TREATMENT_TYPE>`
- **Branches 1–7:** one per automated SMS that ends in a question. Each branch has trigger phrase + action + tag.
- **Discovery:** rewrite for the offer's branch pair (DPN: first-timer/burned-before; IV: wellness-curious/symptom-driven)
- **Offer details:** OFFER_NAME, price, deposit (if any), what's included
- **In-scope / Out-of-scope** rules
- **Step 1–8 conversation flow** (set frame → pin solution → treatment overview → objections → pitch → close)
- **Tool rules:** Human_Handover triggers, Ai_Stop, Add_Tag_Not_Interested, booking_assistance

## QA Checklist (deploy gate)

The 25-item DPN QA checklist applies almost verbatim. Auto-generated into `<offer>-sequence-qa.md` with each item marked Build & Test / Train / Print / Confirm / Check. Build cannot proceed until all marked items have an owner.

## What this skeleton does NOT solve

- Specific timing per niche (DPN morning calls might be wrong for IV's mobile-service model)
- Whether the offer has a deposit / refundable hold (check Notion `Deposit Required`)
- Whether before/after images exist (`Before Afters Available` — IV says No, so D0 T+1 is text-only)
- Whether a doctor video exists for embedding (`Doctor Video Available`)

These get resolved at generation time per offer, not in the skeleton.
