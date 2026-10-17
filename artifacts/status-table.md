# Status table — unknown URLs become real 404s

**Before** = live `https://alainashockabsorbers.com` (SPA fallback still rewriting missing paths to `index.html`).
**After** = local Apache 2.4.58 (`AllowOverride All`, DocumentRoot = this repo, `http://127.0.0.1:8080`). Trailing-slash `Location` hosts differ because DirectorySlash uses the request host; path and 301 code are unchanged. `www` / HTTPS / gas-springs rules still emit the production `https://alainashockabsorbers.com/...` Location.

## Real pages (must stay 200)

All **120** audited real routes returned **200** on the live site before the change, and **200** on local Apache after (including `/dickey-bonnet-struts/`, both child sitemaps, and every product / category / vehicle landing).

| URL | Before (live) | After (local Apache) | Body |
|---|---|---|---|
| `/` | 200 | 200 | Homepage title *Truck Cabin Damper Manufacturer in India \| Alaina Shockers* |
| `/cabin-dampers/` | 200 | 200 | Category title *Truck Cabin Damper Manufacturer India – Tata, Leyland, Eicher \| Alaina* |
| `/products/al-ta-hd-0241-a/` | 200 | 200 | Product title *4018 Hywa / Prima Cabin (AL-TA-HD-0241(A)) \| Alaina* |
| `/shockers/` | 200 | 200 | Shockers index |
| `/dickey-bonnet-struts/` | 200 | 200 | Enquiry landing (prerendered, not in sitemap) |
| `/sitemap.xml` | 200 | 200 | Sitemap index |
| `/robots.txt` | 200 | 200 | robots.txt |

## Fake URLs (must become 404 + 404.html)

| URL | Before (live) | After (local Apache) | After body |
|---|---|---|---|
| `/this-does-not-exist` | **200** homepage | **404** | `Page not found \| Alaina Shockers` (`404.html`) |
| `/this-does-not-exist/` | **200** homepage | **404** | `404.html` |
| `/cabin-dampers/fake-xyz` | **200** homepage | **404** | `404.html` |
| `/random.html` | **200** homepage | **404** | `404.html` |
| `/products/no-such-sku/` | (not probed live; same SPA fallback) | **404** | `404.html` |
| `/shockers/not-a-vehicle/` | (not probed live; same SPA fallback) | **404** | `404.html` |
| `/404.html` | **200** homepage (file did not exist) | **200** | Direct request for the ErrorDocument file |

## Redirects (must stay 301 with the same Location)

| Request | Before code | Before Location | After code | After Location | Unchanged? |
|---|---|---|---|---|---|
| `/cabin-dampers` (no slash) | 301 | `https://alainashockabsorbers.com/cabin-dampers/` | 301 | `http://127.0.0.1:8080/cabin-dampers/` (DirectorySlash; path `/cabin-dampers/`) | Yes — 301 + trailing slash |
| `/products/al-ta-hd-0241-a` | (DirectorySlash; same class as `/cabin-dampers`) | — | 301 | `http://127.0.0.1:8080/products/al-ta-hd-0241-a/` | Yes |
| `https://www.alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | Yes |
| `https://www.alainashockabsorbers.com/cabin-dampers/` | 301 | `https://alainashockabsorbers.com/cabin-dampers/` | 301 | `https://alainashockabsorbers.com/cabin-dampers/` | Yes |
| `http://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | Yes |
| `/gas-springs` | 301 | `https://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | Yes |
| `/gas-springs/` | 301 | `https://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | Yes |
| `/gas-springs/foo` | 301 | `https://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | Yes |
| `/gassprings` | 301 | `https://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | Yes |
| `/gassprings/` | 301 | `https://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | Yes |
| `/gassprings/inquired/alaina-shockers` | 301 | `https://alainashockabsorbers.com/` | 301 | `https://alainashockabsorbers.com/` | Yes |

After `www` / HTTP-apex tests used `Host:` on local Apache so the existing rewrite rules fire; Location is still the production apex URL.

## Evidence

Screenshots (1280 and 390) of homepage, `/cabin-dampers/`, `/products/al-ta-hd-0241-a/`, and the 404 URL, before (live) and after (local), plus this file and `route-audit.md`, are in `artifacts/evidence.zip`.
