# /build-sequence

**Usage:** `/build-sequence <client>-<offer>`

Generates a complete 28-day nurture sequence from a vault offer file. Produces a deployable Python campaign + the operational sidekicks.

Example: `/build-sequence iv-wellness-first-drip-welcome`

---

## What this command does

Reads `offers/<client>-<offer>.md` + vault context. Generates copy via the embedded master prompt. Wraps copy in the 28-day skeleton. Runs QA gate. Writes 4 files.

## Inputs (read in this order)

1. `offers/<client>-<offer>.md` — primary spec
2. `clients/<client>/overview.md` — client context (location ID, ops constraints, contact)
3. `business/brand.md` — voice/copy defaults
4. `business/overview.md` — DLF positioning (for compliance framing)
5. `lib/prompts/master-copy-prompt.md` — Doc 1 verbatim (the copy generator)
6. `lib/prompts/twenty-eight-day-skeleton.md` — Doc 2 structure
7. `lib/prompts/iv-adjustments.md` (or future `<niche>-adjustments.md`) — applied IF offer's `offer_type` matches

## Outputs (written in this order)

1. `clients/<client>/<offer>-sequence-qa.md` — QA report. Written FIRST. If any item fails, stop and surface to user before writing the rest.
2. `clients/<client>/<offer>-manual-touchpoints.md` — front desk runbook (calls, voicemails, manual SMS templates). Printable.
3. `clients/<client>/<offer>-ai-bot-prompt.md` — paste into GHL Conversation AI. Includes all 7 branches mapped to automated SMS triggers.
4. `campaigns/<client>-<offer>-nurture.py` — engine-deployable. Imports from `lib.engine`, defines `CAMPAIGN` dict with 3 workflows (master, keyword recovery, reply handler). Uses `LOCATION_ID` from `clients/<client>/overview.md` frontmatter `ghl_location_id`.

## Execution flow when invoked

### Phase 1 — Variable resolution (no LLM generation yet)

1. Read offer file. If any of the 8 Doc 1 variables = TBD, ABORT and tell user to run `/extract-offer` first or fill manually.
2. Read client overview. Extract `ghl_location_id`. If missing, abort.
3. Detect niche from `offer_type`. Load matching adjustments file (currently only `iv-adjustments.md`; default = no overrides).
4. Resolve all merge fields by reading `clients/<client>/overview.md` (location name, phone, address, consult handler name).
5. Surface to user: "Generating sequence with these inputs: [...]. Confirm before generation?"

### Phase 2 — Copy generation (you = the LLM)

6. Inline-execute the master prompt from `lib/prompts/master-copy-prompt.md` with the 8 variables filled in. Apply niche adjustments verbatim before generating.
7. Output the 10 copy blocks:
   - Day 1 email + SMS
   - Day 2 email + (D2 5pm SMS) + (D2 afternoon manual SMS template)
   - Day 3 email + (D3 SMS pattern interrupt)
   - Day 4 email Variant A (branched: wellness-curious/symptom-driven for IV) + Variant B + (D4 5pm SMS)
   - Day 5 (D5 morning Hail Mary template + D5 5pm SMS curiosity gap)
   - Day 7 email Variant A + Variant B + SMS
   - Day 10 email (logic + cost of inaction)
   - Day 12 SMS (objection surfacer)
   - Day 14 email + SMS
   - Day 28 SMS (breakup)
   - Bonus: D0 T+0 confirmation SMS, D0 T+1 qualifier SMS (text-only for IV)
   - Bonus: voicemail drop script, manual call script, internal alert template

### Phase 3 — QA gate

8. Run every check from `lib/prompts/master-copy-prompt.md` "Output QA Gate" section.
9. Run the 25-item DPN-style checklist from `lib/prompts/twenty-eight-day-skeleton.md`.
10. Write `<offer>-sequence-qa.md` with each item PASS/FAIL/REVIEW. Mark BUILD-blocking failures clearly.
11. If ANY blocking failure: stop. Show user the failure list, ask whether to regenerate the affected piece(s) or proceed anyway.

### Phase 4 — File assembly

12. Build `<offer>-manual-touchpoints.md`:
    - Internal alert templates
    - D0 double-dial protocol + voicemail script
    - D2 morning call + D2 afternoon SMS templates
    - D3 afternoon call template
    - D5 morning Hail Mary SMS template
    - Print-ready format

13. Build `<offer>-ai-bot-prompt.md`:
    - Identity block populated from client + offer
    - 7 branches, each with: trigger phrase (must match the automated SMS exactly), action, tag to apply
    - Discovery flow uses the niche's branch pair (IV: wellness-curious / symptom-driven)
    - Offer details (name, price, deposit, what's included)
    - Tool rules
    - Save the format from the DPN example verbatim, just swap content

14. Build `campaigns/<client>-<offer>-nurture.py`:
    - Standard imports from `lib.engine`
    - `LOCATION_ID`, `COMPANY_ID`, `USER_ID` from client overview
    - `CAMPAIGN` dict with 3 workflows:
      - `01-master`: 28-day automated timeline (excludes manual touchpoints)
      - `02-keyword-recovery`: triggered by `<offer>-keyword-trigger` tag
      - `03-reply-handler`: triggered by `<offer>-replied` tag
    - Use `link_steps()` for each workflow's templates list
    - Branched copy (D4 A/B, D7 A/B): for now implement as separate sub-workflows triggered by tags rather than `if_else` (simpler — see iv-adjustments.md note)
    - All tag names follow `<offer>-<status>` convention (e.g., `firstdripwelcome-lead`, `firstdripwelcome-curious`)
    - End the file with the standard `if __name__ == "__main__":` deploy block (mirror `iv-wellness-nurture.py`)

15. Run `python3 -c "import ast; ast.parse(open('campaigns/<file>.py').read())"` to verify it parses. If it doesn't, fix and re-verify.

### Phase 5 — Report

16. Print to user:
    - 4 files written, with paths
    - QA summary (X PASS / Y REVIEW / Z FAIL)
    - Items requiring human action before deploy (e.g., "voicemail drop must be recorded in client's voice and uploaded to GHL", "deadline date is TBD — set in Notion before launch")
    - Suggested next step: `python3 campaigns/<client>-<offer>-nurture.py` to deploy

## Constraints

- Do NOT commit anything. User reviews diffs.
- Do NOT deploy. The user runs the `.py` themselves after review.
- Do NOT touch `lib/engine.py`, `lib/prompts/*` (those are sources of truth), `tests/`, `.github/`, `.obsidian/`.
- Do NOT regenerate copy that already passed QA in Phase 3 unless user asks.
- If `clients/<client>/overview.md` is missing required fields, abort with what's missing.
- Tag naming: kebab-case, prefix with offer slug. NEVER reuse a tag name across offers (one offer's `lead` tag must not collide with another's).

## Idempotence

If files already exist (e.g., re-running on same offer):
- `sequence-qa.md`: overwrite (it's a fresh run)
- `manual-touchpoints.md`: overwrite
- `ai-bot-prompt.md`: ask user — overwrite or save as `-v2`?
- `campaigns/<file>.py`: ask user — overwrite or save as `-v2`?

The `.py` file is the most user-edited artifact post-generation, so don't clobber it without consent.
