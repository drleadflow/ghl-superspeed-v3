#!/usr/bin/env python3
"""
TVAAI — T-Shape2 Body Sculpting $199 Special nurture (REBUILD, relaxed cadence).

Rebuilt 2026-06-03 against `ghl-cli/TVAAI-setter-playbook-and-28day-nurture.md`.
The playbook's data is unambiguous: short, personal, one-question messages
convert; long salesy scarcity blasts destroy the list (18 of 20 opt-outs in the
data followed an automation blast). So this version is SMS-first, every text is
one fact + one question, emails are short value pieces with a single button, and
the old deadline/scarcity email is GONE.

WHAT CHANGED vs the v1 build:
- Trigger is now a NATIVE Facebook Lead Gen submission (not a tag swap post-deploy).
- Entry stamps `latest_optin` and CREATES an opportunity in the FlowBot Pipeline
  (Engagement: NEW Lead In), so every paid lead is attributed from message 1.
- Copy rewritten to the playbook house style: relaxed, natural, no scarcity.
- Touch 1 is overtly automated (system confirm + opt-out). Touch 2 lands a bit
  later and reads as a real person (Ashley) texting personally.
- Cadence relaxed: front-loaded first 72h (speed-to-lead), then a gentle taper
  every 1 to 4 days through day 28. ~13 SMS + 6 emails, no double value sends.
- Keyword is SCULPT (not RESET) so it never collides with the other live TVAAI
  offers (Wrinkle Reset, Lip Bacio, V-Hacker) that all reused RESET.
- Reply handler fires an INSTANT internal alert (playbook's never-ghost rule:
  any inbound question/yes with no reply in 5 min is the #1 recoverable leak).

COEXISTS WITH THE POWER-DIALER: a separate workflow calls the clinic and patches
the lead through within ~5 min (retry every 10 min, stop at 30 min). The T+0 SMS
below tells the lead a call is coming so the channels don't feel disjointed.

Trigger model (engine emits these natively — see lib/engine._build_trigger_body):
- WF-01: facebook_lead_gen, filtered to the connected TVAAI page. Set FB_FORM_ID
  to the specific T-Shape2 lead form in the GHL trigger UI to gate it precisely
  (page filter alone also catches the other offers' forms).
- WF-02: contact_tag `tshape2-keyword-trigger`. Wire the inbound SMS keyword
  SCULPT in the GHL UI, filtered to contacts holding `tshape2-lead`.
- WF-03: customer_reply filtered to "replied to WF-01". Also enable the
  workflow's "remove from other workflows on reply" so the cadence pauses while
  the setter / AI talks (playbook A5 + suppression rules).

Compliance (TVAAI premium voice + body-composition rules):
- "supports body contouring / circumference reduction across a series / patients
  often describe inches lost over a series." Never treats / cures / melts / burns
  / guaranteed / "lose X inches" / before-after / instant / 100%.
- T-Shape2 = non-invasive RF + EMS, zero downtime. One session is a test of how
  the body responds, not the final result; results compound over 6 to 12 sessions.
- No em dashes in customer-facing body strings (use " - "). Workflow DISPLAY names
  use " — " per the v3 convention.
- {{custom_values.text_message_name}} is the front-desk persona (Ashley).
- {{custom_values.booking_link}} must be set to https://tvaa.doctorleadflow.com/t-shapecal
  (run scripts/set_custom_values.py if not already set).
- Tag prefix: `tshape2-`
"""

import sys, os, uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step,
    update_contact_field_step, link_steps,
)

LOCATION_ID = "jiR5qR3g4OrMRx6BmpF2"
COMPANY_ID  = "R1HWQKyMMoj4PJ5mAYed"
USER_ID     = "YewkebOufK3hmeP1gx4B"
PARENT_FOLDER = ""

FROM_NAME = "{{custom_values.text_message_name}}"

# ── Pipeline (FlowBot Pipeline, live lookup 2026-06-03) ───────────────────────
PIPELINE_ID       = "u09rpJjacN2ZGQR8SJvi"                    # FlowBot Pipeline
STAGE_ENGAGEMENT  = "95602725-cc9f-4989-bd18-3517c1bd0096"    # Engagement (NEW: Lead In)
STAGE_ENGAGED     = "73f303ed-8139-4a71-b6c2-d806e64a3124"    # ENG: Engaged (replied)
STAGE_QUALIFYING  = "6139a713-c939-487c-917a-a2a99ea121cc"    # QUAL: Qualifying
STAGE_NOREPLY     = "e3d0b6f0-5433-4525-a4a8-af9c482bf89b"    # NR: 28-Day No-Reply

