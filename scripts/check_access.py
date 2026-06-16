#!/usr/bin/env python3
"""
Pre-flight access check for a GHL location — "is this account good to go?"

Makes one cheap live read to prove auth, then verifies the two custom values the
sequence copy depends on (booking_link, text_message_name) are present and
non-empty. Replaces a multi-step manual probe with a single auto-approvable run.

Usage:
  python3 scripts/check_access.py <location_id> [--refresh-token TOK] [--id-token TOK]

Auth (one of these must yield a valid token-id):
  --refresh-token TOK     a Firebase refresh token (starts AMf-...); exchanged on expiry
  --id-token TOK          a fresh Firebase id_token (~1h TTL)
  $GHL_FIREBASE_REFRESH_TOKEN / $GHL_FIREBASE_TOKEN   same, via environment
  (env is also auto-loaded from project .env and ~/.env.secrets at startup)

Exit codes (scriptable):
  0  READY      — auth ok AND booking_link + text_message_name present & non-empty
  1  NOT READY  — auth ok but key custom value(s) missing/empty
  2  AUTH FAIL  — could not prove a live read

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
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.engine import GHLClient, TokenManager  # noqa: E402
from lib.a2p_values import fetch_custom_values  # noqa: E402
from scripts.dump_workflows import walk_tree  # noqa: E402

# The two custom values the sequence copy needs at send time.
KEY_VALUES = ["booking_link", "text_message_name"]


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


# ── Main ─────────────────────────────────────────────────────────────────────

def _parse_args(argv):
    ap = argparse.ArgumentParser(prog="check_access.py", add_help=True)
    ap.add_argument("location_id")
    ap.add_argument(
        "--refresh-token",
        default=os.environ.get("GHL_FIREBASE_REFRESH_TOKEN", "") or None,
    )
    ap.add_argument(
        "--id-token",
        default=os.environ.get("GHL_FIREBASE_TOKEN", "") or None,
    )
    return ap.parse_args(argv)


def main(argv):
    _load_env_tokens()
    args = _parse_args(argv)
    # Re-resolve token defaults now that env is loaded (argparse defaults were
    # baked before _load_env_tokens ran).
    refresh = args.refresh_token or os.environ.get("GHL_FIREBASE_REFRESH_TOKEN") or None
    id_token = args.id_token or os.environ.get("GHL_FIREBASE_TOKEN") or None

    loc = args.location_id
    print("GHL access check — location %s" % loc)
    print("-" * 48)

    if not (refresh or id_token):
        print("Auth:          FAILED (no token; set $GHL_FIREBASE_REFRESH_TOKEN "
              "or $GHL_FIREBASE_TOKEN, or pass --refresh-token/--id-token)")
        print("Verdict:       NOT READY")
        return 2

    client = build_client(loc, id_token=id_token, refresh_token=refresh)

    # 1) One cheap live read to prove auth.
    try:
        tree = walk_tree(client, loc)
    except Exception as exc:  # noqa: BLE001
        print("Auth:          FAILED (%s)" % exc)
        print("Verdict:       NOT READY")
        return 2

    folders = tree.get("folders", [])
    workflows = tree.get("workflows", [])
    if not folders and not workflows:
        # walk_tree swallows errors and returns empties on a bad token, so an
        # all-empty result is treated as an auth failure rather than a real
        # (but empty) location.
        print("Auth:          FAILED (live read returned nothing — likely a bad "
              "or expired token)")
        print("Verdict:       NOT READY")
        return 2

    print("Auth:          OK")
    print("Live read:     %d folder(s), %d workflow(s)" % (len(folders), len(workflows)))

    # 2) Custom values.
    try:
        cvs = fetch_custom_values(client, loc)
    except Exception as exc:  # noqa: BLE001
        print("Custom values: FAILED (%s)" % exc)
        print("Verdict:       NOT READY")
        return 1

    print("Custom values: %d present" % len(cvs))

    # 3) Key value scorecard.
    gaps = []
    for slug in KEY_VALUES:
        entry = cvs.get(slug)
        if entry is None:
            state = "MISSING"
            gaps.append("%s (missing)" % slug)
        elif not (entry.get("value") or "").strip():
            state = "EMPTY"
            gaps.append("%s (empty)" % slug)
        else:
            state = "PRESENT"
        print("  %-20s %s" % (slug + ":", state))

    # 4) Verdict.
    print("-" * 48)
    if gaps:
        print("Verdict:       NOT READY — %s" % ", ".join(gaps))
        return 1
    print("Verdict:       READY")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
