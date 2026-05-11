#!/usr/bin/env python3
"""
Scrape a business website into compact JSON for A2P custom-value generation.

Usage:  python3 scripts/a2p_scrape.py <url>
Prints JSON to stdout:
  {url, title, meta_description, headings[], candidate_email, candidate_emails[],
   candidate_phone, candidate_phones[], candidate_colors[], text}
On failure prints {"error": "..."} to stdout and exits 1. Stdlib only.
"""
import json
import re
import ssl
import sys
import urllib.request
from html.parser import HTMLParser

CHROME_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
_CTX = ssl.create_default_context()
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}")
_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
_SKIP_TAGS = {"script", "style", "noscript", "head", "svg"}
_HEADING_TAGS = {"h1", "h2", "h3"}
_TEXT_BUDGET = 8000


class _Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self._title_parts = []
        self._in_title = False
        self._skip_depth = 0
        self.meta_description = ""
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
        if tag == "meta" and (d.get("name", "").lower() == "description") and not self.meta_description:
            self.meta_description = d.get("content", "") or ""
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


def parse_html(html, url):
    """Pure HTML -> dict. Colours come from the raw HTML (CSS) but text/headings
    exclude <script>/<style>/<head> content."""
    p = _Extract()
    p.feed(html)
    emails = sorted({m.group(0).lower() for m in _EMAIL_RE.finditer(html)})
    phones = sorted({m.group(0) for m in _PHONE_RE.finditer(p.text)})
    # only count hex colours that appear OUTSIDE <script> blocks
    no_script = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    colors = sorted({m.group(0).lower() for m in _HEX_RE.finditer(no_script)})
    return {
        "url": url,
        "title": p.title,
        "meta_description": p.meta_description.strip(),
        "headings": p.headings[:40],
        "candidate_email": emails[0] if emails else "",
        "candidate_emails": emails[:10],
        "candidate_phone": phones[0] if phones else "",
        "candidate_phones": phones[:10],
        "candidate_colors": colors[:20],
        "text": p.text[:_TEXT_BUDGET],
    }


def scrape(url):
    req = urllib.request.Request(url, headers={"User-Agent": CHROME_UA, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, context=_CTX, timeout=20) as resp:
        raw = resp.read()
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("latin-1", errors="replace")
    return parse_html(html, url)


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
