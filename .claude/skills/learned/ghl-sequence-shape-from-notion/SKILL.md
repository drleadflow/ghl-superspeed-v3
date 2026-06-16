---
name: ghl-sequence-shape-from-notion
description: "Map Notion offer properties to deterministic shape changes in the generated 28-day GHL nurture sequence"
user-invocable: false
origin: auto-extracted
---

# GHL Sequence Shape from Notion Properties

**Extracted:** 2026-05-05
**Context:** Running /build-sequence after /extract-offer has populated `offers/<client>-<offer>.md` from Notion

## Problem

The Doc 1 master copy prompt assumes a stock 14-day shape; the Doc 2 orchestration assumes a stock 28-day shape with V2 deadline overlay. Real offers vary — some have no deadline, some have no before/after photos, some require deposits, some don't. Generating the stock shape regardless produces awkward copy and structurally broken workflows (e.g., a "before pricing changes" email when the offer has no deadline).

## Solution

Apply this decision table BEFORE running the master copy prompt. Each Notion property triggers a deterministic shape change.

| Notion property | Value | Shape change |
|---|---|---|
| `Has Deadline` | No / "" | DROP V2 Day 5 loss-framed deadline email · D5 5pm SMS becomes curiosity/value hook (no scarcity tone) · Day 14 omits "before pricing changes" framing · Total touchpoints 28 → 27 |
| `Has Deadline` | Yes + `Deadline Date` empty | Treat as "no deadline" for generation but flag for user to set before deploy |
| `Has Deadline` | Yes + `Deadline Date` set | Full V2 overlay; resolve `{{custom_values.offer_deadline}}` at runtime |
| `Before Afters Available` | No | D0 T+1 = SMS text-only (NOT MMS) · "reply 'photos'" micro-CTA replaced with niche-appropriate substitute (e.g., "reply 'formulas'" for IV) · Bot Branch 1 stops referencing photos |
| `Before Afters Available` | Yes | D0 T+1 = MMS with 3 pre-loaded images · "reply 'photos'" CTAs included |
| `Deposit Required` | No | Skip deposit-hold CTAs · D1 mentions "card on file or pay at visit" · D4 CTA = "Book Your Slot" not "Hold My Spot, $X Deposit" |
| `Deposit Required` | Yes | D1 includes deposit paragraph · D4 CTA = "Hold My Spot, $X Deposit" · Bot Step 8.2 includes deposit collection |
| `Doctor Video Available` | "Need to film" / "" | No video embed; sequence runs without it |
| `Doctor Video Available` | URL | Embed link in D2 objection-handler email body |
| `Uses Bot` | No | Bot prompt still generated; QA flags as "manual fallback until bot enabled" |
| `Uses Bot` | Yes | Bot prompt primary; SMS hooks designed for bot reply parsing |
| `Offer Type` matches IV / drip / infusion | — | Apply `lib/prompts/iv-adjustments.md` — these OVERRIDE the rows above where they conflict (e.g., IV is text-only D0 T+1 even if `Before Afters=Yes`) |

## Override Hierarchy (highest wins)

1. Niche adjustments file (`lib/prompts/<niche>-adjustments.md`)
2. Notion property table above
3. Stock Doc 2 28-day skeleton

## Implementation order in /build-sequence

1. Read offer frontmatter
2. Detect niche from `Offer Type`; load matching adjustments file
3. Walk the property table; collect shape changes
4. Inject consolidated shape changes into Doc 1 prompt as a "SHAPE OVERRIDES" section before generation
5. Run copy generation
6. Apply structural changes to the 28-day skeleton (drop/replace touchpoints) BEFORE writing the `.py`
7. Document final touchpoint count + dropped/modified items in QA report ("27 touchpoints — Day 5 deadline email dropped per `Has Deadline=No`")

## When to Use

Every `/build-sequence` invocation. This is mandatory pre-generation logic, not optional optimization.

## Anti-pattern

Generating the stock 28-day sequence regardless of Notion properties, then patching after the fact. Produces:
- Compliance-risky deadline language on no-deadline offers
- MMS steps for offers with no images (engine accepts but renders empty)
- Deposit CTAs on no-deposit offers
- Wasted touchpoints (V2 emails sent into the void)
- "Reply 'photos'" CTAs on IV/wellness offers where no photos exist
