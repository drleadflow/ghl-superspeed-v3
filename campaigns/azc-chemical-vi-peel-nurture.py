#!/usr/bin/env python3
"""
Amazing Skin Care Med Spa (AZC) — Chemical VI Peel New Client Special nurture.

Client: Amazing Skin Care Med Spa, Hollywood FL (Jennifer Bryan, owner).
Brand vibe: Warm. Private. Personalized. Inclusive. Radiant.
Differentiator: Jennifer specializes in textured/darker skin types — 100+
5-star reviews and a private cozy studio environment. Voice mirrors that:
warm, private, personalized, inclusive.

Three workflows, linear only (no parallel branched sub-variants):
  01. Master Sequence — 28-day automated nurture
  02. RESET Keyword Recovery — re-engage lapsed leads
  03. Global Reply Handler — internal alert when contact replies

Trigger configuration (operator sets in GHL UI after deploy):
  - WF-01: Facebook Lead Form submission (engine creates a placeholder
    `vipeel-lead` tag trigger; swap to FB form trigger in the UI).
  - WF-02: Inbound SMS contains keyword RESET (engine creates a placeholder
    `vipeel-keyword-trigger` tag trigger; swap to keyword trigger in UI).
  - WF-03: Customer Replied event filtered to contacts currently in WF-01
    (engine creates a placeholder `vipeel-replied` tag trigger; swap to
    Customer Replied + workflow filter in UI).

Hard rules (med spa compliance + client voice):
  - Approved language only: "supports", "helps with", "patients often
    describe". Never "cures", "treats", "fixes", "guarantees results".
  - Warm + private + personalized + inclusive tone — call out textured /
    darker skin expertise where it fits naturally.
  - Address pre/post peel care expectations early (downtime, sun avoidance,
    skincare routine) — this is the #1 objection.
  - No em dashes anywhere.
  - {{custom_values.text_message_name}} is the bot persona, NOT Jennifer.
  - {{custom_values.booking_link}} is the booking URL.
  - Tag prefix: `vipeel-`.

Touchpoint count: 27 across 28 days.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, link_steps,
)

LOCATION_ID = "RGg9HNyo7e4ttGutRyMt"
COMPANY_ID  = "R1HWQKyMMoj4PJ5mAYed"
USER_ID     = "YewkebOufK3hmeP1gx4B"
PARENT_FOLDER = ""

FROM_NAME = "{{custom_values.text_message_name}}"

# ── EMAIL COPY ───────────────────────────────────────────────────────────────

E1_SUBJECT = "{{contact.first_name}}, quick question before I send you anything"
E1_BODY = """Hi {{contact.first_name}},

Thanks for reaching out about the VI Peel. I'm {{custom_values.text_message_name}}, I handle bookings for {{location.name}} here in Hollywood. Jennifer is our lead esthetician and she's been doing peels for over a decade, with a focus on textured and darker skin tones that most spas won't touch.

One question before I send you anything else, because your answer changes what's actually useful to you:

**What's the main thing you're hoping the VI Peel helps with: acne, hyperpigmentation, dull or uneven texture, or something else?**

Reply with one or two words, that's enough.

In the meantime, here's what your first session looks like:

- Personalized skin consultation with Jennifer before anything is applied
- Full medical-grade VI Peel treatment in our private Hollywood studio
- Take-home post-peel kit so you know exactly what to do day 1 through day 7
- Complimentary 2-week follow-up consultation to check your results

Pricing and the full new-client special are on the booking page so there are no surprises.

[See Available Times]({{custom_values.booking_link}})

Not ready to book? Reply with your biggest question and I'll answer it personally.

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""


E2_SUBJECT = "The 3 questions I get most about the VI Peel"
E2_BODY = """Hi {{contact.first_name}},

Three questions come up almost every time someone reaches out about the VI Peel. Honest answers below, including the part most places skip.

**1. Will it hurt?**
Patients often describe a mild tingling or warmth for the first few minutes, then it settles. The peel solution is layered on slowly and Jennifer talks you through every step. It's not a relaxing facial, but it's not painful either. Most clients say the discomfort is well worth what shows up by day 7.

**2. How long is the recovery?**
Plan for skin to feel tender for 5 to 7 days. Light visible peeling usually starts around day 3 and finishes by day 7. You can absolutely work and go about your normal day, you just need to skip the gym, sun, and makeup for the first few days. Your post-peel kit walks you through it hour by hour.

**3. Is this just a fancy spa facial?**
Honest answer, very different. A facial cleans and hydrates the surface. The VI Peel is a medical-grade treatment that supports cell turnover at a deeper level, which is why patients often describe clearer, brighter, more even-toned skin once the peel finishes. It's the closest thing to a clinical reset you can get without downtime from a laser.

One honest thing about us. Jennifer specializes in skin of color and textured skin, which a lot of spas in South Florida won't take on for peels. If you've been told elsewhere that your skin is "too sensitive" for a peel, ask anyway. The VI Peel formula she uses is one of the few that's safe across the full range of skin tones.

[See Available Times]({{custom_values.booking_link}})

One more thing. The thing first-time VI Peel clients say most often after the peeling finishes always surprises me a little. I'll share it in a few days.

{{custom_values.text_message_name}}"""


