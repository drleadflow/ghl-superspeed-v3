#!/usr/bin/env python3
"""
Self-improving harness analyzer: surface recurring shell commands worth automating.

Reads the usage ledger written by .claude/hooks/log-bash-usage.py
(.claude/metrics/bash-usage.jsonl) and tallies command SIGNATURES (program +
first subcommand, args/paths/IDs/flags stripped). Commands that recur past a
threshold and aren't already automated become candidates: an allow-rule, a
wrapper script, or a full skill.

Usage:
  python3 scripts/suggest_skills.py [--threshold N]   # write skill-candidates.md
  python3 scripts/suggest_skills.py --session          # short SessionStart notice
  python3 scripts/suggest_skills.py --reindex          # regenerate .claude/skills/_INDEX.md
  python3 scripts/suggest_skills.py --lint             # skill-doctor: enforce script+md+gotchas
  python3 scripts/suggest_skills.py --scaffold <name>  # create a new skill skeleton

Outputs:
  .claude/metrics/skill-candidates.md   table of candidates (default mode)
  .claude/skills/_INDEX.md              registry of scripts + skills (--reindex)
  .claude/skills/<name>/...             scaffolded skill (--scaffold)

Gotchas:
  - SessionStart calls this with --session; it MUST print nothing when there are
    no candidates over threshold, and at most ~5 lines when there are.
  - Signature normalization is deliberately dumb/deterministic: leading program,
    plus first bare-word subcommand for known multi-verb tools, everything else
    stripped. Tune KNOWN_MULTI_VERB / IGNORE rather than adding cleverness.
  - "Already automated" detection globs scripts/*.py, .claude/skills/*/, and the
    allow-rules in .claude/settings*.json — keep those paths in sync if they move.
  - stdlib only; no third-party deps.
"""
import argparse
import glob
import json
import os
import re
from datetime import datetime, timezone

# repo root = one level up from scripts/<this file>
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS_DIR = os.path.join(REPO_ROOT, ".claude", "metrics")
LEDGER = os.path.join(METRICS_DIR, "bash-usage.jsonl")
CANDIDATES_MD = os.path.join(METRICS_DIR, "skill-candidates.md")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
SKILLS_DIR = os.path.join(REPO_ROOT, ".claude", "skills")
INDEX_MD = os.path.join(SKILLS_DIR, "_INDEX.md")
SETTINGS_FILES = [
    os.path.join(REPO_ROOT, ".claude", "settings.json"),
    os.path.join(REPO_ROOT, ".claude", "settings.local.json"),
]

DEFAULT_THRESHOLD = 3

# Trivial / builtin commands we never suggest automating.
IGNORE = {
    "ls", "cd", "echo", "cat", "pwd", "find", "stat", "grep", "head", "tail",
    "mkdir", "rm", "mv", "cp", "source", "which", "touch", "true", "false",
    "export", "set", "test",
}

# Tools whose first subcommand is meaningful (verb-style CLIs).
KNOWN_MULTI_VERB = {
    "git", "npm", "npx", "pnpm", "yarn", "gh", "docker", "kubectl", "cargo",
    "go", "pip", "pip3", "brew", "terraform", "vercel", "wrangler", "aws",
}

# Interpreters where the meaningful unit is the script being run.
INTERPRETERS = {"python", "python3", "node", "bash", "sh", "ruby", "deno"}

_FLAG = re.compile(r"^-")
_URL = re.compile(r"^[a-z]+://", re.I)
_LOOKS_LIKE_PATH = re.compile(r"[/\\]")
_LOOKS_LIKE_ID = re.compile(r"[0-9]")


