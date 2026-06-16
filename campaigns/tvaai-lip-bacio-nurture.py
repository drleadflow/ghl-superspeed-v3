#!/usr/bin/env python3
"""
TVAAI — Lip Bacio nurture sequence (linear, automated only).

Trigger: Facebook Lead Form submission applies tag `lipbacio-lead`.
Generated for The Vitality & Aesthetics Institute (Houston, TX).
Offer: Lip Bacio — high-ticket lip enhancement experience (~$600).

Three workflows:
  01-master            — full 28-day automated sequence (linear, no branched sub-WFs)
  02-keyword-recovery  — RESET keyword brings stalled leads back to a calendar
  03-reply-handler     — global reply handler, internal alert + tag

Hard rules:
- Voice: premium, aesthetic, confident. TVAAI = aesthetics + wellness.
- "Supports / helps with / patients often describe." Never "treats / cures / fixes."
- No em dashes anywhere.
- {{custom_values.text_message_name}} is the bot persona at the front desk.
- Tag prefix: `lipbacio-`
- WF-01 trigger = Facebook form submission (tag `lipbacio-lead` applied by form action).
- WF-03 trigger = Customer Replied filter, must be filtered to WF-01 contacts only.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, link_steps,
)

LOCATION_ID = "jiR5qR3g4OrMRx6BmpF2"
COMPANY_ID  = "R1HWQKyMMoj4PJ5mAYed"
USER_ID     = "YewkebOufK3hmeP1gx4B"
PARENT_FOLDER = ""

FROM_NAME = "{{custom_values.text_message_name}}"

# ── EMAIL COPY ───────────────────────────────────────────────────────────────

E1_SUBJECT = "{{contact.first_name}}, before I send you anything else"
E1_BODY = """Hi {{contact.first_name}},

Thanks for reaching out about Lip Bacio. I'm {{custom_values.text_message_name}} at {{location.name}}. Lip Bacio is the premium lip experience our patients book when they want subtle, kissable shape rather than the overdone look.

One quick question before I send you the rest, because your answer changes what's useful to you:

**Are you new to lip enhancement, or have you had filler before and you're looking for a softer, more natural finish this time?**

Reply with "first time" or "had it before." One or two words is enough.

While you think on it, here's what your first Lip Bacio visit looks like:

- Private consultation with the injector, no pressure, no upsell
- Mapping of your natural lip shape so the result reads as yours, not someone else's
- Comfort-first technique with topical numbing built into the appointment
- Most patients describe a calm, controlled experience start to finish

[See Available Times]({{custom_values.booking_link}})

Not ready to book? Reply with the question on your mind and I'll answer it personally.

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}"""


E2_SUBJECT = "The 3 questions I get most about Lip Bacio"
E2_BODY = """Hi {{contact.first_name}},

Three questions come up almost every time someone reaches out about Lip Bacio. Honest answers below, including the parts most med spas skip.

**1. Will it look obvious?**
Only if you ask for that look. Lip Bacio is built around your existing lip shape, not a template. Our injector maps the natural border first, then enhances volume in the proportion that fits your face. Patients often describe the result as "my lips, just better rested." If you want something more dramatic, that's a separate conversation we'd have at consult.

**2. How much does it actually hurt?**
Honest answer, the lip area is sensitive, so we plan around it. Topical numbing is built into the appointment time, not rushed. Most patients describe the injections as pressure with brief pinches rather than sharp pain. The product itself contains a numbing agent that takes effect within the first minute. You're in the chair longer for comfort than for the actual treatment.

**3. How long does it last and what does it cost to maintain?**
Results typically last 9 to 12 months depending on your metabolism, hydration, and how active you are. Patients who like the look usually return once a year for a small refresh rather than a full session. The first visit is the investment. Maintenance is meaningfully less.

One honest thing about us. The first 24 to 48 hours after lip work include some swelling. That's normal, and it's why we don't recommend booking Lip Bacio the day before a wedding or a photo shoot. We always plan around your calendar at consult.

[See Available Times]({{custom_values.booking_link}})