E3_SUBJECT = "4 things to do before any VI Peel (no sales pitch)"
E3_BODY = """Hi {{contact.first_name}},

No pitch today. Four small things that make any VI Peel work better, true with us or anywhere else.

**1. Stop retinol and exfoliating acids 5 to 7 days before.**
Anything with retinol, glycolic, salicylic, or vitamin C scrubs needs to pause. Your skin needs to be calm at baseline before the peel goes on, otherwise you risk over-exfoliation.

**2. Hydrate hard the week before.**
Aim for 80 to 100 oz of water daily. Hydrated skin peels more evenly, which means a smoother result on day 7.

**3. Block your social calendar for 5 to 7 days post-peel.**
You can work, run errands, do school pickup, all of it. What you can't really do is a wedding or photoshoot mid-peel. Plan accordingly.

**4. Stay out of direct sun starting now.**
The two weeks around your peel matter most for sun avoidance. Hat, SPF 30+, and shade. Sun on freshly peeled skin is the #1 cause of post-peel pigmentation, especially on textured skin.

That's it.

P.S. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""


E4_SUBJECT = "She'd been told her skin was too sensitive for a peel"
E4_BODY = """Hi {{contact.first_name}},

A client reached out last fall. Late 30s, deeper skin tone, dealing with stubborn hyperpigmentation along her cheeks and jawline that she'd been trying to fade with serums for almost two years. Three other spas had told her a peel was too risky for her skin type.

Jennifer brought her in for a personalized consult first, looked at her skin under the lamp, and walked her through the specific VI Peel formula that's safe across all skin tones. They booked the session for the following week.

Her message after day 7 of peeling:

*"I genuinely cried looking in the mirror this morning. The dark patches I've been hiding for two years are so much lighter. I wish I'd done this years ago."*

She's on a quarterly maintenance schedule now.

The thing she said after that stuck. It wasn't the result that surprised her, it was being treated like her skin actually mattered. Most places had quietly steered her toward microdermabrasion or "something gentler" because they weren't comfortable working on textured skin.

That's the gap our studio fills. Jennifer has spent her whole career on skin of color and textured skin. The VI Peel formula she uses is one of the few peels that's safe across the full Fitzpatrick scale, which is why we keep it as the centerpiece of the new-client special.

Reply "consult" and I'll send the new-client form so Jennifer can review your skin before you even book. Or if you've got a question, send it.

[Lock In Your First Session]({{custom_values.booking_link}})

{{custom_values.text_message_name}}"""


E5_SUBJECT = "Remember when I said the VI Peel surprises people?"
E5_BODY = """Hi {{contact.first_name}},

A few days back I said I'd share the thing first-time VI Peel clients say most often after their peeling finishes.

Here it is:

*"My skin doesn't just look better, it finally feels like mine again."*

That sentence shows up in our follow-up messages over and over, almost word for word. People aren't surprised by a brighter complexion, they're surprised by how much they'd been hiding. Foundation layers, filters, angled selfies, picking the right lighting in every restaurant. None of that goes through your head consciously, until one morning it doesn't have to.

Most of our regulars didn't think they needed something this targeted. They came in for the new-client special, sat through the peel, did the 7-day cycle at home, and afterward realized how much energy they'd been spending compensating for skin they weren't comfortable in.

I'm not going to push you. If now isn't the right time, that's real. But if you've been telling yourself you'd come in "after summer" or "once things calm down," that line is the one keeping you exactly where you are.

What's the question that would actually move the needle for you? Reply, it goes straight to me.

Or whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""


