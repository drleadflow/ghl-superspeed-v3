#!/usr/bin/env python3
"""Create or update LOCATION custom values on a GHL sub-account.

Usage:
  python3 scripts/set_custom_values.py <location_id> slug=value [slug=value ...]

Example:
  python3 scripts/set_custom_values.py 9uog1fOUDtxkSr4ZPx1i \\
      text_message_name=Ashley booking_link=https://go.x.com/cal

The slug is what the copy merges ({{custom_values.<slug>}}). GHL derives the
slug from the display name, so this passes name = Title-Cased slug (e.g.
"booking_link" -> "Booking Link" -> slug booking_link). Existing values are
updated in place; missing ones are created. Re-fetches and prints the result.

Gotchas:
- Needs the lowercase `version: 2021-07-28` header (handled by lib.a2p_values).
- A blank value is skipped (never overwrites a non-empty value with empty).
- Title-casing must round-trip to the slug you want; for odd slugs set the
  value manually in the GHL UI instead.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ghl import client  # noqa: E402

_CV_HEADERS = {"version": "2021-07-28"}


def main(argv):
    if len(argv) < 2 or "=" not in "".join(argv[1:]):
        print(__doc__)
        return 2
    loc = argv[0]
    pairs = []
    for a in argv[1:]:
        if "=" not in a:
            print(f"skip (no '='): {a}")
            continue
        slug, val = a.split("=", 1)
        pairs.append((slug.strip(), val))
    c = client(loc)
    from lib.a2p_values import fetch_custom_values
    existing = fetch_custom_values(c, loc)
    for slug, val in pairs:
        name = slug.replace("_", " ").title()
        if not val.strip():
            print(f"skip {slug}: blank value")
            continue
        cur = existing.get(slug)
        if cur and cur.get("id"):
            r = c.request("PUT", f"/locations/{loc}/customValues/{cur['id']}",
                          {"name": cur.get("name") or name, "value": val},
                          extra_headers=_CV_HEADERS)
            act = "updated"
        else:
            r = c.request("POST", f"/locations/{loc}/customValues/",
                          {"name": name, "value": val}, extra_headers=_CV_HEADERS)
            act = "created"
        ok = (r is None) or (isinstance(r, dict) and not r.get("_error"))
        print(f"{act:8} {slug:24} -> {'OK' if ok else r}")
    print("\n--- verify ---")
    after = fetch_custom_values(c, loc)
    for slug, _ in pairs:
        v = after.get(slug)
        print(f"  {slug:24} present={slug in after}  value={(v or {}).get('value')!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
