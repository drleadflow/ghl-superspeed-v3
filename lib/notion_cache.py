#!/usr/bin/env python3
"""
Notion API + last_edited_time cache.

Uses stdlib only (urllib.request) to match the engine.py aesthetic — no pip deps.

Public API:
    get_page(page_id, *, force=False)      -> dict (full page object + cached blocks)
    list_database(database_id, *, force=False) -> list[dict] (db rows, paginated)
    cache_stats()                           -> dict (count, oldest, newest, total bytes)
    clear(page_id=None)                     -> int (entries deleted)

Cache layout:
    .cache/notion/<page_id>.json       full page object incl. _blocks list
    .cache/notion/<page_id>.meta.json  {last_edited_time, fetched_at}
    .cache/notion/db_<db_id>.json      db query results
    .cache/notion/db_<db_id>.meta.json {row_etags: {row_id: last_edited_time}, fetched_at}

Cache-hit dynamics:
    Every call hits Notion API once for the cheap pages.retrieve (returns last_edited_time
    + properties in <500 tokens). If unchanged, returns cached merged object. Block children
    are only refetched when last_edited_time differs.
"""

from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"
CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
PROJECT_ROOT = Path(__file__).parent.parent
CACHE_DIR = PROJECT_ROOT / ".cache" / "notion"
DOTENV_PATH = PROJECT_ROOT / ".env"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds
CTX = ssl.create_default_context()


# ── Errors ────────────────────────────────────────────────────────────────────

class NotionError(Exception):
    """Notion API call failed (non-rate-limit)."""


class NotionAuthError(NotionError):
    """NOTION_TOKEN missing or invalid."""


# ── .env loader (stdlib, no python-dotenv dep) ────────────────────────────────

def _load_dotenv(path: Path = DOTENV_PATH) -> None:
    """
    Load KEY=VALUE pairs from a project-local .env file into os.environ.
    Existing env vars are NOT overridden (shell wins). Silent no-op if file missing.
    Supports quoted values and `# comments`.
    """
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            if key and val and key not in os.environ:
                os.environ[key] = val
    except OSError:
        pass


_load_dotenv()


# ── Internal HTTP ─────────────────────────────────────────────────────────────

TOKEN_ENV_VARS = ("NOTION_DLF_TOKEN", "NOTION_TOKEN")
"""Env vars checked in order. Set NOTION_DLF_TOKEN in the project .env (or
~/.env.secrets) with a DLF-workspace integration token. NOTION_TOKEN is the
user-global fallback."""


def _token() -> str:
    for var in TOKEN_ENV_VARS:
        tok = os.environ.get(var)
        if tok:
            return tok
    raise NotionAuthError(
        f"No Notion token found. Tried {TOKEN_ENV_VARS}. "
        f"Set NOTION_DLF_TOKEN in {DOTENV_PATH.name} (project root) or ~/.env.secrets. "
        f"The integration ('Client-Offers') must be invited to the Offers database in Notion."
    )


def whoami() -> dict:
    """Returns the integration identity (bot user object) for diagnostic purposes."""
    return _request("GET", "/users/me")


def _request(method: str, path: str, body: Optional[dict] = None) -> dict:
    """One request to the Notion API with 429 retry-after honoring."""
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
        "User-Agent": CHROME_UA,
    }

    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                err_body = ""

            if status == 401:
                raise NotionAuthError(
                    f"Notion 401 Unauthorized. Token may be invalid or revoked. Body: {err_body[:200]}"
                ) from e

            if status == 404:
                raise NotionError(
                    f"Notion 404 Not Found at {path}. "
                    f"Either the page/db doesn't exist or your integration isn't shared with it. "
                    f"Body: {err_body[:200]}"
                ) from e

            if status == 429 and attempt <= MAX_RETRIES:
                # Notion sets Retry-After (integer seconds)
                retry_after = float(e.headers.get("Retry-After", RETRY_BASE_DELAY * attempt))
                time.sleep(retry_after)
                continue

            if 500 <= status < 600 and method == "GET" and attempt <= MAX_RETRIES:
                # Transient server error on idempotent call: backoff and retry
                time.sleep(RETRY_BASE_DELAY * attempt)
                continue

            raise NotionError(
                f"Notion {status} {method} {path} (attempt {attempt}): {err_body[:300]}"
            ) from e
        except urllib.error.URLError as e:
            if attempt <= MAX_RETRIES:
                time.sleep(RETRY_BASE_DELAY * attempt)
                continue
            raise NotionError(f"Notion network error: {e}") from e


