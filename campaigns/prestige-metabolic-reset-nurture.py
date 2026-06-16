#!/usr/bin/env python3
"""
A Prestige Aesthetics & Wellness — 12-Week Metabolic & Aesthetic Reset
28-day Email + SMS nurture sequence (physician-guided, high-ticket avatar).

Provider: Andrea Pryor, WHNP-BC (Women's Health NP, 23 yrs). Avatar: women
28-60, peri/menopausal, $100-200K, 20-mile radius of Franklin TN.
Offer: Tier 1 $850 / Tier 2 $999.99 (financing via Cherry + Afterpay).

────────────────────────────────────────────────────────────────────────────
BUILD DECISIONS (locked with client 2026-06-01):
- Deadline is a LOCATION custom value {{custom_values.offer_deadline}}, updated
  per cohort (no per-contact date math — that JSON is unproven on this account).
- Day 4 / Day 7 ship SINGLE-VARIANT (no 50/50 split). The whole sequence is
  therefore LINEAR — the engine's link_steps only wires linear chains, and
  find_opportunity / if_else forks are not auto-wireable here. So:
    * WF-01 CREATES the opportunity in Flowbot/Engagement at entry.
    * WF-02 UPDATES it to Connected/Qualifying on reply (no find-fork needed —
      every lead already has an opp from WF-01 entry).
- Opportunity actions use the account's real types: internal_create_opportunity
  / internal_update_opportunity (schema captured live 2026-06-01 from this
  location's existing workflows, NOT the engine's create_opportunity helper).
- Andrea's GHL user id (live): bgBaxTaIfRDjkPisLwjR.

ACCOUNT SETUP REQUIRED BEFORE DEPLOY (location custom values — create+populate):
  text_message_name  → front-desk persona name (NOT "Andrea"; she's the provider)
  booking_link       → consult booking URL (Square or native GHL calendar)
  offer_name         → "12-Week Metabolic & Aesthetic Reset - Tier 1 $850 / Tier 2 $999.99"
  offer_deadline     → current cohort enrollment-close date (update each cohort)

FILL BEFORE DEPLOY (constants below):
  PIPELINE_ID, STAGE_ENGAGEMENT, STAGE_CONNECTED  ← from ghl-cli pipeline lookup
  FB_PAGE_ID, FB_FORM_ID                          ← if using a native FB trigger
      (default ships a contact_tag trigger `apr-lead`; set the FB form to add
       that tag on submit, or swap to Facebook Form Submission in the UI.)

COMPLIANCE (medical weight mgmt + aesthetics): no specific outcome/weight
claims, no diagnostic language, no guarantees. GLP-1 stays conditional
("may be part of the protocol if appropriate"). Patient stories use initials
only. Maintained throughout — see clients/prestige/metabolic-reset-qa.md.

Hard rules: no em dashes in body copy; {{custom_values.text_message_name}} is
the bot persona, never Andrea; SMS is text-only; no financing math beyond the
Day 12 installment figures already in copy.

Workflows:
  01-master      28-day automated timeline (creates opp, 19 emails + 2 SMS)
  02-reply       Customer replied to WF-01 -> move opp to Connected + alert
  03-reset       Inbound SMS "reset" -> returning-lead recapture
  04-postbooking Appointment booked -> Version-B referral bump email
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
ANDREA_USER_ID = "bgBaxTaIfRDjkPisLwjR"   # live: "Assign to Andrea"

# ── Pipeline (FILL from ghl-cli pipeline lookup) ──────────────────────────────
PIPELINE_ID      = "AGdm3AvcscakYeyNKyvd"                    # FlowBot Pipeline
STAGE_ENGAGEMENT = "27dd6a6f-8af0-40fc-b3e6-27f6002b0454"    # Engagement (new lead)
STAGE_CONNECTED  = "7852d7c5-b592-4a18-bf90-2a309873c778"    # Connected/Qualification (replied)
STAGE_NOREPLY    = "8e46358d-0b05-4d3e-8746-bbe60db233d1"    # No-Reply (unused v1; here for reference)

# ── FB trigger (optional; default uses the apr-lead tag trigger) ───────────────
FB_PAGE_ID = ""
FB_FORM_ID = ""


# ── Local step builders for action types the engine has no helper for ──────────
# Schemas captured live 2026-06-01 from this location's existing workflows.

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


def update_opportunity_step(name: str, pipeline_id: str, stage_id: str,
                            opp_name: str = "{{contact.name}}") -> dict:
    return {"id": _uid(), "type": "internal_update_opportunity", "name": name,
            "attributes": {
                "allowBackward": False,
                "type": "internal_update_opportunity",
                "__customInputFields__": [
                    {"__customInputs__": {}, "value": opp_name,
                     "filterField": "name", "valueFieldType": "string"},
                    {"__customInputs__": {}, "value": pipeline_id,
                     "filterField": "pipelineId", "valueFieldType": "select"},
                    {"__customInputs__": {}, "value": stage_id,
                     "filterField": "pipelineStageId", "valueFieldType": "select"},
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
    """Internal notification (SMS) to the assigned user. Captured shape:
    {type:'sms', sms:{body, userType:'assign', attachments:[]}}"""
    return {"id": _uid(), "type": "internal_notification", "name": name,
            "attributes": {"type": "sms",
                           "sms": {"body": body, "userType": "assign",
                                   "attachments": []}}}


# ── Copy ──────────────────────────────────────────────────────────────────────
# Plain text. dm_email() renders one <p> per non-blank line (single enter
# between sections). A bare "[Label]" line auto-links to {{custom_values.booking_link}}.
# Inline "[text](url)" / **bold** / *italic* are honored.

E01_SUBJECT = "{{contact.first_name}}, one question before we talk"
E01 = """Hi {{contact.first_name}},
Thanks for your interest in Andrea's program at {{location.name}}. I'm {{custom_values.text_message_name}} - I work with Andrea on new patient onboarding.
Before I send you anything else, I want to ask you something.
Why now? Not 'why this program' - why now, specifically. Something shifted, or got worse, or finally tipped. I want to know what that was, because women who reach out to us usually aren't here because of a number on the scale. They're here because something else stopped being okay.
Quick overview while you think about that:
This is a 12-week physician-guided metabolic and wellness program - not a diet plan. Andrea Pryor is a Women's Health NP with 23 years of clinical experience who specializes in exactly this: the metabolic and hormonal complexity that most practices brush past.
Tier 1 starts at $850 for 3 months. Financing through Cherry and Afterpay is available - I'll send that breakdown shortly.
A small deposit holds your consultation. If you come in and Andrea doesn't think you're a strong candidate, we refund it in full. If you decide to move forward, it's applied to your program. Either way, you come out ahead.
If you're ready to just book a consultation:
[See Available Times]
Or reply and tell me where you're starting from. I'm a real person reading these.
Talk soon,
{{custom_values.text_message_name}}
{{location.name}} · {{location.phone}} · {{location.email}}"""

SMS_D1 = ("Hi {{contact.first_name}}, this is {{custom_values.text_message_name}} from "
          "{{location.name}} in Franklin. Emailed you about Andrea's 12-week program. "
          "One question: what's bringing you here right now - energy, metabolism, "
          "hormones, skin, or something else? Reply STOP to opt out.")

E02_SUBJECT = "What makes this different from programs you've tried (and what it won't do)"
E02 = """Hi {{contact.first_name}},
Most women who reach out to us have tried something before. Probably more than one thing. And most of them have a version of the same question even if they don't say it directly: what makes you any different?
Fair question. Here's the honest version.
"I've done programs before and nothing worked."
The most common reason programs don't work for women in their 40s and 50s isn't willpower - it's that the program wasn't designed for the body they're actually in. Perimenopause and menopause change how your body processes food, stores fat, and responds to exercise in ways most generic programs don't account for. Andrea specifically works with women navigating hormonal transitions. That's 23 years of clinical practice, not a marketing position.
What's actually different: monthly 3D body composition scans. Not just weight. Muscle mass, visceral fat, body fat percentage - the numbers that show what's actually changing. Most programs give you a scale and a food log. This gives you clinical data.
"$850 is a lot - especially after I've already spent money on things that didn't work."
That's a reasonable concern and we hear it often. Here's how to think about it: $850 for 3 months of physician oversight, monthly body composition scans, B12 injections, nutrition guidance, curated nutraceuticals, and clinical check-ins comes to roughly $71 a week. Compare that to the supplements, programs, or telehealth prescriptions that didn't have individualized clinical oversight behind them. The price isn't low. But it's priced around actual clinical delivery, not a subscription app.
Financing is available through Cherry and Afterpay - I'll send the full breakdown in a few days.
"Will I actually get real attention, or be processed through a protocol?"
This is the one we take most seriously. Andrea sees a limited number of patients - not a volume number. Your nutrition guidance is personalized. Your B12 protocol is calibrated to your bloodwork. Your scan results are reviewed by Andrea each month. If something isn't tracking as expected, she adjusts. That's clinical oversight, not coaching.
What this program won't do:
It won't work without your active participation. Visits, nutrition tracking, following the protocol - those are your side of the commitment. If you want something passive, this isn't it. Results build over 12 weeks, not the first two. And it's not a replacement for your primary care physician - this is a wellness program, not primary care.
One honest thing about us: this isn't a virtual program. Monthly body composition scans and injections require in-person visits at our Franklin, TN clinic. If you're more than 30 miles away, the monthly visit cadence will require some planning. That's the trade-off for clinical oversight that's real.
If that sounds like the kind of program you've been looking for:
[See Available Times]
One more thing - I'll share in a few days the specific metric women in this program say changed how they think about their health. It's not the one most people expect.
- {{custom_values.text_message_name}}"""

E03_SUBJECT = "4 things worth knowing about metabolic health in your 40s and 50s"
E03 = """Hi {{contact.first_name}},
No pitch today. This is the kind of information Andrea shares in first consultations - worth knowing whether you work with us or not.
1. The scale isn't measuring what matters most.
Weight is a blunt instrument. Two women can weigh the same and have completely different metabolic profiles - one with high muscle mass and low visceral fat, one the opposite. Visceral fat is the number that correlates most directly with cardiovascular risk, insulin sensitivity, and inflammation. Most people have never seen their visceral fat score, because most assessments don't measure it.
2. In perimenopause, cortisol does what it wants - and it affects your waist.
As estrogen declines, the body becomes more cortisol-sensitive. Chronic stress - which most women in their 40s carry as a baseline - stops being something you can outrun. Cortisol directly promotes central fat storage. This is why women who haven't changed anything about their eating or exercise find weight redistributing to their midsection. It's hormonal, not behavioral.
3. Most women over 40 are significantly under-eating protein.
Standard dietary guidelines were designed around a younger, more general population. Women in perimenopause and beyond need considerably more protein to preserve muscle mass - which is directly tied to metabolic rate. Most women eating what they think is a 'healthy' amount of protein are consuming about 60-70% of what their body actually needs at this life stage.
4. Poor sleep is metabolic work you can't compensate for.
Ghrelin (hunger hormone) goes up with sleep deprivation. Leptin (satiety hormone) goes down. This isn't a willpower problem - it's a hormonal one. Every night of poor sleep makes the next day's food choices harder at a biological level. If sleep isn't part of the conversation, most metabolic interventions are swimming upstream.
File this away. It's the context Andrea brings to every patient.
- {{custom_values.text_message_name}}
P.S. Ready to schedule? [Book a consultation here]({{custom_values.booking_link}})."""

E04_SUBJECT = "She'd tried four different approaches before she called us. Here's what she said."
E04 = """Hi {{contact.first_name}},
A patient - we'll call her L - came to us at 51. Perimenopausal, professional, had been managing her own health for decades. She'd done two online weight programs, tried a GLP-1 from a telehealth provider, and had a gym membership she used consistently. Nothing was moving. Her PCP told her labs were 'fine.'
She was tired of being told she was fine.
What she told us in her first consultation: 'I don't want to be managed. I want someone to actually look at what's happening.'
We ran her 3D body composition scan at baseline. Her muscle mass was significantly lower than expected for her activity level - her body was losing muscle, not just fat. Her visceral fat was elevated despite the fact that her weight hadn't changed much. Her PCP's labs were fine because they weren't looking at body composition.
Three months later, her visceral fat had dropped and her muscle mass had improved. She'd lost inches she'd been trying to lose for two years. She told us the number on the scale mattered less than she expected - what mattered was the scan that showed her what was actually happening.
'I stopped feeling crazy,' she said. 'I had data. Someone was paying attention.'
If you want to ask a question before scheduling, just reply. Or grab a consultation time:
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

