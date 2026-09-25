#!/usr/bin/env python3
"""Generate crawlable SEO pages, image sitemaps, and WebP copies from catalogue data."""
from __future__ import annotations

import html as htmlmod
import json
import os
import re
import shutil
import struct
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://alainashockabsorbers.com"
TODAY = date.today().isoformat()
WA = "https://wa.me/917982555636"
PHONE = "+91 79825 55636"
EMAIL = "adhyanmahajan26@gmail.com"

sys.path.insert(0, str(ROOT))


def slugify(s: str) -> str:
    s = htmlmod.unescape(s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def esc(s: str) -> str:
    return htmlmod.escape(htmlmod.unescape(s or ""), quote=True)


def load_products() -> list[dict]:
    text = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r"const PRODUCTS = (\[.*?\]);", text)
    if not m:
        raise SystemExit("PRODUCTS array not found in index.html")
    return json.loads(m.group(1))


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as f:
            if f.read(8) != b"\x89PNG\r\n\x1a\n":
                return None
            length, typ = struct.unpack(">I4s", f.read(8))
            if typ != b"IHDR":
                return None
            w, h = struct.unpack(">II", f.read(8))
            return w, h
    except OSError:
        return None


def img_size(path: Path) -> tuple[int, int] | None:
    if path.suffix.lower() == ".png":
        sz = png_size(path)
        if sz:
            return sz
    try:
        from PIL import Image

        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def kind_for(p: dict) -> dict:
    tag = htmlmod.unescape(p.get("tag") or "")
    cat = p.get("cat") or ""
    if tag == "Cabin":
        return {
            "key": "cabin-damper",
            "label": "cabin damper",
            "plural": "cabin dampers",
            "headline": "Cabin Damper",
            "keywords": "cabin damper, cabin shocker, truck cabin damper, AL-CD",
        }
    if tag == "Steering":
        return {
            "key": "steering-damper",
            "label": "steering damper",
            "plural": "steering dampers",
            "headline": "Steering Damper",
            "keywords": "steering damper, steering shocker, AL-DA",
        }
    if tag == "Stabilizer":
        return {
            "key": "stabilizer",
            "label": "shock absorber stabilizer",
            "plural": "shock absorber stabilizers",
            "headline": "Shock Absorber Stabilizer",
            "keywords": "shock absorber stabilizer, stabilizer shocker",
        }
    if cat == "RS":
        return {
            "key": "rare-strut",
            "label": "rare strut",
            "plural": "rare struts",
            "headline": "Rare Strut / Shock Absorber",
            "keywords": "rare strut, shock absorber, shocker, car strut, AL-RS",
        }
    return {
        "key": "shock-absorber",
        "label": "shock absorber",
        "plural": "shock absorbers",
        "headline": "Shock Absorber / Shocker",
        "keywords": "shock absorber, shocker, truck shocker, AL-DA",
    }


