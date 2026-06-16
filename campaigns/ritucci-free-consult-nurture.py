#!/usr/bin/env python3
"""
Ritucci Regenerative Medicine — Free Consultation — Non-Surgical Joint Pain Relief nurture sequence.

Generated: 2026-05-06 (full copy populated by /build-sequence)
Voice rebuild: 2026-06-12 — rewrote all touchpoints into a warm, empathy-first,
  conversational intake voice (set by the new D0 SMS). Persona speaks as
  {{custom_values.text_message_name}}; Dr. Ritucci is referred to in the third
  person. Dropped the old "candidacy filter / no pitch" hard edge; kept the
  honest "we'll tell you straight" candidacy gating for compliance. Email bodies
  use single newlines between sections (each renders as a margin-spaced paragraph).

Source offer: offers/ritucci-free-consult.md
Source client: clients/ritucci/overview.md

Sequence: 27 touchpoints across 28 days (Day 5 deadline email DROPPED — has_deadline=False).
Trigger: Facebook Lead Form submit applies tag `ritucci-free-consult-lead`.

Shape decisions applied (from offer frontmatter):
  - Has Deadline=No → DROP V2 Day 5 deadline email · D5 5pm SMS becomes curiosity hook · 28→27 touchpoints
  - Before Afters=No / images_available=No → no MMS, no photo references
  - Doctor Video=Yes → video drop-in available in D4A email (link manually inserted post-deploy)
  - Deposit Required=No → no deposit-hold flow, no card-on-file language
  - Uses Bot=No → bot prompt generated as future-state doc only (not deployed)
  - Niche=Regenerative → no "cures/heals/regrows/reverses"; candidacy-gated language; no published pricing

Tag namespace: ritucci-free-consult-* (prefixed to avoid collision with Ultra offer's MOVE namespace).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, link_steps,
)

# ── Constants (sourced from clients/ritucci/overview.md frontmatter) ──────────

LOCATION_ID = "gasmmKGJL9bP7ruM49bh"
COMPANY_ID  = "KKPPvB49R6ZQWMQr0OF9"
USER_ID     = "ELplzcqBW6cymI3mOd0J"
PARENT_FOLDER = ""

FROM_NAME = "{{custom_values.text_message_name}}"

# Booking link is a custom value (resolved by GHL at send time — never hardcode)
BOOKING_LINK = "{{custom_values.booking_link}}"

# Offer constants
OFFER_NAME    = "Free Consultation — Non-Surgical Joint Pain Relief"
OFFER_KEYWORD = "CONSULT"

# Notion offer page (engine ticks "28 Day Nurture Sequence Built" on full success)
NOTION_PAGE_ID = "34f728795ff081058d2cd23fff7d2184"

# Tag namespace (one offer's tag must NEVER collide with another's)
TAG_LEAD              = "ritucci-free-consult-lead"
TAG_KEYWORD_TRIGGER   = "ritucci-free-consult-keyword-trigger"
TAG_RETURNING_LEAD    = "ritucci-free-consult-returning-lead"
TAG_NURTURE_COMPLETE  = "ritucci-free-consult-nurture-complete"
TAG_REPLIED           = "ritucci-free-consult-replied"
TAG_SYMPTOM_DRIVEN    = "ritucci-free-consult-symptom-driven"
TAG_CURIOUS           = "ritucci-free-consult-curious"


# ── Email + SMS copy ──────────────────────────────────────────────────────────

# D0 T+0 confirmation SMS (auto-fires on form submit, before tag step delay)
# Initial intro — supplied verbatim; STOP footer appended for A2P first-contact compliance.
SMS_D0_CONFIRM = (
    "Hey {{contact.first_name}}, thanks for reaching out! Pain can make even normal "
    "days feel harder than they should. Our goal at Ritucci Medicine is to help you "
    "get relief, move better, and get back to the parts of life you've been missing. "
    "Reply STOP to opt out."
)

# D0 T+1 qualifier SMS (text-only — no MMS, images_available=False)
# Automated personal follow-up — supplied copy, one broken clause lightly cleaned.
SMS_D0_T1 = (
    "Hey {{contact.first_name}}, this is {{custom_values.text_message_name}}. To "
    "better understand what's going on, where is the pain located? Is it your neck, "
    "back, or somewhere else? And what have you done about it so far?"
)

# ── Day 1 — Welcome + qualifier ──
E1_SUBJECT = "let's figure out what's going on with your pain"
E1_PREVIEW = "a 30-minute conversation with the doctor - no pressure"
E1_BODY = """Hey {{contact.first_name}},
Thanks again for reaching out. I know living with joint or spine pain wears on you - not just physically, but in all the little things you quietly stop doing because they're not worth the ache afterward.
I wanted to reach out personally, because the first step here is simple: a 30-minute conversation with Dr. Ritucci, on the phone or video. Here's what that looks like:
- We talk through where your pain is and how long it's been going on
- We look at your imaging together (X-ray or MRI) if you have it
- You get an honest read on whether our non-surgical regenerative approach could be a fit for you
That's it. No pressure and no hard sell. If it isn't the right path for you, we'll tell you straight.
One thing that helps me point you in the right direction: where is the pain showing up most, and what have you already tried? Just reply here - I read these myself.
[See Available Times]
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

