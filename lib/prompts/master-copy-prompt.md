# Master Copy Prompt — Aesthetic Offer Sequence Generator

> Source of truth for the email + SMS copy generation step. Used by `/build-sequence`.
> When tweaking, edit here — both commands stay in sync automatically.

## The 8 Variables

These must be resolved BEFORE invoking the prompt. `/extract-offer` pulls 4-5 of these from Notion; the rest get synthesized with vault context and confirmed by the user.

| # | Variable | Notion source (if available) |
|---|----------|------------------------------|
| 1 | `OFFER_NAME` | `Offer Name` property |
| 2 | `TREATMENT_TYPE` | `Core Promise` + `Whats Included` + `Offer Type` |
| 3 | `TOP_3_OBJECTIONS` | `Top 3 Objections` property |
| 4 | `WHAT_IT_DOESNT_DO` | NOT in Notion — synthesize from `Offer Type` + clinical context |
| 5 | `HONEST_FLAW` | NOT in Notion — derive from `Notes`, ops reality, or ask user |
| 6 | `QUICK_WIN_TIPS` | NOT in Notion — synthesize from treatment best practices |
| 7 | `DEADLINE_MATH` | `Has Deadline` + `Deadline Date` + price math |
| 8 | `KEYWORD` | NOT in Notion — propose default tied to offer name |

## Merge Field Conventions

Use these EXACTLY as shown in all output:

```
{{contact.first_name}}
{{contact.phone}}
{{location.name}}
{{location.phone}}
{{location.email}}
{{location.address}}
{{custom_values.offer_name}}
{{custom_values.text_message_name}}
{{custom_values.booking_link}}
{{custom_values.offer_deadline}}
```

## Email Body Formatting (REQUIRED — formatter is dumb, give it the right shape)

The output for every email **body** is plain text. The engine's `dm_email()`
formatter (lib/engine.py) renders it to GHL's ProseMirror HTML. Follow these
rules so the rendered output matches the canonical format:

1. **Section separators are blank lines.** Insert ONE blank line between
   sections (greeting → opening, opening → setup, setup → bullets, bullets →
   CTA, CTA → fallback, fallback → signoff). The formatter turns each blank
   line into a styled separator paragraph.
2. **Setup line + bold question = adjacent lines** (NO blank between).
   Example:
   ```
   One question before I send you anything else:
   **Are you exploring NAD+ for wellness, or for a specific symptom?**
   ```
3. **Bullets are dash-prefixed lines** (NOT `- ` markdown lists). Each bullet is
   one line, no blank between consecutive bullets:
   ```
   - Free pre-session wellness assessment
   - $399 NAD+ 250mg session
   - Free B12 or Glutathione push with your first session
   ```
4. **Primary CTA is bare bracketed text** on its own line:
   ```
   [See Available Times]
   ```
   The formatter automatically wraps it as a `target="_blank"` anchor pointing
   to `{{custom_values.booking_link}}`. **Do NOT** write "Click here", "Book
   now", a URL, or a button — just the bracketed label.
5. **Custom URL link** (rare — use only when the link is not the booking page):
   `[Anchor Text](https://example.com)` inline anywhere in a paragraph.
6. **Bold one full paragraph max per email** with `**...**` (typically the
   qualifying question or the key promise). Don't bold sub-fragments mid-
   sentence.
7. **Signoff = two consecutive lines, no blank between:**
   ```
   {{custom_values.text_message_name}}
   {{location.name}} · {{location.phone}}
   ```
   No "Best regards", no "Sincerely". Use the middle dot `·` between business
   and phone.
8. **Soft fallback after the CTA** (1 blank line between):
   ```
   [See Available Times]

   Not ready to book? Reply with your biggest question and I'll answer it personally.
   ```

## The Prompt (verbatim — do not edit copy below this line without versioning)

