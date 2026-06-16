# PRIMER.md

Session handoff document. Update at the end of a session.

## Active Project
GHL Superspeed v3 campaign engine + its self-improving agent harness.

## Last Completed
Harness audit + setup (2026-06-16):
- Built the **gotcha-fixer loop**: `capture-gotcha.py` hook → `scripts/gotcha.py`
  ledger (`.claude/gotchas/OPEN.md`) → `gotcha-fixer` skill dispatches a
  background agent per failure to patch + record + resolve.
- Added **skill-doctor** lint (`suggest_skills.py --lint`) enforcing
  md + `## Gotchas` + `## Files` + scripts; fixed `--reindex` (folded YAML +
  nested `learned/` skills).
- New **`audit-location`** skill (read-only dump/flow-map/docx of a live location).
- Docs: `.claude/HARNESS.md` (the harness map), CLAUDE.md + README harness
  sections, memory (`project_gotcha_fixer_system`, updated `project_harness_scripts`).
- Cleanup: removed stray `.claude/skills/.claude/`; gitignored `.env.bak*`.

## Next Steps
- Nothing committed yet (per house rule). Review + commit when ready.
- Build backlog skills as needed — see `.claude/skills/_BACKLOG.md` (top pick:
  `onboard-client`).

## Open Blockers
None.

## Session Notes
- `audit-location` records a real latent gotcha: `build_workflow_docx.js`
  hardcodes a `node_modules/docx` path. Run the `gotcha-fixer` skill (or log it)
  if a `.docx` build fails on another machine.
- Harness health check: `python3 scripts/suggest_skills.py --lint && python3 scripts/gotcha.py list`.
