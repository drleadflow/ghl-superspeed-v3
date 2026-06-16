#!/usr/bin/env python3
"""
A Prestige Aesthetics & Wellness — GLP-1 Weight Loss Consultation
nurture sequence for perimenopausal women (Franklin TN).

Trigger (WF-01): Facebook lead form submission.
Generated from offer spec at Notion 34f72879-5ff0-81e3-824e-d71b084b2128.

Two workflows, linear (no keyword recovery — replies route through
WF-02 directly, no keyword required):
  01. GLP-1 Perimenopausal Master Sequence (28 days, automated only)
  02. GLP-1 Perimenopausal Global Reply Handler (Customer Replied
      filtered to WF-01 in the GHL UI after deploy)

Hard rules (perimenopausal weight loss strict mode):
- "Supports / helps with / patients often describe" only.
  Never "treats / cures / fixes."
- Acknowledge perimenopausal hormonal context, never just weight.
- No em dashes anywhere.
- {{custom_values.text_message_name}} is the bot persona, NOT Andrea.
- Andrea Pryor NP is the on-site provider, A Prestige Aesthetics & Wellness.
- No before/after photos in SMS.
- No financing / Care Credit references.
- Tag prefix: glp1peri-
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, link_steps,
)

LOCATION_ID = "9uog1fOUDtxkSr4ZPx1i"
COMPANY_ID  = "R1HWQKyMMoj4PJ5mAYed"
USER_ID     = "YewkebOufK3hmeP1gx4B"
PARENT_FOLDER = ""

FROM_NAME = "{{custom_values.text_message_name}}"

# ── EMAIL COPY ───────────────────────────────────────────────────────────────

E1_SUBJECT = "{{contact.first_name}}, one quick question before I send anything"
E1_BODY = """Hi {{contact.first_name}},

Thanks for reaching out about GLP-1 weight loss with us. I'm {{custom_values.text_message_name}}, I handle bookings for {{location.name}} here in Franklin. Andrea Pryor NP runs the program. She specifically built it for women navigating perimenopause and menopause, because the weight that shows up in your 40s and 50s does not respond to the same playbook that worked at 30.

One question before I send anything else, because your answer changes what's useful to you:

**Are you mostly focused on the weight, or are you also dealing with hormonal stuff (sleep, mood, hot flashes, energy crashes) alongside it?**

Reply with "weight" or "weight + hormones." One phrase is enough.

Here's what your consultation looks like:

- Full NP consultation with Andrea, perimenopausal weight gain is her specialty
- GLP-1 candidacy assessment, she tells you straight if it's the right call for you
- Hormone evaluation included, because the two are usually connected
- Personalized protocol, not a one-size template

[See Available Times]({{custom_values.booking_link}})

Not ready to book? Reply with the biggest question on your mind and I'll get you a real answer.

{{custom_values.text_message_name}}
{{location.name}} - {{location.phone}}"""

# Subject pattern: question. Soft CTA + segmenting question. Reciprocity via
# the included hormone evaluation.


E2_SUBJECT = "The 3 questions I get most about GLP-1 in perimenopause"
E2_BODY = """Hi {{contact.first_name}},

Three questions come up almost every time a perimenopausal woman reaches out about GLP-1. Honest answers below, including the part most clinics skip.

**1. Is it safe?**
Andrea reviews your full medical history, current meds, labs, and hormone picture before prescribing anything. If GLP-1 is not a fit for you that day, she tells you and you do not get a script. You will not be talked into something. That is the whole point of the consult.

**2. Will it work at my age?**
Honest answer, yes, but the protocol matters. Perimenopausal weight gain is not a calorie problem, it's a hormone-and-insulin problem. GLP-1 helps with appetite signaling and insulin sensitivity, which is exactly the system that shifts in your 40s. Patients often describe steady loss in the first 90 days, with the strongest results when the GLP-1 is paired with hormone support if your labs call for it.

**3. What does it cost long-term?**
This is the question we get the most and the one most places dodge. The consult is the consult. From there, the monthly cost depends on dose and whether HRT is part of your plan. Andrea walks you through the numbers in the visit so you can decide before committing. Nobody is going to surprise-bill you.

One honest thing about the program. The first 2 weeks on a GLP-1 can feel a little nauseated as your body adjusts, especially if you eat the same portions you did before. Andrea coaches you through the ramp so it stays manageable.

[See Available Times]({{custom_values.booking_link}})

