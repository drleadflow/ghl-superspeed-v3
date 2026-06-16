# Engine action schemas + the correct opportunity pattern

Captured live 2026-06-01 from the APrestige location (incl. a watch session where
the operator demoed the RIGHT way). Use these exact shapes. Built-in helpers
(`sms_step`, `email_step`, `wait_step`, `tag_step`, `update_contact_field_step`,
`link_steps`) come from `lib.engine`.

## Triggers (`wf_def["trigger"] = {...}`)
```python
# Facebook lead form — the STANDARD WF-01 entry trigger.
{"type": "facebook_lead_gen", "fb_page_id": "<pageId>", "fb_form_id": "<formId>",
 "name": "Facebook Lead Form Submitted"}
# Tag (fallback entry / post-booking)
{"type": "contact_tag", "tag": "apr-lead"}
# Replied to a workflow (reply handler) — REQUIRES source_wf_key
{"type": "customer_reply", "source_wf_key": "01-master"}
# Replied + keyword (keyword recapture) — REQUIRES source_wf_key too
{"type": "customer_reply", "source_wf_key": "01-master", "keyword": "reset"}
```
**FB trigger — live save shape (correction):** the form condition uses
`is-any-of` + an ARRAY + `type:"multiselect"`, NOT `==`/`select`. The page uses
`==`/`select`. The engine's `_build_trigger_body` currently emits `==`/`select`
for the form — verify it matches this when wiring FB natively:
```json
"conditions":[
 {"operator":"==","field":"facebook.pageId","value":"<pageId>","title":"Page Is","type":"select"},
 {"operator":"is-any-of","field":"facebook.formId","value":["<formId>"],"title":"Form Is","type":"multiselect"}],
"type":"facebook_lead_gen","masterType":"highlevel","active":true,
"actions":[{"workflow_id":"<wf>","type":"add_to_workflow"}]
```
(APrestige: pageId `1005376745985153`, formId `26666569506358235`.)
Switching an existing tag-triggered WF to FB: POST the new facebook_lead_gen
trigger, then DELETE the old contact_tag trigger.

## THE STANDARD WF-01 ENTRY BLOCK (do this on every build)
Order at the top of WF-01, BEFORE the email/SMS timeline:

1. **Update Contact Field — "Latest Opt-In"** = this offer's opt-in label.
   ```json
   {"type":"update_contact_field","actionType":"update_field_data",
    "fields":[{"field":"<CONTACT_LATEST_OPTIN_FIELD_UUID>","value":"<Offer Opt-In Label>",
               "title":"Latest Opt-In","type":"string","date":""}]}
   ```
   APrestige contact field UUID: `rcI7s4wk5E8SydAZ5WSe`. Merge tag `{{contact.latest_optin}}`.

2. **Find Opportunity** (multipath, forks Found / Not Found):
   ```json
   {"type":"find_opportunity","sorting":"latest","cat":"multi-path","convertToMultipath":true,
    "__customInputFields__":[{"__customInputs__":{},"filterField":"pipeline_id","value":"eq","secondValue":"<PIPELINE_ID>"}],
    "__customInputs__":{},
    "transitions":[
      {"id":"<FOUND_ID>","name":"Opportunity Found","fields":[],"meta":{"__branchKey__":"predefined_Opportunity Found"},"conditionType":"pre-defined"},
      {"id":"<NOTFOUND_ID>","name":"Opportunity Not Found","fields":[],"meta":{"__branchKey__":"predefined_Opportunity Not Found"},"conditionType":"pre-defined"}]}
   ```

3. **Opportunity Found → `internal_update_opportunity`** (Engagement):
   ```json
   {"type":"internal_update_opportunity","allowBackward":false,"__customInputFields__":[
     {"dataType":"SINGLE_OPTIONS","filterField":"pipelineId","value":"<PIPELINE_ID>","valueFieldType":"select","__customInputs__":{}},
     {"dataType":"SINGLE_OPTIONS","filterField":"pipelineStageId","value":"<STAGE_ENGAGEMENT>","valueFieldType":"select","__customInputs__":{}},
     {"dataType":"TEXT","filterField":"custom_fields.<OPP_LATEST_OPTIN_FIELD>","value":"{{contact.latest_optin}}","valueFieldType":"string","__customInputs__":{}},
     {"dataType":"TEXT","filterField":"source","value":"{{contact.source}}","valueFieldType":"string","__customInputs__":{}},
     {"dataType":"SINGLE_OPTIONS","filterField":"status","value":"open","valueFieldType":"select","__customInputs__":{}}],
    "__customInputs__":{}}
   ```

