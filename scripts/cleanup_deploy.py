#!/usr/bin/env python3
"""Delete a campaign's workflows (+ their triggers) and folder, for a clean redeploy.

Re-running a campaign .py creates DUPLICATES (the engine has no update mode), so
before redeploying a partially-failed build, wipe it with this.

Usage:
  python3 scripts/cleanup_deploy.py <location_id> --folder "Folder Name"
  python3 scripts/cleanup_deploy.py <location_id> --folder-id <folder_id>
  python3 scripts/cleanup_deploy.py <location_id> <wf_id> [wf_id ...]

Deletes each workflow's triggers first (avoids 409 on recreate), then the
workflows, then the folder (folder mode only). DESTRUCTIVE — only target a
build you just created.

Gotchas:
- Delete triggers BEFORE workflows; lingering triggers 409 on the next deploy.
- Folder mode deletes ALL workflows under the named folder.
- COLLISION GUARD: `--folder` substring-matched and silently deleted the FIRST
  match. A failed redeploy leaves a SECOND folder with the SAME name as the
  prior (live) build, so `--folder` could wipe the live one. This now ABORTS if
  the name matches more than one folder and prints their IDs — pass `--folder-id`
  to target one exactly. (Real incident 2026-06-03: deleted a live v1 folder.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ghl import client  # noqa: E402


def _del_triggers(c, loc, wid):
    tr = c.request("GET", f"/workflow/{loc}/trigger?workflowId={wid}")
    trs = tr if isinstance(tr, list) else (tr.get("triggers") if isinstance(tr, dict) else [])
    n = 0
    for t in (trs or []):
        if t.get("id"):
            c.request("DELETE", f"/workflow/{loc}/trigger/{t['id']}")
            n += 1
    return n


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    loc = argv[0]
    c = client(loc)
    folder_id = None
    if argv[1] == "--folder-id":
        folder_id = argv[2]
    elif argv[1] == "--folder":
        name = argv[2]
        idx = c.request("GET", f"/workflow/{loc}/list?parentId=root&limit=200")
        matches = [row for row in (idx.get("rows") or [])
                   if row.get("type") == "directory" and name in (row.get("name") or "")]
        if not matches:
            print(f"No folder matching {name!r}")
            return 1
        if len(matches) > 1:
            print(f"ABORT: {len(matches)} folders match {name!r} — refusing to "
                  f"guess which to delete. Re-run with --folder-id <id>:")
            for m in matches:
                print(f"  --folder-id {m['id']}   ({m.get('name')!r})")
            return 1
        folder_id = matches[0]["id"]
    if folder_id:
        kids = c.request("GET", f"/workflow/{loc}/list?parentId={folder_id}&limit=200")
        wf_ids = [r["id"] for r in (kids.get("rows") or []) if r.get("type") == "workflow"]
    else:
        wf_ids = argv[1:]

    for wid in wf_ids:
        n = _del_triggers(c, loc, wid)
        r = c.request("DELETE", f"/workflow/{loc}/{wid}")
        ok = (r is None) or (isinstance(r, dict) and not r.get("_error"))
        print(f"deleted wf {wid} (+{n} triggers) -> {'OK' if ok else r}")
    if folder_id:
        r = c.request("DELETE", f"/workflow/{loc}/{folder_id}")
        ok = (r is None) or (isinstance(r, dict) and not r.get("_error"))
        print(f"deleted folder {folder_id} -> {'OK' if ok else r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
