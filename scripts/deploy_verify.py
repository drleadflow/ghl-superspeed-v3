#!/usr/bin/env python3
"""Verify a deployed campaign: step counts + trigger-linked status (READ-ONLY).

Usage:
  python3 scripts/deploy_verify.py <location_id> --folder "Folder Name"
  python3 scripts/deploy_verify.py <location_id> <wf_id> [wf_id ...]

For each workflow prints: step count, type tally, and whether its trigger is
LINKED to the first step (an unlinked trigger floats and never fires). Exits 0
only if every workflow has >=1 step AND exactly one LINKED trigger.

Gotchas:
- Steps live in `workflowData.templates`, not a top-level `steps` key.
- A workflow with a shell but 0 steps means its step batch failed on save
  (often a single rejected action type aborts the whole batch).
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ghl import client  # noqa: E402


def _wf_ids_in_folder(c, loc, folder_name):
    idx = c.request("GET", f"/workflow/{loc}/list?parentId=root&limit=200")
    folder_id = None
    for row in (idx.get("rows") or []):
        if row.get("type") == "directory" and folder_name in (row.get("name") or ""):
            folder_id = row["id"]
            break
    if not folder_id:
        return []
    kids = c.request("GET", f"/workflow/{loc}/list?parentId={folder_id}&limit=200")
    return [r["id"] for r in (kids.get("rows") or []) if r.get("type") == "workflow"]


def verify(c, loc, wf_ids):
    all_ok = True
    for wid in wf_ids:
        g = c.request("GET", f"/workflow/{loc}/{wid}")
        name = g.get("name") if isinstance(g, dict) else wid
        tpl = (g.get("workflowData") or {}).get("templates") or []
        first = tpl[0]["id"] if tpl else None
        tr = c.request("GET", f"/workflow/{loc}/trigger?workflowId={wid}")
        trs = tr if isinstance(tr, list) else (tr.get("triggers") if isinstance(tr, dict) else [])
        trs = trs or []
        linked = len(trs) == 1 and trs[0].get("targetActionId") == first
        ok = len(tpl) > 0 and linked
        all_ok = all_ok and ok
        cc = dict(Counter(s.get("type") for s in tpl))
        print(f"{'OK ' if ok else 'BAD'} | {name}")
        print(f"      steps={len(tpl)} {cc}")
        for t in trs:
            ln = "LINKED" if t.get("targetActionId") == first else "UNLINKED"
            print(f"      trigger {t.get('type')} {ln}")
        if not trs:
            print("      trigger NONE")
    print("\nALL GOOD:", all_ok)
    return all_ok


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    loc = argv[0]
    c = client(loc)
    if argv[1] == "--folder":
        wf_ids = _wf_ids_in_folder(c, loc, argv[2])
        if not wf_ids:
            print(f"No workflows found in folder matching {argv[2]!r}")
            return 1
    else:
        wf_ids = argv[1:]
    return 0 if verify(c, loc, wf_ids) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
