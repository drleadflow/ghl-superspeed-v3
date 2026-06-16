#!/usr/bin/env python3
"""
Healthspan By Design LLC — Premier Wellness Assessment (PWA) nurture
sequence. A $1,500 high-ticket preventive / longevity assessment for an
affluent, skeptical, well-read audience age 30-65 in FL, NY, AZ, and TX
who follow Attia / Huberman / Bryan Johnson and want it applied to them
specifically by a real MD. Dr. Joel Wussow MD is the physician.

GENERATED FOR REVIEW — NOT YET DEPLOYED. Do not run main() until the
deploy gates below are cleared (see the constants block).

Trigger model (per project_iv_wellness_nad_workflow_rules):
- WF-01 ships with a tag trigger `pwa-lead` because the engine's
  automatic trigger creation only handles `contact_tag` types. The
  Facebook lead form must be swapped to a Facebook Form Submission
  trigger in the GHL UI after deploy (or set the form to add the
  `pwa-lead` tag on submit so the existing tag trigger fires).
- WF-02 trigger is `Customer Replied` filtered to `replied to workflow
  = WF-01 Master Sequence` (set up in GHL UI after WF-01 ID is captured).

Two workflows, linear (no keyword recovery — replies route through
WF-02 directly, no keyword required):
  01. PWA — Master Sequence (28 days, automated only)
  02. PWA — Global Reply Handler

Touchpoint count: 18 contact-facing sends (7 emails + 11 SMS) across
28 days, 38 master nodes incl. waits. Has Deadline=No and Deposit
Required=No per the offer spec, so there is NO deposit-deadline email.
The urgency lever is limited monthly PWA capacity plus advance
mobile-phlebotomy scheduling, de-risked by the credit-back and the
find-3-risks-or-refund guarantee.

Three clinical pillars are rotated as distinct content angles (Joel's
own framing):
  1. Precision cardiovascular risk — PREVENT 10/30-yr refined by
     risk-enhancing factors. ApoB & Lp(a) are SUPPORTING markers, not
     the headline ("we read your whole cardiovascular risk pattern most
     doctors never assemble").
  2. Metabolic / early diabetes — LPIR catches insulin resistance
     about 8 years upstream of your annual physical.
  3. Evidence-based hormone optimization as preventive / longevity
     medicine with timing-dependent benefit.

Belief-shift spine: your body is telling a story most doctors cannot
read, and the PWA reads it.

Hard rules (medical / longevity strict mode):
- Educational and modality-stating ONLY. Never diagnostic. No
  symptom-to-diagnosis claims.
- No personal-attribute copy. Never assert the reader's health state.
- Never promise outcomes or cures. Use "assess / identify / stratify /
  personalized plan," never "fix / cure / reverse / guarantee you'll."
- The ONLY guarantee allowed is the literal refund guarantee (find >=3
  modifiable risks or refund). State it exactly, do not embellish.
- Never use "100%" anywhere in body copy except the literal "$1,500
  credited 100% toward..." bonus.
- No em dashes anywhere in body copy (allowed in workflow names and
  this docstring only).
- Use {{custom_values.booking_link}} for any booking CTA (booking link
  not set yet — never hardcode a URL).
- {{custom_values.text_message_name}} is the front-desk / concierge
  persona, NOT Dr. Wussow. Uses Bot=No, so it is a patient-coordinator
  who hands off to Dr. Wussow, not a bot.
- Tag prefix: pwa-
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.engine import (
    TokenManager, GHLClient, CampaignBuilder,
    sms_step, email_step, wait_step, tag_step, link_steps,
)

# ── DEPLOY GATES (read before running main) ──────────────────────────────────
# This file is GENERATED FOR REVIEW and is NOT yet deployed. Before deploy:
#   1. Resolve USER_ID — the new location's user_id must be pulled before
#      deploy (the placeholder below is intentional and will fail fast).
#   2. Refresh the GHL Firebase token (set GHL_FIREBASE_REFRESH_TOKEN).
#   3. Confirm the booking_link AND text_message_name custom values exist
#      on location EnmtjE3RhgP6s0oIn1GV. Both resolve at send time.
LOCATION_ID = "EnmtjE3RhgP6s0oIn1GV"   # Healthspan By Design LLC sub-account
COMPANY_ID  = "R1HWQKyMMoj4PJ5mAYed"   # DLF agency
USER_ID     = "TODO_RESOLVE_AT_DEPLOY"  # leave as this literal placeholder; pull the new location's user_id before deploy
PARENT_FOLDER = ""

FROM_NAME = "{{custom_values.text_message_name}}"

# ── EMAIL COPY ───────────────────────────────────────────────────────────────

E1_SUBJECT = "{{contact.first_name}}, the question your labs can't answer on their own"
E1_BODY = """Hi {{contact.first_name}},

