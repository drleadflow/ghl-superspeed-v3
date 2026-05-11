# /a2p-fill-values

**Usage:** `/a2p-fill-values <business_url> <location_id> [--client <slug>] [--refresh-token <token>]`

Populate the 18 custom values that the pre-built "A2P Landing Page" funnel + opt-in form
reference on a GHL sub-account. Scrapes the business website, optionally reads a vault
brief, generates the on-brand copy, previews everything as a dry run, then writes it.

**Does NOT touch** the funnel pages, the opt-in form, the other ~58 custom values, or any
workflow — those merge-tag off these 18 values and never change.

Examples:
- `/a2p-fill-values https://aprestigeaesthetics.com 9uog1fOUDtxkSr4ZPx1i --client prestige`
- `/a2p-fill-values https://example-medspa.com abc123LOCID`

---

## The 18 values (see `lib/a2p_values.py:A2P_VALUE_KEYS` for the canonical list)

Facts (resolve in priority order — brief → location API → site): `business_short_name`,
`business_profile__legal_business_name`, `business_profile__phone_number`, `from_email`,
`logo` (always the literal `{{location.logo_url}}`), `primary_color`, `secondary_color__hex_code`.

Copy (you generate from the scraped site + brief, in DLF brand voice — see `business/` for
voice/positioning if present): `about_us__description`, `business_welcome_message`,
`business_solution__description`, `our_services_1..4`, `our_services_1..4__description`.

## Steps

1. **Scrape the site** — run `python3 scripts/a2p_scrape.py <business_url>` and read the JSON.
   If it returns `{"error": ...}`, note it and continue with brief-only (you will flag the
   facts you can't source).

2. **Read the brief (optional)** — if `--client <slug>` was given, read whichever of these
   exist: `clients/<slug>/overview.md`, `clients/<slug>/services.md`. (`overview.md` may also
   carry `ghl_location_id` — sanity-check it against the `<location_id>` arg.)

3. **Resolve the 7 facts:**
   - `business_short_name` — the friendly trading name (brief > site `<title>` cleaned up).
   - `business_profile__legal_business_name` — the registered legal entity. Only from the
     brief. If absent, leave it BLANK — `a2p_apply.py` will flag it for the user to set from
     the Twilio registration. Never guess this.
   - `business_profile__phone_number` — brief first. If absent, you may leave blank (flagged);
     do not invent one. (A future enhancement may pull the location's purchased number via API.)
   - `from_email` — brief first; else `info@<registrable-domain-of-business_url>`.
   - `logo` — always the literal string `{{location.logo_url}}`.
   - `primary_color` / `secondary_color__hex_code` — pick from the scrape's `candidate_colors`
     only if you are reasonably confident they are brand colours (ignore obvious black/white/grey
     unless the brand clearly uses them). Otherwise leave blank — better empty than wrong.

4. **Write the 11 copy values** from the scraped `headings`/`text`/`meta_description` + brief,
   in DLF brand voice. Keep `our_services_N` to a short headline line and `our_services_N__description`
   to one sentence. If the business clearly offers fewer than 4 services, fill what's real and
   leave the rest blank (they'll be skipped, not blanked).

5. **Write the value map** to `/tmp/a2p-values-<location_id>.json` — a JSON object `{slug: value}`
   containing only the slugs you have content for.

6. **Dry run** — run:
   `python3 scripts/a2p_apply.py <location_id> /tmp/a2p-values-<location_id>.json --dry-run [--refresh-token <token>]`
   Show the user the full proposed value map and the dry-run report. Call out anything flagged
   for manual entry. For a non-DLF agency sub-account (e.g. Prestige), the `--refresh-token` is
   required (see the 'Non-DLF Agency deploy auth' memory).

7. **On the user's OK** — re-run the same command WITHOUT `--dry-run`. Report the result.

8. **Log it** — append a completion entry to `drleadflow/blade-ops/contents/logs/dev-activity.json`
   per this repo's `CLAUDE.md` (`message: "A2P custom values populated for <client/loc>"`).

## Notes

- Idempotent — safe to re-run; values that didn't change get PUT with the same content.
- If you see GHL `401`s for a non-DLF agency location, you forgot `--refresh-token` (or the
  broker/MCP has a DLF token cached — `make_client` already sets `prefer_refresh_token` when a
  refresh token is passed, which suppresses the broker but not the MCP fallback; if it still
  fails, run from a shell with `GHL_TOKEN_BROKER_*` unset).
