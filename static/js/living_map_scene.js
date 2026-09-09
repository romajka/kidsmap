/* Small map stories, laid out in public pages' real open spaces.
   Park/book/art/trophy geometry follows static/icons/categories/*.svg. */
(() => {
  'use strict';
  const icons = {
    map: 'M3 5 9 2 15 5 21 2V19L15 22 9 19 3 22Z M9 2V19 M15 5V22',
    park: 'M10 22v-6.5 M18 22v-5 M10 15.5a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9 M18 17a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7',
    book: 'M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20 M8 6H16 M8 10H14',
    art: 'M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c2 0 2-2 1-3s0-3 1.5-3H16c3 0 6-2 6-5S18 2 12 2Z M8 7h.1 M14 6h.1 M18 10h.1 M6 12h.1',
    trophy: 'M6 9H4.5a2.5 2.5 0 0 1 0-5H6 M18 9h1.5a2.5 2.5 0 0 0 0-5H18 M4 22h16 M10 16V19L7 22 M14 16V19L17 22 M18 2H6v7c0 6 4 9 6 9s6-3 6-9V2Z',
  };
  const paths = new Map();
  const clamp = value => Math.max(0, Math.min(1, value));
  const ease = value => value * value * (3 - 2 * value);

  function timeline(time, delay, reduced = false) {
    if (reduced) return {progress: 1, opacity: 1};
    const phase = ((time + delay) % 12000) / 12000;
    return {progress: ease(clamp(phase / .68)), opacity: 1 - ease(clamp((phase - .84) / .16))};
  }

  function create({width, height, bands, masks, connectHero = true}) {
    const mobile = width < 768;
    const radius = mobile ? 17 : 21;
    const occupied = [];
    function clear(x, y) {
      return x >= radius + 3 && x <= width - radius - 3 && y > radius + 80 && y < height - radius &&
        !masks.some(r => x + radius > r.left && x - radius < r.right && y + radius > r.top && y - radius < r.bottom) &&
        !occupied.some(p => Math.hypot(p.x - x, p.y - y) < radius * 3);
    }
    function locate(x, y) {
      // Prefer the intended horizontal corridor; shift only if UI occupies it.
      for (let distance = 0; distance <= 112; distance += 8) {
        const offsets = distance ? [[0, -distance], [0, distance], [-distance, 0], [distance, 0]] : [[0, 0]];
        for (const [dx, dy] of offsets) if (clear(x + dx, y + dy)) return {x: x + dx, y: y + dy};
      }
      return null;
    }
    const routes = [];
    for (const [index, y] of bands.entries()) {
      const targets = mobile ? [34, width - 34] : [width * .09, width * .52, width * .91];
      const kinds = ['map', 'park', 'art', 'book', 'trophy'];
      const nodes = targets.flatMap((x, i) => {
        const point = locate(x, y);
        if (!point) return [];
        occupied.push(point);
        return [{...point, kind: kinds[(index * 2 + i) % kinds.length], radius}];
      }).sort((a, b) => a.x - b.x);
      if (nodes.length < 2) continue;
      const points = [];
      for (let leg = 0; leg < nodes.length - 1; leg++) {
        const a = nodes[leg], b = nodes[leg + 1];
        const bend = (index % 2 ? 1 : -1) * (mobile ? 16 : 28);
        for (let sample = 0; sample <= 48; sample++) {
          const t = sample / 48, u = 1 - t;
          points.push({x: a.x + (b.x - a.x) * t,
            y: u * u * u * a.y + 3 * u * u * t * (a.y + bend) + 3 * u * t * t * (b.y - bend) + t * t * t * b.y});
        }
      }
      nodes.forEach((node, i) => { node.at = i / (nodes.length - 1); });
      routes.push({nodes, points, top: Math.min(...points.map(p => p.y)) - 50,
        bottom: Math.max(...points.map(p => p.y)) + 50, delay: index * 1800});
    }
    // Two rounded streets connect the hero's top and bottom corridors.
    // Keep these in desktop gutters; mobile has no room for side streets.
    if (connectHero && width >= 1024 && routes.length > 1) {
      for (const side of [0, 1]) {
        const a = side ? routes[0].nodes.at(-1) : routes[0].nodes[0];
        const b = side ? routes[1].nodes.at(-1) : routes[1].nodes[0];
        if (b.y - a.y < 260) continue;
        const edge = side ? width - 34 : 34;
        const point = locate(edge, (a.y + b.y) / 2);
        if (!point) continue;
        occupied.push(point);
        const node = {...point, kind: side ? 'trophy' : 'book', radius, at: .5};
        const points = [];
        for (let i = 0; i <= 24; i++) {
          const t = i / 24, u = 1 - t;
          points.push({x: u * u * a.x + 2 * u * t * edge + t * t * edge,
            y: a.y + t * t * 90});
        }
        for (let i = 1; i <= 36; i++) points.push({x: edge, y: a.y + 90 + (b.y - a.y - 180) * i / 36});
        for (let i = 1; i <= 24; i++) {
          const t = i / 24, u = 1 - t;
          points.push({x: u * u * edge + 2 * u * t * edge + t * t * b.x,
            y: u * u * (b.y - 90) + 2 * u * t * b.y + t * t * b.y});
        }
        routes.push({nodes: [node], points, top: a.y - 50, bottom: b.y + 50, delay: side ? 2400 : 6000});
      }
    }
    return routes;
  }

  function createVertical({width, top, bottom, gutter, masks}) {
    if (bottom - top < 100) return [];
    const edge = Math.min(38, Math.max(6, gutter / 2));
    const bend = Math.min(10, Math.max(0, (gutter - 20) / 5));
    const entry = gutter + 28;
    const turnHeight = Math.min((bottom - top) * .6, Math.max(120, Math.min(360, (entry - edge) * .9)));
    const turnTop = bottom - turnHeight;
    const steps = Math.ceil((turnTop - top) / 24);
    return [0, 1].map(side => {
      const wave = y => edge + Math.sin((y - top) / 210) * bend;
      const mirror = (x, y) => ({x: side ? width - x : x, y});
      const points = Array.from({length: steps + 1}, (_, i) => {
        const y = top + (turnTop - top) * i / steps;
        return mirror(wave(y), y);
      });
      // Match the side street's tangent, then ease into a horizontal footer
      // entry. Curve height scales with the gutter instead of squeezing a
      // wide turn into the final 100px. Dense curve samples remove faceting.
      const startX = wave(turnTop);
      const slope = Math.cos((turnTop - top) / 210) * bend / 210;
      const controlX = startX + slope * turnHeight * .55;
      const controlY = turnTop + turnHeight * .55;
      const curveSteps = Math.ceil((turnHeight + entry - startX) / 1.5);
      for (let i = 1; i <= curveSteps; i++) {
        const t = i / curveSteps, u = 1 - t;
        points.push(mirror(
          u ** 3 * startX + 3 * u * u * t * controlX + 3 * u * t * t * (entry - (entry - startX) * .45) + t ** 3 * entry,
          u ** 3 * turnTop + 3 * u * u * t * controlY + 3 * u * t * t * bottom + t ** 3 * bottom,
        ));
      }
      let distance = 0;
      const distances = points.map((point, i) => {
        if (i) distance += Math.hypot(point.x - points[i - 1].x, point.y - points[i - 1].y);
        return distance;
      });
      const nodes = [];
      const kinds = ['park', 'map', 'book', 'art', 'trophy'];
      if (gutter >= 48) {
        for (let y = top + 180 + side * 190; y < bottom - 120; y += 520) {
          const point = pointAtY(points, y);
          const radius = 18;
          // Include the hover halo in collision clearance.
          if (masks.some(r => point.x + radius + 7 > r.left && point.x - radius - 7 < r.right &&
              y + radius + 7 > r.top && y - radius - 7 < r.bottom)) continue;
          nodes.push({...point, kind: kinds[(nodes.length + side * 2) % kinds.length], radius, at: 0});
        }
      }
      return {vertical: true, side, points, distances, nodes, top, bottom};
    });
  }

  function pointAt(points, progress) {
    const position = clamp(progress) * (points.length - 1);
    const index = Math.floor(position), fraction = position - index;
    const a = points[index], b = points[Math.min(index + 1, points.length - 1)];
    return {x: a.x + (b.x - a.x) * fraction, y: a.y + (b.y - a.y) * fraction, index};
  }

  function pointOnAxis(points, target, valueAt) {
    let low = 0, high = points.length - 1;
    while (high - low > 1) {
      const middle = (low + high) >> 1;
      if (valueAt(middle) <= target) low = middle;
      else high = middle;
    }
    const fraction = clamp((target - valueAt(low)) / (valueAt(high) - valueAt(low) || 1));
    const a = points[low], b = points[high];
    return {x: a.x + (b.x - a.x) * fraction, y: a.y + (b.y - a.y) * fraction, index: low};
  }

  function pointAtY(points, y) { return pointOnAxis(points, y, index => points[index].y); }
  function pointAtDistance(route, distance) {
    return pointOnAxis(route.points, distance, index => route.distances[index]);
  }

  function strokeDistance(ctx, route, from, to) {
    const a = pointAtDistance(route, Math.min(from, to));
    const b = pointAtDistance(route, Math.max(from, to));
    strokePath(ctx, [a, ...route.points.slice(a.index + 1, b.index + 1), b]);
  }

  function strokePath(ctx, points, end = points.length, tip) {
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < end; i++) ctx.lineTo(points[i].x, points[i].y);
    if (tip) ctx.lineTo(tip.x, tip.y);
    ctx.stroke();
  }

  function landmark(ctx, node, story, time, opacity, palette, pointer, reduced) {
    const arrive = reduced ? 1 : clamp((story.progress - node.at + .1) / .1);
    const pulse = reduced ? 0 : Math.sin(arrive * Math.PI);
    const near = pointer.active ? clamp(1 - Math.hypot(pointer.x - node.x, pointer.y - node.y) / 190) : 0;
    const scale = .88 + ease(arrive) * .12 + pulse * .14 + near * .12;
    ctx.save();
    ctx.translate(node.x, node.y + (reduced ? 0 : Math.sin(time * .001 + node.x) * 2));
    ctx.scale(scale, scale);
    ctx.setLineDash([]);
    ctx.globalAlpha = opacity * (.1 + pulse * .2 + near * .1);
    ctx.fillStyle = palette.mint;
    ctx.beginPath(); ctx.arc(0, 0, node.radius + 7 + pulse * 8, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = opacity * .9;
    ctx.fillStyle = palette.paper;
    ctx.beginPath(); ctx.arc(0, 0, node.radius, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = palette.green;
    ctx.lineWidth = 1.3;
    ctx.globalAlpha = opacity * (.28 + arrive * .3);
    ctx.stroke();
    ctx.globalAlpha = opacity * (.5 + arrive * .4);
    const size = node.radius * (node.kind === 'map' ? 1.3 : 1.1);
    ctx.translate(-size / 2, -size / 2);
    ctx.scale(size / 24, size / 24);
    ctx.lineWidth = 1.65;
    if (!paths.has(node.kind)) paths.set(node.kind, new Path2D(icons[node.kind]));
    ctx.stroke(paths.get(node.kind));
    ctx.restore();
  }

  function drawVertical(ctx, route, {time, scroll, height, palette, pointer, reduced}) {
    const atY = y => pointAtY(route.points, y);
    const first = atY(scroll - 40).index;
    const last = atY(scroll + height + 40).index + 2;
    const near = pointer.active && !reduced ? Math.max(0, 1 - Math.abs(atY(pointer.y + scroll).x - pointer.x) / 150) : 0;
    ctx.strokeStyle = palette.green;
    ctx.lineWidth = 1.4 + near * .5;
    ctx.setLineDash([3, 8]);
    ctx.globalAlpha = .22 + near * .13;
    strokePath(ctx, route.points.slice(first, last));
    ctx.setLineDash([]);
    if (!reduced) {
      const phase = ((time * .07 * (route.side ? 1 : -1)) % 680 + 680) % 680;
      const length = route.distances.at(-1);
      for (let distance = phase; distance < length; distance += 680) {
        const tip = pointAtDistance(route, distance);
        if (tip.y < scroll - 150 || tip.y > scroll + height + 150) continue;
        // A tapered trail makes the direction visible without flashing.
        for (let tail = 6; tail >= 0; tail--) {
          const from = distance + (route.side ? -1 : 1) * tail * 19;
          const to = from + (route.side ? -1 : 1) * 19;
          if (from < 0 || to > length || to < 0 || from > length) continue;
          ctx.globalAlpha = (.65 + near * .15) * (1 - tail / 7);
          ctx.lineWidth = 2.4;
          strokeDistance(ctx, route, from, to);
        }
        ctx.fillStyle = palette.green; ctx.globalAlpha = .1;
        ctx.beginPath(); ctx.arc(tip.x, tip.y, 11, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = .8;
        ctx.beginPath(); ctx.arc(tip.x, tip.y, 3.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = palette.paper; ctx.globalAlpha = 1;
        ctx.beginPath(); ctx.arc(tip.x, tip.y, 1.4, 0, Math.PI * 2); ctx.fill();
      }
    }
    for (const node of route.nodes) {
      if (node.y < scroll - 40 || node.y > scroll + height + 40) continue;
      landmark(ctx, node, {progress: 1, opacity: 1}, time, .7, palette,
        {x: pointer.x, y: pointer.y + scroll, active: pointer.active && !reduced}, reduced);
    }
  }

  function draw(ctx, routes, {time, scroll, height, intensity, palette, pointer, reduced}) {
    ctx.save();
    ctx.translate(0, -scroll);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const route of routes) {
      if (route.top > scroll + height || route.bottom < scroll) continue;
      if (route.vertical) {
        drawVertical(ctx, route, {time, scroll, height, palette, pointer, reduced});
        continue;
      }
      const strength = Math.max(.35, intensity(route.nodes[0].y));
      const story = timeline(time, route.delay, reduced);
      const points = route.points;
      // A quiet complete cartographic trail remains behind the growing route.
      ctx.strokeStyle = palette.green;
      ctx.setLineDash([2, 7]); ctx.lineWidth = 1.3;
      ctx.globalAlpha = strength * .3;
      strokePath(ctx, points);
      ctx.setLineDash([]); ctx.lineWidth = 2;
      ctx.globalAlpha = strength * .62 * story.opacity;
      const tip = pointAt(points, story.progress);
      strokePath(ctx, points, tip.index + 1, tip);
      if (!reduced && story.progress < 1) {
        ctx.globalAlpha = strength * .13; ctx.fillStyle = palette.green;
        ctx.beginPath(); ctx.arc(tip.x, tip.y, 12, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = strength * .85;
        ctx.beginPath(); ctx.arc(tip.x, tip.y, 4, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = strength; ctx.fillStyle = palette.paper;
        ctx.beginPath(); ctx.arc(tip.x, tip.y, 1.6, 0, Math.PI * 2); ctx.fill();
      }
      for (const node of route.nodes) landmark(ctx, node, story, time, strength, palette,
        {x: pointer.x, y: pointer.y + scroll, active: pointer.active && !reduced}, reduced);
    }
    ctx.restore();
  }
  window.KidsMapLivingScene = {create, createVertical, timeline, pointAt, pointAtDistance, draw};
})();
