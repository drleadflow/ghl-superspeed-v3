---
name: gotcha-fixer
description: "Use when there are open gotchas to fix, when the SessionStart notice says '[gotchas] N open', when the user says 'fix the gotchas / clear the gotcha log / run the gotcha fixer', or right after a deploy/script failure that was captured. Dispatches a background agent per open gotcha to root-cause it, patch the offending script/skill, append the lesson to that skill's Gotchas, and mark it resolved."
---

# Gotcha Fixer — capture → background-fix → resolve

When a known footgun (a "gotcha") bites — a deploy fails, a script throws, an auth
path breaks — it gets captured to the gotcha ledger. This skill works through the
OPEN gotchas, dispatching a background agent per gotcha so fixes happen in
parallel without blocking the main session. Each fix is durable: it patches the
real cause AND records the lesson where the next run will see it.

## How gotchas get captured (you usually don't do this by hand)

- **Auto:** the `.claude/hooks/capture-gotcha.py` PostToolUse hook scans every
  Bash result for high-confidence failure signatures (traceback, "corrupted type",
  "ALL GOOD: False", 401/403, "command not found", …) and logs them, skipping
  documented-benign noise.
- **Manual:** when you hit a footgun the hook can't see, log it:
  `python3 scripts/gotcha.py log "<what failed>" --skill <name> --cmd "<cmd>"`

## Usage — work the open queue

1. **See what's open:** `python3 scripts/gotcha.py list` (or read
   `.claude/gotchas/OPEN.md`). If none, stop — nothing to do.
2. **Get briefs:** `bash .claude/skills/gotcha-fixer/scripts/run-fixer.sh`
   prints one agent-ready brief per open gotcha (or pass an `<id>` for one).
3. **Dispatch one background agent per gotcha.** Use the Agent tool with
   `subagent_type: general-purpose` and `run_in_background: true` so they run in
   parallel and you keep working. Feed each agent the brief plus the template
   below. Dispatch independent gotchas in a single message (parallel).
4. **On completion**, each agent has already patched the code, appended the
   lesson, and called `gotcha.py resolve`. Re-render and confirm the queue
   drained: `python3 scripts/gotcha.py render && python3 scripts/gotcha.py list`.
5. Run `python3 scripts/suggest_skills.py --lint` to confirm any skill you
   touched still has its `## Gotchas`/`## Files` sections + scripts.

### Background-agent prompt template

> You are fixing ONE captured gotcha in the GHL-Superspeed-V3-Better-Version repo.
> Do NOT commit. Make the MINIMAL durable fix.
>
> {paste the brief block for this gotcha here}
>
> Steps: (1) Reproduce/confirm the root cause from the command + repo code — read
> the offending script/skill before editing. (2) Apply the smallest fix that
> prevents recurrence (prefer a guard/validation over a band-aid). (3) Append a
> one-line lesson to the relevant skill's `## Gotchas` section (or to
> `references/engine-schemas.md` if it's an engine/API quirk). (4) If it's a
> deploy-breaker, add a static check to `scripts/preflight_campaign.py`. (5) Mark
> resolved: `python3 scripts/gotcha.py resolve <id> "<one-line how-fixed>" --skill <name>`.
> Report: root cause, the exact fix (files+lines), and where you recorded the lesson.

## Gotchas

- **The fixer's hook is conservative by design.** It only flags a curated
  allow-list and EXCLUDES known-benign noise (e.g. the 3x "REQUEST ERROR:
  Expecting value" every deploy prints). If a real failure isn't auto-captured,
  log it manually — don't widen the hook's signature list without excluding the
  new false positives it will create.
- **A recurrence re-opens a resolved gotcha** (same signature ⇒ same id). If a
  gotcha keeps re-opening, the fix didn't hold — escalate to a structural fix
  (preflight check / engine guard), not another patch.
- **Background agents must not commit** and should touch only the files their
  gotcha implicates — keep them scoped so parallel agents don't collide.
- **Resolve is the contract.** A gotcha is only "done" when the agent calls
  `gotcha.py resolve <id>`; patching code without resolving leaves it OPEN and it
  will be re-dispatched next run.
- **`id` is a content signature**, not a sequence number — don't assume ordering;
  always pass the exact id from `list`/`OPEN.md`.

## Files

- `scripts/run-fixer.sh` — prints agent-ready briefs for open gotchas (wraps
  `scripts/gotcha.py brief`).
- Repo `scripts/gotcha.py` — the ledger CLI (`log` / `list` / `resolve` /
  `render` / `session` / `brief`).
- `.claude/hooks/capture-gotcha.py` — auto-capture hook (Bash PostToolUse).
- `.claude/gotchas/OPEN.md` — the live open queue; `RESOLVED.md` — fix history.
- `.claude/skills/AUTHORING.md` — where the `## Gotchas` section lives in every skill.
