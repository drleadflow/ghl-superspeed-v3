#!/usr/bin/env python3
"""
Ritucci Regenerative Medicine — Ultra Regenerative Package nurture sequence.

Generated: 2026-05-06 (populated by /build-sequence)
Source offer:  offers/ritucci-ultra-regenerative.md
Source client: clients/ritucci/overview.md
QA report:     clients/ritucci/ultra-regenerative-sequence-qa.md
Manual ops:    clients/ritucci/ultra-regenerative-manual-touchpoints.md
AI bot prompt: clients/ritucci/ultra-regenerative-ai-bot-prompt.md

Trigger: Facebook Lead Form Submitted (Ultra Regenerative ad).
Has Deadline = No → 27 automated touchpoints (Day 5 deadline email dropped).

Compliance constraints baked into every piece of copy:
  - No "cures / heals / regrows / reverses / fixes" claims
  - No published pricing in any prospect-facing copy
  - $100 no-show fee is INTERNAL POLICY — NEVER surfaced
  - No before/after photos (images_available=false), no doctor video (still to be filmed)
  - Real testimonials only; composite/example patients are unnamed
  - Candidacy-gated language ("if you're a candidate", "depending on evaluation")
  - PRP / BMAC / A2M described as minimally manipulated autologous biologics

Token rules:
  - {{custom_values.booking_link}} and {{custom_values.text_message_name}} stay as runtime tokens
  - Tag namespace: ritucci-ultra-regenerative-* (NEVER bare lead/replied/booked)
  - Free Consult offer uses ritucci-free-consult-* — must not collide

Pre-deploy human action (see QA report Section C):
  1. Set GHL custom value `text_message_name` for location gasmmKGJL9bP7ruM49bh
     (Ultra uses a bot persona — NOT "Steven Ritucci Jr.")
  2. Set GHL custom value `booking_link` for the Ultra-package calendar URL
  3. Replace TODO_FB_PAGE_ID below with the real Facebook page ID
     (GET /integrations/facebook/{loc}/trigger/pages once connected)
  4. Paste ultra-regenerative-ai-bot-prompt.md into GHL Conversation AI
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

FROM_NAME    = "{{custom_values.text_message_name}}"
BOOKING_LINK = "{{custom_values.booking_link}}"

OFFER_NAME    = "Ultra Regenerative Package"
OFFER_PRICE   = "consult-determined"  # NEVER quote a number in copy
OFFER_KEYWORD = "MOVE"

NOTION_PAGE_ID = "355728795ff081139b6ce2479ac60b1d"

# Tag namespace — every tag prefixed with the offer slug
TAG_LEAD             = "ritucci-ultra-regenerative-lead"
TAG_KEYWORD_TRIGGER  = "ritucci-ultra-regenerative-keyword-trigger"
TAG_RETURNING_LEAD   = "ritucci-ultra-regenerative-returning-lead"
TAG_NURTURE_COMPLETE = "ritucci-ultra-regenerative-nurture-complete"
TAG_REPLIED          = "ritucci-ultra-regenerative-replied"


# ── Touchpoint copy ───────────────────────────────────────────────────────────

# D0 T+1 — Qualifier SMS (text-only, no MMS — images_available=false)
SMS_D0_T1 = (
    "Hey {{contact.first_name}}, this is {{custom_values.text_message_name}} from "
    "Ritucci Regenerative Medicine. Got your request — quick question so I can "
    "send the right info: reply 'surgery' if you've been told surgery may be "
    "your next step, or 'pain' if you're managing chronic flare-ups and want "
    "to avoid getting there. Reply STOP to opt out."
)

# ── D1 ──
E1_SUBJECT = "is non-surgical regeneration actually an option for your joint?"
E1_PREVIEW = "Quick rundown of the protocol + one segmenting question before I send anything else"
E1_BODY = """Hey {{contact.first_name}},

{{custom_values.text_message_name}} here from Ritucci Regenerative Medicine in Norwood. You reached out about non-surgical options for chronic joint pain — thanks for raising your hand.

Before I send you anything else, here's the quick version of what we do, in three lines:

- An 8–12 week customized protocol — not a single PRP injection like most clinics offer
- Layered therapies (PRP, A2M, bone marrow concentrate, focused shockwave) chosen per joint
- Every procedure ultrasound-guided by Dr. Ritucci — a double-board-certified physician

