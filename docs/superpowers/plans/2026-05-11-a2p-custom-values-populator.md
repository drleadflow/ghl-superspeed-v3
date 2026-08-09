# A2P Custom-Value Populator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Repo convention note:** the owner has a *no-auto-commit* rule. Each task ends with a `git add` (staging) step and a `git commit` step shown for completeness — but when executing, batch the commits and only run `git commit` once the owner OKs it (e.g. at the end, or at natural checkpoints). Never push.

**Goal:** A skill + helper scripts that, given a business URL + GHL sub-account ID (+ optional vault brief), populate the 18 custom values the pre-built A2P landing-page funnel + opt-in form reference on that sub-account.

**Architecture:** `lib/a2p_values.py` holds the deterministic GHL mechanics (the canonical 18-key list, fetch existing custom values, create-or-update each, skip blanks). `scripts/a2p_scrape.py` turns a URL into compact JSON (stdlib only) so the LLM reads structured data, not raw HTML. `scripts/a2p_apply.py` is a thin CLI over the lib with `--dry-run`. `.claude/commands/a2p-fill-values.md` is the orchestrating skill: scrape → read brief → Claude composes the value map → dry-run preview → apply → log. A 4-line addition to `engine.TokenManager` lets non-DLF agency tokens win over the cached broker/MCP token.

**Tech stack:** Python 3.9 (stdlib only — `urllib`, `re`, `html.parser`, `argparse`, `json`, `dataclasses`); reuses `lib/engine.py` (`TokenManager`, `GHLClient`); tests are standalone scripts in `tests/` (run with `python3 tests/test_a2p_values.py`; `pytest` also works if installed) mirroring `tests/test_engine.py`.

---

## File structure

| File | Status | Responsibility |
|---|---|---|
| `lib/engine.py` | modify (~4 lines in `TokenManager`) | add `prefer_refresh_token` flag so an explicit non-DLF refresh token is used before the cached broker/MCP token |
| `lib/a2p_values.py` | create | `A2P_VALUE_KEYS` (the 18); `make_client()`; `fetch_custom_values()`; `apply_values()` + `Report` |
| `scripts/a2p_scrape.py` | create | `parse_html(html, url) -> dict`; `scrape(url) -> dict`; `main(argv)` — URL → compact business JSON |
| `scripts/a2p_apply.py` | create | CLI: `<location_id> <value_map.json> [--dry-run] [--refresh-token=…]` → calls `apply_values`, prints report |
| `.claude/commands/a2p-fill-values.md` | create | the skill — orchestrates scrape + brief + LLM copy + dry-run + apply + blade-ops log |
| `tests/test_a2p_values.py` | create | unit tests for the `TokenManager` flag, `make_client`, `fetch_custom_values`, `apply_values`, and `a2p_apply` arg/file errors |
| `tests/test_a2p_scrape.py` | create | fixture test for `parse_html` |
| `tests/fixtures/sample_business.html` | create | tiny HTML fixture for the scrape test |
| `README.md` | modify (1 row) | add the new skill to the skills/commands list |

---

## Task 1: `TokenManager.prefer_refresh_token` flag

**Files:**
- Modify: `lib/engine.py` (`TokenManager.__init__` and `TokenManager.get_token`)
- Test: `tests/test_a2p_values.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_a2p_values.py` with this content (more tests get appended in later tasks):

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/test_a2p_values.py`
Expected: FAIL — `test_token_manager_has_prefer_refresh_flag_default_false` raises `AttributeError: 'TokenManager' object has no attribute 'prefer_refresh_token'`.

- [ ] **Step 3: Implement the flag in `lib/engine.py`**

In `TokenManager.__init__` (currently ends with `self._refresh_token: Optional[str] = None`), add one line:

```python
    def __init__(self, location_id: str):
        self.location_id = location_id
        self._token: Optional[str] = None
        self._token_time: float = 0
        self._refresh_token: Optional[str] = None
        self.prefer_refresh_token: bool = False  # when True + a refresh token is set, use Firebase before broker/MCP
```

In `TokenManager.get_token`, immediately after the "current token still fresh" check and before the broker call, insert:

```python
        # 1b. If caller explicitly wants the refresh-token identity, use it first
        #     (avoids a cached DLF broker/MCP token winning for a non-DLF agency location).
        if self.prefer_refresh_token and self._refresh_token:
            token = self._refresh_firebase()
            if token:
                self._token = token
                self._token_time = time.time()
                return token
```

(So the order becomes: cached → preferred-refresh → broker → mcp → refresh → env → argv.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 tests/test_a2p_values.py`
Expected: `3/3 passed`

- [ ] **Step 5: Stage (commit deferred per repo rule)**

```bash
git add lib/engine.py tests/test_a2p_values.py
git commit -m "feat(engine): TokenManager.prefer_refresh_token flag for non-DLF agency auth"
```

---

## Task 2: `lib/a2p_values.py` — `A2P_VALUE_KEYS` + `make_client`

**Files:**
- Create: `lib/a2p_values.py`
- Test: `tests/test_a2p_values.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_a2p_values.py`**

Insert these *above* the `# ---- standalone runner ----` section:

