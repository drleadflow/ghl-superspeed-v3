#!/usr/bin/env python3
"""
IV Wellness — Generic Intake Nurture (28-day, two intake paths fan-in to one body).

Architecture:
  01a-intro-scratchoff   Day-0 intro for scratch-off opt-ins (name/email/phone only)
  01b-intro-form         Day-0 intro for main on-site form opt-ins (full payload)
  02-generic-28day       Shared 28-day nurture body, service-agnostic

Site: https://drip.iv-wellness.com/iv-wellness

Triggers are NOT wired by this script. Wire them in the GHL UI:
  - 01a: Facebook lead form (scratch-off page) OR contact tag `iv-scratchoff-lead`
  - 01b: Facebook lead form (main on-site form) OR contact tag `iv-form-lead`
  - 02:  Contact gets tag `iv-wellness-nurture-start` (set at end of both intros)

Hard rules (IV strict mode):
- "Supports / helps with / patients often describe" only. Never treats/cures/fixes.
- No before/after photos, no MMS.
- No em dashes anywhere.
- {{custom_values.text_message_name}} is the bot persona, NOT the on-site RN.
- Real testimonials only (Erin, Abby, Michelle) or unnamed composites.
- No Care Credit / financing.

Note on `{{contact.latest_optin}}`:
- 01a sets it to "your first IV drip" (scratch-off form has no service field).
- 01b assumes the on-site form's `Service Interested In` field is wired to the
  `latest_optin` custom field in GHL. If it lands on a different field, add a
  second update_contact_field_step in 01b copying the value across.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, update_contact_field_step, link_steps,
)

LOCATION_ID = "2DvWWl1Ao2MAC9BZVshG"
COMPANY_ID  = "R1HWQKyMMoj4PJ5mAYed"
USER_ID     = "YewkebOufK3hmeP1gx4B"
PARENT_FOLDER = ""

FROM_NAME = "{{custom_values.text_message_name}}"

# Tag used by Generic 28-Day to ingest from either intro
HANDOFF_TAG = "iv-wellness-nurture-start"
COMPLETE_TAG = "iv-wellness-nurture-complete"


# ── INTRO A — SCRATCH-OFF COPY ────────────────────────────────────────────────

SMS_A_T0 = "Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} from IV Wellness. You unlocked 25% off your first IV drip. I just locked the discount to your record so it's good whenever you book."

SMS_A_T1 = "Quick one, are you looking to come in this week, or just exploring? Either's fine, just helps me know what to send."

EMAIL_A_SUBJECT = "Your 25% off is locked in {{contact.first_name}}"
EMAIL_A_BODY = """Hi {{contact.first_name}},
Quick recap of what you unlocked:
- 25% off your first IV drip with us, automatic at booking, no code to remember
- Free pre-session wellness assessment with the RN before anything goes in
- Choice of any drip on our menu (Skinny, Myers, NAD+, Glutathione, Brain Booster, Afterparty Recovery, more)
- Mobile setup, the RN comes to your home, hotel, or office within 20 miles of Cincinnati
[See Available Times]({{custom_values.booking_link}})
If you're not sure which drip is the right pick, hit reply and tell me what you're hoping to feel better from (energy, recovery, skin, focus, post-event). I'll point you at the one that fits.
{{custom_values.text_message_name}}
IV Wellness · {{location.phone}}"""


# ── INTRO B — MAIN FORM COPY ──────────────────────────────────────────────────

SMS_B_T0 = "Hi {{contact.first_name}}, {{custom_values.text_message_name}} from IV Wellness. Got your request for {{contact.latest_optin}}. Pulling the calendar now, will text you to lock the slot."

SMS_B_T1 = "Heads up, the time you picked is a request, not a confirmation yet. RN checks the schedule and I'll text within the hour during business hours to lock it or suggest the closest open window."

EMAIL_B_SUBJECT = "What to expect for your {{contact.latest_optin}}"
EMAIL_B_BODY = """Hi {{contact.first_name}},
Your request is in. Here's what happens next and how to prep so the session runs smoothly.
**Your request:**
- Service: {{contact.latest_optin}}
- Preferred: {{contact.preferred_date}} at {{contact.preferred_time}}
- Address: {{contact.address1}}
**What happens next:**
1. RN reviews your request and confirms availability
2. You get a text from us locking the slot or suggesting the closest open window
3. RN arrives 5 minutes early to set up
**Quick prep that makes any drip work better:**
- Hydrate hard the day before, 80 to 100 oz of water
- Eat a real meal about 60 minutes before, not just coffee
- Block the full hour, the drip runs better when you're not trying to take calls mid-session
[See Service Details]({{custom_values.booking_link}})
If anything changed about your timing, service, or address, hit reply and I'll handle it.
{{custom_values.text_message_name}}
IV Wellness · {{location.phone}}"""


# ── GENERIC 28-DAY BODY COPY ──────────────────────────────────────────────────

# D1 — Top 3 questions email + evening SMS
E1_SUBJECT = "{{contact.first_name}}, the 3 questions I get most"
E1_BODY = """Hi {{contact.first_name}},
Three questions come up almost every time someone's about to book a first drip. Honest answers below, including the part most places skip.
**1. Is it safe?**
Every first session includes a full wellness assessment by a licensed RN before anything goes in. She reviews your meds, current state, and any past IV history. If anything is a flag, she tells you straight and we don't run the session. You don't pay for one that isn't a fit.
**2. Will I really feel a difference?**
Honest answer, depends on the drip. Hydration drips work fast, you feel it inside the hour. NAD+ takes 24 to 48 hours for most people. Glutathione you notice over a week. Patients often describe a noticeable lift on their first session, but the strongest results come from doing 3 to 4 in the first month.
**3. Why mobile?**
Because sitting in a clinic for 45 to 90 minutes is the part most people skip. Home, hotel, office, the RN comes to wherever you're already going to be. Same protocol, same nurses, no waiting room.
[See Available Times]({{custom_values.booking_link}})
Whatever you're hoping to feel better from, hit reply and tell me. I'll point you at the drip that fits and answer any other question.
{{custom_values.text_message_name}}"""

SMS_D1_PM = "Hey {{contact.first_name}}, just sent over the top 3 questions about IV drips. If you've got a different one rattling around, send it, I read these."


# D2 — Objection handler email + 5pm SMS
E2_SUBJECT = "The honest part about IV drips most places leave out"
E2_BODY = """Hi {{contact.first_name}},
Three honest things about drips that most clinics don't tell you up front.
**One: NAD+ at full dose burns the first 20 minutes.**
Your chest feels warm and your face flushes. We slow the drip way down at the start, but anyone who tells you it's totally comfortable is lying. The rest of the session is fine. If you're considering NAD+, know that going in.
**Two: A single Skinny Drip won't change the scale.**
What it does is support metabolism and energy at the cellular level so the rest of your routine works better. Patients often describe feeling lighter and clearer within the day, but the body composition piece is a multi-session story.
**Three: Hydration drips don't replace water.**
A Myers Cocktail or hydration push will catch you up fast if you're depleted (post-flight, post-event, post-sick), but the daily 80 to 100 oz of water is still the baseline. The drip is the ceiling boost, not the floor.
**Why I'm telling you this up front:**
Because patients who book with realistic expectations are the ones who stick with the protocol. The ones who think one session fixes everything end up disappointed.
[See Available Times]({{custom_values.booking_link}})
The free pre-session wellness assessment is what tells us straight which drip fits where you are today.
{{custom_values.text_message_name}}"""

SMS_D2_5PM = "Hey {{contact.first_name}}, I put together a quick what-to-expect rundown for first drips. Takes 2 minutes to read. Want me to send it?"


# D3 — Prep tips email + interrupt SMS
E3_SUBJECT = "4 things to do before any IV drip (no sales pitch)"
E3_BODY = """Hi {{contact.first_name}},
No pitch today. Four small things that make any drip work better, true with us or anywhere else.
**1. Hydrate hard the day before.**
Aim for 80 to 100 oz of water. The drip runs better when you're already topped off, and the IV stick is much easier when your veins are showing up.
**2. Eat a real meal about 60 minutes before.**
Not a granola bar, not just coffee. Empty stomach plus IV leaves some people lightheaded in the first 20 minutes.
**3. Block the full hour.**
A drip is not a session you squeeze between meetings. Plan to sit for the whole thing. Trying to take a call mid-drip is the most common regret first-timers report.
**4. Wear something with sleeves that roll easy.**
The RN works in your forearm. Tight long sleeves slow the setup. Tee shirt, tank top, or a button-down works.
That's it.
P.S. Whenever you're ready: {{custom_values.booking_link}}
{{custom_values.text_message_name}}"""

SMS_D3 = "Is this {{contact.first_name}}?"


# D4 — Composite client story + 5pm SMS
E4_SUBJECT = "She came in just to try it once"
E4_BODY = """Hi {{contact.first_name}},
A client reached out last fall. Mid-40s, not a specific symptom, just curious about IV drips after a friend told her about us. She booked one Myers Cocktail, told us afterward she'd see how it went.
Her words on the way out, copy-pasted from the follow-up text:
*"That's the clearest my head's been in months. I don't know what I was running on but it wasn't this."*
She went on to do the membership cadence. Now she comes monthly.
The thing she told me after that stuck. She wasn't tired. She just hadn't realized she was drifting through her days at 70%. She didn't know what fully on felt like anymore.
Drips don't do anything dramatic. They restore baseline. Most first-timers describe it the same way she did, "this is how I should already be feeling."
Reply "menu" and I'll send the full drip list if you want to see what we offer alongside Myers. Or if you've got a question, send it.
[Lock In Your First Session]({{custom_values.booking_link}})
{{custom_values.text_message_name}}"""

SMS_D4_5PM = "Hey {{contact.first_name}}, did you want me to grab a slot for next week, or play it by ear? Either's fine."


# D5 — Curiosity gap SMS only
SMS_D5_5PM = "Hey {{contact.first_name}}, most first-time IV clients are surprised by one specific thing. Mind if I share?"


# D7 — Zeigarnik close email + direct SMS
E7_SUBJECT = "Remember when I said drips surprise people?"
E7_BODY = """Hi {{contact.first_name}},
A few days back I said I'd share the thing first-time IV clients say most often after their session.
Here it is:
*"I didn't know I was running on empty until I wasn't."*
That sentence shows up in our exit feedback about once a week, almost word for word. People aren't surprised by the session itself. They're surprised by the gap, how off-baseline they'd been without realizing.
Most of our regulars didn't think they needed support. They came in for a one-off, sat through the 45 to 90 minutes, and afterward realized they'd been calling exhaustion "just busy" or "just my age" for months.
I'm not going to push you. If now isn't the right time, that's real. But if you've been telling yourself you'd come in "when things slow down," that line is the one keeping you exactly where you are.
What's the question that would actually move the needle for you? Reply, it goes straight to me.
Or whenever you're ready: {{custom_values.booking_link}}
{{custom_values.text_message_name}}"""

SMS_D7 = "Hey {{contact.first_name}}, honest one, what's actually holding you back? No pressure."


# D10 — Compounding math email
E10_SUBJECT = "Why the first month matters more than the first drip"
E10_BODY = """Hi {{contact.first_name}},
Quick honest one. No sell.
Most people treat IV drips like a one-time experiment. Try it once, see how it feels, decide later. That's a fine way to test the floor of what the drip does. It is not how the protocol actually works.
Here's the part that surprises clients:
**A single drip moves you noticeably back toward baseline.** That window of feeling clear and steady lasts a few days for most people, then it fades, because your body is already drawing down again.
**The 3-to-4 session protocol in the first month is what compounds.** Each session puts more nutrients into the system before the previous infusion has fully tapered. The lift gets longer-lasting, the gap between sessions widens, and you settle into a maintenance cadence that's usually monthly.
**A first-timer who books one drip and tries to evaluate the protocol from there is grading the wrong test.** The single session shows you it works. The first month shows you what it actually does.
That's the actual math. Not "you'll feel like a million bucks." Just "your body's machinery for energy, recovery, and clarity starts running at the level it should already be at."
The free wellness assessment and your 25% off (if you came in through a scratch-off) are still on the table. Whenever you're ready: {{custom_values.booking_link}}
{{custom_values.text_message_name}} · {{location.phone}}"""


# D12 — Objection surfacer SMS
SMS_D12 = "{{contact.first_name}}, when I don't hear back it's usually timing or a question I haven't answered. Is it one of those?"


# D14 — Peak-end / RECOVER keyword email + SMS
E14_SUBJECT = "Last email from me, plus my direct line"
E14_BODY = """Hi {{contact.first_name}},
Last email from me on this. I mean it.
People wait for a reason. The most common ones I hear:
- "I'll book when I'm not so busy" (you won't be, the calendar doesn't clear)
- "I want to see if I really need it first" (the only way to know is one session, and the wellness assessment is included)
- "I'm not sure which drip is right for me" (that's literally what the on-site assessment is for, and it's free)
If any of those is you, I get it. I'll stop emailing.
Two ways to come back when you're ready:
**1.** Book directly: {{custom_values.booking_link}}
**2.** Text **{{location.phone}}** with the keyword **RECOVER**. Goes to our desk, not a queue. You don't fill out a form again, the keyword tells our system who you are and gets you straight to a slot.
Whatever you decide, thanks for considering us.
{{custom_values.text_message_name}}
IV Wellness
{{location.address}}
{{location.phone}}"""

SMS_D14 = "Last one from me, {{contact.first_name}}. Whenever you're ready, text RECOVER to {{location.phone}} and I'll get the RN on the calendar that week."


# D28 — Breakup SMS
SMS_D28 = "Hi {{contact.first_name}}, {{custom_values.text_message_name}}. Should I close your file or keep it open for whenever you're ready?"


# ── CAMPAIGN ──────────────────────────────────────────────────────────────────

CAMPAIGN = {
    # 01a. Scratch-off intro — name/email/phone only, no service preference.
    # Stamps latest_optin = "Scratch Off" as a LEAD-SOURCE label (per user
    # convention 2026-05-08: latest_optin tracks how the lead arrived, not
    # the requested service). Ends by handing off to the 28-day body.
    "01a-intro-scratchoff": {
        "name": "01a. IV Wellness — Scratch-Off Intro (Day 0)",
        # Trigger: wire in GHL UI (FB lead form for scratch-off page, or tag).
        "templates": link_steps([
            # IV Wellness "Latest Opt-In" custom field UUID (verified 2026-05-08).
            update_contact_field_step("Set latest_optin = Scratch Off",
                                      "NnAIZ8j1JcHrLkQozw13", "Scratch Off",
                                      title="Latest Opt-In", field_type="string"),
            wait_step("Wait .1 min", 0.1, "minutes"),
            sms_step("A T+0 welcome + 25% locked", SMS_A_T0),
            wait_step("Wait 1 min", 1, "minutes"),
            sms_step("A T+1m timing question", SMS_A_T1),
            wait_step("Wait 1 hour", 1, "hour"),
            email_step("A T+1hr 25% recap email", EMAIL_A_SUBJECT, EMAIL_A_BODY, FROM_NAME),
            tag_step("Handoff to generic 28-day", [HANDOFF_TAG]),
        ]),
    },

    # 01b. Main on-site form intro — full form payload available.
    # Assumes form's `Service Interested In` is wired to the `latest_optin`
    # custom field in GHL. If not, add an extra update_contact_field_step
    # before the welcome SMS to copy the value across.
    "01b-intro-form": {
        "name": "01b. IV Wellness — Main Form Intro (Day 0)",
        # Trigger: wire in GHL UI (FB lead form for main site form, or tag).
        "templates": link_steps([
            wait_step("Wait .1 min", 0.1, "minutes"),
            sms_step("B T+0 welcome with service", SMS_B_T0),
            wait_step("Wait 1 min", 1, "minutes"),
            sms_step("B T+1m request-not-confirmation", SMS_B_T1),
            wait_step("Wait 1 hour", 1, "hour"),
            email_step("B T+1hr what-to-expect", EMAIL_B_SUBJECT, EMAIL_B_BODY, FROM_NAME),
            tag_step("Handoff to generic 28-day", [HANDOFF_TAG]),
        ]),
    },

    # 02. Generic 28-day body — service-agnostic, fed by both intros.
    # Trigger: contact gets tag HANDOFF_TAG (set at end of 01a and 01b).
    "02-generic-28day": {
        "name": "02. IV Wellness — Generic 28-Day Nurture",
        # Trigger: wire in GHL UI to fire on `iv-wellness-nurture-start` tag.
        "templates": link_steps([
            # D1 (T+0 from handoff = roughly Day 1 since intros end ~T+1h on D0)
            wait_step("Wait to D1 10am", 22, "hour"),
            email_step("D1 Top 3 questions", E1_SUBJECT, E1_BODY, FROM_NAME),
            wait_step("Wait to D1 evening", 8, "hour"),
            sms_step("D1 evening light nudge", SMS_D1_PM),

            # D2
            wait_step("Wait to D2 10am", 14, "hour"),
            email_step("D2 Honest objection handler", E2_SUBJECT, E2_BODY, FROM_NAME),
            wait_step("Wait to D2 5pm", 7, "hour"),
            sms_step("D2 5pm reciprocity hook", SMS_D2_5PM),

            # D3
            wait_step("Wait to D3 10am", 17, "hour"),
            email_step("D3 Prep tips", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("Wait 1 min", 1, "minutes"),
            sms_step("D3 pattern interrupt", SMS_D3),

            # D4
            wait_step("Wait to D4 10am", 24, "hour"),
            email_step("D4 Composite client story", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("Wait to D4 5pm", 7, "hour"),
            sms_step("D4 5pm soft slot hold", SMS_D4_5PM),

            # D5
            wait_step("Wait to D5 5pm", 24, "hour"),
            sms_step("D5 5pm curiosity gap", SMS_D5_5PM),

            # D7 (skip D6)
            wait_step("Wait to D7 10am", 41, "hour"),
            email_step("D7 Zeigarnik close", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("Wait 1 min", 1, "minutes"),
            sms_step("D7 direct question", SMS_D7),

            # D10
            wait_step("Wait to D10 10am", 3, "days"),
            email_step("D10 Compounding math", E10_SUBJECT, E10_BODY, FROM_NAME),

            # D12
            wait_step("Wait to D12 10am", 2, "days"),
            sms_step("D12 objection surfacer", SMS_D12),

            # D14
            wait_step("Wait to D14 9am", 47, "hour"),
            email_step("D14 Peak-end + RECOVER", E14_SUBJECT, E14_BODY, FROM_NAME),
            wait_step("Wait 1 hour", 1, "hour"),
            sms_step("D14 keyword reminder", SMS_D14),

            # D28
            wait_step("Wait to D28 10am", 14, "days"),
            sms_step("D28 breakup", SMS_D28),

            tag_step("Mark nurture complete", [COMPLETE_TAG]),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"IV Wellness Intake Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="IV Wellness Intake Nurture",
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
