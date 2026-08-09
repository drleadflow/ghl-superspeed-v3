# /a2p-fill-values

**Usage:** `/a2p-fill-values <business_url> <location_id> [--client <slug>] [--refresh-token <token>] [--refresh-all]`

Populate the 18 custom values that the pre-built "A2P Landing Page" funnel + opt-in form
reference on a GHL sub-account. **By default it only fills the slots that are still empty** —
it reads the location's current values first and never churns content that's already there.
Pass `--refresh-all` to regenerate every copy slot from scratch.

Flow: read the location's existing 18 → scrape the business website → optionally read a vault
brief → generate copy for the *missing* slots only → preview as a dry run → write on your OK.

**Does NOT touch** the funnel pages, the opt-in form, the other ~58 custom values, or any
workflow — those merge-tag off these 18 values and never change.

Examples:
- `/a2p-fill-values https://aprestigeaesthetics.com 9uog1fOUDtxkSr4ZPx1i --client prestige`
- `/a2p-fill-values https://example-medspa.com abc123LOCID`
- `/a2p-fill-values https://example-medspa.com abc123LOCID --refresh-all`

---

## The 18 values (see `lib/a2p_values.py:A2P_VALUE_KEYS` for the canonical list)

Facts (resolve in priority order — **existing value on the location** → brief → location API → site):
`business_short_name`, `business_profile__legal_business_name`, `business_profile__phone_number`,
`from_email`, `logo` (always the literal `{{location.logo_url}}`), `primary_color`,
`secondary_color__hex_code`.

Copy (you generate from the scraped site + brief, in DLF brand voice — see `business/brand.md`):
`about_us__description`, `business_welcome_message`, `business_solution__description`,
`our_services_1..4`, `our_services_1..4__description`.

## Steps

1. **Read what's already there** — first fetch the location's current values:
   ```
   python3 -c "import sys,os; sys.path.insert(0,'.'); from lib.a2p_values import make_client, fetch_custom_values; \
     c=make_client('<location_id>', os.environ.get('GHL_FIREBASE_REFRESH_TOKEN')); \
     import json; print(json.dumps({k:v['value'] for k,v in fetch_custom_values(c,'<location_id>').items() if k in dict((s,1) for s,_,_ in __import__('lib.a2p_values',fromlist=['A2P_VALUE_KEYS']).A2P_VALUE_KEYS)}, indent=2))"
   ```
   (or just `python3 scripts/a2p_apply.py <location_id> /dev/null --dry-run` won't show them — use the snippet above.)
   Many accounts have already been through GHL's A2P SaaS setup, so 12–18 of these are already
   filled. **Only generate content for the empty ones** unless `--refresh-all` was passed.

2. **Scrape the site** — `python3 scripts/a2p_scrape.py <business_url>`, read the JSON. It already
   retries with a Googlebot UA if the site's WAF 403s a normal UA (`fetch_ua` tells you which won),
   and for WordPress/Elementor sites it returns a trustworthy `brand_colors` map
   (`{primary, secondary, accent, text, theme_color}`) pulled from the Elementor global kit CSS —
   use *that* for the colour facts, not the noisy `candidate_colors` list.
   If it still returns `{"error": ...}` (rare — both UAs blocked), fall back to the `WebFetch`
   tool to pull headings / about / services / phone / email, and accept that `primary_color` /
   `secondary_color__hex_code` will stay blank (flag them).

3. **Read the brief (optional)** — if `--client <slug>` was given, read whichever exist:
   `clients/<slug>/overview.md`, `clients/<slug>/services.md`, `clients/<slug>/offers.md`.
   (`overview.md` may also carry `ghl_location_id` — sanity-check it against the `<location_id>` arg.)

4. **Resolve the 7 facts (skip any already populated on the location, unless `--refresh-all`):**
   - `business_short_name` — friendly trading name (existing > brief > site `<title>` cleaned up).
   - `business_profile__legal_business_name` — the registered legal entity. Only from the brief
     (or an existing value). If you can't source it, leave it BLANK — it must match the Twilio
     A2P registration exactly. Never guess. If an existing value looks like a placeholder
     (e.g. "APs Aesthetics and Wellness"), don't overwrite it — *flag it* for the user to verify.
   - `business_profile__phone_number` — brief > existing > site. If the existing value differs
     from the number on the website, leave the existing one (it's usually the Twilio-purchased
     number) and just note the discrepancy. Never invent one.
   - `from_email` — existing > brief > `info@<registrable-domain-of-business_url>`.
   - `logo` — always the literal string `{{location.logo_url}}`.
   - `primary_color` / `secondary_color__hex_code` — use the scrape's `brand_colors.primary` /
     `brand_colors.secondary` (fall back to `brand_colors.theme_color` / `accent`). If `brand_colors`
     is empty, leave them blank — better empty than a guessed button colour.

5. **Write the copy values** (only the empty ones, unless `--refresh-all`) from the scraped
   `headings`/`text`/`meta_description` + brief, in DLF brand voice. Keep `our_services_N` to a
   short headline line and `our_services_N__description` to one sentence. If the business clearly
   offers fewer than 4 services, fill what's real and leave the rest blank (skipped, not blanked).
   Respect the client's compliance language if the brief states it (e.g. med-spa: "softens / supports
   a refreshed look", never "erases / freezes / cures / fixes / 100%"; no em dashes if the client
   bans them).

