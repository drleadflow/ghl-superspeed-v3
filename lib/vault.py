#!/usr/bin/env python3
"""
Vault query layer — read-only access to the local Obsidian vault.

Pure local. Zero network. Zero LLM tokens. Use this anywhere a build step needs
offer/service/client data — replaces fetching from Notion at session time.

Public API:
    get_offer(slug)          -> dict | None
    get_service(slug)        -> dict | None
    get_client(slug)         -> dict | None      # reads clients/<slug>/overview.md
    list_offers()            -> list[dict]       # all offers/*.md (excludes _template, README)
    list_services()          -> list[dict]
    list_clients()           -> list[dict]
    find_offers(**filters)   -> list[dict]       # filters: client=, status=, offer_type=, etc.

Each returned dict carries:
    All frontmatter keys (parsed YAML)
    "_slug": filename slug (e.g., "iv-wellness-nad-iv-therapy")
    "_path": absolute path to source file
    "_body": markdown body (after frontmatter)
    "_sections": dict of {section_title: section_body} from `## Heading` splits

Required dep: PyYAML (system-installed, version 6+).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

import re

import yaml

VAULT_ROOT = Path(__file__).parent.parent
OFFERS_DIR = VAULT_ROOT / "offers"
SERVICES_DIR = VAULT_ROOT / "services"
CLIENTS_DIR = VAULT_ROOT / "clients"
TEMPLATES_DIR = VAULT_ROOT / "templates"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?\n)---\s*\n?(.*)$", re.DOTALL)
_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

_HIDDEN_PREFIXES = ("_", ".")
_INDEX_NAMES = {"README.md", "_index.md"}


# ── Errors ────────────────────────────────────────────────────────────────────

class VaultError(Exception):
    """Bad path, malformed frontmatter, or missing required field."""


# ── Internals ─────────────────────────────────────────────────────────────────

def _read_md(path: Path) -> tuple[dict, str]:
    """Returns (frontmatter_dict, body_str). Empty dict if no frontmatter block."""
    if not path.exists():
        raise VaultError(f"Vault file missing: {path}")
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_text, body = m.group(1), m.group(2)
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        raise VaultError(f"Bad YAML frontmatter in {path}: {e}") from e
    if not isinstance(fm, dict):
        raise VaultError(f"Frontmatter in {path} is not a mapping (got {type(fm).__name__})")
    return fm, body


def _split_sections(body: str) -> dict[str, str]:
    """Split markdown body on `## ` headings. Returns {heading_text: section_body}."""
    out: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(body))
    if not matches:
        return out
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        out[title] = body[start:end].strip()
    return out


def _slug_from_path(path: Path) -> str:
    return path.stem


def _is_listable(path: Path) -> bool:
    name = path.name
    if name in _INDEX_NAMES:
        return False
    if any(name.startswith(p) for p in _HIDDEN_PREFIXES):
        return False
    return True


def _hydrate(path: Path) -> dict:
    fm, body = _read_md(path)
    sections = _split_sections(body)
    return {
        **fm,
        "_slug": _slug_from_path(path),
        "_path": str(path),
        "_body": body.strip(),
        "_sections": sections,
    }


# ── Public: offers ────────────────────────────────────────────────────────────

def get_offer(slug: str) -> Optional[dict]:
    path = OFFERS_DIR / f"{slug}.md"
    if not path.exists():
        return None
    return _hydrate(path)


def list_offers() -> list[dict]:
    return [
        _hydrate(p)
        for p in sorted(OFFERS_DIR.glob("*.md"))
        if _is_listable(p)
    ]


def find_offers(**filters: Any) -> list[dict]:
    """
    Filter offers by any frontmatter field. Examples:
        find_offers(client="iv-wellness")
        find_offers(client="iv-wellness", status="active")
        find_offers(offer_type="IV Therapy")
    """
    items = list_offers()
    for k, v in filters.items():
        items = [o for o in items if o.get(k) == v]
    return items


# ── Public: services ──────────────────────────────────────────────────────────

def get_service(slug: str) -> Optional[dict]:
    path = SERVICES_DIR / f"{slug}.md"
    if not path.exists():
        return None
    return _hydrate(path)


def list_services() -> list[dict]:
    return [
        _hydrate(p)
        for p in sorted(SERVICES_DIR.glob("*.md"))
        if _is_listable(p)
    ]


# ── Public: clients ───────────────────────────────────────────────────────────

def get_client(slug: str) -> Optional[dict]:
    """
    Reads clients/<slug>/overview.md. Also attaches:
        "_offers":   list of offer dicts (full hydrate) where offer.client == slug
        "_services": parsed table from services.md (best-effort wikilink extraction)
    """
    overview_path = CLIENTS_DIR / slug / "overview.md"
    if not overview_path.exists():
        return None
    data = _hydrate(overview_path)
    data["_offers"] = find_offers(client=slug)
    data["_services_index_path"] = str(CLIENTS_DIR / slug / "services.md")
    data["_offers_index_path"] = str(CLIENTS_DIR / slug / "offers.md")
    data["_campaigns_index_path"] = str(CLIENTS_DIR / slug / "campaigns.md")
    return data


def list_clients() -> list[dict]:
    out: list[dict] = []
    if not CLIENTS_DIR.exists():
        return out
    for child in sorted(CLIENTS_DIR.iterdir()):
        if not child.is_dir():
            continue
        if any(child.name.startswith(p) for p in _HIDDEN_PREFIXES):
            continue  # skip _template, .DS_Store
        overview = child / "overview.md"
        if overview.exists():
            out.append(_hydrate(overview))
    return out


# ── Public: validation ────────────────────────────────────────────────────────

OFFER_REQUIRED_FIELDS = ("client", "name", "offer_type", "status")
SERVICE_REQUIRED_FIELDS = ("name", "duration_minutes")
CLIENT_REQUIRED_FIELDS = ("client_slug", "business_name", "ghl_location_id")


def validate_offer(offer: dict) -> list[str]:
    """Returns list of missing-field complaints. Empty list = valid."""
    return [f for f in OFFER_REQUIRED_FIELDS if not offer.get(f)]


def validate_service(service: dict) -> list[str]:
    return [f for f in SERVICE_REQUIRED_FIELDS if not service.get(f)]


def validate_client(client: dict) -> list[str]:
    return [f for f in CLIENT_REQUIRED_FIELDS if not client.get(f)]


# ── CLI smoke test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m lib.vault list-offers")
        print("  python -m lib.vault list-clients")
        print("  python -m lib.vault offer <slug>")
        print("  python -m lib.vault service <slug>")
        print("  python -m lib.vault client <slug>")
        print("  python -m lib.vault find <key>=<value> [<key>=<value> ...]")
        sys.exit(1)

    cmd = sys.argv[1]

    def _strip(o: Any) -> Any:
        """Drop heavy fields from CLI output for readability."""
        if isinstance(o, dict):
            return {k: _strip(v) for k, v in o.items() if k not in ("_body", "_sections")}
        if isinstance(o, list):
            return [_strip(x) for x in o]
        return o

    if cmd == "list-offers":
        for o in list_offers():
            print(f"{o['_slug']:<50} client={o.get('client', '?'):<20} status={o.get('status', '?')}")
    elif cmd == "list-clients":
        for c in list_clients():
            print(f"{c.get('client_slug', '?'):<25} {c.get('business_name', '?')}")
    elif cmd == "offer" and len(sys.argv) >= 3:
        o = get_offer(sys.argv[2])
        print(json.dumps(_strip(o), indent=2, default=str))
    elif cmd == "service" and len(sys.argv) >= 3:
        s = get_service(sys.argv[2])
        print(json.dumps(_strip(s), indent=2, default=str))
    elif cmd == "client" and len(sys.argv) >= 3:
        c = get_client(sys.argv[2])
        print(json.dumps(_strip(c), indent=2, default=str))
    elif cmd == "find":
        filters: dict[str, str] = {}
        for arg in sys.argv[2:]:
            if "=" not in arg:
                continue
            k, v = arg.split("=", 1)
            filters[k] = v
        results = find_offers(**filters)
        for o in results:
            print(f"{o['_slug']:<50} client={o.get('client', '?'):<20} type={o.get('offer_type', '?')}")
        print(f"\n({len(results)} match)")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