Thanks for reaching out about the Premier Wellness Assessment. I'm {{custom_values.text_message_name}}, I run the front desk for {{location.name}} and I coordinate the assessment from your first reply through your report. Dr. Joel Wussow MD is the physician who reviews your case and sits with you for the consult.

Let me tell you what this actually is, because it is not another lab subscription.

You can already buy a box of biomarkers. Function, Superpower, InsideTracker, Blueprint will all sell you a panel and a dashboard. What none of them sell you is a preventive-medicine physician who assembles those numbers into the one thing that matters: your individual risk picture, and the highest-leverage moves to act on first.

That is the whole idea behind the PWA. Your body is telling a story right now. Most annual physicals are not built to read it. We are.

Here is what the Premier Wellness Assessment includes:

- A 100+ biomarker panel: cardiometabolic, hormone, thyroid, inflammatory, and advanced lipids including ApoB and Lp(a)
- Mobile phlebotomy at your home or office, so you never sit in a waiting room
- A 60-minute consult with Dr. Wussow to review your full intake and results
- Your 10-year and 30-year cardiovascular risk, stratified using the AHA PREVENT framework and refined by your risk-enhancing factors
- Your 8-year diabetes risk using LPIR, which can identify insulin resistance about 8 years before an A1c moves
- A full hormone and metabolic read, interpreted against optimal ranges rather than population averages
- A written, plain-language Patient PWA Report with a prioritized action plan you can start on immediately

One question, because your answer changes what I send next:

**What pushed you to look into this now? A specific health scare or family diagnosis, a milestone birthday, or just that you have tried other things and want real answers from an MD?**

Reply with "scare," "birthday," or "answers." One word is enough.

[Book Your Premier Wellness Assessment]({{custom_values.booking_link}})

Not ready to book? Reply with the question that is actually on your mind. I read every one and hand the clinical ones to Dr. Wussow.

{{custom_values.text_message_name}}
{{location.name}}
{{location.phone}}"""

# Subject pattern: name the gap a data dump can't fill. Belief-shift
# spine up front (body tells a story most doctors can't read). Itemizes
# what you get (objection #2). Soft segment Q maps to the 3 buying
# triggers (scare / birthday / answers). No diagnostic claims, no
# personal-attribute copy, no "100%". Concierge persona hands off to MD.


E2_SUBJECT = "Why your doctor said you're fine (and why you don't believe it)"
E2_BODY = """Hi {{contact.first_name}},

The three questions almost everyone asks before booking the Premier Wellness Assessment are the honest ones. Here they are, answered plainly.

**1. Is this just expensive lab work?**
No. The labs are the raw material, not the product. Function and the other direct-to-consumer panels hand you data and a dashboard, then leave the interpretation to you. Fountain Life does deep diagnostics but starts north of $20,000 with no entry tier. ConciergeMD gives you a doctor but is not built around longevity risk. The PWA is the combination none of them offer: a preventive-medicine physician, a proprietary longevity framework, and a written prioritized plan, at a defined $1,500. And the fee is credited 100% toward Annual Concierge or program enrollment if you continue within 30 days.

**2. What do I actually walk away with?**
A 60-minute consult with Dr. Wussow and a written Patient PWA Report. The report assembles your 100+ biomarkers into your 10-year and 30-year cardiovascular risk, your 8-year diabetes risk, your hormone and metabolic status, and a prioritized list of the highest-leverage things to act on, in order. Not 80 numbers in the green and red. A plan.

