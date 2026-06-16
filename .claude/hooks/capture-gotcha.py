#!/usr/bin/env python3
"""
PostToolUse hook (Bash): auto-capture high-confidence command FAILURES as gotchas.

Reads Claude Code hook JSON from stdin, scans the Bash tool_response for known
failure signatures, and appends a `log` event to .claude/gotchas/raw.jsonl. The
gotcha-fixer skill later dispatches a background agent per open gotcha to fix it.

This is intentionally CONSERVATIVE: it only fires on a curated allow-list of
genuinely-bad signatures, and it EXCLUDES known-benign noise (e.g. the 3x
"REQUEST ERROR: Expecting value" that every deploy prints harmlessly). Better to
miss a gotcha than to spam the ledger with false positives.

Gotchas:
  - Runs on EVERY Bash call → must be fast and must ALWAYS exit 0 (bare except).
  - Does NOT render OPEN.md (that's deferred to `gotcha.py render`/`session`),
    so the hot path stays a single append.
  - Dedup is by signature (signature pattern + command program), so the same
    failure on the same command collapses to one entry instead of spamming.
  - Telemetry file (raw.jsonl) is git-ignored; the rendered OPEN.md is tracked.
"""
import sys


# (pattern substring, human label). Matched case-insensitively against output.
FAILURE_SIGNATURES = [
    ("traceback (most recent call last)", "Python traceback"),
    ("corrupted type", "GHL save API: corrupted action type"),
    ("steps failed", "deploy: steps failed"),
    ("all good: false", "deploy_verify: ALL GOOD False"),
    ("0-step workflow", "deploy: 0-step workflow"),
    ("no trigger", "deploy: workflow has no trigger"),
    ("auth failed", "GHL auth failed"),
    ("401 unauthorized", "HTTP 401 Unauthorized"),
    ("403 forbidden", "HTTP 403 Forbidden"),
    ("command not found", "shell: command not found"),
    ("modulenotfounderror", "Python ModuleNotFoundError"),
    ("permission denied", "permission denied"),
]

# Substrings that mark output as benign even if a signature also matched.
BENIGN_EXCLUDES = [
    "request error: expecting value",   # documented benign deploy noise
    "warns on internal_",               # validate_campaign benign warning
]


def main():
    try:
        import json
        import os
        import hashlib
        from datetime import datetime, timezone

        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return
        data = json.loads(raw)

        tool_input = data.get("tool_input") or {}
        command = (tool_input.get("command") or "")[:300]

        resp = data.get("tool_response")
        if isinstance(resp, dict):
            text = " ".join(str(resp.get(k, "")) for k in ("stdout", "stderr", "output", "error"))
        else:
            text = str(resp or "")
        haystack = text.lower()
        if not haystack.strip():
            return

        if any(b in haystack for b in BENIGN_EXCLUDES):
            return

        matched = None
        for needle, label in FAILURE_SIGNATURES:
            if needle in haystack:
                matched = label
                break
        if not matched:
            return

        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        gotcha_dir = os.path.join(repo_root, ".claude", "gotchas")
        os.makedirs(gotcha_dir, exist_ok=True)
        ledger = os.path.join(gotcha_dir, "raw.jsonl")

        prog = (command.split() or ["?"])[0]
        prog = os.path.basename(prog)
        msg = f"{matched} while running `{prog}`"
        gid = hashlib.sha1((msg.lower() + "|").encode("utf-8")).hexdigest()[:8]

        entry = {
            "event": "log", "id": gid,
            "ts": datetime.now(timezone.utc).isoformat(),
            "msg": msg, "skill": "", "cmd": command, "source": "hook",
        }
        with open(ledger, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # Never let capture break a tool call.
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
