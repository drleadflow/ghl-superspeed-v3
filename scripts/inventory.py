#!/usr/bin/env python3
"""
Inventory of a GHL location — "what do we have in here?"

Prints the workflow folder tree (with per-folder + total counts) and every
custom value (slug + truncated preview), flagging which A2P custom-value slugs
are missing. With --json, dumps the whole inventory as machine-readable JSON so
other scripts can consume it.

Usage:
  python3 scripts/inventory.py <location_id> [--refresh-token TOK] [--id-token TOK] [--json]

Auth (one of these must yield a valid token-id):
  --refresh-token TOK     a Firebase refresh token (starts AMf-...); exchanged on expiry
  --id-token TOK          a fresh Firebase id_token (~1h TTL)
  $GHL_FIREBASE_REFRESH_TOKEN / $GHL_FIREBASE_TOKEN   same, via environment
  (env is also auto-loaded from project .env and ~/.env.secrets at startup)

Read-only: never POSTs/PUTs/DELETEs. Safe to run repeatedly.

## Gotchas
- Env auto-load ONLY pulls GHL_FIREBASE_TOKEN / GHL_FIREBASE_REFRESH_TOKEN from
  the project .env and ~/.env.secrets; nothing else is imported, and no token
  value is ever printed.
- Read-only — this script issues GET requests exclusively.
- The customValues endpoint needs the API version header; that is handled inside
  lib.a2p_values.fetch_custom_values (do not call the endpoint without it).
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.engine import GHLClient, TokenManager  # noqa: E402
from lib.a2p_values import fetch_custom_values, A2P_VALUE_KEYS  # noqa: E402
from scripts.dump_workflows import walk_tree  # noqa: E402

_PREVIEW_MAX = 60


# ── Env auto-load (2 GHL token vars only) ─────────────────────────────────────

def _load_env_tokens():
    """Silently populate the 2 GHL token env vars from project .env / ~/.env.secrets.

    Only fills a var if it is not already set. Parses simple KEY=VALUE lines and
    strips surrounding quotes. Missing files are skipped. Never prints values.
    """
    wanted = ("GHL_FIREBASE_TOKEN", "GHL_FIREBASE_REFRESH_TOKEN")
    paths = [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.expanduser("~/.env.secrets"),
    ]
    for path in paths:
        try:
            with open(path) as fh:
                lines = fh.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            if key not in wanted or os.environ.get(key):
                continue
            val = val.strip().strip('"').strip("'")
            if val:
                os.environ[key] = val


# ── Auth glue ────────────────────────────────────────────────────────────────

def build_client(location_id, id_token=None, refresh_token=None):
    tm = TokenManager(location_id)
    if refresh_token:
        tm.set_refresh_token(refresh_token)
        tm.prefer_refresh_token = True
    elif id_token:
        tm._token = id_token  # noqa: SLF001
        tm._token_time = time.time()  # noqa: SLF001
    return GHLClient(tm, location_id)


# ── Inventory assembly ────────────────────────────────────────────────────────

def _folder_path(folder, folder_by_id):
    """Full slash path for a folder, including its own name."""
    path, fid = [folder["name"]], folder.get("_parentFolderId")
    while fid and fid in folder_by_id:
        f = folder_by_id[fid]
        path.insert(0, f["name"])
        fid = f.get("_parentFolderId")
    return path


def build_inventory(client, location_id):
    tree = walk_tree(client, location_id)
    folders = tree.get("folders", [])
    workflows = tree.get("workflows", [])
    folder_by_id = {f["id"]: f for f in folders}

    # Count workflows per folder id ("root" for top-level).
    counts = {}
    for w in workflows:
        key = w.get("_parentFolderId") or "root"
        counts[key] = counts.get(key, 0) + 1

    folder_rows = []
    for f in folders:
        path = _folder_path(f, folder_by_id)
        folder_rows.append({
            "id": f["id"],
            "name": f["name"],
            "path": path,
            "parentFolderId": f.get("_parentFolderId"),
            "workflowCount": counts.get(f["id"], 0),
        })
    folder_rows.sort(key=lambda r: " / ".join(r["path"]).lower())

    cvs = fetch_custom_values(client, location_id)
    a2p_slugs = [slug for slug, _name, _cat in A2P_VALUE_KEYS]
    missing_a2p = [slug for slug in a2p_slugs if slug not in cvs]

    return {
        "locationId": location_id,
        "rootWorkflowCount": counts.get("root", 0),
        "totalWorkflows": len(workflows),
        "totalFolders": len(folders),
        "folders": folder_rows,
        "workflows": [
            {
                "id": w["id"],
                "name": w.get("name"),
                "status": w.get("status"),
                "parentFolderId": w.get("_parentFolderId"),
            }
            for w in workflows
        ],
        "customValues": {
            slug: {"name": v.get("name", ""), "value": v.get("value", "")}
            for slug, v in cvs.items()
        },
        "a2pMissing": missing_a2p,
    }


def _truncate(value):
    value = (value or "").replace("\n", " ").replace("\r", " ").strip()
    if not value:
        return "(empty)"
    if len(value) > _PREVIEW_MAX:
        return value[:_PREVIEW_MAX - 1] + "…"
    return value


def print_human(inv):
    loc = inv["locationId"]
    print("Inventory — location %s" % loc)
    print("=" * 56)

    print("Workflow tree (%d folder(s), %d workflow(s) total)"
          % (inv["totalFolders"], inv["totalWorkflows"]))
    print("-" * 56)
    if inv["rootWorkflowCount"]:
        print("  (root)  [%d]" % inv["rootWorkflowCount"])
    for f in inv["folders"]:
        depth = len(f["path"]) - 1
        indent = "  " + ("  " * depth)
        print("%s%s  [%d]" % (indent, f["name"], f["workflowCount"]))
    print()

    cvs = inv["customValues"]
    print("Custom values (%d present)" % len(cvs))
    print("-" * 56)
    for slug in sorted(cvs):
        print("  %-34s %s" % (slug, _truncate(cvs[slug].get("value"))))
    print()

    missing = inv["a2pMissing"]
    if missing:
        print("A2P slugs MISSING (%d):" % len(missing))
        for slug in missing:
            print("  - %s" % slug)
    else:
        print("A2P slugs: all %d present." % len(A2P_VALUE_KEYS))


# ── Main ─────────────────────────────────────────────────────────────────────

def _parse_args(argv):
    ap = argparse.ArgumentParser(prog="inventory.py", add_help=True)
    ap.add_argument("location_id")
    ap.add_argument(
        "--refresh-token",
        default=os.environ.get("GHL_FIREBASE_REFRESH_TOKEN", "") or None,
    )
    ap.add_argument(
        "--id-token",
        default=os.environ.get("GHL_FIREBASE_TOKEN", "") or None,
    )
    ap.add_argument("--json", action="store_true",
                    help="dump the full inventory as JSON instead of the human view")
    return ap.parse_args(argv)


def main(argv):
    _load_env_tokens()
    args = _parse_args(argv)
    refresh = args.refresh_token or os.environ.get("GHL_FIREBASE_REFRESH_TOKEN") or None
    id_token = args.id_token or os.environ.get("GHL_FIREBASE_TOKEN") or None

    if not (refresh or id_token):
        print("ERROR: provide --refresh-token or --id-token (or set "
              "$GHL_FIREBASE_REFRESH_TOKEN / $GHL_FIREBASE_TOKEN).",
              file=sys.stderr)
        return 2

    client = build_client(args.location_id, id_token=id_token, refresh_token=refresh)
    inv = build_inventory(client, args.location_id)

    if args.json:
        print(json.dumps(inv, indent=2, ensure_ascii=False))
    else:
        print_human(inv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
