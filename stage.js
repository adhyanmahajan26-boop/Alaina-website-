/* Alaina — the rendered films on the homepage.
   One canvas is shared by the hero and "Inside a cabin damper":
     c  hero film: a car drives in, brakes, its body lifts apart and the camera goes in to the strut (plays by itself)
     b  a truck pulls up, its cabin lifts apart and the camera goes in to the cabin damper (played by scrolling)
     s  the cabin damper comes apart and the camera visits each part (played by scrolling, straight after b)
     r  the assembled damper cycling on the rig
   Further down, the shocker section plays x (a light truck and its axle shocker) and the strut section plays q
   (the car again, from behind, and its rear strut).
   Frames are pre-rendered with scripts/render (see README), so this looks the same on every phone. */
(function () {
  'use strict';
  var d = document, root = d.documentElement;
  var stage = d.getElementById('stage'), cv = d.getElementById('seq');
  if (!stage || !cv || !cv.getContext) return;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return; // the still frame and a plain list of parts stay in place

  var ctx = cv.getContext('2d');
  var sq = stage.querySelector('.stage-sq'), anatomy = d.getElementById('anatomy'), intro = d.getElementById('range');
  var steps = [].slice.call(stage.querySelectorAll('.an-steps li:not(.an-lead)'));
  var ticks = [].slice.call(stage.querySelectorAll('.an-bar i'));
  var lead = stage.querySelector('.an-lead'), replay = d.getElementById('replay'), read = stage.querySelector('.hero-read');

  var N = { c: +cv.getAttribute('data-c') || 78, b: +cv.getAttribute('data-b') || 59, s: 85, r: 12 }, SEG = 14; // SEG frames between two stops of the tour
  var FPS = 18, HOLD = 10, XF = 5;             // scroll "frames" the truck film rests on the damper, then dissolves to the damper on its own
  var R_REST = 2, R_MM = 4.5;                  // millimetres of stroke per frame on the rig
  var wide = function () { return window.innerWidth > 860; };
  var big = wide() && window.innerWidth * (window.devicePixelRatio || 1) > 1500;
  var seqDir = stage.getAttribute('data-seq') || 'seq/';
  var dirs = { c: seqDir + 'film/', b: seqDir + 'film/', s: seqDir + (big ? '1080/' : '720/'), r: seqDir + (big ? '1080/' : '720/') };
  var F = { c: [], b: [], s: [], r: [] }, shown = '';

  function pad(i, n) { i = String(i); while (i.length < n) i = '0' + i; return i; }
  function load(set, i, cb) {
    if (F[set][i]) return;
    var im = new Image();
    im.decoding = 'async';
    im.onload = function () { im.ok = true; shown = ''; if (cb) cb(); };
    im.onerror = function () { if (cb) cb(); };
    im.src = dirs[set] + set + pad(i, set === 'r' ? 2 : 3) + '.webp';
    F[set][i] = im;
  }
  // a film loads in order, a few frames at a time, so the first frames are never stuck behind the last ones
  function loadInOrder(set, done) {
    var next = 0, open = 0;
    (function pump() {
      while (open < 4 && next < N[set]) { open++; load(set, next++, function () { open--; pump(); }); }
      if (next >= N[set] && open === 0 && done) { var f = done; done = null; f(); }
    })();
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
  function ready(set, i) { var im = F[set][i]; return !!(im && im.ok); }

  /* layout: on phones the picture sits low in the hero and moves up under the heading once the tour starts */
  var vh = 0, side = 0, shiftY = 0, shiftS = 1, anTop = 0, anLen = 1, inTop = 0, inH = 0, dimNow = -1, PB = 0.3;
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
    anTop = a.top + y - vh * 0.06;                 // the truck starts to arrive once the products title card has left
    anLen = Math.max(1, a.top + y + a.height - vh - anTop);
    if (intro) { var ir = intro.getBoundingClientRect(); inTop = ir.top + y; inH = ir.height; }
    shown = '';
  }

  /* the hero film runs on a clock that only moves while the next frame is there to show */
  var clock = 0, playing = false, ended = false, last = 0, inView = true, started = false, pos = 0;
  function play() { clock = 0; playing = true; ended = false; shown = ''; if (read) read.classList.remove('done'); }

  var prevIm = null, curIm = null, curSet = '', swT = -1e9;
  function put(im, a) {
    if (!im) return;
    ctx.globalAlpha = a;
    ctx.drawImage(im, 0, 0, cv.width, cv.height);
  }
  // draw one frame, or two blended; a change of film dissolves instead of cutting
  function draw(now, set, im, key, im2, mix) {
    var fading = now - swT < 420;
    if (!im || (key === shown && !fading)) return;
    if (set !== curSet) { if (curSet && curIm) { prevIm = curIm; swT = now; fading = true; } curSet = set; }
    shown = key; curIm = im;
    ctx.globalAlpha = 1;
    ctx.clearRect(0, 0, cv.width, cv.height);
    put(im, 1);
    if (im2 && mix > 0.01) put(im2, mix);
    if (fading && prevIm) put(prevIm, 1 - (now - swT) / 420);
    ctx.globalAlpha = 1;
  }

  function frame(now) {
    requestAnimationFrame(frame);
    if (!inView || d.hidden || root.classList.contains('cat-open')) { last = now; return; }
    var dt = Math.min(0.05, (now - last) / 1000 || 0.016); last = now;
    var sy = window.pageYOffset;
    var ap = Math.max(0, Math.min(1, (sy - anTop) / anLen));
    // on phones the products title card passes over the picture, so the picture steps back while it does
    if (inH) {
      var k = wide() ? 0 : Math.max(0, Math.min(1, Math.min((sy + vh - inTop) / (vh * 0.24) - 0.1, (inTop + inH - sy) / (vh * 0.3) + 0.85)));
      k = k * k * (3 - 2 * k);
      if (Math.abs(k - dimNow) > 0.004) { dimNow = k; sq.style.opacity = (1 - 0.84 * k).toFixed(3); }
    }
    // one scroll position runs the truck film, the dissolve and then the tour of the damper
    var end = N.b - 1, pre = end + HOLD, tgt = ap <= 0 ? 0 : ap < PB ? ap / PB * pre : pre + XF + (ap - PB) / (1 - PB) * (N.s - 1);
    pos += (tgt - pos) * Math.min(1, dt * 9);
    if (Math.abs(tgt - pos) < 0.02) pos = tgt;
    var fS = pos - pre - XF;                         // frame of the tour (negative while the truck is still on)
    var touring = fS > 0.3, m = Math.max(0, Math.min(1, pos / 6));
    m = m * m * (3 - 2 * m);
    if (!wide()) sq.style.transform = 'translate(-50%,' + (shiftY * m).toFixed(1) + 'px) scale(' + (1 + (shiftS - 1) * m).toFixed(4) + ')';
    stage.classList.toggle('touring', touring);
    stage.classList.toggle('film', fS < 1);

    if (ap <= 0 && pos < 0.5) {
      // hero
      if (playing) {
        var want = Math.floor(clock * FPS);
        if (want >= N.c - 1) { want = N.c - 1; playing = false; ended = true; if (read) read.classList.add('done'); }
        else if (ready('c', Math.min(N.c - 1, want + 1))) clock += dt;
        if (ready('c', want)) draw(now, 'c', F.c[want], 'c' + want);
        var ahead = F.c[want + 2]; if (ahead && ahead.ok && ahead.decode) ahead.decode().catch(function () {});
      } else {
        draw(now, 'c', pick('c', ended ? N.c - 1 : 0), 'c' + (ended ? 'end' : 'start'));
      }
    } else if (fS <= -XF) {
      var bi = Math.min(end, Math.round(pos));
      draw(now, 'b', pick('b', bi), 'b' + bi);
    } else if (fS < 0) {
      var mix = 1 + fS / XF;                          // 0 → 1 across the dissolve
      draw(now, 'b', pick('b', end), 'x' + mix.toFixed(2), pick('s', 0), mix);
    } else if (fS > N.s - 1.4) {
      var rx = 17 + 16 * Math.sin(now / 1000 * 2 * Math.PI * 1.25);
      var ri = Math.round(R_REST + rx / R_MM);
      draw(now, 's', pick('r', ri), 'r' + ri);
    } else {
      var si = Math.round(fS);
      draw(now, 's', pick('s', si), 's' + si);
    }
    // which part the camera is on
    var stop = Math.round(fS / SEG), near = Math.abs(fS - stop * SEG) < SEG * 0.42;
    for (var i = 0; i < steps.length; i++) steps[i].classList.toggle('is-active', fS > 0 && near && stop === i + 1);
    for (var j = 0; j < ticks.length; j++) ticks[j].classList.toggle('on', fS >= (j + 1) * SEG - SEG * 0.42);
    if (lead) lead.classList.toggle('is-active', ap > 0 && fS < SEG * 0.42);
  }

  if (replay) replay.addEventListener('click', function () { if (window.pageYOffset < anTop) play(); });

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (en) { inView = en[0].isIntersecting; }, { rootMargin: '200px' }).observe(stage);
  }
  var rt;
  window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(measure, 120); });
  window.addEventListener('load', measure);
  if (d.fonts && d.fonts.ready) d.fonts.ready.then(measure);

  root.classList.add('seq');
  measure();
  // the truck and the tour load once the hero film is in, or as soon as the reader starts to scroll
  function later() {
    if (started) return; started = true;
    loadInOrder('b', function () {
      loadSet('s', range(N.s, 2));
      loadSet('s', range(N.s, 2, 1));
      loadSet('r', range(N.r, 1));
    });
  }
  load('c', 0, function () { root.classList.add('seq-on'); });
  loadInOrder('c', later);
  window.addEventListener('scroll', later, { passive: true, once: true });
  // someone who lands part-way down the page (a #link, a reload) should not come back up to a film in mid-flow
  if (window.pageYOffset > anTop) { ended = true; if (read) read.classList.add('done'); } else play();
  requestAnimationFrame(function (t) { last = t; frame(t); });
})();

