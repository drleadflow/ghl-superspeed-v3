#!/usr/bin/env python3
"""
Gotcha ledger: capture, list, and resolve "gotchas" (known footguns / failures)
so the gotcha-fixer skill can dispatch a background agent to analyze + fix them.

This is the human/CLI face of the gotcha-fixer loop:

    capture (hook or manual)  ->  raw.jsonl  ->  render  ->  OPEN.md
                                                   |
                                  gotcha-fixer skill spawns a background agent
                                                   |
                                  resolve  ->  RESOLVED.md (+ skill ## Gotchas patched)

Storage (.claude/gotchas/):
  raw.jsonl     append-only event ledger (git-ignored; churny)
  OPEN.md       rendered open gotchas (tracked) — what the fixer works through
  RESOLVED.md   rendered resolution log (tracked) — institutional memory

Gotchas are DEDUPED by signature: re-logging the same (message, skill) just bumps
the count + last-seen instead of spamming a new entry. A resolved gotcha that
recurs re-opens (so a fix that didn't hold resurfaces).

Usage:
  python3 scripts/gotcha.py log "<what failed>" [--skill <name>] [--cmd "<cmd>"] [--source hook|manual]
  python3 scripts/gotcha.py list [--all]          # open (default) or all
  python3 scripts/gotcha.py resolve <id> "<how it was fixed>" [--skill <name>]
  python3 scripts/gotcha.py render                # rebuild OPEN.md / RESOLVED.md from the ledger
  python3 scripts/gotcha.py session               # short SessionStart notice (or nothing)
  python3 scripts/gotcha.py brief [<id>]          # agent-ready brief for open gotcha(s)

Gotchas (of this tool):
  - stdlib only; must never raise in a way that blocks a hook (the hook appends
    to raw.jsonl directly and never calls this; this folds the ledger on demand).
  - `id` is a stable 8-char signature of (normalized msg + skill), so the hook and
    a human logging the "same" failure collapse to one entry.
  - render() is idempotent — safe to run every SessionStart.
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOTCHA_DIR = os.path.join(REPO_ROOT, ".claude", "gotchas")
LEDGER = os.path.join(GOTCHA_DIR, "raw.jsonl")
OPEN_MD = os.path.join(GOTCHA_DIR, "OPEN.md")
RESOLVED_MD = os.path.join(GOTCHA_DIR, "RESOLVED.md")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _sig(msg, skill):
    norm = " ".join((msg or "").lower().split())[:200] + "|" + (skill or "")
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:8]


def _append(event):
    os.makedirs(GOTCHA_DIR, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def _load():
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


def _state():
    """Fold the event ledger into id -> record (open/resolved)."""
    state = {}
    for ev in _load():
        gid = ev.get("id")
        if not gid:
            continue
        kind = ev.get("event", "log")
        if kind == "log":
            rec = state.get(gid)
            if rec is None:
                state[gid] = {
                    "id": gid,
                    "msg": ev.get("msg", ""),
                    "skill": ev.get("skill", ""),
                    "cmd": ev.get("cmd", ""),
                    "source": ev.get("source", "manual"),
                    "first": ev.get("ts", ""),
                    "last": ev.get("ts", ""),
                    "count": 1,
                    "status": "open",
                    "resolution": "",
                    "resolved_ts": "",
                }
            else:
                rec["count"] += 1
                rec["last"] = ev.get("ts", rec["last"])
                rec["status"] = "open"  # recurrence re-opens
                if ev.get("msg"):
                    rec["msg"] = ev["msg"]
                if ev.get("cmd"):
                    rec["cmd"] = ev["cmd"]
        elif kind == "resolve":
            rec = state.get(gid)
            if rec:
                rec["status"] = "resolved"
                rec["resolution"] = ev.get("resolution", "")
                rec["resolved_ts"] = ev.get("ts", "")
                if ev.get("skill"):
                    rec["skill"] = ev["skill"]
    return state


def _open(state):
    return [r for r in state.values() if r["status"] == "open"]


def cmd_log(args):
    gid = _sig(args.message, args.skill)
    _append({
        "event": "log", "id": gid, "ts": _now(),
        "msg": args.message, "skill": args.skill or "",
        "cmd": args.cmd or "", "source": args.source,
    })
    render()
    print(gid)


def cmd_resolve(args):
    state = _state()
    if args.id not in state:
        raise SystemExit(f"gotcha: unknown id '{args.id}' (see `gotcha.py list`)")
    _append({
        "event": "resolve", "id": args.id, "ts": _now(),
        "resolution": args.resolution, "skill": args.skill or "",
    })
    render()
    print(f"resolved {args.id}")


def cmd_list(args):
    state = _state()
    recs = list(state.values()) if args.all else _open(state)
    recs.sort(key=lambda r: (r["status"], r["last"]), reverse=True)
    if not recs:
        print("No open gotchas." if not args.all else "No gotchas logged.")
        return
    for r in recs:
        flag = "OPEN " if r["status"] == "open" else "DONE "
        skill = f" [{r['skill']}]" if r["skill"] else ""
        n = f" x{r['count']}" if r["count"] > 1 else ""
        print(f"{flag}{r['id']}{skill}{n}  {r['msg'][:90]}")


def _agent_brief(rec):
    return (
        f"### Gotcha {rec['id']}{' [' + rec['skill'] + ']' if rec['skill'] else ''}\n"
        f"- **What failed:** {rec['msg']}\n"
        + (f"- **Command:** `{rec['cmd']}`\n" if rec['cmd'] else "")
        + f"- **Seen:** {rec['count']}x (first {rec['first'][:19]}, last {rec['last'][:19]}, via {rec['source']})\n"
        "- **Your job:** root-cause it, apply the minimal durable fix to the "
        "offending script/skill, append the one-line lesson to that skill's "
        "`## Gotchas` section, then run "
        f"`python3 scripts/gotcha.py resolve {rec['id']} \"<how you fixed it>\""
        f"{' --skill ' + rec['skill'] if rec['skill'] else ''}`.\n"
    )


def cmd_brief(args):
    state = _state()
    if args.id:
        rec = state.get(args.id)
        if not rec:
            raise SystemExit(f"gotcha: unknown id '{args.id}'")
        recs = [rec]
    else:
        recs = _open(state)
    if not recs:
        print("No open gotchas to brief.")
        return
    print("\n".join(_agent_brief(r) for r in recs))


def render():
    state = _state()
    open_recs = _open(state)
    open_recs.sort(key=lambda r: r["last"], reverse=True)
    resolved = [r for r in state.values() if r["status"] == "resolved"]
    resolved.sort(key=lambda r: r["resolved_ts"], reverse=True)

    os.makedirs(GOTCHA_DIR, exist_ok=True)
    ol = [
        "# Open Gotchas",
        "",
        "_Auto-rendered by `scripts/gotcha.py` from the capture ledger. "
        "The `gotcha-fixer` skill works through these with background agents._",
        "",
    ]
    if not open_recs:
        ol.append("_None open. 🎉_")
    else:
        ol.append("| id | skill | seen | what failed |")
        ol.append("|---|---|---:|---|")
        for r in open_recs:
            safe_msg = r["msg"][:120].replace("|", "\\|")
            ol.append(f"| `{r['id']}` | {r['skill'] or '—'} | {r['count']}x | {safe_msg} |")
    with open(OPEN_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(ol) + "\n")

    rl = [
        "# Resolved Gotchas",
        "",
        "_Institutional memory: how past footguns were fixed. "
        "A recurrence re-opens the gotcha automatically._",
        "",
    ]
    if not resolved:
        rl.append("_Nothing resolved yet._")
    else:
        for r in resolved:
            skill = f" [{r['skill']}]" if r["skill"] else ""
            rl.append(f"- **{r['id']}**{skill} ({r['resolved_ts'][:10]}): "
                      f"{r['msg'][:100]} → {r['resolution']}")
    with open(RESOLVED_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rl) + "\n")


def cmd_render(args):
    render()
    print(f"rendered {OPEN_MD} + {RESOLVED_MD}")


def cmd_session(args):
    open_recs = _open(_state())
    if not open_recs:
        return
    n = len(open_recs)
    word = "gotcha" if n == 1 else "gotchas"
    ids = ", ".join(r["id"] for r in open_recs[:4])
    print(f"[gotchas] {n} open {word} ({ids}) — run the gotcha-fixer skill to "
          "dispatch background fixes. See .claude/gotchas/OPEN.md")


def main():
    ap = argparse.ArgumentParser(description="Gotcha capture/resolve ledger.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("log", help="log a gotcha")
    p.add_argument("message")
    p.add_argument("--skill", default="")
    p.add_argument("--cmd", default="")
    p.add_argument("--source", default="manual", choices=["manual", "hook"])
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("resolve", help="mark a gotcha resolved")
    p.add_argument("id")
    p.add_argument("resolution")
    p.add_argument("--skill", default="")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("list", help="list gotchas")
    p.add_argument("--all", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("brief", help="agent-ready brief for open gotcha(s)")
    p.add_argument("id", nargs="?", default="")
    p.set_defaults(func=cmd_brief)

    sub.add_parser("render", help="rebuild OPEN.md/RESOLVED.md").set_defaults(func=cmd_render)
    sub.add_parser("session", help="short SessionStart notice").set_defaults(func=cmd_session)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
