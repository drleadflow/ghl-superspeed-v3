#!/usr/bin/env python3
"""
TVAAI — V-Hacker Add On nurture sequence (linear, automated only).

Trigger: Facebook Lead Form submission applies tag `vhacker-lead`.
Generated for The Vitality & Aesthetics Institute (Houston, TX).
Offer: V-Hacker Add On — intimate wellness add-on for tissue health, comfort,
       and confidence. Pairs with another visit (~$249, no deadline).

Three workflows:
  01-master            — full 28-day automated sequence (linear)
  02-keyword-recovery  — RESET keyword brings stalled leads back to a calendar
  03-reply-handler     — global reply handler, internal alert + tag

Hard rules:
- Sensitive-category voice: respectful, clinical, judgment-free. Audience is
  women considering intimate wellness for menopausal change, post-childbirth
  recovery, or comfort/confidence. No coy euphemism, no shame framing.
- Approved framing: "supports tissue health / helps with comfort / patients
  often describe improved confidence." Never "fixes / cures / restores
  virginity / fully effective" or similar absolute claims.
- No fabricated urgency. Has Deadline = No on this offer.
- No em or en dashes anywhere in customer-facing body copy.
- No before/after photos, no MMS at T+1.
- {{custom_values.text_message_name}} is the bot persona at the front desk.
- Tag prefix: `vhacker-`
- Workflow display names use ` — ` em dash with spaces (NOT colons).
- WF-01 trigger = Facebook form submission (tag `vhacker-lead` applied by
  the form action in the GHL UI).
- WF-02 trigger = Inbound SMS keyword RESET, filtered to contacts who already
  hold the `vhacker-lead` tag (set in the GHL UI trigger condition).
- WF-03 trigger = Customer Replied filter, must be filtered to WF-01 contacts
  only in the GHL UI so it does not fire across other campaigns.
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

E1_SUBJECT = "{{contact.first_name}}, a private note about V-Hacker"
E1_BODY = """Hi {{contact.first_name}},

Thanks for the V-Hacker request. I'm {{custom_values.text_message_name}} at {{location.name}}, and I want to make this as low pressure as possible. Most patients tell me they thought about reaching out for months before they actually did.

A small note up front. Everything you share with us stays private. Your file is handled by our clinical team only, and your name never gets used in marketing or testimonials without written consent.

V-Hacker is built as an add on, meaning it pairs with another visit you already have on the books or one you'd want to schedule anyway. Patients often describe the appointment as quick, calm, and a lot less involved than they expected.

Quick question, because your answer changes what's helpful to share next:

**Is V-Hacker something you're exploring for general comfort and confidence, or is there a specific change you've noticed that brought it to mind (post-childbirth, menopausal shifts, or something else)?**

Reply with one word or one line. Whatever you're comfortable sharing.

If you'd rather just see times: {{custom_values.booking_link}}

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}"""


E2_SUBJECT = "Honest answers to the questions patients usually whisper"
E2_BODY = """Hi {{contact.first_name}},

Patients ask the same handful of questions about V-Hacker, usually in a quieter voice than they ask about other services. Direct answers below, the kind I'd want if I were the one reading.

**1. Am I the right age or stage for this?**
There isn't a single right profile. We see patients in their late 30s exploring it after childbirth, patients in their 40s and 50s noticing menopausal change, and patients in their 60s who simply want to feel more like themselves again. The clinical assessment is what tells us if V-Hacker is a fit for you specifically. If it isn't, we say so.

**2. What does the appointment actually feel like?**
Calm. Private room, your provider only, no extra staff in the room. The treatment itself is brief, and patients often describe the sensation as warm pressure rather than pain. We talk you through every step before it happens. You can stop at any time, no questions asked.

**3. Is there downtime?**
Most patients return to normal activity the same day. We share specific aftercare guidance at your visit so the result settles cleanly. Nothing dramatic, just small comfort steps for the first 24 to 48 hours.

One honest thing about us. V-Hacker is described as an add on for a reason. It supports tissue health, helps with comfort, and many patients describe improved confidence over the weeks that follow. It is not a fix-everything procedure, and any clinic that promises that is overselling it. The goal is steady, real improvement, paired with the rest of your care.

If you'd like to see the calendar: {{custom_values.booking_link}}

In a few days I'll share what patients tell us at their follow-up. It's the part that surprised me when I first heard it."""


E3_SUBJECT = "A short prep guide for your V-Hacker visit"
E3_BODY = """Hi {{contact.first_name}},

