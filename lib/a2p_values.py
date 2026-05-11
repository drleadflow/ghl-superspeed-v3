#!/usr/bin/env python3
"""
A2P custom-value populator — the deterministic GHL mechanics.

Given a GHL sub-account, ensure the 18 custom values that the pre-built
"A2P Landing Page" funnel + opt-in form reference are present and populated.
The funnel pages themselves are NOT touched — they merge-tag off these values.

Public API:
    A2P_VALUE_KEYS                               — the canonical 18 (slug, name, category)
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


def fetch_custom_values(client, location_id):
    """Fetch all custom values on the location, keyed by their `{{custom_values.<slug>}}` slug.

    Returns {slug: {"id": str, "name": str, "value": str}}.
    Raises RuntimeError if the API call fails.
    """
    resp = client.request("GET", "/locations/%s/customValues/" % location_id)
    if not isinstance(resp, dict) or resp.get("_error"):
        raise RuntimeError("Failed to fetch custom values for %s: %r" % (location_id, resp))
    items = resp.get("customValues") or resp.get("custom_values") or []
    total = resp.get("total")
    if total is not None and total != len(items):
        # This internal endpoint returns everything in one shot today; if that ever
        # changes, fail loudly rather than POST duplicates for the unseen page(s).
        raise RuntimeError(
            "custom values response for %s looks paginated: got %d of %d "
            "(fetch_custom_values does not page)" % (location_id, len(items), total)
        )
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
