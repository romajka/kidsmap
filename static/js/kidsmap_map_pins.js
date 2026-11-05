/* KidsMap — shared map pin & cluster visuals (home, catalog, detail).
 *
 * Builds DOM visuals for the existing public marker wrapper
 * (google_maps_markers.js → createPublicMarker): pins and clusters are real
 * elements, so hover / focus / selected / visited states and motion live in
 * CSS (components/google_maps.css, "km-pin" / "km-cluster").
 *
 * Category icons arrive as server-side SVG strings. They are rendered through
 * <img src="data:..."> only — never injected as markup — so an icon can never
 * run script in the page.
 */
(function () {
  'use strict';

  var FALLBACK_GLYPH =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
    '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>';
  var DEFAULT_INK = '#136f38';
  var DEFAULT_TINT = '#e8f3e5';
  var HEX = /^#[0-9a-f]{3,8}$/i;
  var VISITED_KEY = 'kidsmap:visited-places';

  function safeColor(value, fallback) {
    var color = String(value || '').trim();
    return HEX.test(color) ? color : fallback;
  }

  function glyphUrl(place, color) {
    var source = (place && place.category_icon_svg) || FALLBACK_GLYPH;
    if (!/^\s*<svg[\s>]/i.test(source)) source = FALLBACK_GLYPH;
    if (!/xmlns=/.test(source)) source = source.replace(/<svg/i, '<svg xmlns="http://www.w3.org/2000/svg"');
    return 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(source.replace(/currentColor/g, color));
  }

  function members(point) {
    return Array.isArray(point && point.members) && point.members.length ? point.members : (point ? [point] : []);
  }

  // ── Visited (per viewer, best effort) ────────────────────────────────────
  var visitedCache = null;
  function visitedSet() {
    if (visitedCache) return visitedCache;
    visitedCache = new Set();
    try {
      var raw = window.sessionStorage.getItem(VISITED_KEY);
      (raw ? JSON.parse(raw) : []).forEach(function (id) { visitedCache.add(String(id)); });
    } catch (error) { /* storage unavailable: visited state is optional */ }
    return visitedCache;
  }
  function isVisited(point) {
    var seen = visitedSet();
    var list = members(point);
    return list.length > 0 && list.every(function (m) { return seen.has(String(m.id || m.url || '')); });
  }
  function markVisited(point) {
    var seen = visitedSet();
    members(point).forEach(function (m) { seen.add(String(m.id || m.url || '')); });
    try { window.sessionStorage.setItem(VISITED_KEY, JSON.stringify(Array.from(seen).slice(-300))); } catch (error) { /* optional */ }
  }

  // ── Place pin ────────────────────────────────────────────────────────────
  // 40 × 50 box, anchored at the tip (20, 50).
  var PIN = {width: 40, height: 50, anchorX: 20, anchorY: 50};

  function placePin(point) {
    var ink = safeColor(point && point.category_color_text, DEFAULT_INK);
    var tint = safeColor(point && point.category_color_bg, DEFAULT_TINT);
    var count = members(point).length;

    var pin = document.createElement('span');
    pin.className = 'km-pin';
    pin.style.setProperty('--pin-ink', ink);
    pin.style.setProperty('--pin-tint', tint);
    if (isVisited(point)) pin.classList.add('is-visited');

    var drop = document.createElement('span');
    drop.className = 'km-pin__drop';
    var medal = document.createElement('span');
    medal.className = 'km-pin__medal';
    var glyph = document.createElement('img');
    glyph.className = 'km-pin__glyph';
    glyph.src = glyphUrl(point, ink);
    glyph.alt = '';
    glyph.draggable = false;
    glyph.setAttribute('aria-hidden', 'true');
    medal.append(glyph);
    drop.append(medal);
    pin.append(drop);

    if (count > 1) {
      var badge = document.createElement('span');
      badge.className = 'km-pin__badge';
      badge.textContent = String(count);
      pin.append(badge);
    }

    var label = document.createElement('span');
    label.className = 'km-pin__label';
    label.textContent = (point && (point.name || (members(point)[0] || {}).name)) || '';
    pin.append(label);

    var check = document.createElement('span');
    check.className = 'km-pin__visited';
    check.setAttribute('aria-hidden', 'true');
    pin.append(check);
    return pin;
  }

  // ── Cluster ──────────────────────────────────────────────────────────────
  function clusterTier(total) {
    if (total >= 50) return {name: 'l', size: 56};
    if (total >= 10) return {name: 'm', size: 48};
    return {name: 's', size: 40};
  }

  // Counts places (not location points) per category colour for the ring.
  function clusterSummary(markers) {
    var byColor = new Map();
    var total = 0;
    (markers || []).forEach(function (marker) {
      members(marker && marker.__kidsMapPlace).forEach(function (place) {
        var root = marker.__kidsMapPlace || {};
        var color = safeColor(place.category_color_text || root.category_color_text, DEFAULT_INK);
        byColor.set(color, (byColor.get(color) || 0) + 1);
        total += 1;
      });
    });
    if (!total) total = (markers || []).length;
    var parts = Array.from(byColor.entries()).sort(function (a, b) { return b[1] - a[1]; });
    if (parts.length > 4) {
      var rest = parts.slice(3).reduce(function (sum, part) { return sum + part[1]; }, 0);
      parts = parts.slice(0, 3).concat([[DEFAULT_INK, rest]]);
    }
    return {total: total, parts: parts};
  }

  function ringGradient(parts, total) {
    if (!parts.length) return DEFAULT_INK;
    if (parts.length === 1) return parts[0][0];
    var at = 0;
    var stops = parts.map(function (part) {
      var from = at;
      at += (part[1] / total) * 360;
      return part[0] + ' ' + from.toFixed(1) + 'deg ' + at.toFixed(1) + 'deg';
    });
    return 'conic-gradient(' + stops.join(', ') + ')';
  }

  function cluster(markers) {
    var summary = clusterSummary(markers);
    var tier = clusterTier(summary.total);
    var root = document.createElement('span');
    root.className = 'km-cluster km-cluster--' + tier.name;
    root.style.setProperty('--cluster-size', tier.size + 'px');
    root.style.setProperty('--cluster-ring', ringGradient(summary.parts, summary.total));
    var ring = document.createElement('span');
    ring.className = 'km-cluster__ring';
    var core = document.createElement('span');
    core.className = 'km-cluster__core';
    var value = document.createElement('span');
    value.className = 'km-cluster__count';
    value.textContent = summary.total > 99 ? '99+' : String(summary.total);
    core.append(value);
    root.append(ring, core);
    return {element: root, size: tier.size, total: summary.total};
  }

  // ── Basemap style (raster maps without a Cloud Map ID) ───────────────────
  // Hides business POIs and transit clutter so KidsMap pins lead; keeps parks,
  // schools-free and calm pastel water/green. Ignored by Google when a mapId
  // is set (Cloud styling then applies).
  var STYLES = [
    {featureType: 'poi', elementType: 'labels.icon', stylers: [{visibility: 'off'}]},
    {featureType: 'poi.business', stylers: [{visibility: 'off'}]},
    {featureType: 'poi.medical', stylers: [{visibility: 'off'}]},
    {featureType: 'poi.government', stylers: [{visibility: 'off'}]},
    {featureType: 'poi.place_of_worship', stylers: [{visibility: 'off'}]},
    {featureType: 'poi.school', stylers: [{visibility: 'off'}]},
    {featureType: 'poi.attraction', elementType: 'labels', stylers: [{visibility: 'off'}]},
    {featureType: 'poi.park', elementType: 'geometry', stylers: [{color: '#d9eed3'}]},
    {featureType: 'poi.park', elementType: 'labels.text.fill', stylers: [{color: '#4b7a52'}]},
    {featureType: 'transit', stylers: [{visibility: 'off'}]},
    {featureType: 'road', elementType: 'labels.icon', stylers: [{visibility: 'off'}]},
    {featureType: 'road.highway', elementType: 'geometry.fill', stylers: [{color: '#ffffff'}]},
    {featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{color: '#e3e8e1'}]},
    {featureType: 'road.arterial', elementType: 'labels.text.fill', stylers: [{color: '#7c8a80'}]},
    {featureType: 'landscape', elementType: 'geometry', stylers: [{color: '#f6f8f3'}]},
    {featureType: 'water', elementType: 'geometry', stylers: [{color: '#c9e6ef'}]},
    {featureType: 'water', elementType: 'labels.text.fill', stylers: [{color: '#5f8e9c'}]},
    {featureType: 'administrative', elementType: 'labels.text.fill', stylers: [{color: '#5b6b60'}]},
  ];

  // Shared map options for every public KidsMap map.
  function applyMapDefaults(options, mapId) {
    options.clickableIcons = false;
    if (!mapId) options.styles = STYLES;
    return options;
  }

  window.KidsMapPins = {
    PIN: PIN,
    placePin: placePin,
    cluster: cluster,
    clusterSummary: clusterSummary,
    markVisited: markVisited,
    isVisited: isVisited,
    styles: STYLES,
    applyMapDefaults: applyMapDefaults,
  };
})();
