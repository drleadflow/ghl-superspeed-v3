#!/usr/bin/env python3
"""
A2P custom-value populator — unit tests (no live API).
Run: python3 tests/test_a2p_values.py   (standalone)
 or: python3 -m pytest tests/test_a2p_values.py -v
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import TokenManager


def test_token_manager_has_prefer_refresh_flag_default_false():
    tm = TokenManager("loc123")
    assert tm.prefer_refresh_token is False


def test_token_manager_prefers_refresh_token_when_set():
    tm = TokenManager("loc123")
    tm.set_refresh_token("RTOKEN")
    tm.prefer_refresh_token = True
    calls = []
    tm._fetch_from_broker = lambda: (calls.append("broker"), "BROKER_TOKEN")[1]
    tm._fetch_from_mcp = lambda: (calls.append("mcp"), "MCP_TOKEN")[1]
    tm._refresh_firebase = lambda: (calls.append("firebase"), "FIREBASE_TOKEN")[1]
    got = tm.get_token()
    assert got == "FIREBASE_TOKEN"
    assert calls == ["firebase"]  # broker/mcp not consulted


def test_token_manager_default_order_still_broker_first():
    tm = TokenManager("loc123")
    tm.set_refresh_token("RTOKEN")  # prefer flag NOT set
    calls = []
    tm._fetch_from_broker = lambda: (calls.append("broker"), "BROKER_TOKEN")[1]
    tm._fetch_from_mcp = lambda: (calls.append("mcp"), "MCP_TOKEN")[1]
    tm._refresh_firebase = lambda: (calls.append("firebase"), "FIREBASE_TOKEN")[1]
    got = tm.get_token()
    assert got == "BROKER_TOKEN"
    assert calls == ["broker"]


# ---- standalone runner ----
def _run_all():
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for f in funcs:
        try:
            f(); print(f"  PASS {f.__name__}")
        except Exception as e:
            failed += 1; print(f"  FAIL {f.__name__}: {e!r}")
    print(f"\n{len(funcs)-failed}/{len(funcs)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run_all())
