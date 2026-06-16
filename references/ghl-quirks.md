---
type: reference
last_updated: 2026-05-05
---

# GHL API Quirks

Hard-won knowledge about GHL's internal API. Mirror of the "Gotchas" section in `../README.md` plus anything else discovered during deployments.

## Wait unit strings are inconsistent

- `minutes` (plural)
- `hour` (SINGULAR — not `hours`)
- `days` (plural)

Engine maps automatically — pass `"hours"` and it sends `"hour"`.

## Tags must exist before triggers reference them

`POST /workflow/{loc}/tags/create` BEFORE creating a trigger that references the tag. Otherwise the trigger renders with a blank tag in the UI.

## Triggers need targetActionId

After `POST /trigger`, follow up with `PUT /trigger/{id}` including `targetActionId` pointing to the first step's UUID. Without this, the trigger floats disconnected on the advanced canvas.

## Version field is mandatory on PUT

Every `PUT /workflow/{loc}/{wfId}` must include the current `version`. Stale versions are rejected.

## Auto-save endpoint requires a UI session

`PUT /workflow/{loc}/{wfId}/auto-save` only works inside an active editor session. For programmatic use, use the regular `PUT` with `triggersChanged: true` + `oldTriggers`/`newTriggers`.

## Auth is Firebase JWT, not OAuth

Header: `token-id: <firebase-jwt>`, NOT `Authorization: Bearer`. Also requires `channel: APP`.

## New findings

(Add as discovered.)

- 
