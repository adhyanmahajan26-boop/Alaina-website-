# SEO comparison: this branch against `main`

Every HTML page on `main` (124) was compared with the same page on this branch.

| Checked on every page | Result |
| --- | --- |
| `<title>`, meta description, keywords, robots | identical |
| canonical and hreflang | identical |
| Open Graph and Twitter tags | identical |
| `<h1>` | identical |
| JSON-LD blocks (parsed and compared as data) | identical |
| Internal links | none removed; added: `alaina-x-superlift/` and the dock's `#find` link |
| `<h2>` | identical, except two new headings on the homepage: "Inside a cabin damper" and "Alaina × Superlift" |
| `<img src>` of every product photo | unchanged (original PNGs); the matched cut-outs are `<source>` alternatives |

Body copy differs only by the new sections and a "Details" label on each product card.
`python3 scripts/check_seo.py` passes on all 124 pages, and `scripts/build_seo.py` is idempotent.
The new `/alaina-x-superlift/` page is `noindex, follow` and is not in the sitemap.