def _strip_quotes_and_pipes(command):
    """Collapse the command to its first pipeline segment, dropping env-var
    prefixes (FOO=bar cmd). Returns a best-effort token list."""
    # Take only the first segment of a pipe/&&/; chain — that's the "real" verb.
    segment = re.split(r"\s*(?:\|\||\||&&|;)\s*", command.strip(), maxsplit=1)[0]
    # Remove quoted strings entirely so their contents never become tokens.
    segment = re.sub(r'"[^"]*"', " ", segment)
    segment = re.sub(r"'[^']*'", " ", segment)
    tokens = segment.split()
    # Drop leading VAR=value env assignments.
    while tokens and "=" in tokens[0] and not tokens[0].startswith("-"):
        tokens.pop(0)
    return tokens


def signature(command):
    """Normalize a raw command to a stable signature.

    Examples:
      git commit -m "x"                              -> git commit
      python3 scripts/dump_workflows.py 9uog --out   -> python3 scripts/dump_workflows.py
      gh api repos/foo/bar                           -> gh api
      curl -s https://x | jq .                       -> curl
    """
    if not command or not command.strip():
        return ""
    tokens = _strip_quotes_and_pipes(command)
    if not tokens:
        return ""

    prog = os.path.basename(tokens[0]) if _LOOKS_LIKE_PATH.search(tokens[0]) else tokens[0]
    rest = tokens[1:]

    def first_bare(args):
        for a in args:
            if _FLAG.match(a) or _URL.match(a) or "=" in a:
                continue
            return a
        return None

    if prog in INTERPRETERS:
        # python3 scripts/foo.py  -> keep the script path (the meaningful unit)
        target = first_bare(rest)
        if target and _LOOKS_LIKE_PATH.search(target):
            return f"{prog} {target}"
        if target and not _LOOKS_LIKE_ID.search(target):
            # e.g. `npm run build` style isn't here, but `node server` -> node server
            return f"{prog} {target}"
        return prog

    if prog in KNOWN_MULTI_VERB:
        verb = first_bare(rest)
        if verb and not _LOOKS_LIKE_PATH.search(verb) and not _LOOKS_LIKE_ID.search(verb):
            return f"{prog} {verb}"
        return prog

    return prog


def load_entries():
    """Yield parsed ledger entries; skip unreadable lines."""
    if not os.path.exists(LEDGER):
        return []
    out = []
    with open(LEDGER, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def existing_automation():
    """Set of signatures already covered by a script, skill, or allow-rule."""
    covered = set()

    # scripts/*.py  -> "python3 scripts/<name>.py" and bare "scripts/<name>.py"
    for p in glob.glob(os.path.join(SCRIPTS_DIR, "*.py")):
        rel = os.path.relpath(p, REPO_ROOT)
        covered.add(f"python3 {rel}")
        covered.add(f"python {rel}")

    # allow-rules in settings*.json  -> derive signatures from Bash(...) entries
    for sf in SETTINGS_FILES:
        if not os.path.exists(sf):
            continue
        try:
            with open(sf, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
            rules = (cfg.get("permissions") or {}).get("allow") or []
            for rule in rules:
                m = re.match(r"^Bash\((.*)\)$", rule)
                if not m:
                    continue
                inner = m.group(1).strip()
                # Drop trailing wildcard markers Claude uses (:* or *).
                inner = inner.rstrip("*").rstrip(":").strip()
                sig = signature(inner)
                if sig:
                    covered.add(sig)
        except Exception:
            continue

    return covered


def existing_skill_names():
    if not os.path.isdir(SKILLS_DIR):
        return set()
    return {
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d)) and not d.startswith("_")
    }


def tally(entries):
    """Map signature -> {count, first, last}."""
    stats = {}
    for e in entries:
        cmd = e.get("command") or ""
        sig = signature(cmd)
        if not sig:
            continue
        prog = sig.split()[0]
        if prog in IGNORE:
            continue
        ts = e.get("ts") or ""
        s = stats.setdefault(sig, {"count": 0, "first": ts, "last": ts})
        s["count"] += 1
        if ts:
            if not s["first"] or ts < s["first"]:
                s["first"] = ts
            if not s["last"] or ts > s["last"]:
                s["last"] = ts
    return stats


