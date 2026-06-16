# Claude Code Instructions

## After completing any significant work, log it:

Use `gh api` to update `drleadflow/blade-ops/contents/logs/dev-activity.json`. No token needed in code — `gh` handles auth from the keyring.

```bash
# 1. Fetch current log (get sha + decoded content)
gh api repos/drleadflow/blade-ops/contents/logs/dev-activity.json > /tmp/log.json
SHA=$(jq -r .sha /tmp/log.json)
jq -r .content /tmp/log.json | base64 -d > /tmp/current.json

# 2. Prepend new entry
jq --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
   '. = [{repo:"drleadflow/ghl-superspeed-v3", message:"DESCRIBE_WHAT_YOU_BUILT", by:"claude-code", timestamp:$ts, details:"OPTIONAL_DETAILS"}] + .' \
   /tmp/current.json > /tmp/updated.json

# 3. PUT back (base64-encoded)
CONTENT=$(base64 -i /tmp/updated.json)
gh api -X PUT repos/drleadflow/blade-ops/contents/logs/dev-activity.json \
  -f message="log: claude-code activity" \
  -f content="$CONTENT" \
  -f sha="$SHA"
```

## Building & Deploying Campaigns

**Stack:** zero-dependency Python 3 stdlib (no `pip install`). This is NOT the
Next.js + Vitest stack described in the parent `~/Desktop/GITHUB/CLAUDE.md` — do
not run `npm`/`vitest` here. Tests: `python3 tests/test_engine.py`.

Campaigns are Python files in `campaigns/` that import `lib/engine.py` and deploy
GHL workflows. For a build+DEPLOY task, load the **`ship-nurture`** skill — it
encodes the full flow and the known failures. Safe deploy order (never skip):

```bash
python3 scripts/preflight_campaign.py campaigns/<file>.py   # PRE-deploy gate — must exit 0
python3 campaigns/<file>.py                                 # deploy (folder + workflows + triggers)
python3 scripts/deploy_verify.py <loc> --folder "<name>"    # POST-deploy gate — must say ALL GOOD
```

Deploy gotchas (these break silently — preflight catches the first three):
- **Opportunity stage moves use `create_opportunity` (it upserts), NEVER
  `update_opportunity`** — `internal_update_opportunity` is rejected as "corrupted
  type" and a single bad action zeroes ALL steps across every workflow.
- **`customer_reply` triggers REQUIRE a workflow filter** (`source_wf_key`), or they
  deploy with no trigger at all.
- **No em dashes in customer copy** (use ` - `); the builder wires LINEAR chains only.
- **Redeploy duplicates** — clean a failed build first with
  `scripts/cleanup_deploy.py <loc> --folder-id <id>` (use `--folder-id`, not
  `--folder`: two folders can share a name and name-match deletes the wrong/live one).

Full gotcha catalog + action JSON: `.claude/skills/ship-nurture/references/engine-schemas.md`.
Script registry: `.claude/skills/_INDEX.md`.

## The Harness (read `.claude/HARNESS.md`)

`.claude/` runs a self-improving agent harness. The one-page map is
**`.claude/HARNESS.md`** — read it to understand how the pieces fit. Key rules:

- **Skills live in `.claude/skills/<name>/`** and MUST have `SKILL.md`
  (with `## Gotchas` + `## Files`) and `scripts/` (own or cited `scripts/...`).
  Enforced by `python3 scripts/suggest_skills.py --lint` (keep it exit 0).
  Scaffold new ones with `--scaffold <name>`, then `--reindex`.
- **Gotchas (failures) auto-capture** to `.claude/gotchas/OPEN.md` via a Bash
  hook. When something breaks, log it: `python3 scripts/gotcha.py log "<what>"
  --skill <name>`. To clear the queue, invoke the **`gotcha-fixer`** skill — it
  dispatches a background agent per gotcha to root-cause, patch, record the
  lesson in the skill's `## Gotchas`, and resolve it.
- **Operational skills:** `ship-nurture` (build+deploy a nurture), `audit-location`
  (read-only dump/map/doc a live GHL location), `gotcha-fixer` (work the queue).
- Recurring commands worth automating surface in `.claude/metrics/skill-candidates.md`.

## Project Context
- This is a Dr. Lead Flow project
- Owner: Blade (Emeka Ajufo)
- All work feeds into the Command Center at https://blade-command-center.vercel.app
- Log significant completions to blade-ops/logs/dev-activity.json

## Standards
- Commit messages should be descriptive
- After major features, update blade-ops/projects/ if relevant
- Reference blade-ops task files when completing tracked work

## Vault (Knowledge Base)

This folder doubles as an Obsidian vault. Business knowledge sits alongside the engine code:

- `services/` — service catalog (name, description, booking duration, intake)
- `offers/` — packaged offers
- `clients/` — per-client knowledge (currently `_template/` only)
- `campaigns/` — both Python campaign files (`*.py`) AND a vault index (`_index.md`) linking them to services/offers
- `references/` — GHL API quirks and reusable workflow patterns
- `templates/` — both Python campaign blueprints (`blueprints.json`) AND Obsidian note templates (`*.md`)
- `business/` — DLF positioning, brand voice, copy defaults

See `VAULT-README.md` for the full layout.