/* The product lines further down: a canvas with data-film plays its film once, each time its picture comes well into view. */
(function () {
  'use strict';
  var d = document;
  var cvs = [].slice.call(d.querySelectorAll('canvas[data-film]'));
  if (!cvs.length || !cvs[0].getContext || !('IntersectionObserver' in window)) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return; // the still stays
  var stage = d.getElementById('stage');
  var dir = ((stage && stage.getAttribute('data-seq')) || 'seq/') + 'film/';
  var live = [], running = false, last = 0;

  var items = cvs.map(function (cv) {
    return { cv: cv, ctx: cv.getContext('2d'), set: cv.getAttribute('data-film'), n: +cv.getAttribute('data-n') || 59, fps: +cv.getAttribute('data-fps') || 14,
      box: cv.parentNode, host: cv.closest('.line') || cv.parentNode, F: [], t: 0, shown: -1, loaded: false, seen: false };
  });
  function pad(i) { i = String(i); while (i.length < 3) i = '0' + i; return i; }
  // frames load in order, a few at a time, so the film can start before the whole of it is in
  function load(it) {
    if (it.loaded) return; it.loaded = true;
    var next = 0, open = 0;
    (function pump() {
      while (open < 4 && next < it.n) {
        open++;
        (function (k) {
          var im = new Image(); im.decoding = 'async';
          im.onload = function () { im.ok = true; open--; if (k === 0 && !it.box.classList.contains('on')) { size(it); it.box.classList.add('on'); } kick(); pump(); };
          im.onerror = function () { open--; pump(); };
          im.src = dir + it.set + pad(k) + '.webp';
          it.F[k] = im;
        })(next++);
      }
    })();
  }
  function size(it) {
    var px = Math.round(Math.min(720, it.box.getBoundingClientRect().width * Math.min(window.devicePixelRatio || 1, 3)));
    if (px > 0 && it.cv.width !== px) { it.cv.width = px; it.cv.height = px; it.shown = -1; }
  }
  function ok(it, i) { var im = it.F[i]; return !!(im && im.ok); }
  function frame(now) {
    if (!live.length) { running = false; return; }
    requestAnimationFrame(frame);
    var dt = Math.min(0.05, (now - last) / 1000 || 0.016); last = now;
    live.forEach(function (it) {
      var i = Math.min(it.n - 1, Math.floor(it.t * it.fps));
      if (i < it.n - 1 && ok(it, i + 1)) it.t += dt;             // waits for frames that have not arrived
      if (i === it.shown || !ok(it, i)) return;
      it.shown = i;
      it.ctx.clearRect(0, 0, it.cv.width, it.cv.height);
      it.ctx.drawImage(it.F[i], 0, 0, it.cv.width, it.cv.height);
    });
  }
  function kick() { if (!running && live.length) { running = true; last = performance.now(); requestAnimationFrame(frame); } }

  var near = new IntersectionObserver(function (en) {
    en.forEach(function (e) { if (e.isIntersecting) { items.forEach(function (it) { if (it.host === e.target) load(it); }); near.unobserve(e.target); } });
  }, { rootMargin: '150% 0px' });
  // the picture has to be well on screen before its film starts; it starts again once it has left and come back
  var seen = new IntersectionObserver(function (en) {
    en.forEach(function (e) {
      items.forEach(function (it) {
        if (it.box !== e.target) return;
        var k = live.indexOf(it);
        if (e.isIntersecting && e.intersectionRatio >= 0.45) { if (k < 0) { if (!it.seen) { it.t = 0; it.shown = -1; it.seen = true; } live.push(it); size(it); } }
        else if (!e.isIntersecting) { if (k >= 0) live.splice(k, 1); it.seen = false; }
      });
    });
    kick();
  }, { threshold: [0, 0.45] });
  items.forEach(function (it) { near.observe(it.host); seen.observe(it.box); });
  var rt;
  window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { items.forEach(size); }, 150); });
})();