One question before I send the next email so I send the right thing:

**Have you been told surgery is the next step, or are you trying to get ahead of it before it gets there?**

If you'd rather just see what's open, here's Dr. Ritucci's 15-min candidacy consult — he'll tell you up front whether you're a fit:

[See Available Times]

Not ready to book? Reply with your biggest question and I'll answer it personally.

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}
"""

SMS_D1 = (
    "Hey {{contact.first_name}} — {{custom_values.text_message_name}} from Ritucci. "
    "Quick one to match the email: surgery on the table, or trying to avoid "
    "getting there? Reply 'surgery' or 'pain' and I'll send the right info."
)

# ── D2 ──
E2_SUBJECT = "the 3 things people actually worry about with regenerative protocols"
E2_PREVIEW = "Cost, whether it'll work for you, and one honest tradeoff most clinics won't mention"
E2_BODY = """{{contact.first_name}},

When patients reach out about the Ultra protocol, three concerns come up almost every time. Worth handling them up front instead of dancing around them.

**1. "It's expensive — I'm not sure it's worth it."**

Fair. The Ultra package isn't a $1,700 single-injection PRP — it's a multi-phase plan, customized to the joint and severity. Pricing's set on the consult because the protocol layers vary per case. We have payment plans and financing so the math is workable for most patients. The 15-minute consult is free, so you see the number before deciding.

**2. "What if it doesn't work for me?"**

Honest answer: not every joint is a candidate. Severe end-stage cartilage loss isn't something a regenerative protocol fixes. That's why every patient gets a candidacy review first — Dr. Ritucci tells you up front if it's not a fit and points you to a better path. The plan also re-tunes if you're not progressing as expected, so no one stays stuck on a protocol that isn't working.

**3. "I need time to think — or to talk to my spouse."**

Totally normal. Bring your spouse to the 15-min consult. Most patients do.

Now the part most clinics don't mention. The bone marrow aspiration step is brief, but the harvest site (your hip) is sore for 2–3 days afterward. Most patients are back to desk work the next day, but you're not running stairs that weekend. That's a real tradeoff — worth knowing before you commit.

If you want to see Dr. Ritucci's 15-min consult and get the candidacy review:

[See Available Times]

One more thing — there's a weird thing patients say in week 4 of the protocol that surprises us every time. I'll share it in a few days.

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}
"""

SMS_D2_5PM = (
    "{{contact.first_name}}, want me to text you a 1-page rundown of the "
    "4-therapy protocol so you know what's actually involved before any "
    "consult? Reply 'yes' and I'll send."
)

# ── D3 ──
E3_SUBJECT = "4 things to do before any regenerative consult (no pitch in this one)"
E3_PREVIEW = "Pure prep — these make every protocol work better whether you book with us or someone else"
E3_BODY = """{{contact.first_name}},

No pitch in this email. Just four things that meaningfully improve any regenerative consult — whether you book with us, with another clinic, or just want to be ready for when the timing's right.

1. Bring imaging if you have it. X-ray or MRI of the joint speeds up the candidacy review by 10x. If you don't have any, that's fine — Dr. Ritucci does an ultrasound-guided exam at the consult.

2. Hydrate well the 48 hours before. Better blood draw, better PRP yield. Not optional if you want the protocol to work the way it's designed to.

3. Skip NSAIDs (ibuprofen, Aleve) for 7 days before any procedure. They blunt the inflammatory cascade that the regenerative response relies on. Most clinics forget to tell you this.

4. Plan a 2–3 day light schedule after the procedure. The injections themselves are quick, but the harvest site needs a couple of low-activity days to settle.

That's it. File this away.

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}

P.S. If you do want to grab the 15-min consult: [{{custom_values.booking_link}}]({{custom_values.booking_link}})
"""

SMS_D3 = (
    "Quick one, {{contact.first_name}} — what's the one daily activity your "
    "joint pain interferes with most? Stairs, sleep, walking, exercise, "
    "something else? Trying to get the picture for Dr. Ritucci's review."
)

# ── D4 — Variant A (surgery-avoider segment / openers + clickers) ──
E4A_SUBJECT = "the patient who told me he'd already scheduled the surgery"
E4A_PREVIEW = "Sometimes the timeline tightens up — here's how that played out for one patient last year"
E4A_BODY = """{{contact.first_name}},

