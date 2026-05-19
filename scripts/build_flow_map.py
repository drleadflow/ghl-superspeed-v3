#!/usr/bin/env python3
"""
Static cross-workflow flow map for a dumped GHL location.

Reads <out-dir>/workflows/*.json + *.triggers.json (produced by
scripts/dump_workflows.py) and emits <out-dir>/_flows.json + _flows.md.

For every workflow it computes:
  - outbound.calls_workflows   : add_to_workflow → wf id
  - outbound.removes_workflows : remove_from_workflow → wf id
  - outbound.adds_tags         : add_contact_tag → tags
  - outbound.removes_tags      : remove_contact_tag → tags
  - inbound.called_by          : workflows that add_to_workflow → this id
  - inbound.triggered_by_tag   : workflows that add a tag this workflow triggers on
  - triggers                   : compact list (type + key field/value)

Pure static analysis — no API calls.
"""
import argparse
import glob
import json
import os
import sys


def _collect_tags_in_trigger(trig):
    """Return list of tag strings this trigger fires on (contact_tag type only)."""
    if trig.get("type") != "contact_tag":
        return []
    tags = []
    for c in (trig.get("conditions") or []):
        val = c.get("value") if c.get("value") is not None \
            else c.get("conditionValue")
        if isinstance(val, list):
            tags.extend(str(v).lower() for v in val)
        elif val:
            tags.append(str(val).lower())
    return tags


def _trigger_summary(trig):
    """Compact one-line summary for a trigger."""
    ty = trig.get("type") or "?"
    conds = trig.get("conditions") or trig.get("filters") or []
    parts = []
    for c in conds:
        field = c.get("field") or c.get("conditionType") or "?"
        op = c.get("operator") or c.get("conditionOperator") or ""
        val = c.get("value") if c.get("value") is not None \
            else c.get("conditionValue")
        if isinstance(val, list) and len(val) > 3:
            val = val[:3] + ["…"]
        parts.append(f"{field} {op} {val}")
    return {"type": ty, "conditions": parts}


def _walk_templates(tmpls):
    """Yield (template) recursively, flattening if_else branches."""
    if not tmpls:
        return
    for t in tmpls:
        yield t
        # if_else: branches are listed as siblings (not nested in attributes)
        # in GHL's serialization, so no recursion needed for the cases we've
        # seen. If GHL ever nests, add recursion on t.attributes.branches here.


def analyze(out_dir):
    wf_paths = sorted(p for p in glob.glob(
        os.path.join(out_dir, "workflows", "*.json"))
        if not p.endswith(".triggers.json"))

    workflows = {}  # id → analyzed record
    for p in wf_paths:
        d = json.load(open(p))
        wf_id = d.get("id") or d.get("_id")
        if not wf_id:
            continue
        trig_path = p.replace(".json", ".triggers.json")
        triggers = json.load(open(trig_path)) if os.path.exists(trig_path) else []

        tmpls = (d.get("workflowData") or {}).get("templates") or []
        calls, removes_wf = [], []
        adds_tags, removes_tags = set(), set()
        step_type_counts = {}

        for t in _walk_templates(tmpls):
            ty = t.get("type") or "?"
            step_type_counts[ty] = step_type_counts.get(ty, 0) + 1
            attrs = t.get("attributes") or {}
            if ty == "add_to_workflow":
                wid = attrs.get("workflow_id") or attrs.get("workflowId")
                # GHL stores this as either a single string or a list of ids.
                if isinstance(wid, list):
                    calls.extend(x for x in wid if x)
                elif wid:
                    calls.append(wid)
            elif ty == "remove_from_workflow":
                wid = attrs.get("workflow_id") or attrs.get("workflowId")
                if isinstance(wid, list):
                    removes_wf.extend(x for x in wid if x)
                elif wid:
                    removes_wf.append(wid)
            elif ty == "add_contact_tag":
                for tag in (attrs.get("tags") or []):
                    adds_tags.add(str(tag).lower())
            elif ty == "remove_contact_tag":
                for tag in (attrs.get("tags") or []):
                    removes_tags.add(str(tag).lower())

        # Triggers — collect tags this workflow fires on
        fired_by_tags = set()
        trigger_summaries = []
        for trig in (triggers or []):
            trigger_summaries.append(_trigger_summary(trig))
            for tag in _collect_tags_in_trigger(trig):
                fired_by_tags.add(tag)

        workflows[wf_id] = {
            "id": wf_id,
            "name": d.get("name"),
            "status": d.get("status"),
            "parentFolderId": d.get("parentId"),
            "triggers": trigger_summaries,
            "fired_by_tags": sorted(fired_by_tags),
            "step_type_counts": step_type_counts,
            "step_count": sum(step_type_counts.values()),
            "outbound": {
                "calls_workflows": calls,
                "removes_workflows": removes_wf,
                "adds_tags": sorted(adds_tags),
                "removes_tags": sorted(removes_tags),
            },
            "inbound": {  # filled in pass 2
                "called_by": [],
                "removed_by": [],
                "triggered_by_tag_adders": [],
            },
        }

    # Pass 2 — inbound edges
    id_to_name = {wid: w["name"] for wid, w in workflows.items()}

    # Build a tag → [workflows that add it] map
    tag_adders = {}  # tag → [wf_id, ...]
    for wid, w in workflows.items():
        for tag in w["outbound"]["adds_tags"]:
            tag_adders.setdefault(tag, []).append(wid)

    for wid, w in workflows.items():
        for target in w["outbound"]["calls_workflows"]:
            if target in workflows:
                workflows[target]["inbound"]["called_by"].append(wid)
        for target in w["outbound"]["removes_workflows"]:
            if target in workflows:
                workflows[target]["inbound"]["removed_by"].append(wid)

    for wid, w in workflows.items():
        for tag in w["fired_by_tags"]:
            for adder in tag_adders.get(tag, []):
                if adder != wid:  # don't self-link on shared tags
                    w["inbound"]["triggered_by_tag_adders"].append(
                        {"workflow_id": adder, "via_tag": tag}
                    )

    return {
        "workflows": workflows,
        "tag_adders": tag_adders,
        "id_to_name": id_to_name,
    }


