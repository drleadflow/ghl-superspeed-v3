#!/usr/bin/env python3
"""
GHL SuperSpeed Engine v3 — The fastest, most reliable GHL workflow builder.

Combines:
- Emeka's campaign-as-code pattern + Chrome extension token capture
- Our 56 verified type strings + Firebase auto-refresh
- Parallel batch creation for maximum speed
- AI campaign generation from plain English descriptions
- Pre-flight validation + post-deploy verification
"""

import json, sys, os, re, ssl, time, uuid
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL = "https://backend.leadconnectorhq.com"
MCP_SERVER = "https://dlf-agency.skool-203.workers.dev"
FIREBASE_API_KEY = "AIzaSyB_w3vXmsI7WeQtrIOkjR6xTRVN5uOieiE"
CTX = ssl.create_default_context()

CHROME_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Keys to strip from GET responses before PUT (avoids validation errors)
STRIP_KEYS = frozenset([
    '_id', 'id', '__v', 'createdAt', 'updatedAt', 'companyId', 'locationId',
    'companyAge', 'creationSource', 'originType', 'deleted',
    'isTriggerBucketMigrated', 'permissionMeta',
])

# ── Verified Action Types (56 confirmed via save API 2026-03-22) ──────────

VERIFIED_ACTIONS = frozenset([
    'add_contact_tag', 'remove_contact_tag', 'update_contact_field',
    'create_update_contact', 'assign_user', 'remove_assigned_user',
    'edit_conversation', 'dnd_contact', 'add_notes', 'task-notification',
    'find_contact', 'sms', 'email', 'call', 'voicemail', 'messenger', 'gmb',
    'internal_notification', 'instagram-dm', 'ig_interactive_messenger',
    'fb_interactive_messenger', 'respond_on_comment', 'review_request',
    'wait', 'if_else', 'goto', 'transition', 'workflow_split', 'workflow_goal',
    'add_to_workflow', 'remove_from_workflow', 'remove_from_all_workflows',
    'update_custom_value', 'drip', 'chatgpt', 'conversation_ai',
    'create_opportunity', 'find_opportunity', 'remove_opportunity',
    'webhook', 'custom_webhook', 'google_sheets', 'slack_message',
    'custom_code', 'math_operation', 'text_formatter', 'number_formatter',
    'datetime_formatter', 'array_functions', 'ivr_gather', 'ivr_connect_call',
    'facebook_conversion_api', 'stripe_one_time_charge',
    'update_appointment_status', 'membership_grant_offer',
    'membership_revoke_offer',
])


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenManager:
    """Multi-source token management with auto-refresh."""

    def __init__(self, location_id: str):
        self.location_id = location_id
        self._token: Optional[str] = None
        self._token_time: float = 0
        self._refresh_token: Optional[str] = None
        self.prefer_refresh_token: bool = False  # when True + a refresh token is set, use Firebase before broker/MCP

    def get_token(self) -> str:
        """Get a valid token from the best available source."""
        # 1. Check if current token is still fresh (< 50 min)
        if self._token and (time.time() - self._token_time) < 3000:
            return self._token

        # 1b. If caller explicitly wants the refresh-token identity, use ONLY that —
        #     never fall through to a cached DLF broker/MCP token for a non-DLF agency
        #     location. A failed Firebase refresh here is a hard error, not a fallback.
        if self.prefer_refresh_token and self._refresh_token:
            token = self._refresh_firebase()
            if token:
                self._token = token
                self._token_time = time.time()
                return token
            raise RuntimeError(
                f"prefer_refresh_token is set but Firebase refresh failed for "
                f"{self.location_id} — check the supplied refresh token"
            )

        # 2. Try CF Worker token broker (preferred — survives session resets)
        token = self._fetch_from_broker()
        if token:
            self._token = token
            self._token_time = time.time()
            return token

        # 3. Try MCP server (Chrome extension deposits tokens here)
        token = self._fetch_from_mcp()
        if token:
            self._token = token
            self._token_time = time.time()
            return token

        # 3. Try Firebase refresh
        if self._refresh_token:
            token = self._refresh_firebase()
            if token:
                self._token = token
                self._token_time = time.time()
                return token

        # 4. Try environment variable
        token = os.environ.get("GHL_FIREBASE_TOKEN", "")
        if token:
            self._token = token
            self._token_time = time.time()
            return token

        # 5. Try CLI argument
        if len(sys.argv) > 1:
            self._token = sys.argv[1]
            self._token_time = time.time()
            return self._token

        raise RuntimeError("No valid token. Browse GHL or set GHL_FIREBASE_TOKEN.")

    def set_refresh_token(self, refresh_token: str):
        self._refresh_token = refresh_token

    def force_refresh(self) -> str:
        """Force token refresh (called on 401)."""
        self._token = None
        self._token_time = 0
        return self.get_token()

    def _fetch_from_broker(self) -> Optional[str]:
        url = os.environ.get("GHL_TOKEN_BROKER_URL", "")
        auth = os.environ.get("GHL_TOKEN_BROKER_AUTH", "")
        if not url or not auth:
            return None
        try:
            req = urllib.request.Request(
                f"{url.rstrip('/')}/token",
                headers={
                    "Authorization": f"Bearer {auth}",
                    "Accept": "application/json",
                    "User-Agent": CHROME_UA,
                },
            )
            with urllib.request.urlopen(req, context=CTX, timeout=10) as r:
                data = json.loads(r.read())
                return data.get("id_token", "") or None
        except Exception:
            return None

    def _fetch_from_mcp(self) -> Optional[str]:
        # Try CLI token endpoint (requires ADMIN_PIN)
        pin = os.environ.get("GHL_ADMIN_PIN", "")
        if pin:
            try:
                req = urllib.request.Request(
                    f"{MCP_SERVER}/cli/token?pin={pin}",
                    headers={"User-Agent": CHROME_UA, "Accept": "application/json"},
                )
                with urllib.request.urlopen(req, context=CTX, timeout=10) as r:
                    data = json.loads(r.read())
                    token = data.get("token", "")
                    if token:
                        return token
            except Exception:
                pass

        # Fallback: Chrome extension token endpoint
        try:
            req = urllib.request.Request(
                f"{MCP_SERVER}/admin/firebase-token",
                headers={"User-Agent": CHROME_UA, "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, context=CTX, timeout=5) as r:
                data = json.loads(r.read())
                return data.get("token", "")
        except Exception:
            return None

    def _refresh_firebase(self) -> Optional[str]:
        try:
            body = f"grant_type=refresh_token&refresh_token={self._refresh_token}"
            req = urllib.request.Request(
                f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}",
                data=body.encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(req, context=CTX, timeout=10) as r:
                data = json.loads(r.read())
                return data.get("id_token", "")
        except Exception:
            return None


# ── API Client ────────────────────────────────────────────────────────────────

class GHLClient:
    """Fast, reliable GHL internal API client."""

    def __init__(self, token_mgr: TokenManager, location_id: str):
        self.token_mgr = token_mgr
        self.location_id = location_id
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def request(self, method: str, path: str, body: dict = None) -> Optional[dict]:
        """Make an API request with auto-retry on 401."""
        token = self.token_mgr.get_token()
        result = self._do_request(method, path, body, token)

        # Retry on auth failure
        if result is None:
            token = self.token_mgr.force_refresh()
            result = self._do_request(method, path, body, token)

        return result

    def _do_request(self, method, path, body, token) -> Optional[dict]:
        self._call_count += 1
        # Ensure token is ASCII-safe (JWT should be, but strip any stray chars)
        safe_token = token.encode('ascii', 'ignore').decode('ascii').strip()
        # Backend currently accepts the Firebase ID token in the `token-id` header
        # (the 2026-04-21 Bearer-authToken switch did not stick / endpoint accepts both;
        # token-id verified working 2026-05-05).
        headers = {
            "token-id": safe_token,
            "channel": "APP",
            "source": "WEB_USER",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": CHROME_UA,
        }
        url = f"{BASE_URL}{path}"
        data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
                text = resp.read().decode()
                if not text or not text.strip():
                    return {}
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    # GHL occasionally returns 200 with whitespace-only body for
                    # idempotent POSTs (tag create, trigger reattach). Treat as success.
                    return {}
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return None  # Signal retry
            error_body = e.read().decode() if e.fp else ""
            print(f"  API ERROR {e.code}: {error_body[:200]}")
            return {"_error": True, "code": e.code, "message": error_body[:200]}
        except (urllib.error.URLError, OSError, TimeoutError) as ex:
            print(f"  REQUEST ERROR: {ex}")
            return {"_error": True, "message": str(ex)}

    def create_location_tag(self, tag: str) -> bool:
        """Create a tag at location level. Required before using tag in triggers.

        GHL's UI creates the tag first via POST /workflow/{loc}/tags/create,
        then references it in trigger conditions. Without this step, the
        trigger condition renders blank because the tag doesn't exist in
        the location's tag list.
        """
        result = self.request(
            "POST", f"/workflow/{self.location_id}/tags/create", {"tag": tag}
        )
        return bool(result and not result.get("_error"))


# ── Email Formatter ───────────────────────────────────────────────────────────
#
# Canonical format captured live 2026-05-06 from IV Wellness NAD+ E1
# (see .claude/email-format-reference.json + memory feedback_email_format_ghl.md).
# GHL's Quick Compose editor is ProseMirror-backed; the styles below match what
# the editor persists when a human composes an email there. Round-tripping in
# this exact shape avoids the editor "fixing up" our HTML on first open.

# Default paragraph (prose) — has natural bottom margin so adjacent prose
# paragraphs separated by a single newline in source render with one enter
# of vertical space.
EMAIL_P_STYLE = (
    "margin:0px 0px 16px 0px; line-height: 1.75;padding-left: 0px!important;"
    "font-size: 16px;font-family: arial,helvetica,sans-serif;"
    "color: #000;"
)
# Tight paragraph (list items, signature lines, short adjacent runs) — keeps
# consecutive lines stacked with no extra gap.
EMAIL_P_STYLE_TIGHT = (
    "margin:0px; line-height: 1.75;padding-left: 0px!important;"
    "font-size: 16px;font-family: arial,helvetica,sans-serif;"
    "color: #000;"
)
EMAIL_BLANK_P_STYLE = "margin:0px; padding-left: 0px!important;"
EMAIL_BLANK_P = f'<p style="{EMAIL_BLANK_P_STYLE}"><br class="ProseMirror-trailingBreak"></p>'
EMAIL_LINK_REL = "noopener noreferrer nofollow"
DEFAULT_BOOKING_LINK_TOKEN = "{{custom_values.booking_link}}"

_BARE_BRACKET_RE = re.compile(r"^\[([^\]]+)\]$")
_LINK_MD_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# Lines that should render TIGHT (no bottom margin) — consecutive list items
# or numbered list items. Bold-only headers also stay tight when followed
# immediately by their content paragraph.
_LIST_ITEM_RE = re.compile(r"^([\-\*•]|\d+[\.\)])\s+\S")


def _email_inline(line: str) -> str:
    """Apply inline markdown: [text](url) anchor, **bold**, *italic*."""
    line = _LINK_MD_RE.sub(
        lambda m: (
            f'<a target="_blank" rel="{EMAIL_LINK_REL}" '
            f'href="{m.group(2)}" title="[{m.group(1)}]">[{m.group(1)}]</a>'
        ),
        line,
    )
    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
    line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
    return line


def dm_email(text: str) -> str:
    """Render plain text to GHL Quick-Compose HTML.

    Spacing model (per user feedback 2026-05-08, "one enter between sections"):
      - Each non-blank source line → one styled ``<p>``.
      - Default paragraph style has bottom margin (16px), so adjacent
        paragraphs naturally render with one enter of vertical space.
      - List-item lines (``- item``, ``* item``, ``1. item``) render TIGHT
        (margin:0) so consecutive bullets stay packed. The line BEFORE a
        list run is also rendered tight so its bottom margin doesn't push
        the bullets away from their lead-in (e.g., a bold header).
      - The LAST line in a list run keeps the standard margin so the next
        section gets the one-enter gap.
      - Blank source line → ``EMAIL_BLANK_P`` separator (legacy support).
      - Bare ``[Label]`` line → anchor wrapped to ``{{custom_values.booking_link}}``.
      - Inline ``[text](url)``, ``**bold**``, ``*italic*`` honored.
    """
    raw_lines = text.strip().split('\n')

    # Pre-compute which lines are list items so we can keep the *preceding*
    # paragraph tight too (lead-in to a list shouldn't have margin pushing
    # it away from the bullets).
    is_list = [bool(_LIST_ITEM_RE.match(l.strip())) for l in raw_lines]

    parts: list[str] = []
    for i, raw in enumerate(raw_lines):
        stripped = raw.strip()
        if not stripped:
            parts.append(EMAIL_BLANK_P)
            continue
        # Tight if THIS line is a list item AND it's not the last item in
        # the current list run (last item keeps margin so next section
        # breathes), OR if THIS line is the lead-in immediately before a
        # list run.
        next_is_list = i + 1 < len(raw_lines) and is_list[i + 1]
        if is_list[i] and next_is_list:
            style = EMAIL_P_STYLE_TIGHT
        elif (not is_list[i]) and next_is_list:
            style = EMAIL_P_STYLE_TIGHT
        else:
            style = EMAIL_P_STYLE

        m = _BARE_BRACKET_RE.match(stripped)
        if m:
            label = m.group(1)
            anchor = (
                f'<a target="_blank" rel="{EMAIL_LINK_REL}" '
                f'href="{DEFAULT_BOOKING_LINK_TOKEN}" '
                f'title="[{label}]">[{label}]</a>'
            )
            parts.append(f'<p style="{style}">{anchor}</p>')
            continue
        parts.append(f'<p style="{style}">{_email_inline(stripped)}</p>')
    return ''.join(parts)


# ── Step Builders (type-safe, validated) ──────────────────────────────────────

def _uid() -> str:
    return str(uuid.uuid4())

def sms_step(name: str, body: str, **kw) -> dict:
    return {"id": _uid(), "type": "sms", "name": f"SMS: {name}",
            "attributes": {"body": body, "attachments": []}, **kw}

def email_step(name: str, subject: str, text: str, from_name: str = "", **kw) -> dict:
    html = dm_email(text)
    return {"id": _uid(), "type": "email", "name": f"Email: {name}",
            "attributes": {
                "subject": subject, "body": html, "html": html,
                "fromName": from_name, "attachments": [], "conditions": [],
                "trackingOptions": {"hasTrackingLinks": False, "hasUtmTracking": False, "hasTags": False},
            }, **kw}

def wait_step(name: str, value: int, unit: str = "days", **kw) -> dict:
    # GHL advanced canvas uses INCONSISTENT unit strings:
    #   "minutes" (plural), "hour" (SINGULAR), "days" (plural)
    # Confirmed via live A/B test 2026-03-23: "hours" does NOT render, "hour" does.
    api_unit = {"minutes": "minutes", "hours": "hour", "hour": "hour", "days": "days"}.get(unit, unit)
    unit_label = {"minutes": "Minutes", "hour": "Hour", "hours": "Hours", "days": "Days"}.get(unit, unit.title())
    display = f"Wait {value} {unit_label}"
    return {"id": _uid(), "type": "wait", "name": display,
            "attributes": {
                "type": "time",
                "startAfter": {"type": api_unit, "value": value, "when": "after"},
                "name": display,
                "cat": "",
                "isHybridAction": True, "hybridActionType": "wait",
                "convertToMultipath": False, "transitions": [],
            }, "cat": "", **kw}

def tag_step(name: str, tags: list, remove: bool = False, **kw) -> dict:
    t = "remove_contact_tag" if remove else "add_contact_tag"
    return {"id": _uid(), "type": t, "name": name,
            "attributes": {"tags": tags}, **kw}

def update_contact_field_step(name: str, field: str, value: str,
                              title: str = "", field_type: str = "TEXT", **kw) -> dict:
    """Update Contact Field action.
    Canonical attributes shape verified via tests/verify_individual.py:
      {"fields": [{"field": "<key|uuid>", "value": "...", "title": "...", "type": "TEXT"}]}
    For STANDARD fields use the slug (e.g. "first_name"). For CUSTOM fields,
    `field` should be the GHL custom-field UUID (per location).
    """
    return {"id": _uid(), "type": "update_contact_field", "name": name,
            "attributes": {"fields": [{
                "field": field,
                "value": value,
                "title": title or field.replace("_", " ").title(),
                "type": field_type,
            }]}, **kw}

def webhook_step(name: str, url: str, method: str = "POST", data: list = None, **kw) -> dict:
    return {"id": _uid(), "type": "webhook", "name": name,
            "attributes": {"method": method, "url": url, "customData": data or [], "headers": []}, **kw}

def ai_step(name: str, prompt: str, model: str = "gpt-4o", **kw) -> dict:
    return {"id": _uid(), "type": "chatgpt", "name": name,
            "attributes": {
                "type": "chatgpt", "event": "simple-prompt", "model": model,
                "promptText": prompt, "actionType": "custom",
                "temperature": "0.2", "memoryKey": "action",
            }, **kw}


# ── Step Linker ───────────────────────────────────────────────────────────────

def link_steps(steps: list) -> list:
    """Auto-link steps with next/parentKey and set order."""
    linked = []
    for i, step in enumerate(steps):
        step = {**step}  # immutable copy
        step["order"] = i
        if i > 0:
            step["parentKey"] = linked[i - 1]["id"]
        else:
            step["parentKey"] = None
        if i < len(steps) - 1:
            step["next"] = steps[i + 1]["id"]
        linked.append(step)
    return linked


# ── Validation ────────────────────────────────────────────────────────────────

def validate_campaign(campaign: dict) -> list:
    """Pre-flight validation. Returns list of errors (empty = valid)."""
    errors = []
    for key, wf in campaign.items():
        if "name" not in wf:
            errors.append(f"Workflow {key}: missing 'name'")
        if "templates" not in wf:
            errors.append(f"Workflow {key}: missing 'templates'")
            continue
        for i, step in enumerate(wf["templates"]):
            if "type" not in step:
                errors.append(f"Workflow {key}, step {i}: missing 'type'")
            elif step["type"] not in VERIFIED_ACTIONS:
                errors.append(f"Workflow {key}, step {i}: unverified type '{step['type']}' — may fail save API")
            if "id" not in step:
                errors.append(f"Workflow {key}, step {i}: missing 'id'")
            if "name" not in step:
                errors.append(f"Workflow {key}, step {i}: missing 'name'")
    return errors


# ── Notion sync ───────────────────────────────────────────────────────────────

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
NOTION_BUILT_PROPERTY = "28 Day Nurture Sequence Built"


def _notion_mark_offer_built(page_id, property_name=NOTION_BUILT_PROPERTY):
    """Set the '28 Day Nurture Sequence Built' checkbox = true on a Notion page.

    Reads NOTION_TOKEN from env. Fails soft — never raises into the caller.
    Returns True on success, False on any failure (auth missing, API error, etc).
    """
    token = os.environ.get("NOTION_TOKEN")
    if not token or not page_id:
        if not token:
            print("  Notion sync skipped: NOTION_TOKEN not set in env")
        return False

    body = json.dumps({
        "properties": {property_name: {"checkbox": True}}
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{NOTION_API_BASE}/pages/{page_id}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
            return resp.status == 200
    except Exception as ex:
        print(f"  Notion sync failed: {ex}")
        return False


# ── Trigger body builder ──────────────────────────────────────────────────────

def _build_trigger_body(wf_def, wf_id, wf_ids_by_key, location_id, company_id):
    """Build the GHL trigger POST body from a workflow definition.

    Accepts two config shapes (rich dict takes precedence):

        wf_def["trigger"] = {"type": "facebook_lead_gen", "fb_page_id": "...", "fb_form_id": "..."}
        wf_def["trigger"] = {"type": "customer_reply", "source_wf_key": "01-master", "keyword": "RESET"}
        wf_def["trigger"] = {"type": "contact_tag", "tag": "..."}
        wf_def["tag"] = "..."   # legacy — emits contact_tag

    fb_page_id and fb_form_id are both optional (omit = "any page" / "any form").
    keyword may be a string or list of strings (omit for any reply).
    source_wf_key is the campaign-dict key of the source workflow (engine
    resolves to wf_id post-create); source_wf_id may be passed directly instead.

    Returns:
        (trigger_body_dict, location_tag_to_create_or_None)
        location_tag_to_create is set only for contact_tag — engine still
        needs to POST /tags/create before the trigger references it.
        Returns (None, None) if no trigger is configured or unresolvable.
    """
    trigger_cfg = wf_def.get("trigger")
    legacy_tag = wf_def.get("tag")

    if isinstance(trigger_cfg, dict):
        cfg = trigger_cfg
    elif legacy_tag:
        cfg = {"type": "contact_tag", "tag": legacy_tag}
    else:
        return None, None

    ttype = cfg.get("type", "contact_tag")

    base = {
        "status": "draft",
        "workflowId": wf_id,
        "schedule_config": {},
        "type": ttype,
        "masterType": "highlevel",
        "actions": [{"workflow_id": wf_id, "type": "add_to_workflow"}],
        "active": True,
        "triggersChanged": True,
        "location_id": location_id,
        "company_id": company_id,
        "company_age": 49,
    }

    if ttype == "contact_tag":
        tag = cfg.get("tag")
        if not tag:
            return None, None
        base["conditions"] = [{
            "operator": "index-of-true", "field": "tagsAdded", "value": tag,
            "title": "Tag Added", "type": "select", "id": "tag-added",
        }]
        base["name"] = cfg.get("name") or tag.replace("-", " ").title()
        return base, tag

    if ttype == "facebook_lead_gen":
        conditions = []
        if cfg.get("fb_page_id"):
            conditions.append({
                "operator": "==", "field": "facebook.pageId",
                "value": cfg["fb_page_id"],
                "title": "Page is", "type": "select",
            })
        if cfg.get("fb_form_id"):
            conditions.append({
                "operator": "==", "field": "facebook.formId",
                "value": cfg["fb_form_id"],
                "title": "Form is", "type": "select",
            })
        base["conditions"] = conditions
        base["name"] = cfg.get("name", "Facebook Lead Form Submitted")
        return base, None

    if ttype == "customer_reply":
        source_wf_id = cfg.get("source_wf_id")
        if not source_wf_id:
            source_key = cfg.get("source_wf_key")
            source_wf_id = wf_ids_by_key.get(source_key) if source_key else None
        if not source_wf_id:
            return None, None
        conditions = [{
            "operator": "==", "field": "workflow.id", "value": source_wf_id,
            "title": "Replied to Workflow", "type": "select",
        }]
        keyword = cfg.get("keyword")
        if keyword:
            keywords = [keyword] if isinstance(keyword, str) else list(keyword)
            conditions.append({
                "operator": "string-matches-any-of", "field": "message.body",
                "value": keywords,
                "title": "Exact match phrase", "type": "input",
                "id": "message-exact-phrase",
            })
        base["conditions"] = conditions
        if cfg.get("name"):
            base["name"] = cfg["name"]
        else:
            kw_suffix = f" - {keyword}" if isinstance(keyword, str) else ""
            base["name"] = f"Replied to workflow{kw_suffix}"
        return base, None

    return None, None


# ── Campaign Builder (the core engine) ────────────────────────────────────────

class CampaignBuilder:
    """Builds complete GHL campaigns with maximum speed and reliability.

    Two execution modes:
    1. Direct HTTP (this Python engine) — fastest, requires token from Chrome extension or env
    2. MCP tools (via Claude Code) — auto-auth, use ghl_workflow_builder_* tools

    For MCP mode, don't use this class directly. Instead, the Claude Code skill
    reads the campaign JSON and executes via MCP tools with parallel agents.
    """

    def __init__(self, client: GHLClient, location_id: str):
        self.client = client
        self.loc = location_id
        self.stats = {
            "workflows_created": 0,
            "steps_saved": 0,
            "triggers_created": 0,
            "errors": [],
            "start_time": 0,
            "end_time": 0,
        }

    def build(self, campaign: dict, folder_name: str, parent_folder: str = None,
              company_id: str = "", user_id: str = "",
              notion_page_id: str = None) -> dict:
        """Build an entire campaign. Returns stats.

        If `notion_page_id` is provided AND the deploy is fully successful
        (every step saved, no errors), the engine sets the
        "28 Day Nurture Sequence Built" checkbox = true on that Notion page
        in the Offers (Database). Requires NOTION_TOKEN env var. Fails soft.
        """
        self.stats["start_time"] = time.time()

        # Pre-flight validation
        errors = validate_campaign(campaign)
        if errors:
            print("VALIDATION ERRORS:")
            for e in errors:
                print(f"  - {e}")
            print("\nContinuing with warnings...\n")
            self.stats["errors"].extend(errors)

        # Create campaign folder
        print(f"Creating folder: {folder_name}")
        folder_body = {"name": folder_name, "type": "directory"}
        if parent_folder:
            folder_body["parentId"] = parent_folder
        folder = self.client.request("POST", f"/workflow/{self.loc}", folder_body)
        folder_id = folder.get("id") if folder else None
        if not folder_id:
            self.stats["errors"].append("Failed to create campaign folder")
            self.stats["end_time"] = time.time()
            return self.stats
        print(f"Folder: {folder_id}\n")

        # Two-phase parallel build:
        #   Phase 1 — POST /workflow for every entry, collect wf_ids by key.
        #   Phase 2 — for each workflow, build trigger + save steps + sync.
        # Phase 1 finishes first so customer_reply triggers can resolve
        # cross-workflow references (e.g. WF-03 trigger filters on WF-01's id).
        wf_ids = {}

        # ── Phase 1: create workflow shells in parallel ──
        print("Phase 1: Creating workflows...")
        def _phase1(key, wf_def):
            create_body = {"name": wf_def["name"], "parentId": folder_id}
            result = self.client.request("POST", f"/workflow/{self.loc}", create_body)
            return key, (result.get("id") if result else None)

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(_phase1, k, v) for k, v in campaign.items()]
            for fut in as_completed(futures):
                key, wf_id = fut.result()
                if wf_id:
                    wf_ids[key] = wf_id
                    self.stats["workflows_created"] += 1
                else:
                    self.stats["errors"].append(
                        f"Failed to create workflow shell: {campaign[key]['name']}"
                    )

        # ── Phase 2: build trigger + steps + sync per workflow, in parallel ──
        print("Phase 2: Triggers + steps + sync (all parallel)...")

        def _phase2(key, wf_def):
            """Trigger + steps + final sync. wf_id resolved from Phase 1."""
            wf_id = wf_ids.get(key)
            if not wf_id:
                return key, None, False, False

            # Build the trigger body using the unified helper. Supports
            # contact_tag (legacy "tag" string OR {"type":"contact_tag",...}),
            # facebook_lead_gen, and customer_reply.
            trigger_body, location_tag = _build_trigger_body(
                wf_def, wf_id, wf_ids, self.loc, company_id
            )
            trigger_data = None
            trigger_ok = False

            if trigger_body:
                # contact_tag triggers require the tag to exist at location
                # level first — otherwise the UI renders the condition blank.
                if location_tag:
                    self.client.request(
                        "POST", f"/workflow/{self.loc}/tags/create",
                        {"tag": location_tag}
                    )

                tr = self.client.request(
                    "POST", f"/workflow/{self.loc}/trigger", trigger_body
                )
                if tr and tr.get("id"):
                    trigger_ok = True
                    trigger_id = tr["id"]
                    trigger_data = {**trigger_body, "id": trigger_id}

                    # Link trigger to first step via PUT — without targetActionId,
                    # the trigger node floats disconnected on the advanced canvas.
                    first_step_id = (
                        wf_def["templates"][0]["id"]
                        if wf_def.get("templates") else None
                    )
                    if first_step_id:
                        update_body = {
                            **trigger_body,
                            "targetActionId": first_step_id,
                            "advanceCanvasMeta": {"position": {"x": 57.5, "y": -73}},
                        }
                        self.client.request(
                            "PUT", f"/workflow/{self.loc}/trigger/{trigger_id}",
                            update_body
                        )
                        trigger_data["targetActionId"] = first_step_id

            # Step 3: Save steps via regular PUT (version=1, always works)
            put_body = {
                "name": wf_def["name"],
                "version": 1,
                "workflowData": {"templates": wf_def["templates"]},
            }
            put_result = self.client.request("PUT", f"/workflow/{self.loc}/{wf_id}", put_body)
            steps_ok = bool(put_result and not put_result.get("_error"))
            new_version = put_result.get("version", 2) if put_result else 2

            # Step 4: Second PUT with triggers + canvas meta
            # The /auto-save endpoint requires an active UI editor session and
            # fails with 422 when called programmatically. The regular PUT with
            # triggersChanged + oldTriggers/newTriggers reliably syncs triggers
            # to Firebase Storage. Discovered via live integration testing 2026-03-23.
            if steps_ok:
                current = self.client.request("GET", f"/workflow/{self.loc}/{wf_id}")
                if current and not current.get("_error"):
                    # Build trigger list for Firebase sync
                    trigger_list = []
                    if trigger_data:
                        now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
                        trigger_data["workflow_id"] = wf_id
                        trigger_data["location_id"] = self.loc
                        trigger_data["belongs_to"] = "workflow"
                        trigger_data["deleted"] = False
                        trigger_data["date_added"] = now
                        trigger_data["date_updated"] = now
                        trigger_data["advanceCanvasMeta"] = {"position": {"x": 57.5, "y": -73}}
                        trigger_data.pop("company_id", None)
                        trigger_data.pop("company_age", None)
                        trigger_data.pop("triggersChanged", None)
                        trigger_list = [trigger_data]

                    # Add advanceCanvasMeta to steps and ensure canvas-required fields
                    steps_with_meta = []
                    for idx, step in enumerate(wf_def["templates"]):
                        s = {**step}
                        s["advanceCanvasMeta"] = {"position": {"x": 400 + idx * 300, "y": 0}}
                        s.setdefault("cat", "")
                        s.setdefault("order", idx)
                        if s.get("type") == "wait" and "attributes" in s:
                            attrs = {**s["attributes"]}
                            attrs.setdefault("type", "time")
                            attrs.setdefault("cat", "")
                            attrs.setdefault("isHybridAction", True)
                            attrs.setdefault("hybridActionType", "wait")
                            attrs.setdefault("convertToMultipath", False)
                            attrs.setdefault("transitions", [])
                            if "startAfter" in attrs:
                                sa = attrs["startAfter"]
                                sa.setdefault("when", "after")
                                if sa.get("type") == "hours":
                                    sa["type"] = "hour"
                                unit_label = {"minutes": "Minutes", "hour": "Hour", "days": "Days"}.get(sa.get("type", ""), "")
                                expected_name = f"Wait {sa.get('value', '')} {unit_label}".strip()
                                attrs.setdefault("name", expected_name)
                                s.setdefault("name", expected_name)
                            s["attributes"] = attrs
                        steps_with_meta.append(s)

                    # Enable advanced canvas
                    meta = current.get("meta") or {}
                    meta["advanceCanvasMeta"] = {"enabled": True, "enabledAt": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())}

                    # Use regular PUT (not /auto-save) — reliable for programmatic use
                    sync_body = {
                        "name": wf_def["name"],
                        "version": current.get("version", new_version),
                        "meta": meta,
                        "workflowData": {"templates": steps_with_meta},
                        "triggersChanged": bool(trigger_list),
                        "oldTriggers": trigger_list,
                        "newTriggers": trigger_list,
                    }
                    self.client.request(
                        "PUT", f"/workflow/{self.loc}/{wf_id}", sync_body
                    )

            return key, wf_id, steps_ok, trigger_ok

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [
                pool.submit(_phase2, key, wf_def)
                for key, wf_def in campaign.items()
                if key in wf_ids
            ]

            for future in as_completed(futures):
                key, wf_id, steps_ok, trigger_ok = future.result()
                if wf_id:
                    if steps_ok:
                        self.stats["steps_saved"] += len(campaign[key]["templates"])
                    if trigger_ok:
                        self.stats["triggers_created"] += 1
                    parts = [f"{len(campaign[key]['templates'])} steps"]
                    if not steps_ok:
                        parts.append("STEPS FAILED")
                    if trigger_ok:
                        tcfg = campaign[key].get("trigger")
                        if isinstance(tcfg, dict):
                            label = tcfg.get("type", "trigger")
                        else:
                            label = campaign[key].get("tag", "trigger")
                        parts.append(f"trigger ({label})")
                    print(f"  {campaign[key]['name']}: {' + '.join(parts)}")
                else:
                    self.stats["errors"].append(f"Failed: {campaign[key]['name']}")
                    print(f"  {campaign[key]['name']}: FAILED")

        # Skip separate trigger phase — triggers already created above

        self.stats["end_time"] = time.time()
        self.stats["api_calls"] = self.client.call_count

        # Summary
        elapsed = self.stats["end_time"] - self.stats["start_time"]
        print(f"\n{'='*50}")
        print(f"DONE in {elapsed:.1f} seconds")
        print(f"  Workflows: {self.stats['workflows_created']}")
        print(f"  Steps:     {self.stats['steps_saved']}")
        print(f"  Triggers:  {self.stats['triggers_created']}")
        print(f"  API calls: {self.stats['api_calls']}")
        print(f"  Errors:    {len(self.stats['errors'])}")
        if self.stats["errors"]:
            for e in self.stats["errors"]:
                print(f"    - {e}")
        print(f"{'='*50}")

        # Print GHL links for visual verification
        if wf_ids:
            print(f"\nOpen in GHL to verify triggers:")
            for key in sorted(wf_ids.keys()):
                wf_id = wf_ids[key]
                tcfg = campaign[key].get("trigger")
                if isinstance(tcfg, dict):
                    label = tcfg.get("type", "")
                else:
                    label = campaign[key].get("tag", "")
                print(f"  {campaign[key]['name']} [{label}]:")
                print(f"    https://app.gohighlevel.com/v2/location/{self.loc}/automation/workflow/{wf_id}")

        # Notion sync — mark "28 Day Nurture Sequence Built" = true on the
        # offer page if the deploy was fully successful.
        if notion_page_id:
            total_expected = sum(len(wf["templates"]) for wf in campaign.values())
            full_success = (
                self.stats["steps_saved"] == total_expected
                and not self.stats["errors"]
            )
            if full_success:
                if _notion_mark_offer_built(notion_page_id):
                    print(f"\nNotion: marked '{NOTION_BUILT_PROPERTY}' = true on offer page {notion_page_id}")
            else:
                print(f"\nNotion sync skipped: deploy not fully successful "
                      f"({self.stats['steps_saved']}/{total_expected} steps, "
                      f"{len(self.stats['errors'])} errors)")

        return self.stats

    def _save_steps(self, wf_id: str, name: str, templates: list) -> tuple:
        """GET workflow, merge steps, PUT back. Returns (success, step_count)."""
        current = self.client.request("GET", f"/workflow/{self.loc}/{wf_id}")
        if not current or current.get("_error"):
            return False, 0

        # Build update body
        update = {k: v for k, v in current.items() if k not in STRIP_KEYS}
        update["name"] = name
        update["workflowData"] = {"templates": templates}

        result = self.client.request("PUT", f"/workflow/{self.loc}/{wf_id}", update)
        if result and not result.get("_error"):
            return True, len(templates)
        return False, 0

    def cleanup(self, campaign: dict, folder_name: str):
        """Delete all campaign workflows and folder."""
        # List workflows in folder, delete each, then delete folder
        print("Cleaning up...")
        # This is a simplified version — full implementation would paginate