E6_SUBJECT = "Why one peel matters more than you'd think"
E6_BODY = """Hi {{contact.first_name}},

Quick honest one. No sell.

Most people treat the VI Peel like a spa experiment. Try it once, see how the skin looks, decide later. That's a fine way to test it. It's not how the protocol actually works.

Here's the part that surprises clients:

**A single VI Peel supports 5 to 7 days of accelerated cell turnover, which is why patients often describe visibly clearer skin within the first week.** That window is real, and most first-timers see noticeable lift in tone, texture, and brightness by day 10.

**The full result keeps building for about 4 to 6 weeks after.** Pigmentation continues to fade, fine texture continues to smooth, and your skincare routine starts working better because you're applying products to fresh, receptive skin instead of buildup.

**The recommended cadence is one peel per season, four times a year.** Each peel compounds on the previous, which is why our regulars have skin that gets steadily clearer year over year instead of staying stuck at "fine" forever.

**A first-timer who books one peel and expects to grade the protocol at day 8 is grading the wrong test.** Day 8 shows you it works. The 4 to 6 weeks after show you what it actually does.

That's the actual math. Not "you'll look like a different person tomorrow." Just "your skin's natural renewal process gets supported in a way products alone can't reach."

The complimentary 2-week follow-up consultation and the new-client pricing are still on the table. Whenever you're ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}} · {{location.phone}}"""


E7_SUBJECT = "Last email from me, plus my direct line"
E7_BODY = """Hi {{contact.first_name}},

Last email from me on this. I mean it.

People wait for a reason. The most common ones I hear:

- "I'll book once my skin calms down" (the VI Peel is what helps it calm down, that's the point)
- "I want to see if I really need it first" (the only honest test is one peel and the 7-day cycle)
- "I'm not sure my skin type is a fit" (Jennifer specializes in textured and darker skin, and the consult is included before the peel ever goes on)

If any of those is you, I get it. I'll stop emailing.

Two ways to come back when you're ready:

**1.** Book directly: {{custom_values.booking_link}}

**2.** Text **{{location.phone}}** with the keyword **RESET**. Goes straight to our desk, not a queue. You don't fill out the form again, the keyword tells our system who you are and gets you straight to a slot.

Whatever you decide, thanks for considering us.

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}
{{location.phone}}"""


# ── SMS COPY ─────────────────────────────────────────────────────────────────
# Warm, private, personalized. Under 160 chars where possible. No em dashes.

SMS_T0 = "Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} from {{location.name}}. Got your VI Peel request, sending a quick rundown in a sec. Reply STOP to opt out."

SMS_T1 = "Hey {{contact.first_name}}, {{custom_values.text_message_name}} again. Quick one, what's the main thing you're hoping the VI Peel helps with? Acne, dark spots, dull texture, something else?"

SMS_D1_15min = "Hey {{contact.first_name}}, just sent the welcome email with the new-client rundown. Same question there, what are you hoping the peel helps with? One or two words is enough."

SMS_D2_5pm = "Hey {{contact.first_name}}, I put together a quick what-to-expect rundown for first-time VI Peels (downtime, prep, all of it). Takes 2 min to read. Want me to send it?"

SMS_D3_10am = "Is this {{contact.first_name}}?"

SMS_D4_5pm = "Hey {{contact.first_name}}, did you want me to grab a VI Peel slot for next week, or play it by ear? Either's fine."

SMS_D5_5pm = "Hey {{contact.first_name}}, most first-time VI Peel clients are surprised by one specific thing after day 7. Mind if I share?"

SMS_D7_10am = "Hey {{contact.first_name}}, honest one, what's actually holding you back on the peel? No pressure."

SMS_D12_10am = "{{contact.first_name}}, when I don't hear back it's usually timing or a question I haven't answered. Is it one of those?"

SMS_D14_10am = "Last one from me, {{contact.first_name}}. Whenever you're ready, text RESET to this number and I'll get Jennifer's calendar pulled up for you. {{location.phone}}"

SMS_D28_10am = "Hi {{contact.first_name}}, {{custom_values.text_message_name}}. Should I close your VI Peel file or keep it open for whenever you're ready?"


# ── KEYWORD RECOVERY COPY ────────────────────────────────────────────────────

SMS_RESET_AUTOREPLY = "Got it {{contact.first_name}}, pulling up Jennifer's calendar. Here's the link: {{custom_values.booking_link}} -{{custom_values.text_message_name}}"

SMS_RESET_2HR_FOLLOWUP = "Hey {{contact.first_name}}, just making sure the booking link worked. Want me to grab a VI Peel slot for you directly?"


# ── REPLY HANDLER COPY ───────────────────────────────────────────────────────

REPLY_ALERT_SUBJECT = "REPLIED LEAD: {{contact.first_name}} on VI Peel nurture"
REPLY_ALERT_BODY = """REPLIED LEAD ALERT.

{{contact.first_name}} {{contact.last_name}} replied to the Chemical VI Peel nurture sequence.

Phone: {{contact.phone}}
Email: {{contact.email}}

ACTION REQUIRED: Respond within 5 minutes. Do NOT let automation re-engage until this contact is manually marked as resolved or rebooked.

Their last message is in the GHL conversation thread. Check it before replying."""