SMS_D4 = ("{{contact.first_name}} - I know I've been in your inbox a bit. Want me to just "
          "text you a quick summary of what the 12-week program actually includes and stop "
          "with the emails? Your call. Reply STOP to opt out.")

E05_SUBJECT = "Why Andrea built this program (the version she tells patients, not the website version)"
E05 = """Hi {{contact.first_name}},
I want to share something from Andrea directly - because her reason for building this program matters for understanding what it actually is.
Andrea has been a Women's Health NP for 23 years. Before she opened APrestige Aesthetics, she spent most of that career in clinical settings seeing women who came in with metabolic concerns - weight, fatigue, hormonal changes, brain fog - and watching them leave with generic advice.
Here's the pattern she kept seeing: women in their 40s and 50s would describe symptoms that didn't fit standard lab ranges. They'd be told their thyroid was 'within normal limits,' their bloodwork was 'fine,' their BMI was 'manageable.' They were doing everything right. Still struggling. And they'd been told - implicitly or directly - that the problem was behavioral. Eat less. Move more. Sleep better. Stress less.
Most of them had already tried that.
Andrea built this program because the women who most need clinical metabolic support are the ones most likely to be dismissed in standard care settings. The 3D body composition scan exists because she was tired of relying on the scale as the only metric. The personalized nutrition guidance exists because standard caloric advice doesn't account for perimenopausal metabolic shifts. The monthly clinical oversight exists because she wanted to know what was actually happening in a patient's body - not just check a box at an annual visit.
This isn't a wellness program she attached her name to. She designed it around the gaps she spent two decades watching the system fail to fill.
If that matters to you when you're deciding where to put your trust and your money:
[Schedule a Consultation]
- {{custom_values.text_message_name}}, on behalf of Andrea Pryor, WHNP-BC"""