A patient came in last year — early 60s, knee pain for almost two years, told by his orthopedist he was looking at a knee replacement. He'd already scheduled the surgery for three months out.

He came to Dr. Ritucci's consult mostly to "be sure he'd exhausted everything" before going under.

Imaging review showed he was a candidate. Dr. Ritucci was honest with him: the protocol may help reduce pain and improve function, but it wasn't a guaranteed alternative — it depended on how his joint responded over the 8–12 weeks.

He decided to try it before the surgery date.

Eight weeks in, he told us something I think about a lot: "I forgot I had the surgery scheduled."

That's not a guarantee for anyone reading this — every joint is different, and outcomes depend on candidacy and severity. But it's the kind of case that's why Dr. Ritucci built the protocol.

Want me to send one more story I think matches your case? Reply 'story' and I'll send.

Or if you want to see whether you're a candidate yourself:

[See Available Times]

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}
"""

# ── D4 — Variant B (flare-up-pain segment / non-openers — short re-subject) ──
E4B_SUBJECT = "still here if the joint pain's still there"
E4B_PREVIEW = "Short note in case the previous emails got buried"
E4B_BODY = """{{contact.first_name}},

Quick one — sending a short version since the longer emails this week may have gotten buried.

If you're still dealing with chronic joint pain and curious whether you're a candidate for a regenerative protocol (PRP + bone marrow concentrate + A2M + focused shockwave, customized over 8–12 weeks), Dr. Ritucci's 15-min candidacy consult is the next step.

He tells you honestly whether you're a fit. If you're not, he'll point you to a better path.

[See Available Times]

Reply 'story' if you want one more patient case before you decide.

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}
"""

SMS_D4_5PM = (
    "{{contact.first_name}} — I know I've been emailing. If it's annoying, "
    "just reply 'less' and I'll switch to text-only. Or 'story' and I'll send "
    "one more patient case I think matches yours."
)

# ── D5 — 5pm SMS (curiosity gap; deadline email DROPPED — has_deadline=false) ──
SMS_D5_5PM = (
    "{{contact.first_name}}, weird question: what's the one thing you'd be "
    "doing right now if your joint didn't hurt? Just curious — not selling."
)

# ── D7 — Variant A (closes the D2 Zeigarnik loop) ──
E7A_SUBJECT = "remember when I said there's a weird thing patients say in week 4?"
E7A_PREVIEW = "Closing the loop from earlier this week — and one realistic ask"
E7A_BODY = """{{contact.first_name}},

I owe you the close from earlier this week — I said there's a thing patients say around week 4 of the protocol that surprises us every time.

Here it is.

The most common version is some flavor of: "I wish I'd done this sooner."

Not "this fixed me" — most patients don't talk that way after week 4 because the protocol's still running. It's the looking-back-at-the-last-two-years-of-trying-everything-else feeling. Every cortisone shot, every round of PT, every "let's wait and see" appointment.

The reason I think it's worth sharing isn't to push you. It's that it's the same regret pattern most patients describe before they book — they just describe it about waiting too long, not waiting too short.

So one direct ask: what's the one thing keeping you from booking the candidacy consult? Reply with the answer — even one word — and I'll respond honestly. If it's a fit, I'll show you the next step. If not, I'll tell you and stop emailing.

Or if you want to skip the email and go straight to the 15-min consult:

[See Available Times]

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}
"""

# ── D7 — Variant B (non-openers — direct restate) ──
E7B_SUBJECT = "one direct question for you"
E7B_PREVIEW = "If you're done thinking about this, fine — just want to know"
E7B_BODY = """{{contact.first_name}},

One direct question.

What's the one thing keeping you from booking the 15-min consult to see if you're a candidate for the regenerative protocol?

Reply with the answer — cost, timing, "not sure it'll work", "talking to my spouse", or "not the right time" all count. I'll respond honestly. If it's a fit I'll show you the next step. If not, I'll stop emailing.

Or just grab a slot:

[See Available Times]

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}
"""

SMS_D7 = (
    "{{contact.first_name}}, one direct question — what's the actual reason "
    "you haven't booked the 15-min consult yet? Cost, timing, doubt, or "
    "something else? I'll answer honestly."
)

# ── D10 — Logic + cost-of-inaction email ──
E10_SUBJECT = "the math most patients don't do until it's too late"
E10_PREVIEW = "Not financial math — joint math. Worth 60 seconds."
E10_BODY = """{{contact.first_name}},

