---
name: audit-location
description: "Use when the user asks to audit, document, dump, map, or analyze the workflows in an existing GHL location / sub-account. Triggers: 'what's in this account', 'dump the workflows for <loc>', 'build a flow map / docx report for <location>', 'audit <client>'s automations'. READ-ONLY — never writes to GHL."
---

# Audit Location — live GHL location → dump + analytics + flow map + docx

Document any live GHL location in one pass. This wraps the repo's four read-only
"dumper" scripts in the correct dependency order. It NEVER writes to GHL — every
underlying call is a GET. Output is files on disk under `--out-dir`.

All scripts run under the `Bash(python3 *)` allow rule (no prompts). Node is
needed only for the optional `.docx` step. Repo: GHL-Superspeed-V3-Better-Version.

## Usage

The fast path is the bundled wrapper, which runs all four phases in order and
stops only if the structural dump (phase 1) fails:

```bash
python3 .claude/skills/audit-location/scripts/audit_location.py <loc> \
    --out-dir /tmp/audit-<client> --label "<Client Name>"
# flags: --no-docx (skip Node), --no-analytics, --refresh-token/--id-token
```

Or run the phases by hand (what the wrapper does — use these to debug a single
phase or skip steps):

### Phase 0 — Resolve the location ID (no API call)
- If given a location ID, use it.
- If given a name/short code, check memory `project_client_location_ids`
  (IV Wellness, Prestige, AZC, TVAAI, Ritucci) and the `clients/` folder.
- If still unknown, ask once. Then sanity-check auth:
  `python3 scripts/check_access.py <loc>` (exit 2 = auth broken, see Gotchas).

### Phase 1 — Dump (structural; REQUIRED, all else depends on it)
```bash
python3 scripts/dump_workflows.py <loc> --out-dir <dir>
# optional: --limit N (first N workflows, debug) --refresh-token/--id-token
```
Writes `<dir>/_index.json`, `<dir>/_index.md`, and per-workflow
`<dir>/workflows/<slug>__<id8>.{json,triggers.json,md}` (folders, triggers,
every step with email/SMS body previews).

### Phase 2 — Analytics merge (enrollment counts; optional)
```bash
python3 scripts/dump_workflow_analytics.py <loc> --out-dir <dir>
# same --out-dir as phase 1 (it reads _index.json); optional --batch-size 10
```
Writes `<dir>/_analytics.json` + `_analytics.md` (lifetime/finished/active
enrollments, top-20, zero-traffic list, per-folder breakdown, location error
count). Per-step funnel drop-off is NOT captured (see Gotchas).

### Phase 3 — Flow map (static cross-workflow graph; no API calls)
```bash
python3 scripts/build_flow_map.py <dir>
# positional out-dir, NOT --out-dir; reads the phase-1 dump only
```
Writes `<dir>/_flows.json` + `_flows.md` (entry points, `add_to_workflow`
chains, tag-mediated handoffs, orphans, per-workflow in/out connections).

### Phase 4 — Docx report (optional; needs Node)
```bash
node scripts/build_workflow_docx.js <dir> --label "<Client Name>"
```
Reads `_index.json` (+ `_flows.json`/`_analytics.json` if present) and writes
`<dir>/<label-slug>-Workflow-Documentation.docx` — cover, account totals,
top-20 table, linked index, and a per-workflow section with triggers + steps.

## Gotchas

- **READ-ONLY.** Every wrapped script issues GETs only — no POST/PUT/DELETE.
  Safe to run repeatedly; re-running overwrites the prior dump in `--out-dir`.
- **Auth = a Firebase token, not the MCP / ghl-cli path.** Pass
  `--refresh-token` (AMf-... refresh token) or `--id-token` (fresh ~1h id_token),
  or set `$GHL_FIREBASE_REFRESH_TOKEN` / `$GHL_FIREBASE_TOKEN`. `inventory.py` /
  `check_access.py` auto-load those two vars from project `.env` and
  `~/.env.secrets`; `dump_workflows.py` does NOT auto-load — pass the flag or
  export the env var before running it (the wrapper forwards whatever env it sees).
- **Non-DLF agency → pass the client's OWN refresh token inline.** For Ritucci
  (separate Agency) and any non-DLF sub-account, an ambient DLF refresh token
  wins silently and you read the wrong/no data. Use `--refresh-token` explicitly.
- **Phase order is fixed.** Analytics (2), flow map (3), and docx (4) all read
  phase 1's `_index.json` / `workflows/*.json`. Run `dump_workflows.py` first or
  they error / no-op. The wrapper enforces this and aborts only if phase 1 fails.
- **Flag shape differs per script.** `dump_workflows.py` /
  `dump_workflow_analytics.py` take `--out-dir <dir>`; `build_flow_map.py` and
  `build_workflow_docx.js` take the dir as a **positional** arg. Easy to mix up
  by hand — the wrapper handles it.
- **Analytics can 401 independently of the dump.** The enroll-stats endpoint
  also requires `version` + an `Origin`/`Referer` from the workflows-app
  subdomain (handled in-script). A valid token can still get 0/N stats; that
  phase is non-fatal in the wrapper — the dump, flow map and docx still build.
- **Per-step funnel drop-off is NOT in the analytics dump.** Only workflow-level
  totals (enrolled / finished / active). The GHL UI loads per-step funnel data
  from an un-mapped route inside the builder iframe. To add it, sniff one
  workflow's Enrollment History tab live and extend `dump_workflow_analytics.py`.
- **Docx step is Node, not Python**, and the `docx` lib is resolved from a
  hardcoded global path inside `build_workflow_docx.js`
  (`/Users/bleupreneur/.npm-global/lib/node_modules/docx`). If `node` is absent
  or that module path is wrong, the docx step fails — verify it before promising
  a `.docx`; the rest of the audit is unaffected (use `--no-docx`).
- **Large locations = large output.** A dump writes one `.json` + `.triggers.json`
  + `.md` per workflow, with full email HTML inlined. For an account with many
  workflows the dir can be large and the docx many pages — point `--out-dir` at
  `/tmp` and skim `_index.md` / `_analytics.md` rather than reading every file.

## Files

- `scripts/audit_location.py` — the convenience wrapper (this skill's only own
  script). Runs the four phases below in dependency order; phase 1 is fatal,
  2-4 are non-fatal.
- Repo scripts it orchestrates (the read-only dumper family, all in `scripts/`):
  - `dump_workflows.py` — phase 1, structural dump (`_index.*` + `workflows/*`).
  - `dump_workflow_analytics.py` — phase 2, enrollment analytics merge.
  - `build_flow_map.py` — phase 3, static cross-workflow flow map.
  - `build_workflow_docx.js` — phase 4, `.docx` report (Node).
  - `check_access.py` — phase 0 auth/readiness probe (optional pre-check).
  - `inventory.py` / `ghl_pipelines.py` — sibling read-only views (folder/CV
    inventory; pipelines + stage IDs) if the audit needs them.
