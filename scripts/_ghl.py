#!/usr/bin/env python3
"""Shared GHL client helper for the scripts/ tools.

Loads GHL_FIREBASE_TOKEN / GHL_FIREBASE_REFRESH_TOKEN from the project .env
and ~/.env.secrets (only those two keys, silently), and builds a GHLClient
that PREFERS the refresh token (a stale id-token otherwise wins and 401s).

Usage (from another script):
    from _ghl import client, load_env
    c = client("<location_id>")

Gotchas:
- Only the two GHL token vars are read from the env files; nothing is printed.
- prefer_refresh_token=True is forced — required for reliable auth.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

_TOKEN_KEYS = ("GHL_FIREBASE_TOKEN", "GHL_FIREBASE_REFRESH_TOKEN")


def load_env():
    for p in (os.path.join(REPO, ".env"), os.path.expanduser("~/.env.secrets")):
        try:
            f = open(p)
        except OSError:
            continue
        with f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                if k in _TOKEN_KEYS and not os.environ.get(k):
                    os.environ[k] = v.strip().strip('"').strip("'")


def client(location_id):
    """Build a refresh-token-preferring GHLClient for a location."""
    load_env()
    from lib.a2p_values import make_client
    return make_client(location_id,
                        refresh_token=os.environ.get("GHL_FIREBASE_REFRESH_TOKEN"))