```python
from lib.a2p_values import A2P_VALUE_KEYS, make_client
from lib.engine import GHLClient


def test_a2p_value_keys_shape():
    slugs = [k[0] for k in A2P_VALUE_KEYS]
    cats = [k[2] for k in A2P_VALUE_KEYS]
    assert len(A2P_VALUE_KEYS) == 18
    assert len(set(slugs)) == 18                       # unique
    assert all(c in ("fact", "copy") for c in cats)
    assert cats.count("fact") == 7 and cats.count("copy") == 11
    # every entry is (slug:str, canonical_name:str, category:str)
    assert all(isinstance(s, str) and isinstance(n, str) and s and n for s, n, c in A2P_VALUE_KEYS)
    # spot-check a couple of slugs we observed live
    assert ("logo", "Logo", "fact") in A2P_VALUE_KEYS
    assert ("our_services_4__description", "Our Services 4 - Description", "copy") in A2P_VALUE_KEYS


def test_make_client_wires_location_and_refresh_token():
    c = make_client("LOCXYZ", refresh_token="RT")
    assert isinstance(c, GHLClient)
    assert c.location_id == "LOCXYZ"
    assert c.token_mgr.location_id == "LOCXYZ"
    assert c.token_mgr._refresh_token == "RT"
    assert c.token_mgr.prefer_refresh_token is True   # refresh token implies preference


def test_make_client_no_refresh_token():
    c = make_client("LOCXYZ")
    assert isinstance(c, GHLClient)
    assert c.token_mgr._refresh_token is None
    assert c.token_mgr.prefer_refresh_token is False
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 tests/test_a2p_values.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.a2p_values'`.

- [ ] **Step 3: Create `lib/a2p_values.py` with the constants + `make_client`**

```python
#!/usr/bin/env python3
"""
A2P custom-value populator — the deterministic GHL mechanics.

Given a GHL sub-account, ensure the 18 custom values that the pre-built
"A2P Landing Page" funnel + opt-in form reference are present and populated.
The funnel pages themselves are NOT touched — they merge-tag off these values.

Public API:
    A2P_VALUE_KEYS                       — the canonical 18 (slug, name, category)
    make_client(location_id, refresh_token=None) -> GHLClient
    fetch_custom_values(client, location_id)     -> {slug: {"id","name","value"}}
    apply_values(client, location_id, value_map, *, dry_run=False) -> Report (dict)
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.engine import TokenManager, GHLClient  # noqa: E402

# ── The 18 custom values the A2P funnel + opt-in form reference ────────────────
# (slug, canonical GHL display name, category)
#   "fact" — resolved deterministically: brief -> location API -> site
#   "copy" — LLM-generated from the scraped site + brief, in DLF brand voice
# Names captured live 2026-05-11 from the reference location (Prestige) so they
# match what GHL expects when CREATING a missing value; when UPDATING an existing
# value, apply_values keeps whatever name is already on the location.
A2P_VALUE_KEYS = [
    ("business_short_name",                    "Business Short Name",                    "fact"),
    ("business_profile__legal_business_name",  "Business Profile - Legal Business Name",  "fact"),
    ("business_profile__phone_number",         "BUSINESS PROFILE - Phone Number",         "fact"),
    ("from_email",                             "From Email",                              "fact"),
    ("logo",                                   "Logo",                                    "fact"),
    ("primary_color",                          "Primary Color",                           "fact"),
    ("secondary_color__hex_code",              "Secondary Color - Hex Code",              "fact"),
    ("about_us__description",                  "About Us - Description",                  "copy"),
    ("business_welcome_message",               "Business Welcome Message",                "copy"),
    ("business_solution__description",         "Business Solution - Description",          "copy"),
    ("our_services_1",                         "Our Services 1",                          "copy"),
    ("our_services_1__description",            "Our Services 1 - Description",             "copy"),
    ("our_services_2",                         "Our Services 2",                          "copy"),
    ("our_services_2__description",            "Our Services 2 - Description",             "copy"),
    ("our_services_3",                         "Our Services 3",                          "copy"),
    ("our_services_3__description",            "Our Services 3 - Description",             "copy"),
    ("our_services_4",                         "Our Services 4",                          "copy"),
    ("our_services_4__description",            "Our Services 4 - Description",             "copy"),
]

_SLUG_BY_KEY = {slug: (name, cat) for slug, name, cat in A2P_VALUE_KEYS}
_CV_SLUG_RE = re.compile(r"custom_values\.([a-zA-Z0-9_\-]+)")


def make_client(location_id, refresh_token=None):
    """Build a GHLClient for a location.

    If `refresh_token` is supplied (a client's GHL Firebase refresh token, e.g.
    for a non-DLF agency sub-account), it's set on the TokenManager and the
    `prefer_refresh_token` flag is turned on so that identity wins over any
    cached broker/MCP token (see the 'Non-DLF Agency deploy auth' lesson).
    """
    tm = TokenManager(location_id)
    if refresh_token:
        tm.set_refresh_token(refresh_token)
        tm.prefer_refresh_token = True
    return GHLClient(tm, location_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 tests/test_a2p_values.py`
Expected: `6/6 passed`