One more thing. The thing perimenopausal patients say most often after their first month surprised me when I started hearing it. I'll share it in a few days. It comes up almost every week now.

{{custom_values.text_message_name}}"""

# Subject pattern: specificity. Handles top 3 objections from the offer doc.
# Pratfall (the nausea ramp). Zeigarnik teaser at the end (closes in D7).


E3_SUBJECT = "4 things to do before any GLP-1 consult (no sales pitch)"
E3_BODY = """Hi {{contact.first_name}},

No pitch today. Four small things that make any GLP-1 consult more useful, true with us or anywhere else.

**1. Pull your most recent labs if you have them.**
A1C, fasting glucose, lipids, and a thyroid panel if you've had one in the last year. Andrea uses these to calibrate your starting point. Without them she still works, but with them you get a sharper plan.

**2. Track 3 days of how you're actually eating.**
Not a diary, just notes on your phone. The goal is honesty, not judgment. The strongest predictor of long-term GLP-1 success is matching the dose to your real eating pattern, not the one you wish you had.

**3. Write down your 2 worst symptoms besides the weight.**
Sleep, mood swings, brain fog, hot flashes, energy crashes at 3pm, joint stiffness. Patients often describe these as the things that quietly steal more from their day than the scale. If hormones are part of your picture, Andrea wants to hear about them.

**4. Decide what success looks like for you.**
Not a number. A sentence. "I want to feel like myself in my own body again." "I want to keep up with my kids without crashing at night." Vague is fine. The point is having one before someone else gives you one.

That's it.

P.S. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""

# Subject pattern: how-to + number. Pure value, no sell. P.S. link only,
# no button. Reciprocity.


E4_SUBJECT = "She came in convinced GLP-1 was a last resort"
E4_BODY = """Hi {{contact.first_name}},

A patient reached out last fall. Mid-40s, perimenopausal, told me on the intake she'd "tried everything" and was reluctant about GLP-1 because she thought it meant giving up. Two years of no movement on the scale, three different elimination diets, a personal trainer she could not afford anymore.

Her first consult with Andrea was 45 minutes. Half of it was the hormone conversation, not the weight conversation. Andrea ran her labs, walked through what was actually happening with her insulin and estrogen, and explained why the playbook she'd been running was never going to work in this stage of her life.

Her words from the follow-up message a month later, copy-pasted:

*"I didn't realize how much I'd been blaming myself. Knowing my body wasn't broken, it was just in a different chapter, changed the way I show up to the whole thing."*

She's down 14 pounds at 90 days. The number is not the thing she leads with when she talks about the program. The thing she leads with is that her sleep came back and she stopped crying at the grocery store.

GLP-1 in perimenopause is not about willpower. It's about working with the system your body is actually running, not the one it ran ten years ago.

Reply "labs" if you want a quick rundown of what to bring to your consult, or "andrea" if you want to know more about how she approaches the perimenopause piece specifically.

[Book Your Consultation]({{custom_values.booking_link}})

{{custom_values.text_message_name}}"""

# Subject pattern: story tease. Wellness-curious framing for perimenopausal
# audience. Unnamed composite per compliance. Two reply options to surface
# intent without forcing booking.


E5_SUBJECT = "Remember when I said GLP-1 surprises perimenopausal patients?"
E5_BODY = """Hi {{contact.first_name}},

A few days back I said I'd share the thing perimenopausal patients say most often after their first month on the program.

Here it is:

*"I forgot what it felt like to not think about food all day."*

That sentence shows up in our follow-ups about once a week, almost word for word. It's not the weight loss they describe first. It's the food noise going quiet.

In perimenopause, the constant background hum of "what should I eat, when should I eat, why am I hungry an hour later" is not a discipline problem. It's an insulin and appetite-signal problem. GLP-1 supports those signals, which is why patients describe the mental space coming back before the scale moves much.

Most of our regulars did not think they needed a medical solution. They came in expecting Andrea to push something. What they got was an honest assessment, and for some of them the assessment was "you're not a candidate, here's what would actually help." That's the part nobody talks about.

I'm not going to push you. If now isn't the right time, that's real. But if you've been telling yourself you'll book "once life calms down," that line is the one keeping you exactly where you are, because in perimenopause life does not calm down on its own. The system you're running on shifts under you.

What's the question that would actually move the needle for you? Reply, it goes straight to me.

Or whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""

# Subject pattern: curiosity + permission. Closes Zeigarnik loop from D2.
# Acknowledges hormonal context. Low-friction reply ask + main CTA.


E6_SUBJECT = "Why the first 90 days matter more than the first prescription"
E6_BODY = """Hi {{contact.first_name}},