# ── Latest Opt-In custom field (live lookup 2026-06-03) ───────────────────────
LATEST_OPTIN_FIELD = "gc3xB0SQn4Vm3xitMxft"                   # contact.latest_optin
LATEST_OPTIN_VALUE = "T-Shape2 $199 Special"

# ── Facebook Lead Gen trigger ─────────────────────────────────────────────────
FB_PAGE_ID = "68bb1c6be605ed4b55c7e2c2"   # the one connected TVAAI page (live)
FB_FORM_ID = ""                           # set the T-Shape2 form in the GHL UI to gate precisely

KEYWORD = "SCULPT"


# ── Local step builders for action types the engine has no helper for ──────────
# internal_create/update_opportunity schemas captured live from this account's
# existing workflows (mirrors campaigns/prestige-metabolic-reset-nurture.py).

def _uid() -> str:
    return str(uuid.uuid4())


def create_opportunity_step(name: str, pipeline_id: str, stage_id: str,
                            source: str = "T-Shape2 $199 Special") -> dict:
    return {"id": _uid(), "type": "internal_create_opportunity", "name": name,
            "attributes": {
                "pipelineId": pipeline_id,
                "type": "internal_create_opportunity",
                "__customInputFields__": [
                    {"__customInputs__": {}, "filterField": "pipelineStageId",
                     "value": stage_id, "valueFieldType": "select"},
                    {"__customInputs__": {}, "filterField": "source",
                     "value": source, "valueFieldType": "string"},
                ],
                "__customInputs__": {},
            }}


# NOTE: `internal_update_opportunity` is rejected by the save API ("corrupted
# type"). GHL's create-opportunity action UPSERTS — for a contact who already
# has an opp in this pipeline it just moves the stage — so all stage MOVES below
# reuse create_opportunity_step (verified gotcha 2026-06-03; matches prestige).


def internal_sms_alert_step(name: str, body: str) -> dict:
    """Internal SMS notification to the assigned user (fires to whoever's
    assigned; no-op if unassigned, so it never force-reassigns)."""
    return {"id": _uid(), "type": "internal_notification", "name": name,
            "attributes": {"type": "sms",
                           "sms": {"body": body, "userType": "assign",
                                   "attachments": []}}}


# ── SMS COPY ───────────────────────────────────────────────────────────────────
# House style: one fact + one question, conversational, no em dashes.
# T0 is the automated system confirm. T2 onward read like Ashley personally.

SMS_T0 = ("Hi {{contact.first_name}}, this is {{location.name}}. Got your $199 "
          "T-Shape2 request - someone will try you by phone shortly. "
          "Reply STOP to opt out.")

SMS_T2_HUMAN = ("Hey {{contact.first_name}}, it's {{custom_values.text_message_name}} "
                "at TVAAI. What area are you hoping to tighten or tone?")

SMS_D0_4HR = ("{{contact.first_name}}, I can hold a $199 T-Shape2 spot this week - "
              "are mornings or afternoons easier for you?")

SMS_D1 = ("Still happy to hold a T-Shape2 spot for you, {{contact.first_name}}. "
          "Want me to grab one, or still deciding?")

SMS_D2_PHONE = ("{{contact.first_name}}, sometimes it's easier by phone. Is this a "
                "good number to reach you at?")

SMS_D3 = ("Want me to get you on the T-Shape2 calendar this week, "
          "{{contact.first_name}}? I can text you the link right now.")

SMS_D6_PRICE = ("Quick note {{contact.first_name}} - the $199 is your first session "
                "plus the body assessment, no commitment after. Want the link?")

SMS_D10 = ("{{contact.first_name}}, I've got a couple T-Shape2 openings this week. "
           "Want one held, no obligation?")

SMS_D12 = ("Still on your mind, {{contact.first_name}}? Happy to answer anything "
           "about T-Shape2 - what's your main hesitation?")

SMS_D16 = ("No rush {{contact.first_name}} - want me to pencil in a T-Shape2 time "
           "for whenever's easier and send the details?")

SMS_D20 = ("{{contact.first_name}}, yes or no - still thinking about T-Shape2 "
           "this season?")

SMS_D24 = ("I can still hold a $199 T-Shape2 session next week if it helps, "
           "{{contact.first_name}} - want one?")

SMS_D27 = ("Want me to keep checking in, {{contact.first_name}}, or pause for now? "
           "Totally your call.")


