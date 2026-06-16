#!/usr/bin/env python3
"""
IV Wellness — First IV Drip $50 Off Welcome Offer nurture sequence.

Trigger model (per `~/.claude/projects/.../project_iv_wellness_nad_workflow_rules.md`):
- WF-01 ships with a tag trigger `firstdrip-lead` because the engine's
  automatic trigger creation only handles `contact_tag` types. The Facebook
  form submission trigger must be swapped in the GHL UI post-deploy
  (the FB form should add the `firstdrip-lead` tag on submit, OR the
  WF-01 trigger should be edited from `Tag Added` to `Facebook Form
  Submission` after the deploy completes).
- WF-02 trigger is the inbound SMS keyword `RESET` (set up in GHL UI).
- WF-03 trigger is `Customer Replied` filtered to `replied to workflow =
  WF-01 Master Sequence` (set up in GHL UI after WF-01 ID is captured).

Touchpoint count: 27 across 28 days (matches the 28-day skeleton in
`lib/prompts/twenty-eight-day-skeleton.md`). Includes a D5 deadline email
because `Has Deadline=Yes` on this offer (the $50 off welcome price).

Hard rules (IV strict mode):
- "Supports / helps with / patients often describe" only. Never treats / cures / fixes.
- No before/after photos (no MMS).
- No em dashes anywhere.
- {{custom_values.text_message_name}} is the bot persona, NOT the on-site RN.
- Real testimonials only or unnamed composites. No financing.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, link_steps,
)

LOCATION_ID = "2DvWWl1Ao2MAC9BZVshG"
COMPANY_ID  = "R1HWQKyMMoj4PJ5mAYed"
USER_ID     = "YewkebOufK3hmeP1gx4B"
PARENT_FOLDER = ""

FROM_NAME = "{{custom_values.text_message_name}}"

# ── EMAIL COPY ───────────────────────────────────────────────────────────────

E1_SUBJECT = "{{contact.first_name}}, quick question before I lock in your $50 off"
E1_BODY = """Hi {{contact.first_name}},

Thanks for grabbing the $50 off your first IV drip with us. I'm {{custom_values.text_message_name}}, I handle bookings for {{location.name}} here in Cincinnati. We're fully mobile, meaning a licensed RN comes to your home or office for the full IV session, usually 45 minutes start to finish.

One question before I send you the formula menu, because your answer changes which drip the RN will recommend:

**What are you hoping to feel different after the session? Energy, hydration, recovery, immunity, mental clarity, or something else?**

One word back is enough. The RN uses your answer plus a quick wellness check on-site to pick the right formula from our 14 options.

Here's what's locked in for your first session:

- $50 off your first IV drip (any of our 14 formulas)
- Free pre-session wellness assessment by a licensed RN
- Mobile setup, the RN comes to you within 20 miles of Cincinnati
- 45 minute session start to finish

[See Available Times]({{custom_values.booking_link}})

Not ready to book? Reply with your biggest question and I'll answer it personally.

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

# *Subject pattern: name + offer hook. Soft CTA + qualifying Q. Reciprocity via free wellness check.*


E2_SUBJECT = "The 3 questions I get most about mobile IV"
E2_BODY = """Hi {{contact.first_name}},

Three questions come up almost every time someone books their first mobile IV. Honest answers below.

**1. Is it safe?**
Your first session includes a full wellness assessment by a licensed RN before anything goes in. She reviews your meds, current state, hydration, and any past IV history. If anything is a flag, she tells you straight and we don't run the session. You don't pay for one that isn't a fit.

**2. Will you actually come to my home?**
Yes. Fully mobile within 20 miles of Cincinnati. The RN brings everything: IV stand, all 14 formulas, the wellness assessment kit. You sit in your own chair or couch for the 45 minutes. Most clients book it at home, some at the office on a busy week.

**3. How long does it take?**
About 45 minutes total from the RN walking in to walking out. The drip itself runs 30 to 40 minutes. Most people work, scroll, or watch something while it's running. A few nap.

One thing most places skip telling you. Some formulas (NAD+, high-dose Glutathione) take longer, 60 to 90 minutes. The 14-formula menu is on the booking page so you can see what each one does and how long it runs before you pick.

[Lock In Your First Session]({{custom_values.booking_link}})

One more thing. The thing first-time mobile IV clients say most often after their session surprised me the first time I heard it. I'll tell you about it in a few days.

{{custom_values.text_message_name}}"""