SMS_D1 = (
    "Hey {{contact.first_name}}, it's {{custom_values.text_message_name}} from Ritucci. "
    "Just following up - where's the pain hitting you most, and how long has it been "
    "going on? Even a quick reply helps me point you in the right direction."
)

# ── Day 2 — Objections + Zeigarnik open ──
E2_SUBJECT = "the questions most people ask us first"
E2_PREVIEW = "will it help, is it covered, how is it different - honest answers"
E2_BODY = """Hey {{contact.first_name}},
When people reach out about non-surgical options for joint or spine pain, a few questions come up almost every time. I want to answer them up front so you know exactly what you'd be walking into.
**"Will this actually help me?"**
Honest answer: it depends on your situation. Dr. Ritucci uses ultrasound-guided regenerative treatments designed to support your body's own repair process. A lot of patients get meaningful relief and move better - but we won't promise an outcome before we've looked at your case. That's what the consult is for. We look first, then tell you straight whether it's worth pursuing.
**"Is it covered by insurance?"**
The consult itself is free. The treatments that may follow usually aren't covered yet - regenerative care is still a newer category. We're upfront about all of that on the call so nothing catches you off guard.
**"How is this different from a cortisone shot?"**
Cortisone quiets inflammation for a while. The approaches we use are aimed at supporting the tissue itself, not just turning down the volume on the pain. Different idea, different timeline.
The honest truth is the consult exists to figure out whether we can actually help you - not to talk you into anything. If we're not the right fit, you'll know quickly.
[See Available Times]
A few days from now I'll share the one thing patients tell us most often at the end of these calls - it stuck with me.
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

SMS_D2_5PM = (
    "Hey {{contact.first_name}}, want me to send over a simple 1-page guide on what to "
    "bring to your consult so you get the most out of it? Just reply YES."
)

# ── Day 3 — Quick-win, no sell ──
E3_SUBJECT = "4 things worth doing before any pain consult (mine or anyone else's)"
E3_PREVIEW = "quick wins - useful even if you never call us"
E3_BODY = """Hey {{contact.first_name}},
No pitch in this one. If you're going to talk to anyone about chronic joint or spine pain - us or another clinic - these four things make that conversation far more useful:
1. Have your imaging handy. An X-ray or MRI report, even a phone photo of it, saves a lot of guesswork.
2. Notice what's changed in the last few months. "It hurts" is a start, but "I used to walk 30 minutes, now I stop at 10" tells us much more.
3. Make a quick list of what you've already tried - physical therapy, cortisone, anti-inflammatories, other clinics - and how long any relief lasted.
4. Give yourself the full 30 minutes. Most people think the imaging is the important part. Honestly, your questions are.
Use it anywhere, with anyone.
P.S. If you'd like to use it with us: {{custom_values.booking_link}}
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

SMS_D3 = (
    "Hey {{contact.first_name}}, real quick - what's the one thing that's been holding "
    "you back from booking? No pressure, I'm just curious."
)