def render_md(analysis, out_dir):
    workflows = analysis["workflows"]
    id_to_name = analysis["id_to_name"]
    tag_adders = analysis["tag_adders"]

    # Load folder/path info from _index.json so we can group by folder
    idx_path = os.path.join(out_dir, "_index.json")
    folder_of = {}
    if os.path.exists(idx_path):
        idx = json.load(open(idx_path))
        for w in idx.get("workflows", []):
            folder_of[w["id"]] = " / ".join(w.get("path", []) or ["(root)"])

    def link(wid):
        name = id_to_name.get(wid, "?")
        # Build slug-style file link to align with dump_workflows.py output
        from re import sub
        safe = sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-").lower()[:60]
        return f"[{name}](workflows/{safe}__{wid[:8]}.md)"

    lines = [f"# Cross-workflow flow map — {len(workflows)} workflow(s)", ""]

    # Section 1: orphan workflows (no inbound, no outbound)
    orphans = [w for w in workflows.values()
               if not w["inbound"]["called_by"]
               and not w["inbound"]["triggered_by_tag_adders"]
               and not w["outbound"]["calls_workflows"]
               and not w["outbound"]["adds_tags"]]
    if orphans:
        lines.append("## Standalone workflows")
        lines.append("")
        lines.append("_No add_to_workflow chains and no tag handoffs in "
                     "either direction. These are self-contained._")
        lines.append("")
        for w in sorted(orphans, key=lambda x: x["name"] or ""):
            tr = w["triggers"][0]["type"] if w["triggers"] else "no-trigger"
            lines.append(f"- {link(w['id'])} — trigger: `{tr}`, "
                         f"{w['step_count']} steps")
        lines.append("")

    # Section 2: entry points — workflows triggered by external events
    # (not by other workflows)
    entry_points = []
    for w in workflows.values():
        if w["triggers"] and not w["inbound"]["called_by"]:
            entry_points.append(w)
    if entry_points:
        lines.append("## Entry points")
        lines.append("")
        lines.append("_Workflows fired by external events (form submit, IG "
                     "comment, payment, calendar booking, etc.) — these are "
                     "the top of the funnel._")
        lines.append("")
        by_trig_type = {}
        for w in entry_points:
            for tr in w["triggers"]:
                by_trig_type.setdefault(tr["type"], []).append(w)
        for tt in sorted(by_trig_type):
            lines.append(f"### `{tt}`")
            lines.append("")
            seen = set()
            for w in sorted(by_trig_type[tt], key=lambda x: x["name"] or ""):
                if w["id"] in seen:
                    continue
                seen.add(w["id"])
                lines.append(f"- {link(w['id'])} → "
                             f"calls {len(w['outbound']['calls_workflows'])} "
                             f"workflow(s), adds {len(w['outbound']['adds_tags'])} "
                             f"tag(s)")
            lines.append("")

    # Section 3: workflow → workflow chains (add_to_workflow)
    chains = [(wid, w) for wid, w in workflows.items()
              if w["outbound"]["calls_workflows"]]
    if chains:
        lines.append("## Workflow → Workflow chains (`add_to_workflow`)")
        lines.append("")
        for wid, w in sorted(chains, key=lambda kv: kv[1]["name"] or ""):
            lines.append(f"### {link(wid)}")
            for target in w["outbound"]["calls_workflows"]:
                if target in workflows:
                    lines.append(f"  - → {link(target)}")
                else:
                    lines.append(f"  - → `{target}` (NOT FOUND in this dump)")
            lines.append("")

    # Section 4: tag-mediated handoffs
    if tag_adders:
        lines.append("## Tag-mediated handoffs")
        lines.append("")
        lines.append("_Tag added by workflow A → triggers workflow B (B's "
                     "trigger filters on that tag)._")
        lines.append("")
        triggered_tag_pairs = []
        for wid, w in workflows.items():
            for fb in w["inbound"]["triggered_by_tag_adders"]:
                triggered_tag_pairs.append((fb["workflow_id"], fb["via_tag"], wid))
        if not triggered_tag_pairs:
            lines.append("_No tag-mediated handoffs detected — every tag added "
                         "by a workflow is consumed downstream of GHL (not by "
                         "another workflow in this location)._")
            lines.append("")
        else:
            triggered_tag_pairs.sort(key=lambda t: (
                id_to_name.get(t[0]) or "", t[1], id_to_name.get(t[2]) or ""))
            for adder_id, tag, target_id in triggered_tag_pairs:
                lines.append(f"- {link(adder_id)} adds `{tag}` → "
                             f"{link(target_id)} fires")
            lines.append("")

    # Section 5: per-workflow detail (inbound + outbound at a glance)
    lines.append("## Per-workflow connections")
    lines.append("")
    by_folder = {}
    for wid, w in workflows.items():
        by_folder.setdefault(folder_of.get(wid, "(unknown)"), []).append(w)
    for fname in sorted(by_folder):
        lines.append(f"### {fname}")
        lines.append("")
        for w in sorted(by_folder[fname], key=lambda x: x["name"] or ""):
            in_called = w["inbound"]["called_by"]
            in_tagged = w["inbound"]["triggered_by_tag_adders"]
            out_calls = w["outbound"]["calls_workflows"]
            out_tags = w["outbound"]["adds_tags"]
            lines.append(f"- **{link(w['id'])}**")
            lines.append(f"    - in: {len(in_called)} caller(s), "
                         f"{len(in_tagged)} tag-trigger(s); "
                         f"out: calls {len(out_calls)}, adds tags {out_tags}")
            if in_called:
                lines.append(f"    - called by: "
                             + ", ".join(link(x) for x in in_called[:8])
                             + (" …" if len(in_called) > 8 else ""))
            if in_tagged:
                samples = in_tagged[:5]
                lines.append(
                    "    - tag triggers: "
                    + "; ".join(f"{link(s['workflow_id'])} via `{s['via_tag']}`"
                                for s in samples)
                    + (" …" if len(in_tagged) > 5 else "")
                )
            if out_calls:
                lines.append(f"    - calls: "
                             + ", ".join(link(x) for x in out_calls[:8])
                             + (" …" if len(out_calls) > 8 else ""))
        lines.append("")

    return "\n".join(lines)


def main(argv):
    ap = argparse.ArgumentParser(prog="build_flow_map.py")
    ap.add_argument("out_dir", help="path to a dump dir produced by dump_workflows.py")
    args = ap.parse_args(argv)
    if not os.path.isdir(os.path.join(args.out_dir, "workflows")):
        print(f"ERROR: {args.out_dir}/workflows missing — is this a dump dir?",
              file=sys.stderr)
        return 2
    analysis = analyze(args.out_dir)
    with open(os.path.join(args.out_dir, "_flows.json"), "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    md = render_md(analysis, args.out_dir)
    with open(os.path.join(args.out_dir, "_flows.md"), "w") as f:
        f.write(md)
    n = len(analysis["workflows"])
    chained = sum(1 for w in analysis["workflows"].values()
                  if w["outbound"]["calls_workflows"])
    tag_pairs = sum(len(w["inbound"]["triggered_by_tag_adders"])
                    for w in analysis["workflows"].values())
    print(f"[flow] analyzed {n} workflows")
    print(f"[flow] {chained} have add_to_workflow chains")
    print(f"[flow] {tag_pairs} tag-mediated handoff edge(s)")
    print(f"[flow] wrote _flows.json + _flows.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