def normalize_pn(pn: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", (pn or "").upper())


def to_webp(src: Path, dest: Path, max_w: int = 1600, quality: int = 80) -> bool:
    if not src.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime and dest.stat().st_size > 0:
        return True
    try:
        from PIL import Image

        with Image.open(src) as im:
            im = im.convert("RGB") if im.mode in ("RGBA", "P", "LA") else im.convert("RGB")
            if im.width > max_w:
                h = int(im.height * (max_w / im.width))
                im = im.resize((max_w, h), Image.Resampling.LANCZOS)
            im.save(dest, "WEBP", quality=quality, method=4)
        return dest.exists() and dest.stat().st_size > 0
    except Exception as e:
        print("webp fail", src, e)
        return False


def keyword_name(p: dict) -> str:
    k = p["_kind"]["key"]
    pn = slugify(p["partno"])
    veh = slugify(f"{p['brand']} {htmlmod.unescape(p['name'])}")
    stem = f"alaina-{k}-{pn}-{veh}"
    return stem[:90].rstrip("-")


def enrich(products: list[dict]) -> list[dict]:
    cat_photos = list((ROOT / "catalogue-photos").glob("*.png")) if (ROOT / "catalogue-photos").exists() else []
    photo_index = {}
    for fp in cat_photos:
        photo_index[normalize_pn(fp.stem.split(" - ")[1] if " - " in fp.stem else fp.stem)] = fp

    out = []
    for p in products:
        p = dict(p)
        p["_kind"] = kind_for(p)
        p["_slug"] = slugify(p["partno"])
        p["_name"] = htmlmod.unescape(p["name"])
        p["_tag"] = htmlmod.unescape(p["tag"])
        p["_app"] = htmlmod.unescape(p["app"])
        p["_oe"] = htmlmod.unescape(p.get("oe") or "")
        p["_url"] = f"/products/{p['_slug']}/"
        p["_abs"] = SITE + p["_url"]
        img = p.get("img") or ""
        card = p.get("card") or ""
        p["_img_path"] = ROOT / img if img else None
        p["_card_path"] = ROOT / card if card else None
        p["_has_photo"] = bool(img and p["_img_path"] and p["_img_path"].exists())
        p["_size"] = img_size(p["_img_path"]) if p["_has_photo"] else None
        p["_card_size"] = img_size(p["_card_path"]) if card and p["_card_path"] and p["_card_path"].exists() else None
        p["_alt"] = (
            f"Alaina {p['_kind']['label']} {p['partno']} for {p['brand']} {p['_app']}"
            if p["_has_photo"]
            else ""
        )
        p["_webp"] = None
        p["_card_webp"] = None
        extra = []
        npn = normalize_pn(p["partno"])
        if npn in photo_index:
            extra.append(photo_index[npn])
        p["_extra_photos"] = extra
        out.append(p)
    return out


def convert_images(products: list[dict]) -> None:
    img_dir = ROOT / "images"
    for p in products:
        if not p["_has_photo"]:
            continue
        dest = img_dir / (keyword_name(p) + ".webp")
        if to_webp(p["_img_path"], dest):
            p["_webp"] = dest.relative_to(ROOT).as_posix()
            p["_webp_size"] = img_size(dest)
        if p["_card_path"] and p["_card_path"].exists():
            cdest = img_dir / (keyword_name(p) + "-card.webp")
            if to_webp(p["_card_path"], cdest, max_w=800, quality=78):
                p["_card_webp"] = cdest.relative_to(ROOT).as_posix()


def abs_url(path: str) -> str:
    path = path.lstrip("/")
    return SITE + "/" + quote(path, safe="/()-_.~")


def picture(rel_prefix: str, p: dict, *, lazy: bool, class_name: str = "") -> str:
    if not p["_has_photo"]:
        return (
            '<div class="seo-nopic" role="img" aria-label="Photo not yet shot">'
            "<span>Photo on request</span></div>"
        )
    w, h = p["_size"] or (800, 800)
    src_png = rel_prefix + p["img"]
    src_webp = rel_prefix + p["_webp"] if p["_webp"] else ""
    loading = "lazy" if lazy else "eager"
    fetch = ' fetchpriority="high"' if not lazy else ""
    cls = f' class="{class_name}"' if class_name else ""
    img = (
        f'<img{cls} src="{esc(src_png)}" alt="{esc(p["_alt"])}" title="{esc(p["_alt"])}" '
        f'width="{w}" height="{h}" loading="{loading}"{fetch} decoding="async"/>'
    )
    if src_webp:
        return (
            f'<picture><source type="image/webp" srcset="{esc(src_webp)}"/>{img}</picture>'
        )
    return img


def json_ld(obj) -> str:
    return (
        '<script type="application/ld+json">\n'
        + json.dumps(obj, ensure_ascii=False, indent=2)
        + "\n</script>"
    )


def head_tags(
    *,
    title: str,
    description: str,
    canonical: str,
    keywords: str,
    og_type: str,
    image: str | None,
    image_alt: str | None,
) -> str:
    img = image or f"{SITE}/images/tata-4018-hywa-cabin.png"
    ialt = image_alt or title
    return f"""<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}"/>
<meta name="keywords" content="{esc(keywords)}"/>
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1"/>
<meta name="author" content="Alaina Shockers"/>
<meta name="geo.region" content="IN"/>
<meta name="geo.placename" content="India"/>
<meta name="language" content="en-IN"/>
<link rel="canonical" href="{esc(canonical)}"/>
<link rel="alternate" hreflang="en-IN" href="{esc(canonical)}"/>
<link rel="alternate" hreflang="x-default" href="{esc(canonical)}"/>
<meta property="og:type" content="{esc(og_type)}"/>
<meta property="og:site_name" content="Alaina Shockers"/>
<meta property="og:locale" content="en_IN"/>
<meta property="og:title" content="{esc(title)}"/>
<meta property="og:description" content="{esc(description)}"/>
<meta property="og:url" content="{esc(canonical)}"/>
<meta property="og:image" content="{esc(img)}"/>
<meta property="og:image:alt" content="{esc(ialt)}"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{esc(title)}"/>
<meta name="twitter:description" content="{esc(description)}"/>
<meta name="twitter:image" content="{esc(img)}"/>
<meta name="twitter:image:alt" content="{esc(ialt)}"/>
<link rel="icon" href="/favicon.ico" sizes="48x48"/>
<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png"/>
<link rel="icon" type="image/svg+xml" href="/favicon.svg"/>
<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192x192.png"/>
<link rel="icon" type="image/png" sizes="512x512" href="/favicon-512x512.png"/>
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"/>
<link rel="manifest" href="/site.webmanifest"/>
<meta name="theme-color" content="#FF4A1A"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="{esc('REL')}style.css?v=seo1"/>"""


CHROME_NAV = """
<div id="topbar">
  <div class="wrap">
    <span class="tb-left">Technical Catalogue <b>No.04</b> — 2026 Edition</span>
    <div class="tb-right">
      <span>Est. <b>1978</b> · India</span>
      <a href="tel:+917982555636">+91 79825 55636</a>
    </div>
  </div>
</div>
<header id="nav">
  <div class="wrap">
    <a href="{home}" class="brand">
      <div class="brand-mark">A</div>
      <div class="brand-word">ALAINA<sup>®</sup><small>PRECISION DAMPING</small></div>
    </a>
    <nav class="navlinks">
      <a href="{home}#range"><i>01</i> Range</a>
      <a href="{home}#catalogue"><i>02</i> Catalogue</a>
      <a href="{cd}">Cabin Dampers</a>
      <a href="{sa}">Shockers</a>
      <a href="{rs}">Rare Struts</a>
      <a href="{home}#enquire" class="nav-cta">Enquire &#8599;</a>
    </nav>
    <button class="nav-burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
  </div>
</header>
<div id="mobnav">
  <div class="mn-top">
    <div class="brand-word" style="color:var(--paper)">ALAINA<sup>®</sup></div>
    <button class="mn-x" id="mnClose">&#10005;</button>
  </div>
  <nav>
    <a href="{home}#range"><span>01</span> Range</a>
    <a href="{home}#catalogue"><span>02</span> Catalogue</a>
    <a href="{cd}"><span>03</span> Cabin Dampers</a>
    <a href="{sa}"><span>04</span> Shockers</a>
    <a href="{rs}"><span>05</span> Rare Struts</a>
    <a href="{home}#enquire"><span>06</span> Enquire</a>
  </nav>
</div>
"""


def chrome(rel: str) -> tuple[str, str]:
    home = rel + "index.html" if rel else "/"
    # Prefer clean directory URLs
    nav = CHROME_NAV.format(
        home=rel or "/",
        cd=rel + "cabin-dampers/",
        sa=rel + "shock-absorbers/",
        rs=rel + "rare-struts/",
    )
    footer = f"""
<footer>
  <div class="wrap">
    <div class="foot-top">
      <div class="foot-word">Alaina<sup>®</sup></div>
      <a href="#top" class="foot-up" aria-label="Back to top">↑</a>
    </div>
    <div class="foot-mid">
      <div class="fcol">
        <div class="fc-lab">Colophon</div>
        <p>Precision damping engineered for India's toughest roads. Distributed by Mahajan Motors India.</p>
      </div>
      <div class="fcol">
        <div class="fc-lab">Catalogue</div>
        <a href="{rel}cabin-dampers/">Cabin dampers</a>
        <a href="{rel}shock-absorbers/">Shock absorbers / shockers</a>
        <a href="{rel}rare-struts/">Rare struts</a>
        <a href="{rel}steering-dampers/">Steering dampers</a>
        <a href="{rel}al-cd/">AL-CD series</a>
        <a href="{rel}al-rs/">AL-RS series</a>
        <a href="{rel}al-da/">AL-DA series</a>
      </div>
      <div class="fcol">
        <div class="fc-lab">Also</div>
        <a href="{rel}gas-springs/">Gas springs</a>
        <a href="{rel}dickey-bonnet-struts/">Dickey &amp; bonnet struts</a>
        <a href="{rel}shockers/">Shockers index</a>
        <a href="{rel}#catalogue">Full catalogue</a>
      </div>
      <div class="fcol">
        <div class="fc-lab">Contact</div>
        <a href="tel:+917982555636" class="mono">{PHONE}</a>
        <a href="mailto:{EMAIL}" class="mono">{EMAIL}</a>
        <a href="{WA}?text=Hi%2C%20I%20want%20to%20enquire%20about%20Alaina%20Shockers." target="_blank" rel="noopener">WhatsApp ↗</a>
      </div>
    </div>
    <div class="foot-base">
      <span>© 2026 Alaina Shockers — All parts catalogued</span>
      <span>Technical Catalogue No.04</span>
    </div>
  </div>
</footer>
<a id="wafab" href="{WA}?text=Hi%2C%20I%20want%20to%20enquire%20about%20Alaina%20Shockers." target="_blank" rel="noopener">WhatsApp</a>
<script>
(function(){{
  var b=document.getElementById('burger'), m=document.getElementById('mobnav'), x=document.getElementById('mnClose');
  if(b) b.onclick=function(){{m.classList.add('open');}};
  if(x) x.onclick=function(){{m.classList.remove('open');}};
}})();
</script>
"""
    return nav, footer


def page_shell(rel: str, head: str, body: str, ld: list) -> str:
    nav, footer = chrome(rel)
    head = head.replace("REL", rel)
    lds = "\n".join(json_ld(x) for x in ld)
    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
{head}
{lds}
</head>
<body>
<a id="top"></a>
{nav}
{body}
{footer}
</body>
</html>
"""


def crumbs(items: list[tuple[str, str]]) -> str:
    lis = []
    els = []
    for i, (name, url) in enumerate(items, 1):
        lis.append(f'<li><a href="{esc(url)}">{esc(name)}</a></li>' if i < len(items) else f"<li><span>{esc(name)}</span></li>")
        els.append({"@type": "ListItem", "position": i, "name": name, "item": url if url.startswith("http") else SITE + (url if url.startswith("/") else "/" + url)})
    # fix last item url
    els[-1]["item"] = items[-1][1] if items[-1][1].startswith("http") else SITE + (items[-1][1] if items[-1][1].startswith("/") else "/" + items[-1][1])
    html = '<nav class="crumbs" aria-label="Breadcrumb"><ol>' + "".join(lis) + "</ol></nav>"
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": els}
    return html, ld


def product_card_html(rel: str, p: dict, lazy: bool = True) -> str:
    wamsg = quote(f"Hi, I want to enquire about {p['partno']} — {p['_name']} ({p['_app']}).")
    img = ""
    if p["_has_photo"]:
        src_png = rel + p["img"]
        w, h = p["_size"] or (400, 400)
        img_tag = (
            f'<img src="{esc(src_png)}" alt="{esc(p["_alt"])}" title="{esc(p["_alt"])}" '
            f'width="{w}" height="{h}" loading="{"lazy" if lazy else "eager"}" decoding="async"/>'
        )
        if p["_webp"]:
            webp = rel + p["_webp"]
            img = f'<picture><source type="image/webp" srcset="{esc(webp)}"/>{img_tag}</picture>'
        else:
            img = img_tag
        stage = f'<a class="pc-stage" href="{rel}products/{p["_slug"]}/">{img}</a>'
    else:
        stage = (
            f'<a class="pc-stage no-zoom" href="{rel}products/{p["_slug"]}/">'
            f'<span class="nopic">Photo<br/>on request</span></a>'
        )
    return f"""<article class="pcard">
  {stage}
  <div class="pc-body">
    <div class="pc-top"><span class="pc-no">{esc(p['partno'])}</span><span class="pc-brand">{esc(p['brand'])}</span></div>
    <h3 class="pc-name"><a href="{rel}products/{p['_slug']}/">{esc(p['_name'])}</a></h3>
    <div class="pc-app">{esc(p['_app'])}</div>
    <div class="pc-oe">{'OE ' + esc(p['_oe']) if p['_oe'] else '&nbsp;'}</div>
  </div>
  <div class="pc-foot">
    <a class="pc-btn" href="{rel}products/{p['_slug']}/">View →</a>
    <a class="pc-btn wa" target="_blank" rel="noopener" href="{WA}?text={wamsg}">WA</a>
  </div>
</article>"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def product_jsonld(p: dict) -> dict:
    images = []
    if p["_webp"]:
        images.append(abs_url(p["_webp"]))
    if p["_has_photo"]:
        images.append(abs_url(p["img"]))
    # unique preserve order
    seen = set()
    imgs = []
    for u in images:
        if u not in seen:
            seen.add(u)
            imgs.append(u)
    desc = (
        f"Alaina {p['_kind']['label']} {p['partno']} — {p['_name']} for {p['brand']} {p['_app']}."
        + (f" OE reference {p['_oe']}." if p["_oe"] else "")
        + " OE-matched and pressure-tested. Listed in Alaina Technical Catalogue No.04. Enquire for availability."
    )
    obj = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"Alaina {p['_kind']['headline']} {p['_name']} ({p['partno']})",
        "description": desc,
        "brand": {"@type": "Brand", "name": "Alaina"},
        "sku": p["partno"],
        "mpn": p["partno"],
        "category": p["_kind"]["headline"],
        "url": p["_abs"],
    }
    if imgs:
        obj["image"] = imgs
    extra_props = [
        {"@type": "PropertyValue", "name": "Vehicle application", "value": f"{p['brand']} {p['_app']}"},
        {"@type": "PropertyValue", "name": "Position / type", "value": p["_tag"]},
        {"@type": "PropertyValue", "name": "Catalogue line", "value": "Heavy Duty" if p["cat"] == "HD" else "Rare Struts"},
    ]
    if p["_oe"]:
        extra_props.append({"@type": "PropertyValue", "name": "OE reference", "value": p["_oe"]})
    obj["additionalProperty"] = extra_props
    # no offers — no prices in repo
    return obj


