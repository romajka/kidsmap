// Mappy 3D companion for kidsmap.az
// mountMappy(element, { src, lang }) -> controller
// The element may already hold a fallback <img>; it is hidden only once the 3D bear is ready.
import {
  WebGLRenderer, Scene, PerspectiveCamera, HemisphereLight, DirectionalLight, AnimationMixer, LoopRepeat, LoopOnce,
  Clock, Raycaster, Vector2, Vector3, Quaternion, Euler, MathUtils, Mesh, PlaneGeometry, MeshBasicMaterial, CanvasTexture,
  SRGBColorSpace, NeutralToneMapping,
} from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { advanceSpring } from './spring.mjs';
import { bindPressGesture } from './press-gesture.mjs';

// facial presets: morph target name -> weight (".L"/".R" suffix = one side only)
const EXPRESSIONS = {
  neutral: {},
  happy: { happy: 1, grin: 1, open: 0.85, blush: 1 },
  laugh: { happy: 1, grin: 1, open: 1, blush: 1, up: 0.5 },
  surprised: { wide: 1, up: 1, o: 1 },
  sad: { sad: 1, frown: 1 },
  sleepy: { blink: 0.8, sad: 0.35 },
  asleep: { blink: 1 },
  grumpy: { angry: 1, frown: 0.6 },
  shy: { happy: 0.7, grin: 0.6, blush: 1 },
  wink: { 'blink.R': 1, grin: 1, blush: 0.6, 'up.L': 0.5 },
  curious: { wide: 0.35, 'up.L': 0.8, o: 0.25 },
};

const SAY = {
  hello: { az: 'Salam! Mən Mappy!', ru: 'Привет! Я Mappy!', en: "Hi! I'm Mappy!" },
  hooray: { az: 'Yaşasın!', ru: 'Ура!', en: 'Hooray!' },
  hop: { az: 'Hoppa!', ru: 'Опа!', en: 'Whee!' },
  play: { az: 'Gəl oynayaq!', ru: 'Давай играть!', en: "Let's play!" },
  oops: { az: 'Oy!', ru: 'Ой!', en: 'Oh!' },
  hug: { az: 'Qucaqlaşaq!', ru: 'Обнимашки!', en: 'Hugs!' },
  map: { az: 'Xəritəyə bax!', ru: 'Загляни на карту!', en: 'Check the map!' },
  tickle: { az: 'Qıdığım gəlir!', ru: 'Щекотно!', en: "That tickles!" },
  zzz: { az: 'Zzz…', ru: 'Zzz…', en: 'Zzz…' },
  like: { az: 'Xoşuma gəlir!', ru: 'Мне нравится!', en: 'I like that!' },
  nose: { az: 'Burnum!', ru: 'Мой нос!', en: 'My nose!' },
  five: { az: 'Beş ver!', ru: 'Дай пять!', en: 'High five!' },
};

const REACTIONS = [
  { clip: 'wave', expr: 'happy', say: 'hello' },
  { clip: 'jump', expr: 'laugh', say: 'hooray' },
  { clip: 'spin', expr: 'happy', say: 'hop', motion: true },
  { clip: 'dance', expr: 'laugh', say: 'play', hold: 2.4 },
  { clip: 'surprised', expr: 'surprised', say: 'oops' },
  { clip: 'hug', expr: 'shy', say: 'hug' },
  { clip: 'point', expr: 'wink', say: 'map' },
];

// what he does when a part of him is pressed; repeated presses on the same part walk through the list
const ZONES = {
  head: [{ clip: 'pat', expr: 'shy', say: 'like' }, { clip: 'hug', expr: 'shy', say: 'hug' }, { clip: 'dance', expr: 'laugh', say: 'play', hold: 2.4 }],
  nose: [{ clip: 'boop', expr: 'surprised', say: 'nose' }, { clip: 'surprised', expr: 'surprised', say: 'oops' }],
  belly: [{ clip: 'giggle', expr: 'laugh', say: 'tickle' }, { clip: 'dance', expr: 'laugh', say: 'play', hold: 2.4 }, { clip: 'hug', expr: 'shy', say: 'hug' }],
  hand: [{ clip: 'highfive', expr: 'happy', say: 'five' }, { clip: 'wave', expr: 'happy', say: 'hello' }],
  foot: [{ clip: 'jump', expr: 'laugh', say: 'hop' }, { clip: 'spin', expr: 'happy', say: 'hooray', motion: true }],
  ear: [{ clip: 'earflick', expr: 'wink', say: 'oops' }, { clip: 'pat', expr: 'shy', say: 'like' }],
  bow: [{ clip: 'spin', expr: 'happy', say: 'hooray', motion: true }, { clip: 'wave', expr: 'happy', say: 'hello' }],
  pack: [{ clip: 'point', expr: 'wink', say: 'map' }, { clip: 'jump', expr: 'laugh', say: 'hooray' }],
};

