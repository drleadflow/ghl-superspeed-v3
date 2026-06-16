# IV Therapy Niche Adjustments

> Overrides applied by `/build-sequence` when offer's `Offer Type` includes "IV" / "drip" / "infusion".
> Other niches (Botox, lasers, facials, body contouring) get their own adjustment files in time.

## Hard overrides

### No before/after images
- D0 T+1 min becomes text-only SMS, not MMS
- Replace "reply 'photos'" micro-CTA with "reply 'formulas'" → bot delivers formula menu
- Day 4 Variant A removes the photo offer; substitute "reply with your goal and I'll suggest a formula"

### Compliance language (FDA / FTC sensitive)
Banned phrases:
- ❌ cures, treats, fixes, eliminates, guarantees
- ❌ "lose X pounds", "boost immunity", "reverse aging" (specific outcome claims)
- ❌ "medical-grade results", "doctor-prescribed" (unless literally true and documented)

Approved phrases:
- ✅ "supports", "complements", "helps with", "may help"
- ✅ "patients often describe feeling…"
- ✅ "in our experience"
- ✅ Cite the formula by name without claiming what it does (e.g., "the Myers cocktail" not "the Myers cocktail that fixes fatigue")

### Branch pair: Wellness-curious vs. Symptom-driven
Replaces DPN's first-timer/burned-before pair.

**D0 T+1 qualifier SMS:**
> Hey {{contact.first_name}}, {{custom_values.text_message_name}} here. Quick question — are you exploring IV therapy for general wellness, or is there something specific you're trying to feel better from?

Reply parsing:
- "wellness", "energy", "longevity", "curious", "general" → `<offer>-curious`
- "tired", "hangover", "sick", "migraine", "recover", "athletic", specific symptom → `<offer>-symptom-driven`

### Day 4 Variant A — branched copy

**Wellness-curious variant:**
- Lead with a "she came in just to try it, ended up with a monthly drip" story
- Frame: discovery, exploration, baseline-setting
- Soft CTA

**Symptom-driven variant:**
- Lead with a specific symptom + specific formula match (e.g., post-flu Cold & Flu drip)
- Frame: targeted relief, RN assessment, fast turnaround
- Slightly stronger CTA

### Pratfall flaw — operational, not clinical
DPN flaw: "parking is bad" → operational
IV flaw must also be operational (mobile service has its own constraints):
- "We only cover 20 miles around Cincinnati — outside that, we can't come to you"
- "Mobile means we work around the RN's drive route, so same-day isn't always doable"
- "We don't do walk-ins — every drip is by appointment so the RN can pre-mix"

NOT acceptable as flaws (bad pratfall):
- "We're really thorough" (humble-brag)
- "Our RN is so nice" (not a flaw)
- "We only use the highest quality ingredients" (humble-brag)

### Manual call script — adapted for mobile
Front desk doesn't say "come in" — they say "what's the closest you to home address you'd want the drip delivered to":

```
Hi {{contact.first_name}}, this is [Staff Name] from {{location.name}}.
I saw you just requested the $50-off welcome drip. I'm calling to get
your RN visit on the schedule. Are you looking for something this week
or next? And just to confirm — are you in the Cincinnati area within
20 miles?
```

### Voicemail drop — adapted for mobile
```
Hi {{contact.first_name}}, this is {{custom_values.text_message_name}}
from {{location.name}}. I'm calling about the IV drip you requested.
We've got a few RN slots opening up this week — call me back at
{{location.phone}} or just reply to my text to lock one in. Talk soon!
```

### AI bot — IV-specific identity addendum
Append to bot system prompt:

> You specialize in mobile IV therapy across {{location.address}} and a 20-mile radius.
> You are NOT a doctor — you are the booking concierge. Any clinical question (drug
> interactions, pregnancy, current medications, IV history) triggers Human_Handover.
> The RN does the assessment on-site, not over text.
>
> 14 formulas available, but DON'T list them all unprompted. If asked, offer to send
> the menu link or pick the top 3 based on what they've shared.

### Step types per touchpoint (engine mapping)

| Touchpoint | Engine step |
|------------|-------------|
| D0 T+0 SMS | `sms_step` |
| D0 T+1 SMS qualifier | `sms_step` (text-only, NOT MMS) |
| D1 10am email | `email_step` (use `dm_email()` for HTML conversion) |
| D1 10:15am SMS | `sms_step` after `wait_step("15 min", 15, "minutes")` |
| Manual touchpoints | NOT in `.py` — go to `manual-touchpoints.md` |
| Tag application | `tag_step` |
| Branched email/SMS | Engine handles via `if_else` step OR split into separate workflows triggered by branch tag (preferred — simpler than if_else) |

### What goes into Notion's empty fields

When the offer's `Deadline Date` is empty but `Has Deadline=Yes`, default to: `30 days from extraction date`. Surface to user for confirmation.

When `Risk Reversal` is empty, propose: "Talk to the RN before any needle. If it's not a fit, no charge."

When `Guarantee` is empty: leave empty. Don't invent.

### Suggested KEYWORD per offer type

| Offer | KEYWORD |
|-------|---------|
| First-visit drip | DRIP |
| Recovery / hangover | RECOVER |
| Energy / NAD+ | BOOST |
| Beauty / Glow Up | GLOW |
| Membership | MEMBER |
| Athlete | ATHLETE |

User can override at generation time.