def render_product(p: dict, all_products: list[dict]) -> str:
    rel = "../../"
    kind = p["_kind"]
    title = f"{p['_name']} ({p['partno']}) | Alaina {kind['headline']}"
    desc = (
        f"Alaina {kind['label']} {p['partno']} for {p['brand']} {p['_app']}."
        + (f" OE {p['_oe']}." if p["_oe"] else "")
        + " Pressure-tested, OE-matched. Enquire on WhatsApp for stock."
    )
    img_abs = abs_url(p["_webp"] or p["img"]) if p["_has_photo"] else abs_url("images/damper-closeup.jpg")
    keywords = (
        f"Alaina {kind['label']}, {p['partno']}, {p['brand']} {p['_name']}, "
        f"shocker for {p['brand']} {p['_app']}, {kind['keywords']}, Alaina shockers"
    )
    head = head_tags(
        title=title,
        description=desc,
        canonical=p["_abs"],
        keywords=keywords,
        og_type="product",
        image=img_abs,
        image_alt=p["_alt"] or title,
    )
    crumb_html, crumb_ld = crumbs(
        [
            ("Home", SITE + "/"),
            (kind["plural"].title(), SITE + category_url_for_kind(kind["key"])),
            (p["partno"], p["_abs"]),
        ]
    )
    related = [x for x in all_products if x["brand"] == p["brand"] and x["_slug"] != p["_slug"]][:8]
    fig = ""
    if p["_has_photo"]:
        cap = f"Alaina {kind['label']} {p['partno']} — {p['brand']} {p['_name']} ({p['_app']})"
        fig = f"""
        <figure class="seo-figure">
          {picture(rel, p, lazy=False)}
          <figcaption>{esc(cap)}</figcaption>
        </figure>
        """
    else:
        fig = """
        <div class="seo-nopic-lg">
          <p>No product photo in the catalogue yet. Ask for a current unit photo when you enquire.</p>
        </div>
        """
    oe_row = f'<div class="seo-kv"><span>OE reference</span><b>{esc(p["_oe"])}</b></div>' if p["_oe"] else ""
    rel_grid = "".join(product_card_html(rel, x) for x in related)
    wa = quote(f"Hi, I want to enquire about {p['partno']} — {p['_name']} ({p['_app']}).")
    body = f"""
<main class="seo-main wrap">
  {crumb_html}
  <p class="kicker">{esc(p['brand'])} · {esc(kind['headline'])}</p>
  <h1>{esc(p['_name'])} <span class="seo-h1-sub">{esc(p['partno'])}</span></h1>
  <p class="seo-lead">Alaina {esc(kind['label'])} for {esc(p['brand'])} {esc(p['_app'])}. Listed in Technical Catalogue No.04. Built to OE reference dimensions and pressure-tested before dispatch.</p>
  <div class="seo-split">
    {fig}
    <aside class="seo-spec">
      <div class="seo-kv"><span>Part number</span><b class="mono">{esc(p['partno'])}</b></div>
      <div class="seo-kv"><span>Brand (vehicle)</span><b>{esc(p['brand'])}</b></div>
      <div class="seo-kv"><span>Type</span><b>{esc(kind['headline'])}</b></div>
      <div class="seo-kv"><span>Position</span><b>{esc(p['_tag'])}</b></div>
      <div class="seo-kv"><span>Application</span><b>{esc(p['_app'])}</b></div>
      {oe_row}
      <div class="seo-kv"><span>Line</span><b>{"Heavy Duty" if p["cat"]=="HD" else "Rare Struts"}</b></div>
      <p class="seo-note">Price is quoted on enquiry — this catalogue does not publish list prices.</p>
      <a class="es-wa" href="{WA}?text={wa}" target="_blank" rel="noopener">WhatsApp this part ↗</a>
    </aside>
  </div>
  <section>
    <h2>Fitment</h2>
    <p>This {esc(kind['label'])} is catalogued for <strong>{esc(p['brand'])} {esc(p['_app'])}</strong>. Confirm the OE number{" (" + esc(p['_oe']) + ")" if p["_oe"] else ""} and the old unit before ordering. For the same vehicle see other Alaina {esc(p['brand'])} parts below.</p>
  </section>
  {"<section><h2>More " + esc(p["brand"]) + " parts</h2><div class='cat-grid'>" + rel_grid + "</div></section>" if related else ""}
</main>
"""
    ld = [product_jsonld(p), crumb_ld]
    return page_shell(rel, head, body, ld)


def category_url_for_kind(key: str) -> str:
    return {
        "cabin-damper": "/cabin-dampers/",
        "rare-strut": "/rare-struts/",
        "shock-absorber": "/shock-absorbers/",
        "steering-damper": "/steering-dampers/",
        "stabilizer": "/shock-absorbers/",
    }.get(key, "/shock-absorbers/")


def item_list_ld(name: str, url: str, items: list[dict]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "numberOfItems": len(items),
        "url": url,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "url": p["_abs"],
                "name": f"Alaina {p['_name']} ({p['partno']})",
            }
            for i, p in enumerate(items, 1)
        ],
    }


def collection_product_ld(name: str, description: str, images: list[str], url: str) -> dict:
    obj = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": description,
        "brand": {"@type": "Brand", "name": "Alaina"},
        "url": url,
        "category": "Automotive suspension parts",
    }
    if images:
        obj["image"] = images[:12]
    return obj


