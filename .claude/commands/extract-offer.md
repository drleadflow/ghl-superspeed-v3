# /extract-offer

**Usage:** `/extract-offer <notion-url>`

Pulls an offer from the DLF Notion `🗄️ Offers (Database)` and writes a vault-native `offers/<client>-<offer>.md` file ready for `/build-sequence` to consume.

---

## What this command does

1. Fetches the Notion page via `mcp__claude_ai_Notion__notion-fetch`
2. Auto-derives slugs:
   - `client_slug` from Notion `Clinic Name` property → kebab-case (e.g., `IV-Wellness` → `iv-wellness`)
   - `offer_slug` from Notion `Offer Name` → kebab-case, max 4 words (e.g., `First IV Drip — $50 Off Welcome Offer` → `first-drip-welcome`)
3. Maps Notion properties → frontmatter (see Property Map below)
4. Surfaces missing/synthesis-required fields BEFORE writing
5. Writes `offers/<client>-<offer>.md`
6. Updates `clients/<client>/offers.md` index (creates `clients/<client>/` if it doesn't exist)
7. If `services/` is empty for this client, prompts user about whether to populate from the offer's available delivery options (e.g., the 14 IV formulas)

## Property Map (Notion → frontmatter)

| Notion property | Frontmatter key | Notes |
|-----------------|-----------------|-------|
| `Offer Name` | `name` | |
| `Offer Type` | `offer_type` | |
| `Status` | `status` | "Live" → "active" |
| `Whats Included` | body section | |
| `Core Promise` | body section | |
| `Top 3 Objections` | `top_3_objections` (array) | parse from string |
| `Biggest Pain Point` | `biggest_pain_point` | |
| `Desired Outcome` | `desired_outcome` | |
| `Why Someone Says Yes` | `why_yes` | |
| `Top 3 Buying Triggers` | `buying_triggers` (array) | |
| `What Makes Ours Better` | `differentiators` | |
| `Has Deadline` | `has_deadline` (bool) | |
| `Deadline Date` | `deadline_date` | ISO; if empty + has_deadline=Yes, default to "TBD — confirm with client" |
| `Bonuses` | `bonuses` | |
| `Risk Reversal` | `risk_reversal` | |
| `Guarantee` | `guarantee` | |
| `Deposit Required` | `deposit_required` (bool) | |
| `Age Range` | `age_range` | |
| `Gender` | `gender` (array) | |
| `Geographic Radius` | `geographic_radius` | |
| `Consult Handler` | `consult_handler` | |
| `Specialty` | `specialty` | |
| `Booking Link` | `booking_link` | maps to `{{custom_values.booking_link}}` |
| `Before Afters Available` | `images_available` (bool) | "No" → no MMS at D0 T+1 |
| `Doctor Video Available` | `doctor_video` | |
| `Uses Bot` | `uses_bot` (bool) | |
| `Monthly Budget` | `monthly_budget` | |
| `Target CPL` | `target_cpl` | |
| `Last Updated` | `notion_last_updated` | |

Plus a `notion_url` field with the canonical Notion URL for back-reference, and `notion_offer_id` (the UUID).

## Body sections (markdown)

```
# {{name}}

**Client:** {{client}} · **Status:** {{status}} · **Type:** {{offer_type}}
**Notion:** {{notion_url}}

## Core Promise
{{core_promise}}

## What's Included
{{whats_included}}

## Top 3 Objections
1. ...
2. ...
3. ...

## Bonuses / Risk Reversal
- Bonuses: ...
- Risk reversal: ...
- Guarantee: ...

## Compliance Notes
(Auto-populated by niche detector — IV gets the strict-mode banner)

## Sequence Variables (for /build-sequence)

These map to Doc 1's 8 variables. Anything `TBD` must be filled by the user before /build-sequence runs.

- OFFER_NAME: {{name}}
- TREATMENT_TYPE: (synthesized from core_promise + whats_included)
- TOP_3_OBJECTIONS: {{top_3_objections}}
- WHAT_IT_DOESNT_DO: TBD
- HONEST_FLAW: TBD
- QUICK_WIN_TIPS: TBD
- DEADLINE_MATH: (from has_deadline + deadline_date + price)
- KEYWORD: TBD (suggestion: ...)

## Notes
{{any "Notes" section from Notion content}}
```

## Execution flow when invoked

1. **Try the local cache first (token-lean path):**
   - Run `python3 -m lib.notion_cache <url>` to fetch via the direct Notion API + last_edited_time cache.
   - On cache hit (page unchanged since last fetch), no body re-fetch — properties returned in <500 tokens.
   - On cache miss or stale, the cache layer fetches blocks once and stores them.
   - Auth: requires `NOTION_DLF_TOKEN` (or fallback `NOTION_TOKEN`) in `~/.env.secrets`. The integration must be invited to the DLF Offers DB. If 401/404, fall through to the MCP path below.
2. **MCP fallback (when token isn't configured or page isn't shared with the integration):**
   - Verify Notion MCP is loaded. If not: `ToolSearch` for `mcp__claude_ai_Notion__notion-fetch` first.
   - Call `notion-fetch` with the URL.
3. Validate the page is in `🗄️ Offers (Database)` by checking ancestor path. If it's not, abort with: "This page isn't in the Offers database. Pass an offer page URL."
4. Extract the property dict and content body. Note: the cache layer returns properties under `page['properties']` (Notion API shape) and content blocks under `page['_blocks']` (cache-only key). The MCP path returns rendered markdown; the property→frontmatter map below applies in both cases.
5. Build `client_slug` and `offer_slug`. Show them to user, allow override.
6. Build the markdown file in memory.
7. Surface a checklist of TBD fields:
   ```
   The following Doc 1 variables aren't in Notion. Defaults proposed:
   - WHAT_IT_DOESNT_DO: <my synthesized default>
   - HONEST_FLAW: <my synthesized default OR "I need this from you">
   - QUICK_WIN_TIPS: <my synthesized default>
   - KEYWORD: <suggestion>
   Confirm or override before I write the file.
   ```
8. After confirmation, write `offers/<client>-<offer>.md`.
9. If `clients/<client>/` doesn't exist, copy the `_template/` structure and fill in what we know.
10. Update `clients/<client>/offers.md` table to include this offer.
11. Update `offers/README.md` index table.
12. Report: file path, what was filled vs. TBD, what to do next (`/build-sequence <client>-<offer>` or fill TBDs first).

## Error handling

- Notion page not in Offers database → abort with explanation
- Notion MCP not authed → tell user to run `/mcp` and reconnect
- File would overwrite existing offer → ask "update or new slug?"
- Required Notion property missing (no `Offer Name`) → abort with which property is missing
- Client `clients/<slug>/` exists but is for different client (slug collision) → ask user for explicit slug

## Constraints

- Don't commit anything. User reviews diffs.
- Don't run `/build-sequence` automatically — they're separate commands.
- Don't fabricate data. TBD is the right answer when Notion is silent.
- Don't touch `lib/`, `tests/`, `.github/`, `.obsidian/`, engine code.