# ── EMAIL COPY ─────────────────────────────────────────────────────────────────
# Short. dm_email() renders one <p> per non-blank line (single enter between
# sections). A bare "[Label]" line auto-links to {{custom_values.booking_link}}.

E1_SUBJECT = "{{contact.first_name}}, here's everything on your $199 T-Shape2"
E1_BODY = """Hi {{contact.first_name}},
Quick rundown on the $199 T-Shape2 session you reached out about, so you have it in writing.
What the $199 includes:
- A complimentary body composition assessment with our team
- One T-Shape2 session, RF plus EMS, about 30 to 45 minutes
- A look at which areas would respond best if you decide on a series
- Zero downtime, you head right back to your day
The honest version: T-Shape2 supports body contouring and skin tightening across a series. One session is a real test of how your body responds, not the final result. The $199 (regularly $350) is built so you can run that test before deciding on anything more.
We're at 2603 Augusta Dr, Suite 1450 in Houston.
[See Available Times]
Or just reply with the area you want to work on - a real person reads these.
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""


E2_SUBJECT = "What to expect at your T-Shape2 session"
E2_BODY = """Hi {{contact.first_name}},
If you've never done a body contouring session, here's exactly what a T-Shape2 visit looks like, start to finish.
- First, a quick body composition assessment so we know your starting point and which areas to focus on
- Then the session: a warm handpiece moves over the area for 30 to 45 minutes. Most patients describe it as relaxing, like a warm deep-tissue massage
- After: nothing. No downtime, no marks, no recovery. You can work out, go to dinner, or head back to work
That's the whole visit. Real contouring builds across a series, but the first session shows you how your body responds.
[See Available Times]
- {{custom_values.text_message_name}}"""


E3_SUBJECT = "The one thing patients wish they'd known about body contouring"
E3_BODY = """Hi {{contact.first_name}},
No pitch today. Just the thing patients tell us they wish they'd understood sooner about non-invasive body contouring.
It's this: the scale is the wrong way to measure it.
T-Shape2 supports circumference reduction and skin tightening in the areas we treat. That shows up in how your clothes fit and in your measurements, often before it shows up on the scale, because you're changing the shape of an area, not your overall weight.
The patients who get the most from it are the ones already consistent with movement and nutrition who have hit a stubborn area that won't budge. It supports that work. It doesn't replace it.
If that sounds like you, the $199 first session is the lowest-stakes way to see how your body responds.
[See Available Times]
- {{custom_values.text_message_name}}"""


E4_SUBJECT = "How one patient tested T-Shape2 before committing"
E4_BODY = """Hi {{contact.first_name}},
One short story, because it's the most common version of why patients book the $199.
A patient reached out earlier this year. In good shape, two kids, had been working the same lower-ab area for almost a year with diet and training and stopped seeing change. She didn't want to commit to a series before knowing if her body would even respond, so she booked the $199 first session just to test it.
Her words about a week later: "Felt different in my clothes by day 5. Just enough to tell something was finally engaging that area." She's now partway through a series.
That's what the $199 is for. The test, not the transformation. You find out how your body responds, then you decide.
[See Available Times]
- {{custom_values.text_message_name}}"""


E5_SUBJECT = "What realistic T-Shape2 results actually look like"
E5_BODY = """Hi {{contact.first_name}},
Worth being straight with you about what to expect, because honest expectations are what make patients happy with the result.
- One session is a test, not a finish line. You may notice a subtle change in how an area feels or how clothes fit. That's the signal your body responds
- Real contouring compounds across a series, usually 6 to 12 sessions, with the most noticeable change around the middle of the series
- It's not weight loss. It supports the shape of treated areas. If the scale is your only goal, we'll tell you honestly at the assessment
No hype and no guarantees, just the technology doing what it does on the right candidate.
The $199 first session and the assessment are still open whenever you want the data.
[See Available Times]
- {{custom_values.text_message_name}} · {{location.phone}}"""


E6_SUBJECT = "I'll stop here, {{contact.first_name}} - but the door's open"
E6_BODY = """Hi {{contact.first_name}},
This is the last note from me on the $199 T-Shape2 session, and I mean it. No hard feelings if the timing just isn't right.
If it ever is, two easy ways back:
1. Book whenever you like: [See Available Times]
2. Text SCULPT to {{location.phone}} and we'll pull up the body sculpting calendar and find you a time. No need to fill anything out again.
Whatever you decide, thanks for considering us.
{{custom_values.text_message_name}}
{{location.name}}
2603 Augusta Dr, Suite 1450, Houston
{{location.phone}}"""


# ── KEYWORD RECOVERY COPY (SCULPT) ─────────────────────────────────────────────

SMS_SCULPT_AUTOREPLY = ("Got it {{contact.first_name}}, pulling up the body sculpting "
                        "calendar. Here's the link: {{custom_values.booking_link}} "
                        "-{{custom_values.text_message_name}}")

SMS_SCULPT_2HR = ("Hey {{contact.first_name}}, just checking the booking link worked. "
                  "Want me to grab a $199 T-Shape2 slot for you directly?")


# ── REPLY HANDLER COPY ─────────────────────────────────────────────────────────

REPLY_ALERT_SMS = ("REPLIED: {{contact.first_name}} {{contact.last_name}} answered the "
                   "T-Shape2 nurture. Reply within 5 min. Phone {{contact.phone}}.")

REPLY_ALERT_SUBJECT = "REPLIED LEAD: {{contact.first_name}} on T-Shape2 nurture"
REPLY_ALERT_BODY = """REPLIED LEAD ALERT.
{{contact.first_name}} {{contact.last_name}} replied to the T-Shape2 Body Sculpting nurture.
Phone: {{contact.phone}}
Email: {{contact.email}}
ACTION: Respond within 5 minutes (never-ghost rule). After 2 answered questions, send two concrete slots plus the booking link in the same message - do not end on an open question.
Their last message is in the GHL conversation thread."""


# ── CAMPAIGN ───────────────────────────────────────────────────────────────────
# 01-master timeline (cumulative from FB form submit):
#   T+0       SMS_T0          automated confirm + opt-out (call is also coming)
#   T+25m     SMS_T2_HUMAN    Ashley, personal, one question (what area)
#   T+1h      E1              what the $199 includes + plain pricing + address
#   T+4h      SMS_D0_4HR      soft hold (mornings vs afternoons)
#   D1        SMS_D1          re-offer, single question
#   D2        E2              what to expect at the session (3 bullets)
#   D2 pm     SMS_D2_PHONE    phone pivot (winning line from the data)
#   D3        SMS_D3          direct booking ask
#   D5        E3              education (scale is the wrong measure)
#   D6        SMS_D6_PRICE    price pre-empt ($199, no commitment)
#   D7        E4              single social proof, short
#   D10       SMS_D10         soft availability, no scarcity
#   D12       SMS_D12         hesitation surfacer
#   D14       E5              realistic results expectations
#   D16       SMS_D16         payday-friendly pencil-in
#   D20       SMS_D20         yes/no revive
#   D24       SMS_D24         concrete offer again
#   D27       SMS_D27         soft breakup setup
#   D28       E6              graceful breakup + SCULPT keyword
#   D28       move opp -> NR: 28-Day No-Reply + tag complete

CAMPAIGN = {
    "01-master": {
        "name": "01. T-Shape2 Body Sculpting — Master Sequence",
        "trigger": {
            "type": "facebook_lead_gen",
            "fb_page_id": FB_PAGE_ID,
            "fb_form_id": FB_FORM_ID or None,
            "name": "T-Shape2 $199 - Facebook Lead Form Submitted",
        },
        "templates": link_steps([
            update_contact_field_step("Stamp Latest Opt-In = T-Shape2 $199",
                                      LATEST_OPTIN_FIELD, LATEST_OPTIN_VALUE,
                                      title="Latest Opt-In", field_type="string"),
            create_opportunity_step("Create Opp — FlowBot / Engagement (New Lead In)",
                                    PIPELINE_ID, STAGE_ENGAGEMENT),
            sms_step("S0 Automated Confirm + Opt-Out (T+0)", SMS_T0),
            wait_step("25 min", 25, "minutes"),
            sms_step("S2 Personal Hello — What Area (T+25m)", SMS_T2_HUMAN),
            wait_step("35 min", 35, "minutes"),
            email_step("E1 Rundown + Pricing + Address (T+1h)", E1_SUBJECT, E1_BODY, FROM_NAME),
            wait_step("3 hours", 3, "hour"),
            sms_step("S_D0 Soft Hold Mornings vs Afternoons (T+4h)", SMS_D0_4HR),
            wait_step("20 hours", 20, "hour"),
            sms_step("S_D1 Re-Offer Single Question (D1)", SMS_D1),
            wait_step("22 hours", 22, "hour"),
            email_step("E2 What to Expect at the Session (D2)", E2_SUBJECT, E2_BODY, FROM_NAME),
            wait_step("6 hours", 6, "hour"),
            sms_step("S_D2 Phone Pivot (D2 pm)", SMS_D2_PHONE),
            wait_step("16 hours", 16, "hour"),
            sms_step("S_D3 Direct Booking Ask (D3)", SMS_D3),
            wait_step("2 days", 2, "days"),
            email_step("E3 Education — Scale Is the Wrong Measure (D5)", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("1 day", 1, "days"),
            sms_step("S_D6 Price Pre-Empt (D6)", SMS_D6_PRICE),
            wait_step("1 day", 1, "days"),
            email_step("E4 Single Social Proof (D7)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("3 days", 3, "days"),
            sms_step("S_D10 Soft Availability (D10)", SMS_D10),
            wait_step("2 days", 2, "days"),
            sms_step("S_D12 Hesitation Surfacer (D12)", SMS_D12),
            wait_step("2 days", 2, "days"),
            email_step("E5 Realistic Results Expectations (D14)", E5_SUBJECT, E5_BODY, FROM_NAME),
            wait_step("2 days", 2, "days"),
            sms_step("S_D16 Payday-Friendly Pencil-In (D16)", SMS_D16),
            wait_step("4 days", 4, "days"),
            sms_step("S_D20 Yes/No Revive (D20)", SMS_D20),
            wait_step("4 days", 4, "days"),
            sms_step("S_D24 Concrete Offer Again (D24)", SMS_D24),
            wait_step("3 days", 3, "days"),
            sms_step("S_D27 Soft Breakup Setup (D27)", SMS_D27),
            wait_step("1 day", 1, "days"),
            email_step("E6 Graceful Breakup + SCULPT Keyword (D28)", E6_SUBJECT, E6_BODY, FROM_NAME),
            create_opportunity_step("Move Opp — NR: 28-Day No-Reply (upsert)",
                                    PIPELINE_ID, STAGE_NOREPLY),
            tag_step("Mark T-Shape2 Nurture Complete", ["tshape2-nurture-complete"]),
        ]),
    },

    "02-keyword-recovery": {
        "name": "02. T-Shape2 Body Sculpting — SCULPT Keyword Recovery",
        "tag": "tshape2-keyword-trigger",
        "templates": link_steps([
            tag_step("Apply Returning Lead Tag", ["tshape2-returning-lead"]),
            tag_step("Remove Nurture Complete Tag", ["tshape2-nurture-complete"], remove=True),
            create_opportunity_step("Move Opp — ENG: Engaged (upsert)",
                                    PIPELINE_ID, STAGE_ENGAGED),
            sms_step("SCULPT Auto-Reply with Booking Link", SMS_SCULPT_AUTOREPLY),
            wait_step("2 hours", 2, "hour"),
            sms_step("SCULPT 2-Hour Follow-Up", SMS_SCULPT_2HR),
        ]),
    },

    "03-reply-handler": {
        "name": "03. T-Shape2 Body Sculpting — Global Reply Handler",
        "trigger": {"type": "customer_reply", "source_wf_key": "01-master"},
        "templates": link_steps([
            tag_step("Confirm Reply Tag Applied", ["tshape2-replied"]),
            create_opportunity_step("Move Opp — ENG: Engaged (replied, upsert)",
                                    PIPELINE_ID, STAGE_ENGAGED),
            internal_sms_alert_step("Instant Internal SMS Alert (5-min rule)", REPLY_ALERT_SMS),
            email_step("Internal Email Alert to Front Desk", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── RUN ────────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"T-Shape2 Body Sculpting Nurture (rebuild): {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

    token_mgr = TokenManager(LOCATION_ID)
    if os.environ.get("GHL_FIREBASE_REFRESH_TOKEN"):
        token_mgr.set_refresh_token(os.environ["GHL_FIREBASE_REFRESH_TOKEN"])

    client = GHLClient(token_mgr, LOCATION_ID)

    print("Testing auth...")
    test = client.request("GET", f"/workflow/{LOCATION_ID}/list?parentId=root&limit=1")
    if not test:
        print("Auth failed! Check your token.")
        sys.exit(1)
    print("Auth OK\n")

    builder = CampaignBuilder(client, LOCATION_ID)
    stats = builder.build(
        CAMPAIGN,
        folder_name="T-Shape2 Body Sculpting — $199 Special",
        parent_folder=PARENT_FOLDER or None,
        company_id=COMPANY_ID,
        user_id=USER_ID,
    )

    if stats["steps_saved"] == total_steps:
        print(f"\nAll {total_steps} steps saved!")
    else:
        print(f"\nWARNING: Expected {total_steps}, saved {stats['steps_saved']}")


if __name__ == "__main__":
    main()
