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
  var d = document, root = d.documentElement, stage = d.getElementById('stage');
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return; // the stills and a plain list of parts stay in place

  var dpr = window.devicePixelRatio || 1;
  var seqDir = (stage && stage.getAttribute('data-seq')) || 'seq/';
  // the films come in two sizes: the larger one goes to sharp screens on a connection and a phone that can take it
  var net = navigator.connection || {}, slow = net.saveData || /(^|-)[23]g$/.test(net.effectiveType || '');
  var able = !!stage && stage.hasAttribute('data-hd') && !slow && (navigator.deviceMemory || 8) >= 4 && (navigator.hardwareConcurrency || 8) >= 4;
  var weak = false;                             // set when the hero film could not keep its pace: everything after it takes the smaller frames
  function sharp(cssWidth) { return able && !weak && cssWidth * dpr > 900; }
  function pad(i, n) { i = String(i); while (i.length < n) i = '0' + i; return i; }

  /* A reel is one film's frames.
     Decoding a frame is the expensive part of showing it, so frames are fetched as files and the few around the one on
     screen are decoded off the main thread (createImageBitmap on a blob). Scrolling and the page never wait for a decode.
     Without that API the reel falls back to plain <img> frames. */
  var BMP = typeof createImageBitmap === 'function' && typeof fetch === 'function' && typeof Promise === 'function';
  function Reel(n, src) {
    this.n = n; this.src = src;
    this.ok = [];                               // frame has arrived
    this.bl = []; this.im = [];                 // its file, or its <img> on the fallback path
    this.bm = {}; this.busy = {};               // decoded frames, and the time each decode was asked for
    this.lo = 0; this.hi = -1; this.last = 0; this.fwd = true;
    this.plain = !BMP; this.got = -1; this.exact = false;
    this.all = n <= 14;                         // a short loop stays decoded whole
  }
  var RP = Reel.prototype;
  RP.image = function (i, url, cb) {
    var me = this, im = new Image();
    im.decoding = 'async';
    im.onload = function () { me.ok[i] = true; if (cb) cb(); };
    im.onerror = function () { if (cb) cb(); };
    im.src = url;
    this.im[i] = im;
  };
  RP.fetch = function (i, cb) {
    if (this.asked && this.asked[i]) return;
    (this.asked || (this.asked = []))[i] = true;
    var me = this, url = this.src(i);
    if (this.plain) { this.image(i, url, cb); return; }
    fetch(url).then(function (r) { if (!r.ok) throw 0; return r.blob(); }).then(function (b) {
      me.bl[i] = b;
      if (me.plain) { me.image(i, URL.createObjectURL(b), cb); return; }
      me.ok[i] = true;
      if (i >= me.lo && i <= me.hi) me.decode(i, performance.now());
      if (cb) cb();
    }, function () { if (cb) cb(); });
  };
  // in order, a few at a time, so the first frames are never stuck behind the last ones
  RP.fetchAll = function (done, each) {
    var me = this, next = 0, open = 0;
    (function pump() {
      while (open < 4 && next < me.n) { open++; (function (k) { me.fetch(k, function () { open--; if (each) each(k); pump(); }); })(next++); }
      if (next >= me.n && open === 0 && done) { var f = done; done = null; f(); }
    })();
  };
  RP.fetchSome = function (order) { for (var k = 0; k < order.length; k++) this.fetch(order[k]); };
  RP.decode = function (k, now) {
    var me = this;
    if (me.plain || me.bm[k] || me.busy[k] || !me.ok[k]) return;
    me.busy[k] = now || 1;
    var p;
    try { p = createImageBitmap(me.bl[k]); } catch (e) { me.toPlain(); return; }
    p.then(function (b) {
      me.busy[k] = 0;
      if (me.plain || k < me.lo || k > me.hi) { b.close(); return; }
      me.bm[k] = b;
    }, function () { me.busy[k] = 0; me.toPlain(); });
  };
  // this browser cannot decode the files directly: carry on with <img> frames
  RP.toPlain = function () {
    if (this.plain) return;
    this.plain = true; this.free();
    for (var i = 0; i < this.n; i++) if (this.bl[i] && !this.im[i]) { this.ok[i] = false; this.image(i, URL.createObjectURL(this.bl[i])); }
  };
  // nearest frame that has arrived, so a slow connection shows a coarser animation instead of gaps
  RP.near = function (i) {
    for (var k = 0; k < this.n; k++) {
      if (this.ok[i - k]) return i - k;
      if (this.ok[i + k]) return i + k;
    }
    return -1;
  };
  // keep the frames around j decoded, further ahead in the direction of travel, and let go of the rest
  RP.warm = function (j, now) {
    if (j !== this.last) { this.fwd = j > this.last; this.last = j; }
    var lo = this.all ? 0 : Math.max(0, j - (this.fwd ? 1 : 5)), hi = this.all ? this.n - 1 : Math.min(this.n - 1, j + (this.fwd ? 5 : 1)), k;
    if (lo !== this.lo || hi !== this.hi) {
      this.lo = lo; this.hi = hi;
      for (k in this.bm) if (+k < lo || +k > hi) { this.bm[k].close(); delete this.bm[k]; }
    }
    this.decode(j, now);
    for (k = 1; k <= 5; k++) { this.decode(j + (this.fwd ? k : -k), now); }
    if (this.all) for (k = lo; k <= hi; k++) this.decode(k, now);
    else this.decode(j + (this.fwd ? -1 : 1), now);
  };
  /* What to draw for frame i. Sets .got (the frame handed back) and .exact (it is the one asked for).
     If that frame is still decoding, the closest decoded one stands in for it; null means keep what is on screen. */
  RP.at = function (i, now) {
    i = Math.max(0, Math.min(this.n - 1, i));
    var j = this.near(i);
    this.exact = false; this.got = -1; this.used = now;
    if (j < 0) return null;
    if (this.plain) { this.got = j; this.exact = j === i; return this.im[j]; }
    this.warm(j, now);
    if (this.bm[j]) { this.got = j; this.exact = j === i; return this.bm[j]; }
    var best = -1, k;
    for (k = this.lo; k <= this.hi; k++) if (this.bm[k] && (best < 0 || Math.abs(k - j) < Math.abs(best - j))) best = k;
    if (best >= 0) { this.got = best; return this.bm[best]; }
    return null;
  };
  // frame i can be shown without a wait (a film on a clock only moves on once its next frame can)
  RP.has = function (i, now) {
    if (!this.ok[i]) return false;
    if (this.plain || this.bm[i] || i < this.lo || i > this.hi) return true;
    this.decode(i, now);
    return false;
  };
  // let go of decoded frames: all of them, or all but the one on screen (it may still be needed for a dissolve)
  RP.free = function (keep) {
    for (var k in this.bm) if (!keep || +k !== this.got) { this.bm[k].close(); delete this.bm[k]; }
    this.lo = keep && this.bm[this.got] ? this.got : 0; this.hi = keep && this.bm[this.got] ? this.got : -1;
  };
  // canvas pixels for a picture this wide: the frames' own size when the screen is about that sharp, so a frame is copied, not resampled
  function pixels(cssWidth, max) { var px = Math.round(cssWidth * Math.min(dpr, 3)); return px >= max * 0.8 ? max : px; }
  function paint(ctx, im, w, h) { try { ctx.drawImage(im, 0, 0, w, h); return true; } catch (e) { return false; } }

  /* ─── the hero and the cabin damper, on one canvas ─── */
  (function () {
    var cv = d.getElementById('seq');
    if (!stage || !cv || !cv.getContext) return;
    var ctx = cv.getContext('2d');
    var sq = stage.querySelector('.stage-sq'), anatomy = d.getElementById('anatomy'), intro = d.getElementById('range');
    var steps = [].slice.call(stage.querySelectorAll('.an-steps li:not(.an-lead)'));
    var ticks = [].slice.call(stage.querySelectorAll('.an-bar i'));
    var lead = stage.querySelector('.an-lead'), replay = d.getElementById('replay'), read = stage.querySelector('.hero-read');

    var N = { c: +cv.getAttribute('data-c') || 78, b: +cv.getAttribute('data-b') || 59, s: 85, r: 12 }, SEG = 14; // SEG frames between two stops of the tour
    var FPS = 18, HOLD = 10, XF = 5;             // scroll "frames" the truck film rests on the damper, then dissolves to the damper on its own
    var R_REST = 2, R_MM = 4.5;                  // millimetres of stroke per frame on the rig
    var wide = function () { return window.innerWidth > 860; };
    var big = wide() && window.innerWidth * dpr > 1500;
    var hd = sharp(sq.getBoundingClientRect().width), FMAX = hd ? 1080 : 720;
    var tour = seqDir + (big ? '1080/' : '720/');
    var dirs = { c: seqDir + 'film/' + (hd ? '1080/' : '720/'), b: '', s: tour, r: tour };
    var R = {};
    ['c', 'b', 's', 'r'].forEach(function (set) {
      R[set] = new Reel(N[set], function (i) { return dirs[set] + set + pad(i, set === 'r' ? 2 : 3) + '.webp'; });
    });
    function range(n, step, from) { var a = []; for (var i = from || 0; i < n; i += step) a.push(i); return a; }

    /* layout: on phones the picture sits low in the hero and moves up under the heading once the tour starts */
    var vh = 0, side = 0, shiftY = 0, shiftS = 1, anTop = 0, anLen = 1, inTop = 0, inH = 0, dimNow = -1, PB = 0.3;
    var tfNow = '', wantKey = '', gotKey = '', settled = false, state = '';
    function measure() {
      vh = window.innerHeight;
      sq.style.transform = ''; tfNow = '';
      var r = sq.getBoundingClientRect(), view = stage.querySelector('.stage-view').getBoundingClientRect();
      side = r.width;
      var px = pixels(side, Math.max(FMAX, big ? 1080 : 720));
      if (cv.width !== px) { cv.width = px; cv.height = px; }
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
      wantKey = gotKey = '';
    }

    /* the hero film runs on a clock that only moves while the next frame is there to show */
    var clock = 0, playing = false, ended = false, last = 0, inView = true, started = false, pos = 0, idle = false, tick = 0;
    var paceN = 0, paceSlow = 0;
    function play() { clock = 0; playing = true; ended = false; wantKey = ''; if (read) read.classList.remove('done'); }

    var prevIm = null, curIm = null, curSet = '', swT = -1e9, first = true;
    // show frame i of a reel, or two frames blended; a change of film dissolves instead of cutting
    function show(now, set, reel, i, reel2, i2, mix) {
      var fading = now - swT < 420;
      var wk = set + '/' + reel.n + '/' + i + (reel2 ? '+' + mix.toFixed(2) : '');
      if (wk === wantKey && settled && !fading) return;
      var im = reel.at(i, now), ok = reel.exact, gk = reel.n + ':' + reel.got, im2 = null;
      if (!im) return;
      if (reel2) { im2 = reel2.at(i2, now); if (im2) gk += '+' + reel2.got + '@' + mix.toFixed(2); ok = ok && !!im2 && reel2.exact; }
      wantKey = wk; settled = ok;
      if (gk === gotKey && !fading) return;
      if (set !== curSet) { if (curSet && curIm) { prevIm = curIm; swT = now; fading = true; } curSet = set; }
      gotKey = gk; curIm = im;
      ctx.globalAlpha = 1;
      if (set === 's') ctx.clearRect(0, 0, cv.width, cv.height);   // only the tour's frames are see-through; a film frame covers the canvas
      paint(ctx, im, cv.width, cv.height);
      if (im2 && mix > 0.01) { ctx.globalAlpha = mix; paint(ctx, im2, cv.width, cv.height); }
      if (fading && prevIm) { ctx.globalAlpha = Math.max(0, 1 - (now - swT) / 420); paint(ctx, prevIm, cv.width, cv.height); }
      ctx.globalAlpha = 1;
      if (first) { first = false; root.classList.add('seq-on'); }
    }

    function frame(now) {
      requestAnimationFrame(frame);
      if (!inView || d.hidden || root.classList.contains('cat-open')) {
        if (!idle) { idle = true; for (var q in R) R[q].free(true); }
        last = now; return;
      }
      idle = false;
      var raw = now - last, dt = Math.min(0.05, raw / 1000 || 0.016); last = now;
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
      var m = Math.max(0, Math.min(1, pos / 6));
      m = m * m * (3 - 2 * m);
      if (!wide()) {
        var tf = 'translate(-50%,' + (shiftY * m).toFixed(1) + 'px) scale(' + (1 + (shiftS - 1) * m).toFixed(4) + ')';
        if (tf !== tfNow) { tfNow = tf; sq.style.transform = tf; }
      }

      if (ap <= 0 && pos < 0.5) {
        // hero
        if (playing) {
          var want = Math.floor(clock * FPS);
          if (want >= N.c - 1) { want = N.c - 1; playing = false; ended = true; if (read) read.classList.add('done'); }
          else if (R.c.has(want + 1, now)) clock += dt;
          show(now, 'c', R.c, want);
          if (clock > 0.8) { paceN++; if (raw > 40) paceSlow++; }
        } else {
          show(now, 'c', R.c, ended ? N.c - 1 : 0);
        }
      } else if (fS <= -XF) {
        show(now, 'b', R.b, Math.min(end, Math.round(pos)));
      } else if (fS < 0) {
        show(now, 'b', R.b, end, R.s, 0, 1 + fS / XF);   // 0 → 1 across the dissolve
      } else if (fS > N.s - 1.4) {
        var rx = 17 + 16 * Math.sin(now / 1000 * 2 * Math.PI * 1.25);
        show(now, 's', R.r, Math.round(R_REST + rx / R_MM));
      } else {
        show(now, 's', R.s, Math.round(fS));
      }
      // which part the camera is on; the page is only touched when that changes
      var stop = Math.round(fS / SEG), on = fS > 0 && Math.abs(fS - stop * SEG) < SEG * 0.42 ? stop : 0;
      var done = Math.max(0, Math.min(ticks.length, Math.floor((fS + SEG * 0.42) / SEG)));
      var st = (fS > 0.3 ? 't' : '') + (fS < 1 ? 'f' : '') + on + '.' + done + (ap > 0 && fS < SEG * 0.42 ? 'l' : '');
      if (st !== state) {
        state = st;
        stage.classList.toggle('touring', fS > 0.3);
        stage.classList.toggle('film', fS < 1);
        for (var i = 0; i < steps.length; i++) steps[i].classList.toggle('is-active', on === i + 1);
        for (var j = 0; j < ticks.length; j++) ticks[j].classList.toggle('on', j < done);
        if (lead) lead.classList.toggle('is-active', ap > 0 && fS < SEG * 0.42);
      }
      // films that have been off the canvas for a while give their decoded frames back
      if (++tick % 90 === 0) for (var s in R) if (R[s].hi >= R[s].lo && now - R[s].used > 2500) R[s].free(true);
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
      // a phone that dropped a third of the hero film's frames gets the smaller frames from here on
      if (hd && paceN > 30 && paceSlow / paceN > 0.34) { weak = true; FMAX = 720; measure(); }
      dirs.b = seqDir + 'film/' + (hd && !weak ? '1080/' : '720/');
      R.b.fetchAll(function () {
        R.s.fetchSome(range(N.s, 2));
        R.s.fetchSome(range(N.s, 2, 1));
        R.r.fetchSome(range(N.r, 1));
      });
    }
    R.c.fetchAll(later);
    window.addEventListener('scroll', later, { passive: true, once: true });
    // someone who lands part-way down the page (a #link, a reload) should not come back up to a film in mid-flow
    if (window.pageYOffset > anTop) { ended = true; if (read) read.classList.add('done'); } else play();
    requestAnimationFrame(function (t) { last = t; frame(t); });
  })();

  /* ─── the product lines further down: a canvas with data-film plays its film once, each time its picture comes well into view ─── */
  (function () {
    var cvs = [].slice.call(d.querySelectorAll('canvas[data-film]'));
    if (!cvs.length || !cvs[0].getContext || !('IntersectionObserver' in window)) return;
    var live = [], running = false, last = 0;

    var items = cvs.map(function (cv) {
      var it = { cv: cv, ctx: cv.getContext('2d', { alpha: false }), set: cv.getAttribute('data-film'), n: +cv.getAttribute('data-n') || 59, fps: +cv.getAttribute('data-fps') || 14,
        box: cv.parentNode, host: cv.closest('.line') || cv.parentNode, t: 0, shown: -1, drawn: -1, settled: false, loaded: false, seen: false, max: 720, dir: '' };
      it.reel = new Reel(it.n, function (i) { return it.dir + it.set + pad(i, 3) + '.webp'; });
      return it;
    });
    function load(it) {
      if (it.loaded) return; it.loaded = true;
      var hd = sharp(it.box.getBoundingClientRect().width);
      it.max = hd ? 1080 : 720; it.dir = seqDir + 'film/' + (hd ? '1080/' : '720/');
      it.reel.fetchAll(null, function (k) { if (k === 0) wake(it); });
    }
    function size(it) {
      var px = pixels(it.box.getBoundingClientRect().width, it.max);
      if (px > 0 && it.cv.width !== px) { it.cv.width = px; it.cv.height = px; it.shown = it.drawn = -1; }
    }
    function wake(it) { if (live.indexOf(it) < 0) live.push(it); kick(); }
    function frame(now) {
      if (!live.length) { running = false; return; }
      requestAnimationFrame(frame);
      var dt = Math.min(0.05, (now - last) / 1000 || 0.016), over = null; last = now;
      live.forEach(function (it) {
        // until its picture is well in view a film waits on its first frame, the empty studio
        var i = it.seen ? Math.min(it.n - 1, Math.floor(it.t * it.fps)) : 0;
        if (it.seen && i < it.n - 1 && it.reel.has(i + 1, now)) it.t += dt;   // waits for frames that have not arrived
        if (i !== it.shown || !it.settled) {
          var im = it.reel.at(i, now);
          if (im) {
            if (it.reel.got !== it.drawn) {
              if (it.drawn < 0) size(it);
              if (paint(it.ctx, im, it.cv.width, it.cv.height)) { it.drawn = it.reel.got; it.box.classList.add('on'); }
            }
            it.shown = i; it.settled = it.reel.exact;
          }
        }
        // nothing more to draw: step out of the loop and give the decoded frames back
        if (it.settled && it.shown === (it.seen ? it.n - 1 : 0) && it.drawn === it.shown) { (over || (over = [])).push(it); it.reel.free(); }
      });
      if (over) live = live.filter(function (it) { return over.indexOf(it) < 0; });
    }
    function kick() { if (!running && live.length) { running = true; last = performance.now(); requestAnimationFrame(frame); } }

    var near = new IntersectionObserver(function (en) {
      en.forEach(function (e) { if (e.isIntersecting) { items.forEach(function (it) { if (it.host === e.target) load(it); }); near.unobserve(e.target); } });
    }, { rootMargin: '150% 0px' });
    // the picture has to be well on screen before its film starts; it goes back to the start once it has left
    var seen = new IntersectionObserver(function (en) {
      en.forEach(function (e) {
        items.forEach(function (it) {
          if (it.box !== e.target) return;
          if (e.isIntersecting && e.intersectionRatio >= 0.45) { if (!it.seen) { it.seen = true; it.t = 0; it.shown = -1; it.settled = false; wake(it); } }
          else if (!e.isIntersecting && it.seen) { it.seen = false; it.shown = -1; it.settled = false; wake(it); }
        });
      });
    }, { threshold: [0, 0.45] });
    items.forEach(function (it) { near.observe(it.host); seen.observe(it.box); });
    var rt;
    window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { items.forEach(function (it) { if (it.drawn >= 0) { size(it); if (it.drawn < 0) { it.settled = false; wake(it); } } }); }, 150); });
  })();
})();
