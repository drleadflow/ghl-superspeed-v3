#!/usr/bin/env python3
"""
Summer Glow — Fallback Nurture (form leads who never text) — A Prestige, Franklin TN

Framework mirror of campaigns/wrinklereset-nurture.py. Trigger = tag
`summerglow-qualify` added → 6-touch nurture over 7 days in Andrea's voice.
Compliant copy: no drug names, no guaranteed outcomes, free-consultation offer.
Exits: Stop on Response (patched post-build) · `claimed-summerglow` goal (UI) ·
appointment-booked exit workflow.

Usage: python3 campaigns/prestige-summerglow-nurture.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, wait_step, tag_step, link_steps,
)

LOCATION_ID = "9uog1fOUDtxkSr4ZPx1i"   # A Prestige (verified vs closebot-account-map)
COMPANY_ID = "R1HWQKyMMoj4PJ5mAYed"
PARENT_FOLDER = "fc6df18a-2058-468f-9591-c2c22691899e"  # Summer Glow Funnel folder

QUALIFY_TAG = "summerglow-qualify"
EXHAUSTED_TAG = "nurture | exhausted | summerglow"

CAMPAIGN = {
    "nurture": {
        "name": "Summer Glow — Qualify Nurture (No Text)",
        "tag": QUALIFY_TAG,
        "templates": link_steps([
            wait_step("5 Min", 5, "minutes"),
            sms_step("Is This You Opener",
                "Hey, is this {{contact.first_name}}? This is Andrea's office at A Prestige "
                "in Franklin — your Summer Glow request just came through! ☀️ Want me to hold "
                "a free consultation spot for you this week? Just reply \"hold my spot\""),
            wait_step("4 Hours", 4, "hours"),
            sms_step("The Value",
                "No pressure {{contact.first_name}} — the consultation is free and completely "
                "personalized. Andrea (Women's Health NP, 23 years) looks at your skin AND the "
                "whole picture, then maps your 8-week plan. If it's not the right fit, she'll "
                "tell you. Reply \"hold my spot\" and we'll find a time."),
            wait_step("1 Day (VM drop goes here)", 1, "days"),
            # MANUAL: insert ringless-voicemail step here in the GHL UI
            wait_step("1 Day", 1, "days"),
            sms_step("Scarcity + Deadline",
                "Quick one {{contact.first_name}} — summer protocol spots are limited and this "
                "week's consultation calendar is filling. Text me back and I'll get you in with "
                "Andrea before it closes out ☀️"),
            wait_step("2 Days (call task goes here)", 2, "days"),
            # task step inserted via API patch after build
            wait_step("3 Days", 3, "days"),
            sms_step("Takeaway Closer",
                "Hey {{contact.first_name}} — still want the free Summer Glow consultation? "
                "I don't want to keep blowing up your phone, so just reply \"yes please\" or "
                "\"no thanks\" and I'll take care of it either way \U0001F642"),
            wait_step("1 Day", 1, "days"),
            tag_step("Mark Nurture Exhausted", [EXHAUSTED_TAG]),
        ]),
    },
}


def main():
    client = GHLClient(TokenManager(LOCATION_ID), LOCATION_ID)
    print("Testing auth...")
    if not client.request("GET", f"/workflow/{LOCATION_ID}/list?parentId=root&limit=1"):
        print("Auth failed."); sys.exit(1)
    print("Auth OK\n")
    for tag in (QUALIFY_TAG, EXHAUSTED_TAG):
        client.create_location_tag(tag)
    builder = CampaignBuilder(client, LOCATION_ID)
    return builder.build(CAMPAIGN, folder_name="Summer Glow Nurture",
                         parent_folder=PARENT_FOLDER or None, company_id=COMPANY_ID)


if __name__ == "__main__":
    main()
