#!/usr/bin/env python3
"""
Campaign skeleton generator — deterministic .py scaffold from a vault offer.

Reads offer + client from the local vault (zero Notion calls, zero LLM tokens),
applies shape decisions from the offer's frontmatter, and emits a runnable
campaigns/<slug>-nurture.py skeleton with:

    - Engine imports
    - LOCATION_ID, COMPANY_ID, USER_ID, FROM_NAME pre-filled from vault
    - 3-workflow CAMPAIGN dict (master / keyword-recovery / reply-handler)
    - Touchpoint placeholders with TODO copy markers
    - Standard `if __name__ == "__main__":` deploy block

This is the FAST path. For full LLM copy generation + QA + manual touchpoints
+ AI bot prompt, run /build-sequence after this.

Public API:
    build_skeleton(offer_slug, *, output_path=None, force=False) -> Path
    render_skeleton(offer, client) -> str   # just renders, doesn't write

CLI:
    python -m lib.skeleton_builder <offer-slug>
    python -m lib.skeleton_builder <offer-slug> --print
    python -m lib.skeleton_builder <offer-slug> --force
"""

from __future__ import annotations

import ast
import datetime
import re
import sys
from pathlib import Path
from typing import Optional

from lib import vault

CAMPAIGNS_DIR = vault.VAULT_ROOT / "campaigns"


# ── Shape decisions (mirror .claude/skills/learned/ghl-sequence-shape-from-notion) ──

def shape_decisions(offer: dict) -> list[str]:
    """
    Walks the Notion shape decision table against offer frontmatter.
    Returns list of human-readable shape change notes for the docstring.
    """
    notes: list[str] = []

    has_deadline = offer.get("has_deadline")
    deadline_date = offer.get("deadline_date") or ""
    if not has_deadline or (has_deadline and not deadline_date.strip()):
        notes.append(
            "Has Deadline=No → DROP V2 Day 5 deadline email · D5 5pm SMS becomes "
            "curiosity hook · 28→27 touchpoints"
        )
    else:
        notes.append(f"Has Deadline=Yes ({deadline_date}) → full V2 deadline overlay applied")

    images = offer.get("images_available")
    if images is False or images == "No":
        notes.append("Before Afters=No → D0 T+1 SMS text-only (no MMS) · niche reply hook substituted")
    else:
        notes.append("Before Afters=Yes → D0 T+1 MMS with 3 pre-loaded images")

    deposit = offer.get("deposit_required")
    if deposit:
        notes.append("Deposit Required=Yes → D1 deposit paragraph · D4 'Hold My Spot' CTA")
    else:
        notes.append("Deposit Required=No → 'Book Your Slot' CTA · no deposit-hold flow")

    doc_video = offer.get("doctor_video") or ""
    if doc_video and doc_video.strip().lower().startswith("http"):
        notes.append(f"Doctor Video URL set → embedded in D2 objection-handler email")
    else:
        notes.append("Doctor Video=Need to film/empty → no video embed")

    if not offer.get("uses_bot"):
        notes.append("Uses Bot=No → bot prompt generated as manual fallback (QA flag)")

    offer_type = (offer.get("offer_type") or "").lower()
    if any(k in offer_type for k in ("iv", "drip", "infusion")):
        notes.append("Niche=IV → lib/prompts/iv-adjustments.md OVERRIDES rows above on conflict")

    return notes


# ── Naming helpers ─────────────────────────────────────────────────────────────

def _alphanum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _tag_prefix(offer: dict) -> str:
    """
    Mirror the existing convention from iv-wellness-nad-iv-therapy-nurture.py:
    slug 'iv-wellness-nad-iv-therapy' → strip client prefix → 'nad-iv-therapy' →
    alphanumeric squash → 'nadivtherapy'.
    """
    slug = offer["_slug"]
    client = offer.get("client", "")
    short = slug
    if client and slug.startswith(f"{client}-"):
        short = slug[len(client) + 1:]
    return _alphanum(short) or _alphanum(slug)


def _folder_name(offer: dict) -> str:
    return f"{offer.get('name', offer['_slug'])} Nurture"


# ── Renderer ───────────────────────────────────────────────────────────────────

