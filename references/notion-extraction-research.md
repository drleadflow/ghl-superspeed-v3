---
type: reference
title: Notion Extraction Research
last_updated: 2026-05-05
purpose: Phase 0 research for Notion → local vault → campaign pipeline (token-lean build)
---

# Notion Extraction Research

## TL;DR — Chosen Approach

| Decision | Choice |
|---|---|
| Python lib | **`notion-sdk-py` (notion-client)** — 2.2k stars, v3.0.0 (Feb 2026), httpx-based, built-in 429 retry |
| Change detection | `client.pages.retrieve(page_id)` → compare `last_edited_time` (top-level field) |
| Cache shape | `.cache/notion/<page_id>.json` (full page) + `.cache/notion/<page_id>.meta.json` (etag-equivalent) |
| Markdown conversion | **DIY** — we already have the property→frontmatter map in `/extract-offer`. Don't bundle `notion2markdown` (23 stars, no incremental sync). |
| Rate-limit posture | 3 req/sec average, 10 burst — SDK handles 429 + Retry-After automatically |
| Auth | `$NOTION_TOKEN` from `~/.env.secrets` (already set as of 2026-05-05) |

**Token-savings dynamic:** `pages.retrieve` returns BOTH `last_edited_time` AND all DB properties in a single call (no separate block-children fetch). Since most of our offer-frontmatter data lives in Notion DB properties (price, has_deadline, top_3_objections, etc.), a single ~500-token API hit covers the cache-miss case. Cache hits = 0 tokens.

---

## Library Comparison

| Lib | Stars | Maintenance | Pros | Cons |
|---|---|---|---|---|
| **notion-sdk-py (ramnes)** ✅ | 2.2k | Active (v3.0 Feb 2026) | Typed, async support, auto-retry on 429, Pythonic ergonomics, only dep is httpx | Slightly heavier than raw requests |
| notion-py-requests (nyoungstudios) | low | Less active | Lightweight, mirrors official JS SDK structure, auto-pagination | Smaller community, fewer examples |
| Raw `requests` / `urllib` | n/a | n/a | Zero deps beyond stdlib | We'd write retry/backoff/pagination ourselves |
| notion-py (jamalex) | high | Stale | Powerful (block tree + caching) | Reverse-engineered v3 API, predates official API, brittle |
| notion2markdown (alvinwan) | 23 | Low | Writes YAML frontmatter on export — matches our shape | No incremental sync, low maintenance, would force its conventions |
| notion2md (echo724) | mid | OK | CLI exporter | Not a library API, optimized for one-shot export |

**Why notion-sdk-py over raw requests:** built-in 429 handling alone is worth it. The 3 req/sec limit + token bucket + Retry-After behavior is non-trivial to implement correctly, and breaking the rate limit on a sync run gets the integration token throttled.

**Why not bundle notion2markdown:** we already have the canonical property→frontmatter map in `.claude/commands/extract-offer.md` (26 fields). Importing a 3rd-party converter means either (a) overriding its output to match our schema, which negates its value, or (b) drifting our schema to its defaults. Owning the mapping is correct here.

---

## Change Detection Pattern (the actual win)

The Notion REST API for `GET /v1/pages/{page_id}` returns the full page object including:

```
{
  "object": "page",
  "id": "...",
  "created_time": "...",
  "last_edited_time": "2026-05-04T17:23:00.000Z",  ← cheap change marker
  "properties": { ... full DB properties ... },     ← most of what we need
  "parent": { ... },
  "icon": null,
  "cover": null,
  ...
}
```

