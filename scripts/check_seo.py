#!/usr/bin/env python3
"""Fail if any built page breaks the SEO basics. Run after scripts/build_seo.py.

Checks every HTML page for: one <title>, a meta description, a canonical URL,
one <h1>, valid JSON-LD with the fields Google reads, FAQ answers that are
visible on the page, and local links, images and WebP sources that exist.
Also checks that every sitemap URL is a built page.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://alainashockabsorbers.com"
SKIP_DIRS = {".git", "scripts", "artifacts", "node_modules"}

errors: list[str] = []


def err(page: Path, msg: str) -> None:
    errors.append(f"{page.relative_to(ROOT)}: {msg}")


def pages() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("*.html")
        if not SKIP_DIRS & set(p.relative_to(ROOT).parts) and not p.name.startswith("google")
    )


def visible_text(doc: str) -> str:
    doc = re.sub(r"<script.*?</script>|<style.*?</style>", " ", doc, flags=re.S)
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", doc)))


def resolve(page: Path, ref: str) -> Path | None:
    """Local file a link/src points at, or None for external, anchor-only and special links."""
    ref = ref.strip()
    if not ref or ref.startswith(("#", "mailto:", "tel:", "javascript:", "data:")) or "${" in ref:
        return None
    u = urlparse(ref)
    if u.scheme or u.netloc:
        if u.netloc != urlparse(SITE).netloc:
            return None
        ref = u.path
    else:
        ref = u.path
    if not ref:
        return None
    ref = unquote(ref)
    target = (ROOT / ref.lstrip("/")) if ref.startswith("/") else (page.parent / ref)
    return target


def exists(target: Path) -> bool:
    return target.is_file() or (target.is_dir() and (target / "index.html").is_file())


def check_ld(page: Path, doc: str, text: str) -> None:
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', doc, flags=re.S)
    if not blocks and page.name != "404.html":
        err(page, "no JSON-LD")
    for raw in blocks:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            err(page, f"JSON-LD does not parse: {e}")
            continue
        t = data.get("@type")
        types = t if isinstance(t, list) else [t]
        if "Product" in types:
            for field in ("name", "image", "sku", "brand", "description"):
                if not data.get(field):
                    err(page, f"Product missing {field}")
            if "offers" in data:
                offers = data["offers"] if isinstance(data["offers"], list) else [data["offers"]]
                for o in offers:
                    for field in ("price", "priceCurrency", "availability"):
                        if not o.get(field):
                            err(page, f"Offer missing {field}")
        if "FAQPage" in types:
            for q in data.get("mainEntity", []):
                name = q.get("name", "")
                answer = q.get("acceptedAnswer", {}).get("text", "")
                if name not in text:
                    err(page, f"FAQ question not visible on page: {name}")
                if re.sub(r"\s+", " ", answer)[:60] not in text:
                    err(page, f"FAQ answer not visible on page: {name}")
        if "BreadcrumbList" in types:
            for el in data.get("itemListElement", []):
                if not str(el.get("item", "")).startswith(SITE):
                    err(page, "breadcrumb item is not an absolute site URL")
        if {"AutoPartsStore", "LocalBusiness"} & set(types):
            if not data.get("address"):
                err(page, f"{t} missing address")


def check_page(page: Path) -> None:
    doc = page.read_text(encoding="utf-8")
    text = visible_text(doc)
    titles = re.findall(r"<title>(.*?)</title>", doc, flags=re.S)
    if len(titles) != 1 or not titles[0].strip():
        err(page, f"expected one non-empty <title>, found {len(titles)}")
    if not re.search(r'<meta name="description" content="[^"]{50,}"', doc):
        err(page, "missing or short meta description")
    if page.name != "404.html":
        if not re.search(r'<link rel="canonical" href="https://alainashockabsorbers\.com/[^"]*"', doc):
            err(page, "missing canonical")
        if len(re.findall(r"<h1[\s>]", doc)) != 1:
            err(page, "expected exactly one <h1>")
    check_ld(page, doc, text)
    for attr, ref in re.findall(r'\s(href|src|srcset|poster)="([^"]+)"', doc):
        for one in ref.split(",") if attr == "srcset" else [ref]:
            target = resolve(page, one.split()[0] if one.split() else one)
            if target is None:
                continue
            if target.suffix == "" and not target.exists():
                target = target / "index.html"
            if not exists(target):
                err(page, f"{attr} points at a missing file: {one}")


def check_sitemaps() -> None:
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for sm in ("sitemap-pages.xml", "sitemap-products.xml"):
        tree = ET.parse(ROOT / sm)
        for loc in tree.findall(".//s:url/s:loc", ns):
            path = urlparse(loc.text).path
            target = ROOT / path.lstrip("/") / "index.html" if path.endswith("/") else ROOT / path.lstrip("/")
            if not target.is_file():
                errors.append(f"{sm}: {loc.text} has no built page")


def check_webp_map() -> None:
    doc = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r"/\*WEBP_START\*/(.*?)/\*WEBP_END\*/", doc, flags=re.S)
    if not m:
        errors.append("index.html: WEBP map markers missing")
        return
    for png, webp in json.loads(m.group(1)).items():
        if not (ROOT / webp).is_file():
            errors.append(f"index.html: WebP copy missing for {png}: {webp}")


def main() -> None:
    built = pages()
    for page in built:
        check_page(page)
    check_sitemaps()
    check_webp_map()
    if errors:
        print("\n".join(errors))
        raise SystemExit(f"{len(errors)} SEO problem(s) in {len(built)} pages")
    print(f"SEO check passed: {len(built)} pages")


if __name__ == "__main__":
    sys.exit(main())