6. **Write the value map** to `/tmp/a2p-values-<location_id>.json` — a JSON object `{slug: value}`
   containing **only the slugs you're actually changing** (the empty ones, plus any `--refresh-all`
   regen). Slugs you omit are left untouched.

7. **Dry run** —
   `python3 scripts/a2p_apply.py <location_id> /tmp/a2p-values-<location_id>.json --dry-run`
   Show the user the proposed value map + the dry-run report. Note: the `/!\ set these manually`
   line only reflects blanks *in your value map* — ignore it for any fact that's already populated
   on the location. Genuinely call out only the facts that are blank both places (and the legal-name
   verification, always).

8. **On the user's OK** — re-run the same command WITHOUT `--dry-run`. Report the result, then
   re-fetch (the snippet from step 1) to confirm the new values landed.

9. **Log it** — append a completion entry to `drleadflow/blade-ops/contents/logs/dev-activity.json`
   per this repo's `CLAUDE.md` (`message: "A2P custom values populated for <client/loc>"` — or
   "...filled <which> for ..." if you only topped up a couple of slots).

## Notes & gotchas

- **Idempotent** — safe to re-run; values that didn't change get PUT with the same content.
- **Auth** — `make_client(loc, refresh_token)` / `scripts/a2p_apply.py` default `--refresh-token`
  to `$GHL_FIREBASE_REFRESH_TOKEN` (set in this project's `.env`), which is the DLF-agency
  identity and works for every DLF sub-account (incl. Prestige, IV Wellness, AZC, TVAAI).
  Pass `--refresh-token <token>` explicitly only for a client on a *different* agency (e.g.
  Ritucci) — see the 'Non-DLF Agency deploy auth' memory.
- **`version` header** — the backend `/locations/{id}/customValues/` GET/PUT/POST endpoints 401
  with *"version header was not found"* unless `version: 2021-07-28` is sent. `lib/a2p_values.py`
  passes it via `_CV_HEADERS` → `GHLClient.request(..., extra_headers=...)`. Don't remove that.
- **Firebase refresh rate-limit** — Google's securetoken endpoint rate-limits rapid successive
  refreshes; back-to-back `a2p_apply.py` runs can raise *"prefer_refresh_token is set but Firebase
  refresh failed"*. If you see exactly that, wait ~15s and retry once — it's not a bad token.
- **WAF-blocked sites** — `a2p_scrape.py` already falls back Chrome-UA → Googlebot-UA. If both are
  blocked, `WebFetch` (different egress IP, renders to markdown) usually still works for the
  text/facts; brand colours just won't be recoverable that way.
- This command never touches the funnel pages, the opt-in form, workflows, or the ~58 non-A2P
  custom values.