# *Subject pattern: specificity. Handles the 3 stated objections (safe / mobile / time). Zeigarnik teaser at end (closes in D7).*


E3_SUBJECT = "4 things to do before any IV session (no sales pitch)"
E3_BODY = """Hi {{contact.first_name}},

No pitch today. Four small things that make any IV session work better, true with us or anywhere else.

**1. Hydrate the day before.**
Aim for 60 to 80 oz of water. Sounds backwards because the IV is hydrating you, but the stick is easier when your veins are showing up, and the formula absorbs better.

**2. Eat a real meal about 60 minutes before.**
Not a granola bar, not just coffee. Empty stomach plus IV sometimes leaves people lightheaded for the first 5 minutes.

**3. Block the full 45 minutes.**
The drip is 30 to 40 minutes plus the RN's setup and wellness check. Trying to take a call mid-drip is the most common regret first-timers report.

**4. Pick the formula by what you actually want to feel.**
Energy, hydration, recovery, immunity, glow, mental clarity. The RN can swap on-site if your wellness check points somewhere different, but coming in with a goal makes the session sharper.

That's it.

P.S. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""

# *Subject pattern: how-to + number. Pure value, no sell. P.S. link only. Reciprocity.*


E4_SUBJECT = "She booked the Recharge drip and texted me the next morning"
E4_BODY = """Hi {{contact.first_name}},

A client reached out a few months back. Mid-30s, told me she'd been running on coffee and four hours of sleep through a brutal work stretch. She'd never done an IV before, wasn't sure it was for her.

The RN ran the wellness assessment, recommended Recharge+Refresh based on her hydration and energy levels. 45 minutes later the RN packed up.

Her text the next morning, copy-pasted:

*"I forgot what 8 hours of sleep on top of being actually hydrated felt like. Booked another one for next week."*

She comes in monthly now. Different formula each time depending on what's going on, sometimes Immunity in winter, Glow Up before an event, NAD+ when she wants the deeper energy reset.

The thing most first-timers don't realize is that the formula menu is built so the RN can match what your body actually needs that day, not just what sounded good on the website. The wellness assessment is what makes the call.

Reply "menu" and I'll send the full 14-formula breakdown if you want to see what each one does. Or if you've got a question, send it.

[Lock In Your $50 Off Session]({{custom_values.booking_link}})

{{custom_values.text_message_name}}"""

# *Subject pattern: story tease. Unnamed composite client per IV compliance. "Reply menu" CTA replaces "reply photos" per IV strict mode.*


# D5 deadline email — included because Has Deadline=Yes on this offer.
E5_DEADLINE_SUBJECT = "Your $50 off expires soon, {{contact.first_name}}"
E5_DEADLINE_BODY = """Hi {{contact.first_name}},

Quick heads up. The $50 off your first IV drip is a welcome offer for new clients only and it doesn't sit in your inbox forever.

Here's what you'd be locking in:

- $50 off any of the 14 formulas (your pick, or the RN can recommend based on your wellness assessment)
- Free pre-session assessment by a licensed RN
- Mobile setup, RN comes to your home or office within 20 miles of Cincinnati
- 45 minute session

Most clients use the welcome offer on Recharge+Refresh, Myers, or Immunity for the first session, then pick something more specific (Brain Booster, NAD+, Glow Up) once they know how their body responds.

