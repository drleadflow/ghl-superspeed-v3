# Skill Backlog — recommended next automations

Prioritized candidates for new skills/systems, from domain analysis (telemetry is
still sparse — `suggest_skills.py` only surfaces low-signal `sed`/`ghl` so far).
Each, when built, must follow `AUTHORING.md` (md + `## Gotchas` + `## Files` + scripts)
and pass `suggest_skills.py --lint`.

## Built this session (2026-06-16)
- ✅ `audit-location` — read-only dump/flow-map/docx of a live GHL location.
- ✅ `gotcha-fixer` — capture-failure → background-fix loop.
- ✅ skill-doctor lint + folded-YAML/nested-skill reindex fix.

## High value — build next
1. **`onboard-client`** — new client → scaffold `clients/<slug>/` from `_template/`,
   run `check_access.py` + `inventory.py`, capture the location ID into memory
   (`project_client_location_ids`), stub the A2P + offer files. We've onboarded 5+
   clients (IV Wellness, Prestige, AZC, TVAAI, Ritucci) by hand — this is the most
   repeated multi-step human flow. Reuses existing scripts; mostly orchestration.
2. **Promote `/a2p-fill-values` → a `a2p-values` skill.** It already has the parts
   (`lib/a2p_values.py`, `scripts/a2p_scrape.py`, `scripts/a2p_apply.py`,
   `scripts/set_custom_values.py`) and recorded gotchas (memory
   `project_a2p_custom_value_populator`). Wrapping it as a skill gives it a
   `## Gotchas` home and lets the gotcha-fixer maintain it.

## Medium value
3. **`offer-to-campaign`** — chain the three vault commands
   (`/extract-offer` → `/build-sequence` / `/build-campaign-skeleton`) into one
   skill so a Notion offer URL becomes a deployable campaign skeleton in one step.
4. **`vault-lint`** — validate services/offers/clients frontmatter + wikilinks
   (a `vault-lint` slash command already exists in the global set; consider a
   repo-local script so it runs under the `python3 *` allow rule).

## Low value / watch
- `sed` (5×) and `ghl` (4×) are the only telemetry candidates. `sed` is ad-hoc
  text editing — don't allow-rule it (destructive surface). `ghl` is the external
  `ghl-cli`; already a known tool, no wrapper needed.
- The 84× `cd` count is navigation noise, not an automation target.
