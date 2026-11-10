"""Shared page furniture: icon sprite, logo mark and the small inline boot script.

The homepage (index.html) carries literal copies of SPRITE and MARK; every other
page gets them from scripts/build_seo.py. Change them here and in index.html together.
"""

ASSET_VERSION = "20"

# Runs before first paint: applies the saved theme and flags that JS is available.
# If site.js never arrives, the flag is dropped so scroll-reveal content stays visible.
HEAD_BOOT = (
    "<script>(function(){var d=document.documentElement;d.classList.add('js');"
    "try{var t=localStorage.getItem('alaina-theme');if(t==='dark'||t==='light')d.setAttribute('data-theme',t)}catch(e){}"
    "setTimeout(function(){if(!window.__alainaReady)d.classList.remove('js')},3000)})();</script>"
)

WA_PATHS = (
    '<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164'
    "-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13"
    "-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207"
    "-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462"
    " 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085"
    ' 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>'
    '<path d="M11.999 2C6.477 2 2 6.477 2 12c0 1.821.487 3.53 1.338 5.001L2.044 22l5.112-1.338A9.955 9.955 0 0011.999 22'
    "C17.522 22 22 17.523 22 12S17.522 2 11.999 2zm0 18c-1.658 0-3.197-.489-4.487-1.33l-.322-.19-3.038.795.812-2.966-.209-.333"
    'A7.944 7.944 0 014 12c0-4.411 3.589-8 8-8s8 3.589 8 8-3.589 8-8 8z"/>'
)

SPRITE = (
    '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>'
    f'<symbol id="i-wa" viewBox="0 0 24 24">{WA_PATHS}</symbol>'
    '<symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.6-3.6"/></symbol>'
    '<symbol id="i-go" viewBox="0 0 24 24"><path d="M7 17 17 7M8 7h9v9"/></symbol>'
    '<symbol id="i-next" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>'
    '<symbol id="i-grid" viewBox="0 0 24 24"><rect x="4" y="4" width="7" height="7" rx="1.6"/>'
    '<rect x="13" y="4" width="7" height="7" rx="1.6"/><rect x="4" y="13" width="7" height="7" rx="1.6"/>'
    '<rect x="13" y="13" width="7" height="7" rx="1.6"/></symbol>'
    '<symbol id="i-home" viewBox="0 0 24 24"><path d="M4 11.5 12 5l8 6.5V20h-5.2v-5.2H9.2V20H4z"/></symbol>'
    '<symbol id="i-gas" viewBox="0 0 24 24"><circle cx="4.5" cy="19.5" r="1.7"/><circle cx="19.5" cy="4.5" r="1.7"/>'
    '<path d="m5.8 18.2 3-3M15.2 8.8l3-3"/><path d="m8.3 15.7 6.4-6.4" stroke-width="4.6"/></symbol>'
    '<symbol id="i-spin" viewBox="0 0 24 24"><path d="M3 12h18M7 8l-4 4 4 4M17 8l4 4-4 4"/></symbol>'
    "</defs></svg>"
)

# Logo mark: an "A" whose crossbar is a damper rod running out of the letter.
MARK_INNER = (
    '<rect width="48" height="48" rx="11" fill="#FF4A1A"/>'
    '<path fill="#fff" d="M10 37.5 20.4 10.5h7.2L38 37.5h-6.9L24 17.6 16.9 37.5z"/>'
    '<path fill="#101114" d="M17.2 27.2h23.3v4.6H15.4z"/>'
)
MARK = f'<svg class="brand-mark" viewBox="0 0 48 48" aria-hidden="true">{MARK_INNER}</svg>'

# Small animated gas spring used on the Superlift teaser and partner page.
GASSPRING = (
    '<svg viewBox="0 0 440 150" role="img" aria-label="Gas spring"><defs>'
    '<linearGradient id="gsb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3a3c42"/>'
    '<stop offset=".35" stop-color="#17181b"/><stop offset="1" stop-color="#050506"/></linearGradient>'
    '<linearGradient id="gsr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/>'
    '<stop offset=".5" stop-color="#b9bcc4"/><stop offset="1" stop-color="#5d6068"/></linearGradient></defs>'
    '<g transform="rotate(-14 220 75)"><g class="gs-rod">'
    '<rect x="250" y="69.5" width="152" height="11" rx="5.5" fill="url(#gsr)"/>'
    '<circle cx="408" cy="75" r="13" fill="#17181b" stroke="rgba(255,255,255,.45)"/>'
    '<circle cx="408" cy="75" r="4.5" fill="#FF4A1A"/></g>'
    '<rect x="52" y="60" width="232" height="30" rx="8" fill="url(#gsb)" stroke="rgba(255,255,255,.28)"/>'
    '<rect x="264" y="60" width="20" height="30" rx="4" fill="#2c2e33"/>'
    '<rect x="96" y="60.5" width="5" height="29" fill="#FF4A1A"/>'
    '<circle cx="36" cy="75" r="13" fill="#17181b" stroke="rgba(255,255,255,.45)"/>'
    '<circle cx="36" cy="75" r="4.5" fill="#FF4A1A"/></g></svg>'
)
