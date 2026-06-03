document.documentElement.classList.add('js');

/* PROGRESS BAR */
const bar=document.getElementById('bar');
addEventListener('scroll',()=>{bar.style.width=(scrollY/(document.body.scrollHeight-innerHeight)*100)+'%'},{passive:true});

/* NAV STICK */
const nav=document.getElementById('nav');
addEventListener('scroll',()=>nav.classList.toggle('stuck',scrollY>40),{passive:true});

/* REVEAL */
const obs=new IntersectionObserver((es)=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');obs.unobserve(e.target)}}),{threshold:.15});
document.querySelectorAll('[data-reveal]').forEach(el=>obs.observe(el));
setTimeout(()=>document.querySelectorAll('[data-reveal]:not(.in)').forEach(el=>el.classList.add('in')),3000);

/* STAT COUNTERS */
function up(el,t){let n=0,s=Math.max(1,Math.ceil(t/45));const iv=setInterval(()=>{n=Math.min(n+s,t);el.textContent=n;if(n>=t)clearInterval(iv)},26)}
const sObs=new IntersectionObserver((es)=>es.forEach(e=>{if(e.isIntersecting){e.target.querySelectorAll('[data-count]').forEach(el=>up(el,+el.dataset.count));sObs.unobserve(e.target)}}),{threshold:.4});
sObs.observe(document.getElementById('statsGrid'));

/* ASSEMBLY SEQUENCE */
const STEPS=[
 ['Parts Ready','Every precision component laid out before assembly — piston, seals, springs, mounts, and the damper body.'],
 ['Seal & Oil Seal','High-performance oil seals pressed into the body, engineered for over a million compression cycles without leakage.'],
 ['Piston Rod Inserted','The chrome-plated piston rod slid into the cylinder with zero-tolerance alignment for consistent damping force.'],
 ['Coil Spring Fitted','The precision-wound coil spring seated around the body — rated for the exact load range of the application.'],
 ['Top Mount Fixed','The top mount assembly torqued to specification, completing the connection between damper and chassis.'],
 ['Shocker Assembled','A fully assembled Alaina shocker, ready for quality inspection before dispatch to the fitment stage.'],
 ['Shocker Installed','The unit mounted into the wheel arch, connecting knuckle, brake, and suspension geometry in one step.'],
 ['Wheel Fitted','The wheel refitted and torqued — the shocker now sits live in the suspension, carrying full vehicle weight.'],
 ['Smooth Performance','On the road the damper absorbs every input — potholes, undulations, hard stops — invisibly and consistently.'],
 ['Driving Smoothly','From raw components to confident driving. This is what every Alaina shocker is built to deliver, kilometre after kilometre.']
];

const asmSec=document.getElementById('assembly'),
      dots=document.querySelectorAll('.asm-dot'),
      aNum=document.getElementById('asmNum'),
      aLab=document.getElementById('asmLabel'),
      aDesc=document.getElementById('asmDesc'),
      aFill=document.getElementById('asmFill'),
      aUi=document.getElementById('asmUi'),
      glow=document.getElementById('asmGlow'),
      rig=document.getElementById('rig'),
      unitWrap=document.getElementById('unitWrap'),
      gBody=document.getElementById('gBody'),
      gEye=document.getElementById('gEye'),
      gSeatL=document.getElementById('gSeatL'),
      gRod=document.getElementById('gRod'),
      gSeatU=document.getElementById('gSeatU'),
      gMount=document.getElementById('gMount'),
      gTop=document.getElementById('gTop'),
      gSpring=document.getElementById('gSpring'),
      scene=document.getElementById('scene'),
      chassis=document.getElementById('chassis'),
      spokesG=document.getElementById('spokes'),
      roadDash=document.getElementById('roadDash'),
      speed=document.getElementById('speed'),
      gThreads=document.getElementById('gThreads'),
      gBoot=document.getElementById('gBoot'),
      discHoles=document.getElementById('discHoles');

/* ── generate detail parts ── */
const SPR_TOP=330, SPR_BOT=596, COILS=9, RX=68, RY=16;
const SPRH=SPR_BOT-SPR_TOP, GAP=SPRH/(COILS-1);
(function(){
  /* COIL SPRING — 5-layer realistic 3D coil */
  let s='';
  for(let i=0;i<COILS;i++){
    const cy=SPR_TOP+i*GAP;
    s+=`<ellipse cx="183" cy="${(cy+RY+5).toFixed(1)}" rx="${RX-4}" ry="${Math.round(RY*0.45)}" fill="rgba(0,0,0,0.38)"/>`;
    s+=`<path d="M ${180+RX} ${cy} A ${RX} ${RY} 0 0 1 ${180-RX} ${cy}" fill="none" stroke="url(#gCoilDk)" stroke-width="18" stroke-linecap="round"/>`;
    s+=`<path d="M ${180-RX} ${cy} A ${RX} ${RY} 0 0 0 ${180+RX} ${cy}" fill="none" stroke="url(#gCoil)" stroke-width="18" stroke-linecap="round"/>`;
    s+=`<path d="M ${180-RX+20} ${cy-4} A ${RX-20} ${RY-5} 0 0 0 ${180+RX-20} ${cy-4}" fill="none" stroke="rgba(255,165,90,0.68)" stroke-width="3.5" stroke-linecap="round"/>`;
    s+=`<path d="M ${180-RX+8} ${cy+2} A ${RX-8} ${RY-3} 0 0 0 ${180+RX-8} ${cy+2}" fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="1.5" stroke-linecap="round"/>`;
  }
  gSpring.innerHTML=s;

  /* THREAD DETAIL on lower body */
  let t='';
  for(let y=488;y<=576;y+=10){
    t+=`<rect x="153" y="${y}" width="54" height="2.5" rx="1" fill="rgba(0,0,0,0.38)"/>`;
    t+=`<rect x="153" y="${y+2}" width="54" height="1" rx="0.5" fill="rgba(255,255,255,0.055)"/>`;
  }
  gThreads.innerHTML=t;

  /* DUST BOOT — accordion bellows with depth */
  let bt='';
  for(let y=182;y<=290;y+=16){
    bt+=`<ellipse cx="180" cy="${y}" rx="22" ry="9" fill="url(#gRubber)" stroke="#0a0b0e" stroke-width="1.5"/>`;
    bt+=`<ellipse cx="180" cy="${y+8}" rx="15" ry="5" fill="#0e0f13" stroke="#1a1b20" stroke-width="1"/>`;
    bt+=`<ellipse cx="180" cy="${y}" rx="22" ry="9" fill="none" stroke="rgba(255,255,255,0.045)" stroke-width="1"/>`;
  }
  gBoot.innerHTML=bt;

  /* WHEEL SPOKES */
  let sk='';
  for(let i=0;i<5;i++){
    const angle=i*72;
    sk+=`<rect x="183" y="510" width="24" height="86" rx="7" fill="url(#gRim)" stroke="#0a0c10" stroke-width="2" transform="rotate(${angle} 195 610)"/>`;
    sk+=`<rect x="188" y="515" width="8" height="76" rx="4" fill="rgba(255,255,255,0.09)" transform="rotate(${angle} 195 610)"/>`;
  }
  spokesG.innerHTML=sk;

  /* BRAKE DISC HOLES */
  let dh='';
  for(let i=0;i<10;i++){
    const a=i/10*2*Math.PI, x=195+48*Math.cos(a), y=610+48*Math.sin(a);
    dh+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4" fill="#14161c"/>`;
  }
  for(let i=0;i<5;i++){
    const a=i/5*2*Math.PI+0.3, x=195+60*Math.cos(a), y=610+60*Math.sin(a);
    dh+=`<rect x="${(x-2).toFixed(1)}" y="${(y-7).toFixed(1)}" width="4" height="14" rx="2" fill="#1a1c22" transform="rotate(${(a*180/Math.PI).toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)})"/>`;
  }
  discHoles.innerHTML=dh;
})();

const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const seg=(p,a,b)=>clamp((p-a)/(b-a),0,1);
const eo=t=>1-Math.pow(1-t,3);
function setG(el,dy,op){el.setAttribute('transform',`translate(0 ${dy})`);el.setAttribute('opacity',op);}

function frame(p){
  /* ── PHASE 1: BUILD (0 – .50) ── */
  const b=eo(seg(p,0,.10));    setG(gBody,(1-b)*-130,b);
  const e=eo(seg(p,.03,.12));  setG(gEye,(1-e)*90,e);
  const sl=eo(seg(p,.16,.24)); setG(gSeatL,(1-sl)*-50,sl);
  const rd=eo(seg(p,.10,.22)); setG(gRod,(1-rd)*200,rd);
  const su=eo(seg(p,.30,.38)); setG(gSeatU,(1-su)*-34,su);
  const mt=eo(seg(p,.40,.52)); setG(gMount,(1-mt)*-190,mt);
  const sp=eo(seg(p,.22,.40));

  /* ── PHASE 3: WORKING stroke (.72 – 1) ── */
  const w=seg(p,.72,1);
  let d=0,sy=1;
  if(w>0){ d=((1-Math.cos(w*5*Math.PI))/2)*32; sy=(SPRH-d)/SPRH; }
  gTop.setAttribute('transform',`translate(0 ${d})`);

  const spDy=(1-sp)*-215;
  gSpring.setAttribute('opacity',sp);
  gSpring.setAttribute('transform',`translate(0 ${spDy}) translate(0 ${SPR_BOT}) scale(1 ${sy}) translate(0 ${-SPR_BOT})`);

  /* assembled pop at end of build */
  const pop=seg(p,.46,.58), ps=1+0.03*Math.sin(pop*Math.PI);
  rig.setAttribute('transform',`translate(180 400) scale(${ps}) translate(-180 -400)`);

  /* ── PHASE 2: FITMENT (.50 – .72) ── */
  const f=eo(seg(p,.50,.72));
  const si=1-0.30*f, tyU=10*f;
  unitWrap.setAttribute('transform',`translate(0 ${tyU}) translate(180 400) scale(${si}) translate(-180 -400)`);

  /* scene fade-in; chassis bobs during working */
  scene.setAttribute('opacity',clamp(seg(p,.50,.64),0,1));
  const sceneDy=(1-f)*26;
  scene.setAttribute('transform',`translate(0 ${sceneDy})`);
  chassis.setAttribute('transform',`translate(0 ${d})`);

  /* ── PHASE 3: WORKING visuals ── */
  spokesG.setAttribute('transform',`rotate(${w*1080} 195 610)`);
  roadDash.setAttribute('transform',`translate(${-((w*420)%80)} 0)`);
  speed.setAttribute('opacity',(clamp(seg(p,.74,.84),0,1)*0.85*(0.5+0.5*Math.sin(w*8*Math.PI))).toFixed(3));

  glow.style.opacity=(seg(p,.46,.62)*0.8)*(w>0?(.5+.5*((1-Math.cos(w*4*Math.PI))/2)):1);
}

let burstAsm=function(){};

/* ── CANVAS PARTICLE OVERLAY ── */
(function(){
  const cvs=document.getElementById('asmCanvas');
  if(!cvs) return;
  const ctx=cvs.getContext('2d');
  let W,H,cx,cy;
  const particles=[];
  let lastIdx=-1, pulseT=0, currentP=0, t=0;

  function resize(){
    W=cvs.offsetWidth; H=cvs.offsetHeight;
    cvs.width=W; cvs.height=H;
    cx=W*0.75; cy=H*0.50;
  }
  resize();
  addEventListener('resize',resize);

  function Particle(x,y,type){
    this.x=x;this.y=y;
    this.vx=(Math.random()-0.5)*4;
    this.vy=(Math.random()-2.2)*3.5;
    this.life=1;this.decay=0.018+Math.random()*0.022;
    this.r=1.5+Math.random()*3;this.type=type;
  }
  Particle.prototype.update=function(){this.vy+=0.12;this.x+=this.vx;this.y+=this.vy;this.vx*=0.97;this.life-=this.decay;};
  Particle.prototype.draw=function(){
    const a=Math.max(0,this.life);
    if(this.type==='spark'){
      ctx.save();ctx.globalAlpha=a;
      ctx.strokeStyle=`rgba(255,${100+Math.floor(100*a)},0,${a})`;
      ctx.lineWidth=this.r*0.6;ctx.beginPath();
      ctx.moveTo(this.x,this.y);ctx.lineTo(this.x-this.vx*4,this.y-this.vy*4);ctx.stroke();ctx.restore();
    } else {
      ctx.save();ctx.globalAlpha=a*0.5;
      ctx.fillStyle=`rgba(255,${150+Math.floor(80*a)},50,1)`;
      ctx.beginPath();ctx.arc(this.x,this.y,this.r,0,Math.PI*2);ctx.fill();ctx.restore();
    }
  };

  function burst(n){
    const bx=cx+(Math.random()-0.5)*80, by=cy+(Math.random()-0.5)*120;
    for(let i=0;i<n;i++) particles.push(new Particle(bx,by,'spark'));
    for(let i=0;i<Math.floor(n/2);i++) particles.push(new Particle(bx,by,'dust'));
    pulseT=1;
  }

  function drawOrbit(){
    const R=Math.min(W,H)*0.22, N=6;
    for(let i=0;i<N;i++){
      const a=(i/N)*Math.PI*2+t*0.4;
      const x=cx+Math.cos(a)*R, y=cy+Math.sin(a)*R*0.55;
      const fade=0.3+0.3*Math.sin(t*1.2+i);
      ctx.save();ctx.globalAlpha=fade;ctx.fillStyle='#FF4D00';
      ctx.beginPath();ctx.arc(x,y,2.5,0,Math.PI*2);ctx.fill();ctx.restore();
    }
  }

  function drawPulse(){
    if(pulseT<=0)return;
    const r=(1-pulseT)*Math.min(W,H)*0.28;
    ctx.save();ctx.globalAlpha=pulseT*0.6;
    ctx.strokeStyle='#FF4D00';ctx.lineWidth=2;
    ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();ctx.restore();
    pulseT-=0.022;
  }

  function loop(){
    requestAnimationFrame(loop);
    ctx.clearRect(0,0,W,H);
    t+=0.016;
    drawOrbit();drawPulse();
    for(let i=particles.length-1;i>=0;i--){
      particles[i].update();particles[i].draw();
      if(particles[i].life<=0) particles.splice(i,1);
    }
  }
  loop();

  /* expose burst to outer scope */
  burstAsm=burst;
})();

/* ── strut scroll driver ── */
let curIdx=-1;
function narrate(p){
  aFill.style.width=(p*100)+'%';
  const idx=Math.min(9,Math.floor(p*9.999));
  dots.forEach((d,i)=>d.classList.toggle('on',i===idx));
  if(idx===curIdx)return;
  curIdx=idx; burstAsm(26);
  aUi.classList.add('asm-changing');
  setTimeout(()=>{
    aNum.textContent=String(idx+1).padStart(2,'0');
    aLab.textContent=STEPS[idx][0];
    aDesc.textContent=STEPS[idx][1];
    aUi.classList.remove('asm-changing');
  },220);
}
function asmStartTimer(){}
function asmStopTimer(){}
let ticking=false;
function onScroll(){
  if(ticking)return;ticking=true;
  requestAnimationFrame(()=>{
    const r=asmSec.getBoundingClientRect();
    const total=asmSec.offsetHeight-innerHeight;
    const p=clamp((-r.top)/total,0,1);
    frame(p);narrate(p);ticking=false;
  });
}
addEventListener('scroll',onScroll,{passive:true});
addEventListener('resize',onScroll);
frame(0);narrate(0);

/* ═══════════════════════════════════════════════════
   CABIN DAMPER ASSEMBLY ANIMATION
═══════════════════════════════════════════════════ */
(function(){
  const CAB_STEPS=[
    ['Cylinder Prepared',    'The outer tube precision-bored and cleaned — every micron matters for consistent damping force over a million cycles.'],
    ['Inner Tube Inserted',  'Twin-tube construction: the inner cylinder pressed inside the outer, creating the primary working chamber for the piston.'],
    ['Oil Fill',             'VG46 hydraulic oil filled to the exact specification — volume and viscosity directly determine damping response.'],
    ['Piston Rod Inserted',  'The hard-chrome piston rod — Ra ≤ 0.2μm surface finish — slid through the rod guide with zero-tolerance alignment.'],
    ['Seal Pack Pressed',    'Dual-lip NBR seals torqued into position, rated for over a million full-stroke cycles without leakage under Indian road conditions.'],
    ['Dust Boot Fitted',     'A thermoplastic rubber accordion boot snapped over the exposed rod — blocking dust, water, and road debris from the seal face.'],
    ['Top Eye Mounted',      'The forged mounting eye welded and pressure-tested — connecting the damper to the cab frame at its rated load capacity.'],
    ['Damper Complete',      'The fully assembled cabin damper pressure-tested at 15 BAR. Zero leaks. Force curve verified. Ready for dispatch.'],
    ['Cab Mounted',          'The unit bolted between the cab floor bracket and chassis rail — isolating the cab from engine vibration and road shock.'],
    ['Cabin Stable',         'At speed, over potholes, under full payload — the Alaina cabin damper keeps the driver\'s environment smooth. Every kilometre.']
  ];

  const cabSec  = document.getElementById('cab-assembly');
  if(!cabSec) return;

  const cabDots = cabSec.querySelectorAll('.asm-dot'),
        cabNum  = document.getElementById('cabNum'),
        cabLab  = document.getElementById('cabLabel'),
        cabDesc = document.getElementById('cabDesc'),
        cabFill = document.getElementById('cabFill'),
        cabUi   = document.getElementById('cabUi'),
        cabGlow = document.getElementById('cabGlow'),
        cRig    = document.getElementById('cRig'),
        cUnitWrap=document.getElementById('cUnitWrap'),
        cBody   = document.getElementById('cBody'),
        cEyeBot = document.getElementById('cEyeBot'),
        cSealPack=document.getElementById('cSealPack'),
        cRod    = document.getElementById('cRod'),
        cBoot   = document.getElementById('cBoot'),
        cEyeTop = document.getElementById('cEyeTop'),
        cTop    = document.getElementById('cTop'),
        cScene  = document.getElementById('cScene'),
        cTruck  = document.getElementById('cTruck'),
        cRoadDash=document.getElementById('cRoadDash'),
        cSpeed  = document.getElementById('cSpeed');

  /* ── generate cabin boot rings (minimal — cabin dampers have light boot) ── */
  (function(){
    let bt='';
    cBoot.innerHTML=''; /* cabin dampers have no visible boot */
  })();

  const clampC=(v,a,b)=>Math.max(a,Math.min(b,v));
  const segC=(p,a,b)=>clampC((p-a)/(b-a),0,1);
  const eoC=t=>1-Math.pow(1-t,3);
  function setGC(el,dy,op){el.setAttribute('transform',`translate(0 ${dy})`);el.setAttribute('opacity',op);}

  /* stroke travel for working phase */
  const STROKE=100;

  function cabFrame(p){
    /* PHASE 1: BUILD (0 – 0.50) */
    const b  = eoC(segC(p,0,.10));    setGC(cBody,    (1-b)*-160, b);
    const eb = eoC(segC(p,.04,.14));  setGC(cEyeBot,  (1-eb)*80,  eb);
    const sp = eoC(segC(p,.14,.24));  setGC(cSealPack,(1-sp)*-50, sp);
    const rd = eoC(segC(p,.10,.22));  setGC(cRod,     (1-rd)*240, rd);
    const et = eoC(segC(p,.36,.50));  setGC(cEyeTop,  (1-et)*-220,et);

    /* boot fades in with rod */
    cBoot.setAttribute('opacity', segC(p,.26,.40));

    /* assembled bounce at end of build */
    const pop=segC(p,.48,.60), ps=1+0.025*Math.sin(pop*Math.PI);
    cRig.setAttribute('transform',`translate(180 400) scale(${ps}) translate(-180 -400)`);

    /* PHASE 2: FITMENT (0.50 – 0.72) — unit scales into truck */
    const f  = eoC(segC(p,.50,.72));
    const si = 1-0.28*f, tyU=8*f;
    cUnitWrap.setAttribute('transform',
      `translate(0 ${tyU}) translate(180 400) scale(${si}) translate(-180 -400)`);

    /* Truck scene fades in */
    cScene.setAttribute('opacity', clampC(segC(p,.50,.66),0,1));
    const scDy=(1-f)*24;
    cScene.setAttribute('transform',`translate(0 ${scDy})`);

    /* PHASE 3: WORKING (0.72 – 1.0) — rod pumps with clear visible stroke */
    const w = segC(p,.72,1);
    /* 2 full slow cycles — deliberate, readable compression strokes */
    const strokeCycle = w>0 ? (1-Math.cos(w*4*Math.PI))/2 : 0;
    const d = strokeCycle * STROKE;

    /* compression phase: 0=fully extended, 1=fully compressed */
    const comp = w>0 ? Math.max(0, Math.sin(w*4*Math.PI)) : 0;

    /* rod + attached cab eye compress into body */
    cTop.setAttribute('transform',`translate(0 ${d})`);
    /* truck cab bounces in sync */
    if(cTruck) cTruck.setAttribute('transform',`translate(0 ${d*0.9})`);

    /* road dashes scroll */
    if(cRoadDash) cRoadDash.setAttribute('transform',`translate(${-((w*420)%80)} 0)`);

    /* motion lines brighten on compression */
    if(cSpeed) cSpeed.setAttribute('opacity',
      (clampC(segC(p,.74,.86),0,1)*(0.4+0.6*comp)).toFixed(3));

    /* glow pulses hard on compression, dims on extension */
    const glowBase = segC(p,.48,.64)*0.9;
    cabGlow.style.opacity = w>0
      ? (glowBase*(0.3+0.7*comp)).toFixed(3)
      : glowBase.toFixed(3);
  }

  /* ── canvas particle overlay ── */
  let burstCabFn=function(){};
  const cabCvs=document.getElementById('cabCanvas');
  if(cabCvs){
    const ctx=cabCvs.getContext('2d');
    let W,H,cx,cy,t=0,pulseT=0;
    const parts=[];
    function resizeCab(){
      W=cabCvs.offsetWidth||cabCvs.parentElement.offsetWidth;
      H=cabCvs.offsetHeight||cabCvs.parentElement.offsetHeight;
      cabCvs.width=W; cabCvs.height=H;
      cx=W*0.75; cy=H*0.50;
    }
    resizeCab();
    addEventListener('resize',resizeCab);
    function burstCabLocal(n){
      const bx=cx+(Math.random()-0.5)*60,by=cy+(Math.random()-0.5)*100;
      for(let i=0;i<n;i++){
        parts.push({x:bx,y:by,
          vx:(Math.random()-0.5)*4,vy:(Math.random()-2.2)*3.5,
          life:1,decay:0.02+Math.random()*0.02,r:1.5+Math.random()*3,
          type:Math.random()<0.6?'spark':'dust'});
      }
      pulseT=1;
    }
    burstCabFn=burstCabLocal;
    (function cabLoop(){
      requestAnimationFrame(cabLoop);
      ctx.clearRect(0,0,W,H);
      t+=0.016;
      const R=Math.min(W,H)*0.20;
      for(let i=0;i<6;i++){
        const a=(i/6)*Math.PI*2+t*0.35;
        const x=cx+Math.cos(a)*R,y=cy+Math.sin(a)*R*0.55;
        ctx.save();ctx.globalAlpha=0.28+0.22*Math.sin(t+i);
        ctx.fillStyle='#FF4D00';
        ctx.beginPath();ctx.arc(x,y,2.5,0,Math.PI*2);ctx.fill();ctx.restore();
      }
      if(pulseT>0){
        const r=(1-pulseT)*Math.min(W,H)*0.26;
        ctx.save();ctx.globalAlpha=pulseT*0.55;
        ctx.strokeStyle='#FF4D00';ctx.lineWidth=2;
        ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();ctx.restore();
        pulseT-=0.022;
      }
      for(let i=parts.length-1;i>=0;i--){
        const s=parts[i];
        s.vy+=0.12;s.x+=s.vx;s.y+=s.vy;s.vx*=0.97;s.life-=s.decay;
        const a=Math.max(0,s.life);
        if(s.type==='spark'){
          ctx.save();ctx.globalAlpha=a;
          ctx.strokeStyle=`rgba(255,${100+Math.floor(100*a)},0,${a})`;
          ctx.lineWidth=s.r*0.6;ctx.beginPath();
          ctx.moveTo(s.x,s.y);ctx.lineTo(s.x-s.vx*4,s.y-s.vy*4);ctx.stroke();ctx.restore();
        } else {
          ctx.save();ctx.globalAlpha=a*0.5;
          ctx.fillStyle=`rgba(255,${150+Math.floor(80*a)},50,1)`;
          ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);ctx.fill();ctx.restore();
        }
        if(s.life<=0) parts.splice(i,1);
      }
    })();
  }

  /* ── cabin scroll driver ── */
  window._cabStartTimer=function(){};
  window._cabStopTimer=function(){};
  let cabCurIdx=-1;
  function cabNarrate(p){
    cabFill.style.width=(p*100)+'%';
    const idx=Math.min(9,Math.floor(p*9.999));
    cabDots.forEach((d,i)=>d.classList.toggle('on',i===idx));
    if(idx===cabCurIdx)return;
    cabCurIdx=idx; burstCabFn(26);
    cabUi.classList.add('asm-changing');
    setTimeout(()=>{
      cabNum.textContent=String(idx+1).padStart(2,'0');
      cabLab.textContent=CAB_STEPS[idx][0];
      cabDesc.textContent=CAB_STEPS[idx][1];
      cabUi.classList.remove('asm-changing');
    },220);
  }
  let cabTicking=false;
  function cabScroll(){
    if(cabTicking)return;cabTicking=true;
    requestAnimationFrame(()=>{
      const r=cabSec.getBoundingClientRect();
      const total=cabSec.offsetHeight-innerHeight;
      const p=Math.max(0,Math.min(1,(-r.top)/total));
      cabFrame(p);cabNarrate(p);cabTicking=false;
    });
  }
  addEventListener('scroll',cabScroll,{passive:true});
  addEventListener('resize',cabScroll);
  cabFrame(0);cabNarrate(0);
})();