- [ ] **Step 5: Stage / commit**

```bash
git add lib/a2p_values.py tests/test_a2p_values.py
git commit -m "feat(a2p): A2P_VALUE_KEYS + make_client"
```

---

## Task 3: `fetch_custom_values`

**Files:**
- Modify: `lib/a2p_values.py` (append function)
- Test: `tests/test_a2p_values.py` (append)

- [ ] **Step 1: Append failing tests**

Insert above the standalone runner:

```python
from lib.a2p_values import fetch_custom_values


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


def test_fetch_custom_values_parses_fieldkey_slug():
    client = _FakeClient({"customValues": [
        _cv_item("Logo", "logo", "{{location.logo_url}}"),
        _cv_item("Business Short Name", "business_short_name", "Acme Co"),
        {"id": "weird", "name": "No Field Key", "value": "x"},          # no fieldKey -> skipped
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 tests/test_a2p_values.py`
Expected: FAIL — `ImportError: cannot import name 'fetch_custom_values'`.

- [ ] **Step 3: Append `fetch_custom_values` to `lib/a2p_values.py`**

```python
def fetch_custom_values(client, location_id):
    """Fetch all custom values on the location, keyed by their `{{custom_values.<slug>}}` slug.

    Returns {slug: {"id": str, "name": str, "value": str}}.
    Raises RuntimeError if the API call fails.
    """
    resp = client.request("GET", "/locations/%s/customValues/" % location_id)
    if not isinstance(resp, dict) or resp.get("_error") or resp is None:
        raise RuntimeError("Failed to fetch custom values for %s: %r" % (location_id, resp))
    items = resp.get("customValues") or resp.get("custom_values") or []
    out = {}
    for it in items:
        fk = it.get("fieldKey") or ""
        m = _CV_SLUG_RE.search(fk)
        if not m:
            continue
        out[m.group(1)] = {
            "id": it.get("id") or it.get("_id"),
            "name": it.get("name", "") or "",
            "value": it.get("value", "") or "",
        }
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 tests/test_a2p_values.py`
Expected: `8/8 passed`

- [ ] **Step 5: Stage / commit**

```bash
git add lib/a2p_values.py tests/test_a2p_values.py
git commit -m "feat(a2p): fetch_custom_values"
```

---

## Task 4: `apply_values` + `Report`

**Files:**
- Modify: `lib/a2p_values.py` (append function)
- Test: `tests/test_a2p_values.py` (append)

- [ ] **Step 1: Append failing tests**

Insert above the standalone runner:

```python
from lib.a2p_values import apply_values


def _full_value_map():
    return {slug: ("VAL_" + slug) for slug, _n, _c in A2P_VALUE_KEYS}


def test_apply_values_creates_all_when_none_exist():
    client = _FakeClient({"customValues": []})
    rep = apply_values(client, "LOC", _full_value_map())
    assert len(rep["created"]) == 18 and rep["updated"] == [] and rep["skipped"] == [] and rep["errors"] == []
    posts = [c for c in client.calls if c[0] == "POST"]
    assert len(posts) == 18
    # body uses the canonical name + the value
    first = posts[0]
    assert first[1] == "/locations/LOC/customValues/"
    assert set(first[2].keys()) == {"name", "value"}
    assert rep["resolved"]["logo"] == "VAL_logo"


def test_apply_values_updates_when_all_exist():
    existing = {"customValues": [
        _cv_item(name, slug, "old") for slug, name, _c in A2P_VALUE_KEYS
    ]}
    client = _FakeClient(existing)
    rep = apply_values(client, "LOC", _full_value_map())
    assert len(rep["updated"]) == 18 and rep["created"] == [] and rep["errors"] == []
    puts = [c for c in client.calls if c[0] == "PUT"]
    assert len(puts) == 18
    assert puts[0][1] == "/locations/LOC/customValues/id_" + A2P_VALUE_KEYS[0][0]
    assert puts[0][2] == {"name": A2P_VALUE_KEYS[0][1], "value": "VAL_" + A2P_VALUE_KEYS[0][0]}


def test_apply_values_skips_blank_and_missing_values():
    client = _FakeClient({"customValues": [_cv_item(n, s, "old") for s, n, _c in A2P_VALUE_KEYS]})
    vm = {"logo": "{{location.logo_url}}", "primary_color": "   ", "from_email": ""}  # rest absent
    rep = apply_values(client, "LOC", vm)
    assert rep["updated"] == ["logo"]
    assert len(rep["skipped"]) == 17
    skipped_slugs = {s for s, _r in rep["skipped"]}
    assert "primary_color" in skipped_slugs and "from_email" in skipped_slugs
    # only the GET + one PUT
    assert [c[0] for c in client.calls] == ["GET", "PUT"]


def test_apply_values_dry_run_makes_no_writes():
    client = _FakeClient({"customValues": [_cv_item("Logo", "logo", "old")]})  # only logo exists
    rep = apply_values(client, "LOC", _full_value_map(), dry_run=True)
    assert "logo" in rep["updated"]
    assert len(rep["created"]) == 17  # the other 17 would be created
    assert [c[0] for c in client.calls] == ["GET"]  # no POST/PUT


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
            return None  # GHLClient signals unrecoverable auth failure as None
    client = _AuthFail({"customValues": []})
    rep = apply_values(client, "LOC", {"logo": "x"})
    assert rep["errors"] and "auth" in rep["errors"][0][1].lower()


def test_apply_values_ignores_unknown_slugs():
    client = _FakeClient({"customValues": []})
    rep = apply_values(client, "LOC", {"bogus_slug": "x", "logo": "{{location.logo_url}}"})
    assert rep["created"] == ["logo"]
    assert all(c[0] != "POST" or c[2]["value"] == "{{location.logo_url}}" for c in client.calls)
    posts = [c for c in client.calls if c[0] == "POST"]
    assert len(posts) == 1
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 tests/test_a2p_values.py`
Expected: FAIL — `ImportError: cannot import name 'apply_values'`.