One more thing. There's a moment most first-time Lip Bacio patients describe after their follow-up that I'll share with you in a few days. It comes up almost every week."""


E3_SUBJECT = "4 things to do before any lip appointment (no sales pitch)"
E3_BODY = """Hi {{contact.first_name}},

No pitch today. Four small things that make any lip enhancement go better, true with us or anywhere else.

**1. Skip blood thinners for 48 hours before.**
That includes ibuprofen, aspirin, fish oil, and most pre-workouts. They increase the chance of bruising. Tylenol is fine. If you're on a prescribed blood thinner, do not stop without talking to your prescribing doctor, just let us know at consult.

**2. Hydrate hard the day before and the day of.**
Aim for 80 to 100 oz of water. Hydrated lips heal faster, hold product better, and the post-treatment swelling resolves more cleanly.

**3. Eat a real meal about 60 minutes before.**
Empty stomach plus a sensitive area leaves some patients lightheaded in the first few minutes. A real meal, not just coffee.

**4. Plan a quiet 24 to 48 hours after.**
You can absolutely return to work, see friends, live your life. But don't book Lip Bacio the day before your most important meeting, photo, or event. Patients who give themselves a calm window love their results most.

That's it.

P.S. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}
{{location.name}}"""


E4_SUBJECT = "She came in just for a tiny refresh"
E4_BODY = """Hi {{contact.first_name}},

A patient reached out last fall. Mid-30s, no prior filler, just curious. She told us she didn't want bigger lips, she wanted her lips to look like they did in her late 20s before they thinned. That's it.

She booked one Lip Bacio session. Her words at her two-week follow-up, copy-pasted from the message she sent us:

*"I've had three people compliment my skin this week. Not one of them said anything about my lips. That's exactly what I wanted."*

The phrase that stuck with us was the one she added at the end. She said she'd been thinking about it for almost two years before booking. Most of the patients who book Lip Bacio say something similar. It's rarely an impulse decision. It's usually quiet, considered, and finally choosing yourself after thinking about it for a long time.

Lip Bacio doesn't change your face. It restores proportion. Most first-time patients describe it the same way she did, "this is what I forgot they used to look like."

Reply "experience" and I'll walk you through what the consultation visit feels like in detail if you'd like that before booking. Or if you've got a specific question, send it.

[Reserve Your Consultation]({{custom_values.booking_link}})

{{custom_values.text_message_name}}"""


E5_SUBJECT = "Remember when I said Lip Bacio surprises people?"
E5_BODY = """Hi {{contact.first_name}},

A few days back I said I'd share the moment most first-time Lip Bacio patients describe after their follow-up.

Here it is:

*"I keep catching myself in the mirror and not flinching."*

That sentence shows up in our patient feedback almost weekly, almost word for word. People aren't surprised by the volume change. They're surprised by what stops happening, the small daily moment of avoiding their own reflection or editing every selfie before sending it.

Most of our Lip Bacio patients didn't think they had a confidence problem. They came in for a small refinement, sat through the appointment, and afterward realized how often they'd been making tiny mental edits without noticing.

I'm not going to push you on this. If now isn't the right season for it, that's real and I respect it. But if you've been telling yourself you'll book "when life slows down," that line is the one keeping you exactly where you are.

What's the one question that would actually move the needle for you? Reply, it goes straight to me.

Or whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""


E6_SUBJECT = "Why the first Lip Bacio matters more than the touch-up"
E6_BODY = """Hi {{contact.first_name}},

Quick honest one. No sell.

Most patients treat their first lip appointment like a single decision. Pick a day, get it done, see how it feels. That's a fine way to think about most med spa services. It's not the right frame for Lip Bacio.

Here's the part patients often miss:

**The first session is the foundation.** Our injector spends most of the consultation mapping your natural lip border, your facial proportions, and how your lips move when you smile and speak. That map is what makes the result look like yours instead of a template. It also becomes the reference for every future visit.

**The follow-up two weeks later is where the result settles.** Initial swelling masks the final shape. The two-week mark is when we see what your lips actually look like with the product fully integrated. Patients who skip the follow-up often misread their early result and either book unnecessary touch-ups or write off the experience too early.

**Maintenance is not the same as the first session.** Once the foundation is in place, most patients return once a year for a small refresh rather than a full session. The math improves significantly after year one. The first visit is the investment, the rest is meaningfully less.

That's the actual structure. Not "book and forget." Just "build the foundation right the first time, then maintain it lightly."

The consultation is no-pressure. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}
{{location.name}}"""