/* ═══════════════════════════════════════════════════
   PAGE ROUTER
═══════════════════════════════════════════════════ */
const PAGE_MAP={
  home:    ['hero','stats','marquee'],
  products:['products'],
  tech:    ['tech','assembly','cab-assembly'],
  trucks:  ['trucks'],
  catalog: ['catalog'],
  contact: ['contact','page-footer'],
};
const HASH_PAGE={
  '':'home','hero':'home',
  'products':'products','tech':'tech',
  'trucks':'trucks','catalog':'catalog',
  'contact':'contact',
};

let _currentPage='home';

function routeTo(key){
  if(!PAGE_MAP[key]) key='home';
  _currentPage=key;

  /* hide all managed els */
  Object.values(PAGE_MAP).flat().forEach(id=>{
    const el=document.getElementById(id);
    if(el){el.style.display='none';el.classList.remove('pg-in');}
  });

  /* show page els */
  PAGE_MAP[key].forEach(id=>{
    const el=document.getElementById(id);
    if(!el) return;
    /* restore display */
    if(['assembly','cab-assembly','catalog','tech','page-footer','stats','marquee','hero'].includes(id))
      el.style.display='block';
    else el.style.display='flex';
    /* fade */
    requestAnimationFrame(()=>el.classList.add('pg-in'));
    /* trigger reveals */
    el.querySelectorAll('[data-reveal]:not(.in)').forEach(r=>setTimeout(()=>r.classList.add('in'),80));
  });

  window.scrollTo(0,0);


  /* re-init 3D tilt when catalogue becomes visible */
  if(key==='catalog') setTimeout(init3DTilt,60);

  /* mark tech-asm-mode for label hiding */
  ['assembly','cab-assembly'].forEach(id=>{
    const el=document.getElementById(id);
    if(el) el.classList.toggle('tech-asm-mode',key==='tech');
  });

  /* nav highlight */
  document.querySelectorAll('.navlinks a, .mob-links a').forEach(a=>{
    const h=(a.getAttribute('href')||'').replace('#','');
    a.classList.toggle('nav-active',HASH_PAGE[h]===key);
  });
}