- [ ] **Step 3: Append `apply_values` to `lib/a2p_values.py`**

```python
def _new_report():
    return {"created": [], "updated": [], "skipped": [], "errors": [], "resolved": {}}


def apply_values(client, location_id, value_map, *, dry_run=False):
    """Create or update the 18 A2P custom values on `location_id`.

    value_map: {slug: value}. Slugs not in A2P_VALUE_KEYS are ignored. A value
    that is None or blank/whitespace is SKIPPED (never overwrites an existing
    non-empty value with empty). Existing values are updated via
    PUT /locations/{loc}/customValues/{id}; missing ones are created via
    POST /locations/{loc}/customValues/ (body {name, value}).

    Returns a Report dict:
        {"created": [slug,...], "updated": [slug,...],
         "skipped": [(slug, reason),...], "errors": [(slug, message),...],
         "resolved": {slug: value,...}}   # values that had content (for display)
    """
    existing = fetch_custom_values(client, location_id)
    report = _new_report()
    for slug, canonical_name, _cat in A2P_VALUE_KEYS:
        raw = value_map.get(slug)
        value = ("" if raw is None else str(raw)).strip()
        if not value:
            report["skipped"].append((slug, "no value"))
            continue
        report["resolved"][slug] = value
        cur = existing.get(slug)
        if dry_run:
            (report["updated"] if (cur and cur.get("id")) else report["created"]).append(slug)
            continue
        if cur and cur.get("id"):
            res = client.request(
                "PUT", "/locations/%s/customValues/%s" % (location_id, cur["id"]),
                {"name": cur.get("name") or canonical_name, "value": value},
            )
            bucket = "updated"
        else:
            res = client.request(
                "POST", "/locations/%s/customValues/" % location_id,
                {"name": canonical_name, "value": value},
            )
            bucket = "created"
        if res is None:
            report["errors"].append((slug, "auth failed (could not refresh token)"))
        elif isinstance(res, dict) and res.get("_error"):
            report["errors"].append((slug, "HTTP %s: %s" % (res.get("code"), res.get("message"))))
        else:
            report[bucket].append(slug)
    return report
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 tests/test_a2p_values.py`
Expected: `15/15 passed`

- [ ] **Step 5: Stage / commit**

```bash
git add lib/a2p_values.py tests/test_a2p_values.py
git commit -m "feat(a2p): apply_values (create/update/skip + report)"
```

---

## Task 5: `scripts/a2p_scrape.py`

**Files:**
- Create: `scripts/a2p_scrape.py`
- Create: `tests/fixtures/sample_business.html`
- Create: `tests/test_a2p_scrape.py`

- [ ] **Step 1: Create the fixture `tests/fixtures/sample_business.html`**

```html
<!doctype html>
<html>
<head>
  <title>Acme Aesthetics &amp; Wellness — Franklin, TN</title>
  <meta name="description" content="Acme Aesthetics is a med spa in Franklin, TN offering injectables, facials, and laser treatments.">
  <style>:root{--brand:#1a2b3c} a{color:#ff6600}</style>
  <script>var x = "#000000 should be ignored";</script>
</head>
<body>
  <h1>Welcome to Acme Aesthetics</h1>
  <p>Call us at (615) 555-0123 or email hello@acmeaesthetics.com.</p>
  <h2>Our Services</h2>
  <h3>Botox &amp; Fillers</h3>
  <p>Smooth lines and restore volume.</p>
</body>
</html>
```

- [ ] **Step 2: Write the failing test — `tests/test_a2p_scrape.py`**

```python
#!/usr/bin/env python3
"""
a2p_scrape — fixture test for HTML parsing (no network).
Run: python3 tests/test_a2p_scrape.py   (standalone)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from a2p_scrape import parse_html

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_business.html")


def test_parse_html_extracts_core_fields():
    html = open(FIXTURE, encoding="utf-8").read()
    d = parse_html(html, "https://acmeaesthetics.com")
    assert d["url"] == "https://acmeaesthetics.com"
    assert "Acme Aesthetics" in d["title"] and "Franklin, TN" in d["title"]
    assert "med spa in Franklin" in d["meta_description"]
    assert "Welcome to Acme Aesthetics" in d["headings"]
    assert "Botox & Fillers" in d["headings"]
    assert d["candidate_email"] == "hello@acmeaesthetics.com"
    assert d["candidate_phone"] == "(615) 555-0123"
    assert "#1a2b3c" in d["candidate_colors"] and "#ff6600" in d["candidate_colors"]
    assert "#000000" not in d["candidate_colors"]            # came from a <script>, must be skipped
    assert "Smooth lines and restore volume." in d["text"]
    assert "should be ignored" not in d["text"]              # <script> body excluded


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
```

