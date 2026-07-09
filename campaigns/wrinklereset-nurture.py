#!/usr/bin/env python3
"""
Wrinkle Reset — Fallback Nurture (form leads who never text) — TVAAI

Builds Workflow #3 from workspace/wrinklereset-nurture-workflow-spec.md:
trigger = tag `wrinklereset-qualify` added → 6-touch nurture over 7 days.

Engine-buildable steps only (sms/wait/add_contact_tag). Three finishing
touches are MANUAL in the GHL UI after this runs (see printout at end):
goal event (sophia-live → end), day-1 voicemail drop, day-4 call task.

Usage:
    python3 campaigns/wrinklereset-nurture.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, wait_step, tag_step, link_steps,
)

LOCATION_ID = "jiR5qR3g4OrMRx6BmpF2"   # TVAAI (verified vs closebot-account-map)
COMPANY_ID = "R1HWQKyMMoj4PJ5mAYed"
PARENT_FOLDER = ""

QUALIFY_TAG = "wrinklereset-qualify"
EXHAUSTED_TAG = "nurture | exhausted | wr founding"

CAMPAIGN = {
    "nurture": {
        "name": "Wrinkle Reset — Qualify Nurture (No Text)",
        "tag": QUALIFY_TAG,
        "templates": link_steps([
            wait_step("5 Min", 5, "minutes"),
            sms_step("Is This You Opener",
                "Hey, is this {{contact.first_name}}? It's Sophia with TVAAI — your "
                "Wrinkle Reset request just came through and I've got one of the 50 "
                "founding spots with your name on it \U0001F642 Want me to hold it? "
                "Just reply \"hold my spot\""),
            wait_step("4 Hours", 4, "hours"),
            sms_step("The Math",
                "No pressure {{contact.first_name}} — I just don't want you paying "
                "$560 for your next 40 units when it could be $360 here. Same "
                "Allergan Botox, $9/unit as a founding member. Reply \"hold my "
                "spot\" and it's yours."),
            wait_step("1 Day (VM drop goes here)", 1, "days"),
            # MANUAL: insert ringless-voicemail step here in the GHL UI
            wait_step("1 Day", 1, "days"),
            sms_step("Scarcity + Deadline",
                "Quick one {{contact.first_name}} — the founding spots are going to "
                "Houston ladies done paying $14/unit at the \"luxury\" places. Yours "
                "is held through this week only. Text me back and I'll lock in your "
                "$9/unit before they're gone ✨"),
            wait_step("2 Days (call task goes here)", 2, "days"),
            # MANUAL: insert "Add Task" step here in the GHL UI (day-4 call)
            wait_step("3 Days", 3, "days"),
            sms_step("Takeaway Closer",
                "Hey {{contact.first_name}} — still want the $9/unit founding spot? "
                "I don't want to keep blowing up your phone, so just reply \"yes "
                "please\" or \"no thanks\" and I'll take care of it either way \U0001F642"),
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
        print("Auth failed — no token. See engine token options.")
        sys.exit(1)
    print("Auth OK\n")

    # Tags must exist at location level before trigger/steps reference them
    for tag in (QUALIFY_TAG, EXHAUSTED_TAG):
        ok = client.create_location_tag(tag)
        print(f"Tag {'created/exists' if ok else 'CREATE FAILED'}: {tag}")
    print()

    builder = CampaignBuilder(client, LOCATION_ID)
    stats = builder.build(
        CAMPAIGN,
        folder_name="Wrinkle Reset Funnel",
        parent_folder=PARENT_FOLDER or None,
        company_id=COMPANY_ID,
    )

    print("\nMANUAL FINISHING TOUCHES (GHL UI, ~5 min):")
    print("  1. Goal Event: Contact Tag Added `sophia-live` → End this workflow")
    print("  2. Insert ringless-VM step after 'Wait 1 Day (VM drop goes here)'")
    print("  3. Insert Add Task step after 'Wait 2 Days (call task goes here)'")
    print("  4. Set SMS send window 9:00–20:00 in workflow settings")
    print("  5. PUBLISH the workflow + trigger")
    return stats


if __name__ == "__main__":
    main()
