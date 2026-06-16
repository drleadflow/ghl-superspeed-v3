# Superspeed Vault

Business knowledge base for the GHL Superspeed v3 campaign engine.

This vault holds the **what** and **why** behind the campaigns. The Python engine (`lib/`, `campaigns/*.py`) is the **how**, sitting in the same folder.

## Layout

```
GHL-Superspeed-V3-Better-Version/   ← Obsidian vault + git repo (one and the same)
  business/        DLF positioning, brand voice, copy defaults     [vault]
  services/        Service catalog                                 [vault]
  offers/          Offers — structure, pricing, deliverables       [vault]
  clients/         Per-client knowledge (currently _template/ only)[vault]
  references/      GHL API quirks and reusable workflow patterns   [vault]
  campaigns/       MIXED — *.py campaign code AND _index.md (vault)
  templates/       MIXED — blueprints.json (engine) AND *.md (vault)
  lib/             Python engine                                   [code]
  scripts/         Helper scripts                                  [code]
  tests/           Test suite                                      [code]
  CLAUDE.md, README.md, .gitignore, .github/                       [code]
```

## What does NOT live here

- Personal context (me, team, priorities) — that's in Bleu's vault
- Session handoffs / daily notes / decision logs — also Bleu
- Real client data — wait until the system is dialed in against `_template`

## Plugin config notes

Code and knowledge share the same root, so plugins need a bit of guidance:

- **Smart Connections** → Settings → Excluded folders → add `lib`, `scripts`, `tests`, `.github`, `__pycache__` so it doesn't embed Python source
- **Templater** → Template folder location → `templates` (will see both engine `blueprints.json` and the `.md` templates — only the `.md` files are usable as Templater templates)
- **Git** → operates on the single repo root; both code and vault commits land in the same history

## How to add knowledge

- **New service** → copy `services/_template.md` → fill in frontmatter → save as `services/<name>.md`
- **New offer** → same pattern with `offers/_template.md`
- **New client** (after system is perfected) → duplicate `clients/_template/` → rename to client slug
- **Campaign documentation** → add a row to `campaigns/_index.md` with links to relevant services/offers

## Linking

Use Obsidian wikilinks: `[[services/onboarding-call]]`, `[[offers/audit-package]]`. They keep the graph navigable as the vault grows.