There's a math problem most chronic-pain patients don't run until it's too late. It goes like this.

The longer a degenerating joint stays untreated, the more compensation patterns build up — your other knee, your hips, your lower back start absorbing the load. By the time you get to surgery, you're not just rehabbing one joint — you're untangling years of compensation.

That's not a scare tactic. It's the reason "wait and see" is the most expensive option for chronic joint pain. Not in dollars. In the additional joints that quietly take on damage while the original one keeps degenerating.

The Ultra protocol is designed to support function and may help reduce pain in candidates whose joint is still in the regenerative window. That window narrows over time.

Whether the answer is our protocol, surgery, or something else entirely, the action that has the lowest cost is the candidacy review — 15 minutes, free, and you walk out knowing whether you're in the window or not.

[See Available Times]

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}
"""

# ── D12 — Objection surfacer SMS ──
SMS_D12 = (
    "{{contact.first_name}}, real question — what's the actual reason you "
    "haven't booked yet? Cost, timing, not sure it'll work, or something "
    "else? Whatever it is, I can probably answer it."
)

# ── D14 — Peak-end email + KEYWORD plant ──
E14_SUBJECT = "Last email from me — plus my direct line"
E14_PREVIEW = "Wrapping up. Real reasons people wait, plus how to skip the line if you come back later."
E14_BODY = """{{contact.first_name}},

This is the last email from me on the Ultra Regenerative Package.

Looking back at every patient who didn't book within their first two weeks, the real reasons usually fall into one of these:

- Pain wasn't bad enough yet to justify the time/cost
- Spouse needed to see the candidacy review before agreeing
- Wanted to try one more conservative thing first
- Already on a surgery track and felt locked in
- Just plain too much going on right now

All of those are honest reasons. None of them mean the door's closed.

Two ways to come back when timing's right.

1. Call us directly: {{location.phone}}. Ask for a 15-min candidacy consult — say you got my emails and want to skip the re-intake. We'll make it easy.

2. Text the word MOVE to this number anytime. That triggers the same "skip the re-intake" path automatically — handy if you don't feel like a phone call.

Take care of the joint. Whether you go with us or someone else, don't sit on it.

{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}}
"""

SMS_D14 = (
    "{{contact.first_name}}, last text from me on this. If timing's wrong "
    "now, just text MOVE to this number whenever you're ready and I'll skip "
    "you past the re-intake. Take care."
)

# ── D28 — Breakup SMS ──
SMS_D28 = (
    "Last one, {{contact.first_name}} — closing your file today unless I "
    "hear back. Reply 'open' and I'll keep it active. Take care either way."
)

# ── Keyword recovery responses (WF-02) ──
SMS_KEYWORD_AUTOREPLY = (
    "Welcome back, {{contact.first_name}}. Skipping you past the re-intake. "
    "Here's Dr. Ritucci's 15-min candidacy consult: {{custom_values.booking_link}}"
)
SMS_KEYWORD_2HR_FOLLOWUP = (
    "{{contact.first_name}}, link still live if you want it: "
    "{{custom_values.booking_link}}. Or reply with the joint and I'll "
    "see if I can find you something sooner."
)

# ── Reply handler internal alert (WF-03) ──
REPLY_ALERT_SUBJECT = "Reply received — Ultra Regenerative Package lead"
REPLY_ALERT_BODY = """A lead in the Ultra Regenerative Package nurture replied.

Contact: {{contact.first_name}} {{contact.last_name}}
Phone:   {{contact.phone}}
Email:   {{contact.email}}

Open the conversation in GHL and respond within 5 minutes.

