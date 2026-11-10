/* Alaina — the rendered products on the homepage.
   The cabin damper has three frame sets, drawn to one canvas:
     h  the damper at rest, swept through its stroke (driven by a spring-and-damper model you can press)
     s  the scroll sequence: it comes apart and the camera visits each part
     r  the assembled unit cycling on the rig
   The shocker (k) and the strut (t) each turn through one short set as their section scrolls past.
   Frames are pre-rendered with scripts/render/damper.py and lines.py (see README), so this looks the same on every phone. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var stage = d.getElementById('stage'), cv = d.getElementById('seq');
  if (!stage || !cv || !cv.getContext) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return; // the poster frame and a plain list of parts stay in place

  var ctx = cv.getContext('2d');
  var sq = stage.querySelector('.stage-sq'), anatomy = d.getElementById('anatomy'), intro = d.getElementById('range');
  var steps = [].slice.call(stage.querySelectorAll('.an-steps li'));
  var ticks = [].slice.call(stage.querySelectorAll('.an-bar i'));
  var travel = d.getElementById('travel'), hint = stage.querySelector('.hr-hint');

  var N = { h: 24, s: 85, r: 12 }, SEG = 14;         // SEG frames between two stops of the scroll sequence
  var H_REST = 4, H_MM = 2.7, R_REST = 2, R_MM = 4.5; // millimetres of stroke per frame
  var wide = function () { return window.innerWidth > 860; };
  var big = wide() && window.innerWidth * (window.devicePixelRatio || 1) > 1500;
  var base = (stage.getAttribute('data-seq') || 'seq/') + (big ? '1080/' : '720/');
  var F = { h: [], s: [], r: [] }, dirty = true, shown = '';

  function pad(i, n) { i = String(i); while (i.length < n) i = '0' + i; return i; }
  function load(set, i) {
    if (F[set][i]) return;
    var im = new Image();
    im.decoding = 'async';
    im.onload = function () { im.ok = true; dirty = true; if (!root.classList.contains('seq-on') && set === 'h' && i === H_REST) { root.classList.add('seq-on'); } };
    im.src = base + set + pad(i, set === 's' ? 3 : 2) + '.webp';
    F[set][i] = im;
  }
  function loadSet(set, order) { for (var k = 0; k < order.length; k++) load(set, order[k]); }
  function range(n, step, from) { var a = []; for (var i = from || 0; i < n; i += step) a.push(i); return a; }
  // nearest frame that has arrived, so a slow connection shows a coarser animation instead of gaps
  function pick(set, i) {
    i = Math.max(0, Math.min(N[set] - 1, i));
    for (var k = 0; k < N[set]; k++) {
      var a = F[set][i - k], b = F[set][i + k];
      if (a && a.ok) return a;
      if (b && b.ok) return b;
    }
    return null;
  }

  /* layout: on phones the damper sits low in the hero and moves up under the heading once the tour starts */
  var vh = 0, side = 0, shiftY = 0, shiftS = 1, anTop = 0, anLen = 1, inTop = 0, inH = 0, dimNow = -1;
  function measure() {
    vh = window.innerHeight;
    sq.style.transform = '';
    var r = sq.getBoundingClientRect(), view = stage.querySelector('.stage-view').getBoundingClientRect();
    side = r.width;
    var px = Math.round(Math.min(big ? 1080 : 720, side * Math.min(window.devicePixelRatio || 1, 3)));
    if (cv.width !== px) { cv.width = px; cv.height = px; shown = ''; }
    if (wide()) { shiftY = 0; shiftS = 1; }
    else {
      var head = stage.querySelector('.an-head'), dock = parseFloat(getComputedStyle(root).getPropertyValue('--dock-h')) || 0;
      var top = (head ? head.offsetHeight : 60) + parseFloat(getComputedStyle(root).getPropertyValue('--nav-h')) + 18;
      var room = vh - top - dock - 158;
      var s2 = Math.max(200, Math.min(window.innerWidth, room));
      shiftS = s2 / side;
      shiftY = (top + s2 / 2) - ((r.top - view.top) + side / 2);
    }
    var a = anatomy.getBoundingClientRect(), y = window.pageYOffset;
    anTop = a.top + y - vh * 0.06;                 // the tour starts once the products title card has left
    anLen = Math.max(1, a.top + y + a.height - vh - anTop);
    if (intro) { var ir = intro.getBoundingClientRect(); inTop = ir.top + y; inH = ir.height; }
    dirty = true;
  }

  /* spring and damper: x is compression in mm */
  var x = 0, v = 0, pressed = false, last = 0, nextBump = 0, fS = 0, inView = true, started = false;
  var W0 = 2 * Math.PI * 2.1, ZETA = 0.3;
  function physics(dt, now) {
    var target = pressed ? 40 : 0;
    var acc = -W0 * W0 * (x - target) - 2 * ZETA * W0 * v;
    v += acc * dt; x += v * dt;
    if (x > 51) { x = 51; v = 0; }
    if (x < -10.5) { x = -10.5; v = 0; }
    if (!pressed && now > nextBump) {            // the road keeps talking
      v += 160 + Math.random() * 240;
      nextBump = now + 2600 + Math.random() * 2600;
    }
  }

  function draw(im, key) {
    if (!im || key === shown) return;
    shown = key;
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.drawImage(im, 0, 0, cv.width, cv.height);
  }

  function frame(now) {
    requestAnimationFrame(frame);
    if (!inView || d.hidden || root.classList.contains('cat-open')) { last = now; return; }
    var dt = Math.min(0.033, (now - last) / 1000 || 0.016); last = now;
    var sy = window.pageYOffset;
    var ap = Math.max(0, Math.min(1, (sy - anTop) / anLen));
    // on phones the products title card passes over the damper, so the damper steps back while it does
    if (inH) {
      var k = wide() ? 0 : Math.max(0, Math.min(1, Math.min((sy + vh - inTop) / (vh * 0.24) - 0.1, (inTop + inH - sy) / (vh * 0.3) + 0.85)));
      k = k * k * (3 - 2 * k);
      if (Math.abs(k - dimNow) > 0.004) { dimNow = k; sq.style.opacity = (1 - 0.8 * k).toFixed(3); }
    }
    var tF = ap * (N.s - 1);
    fS += (tF - fS) * Math.min(1, dt * 9);
    if (Math.abs(tF - fS) < 0.02) fS = tF;
    var touring = fS > 0.3, m = Math.max(0, Math.min(1, fS / 6));
    m = m * m * (3 - 2 * m);
    if (!wide()) sq.style.transform = 'translate(-50%,' + (shiftY * m).toFixed(1) + 'px) scale(' + (1 + (shiftS - 1) * m).toFixed(4) + ')';
    stage.classList.toggle('touring', touring);

    var onRig = fS > N.s - 1.4;
    if (!touring) {
      physics(dt, now);
      var hi = Math.round(H_REST + x / H_MM);
      draw(pick('h', hi), 'h' + hi);
      if (travel) { var tx = Math.abs(x) < 0.15 ? 0 : x; travel.textContent = (tx < 0 ? '-' : '') + pad(Math.abs(tx).toFixed(1), 4); }
    } else if (onRig) {
      var rx = 17 + 16 * Math.sin(now / 1000 * 2 * Math.PI * 1.25);
      var ri = Math.round(R_REST + rx / R_MM);
      draw(pick('r', ri), 'r' + ri);
    } else {
      var si = Math.round(fS);
      draw(pick('s', si), 's' + si);
    }
    // which part the camera is on
    var stop = Math.round(fS / SEG), near = Math.abs(fS - stop * SEG) < SEG * 0.42;
    for (var i = 0; i < steps.length; i++) steps[i].classList.toggle('is-active', near && stop === i + 1);
    for (var j = 0; j < ticks.length; j++) ticks[j].classList.toggle('on', fS >= (j + 1) * SEG - SEG * 0.42);
  }

  /* pressing the damper loads it; letting go lets it settle */
  function down(e) {
    if (stage.classList.contains('touring')) return;
    pressed = true; nextBump = Infinity;
    if (hint) hint.classList.add('used');
  }
  function up() { if (pressed) { pressed = false; nextBump = performance.now() + 4000; } }
  sq.addEventListener('pointerdown', down);
  window.addEventListener('pointerup', up);
  window.addEventListener('pointercancel', up);
  window.addEventListener('scroll', function () { if (pressed) up(); }, { passive: true });

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (en) { inView = en[0].isIntersecting; }, { rootMargin: '200px' }).observe(stage);
  }
  var rt;
  window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(measure, 120); });
  window.addEventListener('load', measure);
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(measure);

  root.classList.add('seq');
  measure();
  load('h', H_REST);
  loadSet('h', range(N.h, 1));
  // the scroll sequence loads once the first paint is out of the way: every other frame first, then the rest
  function later() {
    if (started) return; started = true;
    loadSet('s', range(N.s, 2));
    loadSet('s', range(N.s, 2, 1));
    loadSet('r', range(N.r, 1));
  }
  if (d.readyState === 'complete') setTimeout(later, 400); else window.addEventListener('load', function () { setTimeout(later, 400); });
  window.addEventListener('scroll', later, { passive: true, once: true });
  // settle in on arrival
  x = 34; v = 0; nextBump = performance.now() + 3200;
  requestAnimationFrame(function (t) { last = t; frame(t); });
})();

