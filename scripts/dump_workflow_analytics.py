#!/usr/bin/env python3
"""
Pull workflow-level analytics for a GHL location and merge with an existing
structural dump (produced by scripts/dump_workflows.py).

For each workflow we capture:
  - total enrollments ever (from /workflows/status/search/enroll-stats-cache)
  - completed (`finished`)
  - currently active = total - finished
  - error count (from /workflow/{loc}/error-notification/count, location-wide)

Output:
  <out-dir>/_analytics.json   raw per-workflow counts + location totals
  <out-dir>/_analytics.md     readable report:
                                * location totals,
                                * top N by enrollment,
                                * zero-traffic workflows,
                                * per-folder breakdown

Per-step funnel data (where contacts fell off) is NOT in this dump — the GHL UI
loads it via a separate route inside the workflow-builder iframe that we have
not yet mapped. To unlock that, sniff one workflow's Enrollment History tab in
the live UI and add the endpoint here.

Usage:
  python3 scripts/dump_workflow_analytics.py <location_id> --out-dir DIR
          --id-token TOK [--batch-size 10]

  --id-token   a fresh Firebase id_token (token-id header value). Read from
               the page's IndexedDB firebaseLocalStorageDb, or from any XHR's
               token-id header. ~1h TTL.
  --refresh-token  Firebase refresh token (AMf-...). Used if id-token is absent.
"""
import argparse
import json
import os
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.engine import GHLClient, TokenManager  # noqa: E402


def build_client(location_id, id_token=None, refresh_token=None):
    tm = TokenManager(location_id)
    # Prefer id_token if both are provided — when the caller paste-passes a
    # token-id from a live request, it's authoritative for this run (an
    # ambient refresh_token from $GHL_FIREBASE_REFRESH_TOKEN may be stale).
    if id_token:
        tm._token = id_token  # noqa: SLF001
        tm._token_time = time.time()  # noqa: SLF001
    elif refresh_token:
        tm.set_refresh_token(refresh_token)
        tm.prefer_refresh_token = True
    return GHLClient(tm, location_id)


def fetch_enroll_stats(client, location_id, workflow_ids, batch_size=10):
    """Returns {wf_id: {total, finished}}."""
    out = {}
    # This endpoint enforces both `version` AND a referer/origin from the
    # workflows-app subdomain. Without all three a valid token-id still 401s.
    headers = {
        "version": "2021-04-15",
        "Origin": "https://client-app-automation-workflows.leadconnectorhq.com",
        "Referer": "https://client-app-automation-workflows.leadconnectorhq.com/",
    }
    for i in range(0, len(workflow_ids), batch_size):
        chunk = workflow_ids[i:i + batch_size]
        # GHL rejects raw brackets in the query — they MUST be URL-encoded as
        # %5B%5D. The live UI sends `workflowIds%5B%5D=...`.
        pairs = [("workflowIds[]", wid) for wid in chunk]
        pairs.append(("locationId", location_id))
        qs = urllib.parse.urlencode(pairs)
        path = "/workflows/status/search/enroll-stats-cache?" + qs
        resp = client.request("GET", path, extra_headers=headers)
        if not isinstance(resp, list):
            print(f"  ! enroll-stats batch failed: {resp}", file=sys.stderr)
            continue
        for row in resp:
            wid = row.get("workflowId")
            if wid:
                out[wid] = {
                    "total": int(row.get("total") or 0),
                    "finished": int(row.get("finished") or 0),
                }
    return out


def fetch_error_count(client, location_id):
    resp = client.request(
        "GET", f"/workflow/{location_id}/error-notification/count"
    )
    if isinstance(resp, int):
        return resp
    if isinstance(resp, dict):
        return int(resp.get("count") or resp.get("total") or 0)
    return None


def load_index(out_dir):
    """Read _index.json (from dump_workflows.py) for workflow id + folder data."""
    path = os.path.join(out_dir, "_index.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} missing — run scripts/dump_workflows.py first"
        )
    with open(path) as f:
        return json.load(f)