E07_SUBJECT = "No rush, {{contact.first_name}} - quick question though"
E07 = """Hi {{contact.first_name}},
Remember when I said I'd share the specific metric women in the program say changed how they think about their health?
Here it is: visceral fat score.
Not weight. Not BMI. Not even total body fat percentage.
Visceral fat - the fat stored around the organs - is the number most women have never seen, because most health assessments don't measure it. It's the metric that correlates most directly with metabolic health, cardiovascular risk, and systemic inflammation. And it's often the number that moves first when the program is working - before the scale shows much of anything.
Most women in the program tell us the same thing around week 6: the scale hadn't moved much, but their visceral fat score had dropped meaningfully, their energy felt different, and their clothes were fitting differently. They'd stopped needing the scale to tell them something was working - the clinical data was doing that instead.
That's what body composition tracking does that a bathroom scale can't.
If there's a specific question holding you back - whether this program is right for your situation, what the consultation looks like, or something else - reply and I'll answer it directly. No booking required.
And if you're ready:
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E08_SUBJECT = "Here's exactly what the 12 weeks look like - laid out plainly"
E08 = """Hi {{contact.first_name}},
Several people have asked me to walk through what the program actually includes, week by week. Here it is.
Month 1:
- Baseline 3D body composition scan - your starting data. Muscle mass, visceral fat, body fat %, full measurements. Not a number to feel bad about - a clinical baseline to measure against over 12 weeks.
- Intake consultation with Andrea - your full health history, goals, current medications, and hormonal picture. This is where Andrea gets the context she needs to individualize your protocol.
- B12 injections begin - scheduled on a protocol calibrated to your needs.
- Personalized nutrition guidance - not a generic meal plan. Macronutrient targets based on your composition scan and health history.
- Curated nutraceuticals - the specific supplements Andrea recommends based on your intake. Not a wellness pack off a shelf.
Month 2:
- Second 3D body composition scan - month-over-month comparison. This is where most women see the first measurable evidence of change in the data.
- Check-in with Andrea - protocol adjustments based on your scan results and how you've been feeling.
- Continued B12 and nutrition support.
Month 3:
- Final 3D body composition scan - full 12-week comparison. Where you started, where you are.
- Closing conversation with Andrea about what comes next - maintenance protocol, continued treatment, or transition plan.
Optional aesthetic add-ons:
- Botox: $10/unit - conservative, natural-looking results
- CO2 laser resurfacing: $750 - Andrea performs these personally; it's one of her specialties
- Chemical peels and microneedling also available
- Add-ons can be scheduled alongside the wellness program - some women find it useful to work on both at the same time
Pricing:
- Tier 1: $850 for the full 3-month program
- Tier 2: $999.99 - includes extended support + financing via Cherry/Afterpay
No mystery. No upsell maze. If you have a specific question about any part of it, just reply.
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E10_SUBJECT = "Most women in the program don't think about the skin piece until week 6"
E10 = """Hi {{contact.first_name}},
I want to mention something we see often enough in the program that it's worth naming early.
Women come in focused on the metabolic piece - the weight, the energy, the body composition. Completely understandable. That's why they came.
Around week 6, something shifts. The body composition data is improving. They're feeling different - not dramatically, but measurably. And then they start looking at their skin.
This is especially true for women in perimenopause and beyond. The same hormonal shifts that affect metabolism affect skin - collagen production, texture, elasticity, uneven pigmentation. These changes happen on a similar timeline to the metabolic changes. So when the program is working, some women find they want to work on both things simultaneously.
We offer:
- Botox at $10/unit - Andrea approaches injectables conservatively; natural-looking results are the goal
- CO2 laser resurfacing at $750 - Andrea performs these personally and this is one of her specialties
- Chemical peels and microneedling as additional options
We mention this not as an upsell, but because women who want to address both goals often wish they'd started them together rather than sequentially. Recovery periods align, and there's a clinical logic to working on the whole picture at once.
The metabolic program stands on its own either way. This is just information.
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E12_SUBJECT = "The financing question - here's the actual math"
E12 = """Hi {{contact.first_name}},
I get a lot of questions about financing, and I want to give you a straight answer because the terms can be confusing.
Cherry:
Cherry is a medical financing platform built specifically for wellness and aesthetic procedures. It works like a credit line - you apply, get approved, and can spread the cost over monthly payments. Approval decisions are typically fast. Rates vary based on your credit profile and the repayment term you select. You can run a soft eligibility check without it affecting your credit score.
Afterpay:
Afterpay splits the cost into 4 equal installments paid every two weeks. No interest if paid on time.
- Tier 1 ($850): approximately $212.50 per installment
- Tier 2 ($999.99): approximately $250 per installment
Both options are available through our booking process. If you want to explore Cherry eligibility before committing to anything, I can walk you through that before you put a deposit down.
Why I'm sending this: the upfront price is the most common reason women pause on this. It's worth knowing there's a structured way to access the program without $850 or $999 hitting at once. The program doesn't change based on how you pay - Andrea's oversight, the scans, and the protocol are the same either way.
Any questions, just reply. Or if you're ready:
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E14_SUBJECT = "Still thinking about it? That's completely normal."
E14 = """Hi {{contact.first_name}},
Two weeks in from your first inquiry and you haven't booked yet. That's fine - this is a considered decision.
I want to ask you one specific question, because the answer usually tells me something useful:
What's the one thing that would need to be true for you to feel confident about booking?
Not 'what are your hesitations' - just: the one thing.
Sometimes it's 'I need to know if my insurance covers any of this.' (It typically doesn't for this program - but I can give you a direct answer and the documentation if you need it for HSA reimbursement.)
Sometimes it's 'I need to know if this is right for my specific situation.' (That's exactly what the consultation is for. Andrea will tell you directly in the first meeting if she doesn't think you're a good candidate - and if she doesn't, she'll say so.)
Sometimes it's 'I just haven't had the time to think it through properly.' (Also real. Reply and we'll find a time to talk it through.)
Reply and tell me what that one thing is. I'll answer it.
- {{custom_values.text_message_name}}"""

