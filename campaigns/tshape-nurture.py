#!/usr/bin/env python3
"""
T-Shape — Fallback Nurture (form leads who never text) — TVAAI

Mirror of campaigns/wrinklereset-nurture.py for the $199 T-Shape Body Sculpting
intro offer. Same architecture: trigger = tag `tshape-qualify` added → 6-touch
nurture over 7 days. Post-build API patches (stopOnResponse, task step, publish)
are applied by the runner in this session; manual UI items: goal event, VM step,
send window.

Usage:
    python3 campaigns/tshape-nurture.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, wait_step, tag_step, link_steps,
)

LOCATION_ID = "jiR5qR3g4OrMRx6BmpF2"   # TVAAI
COMPANY_ID = "R1HWQKyMMoj4PJ5mAYed"
PARENT_FOLDER = "3add24e6-713f-4263-9c10-ab93fdf04239"  # Wrinkle Reset Funnel folder (rename to "TVAAI Funnels" in UI if desired)

QUALIFY_TAG = "tshape-qualify"
EXHAUSTED_TAG = "nurture | exhausted | tshape"

CAMPAIGN = {
    "nurture": {
        "name": "T-Shape — Qualify Nurture (No Text)",
        "tag": QUALIFY_TAG,
        "templates": link_steps([
            wait_step("5 Min", 5, "minutes"),
            sms_step("Is This You Opener",
                "Hey, is this {{contact.first_name}}? It's Sophia with TVAAI — your "
                "T-Shape body sculpting request just came through and I'm holding one "
                "of the 7 intro-pricing spots for you \U0001F642 Want me to lock it in? "
                "Just reply \"hold my spot\""),
            wait_step("4 Hours", 4, "hours"),
            sms_step("The Value",
                "No pressure {{contact.first_name}} — quick recap: your $199 T-Shape "
                "session targets stubborn fat AND tightens skin in one 45-minute visit. "
                "No surgery, no downtime, back to your day right after. Reply \"hold my "
                "spot\" and it's yours."),
            wait_step("1 Day (VM drop goes here)", 1, "days"),
            # MANUAL: insert ringless-voicemail step here in the GHL UI
            wait_step("1 Day", 1, "days"),
            sms_step("Scarcity + Deadline",
                "Quick one {{contact.first_name}} — the 7 intro spots for T-Shape are "
                "nearly gone and yours is only held through this week. Text me back and "
                "I'll lock in your $199 session before they're filled ✨"),
            wait_step("2 Days (call task goes here)", 2, "days"),
            # task step inserted via API patch after build
            wait_step("3 Days", 3, "days"),
            sms_step("Takeaway Closer",
                "Hey {{contact.first_name}} — still want the $199 T-Shape intro session? "
                "I don't want to keep blowing up your phone, so just reply \"yes please\" "
                "or \"no thanks\" and I'll take care of it either way \U0001F642"),
            wait_step("1 Day", 1, "days"),
            tag_step("Mark Nurture Exhausted", [EXHAUSTED_TAG]),
        ]),
    },
}


def main():
    token_mgr = TokenManager(LOCATION_ID)
    client = GHLClient(token_mgr, LOCATION_ID)
    print("Testing auth...")
    if not client.request("GET", f"/workflow/{LOCATION_ID}/list?parentId=root&limit=1"):
        print("Auth failed."); sys.exit(1)
    print("Auth OK\n")
    for tag in (QUALIFY_TAG, EXHAUSTED_TAG):
        client.create_location_tag(tag)
    builder = CampaignBuilder(client, LOCATION_ID)
    # Build directly into the existing folder: pass folder as parent via a
    # one-workflow campaign; CampaignBuilder creates its own folder, so we
    # instead create the workflow manually if folder nesting matters.
    stats = builder.build(
        CAMPAIGN,
        folder_name="T-Shape Funnel",
        parent_folder=PARENT_FOLDER or None,
        company_id=COMPANY_ID,
    )
    return stats


if __name__ == "__main__":
    main()
