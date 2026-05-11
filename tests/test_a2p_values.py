#!/usr/bin/env python3
"""
A2P custom-value populator — unit tests (no live API).
Run: python3 tests/test_a2p_values.py   (standalone)
 or: python3 -m pytest tests/test_a2p_values.py -v
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import TokenManager, GHLClient
from lib.a2p_values import (
    A2P_VALUE_KEYS, make_client, fetch_custom_values, apply_values,
)


# ── TokenManager.prefer_refresh_token ────────────────────────────────────────
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
    assert calls == ["firebase"]


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


# ── A2P_VALUE_KEYS + make_client ─────────────────────────────────────────────
def test_a2p_value_keys_shape():
    slugs = [k[0] for k in A2P_VALUE_KEYS]
    cats = [k[2] for k in A2P_VALUE_KEYS]
    assert len(A2P_VALUE_KEYS) == 18
    assert len(set(slugs)) == 18
    assert all(c in ("fact", "copy") for c in cats)
    assert cats.count("fact") == 7 and cats.count("copy") == 11
    assert all(isinstance(s, str) and isinstance(n, str) and s and n for s, n, c in A2P_VALUE_KEYS)
    assert ("logo", "Logo", "fact") in A2P_VALUE_KEYS
    assert ("our_services_4__description", "Our Services 4 - Description", "copy") in A2P_VALUE_KEYS


def test_make_client_wires_location_and_refresh_token():
    c = make_client("LOCXYZ", refresh_token="RT")
    assert isinstance(c, GHLClient)
    assert c.location_id == "LOCXYZ"
    assert c.token_mgr.location_id == "LOCXYZ"
    assert c.token_mgr._refresh_token == "RT"
    assert c.token_mgr.prefer_refresh_token is True


def test_make_client_no_refresh_token():
    c = make_client("LOCXYZ")
    assert isinstance(c, GHLClient)
    assert c.token_mgr._refresh_token is None
    assert c.token_mgr.prefer_refresh_token is False


# ── fake GHLClient for fetch/apply tests ─────────────────────────────────────
class _FakeClient:
    """Minimal stand-in for GHLClient that records calls and returns canned data."""
    def __init__(self, cv_response, post_response=None, put_response=None):
        self.calls = []
        self._cv = cv_response
        self._post = post_response if post_response is not None else {}   # GHL empty-200 on create
        self._put = put_response if put_response is not None else {"customValue": {"id": "x"}}
    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if method == "GET" and path.endswith("/customValues/"):
            return self._cv
        if method == "POST" and path.endswith("/customValues/"):
            return self._post
        if method == "PUT":
            return self._put
        return {}


def _cv_item(name, slug, value=""):
    return {"id": "id_" + slug, "name": name, "fieldKey": "{{ custom_values." + slug + " }}", "value": value}


# ── fetch_custom_values ──────────────────────────────────────────────────────
def test_fetch_custom_values_parses_fieldkey_slug():
    client = _FakeClient({"customValues": [
        _cv_item("Logo", "logo", "{{location.logo_url}}"),
        _cv_item("Business Short Name", "business_short_name", "Acme Co"),
        {"id": "weird", "name": "No Field Key", "value": "x"},
    ]})
    out = fetch_custom_values(client, "LOC")
    assert set(out.keys()) == {"logo", "business_short_name"}
    assert out["logo"] == {"id": "id_logo", "name": "Logo", "value": "{{location.logo_url}}"}
    assert out["business_short_name"]["value"] == "Acme Co"
    assert client.calls == [("GET", "/locations/LOC/customValues/", None)]


def test_fetch_custom_values_raises_on_error():
    client = _FakeClient({"_error": True, "code": 401, "message": "nope"})
    try:
        fetch_custom_values(client, "LOC")
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


# ── apply_values ─────────────────────────────────────────────────────────────
def _full_value_map():
    return {slug: ("VAL_" + slug) for slug, _n, _c in A2P_VALUE_KEYS}


def test_apply_values_creates_all_when_none_exist():
    client = _FakeClient({"customValues": []})
    rep = apply_values(client, "LOC", _full_value_map())
    assert len(rep["created"]) == 18 and rep["updated"] == [] and rep["skipped"] == [] and rep["errors"] == []
    posts = [c for c in client.calls if c[0] == "POST"]
    assert len(posts) == 18
    first = posts[0]
    assert first[1] == "/locations/LOC/customValues/"
    assert set(first[2].keys()) == {"name", "value"}
    assert rep["resolved"]["logo"] == "VAL_logo"


def test_apply_values_updates_when_all_exist():
    existing = {"customValues": [_cv_item(name, slug, "old") for slug, name, _c in A2P_VALUE_KEYS]}
    client = _FakeClient(existing)
    rep = apply_values(client, "LOC", _full_value_map())
    assert len(rep["updated"]) == 18 and rep["created"] == [] and rep["errors"] == []
    puts = [c for c in client.calls if c[0] == "PUT"]
    assert len(puts) == 18
    assert puts[0][1] == "/locations/LOC/customValues/id_" + A2P_VALUE_KEYS[0][0]
    assert puts[0][2] == {"name": A2P_VALUE_KEYS[0][1], "value": "VAL_" + A2P_VALUE_KEYS[0][0]}


def test_apply_values_skips_blank_and_missing_values():
    client = _FakeClient({"customValues": [_cv_item(n, s, "old") for s, n, _c in A2P_VALUE_KEYS]})
    vm = {"logo": "{{location.logo_url}}", "primary_color": "   ", "from_email": ""}
    rep = apply_values(client, "LOC", vm)
    assert rep["updated"] == ["logo"]
    assert len(rep["skipped"]) == 17
    skipped_slugs = {s for s, _r in rep["skipped"]}
    assert "primary_color" in skipped_slugs and "from_email" in skipped_slugs
    assert [c[0] for c in client.calls] == ["GET", "PUT"]


def test_apply_values_dry_run_makes_no_writes():
    client = _FakeClient({"customValues": [_cv_item("Logo", "logo", "old")]})
    rep = apply_values(client, "LOC", _full_value_map(), dry_run=True)
    assert "logo" in rep["updated"]
    assert len(rep["created"]) == 17
    assert [c[0] for c in client.calls] == ["GET"]


def test_apply_values_records_errors():
    client = _FakeClient({"customValues": []}, post_response={"_error": True, "code": 422, "message": "bad name"})
    rep = apply_values(client, "LOC", {"logo": "x"})
    assert rep["errors"] and rep["errors"][0][0] == "logo" and "422" in rep["errors"][0][1]
    assert rep["created"] == []


def test_apply_values_records_auth_failure():
    class _AuthFail(_FakeClient):
        def request(self, method, path, body=None):
            self.calls.append((method, path, body))
            if method == "GET":
                return {"customValues": []}
            return None
    client = _AuthFail({"customValues": []})
    rep = apply_values(client, "LOC", {"logo": "x"})
    assert rep["errors"] and "auth" in rep["errors"][0][1].lower()


def test_apply_values_ignores_unknown_slugs():
    client = _FakeClient({"customValues": []})
    rep = apply_values(client, "LOC", {"bogus_slug": "x", "logo": "{{location.logo_url}}"})
    assert rep["created"] == ["logo"]
    posts = [c for c in client.calls if c[0] == "POST"]
    assert len(posts) == 1
    assert posts[0][2]["value"] == "{{location.logo_url}}"


# ── a2p_apply CLI (arg / file error paths; happy path covered via fake client) ─
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import a2p_apply  # noqa: E402


def test_apply_cli_missing_value_map_file_exits_2():
    rc = a2p_apply.main(["LOC", "/no/such/file.json"])
    assert rc == 2


def test_apply_cli_non_object_value_map_exits_2():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, b"[1, 2, 3]")
    os.close(fd)
    try:
        rc = a2p_apply.main(["LOC", path])
        assert rc == 2
    finally:
        os.unlink(path)


def test_apply_cli_dry_run_with_fake_client():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, json.dumps({"logo": "{{location.logo_url}}"}).encode())
    os.close(fd)
    orig = a2p_apply.make_client
    a2p_apply.make_client = lambda loc, refresh_token=None: _FakeClient({"customValues": []})
    try:
        rc = a2p_apply.main(["LOC", path, "--dry-run"])
        assert rc == 0
    finally:
        a2p_apply.make_client = orig
        os.unlink(path)


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