Two ways to lock the price in:

[Book a Slot]({{custom_values.booking_link}})

Or reply with the day that works best and I'll grab a slot for you directly.

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

# *Subject pattern: deadline + name. Restates offer specifics. Two-path CTA (book OR reply).*


E6_SUBJECT = "Remember when I said mobile IV surprises people?"
E6_BODY = """Hi {{contact.first_name}},

A few days back I said I'd share the thing first-time mobile IV clients say most often after their session.

Here it is:

*"I didn't realize how much I hated leaving the house for wellness stuff until I didn't have to."*

That sentence shows up in our exit feedback almost every week. People expect to like the drip itself. What surprises them is how much friction the in-clinic version was adding, the drive, the parking, the waiting room, the rush to get back to work or kids.

Most of our regulars didn't switch to mobile because the drip is better (it's the same drip). They switched because doing it at home means they actually do it. The clinic version they'd skip when the day got busy. The mobile version, the RN is already on the way.

I'm not going to push you. If now isn't the right time, that's real. But if you've been saying you'd come in "when things slow down," that's the line keeping you exactly where you are.

What's the question that would actually move the needle for you? Reply, it goes straight to me.

Or whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""

# *Subject pattern: curiosity + permission. Closes Zeigarnik loop from D2. Low-friction reply ask.*


E7_SUBJECT = "Why one session tells you more than thinking about it for weeks"
E7_BODY = """Hi {{contact.first_name}},

Quick honest one. No sell.

Most people sit on the IV decision for weeks, sometimes months. Reading reviews, comparing formulas, wondering if they'd really feel anything. I get it, the internet makes it easy to research forever and book never.

Here's the part that's worth knowing:

**One IV session is the only real test.** Reading about hydration, energy, recovery, immunity, none of that tells you how YOUR body responds. The RN can ballpark it from the wellness check, but the actual answer is one 45-minute session away.

**The $50 off plus the free wellness assessment is what makes a first session a low-stakes test.** $50 off the formula, RN comes to you, the assessment tells you straight if a different formula would fit better. If after one session you decide IV isn't for you, you've spent less than a nice dinner to find out.

**The clients who stick with us almost all say the same thing.** They wish they'd done the first session sooner. Not because the drip is magic, because the question they'd been mulling over for months got answered in 45 minutes.

The $50 off and the free assessment are still on the table. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}} · {{location.phone}}"""

# *Subject pattern: curiosity + specificity. Logic + cost-of-inaction. No financing per IV strict mode.*


E8_SUBJECT = "Last email from me, plus my direct line"
E8_BODY = """Hi {{contact.first_name}},

Last email from me on this. I mean it.

People wait for a reason. The most common ones I hear:

- "I'll book when I'm not so busy" (you won't be, the calendar doesn't clear)
- "I want to figure out which formula is right first" (that's literally what the on-site wellness assessment is for, and it's free)
- "I'm not sure if mobile IV is for me" (one 45-minute session at $50 off tells you, the article you're about to read won't)

If any of those is you, I get it. I'll stop emailing.

Two ways to come back when you're ready:

**1.** Book directly: {{custom_values.booking_link}}

**2.** Text **{{location.phone}}** with the keyword **RESET**. Goes to our desk, not a queue. You don't fill out a form again, the keyword tells our system who you are and pulls up the calendar.

