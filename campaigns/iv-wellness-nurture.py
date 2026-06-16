#!/usr/bin/env python3
"""
IV Wellness Recovery System, 28-day nurture sequence.

Trigger: contact gets tag `iv-nurture-start`.
Linear deploy of WF-01 from iv-wellness-recovery-system.md.

7 emails + 10 SMS + 1 tag, ~35 step nodes over 28 days.

Branching from the doc (4A/4B opener split, 4A first-timer vs tried-before
split, 5A/5B Zeigarnik gating, WF-07 reply handler, WF-06 RECOVER keyword)
needs to be wired in the GHL UI as parallel workflows. The linear deploy
sends the first-timer 4A and the loop-close 5A as defaults.

Hard rules:
- No em dashes anywhere.
- "Support / help / wellness" only. Never treats / cures / fixes.
- Ashley is a concierge bot persona. Never claims to be a nurse.
- Real published testimonials only (Erin, Abby, Michelle). Composites unnamed.
- No Care Credit, no financing.
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

FROM_NAME = "Ashley"

# ── EMAIL COPY ───────────────────────────────────────────────────────────────

E1_SUBJECT = "{{contact.first_name}}, quick question before I send anything"
E1_BODY = """Hi {{contact.first_name}},

Thanks for reaching out about a drip. I'm Ashley, I handle bookings for IV Wellness here in Cincinnati. We do mobile drips, meaning a licensed nurse comes to your home, hotel, or office, wherever you'd actually want to be sitting for 45 minutes.

One question before I send anything else, because your answer changes what's useful to you:

**Is this your first IV ever, or have you had drips before?**

Reply with "first" or "before." One word is enough.

In the meantime, here's what your first visit looks like:

- Quick wellness check before anything goes in (free, included)
- 15% off any drip
- Free add-on of your choice: Red Light, Compression Boots, or PEMF mat

Pricing starts at $175 for our Boost drip. Everything's on our site so there are no surprises.

