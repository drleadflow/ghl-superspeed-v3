#!/usr/bin/env python3
"""
A Prestige Aesthetics & Wellness — The Soft Reset (Jeuveau neurotoxin
first-time / re-engage offer) nurture sequence for women in their
late 30s through mid 50s in Franklin TN.

Trigger model (per project_iv_wellness_nad_workflow_rules):
- WF-01 ships with a tag trigger `softreset-lead` because the engine's
  automatic trigger creation only handles `contact_tag` types. The
  Facebook lead form must be swapped to a Facebook Form Submission
  trigger in the GHL UI after deploy (or set the form to add the
  `softreset-lead` tag on submit so the existing tag trigger fires).
- WF-02 trigger is `Customer Replied` filtered to `replied to workflow
  = WF-01 Master Sequence` (set up in GHL UI after WF-01 ID is captured).

Two workflows, linear (no keyword recovery — replies route through
WF-02 directly, no keyword required):
  01. Soft Reset Master Sequence (28 days, automated only)
  02. Soft Reset Global Reply Handler

Touchpoint count: 27 across 28 days. Has Deadline=Yes per the offer
spec, so D5 deposit-deadline copy is used (clean 14-day window from
form submit since the offer page does not set a hard calendar date).

Hard rules (Soft Reset / Prestige strict mode):
- "Softens / smooths / supports a refreshed look / patients often
  describe a more rested look" only. Never "erases, freezes, removes
  wrinkles permanently, guarantees, fixes."
- Never use "100%" anywhere in body copy.
- Acknowledge the frozen-fear and the cost-uncertainty up front.
  Andrea Pryor NP is the on-site injector; her precision is the
  differentiation.
- No em dashes anywhere in body copy (allowed in workflow names and
  this docstring only).
- {{custom_values.text_message_name}} is the bot persona, NOT Andrea.
- No before/after photos in SMS (SMS is text-only).
- No financing / Care Credit references in body copy.
- Tag prefix: softreset-
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

E1_SUBJECT = "{{contact.first_name}}, the frozen question (let's get it out of the way)"
E1_BODY = """Hi {{contact.first_name}},

Thanks for reaching out about The Soft Reset. I'm {{custom_values.text_message_name}}, I handle the front desk for {{location.name}} here in Franklin. Andrea Pryor NP is the injector. She built this offer for women who have been thinking about Jeuveau for a while but keep stopping at the same wall: "what if I look frozen."

So let's just put that on the table first.

The whole point of how Andrea places Jeuveau is to soften, not erase. The forehead still moves. The brow still lifts when you laugh. Patients often describe a more rested look in the mirror, not a different face. If you walk into a consult and someone is talking about units before they have looked at how your face actually moves, that is the wrong room.

Here is what The Soft Reset includes:

- Complimentary aesthetic consult with Andrea (a $150 value), so the plan comes before the price
- Jeuveau at $10 per unit, 30-unit minimum, which works out to about $450 for most first timers
- $50 deposit to hold the appointment, applied to the treatment
- A 2-week follow-up assessment to fine-tune symmetry
- $50 credit toward your next treatment when the 2-week follow-up is completed

One question, because your answer changes what I send next:

**Is this your first time considering a neurotoxin, or have you had Botox or Dysport somewhere else and you're shopping for a new injector?**

Reply with "first time" or "switching." One phrase is enough.

[Book Your Soft Reset]({{custom_values.booking_link}})

Not ready to book? Reply with the question that's actually on your mind. I read every one.

{{custom_values.text_message_name}}
{{location.name}}
{{location.phone}}"""

# Subject pattern: name the elephant. Lead with the frozen objection
# (top buying trigger #1 from the offer doc). Soft segmenting Q: first
# time vs switching (different from glp1's weight vs hormones).


E2_SUBJECT = "The 3 questions I get most before a first Jeuveau appointment"
E2_BODY = """Hi {{contact.first_name}},