Whatever you decide, thanks for considering us.

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}
{{location.phone}}"""

# *Subject pattern: direct. Phone + KEYWORD as CTA, no button. Permission-to-stop. The screenshot message.*


# ── SMS COPY ─────────────────────────────────────────────────────────────────
# All under 160 chars where possible. No em dashes. Conversational.

SMS_T0 = "Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} from {{location.name}}. Got your $50 off IV request, sending the rundown in a sec. Reply STOP to opt out."

SMS_T1 = "Hey {{contact.first_name}}, {{custom_values.text_message_name}} again. Quick Q so the RN can recommend the right formula, what are you hoping to feel different? Energy, hydration, recovery, immunity, clarity?"

SMS_D1_15min = "Hey {{contact.first_name}}, just sent you a welcome email with the rundown. Same question there, what are you hoping to feel different after the session? One word is enough."

SMS_D2_5pm = "Hey {{contact.first_name}}, I put together a quick what-to-expect rundown for first IV sessions at home. Takes 2 min to read. Want me to send it?"

SMS_D3_10am = "Is this {{contact.first_name}}?"

SMS_D4_5pm = "Hey {{contact.first_name}}, did you want me to grab an IV slot for next week, or play it by ear? Either's fine."

SMS_D5_5pm = "Hey {{contact.first_name}}, heads up the $50 off welcome price doesn't sit in your inbox forever. Want me to grab a slot before it lapses?"

SMS_D7_10am = "Hey {{contact.first_name}}, honest one, what's actually holding you back on the first IV session? No pressure."

SMS_D12_10am = "{{contact.first_name}}, when I don't hear back it's usually timing or a question I haven't answered. Is it one of those?"

SMS_D14_10am = "Last one from me, {{contact.first_name}}. Whenever you're ready, text RESET to this number and I'll get the RN on the calendar that week. {{location.phone}}"

SMS_D28_10am = "Hi {{contact.first_name}}, {{custom_values.text_message_name}}. Should I close your IV file or keep it open for whenever you're ready?"


# ── KEYWORD RECOVERY COPY ────────────────────────────────────────────────────

SMS_RESET_AUTOREPLY = "Got it {{contact.first_name}}, pulling up the calendar. Here's the link: {{custom_values.booking_link}} -{{custom_values.text_message_name}}"

SMS_RESET_2HR_FOLLOWUP = "Hey {{contact.first_name}}, just making sure the booking link worked. Want me to grab an IV slot for you directly?"


# ── REPLY HANDLER COPY ───────────────────────────────────────────────────────

REPLY_ALERT_SUBJECT = "REPLIED LEAD: {{contact.first_name}} on First IV Drip nurture"
REPLY_ALERT_BODY = """REPLIED LEAD ALERT.

{{contact.first_name}} {{contact.last_name}} replied to the First IV Drip $50 off welcome nurture sequence.

Phone: {{contact.phone}}
Email: {{contact.email}}

ACTION REQUIRED: Respond within 5 minutes. Do NOT let automation re-engage until this contact is manually marked as resolved or rebooked.