- [ ] **Step 3: Run to verify it fails**

Run: `python3 tests/test_a2p_scrape.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'a2p_scrape'`.

- [ ] **Step 4: Create `scripts/a2p_scrape.py`**

```python
#!/usr/bin/env python3
"""
Scrape a business website into compact JSON for A2P custom-value generation.

Usage:  python3 scripts/a2p_scrape.py <url>
Prints JSON to stdout:
  {url, title, meta_description, headings[], candidate_email, candidate_emails[],
   candidate_phone, candidate_phones[], candidate_colors[], text}
On failure prints {"error": "..."} to stdout and exits 1. Stdlib only.
"""
import json
import re
import ssl
import sys
import urllib.request
from html.parser import HTMLParser

CHROME_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
_CTX = ssl.create_default_context()
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}")
_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
_SKIP_TAGS = {"script", "style", "noscript", "head", "svg"}
_HEADING_TAGS = {"h1", "h2", "h3"}
_TEXT_BUDGET = 8000


class _Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self._title_parts = []
        self._in_title = False
        self._skip_depth = 0
        self.meta_description = ""
        self.headings = []
        self._h_tag = None
        self._h_parts = []
        self._text_parts = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta" and (d.get("name", "").lower() == "description") and not self.meta_description:
            self.meta_description = d.get("content", "") or ""
        if tag in _HEADING_TAGS and self._skip_depth == 0:
            self._h_tag, self._h_parts = tag, []

    def handle_startendtag(self, tag, attrs):
        # <meta .../> self-closing
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in _HEADING_TAGS and self._h_tag == tag:
            txt = " ".join("".join(self._h_parts).split())
            if txt:
                self.headings.append(txt)
            self._h_tag, self._h_parts = None, []

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._h_tag:
            self._h_parts.append(data)
        if self._skip_depth == 0:
            s = data.strip()
            if s:
                self._text_parts.append(s)

    @property
    def title(self):
        return " ".join("".join(self._title_parts).split())

    @property
    def text(self):
        return " ".join(" ".join(self._text_parts).split())


def parse_html(html, url):
    """Pure HTML -> dict. Colours come from the raw HTML (CSS) but text/headings
    exclude <script>/<style>/<head> content."""
    p = _Extract()
    p.feed(html)
    emails = sorted({m.group(0).lower() for m in _EMAIL_RE.finditer(html)})
    phones = sorted({m.group(0) for m in _PHONE_RE.finditer(p.text)})
    # only count hex colours that appear OUTSIDE <script> blocks
    no_script = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    colors = sorted({m.group(0).lower() for m in _HEX_RE.finditer(no_script)})
    return {
        "url": url,
        "title": p.title,
        "meta_description": p.meta_description.strip(),
        "headings": p.headings[:40],
        "candidate_email": emails[0] if emails else "",
        "candidate_emails": emails[:10],
        "candidate_phone": phones[0] if phones else "",
        "candidate_phones": phones[:10],
        "candidate_colors": colors[:20],
        "text": p.text[:_TEXT_BUDGET],
    }


def scrape(url):
    req = urllib.request.Request(url, headers={"User-Agent": CHROME_UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, context=_CTX, timeout=20) as resp:
        raw = resp.read()
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("latin-1", errors="replace")
    return parse_html(html, url)


def main(argv):
    if len(argv) < 2 or not argv[1].strip():
        print(json.dumps({"error": "usage: a2p_scrape.py <url>"}))
        return 1
    try:
        print(json.dumps(scrape(argv[1].strip()), ensure_ascii=False))
        return 0
    except Exception as e:  # noqa: BLE001 — surface any fetch/parse failure as JSON
        print(json.dumps({"error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 tests/test_a2p_scrape.py`
Expected: `1/1 passed`

- [ ] **Step 6: Stage / commit**

```bash
git add scripts/a2p_scrape.py tests/test_a2p_scrape.py tests/fixtures/sample_business.html
git commit -m "feat(a2p): a2p_scrape.py — URL -> compact business JSON"
```

---

## Task 6: `scripts/a2p_apply.py` (thin CLI)

**Files:**
- Create: `scripts/a2p_apply.py`
- Test: `tests/test_a2p_values.py` (append CLI error-path tests)

- [ ] **Step 1: Append failing tests to `tests/test_a2p_values.py`**

Insert above the standalone runner:

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import a2p_apply  # noqa: E402


def test_apply_cli_missing_value_map_file_exits_2():
    rc = a2p_apply.main(["LOC", "/no/such/file.json"])
    assert rc == 2


def test_apply_cli_non_object_value_map_exits_2(tmp_path=None):
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, b"[1, 2, 3]")
    os.close(fd)
    try:
        rc = a2p_apply.main(["LOC", path])
        assert rc == 2
    finally:
        os.unlink(path)