PYTHON_HEADER = '''#!/usr/bin/env python3
"""
{client_name} — {offer_name} nurture sequence (SKELETON).

Generated: {timestamp}
Source offer: offers/{offer_slug}.md
Source client: clients/{client_slug}/overview.md

THIS IS A STRUCTURAL SKELETON. Touchpoints are placeholders with TODO copy markers.
Run `/build-sequence {offer_slug}` to populate full LLM-generated copy + QA report
+ manual-touchpoints + AI bot prompt. Or hand-fill the TODO blocks below.

Trigger: contact gets tag `{tag_prefix}-lead`.

Shape decisions applied (from offer frontmatter):
{shape_notes_block}

Hard rules ({niche_label}):
{hard_rules_block}
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, update_contact_field_step, link_steps,
)

# ── Constants (sourced from vault — do not hand-edit, re-run /build-campaign-skeleton) ──

LOCATION_ID = "{location_id}"
COMPANY_ID  = "{company_id}"
USER_ID     = "{user_id}"
PARENT_FOLDER = ""

FROM_NAME = "{from_name}"

# Booking link is a custom value (resolved by GHL at send time)
BOOKING_LINK = "{booking_link}"

# Offer constants
OFFER_NAME    = "{offer_name}"
OFFER_PRICE   = "{offer_price}"
OFFER_KEYWORD = "{offer_keyword}"

# Notion offer page (engine ticks "28 Day Nurture Sequence Built" on full success)
NOTION_PAGE_ID = "{notion_page_id}"

# Tag namespace (one offer's tag must NEVER collide with another's)
TAG_LEAD             = "{tag_prefix}-lead"
TAG_KEYWORD_TRIGGER  = "{tag_prefix}-keyword-trigger"
TAG_RETURNING_LEAD   = "{tag_prefix}-returning-lead"
TAG_NURTURE_COMPLETE = "{tag_prefix}-nurture-complete"
TAG_REPLIED          = "{tag_prefix}-replied"


# ── Touchpoint copy (TODO — fill via /build-sequence or by hand) ──
# Each placeholder is a structurally-correct GHL step. Subject + body are TODO.
# Keep this section editable — every constant below is a real step in the workflow.

# D0 T+0 welcome SMS (sent ~immediately after FB lead form submit)
SMS_T0_WELCOME = "Hi {{{{contact.first_name}}}}, this is {{{{custom_values.text_message_name}}}} from {{{{location.name}}}}. Thanks for your interest in our {{{{contact.latest_optin}}}}!"

# D0 T+1m timing question SMS (segments urgency: now vs upcoming event)
SMS_T1_TIMING = "Are you looking to come in soon, or planning ahead for an event coming up?"

# D1 — Email + SMS
E1_SUBJECT = "TODO: D1 subject"
E1_BODY    = "TODO: D1 body — segmenting question + free wellness assessment + price + booking link."
SMS_D1     = "TODO: D1 evening SMS — light nudge."

# D2 — Email (objections) + 5pm SMS
E2_SUBJECT = "TODO: D2 subject"
E2_BODY    = "TODO: D2 body — top 3 objections answered with pratfall flaw + Zeigarnik teaser."
SMS_D2_5PM = "TODO: D2 5pm SMS — micro CTA."

# D3 — Education email + interrupt SMS
E3_SUBJECT = "TODO: D3 subject"
E3_BODY    = "TODO: D3 body — quick-win tips, no pitch."
SMS_D3     = "TODO: D3 SMS — pattern interrupt."

# D4 — Branched (wellness-curious / symptom-driven) + 5pm SMS
E4A_SUBJECT = "TODO: D4 Variant A subject (wellness-curious)"
E4A_BODY    = "TODO: D4 Variant A body."
E4B_SUBJECT = "TODO: D4 Variant B subject (symptom-driven)"
E4B_BODY    = "TODO: D4 Variant B body."
SMS_D4_5PM  = "TODO: D4 5pm SMS."

# D5 — 5pm curiosity SMS (deadline email DROPPED if Has Deadline=No, see shape notes)
SMS_D5_5PM  = "TODO: D5 5pm SMS — curiosity gap (no scarcity tone if no deadline)."

# D7 — Branched + SMS (closes the D2 Zeigarnik teaser)
E7A_SUBJECT = "TODO: D7 Variant A subject"
E7A_BODY    = "TODO: D7 Variant A body — closes D2 teaser."
E7B_SUBJECT = "TODO: D7 Variant B subject"
E7B_BODY    = "TODO: D7 Variant B body."
SMS_D7      = "TODO: D7 SMS."

# D10 — Logic + cost-of-inaction email
E10_SUBJECT = "TODO: D10 subject"
E10_BODY    = "TODO: D10 body — logic frame + cost of inaction."

# D12 — Objection surfacer SMS
SMS_D12     = "TODO: D12 SMS — surface unspoken objection."

# D14 — Email + SMS (KEYWORD reveal)
E14_SUBJECT = "TODO: D14 subject"
E14_BODY    = "TODO: D14 body — final value frame, references KEYWORD."
SMS_D14     = "TODO: D14 SMS — reveals reply keyword '{offer_keyword}'."

# D28 — Breakup SMS
SMS_D28     = "TODO: D28 breakup SMS."

# Keyword recovery responses
SMS_KEYWORD_AUTOREPLY     = "TODO: '{offer_keyword}' keyword auto-reply with booking link."
SMS_KEYWORD_2HR_FOLLOWUP  = "TODO: 2-hour follow-up if booking link not clicked."

# Reply handler internal alert
REPLY_ALERT_SUBJECT = "Reply received — {offer_name} lead"
REPLY_ALERT_BODY    = "TODO: internal alert template (front desk)."


# ── Workflows ──────────────────────────────────────────────────────────────────

CAMPAIGN = {{
    "01-master": {{
        "name": "01. {offer_name} — Master Nurture",
        # Trigger: Facebook Lead Form Submitted. Fill fb_page_id with the FB
        # page ID after launch (find it via GET /integrations/facebook/{{loc}}/
        # trigger/pages). Add "fb_form_id" to filter to a specific lead form,
        # or omit both for "any page / any form".
        "trigger": {{
            "type": "facebook_lead_gen",
            "fb_page_id": "TODO_FB_PAGE_ID",
            "name": "Facebook Lead Form Submitted",
        }},
        "templates": link_steps([
            # Open with: stamp `latest_optin` so {{{{contact.latest_optin}}}}
            # resolves in every downstream message, then welcome + timing-segment.
            update_contact_field_step("Set latest_optin", "latest_optin", OFFER_NAME),
            wait_step("Wait .1 min", 0.1, "minutes"),
            sms_step("D0 T+0 welcome", SMS_T0_WELCOME),
            wait_step("Wait 1 min", 1, "minutes"),
            sms_step("D0 T+1m timing question", SMS_T1_TIMING),
            wait_step("Wait to D1", 1, "day"),

            email_step("D1 segmenting email", E1_SUBJECT, E1_BODY, FROM_NAME),
            sms_step("D1 evening SMS", SMS_D1),
            wait_step("Wait to D2", 1, "day"),

            email_step("D2 objections email", E2_SUBJECT, E2_BODY, FROM_NAME),
            sms_step("D2 5pm SMS", SMS_D2_5PM),
            wait_step("Wait to D3", 1, "day"),

            email_step("D3 education email", E3_SUBJECT, E3_BODY, FROM_NAME),
            sms_step("D3 interrupt SMS", SMS_D3),
            wait_step("Wait to D4", 1, "day"),

            email_step("D4 wellness-curious", E4A_SUBJECT, E4A_BODY, FROM_NAME),
            sms_step("D4 5pm SMS", SMS_D4_5PM),
            wait_step("Wait to D5", 1, "day"),

            sms_step("D5 5pm SMS", SMS_D5_5PM),
            wait_step("Wait to D7", 2, "day"),

            email_step("D7 close email", E7A_SUBJECT, E7A_BODY, FROM_NAME),
            sms_step("D7 SMS", SMS_D7),
            wait_step("Wait to D10", 3, "day"),

            email_step("D10 logic email", E10_SUBJECT, E10_BODY, FROM_NAME),
            wait_step("Wait to D12", 2, "day"),

            sms_step("D12 objection SMS", SMS_D12),
            wait_step("Wait to D14", 2, "day"),

            email_step("D14 final email", E14_SUBJECT, E14_BODY, FROM_NAME),
            sms_step("D14 keyword SMS", SMS_D14),
            wait_step("Wait to D28", 14, "day"),

            sms_step("D28 breakup", SMS_D28),
            tag_step("Mark nurture complete", [TAG_NURTURE_COMPLETE]),
        ]),
    }},

    "02-keyword-recovery": {{
        "name": "02. {offer_name} — {offer_keyword} Keyword Recovery",
        # Trigger: Customer replied to WF-01 with the offer keyword.
        # Engine resolves source_wf_key → wf_id of "01-master" automatically.
        "trigger": {{
            "type": "customer_reply",
            "source_wf_key": "01-master",
            "keyword": "{offer_keyword}",
        }},
        "templates": link_steps([
            tag_step("Apply returning lead tag", [TAG_RETURNING_LEAD]),
            tag_step("Remove nurture-complete", [TAG_NURTURE_COMPLETE], remove=True),
            sms_step("Keyword auto-reply", SMS_KEYWORD_AUTOREPLY),
            wait_step("2 hours", 2, "hour"),
            sms_step("2-hour follow-up", SMS_KEYWORD_2HR_FOLLOWUP),
        ]),
    }},

    "03-reply-handler": {{
        "name": "03. {offer_name} — Global Reply Handler",
        # Trigger: Customer replied to WF-01 (any reply, no keyword filter).
        "trigger": {{
            "type": "customer_reply",
            "source_wf_key": "01-master",
        }},
        "templates": link_steps([
            tag_step("Confirm reply tag", [TAG_REPLIED]),
            email_step("Internal alert", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    }},
}}


# ── Run ────────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"{offer_name} Nurture: {{len(CAMPAIGN)}} workflow(s), {{total_steps}} steps\\n")

    token_mgr = TokenManager(LOCATION_ID)
    if os.environ.get("GHL_FIREBASE_REFRESH_TOKEN"):
        token_mgr.set_refresh_token(os.environ["GHL_FIREBASE_REFRESH_TOKEN"])

    client = GHLClient(token_mgr, LOCATION_ID)

    print("Testing auth...")
    test = client.request("GET", f"/workflow/{{LOCATION_ID}}/list?parentId=root&limit=1")
    if not test:
        print("Auth failed — check your token.")
        sys.exit(1)
    print("Auth OK\\n")

    builder = CampaignBuilder(client, LOCATION_ID)
    stats = builder.build(
        CAMPAIGN,
        folder_name="{folder_name}",
        parent_folder=PARENT_FOLDER or None,
        company_id=COMPANY_ID,
        user_id=USER_ID,
        notion_page_id=NOTION_PAGE_ID or None,
    )

    if stats["steps_saved"] == total_steps:
        print(f"\\nAll {{total_steps}} steps saved!")
    else:
        print(f"\\nWARNING: Expected {{total_steps}}, saved {{stats['steps_saved']}}")


if __name__ == "__main__":
    main()
'''