**3. Couldn't my regular doctor do this?**
Most cannot, and it is not a knock on them. A standard physical was designed to catch disease that is already present, not to stratify risk a decade or three out. Many PCPs do not order ApoB, Lp(a), advanced lipid morphology, or markers of insulin sensitivity, and the visit is rarely long enough to interpret them against your family history and risk-enhancing factors. "Your standard panel looks fine" can be true at the same time your risk pattern is worth acting on. Those are two different questions.

One honest thing. The PWA is an assessment and a plan, not a treatment session and not a cure. What it does is identify what is worth your attention and hand you the first moves. The work after that is yours, and the concierge follow-up exists because optimization is a long game, not a single visit.

[Book Your Premier Wellness Assessment]({{custom_values.booking_link}})

In a few days I will send you the one set of numbers most people your age have never had assembled, and why the 30-year version of it matters more than the 10-year. It surprises almost everyone.

{{custom_values.text_message_name}}"""

# Subject pattern: name the belief ("you're fine" vs "you don't believe
# it"). Handles all 3 objections head-on (price-vs-value against
# Function/Fountain Life/ConciergeMD, what-you-get itemized, why-PCP-
# won't/can't). Honest-flow (assessment not cure). Zeigarnik teaser
# closes in E3 (cardiovascular pillar). "credited 100%" is the ONLY
# allowed 100% use. No diagnostic or personal-attribute copy.


E3_SUBJECT = "The 30-year number almost no one has ever seen"
E3_BODY = """Hi {{contact.first_name}},

A few days ago I promised you the set of numbers most people your age have never had assembled. Here it is, and it is the first of our three clinical pillars: precision cardiovascular risk.

Most risk conversations stop at cholesterol and a 10-year estimate. The PWA reads the whole pattern.

**The 10-year and 30-year view.** Dr. Wussow stratifies your cardiovascular risk using the AHA PREVENT framework and refines it with your risk-enhancing factors, your family history, and your own biomarkers. The 30-year number is the one that tends to land hardest, because someone in their 40s can carry a 10-year risk that looks reassuring while the 30-year picture tells a different story. You cannot act on a number nobody ever calculated for you.

**The markers most panels skip.** ApoB and Lp(a) are part of this. They are not the headline though, and anyone who treats a single number as the whole answer is doing the same thing the dashboard apps do. The headline is the assembled pattern: how your lipids, your inflammatory markers, your metabolic state, and your history fit together into a risk profile your annual physical was never built to construct.

**Why assembling it matters.** Any lab can report ApoB. Reading it in the context of everything else, against optimal ranges, and turning it into "here is what to do first," is the part that needs a physician and a framework. That is what the consult and the written report are for.

This is the belief that the PWA is built on. Your body is telling a story right now. The cardiovascular chapter of that story is usually the most actionable, and it is the one most often left unread.

[Book Your Premier Wellness Assessment]({{custom_values.booking_link}})

P.S. The next thing I send is about the chapter that shows up about 8 years before your annual physical would catch it.

{{custom_values.text_message_name}}"""

# Subject pattern: curiosity + specificity (the 30-year number). PILLAR
# 1 (precision cardiovascular risk). ApoB/Lp(a) framed explicitly as
# SUPPORTING, not headline, per spec. Reinforces belief-shift spine.
# Zeigarnik teaser tees up E4 (metabolic pillar). No diagnostic claims.


E4_SUBJECT = "The signal that shows up 8 years early"
E4_BODY = """Hi {{contact.first_name}},

Last time I said the next chapter shows up about 8 years before your annual physical would catch it. This is our second clinical pillar: metabolic and early diabetes risk.

Here is the part most people are never told.

By the time a fasting glucose or an A1c drifts out of range, the underlying process has usually been building for years. The body compensates quietly for a long time before the standard markers move. That is why someone can pass their annual labs and still be on a path worth changing.