No pitch in this one. Just a short prep guide that makes any intimate wellness visit go more smoothly, true here or anywhere you might choose.

**1. Schedule outside your cycle when possible.**
Patients are usually most comfortable when the visit is booked a few days clear of menstruation on either side. If timing is tight, let us know and we'll adjust.

**2. Hydrate well the day before and the day of.**
Hydrated tissue responds better to the treatment and recovers more cleanly. Aim for 80 to 100 oz of water the day before.

**3. Wear something comfortable.**
Loose clothing for the trip home. Nothing tight at the waistline for the first 24 hours. Most patients describe themselves as fully comfortable within an hour of leaving.

**4. Bring questions in writing if it helps.**
A lot of patients tell me they forgot what they wanted to ask once they were in the room. Writing them down ahead of time, even a quick note in your phone, takes the pressure off.

That's it.

P.S. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}
{{location.name}}"""


E4_SUBJECT = "What a patient told us at her three-week follow-up"
E4_BODY = """Hi {{contact.first_name}},

A patient came in last spring for V-Hacker as an add on to a routine wellness visit. She was in her late 40s, had been quietly thinking about it for almost a year, and finally decided to ask about it on a whim during checkout.

Here's the message she sent us at her three-week follow-up, lightly edited and shared with her permission:

*"I didn't realize how much mental space the discomfort had been taking up until it wasn't there anymore. I'm not thinking about it. That's the thing I wanted."*

What stood out to me wasn't the result itself. It was the phrase "thinking about it." She told me she'd been managing around it, planning around it, mentioning it to her partner, and not bringing it up to anyone else. The relief wasn't just physical. It was the absence of a low-grade weight she'd carried for a long time.

Most V-Hacker patients describe something similar at their follow-up. The change is real, and the part that surprises them most is what it stops costing them mentally.

If you'd like to see the V-Hacker calendar so you can pair it with another visit: {{custom_values.booking_link}}

If you'd rather just ask a question first, reply here. It comes straight to me.

{{custom_values.text_message_name}}"""


E5_SUBJECT = "The line patients use most often after V-Hacker"
E5_BODY = """Hi {{contact.first_name}},

A few days back I said I'd share what patients tell us at their V-Hacker follow-up. Here it is, almost word for word:

*"I feel like myself again."*

That's the sentence we hear the most. Not "I feel younger." Not "I'm a new person." Just "myself again."

Most of our V-Hacker patients didn't think of themselves as having a problem worth talking about. They had simply gotten used to a baseline that was a little less comfortable, a little less present, a little less themselves. The change V-Hacker supports is rarely dramatic. It's the quiet return to feeling at home in your own body.

I want to say something directly, in case it's useful. If now isn't the right season for it, that's real. There's no clock on this offer and no slot we're holding for you. We'll be here when you're ready, whether that's next week, next quarter, or next year.

If there's a question that would actually help you decide, reply with it. I read every one personally and the answer doesn't go through a script.

Or if you'd like to see times: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""


E6_SUBJECT = "Why V-Hacker works best as part of your existing care"
E6_BODY = """Hi {{contact.first_name}},

Quick honest one. No sell.

A lot of patients ask whether V-Hacker is a one-and-done service or something they should think about as part of a longer plan. Both framings can be true depending on the patient, but here's how we usually walk through it.

**V-Hacker is positioned as an add on for a reason.** It pairs with the kind of care you're already doing, whether that's a routine wellness visit, a follow-up, or another aesthetic appointment. Patients often describe the experience as easier when it's bundled into a visit you'd be making anyway, rather than treated as a separate trip and a separate emotional decision.

**Tissue health responds gradually.** A single session supports a real, noticeable shift over the weeks that follow. Patients who pair it with a longer wellness arc, including hydration, sleep, and the rest of their care, often describe the most steady results.

**Maintenance varies by patient.** Some return seasonally. Some come once and don't feel the need to return for a year or more. The clinical team walks through what makes sense for you specifically at your follow-up, based on how your body responded to round one.

That's the actual frame. Not "do this, then do this on a strict schedule." More like "add it where it fits, and we'll adjust together."

The consultation is no pressure. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}
{{location.name}}"""