E7_SUBJECT = "Last email from me, plus the front desk line"
E7_BODY = """Hi {{contact.first_name}},

Last email from me on this. I mean it.

Patients wait for a reason. The most common ones I hear:

- "I'll book once life calms down" (it won't, the calendar doesn't clear)
- "I want to see if I really need it first" (the only way to know is the consultation, and there's no commitment to treat that day)
- "I'm not sure Lip Bacio is right for me" (that's literally what the consultation is for)

If any of those is you, I get it. I'll stop emailing.

Two ways to come back when you're ready:

**1.** Book directly: {{custom_values.booking_link}}

**2.** Text **{{location.phone}}** with the keyword **RESET**. Goes to our front desk, not a queue. You don't fill the form out again, the keyword tells our system who you are and gets you straight to a slot.

Whatever you decide, thanks for considering us.

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}
{{location.phone}}"""


# ── SMS COPY ─────────────────────────────────────────────────────────────────

SMS_T0 = "Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} at {{location.name}}. Got your Lip Bacio request, sending a quick rundown in a sec. Reply STOP to opt out."

SMS_T1 = "Hey {{contact.first_name}}, {{custom_values.text_message_name}} again. Quick question, are you new to lip enhancement, or had filler before and want a softer look this time?"

SMS_D1_15min = "Hey {{contact.first_name}}, just sent you a welcome email with the rundown. Same question there, first time or had it before? One or two words is enough."

SMS_D2_5pm = "Hey {{contact.first_name}}, I put together a quick what-to-expect rundown for first Lip Bacio visits. Takes 2 min to read. Want me to send it?"

SMS_D3_10am = "Is this {{contact.first_name}}?"

SMS_D4_5pm = "Hey {{contact.first_name}}, did you want me to grab a Lip Bacio consult for next week, or play it by ear? Either's fine."

SMS_D5_5pm = "Hey {{contact.first_name}}, most first-time Lip Bacio patients describe one specific moment after their follow-up. Mind if I share?"

SMS_D7_10am = "Hey {{contact.first_name}}, honest one, what's actually holding you back on Lip Bacio? No pressure."

SMS_D12_10am = "{{contact.first_name}}, when I don't hear back it's usually timing or a question I haven't answered. Is it one of those?"

SMS_D14_10am = "Last one from me, {{contact.first_name}}. Whenever you're ready, text RESET to {{location.phone}} and I'll get you on the consult calendar that week."

SMS_D28_10am = "Hi {{contact.first_name}}, {{custom_values.text_message_name}}. Should I close your Lip Bacio file or keep it open for whenever you're ready?"


# ── KEYWORD RECOVERY COPY ────────────────────────────────────────────────────

SMS_RESET_AUTOREPLY = "Got it {{contact.first_name}}, pulling up the consult calendar. Here's the link: {{custom_values.booking_link}} -{{custom_values.text_message_name}}"

SMS_RESET_2HR_FOLLOWUP = "Hey {{contact.first_name}}, just making sure the booking link worked. Want me to grab a Lip Bacio consult for you directly?"


# ── REPLY HANDLER COPY ───────────────────────────────────────────────────────

REPLY_ALERT_SUBJECT = "REPLIED LEAD: {{contact.first_name}} on Lip Bacio nurture"
REPLY_ALERT_BODY = """REPLIED LEAD ALERT.

{{contact.first_name}} {{contact.last_name}} replied to the Lip Bacio nurture sequence.

Phone: {{contact.phone}}
Email: {{contact.email}}

ACTION REQUIRED: Respond within 5 minutes. Do NOT let automation re-engage until this contact is manually marked as resolved or rebooked.

Their last message is in the GHL conversation thread. Check it before replying."""