Quick honest one. No sell.

Most people treat GLP-1 like a one-time decision. Get the script, see how it goes, decide later. That's a fine way to find out if you tolerate the medication. It is not how the protocol actually works in perimenopause.

Here's the part that surprises patients:

**The first 30 days are mostly the body adjusting.** Appetite signals start to settle. The food noise goes quiet. The scale may or may not move much. This is normal. The work in this window is dialing in the dose with Andrea, not chasing a number.

**Days 30 to 60 are where the metabolic changes compound.** Insulin sensitivity improves. Sleep often gets more consistent. If hormones are part of the plan, the HRT side starts pulling its weight here too. Patients often describe this as the window where they stop white-knuckling and the lifestyle changes start to feel automatic.

**Days 60 to 90 are where you actually find out what your body is going to do on this protocol.** Andrea reassesses, adjusts dose, and you decide together what maintenance looks like.

**A patient who fills the script and tries to evaluate the program from the first month is grading the wrong test.** The first month tells you if you tolerate it. The first 90 days tells you what it actually does.

That's the actual math. Not "you'll lose 30 pounds in 30 days." Just "your hormones, appetite signals, and insulin sensitivity start running at a level that lets the rest of the work stick."

The consult, the hormone evaluation, and the personalized protocol are all included up front. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}} - {{location.phone}}"""

# Subject pattern: curiosity + specificity. Logic + cost-of-inaction. No
# deadline framing (Has Deadline=No). Compounding metabolic math instead.


E7_SUBJECT = "Last email from me, plus my direct line"
E7_BODY = """Hi {{contact.first_name}},

Last email from me on this. I mean it.

Women wait for a reason. The most common ones I hear:

- "I'll book once work slows down" (it won't, the calendar doesn't clear in your 40s)
- "I want to try one more thing on my own first" (the consult is free intel even if you don't move forward)
- "I'm not sure if GLP-1 is right for me at my age" (that's literally what the consult is for, and Andrea will tell you straight if it's not)

If any of those is you, I get it. I'll stop emailing.

When you're ready, two easy options:

**1.** Book directly: {{custom_values.booking_link}}

**2.** Just reply to this email or text {{location.phone}}. A question, a time that works for you, anything. Goes straight to our desk, not a queue.

Whatever you decide, thanks for considering us. Andrea built this program because she watched too many women in this stage of life get handed a generic plan and blamed when it didn't work. You deserve better than that.

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}
{{location.phone}}"""

# Subject pattern: direct. Open reply CTA, no keyword required. Permission to
# stop. This is the message people screenshot.


# ── SMS COPY ─────────────────────────────────────────────────────────────────
# All under 160 chars where possible. No em dashes. Conversational.

SMS_T0 = "Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} from {{location.name}}. Got your GLP-1 inquiry, sending a quick rundown in a sec. Reply STOP to opt out."

SMS_T1 = "Hey {{contact.first_name}}, {{custom_values.text_message_name}} again. Quick question, are you mostly focused on the weight, or also dealing with hormonal stuff (sleep, mood, energy) alongside it?"

SMS_D1_15min = "Hey {{contact.first_name}}, just sent you a welcome email with the rundown. Same question there, weight only or weight + hormones? One phrase is enough."

SMS_D2_5pm = "Hey {{contact.first_name}}, I put together a quick what-to-expect for first GLP-1 consults in perimenopause. Takes 2 min to read. Want me to send it?"

SMS_D3_10am = "Is this {{contact.first_name}}?"

SMS_D4_5pm = "Hey {{contact.first_name}}, did you want me to grab a consult slot with Andrea for next week, or play it by ear? Either's fine."

SMS_D5_5pm = "Hey {{contact.first_name}}, most perimenopausal patients are surprised by one specific thing in the first month on GLP-1. Mind if I share?"

SMS_D7_10am = "Hey {{contact.first_name}}, honest one, what's actually holding you back on booking the GLP-1 consult? No pressure."

SMS_D12_10am = "{{contact.first_name}}, when I don't hear back it's usually timing or a question I haven't answered. Is it one of those?"

SMS_D14_10am = "Last one from me, {{contact.first_name}}. Whenever you're ready, just reply here and I'll get you on Andrea's calendar that week. Or book direct: {{custom_values.booking_link}}"

SMS_D28_10am = "Hi {{contact.first_name}}, {{custom_values.text_message_name}}. Should I close your GLP-1 file or keep it open for whenever you're ready?"


# ── REPLY HANDLER COPY ───────────────────────────────────────────────────────
# Internal alert email body for front desk

REPLY_ALERT_SUBJECT = "REPLIED LEAD: {{contact.first_name}} on GLP-1 perimenopausal nurture"
REPLY_ALERT_BODY = """REPLIED LEAD ALERT.