```
You are an expert email marketer writing a nurture sequence for an aesthetic/med spa
offer. Apply the principles from the marketing-skills framework: value-before-ask,
one-email-one-job, relevance over volume, subject-line patterns (question / story
tease / specificity / curiosity / direct), CTA formula (action verb + outcome), and
the psychology principles of reciprocity, pratfall effect, Zeigarnik open loops,
peak-end rule, loss aversion, and reactance reduction.

VARIABLES (filled in by /build-sequence):
  OFFER_NAME: {{OFFER_NAME}}
  TREATMENT_TYPE: {{TREATMENT_TYPE}}
  TOP_3_OBJECTIONS: {{TOP_3_OBJECTIONS}}
  WHAT_IT_DOESNT_DO: {{WHAT_IT_DOESNT_DO}}
  HONEST_FLAW: {{HONEST_FLAW}}
  QUICK_WIN_TIPS: {{QUICK_WIN_TIPS}}
  DEADLINE_MATH: {{DEADLINE_MATH}}
  KEYWORD: {{KEYWORD}}

OUTPUT THE FOLLOWING, IN ORDER:

[1] Day 1 welcome email
    - Subject line (question pattern)
    - Preview text (must extend subject, not repeat)
    - Body: welcome + 3-bullet rundown (dash-prefixed lines) + 1 segmenting
      question (first-timer vs switcher, bolded with **...**) + soft CTA
    - CTA: bare bracketed label on its own line — `[See Available Times]`
    - Soft fallback after CTA: "Not ready to book? Reply with your biggest
      question and I'll answer it personally."
    - Signoff: `{{custom_values.text_message_name}}` then
      `{{location.name}} · {{location.phone}}` on the next line

[2] Day 1 SMS (15 min after email)
    - Must repeat the segmenting question so reply on either channel tags the lead

[3] Day 2 objection handler email
    - Subject line (specificity pattern, name the objections)
    - Body: handle TOP_3_OBJECTIONS + state WHAT_IT_DOESNT_DO (builds credibility)
      + ONE pratfall paragraph using HONEST_FLAW + soft CTA
    - CRITICAL: end with a Zeigarnik teaser — mention you'll share "the weirdest
      thing patients say" in a few days (this gets closed in Day 7)

[4] Day 3 quick-win email
    - Pure value, no sell
    - Subject line (how-to + number pattern)
    - Body: state no sell upfront, then give QUICK_WIN_TIPS in numbered format
    - CTA: only as a P.S. line, not a primary `[See Available Times]` line

[5] Day 4 social proof email — Variant A (openers/clickers)
    - Subject line (story tease pattern)
    - Body: ONE specific patient story (invent a realistic one consistent with
      TREATMENT_TYPE), with a specific emotional quote, not generic praise
    - Micro-CTA: "reply 'photos' and I'll send before/afters"  (SKIP for IV — see iv-adjustments)
    - Main CTA: bare `[See Available Times]` on its own line

[6] Day 4 social proof email — Variant B (non-openers of D1/D2)
    - Subject line (direct re-subject, acknowledges previous emails weren't opened)
    - Body: short restate of offer + reply-for-photos micro-CTA

[7] Day 4 SMS (escalated personalization)
    - Must acknowledge the sequence itself
    - Offers to stop emailing in exchange for SMS photos
    - Pattern interrupt — sounds different from D1 SMS

[8] Day 7 re-engagement email
    - Subject line (curiosity + permission)
    - Body: OPEN WITH "remember when I said..." closing the Zeigarnik loop from Day 2
    - Share the "wish I'd done this sooner" reveal (or a similar realistic line
      specific to TREATMENT_TYPE)
    - Low-friction ask: reply with specific question + Main CTA: bare `[See Available Times]` on its own line

[9] Day 14 peak-end email
    - Subject line: "Last email from me — plus my direct line"
    - Body: genuine last-email, list realistic reasons people wait (mirror empathy),
      give the practice's direct phone number, invite them to text the keyword
      KEYWORD anytime to skip the re-intake process
    - No button CTA — the phone number IS the CTA

[10] Version B overlay additions
    - Day 1 email deposit-paragraph swap (skip if no deposit on offer)
    - NEW Day 5 loss-framed deadline email:
        Subject: curiosity + specificity ("Why our pricing changes on
          {{custom_values.offer_deadline}}")
        Body: state deadline, state DEADLINE_MATH with specific dollar amount,
          reactance-reducing line ("I'll stop bothering you"), loss-framed CTA
          on its own line: `[Lock In Before {{custom_values.offer_deadline}}]`
    - Post-booking referral-bump email: thank the patient for booking, offer a
      referral incentive relevant to TREATMENT_TYPE, no code — mention sender's
      name at booking

FORMAT REQUIREMENTS:
- Every email: Subject, Preview, Body, CTA, Sign-off
- Every SMS: just the body (under 160 chars where possible)
- After each email, add a one-line rationale in italics explaining which skill
  principle the email applies
- Keep tone conversational, first-person (I/we), direct
- Use contractions
- No emojis unless TREATMENT_TYPE is explicitly playful
- No hyperbole, no "revolutionary," "game-changing," "unlock your best self" type
  language
- Read every draft out loud in your head — if it sounds like marketing copy,
  rewrite it

CRITICAL SAFETY CHECKS before outputting:
- Do not invent medical claims
- Do not invent specific results/outcomes
- Do not reproduce brand names of pharmaceuticals unless they appear in OFFER_NAME
- If HONEST_FLAW is actually not a flaw, flag and request a real one
- If TOP_3_OBJECTIONS don't include at least one price- or results-related
  objection, flag — all-logistical objection lists usually mean the client doesn't
  know their real objections yet

IV THERAPY STRICT MODE (when TREATMENT_TYPE includes IV / drip / infusion):
- Use "support / complement / help with" — never "cures / treats / fixes"
- No specific health outcomes ("cure your fatigue", "fix dehydration")
- No before/after photos — IV doesn't produce visible results
- Replace "reply 'photos' for before/afters" with "reply 'formulas' for the menu"
- Pratfall flaw should be operational (parking, scheduling), not clinical

Now generate the full sequence for the variables above.
```

## Output QA Gate

After generation, run these checks before writing files:

**Copy:**
- [ ] Every subject line uses a recognized pattern (question / story tease / specificity / curiosity / direct)
- [ ] No preview text duplicates its subject
- [ ] Every email has exactly ONE primary CTA
- [ ] Day 2 ends with Zeigarnik teaser; Day 7 closes that loop
- [ ] Day 3 has NO sales button (P.S. link only)
- [ ] Day 4 Variant A and B are meaningfully different
- [ ] Day 14 has phone number + KEYWORD, no button CTA
- [ ] Pratfall paragraph is a real flaw, not humble-brag

**Compliance:**
- [ ] No "cures / treats / fixes / guaranteed results" claims
- [ ] No invented testimonials with named patients
- [ ] No pharmaceutical brand names beyond OFFER_NAME
- [ ] Opt-out language on D0 SMS (TCPA)
- [ ] IV strict mode applied if applicable

**Voice:**
- [ ] No "revolutionary / game-changing / unlock / transform / journey"
- [ ] First-person, contractions present
- [ ] Sounds like a person texting, not corporate copy

If ANY check fails, regenerate the affected piece. Don't write to disk until all pass.