E15_SUBJECT = '"I stopped explaining myself at the doctor\'s office." What she meant by that.'
E15 = """Hi {{contact.first_name}},
A patient - M, 47 - came to us nine months ago. Fatigue she couldn't shake. Weight that wouldn't move despite what she was doing. A low-grade feeling that something was off. Her primary care had run the standard panel several times. Everything within normal range.
She'd started to wonder if she was just tired, and if being tired was just part of getting older.
After her baseline 3D scan and intake with Andrea, she got something she hadn't had in years: clinical data that matched what she was actually experiencing. Her visceral fat was elevated. Her muscle mass had declined more than expected for her age and activity level. Her hormone picture, reviewed through the lens of someone who specializes in it, showed a pattern that explained a great deal.
She wasn't imagining it. She wasn't just aging.
After 12 weeks her numbers had improved. But more than the numbers: 'I stopped having to convince anyone that I wasn't making it up. I had the data. I understood what was happening in my own body.'
She came back for the CO2 laser afterward. Same reason, she said: 'I wanted someone who actually looked at what I was dealing with.'
If that's what you've been looking for:
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E17_SUBJECT = "The GLP-1 question - what it is, what it isn't, and how we use it"
E17 = """Hi {{contact.first_name}},
A significant number of women who reach out to us have some experience with GLP-1 medications - Semaglutide, Tirzepatide, or similar. Some were prescribed through a telehealth service. Some tried it and stopped. Some are still on it and aren't sure they're getting the right oversight.
I want to give you a clear picture of how Andrea thinks about this.
GLP-1 medications are a legitimate and effective tool for metabolic weight management when they're used correctly - with clinical oversight, appropriate patient selection, and an understanding that medication is one component of a larger protocol, not the full answer.
Where most telehealth experiences fall short: telehealth prescribers typically can't monitor body composition. So patients lose weight, but a meaningful portion of what's lost can be muscle mass - especially without the protein guidance and monitoring to prevent it. That's why body composition tracking matters. Weight down plus muscle lost is a very different clinical picture than weight down plus muscle preserved or increased.
GLP-1 management is one of Andrea's clinical specialties. If it's appropriate for your situation, it may be part of the protocol. If you've already been on it and want to understand what your body composition actually looks like, the 3D scan gives you that picture.
If you have specific questions about GLP-1 and how it fits in the program, reply and I'll have Andrea address them directly. This is one of her areas of expertise - it's worth getting a real clinical answer.
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E19_SUBJECT = "Why the scale is the worst way to track what's actually changing"
E19 = """Hi {{contact.first_name}},
A few people have asked me to describe what the 3D body composition scan actually involves. Here it is.
The scan takes about 60 seconds. You stand on a platform that rotates 360 degrees around you. It captures:
- Body fat percentage
- Lean muscle mass by region
- Visceral fat score
- Body measurements at specific anatomical points
- A 3D avatar showing your current silhouette
What you get is a data report, not just a number. A month later, you get a second scan. The comparison shows exactly what shifted - and where.
Why this matters more than the scale: two pounds of fat and two pounds of muscle weigh the same. They look different, feel different, and have entirely different metabolic implications. The scale can't distinguish between them. The scan can.
For women in perimenopause, this is especially relevant. The scale may stay flat while body composition is actively improving. Or the opposite can be true - muscle can quietly decline while total weight holds steady. The scale shows you mass. The scan shows you what kind.
Your first scan is included in the program. It's the first thing we do at your initial visit - your baseline, before anything else.
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E21_SUBJECT = "Enrollment for the next cohort - here's the math on waiting"
E21 = """Hi {{contact.first_name}},
Straight talk on timing.
We run the program in cohorts - small groups that start together so Andrea can maintain the level of clinical oversight each patient deserves. Enrollment for the next cohort closes {{custom_values.offer_deadline}}.
Here's what waiting for the following cohort means practically:
- Your baseline 3D scan doesn't happen until the next start window
- The 12-week program runs roughly six weeks later than it could
- Any aesthetic add-ons you want to coordinate get pushed accordingly
- The progress you'd start making now doesn't start until then
If finishing before a specific event, transition, or personal deadline matters to you, the math is simple.
If timing genuinely isn't right, the following cohort will be available. I'll note your file and reach out when enrollment opens.
But if you've been thinking about this for three weeks and the main thing standing between you and booking is inertia - this is the prompt.
[Lock In Before {{custom_values.offer_deadline}}]
- {{custom_values.text_message_name}}"""

E22_SUBJECT = "The three types of women who do well in this program (and one who doesn't)"
E22 = """Hi {{contact.first_name}},
I want to be direct about who this program works best for - and who it probably isn't the right fit for. If you've been on the fence, this might clarify things.
Who tends to do well:
Women who've been managing their own health for years and want a clinical partner who will actually look at their data - not a program that hands them a plan and checks back in 90 days. Women who've noticed metabolic changes they can't reverse through the approaches that used to work. Women who've tried generic programs and are ready for something physician-supervised and individualized.
Another profile that also does well:
Women who feel like they're doing everything right and still aren't seeing results. The frustration of doing the work without getting real data or real answers is exactly what this program was built around.
Who this probably isn't for:
Women who want a passive experience - something they can take or follow without significant engagement. The program requires you to show up for visits, follow the nutrition guidance, and track what Andrea asks you to track. The clinical oversight is only as useful as the information you bring to it.
Also: if you're looking for dramatic results in the first two weeks, this isn't the right fit. This is a 12-week protocol that builds. The data compounds over time.
If you read the first or second description and thought 'that's me' - the consultation is the right next step. Andrea will tell you directly in that first meeting whether she thinks you're a strong candidate. If she doesn't, she'll say so.
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E24_SUBJECT = "What 12 weeks from now looks like - specifically"
E24 = """Hi {{contact.first_name}},
I want to paint a concrete picture of what 12 weeks from your first consultation looks like. Not as a promise - as a way of thinking through what you're actually deciding.
Twelve weeks from now, you'll have:
- Three 3D body composition scans - a baseline, a midpoint, and a final. You'll know exactly how your body composition changed over that period, by the data.
- Monthly B12 injections completed on a protocol calibrated to you.
- Nutrition guidance that's been adjusted twice based on your actual scan results - not a generic template you started with and stuck to regardless of what was happening.
- Clinical oversight from a provider who specializes in the hormonal and metabolic complexity of women in your life stage - not a mention at an annual visit.
- A conversation with Andrea about what comes next: maintenance protocol, aesthetic treatments, or simply clarity on what worked and why.
What most women tell us they weren't expecting: how much it matters to simply have someone who looked. Not who told them everything was fine. Not who handed them a plan. Someone who tracked the data month by month and adjusted based on it.
That's 12 weeks from now. The first step is the consultation.
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E26_SUBJECT = "The women who get the most out of this program share one thing"
E26 = """Hi {{contact.first_name}},
I've noticed a pattern across women who complete the 12-week program and continue working with Andrea afterward.
It's not that they're more disciplined. It's not that they started in a better place. It's that they told someone.
They told a close friend what they were doing. Or a sister. Or a partner. Not to get permission - but because having one person who knew the commitment was real made the commitment feel real.
Health decisions made entirely in private are easy to walk back. The same decision named out loud to one person who matters is harder to abandon - not because of external pressure, but because it becomes part of how you see yourself.
I'm mentioning this because if you've been sitting on this for several weeks, there might be something useful in saying it out loud to someone who matters to you. Not to get permission. Just to make it real.
And - if that person also wants to do the program: if you refer someone who books a consultation before your program starts, you each receive a complimentary B12 injection added to your first visit. No code, no formal process. Just mention it when you book.
[Schedule a Consultation]
- {{custom_values.text_message_name}}"""

E28_SUBJECT = "Last email from me - plus my direct line"
E28 = """Hi {{contact.first_name}},
Last email from me on this, I promise.
If the timing isn't right - something shifted in your life, a better window is coming, you're not ready yet - I understand. Women book consultations with Andrea months after their first inquiry. The need doesn't go away on its own.
Here's my direct line: {{location.phone}}.
When you're ready, text me the word RESET and I'll get you a consultation within the week. No intake from scratch, no explaining your situation to someone who doesn't remember you, no starting the conversation over. I'll have your file and we'll pick up exactly where you left off.
Take care of yourself.
{{custom_values.text_message_name}}
APrestige Aesthetics, Franklin, TN"""

E_POSTBOOK_SUBJECT = "Your consultation is confirmed - one thing before you go"
E_POSTBOOK = """Hi {{contact.first_name}},
You're scheduled. We'll see you for your consultation with Andrea.
One thing before you go: if you know a woman who's been navigating the same kind of metabolic and hormonal complexity you have - someone who's been told everything is 'fine' and knows it isn't - and she books a consultation before your program starts, you each receive a complimentary B12 injection at your first visit. No code, no formal process. Just have her mention your name.
See you soon,
{{custom_values.text_message_name}}
APrestige Aesthetics, Franklin, TN"""

SMS_RESET_REPLY = ("Got it {{contact.first_name}} - I have your file and can get you in with "
                   "Andrea this week. Here's the booking link: {{custom_values.booking_link}}")


# ── CAMPAIGN ──────────────────────────────────────────────────────────────────

CAMPAIGN = {
    "01-master": {
        "name": "01. Metabolic Reset — Master Sequence (28d)",
        # Default: tag trigger. Set the FB lead form to add `apr-lead` on submit,
        # or swap to Facebook Form Submission in the UI (FB_PAGE_ID/FB_FORM_ID).
        "trigger": {"type": "contact_tag", "tag": "apr-lead"},
        "templates": link_steps([
            create_opportunity_step("Create Opp — Flowbot/Engagement",
                                    PIPELINE_ID, STAGE_ENGAGEMENT),
            email_step("E01 Welcome", E01_SUBJECT, E01),
            wait_step("after E01", 15, "minutes"),
            sms_step("D1 segmenting Q", SMS_D1),
            wait_step("to D2", 1, "days"),
            email_step("E02 Objection Handler", E02_SUBJECT, E02),
            wait_step("to D3", 1, "days"),
            email_step("E03 Quick Win", E03_SUBJECT, E03),
            wait_step("to D4", 1, "days"),
            email_step("E04 Social Proof", E04_SUBJECT, E04),
            wait_step("after E04", 4, "hour"),
            sms_step("D4 pattern interrupt", SMS_D4),
            wait_step("to D5", 1, "days"),
            email_step("E05 Andrea's Story", E05_SUBJECT, E05),
            wait_step("to D7", 2, "days"),
            email_step("E07 Re-engagement / Zeigarnik close", E07_SUBJECT, E07),
            wait_step("to D8", 1, "days"),
            email_step("E08 Program Breakdown", E08_SUBJECT, E08),
            wait_step("to D10", 2, "days"),
            email_step("E10 Skin Crossover", E10_SUBJECT, E10),
            wait_step("to D12", 2, "days"),
            email_step("E12 Financing", E12_SUBJECT, E12),
            wait_step("to D14", 2, "days"),
            email_step("E14 Mid-Sequence Check-In", E14_SUBJECT, E14),
            wait_step("to D15", 1, "days"),
            email_step("E15 Social Proof #2", E15_SUBJECT, E15),
            wait_step("to D17", 2, "days"),
            email_step("E17 GLP-1 Education", E17_SUBJECT, E17),
            wait_step("to D19", 2, "days"),
            email_step("E19 3D Scan Explainer", E19_SUBJECT, E19),
            wait_step("to D21", 2, "days"),
            email_step("E21 Enrollment Deadline", E21_SUBJECT, E21),
            wait_step("to D22", 1, "days"),
            email_step("E22 Self-Qualifier", E22_SUBJECT, E22),
            wait_step("to D24", 2, "days"),
            email_step("E24 90-Day Vision", E24_SUBJECT, E24),
            wait_step("to D26", 2, "days"),
            email_step("E26 Commitment + Referral", E26_SUBJECT, E26),
            wait_step("to D28", 2, "days"),
            email_step("E28 Peak-End Final", E28_SUBJECT, E28),
            tag_step("Mark nurture complete", ["apr-nurture-complete"]),
        ]),
    },

    "02-reply": {
        "name": "02. Metabolic Reset — Reply Handler",
        "trigger": {"type": "customer_reply", "source_wf_key": "01-master"},
        "templates": link_steps([
            # CONVENTION: WF-02 uses the SAME opportunity mix as WF-01's entry
            # block (Find Opportunity -> Found: update / Not Found: create, with
            # latest_optin + source + status open) but at the Connected/Qualifying
            # stage. That block is MULTIPATH (find/transition/goto) which the
            # engine's link_steps can't wire, so it's built in the GHL UI.
            # Until a multipath helper exists, this linear create->Connected is a
            # deployable placeholder (upserts the existing opp).
            create_opportunity_step("Move Opp — Connected/Qualifying",
                                    PIPELINE_ID, STAGE_CONNECTED),
            tag_step("Tag replied", ["apr-replied"]),
            assign_user_step("Assign to Andrea", ANDREA_USER_ID),
            internal_sms_alert_step(
                "Alert: lead replied",
                "APrestige reply: {{contact.name}} replied to the nurture. "
                "{{contact.phone}} / {{contact.email}}. Reply + tag the interest "
                "(metabolic / hormonal / skin / glp1)."),
        ]),
    },

    "03-reset": {
        "name": "03. Metabolic Reset — RESET Keyword Recapture",
        # Engine's customer_reply requires a workflow filter, so RESET is scoped
        # to WF-01 repliers — which is exactly the Day-28 recapture audience.
        # For a fully GLOBAL inbound-SMS "reset" trigger, add an Inbound Message
        # trigger in the GHL UI instead.
        "trigger": {"type": "customer_reply", "source_wf_key": "01-master",
                    "keyword": "reset", "name": "Texted RESET (from Day 28)"},
        "templates": link_steps([
            tag_step("Tag returning lead", ["apr-returning-lead"]),
            tag_step("Clear nurture-complete", ["apr-nurture-complete"], remove=True),
            sms_step("RESET auto-reply", SMS_RESET_REPLY),
            assign_user_step("Assign to Andrea", ANDREA_USER_ID),
            internal_sms_alert_step(
                "Alert: RESET returning lead",
                "Returning APrestige lead - {{contact.first_name}} texted RESET "
                "from the Day 28 email. Call {{contact.phone}} within 2 hours if "
                "not booked via the link."),
        ]),
    },

    "04-postbooking": {
        "name": "04. Metabolic Reset — Post-Booking Referral Bump",
        # Real trigger should be Appointment Booked (wire in UI) or set the
        # calendar to add `apr-booked` on schedule.
        "trigger": {"type": "contact_tag", "tag": "apr-booked"},
        "templates": link_steps([
            email_step("E_postbook Referral Bump", E_POSTBOOK_SUBJECT, E_POSTBOOK),
        ]),
    },
}


if __name__ == "__main__":
    total_steps = sum(len(wf["templates"]) for wf in CAMPAIGN.values())
    print(f"Metabolic Reset Nurture: {len(CAMPAIGN)} workflow(s), {total_steps} steps\n")

    # Guard: refuse to deploy with unfilled pipeline constants.
    placeholders = [c for c in (PIPELINE_ID, STAGE_ENGAGEMENT, STAGE_CONNECTED)
                    if "FILL_ME" in c]
    if placeholders:
        print("ABORT: pipeline constants not filled:", placeholders)
        print("Run the ghl-cli pipeline lookup and set PIPELINE_ID / STAGE_* first.")
        sys.exit(1)

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
        "APrestige — 12-Week Metabolic Reset",
        company_id=COMPANY_ID,
        user_id=USER_ID,
    )
    print(stats)
