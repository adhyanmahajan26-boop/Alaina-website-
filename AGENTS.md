# Alaina Shockers — Grok / Cloud Agent handover

This repository is the **Alaina Shockers** marketing site
([alainashockabsorbers.com](https://alainashockabsorbers.com)).

You are a Cursor cloud agent. A Grok bot will prompt you to edit this website.
The **chief** (site owner) approves or rejects changes from **screenshot + video
proof only** — not from a text description.

## Stack

- Plain HTML + CSS + JS. No bundler, no framework, no `pnpm`/`npm` build.
- Main files: `index.html`, `style.css`, `script.js`
- Product photos: `images/` (and `catalogue-photos/` source stills)
- Hero / proving videos: `hero-video.mp4`, `testing-video.mp4`
- Local preview:

```bash
python3 -m http.server 5174
# open http://127.0.0.1:5174
```

## Site map (one page)

| Section | Anchor | What it is |
|---|---|---|
| Hero | `#hero` / `#top` | Full-bleed video, headline, four brand jumps |
| Range | `#range` | Three product lines |
| Catalogue | `#catalogue` | 74 SKU card grid, search, brand chips, lightbox |
| Testing | `#proving` | Factory test video + four claims |
| About | `#about` | 1978 house story |
| Enquire | `#enquire` | WhatsApp form + trade desk |

Do **not** deploy to Hostinger or push live until the chief explicitly approves
the visual proof for that change.

## Chief approval protocol (mandatory)

For **every** user-visible change:

1. Note the **before** state (screenshot of the affected section if it already exists).
2. Make the edit.
3. Preview at `http://127.0.0.1:5174` and exercise the change like a real visitor.
4. Capture **after** screenshots of every affected section (desktop 1440×900; also
   mobile 390×844 if layout or nav changed).
5. Record a **video** of the changed flow end-to-end (`RecordScreen` + `computerUse`).
   Discard failed takes. Only keep a successful walkthrough.
6. Copy screenshots into `/opt/cursor/artifacts` with snake_case names, e.g.
   `screenshot_hero_after.png`, `screenshot_catalogue_filter_after.png`.
7. Run `videoReview` on the recording before claiming it is correct.
8. Put the screenshots and video in the PR body **and** the final message using
   HTML `<img>` / `<video>` tags. Ask the chief to approve from that proof.

**Never ask for approval from prose alone.**

## Editing rules

- Keep the dark technical-catalogue look (paper on charcoal, orange accent `#FF4D00` only if already in use — match existing tokens in `style.css`).
- Do not invent SKUs, OE numbers, or product photos.
- Do not hardcode Hostinger / FTP / WhatsApp credentials in files.
- Prefer small, reviewable diffs. One visual change-set per PR when possible.
- After code changes: commit, push, open/update the PR, then attach proof.

## Ready for Grok prompts

When a prompt arrives (copy, layout, catalogue, colour, nav, form, etc.):

1. Restate the requested change in one sentence.
2. Implement it.
3. Ship screenshot + video proof.
4. Stop and wait for chief approval before going live.