# ── Day 4 — Branched social proof (Variant A in master WF) ──
E4A_SUBJECT = "a patient who was weeks away from surgery"
E4A_PREVIEW = "what changed after one conversation - and what didn't"
E4A_BODY = """Hey {{contact.first_name}},
I want to share a story, because it might sound familiar.
A patient came to us last fall with knee pain. He'd been told he needed a partial replacement, and surgery was already on the calendar. His daughter found us late one night searching for non-surgical options.
On his consult, Dr. Ritucci went through his MRI with him. There was wear, but enough healthy structure that he was a good candidate for our approach. He chose to hold off on surgery, went through the treatment plan, and he's back to his weekend hikes.
Here's the part I want you to hear, though: we've had other patients sit through the same consult and hear the opposite - that surgery was the better path for them, and we said so. The point of the call is to give you a real answer either way.
If you'd like that answer for your situation:
[See Available Times]
Not ready to book? Just reply with where your pain is and how long it's been going on, and I'll tell you whether the consult is even worth your time.
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

# Variant B (non-openers of D1/D2) — currently queued for future split into sub-workflows
# per skeleton spec line 92. Master WF runs Variant A only at this stage.
E4B_SUBJECT = "still thinking about the consult?"
E4B_PREVIEW = "30 minutes, no pressure, a real answer"
E4B_BODY = """Hey {{contact.first_name}},
Just a quick note in case my last few emails got buried.
The free 30-minute consult is still open whenever you want it. You share where your pain is and what you've tried, Dr. Ritucci looks at your situation, and you walk away knowing whether our non-surgical approach could be a fit. That's the whole thing.
[See Available Times]
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

SMS_D4_5PM = (
    "Hey {{contact.first_name}}, I know I've sent a few notes - want me to keep it to "
    "text only? Just reply TEXT and I'll ease off the emails."
)

# ── Day 5 — Curiosity SMS only (deadline email DROPPED — has_deadline=False) ──
SMS_D5_5PM = (
    "Hey {{contact.first_name}}, something that surprises a lot of people - the consult "
    "is just as much about ruling things out as ruling them in. Reply 1 if you'd like "
    "me to explain why that actually works in your favor."
)

# ── Day 7 — Re-engagement (closes D2 Zeigarnik) ──
E7A_SUBJECT = "the thing patients tell us most often"
E7A_PREVIEW = "it wasn't what I expected"
E7A_BODY = """Hey {{contact.first_name}},
A while back I said I'd share the thing patients tell us most often at the end of these consults. Here it is.
More than anything else, what we hear is: "I wish I'd had this conversation a year ago."
Not "thanks for fixing me." Just regret about how long they waited to get a clear answer.
What gets me about that is the consult is free. No commitment, no card on file, nothing owed if you decide not to move forward. The only cost is 30 minutes. And still, most people sit on it for months.
I'm not going to tell you now is your moment - only you know that. But if it's been on your mind and you want a low-pressure next step:
Just reply with where the pain is and how long it's been going on. I'll tell you honestly whether the consult is even worth your time.
[See Available Times]
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

# Variant B for D7 (queued for sub-workflow split)
E7B_SUBJECT = "still here whenever you want to talk it through"
E7B_PREVIEW = "30 min, your questions, an honest answer"
E7B_BODY = """Hey {{contact.first_name}},
Just keeping the door open. The free 30-minute consult is still on the table - you tell us where the pain is and what you've tried, we look at it together, and you leave with an honest read on whether it's worth pursuing.
[See Available Times]
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

SMS_D7 = (
    "Hey {{contact.first_name}}, quick question - if a 30-min call with the doctor "
    "could tell you whether non-surgical relief is realistic for your joint, would "
    "that be helpful right now? Yes or no is totally fine."
)