def render_collection(
    *,
    path: str,
    title: str,
    h1: str,
    description: str,
    keywords: str,
    intro: str,
    items: list[dict],
    crumb_name: str,
    extra_links: list[tuple[str, str]] | None = None,
    product_line_name: str | None = None,
    rel: str | None = None,
) -> str:
    if rel is None:
        depth = path.strip("/").count("/") + 1 if path.strip("/") else 0
        rel = "../" * depth
    url = SITE + path
    first = next((p for p in items if p["_has_photo"]), None)
    og = abs_url(first["_webp"] or first["img"]) if first else abs_url("images/tata-4018-hywa-cabin.png")
    og_alt = first["_alt"] if first else title
    head = head_tags(
        title=title,
        description=description,
        canonical=url,
        keywords=keywords,
        og_type="website",
        image=og,
        image_alt=og_alt,
    )
    crumb_html, crumb_ld = crumbs([("Home", SITE + "/"), (crumb_name, url)])
    grid = "".join(product_card_html(rel, p, lazy=True) for p in items)
    links = ""
    if extra_links:
        links = (
            "<p class='seo-also'>"
            + " ".join(f'<a href="{rel}{href.lstrip("/")}">{esc(lab)}</a>' for lab, href in extra_links)
            + "</p>"
        )
    body = f"""
<main class="seo-main wrap">
  {crumb_html}
  <p class="kicker">Alaina range</p>
  <h1>{esc(h1)}</h1>
  <p class="seo-lead">{intro}</p>
  {links}
  <p class="seo-count">{len(items)} catalogued part{"s" if len(items)!=1 else ""} — every SKU below is from Technical Catalogue No.04.</p>
  <div class="cat-grid">
    {grid if items else "<p>No SKUs for this line are published in the current catalogue. <a href='../#enquire'>Enquire with your vehicle model</a>.</p>"}
  </div>
</main>
"""
    images = []
    for p in items:
        if p.get("_webp"):
            images.append(abs_url(p["_webp"]))
        elif p["_has_photo"]:
            images.append(abs_url(p["img"]))
    ld = [crumb_ld]
    if items:
        ld.append(item_list_ld(h1, url, items))
        ld.append(collection_product_ld(product_line_name or h1, description, images, url))
    else:
        ld.append(
            {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": h1,
                "description": description,
                "url": url,
                "isPartOf": {"@type": "WebSite", "url": SITE + "/", "name": "Alaina Shockers"},
            }
        )
    return page_shell(rel, head, body, ld)


def vehicle_groups(products: list[dict]) -> list[dict]:
    rules = [
        ("tata-4018", "Tata 4018", "Tata", lambda p: p["brand"] == "Tata" and "4018" in (p["_name"] + p["_app"])),
        ("tata-1516", "Tata 1516", "Tata", lambda p: p["brand"] == "Tata" and "1516" in (p["_name"] + p["_app"])),
        ("tata-1518", "Tata 1518", "Tata", lambda p: p["brand"] == "Tata" and "1518" in (p["_name"] + p["_app"])),
        ("tata-hywa", "Tata Hywa", "Tata", lambda p: p["brand"] == "Tata" and "Hywa" in (p["_name"] + p["_app"])),
        ("tata-signa", "Tata Signa", "Tata", lambda p: p["brand"] == "Tata" and "Signa" in (p["_name"] + p["_app"])),
        ("tata-prima", "Tata Prima", "Tata", lambda p: p["brand"] == "Tata" and "Prima" in (p["_name"] + p["_app"])),
        ("tata-1526", "Tata 1526", "Tata", lambda p: p["brand"] == "Tata" and "1526" in (p["_name"] + p["_app"])),
        ("tata-709", "Tata 709", "Tata", lambda p: p["brand"] == "Tata" and "709" in (p["_name"] + p["_app"])),
        ("tata-1109", "Tata 1109", "Tata", lambda p: p["brand"] == "Tata" and "1109" in (p["_name"] + p["_app"])),
        ("tata-2515", "Tata 2515", "Tata", lambda p: p["brand"] == "Tata" and "2515" in (p["_name"] + p["_app"])),
        ("tata-b54", "Tata B54", "Tata", lambda p: p["brand"] == "Tata" and "B54" in (p["_name"] + p["_app"])),
        ("leyland-u-truck", "Ashok Leyland U Truck", "Leyland", lambda p: p["brand"] == "Leyland" and "U Truck" in (p["_name"] + p["_app"])),
        ("leyland-g91", "Ashok Leyland G91", "Leyland", lambda p: p["brand"] == "Leyland" and "G91" in (p["_name"] + p["_app"])),
        ("leyland-stalian", "Ashok Leyland Stalian", "Leyland", lambda p: p["brand"] == "Leyland" and "Stalian" in (p["_name"] + p["_app"])),
        ("leyland-2518", "Ashok Leyland 2518", "Leyland", lambda p: p["brand"] == "Leyland" and "2518" in (p["_name"] + p["_app"])),
        ("leyland-ngc", "Ashok Leyland NGC", "Leyland", lambda p: p["brand"] == "Leyland" and "NGC" in (p["_name"] + p["_app"])),
        ("leyland-a-star", "Ashok Leyland A Star", "Leyland", lambda p: p["brand"] == "Leyland" and "A Star" in (p["_name"] + p["_app"])),
        ("leyland-marcopolo", "Ashok Leyland Marcopolo", "Leyland", lambda p: p["brand"] == "Leyland" and "Marcopolo" in (p["_name"] + p["_app"])),
        ("eicher-canter", "Eicher Canter", "Eicher", lambda p: p["brand"] == "Eicher" and "Canter" in (p["_name"] + p["_app"])),
        ("eicher-pro", "Eicher Pro", "Eicher", lambda p: p["brand"] == "Eicher" and "Pro" in (p["_name"] + p["_app"])),
        ("bharat-benz", "Bharat Benz", "Eicher", lambda p: "Bharat Benz" in (p["_name"] + p["_app"] + p["brand"])),
        ("mann", "Mann cabin", "Eicher", lambda p: "Mann" in (p["_name"] + p["_app"])),
        ("amw", "AMW", "Eicher", lambda p: "AMW" in (p["_name"] + p["_app"])),
        ("mahindra-bolero", "Mahindra Bolero", "Mahindra", lambda p: p["brand"] == "Mahindra" and "Bolero" in (p["_name"] + p["_app"]) and "Pickup" not in p["_name"]),
        ("mahindra-bolero-pickup", "Mahindra Bolero Pickup", "Mahindra", lambda p: p["brand"] == "Mahindra" and "Bolero Pickup" in (p["_name"] + p["_app"])),
        ("mahindra-navi-star", "Mahindra Navi Star", "Mahindra", lambda p: p["brand"] == "Mahindra" and "Navi Star" in (p["_name"] + p["_app"])),
        ("toyota-camry", "Toyota Camry", "Toyota", lambda p: p["brand"] == "Toyota" and "Camry" in (p["_name"] + p["_app"])),
        ("toyota-corolla", "Toyota Corolla", "Toyota", lambda p: p["brand"] == "Toyota" and "Corolla" in (p["_name"] + p["_app"])),
        ("renault-duster", "Renault Duster 4x4", "Renault", lambda p: p["brand"] == "Renault" and "Duster" in (p["_name"] + p["_app"])),
        ("mitsubishi-lancer", "Mitsubishi Lancer", "Mitsubishi", lambda p: p["brand"] == "Mitsubishi" and "Lancer" in p["_name"] and "Cedia" not in p["_name"]),
        ("mitsubishi-lancer-cedia", "Mitsubishi Lancer Cedia", "Mitsubishi", lambda p: p["brand"] == "Mitsubishi" and "Cedia" in (p["_name"] + p["_app"])),
        ("isuzu-d-max", "Isuzu D-Max", "Isuzu", lambda p: p["brand"] == "Isuzu" and "D-Max" in (p["_name"] + p["_app"])),
        ("suzuki-baleno", "Suzuki Baleno", "Suzuki", lambda p: p["brand"] == "Suzuki" and "Baleno" in (p["_name"] + p["_app"])),
        ("mg-hector", "MG Hector", "MG", lambda p: p["brand"] == "MG" and "Hector" in (p["_name"] + p["_app"])),
    ]
    groups = []
    for slug, name, brand, fn in rules:
        items = [p for p in products if fn(p)]
        if items:
            groups.append({"slug": slug, "name": name, "brand": brand, "items": items})
    return groups