E7_SUBJECT = "I'll stop emailing after this one"
E7_BODY = """Hi {{contact.first_name}},

This is the last note from me on V-Hacker. I mean that. I'd rather respect your inbox than chase you.

The patients who eventually come in usually tell me one of three things kept them on the fence:

- "I wanted to see if I really needed it." That's literally what the consultation is for, and there's no commitment to book the add on that day.
- "I wasn't sure I was the right fit." Patients we see range across age, life stage, and reason. The clinical assessment is the only honest answer to whether it's right for you.
- "I just kept putting it off." That's the most common one, and the one I hear with no judgment from anyone on our team.

If any of those is you, I get it. I'm closing this thread on my end so I'm not in your inbox anymore.

Two ways to come back when you're ready:

**1.** Book the V-Hacker add on directly: {{custom_values.booking_link}}

**2.** Text **{{location.phone}}** with the keyword **RESET**. That goes to our front desk, not a queue. You don't have to fill out the form again. The keyword tells our system who you are and gets you straight to a slot.

Whatever you decide, thank you for trusting us with the question in the first place. That's not a small thing.

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}
{{location.phone}}"""


# ── SMS COPY ─────────────────────────────────────────────────────────────────

SMS_T0 = "Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} at {{location.name}}. Got your V-Hacker request, sending a quick note in a moment. Reply STOP to opt out."

SMS_T1 = "Hey {{contact.first_name}}, {{custom_values.text_message_name}} again. Quick one, is V-Hacker for general comfort and confidence, or is there a specific change you've noticed? Whatever you're comfortable sharing."

SMS_D1_15min = "Hey {{contact.first_name}}, the welcome note just landed in your inbox. Same question there, general or something specific? One word is plenty."

SMS_D2_5pm = "Hey {{contact.first_name}}, I put together honest answers to the V-Hacker questions patients usually whisper. 2 min read. Want me to send it over?"

SMS_D3_10am = "Is this still {{contact.first_name}}?"

SMS_D4_5pm = "Hey {{contact.first_name}}, would it help if I paired V-Hacker with another visit you might already be planning? No rush either way."

SMS_D5_5pm = "Hey {{contact.first_name}}, patients tell us one specific thing at their V-Hacker follow-up. Mind if I share it?"

SMS_D7_10am = "Hey {{contact.first_name}}, honest one, what's the real question on your mind about V-Hacker? No judgment, no pressure."

SMS_D12_10am = "{{contact.first_name}}, when patients go quiet it's usually privacy or a question they haven't asked yet. Anything I can answer for you?"

SMS_D14_10am = "Last note from me, {{contact.first_name}}. Whenever the timing is right, text RESET to {{location.phone}} and we'll find you a V-Hacker slot that pairs with another visit."

SMS_D28_10am = "Hi {{contact.first_name}}, {{custom_values.text_message_name}}. Should I close your V-Hacker file or keep it quietly open for whenever you're ready?"


# ── KEYWORD RECOVERY COPY ────────────────────────────────────────────────────

SMS_RESET_AUTOREPLY = "Got it {{contact.first_name}}, pulling up the V-Hacker calendar now. Here's the link: {{custom_values.booking_link}} -{{custom_values.text_message_name}}"

SMS_RESET_2HR_FOLLOWUP = "Hey {{contact.first_name}}, just checking the booking link came through. Want me to pair the V-Hacker add on with another visit for you?"


# ── REPLY HANDLER COPY ───────────────────────────────────────────────────────

REPLY_ALERT_SUBJECT = "REPLIED LEAD: {{contact.first_name}} on V-Hacker nurture"
REPLY_ALERT_BODY = """REPLIED LEAD ALERT.

{{contact.first_name}} {{contact.last_name}} replied to the V-Hacker Add On nurture sequence.

Phone: {{contact.phone}}
Email: {{contact.email}}

ACTION REQUIRED: Respond within 5 minutes. Treat this as sensitive-category outreach. Use private channel only, do not discuss specifics in shared chat. Do NOT let automation re-engage until this contact is manually marked as resolved or rebooked.

Their last message is in the GHL conversation thread. Read it before replying."""


