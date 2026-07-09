# GHL SuperSpeed v3

Build complete GHL workflow campaigns in seconds, not hours. Programmatic workflow creation via GHL's internal API with parallel execution.

**Proven: 8 workflows, 45 steps, 8 triggers deployed in 3.2 seconds.**

> 📖 **Launching a client funnel?** Start with [docs/TAG-FUNNEL-PLAYBOOK.md](docs/TAG-FUNNEL-PLAYBOOK.md) — the repeatable landing-page → tag → SMS → AI-setter system (pages, workflows, tag flow, clone-for-new-client guide) with the [clickable system map](https://healthproceo-diagrams.vercel.app/?diagram=e2e-funnel-system).

---

## What This Does

You define a campaign in Python — workflows, steps (SMS, email, wait, tags), and triggers — then the engine builds everything in GHL simultaneously. All 8 workflows run their full pipeline in parallel.

```python
from lib.engine import *

CAMPAIGN = {
    "welcome": {
        "name": "Welcome Sequence",
        "tag": "new-lead",              # Trigger: fires when this tag is added
        "templates": link_steps([
            sms_step("Welcome", "Hey {{contact.first_name}}, welcome!"),
            wait_step("1 day", 1, "days"),
            email_step("Follow Up", "checking in", "Your follow-up email text here", "Dr. Name"),
            wait_step("2 hours", 2, "hours"),
            tag_step("Mark Done", ["welcome-complete"]),
        ]),
    }
}
```

Then run it:
```bash
python3 campaigns/your-campaign.py
```

Output:
```
Creating folder: Welcome Campaign
Building workflows + steps + triggers (all parallel)...
  Welcome Sequence: 5 steps + trigger (new-lead)
DONE in 1.1 seconds
```

---

## Setup (5 minutes)

### Step 1: Clone

```bash
git clone https://github.com/drleadflow/ghl-superspeed-v3.git
cd ghl-superspeed-v3
```

No pip install needed. Zero dependencies — uses only Python stdlib.

### Step 2: Get a Firebase Token

GHL's internal API uses Firebase JWT tokens (not OAuth). You need one of these auth methods:

#### Option A: MCP Server (Recommended — auto-refresh, never expires)

The DLF Agency MCP Server manages Firebase tokens automatically with a 55-minute KV cache and auto-refresh.

**To get access:** Email **info@doctorleadflow.com** with subject "SuperSpeed Access Request"

You'll receive an ADMIN_PIN. Then:

```bash
# One-liner to get a fresh token (valid ~55 min, auto-refreshes)
export GHL_ADMIN_PIN="your-pin"
export GHL_FIREBASE_TOKEN=$(curl -s "https://dlf-agency.skool-203.workers.dev/cli/token?pin=$GHL_ADMIN_PIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

#### Option B: Firebase Refresh Token (Self-hosted, never expires)

If you have your own GHL account:

1. Log into `app.gohighlevel.com`
2. Open Chrome DevTools > Application > IndexedDB > `firebaseLocalStorageDb` > `firebaseLocalStorage`
3. Click the entry — find `stsTokenManager.refreshToken`
4. Copy the refresh token (long string, never expires)

```bash
export GHL_FIREBASE_REFRESH_TOKEN="your-refresh-token"
```

The engine auto-refreshes this into a 1-hour ID token via Google's `securetoken.googleapis.com` API.

#### Option C: Direct ID Token (Quick test, expires in 1 hour)

From the same IndexedDB entry, copy `stsTokenManager.accessToken`:

```bash
export GHL_FIREBASE_TOKEN="eyJhbG..."
```

This expires in 1 hour. Fine for testing, not for production.

### Step 3: Set Your Location

Edit your campaign file with your GHL location ID:

```python
LOCATION_ID = "your-location-id"  # From GHL URL: app.gohighlevel.com/location/THIS_PART/...
```

### Step 4: Run

```bash
python3 campaigns/ppp-webinar.py
```

---

## How It Works

### The Pipeline (per workflow)

Each workflow runs this 6-step pipeline. All workflows execute in parallel.

```
1. POST /workflow/{loc}                    Create workflow in folder
2. POST /workflow/{loc}/tags/create        Create location tag (so trigger can reference it)
3. POST /workflow/{loc}/trigger            Create trigger with tag condition
4. PUT  /workflow/{loc}/trigger/{id}       Link trigger to first step (targetActionId)
5. PUT  /workflow/{loc}/{wfId}             Save action steps (templates array)
6. PUT  /workflow/{loc}/{wfId}             Sync triggers + enable advanced canvas
```

### Auth Flow

```
TokenManager tries sources in order:
  1. MCP Server /cli/token  (if GHL_ADMIN_PIN set)     — auto-refresh, recommended
  2. Firebase refresh token  (if GHL_FIREBASE_REFRESH_TOKEN set)  — self-hosted
  3. GHL_FIREBASE_TOKEN env var                          — direct, 1hr expiry
  4. CLI argument                                        — python3 script.py <token>
```

On 401, the engine auto-retries with a fresh token.

### API Headers

Every request to `backend.leadconnectorhq.com` needs:
```
token-id: <firebase-jwt>     (NOT Authorization: Bearer)
channel: APP
source: WEB_USER
Content-Type: application/json
```

---

## Proven Step Types (4 core types, fully tested)

These 4 types are battle-tested with correct schemas and UI rendering verified:

### SMS
```python
sms_step("Welcome", "Hey {{contact.first_name}}, welcome!")
```

### Email
```python
email_step("Follow Up", "subject line", "Plain text body (auto-converted to HTML)", "From Name")
```
The `dm_email()` formatter converts plain text with `**bold**` and `*italic*` to styled HTML.

### Wait
```python
wait_step("5 minutes", 5, "minutes")
wait_step("2 hours", 2, "hours")      # IMPORTANT: engine sends "hour" (singular) to API
wait_step("3 days", 3, "days")
```

**Critical:** GHL's canvas uses inconsistent unit strings: `minutes` (plural), `hour` (SINGULAR), `days` (plural). The engine handles this automatically — you always pass "hours" and it sends "hour" to the API.

### Contact Tag
```python
tag_step("Add VIP Tag", ["vip", "high-value"])
tag_step("Remove Old Tag", ["old-tag"], remove=True)
```

### Trigger (Contact Tag Added)
```python
# In your campaign dict, set the "tag" field:
"tag": "nurture-start"    # Creates a contact_tag trigger
```

The engine automatically:
1. Creates the tag at location level (`POST /workflow/{loc}/tags/create`)
2. Creates the trigger with the correct condition schema
3. Links the trigger to the first step via `targetActionId`

---

## Campaign Format

A campaign is a Python dict where each key is a workflow:

```python
CAMPAIGN = {
    "01": {
        "name": "01. Welcome Sequence",           # Workflow name in GHL
        "tag": "welcome-start",                    # Tag trigger (optional)
        "templates": link_steps([                  # Action steps (auto-linked)
            sms_step("SMS 1", "Hey!"),
            wait_step("1 day", 1, "days"),
            email_step("Email 1", "subject", "body text", "Sender"),
            wait_step("2 hours", 2, "hours"),
            sms_step("SMS 2", "Following up!"),
        ]),
    },
    "02": {
        "name": "02. Follow-Up",
        "tag": "follow-up-start",
        "templates": link_steps([
            email_step("Reminder", "don't forget", "Your reminder text"),
            wait_step("3 days", 3, "days"),
            tag_step("Mark Complete", ["sequence-done"]),
        ]),
    },
}
```

`link_steps()` handles:
- UUID generation for each step
- `order` numbering (0, 1, 2...)
- `parentKey` linking (each step points to its predecessor)
- `next` linking (each step points to its successor)

---

## Building Your Own Campaign

### 1. Create a new file

```bash
cp campaigns/ppp-webinar.py campaigns/my-campaign.py
```

### 2. Edit the config

```python
LOCATION_ID = "your-location-id"
PARENT_FOLDER = ""  # Leave empty for root, or set a folder ID
COMPANY_ID = "your-company-id"
USER_ID = "your-user-id"
```

### 3. Define your workflows

Use `sms_step()`, `email_step()`, `wait_step()`, and `tag_step()` inside `link_steps()`.

### 4. Run

```bash
GHL_FIREBASE_TOKEN="your-token" python3 campaigns/my-campaign.py
```

### 5. Verify in GHL

Open the workflow URLs printed in the output:
- **Classic builder:** `https://app.gohighlevel.com/location/{locationId}/workflow/{workflowId}`
- **Advanced canvas:** `https://app.gohighlevel.com/location/{locationId}/workflow/{workflowId}/advanced-canvas`

---

## Speed Benchmarks

| Campaign | Workflows | Steps | Triggers | Time | API Calls |
|----------|-----------|-------|----------|------|-----------|
| PPP Webinar | 8 | 45 | 8 | 3.2s | 58 |
| Single workflow | 1 | 5 | 1 | 0.8s | 8 |

Speed comes from `ThreadPoolExecutor` — all workflows run their full 6-step pipeline simultaneously.

---

## Gotchas (Hard-Won Knowledge)

### Wait "hour" is singular
GHL canvas uses `minutes` (plural), `hour` (SINGULAR), `days` (plural). Sending `"hours"` renders the number but not the unit label. The engine maps this automatically.

### Tags must exist before triggers reference them
`POST /workflow/{loc}/tags/create` with `{"tag": "name"}` BEFORE creating a trigger with that tag. Otherwise the trigger tag renders blank in the UI.

### Triggers need targetActionId
After creating a trigger via `POST /trigger`, update it with `PUT /trigger/{id}` including `targetActionId` pointing to the first step's UUID. Without this, the trigger floats disconnected on the advanced canvas.

### Version field is mandatory on PUT
Every `PUT /workflow/{loc}/{wfId}` must include `version` matching the current version. GHL increments on each save. Stale versions are rejected.

### Auto-save endpoint needs a UI session
`PUT /workflow/{loc}/{wfId}/auto-save` requires an active GHL editor session. For programmatic use, the regular `PUT` with `triggersChanged: true` + `oldTriggers`/`newTriggers` reliably syncs triggers to Firebase.

### Auth is Firebase JWT, not OAuth
Use the `token-id` header with a Firebase JWT. NOT `Authorization: Bearer`. Every request also needs `channel: APP`.

---

## File Structure

```
ghl-superspeed-v3/
  lib/engine.py              Core engine (TokenManager, GHLClient, CampaignBuilder, step builders)
  campaigns/ppp-webinar.py   Example: 8-workflow webinar campaign
  tests/test_engine.py       28 unit tests (all passing)
  tests/verify_individual.py Live API verification for all 56 action types
  tests/verify_consolidated.py  Consolidated 6-workflow verification test
  scripts/refresh-token.sh   Firebase JWT refresh helper
  templates/blueprints.json  Campaign blueprint templates
  chrome-extension/          Chrome extension for passive token capture
```

---

## Additional Action Types (53 verified, use with caution)

Beyond the 4 proven types, 53 total action types pass the save API. These are verified to SAVE but their UI rendering has not been fully validated:

`add_contact_tag`, `remove_contact_tag`, `update_contact_field`, `create_update_contact`, `assign_user`, `remove_assigned_user`, `edit_conversation`, `dnd_contact`, `add_notes`, `task-notification`, `find_contact`, `sms`, `email`, `call`, `voicemail`, `messenger`, `gmb`, `internal_notification`, `instagram-dm`, `ig_interactive_messenger`, `fb_interactive_messenger`, `respond_on_comment`, `review_request`, `wait`, `if_else`, `add_to_workflow`, `remove_from_workflow`, `remove_from_all_workflows`, `update_custom_value`, `drip`, `chatgpt`, `conversation_ai`, `webhook`, `custom_webhook`, `google_sheets`, `slack_message`, `custom_code`, `math_operation`, `text_formatter`, `number_formatter`, `datetime_formatter`, `array_functions`, `ivr_gather`, `ivr_connect_call`, `facebook_conversion_api`, `stripe_one_time_charge`, `update_appointment_status`, `membership_grant_offer`, `membership_revoke_offer`, `create_opportunity`, `remove_opportunity`, `workflow_split`, `transition`

3 types that fail save API due to structural requirements:
- `goto` — must be inside an `if_else` branch
- `find_opportunity` — needs a real `pipeline_id`
- `workflow_goal` — needs non-empty `segments[0].conditions`

---

## MCP Server Integration (Claude Code)

With MCP access, you get 18 workflow builder tools in Claude Code. Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "dlf-agency": {
      "type": "url",
      "url": "https://dlf-agency.skool-203.workers.dev/mcp"
    }
  }
}
```

For MCP access: **info@doctorleadflow.com**

---

## Tests

```bash
python3 tests/test_engine.py     # 28 unit tests, no API calls
```

---

## License

Private. Contact info@doctorleadflow.com for access.