4. **Opportunity Not Found → `internal_create_opportunity`** (Engagement): same
   fields, plus top-level `"pipelineId":"<PIPELINE_ID>"`; no `pipelineId` in the
   customInputFields list (stageId/source/custom_fields/status only).

APrestige: PIPELINE_ID `AGdm3AvcscakYeyNKyvd` (FlowBot), Engagement
`27dd6a6f-8af0-40fc-b3e6-27f6002b0454`, opportunity custom field (Latest Opt-In)
`kLg64KQqKJnTTDLiD9LO`, `status:"open"`.

### Multipath wiring (link_steps can't do this — wire by hand)
```
update_contact_field  .next = find.id
find_opportunity      .next = [FOUND_transition.id, NOTFOUND_transition.id]   # ARRAY
  transition "Opportunity Found"     parent=find  .next = update_opp.id
    internal_update_opportunity      parent=foundTransition  .next = goto.id
      goto {type:"goto","targetNodeId": <FIRST_EMAIL_ID>}   # rejoin
  transition "Opportunity Not Found" parent=find  .next = create_opp.id
    internal_create_opportunity      parent=notFoundTransition  .next = <FIRST_EMAIL_ID>
first email (rejoin point) ... rest of the linear timeline
```
Both branches converge on the first email. Found branch rejoins via a `goto`
node; Not-Found branch's create `.next` points straight at the first email.
**The engine has no multipath builder yet** — until one exists, build this entry
block in the GHL UI (WF-01 on APrestige already has it), or extend the engine
with an `opportunity_entry_block()` helper + custom linker for WF-01.

## Reply handler / keyword recapture opportunity moves
Same principle: to move an opp on reply, use Find Opportunity → Found:update to
the new stage (Connected `7852d7c5-…873c778`). A standalone
`internal_update_opportunity` with NO preceding find is rejected ("corrupted
type"). (A standalone `internal_create_opportunity` saves but is the wrong
pattern — prefer find→update/create.)

## Assign user / internal alert
```python
def assign_user_step(name, user_id):
    return {"id": _uid(), "type": "assign_user", "name": name,
        "attributes": {"only_unassigned_contact": False, "total_index": 1,
            "traffic_split": "equally", "traffic_weightage": {user_id: 1},
            "traffic_index": [{"id": user_id, "indexes": [1]}],
            "user_list": [user_id], "type": "assign_user"}}
def internal_sms_alert_step(name, body):
    return {"id": _uid(), "type": "internal_notification", "name": name,
        "attributes": {"type": "sms",
            "sms": {"body": body, "userType": "assign", "attachments": []}}}
```
(APrestige Andrea user id `bgBaxTaIfRDjkPisLwjR`.)

## `_uid`
```python
import uuid
def _uid(): return str(uuid.uuid4())
```

## Known save-API failures
| Symptom | Cause | Fix |
|---------|-------|-----|
| "corrupted type" / 0 steps saved | `internal_update_opportunity` with NO preceding `find_opportunity` | put it under a Find Opportunity "Found" branch |
| Workflow has no trigger | `customer_reply` without `source_wf_key` | add the workflow filter |
| FB form never matches | formId sent as `==`/select | use `is-any-of` + array + multiselect |
| Duplicate workflows on 2nd run | engine has no update mode | `cleanup_deploy.py` before redeploy |
| 401 on deploy | stale id-token preferred | `prefer_refresh_token=True` (forced in deploy file & `_ghl.py`) |

## Verify after every deploy
`python3 scripts/deploy_verify.py <loc> --folder "<name>"` → require
`ALL GOOD: True`.
