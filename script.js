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
    const maxRot = isPhoto ? 16 : 10;

    function onMove(e) {
      const r = card.getBoundingClientRect();
      const dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
      const dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
      const rotX = (-dy * maxRot).toFixed(2);
      const rotY = (dx * maxRot).toFixed(2);
      const dist = Math.sqrt(dx * dx + dy * dy).toFixed(2);
      card.style.transition = 'transform .08s ease-out,box-shadow .08s';
      card.style.transform = `perspective(700px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(1.045)`;
      card.style.boxShadow =
        `${(-dx * 22).toFixed(0)}px ${(-dy * 16).toFixed(0)}px 44px rgba(0,0,0,0.55),` +
        `0 0 0 1px rgba(255,77,0,${(0.10 + dist * 0.12).toFixed(2)})`;
      const px = ((dx + 1) * 50).toFixed(1);
      const py = ((dy + 1) * 50).toFixed(1);
      const gAlpha = (0.08 + dist * 0.10).toFixed(2);
      glare.style.opacity = '1';
      glare.style.background = `radial-gradient(circle at ${px}% ${py}%,rgba(255,255,255,${gAlpha}) 0%,rgba(255,255,255,.02) 45%,transparent 70%)`;
      if (isPhoto) {
        const img = card.querySelector('.cc-img');
        if (img) img.style.filter = `drop-shadow(${(-dx * 6).toFixed(0)}px ${(-dy * 6).toFixed(0)}px 18px rgba(255,120,0,0.28))`;
      }
    }

    function onLeave() {
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