# ── Cache I/O ─────────────────────────────────────────────────────────────────

def _ensure_cache_dir() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def _normalize_id(page_or_db_id: str) -> str:
    """Normalize a Notion ID to its dashless 32-char form (works as filename and API arg)."""
    raw = page_or_db_id.replace("-", "").strip()
    if len(raw) != 32:
        raise NotionError(
            f"Invalid Notion ID '{page_or_db_id}' — expected 32 hex chars (with or without dashes)."
        )
    return raw


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, obj: Any) -> None:
    _ensure_cache_dir()
    path.write_text(json.dumps(obj, indent=2, sort_keys=True))


# ── Public: pages ─────────────────────────────────────────────────────────────

def get_page(page_id: str, *, force: bool = False, fetch_blocks: bool = True) -> dict:
    """
    Returns full page object (top-level fields + properties + _blocks).

    Strategy:
      1. Always call pages.retrieve (cheap, returns last_edited_time + properties).
      2. If cache hit and last_edited_time unchanged AND blocks already cached: return cache.
      3. Otherwise: fetch blocks (when fetch_blocks=True), repopulate cache.

    The returned dict carries `_cache_hit: bool` for diagnostics.
    """
    norm = _normalize_id(page_id)
    page_file = CACHE_DIR / f"{norm}.json"
    meta_file = CACHE_DIR / f"{norm}.meta.json"

    fresh = _request("GET", f"/pages/{norm}")
    new_let = fresh.get("last_edited_time")

    cached = None if force else _read_json(page_file)
    cached_meta = None if force else _read_json(meta_file)

    have_blocks = bool(cached and "_blocks" in cached)
    unchanged = bool(
        cached_meta and cached_meta.get("last_edited_time") == new_let
    )

    if cached and unchanged and (have_blocks or not fetch_blocks):
        # Refresh top-level + properties in cache (cheap merge) so subtle metadata stays current
        merged = {**cached, **fresh}
        if have_blocks:
            merged["_blocks"] = cached["_blocks"]
        _write_json(page_file, merged)
        merged["_cache_hit"] = True
        return merged

    # Cache miss or stale — pull blocks if requested
    blocks = _list_all_blocks(norm) if fetch_blocks else []
    merged = {**fresh, "_blocks": blocks}
    _write_json(page_file, merged)
    _write_json(meta_file, {
        "last_edited_time": new_let,
        "fetched_at": time.time(),
    })
    merged["_cache_hit"] = False
    return merged


def _list_all_blocks(page_id: str) -> list[dict]:
    out: list[dict] = []
    cursor: Optional[str] = None
    while True:
        qs = "?page_size=100"
        if cursor:
            qs += f"&start_cursor={urllib.parse.quote(cursor)}"
        resp = _request("GET", f"/blocks/{page_id}/children{qs}")
        out.extend(resp.get("results", []))
        if not resp.get("has_more"):
            return out
        cursor = resp.get("next_cursor")
        if not cursor:
            return out


# ── Public: databases ─────────────────────────────────────────────────────────

def list_database(database_id: str, *, force: bool = False, page_size: int = 100) -> list[dict]:
    """
    Returns all rows of a database (paginated). Caches the result keyed by the database ID.

    For change-detection-aware sync, prefer reading row['last_edited_time'] from each result
    and comparing to a per-row local cache before doing per-page block fetches.
    """
    norm = _normalize_id(database_id)
    db_file = CACHE_DIR / f"db_{norm}.json"
    db_meta = CACHE_DIR / f"db_{norm}.meta.json"

    if not force and db_file.exists():
        cached = _read_json(db_file)
        meta = _read_json(db_meta) or {}
        # Cache freshness: 5 minutes by default. For longer staleness, use force=True or /notion-sync.
        if cached is not None and (time.time() - meta.get("fetched_at", 0)) < 300:
            cached_list = cached.get("results", [])
            for row in cached_list:
                row["_cache_hit"] = True
            return cached_list

    results: list[dict] = []
    cursor: Optional[str] = None
    while True:
        body: dict = {"page_size": page_size}
        if cursor:
            body["start_cursor"] = cursor
        resp = _request("POST", f"/databases/{norm}/query", body=body)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
        if not cursor:
            break

    _write_json(db_file, {"results": results})
    _write_json(db_meta, {
        "fetched_at": time.time(),
        "row_count": len(results),
        "row_etags": {r["id"]: r.get("last_edited_time") for r in results},
    })
    for row in results:
        row["_cache_hit"] = False
    return results