Compliance reminders:
- Never quote a price (consult-determined only)
- Never mention the $100 no-show fee (internal-only policy)
- Use "supports / may help / designed to" — never "cures / heals / fixes"
- If the message contains the keyword MOVE, the keyword-recovery workflow has already fired
"""


# ── Workflows ─────────────────────────────────────────────────────────────────

CAMPAIGN = {
    "01-master": {
        "name": "01. Ultra Regenerative Package — Master Nurture",
        # Trigger: Facebook Lead Form Submitted on the Ultra Regenerative ad.
        # Replace TODO_FB_PAGE_ID with the real page ID after launch (find via
        # GET /integrations/facebook/{loc}/trigger/pages once the FB ad
        # account is connected). Add "fb_form_id" to scope to a specific lead
        # form — recommended once Free Consult and Ultra share the same page.
        "trigger": {
            "type": "facebook_lead_gen",
            "fb_page_id": "TODO_FB_PAGE_ID",
            "name": "Facebook Lead Form Submitted",
        },
        "templates": link_steps([
            tag_step("Tag: lead", [TAG_LEAD]),
            sms_step("D0 T+1 qualifier", SMS_D0_T1),
            wait_step("Wait to D1", 1, "day"),

            email_step("D1 segmenting email", E1_SUBJECT, E1_BODY, FROM_NAME),
            sms_step("D1 evening SMS", SMS_D1),
            wait_step("Wait to D2", 1, "day"),

            email_step("D2 objections email", E2_SUBJECT, E2_BODY, FROM_NAME),
            sms_step("D2 5pm SMS", SMS_D2_5PM),
            wait_step("Wait to D3", 1, "day"),

            email_step("D3 quick-win email", E3_SUBJECT, E3_BODY, FROM_NAME),
            sms_step("D3 interrupt SMS", SMS_D3),
            wait_step("Wait to D4", 1, "day"),

            # D4 Variant A: surgery-avoider segment (default; non-openers handled by GHL split if/when added)
            email_step("D4 Variant A (surgery-avoider)", E4A_SUBJECT, E4A_BODY, FROM_NAME),
            email_step("D4 Variant B (flare-up-pain)", E4B_SUBJECT, E4B_BODY, FROM_NAME),
            sms_step("D4 5pm SMS", SMS_D4_5PM),
            wait_step("Wait to D5", 1, "day"),

            sms_step("D5 5pm curiosity SMS", SMS_D5_5PM),
            wait_step("Wait to D7", 2, "day"),

            email_step("D7 Variant A (Zeigarnik close)", E7A_SUBJECT, E7A_BODY, FROM_NAME),
            email_step("D7 Variant B (direct re-subject)", E7B_SUBJECT, E7B_BODY, FROM_NAME),
            sms_step("D7 direct question SMS", SMS_D7),
            wait_step("Wait to D10", 3, "day"),

            email_step("D10 logic email", E10_SUBJECT, E10_BODY, FROM_NAME),
            wait_step("Wait to D12", 2, "day"),

            sms_step("D12 objection surfacer SMS", SMS_D12),
            wait_step("Wait to D14", 2, "day"),

            email_step("D14 peak-end email", E14_SUBJECT, E14_BODY, FROM_NAME),
            sms_step("D14 keyword plant SMS", SMS_D14),
            wait_step("Wait to D28", 14, "day"),

            sms_step("D28 breakup SMS", SMS_D28),
            tag_step("Mark nurture complete", [TAG_NURTURE_COMPLETE]),
        ]),
    },

    "02-keyword-recovery": {
        "name": "02. Ultra Regenerative Package — MOVE Keyword Recovery",
        # Trigger: Customer replied to WF-01 with the offer keyword MOVE.
        # Engine resolves source_wf_key → wf_id of "01-master" automatically.
        "trigger": {
            "type": "customer_reply",
            "source_wf_key": "01-master",
            "keyword": "MOVE",
        },
        "templates": link_steps([
            tag_step("Apply returning lead tag", [TAG_RETURNING_LEAD]),
            tag_step("Remove nurture-complete", [TAG_NURTURE_COMPLETE], remove=True),
            sms_step("Keyword auto-reply", SMS_KEYWORD_AUTOREPLY),
            wait_step("2 hours", 2, "hour"),
            sms_step("2-hour follow-up", SMS_KEYWORD_2HR_FOLLOWUP),
        ]),
    },

    "03-reply-handler": {
        "name": "03. Ultra Regenerative Package — Global Reply Handler",
        # Trigger: Customer replied to WF-01 (any reply, no keyword filter).
        # Fires the internal-alert email for the front desk to take over
        # within 5 minutes. Bot then routes via the 7 branches in
        # ultra-regenerative-ai-bot-prompt.md.
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


# ── Run ───────────────────────────────────────────────────────────────────────

def main():
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"Ultra Regenerative Package Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="Ultra Regenerative Package Nurture",
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
