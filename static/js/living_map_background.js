/* KidsMap Living Map: progressive decoration for public visitor pages. */
(() => {
  'use strict';
  const canvas = document.querySelector('[data-living-map]');
  if (!canvas) return;
  const isHome = document.body.classList.contains('page-home');
  let ctx;
  try { ctx = canvas.getContext('2d'); } catch (_) { return; }
  if (!ctx) return;

  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const mouse = matchMedia('(hover: hover) and (pointer: fine)');
  const desktop = matchMedia('(min-width: 1024px) and (hover: hover) and (pointer: fine)');
  const zones = [
    ['.home-hero', 1], ['.home-hero-search-panel', .55],
    ['.home-hero-stats', .3], ['.home-places-rail', .35],
    ['.home-discover', .5], ['.home-map-panel', .08],
    ['.home-steps', .35], ['.home-owner-banner', .45],
    ['.home-faq-panel', .15], ['.site-footer', .25],
  ];
  // On the home page animations flow freely behind all text/cards;
  // only solid structural panels get cleared. Other pages keep the broad
  // exclusion list so dots never render behind dense article content.
  const protectedSelector = isHome ? [
    '.topbar', '.home-map-panel', '.home-owner-banner',
    '.footer-grid', '.footer-bottom', '.home-faq-item',
    '[data-rail-viewport]',
  ].join(',') : [
    '.topbar',
    '[data-rail-viewport]', '.home-map-panel', '.home-owner-banner',
    '.footer-grid', '.footer-bottom', 'main h1', 'main h2', 'main h3',
    'main p', 'main form', 'main a', 'main button', 'main summary',
    'main img', '.home-faq-item',
    'main li', 'main table', 'main blockquote', 'main iframe',
    'main video', 'main input', 'main textarea', 'main select',
    '.place-gallery', '.detail-card', '.detail-decision', '.place-card',
    '.specialist-card', '.event-card', '.faq-item', '.leaflet-container',
    'main [class*="-card"]', 'main .panel', '.about-stat-box', '.catalog-hero',
    '.about-steps-wrapper',
    '.gm-style', '[data-map]', '[role="dialog"]', '[role="listbox"]',
  ].join(',');
  const pointer = {x: 0, y: 0, active: false, xShift: 0, yShift: 0};
  const state = {
    width: 0, height: 0, pageHeight: 0, scroll: window.scrollY,
    dots: [], routes: [], scenes: [], zones: [], masks: [], ripples: [], frame: 0,
    layoutDirty: true, last: 0, drawnAt: 0, time: 0, slow: 0, quality: 1,
    stopped: false, cleanup: [],
  };
  const styles = getComputedStyle(document.body);
  const colors = ['--brand-turf', '--brand-celadon', '--brand-spruce', '--brand-brick']
    .map(token => styles.getPropertyValue(token).trim());
  if (colors.some(color => !color)) return;
  const palette = {green: colors[0], mint: colors[1], paper: styles.getPropertyValue('--brand-white').trim()};

  function listen(target, name, handler, options) {
    target.addEventListener(name, handler, options);
    state.cleanup.push(() => target.removeEventListener(name, handler, options));
  }

  function configuration() {
    // On a struggling renderer, tiny idle drift needs very few repaints.
    // Keep the local pointer response quicker while the user is exploring.
    const fps = state.quality < 1 ? (pointer.active ? 30 : 12) : 60;
    return {dots: 96, pins: 8, fps};
  }

  // Seeded positions stay stable when fonts, accordion or viewport sizes change.
  function generate() {
    let seed = 7319;
    const random = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
    const config = configuration();
    const count = Math.round(config.dots * state.quality);
    const heroBottom = state.zones[0]?.bottom || 850;
    state.dots = Array.from({length: count + config.pins}, (_, i) => {
      const pin = i >= count;
      const side = random();
      const inHero = !pin && i < count * .3;
      return {
        // More places around the hero, then a quiet, continuous trail below it.
        x: (side < .6 ? (i % 2 ? .93 : .07) + (random() - .5) * .12 : random()) * state.width,
        y: inHero ? 100 + random() * Math.max(100, heroBottom - 100) : random() * state.pageHeight,
        depth: .25 + random() * .75, phase: random() * Math.PI * 2,
        radius: pin ? 5 + random() * 2 : (inHero ? 2.2 + random() * 2.2 : 1.2 + random() * 1.4),
        color: i % 29 === 0 && !pin ? colors[3] : colors[i % 3],
        pin, heroBoost: inHero, dx: 0, dy: 0, influence: 0,
      };
    });
    state.routes = Array.from({length: 6}, (_, i) => ({
      x: state.width * (i % 2 ? .94 : .06),
      y: state.pageHeight * i / 6 + 100,
      span: Math.min(640, state.pageHeight / 5),
      bend: Math.min(150, state.width * .14) * (i % 2 ? -1 : 1),
    }));
  }

  function bounds(element, pad = 0) {
    const r = element.getBoundingClientRect();
    return {left: r.left - pad, top: r.top + state.scroll - pad,
      right: r.right + pad, bottom: r.bottom + state.scroll + pad};
  }

  function measure() {
    state.layoutDirty = false;
    state.scroll = window.scrollY;
    state.width = document.documentElement.clientWidth;
    state.height = window.innerHeight;
    state.pageHeight = document.documentElement.scrollHeight;
    const dpr = Math.min(window.devicePixelRatio || 1, state.quality < 1 ? 1 : 2);
    const width = Math.round(state.width * dpr);
    const height = Math.round(state.height * dpr);
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    state.zones = zones.flatMap(([selector, intensity]) => {
      const element = document.querySelector(selector);
      return element ? [{...bounds(element), intensity, selector}] : [];
    });
    const masks = [...document.querySelectorAll(protectedSelector)]
      .filter(element => element.getClientRects().length)
      .filter(element => {
        if (element.closest('.home-hero-copy')) return false;
        if (element.matches('.home-hero-visual') || element.closest('.home-hero-visual')) return false;
        const viewport = element.closest('[data-rail-viewport], .place-gallery');
        return !viewport || viewport === element;
      })
      .map(element => bounds(element, 12));
    // A whole rail/form already protects its descendants. Avoid repeatedly
    // clearing the same large pixels for every nested link and photograph.
    state.masks = masks.filter((rect, index) => !masks.some((outer, other) =>
      other !== index && outer.left <= rect.left && outer.right >= rect.right &&
      outer.top <= rect.top && outer.bottom >= rect.bottom &&
      (other < index || outer.right - outer.left > rect.right - rect.left ||
        outer.bottom - outer.top > rect.bottom - rect.top)));
    generate();
    const bands = isHome ? state.zones.filter(zone => !['.home-hero-search-panel', '.home-hero-stats', '.home-map-panel'].includes(zone.selector))
      .map((zone, index) => zone.top + (index === 0 ? 24 : -26)) :
      [...document.querySelectorAll('main > *, main section, .site-footer')]
        .filter(element => element.getClientRects().length)
        .map(element => bounds(element).top - 24)
        .sort((a, b) => a - b)
        .filter((y, index, all) => y > 100 && (index === 0 || y - all[index - 1] > 140));
    state.scenes = window.KidsMapLivingScene?.create({width: state.width, height: state.pageHeight, bands, masks: state.masks, connectHero: isHome}) || [];
    const shell = document.querySelector('.site-shell');
    const footer = document.querySelector('.site-footer');
    const hero = state.zones.find(zone => zone.selector === '.home-hero');
    const landmarkMasks = state.scenes.flatMap(route => route.nodes.map(node => ({
      left: node.x - node.radius - 12, right: node.x + node.radius + 12,
      top: node.y - node.radius - 12, bottom: node.y + node.radius + 12,
    })));
    state.scenes.push(...(window.KidsMapLivingScene?.createVertical({
      width: state.width, top: hero ? hero.bottom + 70 : 120,
      bottom: footer ? bounds(footer).bottom - 12 : state.pageHeight - 36,
      gutter: shell ? Math.max(0, bounds(shell).left) : 14, masks: [...state.masks, ...landmarkMasks],
    }) || []));
  }

  function intensityAt(y) {
    let intensity = .3;
    for (const zone of state.zones) {
      // Feather section boundaries; nested search/stats zones override hero.
      const distance = Math.max(zone.top - y, y - zone.bottom, 0);
      if (distance < 64) intensity += (zone.intensity - intensity) * (1 - distance / 64);
    }
    const footerFade = Math.min(1, Math.max(0, (state.pageHeight - y) / 180));
    return intensity * footerFade;
  }

  function drawRoutes() {
    ctx.lineWidth = 1;
    ctx.lineCap = 'round';
    ctx.strokeStyle = colors[0];
    for (const route of state.routes) {
      const y = route.y - state.scroll;
      if (y > state.height + 50 || y + route.span < -50) continue;
      ctx.globalAlpha = .14 * intensityAt(route.y + route.span / 2);
      ctx.setLineDash([1, 8]);
      ctx.lineDashOffset = -state.time * .003;
      const x = route.x + pointer.xShift * .4;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.bezierCurveTo(x + route.bend, y + route.span * .3,
        x - route.bend, y + route.span * .65, x + route.bend * .2, y + route.span);
      ctx.stroke();
      // A short solid segment reads as a path, never a proximity network.
      ctx.setLineDash([]);
      ctx.globalAlpha *= .45;
      ctx.beginPath();
      ctx.moveTo(x, y - 22);
      ctx.quadraticCurveTo(x - 4, y - 12, x, y);
      ctx.stroke();
    }
  }

  function drawPlaces(dt) {
    const easing = 1 - Math.exp(-dt / 150);
    const moving = !motion.matches;
    for (const dot of state.dots) {
      const baseY = dot.y - state.scroll;
      if (baseY < -35 || baseY > state.height + 35) continue;
      const phase = state.time * .00018 + dot.phase;
      const x = dot.x + (moving ? Math.sin(phase) * 4 * dot.depth : 0) + pointer.xShift * dot.depth;
      const y = baseY + (moving ? Math.cos(phase * .8) * 5 * dot.depth : 0) + pointer.yShift * dot.depth;
      const vx = x - pointer.x, vy = y - pointer.y;
      const distance = Math.hypot(vx, vy);
      const influence = pointer.active && moving ? Math.max(0, 1 - distance / 190) : 0;
      dot.dx += ((vx / (distance || 1)) * influence * 10 - dot.dx) * easing;
      dot.dy += ((vy / (distance || 1)) * influence * 10 - dot.dy) * easing;
      dot.influence += (influence - dot.influence) * easing;
      const px = x + dot.dx, py = y + dot.dy;
      const radius = dot.radius * (1 + dot.influence * .18);
      const baseOpacity = dot.heroBoost ? (.38 + dot.depth * .25) : (.2 + dot.depth * .12);
      const opacity = intensityAt(dot.y) * baseOpacity * (1 + dot.influence * .5);
      ctx.fillStyle = dot.color;
      ctx.strokeStyle = dot.color;
      if (dot.pin || dot.influence > .05) {
        ctx.globalAlpha = opacity * .16;
        ctx.beginPath(); ctx.arc(px, py, radius * 3, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = opacity * (moving ? .92 + Math.sin(phase) * .08 : 1);
      ctx.beginPath();
      if (dot.pin) {
        ctx.moveTo(px, py + radius * 1.45);
        ctx.bezierCurveTo(px - radius * 2, py - radius * .3, px - radius, py - radius * 1.5, px, py - radius);
        ctx.bezierCurveTo(px + radius, py - radius * 1.5, px + radius * 2, py - radius * .3, px, py + radius * 1.45);
        ctx.stroke();
        ctx.beginPath(); ctx.arc(px, py - radius * .25, radius * .27, 0, Math.PI * 2); ctx.fill();
      } else {
        ctx.arc(px, py, radius, 0, Math.PI * 2); ctx.fill();
      }
    }
  }

  function render(dt) {
    ctx.clearRect(0, 0, state.width, state.height);
    const ease = 1 - Math.exp(-dt / 220);
    const active = pointer.active && !motion.matches;
    pointer.xShift += ((active ? (pointer.x / state.width - .5) * 12 : 0) - pointer.xShift) * ease;
    pointer.yShift += ((active ? (pointer.y / state.height - .5) * 8 : 0) - pointer.yShift) * ease;
    drawRoutes();
    drawPlaces(dt);
    window.KidsMapLivingScene?.draw(ctx, state.scenes, {
      time: state.time, scroll: state.scroll, height: state.height,
      intensity: intensityAt, reduced: motion.matches, pointer,
      palette,
    });
    state.ripples = state.ripples.filter(ripple => state.time - ripple.start < 1000);
    for (const ripple of state.ripples) {
      const progress = (state.time - ripple.start) / 1000;
      const radius = 9 + (1 - Math.pow(1 - progress, 3)) * 105;
      ctx.strokeStyle = palette.green; ctx.lineWidth = 1.6; ctx.setLineDash([]);
      ctx.globalAlpha = .38 * Math.pow(1 - progress, 2);
      ctx.beginPath(); ctx.arc(ripple.x, ripple.y - state.scroll, radius, 0, Math.PI * 2); ctx.stroke();
      ctx.globalAlpha *= .5;
      ctx.beginPath(); ctx.arc(ripple.x, ripple.y - state.scroll, radius * .62, 0, Math.PI * 2); ctx.stroke();
    }
    // Clear generous safe areas even under transparent UI. Rects are cached,
    // so animation never forces DOM layout or follows moving carousel cards.
    for (const rect of state.masks) {
      const y = rect.top - state.scroll;
      if (y < state.height && rect.bottom > state.scroll) {
        ctx.clearRect(rect.left, y, rect.right - rect.left, rect.bottom - rect.top);
      }
    }
    ctx.globalAlpha = 1;
  }

  function schedule() {
    if (desktop.matches && !state.frame && !state.stopped && !document.hidden) state.frame = requestAnimationFrame(frame);
  }

  function frame(now) {
    state.frame = 0;
    if (!desktop.matches || state.stopped || document.hidden) return;
    const elapsed = state.last ? now - state.last : 17;
    const needsLayout = state.layoutDirty;
    if (needsLayout) measure();
    const interval = 1000 / configuration().fps;
    if (!needsLayout && !motion.matches && elapsed < interval - 1) { schedule(); return; }
    const drawnElapsed = state.drawnAt ? now - state.drawnAt : 17;
    state.drawnAt = now;
    // Carry the fractional frame budget on 90/120/144Hz screens. Resetting to
    // now would turn the 60 FPS target into 45 FPS on a 90Hz display.
    state.last = needsLayout || motion.matches ? now : state.last + interval * Math.max(1, Math.floor(elapsed / interval));
    const dt = Math.min(drawnElapsed, 50);
    if (!motion.matches) state.time += Math.min(drawnElapsed, 150);
    if (!motion.matches && drawnElapsed > interval * 1.45 && drawnElapsed < 200) state.slow++;
    else state.slow = Math.max(0, state.slow - 1);
    if (state.slow > 45 && state.quality > .5) {
      state.quality = .5; state.slow = 0; measure();
    }
    render(dt);
    if (!motion.matches) schedule();
  }

  function invalidate() { state.layoutDirty = true; schedule(); }
  function stop() {
    cancelAnimationFrame(state.frame);
    state.frame = 0; state.last = 0; state.drawnAt = 0; pointer.active = false;
  }
  function resetMotion() {
    stop();
    pointer.xShift = 0; pointer.yShift = 0;
    state.time = 0;
    state.ripples = [];
    for (const dot of state.dots) { dot.dx = 0; dot.dy = 0; dot.influence = 0; }
    schedule();
  }
  function updateAvailability() {
    resetMotion();
    state.layoutDirty = true;
    if (!desktop.matches) {
      // Release a previously allocated desktop bitmap as well as geometry.
      canvas.width = 1; canvas.height = 1;
      state.dots = []; state.routes = []; state.scenes = [];
      state.zones = []; state.masks = [];
    }
  }
  function destroy() {
    state.stopped = true;
    stop();
    observer?.disconnect();
    state.cleanup.forEach(remove => remove());
  }

  listen(window, 'pointermove', event => {
    if (!desktop.matches || !mouse.matches || motion.matches || event.pointerType !== 'mouse') return;
    pointer.x = event.clientX; pointer.y = event.clientY; pointer.active = true;
  }, {passive: true});
  listen(window, 'pointerdown', event => {
    if (!desktop.matches || motion.matches || event.button !== 0 || event.isPrimary === false) return;
    if (event.target?.closest?.('a, button, input, select, textarea, summary, form, [role="button"], [role="dialog"], .leaflet-container, .gm-style')) return;
    state.ripples.push({x: event.clientX, y: event.clientY + state.scroll, start: state.time});
    if (state.ripples.length > 4) state.ripples.shift();
    schedule();
  }, {passive: true});
  listen(document, 'pointerleave', () => { pointer.active = false; });
  listen(window, 'blur', () => { pointer.active = false; });
  listen(window, 'scroll', () => { state.scroll = window.scrollY; pointer.active = false; schedule(); }, {passive: true});
  listen(window, 'resize', invalidate, {passive: true});
  listen(document, 'visibilitychange', () => { stop(); if (!document.hidden) invalidate(); });
  listen(motion, 'change', resetMotion);
  listen(mouse, 'change', resetMotion);
  listen(desktop, 'change', updateAvailability);
  listen(window, 'pagehide', event => { if (event.persisted) stop(); else destroy(); });
  listen(window, 'pageshow', invalidate);
  // Existing reveal transitions and FAQ expansion can move exclusion areas.
  listen(document, 'transitionend', invalidate);
  listen(document, 'toggle', invalidate, true);
  const observer = typeof ResizeObserver === 'function' ? new ResizeObserver(invalidate) : null;
  observer?.observe(document.querySelector('.site-shell') || document.body);
  document.fonts?.ready.then(() => { if (!state.stopped) invalidate(); });
  updateAvailability();
})();
