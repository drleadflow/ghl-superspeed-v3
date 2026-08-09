#!/usr/bin/env python3
"""
Scrape a business website into compact JSON for A2P custom-value generation.

Usage:  python3 scripts/a2p_scrape.py <url>
Prints JSON to stdout:
  {url, fetch_ua, title, meta_description, theme_color, headings[],
   candidate_email, candidate_emails[], candidate_phone, candidate_phones[],
   candidate_colors[], brand_colors{}, text}
On failure prints {"error": "..."} to stdout and exits 1. Stdlib only.

Robustness notes (added 2026-05-11 after live errors):
- Many med-spa sites sit behind a WAF (Cloudflare, Hostinger, Sucuri) that 403s a
  plain Python UA. We retry once with a Googlebot UA, which WAFs usually allow.
- HTML almost never contains the *brand* palette inline. For WordPress + Elementor
  sites (the common case) we additionally fetch the Elementor global-kit CSS and
  read `--e-global-color-primary` / `secondary` / `accent` / `text` from it, plus
  any `<meta name="theme-color">`. Those land in `brand_colors` — far more reliable
  than guessing from `candidate_colors` (which is mostly button/border noise).
"""
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

CHROME_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
# WAFs (Cloudflare/Hostinger/Sucuri) routinely allow Googlebot but block generic UAs.
GOOGLEBOT_UA = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
_UAS = (CHROME_UA, GOOGLEBOT_UA)
_CTX = ssl.create_default_context()
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}")
_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
_KIT_RE = re.compile(r"elementor-kit-(\d+)")
_E_GLOBAL_RE = re.compile(r"--e-global-color-([a-z0-9_]+)\s*:\s*(#[0-9a-fA-F]{3,8})", re.I)
# Elementor's *default* kit colours — if we only see these, the brand never customised them.
_E_DEFAULTS = {"#6ec1e4", "#54595f", "#7a7a7a", "#61ce70"}
_SKIP_TAGS = {"script", "style", "noscript", "head", "svg"}
_HEADING_TAGS = {"h1", "h2", "h3"}
_TEXT_BUDGET = 8000
_CSS_BUDGET = 200_000


class _Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self._title_parts = []
        self._in_title = False
        self._skip_depth = 0
        self.meta_description = ""
        self.theme_color = ""
        self.headings = []
        self._h_tag = None
        self._h_parts = []
        self._text_parts = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = (d.get("name", "") or d.get("property", "")).lower()
            if name == "description" and not self.meta_description:
                self.meta_description = d.get("content", "") or ""
            if name == "theme-color" and not self.theme_color:
                self.theme_color = (d.get("content", "") or "").strip()
        if tag in _HEADING_TAGS and self._skip_depth == 0:
            self._h_tag, self._h_parts = tag, []

    def handle_startendtag(self, tag, attrs):
        # <meta .../> self-closing
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in _HEADING_TAGS and self._h_tag == tag:
            txt = " ".join("".join(self._h_parts).split())
            if txt:
                self.headings.append(txt)
            self._h_tag, self._h_parts = None, []

    def handle_data(self, data):
        if self._in_title:
            self._title_parts.append(data)
        if self._h_tag:
            self._h_parts.append(data)
        if self._skip_depth == 0:
            s = data.strip()
            if s:
                self._text_parts.append(s)

    @property
    def title(self):
        return " ".join("".join(self._title_parts).split())

    @property
    def text(self):
        return " ".join(" ".join(self._text_parts).split())


def _http_get(url, ua, timeout=20):
    """GET a URL with the given UA. Returns the decoded body (str). Raises on HTTP/URL error."""
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,text/css,*/*"})
    with urllib.request.urlopen(req, context=_CTX, timeout=timeout) as resp:
        raw = resp.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def _fetch_html(url):
    """Fetch the page HTML, retrying with a Googlebot UA on a WAF-style block.

    Returns (html, ua_that_worked). Raises the last error if every UA fails.
    """
    last_err = None
    for ua in _UAS:
        try:
            return _http_get(url, ua), ua
        except urllib.error.HTTPError as e:
            last_err = e
            # 403/406/429 from a WAF -> try the next UA; a real 404 won't be fixed by it
            # but it's cheap to retry once anyway.
            if e.code not in (401, 403, 406, 409, 429, 503):
                raise
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            last_err = e
    raise last_err if last_err else RuntimeError("fetch failed")


def _origin(url):
    p = urllib.parse.urlsplit(url)
    return "%s://%s" % (p.scheme or "https", p.netloc)


def _elementor_brand_colors(html, page_url, ua):
    """If the page is Elementor, fetch its global-kit CSS and pull the brand palette.

    Returns {"primary": "#..", "secondary": "#..", "accent": "#..", "text": "#.."}
    (only the keys that resolve), or {} if not Elementor / fetch failed / only defaults.
    """
    m = _KIT_RE.search(html)
    if not m:
        return {}
    kit_id = m.group(1)
    css_url = "%s/wp-content/uploads/elementor/css/post-%s.css" % (_origin(page_url), kit_id)
    try:
        css = _http_get(css_url, ua, timeout=15)[:_CSS_BUDGET]
    except Exception:  # noqa: BLE001 — best-effort enrichment
        return {}
    found = {}
    for name, hexv in _E_GLOBAL_RE.findall(css):
        key = name.lower()
        if key in ("primary", "secondary", "accent", "text") and key not in found:
            found[key] = hexv.lower()
    # If literally every value is an Elementor default, the brand never set a palette.
    if found and all(v in _E_DEFAULTS for v in found.values()):
        return {}
    return found


def parse_html(html, url, fetch_ua=CHROME_UA):
    """Pure HTML -> dict, then enrich with Elementor/theme-color brand palette.

    `candidate_colors` come from the raw HTML (CSS) but text/headings exclude
    <script>/<style>/<head> content. `brand_colors` is the trustworthy palette
    (Elementor globals first, then <meta theme-color>).
    """
    p = _Extract()
    p.feed(html)
    emails = sorted({m.group(0).lower() for m in _EMAIL_RE.finditer(html)})
    phones = sorted({m.group(0) for m in _PHONE_RE.finditer(p.text)})
    # only count hex colours that appear OUTSIDE <script> blocks
    no_script = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    colors = sorted({m.group(0).lower() for m in _HEX_RE.finditer(no_script)})

    brand = _elementor_brand_colors(html, url, fetch_ua)
    if p.theme_color and re.fullmatch(r"#[0-9a-fA-F]{3,8}", p.theme_color):
        brand.setdefault("theme_color", p.theme_color.lower())

    return {
        "url": url,
        "fetch_ua": "googlebot" if fetch_ua == GOOGLEBOT_UA else "chrome",
        "title": p.title,
        "meta_description": p.meta_description.strip(),
        "theme_color": p.theme_color,
        "headings": p.headings[:40],
        "candidate_email": emails[0] if emails else "",
        "candidate_emails": emails[:10],
        "candidate_phone": phones[0] if phones else "",
        "candidate_phones": phones[:10],
        "candidate_colors": colors[:20],
        "brand_colors": brand,
        "text": p.text[:_TEXT_BUDGET],
    }


def scrape(url):
    html, ua = _fetch_html(url)
    return parse_html(html, url, ua)


def main(argv):
    if len(argv) < 2 or not argv[1].strip():
        print(json.dumps({"error": "usage: a2p_scrape.py <url>"}))
        return 1
    try:
        print(json.dumps(scrape(argv[1].strip()), ensure_ascii=False))
        return 0
    except Exception as e:  # noqa: BLE001 — surface any fetch/parse failure as JSON
        print(json.dumps({"error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
