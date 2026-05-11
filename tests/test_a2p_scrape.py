#!/usr/bin/env python3
"""
a2p_scrape — fixture test for HTML parsing (no network).
Run: python3 tests/test_a2p_scrape.py   (standalone)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from a2p_scrape import parse_html

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_business.html")


def test_parse_html_extracts_core_fields():
    html = open(FIXTURE, encoding="utf-8").read()
    d = parse_html(html, "https://acmeaesthetics.com")
    assert d["url"] == "https://acmeaesthetics.com"
    assert "Acme Aesthetics" in d["title"] and "Franklin, TN" in d["title"]
    assert "med spa in Franklin" in d["meta_description"]
    assert "Welcome to Acme Aesthetics" in d["headings"]
    assert "Botox & Fillers" in d["headings"]
    assert d["candidate_email"] == "hello@acmeaesthetics.com"
    assert d["candidate_phone"] == "(615) 555-0123"
    assert "#1a2b3c" in d["candidate_colors"] and "#ff6600" in d["candidate_colors"]
    assert "#000000" not in d["candidate_colors"]            # came from a <script>, must be skipped
    assert "Smooth lines and restore volume." in d["text"]
    assert "should be ignored" not in d["text"]              # <script> body excluded


def _run_all():
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for f in funcs:
        try:
            f(); print(f"  PASS {f.__name__}")
        except Exception as e:
            failed += 1; print(f"  FAIL {f.__name__}: {e!r}")
    print(f"\n{len(funcs)-failed}/{len(funcs)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run_all())