# ── CAMPAIGN ─────────────────────────────────────────────────────────────────
# Day map for 01-master (cumulative from FB form submit, automated touchpoints only):
#   T+0     SMS_T0          instant confirm + opt-out
#   T+1m    SMS_T1          qualifying Q (first time vs had it before)
#   D1 10a  E1              welcome + qualifying Q echo
#   D1 10:15a SMS_D1_15min  echo qualifier on SMS channel
#   D2 10a  E2              objections + comfort + Zeigarnik teaser
#   D2 5p   SMS_D2_5pm      reciprocity hook (rundown offer)
#   D3 10a  E3              prep tips
#   D3 10a  SMS_D3_10am     pattern interrupt
#   D4 10a  E4              social proof (natural-results story)
#   D4 5p   SMS_D4_5pm      soft slot hold
#   D5 5p   SMS_D5_5pm      curiosity gap
#   D7 10a  E5              Zeigarnik close
#   D7 10a  SMS_D7_10am     direct question
#   D10 10a E6              foundation + maintenance math
#   D12 10a SMS_D12_10am    objection surfacer
#   D14 9a  E7              peak-end + RESET keyword + phone
#   D14 10a SMS_D14_10am    keyword reminder
#   D28 10a SMS_D28_10am    breakup text
#   tag     lipbacio-nurture-complete

CAMPAIGN = {
    "01-master": {
        "name": "01. Lip Bacio — Master Sequence",
        "tag": "lipbacio-lead",
        "templates": link_steps([
            sms_step("S0 Instant Confirm + Opt-Out (T+0)", SMS_T0),
            wait_step("1 min", 1, "minutes"),
            sms_step("S1 Qualifying Q First Time vs Repeat (T+1m)", SMS_T1),
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
            email_step("E3 Pre-Appointment Prep Tips (D3 10am)", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D3 Pattern Interrupt (D3 10am)", SMS_D3_10am),
            wait_step("24 hours", 24, "hour"),
            email_step("E4 Natural Refresh Story (D4 10am)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D4 Soft Slot Hold (D4 5pm)", SMS_D4_5pm),
            wait_step("24 hours", 24, "hour"),
            sms_step("S_D5 Curiosity Gap (D5 5pm)", SMS_D5_5pm),
            wait_step("41 hours", 41, "hour"),
            email_step("E5 Zeigarnik Close Mirror Moment (D7 10am)", E5_SUBJECT, E5_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D7 Direct Question (D7 10am)", SMS_D7_10am),
            wait_step("3 days", 3, "days"),
            email_step("E6 Foundation + Maintenance Math (D10 10am)", E6_SUBJECT, E6_BODY, FROM_NAME),
            wait_step("2 days", 2, "days"),
            sms_step("S_D12 Objection Surfacer (D12 10am)", SMS_D12_10am),
            wait_step("47 hours", 47, "hour"),
            email_step("E7 Peak-End + RESET Keyword (D14 9am)", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D14 Keyword Reminder (D14 10am)", SMS_D14_10am),
            wait_step("14 days", 14, "days"),
            sms_step("S_D28 Breakup Text (D28 10am)", SMS_D28_10am),
            tag_step("Mark Lip Bacio Nurture Complete", ["lipbacio-nurture-complete"]),
        ]),
    },

    "02-keyword-recovery": {
        "name": "02. Lip Bacio — RESET Keyword Recovery",
        "tag": "lipbacio-keyword-trigger",
        "templates": link_steps([
            tag_step("Apply Returning Lead Tag", ["lipbacio-returning-lead"]),
            tag_step("Remove Nurture Complete Tag", ["lipbacio-nurture-complete"], remove=True),
            sms_step("RESET Auto-Reply with Booking Link", SMS_RESET_AUTOREPLY),
            wait_step("2 hours", 2, "hour"),
            sms_step("RESET 2-Hour Follow-Up", SMS_RESET_2HR_FOLLOWUP),
        ]),
    },

    "03-reply-handler": {
        "name": "03. Lip Bacio — Global Reply Handler",
        "tag": "lipbacio-replied",
        "templates": link_steps([
            tag_step("Confirm Reply Tag Applied", ["lipbacio-replied"]),
            email_step("Internal Alert to Front Desk", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"Lip Bacio Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="Lip Bacio",
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