def sitemap_url(loc: str, images: list[tuple[str, str]], lastmod: str = TODAY, pri: str = "0.7") -> str:
    parts = [
        "  <url>",
        f"    <loc>{esc(loc)}</loc>",
        f"    <lastmod>{lastmod}</lastmod>",
        "    <changefreq>weekly</changefreq>",
        f"    <priority>{pri}</priority>",
    ]
    seen = set()
    for href, title in images:
        if href in seen:
            continue
        seen.add(href)
        parts.append("    <image:image>")
        parts.append(f"      <image:loc>{esc(href)}</image:loc>")
        if title:
            parts.append(f"      <image:title>{esc(title)}</image:title>")
            parts.append(f"      <image:caption>{esc(title)}</image:caption>")
        parts.append("    </image:image>")
    parts.append("  </url>")
    return "\n".join(parts)


def wrap_urlset(body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        + body
        + "\n</urlset>\n"
    )


def images_for_product(p: dict) -> list[tuple[str, str]]:
    out = []
    if p.get("_webp"):
        out.append((abs_url(p["_webp"]), p["_alt"]))
    if p["_has_photo"]:
        out.append((abs_url(p["img"]), p["_alt"]))
    return out


def patch_index(products: list[dict], categories: list[dict]) -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    # Never rewrite the live host away. Fold the defunct keyword-domain onto SITE.
    text = text.replace("https://alainashockers.com", SITE)
    text = text.replace("http://alainashockers.com", SITE)
    text = text.replace("https://www.alainashockabsorbers.com", SITE)
    text = text.replace("http://www.alainashockabsorbers.com", SITE)
    text = text.replace('<html lang="en">', '<html lang="en-IN">')

    if 'hreflang="en-IN"' not in text:
        text = text.replace(
            f'<link rel="canonical" href="{SITE}/"/>',
            f'<link rel="canonical" href="{SITE}/"/>\n'
            f'<link rel="alternate" hreflang="en-IN" href="{SITE}/"/>\n'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/"/>',
        )
    if "og:image:alt" not in text:
        text = text.replace(
            f'<meta property="og:image" content="{SITE}/images/tata-b54-3718-front.png"/>',
            f'<meta property="og:image" content="{SITE}/images/tata-4018-hywa-cabin.png"/>\n'
            f'<meta property="og:image:alt" content="Alaina cabin damper for Tata 4018 Hywa / Prima"/>',
        )
        text = text.replace(
            f'<meta name="twitter:image" content="{SITE}/images/tata-b54-3718-front.png"/>',
            f'<meta name="twitter:image" content="{SITE}/images/tata-4018-hywa-cabin.png"/>\n'
            f'<meta name="twitter:image:alt" content="Alaina cabin damper for Tata 4018 Hywa / Prima"/>',
        )
    if 'name="language"' not in text:
        text = text.replace(
            '<meta name="geo.placename" content="India"/>',
            '<meta name="geo.placename" content="India"/>\n<meta name="language" content="en-IN"/>',
        )

    org_ld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Alaina Shockers",
        "alternateName": ["Alaina Shocker", "Alaina Shock Absorbers", "Alaina Dampers"],
        "url": SITE + "/",
        "telephone": "+91-79825-55636",
        "email": EMAIL,
        "foundingDate": "1978",
        "parentOrganization": {"@type": "Organization", "name": "Mahajan Motors India"},
        "areaServed": {"@type": "Country", "name": "India"},
        "brand": {"@type": "Brand", "name": "Alaina"},
        "logo": SITE + "/favicon-512x512.png",
    }
    website_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Alaina Shockers",
        "url": SITE + "/",
        "inLanguage": "en-IN",
        "potentialAction": {
            "@type": "SearchAction",
            "target": SITE + "/?q={search_term_string}",
            "query-input": "required name=search_term_string",
        },
    }
    if '"@type": "WebSite"' not in text:
        insert = json_ld(org_ld) + "\n" + json_ld(website_ld) + "\n"
        text = text.replace('<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "AutoPartsStore"', insert + '<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "AutoPartsStore"', 1)

    text = text.replace(
        f'"logo": "{SITE}/images/tata-4018-hywa-cabin.png"',
        f'"logo": "{SITE}/favicon-512x512.png"',
    )
    if '"alternateName"' not in text:
        text = text.replace(
            '  "name": "Alaina Shockers",\n  "url": "' + SITE + '/"',
            '  "name": "Alaina Shockers",\n'
            '  "alternateName": ["Alaina Shocker", "Alaina Shock Absorbers", "Alaina Dampers"],\n'
            '  "url": "' + SITE + '/"',
            1,
        )
    old_icon = '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\'%3E%3Crect width=\'32\' height=\'32\' fill=\'%23171511\'/%3E%3Ctext x=\'16\' y=\'23\' font-family=\'Arial Black\' font-size=\'19\' font-weight=\'900\' fill=\'%23F2F0EA\' text-anchor=\'middle\'%3EA%3C/text%3E%3C/svg%3E"/>'
    new_icon = (
        '<link rel="icon" href="/favicon.ico" sizes="48x48"/>\n'
        '<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png"/>\n'
        '<link rel="icon" type="image/svg+xml" href="/favicon.svg"/>\n'
        '<link rel="icon" type="image/png" sizes="192x192" href="/favicon-192x192.png"/>\n'
        '<link rel="icon" type="image/png" sizes="512x512" href="/favicon-512x512.png"/>\n'
        '<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"/>\n'
        '<link rel="manifest" href="/site.webmanifest"/>\n'
        '<meta name="theme-color" content="#FF4A1A"/>'
    )
    if 'href="/favicon.ico"' not in text:
        text = text.replace(old_icon, new_icon)

    # Homepage body must stay pre-SEO: no static catalog FOUC, no PDF-card images,
    # no seo-browse strip, no range-row/footer visual rewires.
    text = re.sub(
        r"\n<section id=\"seo-browse\">.*?</section>\n",
        "\n",
        text,
        count=1,
        flags=re.S,
    )
    if "<!--SEO_CATALOG_START-->" in text:
        text = re.sub(
            r"<!--SEO_CATALOG_START-->.*?<!--SEO_CATALOG_END-->\n?",
            "",
            text,
            count=1,
            flags=re.S,
        )
        text = re.sub(
            r'(<div class="cat-grid" id="table">)\s*(</div>)',
            r"\1\2",
            text,
            count=1,
        )

    if "URLSearchParams" not in text:
        text = text.replace(
            "let fBrand='All', fQ='';",
            """let fBrand='All', fQ='';
(function(){
  const sp=new URLSearchParams(location.search);
  const q=sp.get('q');
  if(q){fQ=q.trim().toLowerCase();}
})();""",
        )
        text = text.replace(
            "$('#yr').textContent=new Date().getFullYear();\nrenderChips();renderTable();",
            """$('#yr').textContent=new Date().getFullYear();
if(fQ && $('#q')) $('#q').value=fQ;
renderChips();renderTable();
if(fQ) document.getElementById('catalogue')?.scrollIntoView();""",
        )

    path.write_text(text, encoding="utf-8")