def render_md(analytics, idx):
    workflows = analytics["workflows"]
    totals = analytics["totals"]

    by_id = {w["id"]: w for w in idx["workflows"]}

    lines = [
        f"# Workflow analytics — location `{analytics['locationId']}`",
        "",
        f"_Pulled at {analytics['fetchedAt']}._",
        "",
        "## Totals",
        "",
        f"- Workflows: **{totals['workflow_count']}**",
        f"- Total enrollments (lifetime): **{totals['total_enrollments']:,}**",
        f"- Completed: **{totals['total_finished']:,}**",
        f"- Currently active: **{totals['total_active']:,}**",
        f"- Workflows with at least 1 enrollment: "
        f"**{totals['workflows_with_traffic']} / {totals['workflow_count']}**",
        f"- Workflows with zero enrollments: "
        f"**{totals['workflows_zero_traffic']}**",
        f"- Location-wide workflow errors awaiting review: "
        f"**{totals.get('error_notifications', 'n/a')}**",
        "",
    ]

    # Top N by total enrollment
    ranked = sorted(workflows.values(),
                    key=lambda w: w["total"], reverse=True)
    top_n = ranked[:20]
    lines.append("## Top 20 by lifetime enrollment")
    lines.append("")
    lines.append("| # | Workflow | Status | Total | Completed | Active |")
    lines.append("|---|----------|--------|------:|----------:|-------:|")
    for i, w in enumerate(top_n, 1):
        idx_w = by_id.get(w["id"], {})
        status = idx_w.get("status", "?")
        lines.append(
            f"| {i} | {w['name']} | `{status}` | "
            f"{w['total']:,} | {w['finished']:,} | {w['active']:,} |"
        )
    lines.append("")

    # Zero-traffic
    zero = [w for w in ranked if w["total"] == 0]
    if zero:
        lines.append(f"## Zero-enrollment workflows ({len(zero)})")
        lines.append("")
        lines.append("_Either drafts, deprecated, or genuinely unused._")
        lines.append("")
        for w in sorted(zero, key=lambda x: x["name"] or ""):
            idx_w = by_id.get(w["id"], {})
            status = idx_w.get("status", "?")
            lines.append(f"- {w['name']}  `{status}`  `{w['id']}`")
        lines.append("")

    # Per-folder breakdown
    by_folder = {}
    for w in workflows.values():
        idx_w = by_id.get(w["id"], {})
        folder = " / ".join(idx_w.get("path", []) or ["(root)"])
        by_folder.setdefault(folder, []).append(w)
    lines.append("## Per-folder breakdown")
    lines.append("")
    for fname in sorted(by_folder):
        items = by_folder[fname]
        f_total = sum(w["total"] for w in items)
        f_active = sum(w["active"] for w in items)
        lines.append(f"### {fname} — "
                     f"{len(items)} workflow(s) · "
                     f"{f_total:,} total enrollments · "
                     f"{f_active:,} active")
        lines.append("")
        lines.append("| Workflow | Status | Total | Completed | Active |")
        lines.append("|----------|--------|------:|----------:|-------:|")
        for w in sorted(items, key=lambda x: x["total"], reverse=True):
            idx_w = by_id.get(w["id"], {})
            status = idx_w.get("status", "?")
            lines.append(
                f"| {w['name']} | `{status}` | "
                f"{w['total']:,} | {w['finished']:,} | {w['active']:,} |"
            )
        lines.append("")

    return "\n".join(lines)


def main(argv):
    ap = argparse.ArgumentParser(prog="dump_workflow_analytics.py")
    ap.add_argument("location_id")
    ap.add_argument("--out-dir", required=True,
                    help="dump directory (must already contain _index.json)")
    ap.add_argument("--id-token",
                    default=os.environ.get("GHL_FIREBASE_TOKEN") or None)
    ap.add_argument("--refresh-token",
                    default=os.environ.get("GHL_FIREBASE_REFRESH_TOKEN")
                    or None)
    ap.add_argument("--batch-size", type=int, default=10)
    args = ap.parse_args(argv)

    if not (args.id_token or args.refresh_token):
        print("ERROR: --id-token or --refresh-token required.",
              file=sys.stderr)
        return 2

    idx = load_index(args.out_dir)
    workflow_ids = [w["id"] for w in idx["workflows"]]
    print(f"[analytics] {len(workflow_ids)} workflow(s) in index")

    client = build_client(args.location_id, id_token=args.id_token,
                          refresh_token=args.refresh_token)

    print("[analytics] fetching enrollment stats…")
    stats = fetch_enroll_stats(client, args.location_id, workflow_ids,
                               args.batch_size)
    print(f"[analytics] got stats for {len(stats)} / "
          f"{len(workflow_ids)} workflows")

    print("[analytics] fetching location-wide error count…")
    error_count = fetch_error_count(client, args.location_id)

    # Assemble per-workflow record
    workflows = {}
    for w in idx["workflows"]:
        wid = w["id"]
        s = stats.get(wid, {"total": 0, "finished": 0})
        workflows[wid] = {
            "id": wid,
            "name": w["name"],
            "total": s["total"],
            "finished": s["finished"],
            "active": max(0, s["total"] - s["finished"]),
        }

    totals = {
        "workflow_count": len(workflows),
        "total_enrollments": sum(w["total"] for w in workflows.values()),
        "total_finished": sum(w["finished"] for w in workflows.values()),
        "total_active": sum(w["active"] for w in workflows.values()),
        "workflows_with_traffic": sum(1 for w in workflows.values()
                                      if w["total"] > 0),
        "workflows_zero_traffic": sum(1 for w in workflows.values()
                                      if w["total"] == 0),
        "error_notifications": error_count,
    }

    analytics = {
        "locationId": args.location_id,
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "workflows": workflows,
        "totals": totals,
    }
    with open(os.path.join(args.out_dir, "_analytics.json"), "w") as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    with open(os.path.join(args.out_dir, "_analytics.md"), "w") as f:
        f.write(render_md(analytics, idx))

    print(f"\n[analytics] location totals:")
    print(f"  workflows:          {totals['workflow_count']}")
    print(f"  total enrollments:  {totals['total_enrollments']:,}")
    print(f"  completed:          {totals['total_finished']:,}")
    print(f"  active:             {totals['total_active']:,}")
    print(f"  zero-traffic:       {totals['workflows_zero_traffic']}")
    print(f"  errors (location):  {totals['error_notifications']}")
    print(f"\n[analytics] wrote _analytics.json + _analytics.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
