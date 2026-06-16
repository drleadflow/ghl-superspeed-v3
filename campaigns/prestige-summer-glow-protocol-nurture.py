#!/usr/bin/env python3
"""
A Prestige Aesthetics & Wellness — Summer Glow Protocol (v2, warm/Ashley voice)
14-day Email + SMS lead nurture. Goal: new Summer Glow leads -> booked free
skin consultations with Andrea. Aesthetic / skin only.

Tone: warm, personal, calm, human. SMS reads like Ashley / the front desk
naturally texting. Emails read like they come from Ashley personally.

────────────────────────────────────────────────────────────────────────────
BUILD DECISIONS (with client 2026-06-16, v2 rewrite):
- **SMS LINK RULE:** booking link appears ONLY in the Day 0 confirmation SMS and
  the Day 14 final SMS. Every other SMS is reply-driven / nurture, NO link.
  (Deliverability + human feel.) Emails may all carry the link.
- **Booking:** dedicated calendar via custom value {{custom_values.glow_booking_link}}
  = https://go.aprestigeaesthetics.com/protocol-booking (separate from the global
  booking_link/botoxcal the Metabolic Reset uses).
- **Persona:** Ashley (front desk). Andrea is the provider.
- Entry trigger = Facebook lead form (facebook_lead_gen), UNFILTERED (fires on
  any FB lead form — client chose this). Set FB_FORM_ID to scope to the Summer
  Glow form only.
- LINEAR only. Non-linear rules stay UI (documented in the build log):
  hot-lead routing (form-answer fork), pause-on-reply, STOP/unsubscribe exit,
  appointment-relative 24h/2h reminders, remove-from-nurture-on-booking.

ACCOUNT SETUP (location custom values): glow_booking_link (already set).

Hard rules: no em dashes in body copy; SMS text-only; appearance-based claims;
"individual results vary" stays on results content.

Workflows:
  01-master  14-day timeline (creates opp, 9 emails + 10 SMS, SMS-link rule)
  02-reply   Customer replied to WF-01 -> human handoff (notify Ashley + tag)
  03-booked  Booked show-up track entry (tag swap + confirmation SMS)
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lib.engine import (  # noqa: E402
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, link_steps,
)

LOCATION_ID = "9uog1fOUDtxkSr4ZPx1i"
COMPANY_ID  = "R1HWQKyMMoj4PJ5mAYed"
USER_ID     = "YewkebOufK3hmeP1gx4B"
ANDREA_USER_ID = "bgBaxTaIfRDjkPisLwjR"   # live: "Assign to Andrea" (swap to a front-desk/Ashley user id if one exists)

# ── Pipeline (live — same FlowBot pipeline as the Metabolic Reset build) ──────
PIPELINE_ID      = "AGdm3AvcscakYeyNKyvd"                    # FlowBot Pipeline
STAGE_ENGAGEMENT = "27dd6a6f-8af0-40fc-b3e6-27f6002b0454"    # Engagement (new lead)
STAGE_CONNECTED  = "7852d7c5-b592-4a18-bf90-2a309873c778"    # Connected/Qualification (replied)

# ── FB trigger (empty fb_form_id = any FB lead form) ──────────────────────────
FB_PAGE_ID = ""
FB_FORM_ID = ""

LINK = "{{custom_values.glow_booking_link}}"


# ── Local step builders for action types the engine has no helper for ──────────

def _uid() -> str:
    return str(uuid.uuid4())


def create_opportunity_step(name: str, pipeline_id: str, stage_id: str,
                            source: str = "{{contact.source}}") -> dict:
    return {"id": _uid(), "type": "internal_create_opportunity", "name": name,
            "attributes": {
                "pipelineId": pipeline_id,
                "type": "internal_create_opportunity",
                "__customInputFields__": [
                    {"__customInputs__": {}, "filterField": "pipelineStageId",
                     "value": stage_id, "valueFieldType": "select"},
                    {"__customInputs__": {}, "filterField": "source",
                     "value": source, "valueFieldType": "string"},
                ],
                "__customInputs__": {},
            }}


def assign_user_step(name: str, user_id: str) -> dict:
    return {"id": _uid(), "type": "assign_user", "name": name,
            "attributes": {
                "only_unassigned_contact": False, "total_index": 1,
                "traffic_split": "equally",
                "traffic_weightage": {user_id: 1},
                "traffic_index": [{"id": user_id, "indexes": [1]}],
                "user_list": [user_id], "type": "assign_user",
            }}


def internal_sms_alert_step(name: str, body: str) -> dict:
    """Internal notification (SMS) to the assigned user."""
    return {"id": _uid(), "type": "internal_notification", "name": name,
            "attributes": {"type": "sms",
                           "sms": {"body": body, "userType": "assign",
                                   "attachments": []}}}


# ── Copy ──────────────────────────────────────────────────────────────────────
# Plain text; one <p> per non-blank line. Inline "[Label](url)" honored. No em
# dashes. Straight quotes. Typos from the source doc fixed.

# ---- DAY 0 ----
SMS_D0_CONFIRM = (  # HAS link (confirmation)
    "Hi {{contact.first_name}}, we got your request for the Summer Glow Protocol "
    "at A Prestige Aesthetics. Andrea offers a free skin consultation so we can "
    "see what actually makes sense for your skin. You can book here: " + LINK)

SMS_D0_ASHLEY = (  # NO link (personal question)
    "Hey {{contact.first_name}}! My name is Ashley and I saw your request come in. "
    "I wanted to ask a quick question. Are you more focused on getting brighter "
    "skin, smoother texture, softening fine lines, or feeling more confident "
    "without as much makeup?")

E_D0_SUBJECT = "{{contact.first_name}}, glad you reached out"
E_D0 = """Hi {{contact.first_name}},
I'm glad you reached out about the Summer Glow Protocol.
Most people who ask about it are not trying to do anything dramatic. They just want their skin to feel a little more like them again.
Brighter. Smoother. More refreshed. Easier to feel good without having to pile on makeup.
That is exactly what the consultation is for.
Andrea will take a look at your skin, listen to what has been bothering you, and help you understand what would actually make sense.
No pressure. No guessing.
You can book your free consultation here:
[Book Your Free Consultation]({{custom_values.glow_booking_link}})
Talk soon,
Ashley
A Prestige Aesthetics
Franklin, TN
(615) 380-1818"""

SMS_D0_CHECK = (  # NO link (delivery check)
    "Is this {{contact.first_name}}? I just wanted to make sure I had the right "
    "person and that my message actually went through.")

# ---- DAY 1: DiamondGlow ----
E_D1_SUBJECT = "your skin might just need a reset"
E_D1 = """Hi {{contact.first_name}},
A lot of people tell us the same thing:
"I'm using good products, but my skin still looks dull."
That does not mean you are doing anything wrong.
Sometimes dead skin, oil, and buildup sit on the surface and make your skin look tired, even if you are taking care of it.
That is where DiamondGlow can be a really nice first step.
It exfoliates, extracts, and infuses nourishing serums in one treatment, so the skin can look brighter, smoother, and more refreshed.
It is not overcomplicated. It is just a really good reset.
Andrea may recommend it if your skin needs hydration, brightness, or a clean starting point.
You can book your free consultation here:
[Book Your Free Consultation]({{custom_values.glow_booking_link}})
Talk soon,
Ashley
A Prestige Aesthetics"""

# ---- DAY 2: SMS (no link) ----
SMS_D2 = ("A lot of people come in because their skin looks tired even when they're "
          "doing all the right things at home. Is yours more dullness, uneven "
          "texture, sun spots, or fine lines?")

# ---- DAY 3: Microneedling + Exosomes ----
E_D3_SUBJECT = "if texture is what's bothering you"
E_D3 = """Hi {{contact.first_name}},
If texture is one of the things bothering you, you are definitely not alone.
That roughness, enlarged-looking pores, or uneven feeling can be frustrating because skincare at home only does so much.
Microneedling is one of the treatments Andrea may talk through with you because it works deeper than the surface.
It creates tiny micro-channels that support your skin's natural collagen response. Over a series, that can help the skin look smoother, firmer, and more even.
For some people, Andrea may also recommend adding exosomes to support recovery and renewal.
Not everyone needs it. But if texture is on your mind, it is worth asking about.
You can book your free consultation here:
[Book Your Free Consultation]({{custom_values.glow_booking_link}})
Individual results vary.
Talk soon,
Ashley
A Prestige Aesthetics"""

# ---- DAY 4: SMS (no link) ----
SMS_D4 = ("Also wanted to mention, the consultation itself is free. If you ever "
          "decide to move forward with treatment, financing may be available "
          "through Cherry and Afterpay.")

# ---- DAY 5: CO2 Skin Resurfacing ----
E_D5_SUBJECT = "this is one Andrea would need to see in person"
E_D5 = """Hi {{contact.first_name}},
Some skin concerns are easy to talk through over text.
Others really need someone to see your skin in person.
Sun spots, deeper texture, fine lines, and uneven tone can all come from damage that has built up slowly over time.
That is why CO2 skin resurfacing can be such a powerful option for the right person.
It helps resurface the skin while supporting collagen underneath, so the skin can look smoother, tighter, and more even.
But this is not a treatment to guess on.
Andrea would want to look at your skin, talk through your goals, and see if it actually makes sense for you.
That is what the free consultation is for.
You can book here:
[Book Your Free Consultation]({{custom_values.glow_booking_link}})
Individual results vary.
Talk soon,
Ashley
A Prestige Aesthetics"""

# ---- DAY 6: SMS (no link) ----
SMS_D6 = ("Based on what most people ask us about, it usually comes down to glow, "
          "texture, firmness, or softening lines. Which one would make the biggest "
          "difference for you right now?")

# ---- DAY 7: Chemical Peels + Custom Facial ----
E_D7_SUBJECT = "it may not be your skincare"
E_D7 = """Hi {{contact.first_name}},
Sometimes people think their products stopped working.
But a lot of the time, the skin just has a dull layer sitting on top that keeps everything from looking as fresh as it could.
That is where a chemical peel or custom facial may help.
A peel can help improve the look of dullness, uneven tone, rough texture, and tired-looking skin. A custom facial can help maintain that glow between bigger treatments.
The important part is choosing the right one for your skin.
Not too strong. Not too random. Not let's just try this and see.
Andrea can help you figure out what your skin actually needs.
You can book your free consultation here:
[Book Your Free Consultation]({{custom_values.glow_booking_link}})
Talk soon,
Ashley
A Prestige Aesthetics"""

# ---- DAY 8: SMS (no link) ----
SMS_D8 = ("One thing Andrea is big on is not guessing with skin. Sometimes a facial "
          "is enough. Sometimes texture or sun damage needs a different plan. That's "
          "why the consult helps.")

# ---- DAY 9: Botox / Anti-Wrinkle ----
E_D9_SUBJECT = "those little lines can be annoying"
E_D9 = """Hi {{contact.first_name}},
The little lines are usually what people notice first.
Between the brows. Across the forehead. Around the eyes.
At first, they only show when you smile or make a facial expression. Then one day they seem to stay a little longer than you want them to.
Anti-wrinkle injections can help soften those lines in a way that still looks natural.
The goal is not frozen.
The goal is rested. Softer. Still you.
A lot of people pair this with skin treatments because it helps address both the movement lines and the skin quality underneath.
Andrea can walk you through what would make sense for your face.
You can book your free consultation here:
[Book Your Free Consultation]({{custom_values.glow_booking_link}})
Talk soon,
Ashley
A Prestige Aesthetics"""

# ---- DAY 10: SMS (no link) ----
SMS_D10 = ("If you're wanting your skin to feel more refreshed for summer, starting "
           "sooner usually gives more room to map things out instead of rushing last "
           "minute.")

# ---- DAY 11: Fillers + Bio-Stimulators ----
E_D11_SUBJECT = "when you look tired but you're not"
E_D11 = """Hi {{contact.first_name}},
This one is really common.
Someone feels fine, but their face looks tired.
Sometimes that comes from volume changes in the cheeks, around the mouth, or under the eyes. It can make the face look a little more drawn than it used to.
Fillers can help restore soft, natural-looking structure.
Bio-stimulators work a little differently. They help support collagen over time, which can improve the look of firmness and skin quality gradually.
The key is not doing too much.
Andrea's goal is always natural, balanced, and refreshed.
If this is something you have been wondering about, the consultation is the best place to talk it through.
You can book here:
[Book Your Free Consultation]({{custom_values.glow_booking_link}})
Individual results vary.
Talk soon,
Ashley
A Prestige Aesthetics"""

# ---- DAY 12: SMS (no link) ----
SMS_D12 = ("No pressure at all, {{contact.first_name}}. Some people know exactly what "
           "they want, and some just know their skin feels off. Either way, that's "
           "totally normal.")

# ---- DAY 13: PRP / PRF ----
E_D13_SUBJECT = "a more natural option to ask about"
E_D13 = """Hi {{contact.first_name}},
Some people want to improve their skin, but they also want the plan to feel as natural as possible.
That is where PRP or PRF may come up.
They use growth factors from your own blood to support healthier-looking skin, collagen, tone, and texture.
Andrea may recommend it with microneedling for the right person, especially if the goal is better skin quality over time.
It is not something everyone needs, but it can be a really beautiful part of a skin plan.
During your consultation, Andrea can help you see if it makes sense for you.
You can book your free consultation here:
[Book Your Free Consultation]({{custom_values.glow_booking_link}})
Individual results vary.
Talk soon,
Ashley
A Prestige Aesthetics"""

# ---- DAY 14: final SMS (HAS link) + final email ----
SMS_D14 = (  # HAS link
    "Last note for now, {{contact.first_name}}. Your free skin consultation with "
    "A Prestige is still open whenever you are ready. We'd love to help you feel "
    "good in your skin this summer: " + LINK)

E_D14_SUBJECT = "no pressure, {{contact.first_name}}"
E_D14 = """Hi {{contact.first_name}},
I know timing is different for everyone.
Some people are ready right away. Some people need to think about it. Some people just want to understand what their options are before they make a decision.
Totally normal.
Your free consultation is still open whenever you are ready.
If your skin has been feeling dull, uneven, tired, textured, or just not quite how you want it to look, Andrea can help you talk through what would actually make sense.
No pressure.
Just a real conversation about your skin.
You can book anytime here:
[Book Anytime]({{custom_values.glow_booking_link}})
Talk soon,
Ashley
A Prestige Aesthetics
Franklin, TN
(615) 380-1818"""

# ---- Booked show-up track ----
SMS_BOOKED_CONFIRM = (
    "Hi {{contact.first_name}}, you're booked for your free skin consultation with "
    "Andrea at A Prestige Aesthetics. We're excited to meet you and talk through "
    "what makes sense for your skin.")

# Reply-handler internal alert (front desk / Ashley)
ALERT_REPLY = (
    "New reply from Summer Glow lead.\n"
    "Name: {{contact.first_name}} {{contact.last_name}}\n"
    "Phone: {{contact.phone}}\n"
    "Email: {{contact.email}}\n"
    "Source: Summer Glow Protocol\n"
    "Contact Link: {{contact.url}}\n"
    "Please review and reply personally.")


# ── CAMPAIGN ──────────────────────────────────────────────────────────────────

CAMPAIGN = {
    "01-master": {
        "name": "01. Summer Glow Protocol — Master Sequence (14d)",
        "trigger": {"type": "facebook_lead_gen", "fb_page_id": FB_PAGE_ID,
                    "fb_form_id": FB_FORM_ID, "name": "Summer Glow - FB Lead Form"},
        "templates": link_steps([
            tag_step("Tag + stamp source",
                     ["summer-glow-skin", "meta-lead", "nurture-14day"]),
            create_opportunity_step("Create Opp — Flowbot/Engagement",
                                    PIPELINE_ID, STAGE_ENGAGEMENT),
            # Day 0
            sms_step("D0 confirmation (link)", SMS_D0_CONFIRM),
            wait_step("to D0 +5min", 5, "minutes"),
            sms_step("D0 Ashley personal", SMS_D0_ASHLEY),
            wait_step("to D0 +30min", 25, "minutes"),
            email_step("D0 Welcome", E_D0_SUBJECT, E_D0),
            wait_step("to D0 +4hr", 210, "minutes"),
            sms_step("D0 delivery check", SMS_D0_CHECK),
            # Day 1
            wait_step("to D1", 1, "days"),
            email_step("D1 DiamondGlow", E_D1_SUBJECT, E_D1),
            # Day 2
            wait_step("to D2", 1, "days"),
            sms_step("D2 concern question", SMS_D2),
            # Day 3
            wait_step("to D3", 1, "days"),
            email_step("D3 Microneedling", E_D3_SUBJECT, E_D3),
            # Day 4
            wait_step("to D4", 1, "days"),
            sms_step("D4 financing", SMS_D4),
            # Day 5
            wait_step("to D5", 1, "days"),
            email_step("D5 CO2 Laser", E_D5_SUBJECT, E_D5),
            # Day 6
            wait_step("to D6", 1, "days"),
            sms_step("D6 direction question", SMS_D6),
            # Day 7
            wait_step("to D7", 1, "days"),
            email_step("D7 Peels + Facials", E_D7_SUBJECT, E_D7),
            # Day 8
            wait_step("to D8", 1, "days"),
            sms_step("D8 plan-based", SMS_D8),
            # Day 9
            wait_step("to D9", 1, "days"),
            email_step("D9 Botox", E_D9_SUBJECT, E_D9),
            # Day 10
            wait_step("to D10", 1, "days"),
            sms_step("D10 summer timing", SMS_D10),
            # Day 11
            wait_step("to D11", 1, "days"),
            email_step("D11 Fillers", E_D11_SUBJECT, E_D11),
            # Day 12
            wait_step("to D12", 1, "days"),
            sms_step("D12 reassurance", SMS_D12),
            # Day 13
            wait_step("to D13", 1, "days"),
            email_step("D13 PRP/PRF", E_D13_SUBJECT, E_D13),
            # Day 14
            wait_step("to D14", 1, "days"),
            sms_step("D14 final SMS (link)", SMS_D14),
            email_step("D14 final email", E_D14_SUBJECT, E_D14),
            # 14 days elapsed, no booking -> hand off to monthly newsletter
            tag_step("Remove nurture-14day", ["nurture-14day"], remove=True),
            tag_step("Add long-term newsletter", ["long-term-skin-newsletter"]),
        ]),
    },

    "02-reply": {
        "name": "02. Summer Glow Protocol — Reply Handler (human handoff)",
        "trigger": {"type": "customer_reply", "source_wf_key": "01-master"},
        "templates": link_steps([
            create_opportunity_step("Move Opp — Connected/Qualifying",
                                    PIPELINE_ID, STAGE_CONNECTED),
            tag_step("Tag human-response-needed", ["human-response-needed"]),
            assign_user_step("Assign to front desk", ANDREA_USER_ID),
            internal_sms_alert_step("Alert: lead replied (review + reply personally)",
                                    ALERT_REPLY),
        ]),
    },

    "03-booked": {
        "name": "03. Summer Glow Protocol — Booked Show-Up (entry)",
        # Point at Appointment Booked in the UI, or set the calendar to add
        # `booked-show-up` on schedule. 24h/2h reminders are appointment-relative
        # — wire them via the account's Appointment Reminder system (see build log).
        "trigger": {"type": "contact_tag", "tag": "booked-show-up"},
        "templates": link_steps([
            tag_step("Remove nurture-14day", ["nurture-14day"], remove=True),
            sms_step("Booked confirmation", SMS_BOOKED_CONFIRM),
        ]),
    },
}


if __name__ == "__main__":
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"Summer Glow Protocol v2: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

    token_mgr = TokenManager(LOCATION_ID)
    if os.environ.get("GHL_FIREBASE_REFRESH_TOKEN"):
        token_mgr.set_refresh_token(os.environ["GHL_FIREBASE_REFRESH_TOKEN"])
        token_mgr.prefer_refresh_token = True  # don't let a stale id-token win
    client = GHLClient(token_mgr, LOCATION_ID)

    # Cheap auth probe before building.
    test = client.request("GET", f"/workflow/{LOCATION_ID}/list?parentId=root&limit=1")
    if not isinstance(test, dict) or test.get("_error"):
        print("ABORT: auth/list probe failed:", test)
        sys.exit(2)

    builder = CampaignBuilder(client, LOCATION_ID)
    stats = builder.build(
        CAMPAIGN,
        "APrestige — Summer Glow Protocol",
        company_id=COMPANY_ID,
        user_id=USER_ID,
    )
    print(stats)
