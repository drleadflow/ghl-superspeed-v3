#!/usr/bin/env python3
"""
Read-only dump of every workflow in a GHL location.

Usage:
  python3 scripts/dump_workflows.py <location_id> --out-dir <dir> [--refresh-token TOK]
                                                 [--id-token TOK] [--limit N]

Auth (one of these must yield a valid token-id):
  --id-token TOK          a fresh Firebase id_token (~1h TTL); paste from the
                          browser after signInWithCustomToken
  --refresh-token TOK     a Firebase refresh token (starts AMf-...); the script
                          will exchange it on each token expiry
  $GHL_FIREBASE_TOKEN     same as --id-token
  $GHL_FIREBASE_REFRESH_TOKEN   same as --refresh-token

Writes (all under --out-dir):
  _index.json                                full hierarchy: folders + workflows
  _index.md                                  human-readable index
  workflows/<safe-name>__<wf-id>.json        raw workflow detail (incl. templates)
  workflows/<safe-name>__<wf-id>.triggers.json   raw trigger list
  workflows/<safe-name>__<wf-id>.md          readable report (trigger + every step)

Read-only: never POSTs/PUTs/DELETEs. Safe to run repeatedly.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.engine import GHLClient, TokenManager  # noqa: E402


# ── Utility ──────────────────────────────────────────────────────────────────

_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def _slug(s: str, maxlen: int = 60) -> str:
    s = (s or "").strip()
    s = _SAFE.sub("-", s).strip("-").lower()
    return (s[:maxlen] or "untitled").rstrip("-")


def _strip_html(html: str) -> str:
    """Loose tag stripper for previewing email HTML as plain text."""
    if not html:
        return ""
    # Drop <style> / <script> blocks entirely
    html = re.sub(r"<(style|script)\b[^>]*>.*?</\1>", "", html,
                  flags=re.IGNORECASE | re.DOTALL)
    # <br> and </p> → newline
    html = re.sub(r"<\s*br\s*/?\s*>", "\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</\s*p\s*>", "\n", html, flags=re.IGNORECASE)
    # Remaining tags
    html = re.sub(r"<[^>]+>", "", html)
    # Collapse whitespace
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    # Common entities
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'"))
    return html.strip()


# ── Auth glue ────────────────────────────────────────────────────────────────

def build_client(location_id: str, id_token: str = None,
                 refresh_token: str = None) -> GHLClient:
    tm = TokenManager(location_id)
    if refresh_token:
        tm.set_refresh_token(refresh_token)
        tm.prefer_refresh_token = True
    elif id_token:
        # Inject as a pre-baked token. The TokenManager treats this as fresh for
        # 50 minutes — long enough for a single dump run.
        tm._token = id_token  # noqa: SLF001
        tm._token_time = time.time()  # noqa: SLF001
    # else: fall through to broker / MCP / env — usually wrong for non-DLF agencies
    return GHLClient(tm, location_id)


# ── API helpers ──────────────────────────────────────────────────────────────

def list_children(client: GHLClient, location_id: str, parent_id: str) -> list:
    """List folders + workflows under parent_id (use 'root' for top level)."""
    rows = []
    offset = 0
    page = 200
    while True:
        qs = urllib.parse.urlencode({
            "parentId": parent_id, "limit": page, "offset": offset,
            "sortBy": "name", "sortOrder": "asc",
            "includeCustomObjects": "true", "includeObjectiveBuilder": "true",
        })
        resp = client.request("GET", f"/workflow/{location_id}/list?{qs}")
        if not resp or resp.get("_error"):
            print(f"  ! list failed parent={parent_id}: {resp}", file=sys.stderr)
            return rows
        batch = resp.get("rows", []) or []
        rows.extend(batch)
        total = resp.get("count")
        if total is None:
            if len(batch) < page:
                break
        elif len(rows) >= total:
            break
        if not batch:
            break
        offset += page
    return rows


def walk_tree(client: GHLClient, location_id: str) -> dict:
    """Walk root + every folder. Returns {folders: [...], workflows: [...]}."""
    folders, workflows = [], []

    def recurse(parent_id, parent_name, parent_path):
        rows = list_children(client, location_id, parent_id)
        for row in rows:
            row["_parentFolderId"] = None if parent_id == "root" else parent_id
            row["_parentFolderName"] = parent_name
            row["_path"] = parent_path
            if row.get("type") == "directory":
                folders.append(row)
                recurse(row["id"], row["name"], parent_path + [row["name"]])
            elif row.get("type") == "workflow":
                workflows.append(row)

    recurse("root", None, [])
    return {"folders": folders, "workflows": workflows}


def get_workflow_detail(client, location_id, wf_id):
    return client.request("GET", f"/workflow/{location_id}/{wf_id}")


def get_workflow_triggers(client, location_id, wf_id):
    resp = client.request(
        "GET", f"/workflow/{location_id}/trigger?workflowId={wf_id}"
    )
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict) and isinstance(resp.get("triggers"), list):
        return resp["triggers"]
    return []


# ── Markdown rendering ───────────────────────────────────────────────────────

def _fmt_wait(attrs):
    if not attrs:
        return "wait (no attributes)"
    if attrs.get("unit") and attrs.get("amount") is not None:
        return f"wait {attrs['amount']} {attrs['unit']}"
    if attrs.get("waitDateTime"):
        return f"wait until {attrs['waitDateTime']}"
    return "wait: " + json.dumps(attrs)[:200]


def _fmt_if_else_attrs(attrs):
    branches = attrs.get("branches") or []
    out = []
    for b in branches:
        seg_descs = []
        for seg in (b.get("segments") or []):
            for cond in (seg.get("conditions") or []):
                seg_descs.append(
                    f"{cond.get('conditionType','?')}:"
                    f"{cond.get('conditionSubType','')} "
                    f"{cond.get('conditionOperator','')} "
                    f"{cond.get('conditionValue','')}"
                )
        out.append(f"  - branch \"{b.get('name','?')}\": "
                   + ("; ".join(seg_descs) if seg_descs else "(no segments)"))
    return "\n".join(out) if out else "  (no branches)"


def render_step_md(t: dict) -> str:
    t_type = t.get("type") or "?"
    t_name = t.get("name") or "(unnamed)"
    attrs = t.get("attributes") or {}
    lines = [f"### [{t_type}] {t_name}"]

    if t_type == "email":
        subj = attrs.get("subject") or "(no subject)"
        from_name = attrs.get("fromName") or attrs.get("from_name") or ""
        from_email = attrs.get("fromEmail") or attrs.get("from_email") or ""
        html = attrs.get("html") or attrs.get("body") or ""
        lines.append(f"- From: {from_name} <{from_email}>")
        lines.append(f"- Subject: {subj}")
        plain = _strip_html(html)
        lines.append("")
        lines.append("**Body (text preview):**")
        lines.append("```")
        lines.append(plain[:4000] or "(empty)")
        lines.append("```")
        if html:
            lines.append("")
            lines.append("<details><summary>Raw HTML</summary>")
            lines.append("")
            lines.append("```html")
            lines.append(html[:8000])
            lines.append("```")
            lines.append("</details>")

    elif t_type == "sms":
        msg = attrs.get("message") or attrs.get("body") or ""
        lines.append("**Message:**")
        lines.append("```")
        lines.append(msg or "(empty)")
        lines.append("```")
        if attrs.get("attachments"):
            lines.append(f"- attachments: {attrs['attachments']}")

    elif t_type == "internal_notification":
        ch = attrs.get("type") or "?"  # 'sms' or 'email'
        sub = attrs.get(ch) or {}  # nested under attributes.sms / attributes.email
        recip = (sub.get("to") or sub.get("selectedUser")
                 or sub.get("userType") or "?")
        subj = sub.get("subject") or ""
        msg = sub.get("body") or sub.get("html") or ""
        lines.append(f"- channel: {ch}  recipient: {recip}")
        if sub.get("userType"):
            lines.append(f"- userType: {sub.get('userType')}")
        if subj:
            lines.append(f"- subject: {subj}")
        if msg:
            lines.append("```")
            lines.append(_strip_html(msg)[:2000])
            lines.append("```")

    elif t_type == "wait":
        lines.append(f"- {_fmt_wait(attrs)}")

    elif t_type in ("add_contact_tag", "remove_contact_tag"):
        tags = attrs.get("tags") or []
        lines.append(f"- tags: {tags}")

    elif t_type == "if_else":
        op = attrs.get("operator") or attrs.get("if") or ""
        if op:
            lines.append(f"- operator: {op}")
        lines.append(_fmt_if_else_attrs(attrs))

    elif t_type == "goto":
        target = (attrs.get("targetStepId") or attrs.get("targetStep")
                  or attrs.get("target") or "?")
        lines.append(f"- goto step: {target}")

    elif t_type == "webhook":
        url = attrs.get("url") or "?"
        method = attrs.get("method") or "POST"
        lines.append(f"- {method} {url}")
        if attrs.get("data"):
            lines.append("```json")
            lines.append(json.dumps(attrs["data"], indent=2)[:2000])
            lines.append("```")

    elif t_type in ("add_to_workflow", "remove_from_workflow"):
        target = attrs.get("workflow_id") or attrs.get("workflowId")
        lines.append(f"- target workflow id: {target}")

    elif t_type == "create_opportunity":
        lines.append(
            f"- pipeline: `{attrs.get('pipeline_id')}` "
            f"stage: `{attrs.get('pipeline_stage_id')}` "
            f"status: `{attrs.get('opportunity_status')}`"
        )
        lines.append(f"- name: {attrs.get('opportunity_name')}")
        if attrs.get("monetary_value"):
            lines.append(f"- value: {attrs.get('monetary_value')}")

    elif t_type == "math_operation":
        lines.append(f"- {attrs}")

    elif t_type == "google_sheets":
        lines.append(f"- {attrs.get('actionType','?')} → "
                     f"sheet {attrs.get('spreadsheetId','?')}")

    elif t_type == "event_start_date":
        lines.append(f"- {attrs}")

    else:
        # Generic dump for unknown step types
        compact = json.dumps(attrs, ensure_ascii=False)
        lines.append("```json")
        lines.append(compact[:1500])
        lines.append("```")

    return "\n".join(lines)


def render_trigger_md(trig: dict) -> str:
    t_type = trig.get("type") or "?"
    name = trig.get("name") or ""
    lines = [f"- **type:** `{t_type}`" + (f"  —  *{name}*" if name else "")]
    conds = trig.get("conditions") or trig.get("filters") or []
    if conds:
        lines.append("- **conditions:**")
        for c in conds:
            field = c.get("field") or c.get("conditionType") or "?"
            op = c.get("operator") or c.get("conditionOperator") or "?"
            val = c.get("value") if c.get("value") is not None \
                else c.get("conditionValue")
            title = c.get("title")
            line = f"    - `{field}` {op} `{val}`"
            if title:
                line += f"  ({title})"
            lines.append(line)
    return "\n".join(lines)


def render_workflow_md(wf: dict, triggers: list, parent_path: list) -> str:
    name = wf.get("name") or "(unnamed)"
    status = wf.get("status") or "?"
    wf_id = wf.get("id") or wf.get("_id") or "?"
    loc = wf.get("locationId") or "?"
    folder = " / ".join(parent_path) if parent_path else "(root)"
    updated = wf.get("updatedAt") or "?"
    created = wf.get("createdAt") or "?"

    lines = [
        f"# {name}",
        "",
        f"- **id:** `{wf_id}`",
        f"- **status:** `{status}`",
        f"- **folder:** {folder}",
        f"- **location:** `{loc}`",
        f"- **created:** {created}",
        f"- **updated:** {updated}",
        f"- **builder url:** "
        f"https://app.gohighlevel.com/location/{loc}/workflow/{wf_id}",
        "",
    ]

    lines.append("## Triggers")
    lines.append("")
    if not triggers:
        lines.append("_(no triggers found — workflow may use legacy "
                     "`tag` trigger or be manually-fired)_")
    for t in triggers:
        lines.append(render_trigger_md(t))
        lines.append("")

    tmpls = ((wf.get("workflowData") or {}).get("templates")) or []
    lines.append(f"## Steps ({len(tmpls)})")
    lines.append("")
    if not tmpls and wf.get("filePath"):
        lines.append(f"_Templates not inlined — see `filePath`: "
                     f"`{wf.get('filePath')}`_")
        lines.append("")
    # Templates are emitted as authored — GHL's `order` is per-parent within
    # if_else branches, not a global sort key.
    for i, t in enumerate(tmpls):
        lines.append(f"#### Step {i + 1}: id=`{t.get('id','?')}` "
                     f"order={t.get('order')}")
        lines.append(render_step_md(t))
        lines.append("")
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def _parse_args(argv):
    ap = argparse.ArgumentParser(prog="dump_workflows.py", add_help=True)
    ap.add_argument("location_id")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument(
        "--refresh-token",
        default=os.environ.get("GHL_FIREBASE_REFRESH_TOKEN", "") or None,
    )
    ap.add_argument(
        "--id-token",
        default=os.environ.get("GHL_FIREBASE_TOKEN", "") or None,
    )
    ap.add_argument(
        "--limit", type=int, default=0,
        help="dump only the first N workflows (debug; 0 = all)",
    )
    return ap.parse_args(argv)


def main(argv):
    args = _parse_args(argv)
    if not (args.refresh_token or args.id_token):
        print("ERROR: provide --refresh-token or --id-token (or set "
              "$GHL_FIREBASE_REFRESH_TOKEN / $GHL_FIREBASE_TOKEN).",
              file=sys.stderr)
        return 2

    os.makedirs(os.path.join(args.out_dir, "workflows"), exist_ok=True)

    client = build_client(args.location_id, id_token=args.id_token,
                          refresh_token=args.refresh_token)

    print(f"[dump] location={args.location_id} → {args.out_dir}")
    print("[dump] walking folder tree…")
    tree = walk_tree(client, args.location_id)
    folders = tree["folders"]
    workflows = tree["workflows"]
    print(f"[dump] found {len(folders)} folder(s), "
          f"{len(workflows)} workflow(s)")

    folder_by_id = {f["id"]: f for f in folders}

    def path_for(wf):
        path, fid = [], wf.get("_parentFolderId")
        while fid and fid in folder_by_id:
            f = folder_by_id[fid]
            path.insert(0, f["name"])
            fid = f.get("_parentFolderId")
        return path

    # Write the index (folders + workflow summaries) early so a crash mid-dump
    # still leaves a usable map.
    index = {
        "locationId": args.location_id,
        "folders": [
            {"id": f["id"], "name": f["name"],
             "parentFolderId": f.get("_parentFolderId"),
             "path": f.get("_path", []) + [f["name"]]}
            for f in folders
        ],
        "workflows": [
            {"id": w["id"], "name": w["name"],
             "status": w.get("status"),
             "parentFolderId": w.get("_parentFolderId"),
             "path": path_for(w),
             "updatedAt": w.get("updatedAt"),
             "createdAt": w.get("createdAt")}
            for w in workflows
        ],
    }
    with open(os.path.join(args.out_dir, "_index.json"), "w") as f:
        json.dump(index, f, indent=2)

    # Readable index
    idx_md = [f"# Workflow dump — location `{args.location_id}`", ""]
    if folders:
        idx_md.append("## Folders")
        idx_md.append("")
        for f in folders:
            p = " / ".join(f.get("_path", []) + [f["name"]])
            idx_md.append(f"- {p}  `{f['id']}`")
        idx_md.append("")
    idx_md.append(f"## Workflows ({len(workflows)})")
    idx_md.append("")
    by_folder = {}
    for w in workflows:
        key = " / ".join(path_for(w)) or "(root)"
        by_folder.setdefault(key, []).append(w)
    for fname in sorted(by_folder):
        idx_md.append(f"### {fname}")
        idx_md.append("")
        for w in sorted(by_folder[fname], key=lambda x: (x.get("name") or "")):
            slug = _slug(w["name"]) + "__" + (w.get("id") or "")[:8]
            idx_md.append(
                f"- [{w['name']}](workflows/{slug}.md) — "
                f"`{w.get('status','?')}`  `{w['id']}`"
            )
        idx_md.append("")
    with open(os.path.join(args.out_dir, "_index.md"), "w") as f:
        f.write("\n".join(idx_md))

    # Walk every workflow
    targets = workflows[:args.limit] if args.limit else workflows
    for i, w in enumerate(targets, 1):
        wf_id = w["id"]
        name = w["name"]
        print(f"[dump] ({i}/{len(targets)}) {name}  {wf_id}")
        detail = get_workflow_detail(client, args.location_id, wf_id)
        triggers = get_workflow_triggers(client, args.location_id, wf_id)
        slug = _slug(name) + "__" + wf_id[:8]
        base = os.path.join(args.out_dir, "workflows", slug)
        with open(base + ".json", "w") as f:
            json.dump(detail, f, indent=2, ensure_ascii=False)
        with open(base + ".triggers.json", "w") as f:
            json.dump(triggers, f, indent=2, ensure_ascii=False)
        md = render_workflow_md(detail or w, triggers, path_for(w))
        with open(base + ".md", "w") as f:
            f.write(md)

    print(f"[dump] done. {client.call_count} API call(s) made.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
