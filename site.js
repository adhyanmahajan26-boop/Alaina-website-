/* Alaina — shared behaviour for every page: theme, menu, header, reveal, dock, lazy film. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  window.__alainaReady = true;
  var $ = function (s, c) { return (c || d).querySelector(s); };
  var $$ = function (s, c) { return [].slice.call((c || d).querySelectorAll(s)); };
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* theme */
  var tb = $('#themeToggle');
  function syncTheme() {
    if (!tb) return;
    var k = root.getAttribute('data-theme') === 'dark';
    tb.setAttribute('aria-pressed', k);
    tb.setAttribute('aria-label', k ? 'Switch to light mode' : 'Switch to dark mode');
  }
  syncTheme();
  if (tb) tb.addEventListener('click', function () {
    var n = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    var go = function () { root.setAttribute('data-theme', n); syncTheme(); };
    try { localStorage.setItem('alaina-theme', n); } catch (e) {}
    if (d.startViewTransition && !reduce) { var vt = d.startViewTransition(go); ['ready', 'finished', 'updateCallbackDone'].forEach(function (k) { if (vt && vt[k]) vt[k].catch(function () {}); }); } else go();
  });

  /* mobile menu */
  var burger = $('#burger'), menu = $('#mobnav'), mx = $('#mnClose');
  /* several layers can hold the page still at once (menu, catalogue, spec sheet); it scrolls again when the last lets go */
  var locks = {};
  function lock(on, key) {
    key = key || 'menu';
    if (on) locks[key] = 1; else delete locks[key];
    var any = Object.keys(locks).length > 0;
    d.body.style.overflow = any ? 'hidden' : '';
    root.classList.toggle('dock-off', any);
  }
  function closeMenu() {
    if (!menu || !menu.classList.contains('open')) return;
    menu.classList.remove('open'); burger && burger.setAttribute('aria-expanded', 'false'); lock(false);
  }
  function openMenu() { menu.classList.add('open'); burger.setAttribute('aria-expanded', 'true'); lock(true); }
  if (burger && menu) {
    burger.addEventListener('click', openMenu);
    if (mx) mx.addEventListener('click', closeMenu);
    $$('a', menu).forEach(function (a) { a.addEventListener('click', closeMenu); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMenu(); });
  }
  window.AlainaUI = { lock: lock, closeMenu: closeMenu };

  /* header hides on the way down, returns on the way up */
  var lastY = window.pageYOffset, ticking = false;
  function onScroll() {
    ticking = false;
    var y = window.pageYOffset;
    root.classList.toggle('at-top', y < 240);
    root.classList.toggle('at-hero', y < 16);
    if (Math.abs(y - lastY) > 6) {
      root.classList.toggle('nav-hide', y > lastY && y > 520 && !(menu && menu.classList.contains('open')));
      lastY = y;
    }
  }
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();

  /* reveal on scroll */
  var items = $$('[data-reveal]');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (en) {
      en.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    items.forEach(function (el) { io.observe(el); });
  } else items.forEach(function (el) { el.classList.add('in'); });

  /* numbers count up once */
  var counts = $$('[data-count]');
  if (counts.length && 'IntersectionObserver' in window && !reduce) {
    var cio = new IntersectionObserver(function (en) {
      en.forEach(function (e) {
        if (!e.isIntersecting) return;
        cio.unobserve(e.target);
        var el = e.target, to = parseFloat(el.getAttribute('data-count')), from = parseFloat(el.getAttribute('data-from') || 0), t0 = 0;
        (function tick(t) {
          if (!t0) t0 = t;
          var k = Math.min(1, (t - t0) / 1400); k = 1 - Math.pow(1 - k, 4);
          el.textContent = Math.round(from + (to - from) * k);
          if (k < 1) requestAnimationFrame(tick);
        })(performance.now());
      });
    }, { threshold: 0.6 });
    counts.forEach(function (el) { cio.observe(el); });
  }

  /* films: load and play only while on screen */
  var vids = $$('video[data-lazy]');
  if (vids.length && 'IntersectionObserver' in window) {
    var vio = new IntersectionObserver(function (en) {
      en.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) {
          if (!v.src && v.getAttribute('data-src')) v.src = v.getAttribute('data-src');
          if (!reduce) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
        } else if (!v.paused) v.pause();
      });
    }, { rootMargin: '200px' });
    vids.forEach(function (v) { vio.observe(v); });
  }

  /* dock steps aside while typing */
  d.addEventListener('focusin', function (e) { if (e.target.matches && e.target.matches('input,textarea,select')) root.classList.add('dock-off'); });
  d.addEventListener('focusout', function () { if (!Object.keys(locks).length) root.classList.remove('dock-off'); });
  var yr = $('#yr'); if (yr) yr.textContent = new Date().getFullYear();
})();