/* intercept all hash links */
document.addEventListener('click',function(e){
  const a=e.target.closest('a[href^="#"]');
  if(!a) return;
  const hash=a.getAttribute('href').replace('#','');
  const page=HASH_PAGE[hash];
  if(page!==undefined){e.preventDefault();routeTo(page);}
});

/* initial load */
routeTo('home');

/* MOBILE NAV */
(function(){
  const burger=document.getElementById('navBurger');
  const mob=document.getElementById('mobNav');
  const close=document.getElementById('mobClose');
  function openMob(){mob.classList.add('open');document.body.classList.add('mob-open');document.body.style.overflow='hidden';}
  function closeMob(){mob.classList.remove('open');document.body.classList.remove('mob-open');document.body.style.overflow='';}
  if(burger) burger.addEventListener('click',openMob);
  if(close)  close.addEventListener('click',closeMob);
  /* close on link click */
  mob && mob.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMob));
})();

/* CATALOGUE FILTER — works for card grid + table rows */
function ft(m,b){
  document.querySelectorAll('.filt').forEach(t=>t.classList.remove('on'));
  b.classList.add('on');
  /* Cards */
  document.querySelectorAll('.cat-card').forEach(r=>{
    r.style.display=(m==='all'||r.dataset.m===m||r.dataset.cat===m)?'':'none';
  });
  /* Section dividers — show only if at least one card below is visible */
  document.querySelectorAll('.cat-section-divider').forEach(div=>{
    let next=div.nextElementSibling;
    let anyVisible=false;
    while(next&&!next.classList.contains('cat-section-divider')){
      if(next.style.display!=='none') anyVisible=true;
      next=next.nextElementSibling;
    }
    div.style.display=anyVisible?'':'none';
  });
  /* Legacy table rows if present */
  document.querySelectorAll('#tbl tbody tr').forEach(r=>{
    r.style.display=(m==='all'||r.dataset.m===m||r.dataset.cat===m)?'':'none';
  });
}