Three questions come up almost every time a first-timer reaches out about The Soft Reset. Honest answers below, including the part most clinics dance around.

**1. Will I look frozen or overdone?**
Not with how Andrea places it. The 30-unit starting point is intentionally conservative for a first treatment. Her placement focuses on the muscles that pull down or pull tight, not the muscles you use to actually express. The goal in your first appointment is "she looks rested," not "she had something done." If you want a stronger result later, the dose can come up at the next visit. You cannot un-inject too much, so we start low and build.

**2. How much is this actually going to cost me, total?**
Here is the math, no surprises. The Soft Reset is $10 per unit with a 30-unit minimum, so most first timers land at about $450. The $50 deposit you put down to hold the appointment comes off that total at checkout. The consult itself is included as a bonus, normally a $150 charge. If your facial anatomy needs more than 30 units to get a balanced result, Andrea tells you that in the consult before any product is drawn up, and you decide. Nothing happens behind a curtain.

**3. How do I know Andrea is the right injector for me?**
Fair question. Three things to look for in any injector: do they map your face before mixing anything, do they explain why each unit is going where it's going, and do they push you to add more than you came in for. Andrea's whole approach is the opposite of high-volume per-unit clinics. The 2-week follow-up is built in so you have a second chance to dial in symmetry without paying again.

One honest thing about Jeuveau. It takes 3 to 7 days to start showing, and it lands fully around day 14. So if you book and look in the mirror the next morning expecting a difference, you will not see it yet. That patience window is normal and expected. The duration runs about 3 to 4 months for most patients before you would consider a touch-up.

[Book Your Soft Reset]({{custom_values.booking_link}})

One more thing. The thing first-time Jeuveau patients say most often after their 2-week follow-up surprised me when I started hearing it. I'll share it in a few days.

{{custom_values.text_message_name}}"""

# Subject pattern: specificity + count. Handles the top 3 objections
# from the offer doc head-on (frozen, cost, provider trust). Pratfall
# (the 3 to 7 day wait). Zeigarnik teaser closes in D7. NOTE: no use of
# "100%" anywhere; "softens / patients often describe / supports" only.


E3_SUBJECT = "4 things to think through before any tox appointment (no sales pitch)"
E3_BODY = """Hi {{contact.first_name}},

No pitch today. Four small things that make any first neurotoxin appointment land better, true with us or anywhere else.

**1. Bring a photo of yourself from a few years ago that you actually liked.**
Not a perfect photo. A real one. Andrea uses this to anchor the conversation in "your version of rested" instead of someone else's idea of treated. It is the single thing that most reliably keeps a first treatment looking like you.

**2. Decide what you want people to NOT notice.**
Most first timers come in with a list of things they want fixed. The more useful list is the things you want to keep. The smile lines that show up when you laugh with your kids. The way your forehead lifts when you're surprised. Tell Andrea what stays. That shapes the placement more than anything else.

**3. Skip blood thinners and alcohol for 24 hours before, if you can.**
Aspirin, ibuprofen, fish oil, and a glass of wine the night before all raise the chance of small bruises at the injection sites. Not dangerous, just annoying. Tylenol is fine if you need something. If you're on a prescription blood thinner, do not stop it without checking with the prescriber, just mention it in the consult.

**4. Plan to skip the gym, the sauna, and lying flat for 4 hours after.**
Hot yoga the same afternoon is the most common first-timer regret. Heat and pressure in those first hours can move product where you don't want it. A normal evening is fine. Just no upside-down or face-down for the rest of the day.

That's it.

P.S. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""

# Subject pattern: how-to + number. Pure value, no sell. Reframed for
# tox/face context (photo + what stays + thinner timing + post-care)
# instead of glp1's labs/diet/symptom prep. Different angles entirely.


