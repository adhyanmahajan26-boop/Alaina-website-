/* Alaina — the rendered cabin damper on the homepage.
   Three frame sets, drawn to one canvas:
     h  the damper at rest, swept through its stroke (driven by a spring-and-damper model you can press)
     s  the scroll sequence: it comes apart and the camera visits each part
     r  the assembled unit cycling on the rig
   Frames are pre-rendered with scripts/render/damper.py (see README), so this looks the same on every phone. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var stage = d.getElementById('stage'), cv = d.getElementById('seq');
  if (!stage || !cv || !cv.getContext) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return; // the poster frame and a plain list of parts stay in place

  var ctx = cv.getContext('2d');
  var sq = stage.querySelector('.stage-sq'), anatomy = d.getElementById('anatomy');
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
  var vh = 0, side = 0, shiftY = 0, shiftS = 1, anTop = 0, anLen = 1;
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
    anTop = a.top + y - vh * 0.55;                 // the tour starts while the hero copy is still leaving
    anLen = Math.max(1, a.top + y + a.height - vh - anTop);
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
    if (!inView || d.hidden) { last = now; return; }
    var dt = Math.min(0.033, (now - last) / 1000 || 0.016); last = now;
    var ap = Math.max(0, Math.min(1, (window.pageYOffset - anTop) / anLen));
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