/* The shocker and the strut: a short rendered set each, turned by the scroll position of its section. */
(function () {
  'use strict';
  var d = document;
  var cvs = [].slice.call(d.querySelectorAll('canvas[data-scrub]'));
  if (!cvs.length || !cvs[0].getContext || !('IntersectionObserver' in window)) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return; // the still stays
  var stage = d.getElementById('stage');
  var big = window.innerWidth > 860 && window.innerWidth * (window.devicePixelRatio || 1) > 1500;
  var base = ((stage && stage.getAttribute('data-seq')) || 'seq/') + (big ? '1080/' : '720/');
  var live = [], running = false, last = 0;

  var items = cvs.map(function (cv) {
    var it = { cv: cv, ctx: cv.getContext('2d'), set: cv.getAttribute('data-scrub'), n: +cv.getAttribute('data-n') || 30,
      box: cv.parentNode, host: cv.closest('.line') || cv.parentNode, F: [], f: -1, shown: -1, loaded: false };
    return it;
  });
  function pad(i) { return (i < 10 ? '0' : '') + i; }
  function load(it) {
    if (it.loaded) return; it.loaded = true;
    // middle frame first so there is something to show, then every other frame, then the rest
    var order = [it.n >> 1], i;
    for (i = 0; i < it.n; i += 2) order.push(i);
    for (i = 1; i < it.n; i += 2) order.push(i);
    order.forEach(function (k) {
      if (it.F[k]) return;
      var im = new Image(); im.decoding = 'async';
      im.onload = function () { im.ok = true; it.shown = -1; if (!it.box.classList.contains('on')) { size(it); it.box.classList.add('on'); } kick(); };
      im.src = base + it.set + pad(k) + '.webp';
      it.F[k] = im;
    });
  }
  function size(it) {
    var px = Math.round(Math.min(big ? 1080 : 720, it.box.getBoundingClientRect().width * Math.min(window.devicePixelRatio || 1, 3)));
    if (px > 0 && it.cv.width !== px) { it.cv.width = px; it.cv.height = px; it.shown = -1; }
  }
  function pick(it, i) {
    for (var k = 0; k < it.n; k++) {
      var a = it.F[i - k], b = it.F[i + k];
      if (a && a.ok) return a;
      if (b && b.ok) return b;
    }
    return null;
  }
  function frame(now) {
    if (!live.length) { running = false; return; }
    requestAnimationFrame(frame);
    var dt = Math.min(0.05, (now - last) / 1000 || 0.016); last = now;
    var vh = window.innerHeight;
    live.forEach(function (it) {
      var r = it.host.getBoundingClientRect();
      // 0 as the section rises into view, 1 once most of it has gone by
      var p = Math.max(0, Math.min(1, (vh * 0.92 - r.top) / Math.max(1, r.height - vh * 0.08)));
      var target = p * (it.n - 1);
      it.f = it.f < 0 ? target : it.f + (target - it.f) * Math.min(1, dt * 8);
      var i = Math.round(it.f);
      if (i === it.shown) return;
      var im = pick(it, i);
      if (!im) return;
      it.shown = i;
      it.ctx.clearRect(0, 0, it.cv.width, it.cv.height);
      it.ctx.drawImage(im, 0, 0, it.cv.width, it.cv.height);
    });
  }
  function kick() { if (!running && live.length) { running = true; last = performance.now(); requestAnimationFrame(frame); } }

  var near = new IntersectionObserver(function (en) {
    en.forEach(function (e) { if (e.isIntersecting) { items.forEach(function (it) { if (it.host === e.target) load(it); }); near.unobserve(e.target); } });
  }, { rootMargin: '120% 0px' });
  var seen = new IntersectionObserver(function (en) {
    en.forEach(function (e) {
      items.forEach(function (it) {
        if (it.host !== e.target) return;
        var k = live.indexOf(it);
        if (e.isIntersecting && k < 0) { live.push(it); size(it); } else if (!e.isIntersecting && k >= 0) live.splice(k, 1);
      });
    });
    kick();
  }, { rootMargin: '10% 0px' });
  items.forEach(function (it) { near.observe(it.host); seen.observe(it.host); });
  var rt;
  window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { items.forEach(size); }, 150); });
})();