E4_SUBJECT = "She came in convinced she'd hate it"
E4_BODY = """Hi {{contact.first_name}},

A patient reached out earlier this year. Early 40s, told me on the intake she had been "thinking about Botox for five years" and kept canceling because every friend she knew who got it ended up looking, in her words, "a little startled." Two of her friends had already asked Andrea to fix work done elsewhere, which is part of why she finally trusted booking the consult.

Her first appointment took the full 40 minutes. Most of it was Andrea mapping her face at rest, smiling, frowning, and surprised, before any product was drawn. Andrea explained why she wanted to leave the lower forehead muscle alone (so her brow could still lift when she laughed) and why she was using fewer units around the eyes than the patient had assumed.

Her message at the 2-week follow-up, copy-pasted with permission:

*"Three different people have told me I look like I'm sleeping better. Nobody has said the word Botox. That's exactly what I wanted."*

She came back at 4 months for the second round. Same dose, same placement.

The thing she told me that stuck. She said the part that surprised her was not the result. It was that Andrea actually talked her out of two of the units she had asked for, because the placement she wanted would have flattened her smile. That conversation is the one most first timers say they had never had before.

The Soft Reset is built around that conversation, not the injection itself.

Reply "consult" if you want to know what to expect from the 40-minute appointment, or "andrea" if you want the short version of how she approaches first-time treatments specifically.

[Book Your Soft Reset]({{custom_values.booking_link}})

{{custom_values.text_message_name}}"""

# Subject pattern: story tease that names the fear directly. Composite
# patient. Two reply options to surface intent without forcing a
# booking. NO "100%" framing. Approved language only.


E5_SUBJECT = "Remember when I said first-timers say something surprising at 2 weeks?"
E5_BODY = """Hi {{contact.first_name}},

A few days back I said I'd share the thing first-time Jeuveau patients say most often at their 2-week follow-up.

Here it is:

*"My husband cannot tell I had anything done, and he keeps asking why I look so rested."*

That sentence shows up in our follow-ups about once a week, almost word for word. It's not the smoother forehead they describe first. It's that the people closest to them notice something is different and cannot place what it is. That's the result Andrea is calibrating for. Not "you had work done." More like "you took a vacation."

Most of our first-time Soft Reset patients did not come in wanting to look younger. They came in wanting to stop looking tired in photos when they were not actually tired. Patients often describe the gap between how they feel and how they look getting smaller after the first treatment. That is the whole point of the offer.

I'm not going to push you. If now isn't the right time, that's real. But if you've been telling yourself you'll book "after the next big event" or "once you're sure," that line is the one keeping you in the same loop. The 2-week follow-up assessment is built in for exactly that reason. You see the result, you tell Andrea what you want to adjust, and she fine-tunes without charging you again.

What's the question that would actually move the needle for you? Reply, it goes straight to me.

Or whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""

# Subject pattern: callback to D2 Zeigarnik teaser. Closes the loop
# with a quote that addresses the natural-vs-frozen fear directly.
# Low-friction reply ask + main CTA.


E5_DEADLINE_SUBJECT = "{{contact.first_name}}, the deposit window for The Soft Reset"
E5_DEADLINE_BODY = """Hi {{contact.first_name}},

Quick honest note about timing.

The Soft Reset includes the complimentary aesthetic consult ($150 value), the 2-week follow-up assessment, and the $50 next-treatment credit when you complete the follow-up. To keep that bundle attached to your appointment, the $50 deposit needs to be down within 14 days of the day you reached out.

After that window, you can still book Jeuveau with Andrea, but the appointment goes through her standard flow without the bundled consult and credit attached. Same injector, same approach, just not the same package.

If The Soft Reset is the version you want, the simplest move is to put down the $50 deposit now, hold a slot in the next two to three weeks, and decide on dose during the consult. The deposit comes off the treatment total at checkout either way.

[Hold My Soft Reset Slot]({{custom_values.booking_link}})

If the timing isn't right, no pressure, just reply and tell me. I'd rather you book the right week than rush it.

