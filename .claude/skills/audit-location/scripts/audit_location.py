#!/usr/bin/env python3
"""
One-shot READ-ONLY audit of a live GHL location.

Wraps the four read-only "dumper" scripts in the repo into a single, correctly
ordered run so a future agent does not have to remember four invocations:

  1. dump_workflows.py            structural dump (folders + every workflow)
  2. dump_workflow_analytics.py   enrollment counts, merged onto the dump
  3. build_flow_map.py            static cross-workflow flow map (no API calls)
  4. build_workflow_docx.js       (optional) single master .docx report

Steps 2-4 depend on step 1's output (_index.json + workflows/*.json), so the
order is fixed. Step 2 is skipped (with a warning, non-fatally) if its analytics
endpoint 401s — the structural dump + flow map + docx still build without it.

Read-only: every wrapped script issues GETs exclusively. Nothing is written to
GHL; output is files on disk under --out-dir.

Usage:
  python3 scripts/audit_location.py <location_id> --out-dir DIR
          [--label "Client Name"]   # nice title for the .docx
          [--no-docx]               # skip the Node docx step
          [--no-analytics]          # skip the analytics merge
          [--refresh-token TOK] [--id-token TOK]

Auth: same as the wrapped scripts — pass --refresh-token / --id-token, or set
$GHL_FIREBASE_REFRESH_TOKEN / $GHL_FIREBASE_TOKEN. For a non-DLF agency you must
pass that client's OWN refresh token (an ambient DLF token wins silently
otherwise). Env is also auto-loaded from project .env / ~/.env.secrets by the
underlying scripts.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Repo root is two levels up from .claude/skills/audit-location/scripts/.
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SCRIPTS = os.path.join(REPO, "scripts")


def _run(cmd, *, fatal=True):
    print("\n$ " + " ".join(cmd), flush=True)
    rc = subprocess.call(cmd, cwd=REPO)
    if rc != 0:
        msg = f"[audit] step exited {rc}: {cmd[1] if len(cmd) > 1 else cmd[0]}"
        if fatal:
            print(msg + " — aborting.", file=sys.stderr)
            sys.exit(rc)
        print(msg + " — continuing (non-fatal).", file=sys.stderr)
    return rc


def main(argv):
    ap = argparse.ArgumentParser(prog="audit_location.py")
    ap.add_argument("location_id")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--label", default=None,
                    help="display name for the .docx cover (e.g. client name)")
    ap.add_argument("--no-docx", action="store_true")
    ap.add_argument("--no-analytics", action="store_true")
    ap.add_argument("--refresh-token",
                    default=os.environ.get("GHL_FIREBASE_REFRESH_TOKEN") or None)
    ap.add_argument("--id-token",
                    default=os.environ.get("GHL_FIREBASE_TOKEN") or None)
    args = ap.parse_args(argv)

    loc = args.location_id
    out = os.path.abspath(args.out_dir)
    tok = []
    if args.refresh_token:
        tok += ["--refresh-token", args.refresh_token]
    if args.id_token:
        tok += ["--id-token", args.id_token]

    py = sys.executable or "python3"

    # 1) Structural dump (REQUIRED — everything downstream reads its output).
    _run([py, os.path.join(SCRIPTS, "dump_workflows.py"), loc,
          "--out-dir", out] + tok)

    # 2) Analytics merge (optional; non-fatal — endpoint can 401 on some scopes).
    if not args.no_analytics:
        _run([py, os.path.join(SCRIPTS, "dump_workflow_analytics.py"), loc,
              "--out-dir", out] + tok, fatal=False)

    # 3) Static flow map (no API calls; reads the dump only).
    _run([py, os.path.join(SCRIPTS, "build_flow_map.py"), out], fatal=False)

    # 4) Optional .docx report (Node).
    if not args.no_docx:
        docx_cmd = ["node", os.path.join(SCRIPTS, "build_workflow_docx.js"), out]
        if args.label:
            docx_cmd += ["--label", args.label]
        _run(docx_cmd, fatal=False)

    print(f"\n[audit] done → {out}")
    print("[audit] open: _index.md, _analytics.md, _flows.md"
          + ("" if args.no_docx else ", *-Workflow-Documentation.docx"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