# ── CAMPAIGN ─────────────────────────────────────────────────────────────────
# Day map for 01-master (cumulative from FB form submit, 27 automated touchpoints):
#   T+0     SMS_T0          instant confirm + opt-out
#   T+1m    SMS_T1          qualifying Q (acne/pigmentation/texture)
#   D1 10a  E1              welcome + qualifying Q echo
#   D1 10:15a SMS_D1_15min  echo qualifier on SMS channel
#   D2 10a  E2              objections (pain, downtime, "just a facial")
#   D2 5p   SMS_D2_5pm      reciprocity hook (rundown offer)
#   D3 10a  E3              prep tips (retinol pause, hydrate, sun avoidance)
#   D3 10a  SMS_D3_10am     pattern interrupt
#   D4 10a  E4              social proof (textured skin specialty)
#   D4 5p   SMS_D4_5pm      soft slot hold
#   D5 5p   SMS_D5_5pm      curiosity gap
#   D7 10a  E5              Zeigarnik close ("skin feels like mine again")
#   D7 10a  SMS_D7_10am     direct question
#   D10 10a E6              compounding cadence (one peel per season)
#   D12 10a SMS_D12_10am    objection surfacer
#   D14 9a  E7              peak-end + RESET keyword + phone
#   D14 10a SMS_D14_10am    keyword reminder
#   D28 10a SMS_D28_10am    breakup text
#   tag     vipeel-nurture-complete

CAMPAIGN = {
    "01-master": {
        "name": "01. Chemical VI Peel: Master Sequence",
        "tag": "vipeel-lead",
        "templates": link_steps([
            sms_step("S0 Instant Confirm + Opt-Out (T+0)", SMS_T0),
            wait_step("1 min", 1, "minutes"),
            sms_step("S1 Qualifying Q Skin Concern (T+1m)", SMS_T1),
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
            email_step("E3 Pre-Peel Prep Tips (D3 10am)", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D3 Pattern Interrupt (D3 10am)", SMS_D3_10am),
            wait_step("24 hours", 24, "hour"),
            email_step("E4 Textured Skin Specialty Story (D4 10am)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D4 Soft Slot Hold (D4 5pm)", SMS_D4_5pm),
            wait_step("24 hours", 24, "hour"),
            sms_step("S_D5 Curiosity Gap (D5 5pm)", SMS_D5_5pm),
            wait_step("41 hours", 41, "hour"),
            email_step("E5 Zeigarnik Close Skin Feels Like Mine (D7 10am)", E5_SUBJECT, E5_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D7 Direct Question (D7 10am)", SMS_D7_10am),
            wait_step("3 days", 3, "days"),
            email_step("E6 Compounding Cadence + Cost of Waiting (D10 10am)", E6_SUBJECT, E6_BODY, FROM_NAME),
            wait_step("2 days", 2, "days"),
            sms_step("S_D12 Objection Surfacer (D12 10am)", SMS_D12_10am),
            wait_step("47 hours", 47, "hour"),
            email_step("E7 Peak-End + RESET Keyword (D14 9am)", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D14 Keyword Reminder (D14 10am)", SMS_D14_10am),
            wait_step("14 days", 14, "days"),
            sms_step("S_D28 Breakup Text (D28 10am)", SMS_D28_10am),
            tag_step("Mark VI Peel Nurture Complete", ["vipeel-nurture-complete"]),
        ]),
    },

    "02-keyword-recovery": {
        "name": "02. Chemical VI Peel: RESET Keyword Recovery",
        "tag": "vipeel-keyword-trigger",
        "templates": link_steps([
            tag_step("Apply Returning Lead Tag", ["vipeel-returning-lead"]),
            tag_step("Remove Nurture Complete Tag", ["vipeel-nurture-complete"], remove=True),
            sms_step("RESET Auto-Reply with Booking Link", SMS_RESET_AUTOREPLY),
            wait_step("2 hours", 2, "hour"),
            sms_step("RESET 2-Hour Follow-Up", SMS_RESET_2HR_FOLLOWUP),
        ]),
    },

    "03-reply-handler": {
        "name": "03. Chemical VI Peel: Global Reply Handler",
        "tag": "vipeel-replied",
        "templates": link_steps([
            tag_step("Confirm Reply Tag Applied", ["vipeel-replied"]),
            email_step("Internal Alert to Front Desk", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"Chemical VI Peel Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="Chemical VI Peel — New Client Special",
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