The PWA reads this earlier, with a marker called LPIR (lipoprotein insulin resistance). LPIR can identify insulin resistance about 8 years upstream of where a routine A1c would flag it. Paired with the rest of your cardiometabolic phenotyping, your insulin sensitivity, visceral adiposity pattern, atherogenic dyslipidemia, and inflammatory burden, it gives Dr. Wussow a view of where your metabolism is actually trending, not just where it sits today.

Why this matters in plain terms. The earlier a metabolic drift is identified, the more leverage your lifestyle and, where clinically indicated, medical options have. The window when small changes do the most work is the window most physicals are not built to see.

To be clear about what this is. The PWA does not diagnose you over email and it does not promise to reverse anything. It assesses where you are, identifies what is worth acting on, and hands you a prioritized plan. What that plan looks like is individual, which is exactly why it comes from a physician and not an algorithm.

[Book Your Premier Wellness Assessment]({{custom_values.booking_link}})

{{custom_values.text_message_name}}"""

# Subject pattern: specific, intriguing (8 years early). PILLAR 2
# (metabolic / early diabetes, LPIR upstream of A1c). Strict compliance:
# no symptom-to-diagnosis, no personal-attribute, "assess/identify"
# verbs, explicit no-diagnose/no-reverse disclaimer. Speaks generally.


E5_SUBJECT = "Why timing is the whole game with hormones"
E5_BODY = """Hi {{contact.first_name}},

Our third clinical pillar is the one that gets the most noise online and the least careful handling: evidence-based hormone optimization as preventive medicine.

Here is the part that matters, stated carefully.

Hormone status is not just about how you feel day to day. In preventive and longevity medicine it is understood as having a timing-dependent benefit. Acting within the right window tends to be protective. Waiting past it tends to lose much of that benefit. That is a general principle from the evidence base, not a statement about you specifically, and the only way to know where you sit is to measure and interpret it against optimal ranges with a physician.

That is exactly what the PWA does. Your full hormone panel is read alongside your thyroid, inflammatory, and metabolic markers, in the context of your intake and history, by Dr. Wussow. Not against a population average that quietly assumes "normal for your age," but against what optimal actually looks like. Where something is worth addressing, the plan can include lifestyle levers and, where clinically indicated, medical options. Where it is not, you find that out too, which is its own kind of answer.

This is the throughline across all three pillars. Cardiovascular, metabolic, hormonal. Each one is a chapter of the same story your body is telling, and the PWA reads them together rather than one number at a time.

If you have been following Attia or Huberman and thinking "I want this applied to me, by an actual MD," that is precisely the gap this was built to close.

What is the question that would actually move this from interesting to booked for you? Reply, it comes straight to me.

Or whenever you are ready: {{custom_values.booking_link}}

{{custom_values.text_message_name}}"""

# Subject pattern: principle-led (timing is the whole game). PILLAR 3
# (hormone optimization, timing-dependent benefit). Heavily compliance-
# guarded: states timing as general evidence principle NOT about reader,
# "measure/interpret/assess," no promises. Names the Attia/Huberman
# audience. Low-friction reply ask. Ties all 3 pillars to belief spine.


E6_SUBJECT = "What 'find 3 risks or it's free' actually means"
E6_BODY = """Hi {{contact.first_name}},

If the $1,500 has been the thing you keep circling back to, this email is for you. I want to take the financial risk off the table as plainly as I can.

The Premier Wellness Assessment carries a specific guarantee, and I will state it exactly as it stands:

**Find at least 3 modifiable health risks worth acting on, or your $1,500 fee is fully refunded.**

That is the whole guarantee, word for word. Not a satisfaction promise, not fine print. If the assessment does not surface at least three modifiable risks for you to act on, you do not pay for it.

Then there is the part that changes the math entirely. The $1,500 is credited 100% toward Annual Concierge or program enrollment if you continue with Dr. Wussow within 30 days. So for anyone who is likely to keep going, the assessment is effectively the on-ramp, not an added cost. You are moving the money forward, not spending it twice.

Put those two together and here is where you actually stand. If the assessment does not find enough worth acting on, you are refunded. If it does and you continue, your fee is credited toward what comes next. The case where you pay $1,500 and get nothing actionable is the one the guarantee is designed to remove.