/* ══════════════════════════════════════════════════
   3D TILT EFFECT — catalogue cards
══════════════════════════════════════════════════ */
function init3DTilt(){
  document.querySelectorAll('.cat-card').forEach(card=>{
    /* inject glare div once */
    if(card.querySelector('.cc-glare')) return;
    const glare=document.createElement('div');
    glare.className='cc-glare';
    card.appendChild(glare);

    const isPhoto=!!card.querySelector('.has-photo');
    const maxRot=isPhoto?16:10;

    function onMove(e){
      const r=card.getBoundingClientRect();
      const dx=(e.clientX-(r.left+r.width/2))/(r.width/2);
      const dy=(e.clientY-(r.top+r.height/2))/(r.height/2);
      const rotX=(-dy*maxRot).toFixed(2);
      const rotY=(dx*maxRot).toFixed(2);
      const dist=Math.sqrt(dx*dx+dy*dy).toFixed(2);

      card.style.transition='transform .08s ease-out,box-shadow .08s';
      card.style.transform=
        `perspective(700px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(1.045)`;
      card.style.boxShadow=
        `${(-dx*22).toFixed(0)}px ${(-dy*16).toFixed(0)}px 44px rgba(0,0,0,0.55),`+
        `0 0 0 1px rgba(255,77,0,${(0.10+dist*0.12).toFixed(2)})`;

      /* glare — bright highlight follows cursor */
      const px=((dx+1)*50).toFixed(1);
      const py=((dy+1)*50).toFixed(1);
      const gAlpha=(0.08+dist*0.10).toFixed(2);
      glare.style.opacity='1';
      glare.style.background=
        `radial-gradient(circle at ${px}% ${py}%,`+
        `rgba(255,255,255,${gAlpha}) 0%,`+
        `rgba(255,255,255,0.02) 45%,transparent 70%)`;

      /* extra shimmer on photo cards */
      if(isPhoto){
        const img=card.querySelector('.cc-img');
        if(img) img.style.filter=
          `drop-shadow(${(-dx*6).toFixed(0)}px ${(-dy*6).toFixed(0)}px 18px rgba(255,120,0,0.28))`;
      }
    }

    function onLeave(){
      card.style.transition='transform .55s cubic-bezier(.22,1,.36,1),box-shadow .55s';
      card.style.transform='';
      card.style.boxShadow='';
      glare.style.opacity='0';
      const img=card.querySelector('.cc-img');
      if(img) img.style.filter='';
    }

    card.addEventListener('mousemove',onMove,{passive:true});
    card.addEventListener('mouseleave',onLeave);
    /* touch: just reset */
    card.addEventListener('touchstart',onLeave,{passive:true});
  });
}

/* Run once DOM is ready, and re-run after filter changes */
document.addEventListener('DOMContentLoaded',init3DTilt);
setTimeout(init3DTilt,800); /* fallback after page router shows catalogue */

/* LIGHTBOX */
function openLightbox(src,caption){
  const lb=document.getElementById('lightbox');
  document.getElementById('lbImg').src=src;
  document.getElementById('lbCaption').textContent=caption||'';
  lb.classList.add('open');
  document.body.style.overflow='hidden';
}
function closeLightbox(){
  document.getElementById('lightbox').classList.remove('open');
  document.body.style.overflow='';
}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLightbox();});

/* FORM */
function sendForm(e){e.preventDefault();const b=document.getElementById('sbtn');b.textContent='✓ Sent — we\'ll call you shortly';b.style.background='#25D366';setTimeout(()=>{b.textContent='Send Enquiry';b.style.background='';e.target.reset()},3500)}