NICHE_HARD_RULES = {
    "iv": (
        "- 'Supports / helps with / patients often describe' only — never treats/cures/fixes\n"
        "- No before/after photos · No MMS at D0 T+1\n"
        "- No em dashes anywhere\n"
        "- {{custom_values.text_message_name}} is the bot persona, NOT the on-site RN\n"
        "- Real testimonials only · No Care Credit / financing"
    ),
}


def _niche_rules(offer: dict) -> tuple[str, str]:
    offer_type = (offer.get("offer_type") or "").lower()
    if any(k in offer_type for k in ("iv", "drip", "infusion")):
        return "IV strict mode", NICHE_HARD_RULES["iv"]
    return "default", "- (No niche-specific overrides — see lib/prompts/master-copy-prompt.md QA gate)"


def render_skeleton(offer: dict, client: dict) -> str:
    if not offer:
        raise ValueError("Offer is required")
    if not client:
        raise ValueError("Client is required")

    missing_offer = vault.validate_offer(offer)
    if missing_offer:
        raise ValueError(f"Offer missing required fields: {missing_offer}")
    missing_client = vault.validate_client(client)
    if missing_client:
        raise ValueError(f"Client missing required fields: {missing_client}")

    niche_label, hard_rules = _niche_rules(offer)
    notes = shape_decisions(offer)
    shape_notes_block = "\n".join(f"  - {n}" for n in notes)

    company_id = client.get("ghl_company_id") or client.get("company_id") or "TODO_COMPANY_ID"
    user_id = client.get("ghl_user_id") or client.get("user_id") or "TODO_USER_ID"
    from_name = (
        client.get("text_message_from_name")
        or "{{custom_values.text_message_name}}"
    )
    booking_link = (
        offer.get("booking_link")
        or "{{custom_values.booking_link}}"
    )

    rendered = PYTHON_HEADER.format(
        timestamp=datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        client_name=client.get("business_name", client.get("client_slug", "?")),
        offer_name=offer["name"],
        offer_slug=offer["_slug"],
        client_slug=client.get("client_slug", offer.get("client", "?")),
        location_id=client["ghl_location_id"],
        company_id=company_id,
        user_id=user_id,
        from_name=from_name,
        booking_link=booking_link,
        offer_price=str(offer.get("price", "TODO_PRICE")),
        offer_keyword=offer.get("keyword") or "RESET",
        notion_page_id=offer.get("notion_offer_id") or "",
        tag_prefix=_tag_prefix(offer),
        folder_name=_folder_name(offer),
        niche_label=niche_label,
        hard_rules_block=hard_rules,
        shape_notes_block=shape_notes_block,
    )

    # Validate the result parses as Python BEFORE returning it
    try:
        ast.parse(rendered)
    except SyntaxError as e:
        raise RuntimeError(
            f"Generated skeleton has a syntax error at line {e.lineno}: {e.msg}\n"
            f"This is a bug in the skeleton template — please report."
        ) from e

    return rendered


