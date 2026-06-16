---
type: reference
last_updated: 2026-05-05
---

# Workflow Patterns

Reusable campaign shapes that show up across clients.

## Tag-triggered nurture

```
trigger: tag added (`<niche>-nurture-start`)
  → SMS welcome
  → wait 1 day
  → email value drop
  → wait 2 days
  → SMS check-in
  → tag complete
```

When to use: any post-lead-capture nurture where the lead has consented to messaging.

## Webinar registration → attend → follow-up

```
trigger: tag `<event>-registered`
  → email confirmation
  → wait until 24h before event → SMS reminder
  → wait until event time → email "join now"
  → wait 1 day → branch by attendance tag
```

When to use: any one-time event funnel.

## Booked call → reminder → no-show recovery

```
trigger: appointment booked
  → wait until 24h before → SMS reminder
  → wait until 1h before → SMS final reminder
  → branch by show/no-show tag
    show → tag `consult-complete`
    no-show → SMS rebook + tag `no-show`
```

When to use: any service that uses a booking calendar.

## Add new patterns

When you've used the same shape in 2+ campaigns, document it here.