function blobShadow() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d'); const gr = g.createRadialGradient(64, 64, 4, 64, 64, 62);
  gr.addColorStop(0, 'rgba(13,73,36,0.32)'); gr.addColorStop(1, 'rgba(13,73,36,0)');
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  const t = new CanvasTexture(c); t.colorSpace = SRGBColorSpace; return t;
}

export function mountMappy(el, opts = {}) {
  const lang = opts.lang || document.documentElement.lang?.slice(0, 2) || 'az';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const manual = !!opts.manual;            // demo/capture mode: caller drives update(dt)
  const listeners = {};
  const ctl = {
    ready: false, play, express, say, react, touch, pose, update, on(ev, fn) { (listeners[ev] ||= []).push(fn); return ctl; },
    lookAt(x, y) { pointer.set(x, y); lastInput = time; },
    pressAt(zone, on, x = 0) { if (on) { press.on = true; press.zone = zone; press.x = x; } else if (press.on) { press.on = false; touch(zone); } },
    destroy,
  };
  const emit = (ev, d) => (listeners[ev] || []).forEach((f) => f(d));

  let renderer;
  try {
    renderer = new WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power', preserveDrawingBuffer: manual });
  } catch (e) {
    queueMicrotask(() => emit('error', e));
    return ctl;
  }
  const nativeButton = el.tagName === 'BUTTON';
  // Weak phones (few cores or little memory) get a slightly lower pixel ratio and frame rate; the look is the same.
  const lowEnd = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, lowEnd ? 1.5 : 2));
  renderer.outputColorSpace = SRGBColorSpace; renderer.toneMapping = NeutralToneMapping; renderer.toneMappingExposure = 1.05;
  const canvas = renderer.domElement;
  // bleed: how far the canvas reaches past the box (fractions of the box), so hops and raised paws are not cut off
  const bleed = Object.assign({ top: 0, right: 0, bottom: 0, left: 0 }, opts.bleed || {});
  Object.assign(canvas.style, {
    position: 'absolute', left: `${-bleed.left * 100}%`, top: `${-bleed.top * 100}%`,
    width: `${(1 + bleed.left + bleed.right) * 100}%`, height: `${(1 + bleed.top + bleed.bottom) * 100}%`,
    display: 'block', pointerEvents: 'none', opacity: '0', transition: 'opacity .4s ease', zIndex: opts.zIndex ?? 1,
  });
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', 'Mappy');

  const scene = new Scene();
  const camera = new PerspectiveCamera(26, 1, 0.1, 50);
  const BEAR_H = 2.12;                       // feet to ear tips, world units
  function frame() {                         // put the feet on the box's bottom edge and the ears at its top
    const H1 = 1 + bleed.top + bleed.bottom, tf = bleed.top / H1, bf = bleed.bottom / H1;
    const H = BEAR_H / Math.max(0.2, 1 - tf - bf), yc = (0.5 - bf) * H;
    const D = H / (2 * Math.tan(MathUtils.degToRad(camera.fov / 2)));
    camera.position.set(0, yc + 0.12 * H, D); camera.lookAt(0, yc, 0);
  }
  frame();
  scene.add(new HemisphereLight(0xf4fff2, 0x7a9a80, 1.6));
  const key = new DirectionalLight(0xfff6ea, 2.6); key.position.set(-2.5, 4, 4); scene.add(key);
  const rim = new DirectionalLight(0xdfffe6, 1.8); rim.position.set(2.5, 3, -3); scene.add(rim);
  const fill = new DirectionalLight(0xeaf4ff, 0.7); fill.position.set(3, 1, 3); scene.add(fill);
  const shadow = new Mesh(new PlaneGeometry(1.5, 1.5), new MeshBasicMaterial({ map: blobShadow(), transparent: true, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2; shadow.position.y = 0.005; scene.add(shadow);

  let mixer, actions = {}, current = null, bones = {}, morphs = [], root;
  const pointer = new Vector2(0, 0), look = new Vector2(0, 0), restLook = new Vector2(0, -0.3);
  let time = 0, lastInput = 0, blinkAt = 2, blinkT = -1, exprName = 'neutral', exprUntil = 0, sleeping = false;
  let clicks = [], busyUntil = 0, visible = false, raf = 0;
  const target = {}, cur = {};

  function resize() {
    const r = el.getBoundingClientRect(); const w = Math.max(1, r.width), h = Math.max(1, r.height);
    renderer.setSize(w * (1 + bleed.left + bleed.right), h * (1 + bleed.top + bleed.bottom), false);
    camera.aspect = (w * (1 + bleed.left + bleed.right)) / (h * (1 + bleed.top + bleed.bottom)); camera.updateProjectionMatrix(); frame();
  }

  const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
  const onModel = (gltf) => {
    root = gltf.scene; scene.add(root);
    root.traverse((o) => {
      if (o.isBone) bones[o.name] = o;
      if (o.isMesh) {
        o.frustumCulled = false;
        if (o.morphTargetDictionary) morphs.push(o);
        if (o.material && o.material.sheen !== undefined && /fur|cream|bow|pack/.test(o.material.name)) o.material.sheenRoughness = 0.45;
      }
    });
    mixer = new AnimationMixer(root);
    gltf.animations.forEach((c) => { actions[c.name] = mixer.clipAction(c); });
    ['idle', 'dance', 'sleep', 'walk'].forEach((n) => actions[n] && actions[n].setLoop(LoopRepeat));
    ctl.clips = gltf.animations.map((c) => [c.name, c.duration]);
    Object.entries(actions).forEach(([n, a]) => { if (!['idle', 'dance', 'sleep', 'walk'].includes(n)) { a.setLoop(LoopOnce); a.clampWhenFinished = true; } });
    mixer.addEventListener('finished', (e) => { if (e.action === current && current !== actions.sleep) play('idle', 0.35); });
    play('idle', 0);
    if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
    el.appendChild(canvas); resize();
    if (!nativeButton && !el.hasAttribute('tabindex')) { el.tabIndex = 0; el.setAttribute('role', 'button'); el.setAttribute('aria-label', opts.label || 'Mappy'); }
    intro();
    requestAnimationFrame(() => {
      canvas.style.opacity = '1';
      el.querySelectorAll('[data-mappy-fallback]').forEach((n) => (n.style.visibility = 'hidden'));
    });
    ctl.ready = true; emit('ready');
    startLoop();
  };
  if (opts.buffer) loader.parse(opts.buffer, '', onModel, () => emit('error'));
  else loader.load(opts.src || '/static/3d/mappy.glb', onModel, undefined, () => emit('error'));

  // ------------------------------------------------------------ actions & expressions
  function play(name, fade = 0.25, timeScale = 1) {
    const a = actions[name]; if (!a) return;
    if (current === a && a.isRunning()) return;
    a.reset(); a.setEffectiveTimeScale(reduced ? Math.min(timeScale, 0.7) : timeScale); a.setEffectiveWeight(1);
    if (current) a.crossFadeFrom(current, fade, false);
    a.play(); current = a;
  }
  function express(name, holdS = 0) {
    if (!holdS && name !== 'asleep') baseExpr = EXPRESSIONS[name] ? name : 'neutral';
    exprName = EXPRESSIONS[name] ? name : 'neutral';
    exprUntil = holdS ? time + holdS : 0;
  }
  // ---------------------------------------------------------- speech cloud: tied to his head, springs out of him
  let cloud = null, cloudBody = null, cloudText = null, bubbleTimer = 0, cloudOn = false, cloudSide = 1, cloudW = 0, cloudH = 0;
  const anchorV = new Vector3();
  function ensureCloud() {
    if (cloud) return;
    if (!document.getElementById('mappy3d-cloud-style')) {
      const st = document.createElement('style'); st.id = 'mappy3d-cloud-style';
      st.textContent = `
.mappy-say{position:fixed;left:0;top:0;z-index:60;pointer-events:none;will-change:transform}
.mappy-say__b{position:relative;max-width:min(232px,calc(100vw - 24px));padding:11px 16px 12px;border-radius:22px;
  background:#f0f8f2;border:1.5px solid #cae8d1;color:#143c2d;
  font:700 15px/1.38 "Chiron GoRound TC Public","Chiron GoRound TC",system-ui,-apple-system,"Segoe UI",sans-serif;
  letter-spacing:-.005em;text-wrap:balance;
  box-shadow:0 16px 34px -14px rgba(13,73,36,.32),0 3px 10px rgba(13,73,36,.07);
  transform-origin:var(--tx,24px) calc(100% + 9px);opacity:0;scale:.3;visibility:hidden}
.mappy-say__b::after{content:"";position:absolute;bottom:-7.5px;left:calc(var(--tx,24px) - 7px);width:13px;height:13px;
  background:#f0f8f2;border-right:1.5px solid #cae8d1;border-bottom:1.5px solid #cae8d1;border-bottom-right-radius:4px;transform:rotate(45deg)}
.mappy-say__b::before{content:"";position:absolute;inset:1px 1px auto;height:46%;border-radius:20px 20px 40% 40%/20px 20px 14px 14px;
  background:linear-gradient(#fff 0,rgba(255,255,255,0) 100%);opacity:.75;pointer-events:none}
.mappy-say.is-in .mappy-say__b{visibility:visible;animation:mappy-say-in .56s cubic-bezier(.3,1.55,.55,1) both,mappy-say-float 3.4s ease-in-out .56s infinite}
.mappy-say.is-swap .mappy-say__b{visibility:visible;opacity:1;scale:1;animation:mappy-say-swap .42s cubic-bezier(.3,1.6,.55,1) both,mappy-say-float 3.4s ease-in-out .42s infinite}
.mappy-say.is-out .mappy-say__b{visibility:visible;animation:mappy-say-out .26s cubic-bezier(.5,0,.75,0) both}
.mappy-say__t{position:relative}
.mappy-say__w{display:inline-block;white-space:pre;opacity:0;translate:0 7px;scale:.85;animation:mappy-say-word .42s cubic-bezier(.2,1.2,.35,1) forwards;animation-delay:calc(var(--i) * 55ms + 140ms)}
@keyframes mappy-say-in{0%{opacity:0;scale:.3;translate:0 12px}55%{opacity:1;scale:1.06;translate:0 -2px}78%{scale:.985}100%{opacity:1;scale:1;translate:0 0}}
@keyframes mappy-say-swap{0%{opacity:1;scale:.9}55%{scale:1.045}100%{opacity:1;scale:1}}
@keyframes mappy-say-out{0%{opacity:1;scale:1;translate:0 0}100%{opacity:0;scale:.82;translate:0 -8px}}
@keyframes mappy-say-float{0%,100%{translate:0 0}50%{translate:0 -3px}}
@keyframes mappy-say-word{to{opacity:1;translate:0 0;scale:1}}
@media (prefers-reduced-motion:reduce){.mappy-say.is-in .mappy-say__b,.mappy-say.is-swap .mappy-say__b{animation:mappy-say-fade .2s ease both}
 .mappy-say.is-out .mappy-say__b{animation:mappy-say-fade .2s ease reverse both}.mappy-say__w{animation:none;opacity:1;translate:none;scale:none}
 @keyframes mappy-say-fade{from{opacity:0}to{opacity:1;scale:1;translate:0 0}}}`;
      document.head.appendChild(st);
    }
    cloud = document.createElement('div'); cloud.className = 'mappy-say';
    cloud.innerHTML = '<div class="mappy-say__b"><div class="mappy-say__t" role="status" aria-live="polite"></div></div>';
    cloudBody = cloud.firstChild; cloudText = cloudBody.firstChild;
    document.body.appendChild(cloud);
  }
  function words(node, text) {
    node.textContent = '';
    text.split(/(\s+)/).forEach((w, i) => {
      if (!w) return;
      if (/^\s+$/.test(w)) { node.appendChild(document.createTextNode(' ')); return; }
      const sp = document.createElement('span'); sp.className = 'mappy-say__w'; sp.style.setProperty('--i', String(i >> 1)); sp.textContent = w; node.appendChild(sp);
    });
  }
  function say(text, holdS = 2.4) {
    emit('say', text);
    if (opts.bubble === false) return;
    ensureCloud();
    const swap = cloudOn && cloud.classList.contains('is-in') || cloud.classList.contains('is-swap');
    words(cloudText, text);
    cloud.classList.remove('is-in', 'is-out', 'is-swap'); void cloud.offsetWidth;
    cloud.classList.add(swap ? 'is-swap' : 'is-in');
    cloudOn = true; cloudW = cloudBody.offsetWidth; cloudH = cloudBody.offsetHeight;
    cloudSide = 0; placeCloud();
    bubbleTimer = time + Math.max(1.6, holdS + text.length * 0.02);
  }
  function hideBubble() {
    if (!cloud || !cloudOn) return;
    cloudOn = false; cloud.classList.remove('is-in', 'is-swap'); cloud.classList.add('is-out');
  }
  function placeCloud() {
    if (!cloud || (!cloudOn && !cloud.classList.contains('is-out')) || !bones.head) return;
    const r = canvas.getBoundingClientRect(); if (!r.width) return;
    if (!cloudSide) {            // pick the side with room, once per phrase, so the cloud does not flip while he moves
      bones.head.getWorldPosition(anchorV); anchorV.project(camera);
      const hx = r.left + (anchorV.x * 0.5 + 0.5) * r.width;
      cloudSide = hx + 40 + cloudW < innerWidth - 10 ? 1 : -1;
    }
    bones.head.getWorldPosition(anchorV);
    anchorV.x += cloudSide * 0.34; anchorV.y += 0.86;
    anchorV.project(camera);
    const ax = r.left + (anchorV.x * 0.5 + 0.5) * r.width, ay = r.top + (-anchorV.y * 0.5 + 0.5) * r.height;
    const tail = cloudSide > 0 ? 26 : cloudW - 26;
    let left = ax - tail; left = Math.max(10, Math.min(innerWidth - cloudW - 10, left));
    let top = ay - cloudH - 12; top = Math.max(10, top);
    cloudBody.style.setProperty('--tx', `${Math.max(18, Math.min(cloudW - 18, ax - left))}px`);
    cloud.style.transform = `translate3d(${left.toFixed(1)}px,${top.toFixed(1)}px,0)`;
  }
  const t = (k) => (SAY[k] ? SAY[k][lang] || SAY[k].az : k);

  // the mood a page gives him when he appears
  function intro() {
    const m = opts.mood || 'idle';
    if (m === 'welcome') { setTimeout(() => { play('wave', 0.2); express('happy', 2.4); }, 500); }
    else if (m === 'empty') { express('sad'); setTimeout(() => play('look', 0.4), 600); }
    else if (m === 'success') { setTimeout(() => { play('jump', 0.15); express('laugh', 2.2); }, 300); }
    else if (m === 'lost') { express('curious'); setTimeout(() => play('look', 0.4), 500); }
    if (m === 'empty' || m === 'lost') baseExpr = m === 'empty' ? 'sad' : 'curious';
  }
  let baseExpr = 'neutral';
  let lastReaction = -1;
  function react(i) {
    if (!ctl.ready) return;
    if (sleeping) { wake(); return; }
    clicks = clicks.filter((c) => time - c < 1.4); clicks.push(time);
    if (clicks.length >= 4) { clicks = []; play('poke', 0.1); express('grumpy', 1.3); say(t('tickle')); busyUntil = time + 0.7; emit('react', 'tickle'); return; }
    if (time < busyUntil && i === undefined) return;
    let pool = REACTIONS.map((_, k) => k).filter((k) => !(reduced && REACTIONS[k].motion) && k !== lastReaction);
    const k = i ?? pool[Math.floor(Math.random() * pool.length)];
    const r = REACTIONS[k]; lastReaction = k;
    run(r);
  }
  function run(r) {
    if (reduced && r.motion) r = { clip: 'wave', expr: 'happy', say: 'hello' };
    if (current === actions[r.clip]) current.stop(), (current = null);
    play(r.clip, 0.15);
    const len = actions[r.clip]?.getClip().duration || 1.5;
    express(r.expr, r.hold || len); say(t(r.say), Math.max(1.6, len));
    busyUntil = time + Math.min(len, 1.2);
    if (r.hold) setTimeout(() => current === actions[r.clip] && play('idle', 0.4), r.hold * 1000);
    emit('react', r.clip);
  }
  const zoneStep = {};
  function touch(zone) {
    if (!ctl.ready) return;
    if (sleeping) { wake(); return; }
    lastInput = time;
    clicks = clicks.filter((c) => time - c < 1.4); clicks.push(time);
    if (clicks.length >= 4) { clicks = []; play('poke', 0.1); express('grumpy', 1.3); say(t('tickle')); emit('react', 'tickle'); return; }
    const list = ZONES[zone] || ZONES.belly;
    const i = (zoneStep[zone] = ((zoneStep[zone] ?? -1) + 1) % list.length);
    Object.keys(zoneStep).forEach((z) => { if (z !== zone) zoneStep[z] = -1; });
    run(list[i]); emit('touch', zone);
    if (baseExpr === 'sad') baseExpr = 'neutral';
  }
  function pose(name, tSec) {              // freeze one moment of a clip (for previews and tests)
    const a = actions[name]; if (!a) return;
    mixer.stopAllAction(); a.reset(); a.play(); a.paused = true; a.time = tSec; current = a; mixer.update(0); update(0);
  }
  function sleep() { sleeping = true; play('sleep', 0.8); express('asleep'); say(t('zzz'), 1e9); emit('sleep'); }
  function wake() { sleeping = false; hideBubble(); play('surprised', 0.2); express('surprised', 1.0); lastInput = time; emit('wake'); }

  // ------------------------------------------------------------ input
  const onMove = (e) => {
    const r = el.getBoundingClientRect(); if (!r.width) return;
    const x = ((e.clientX - (r.left + r.width / 2)) / innerWidth) * 2.4;
    const y = ((e.clientY - (r.top + r.height * 0.25)) / innerHeight) * -2.4;
    pointer.set(MathUtils.clamp(x, -1, 1), MathUtils.clamp(y, -1, 1));
    if (!sleeping) lastInput = time;
  };
  const ray = new Raycaster(), ndc = new Vector2();
  function zoneAt(e) {
    if (!root) return null;
    const r = canvas.getBoundingClientRect();
    ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    root.traverse((o) => { if (o.isSkinnedMesh) o.boundingSphere = null, (o.boundingBox = null); });
    const hit = ray.intersectObject(root, true)[0]; if (!hit) return null;
    const n = hit.object.name || hit.object.parent?.name || '', p = hit.point;
    let zone = 'belly';
    if (/Arm|Pad/.test(n)) zone = 'hand'; else if (/Leg|Sole/.test(n)) zone = 'foot'; else if (/Nose|Muzzle|Mouth/.test(n)) zone = 'nose';
    else if (/Bow/.test(n)) zone = 'bow'; else if (/Backpack/.test(n)) zone = 'pack'; else if (/Ear/.test(n)) zone = 'ear'; else if (/Eye|Brow|Blush/.test(n)) zone = 'head';
    else if (p.y > 1.62 && Math.abs(p.x) > 0.24) zone = 'ear'; else if (p.y > 1.1) zone = 'head';
    return { zone, x: p.x };
  }
  // the press itself: he squashes under the finger and springs back on release
  const press = { on: false, zone: null, x: 0, v: 0, vel: 0 };
  const inBox = (e) => { const r = canvas.getBoundingClientRect(); return e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom; };
  let stopPressGesture = () => {};
  const onEnter = (event) => {
    if (event.pointerType === 'mouse' && ctl.ready && !sleeping && exprName === baseExpr) express('curious', 0.8);
  };
  // Pointer gestures already react on release. A native keyboard or AT click has no tap position.
  const onClick = (event) => { if (event.detail === 0) touch('belly'); };
  const onKey = (e) => { if (e.target === el && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); touch('belly'); } };
  if (!manual) {
    addEventListener('pointermove', onMove, { passive: true });
    stopPressGesture = bindPressGesture(document, {
      pick: (event) => inBox(event) ? zoneAt(event) : null,
      start: (hit) => {
        press.on = true; press.zone = hit.zone; press.x = hit.x;
        if (!sleeping) lastInput = time;
        if (!sleeping) express(hit.zone === 'belly' ? 'surprised' : 'curious', 0.6);
      },
      release: (hit) => { press.on = false; touch(hit.zone); },
      cancel: () => { press.on = false; },
    });
    el.addEventListener('pointerenter', onEnter);
    el.addEventListener('click', onClick);
    if (!nativeButton) el.addEventListener('keydown', onKey);
  }
  const ro = new ResizeObserver(resize); ro.observe(el);
  const io = new IntersectionObserver(([e]) => {
    visible = e.isIntersecting;
    if (visible) startLoop();
    else hideBubble();
  }, { threshold: 0.01 });
  io.observe(el);
  document.addEventListener('visibilitychange', startLoop);

  // ------------------------------------------------------------ per frame
  const clock = new Clock(); const qTmp = new Quaternion(), eTmp = new Euler(), tmpV = new Vector3(); const ear = { v: 0, vel: 0, px: 0, py: 0 };
  function startLoop() {
    if (ctl.ready && visible && !document.hidden && !manual && !raf) {
      clock.start();
      pending = 0;
      raf = requestAnimationFrame(loop);
    }
  }
  // Frame budget. He is drawn at full rate only while something moves: the pointer, a press, a reaction clip,
  // a blink or a changing face. Standing idle (breathing) or asleep he is drawn less often, which looks the same
  // but leaves the phone's processor free for scrolling and the rest of the page.
  const touchFirst = matchMedia('(pointer: coarse)').matches;   // phones and tablets: no cursor for him to follow
  const FPS = lowEnd ? { active: 30, calm: 10, sleep: 6 } : touchFirst ? { active: 60, calm: 12, sleep: 8 } : { active: 60, calm: 24, sleep: 10 };
  let pending = 0;
  function targetFps() {
    if (press.on || Math.abs(press.v) > 0.002 || Math.abs(press.vel) > 0.01) return FPS.active;
    if (sleeping) return FPS.sleep;
    if (!mixer || current !== actions.idle || blinkT >= 0 || exprUntil || time - lastInput < 2.5) return FPS.active;
    return reduced ? FPS.sleep : FPS.calm;
  }
  function loop() {
    if (!visible || document.hidden) { raf = 0; pending = 0; return; }
    raf = requestAnimationFrame(loop);
    pending += clock.getDelta();
    if (pending < 1 / targetFps() - 0.004) return;   // skip this screen refresh: nothing to draw yet
    update(Math.min(pending, 0.2));
    pending = 0;
  }
  function update(dt) {
    if (!mixer) return;
    time += dt;
    // autonomous life
    if (!sleeping && !reduced && time - lastInput > (opts.sleepAfter || 40) && current === actions.idle) sleep();
    if (!sleeping && current === actions.idle && !reduced && Math.floor(time / 9) !== Math.floor((time - dt) / 9) && time - lastInput > 6) play('look', 0.5);
    if (exprUntil && time > exprUntil) { exprUntil = 0; exprName = baseExpr; }
    if (bubbleTimer && time > bubbleTimer) { bubbleTimer = 0; hideBubble(); }
    if (cloud && !visible) hideBubble();
    mixer.update(dt);

    // head and eyes follow the pointer (added on top of the clip)
    const free = !sleeping;
    look.lerp(free ? pointer : restLook, 1 - Math.exp(-dt * 6));
    // the mixer only rewrites a bone when its clip value changes, so the look offset is removed again after rendering
    const saved = [];
    const addLook = (b, px, py) => { if (!b) return; saved.push([b, b.quaternion.clone()]); eTmp.set(-look.y * py, look.x * px, 0, 'YXZ'); b.quaternion.multiply(qTmp.setFromEuler(eTmp)); };
    addLook(bones.head, 0.55, 0.32); addLook(bones.eyeL, 0.22, 0.18); addLook(bones.eyeR, 0.22, 0.18);
    if (bones.spine && free) { saved.push([bones.spine, bones.spine.quaternion.clone()]); eTmp.set(0, look.x * 0.1, -look.x * 0.03, 'YXZ'); bones.spine.quaternion.multiply(qTmp.setFromEuler(eTmp)); }
    // press spring (underdamped, so release bounces)
    advanceSpring(press, press.on ? 1 : 0, 520, 17, dt);
    const savedScale = [];
    if (Math.abs(press.v) > 0.002 || Math.abs(press.vel) > 0.01) {
      const headish = press.zone === 'head' || press.zone === 'ear' || press.zone === 'nose';
      const b = headish ? bones.head : bones.root, k = press.v * (headish ? 0.16 : 0.11);
      if (b) { savedScale.push([b, b.scale.clone()]); b.scale.multiply(headish ? tmpV.set(1 + k * 0.8, 1 - k, 1 + k * 0.8) : tmpV.set(1 + k * 0.8, 1 + k * 0.8, 1 - k)); }   // the root bone's up axis is its local Z
      if (bones.root && !headish) { saved.push([bones.root, bones.root.quaternion.clone()]); eTmp.set(0, press.x * press.v * 0.12, 0, 'YXZ'); bones.root.quaternion.multiply(qTmp.setFromEuler(eTmp)); }
    }
    // ears lag behind head turns and hops
    if (dt > 0) {
      const drive = MathUtils.clamp((look.x - ear.px) / dt * -0.12 - (Math.abs(bones.root?.position.z ?? 0) - ear.py) / dt * 0.25, -0.6, 0.6);
      ear.px = look.x; ear.py = Math.abs(bones.root?.position.z ?? 0);
      advanceSpring(ear, drive, 160, 9, dt);
    }
    for (const [n, sgn] of [['earL', 1], ['earR', 1]]) if (bones[n]) { saved.push([bones[n], bones[n].quaternion.clone()]); eTmp.set(Math.abs(ear.v) * 0.2, 0, ear.v * sgn, 'YXZ'); bones[n].quaternion.multiply(qTmp.setFromEuler(eTmp)); }
    if (bones.root) shadow.scale.setScalar(1 / (1 + Math.abs(bones.root.position.z) * 1.2));

    // blink on top of the expression
    if (!sleeping && time > blinkAt && blinkT < 0) blinkT = 0;
    let blink = 0;
    if (blinkT >= 0) { blinkT += dt; blink = Math.sin(Math.min(1, blinkT / 0.16) * Math.PI); if (blinkT > 0.16) { blinkT = -1; blinkAt = time + 2.2 + Math.random() * 3.5 + (Math.random() < 0.2 ? -1.8 : 0); } }
    const E = EXPRESSIONS[exprName];
    for (const m of morphs) {
      const side = /L$/.test(m.name) ? 'L' : /R$/.test(m.name) ? 'R' : '';
      for (const [k, idx] of Object.entries(m.morphTargetDictionary)) {
        let v = (E[k] ?? 0); if (side && E[`${k}.${side}`] !== undefined) v = E[`${k}.${side}`];
        if (k === 'blink') v = Math.max(v, E.happy ? 0 : blink);
        const id = m.uuid + k; cur[id] = (cur[id] ?? 0) + (v - (cur[id] ?? 0)) * (1 - Math.exp(-dt * (k === 'blink' ? 40 : 12)));
        m.morphTargetInfluences[idx] = cur[id];
      }
    }
    renderer.render(scene, camera);
    placeCloud();
    for (const [b, q] of saved) b.quaternion.copy(q);
    for (const [b, sc] of savedScale) b.scale.copy(sc);
  }

  function destroy() {
    cancelAnimationFrame(raf); raf = 0; ro.disconnect(); io.disconnect();
    removeEventListener('pointermove', onMove); document.removeEventListener('visibilitychange', startLoop);
    stopPressGesture(); el.removeEventListener('keydown', onKey);
    el.removeEventListener('pointerenter', onEnter); el.removeEventListener('click', onClick);
    renderer.dispose(); canvas.remove(); cloud?.remove();
  }
  return ctl;
}

if (typeof window !== 'undefined') window.mountMappy = mountMappy;