Compare that to the alternatives honestly. A data-only panel is cheaper up front and leaves you to interpret it alone. A full diagnostic center like Fountain Life starts many times higher with no entry tier. The PWA sits where a real physician plan meets a defined, de-risked price.

A practical note on timing, since people ask. A limited number of PWA clients are accepted each month so each person gets full physician attention, and the mobile phlebotomy is scheduled in advance. It is worth starting the conversation before the month you want fills, even if your actual draw is a few weeks out.

[Book Your Premier Wellness Assessment]({{custom_values.booking_link}})

{{custom_values.text_message_name}}
{{location.phone}}"""

# Subject pattern: quote the guarantee verbatim. Objection #1 (price-vs-
# value) head-on. States refund guarantee EXACTLY, no embellishment.
# "credited 100%" is allowed (literal bonus). Urgency lever = limited
# monthly capacity + advance phlebotomy (NOT a deposit deadline; Has
# Deadline=No). De-risks via credit-back. No diagnostic copy.


E7_SUBJECT = "Last email from me, plus my direct line"
E7_BODY = """Hi {{contact.first_name}},

Last email from me on this. I mean it.

People put off an assessment like this for honest reasons. The ones I hear most:

- "I keep meaning to and life keeps getting in the way" (it will keep getting in the way, the calendar does not clear on its own in your 40s or 50s)
- "My doctor said I'm fine" (that answers whether you have disease today, not what your risk pattern looks like a decade or three out, those are different questions)
- "I want to wait until something is actually wrong" (the entire point of preventive work is to act in the window before that, when the leverage is highest)

If any of those is you, I understand, and I will stop emailing.

When you are ready, two easy options:

**1.** Book directly: {{custom_values.booking_link}}

**2.** Just reply to this email, or text {{location.phone}}. A question, a time that works, anything at all. It comes straight to the front desk, not a queue, and I hand the clinical questions to Dr. Wussow.

Whatever you decide, thank you for considering us. Dr. Wussow built the Premier Wellness Assessment because he kept meeting people who had been handed a pile of data with no plan, or told they were fine when their own pattern said otherwise. You deserve the version where a physician reads the whole story and tells you what to do first.

And so it is on the table without any pressure today, here is the rest of what the practice offers once your blueprint exists:

- Annual Concierge, with longitudinal optimization and retest cadence
- Direct text-to-cell access to Dr. Wussow for program clients
- The 30-day credit, so your $1,500 moves forward into whatever you choose

You do not have to think about any of that today. The Premier Wellness Assessment stands on its own, and the guarantee stands behind it: find at least 3 modifiable health risks worth acting on, or your $1,500 fee is fully refunded.

