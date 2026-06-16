#!/usr/bin/env python3
"""Pre-deploy static lint for a campaign .py (catches deploy-breakers BEFORE you ship).

Usage:
  python3 scripts/preflight_campaign.py campaigns/<file>.py

Why this exists: a single bad action type (e.g. internal_update_opportunity)
makes GHL reject the WHOLE step batch with "corrupted type" and saves 0 steps
across every workflow — but the engine only reports it AFTER it has already
created the folder + empty workflows + triggers, forcing a cleanup + redeploy.
`deploy_verify.py` is POST-deploy; this is the PRE-deploy gate that would have
caught it for free. Imports the campaign module (no network — main() is guarded)
and inspects the CAMPAIGN dict + the module's copy strings.

Exit codes: 0 = clean (warnings ok), 1 = ERRORS found (do not deploy), 2 = usage.

Checks (ERROR = deploy-breaker, WARN = quality/foot-gun):
  E1  internal_update_opportunity step      -> rejected by save API; use
                                               create_opportunity at target stage (upserts)
  E2  customer_reply trigger w/o workflow    -> _build_trigger_body returns (None,None);
      filter (source_wf_key/source_wf_id)       workflow deploys with NO trigger, silently
  E3  em dash (— / –) in SMS/email copy      -> violates the no-em-dash copy rule
  W1  blank line (\\n\\n) in an *_BODY string -> adds EMAIL_BLANK_P; too-airy spacing
  W2  required-looking ID constant is empty   -> PIPELINE_ID / STAGE_* / *_FIELD blank
  W3  inbound KEYWORD reused by a sibling     -> multi-offer keyword collision
      campaign
"""
import importlib.util
import os
import re
import sys
import glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(path):
    """Import a campaign file as a module without running main()."""
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    spec = importlib.util.spec_from_file_location("_camp_preflight", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _walk_steps(campaign):
    for wf_key, wf in campaign.items():
        for step in wf.get("templates", []):
            yield wf_key, step


def check(path):
    errors, warns = [], []
    mod = _load(path)
    campaign = getattr(mod, "CAMPAIGN", None)
    if not isinstance(campaign, dict):
        return ["no CAMPAIGN dict found in module"], []

    # E1 — internal_update_opportunity (corrupted-type save failure)
    for wf_key, step in _walk_steps(campaign):
        if step.get("type") == "internal_update_opportunity":
            errors.append(
                f"E1 [{wf_key}] step {step.get('name','?')!r} is "
                f"internal_update_opportunity — REJECTED by save API "
                f"('corrupted type'). Use create_opportunity at the target "
                f"stage (it upserts)."
            )

    # E2 — customer_reply trigger missing its workflow filter
    for wf_key, wf in campaign.items():
        trig = wf.get("trigger")
        if isinstance(trig, dict) and trig.get("type") == "customer_reply":
            if not (trig.get("source_wf_key") or trig.get("source_wf_id")):
                errors.append(
                    f"E2 [{wf_key}] customer_reply trigger has no "
                    f"source_wf_key/source_wf_id — it will deploy with NO "
                    f"trigger, silently."
                )

    # Copy-string scans (SMS_* are plain text; *_BODY / *_SUBJECT are raw source)
    EMDASH = re.compile(r"[—–]")
    for name in dir(mod):
        if not (name.startswith("SMS_") or name.endswith(("_BODY", "_SUBJECT"))):
            continue
        val = getattr(mod, name)
        if not isinstance(val, str):
            continue
        # E3 — em dash in customer-facing copy
        if EMDASH.search(val):
            errors.append(f"E3 copy {name} contains an em/en dash — use ' - '.")
        # W1 — blank line inside an email body
        if name.endswith("_BODY") and "\n\n" in val:
            warns.append(
                f"W1 {name} has a blank line (\\n\\n) — renders an EMAIL_BLANK_P "
                f"(too airy). Use single newlines between sections."
            )

    # W2 — required-looking ID constants left empty
    for name in dir(mod):
        if re.fullmatch(r"(PIPELINE_ID|STAGE_[A-Z0-9_]+|[A-Z0-9_]*FIELD)", name):
            val = getattr(mod, name)
            if isinstance(val, str) and not val.strip():
                warns.append(f"W2 constant {name} is empty — fill before deploy.")

    # W3 — inbound KEYWORD reused by a sibling campaign
    kw = getattr(mod, "KEYWORD", None)
    if isinstance(kw, str) and kw.strip():
        here = os.path.abspath(path)
        for sib in glob.glob(os.path.join(REPO, "campaigns", "*.py")):
            if os.path.abspath(sib) == here:
                continue
            try:
                txt = open(sib, encoding="utf-8").read()
            except OSError:
                continue
            if re.search(rf'KEYWORD\s*=\s*["\']{re.escape(kw)}["\']', txt):
                warns.append(
                    f"W3 KEYWORD {kw!r} is also used by "
                    f"{os.path.basename(sib)} — multi-offer collision; give "
                    f"each offer its own keyword."
                )

    return errors, warns


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    path = argv[0]
    if not os.path.isfile(path):
        print(f"not a file: {path}")
        return 2
    errors, warns = check(path)
    for w in warns:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")
    if errors:
        print(f"\nPREFLIGHT FAILED: {len(errors)} error(s), {len(warns)} warning(s). Do NOT deploy.")
        return 1
    print(f"\nPREFLIGHT OK: 0 errors, {len(warns)} warning(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
