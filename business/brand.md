---
type: brand
last_updated: 2026-05-05
---

# Brand & Copy Defaults

Voice and copy conventions used across Superspeed-deployed campaigns. Per-client overrides live in `clients/<name>/`.

## Voice

- Direct, warm, professional
- First-person from the practice owner where appropriate
- Avoid hype words and emoji in SMS

## SMS Defaults

- Open with `Hey {{contact.first_name}},`
- Sign with practice name, not provider name (unless the message is from the doctor)
- Keep under 160 chars when possible

## Email Defaults

- Subject lines: lowercase, plain, conversational
- Sender name: practice name unless specified per client
- Plain text body, `dm_email()` formatter handles HTML conversion

## Tag Naming Convention

- Lowercase, kebab-case: `new-lead`, `welcome-complete`, `nurture-start`
- Trigger tags end in `-start`, completion tags end in `-complete` or `-done`

## Wait Defaults

- First touch: same day
- Day-2 follow-up: 1 day
- Long nurture: weekly cadence max
