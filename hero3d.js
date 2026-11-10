/* Alaina hero: a procedural 3D cabin damper drawn with plain WebGL (no libraries).
   - Drag to spin it. Scrolling "bumps" it like a real damper.
   - Scrolling into #anatomy stands it upright and pulls the parts apart.
   Falls back to a static photo when WebGL is not available (html.no-gl). */
(function () {
  'use strict';
  var root = document.documentElement;
  var canvas = document.getElementById('gl');
  var stage = document.getElementById('stage');
  if (!canvas || !stage) return;
  var gl = null;
  try {
    gl = canvas.getContext('webgl', { alpha: true, antialias: true, premultipliedAlpha: true, powerPreference: 'high-performance' });
  } catch (e) {}
  if (!gl) { root.classList.add('no-gl'); return; }

  var PI = Math.PI, TAU = PI * 2;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ───────── geometry ───────── */
  function lathe(prof, seg) {
    var v = [], idx = [], i, j;
    for (i = 0; i < prof.length - 1; i++) {
      var a = prof[i], b = prof[i + 1];
      var dr = b[0] - a[0], dy = b[1] - a[1], l = Math.sqrt(dr * dr + dy * dy) || 1;
      var nr = dy / l, ny = -dr / l, base = v.length / 8;
      for (j = 0; j <= seg; j++) {
        var th = j / seg * TAU, c = Math.cos(th), s = Math.sin(th);
        v.push(a[0] * c, a[1], a[0] * s, nr * c, ny, nr * s, j / seg, a[1]);
        v.push(b[0] * c, b[1], b[0] * s, nr * c, ny, nr * s, j / seg, b[1]);
      }
      for (j = 0; j < seg; j++) { var k = base + j * 2; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); }
    }
    return { v: v, idx: idx };
  }
  // Rotate a lathe so its axis lies along Z (a mounting eye), then lift it to y.
  function eyeAt(geo, y) {
    var v = geo.v;
    for (var i = 0; i < v.length; i += 8) {
      var py = v[i + 1], pz = v[i + 2], ny = v[i + 4], nz = v[i + 5];
      v[i + 1] = -pz + y; v[i + 2] = py; v[i + 4] = -nz; v[i + 5] = ny;
    }
    return geo;
  }
  function merge() {
    var v = [], idx = [];
    for (var a = 0; a < arguments.length; a++) {
      var g = arguments[a], base = v.length / 8, i;
      for (i = 0; i < g.v.length; i++) v.push(g.v[i]);
      for (i = 0; i < g.idx.length; i++) idx.push(g.idx[i] + base);
    }
    return { v: v, idx: idx };
  }
  // Coil spring with closed (flat) end coils. Base sits at y = 0.
  function coil(R, r, H, turns, segT, segR) {
    var n = Math.round(turns * segT), ys = [0], i, j, dead = 1.1;
    var tight = 2 * r * 1.03, free = (H - 2 * r - 2 * dead * tight) / (turns - 2 * dead);
    function sm(a, b, x) { x = Math.min(1, Math.max(0, (x - a) / (b - a))); return x * x * (3 - 2 * x); }
    for (i = 1; i <= n; i++) {
      var t = (i - 0.5) / segT;
      var w = sm(dead - 0.35, dead + 0.35, t) * (1 - sm(turns - dead - 0.35, turns - dead + 0.35, t));
      ys.push(ys[i - 1] + (tight + (free - tight) * w) / segT);
    }
    var k = (H - 2 * r) / ys[n];
    var pts = [];
    for (i = 0; i <= n; i++) { var th = i / segT * TAU; pts.push([R * Math.cos(th), r + ys[i] * k, R * Math.sin(th), th]); }
    var v = [], idx = [];
    for (i = 0; i <= n; i++) {
      var p = pts[i], a = pts[Math.max(0, i - 1)], b = pts[Math.min(n, i + 1)];
      var tx = b[0] - a[0], ty = b[1] - a[1], tz = b[2] - a[2], tl = Math.sqrt(tx * tx + ty * ty + tz * tz);
      tx /= tl; ty /= tl; tz /= tl;
      var ex = Math.cos(p[3]), ez = Math.sin(p[3]);
      // B = T x e_r ; N = B x T
      var bx = ty * ez - tz * 0, by = tz * ex - tx * ez, bz = tx * 0 - ty * ex;
      var bl = Math.sqrt(bx * bx + by * by + bz * bz); bx /= bl; by /= bl; bz /= bl;
      var nx = by * tz - bz * ty, ny2 = bz * tx - bx * tz, nz = bx * ty - by * tx;
      for (j = 0; j <= segR; j++) {
        var ph = j / segR * TAU, c = Math.cos(ph), s = Math.sin(ph);
        var ox = c * nx + s * bx, oy = c * ny2 + s * by, oz = c * nz + s * bz;
        v.push(p[0] + ox * r, p[1] + oy * r, p[2] + oz * r, ox, oy, oz, i / n, j / segR);
      }
    }
    var ring = segR + 1;
    for (i = 0; i < n; i++) for (j = 0; j < segR; j++) {
      var q = i * ring + j;
      idx.push(q, q + ring, q + 1, q + 1, q + ring, q + ring + 1);
    }
    return { v: v, idx: idx };
  }

  var SEG = 56;
  function ring() { return lathe([[0.15, -0.19], [0.31, -0.19], [0.35, -0.15], [0.35, 0.15], [0.31, 0.19], [0.15, 0.19], [0.15, -0.19]], 44); }
  function bush() { return lathe([[0.075, -0.215], [0.15, -0.215], [0.15, 0.215], [0.075, 0.215], [0.075, -0.215]], 32); }
  var G = {
    eyeL: merge(eyeAt(ring(), -2.0), lathe([[0, -1.74], [0.17, -1.74], [0.17, -1.44], [0.3, -1.4], [0.3, -1.34], [0, -1.34]], 36)),
    bushL: eyeAt(bush(), -2.0),
    body: lathe([[0.2, -1.36], [0.63, -1.36], [0.67, -1.33], [0.67, -1.29], [0.62, -1.26], [0.37, -1.26], [0.37, -1.19], [0.31, -1.17],
      [0.31, 0.2], [0.28, 0.25], [0.15, 0.27], [0.15, 0.31], [0.11, 0.33], [0, 0.33]], SEG),
    spring: coil(0.485, 0.078, 1.9, 7.2, 30, 12),
    rod: lathe([[0, -0.4], [0.092, -0.4], [0.092, 1.52], [0, 1.52]], 32),
    can: lathe([[0.52, 0.5], [0.6, 0.5], [0.63, 0.53], [0.63, 1.32], [0.57, 1.43], [0.26, 1.5], [0.21, 1.55], [0.21, 1.62], [0, 1.62]], SEG),
    canIn: lathe([[0.52, 1.36], [0.52, 0.5]], SEG),
    band: lathe([[0.636, 0.6], [0.642, 0.605], [0.642, 0.665], [0.636, 0.67]], SEG),
    eyeT: merge(eyeAt(ring(), 2.0), lathe([[0, 1.6], [0.17, 1.6], [0.17, 1.74], [0, 1.74]], 36)),
    bushT: eyeAt(bush(), 2.0)
  };
  var BLK = [0.02, 0.02, 0.024], SATIN = [0.045, 0.046, 0.052], CHROME = [0.93, 0.94, 0.96], BRASS = [0.98, 0.68, 0.26], ORANGE = [1.0, 0.27, 0.08];
  //            geo      color  metal rough group decal emis
  var PARTS = [
    ['eyeL', BLK, 0, 0.34, 0, 0, 0], ['bushL', BRASS, 1, 0.28, 0, 0, 0],
    ['body', SATIN, 0, 0.42, 1, 0, 0],
    ['spring', BLK, 0, 0.2, 2, 0, 0],
    ['rod', CHROME, 1, 0.06, 3, 0, 0],
    ['can', SATIN, 0, 0.36, 4, 1, 0], ['canIn', BLK, 0, 0.8, 4, 0, 0], ['band', ORANGE, 0, 0.4, 4, 0, 0.55],
    ['eyeT', BLK, 0, 0.34, 5, 0, 0], ['bushT', BRASS, 1, 0.28, 5, 0, 0]
  ];
  var EXPLODE = [-0.45, 0, 1.7, 1.75, 2.75, 3.15];
  var ANCHOR = [-2.0, -0.5, -0.32, 0.75, 0.95, 2.0];
  var SPRING_BASE = -1.26, SPRING_H = 1.9;

  /* ───────── shaders ───────── */
  var VS = 'attribute vec3 aP;attribute vec3 aN;attribute vec2 aU;' +
    'uniform mat3 uR;uniform vec3 uOff;uniform vec3 uScl;uniform float uS;uniform float uD;uniform vec2 uProj;uniform vec2 uShift;' +
    'varying vec3 vN;varying vec3 vP;varying vec2 vU;' +
    'void main(){vec3 p=uR*(aP*uScl+uOff)*uS;p.z-=uD;vP=p;vN=uR*(aN/uScl);vU=aU;' +
    'vec4 c=vec4(p.x*uProj.x,p.y*uProj.y,(-p.z-uD)*0.25*(-p.z),-p.z);c.xy+=uShift*c.w;gl_Position=c;}';
  var FS = 'precision highp float;varying vec3 vN;varying vec3 vP;varying vec2 vU;' +
    'uniform vec3 uCol;uniform float uMetal;uniform float uRough;uniform float uDecal;uniform float uEmis;uniform sampler2D uTex;' +
    'vec3 env(vec3 r,float rough){float w=mix(0.05,0.62,rough);float az=atan(r.x,r.z);' +
    'float top=smoothstep(0.5-w,0.96,r.y);' +
    'float s1=exp(-pow((az+0.85)/(0.09+w*0.7),2.0))*smoothstep(-0.75,0.1,r.y);' +
    'float s2=exp(-pow((az-1.3)/(0.1+w*0.7),2.0))*smoothstep(-0.85,0.0,r.y);' +
    'float rim=exp(-pow((abs(az)-2.55)/(0.32+w),2.0));' +
    'vec3 c=vec3(0.012,0.013,0.016)+vec3(0.02,0.022,0.03)*(r.y*0.5+0.5);' +
    'c+=vec3(1.0,0.98,0.95)*top*0.42;c+=vec3(1.0,0.99,0.97)*s1*6.5;c+=vec3(1.0,0.3,0.07)*s2*5.0;c+=vec3(0.45,0.66,1.0)*rim*1.3;return c;}' +
    'void main(){vec3 n=normalize(vN);vec3 v=normalize(-vP);if(dot(n,v)<0.0)n=-n;' +
    'vec3 base=uCol;float rough=uRough;' +
    'if(uDecal>0.5){float t=fract(vU.x*2.0+0.25);vec2 d=vec2((vU.y-0.7)/0.56,(t-0.5)*3.1+0.5);' +
    'if(d.x>0.0&&d.x<1.0&&d.y>0.0&&d.y<1.0){vec4 k=texture2D(uTex,d);base=mix(base,k.rgb,k.a);rough=mix(rough,0.55,k.a);}}' +
    'vec3 r=reflect(-v,n);float ndv=max(dot(n,v),0.0);' +
    'vec3 f0=mix(vec3(0.045),base,uMetal);vec3 F=f0+(1.0-f0)*pow(1.0-ndv,5.0)*(1.0-rough*0.55);' +
    'float d1=max(dot(n,normalize(vec3(-0.5,0.7,0.6))),0.0);float d2=max(dot(n,normalize(vec3(0.85,0.1,0.35))),0.0);' +
    'vec3 diff=base*(0.1+1.1*d1+vec3(1.0,0.45,0.2)*0.5*d2)*(1.0-uMetal);' +
    'vec3 col=diff+env(r,rough)*F+base*uEmis;col=col/(1.0+col*0.75);col=pow(col,vec3(0.4545));gl_FragColor=vec4(col,1.0);}';

  function sh(type, src) {
    var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  var prog, U = {};
  try {
    prog = gl.createProgram();
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FS));
    gl.bindAttribLocation(prog, 0, 'aP'); gl.bindAttribLocation(prog, 1, 'aN'); gl.bindAttribLocation(prog, 2, 'aU');
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  } catch (e) { root.classList.add('no-gl'); return; }
  gl.useProgram(prog);
  ['uR', 'uOff', 'uScl', 'uS', 'uD', 'uProj', 'uShift', 'uCol', 'uMetal', 'uRough', 'uDecal', 'uEmis', 'uTex'].forEach(function (n) { U[n] = gl.getUniformLocation(prog, n); });

  PARTS.forEach(function (p) {
    var g = G[p[0]], vb = gl.createBuffer(), ib = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(g.v), gl.STATIC_DRAW);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(g.idx), gl.STATIC_DRAW);
    p.push(vb, ib, g.idx.length);
  });
  G = null;

  /* ───────── decal: wordmark painted on the dust shield ───────── */
  var tex = gl.createTexture();
  function paintDecal() {
    var c = document.createElement('canvas'); c.width = 1024; c.height = 256;
    var x = c.getContext('2d');
    x.clearRect(0, 0, 1024, 256);
    x.fillStyle = '#f4f3ef'; x.textBaseline = 'alphabetic'; x.textAlign = 'center';
    x.font = '800 150px Archivo, "Arial Black", Arial, sans-serif';
    try { x.fontStretch = '120%'; x.letterSpacing = '6px'; } catch (e) {}
    x.fillText('ALAINA', 512, 150);
    x.fillStyle = '#ff4a1a';
    x.beginPath(); x.moveTo(150, 186); x.lineTo(874, 172); x.lineTo(868, 192); x.lineTo(144, 204); x.closePath(); x.fill();
    x.fillStyle = 'rgba(244,243,239,.8)'; x.font = '500 30px "JetBrains Mono", monospace';
    try { x.fontStretch = '100%'; x.letterSpacing = '14px'; } catch (e) {}
    x.fillText('PRECISION DAMPING', 512, 240);
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    dirty = true;
  }
  var dirty = true;
  paintDecal();
  if (document.fonts && document.fonts.load) {
    Promise.all([document.fonts.load('800 150px Archivo'), document.fonts.load('500 30px "JetBrains Mono"')]).then(paintDecal, function () {});
  }

  /* ───────── state ───────── */
  var W = 0, H = 0, dpr = 1, phone = false;
  var spin = 0.6, spinVel = 0.32, pitchUser = 0, dragging = false, lastX = 0, lastY = 0;
  var comp = 0.12, compVel = 0, lastScroll = window.pageYOffset, lastT = 0;
  var steps = [].slice.call(document.querySelectorAll('.an-steps li'));
  var anatomy = document.getElementById('anatomy');
  var dot = document.querySelector('.an-dot'), bar = document.querySelector('.an-bar');
  var activeStep = -1, visible = true, FOV = Math.tan(14 * PI / 180), D = 10;
  var cta = document.querySelector('.hero-cta-row'), zoneY = -0.46, tiltA = -1.19, hPhoneB = 0.5, yPhoneB = 0.16;

  function resize() {
    var r = canvas.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = Math.max(1, Math.round(r.width)); H = Math.max(1, Math.round(r.height));
    phone = W < 861;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    gl.viewport(0, 0, canvas.width, canvas.height);
    if (phone && cta) {
      // hero: fit the damper into the gap between the buttons and the dock
      var top = cta.getBoundingClientRect().bottom - stage.getBoundingClientRect().top + 8;
      var bottom = H - 92 - (stage.getBoundingClientRect().top + window.pageYOffset), zh = Math.max(120, bottom - top), len = 0.94 * W;
      var sn = Math.max(0.1, Math.min(0.37, zh / len - 0.27));
      tiltA = -(PI / 2 - Math.asin(sn));
      zoneY = 1 - (Math.min(top, bottom - 120) + bottom) / H;
      // anatomy: stand it between the header and the caption card
      var pin = document.querySelector('.an-pin'), list = document.querySelector('.an-steps');
      if (pin && list) {
        var zt = 86, zb = list.getBoundingClientRect().top - pin.getBoundingClientRect().top - 14;
        if (zb - zt > 160) { hPhoneB = (zb - zt) / H * 0.96; yPhoneB = 1 - (zt + zb) / H; }
      }
    }
    dirty = true;
  }
  window.addEventListener('resize', resize, { passive: true });
  resize();

  canvas.addEventListener('pointerdown', function (e) {
    dragging = true; lastX = e.clientX; lastY = e.clientY;
    try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
    compVel += 0.9;
  });
  canvas.addEventListener('pointermove', function (e) {
    if (!dragging) return;
    var dx = e.clientX - lastX, dy = e.clientY - lastY; lastX = e.clientX; lastY = e.clientY;
    spinVel = dx * 0.45; spin += dx * 0.011;
    if (e.pointerType === 'mouse') pitchUser = Math.max(-0.45, Math.min(0.45, pitchUser + dy * 0.004));
  });
  function drop() { dragging = false; }
  canvas.addEventListener('pointerup', drop); canvas.addEventListener('pointercancel', drop); canvas.addEventListener('pointerleave', drop);

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) kick(); }, { rootMargin: '80px' }).observe(stage);
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) kick(); });

  function sm(a, b, x) { x = Math.min(1, Math.max(0, (x - a) / (b - a))); return x * x * (3 - 2 * x); }
  function mix(a, b, t) { return a + (b - a) * t; }

  /* ───────── frame ───────── */
  var raf = 0;
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }
  function frame(now) {
    raf = 0;
    if (!visible || document.hidden) return;
    var dt = Math.min(0.05, (now - lastT) / 1000 || 0.016); lastT = now;

    // scroll: hero progress, anatomy progress, and a bump for the damper
    var sy = window.pageYOffset, dScroll = sy - lastScroll; lastScroll = sy;
    var vh = window.innerHeight;
    var st = stage.getBoundingClientRect();
    var heroT = sm(0.05, 0.92, -st.top / vh);
    var p = 0;
    if (anatomy && !root.classList.contains('no-gl')) {
      var ar = anatomy.getBoundingClientRect();
      p = Math.min(1, Math.max(0, -ar.top / Math.max(1, ar.height - vh)));
    }
    var e = sm(0.0, 0.1, p) * (1 - sm(0.8, 0.93, p));

    // damper physics: a spring-mass that scroll and taps disturb
    compVel += Math.max(-60, Math.min(60, dScroll)) * 0.03;
    var rest = reduce ? 0.12 : 0.13 + 0.05 * Math.sin(now * 0.0011);
    compVel += (-(comp - rest) * 70 - compVel * 7.5) * dt;
    comp += compVel * dt;
    comp = Math.max(-0.03, Math.min(0.42, comp));
    var c = comp * (1 - e);

    if (!dragging) {
      var idle = reduce ? 0 : mix(0.32, 0.5, heroT);
      spinVel += (idle - spinVel) * Math.min(1, dt * 2.2);
      spin += spinVel * dt;
    }

    // pose: hero (lying diagonally) → anatomy (upright)
    var aA = phone ? tiltA : -0.96, aB = phone ? 0 : -0.1;
    var shA = phone ? [0.04, zoneY] : [0.4, -0.03], shB = phone ? [0.36, yPhoneB] : [0.34, 0.0];
    var hA = phone ? 0.94 * W / H : 0.92, hB = phone ? hPhoneB : 0.8;
    if (W / H > 1.9) hA = 0.8;
    var alpha = mix(aA, aB, heroT), hfrac = mix(hA, hB, heroT);
    var shx = mix(shA[0], shB[0], heroT), shy = mix(shA[1], shB[1], heroT);
    var pitch = mix(-0.36, -0.22, heroT) + pitchUser * (1 - heroT);
    var L = 4.68 + 3.6 * e, yc = 1.35 * e - c * 0.5 * (1 - e);
    var S = hfrac * 2 * FOV * D / L;

    // R = Rz(alpha) * Rx(pitch) * Ry(spin), column-major mat3
    var ca = Math.cos(alpha), sa = Math.sin(alpha), cp = Math.cos(pitch), sp = Math.sin(pitch), cs = Math.cos(spin), ss = Math.sin(spin);
    var m00 = cs, m01 = 0, m02 = ss, m10 = sp * ss, m11 = cp, m12 = -sp * cs, m20 = -cp * ss, m21 = sp, m22 = cp * cs;
    var R = new Float32Array([
      ca * m00 - sa * m10, sa * m00 + ca * m10, m20,
      ca * m01 - sa * m11, sa * m01 + ca * m11, m21,
      ca * m02 - sa * m12, sa * m02 + ca * m12, m22
    ]);

    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST); gl.disable(gl.CULL_FACE);
    gl.uniformMatrix3fv(U.uR, false, R);
    gl.uniform1f(U.uS, S); gl.uniform1f(U.uD, D);
    gl.uniform2f(U.uProj, 1 / (FOV * (W / H)), 1 / FOV);
    gl.uniform2f(U.uShift, shx, shy);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(U.uTex, 0);
    gl.enableVertexAttribArray(0); gl.enableVertexAttribArray(1); gl.enableVertexAttribArray(2);

    for (var i = 0; i < PARTS.length; i++) {
      var q = PARTS[i], g = q[4], off = EXPLODE[g] * e - yc - (g >= 3 ? c : 0), scy = 1;
      if (q[0] === 'spring') { scy = (SPRING_H - c) / SPRING_H; off += SPRING_BASE; }
      gl.uniform3f(U.uOff, 0, off, 0); gl.uniform3f(U.uScl, 1, scy, 1);
      gl.uniform3fv(U.uCol, q[1]); gl.uniform1f(U.uMetal, q[2]); gl.uniform1f(U.uRough, q[3]);
      gl.uniform1f(U.uDecal, q[5]); gl.uniform1f(U.uEmis, q[6]);
      gl.bindBuffer(gl.ARRAY_BUFFER, q[7]);
      gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 32, 0);
      gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 32, 12);
      gl.vertexAttribPointer(2, 2, gl.FLOAT, false, 32, 24);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, q[8]);
      gl.drawElements(gl.TRIANGLES, q[9], gl.UNSIGNED_SHORT, 0);
    }
    if (dirty) { dirty = false; canvas.classList.add('ready'); }

    // anatomy captions + hot spot
    if (steps.length) {
      var step = p >= 0.81 ? 5 : Math.max(0, Math.min(4, Math.floor((p - 0.06) / 0.15)));
      if (step !== activeStep) {
        activeStep = step;
        for (var k = 0; k < steps.length; k++) steps[k].classList.toggle('is-active', k === step);
      }
      if (bar) bar.style.setProperty('--anp', p.toFixed(3));
      if (dot) {
        var on = e > 0.55 && step < 5;
        if (on) {
          var ay = ANCHOR[step] + EXPLODE[step] * e - yc;
          var vx = R[3] * ay * S, vy = R[4] * ay * S, vz = R[5] * ay * S - D;
          var nx = vx / (FOV * (W / H)) / -vz + shx, ny = vy / FOV / -vz + shy;
          dot.style.transform = 'translate(' + ((nx * 0.5 + 0.5) * W).toFixed(1) + 'px,' + ((0.5 - ny * 0.5) * H).toFixed(1) + 'px)';
        }
        dot.classList.toggle('on', on);
      }
    }
    kick();
  }
  kick();
  window.AlainaDamper = { spin: function (v) { spin = v; spinVel = 0; dragging = true; } };
})();
