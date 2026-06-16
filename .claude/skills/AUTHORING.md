# Skill-Authoring Convention

How to write skills in this repo so the self-improving harness can register them
and so future-us doesn't trip over the same footguns. The `--scaffold` mode of
`scripts/suggest_skills.py` produces this structure for you.

## A skill is a DIRECTORY, not a file

`.claude/skills/<name>/` holds more than `SKILL.md`. Use progressive disclosure:
keep `SKILL.md` lean and point to the rest, which only gets loaded on demand.

```
.claude/skills/<name>/
  SKILL.md        # lean entrypoint: frontmatter + how-to + gotchas + file map
  references/     # deep docs (API quirks, long examples) loaded only when needed
  scripts/        # helper executables the skill calls
  assets/         # optional: templates, fixtures, sample data
```

## SKILL.md frontmatter

YAML block at the very top:

```yaml
---
name: my-skill
description: Use when the user asks to <trigger phrasing>. Be specific — this is
  the matcher that decides when the skill fires.
---
```

- `name` — directory-safe identifier.
- `description` — **when-to-use** trigger phrasing, not a summary of internals.

## Required sections

Every `SKILL.md` MUST include:

- **`## Gotchas`** — known footguns, edge cases, and things that bit us. This is
  non-negotiable. A skill without recorded gotchas will repeat past mistakes.
- **`## Files`** — point at `references/` and `scripts/` so readers know where the
  depth lives.

Recommended: a `## Usage` section with the high-level invocation/steps.

## Keep SKILL.md lean

If a section grows past a screen, move it to `references/<topic>.md` and link it.
The entrypoint should be skimmable; detail loads on demand.

## Registering

Run `python3 scripts/suggest_skills.py --reindex` after adding a skill to refresh
`.claude/skills/_INDEX.md` (the registry of all scripts + skills).