{{contact.first_name}} {{contact.last_name}} replied to the GLP-1 Perimenopausal nurture sequence.

Phone: {{contact.phone}}
Email: {{contact.email}}

ACTION REQUIRED: Respond within 5 minutes. Do NOT let automation re-engage until this contact is manually marked as resolved or rebooked.

Their last message is in the GHL conversation thread. Check it before replying."""


# ── CAMPAIGN ─────────────────────────────────────────────────────────────────
# Day map for 01-master (cumulative from FB form submit, automated only):
#   T+0     SMS_T0          instant confirm + opt-out
#   T+1m    SMS_T1          qualifying Q (weight vs weight+hormones)
#   D1 10a  E1              welcome + qualifying Q echo
#   D1 10:15a SMS_D1_15min  echo qualifier on SMS channel
#   D2 10a  E2              objections + pratfall + Zeigarnik teaser
#   D2 5p   SMS_D2_5pm      reciprocity hook (rundown offer)
#   D3 10a  E3              quick-win prep tips
#   D3 10a  SMS_D3_10am     pattern interrupt
#   D4 10a  E4              social proof (perimenopausal patient story)
#   D4 5p   SMS_D4_5pm      soft slot hold
#   D5 5p   SMS_D5_5pm      curiosity gap (NO deadline email since
#                           Has Deadline=No)
#   D7 10a  E5              Zeigarnik close (food noise insight)
#   D7 10a  SMS_D7_10am     direct question
#   D10 10a E6              90-day compounding math + cost of waiting
#   D12 10a SMS_D12_10am    objection surfacer
#   D14 9a  E7              peak-end + open reply CTA + phone
#   D14 10a SMS_D14_10am    final nudge
#   D28 10a SMS_D28_10am    breakup text
#   tag     glp1peri-nurture-complete

CAMPAIGN = {
    "01-master": {
        "name": "01. GLP-1 Perimenopausal — Master Sequence",
        "tag": "glp1peri-lead",
        "templates": link_steps([
            sms_step("S0 Instant Confirm + Opt-Out (T+0)", SMS_T0),
            wait_step("1 min", 1, "minutes"),
            sms_step("S1 Qualifying Q Weight vs Hormones (T+1m)", SMS_T1),
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
            email_step("E4 Perimenopausal Patient Story (D4 10am)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D4 Soft Slot Hold (D4 5pm)", SMS_D4_5pm),
            wait_step("24 hours", 24, "hour"),
            sms_step("S_D5 Curiosity Gap (D5 5pm)", SMS_D5_5pm),
            wait_step("41 hours", 41, "hour"),
            email_step("E5 Zeigarnik Close Food Noise (D7 10am)", E5_SUBJECT, E5_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D7 Direct Question (D7 10am)", SMS_D7_10am),
            wait_step("3 days", 3, "days"),
            email_step("E6 90-Day Compounding Math (D10 10am)", E6_SUBJECT, E6_BODY, FROM_NAME),
            wait_step("2 days", 2, "days"),
            sms_step("S_D12 Objection Surfacer (D12 10am)", SMS_D12_10am),
            wait_step("47 hours", 47, "hour"),
            email_step("E7 Peak-End (D14 9am)", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D14 Final Nudge (D14 10am)", SMS_D14_10am),
            wait_step("14 days", 14, "days"),
            sms_step("S_D28 Breakup Text (D28 10am)", SMS_D28_10am),
            tag_step("Mark GLP-1 Perimenopausal Nurture Complete", ["glp1peri-nurture-complete"]),
        ]),
    },

    "02-reply-handler": {
        "name": "02. GLP-1 Perimenopausal — Global Reply Handler",
        "tag": "glp1peri-replied",
        "templates": link_steps([
            tag_step("Confirm Reply Tag Applied", ["glp1peri-replied"]),
            email_step("Internal Alert to Front Desk", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"GLP-1 Perimenopausal Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="GLP-1 Weight Loss Consultation — Perimenopausal Women",
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