{{custom_values.text_message_name}}
{{location.name}}
{{location.address}}
{{location.phone}}"""

# Subject pattern: direct. Peak-end + open reply CTA, no keyword. Names
# the 3 honest blockers (incl. "doctor said fine" = objection #3).
# Permission to stop. Soft cross-sell tee-up to Annual Concierge +
# credit-back. Restates refund guarantee EXACTLY at close. The message
# people screenshot. No diagnostic/personal-attribute copy, no "100%"
# except the literal credit.


# ── SMS COPY ─────────────────────────────────────────────────────────────────
# All conversational, no em dashes, concierge persona (hands off to MD).

SMS_T0 = "Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} at {{location.name}}. Got your Premier Wellness Assessment inquiry, sending a quick rundown in a sec. Reply STOP to opt out."

SMS_T1 = "Hey {{contact.first_name}}, {{custom_values.text_message_name}} again. Quick one so I send the right info: what pushed you to look now? A health scare, a milestone birthday, or just ready for real answers? Reply scare, birthday, or answers."

SMS_D1_15min = "Hey {{contact.first_name}}, just sent your welcome email with the full rundown on the Premier Wellness Assessment. Same question there: scare, birthday, or answers? One word is enough."

SMS_D2_5pm = "Hey {{contact.first_name}}, I put together a short read on the 3 questions people ask most before booking the PWA, including whether your own doctor could just do it. Want me to send it over?"

SMS_D3_10am = "Is this {{contact.first_name}}?"

SMS_D4_5pm = "Hey {{contact.first_name}}, want me to walk you through what the 60-min consult with Dr. Wussow actually covers, or are you good to book? Either is fine."

SMS_D5_5pm = "Quick note {{contact.first_name}}: the PWA fee is credited 100% toward your program if you continue within 30 days, and there's a find-3-risks-or-refund guarantee. Want the link?"

SMS_D7_10am = "Hey {{contact.first_name}}, honest one: what's actually holding you back on the PWA? The price, not knowing what you get, or wondering if your doctor could do it? No pressure."

SMS_D10_10am = "{{contact.first_name}}, only a limited number of PWA clients are booked each month so each gets full physician time, and the at-home blood draw is scheduled ahead. Want me to start your spot for next month?"

SMS_D12_10am = "{{contact.first_name}}, when I don't hear back it's usually one of three: timing, a question I haven't answered, or the price. Which is it? I'll sort it."

SMS_D14_10am = "Last one from me for now, {{contact.first_name}}. Whenever you're ready, reply here and I'll get you onto Dr. Wussow's calendar. Or book direct: {{custom_values.booking_link}}"

SMS_D28_10am = "Hi {{contact.first_name}}, {{custom_values.text_message_name}}. Should I close your Premier Wellness Assessment file, or keep it open for whenever the timing fits?"


# ── REPLY HANDLER COPY ───────────────────────────────────────────────────────
# Internal alert email body for front desk

REPLY_ALERT_SUBJECT = "REPLIED LEAD: {{contact.first_name}} on Premier Wellness Assessment nurture"
REPLY_ALERT_BODY = """REPLIED LEAD ALERT.

{{contact.first_name}} {{contact.last_name}} replied to the Premier Wellness Assessment nurture sequence.

Phone: {{contact.phone}}
Email: {{contact.email}}

ACTION REQUIRED: Respond within 5 minutes. Do NOT let automation re-engage until this contact is manually marked as resolved or booked.