# ── Day 10 — Logic + cost of inaction ──
E10_SUBJECT = "what usually happens when we wait on joint pain"
E10_PREVIEW = "not to worry you - just the honest pattern"
E10_BODY = """Hey {{contact.first_name}},
I want to talk through what tends to happen when joint or spine pain gets put on the back burner - not to worry you, just because it's worth knowing.
When pain has been steady or slowly getting worse, the next several months without any change usually look like this:
- You start favoring the joint, which puts strain on the ones around it
- You move less - less walking, less activity, less of what kept you going
- You lean more on anti-inflammatories or cortisone, which calm things down but don't address what's underneath
- Surgery becomes a more likely conversation, not a less likely one
I'm not saying our approach is automatically the answer for you - the consult is what tells us that. But "wait and see" usually isn't a neutral choice. The joint keeps changing while you decide.
If 30 minutes to find out where you really stand sounds worth it:
[See Available Times]
And if now's still not the time, just reply and tell me what's holding you back. I'll either help you with it or tell you straight if I can't.
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

# ── Day 12 — Objection surfacer SMS ──
SMS_D12 = (
    "Hey {{contact.first_name}}, if you came in for the consult and it went exactly "
    "how you'd hope, what would that look like for you? Reply with the joint and what "
    "you're hoping to get back to."
)

# ── Day 14 — Peak-end + KEYWORD plant ──
E14_SUBJECT = "my last email - plus a direct way back"
E14_PREVIEW = "no button, no pitch - just an open door"
E14_BODY = """Hey {{contact.first_name}},
This is the last email I'll send for now, and I want to be honest about why people wait, because the reasons are usually real:
- "I want to see how it feels in another month" - fair, your body will tell you
- "I've spent money on things that didn't work and I'm cautious now" - completely understandable, and it's exactly why the consult is free
- "I'm hoping insurance changes" - it likely won't for this kind of care, but we can talk it through
- "I just haven't gotten to it" - the most common one, and no judgment at all
If any of those sound like you, here's what I want you to have:
Our number is {{location.phone}} - you can call us directly anytime. Or, if you'd rather skip the form and the back-and-forth, just text the word CONSULT to that number whenever you're ready. It picks right back up and gets you on the calendar.
That's it. The door stays open as long as you need it to.
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}"""

SMS_D14 = (
    "Hey {{contact.first_name}}, last note from me for now. Whenever you're ready, just "
    "reply CONSULT to this number and I'll get you on the calendar - no need to fill "
    "anything out again. Take care of yourself."
)

# ── Day 28 — Breakup SMS ──
SMS_D28 = (
    "Hey {{contact.first_name}}, last message from me. If the timing isn't right, "
    "that's completely okay - the door stays open. Just text CONSULT anytime to pick "
    "it back up. Until then, take care."
)

# ── Keyword recovery responses ──
SMS_KEYWORD_AUTOREPLY = (
    "Hey {{contact.first_name}}, so glad you reached back out. Here's the booking link "
    "- grab whatever slot works for you: {{custom_values.booking_link}} . Or reply and "
    "I'll find a time for you."
)

SMS_KEYWORD_2HR_FOLLOWUP = (
    "Hey {{contact.first_name}}, just checking the booking link worked okay? If you'd "
    "rather I send a few specific times, reply with what's easier - weekday or weekend, "
    "morning or afternoon."
)

# ── Reply handler internal alert ──
REPLY_ALERT_SUBJECT = "Reply received - Free Consultation lead"
REPLY_ALERT_BODY = """A free-consult lead just replied to the nurture sequence.
Contact: {{contact.first_name}} {{contact.last_name}}
Phone: {{contact.phone}}
Email: {{contact.email}}
Reply: {{message.body}}
Action: Respond within 15 min during business hours. If they're sharing pain location or history, acknowledge it personally and offer to book. If they want to book, send the booking link or warm-transfer. If they're ruling themselves out (insurance, out of area, surgery already scheduled), log the reason and tag them out.
- Sequence: Free Consultation - Non-Surgical Joint Pain Relief"""


# ── Workflows ──────────────────────────────────────────────────────────────────

CAMPAIGN = {
    "01-master": {
        "name": "01. Free Consultation — Non-Surgical Joint Pain Relief — Master Nurture (v2 2026-06-12)",
        # Trigger: Facebook Lead Form Submitted. Replace TODO_FB_PAGE_ID with the
        # real Ritucci FB page ID after launch. Add "fb_form_id" to filter to a
        # specific form, or omit both for any-page/any-form.
        "trigger": {
            "type": "facebook_lead_gen",
            "fb_page_id": "TODO_FB_PAGE_ID",
            "name": "Facebook Lead Form Submitted",
        },
        "templates": link_steps([
            tag_step("Tag: lead", [TAG_LEAD]),
            sms_step("D0 T+0 confirm SMS", SMS_D0_CONFIRM),
            wait_step("Wait 1 min", 1, "minute"),
            sms_step("D0 T+1 qualifier SMS", SMS_D0_T1),

            wait_step("Wait to D1 10am", 1, "day"),
            email_step("D1 welcome email", E1_SUBJECT, E1_BODY, FROM_NAME),
            wait_step("Wait 15 min", 15, "minute"),
            sms_step("D1 echo qualifier SMS", SMS_D1),

            wait_step("Wait to D2 10am", 1, "day"),
            email_step("D2 objections email", E2_SUBJECT, E2_BODY, FROM_NAME),
            wait_step("Wait to D2 5pm", 7, "hour"),
            sms_step("D2 5pm reciprocity SMS", SMS_D2_5PM),

            wait_step("Wait to D3 10am", 17, "hour"),
            email_step("D3 quick-win email", E3_SUBJECT, E3_BODY, FROM_NAME),
            sms_step("D3 pattern interrupt SMS", SMS_D3),

            wait_step("Wait to D4 10am", 1, "day"),
            email_step("D4 social proof email (A)", E4A_SUBJECT, E4A_BODY, FROM_NAME),
            wait_step("Wait to D4 5pm", 7, "hour"),
            sms_step("D4 5pm escalated SMS", SMS_D4_5PM),

            wait_step("Wait to D5 5pm", 1, "day"),
            sms_step("D5 5pm curiosity SMS", SMS_D5_5PM),

            wait_step("Wait to D7 10am", 2, "day"),
            email_step("D7 Zeigarnik close email", E7A_SUBJECT, E7A_BODY, FROM_NAME),
            sms_step("D7 direct question SMS", SMS_D7),

            wait_step("Wait to D10 10am", 3, "day"),
            email_step("D10 logic email", E10_SUBJECT, E10_BODY, FROM_NAME),

            wait_step("Wait to D12 10am", 2, "day"),
            sms_step("D12 objection surfacer SMS", SMS_D12),

            wait_step("Wait to D14 9am", 2, "day"),
            email_step("D14 peak-end email", E14_SUBJECT, E14_BODY, FROM_NAME),
            wait_step("Wait 1 hour", 1, "hour"),
            sms_step("D14 keyword plant SMS", SMS_D14),

            wait_step("Wait to D28", 14, "day"),
            sms_step("D28 breakup SMS", SMS_D28),
            tag_step("Mark nurture complete", [TAG_NURTURE_COMPLETE]),
        ]),
    },

    "02-keyword-recovery": {
        "name": "02. Free Consultation — Non-Surgical Joint Pain Relief — CONSULT Keyword Recovery (v2 2026-06-12)",
        # Trigger: Customer replied to WF-01 with the keyword "CONSULT".
        # Engine resolves source_wf_key → wf_id of "01-master" automatically.
        "trigger": {
            "type": "customer_reply",
            "source_wf_key": "01-master",
            "keyword": "CONSULT",
        },
        "templates": link_steps([
            tag_step("Apply returning lead tag", [TAG_RETURNING_LEAD]),
            tag_step("Remove nurture-complete", [TAG_NURTURE_COMPLETE], remove=True),
            sms_step("Keyword auto-reply", SMS_KEYWORD_AUTOREPLY),
            wait_step("Wait 2 hours", 2, "hour"),
            sms_step("2-hour follow-up", SMS_KEYWORD_2HR_FOLLOWUP),
        ]),
    },

    "03-reply-handler": {
        "name": "03. Free Consultation — Non-Surgical Joint Pain Relief — Global Reply Handler (v2 2026-06-12)",
        # Trigger: Customer replied to WF-01 (any reply, no keyword filter).
        "trigger": {
            "type": "customer_reply",
            "source_wf_key": "01-master",
        },
        "templates": link_steps([
            tag_step("Confirm reply tag", [TAG_REPLIED]),
            email_step("Internal alert", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── Run ────────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"Free Consultation — Non-Surgical Joint Pain Relief Nurture: "
          f"{len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

    token_mgr = TokenManager(LOCATION_ID)
    if os.environ.get("GHL_FIREBASE_REFRESH_TOKEN"):
        token_mgr.set_refresh_token(os.environ["GHL_FIREBASE_REFRESH_TOKEN"])

    client = GHLClient(token_mgr, LOCATION_ID)

    print("Testing auth...")
    test = client.request("GET", f"/workflow/{LOCATION_ID}/list?parentId=root&limit=1")
    if not test:
        print("Auth failed — check your token.")
        sys.exit(1)
    print("Auth OK\n")

    builder = CampaignBuilder(client, LOCATION_ID)
    stats = builder.build(
        CAMPAIGN,
        folder_name="Free Consultation — Non-Surgical Joint Pain Relief Nurture (v2 2026-06-12)",
        parent_folder=PARENT_FOLDER or None,
        company_id=COMPANY_ID,
        user_id=USER_ID,
        notion_page_id=NOTION_PAGE_ID or None,
    )

    if stats["steps_saved"] == total_steps:
        print(f"\nAll {total_steps} steps saved!")
    else:
        print(f"\nWARNING: Expected {total_steps}, saved {stats['steps_saved']}")


if __name__ == "__main__":
    main()