def test_apply_cli_dry_run_with_fake_client(monkeypatch=None):
    # patch make_client inside a2p_apply to return a fake, run a real --dry-run pass
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, json.dumps({"logo": "{{location.logo_url}}"}).encode())
    os.close(fd)
    orig = a2p_apply.make_client
    a2p_apply.make_client = lambda loc, refresh_token=None: _FakeClient({"customValues": []})
    try:
        rc = a2p_apply.main(["LOC", path, "--dry-run"])
        assert rc == 0   # no errors on a dry run
    finally:
        a2p_apply.make_client = orig
        os.unlink(path)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 tests/test_a2p_values.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'a2p_apply'`.

- [ ] **Step 3: Create `scripts/a2p_apply.py`**

```python
#!/usr/bin/env python3
"""
Apply a value-map JSON to a GHL location's A2P custom values.

Usage:
  python3 scripts/a2p_apply.py <location_id> <value_map.json> [--dry-run] [--refresh-token=TOKEN]

  <value_map.json>   a JSON object {slug: value, ...}; only the 18 A2P slugs are used.
  --dry-run          classify create/update/skip without writing anything.
  --refresh-token    a client's GHL Firebase refresh token (for non-DLF agency
                     sub-accounts); defaults to $GHL_FIREBASE_REFRESH_TOKEN.

Exit codes: 0 = ok, 1 = one or more values errored, 2 = bad arguments / unreadable value map.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.a2p_values import make_client, apply_values  # noqa: E402

_FLAG_FACTS = ("business_profile__legal_business_name", "business_profile__phone_number", "from_email")


def _parse_args(argv):
    ap = argparse.ArgumentParser(prog="a2p_apply.py", add_help=True)
    ap.add_argument("location_id")
    ap.add_argument("value_map", help="path to JSON file: {slug: value, ...}")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh-token", dest="refresh_token",
                    default=os.environ.get("GHL_FIREBASE_REFRESH_TOKEN", "") or None)
    return ap.parse_args(argv)


def _print_report(report, dry_run):
    tag = "[DRY RUN] " if dry_run else ""
    print("\n%sA2P custom values — %d value(s) to write\n" % (tag, len(report["resolved"])))
    for slug in report["created"]:
        print("  + create  %-40s = %r" % (slug, report["resolved"].get(slug, "")[:80]))
    for slug in report["updated"]:
        print("  ~ update  %-40s = %r" % (slug, report["resolved"].get(slug, "")[:80]))
    for slug, reason in report["skipped"]:
        print("  . skip    %-40s (%s)" % (slug, reason))
    for slug, msg in report["errors"]:
        print("  ! ERROR   %-40s %s" % (slug, msg))
    blanks = {s for s, _r in report["skipped"]}
    flagged = [s for s in _FLAG_FACTS if s in blanks]
    if flagged:
        print("\n  /!\\ set these manually (not derivable from URL/brief): %s" % ", ".join(flagged))
    print("\n  created=%d updated=%d skipped=%d errors=%d\n" % (
        len(report["created"]), len(report["updated"]), len(report["skipped"]), len(report["errors"])))


def main(argv):
    args = _parse_args(argv)
    try:
        with open(args.value_map) as f:
            value_map = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print("ERROR: cannot read value map %s: %s" % (args.value_map, e), file=sys.stderr)
        return 2
    if not isinstance(value_map, dict):
        print("ERROR: value map must be a JSON object {slug: value, ...}", file=sys.stderr)
        return 2
    client = make_client(args.location_id, refresh_token=args.refresh_token)
    report = apply_values(client, args.location_id, value_map, dry_run=args.dry_run)
    _print_report(report, args.dry_run)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 tests/test_a2p_values.py`
Expected: `18/18 passed`

- [ ] **Step 5: Stage / commit**

```bash
git add scripts/a2p_apply.py tests/test_a2p_values.py
git commit -m "feat(a2p): a2p_apply.py CLI (dry-run, refresh-token)"
```

---

## Task 7: `.claude/commands/a2p-fill-values.md` (the skill)

**Files:**
- Create: `.claude/commands/a2p-fill-values.md`

No automated test (it is a prompt document). Verified by the manual smoke test in Task 8.

- [ ] **Step 1: Create `.claude/commands/a2p-fill-values.md`**

```markdown
# /a2p-fill-values

**Usage:** `/a2p-fill-values <business_url> <location_id> [--client <slug>] [--refresh-token <token>]`

Populate the 18 custom values that the pre-built "A2P Landing Page" funnel + opt-in form
reference on a GHL sub-account. Scrapes the business website, optionally reads a vault
brief, generates the on-brand copy, previews everything as a dry run, then writes it.

**Does NOT touch** the funnel pages, the opt-in form, the other ~58 custom values, or any
workflow — those merge-tag off these 18 values and never change.

Examples:
- `/a2p-fill-values https://aprestigeaesthetics.com 9uog1fOUDtxkSr4ZPx1i --client prestige`
- `/a2p-fill-values https://example-medspa.com abc123LOCID`

---

## The 18 values (see `lib/a2p_values.py:A2P_VALUE_KEYS` for the canonical list)

Facts (resolve in priority order — brief → location API → site): `business_short_name`,
`business_profile__legal_business_name`, `business_profile__phone_number`, `from_email`,
`logo` (always the literal `{{location.logo_url}}`), `primary_color`, `secondary_color__hex_code`.

Copy (you generate from the scraped site + brief, in DLF brand voice — see `business/` for
voice/positioning if present): `about_us__description`, `business_welcome_message`,
`business_solution__description`, `our_services_1..4`, `our_services_1..4__description`.

## Steps

1. **Scrape the site** — run `python3 scripts/a2p_scrape.py <business_url>` and read the JSON.
   If it returns `{"error": ...}`, note it and continue with brief-only (you will flag the
   facts you can't source).

2. **Read the brief (optional)** — if `--client <slug>` was given, read whichever of these
   exist: `clients/<slug>/overview.md`, `clients/<slug>/services.md`. (`overview.md` may also
   carry `ghl_location_id` — sanity-check it against the `<location_id>` arg.)

3. **Resolve the 7 facts:**
   - `business_short_name` — the friendly trading name (brief > site `<title>` cleaned up).
   - `business_profile__legal_business_name` — the registered legal entity. Only from the
     brief. If absent, leave it BLANK — `a2p_apply.py` will flag it for the user to set from
     the Twilio registration. Never guess this.
   - `business_profile__phone_number` — brief first. If absent, you may leave blank (flagged);
     do not invent one. (A future enhancement may pull the location's purchased number via API.)
   - `from_email` — brief first; else `info@<registrable-domain-of-business_url>`.
   - `logo` — always the literal string `{{location.logo_url}}`.
   - `primary_color` / `secondary_color__hex_code` — pick from the scrape's `candidate_colors`
     only if you are reasonably confident they are brand colours (ignore obvious black/white/grey
     unless the brand clearly uses them). Otherwise leave blank — better empty than wrong.

4. **Write the 11 copy values** from the scraped `headings`/`text`/`meta_description` + brief,
   in DLF brand voice. Keep `our_services_N` to a short headline line and `our_services_N__description`
   to one sentence. If the business clearly offers fewer than 4 services, fill what's real and
   leave the rest blank (they'll be skipped, not blanked).

5. **Write the value map** to `/tmp/a2p-values-<location_id>.json` — a JSON object `{slug: value}`
   containing only the slugs you have content for.

6. **Dry run** — run:
   `python3 scripts/a2p_apply.py <location_id> /tmp/a2p-values-<location_id>.json --dry-run [--refresh-token <token>]`
   Show the user the full proposed value map and the dry-run report. Call out anything flagged
   for manual entry. For a non-DLF agency sub-account (e.g. Prestige), the `--refresh-token` is
   required (see the 'Non-DLF Agency deploy auth' memory).

7. **On the user's OK** — re-run the same command WITHOUT `--dry-run`. Report the result.

8. **Log it** — append a completion entry to `drleadflow/blade-ops/contents/logs/dev-activity.json`
   per this repo's `CLAUDE.md` (`message: "A2P custom values populated for <client/loc>"`).

## Notes

- Idempotent — safe to re-run; values that didn't change get PUT with the same content.
- If you see GHL `401`s for a non-DLF agency location, you forgot `--refresh-token` (or the
  broker/MCP has a DLF token cached — `make_client` already sets `prefer_refresh_token` when a
  refresh token is passed, which suppresses the broker but not the MCP fallback; if it still
  fails, run from a shell with `GHL_TOKEN_BROKER_*` unset).
```

- [ ] **Step 2: Stage / commit**

```bash
git add .claude/commands/a2p-fill-values.md
git commit -m "feat(a2p): /a2p-fill-values skill"
```

---

## Task 8: Manual smoke test against the reference location (Prestige)

**Files:** none (verification only).

**Requires:** a working token path. Prestige (`9uog1fOUDtxkSr4ZPx1i`) is on a non-DLF agency, so you need its `GHL_FIREBASE_REFRESH_TOKEN`. If you don't have it, **skip this task and note it** — the automated tests already cover the logic; this just confirms endpoint shapes against real data.

- [ ] **Step 1: Dump Prestige's current 18 values into a value-map JSON**

```bash
cd /Users/bleupreneur/Desktop/GITHUB/GHL-Superspeed-V3-Better-Version
set -a; [ -f .env ] && . ./.env; set +a
python3 - <<'PY'
import sys, json
sys.path.insert(0, "lib")
from a2p_values import make_client, fetch_custom_values, A2P_VALUE_KEYS
LOC = "9uog1fOUDtxkSr4ZPx1i"
import os
rt = os.environ.get("PRESTIGE_GHL_FIREBASE_REFRESH_TOKEN") or os.environ.get("GHL_FIREBASE_REFRESH_TOKEN")
c = make_client(LOC, refresh_token=rt)
cur = fetch_custom_values(c, LOC)
vm = {slug: cur[slug]["value"] for slug, _n, _c in A2P_VALUE_KEYS if slug in cur and cur[slug]["value"]}
json.dump(vm, open("/tmp/prestige-current.json", "w"), indent=2)
print("wrote /tmp/prestige-current.json with", len(vm), "non-empty values; slugs:", sorted(vm))
PY
```
Expected: prints ~10–13 non-empty slugs (the copy values + names/email on Prestige; `primary_color` etc. are empty there).

- [ ] **Step 2: Dry-run apply**

```bash
python3 scripts/a2p_apply.py 9uog1fOUDtxkSr4ZPx1i /tmp/prestige-current.json --dry-run --refresh-token "$PRESTIGE_GHL_FIREBASE_REFRESH_TOKEN"
```
Expected: every slug present in the JSON classifies as `~ update` (proves fieldKey matching against real data); slugs absent from the JSON are not reported (they weren't in the map). `errors=0`.

- [ ] **Step 3: One real write (no-op value) to confirm the PUT path**

```bash
echo '{"logo": "{{location.logo_url}}"}' > /tmp/prestige-logo-only.json
python3 scripts/a2p_apply.py 9uog1fOUDtxkSr4ZPx1i /tmp/prestige-logo-only.json --refresh-token "$PRESTIGE_GHL_FIREBASE_REFRESH_TOKEN"
```
Expected: `updated=1 errors=0`. (Visually a no-op — `logo` was already `{{location.logo_url}}`.) If this returns an HTTP 4xx, the PUT body shape (`{name, value}`) or path is wrong — fix `apply_values` and re-run the unit tests + this step.

- [ ] **Step 4: Record the outcome**

If all three steps passed, note it in the PR/commit description. If Step 3 revealed a body-shape problem, the fix goes back into Task 4's `apply_values` (and a regression test into `tests/test_a2p_values.py`).

---

## Task 9: README skills-table entry

**Files:**
- Modify: `README.md` (one row in the commands/skills list, wherever `/build-campaign-skeleton` is listed)

- [ ] **Step 1: Add the row**

Find the table or list that documents the slash commands (it includes `/build-campaign-skeleton`, `/extract-offer`, etc.) and add:

```markdown
| `/a2p-fill-values <url> <location_id> [--client <slug>] [--refresh-token <t>]` | Populate the 18 custom values the A2P landing-page funnel + opt-in form use, from a business URL + optional vault brief. Dry-run preview, then apply. |
```

(Match the existing table's column layout; if the docs use a bulleted list instead of a table, add a matching bullet.)

- [ ] **Step 2: Stage / commit**

```bash
git add README.md
git commit -m "docs: document /a2p-fill-values"
```

---

## Final verification

- [ ] `python3 tests/test_a2p_values.py` → `18/18 passed`
- [ ] `python3 tests/test_a2p_scrape.py` → `1/1 passed`
- [ ] `python3 tests/test_engine.py` → still all green (the `TokenManager` change didn't break anything)
- [ ] `python3 -c "import sys; sys.path.insert(0,'scripts'); import a2p_scrape, a2p_apply; print('imports ok')"`
- [ ] Task 8 smoke test passed (or explicitly skipped + noted because the Prestige refresh token wasn't available)
- [ ] Commits squashed/landed per the owner's preference (the owner runs `git commit` / merges; do not push)

---

## Self-review (completed by plan author)

**Spec coverage:**
- 18 values + fact/copy split → Task 2 (`A2P_VALUE_KEYS`), Task 7 (skill resolves them). ✓
- create-missing / update-existing / skip-blank, never overwrite with empty → Task 4 (`apply_values`) + tests. ✓
- reuse `engine.GHLClient`/`TokenManager`, `--refresh-token` for non-DLF → Task 1 (`prefer_refresh_token`) + Task 2 (`make_client`). ✓
- token-lean URL→JSON → Task 5 (`a2p_scrape.py`). ✓
- thin CLI with `--dry-run` → Task 6 (`a2p_apply.py`). ✓
- orchestrating skill: scrape → brief → LLM copy → dry-run → apply → blade-ops log → Task 7. ✓
- error handling (blank→skip+flag legal name, 401 guidance, empty-200 tolerated, scrape-fail→brief-only, idempotent) → covered in `apply_values` (Task 4), `a2p_apply._print_report` flag block (Task 6), skill notes (Task 7). ✓
- testing: `apply_values` against fake client, scrape fixture test, manual Prestige smoke → Tasks 4, 5, 8. ✓
- spec's 3 open assumptions: PUT/POST body shape is exercised in Task 8 Step 3 (with a fix-loop); GHL-renders-custom-values-in-form-labels is explicitly out of scope (noted in skill); pulling the location's phone via API is left as a future enhancement (skill step 3 says "may leave blank/flagged"). ✓

**Placeholder scan:** no "TBD/TODO/handle edge cases/similar to Task N" — every code step has complete code. ✓

**Type/name consistency:** `make_client(location_id, refresh_token=None)`, `fetch_custom_values(client, location_id)`, `apply_values(client, location_id, value_map, *, dry_run=False)`, Report keys `created/updated/skipped/errors/resolved`, `parse_html(html, url)` — used identically across Tasks 2–8 and the skill doc. `_FakeClient` defined once (Task 3) and reused in Tasks 4 & 6. ✓