# ── Public: helpers for slash commands ────────────────────────────────────────

def page_id_from_url(url: str) -> str:
    """
    Extract a page ID from any common Notion URL shape:
      https://www.notion.so/Some-Title-34f728795ff081468662d1d13d70f1ed
      https://www.notion.so/workspace/Some-Title-34f72879-5ff0-8146-8662-d1d13d70f1ed?pvs=21
      https://www.notion.so/<db_id>?v=<view_id>&p=<page_id>&pm=s   ← database peek view

    For peek views (?p=<id>) the path is the database ID and the page being
    viewed lives in the `p` query parameter — prefer it when present.
    """
    if not url:
        raise NotionError("Empty URL passed to page_id_from_url.")

    parsed = urllib.parse.urlsplit(url)
    qs = urllib.parse.parse_qs(parsed.query)
    peek = (qs.get("p") or [None])[0]
    if peek:
        peek_norm = peek.replace("-", "").lower()
        if len(peek_norm) == 32 and all(c in "0123456789abcdef" for c in peek_norm):
            return peek_norm

    # Last path segment (query/fragment already stripped by urlsplit)
    last = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    candidate = last.replace("-", "")
    for i in range(len(candidate) - 32, -1, -1):
        chunk = candidate[i:i + 32]
        if all(c in "0123456789abcdef" for c in chunk.lower()):
            return chunk.lower()
    raise NotionError(f"Could not extract a page ID from URL: {url}")


def cache_stats() -> dict:
    """Quick health check on the cache."""
    if not CACHE_DIR.exists():
        return {"entries": 0, "bytes": 0, "oldest": None, "newest": None}
    files = list(CACHE_DIR.glob("*.json"))
    times = []
    total = 0
    for f in files:
        st = f.stat()
        total += st.st_size
        times.append(st.st_mtime)
    return {
        "entries": len([f for f in files if not f.name.endswith(".meta.json")]),
        "bytes": total,
        "oldest": min(times) if times else None,
        "newest": max(times) if times else None,
    }


def clear(page_id: Optional[str] = None) -> int:
    """Delete cache entries. Pass page_id for one entry, or None for the whole cache."""
    if not CACHE_DIR.exists():
        return 0
    deleted = 0
    if page_id:
        norm = _normalize_id(page_id)
        for f in [CACHE_DIR / f"{norm}.json", CACHE_DIR / f"{norm}.meta.json"]:
            if f.exists():
                f.unlink()
                deleted += 1
    else:
        for f in CACHE_DIR.glob("*"):
            if f.is_file():
                f.unlink()
                deleted += 1
    return deleted


# ── CLI smoke test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m lib.notion_cache <page-url-or-id> [--force]")
        sys.exit(1)
    arg = sys.argv[1]
    force = "--force" in sys.argv
    pid = page_id_from_url(arg) if arg.startswith("http") else arg
    page = get_page(pid, force=force)
    title_prop = page.get("properties", {})
    # Best-effort title field
    name = None
    for k, v in title_prop.items():
        if v.get("type") == "title" and v.get("title"):
            name = "".join(t.get("plain_text", "") for t in v["title"])
            break
    print(json.dumps({
        "id": page["id"],
        "last_edited_time": page["last_edited_time"],
        "title": name,
        "property_count": len(title_prop),
        "block_count": len(page.get("_blocks", [])),
        "cache_hit": page.get("_cache_hit"),
    }, indent=2))
