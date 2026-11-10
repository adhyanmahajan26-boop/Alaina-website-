# SEO comparison: redesign v2 against main

Every HTML page on `main` (124 files) compared with the rebuilt page on this branch.

| Checked on every page | Result |
| --- | --- |
| `<title>` | identical on 124 of 124 |
| meta description, keywords, robots | identical on 124 of 124 |
| canonical and hreflang | identical on 124 of 124 |
| Open Graph and Twitter tags | identical on 124 of 124 |
| `<h1>` (count and text) | identical on 124 of 124 |
| JSON-LD (parsed and compared) | identical on 124 of 124 |
| `<h2>` list | identical on 123. Homepage gains two: "Inside a cabin damper" and "Alaina × Superlift" |
| Internal links | none removed anywhere. One link to `/alaina-x-superlift/` added per page |
| Sitemap URL sets | identical (`sitemap.xml` 2, `sitemap-pages.xml` 47, `sitemap-products.xml` 74). Only `lastmod` dates moved |
| `robots.txt`, `llms.txt` | unchanged |
| `.htaccess` | three added lines: woff2 MIME type and cache lifetimes. Redirects and CSP unchanged |

Visible text inside `<main>` changed only on product cards: the "View → / WA" buttons became
"Enquire" plus an arrow link, and each card now shows its position tag (Cabin, Front, Rear …).

New page `/alaina-x-superlift/` is `noindex,follow` and is not in the sitemap.

`python3 scripts/check_seo.py`: passed, 124 pages.