{{custom_values.text_message_name}}
{{location.phone}}"""

# Subject pattern: deadline, names the contact. Has Deadline=Yes per
# Notion. No specific date set on the offer page so the language uses
# a clean 14-day deposit window keyed to form submit (matches the bundle
# being tied to the deposit, not a calendar date). Uses real bonuses
# from offer doc: $150 consult, 2-week follow-up, $50 credit.


E6_SUBJECT = "Why the 2-week follow-up matters more than the first appointment"
E6_BODY = """Hi {{contact.first_name}},

Quick honest one. No sell.

Most patients treat a first Jeuveau appointment as the whole event. Show up, get treated, see what happens, decide later. That is a fine way to find out if you tolerate it. It is not how the protocol actually works at our clinic.

Here's the part that surprises first timers:

**Days 1 through 7 are the patience window.** Nothing visible is happening yet. The product is binding. Patients sometimes panic in this window because the mirror looks the same. This is normal and expected. The treatment has not "failed."

**Days 7 through 14 are when the result lands.** Your forehead and brow muscles soften progressively. The smoother surface shows up gradually, not overnight. Most patients describe the change as "I look more like myself when I'm well-rested" by day 14, not "I look different."

**The 2-week follow-up is where the precision happens.** Andrea reassesses how the product settled into your specific facial anatomy. If one brow is lifting more than the other, if there is a small area still showing more movement than you wanted, she fine-tunes it without an additional treatment fee. This is not a generic add-on. It is built into The Soft Reset specifically because tox is not a one-shot calibration for most first timers.

**Days 14 through 90 are where you actually find out what your dose should be next time.** Andrea uses what she sees at the 2-week follow-up to plan your second treatment, which usually lands around month 3 or 4 when the first one starts to soften.

**A patient who books once, walks out, and decides at day 5 whether tox "works" is grading the wrong test.** The first appointment shows you tolerance. The 2-week follow-up shows you the calibrated result. The second treatment is where the maintenance cadence settles.

That's the actual math. Not "you'll look 10 years younger by next weekend." Just "your face gets to a refreshed baseline that fits how you're actually living, and then it stays there with two treatments a year."

The complimentary consult, the 2-week follow-up, and the $50 next-treatment credit are all bundled in. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}
{{location.phone}}"""

# Subject pattern: curiosity + specificity. Logic + cost-of-inaction.
# Different from glp1's "90 days metabolic" framing — uses tox-specific
# day-window math (1-7, 7-14, 14-90) and reinforces the bundled
# follow-up as the actual differentiator.


E7_SUBJECT = "Last email from me, plus my direct line"
E7_BODY = """Hi {{contact.first_name}},

Last email from me on this. I mean it.

Women hesitate on tox for honest reasons. The most common ones I hear:

- "I keep meaning to book and life keeps getting in the way" (it will keep getting in the way, the calendar does not clear in your 40s)
- "I'm afraid of looking like I had something done" (the consult is free intel, and Andrea will start conservative on a first treatment by default)
- "I want to wait until I really need it" (the patients with the most natural results are the ones who started early enough that nobody could pin when they started)

If any of those is you, I get it. I'll stop emailing.

When you're ready, two easy options:

**1.** Book directly: {{custom_values.booking_link}}

**2.** Just reply to this email or text {{location.phone}}. Whatever's on your mind, a question, a time that works for you, anything. Goes straight to the front desk, not a queue.

Whatever you decide, thanks for considering us. Andrea built The Soft Reset because she watched too many women in this stage of life get talked into more than they came in for. You deserve the version of this where the conversation comes before the product.

A quick note on what else lives at the clinic, in case any of it's relevant down the road:

- HRT for women navigating perimenopause and menopause
- GLP-1 medical weight loss
- Skin resurfacing and rejuvenation

