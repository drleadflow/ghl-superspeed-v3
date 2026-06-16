#!/usr/bin/env python3
"""
PostToolUse hook: log every Bash command to a usage ledger for the self-improving harness.

Reads Claude Code hook JSON from stdin, extracts `tool_input.command` and `cwd`,
and appends one JSON line to `.claude/metrics/bash-usage.jsonl`:
    {"ts": "<ISO8601 UTC>", "command": "<cmd>", "cwd": "<cwd>"}

The companion analyzer is scripts/suggest_skills.py, which tallies these lines and
surfaces recurring commands worth turning into scripts/skills/allow-rules.

Usage (wired as a project PostToolUse hook on Bash; not run by hand):
  echo '{"tool_input":{"command":"git status"},"cwd":"/x"}' | python3 .claude/hooks/log-bash-usage.py

Gotchas:
  - Runs on EVERY Bash tool call, so it must be fast and must NEVER block a tool.
  - ALWAYS exits 0, even on malformed/empty stdin or any write error (bare except).
  - Derives the repo root from its own location (.claude/hooks/ -> repo root is two
    levels up), so it works no matter what cwd the hook fires from.
  - Telemetry file (bash-usage.jsonl) is git-ignored; don't rely on it being committed.
"""
import sys


def main() -> None:
    try:
        import json
        import os
        from datetime import datetime, timezone

        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return

        data = json.loads(raw)
        tool_input = data.get("tool_input") or {}
        command = tool_input.get("command")
        if not command:
            return  # nothing useful to log (e.g. non-command Bash payloads)

        cwd = data.get("cwd") or ""

        # repo root = two levels up from .claude/hooks/<this file>
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        metrics_dir = os.path.join(repo_root, ".claude", "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        ledger = os.path.join(metrics_dir, "bash-usage.jsonl")

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "cwd": cwd,
        }
        with open(ledger, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # Never let logging break a tool call.
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