def build_skeleton(offer_slug: str, *, output_path: Optional[Path] = None, force: bool = False) -> Path:
    offer = vault.get_offer(offer_slug)
    if not offer:
        raise FileNotFoundError(
            f"Offer not found: offers/{offer_slug}.md. "
            f"Run `/extract-offer <notion-url>` first or check the slug."
        )
    client_slug = offer.get("client")
    if not client_slug:
        raise ValueError(f"Offer {offer_slug} has no `client` field — cannot resolve location ID.")
    client = vault.get_client(client_slug)
    if not client:
        raise FileNotFoundError(
            f"Client not found: clients/{client_slug}/overview.md. "
            f"Either the client folder is missing or `client` field on the offer is wrong."
        )

    rendered = render_skeleton(offer, client)

    out = output_path or (CAMPAIGNS_DIR / f"{offer_slug}-nurture.py")
    if out.exists() and not force:
        raise FileExistsError(
            f"{out} already exists. Pass --force to overwrite, "
            f"or rename the existing file (e.g., {out.stem}-v1.py)."
        )

    out.write_text(rendered)
    return out


# ── CLI ────────────────────────────────────────────────────────────────────────

def _cli():
    args = sys.argv[1:]
    if not args:
        print(
            "Usage:\n"
            "  python -m lib.skeleton_builder <offer-slug>\n"
            "  python -m lib.skeleton_builder <offer-slug> --print\n"
            "  python -m lib.skeleton_builder <offer-slug> --force"
        )
        sys.exit(1)

    slug = args[0]
    do_print = "--print" in args
    force = "--force" in args

    if do_print:
        offer = vault.get_offer(slug)
        if not offer:
            print(f"ERROR: offers/{slug}.md not found.")
            sys.exit(1)
        client = vault.get_client(offer.get("client", ""))
        if not client:
            print(f"ERROR: clients/{offer.get('client', '?')}/overview.md not found.")
            sys.exit(1)
        print(render_skeleton(offer, client))
        return

    try:
        out = build_skeleton(slug, force=force)
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Wrote: {out}")
    print(f"Verify: python3 -c \"import ast; ast.parse(open('{out}').read())\" && echo OK")
    print(f"Next:   /build-sequence {slug}    (LLM copy + QA + 4 files)")
    print(f"Or:     edit {out} directly to fill TODO copy markers")


if __name__ == "__main__":
    _cli()