[See What's Available]({{custom_values.booking_link}})

Not ready to book? Reply with your biggest question and I'll answer it personally.

Ashley
IV Wellness · (513) 365-7465"""


E2_SUBJECT = "The 3 questions I get most"
E2_BODY = """Hi {{contact.first_name}},

Three questions come up almost every time someone reaches out. Honest answers below, including the bit most places skip.

**1. Are you actually in my area?**
We cover about 15 miles around Cincinnati for single drips. Inside that radius, we come to your home, office, hotel, anywhere quiet you can sit for 45 minutes. Outside the radius, reply with your zip and I'll let you know what's possible.

**2. Does insurance cover this?**
Short answer, no. IV hydration drips are out-of-pocket, same as most aesthetic and wellness services. The reason we can deliver to you, when you want, with a licensed RN, is that we're not running on insurance reimbursement timelines.

**3. Am I sure I want this?**
Totally fair. People come to us for different reasons. Travel recovery, post-night-out, immune support, wedding mornings, post-workout, or just a stretch where they ran themselves dry. You don't need to be sick to drip. Your first visit includes a quick wellness check before anything goes in, and we'll tell you straight if it's not the right fit that day.

One honest thing about us: the IV stick stings for about 10 seconds, then the drip runs 45 to 60 minutes. Bring headphones. That's the trade.

[See What's Available]({{custom_values.booking_link}})

One more thing. The most common thing first-time clients say after their drip surprised me the first time I heard it. I'll tell you about it in a few days. It comes up almost every week now.

Ashley"""


E3_SUBJECT = "4 things to do before any IV (no sales pitch)"
E3_BODY = """Hi {{contact.first_name}},

No pitch today. Here are four small things that make any IV drip work better, true for any provider.

**1. Hydrate the day before.**
Water, not coffee. Drips work either way, but the stick is easier when your veins are already showing up.

**2. Eat something 60 minutes before.**
Real meal, not just coffee or a granola bar. Empty stomach plus IV fluids leaves some people lightheaded.

**3. Wear sleeves that roll up.**
Sounds obvious. You'd be surprised.

**4. Have a quiet spot ready.**
Since we come to you, pick the chair, couch, or recliner where you actually want to be for an hour. Phone charger, glass of water, ideally a spot the dog won't try to lick the IV bag.

That's it.

P.S. Whenever you're ready: {{custom_values.booking_link}}

Ashley"""


# Linear default = E04a_firsttimer (Michelle wedding). Burned-before variant
# is in iv-wellness-recovery-system.md and needs branched deploy in GHL UI.
E4_SUBJECT = "She booked us for the morning after her wedding"
E4_BODY = """Hi {{contact.first_name}},

A client booked us for the morning after her wedding last summer. We came to the hotel suite at 9am.

Her words after we left, copy-pasted from the text:

*"This was the best decision we made for the whole weekend."*

That's Michelle. Never had a drip before. The reason she called us was she didn't want to drag herself out the door for one, and we don't make her.

Two of her friends booked us once they saw her after.

Reply "video" and I'll text you a 90-second clip of what the setup actually looks like in a client's living room. Quieter than people expect.

[Lock In Your First Visit]({{custom_values.booking_link}})

Ashley"""


# Linear default = E05a_loop_close. E05b standalone is in the doc.
E5_SUBJECT = "What our regulars say after their first drip"
E5_BODY = """Hi {{contact.first_name}},

A few days back I said I'd share the thing first-time clients say most often after their drip.

Here it is:

*"I didn't know I was running on empty until I wasn't."*

That sentence comes up on our exit feedback about once a week, almost word for word. People aren't surprised by the drip itself. They're surprised by the gap, how off-baseline they'd been without realizing.

Most of our regulars didn't think they needed support. They came in for a one-off, sat down, and afterward realized they'd been calling exhaustion "just busy" for months.

I'm not going to push you. If now isn't the right time, that's real. But if you've been telling yourself you'd come in "when things slow down," that line is the one keeping you exactly where you are.

What's the question that would actually move the needle for you? Reply, it goes straight to me.

Or whenever you're ready: {{custom_values.booking_link}}

Ashley"""


E6_SUBJECT = "Why one drip compounds, and why most people wait too long"
E6_BODY = """Hi {{contact.first_name}},

Quick honest one. No sell.

Most people treat drips like dessert. Nice when you remember, fine when you don't. Then there's a stretch of bad sleep, travel, a deadline, a bug going around the office, and three weeks later they're wondering why they feel half-checked-out at noon.

Here's the part that surprises clients:

**Hydration and nutrient gaps don't reset on their own.** Drinking water helps. Eating well helps. Both move slower than people assume. A drip moves you back to baseline in about 45 minutes, what your body would do on its own over several days, when you're already too busy for those days to actually clear.

**The cost of waiting isn't dramatic. It's just compounding.**

A first-timer who books in week one of feeling drained vs. week six gets the same drip. But in week six they've spent six weeks dragging at 60%, and probably cancelled at least one thing they cared about because the energy wasn't there.

That's the actual math. Not "you'll feel like a million bucks." Just "you'll have the energy you should already have."

The 15% off and free add-on are still on the table. Whenever you're ready: {{custom_values.booking_link}}

Ashley · (513) 365-7465"""


E7_SUBJECT = "Last one from me, plus my direct line"
E7_BODY = """Hi {{contact.first_name}},

Last email from me on this. I mean it.

People wait for a reason. The most common ones I hear:

- "I'll come in when I'm not so busy" (you won't be, book it now or it doesn't happen)
- "I want to see if I really need it first" (the only way to know is one drip)
- "I'm not sure which one is right for me" (that's literally what the on-site wellness check is for, and it's free)

If any of those is you, I get it. I'll stop emailing.

Two ways to come back when you're ready:

**1.** Book directly: {{custom_values.booking_link}}

**2.** Text **(513) 365-7465** with the keyword **RECOVER**. Goes to our desk, not a queue. You don't fill out a form again, the keyword tells our system who you are.

Whatever you decide, thanks for considering us.

Ashley
IV Wellness
9707 Montgomery Rd, Cincinnati OH 45242
(513) 365-7465"""


# ── SMS COPY ─────────────────────────────────────────────────────────────────
# All under 160 chars. No em dashes. Conversational, lowercase-friendly.

SMS_T0 = "Hi {{contact.first_name}}, this is Ashley from IV Wellness. Got your request for a drip, sending you a quick rundown in a sec."

SMS_T1 = "Hey {{contact.first_name}}, Ashley again. Quick question, first IV ever, or have you had drips before? Reply 'first' or 'before' so I send the right info."

SMS_D2_5pm = "Hey {{contact.first_name}}, I put together a quick what-to-expect rundown for first drips. Takes 2 min to read. Want me to send it?"

SMS_D3_10am = "Is this {{contact.first_name}}?"

SMS_D4_5pm = "Hey {{contact.first_name}}, did you want me to grab a slot for next week, or play it by ear? Either's fine."

SMS_D5_5pm = "Hey {{contact.first_name}}, most first-time clients are surprised by one specific thing about the drip. Mind if I share?"

SMS_D7_10am = "Hey {{contact.first_name}}, honest one, what's actually holding you back? No pressure."

SMS_D12_10am = "{{contact.first_name}}, when I don't hear back it's usually timing or a question I haven't answered. Is it one of those?"

SMS_D14_10am = "Last one from me, {{contact.first_name}}. Whenever you're ready, text RECOVER to this number and I'll get a nurse on the calendar that week. (513) 365-7465"

SMS_D28_10am = "Hi {{contact.first_name}}, Ashley. Should I close your file or keep it open for whenever you're ready?"


# ── CAMPAIGN ─────────────────────────────────────────────────────────────────
# Day map (cumulative from form submit):
#   T+0     SMS_T0          instant confirm
#   T+1m    SMS_T1          qualifying Q
#   D1 10a  E1              welcome
#   D2 10a  E2              objections + Zeigarnik teaser
#   D2 5p   SMS_D2_5pm      reciprocity hook
#   D3 10a  E3              quick-win prep tips
#   D3 10a  SMS_D3_10am     pattern interrupt
#   D4 10a  E4              social proof (Michelle wedding, first-timer default)
#   D4 5p   SMS_D4_5pm      soft slot hold
#   D5 5p   SMS_D5_5pm      curiosity gap
#   D7 10a  E5              Zeigarnik close (default linear, doc 5A)
#   D7 10a  SMS_D7_10am     direct question
#   D10 10a E6              science + cost of inaction
#   D12 10a SMS_D12_10am    objection surfacer
#   D14 9a  E7              peak-end + RECOVER keyword
#   D14 10a SMS_D14_10am    keyword reminder
#   D28 10a SMS_D28_10am    breakup text
#   tag     iv-nurture-complete

CAMPAIGN = {
    "iv_nurture": {
        "name": "IV Wellness Recovery System",
        "tag": "iv-nurture-start",
        "templates": link_steps([
            sms_step("S0 Instant Confirm (T+0)", SMS_T0),
            wait_step("1 min", 1, "minutes"),
            sms_step("S1 Qualifying Q (T+1m)", SMS_T1),
            wait_step("22 hours", 22, "hour"),
            email_step("E1 Welcome + Qualifying Q (D1)", E1_SUBJECT, E1_BODY, FROM_NAME),
            wait_step("24 hours", 24, "hour"),
            email_step("E2 3 Real Objections + Zeigarnik Teaser (D2)", E2_SUBJECT, E2_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D2 Reciprocity Hook (D2 5pm)", SMS_D2_5pm),
            wait_step("17 hours", 17, "hour"),
            email_step("E3 Quick-Win Prep Tips (D3)", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D3 Pattern Interrupt (D3 10am)", SMS_D3_10am),
            wait_step("24 hours", 24, "hour"),
            email_step("E4 Michelle Wedding (D4 first-timer default)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D4 Soft Slot Hold (D4 5pm)", SMS_D4_5pm),
            wait_step("24 hours", 24, "hour"),
            sms_step("S_D5 Curiosity Gap (D5 5pm)", SMS_D5_5pm),
            wait_step("41 hours", 41, "hour"),
            email_step("E5 Running on Empty Reveal (D7)", E5_SUBJECT, E5_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D7 Direct Question (D7)", SMS_D7_10am),
            wait_step("3 days", 3, "days"),
            email_step("E6 Science + Cost of Inaction (D10)", E6_SUBJECT, E6_BODY, FROM_NAME),
            wait_step("2 days", 2, "days"),
            sms_step("S_D12 Objection Surfacer (D12)", SMS_D12_10am),
            wait_step("47 hours", 47, "hour"),
            email_step("E7 Peak-End + RECOVER Keyword (D14)", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D14 Keyword Reminder (D14 10am)", SMS_D14_10am),
            wait_step("14 days", 14, "days"),
            sms_step("S_D28 Breakup Text (D28)", SMS_D28_10am),
            tag_step("Mark Sequence Complete", ["iv-nurture-complete"]),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"IV Wellness Recovery System: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="IV Wellness Recovery System",
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
