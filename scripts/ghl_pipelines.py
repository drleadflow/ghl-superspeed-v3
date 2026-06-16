#!/usr/bin/env python3
"""List opportunity pipelines + stages for a GHL location (READ-ONLY).

Usage:
  python3 scripts/ghl_pipelines.py <location_id> [--json]

Prints every pipeline as `name -> id` with each stage `name -> id`. Use the
IDs in a campaign's create_opportunity steps.

Gotchas:
- Hits backend `/opportunities/pipelines?locationId=` with the lowercase
  `version: 2021-07-28` header. Without that header you get 401
  "version header was not found"; the public services host rejects the
  Firebase JWT entirely.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ghl import client  # noqa: E402

_HDR = {"version": "2021-07-28"}


def get_pipelines(c, loc):
    r = c.request("GET", f"/opportunities/pipelines?locationId={loc}", extra_headers=_HDR)
    if not isinstance(r, dict) or r.get("_error"):
        raise RuntimeError(f"pipelines fetch failed: {r}")
    return r.get("pipelines") or r.get("data") or []


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    loc = argv[0]
    as_json = "--json" in argv
    c = client(loc)
    pls = get_pipelines(c, loc)
    if as_json:
        print(json.dumps(pls, indent=2))
        return 0
    for p in pls:
        print(f"\nPIPELINE  {p.get('name')!r}  id={p.get('id') or p.get('_id')}")
        for s in (p.get("stages") or []):
            print(f"   stage  {s.get('name')!r:38} id={s.get('id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