def suggested_action(sig, info):
    """Heuristic: allow-rule | wrap in scripts/ | build skill."""
    prog = sig.split()[0]
    # Already an interpreter pointing at a script -> it's a flow that varies a lot.
    if prog in INTERPRETERS and len(sig.split()) > 1:
        return "build skill"
    # Multi-verb tool with a stable verb and high frequency -> wrap the flow.
    if prog in KNOWN_MULTI_VERB and info["count"] >= DEFAULT_THRESHOLD * 2:
        return "wrap in scripts/"
    # Default: a single repeated raw command -> just allow it.
    return "add allow-rule"


def candidates(threshold):
    entries = load_entries()
    stats = tally(entries)
    covered = existing_automation()
    rows = []
    for sig, info in stats.items():
        if info["count"] < threshold:
            continue
        if sig in covered:
            continue
        rows.append((sig, info))
    rows.sort(key=lambda r: r[1]["count"], reverse=True)
    return rows


def _short_ts(ts):
    return ts[:19] + "Z" if ts and len(ts) >= 19 else (ts or "?")


def write_candidates(threshold):
    rows = candidates(threshold)
    lines = [
        "# Skill / Automation Candidates",
        "",
        f"_Generated by `scripts/suggest_skills.py` (threshold {threshold}) — "
        f"{datetime.now(timezone.utc).isoformat()}_",
        "",
        "Recurring shell commands detected by the self-improving harness that are "
        "not yet wrapped in a script, skill, or allow-rule.",
        "",
    ]
    if not rows:
        lines.append("_No candidates over threshold yet._")
    else:
        lines.append("| Signature | Count | Last seen | Suggested action |")
        lines.append("|---|---:|---|---|")
        for sig, info in rows:
            lines.append(
                f"| `{sig}` | {info['count']} | {_short_ts(info['last'])} | "
                f"{suggested_action(sig, info)} |"
            )
    os.makedirs(METRICS_DIR, exist_ok=True)
    with open(CANDIDATES_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return rows


def session_notice(threshold):
    rows = candidates(threshold)
    if not rows:
        return  # print NOTHING when there's nothing to surface
    n = len(rows)
    top = ", ".join(f"`{sig}` ({info['count']})" for sig, info in rows[:3])
    word = "command" if n == 1 else "commands"
    print(f"[harness] {n} recurring {word} ready to automate — see "
          f".claude/metrics/skill-candidates.md")
    print(f"[harness] top: {top}")


# --------------------------------------------------------------------------- #
# Registry / index
# --------------------------------------------------------------------------- #

def _docstring_first_line(path):
    """Return the first non-empty line of a Python module docstring, or ''."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
    except Exception:
        return ""
    m = re.search(r'(?s)(?:^|\n)\s*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', src)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _skill_frontmatter(skill_md):
    """Extract name + description from a SKILL.md YAML frontmatter block.

    Handles both inline scalars (`description: foo`) and folded/literal block
    scalars (`description: >` / `description: |` followed by indented lines) —
    ship-nurture uses a folded block, which the naive version captured as ">".
    """
    name = desc = ""
    try:
        with open(skill_md, "r", encoding="utf-8") as fh:
            text = fh.read()
    except Exception:
        return name, desc
    m = re.match(r"(?s)^---\n(.*?)\n---", text)
    block = m.group(1) if m else text
    lines = block.splitlines()
    for i, line in enumerate(lines):
        nm = re.match(r"\s*name\s*:\s*(.+)", line)
        dm = re.match(r"\s*description\s*:\s*(.*)", line)
        if nm and not name:
            name = nm.group(1).strip().strip("\"'")
        if dm and not desc:
            val = dm.group(1).strip()
            if val in (">", "|", ">-", "|-", ">+", "|+"):
                # Folded/literal block scalar: gather subsequent indented lines.
                base_indent = len(line) - len(line.lstrip())
                collected = []
                for nxt in lines[i + 1:]:
                    if not nxt.strip():
                        continue
                    indent = len(nxt) - len(nxt.lstrip())
                    if indent <= base_indent:
                        break
                    collected.append(nxt.strip())
                desc = " ".join(collected).strip().strip("\"'")
            else:
                desc = val.strip("\"'")
    return name, desc


def discover_skills():
    """Find every skill in SKILLS_DIR as (relative_label, SKILL.md path).

    A skill is any directory containing a SKILL.md. Top-level dirs without a
    SKILL.md (e.g. `learned/`) are treated as CATEGORIES — we descend one level
    and surface each child skill as `category/child`. Dirs starting with `_`
    (the index, scaffolding) are skipped.
    """
    out = []
    if not os.path.isdir(SKILLS_DIR):
        return out
    for top in sorted(os.listdir(SKILLS_DIR)):
        if top.startswith("_") or top.startswith("."):
            continue
        top_path = os.path.join(SKILLS_DIR, top)
        if not os.path.isdir(top_path):
            continue
        top_md = os.path.join(top_path, "SKILL.md")
        if os.path.exists(top_md):
            out.append((top, top_md))
            continue
        # Category dir: look one level down for child skills.
        for child in sorted(os.listdir(top_path)):
            child_md = os.path.join(top_path, child, "SKILL.md")
            if os.path.exists(child_md):
                out.append((f"{top}/{child}", child_md))
    return out


# --------------------------------------------------------------------------- #
# Lint / skill-doctor — enforce the script+md+gotchas house rule
# --------------------------------------------------------------------------- #

def lint_skills():
    """Check every skill obeys the repo convention (.claude/skills/AUTHORING.md):
    a SKILL.md with `## Gotchas` and `## Files`, plus a `scripts/` directory.

    Returns (violations, ok_count). Each violation is (skill_label, problem).
    """
    violations = []
    skills = discover_skills()
    checked = 0
    for rel, skill_md in skills:
        skill_dir = os.path.dirname(skill_md)
        try:
            with open(skill_md, "r", encoding="utf-8") as fh:
                text = fh.read()
        except Exception:
            violations.append((rel, "SKILL.md unreadable"))
            continue
        # Auto-extracted `learned/` notes are captured knowledge, not operational
        # skills — exempt from the full script+md+gotchas structure entirely.
        is_learned = "/learned/" in skill_md.replace(os.sep, "/") or \
            bool(re.search(r"(?im)^origin\s*:\s*auto-extracted", text))
        if is_learned:
            continue
        checked += 1
        fm_name, desc = _skill_frontmatter(skill_md)
        if not desc or desc in (">", "|"):
            violations.append((rel, "missing/empty frontmatter description"))
        if not re.search(r"(?im)^#+\s*Gotchas\b", text):
            violations.append((rel, "no `## Gotchas` section (required)"))
        if not re.search(r"(?im)^#+\s*Files\b", text):
            violations.append((rel, "no `## Files` section (required)"))
        # Script requirement: satisfied by an own `scripts/` dir OR by citing
        # repo-level `scripts/...` in SKILL.md (ship-nurture reuses shared tools).
        has_own_scripts = os.path.isdir(os.path.join(skill_dir, "scripts"))
        cites_scripts = bool(re.search(r"scripts/[\w.-]+", text))
        if not has_own_scripts and not cites_scripts:
            violations.append((rel, "no scripts: needs a `scripts/` dir or cited `scripts/...` tools"))
    return violations, checked


def lint_report():
    violations, total = lint_skills()
    if not violations:
        print(f"skill-doctor: {total} skill(s) checked — all pass "
              "(SKILL.md + Gotchas + Files + scripts/).")
        return 0
    print(f"skill-doctor: {len(violations)} issue(s) across {total} skill(s):\n")
    by_skill = {}
    for skill, problem in violations:
        by_skill.setdefault(skill, []).append(problem)
    for skill in sorted(by_skill):
        print(f"  {skill}:")
        for problem in by_skill[skill]:
            print(f"    - {problem}")
    return 1


def reindex():
    lines = [
        "# Automation Registry",
        "",
        "_Auto-generated by `scripts/suggest_skills.py --reindex`. "
        "Lists every wrapper script and skill so we know what already exists._",
        "",
        "> Recurring commands not yet automated are tracked separately in "
        "`.claude/metrics/skill-candidates.md` (run `suggest_skills.py`).",
        "",
        "## Scripts (`scripts/*.py`)",
        "",
        "| Script | Purpose |",
        "|---|---|",
    ]
    for p in sorted(glob.glob(os.path.join(SCRIPTS_DIR, "*.py"))):
        name = os.path.basename(p)
        purpose = _docstring_first_line(p) or "_(no docstring)_"
        lines.append(f"| `scripts/{name}` | {purpose} |")

    lines += ["", "## Skills (`.claude/skills/*/`)", ""]
    skills = discover_skills()
    if not skills:
        lines.append("_No skills yet._")
    else:
        lines.append("| Skill | Description |")
        lines.append("|---|---|")
        for rel, skill_md in skills:
            fm_name, desc = _skill_frontmatter(skill_md)
            lines.append(f"| `{rel}` | {desc or fm_name or rel} |")

    os.makedirs(SKILLS_DIR, exist_ok=True)
    with open(INDEX_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return INDEX_MD


# --------------------------------------------------------------------------- #
# Scaffold
# --------------------------------------------------------------------------- #

SKILL_TEMPLATE = """---
name: {name}
description: TODO — when-to-use trigger phrasing (e.g. "Use when the user asks to ...").
---

# {title}

TODO: one-paragraph summary of what this skill does. Keep SKILL.md lean —
push deep docs into `references/` and helper executables into `scripts/`
(progressive disclosure: load detail only when needed).

## Usage

TODO: how to invoke / the high-level steps.

## Gotchas

- TODO: known footguns, edge cases, and things that bit us. (Required section —
  see .claude/skills/AUTHORING.md.)

## Files

- `references/` — deep docs loaded on demand.
- `scripts/` — helper executables for this skill.
"""


def scaffold(name):
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower()
    if not safe:
        raise SystemExit("scaffold: invalid skill name")
    skill_dir = os.path.join(SKILLS_DIR, safe)
    refs = os.path.join(skill_dir, "references")
    scr = os.path.join(skill_dir, "scripts")
    for d in (skill_dir, refs, scr):
        os.makedirs(d, exist_ok=True)
    for d in (refs, scr):
        keep = os.path.join(d, ".gitkeep")
        if not os.path.exists(keep):
            open(keep, "w").close()
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md):
        title = safe.replace("-", " ").replace("_", " ").title()
        with open(skill_md, "w", encoding="utf-8") as fh:
            fh.write(SKILL_TEMPLATE.format(name=safe, title=title))
    return skill_dir


def main():
    ap = argparse.ArgumentParser(description="Self-improving harness analyzer.")
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                    help=f"min occurrences to flag (default {DEFAULT_THRESHOLD})")
    ap.add_argument("--session", action="store_true",
                    help="print a short SessionStart notice (or nothing)")
    ap.add_argument("--reindex", action="store_true",
                    help="regenerate .claude/skills/_INDEX.md")
    ap.add_argument("--lint", action="store_true",
                    help="skill-doctor: verify every skill has md + Gotchas + Files + scripts/")
    ap.add_argument("--scaffold", metavar="NAME",
                    help="create a new skill skeleton at .claude/skills/NAME/")
    args = ap.parse_args()

    if args.scaffold:
        path = scaffold(args.scaffold)
        print(path)
        return
    if args.lint:
        raise SystemExit(lint_report())
    if args.reindex:
        path = reindex()
        print(path)
        return
    if args.session:
        session_notice(args.threshold)
        return

    rows = write_candidates(args.threshold)
    print(f"Wrote {CANDIDATES_MD} ({len(rows)} candidate(s) over threshold "
          f"{args.threshold}).")


if __name__ == "__main__":
    main()