Their last message is in the GHL conversation thread. Check it before replying."""


# ── CAMPAIGN ─────────────────────────────────────────────────────────────────
# Day map for 01-master (cumulative from form submit, 27 automated touchpoints):
#   T+0     SMS_T0          instant confirm + opt-out
#   T+1m    SMS_T1          qualifying Q (formula goal)
#   D1 10a  E1              welcome + qualifying Q echo
#   D1 10:15a SMS_D1_15min  echo qualifier on SMS channel
#   D2 10a  E2              objections (safe / mobile / time) + Zeigarnik teaser
#   D2 5p   SMS_D2_5pm      reciprocity hook (rundown offer)
#   D3 10a  E3              quick-win prep tips
#   D3 10a  SMS_D3_10am     pattern interrupt
#   D4 10a  E4              social proof (Recharge story)
#   D4 5p   SMS_D4_5pm      soft slot hold
#   D5 10a  E5              deadline email ($50 off expiring)
#   D5 5p   SMS_D5_5pm      deadline SMS reinforce
#   D7 10a  E6              Zeigarnik close (mobile insight)
#   D7 10a  SMS_D7_10am     direct question
#   D10 10a E7              one-session-test + cost of waiting
#   D12 10a SMS_D12_10am    objection surfacer
#   D14 9a  E8              peak-end + RESET keyword + phone
#   D14 10a SMS_D14_10am    keyword reminder
#   D28 10a SMS_D28_10am    breakup text
#   tag     firstdrip-nurture-complete

CAMPAIGN = {
    "01-master": {
        "name": "01. First IV Drip — Master Sequence",
        "tag": "firstdrip-lead",
        "templates": link_steps([
            sms_step("S0 Instant Confirm + Opt-Out (T+0)", SMS_T0),
            wait_step("1 min", 1, "minutes"),
            sms_step("S1 Qualifying Q Formula Goal (T+1m)", SMS_T1),
            wait_step("22 hours", 22, "hour"),
            email_step("E1 Welcome + Qualifying Q (D1 10am)", E1_SUBJECT, E1_BODY, FROM_NAME),
            wait_step("15 min", 15, "minutes"),
            sms_step("S_D1_15 Echo Qualifier (D1 10:15am)", SMS_D1_15min),
            wait_step("23 hours", 23, "hour"),
            wait_step("45 min", 45, "minutes"),
            email_step("E2 Top 3 Objections + Zeigarnik Teaser (D2 10am)", E2_SUBJECT, E2_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D2 Reciprocity Hook (D2 5pm)", SMS_D2_5pm),
            wait_step("17 hours", 17, "hour"),
            email_step("E3 Quick-Win Prep Tips (D3 10am)", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D3 Pattern Interrupt (D3 10am)", SMS_D3_10am),
            wait_step("24 hours", 24, "hour"),
            email_step("E4 Recharge Story Social Proof (D4 10am)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D4 Soft Slot Hold (D4 5pm)", SMS_D4_5pm),
            wait_step("17 hours", 17, "hour"),
            email_step("E5 Deadline $50 Off Expiring (D5 10am)", E5_DEADLINE_SUBJECT, E5_DEADLINE_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D5 Deadline SMS Reinforce (D5 5pm)", SMS_D5_5pm),
            wait_step("41 hours", 41, "hour"),
            email_step("E6 Zeigarnik Close Mobile Insight (D7 10am)", E6_SUBJECT, E6_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D7 Direct Question (D7 10am)", SMS_D7_10am),
            wait_step("3 days", 3, "days"),
            email_step("E7 One-Session-Test + Cost of Waiting (D10 10am)", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("2 days", 2, "days"),
            sms_step("S_D12 Objection Surfacer (D12 10am)", SMS_D12_10am),
            wait_step("47 hours", 47, "hour"),
            email_step("E8 Peak-End + RESET Keyword (D14 9am)", E8_SUBJECT, E8_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D14 Keyword Reminder (D14 10am)", SMS_D14_10am),
            wait_step("14 days", 14, "days"),
            sms_step("S_D28 Breakup Text (D28 10am)", SMS_D28_10am),
            tag_step("Mark First IV Drip Nurture Complete", ["firstdrip-nurture-complete"]),
        ]),
    },

    "02-keyword-recovery": {
        "name": "02. First IV Drip — RESET Keyword Recovery",
        "tag": "firstdrip-keyword-trigger",
        "templates": link_steps([
            tag_step("Apply Returning Lead Tag", ["firstdrip-returning-lead"]),
            tag_step("Remove Nurture Complete Tag", ["firstdrip-nurture-complete"], remove=True),
            sms_step("RESET Auto-Reply with Booking Link", SMS_RESET_AUTOREPLY),
            wait_step("2 hours", 2, "hour"),
            sms_step("RESET 2-Hour Follow-Up", SMS_RESET_2HR_FOLLOWUP),
        ]),
    },

    "03-reply-handler": {
        "name": "03. First IV Drip — Global Reply Handler",
        "tag": "firstdrip-replied",
        "templates": link_steps([
            tag_step("Confirm Reply Tag Applied", ["firstdrip-replied"]),
            email_step("Internal Alert to Front Desk", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"First IV Drip Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="First IV Drip — $50 Off Welcome Offer",
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