Their last message is in the GHL conversation thread. Check it before replying. Hand any clinical questions to Dr. Wussow."""


# ── CAMPAIGN ─────────────────────────────────────────────────────────────────
# Day map for 01-master (cumulative from FB form submit, automated only):
#   T+0     SMS_T0          instant confirm + opt-out
#   T+1m    SMS_T1          qualifying Q (scare / birthday / answers)
#   D1 10a  E1              welcome + belief-shift + what-you-get + qualifier echo
#   D1 10:15a SMS_D1_15min  echo qualifier on SMS channel
#   D2 10a  E2              top 3 objections (price / what-you-get / PCP) + Zeigarnik
#   D2 5p   SMS_D2_5pm      reciprocity hook (3-questions read)
#   D3 10a  E3              PILLAR 1 cardiovascular risk (10/30-yr, ApoB supporting)
#   D3 10a  SMS_D3_10am     pattern interrupt
#   D4 10a  E4              PILLAR 2 metabolic / early diabetes (LPIR 8yr upstream)
#   D4 5p   SMS_D4_5pm      consult-walkthrough offer
#   D5 5p   SMS_D5_5pm      de-risk heads-up (credit-back + refund guarantee)
#   D7 10a  E5              PILLAR 3 hormone optimization (timing-dependent benefit)
#   D7 10a  SMS_D7_10am     direct question (3 named blockers)
#   D10 10a E6              guarantee + credit-back de-risk (objection #1 price)
#   D10 11a SMS_D10_10am    scarcity lever (limited monthly capacity + advance draw)
#   D12 10a SMS_D12_10am    objection surfacer (3 named blockers)
#   D14 9a  E7              peak-end + open reply CTA + cross-sell soft mention + guarantee restated
#   D14 10a SMS_D14_10am    final nudge
#   D28 10a SMS_D28_10am    breakup text
#   tag     pwa-nurture-complete

CAMPAIGN = {
    "01-master": {
        "name": "01. PWA — Master Sequence",
        "tag": "pwa-lead",
        "templates": link_steps([
            sms_step("S0 Instant Confirm + Opt-Out (T+0)", SMS_T0),
            wait_step("1 min", 1, "minutes"),
            sms_step("S1 Qualifying Q Scare vs Birthday vs Answers (T+1m)", SMS_T1),
            wait_step("22 hours", 22, "hour"),
            email_step("E1 Welcome + Belief Shift + What You Get (D1 10am)", E1_SUBJECT, E1_BODY, FROM_NAME),
            wait_step("15 min", 15, "minutes"),
            sms_step("S_D1_15 Echo Qualifier (D1 10:15am)", SMS_D1_15min),
            wait_step("23 hours", 23, "hour"),
            wait_step("45 min", 45, "minutes"),
            email_step("E2 Top 3 Objections + Zeigarnik Teaser (D2 10am)", E2_SUBJECT, E2_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D2 Reciprocity Hook (D2 5pm)", SMS_D2_5pm),
            wait_step("17 hours", 17, "hour"),
            email_step("E3 Pillar 1 Cardiovascular Risk 10-30yr (D3 10am)", E3_SUBJECT, E3_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D3 Pattern Interrupt (D3 10am)", SMS_D3_10am),
            wait_step("24 hours", 24, "hour"),
            email_step("E4 Pillar 2 Metabolic Early Diabetes LPIR (D4 10am)", E4_SUBJECT, E4_BODY, FROM_NAME),
            wait_step("7 hours", 7, "hour"),
            sms_step("S_D4 Consult Walkthrough Offer (D4 5pm)", SMS_D4_5pm),
            wait_step("24 hours", 24, "hour"),
            sms_step("S_D5 De-Risk Heads-Up Credit-Back + Guarantee (D5 5pm)", SMS_D5_5pm),
            wait_step("41 hours", 41, "hour"),
            email_step("E5 Pillar 3 Hormone Optimization Timing (D7 10am)", E5_SUBJECT, E5_BODY, FROM_NAME),
            wait_step("1 min", 1, "minutes"),
            sms_step("S_D7 Direct Question 3 Blockers (D7 10am)", SMS_D7_10am),
            wait_step("3 days", 3, "days"),
            email_step("E6 Guarantee + Credit-Back De-Risk (D10 10am)", E6_SUBJECT, E6_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D10 Scarcity Limited Monthly Capacity (D10 11am)", SMS_D10_10am),
            wait_step("47 hours", 47, "hour"),
            sms_step("S_D12 Objection Surfacer (D12 10am)", SMS_D12_10am),
            wait_step("47 hours", 47, "hour"),
            email_step("E7 Peak-End + Cross-Sell + Guarantee Restated (D14 9am)", E7_SUBJECT, E7_BODY, FROM_NAME),
            wait_step("1 hour", 1, "hour"),
            sms_step("S_D14 Final Nudge (D14 10am)", SMS_D14_10am),
            wait_step("14 days", 14, "days"),
            sms_step("S_D28 Breakup Text (D28 10am)", SMS_D28_10am),
            tag_step("Mark PWA Nurture Complete", ["pwa-nurture-complete"]),
        ]),
    },

    "02-reply-handler": {
        "name": "02. PWA — Global Reply Handler",
        "tag": "pwa-replied",
        "templates": link_steps([
            tag_step("Confirm Reply Tag Applied", ["pwa-replied"]),
            email_step("Internal Alert to Front Desk", REPLY_ALERT_SUBJECT, REPLY_ALERT_BODY, FROM_NAME),
        ]),
    },
}


# ── RUN ──────────────────────────────────────────────────────────────────────

def main():
    # NOTE: This file is generated for review and is NOT yet deployed.
    # Before running this, clear the deploy gates near the constants block:
    #   1. Resolve USER_ID (pull the new location's user_id).
    #   2. Refresh the GHL Firebase token (GHL_FIREBASE_REFRESH_TOKEN).
    #   3. Confirm booking_link + text_message_name custom values exist
    #      on location EnmtjE3RhgP6s0oIn1GV.
    if USER_ID == "TODO_RESOLVE_AT_DEPLOY":
        print("USER_ID is still the placeholder. Resolve it before deploy. Aborting.")
        sys.exit(1)

    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"PWA Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

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
        folder_name="Premier Wellness Assessment",
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