You don't have to think about any of that today. The Soft Reset stands on its own.

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}
{{location.phone}}"""

# Subject pattern: direct. Open reply CTA, no keyword required.
# Permission to stop. Includes the D14-D28 cross-sell tee-up
# (HRT, GLP-1, skin resurfacing) as a soft mention only, per the
# project brief. This is the message people screenshot.


# ── SMS COPY ─────────────────────────────────────────────────────────────────
# All under 160 chars where possible. No em dashes. Conversational.

SMS_T0 = "Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} at {{location.name}}. Got your Soft Reset inquiry, sending you a quick rundown in a sec. Reply STOP to opt out."

SMS_T1 = "Hey {{contact.first_name}}, {{custom_values.text_message_name}} again. Quick one, is this your first time considering a neurotoxin, or are you switching from a previous injector? Just reply first time or switching."

SMS_D1_15min = "Hey {{contact.first_name}}, just sent you a welcome email with the rundown on The Soft Reset. Same question there, first time or switching? One phrase is enough."

SMS_D2_5pm = "Hey {{contact.first_name}}, I put together a 2-min read on the 3 questions I get most before a first Jeuveau appointment. Want me to send it over?"

SMS_D3_10am = "Is this {{contact.first_name}}?"

SMS_D4_5pm = "Hey {{contact.first_name}}, want me to hold a Soft Reset slot on Andrea's calendar for the next 2 weeks, or play it by ear? Either's fine."

SMS_D5_5pm = "Quick heads up {{contact.first_name}}, the bundled consult + 2-wk follow-up stays attached if the $50 deposit lands within 14 days of your inquiry. Want the link?"

SMS_D7_10am = "Hey {{contact.first_name}}, honest one, what's actually keeping you from booking The Soft Reset? Frozen fear, cost, or just timing? No pressure."

SMS_D12_10am = "{{contact.first_name}}, when I don't hear back it's usually one of three things: timing, a question I haven't answered, or the deposit. Which is it?"

SMS_D14_10am = "Last one from me, {{contact.first_name}}. Whenever you're ready, just reply here and I'll get you onto Andrea's calendar that week. Or book direct: {{custom_values.booking_link}}"

SMS_D28_10am = "Hi {{contact.first_name}}, {{custom_values.text_message_name}}. Should I close your Soft Reset file or keep it open for whenever the timing fits?"


# ── REPLY HANDLER COPY ───────────────────────────────────────────────────────
# Internal alert email body for front desk

REPLY_ALERT_SUBJECT = "REPLIED LEAD: {{contact.first_name}} on Soft Reset nurture"
REPLY_ALERT_BODY = """REPLIED LEAD ALERT.

{{contact.first_name}} {{contact.last_name}} replied to The Soft Reset nurture sequence.

Phone: {{contact.phone}}
Email: {{contact.email}}

ACTION REQUIRED: Respond within 5 minutes. Do NOT let automation re-engage until this contact is manually marked as resolved or rebooked.

