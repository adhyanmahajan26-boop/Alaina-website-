#!/usr/bin/env python3
"""Submit changed (or all) sitemap URLs to IndexNow. Run by .github/workflows/indexnow.yml.

The key file sits at the site root (<key>.txt) so engines can verify ownership.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = "alainashockabsorbers.com"
SITE = f"https://{HOST}"
KEY_FILE = next(p for p in ROOT.glob("*.txt") if len(p.stem) == 32 and p.read_text().strip() == p.stem)
KEY = KEY_FILE.stem


def sitemap_urls() -> list[str]:
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []
    for sm in ("sitemap-pages.xml", "sitemap-products.xml"):
        urls += [loc.text for loc in ET.parse(ROOT / sm).findall(".//s:url/s:loc", ns)]
    return urls


def page_url(rel: str) -> str | None:
    if rel == "index.html":
        return SITE + "/"
    if rel.endswith("/index.html"):
        return f"{SITE}/{rel[: -len('index.html')]}"
    return None


def changed_urls() -> list[str]:
    before = os.environ.get("BEFORE", "")
    if not before or set(before) == {"0"}:
        before = "HEAD~1"
    diff = subprocess.run(
        ["git", "diff", "--name-only", before, "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.split()
    known = set(sitemap_urls())
    return sorted({u for u in map(page_url, diff) if u in known})


def main() -> None:
    urls = sitemap_urls() if os.environ.get("ALL") == "true" else changed_urls()
    if not urls:
        print("No changed pages to submit.")
        return
    body = json.dumps(
        {"host": HOST, "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt", "urlList": urls[:10000]}
    ).encode()
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow {r.status}: submitted {len(urls)} URL(s)")
    except urllib.error.HTTPError as e:
        # 403: key file not live yet or not verified; 422: URLs not on this host. Retry next deploy.
        if e.code in (403, 422):
            print(f"::warning::IndexNow returned {e.code}; nothing submitted this time.")
            return
        raise
    for u in urls:
        print(" ", u)


if __name__ == "__main__":
    main()
