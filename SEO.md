# Alaina Shockers SEO

Generated from Technical Catalogue No.04 data already in `index.html`. No part numbers, prices, fitments, specs, ratings or reviews were invented.

## What shipped

- Static HTML for every SKU under `/products/<part-slug>/` (crawlable `<img>`, not JS-only cards).
- Category / series / vehicle landings with unique title, meta description, keywords, canonical, hreflang `en-IN`, `og:*`, `twitter:*`, geo/locale `en_IN`, one H1, BreadcrumbList + ItemList + Product JSON-LD.
- Homepage Organization + WebSite (`SearchAction` on `/?q=`) + existing AutoPartsStore/FAQ JSON-LD. Domain corrected to `https://alainashockers.com`.
- Google image sitemap extension (`xmlns:image`) on sub-sitemaps. `robots.txt` allows pages and image files and points at the sitemap index.
- `.htaccess` serves `sitemap.xml` / `robots.txt` as real files with XML/text content-types, allows WebP, and does **not** SPA-fallback `google2874721c1e7298d6.html`.
- Keyword-rich WebP copies of product photos (`images/alaina-…webp`) while **original PNG paths stay**. Homepage range figures and product cards are real `<img>` tags with alt/title and width/height; below-fold uses `loading="lazy"`.
- Homepage: crawlable product cards + type index.
- Favicon set at the site root (square Alaina `A` mark): `favicon.ico` (16/32/48), `favicon.svg`, 48/192/512 PNGs, `apple-touch-icon.png` (180), `site.webmanifest`. Linked in every page `<head>`. `robots.txt` allows them; `.htaccess` serves them as real files.

## Counts

| Item | Count |
|---|---|
| Catalogue SKUs | 74 |
| SKUs with photo | 73 |
| SKUs without photo | 1 |
| URL entries in sitemaps | 119 |
| Image entries (unique loc per page, summed) | 730 |
| Pages with JSON-LD Product/ItemList/Org | 119 |

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

- `AL-LE-HD-0200` — Leyland Marcopolo / Bharat Benz Front (U Truck / G91 / Stalian / Cargo / Marcopolo)

## Regenerating

```bash
python3 scripts/build_seo.py
```

Requires Pillow (`pip install pillow`) for WebP. Does not modify `google2874721c1e7298d6.html`.
