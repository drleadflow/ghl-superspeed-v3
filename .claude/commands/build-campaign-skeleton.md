# /build-campaign-skeleton

**Usage:** `/build-campaign-skeleton <offer-slug> [--force]`

Generates a deployable Python campaign skeleton from a vault offer file. Pre-fills LOCATION_ID, COMPANY_ID, USER_ID, FROM_NAME, BOOKING_LINK, prices, tag namespace, and a 36-step workflow scaffold with TODO copy markers.

Example: `/build-campaign-skeleton iv-wellness-nad-iv-therapy`

---

## When to use this vs `/build-sequence`

| Need | Use |
|---|---|
| Full LLM copy generation + QA + 4 files (campaign + sequence-qa + manual-touchpoints + ai-bot-prompt) | `/build-sequence` |
| Just the structural `.py` file with vault constants pre-filled — fill copy yourself or pipe through copy gen later | `/build-campaign-skeleton` (this) |
| Iterate on the workflow shape without re-running heavy copy generation each time | `/build-campaign-skeleton --force` |

This command is **deterministic, no LLM, no Notion calls** — pure local vault reads. Generates in <1s, ~3K tokens of slash-command overhead.

## Inputs

1. `offers/<offer-slug>.md` — must exist with valid frontmatter (run `/extract-offer` first if missing)
2. `clients/<client>/overview.md` — must exist with `ghl_location_id` set

## Output

`campaigns/<offer-slug>-nurture.py` — a runnable skeleton with:
- Engine imports + sys.path bootstrap
- `LOCATION_ID`, `COMPANY_ID`, `USER_ID` pulled from client overview
- `FROM_NAME`, `BOOKING_LINK` resolved (or `{{custom_values.*}}` fallbacks)
- Tag namespace prefixed with offer slug (collision-safe)
- 3-workflow `CAMPAIGN` dict: master / keyword-recovery / reply-handler
- ~36 steps with TODO copy markers
- Standard `if __name__ == "__main__":` deploy block
- Header docstring listing applied shape decisions (deadline, before-afters, deposit, niche overrides)

## Execution flow

1. Run: `python3 -m lib.skeleton_builder <offer-slug>` (add `--force` if file exists and user confirmed overwrite)
2. The Python module:
   - Reads `offers/<slug>.md` via `lib.vault.get_offer()`
   - Reads `clients/<client>/overview.md` via `lib.vault.get_client()`
   - Validates required fields (offer.client, offer.name, offer.offer_type, offer.status, client.ghl_location_id)
   - Walks the shape decision table from `.claude/skills/learned/ghl-sequence-shape-from-notion/SKILL.md`
   - Renders the template
   - `ast.parse()` checks syntax before writing
   - Writes to `campaigns/<offer-slug>-nurture.py`
3. After write, the module prints:
   - The output path
   - A verify command (`python3 -c "import ast; ast.parse(open('...').read())"`)
   - Suggested next: `/build-sequence <slug>` for full LLM copy gen, OR edit directly
4. Report to user: file written, step count, applied shape decisions, what's still TODO

## Idempotence

- If `campaigns/<offer-slug>-nurture.py` already exists, the module raises `FileExistsError`. Surface to user: "File exists — overwrite (`--force`) or rename existing?"
- Only the user can decide because the existing file may have hand-edited copy.

## Error handling

- Offer not found → "Run `/extract-offer <notion-url>` first or check the slug spelling. Run `python3 -m lib.vault list-offers` to see available slugs."
- Client overview missing → "Run `/extract-offer` (which auto-creates client folder) or copy `clients/_template/` to `clients/<slug>/`."
- Required field missing on offer/client → list the missing fields, point at the template path
- Generated file fails `ast.parse` → bug in skeleton template. Report with line number and ask user to file an issue.

## Constraints

- Don't deploy. The user runs the `.py` themselves after review.
- Don't fabricate values. If a field is missing from the vault, emit `TODO_<FIELDNAME>` and surface it.
- Don't touch `lib/engine.py`, `lib/prompts/*`, `lib/vault.py`, `lib/skeleton_builder.py` (these are the build infra).
- Don't run `/build-sequence` automatically — they're separate commands. The user decides whether to fill TODOs by hand or via LLM.

## Why this exists (token math)

| Path | Tokens (typical) | What you get |
|---|---|---|
| Hand-write `.py` from Notion | 30–60K (MCP fetches + copy paste turns) | Runnable .py |
| `/build-sequence` (full) | ~30K (LLM copy gen + QA) | Runnable .py + QA + manual touchpoints + AI bot prompt |
| `/build-campaign-skeleton` (this) | ~3K (slash command only, no LLM) | Runnable .py with TODO copy markers |

When you've already generated copy elsewhere or you want to iterate the workflow shape fast, this is the path.