def add_seo_css() -> None:
    css_path = ROOT / "style.css"
    css = css_path.read_text(encoding="utf-8")
    if "seo-main" in css:
        return
    css += """
/* ════════════════ SEO inner pages ════════════════ */
.seo-main{padding:clamp(28px,5vw,72px) 0 80px}
.crumbs ol{display:flex;flex-wrap:wrap;gap:8px;list-style:none;font-family:var(--fm);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--text-40);margin-bottom:22px}
.crumbs li:not(:last-child)::after{content:'/';margin-left:8px;opacity:.5}
.crumbs a:hover{color:var(--brass)}
.seo-main h1{font-family:var(--fd);font-weight:800;font-size:clamp(28px,4vw,52px);line-height:1.05;letter-spacing:-.02em;text-transform:uppercase;margin:10px 0 16px}
.seo-h1-sub{display:block;font-family:var(--fm);font-size:14px;letter-spacing:.16em;color:var(--accent);margin-top:10px;text-transform:none}
.seo-lead{font-size:16px;line-height:1.7;color:var(--text-60);max-width:720px;margin-bottom:28px}
.seo-count{font-family:var(--fm);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-40);margin-bottom:22px}
.seo-split{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(260px,.8fr);gap:36px;align-items:start;margin-bottom:48px}
.seo-figure{background:var(--plate);padding:18px;margin:0}
.seo-figure img,.seo-figure picture{width:100%;height:auto}
.seo-figure figcaption{font-family:var(--fm);font-size:11px;color:#333;margin-top:10px;letter-spacing:.04em}
.seo-figure-extra{margin-top:16px}
.seo-spec{border:1px solid var(--rule);background:var(--bg-2);padding:8px 0 18px}
.seo-kv{display:flex;justify-content:space-between;gap:16px;padding:12px 18px;border-bottom:1px solid var(--rule-soft);font-size:14px}
.seo-kv span{color:var(--text-40);font-family:var(--fm);font-size:11px;letter-spacing:.12em;text-transform:uppercase}
.seo-note{padding:16px 18px 8px;color:var(--text-60);font-size:13px}
.seo-nopic,.seo-nopic-lg{background:var(--bg-3);border:1px dashed var(--rule);min-height:220px;display:grid;place-items:center;color:var(--text-40);text-align:center;padding:24px}
.seo-also{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 18px}
.seo-also a{border:1px solid var(--rule);padding:8px 12px;font-size:13px;color:var(--text-60)}
.seo-also a:hover{border-color:var(--accent);color:var(--text)}
.seo-browse-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:10px}
.seo-browse-grid a{border:1px solid var(--rule);padding:18px;background:var(--bg-2);transition:.2s}
.seo-browse-grid a:hover{border-color:var(--accent)}
.seo-browse-grid strong{display:block;font-family:var(--fd);font-size:18px;margin-bottom:6px}
.seo-browse-grid span{color:var(--text-60);font-size:13px}
#seo-browse{padding:clamp(40px,6vw,80px) 0;border-bottom:1px solid var(--rule)}
.pc-name a:hover{color:var(--accent)}
@media(max-width:900px){.seo-split{grid-template-columns:1fr}}
"""
    css_path.write_text(css, encoding="utf-8")


def write_htaccess() -> None:
    (ROOT / ".htaccess").write_text(
        r"""# Security Headers
Header always set X-Frame-Options "SAMEORIGIN"
Header always set X-Content-Type-Options "nosniff"
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; media-src 'self'; connect-src 'self'; frame-ancestors 'none';"

Options -MultiViews
RewriteEngine On

# Canonical host: https://alainashockabsorbers.com (apex). Preserve path/query.
RewriteCond %{HTTP_HOST} ^www\.alainashockabsorbers\.com$ [NC,OR]
RewriteCond %{HTTPS} !=on
RewriteCond %{HTTP_HOST} ^(www\.)?alainashockabsorbers\.com$ [NC]
RewriteRule ^ https://alainashockabsorbers.com%{REQUEST_URI} [L,R=301]

AddType application/xml .xml
AddType text/plain .txt
AddType image/webp .webp
AddType text/html .html
AddType image/svg+xml .svg
AddType image/x-icon .ico
AddType image/vnd.microsoft.icon .ico
AddType application/manifest+json .webmanifest

<Files "sitemap.xml">
  Header set Content-Type "application/xml; charset=UTF-8"
</Files>
<FilesMatch "^sitemap-.*\.xml$">
  Header set Content-Type "application/xml; charset=UTF-8"
</FilesMatch>
<Files "robots.txt">
  Header set Content-Type "text/plain; charset=UTF-8"
</Files>

# Do not SPA-fallback verification files, sitemaps, robots, or icons
RewriteRule ^google[0-9a-z]+\.html$ - [L]
RewriteRule ^robots\.txt$ - [L]
RewriteRule ^sitemap(-[a-z0-9-]+)?\.xml$ - [L]
RewriteRule ^(favicon\.(ico|svg)|apple-touch-icon\.png|favicon-[0-9]+x[0-9]+\.png|site\.webmanifest)$ - [L]

# SPA Routing Fallback (skips real files and directories)
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.html [QSA,L]

# Cache static assets
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/png "access plus 1 month"
  ExpiresByType image/jpeg "access plus 1 month"
  ExpiresByType image/webp "access plus 1 month"
  ExpiresByType image/svg+xml "access plus 1 month"
  ExpiresByType image/x-icon "access plus 1 month"
  ExpiresByType application/manifest+json "access plus 1 week"
  ExpiresByType application/xml "access plus 1 day"
  ExpiresByType text/plain "access plus 1 day"
  ExpiresByType text/xml "access plus 1 day"
  ExpiresByType video/mp4 "access plus 1 month"
  ExpiresByType text/css "access plus 1 week"
  ExpiresByType application/javascript "access plus 1 week"
</IfModule>

# Block access to sensitive files
<FilesMatch "\.(env|json|md|sh|log|sql|bak)$">
  Order allow,deny
  Deny from all
</FilesMatch>
""",
        encoding="utf-8",
    )


def write_robots() -> None:
    (ROOT / "robots.txt").write_text(
        """User-agent: *
Allow: /
Allow: /images/
Allow: /catalogue-photos/
Allow: /*.webp$
Allow: /*.png$
Allow: /*.jpg$
Allow: /*.jpeg$
Allow: /sitemap.xml
Allow: /robots.txt
Allow: /google2874721c1e7298d6.html
Allow: /favicon.ico
Allow: /favicon.svg
Allow: /favicon-48x48.png
Allow: /favicon-192x192.png
Allow: /favicon-512x512.png
Allow: /apple-touch-icon.png
Allow: /site.webmanifest
Disallow: /scripts/
Disallow: /SEO.md

Sitemap: https://alainashockabsorbers.com/sitemap.xml

User-agent: Googlebot-Image
Allow: /images/
Allow: /catalogue-photos/
Allow: /*.webp$
Allow: /*.png$
Allow: /*.jpg$
Allow: /favicon.ico
Allow: /favicon.svg
Allow: /apple-touch-icon.png
Allow: /site.webmanifest
""",
        encoding="utf-8",
    )