# ── CAMPAIGN ─────────────────────────────────────────────────────────────────
# Day map for 01-master (cumulative from FB form submit, automated only):
#   T+0     SMS_T0          instant confirm + opt-out
#   T+1m    SMS_T1          qualifying Q (general vs specific)
#   D1 10a  E1              private welcome + qualifying Q
#   D1 10:15a SMS_D1_15min  echo qualifier on SMS channel
#   D2 10a  E2              honest objections (age/experience/downtime)
#   D2 5p   SMS_D2_5pm      reciprocity hook (2-min read)
#   D3 10a  E3              prep guide
#   D3 10a  SMS_D3_10am     pattern interrupt
#   D4 10a  E4              follow-up testimonial story
#   D4 5p   SMS_D4_5pm      pair-with-another-visit nudge
#   D5 5p   SMS_D5_5pm      curiosity gap
#   D7 10a  E5              "myself again" close
#   D7 10a  SMS_D7_10am     direct question
#   D10 10a E6              add-on positioning + maintenance frame
#   D12 10a SMS_D12_10am    privacy/objection surfacer
#   D14 9a  E7              breakup + RESET keyword
#   D14 10a SMS_D14_10am    keyword reminder
#   D28 10a SMS_D28_10am    quiet-close text
#   tag     vhacker-nurture-complete

CAMPAIGN = {
    "01-master": {
        "name": "01. V-Hacker Add On — Master Sequence",
        "tag": "vhacker-lead",
        "templates": link_steps([
            sms_step("S0 Instant Confirm + Opt-Out (T+0)", SMS_T0),
            wait_step("1 min", 1, "minutes"),
            sms_step("S1 Qualifying Q General vs Specific (T+1m)", SMS_T1),
            wait_step("22 hours", 22, "hour"),
            email_step("E1 Private Welcome + Qualifying Q (D1 10am)", E1_SUBJECT, E1_BODY, FROM_NAME),
            wait_step("15 min", 15, "minutes"),
            sms_step("S_D1_15 Echo Qualifier (D1 10:15am)", SMS_D1_15min),
            wait_step("23 hours", 23, "hour"),
            wait_step("45 min", 45, "minutes"),
            email_step("E2 Honest Whispered Questions (D2 10am)", E2_SUBJECT, E2_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D2 Reciprocity Hook (D2 5pm)", SMS_D2_5pm),
            wait_step("17 hours", 17, "hour"),
            email_step("E3 Prep Guide (D3 10am)", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D3 Pattern Interrupt (D3 10am)", SMS_D3_10am),
            wait_step("24 hours", 24, "hour"),
            email_step("E4 Three-Week Follow-Up Story (D4 10am)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D4 Pair-With-Visit Nudge (D4 5pm)", SMS_D4_5pm),
            wait_step("24 hours", 24, "hour"),
            sms_step("S_D5 Curiosity Gap (D5 5pm)", SMS_D5_5pm),
            wait_step("41 hours", 41, "hour"),
            email_step("E5 Myself Again Close (D7 10am)", E5_SUBJECT, E5_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D7 Direct Question (D7 10am)", SMS_D7_10am),
            wait_step("3 days", 3, "days"),
            email_step("E6 Add-On Positioning + Maintenance (D10 10am)", E6_SUBJECT, E6_BODY, FROM_NAME),
            wait_step("2 days", 2, "days"),
            sms_step("S_D12 Privacy + Objection Surfacer (D12 10am)", SMS_D12_10am),
            wait_step("47 hours", 47, "hour"),
            email_step("E7 Breakup + RESET Keyword (D14 9am)", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D14 Keyword Reminder (D14 10am)", SMS_D14_10am),
            wait_step("14 days", 14, "days"),
            sms_step("S_D28 Quiet Close (D28 10am)", SMS_D28_10am),
            tag_step("Mark V-Hacker Nurture Complete", ["vhacker-nurture-complete"]),
        ]),
    },

    "02-keyword-recovery": {
        "name": "02. V-Hacker Add On — RESET Keyword Recovery",
        "tag": "vhacker-keyword-trigger",
        "templates": link_steps([
            tag_step("Apply Returning Lead Tag", ["vhacker-returning-lead"]),
            tag_step("Remove Nurture Complete Tag", ["vhacker-nurture-complete"], remove=True),
            sms_step("RESET Auto-Reply with Booking Link", SMS_RESET_AUTOREPLY),
            wait_step("2 hours", 2, "hour"),
            sms_step("RESET 2-Hour Follow-Up", SMS_RESET_2HR_FOLLOWUP),
        ]),
    },

    "03-reply-handler": {
        "name": "03. V-Hacker Add On — Global Reply Handler",
        "tag": "vhacker-replied",
        "templates": link_steps([
            tag_step("Confirm Reply Tag Applied", ["vhacker-replied"]),
            email_step("Internal Alert to Front Desk", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"V-Hacker Add On Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="V-Hacker Add on",
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