**Block content** (the actual rich-text body of the page) requires a separate `GET /v1/blocks/{page_id}/children` call. For our offer pages, the **properties** payload alone covers ~80% of frontmatter fields. Only the body sections (Core Promise, What's Included, Top 3 Objections elaboration, Compliance Notes) need block children.

### Tiered fetch strategy

1. **Always:** call `pages.retrieve(page_id)` (1 request, ~500 tokens of JSON).
2. **Compare `last_edited_time`** with `.cache/notion/<id>.meta.json`.
3. **If unchanged:** return cached merged object. Done. 0 additional calls.
4. **If changed (or no cache):** fetch `blocks.children.list(page_id)` (1+ requests, paginated, page_size=100). Merge into cache. Update meta file.

Worst case (no cache, large page): ~3 requests, ~2K tokens of JSON. Cache hit: 1 request (metadata-only check), ~200 tokens.

Compared to current Notion MCP fetch (which dumps the full page rendering ~3-8K tokens of context noise per call): **5-15x reduction even on cold misses**, near-zero on hits.

---

## Rate Limits & Pagination (operational rules)

- **Average:** 3 requests/second per integration token
- **Bucket:** 10 (burst allowed if idle)
- **429 response:** SDK auto-retries with `Retry-After` (default 2 retries, exponential backoff with jitter)
- **Pagination:** `page_size` max 100 (use this for `blocks.children.list` and DB queries)
- **Bulk endpoint (2026-02-01):** up to 100x reduction — relevant for Phase 4 `/notion-sync` if we walk the whole offers DB
- **Webhooks (2026-03-01):** push instead of poll, don't count against rate limit. Future enhancement, not Phase 1.

**Practical rule for our use:** at ~6-12 offers in the offers DB and intermittent sync needs, we'll never approach the limit. SDK defaults are fine.

---

## Implementation Sketch (preview of Phase 1)

```python
# lib/notion_cache.py (preview)
import json, os, time
from pathlib import Path
from notion_client import Client

CACHE_DIR = Path(__file__).parent.parent / ".cache" / "notion"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_client = None
def _c():
    global _client
    if _client is None:
        token = os.environ["NOTION_TOKEN"]  # fail loud if unset
        _client = Client(auth=token)
    return _client

def get_page(page_id: str, *, force: bool = False) -> dict:
    """Returns full page object (properties + cached blocks). Hits cache when last_edited_time unchanged."""
    page_id = page_id.replace("-", "")
    page_file = CACHE_DIR / f"{page_id}.json"
    meta_file = CACHE_DIR / f"{page_id}.meta.json"

    # Always do the cheap metadata check
    fresh = _c().pages.retrieve(page_id=page_id)
    new_let = fresh["last_edited_time"]

    if not force and meta_file.exists() and page_file.exists():
        meta = json.loads(meta_file.read_text())
        if meta.get("last_edited_time") == new_let:
            cached = json.loads(page_file.read_text())
            cached["_cache_hit"] = True
            return cached

    # Cache miss or stale — fetch blocks too
    blocks = _list_all_blocks(page_id)
    merged = {**fresh, "_blocks": blocks}
    page_file.write_text(json.dumps(merged, indent=2))
    meta_file.write_text(json.dumps({
        "last_edited_time": new_let,
        "fetched_at": time.time(),
    }, indent=2))
    merged["_cache_hit"] = False
    return merged

def _list_all_blocks(page_id: str) -> list[dict]:
    out, cursor = [], None
    while True:
        resp = _c().blocks.children.list(block_id=page_id, page_size=100, start_cursor=cursor)
        out.extend(resp["results"])
        if not resp.get("has_more"): break
        cursor = resp["next_cursor"]
    return out
```

This is illustrative — the real Phase 1 implementation will add a slug→page_id resolver, structured error handling, and optional `force` flag plumbing into `/extract-offer`.

---

## Sources

- [Notion API: Retrieve a page](https://developers.notion.com/reference/retrieve-a-page) — confirms `last_edited_time` is top-level on `GET /v1/pages/{id}`
- [Notion API: Request limits](https://developers.notion.com/reference/request-limits) — 3 req/sec, token bucket, Retry-After contract
- [ramnes/notion-sdk-py (GitHub)](https://github.com/ramnes/notion-sdk-py) — 2.2k stars, v3.0.0 (Feb 2026), httpx + auto-retry
- [alvinwan/notion2markdown (GitHub)](https://github.com/alvinwan/notion2markdown) — 23 stars, MIT, YAML frontmatter export — evaluated and rejected
- [Notion API Rate Limits 2026 — Fazm Blog](https://fazm.ai/blog/notion-api-rate-limits-2026) — confirms 2026-04-01 standard rate-limit headers + 2026-02-01 bulk endpoint
- [marc7806/notion-api-cache (GitHub)](https://github.com/marc7806/notion-api-cache) — confirms last-edited-time-based caching is the standard pattern (proxy reference)
- [Notion API: Page properties](https://developers.notion.com/reference/page-property-values) — confirms property values are returned by `pages.retrieve`

## What we're NOT doing (and why)

- **No notion-py (jamalex)** — reverse-engineered API v3, brittle, predates official API.
- **No webhook setup yet** — overkill for our scale; revisit if sync runs become frequent.
- **No bulk endpoint use yet** — Phase 4 may use it for `/notion-sync` if perf demands.
- **No notion2markdown** — we own the property→frontmatter map; adding a 3rd-party converter creates schema drift.

---

## Gotcha: Notion URL shapes (URL → page_id resolution)

Notion serves at least three URL shapes that all need to resolve to a page ID. The non-obvious one is the **database peek view**, where the path is the *database* and the page being previewed lives in the `?p=` query param.

| Shape | Example | Where the page id lives |
|---|---|---|
| Title-with-id | `https://www.notion.so/Some-Title-34f72879...0f1ed` | trailing 32 hex chars in path |
| Workspace + dashed | `https://www.notion.so/ws/Some-Title-34f72879-5ff0-...?pvs=21` | path (dashes stripped) |
| **Database peek view** | `https://www.notion.so/<db_id>?v=<view>&p=<page_id>&pm=s` | **`?p=` query param**, NOT the path |

`page_id_from_url()` in `lib/notion_cache.py` checks `?p=` first, then falls back to the path. If a future caller strips the query string before resolving, peek-view URLs will silently return the database ID and `GET /pages/<db_id>` will 404.

**Symptom of the bug we hit (2026-05-06):** `/extract-offer` URLs copied from the Offers DB peek view 404'd with `Notion 404 Not Found at /pages/959704...` — that 32-char id is the Offers database, not a page.
