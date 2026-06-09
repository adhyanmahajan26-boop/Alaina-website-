/* ══════════════════════════════════════════
   HERO IGNITION + GENERIC COUNT-UP
══════════════════════════════════════════ */
(function() {
  const hero = document.getElementById('hero');
  if (hero) requestAnimationFrame(() => setTimeout(() => hero.classList.add('lit'), 120));
})();

function animateCount(el) {
  const target = +el.dataset.count;
  const suffix = el.dataset.suffix || '';
  const dur = 1400;
  const start = performance.now();
  function step(now) {
    const t = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = Math.round(eased * target) + suffix;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
(function() {
  const items = document.querySelectorAll('.hero-readout b[data-count]');
  if (!items.length) return;
  setTimeout(() => items.forEach(animateCount), 900);
})();

/* ══════════════════════════════════════════
   SCROLL REVEAL CHOREOGRAPHY
══════════════════════════════════════════ */
(function() {
  const els = document.querySelectorAll('[data-reveal]');
  if (!els.length) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
  els.forEach(el => io.observe(el));
})();



/* ── SCROLL PROGRESS ── */
const bar = document.getElementById('bar');
addEventListener('scroll', () => {
  bar.style.width = (scrollY / (document.body.scrollHeight - innerHeight) * 100) + '%';
}, { passive: true });

/* ── NAV STICK ── */
const nav = document.getElementById('nav');
addEventListener('scroll', () => nav.classList.toggle('stuck', scrollY > 60), { passive: true });

/* ── SMOOTH HASH SCROLL ── */
document.addEventListener('click', function(e) {
  const a = e.target.closest('a[href^="#"]');
  if (!a) return;
  const id = a.getAttribute('href').slice(1);
  if (!id) return;
  const el = document.getElementById(id);
  if (el) { e.preventDefault(); el.scrollIntoView({ behavior: 'smooth' }); }
});

/* ── MOBILE NAV ── */
(function() {
  const burger = document.getElementById('navBurger');
  const mob = document.getElementById('mobNav');
  const close = document.getElementById('mobClose');
  const open = () => { mob.classList.add('open'); document.body.classList.add('mob-open'); document.body.style.overflow = 'hidden'; };
  const shut = () => { mob.classList.remove('open'); document.body.classList.remove('mob-open'); document.body.style.overflow = ''; };
  if (burger) burger.addEventListener('click', open);
  if (close) close.addEventListener('click', shut);
  mob && mob.querySelectorAll('a').forEach(a => a.addEventListener('click', shut));
})();

/* ── STAT COUNTERS ── */
function countUp(el, target) {
  let n = 0, step = Math.max(1, Math.ceil(target / 45));
  const iv = setInterval(() => { n = Math.min(n + step, target); el.textContent = n; if (n >= target) clearInterval(iv); }, 26);
}
const statObs = new IntersectionObserver((es) => es.forEach(e => {
  if (e.isIntersecting) {
    e.target.querySelectorAll('.astat-n[data-count]').forEach(el => countUp(el, +el.dataset.count));
    statObs.unobserve(e.target);
  }
}), { threshold: 0.4 });
const aboutStats = document.querySelector('.about-stats');
if (aboutStats) statObs.observe(aboutStats);

/* ── CATALOGUE FILTER (sidebar + section dividers) ── */
function ft(m, btn) {
  /* update sidebar buttons */
  document.querySelectorAll('.sbar-btn').forEach(b => b.classList.remove('on'));
  if (btn) btn.classList.add('on');

  /* filter cards */
  document.querySelectorAll('.cat-card').forEach(r => {
    const show = m === 'all' || r.dataset.m === m || r.dataset.cat === m;
    r.style.display = show ? '' : 'none';
  });

  /* show/hide section dividers */
  document.querySelectorAll('.cat-section-divider').forEach(div => {
    let next = div.nextElementSibling;
    let anyVisible = false;
    while (next && !next.classList.contains('cat-section-divider')) {
      if (next.style.display !== 'none') anyVisible = true;
      next = next.nextElementSibling;
    }
    div.style.display = anyVisible ? '' : 'none';
  });

  /* re-run 3D tilt on visible cards */
  setTimeout(init3DTilt, 60);
}

/* ── SCROLL TO BRAND (from showcase panels) ── */
function scrollToCat(brand) {
  const catalog = document.getElementById('catalog');
  if (catalog) {
    catalog.scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => {
      const btn = document.querySelector(`.sbar-btn[data-val="${brand}"]`);
      if (btn) ft(brand, btn);
    }, 600);
  }
}

/* ── 3D TILT ── */
function init3DTilt() {
  document.querySelectorAll('.cat-card').forEach(card => {
    if (card.querySelector('.cc-glare')) return;
    const glare = document.createElement('div');
    glare.className = 'cc-glare';
    card.appendChild(glare);

    const isPhoto = !!card.querySelector('.has-photo');
    const maxRot = isPhoto ? 14 : 9;
    let tiltFrame = null;

    // will-change only while hovering — avoids 60 simultaneous GPU layers
    card.addEventListener('mouseenter', () => { card.style.willChange = 'transform'; }, { passive: true });

    function onMove(e) {
      // RAF-throttle: only one calc per frame regardless of mousemove rate
      if (tiltFrame) return;
      const cx = e.clientX, cy = e.clientY;
      tiltFrame = requestAnimationFrame(() => {
        tiltFrame = null;
        const r = card.getBoundingClientRect();
        const dx = (cx - (r.left + r.width / 2)) / (r.width / 2);
        const dy = (cy - (r.top + r.height / 2)) / (r.height / 2);
        const rotX = (-dy * maxRot).toFixed(2);
        const rotY = (dx * maxRot).toFixed(2);
        const dist = Math.sqrt(dx * dx + dy * dy).toFixed(2);
        card.style.transition = 'transform .08s ease-out,box-shadow .08s';
        card.style.transform = `perspective(700px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(1.04)`;
        card.style.boxShadow =
          `${(-dx * 20).toFixed(0)}px ${(-dy * 14).toFixed(0)}px 40px rgba(0,0,0,0.5),` +
          `0 0 0 1px rgba(255,77,0,${(0.10 + dist * 0.12).toFixed(2)})`;
        const px = ((dx + 1) * 50).toFixed(1);
        const py = ((dy + 1) * 50).toFixed(1);
        glare.style.opacity = '1';
        glare.style.background = `radial-gradient(circle at ${px}% ${py}%,rgba(255,255,255,${(0.07 + dist * 0.09).toFixed(2)}) 0%,rgba(255,255,255,.02) 45%,transparent 70%)`;
        if (isPhoto) {
          const img = card.querySelector('.cc-img');
          if (img) img.style.filter = `drop-shadow(${(-dx * 5).toFixed(0)}px ${(-dy * 5).toFixed(0)}px 16px rgba(255,120,0,0.25))`;
        }
      });
    }

    function onLeave() {
      if (tiltFrame) { cancelAnimationFrame(tiltFrame); tiltFrame = null; }
      card.style.willChange = '';
      card.style.transition = 'transform .55s cubic-bezier(.22,1,.36,1),box-shadow .55s';
      card.style.transform = '';
      card.style.boxShadow = '';
      glare.style.opacity = '0';
      const img = card.querySelector('.cc-img');
      if (img) img.style.filter = '';
    }

    card.addEventListener('mousemove', onMove, { passive: true });
    card.addEventListener('mouseleave', onLeave);
    card.addEventListener('touchstart', onLeave, { passive: true });
  });
}

document.addEventListener('DOMContentLoaded', init3DTilt);
setTimeout(init3DTilt, 500);

/* ── LIGHTBOX ── */
function openLightbox(src, caption) {
  const lb = document.getElementById('lightbox');
  document.getElementById('lbImg').src = src;
  document.getElementById('lbCaption').textContent = caption || '';
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeLightbox() {
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

/* ── CONTACT FORM ── */
function sendForm(e) {
  e.preventDefault();
  const b = document.getElementById('sbtn');
  b.textContent = '✓ Sent — we\'ll call you shortly';
  b.style.background = '#25D366';
  setTimeout(() => { b.textContent = 'Send Enquiry →'; b.style.background = ''; e.target.reset(); }, 3500);
}

/* ── ENQUIRE PRE-FILL ── */
function enquireCard(btn) {
  const card = btn.closest('.cat-card');
  const partno = card.querySelector('.cc-partno')?.textContent.trim() || '';
  const name   = card.querySelector('.cc-name')?.textContent.trim()   || '';
  const catalog = document.getElementById('catalog');
  if (catalog) catalog.scrollIntoView({ behavior: 'smooth' });
  const contact = document.getElementById('contact');
  if (contact) contact.scrollIntoView({ behavior: 'smooth' });
  setTimeout(() => {
    const msg = document.getElementById('msgField');
    if (msg) {
      msg.value = `Part No: ${partno} — ${name}\n\nPlease share availability and pricing.`;
      msg.focus();
      msg.dispatchEvent(new Event('input'));
    }
  }, 600);
}

/* ── WHATSAPP CARD QUOTE ── */
function waCard(btn) {
  const card = btn.closest('.cat-card');
  const partno = card.querySelector('.cc-partno')?.textContent.trim() || '';
  const name   = card.querySelector('.cc-name')?.textContent.trim()   || '';
  const text = encodeURIComponent(`Hi, I'm interested in *${partno}* — ${name}. Please share availability and pricing.`);
  window.open(`https://wa.me/917982555636?text=${text}`, '_blank');
}

/* ── CATALOGUE SEARCH ── */
function filterSearch(val) {
  const q = val.trim().toLowerCase();
  const clearBtn = document.getElementById('searchClear');
  if (clearBtn) clearBtn.style.display = q ? '' : 'none';
  document.querySelectorAll('.cat-card').forEach(card => {
    const text = (card.querySelector('.cc-partno')?.textContent || '') + ' ' +
                 (card.querySelector('.cc-name')?.textContent   || '') + ' ' +
                 (card.querySelector('.cc-app')?.textContent    || '') + ' ' +
                 (card.querySelector('.cc-brand')?.textContent  || '');
    card.style.display = (!q || text.toLowerCase().includes(q)) ? '' : 'none';
  });
  document.querySelectorAll('.cat-section-divider').forEach(div => {
    let next = div.nextElementSibling, anyVisible = false;
    while (next && !next.classList.contains('cat-section-divider')) {
      if (next.style.display !== 'none') anyVisible = true;
      next = next.nextElementSibling;
    }
    div.style.display = anyVisible ? '' : 'none';
  });
}

function clearSearch() {
  const inp = document.getElementById('catSearch');
  if (inp) { inp.value = ''; filterSearch(''); inp.focus(); }
}

/* ── NAV ACTIVE ON SCROLL ── */
const sections = ['hero','catalog','about','contact'];
const navLinks = document.querySelectorAll('.navlinks a');
const sectionObs = new IntersectionObserver((es) => {
  es.forEach(e => {
    if (e.isIntersecting) {
      navLinks.forEach(a => {
        const h = (a.getAttribute('href') || '').replace('#', '');
        a.classList.toggle('nav-active', h === e.target.id);
      });
    }
  });
}, { threshold: 0.3, rootMargin: '-70px 0px 0px 0px' });

sections.forEach(id => {
  const el = document.getElementById(id);
  if (el) sectionObs.observe(el);
});

/* ══════════════════════════════════════════
   1. SCROLL-DRIVEN VIDEO SCRUB
══════════════════════════════════════════ */
(function() {
  const vid = document.getElementById('heroVid');
  const hero = document.getElementById('hero');
  if (!vid || !hero) return;

  let scrubActive = false;
  let rafId = null;
  let lastScroll = 0;

  function setScrub(scroll) {
    const heroH = hero.offsetHeight;
    const ratio = Math.min(Math.max(scroll / heroH, 0), 1);
    if (vid.duration && vid.readyState >= 2) {
      vid.currentTime = ratio * vid.duration;
    }
    // Darken overlay slightly while scrolling through hero
    if (ratio > 0.05) {
      hero.classList.add('scrubbing');
    } else {
      hero.classList.remove('scrubbing');
    }
  }

  vid.addEventListener('loadedmetadata', () => {
    // Once metadata loads, enable scrub on scroll
    window.addEventListener('scroll', () => {
      const s = window.scrollY;
      if (s > hero.offsetHeight) {
        // Past hero — resume normal playback
        if (!vid.playing) vid.play().catch(()=>{});
        scrubActive = false;
        hero.classList.remove('scrubbing');
        return;
      }
      // In hero — scrub
      scrubActive = true;
      lastScroll = s;
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => setScrub(lastScroll));
    }, { passive: true });
  });
})();


/* ══════════════════════════════════════════
   6. STAGGERED CARD ENTRANCE
══════════════════════════════════════════ */
(function() {
  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter(e => e.isIntersecting);
    visible.forEach((entry, i) => {
      const card = entry.target;
      setTimeout(() => {
        card.classList.add('card-visible');
      }, i * 55);
      observer.unobserve(card);
    });
  }, { threshold: 0.05, rootMargin: '0px 0px -20px 0px' });

  function observeCards() {
    document.querySelectorAll('.cat-card').forEach(card => {
      if (!card.classList.contains('card-visible')) {
        card.classList.add('will-animate'); // opt-in to hidden state
        observer.observe(card);
      }
    });
    // Safety net: any card still hidden after 1.5s gets revealed
    setTimeout(() => {
      document.querySelectorAll('.cat-card.will-animate:not(.card-visible)').forEach(c => {
        c.classList.add('card-visible');
      });
    }, 1500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', observeCards);
  } else {
    setTimeout(observeCards, 50); // slight delay so layout is stable
  }
})();

/* ══════════════════════════════════════════
   DNA WAVEFORM — unique signal per part no.
══════════════════════════════════════════ */
(function() {
  const NS = 'http://www.w3.org/2000/svg';

  // FNV-1a 32-bit hash — deterministic, fast
  function hash(str) {
    let h = 2166136261 >>> 0;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h;
  }

  // Xorshift RNG seeded per card
  function makeRng(seed) {
    let s = seed >>> 0 || 1;
    return function() {
      s ^= s << 13; s ^= s >> 17; s ^= s << 5;
      return (s >>> 0) / 0xffffffff;
    };
  }

  // Build a smooth organic waveform SVG path
  function buildPath(rng, W, H) {
    const N   = 18;          // control points
    const mid = H * 0.52;
    const amp = H * 0.40;

    // Generate raw y-values with some spikes for character
    const pts = [];
    for (let i = 0; i <= N; i++) {
      const x = (i / N) * W;
      // Occasional sharp spike for EKG-like personality
      const spike = rng() > 0.82 ? (rng() > 0.5 ? 1 : -1) * amp * 0.55 : 0;
      const y = mid + (rng() * 2 - 1) * amp + spike;
      pts.push([x, Math.max(2, Math.min(H - 2, y))]);
    }

    // Smooth cubic bezier through points
    let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
    for (let i = 1; i < pts.length; i++) {
      const cp = (pts[i-1][0] + pts[i][0]) / 2;
      d += ` C${cp.toFixed(1)},${pts[i-1][1].toFixed(1)}` +
           ` ${cp.toFixed(1)},${pts[i][1].toFixed(1)}` +
           ` ${pts[i][0].toFixed(1)},${pts[i][1].toFixed(1)}`;
    }
    return d;
  }

  function injectWaveforms() {
    document.querySelectorAll('.cat-card').forEach(card => {
      if (card.querySelector('.dna-wave')) return; // already done
      const partno = card.querySelector('.cc-partno')?.textContent.trim();
      if (!partno) return;

      const h   = hash(partno);
      const rng = makeRng(h);

      const svg = document.createElementNS(NS, 'svg');
      svg.setAttribute('class', 'dna-wave');
      svg.setAttribute('viewBox', '0 0 220 52');
      svg.setAttribute('preserveAspectRatio', 'none');

      // Waveform path
      const path = document.createElementNS(NS, 'path');
      path.setAttribute('class', 'dna-path');
      path.setAttribute('d', buildPath(rng, 220, 52));
      svg.appendChild(path);

      // Hex fingerprint label — bottom-right corner
      const txt = document.createElementNS(NS, 'text');
      txt.setAttribute('class', 'dna-id');
      txt.setAttribute('x', '217');
      txt.setAttribute('y', '50');
      txt.setAttribute('text-anchor', 'end');
      txt.textContent = '#' + h.toString(16).slice(0, 4).toUpperCase();
      svg.appendChild(txt);

      const wrap = card.querySelector('.cat-card-img-wrap');
      if (wrap) wrap.appendChild(svg);
    });
  }

  // Initial inject
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectWaveforms);
  } else {
    injectWaveforms();
  }

  // Re-inject after filter (new cards may become visible)
  const _ft = window.ft;
  if (_ft) window.ft = function(m, btn) { _ft(m, btn); setTimeout(injectWaveforms, 80); };
})();
