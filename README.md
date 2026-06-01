# Alaina Shockers

Marketing website for **Alaina Shockers** — rare struts, dampers, and heavy-duty
cabin dampers engineered for India's commercial trucks (Eicher, Leyland, Tata) and
passenger vehicles.

A single-file, dependency-free site: premium light (white/orange) automotive design
with a scroll-scrubbed "Making of a Shocker" animation — a fully vector coilover that
**assembles part-by-part, fits into a suspension corner, and cycles on the road** as
you scroll.

## Features

- Clean white UI with an `#FF4D00` orange brand accent
- Cinematic dark **assembly animation** (SVG, scroll-scrubbed): build → fitment into a wheel → driving
- Animated hero, stat counters, marquee ticker, scroll progress bar, sticky nav
- Reveal-on-scroll sections, hover-lift product cards
- Filterable cabin-damper catalogue table
- Contact form + WhatsApp enquiry
- Fully responsive; no build step, no frameworks

## Tech

- Plain **HTML + CSS + JavaScript** in a single `index.html`
- Google Fonts: Archivo, Inter, Space Mono
- Images in `images/`

## Run locally

```bash
python3 -m http.server 5174
# then open http://localhost:5174
```

## Structure

```
.
├── index.html        # entire site (markup, styles, scripts)
├── images/           # hero, product, and reference images
└── README.md
```

## License

© Alaina Shockers. Distributed by Mahajan Motors India. All rights reserved.
