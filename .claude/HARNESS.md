# The Harness — how `.claude/` works in this repo

One page to understand the whole agent setup: the self-improving loops, the skill
system, and the gotcha-fixer. If you only read one `.claude/` file, read this.

> Engine docs: `README.md` (campaign engine) · `VAULT-README.md` (knowledge base) ·
> `CLAUDE.md` (project rules + deploy order). This file is the **agent harness**.

## The three loops

The harness runs three self-improving loops. Each turns repeated friction into a
durable artifact so future-us doesn't re-pay the cost.

```
1. AUTOMATION LOOP        every Bash cmd ──hook──▶ bash-usage.jsonl ──suggest_skills.py──▶ skill-candidates.md
   (recurring cmd → tool)                                                   │
                                                            "wrap this in a script/skill"

2. GOTCHA LOOP            failing Bash ──hook──▶ gotchas/raw.jsonl ──gotcha.py──▶ OPEN.md
   (failure → durable fix)                                                  │
                                                    gotcha-fixer skill ──▶ background agent ──▶ patch + RESOLVED.md

3. SKILL LOOP             new capability ──scaffold──▶ skill dir ──lint──▶ enforced structure ──reindex──▶ _INDEX.md
   (capability → skill)                                          (md + Gotchas + Files + scripts)
```

All three are driven by `scripts/suggest_skills.py` and `scripts/gotcha.py` plus
two PostToolUse hooks. Nothing here needs third-party deps (stdlib Python only).

## Directory map (`.claude/`)

| Path | What it is |
|---|---|
| `HARNESS.md` | This file — the harness map. |
| `settings.json` | Hooks: Bash PostToolUse (usage + gotcha capture), SessionStart (notices). |
| `hooks/log-bash-usage.py` | Appends every Bash cmd to `metrics/bash-usage.jsonl` (automation loop). |
| `hooks/capture-gotcha.py` | Appends high-confidence Bash failures to `gotchas/raw.jsonl` (gotcha loop). |
| `metrics/bash-usage.jsonl` | Raw command ledger (git-ignored, churny). |
| `metrics/skill-candidates.md` | Recurring commands worth automating (generated). |
| `gotchas/OPEN.md` / `RESOLVED.md` | Live gotcha queue + fix history (tracked). |
| `gotchas/raw.jsonl` | Raw gotcha event ledger (git-ignored). |
| `skills/_INDEX.md` | Auto-generated registry of all scripts + skills. |
| `skills/AUTHORING.md` | The skill convention (read before authoring a skill). |
| `skills/<name>/` | A skill: `SKILL.md` + `scripts/` + optional `references/`. |
| `skills/learned/` | Auto-extracted knowledge notes (exempt from the full skill structure). |
| `commands/*.md` | Slash-command docs (`/extract-offer`, etc.) — see "Commands vs skills". |
| `sessions/` | Pre-compact session snapshots. |
| `hindsight/PATTERNS.md` | Behavioral patterns extracted from sessions. |
| `PRIMER.md` | Session handoff template. |

## Skills: the rule

**Every operational skill is a DIRECTORY with: a `SKILL.md` (with a `## Gotchas`
and a `## Files` section), and `scripts/` (its own, or cited repo `scripts/...`).**
This is enforced — run the linter:

```bash
python3 scripts/suggest_skills.py --lint        # skill-doctor: must exit 0
python3 scripts/suggest_skills.py --reindex      # refresh _INDEX.md after adding a skill
python3 scripts/suggest_skills.py --scaffold foo # new skill skeleton (md + Gotchas + scripts/)
```

Current operational skills: `ship-nurture` (build+deploy a nurture from a doc),
`audit-location` (read-only dump/map/doc a live GHL location), `gotcha-fixer`
(work the gotcha queue). `learned/*` are auto-extracted notes, not skills.

The `## Gotchas` section is non-negotiable: it is where the gotcha-fixer writes
the lesson from every fixed failure, so a skill without it has nowhere to learn.

## The gotcha loop in practice

1. Something fails. The capture hook logs it (or you do:
   `python3 scripts/gotcha.py log "<what>" --skill <name>`).
2. SessionStart prints `[gotchas] N open …`. Read `.claude/gotchas/OPEN.md`.
3. Invoke the **gotcha-fixer** skill → it dispatches one background agent per
   gotcha to root-cause, patch, append the lesson to the skill's `## Gotchas`,
   and `gotcha.py resolve` it.
4. A recurrence re-opens the same gotcha (signature = id), so fixes that don't
   hold resurface instead of silently rotting.

## Commands vs skills

- **`.claude/commands/*.md`** = user-typed slash commands (`/extract-offer`,
  `/build-sequence`, `/build-campaign-skeleton`, `/a2p-fill-values`). Thin
  entrypoints a human invokes.
- **`.claude/skills/<name>/`** = agent capabilities Claude auto-selects by the
  `description` trigger, carrying scripts + gotchas. The richer, structured unit.

A command can graduate into a skill when it accretes scripts + gotchas worth
enforcing. `/a2p-fill-values` is the prime candidate (it already has
`lib/a2p_values.py` + `scripts/a2p_*.py` behind it).

## Adding to the harness — quick recipes

| You want to… | Do |
|---|---|
| Automate a command you keep typing | check `metrics/skill-candidates.md`; wrap it in `scripts/` or a skill |
| Add a new skill | `suggest_skills.py --scaffold <name>` → fill SKILL.md → `--lint` → `--reindex` |
| Record a footgun | `gotcha.py log "<what>" --skill <name>` (or let the hook catch it) |
| Fix the open gotchas | invoke the `gotcha-fixer` skill |
| Verify harness health | `suggest_skills.py --lint && gotcha.py list` |
