# Build Defaults — apply these so you don't ask known questions

These are the standing conventions. The doc or the user can override any of them;
otherwise use these.

## Persona / copy
- **SMS / front-desk persona = `Ashley`** (custom value `text_message_name`).
  Never the provider (the bot hands off to the provider).
- **DEFAULT TONE = warm, laid-back, personal, human.** SMS should read like Ashley
  / the front desk is naturally texting one person, NOT like a campaign chasing a
  lead. Emails should feel like they come from Ashley personally, NOT a newsletter
  / blog / sales blast. Short sentences, plain language, low pressure ("no
  pressure", "no guessing", "totally normal"). Ask genuine questions and invite a
  reply. Prefer this voice over the longer, claim-dense "clinical" style unless the
  doc or client explicitly wants it. (Confirmed preferred by client 2026-06-16.)
- **SMS link discipline (default):** include the booking link ONLY in the first
  confirmation SMS and the final SMS. Every SMS in between is reply-driven /
  nurture with NO link — it reads more human and protects deliverability. Emails
  may all carry the link (that's where the lead can slow down and book).
- Fix all body-copy typos and broken merge fields before shipping.
- **NEVER use em/en dashes (—/–) in email or SMS body or subject copy** — use
  `" - "` or restructure. (Dashes are fine only in workflow/step names + code.)
- Convert every CTA to a bare `[Label]` line (auto-links to
  `{{custom_values.booking_link}}`), e.g. `[See Available Times]`,
  `[Schedule a Consultation]`. Inline links use `[text](url)`.
- Spacing: write a single `\n` between sections, no blank lines, `- ` bullets.
  `dm_email` renders `EMAIL_P_STYLE` paragraphs (16px bottom margin), tight
  bullets/lead-ins, and **NO `<br>` separators** (verified correct 2026-06-01).
  Do NOT add blank lines or separators (that double-spaces). Don't trust
  `.claude/email-format-reference.json` for spacing — it's double-spaced.
- One primary CTA per email.

## Workflow structure (standard 4)
1. **WF-01 Master** — entry trigger = **Facebook lead form** (`facebook_lead_gen`
   with page/form IDs). This is the standard FIRST automation for every build.
   Fallback if IDs unknown: `contact_tag <prefix>-lead` + set the FB form to add
   that tag on submit. **Standard entry block (see engine-schemas.md):**
   (a) Update Contact "Latest Opt-In" = this offer's opt-in label →
   (b) **Find Opportunity** (FlowBot) → Found: **update** opp to Engagement /
   Not Found: **create** opp in Engagement (both set the opp's Latest-Opt-In
   custom field = `{{contact.latest_optin}}` and `status: open`) →
   (c) the email/SMS/wait timeline. Last step tags `<prefix>-nurture-complete`.
2. **WF-02 Reply Handler** — trigger `customer_reply` filtered to WF-01. Steps:
   move opp to **Connected/Qualification** (via create-upsert), tag
   `<prefix>-replied`, assign provider, internal SMS alert.
3. **WF-03 Keyword Recapture** (if the doc has a keyword like RESET) — trigger
   `customer_reply` filtered to WF-01 + the keyword. Tag returning, clear
   complete, auto-reply SMS w/ booking link, assign, alert.
4. **WF-04 Post-booking** (if Version-B referral) — trigger `contact_tag
   <prefix>-booked` (point at Appointment Booked in UI). Sends the referral email.

## Splits / branching / deadline
- **No 50/50 splits, no if/else forks** — the engine wires linear only. Ship a
  single strong variant; defer A/B and reply-content auto-segmentation to v2/UI.
- **Deadline** → location custom value `offer_deadline`, updated per cohort
  (NOT a per-contact date field — custom values are global). Day-1 + deadline
  emails merge it. May be left empty until the cohort date is known.

## Tags
- Per-client short **prefix** (e.g. `apr-` for APrestige). NEVER reuse a tag
  across offers. Engine auto-creates tags at deploy.

## Opportunity (correct pattern — find first, then update/create)
- Always **Find Opportunity (FlowBot) → Found: update / Not Found: create** —
  never a bare update (it's rejected without a preceding find) and never a bare
  create (wrong pattern, risks dupes).
- WF-01 entry → stage **Engagement**. WF-02 (on reply) → move to
  **Connected/Qualification**. Both set opp custom field Latest-Opt-In =
  `{{contact.latest_optin}}`, `source = {{contact.source}}`, `status = open`.
- This block is MULTIPATH (transitions + goto rejoin) — the engine's link_steps
  can't wire it; build it in the UI or via a future `opportunity_entry_block()`
  helper. See engine-schemas.md for the exact wiring.

## Compliance (medical weight-mgmt / aesthetics / hormones)
- No specific outcome/weight-loss numbers, no diagnostic/cure/reverse language,
  no guarantees. GLP-1 stays conditional ("may be part of the protocol if
  appropriate"). Patient stories use initials only.
- **Do NOT append "Reply STOP to opt out" (or build a STOP/unsubscribe exit
  workflow) by default.** GHL handles opt-out (DND) automatically, and the
  disclaimer makes copy feel like a bulk campaign rather than a personal text.
  Omit it unless the client explicitly asks for it. (Confirmed by client
  2026-06-16; overrides the old "every SMS includes STOP" rule.)
- Physical-address footer on every email (enable the location email footer in
  GHL, or inline the address).

## Ask the user ONLY for (batch into one question set)
- `booking_link` URL (if not in the doc)
- persona name (only if not Ashley and not in the doc)
- `offer_deadline` value (or confirm leave-empty)
- FB page/form IDs (if not discoverable from the workflow UI)
- the location's Firebase refresh token (only if Phase 0 auth genuinely fails)
- any business call the doc leaves truly ambiguous