def main() -> None:
    import runpy
    runpy.run_path(str(ROOT / "scripts" / "build_favicon.py"), run_name="__main__")
    products = enrich(load_products())
    print("products", len(products))
    convert_images(products)

    cabin = [p for p in products if p["_kind"]["key"] == "cabin-damper"]
    struts = [p for p in products if p["_kind"]["key"] == "rare-strut"]
    steering = [p for p in products if p["_kind"]["key"] == "steering-damper"]
    shockers = [p for p in products if p["_kind"]["key"] in ("shock-absorber", "stabilizer")]
    al_da = [p for p in products if p["_kind"]["key"] in ("cabin-damper", "steering-damper", "shock-absorber", "stabilizer")]
    hd = [p for p in products if p["cat"] == "HD"]

    pages = []  # (path, lastmod, images, priority)

    # product pages
    for p in products:
        html = render_product(p, products)
        dest = ROOT / "products" / p["_slug"] / "index.html"
        write(dest, html)
        pages.append((p["_url"], TODAY, images_for_product(p), "0.8"))

    collections = [
        dict(
            path="/cabin-dampers/",
            title="Cabin Dampers & Cabin Shockers for Tata, Leyland, Eicher | Alaina",
            h1="Cabin dampers",
            description="Alaina cabin dampers (cabin shockers) for Tata, Ashok Leyland, Eicher, Bharat Benz and Mann trucks. OE-matched, pressure-tested. Catalogue No.04.",
            keywords="cabin damper, cabin shocker, truck cabin damper, Tata cabin damper, Leyland cabin damper, Eicher cabin damper, Alaina AL-CD",
            intro="Heavy-duty <strong>cabin dampers</strong> — the unit that keeps a commercial-vehicle cabin civilised. Every part number below is from the live Alaina catalogue (OE references included where the catalogue lists them).",
            items=cabin,
            crumb="Cabin dampers",
            extra=[("AL-CD series", "/al-cd/"), ("Shock absorbers", "/shock-absorbers/"), ("Rare struts", "/rare-struts/")],
            line="Alaina AL-CD Cabin Dampers",
        ),
        dict(
            path="/shock-absorbers/",
            title="Shock Absorbers & Shockers for Trucks and Pickups | Alaina",
            h1="Shock absorbers / shockers",
            description="Alaina shock absorbers and shockers for Tata, Ashok Leyland, Eicher, Mahindra Bolero and Navi Star. Front, rear and stabilizer units from Catalogue No.04.",
            keywords="shock absorber, shockers, truck shocker, Bolero shocker, Tata shocker, Alaina shock absorbers, AL-DA",
            intro="Alaina <strong>shock absorbers</strong> (shockers) catalogued for commercial trucks and Mahindra pickups — front, rear and stabilizer applications as listed in Technical Catalogue No.04.",
            items=shockers,
            crumb="Shock absorbers",
            extra=[("Cabin dampers", "/cabin-dampers/"), ("AL-DA series", "/al-da/"), ("Shockers index", "/shockers/")],
            line="Alaina Shock Absorbers",
        ),
        dict(
            path="/shockers/",
            title="Shockers — Alaina Shock Absorbers for Indian Vehicles",
            h1="Shockers",
            description="Alaina shockers: cabin dampers, truck shock absorbers and rare car struts. Search by part number or vehicle — Tata, Leyland, Eicher, Bolero, Camry and more.",
            keywords="shockers, shocker, shock absorber India, Alaina shockers, cabin shocker",
            intro="In Indian trade, <strong>shocker</strong> means shock absorber. This index lists every Alaina SKU in the published catalogue — cabin dampers, truck shockers, pickup shockers and rare passenger-car struts.",
            items=products,
            crumb="Shockers",
            extra=[("Shock absorbers", "/shock-absorbers/"), ("Cabin dampers", "/cabin-dampers/")],
            line="Alaina Shockers",
        ),
        dict(
            path="/rare-struts/",
            title="Rare Struts for Camry, Corolla, Lancer, Duster, Hector | Alaina",
            h1="Rare struts",
            description="Alaina rare struts for Toyota Camry and Corolla, Mitsubishi Lancer, Renault Duster 4x4, Isuzu D-Max, Suzuki Baleno and MG Hector. Catalogue No.04.",
            keywords="rare strut, Camry strut, Corolla shock absorber, Lancer shocker, Duster 4x4 strut, Hector strut, Alaina AL-RS",
            intro="Passenger-car <strong>rare struts</strong> Alaina still catalogues — models where the OE strut is often hard to find in India. Fitments below are exactly as listed (including year ranges where the catalogue gives them).",
            items=struts,
            crumb="Rare struts",
            extra=[("AL-RS series", "/al-rs/"), ("Shockers", "/shockers/")],
            line="Alaina AL-RS Rare Struts",
        ),
        dict(
            path="/steering-dampers/",
            title="Steering Dampers — Mahindra Bolero / Marshal | Alaina",
            h1="Steering dampers",
            description="Alaina steering damper for Mahindra Bolero / Marshal, part MA-BO-4021, from Technical Catalogue No.04.",
            keywords="steering damper, Bolero steering damper, Marshal steering shocker, Alaina MA-BO-4021",
            intro="Steering dampers published in the Alaina catalogue. Only SKUs that actually appear in Catalogue No.04 are listed.",
            items=steering,
            crumb="Steering dampers",
            extra=[("Bolero shockers", "/shockers/mahindra-bolero/"), ("AL-DA", "/al-da/")],
            line="Alaina Steering Dampers",
        ),
        dict(
            path="/al-cd/",
            title="Alaina AL-CD Cabin Dampers | Truck Cabin Shockers",
            h1="AL-CD cabin dampers",
            description="Alaina AL-CD cabin damper line: every cabin-tagged SKU in Catalogue No.04 for Tata, Ashok Leyland, Eicher, Bharat Benz and Mann.",
            keywords="AL-CD, Alaina AL-CD, cabin damper, cabin shocker, truck cabin damper",
            intro="Index of Alaina <strong>cabin damper</strong> SKUs (the AL-CD line on this site). These are the same cabin parts as the public catalogue — no extra part numbers have been added.",
            items=cabin,
            crumb="AL-CD",
            extra=[("Cabin dampers", "/cabin-dampers/"), ("AL-DA", "/al-da/")],
            line="Alaina AL-CD Cabin Dampers",
        ),
        dict(
            path="/al-rs/",
            title="Alaina AL-RS Rare Struts | Passenger Car Shock Absorbers",
            h1="AL-RS rare struts",
            description="Alaina AL-RS rare strut line: Camry, Corolla, Lancer, Duster, D-Max, Baleno and Hector struts from Catalogue No.04.",
            keywords="AL-RS, Alaina AL-RS, rare strut, car shock absorber",
            intro="Index of Alaina <strong>rare strut</strong> SKUs (the AL-RS line on this site), matching the Rare Struts section of Technical Catalogue No.04.",
            items=struts,
            crumb="AL-RS",
            extra=[("Rare struts", "/rare-struts/"), ("AL-CD", "/al-cd/")],
            line="Alaina AL-RS Rare Struts",
        ),
        dict(
            path="/al-da/",
            title="Alaina AL-DA Dampers | Cabin, Steering and Shock Absorbers",
            h1="AL-DA dampers",
            description="Alaina AL-DA damper line: cabin dampers, steering dampers and shock absorbers from Catalogue No.04. Enquire for vehicle-specific shockers.",
            keywords="AL-DA, Alaina AL-DA, damper, shock absorber, cabin damper, steering damper",
            intro="Index of Alaina <strong>dampers</strong> (the AL-DA line on this site): cabin dampers, steering dampers and shock absorbers/shockers listed in the catalogue. Rare passenger-car struts are indexed under AL-RS.",
            items=al_da,
            crumb="AL-DA",
            extra=[("AL-CD", "/al-cd/"), ("AL-RS", "/al-rs/")],
            line="Alaina AL-DA Dampers",
        ),
        dict(
            path="/gas-springs/",
            title="Gas Springs — Enquire | Alaina Shockers",
            h1="Gas springs",
            description="Alaina Shockers publishes cabin dampers, shock absorbers and rare struts in Catalogue No.04. Gas-spring part numbers are not listed on this site — enquire with your vehicle model.",
            keywords="gas spring, gas strut, Alaina gas spring, bonnet gas spring",
            intro="This website’s published catalogue lists <strong>cabin dampers, shock absorbers/shockers and rare struts</strong> with part numbers. <strong>No gas-spring SKUs, prices or fitments are in the repository</strong>, so none are shown here. If you need a gas spring, send the vehicle model (or a photo of the old unit) on WhatsApp and the trade desk can check.",
            items=[],
            crumb="Gas springs",
            extra=[("Rare struts", "/rare-struts/"), ("Dickey & bonnet struts", "/dickey-bonnet-struts/"), ("Enquire", "/#enquire")],
            line="Alaina Gas Springs (enquiry)",
        ),
        dict(
            path="/dickey-bonnet-struts/",
            title="Dickey & Bonnet Gas Struts — Enquire | Alaina Shockers",
            h1="Dickey & bonnet struts",
            description="Dickey shocker and bonnet gas strut enquiries for Alaina. Catalogue No.04 on this site lists cabin dampers, shock absorbers and rare struts — dickey/bonnet SKUs are not published here.",
            keywords="dickey shocker, bonnet gas strut, dickey strut, boot gas strut, Alaina",
            intro="Searches for <strong>dickey shocker</strong> and <strong>bonnet gas strut</strong> are common. This site does not publish dickey or bonnet strut part numbers, so this page does not invent any. Use the catalogue for cabin dampers and rare struts, or enquire with the car model.",
            items=[],
            crumb="Dickey & bonnet struts",
            extra=[("Gas springs", "/gas-springs/"), ("Rare struts", "/rare-struts/"), ("Enquire", "/#enquire")],
            line="Alaina Dickey & Bonnet Struts (enquiry)",
        ),
    ]

    for c in collections:
        html = render_collection(
            path=c["path"],
            title=c["title"],
            h1=c["h1"],
            description=c["description"],
            keywords=c["keywords"],
            intro=c["intro"],
            items=c["items"],
            crumb_name=c["crumb"],
            extra_links=c["extra"],
            product_line_name=c["line"],
        )
        dest = ROOT / c["path"].strip("/") / "index.html"
        write(dest, html)
        imgs = []
        for p in c["items"]:
            imgs.extend(images_for_product(p)[:1])
        pages.append((c["path"], TODAY, imgs, "0.9"))

    for g in vehicle_groups(products):
        path = f"/shockers/{g['slug']}/"
        title = f"Shocker for {g['name']} | Alaina Shockers"
        desc = (
            f"Alaina shockers and related dampers/struts catalogued for {g['name']}. "
            f"{len(g['items'])} part number(s) from Technical Catalogue No.04."
        )
        intro = (
            f"Parts Alaina lists for <strong>{esc(g['name'])}</strong>. "
            "Only applications written in the catalogue are shown — confirm OE number and the old unit before ordering."
        )
        html = render_collection(
            path=path,
            title=title,
            h1=f"Shocker for {g['name']}",
            description=desc,
            keywords=f"shocker for {g['name']}, {g['name']} shock absorber, {g['name']} cabin damper, Alaina {g['brand']}",
            intro=intro,
            items=g["items"],
            crumb_name=g["name"],
            extra_links=[("All shockers", "/shockers/"), ("Cabin dampers", "/cabin-dampers/"), ("Rare struts", "/rare-struts/")],
            product_line_name=f"Alaina parts for {g['name']}",
        )
        write(ROOT / "shockers" / g["slug"] / "index.html", html)
        imgs = []
        for p in g["items"]:
            imgs.extend(images_for_product(p)[:1])
        pages.append((path, TODAY, imgs, "0.75"))

    # Homepage entry
    home_imgs = []
    for p in products:
        if p["_has_photo"]:
            home_imgs.append((abs_url(p["_webp"] or p["img"]), p["_alt"]))
    pages.insert(0, ("/", TODAY, home_imgs, "1.0"))

    add_seo_css()
    patch_index(products, collections)
    write_htaccess()
    write_robots()

    # sitemaps (split)
    def chunk_urls(entries, n=40):
        for i in range(0, len(entries), n):
            yield entries[i : i + n]

    sm_files = []
    # pages sitemap without dumping all homepage images twice — homepage keeps product photos
    groups = {
        "sitemap-pages.xml": [e for e in pages if not e[0].startswith("/products/")],
        "sitemap-products.xml": [e for e in pages if e[0].startswith("/products/")],
    }
    for fname, entries in groups.items():
        body = "\n".join(sitemap_url(SITE + ("" if loc == "/" else loc), imgs, lm, pri) for loc, lm, imgs, pri in entries)
        write(ROOT / fname, wrap_urlset(body))
        sm_files.append(fname)

    index_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(
            f"  <sitemap>\n    <loc>{SITE}/{fn}</loc>\n    <lastmod>{TODAY}</lastmod>\n  </sitemap>\n"
            for fn in sm_files
        )
        + "</sitemapindex>\n"
    )
    write(ROOT / "sitemap.xml", index_xml)

    missing_photo = [p for p in products if not p["_has_photo"]]
    structured = len(products) + len(collections) + len(vehicle_groups(products)) + 1  # + homepage
    img_count = 0
    for loc, lm, imgs, pri in pages:
        img_count += len({u for u, _ in imgs})

    seo_md = f"""# Alaina Shockers SEO

Generated from Technical Catalogue No.04 data already in `index.html`. No part numbers, prices, fitments, specs, ratings or reviews were invented.

## What shipped

- Static HTML for every SKU under `/products/<part-slug>/` (crawlable `<img>`, not JS-only cards).
- Category / series / vehicle landings with unique title, meta description, keywords, canonical, hreflang `en-IN`, `og:*`, `twitter:*`, geo/locale `en_IN`, one H1, BreadcrumbList + ItemList + Product JSON-LD.
- Homepage Organization + WebSite (`SearchAction` on `/?q=`) + existing AutoPartsStore/FAQ JSON-LD.
- Canonical host is **`https://alainashockabsorbers.com`** (HTTPS, no `www`). `alainashockers.com` does not resolve — it was only a search keyword. `.htaccess` 301s `www` (and HTTP) to that apex URL without changing paths.
- Google image sitemap extension (`xmlns:image`) on sub-sitemaps. `robots.txt` allows pages and image files and points at the sitemap index.
- `.htaccess` serves `sitemap.xml` / `robots.txt` as real files with XML/text content-types, allows WebP, and does **not** SPA-fallback `google2874721c1e7298d6.html`.
- Keyword-rich WebP copies of product photos (`images/alaina-…webp`) while **original PNG paths stay**. Homepage range figures and product cards are real `<img>` tags with alt/title and width/height; below-fold uses `loading="lazy"`.
- Homepage visible layout matches the pre-SEO site. Crawlable SKU HTML lives on `/products/<slug>/` and category landings, using studio `p.img` photos only (not two-column catalogue-card plates or `catalogue-photos/` PDF renders).
- Favicon set at the site root (square Alaina `A` mark): `favicon.ico` (16/32/48), `favicon.svg`, 48/192/512 PNGs, `apple-touch-icon.png` (180), `site.webmanifest`. Linked in every page `<head>`. `robots.txt` allows them; `.htaccess` serves them as real files.

## Counts

| Item | Count |
|---|---|
| Catalogue SKUs | {len(products)} |
| SKUs with photo | {len(products) - len(missing_photo)} |
| SKUs without photo | {len(missing_photo)} |
| URL entries in sitemaps | {len(pages)} |
| Image entries (unique loc per page, summed) | {img_count} |
| Pages with JSON-LD Product/ItemList/Org | {structured} |

Sitemaps: `sitemap.xml` (index) → `sitemap-pages.xml`, `sitemap-products.xml`.

## Keyword → page map

| Query / intent | URL |
|---|---|
| Alaina shockers | `/` |
| shockers | `/shockers/` |
| shock absorber | `/shock-absorbers/` |
| cabin damper / cabin shocker | `/cabin-dampers/` |
| AL-CD cabin dampers | `/al-cd/` |
| rare strut / AL-RS | `/rare-struts/`, `/al-rs/` |
| AL-DA dampers | `/al-da/` |
| steering damper | `/steering-dampers/` |
| gas spring | `/gas-springs/` (enquiry only — **no SKUs in repo**) |
| dickey shocker / bonnet gas strut | `/dickey-bonnet-struts/` (enquiry only — **no SKUs in repo**) |
| shocker for Tata 4018, Bolero, Camry, … | `/shockers/<vehicle-slug>/` |
| SKU / part number | `/products/<slug>/` |

Vehicle landings exist only where the catalogue names that model (4018, Bolero, Camry, Lancer, Hector, D-Max, etc.).

## Series codes AL-CD / AL-RS / AL-DA

Those codes are **not** printed as SKUs in `PRODUCTS`. The pages `/al-cd/`, `/al-rs/`, `/al-da/` are indexes of real catalogue rows:

- **AL-CD** — every SKU with tag `Cabin` (cabin dampers).
- **AL-RS** — every SKU with `cat: RS` (rare struts).
- **AL-DA** — cabin + steering + shock absorber/stabilizer SKUs (dampers). Rare struts stay on AL-RS.

JSON-LD Product on those URLs has **no sku/mpn** (that would invent a series part number). Individual SKU pages use the real `partno` as sku/mpn. **No Offer** blocks — the repo has no prices.

## Products with no photo

Shoot these so they can enter Google Images:

"""
    for p in missing_photo:
        seo_md += f"- `{p['partno']}` — {p['brand']} {p['_name']} ({p['_app']})\n"
    if not missing_photo:
        seo_md += "- (none)\n"
    seo_md += """
## Canonical host

Live site: **`https://alainashockabsorbers.com`** (HTTPS, apex, no `www`). HTTP already 301s to HTTPS on Hostinger; `.htaccess` also 301s `www.alainashockabsorbers.com` to the apex and forces HTTPS, keeping path and query (PNG and catalogue URLs intact).

`alainashockers.com` does not exist (NXDOMAIN). “Alaina shocker(s)” is a **search keyword** only — used in titles, intro copy, `Organization.alternateName` and image alts, not as a hostname.

## Regenerating

```bash
python3 scripts/build_seo.py
```

Requires Pillow (`pip install pillow`) for WebP. Does not modify `google2874721c1e7298d6.html`.
"""
    write(ROOT / "SEO.md", seo_md)

    # write counts sidecar for validation
    write(
        ROOT / "scripts" / "seo-counts.json",
        json.dumps(
            {
                "pages": len(pages),
                "images_in_sitemaps": img_count,
                "products": len(products),
                "missing_photos": [p["partno"] for p in missing_photo],
                "structured_pages": structured,
            },
            indent=2,
        )
        + "\n",
    )
    print("pages", len(pages), "images", img_count, "missing", [p["partno"] for p in missing_photo])


if __name__ == "__main__":
    main()