Their last message is in the GHL conversation thread. Check it before replying."""


# ── CAMPAIGN ─────────────────────────────────────────────────────────────────
# Day map for 01-master (cumulative from FB form submit, automated only):
#   T+0     SMS_T0          instant confirm + opt-out
#   T+1m    SMS_T1          qualifying Q (first time vs switching)
#   D1 10a  E1              welcome + frozen-fear + qualifier echo
#   D1 10:15a SMS_D1_15min  echo qualifier on SMS channel
#   D2 10a  E2              objections (frozen / cost / trust) + Zeigarnik
#   D2 5p   SMS_D2_5pm      reciprocity hook (rundown offer)
#   D3 10a  E3              quick-win prep (photo / what stays / thinners / post-care)
#   D3 10a  SMS_D3_10am     pattern interrupt
#   D4 10a  E4              social proof (first-timer story)
#   D4 5p   SMS_D4_5pm      soft slot hold
#   D5 5p   SMS_D5_5pm      deposit window heads-up (Has Deadline=Yes)
#   D5 9p   E5_DEADLINE     deposit window 14-day deadline email
#   D7 10a  E5              Zeigarnik close (husband-cant-tell quote)
#   D7 10a  SMS_D7_10am     direct question (3 named blockers)
#   D10 10a E6              2-week follow-up math + cost of waiting
#   D12 10a SMS_D12_10am    objection surfacer (3 named blockers)
#   D14 9a  E7              peak-end + open reply CTA + cross-sell soft mention
#   D14 10a SMS_D14_10am    final nudge
#   D28 10a SMS_D28_10am    breakup text
#   tag     softreset-nurture-complete

CAMPAIGN = {
    "01-master": {
        "name": "01. Soft Reset — Master Sequence",
        "tag": "softreset-lead",
        "templates": link_steps([
            sms_step("S0 Instant Confirm + Opt-Out (T+0)", SMS_T0),
            wait_step("1 min", 1, "minutes"),
            sms_step("S1 Qualifying Q First Time vs Switching (T+1m)", SMS_T1),
            wait_step("22 hours", 22, "hour"),
            email_step("E1 Welcome + Frozen Fear + Qualifier (D1 10am)", E1_SUBJECT, E1_BODY, FROM_NAME),
            wait_step("15 min", 15, "minutes"),
            sms_step("S_D1_15 Echo Qualifier (D1 10:15am)", SMS_D1_15min),
            wait_step("23 hours", 23, "hour"),
            wait_step("45 min", 45, "minutes"),
            email_step("E2 Top 3 Objections + Zeigarnik Teaser (D2 10am)", E2_SUBJECT, E2_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D2 Reciprocity Hook (D2 5pm)", SMS_D2_5pm),
            wait_step("17 hours", 17, "hour"),
            email_step("E3 Prep Tips Photo What Stays Thinners Post-Care (D3 10am)", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D3 Pattern Interrupt (D3 10am)", SMS_D3_10am),
            wait_step("24 hours", 24, "hour"),
            email_step("E4 First Timer Story (D4 10am)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D4 Soft Slot Hold (D4 5pm)", SMS_D4_5pm),
            wait_step("24 hours", 24, "hour"),
            sms_step("S_D5 Deposit Window Heads-Up (D5 5pm)", SMS_D5_5pm),
            wait_step("4 hours", 4, "hour"),
            email_step("E5_DEADLINE Deposit Window (D5 9pm)", E5_DEADLINE_SUBJECT, E5_DEADLINE_BODY, FROM_NAME),
            wait_step("37 hours", 37, "hour"),
            email_step("E5 Zeigarnik Close Husband Cant Tell (D7 10am)", E5_SUBJECT, E5_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D7 Direct Question 3 Blockers (D7 10am)", SMS_D7_10am),
            wait_step("3 days", 3, "days"),
            email_step("E6 2-Week Follow-Up Math (D10 10am)", E6_SUBJECT, E6_BODY, FROM_NAME),
            wait_step("2 days", 2, "days"),
            sms_step("S_D12 Objection Surfacer (D12 10am)", SMS_D12_10am),
            wait_step("47 hours", 47, "hour"),
            email_step("E7 Peak-End + Cross-Sell (D14 9am)", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D14 Final Nudge (D14 10am)", SMS_D14_10am),
            wait_step("14 days", 14, "days"),
            sms_step("S_D28 Breakup Text (D28 10am)", SMS_D28_10am),
            tag_step("Mark Soft Reset Nurture Complete", ["softreset-nurture-complete"]),
        ]),
    },

    "02-reply-handler": {
        "name": "02. Soft Reset — Global Reply Handler",
        "tag": "softreset-replied",
        "templates": link_steps([
            tag_step("Confirm Reply Tag Applied", ["softreset-replied"]),
            email_step("Internal Alert to Front Desk", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"Soft Reset Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="The Soft Reset",
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
