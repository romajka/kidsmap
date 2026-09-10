(function () {
  'use strict';
  const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  const reduced = () => motionQuery.matches;
  const literal = p => ({ lat: p.lat(), lng: p.lng() });

  // Membership changes are batched; surviving marker objects stay attached.
  function membership(clusterer, initialMarkers) {
    let current = new Set(initialMarkers || []);
    return function (markers) {
      const next = new Set(markers);
      const removed = [...current].filter(marker => !next.has(marker));
      const added = markers.filter(marker => !current.has(marker));
      if (removed.length) clusterer.removeMarkers(removed, true);
      if (added.length) clusterer.addMarkers(added, true);
      if (removed.length || added.length) clusterer.render();
      current = next;
    };
  }

  function create(map) {
    let frame = null, nativeMoving = false, selected = null;
    const mapEl = map.getDiv();
    function cancel() {
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null;
      if (nativeMoving) {
        nativeMoving = false;
        map.moveCamera({center: literal(map.getCenter()), zoom: map.getZoom()});
      }
    }
    // Capture before Google consumes the gesture. A marker's click can then
    // start a new transition, while wheel/drag/keyboard always take priority.
    ['pointerdown', 'touchstart', 'wheel', 'keydown'].forEach(name => {
      mapEl.addEventListener(name, cancel, {capture: true, passive: true});
    });
    map.addListener('dragstart', cancel);
    map.addListener('idle', () => { nativeMoving = false; });
    motionQuery.addEventListener('change', cancel);
    document.addEventListener('visibilitychange', () => { if (document.hidden) cancel(); });

    function moveTo(target, bounds) {
      cancel();
      if (reduced()) { map.moveCamera(target); return; }
      const vector = map.getRenderingType && map.getRenderingType() === 'VECTOR' && map.get('isFractionalZoomEnabled');
      if (!vector) {
        // Raster zoom uses Google's own tile transition. Never emulate
        // fractional zoom by repeatedly rounding setZoom on animation frames.
        if (bounds) { nativeMoving = true; map.fitBounds(bounds, 56); }
        else { nativeMoving = true; map.panTo(target.center); }
        return;
      }
      const start = literal(map.getCenter()), startZoom = map.getZoom(), started = performance.now();
      let deltaLng = target.center.lng - start.lng;
      if (deltaLng > 180) deltaLng -= 360;
      if (deltaLng < -180) deltaLng += 360;
      function step(now) {
        const t = Math.min(1, (now - started) / 520);
        const eased = t * t * (3 - 2 * t);
        map.moveCamera({
          center: {lat: start.lat + (target.center.lat - start.lat) * eased, lng: start.lng + deltaLng * eased},
          zoom: startZoom + (target.zoom - startZoom) * eased,
        });
        frame = t < 1 ? requestAnimationFrame(step) : null;
      }
      frame = requestAnimationFrame(step);
    }

    function expand(cluster, choose) {
      cancel();
      const markers = cluster.markers || [];
      if (!markers.length) return;
      const first = markers[0].getPosition();
      const coincident = markers.every(marker => {
        const p = marker.getPosition(); return p.lat() === first.lat() && p.lng() === first.lng();
      });
      if (coincident || map.getZoom() >= 18) { choose(markers); return; }
      const bounds = cluster.bounds, projection = map.getProjection();
      if (!bounds || !projection) return;
      const ne = projection.fromLatLngToPoint(bounds.getNorthEast());
      const sw = projection.fromLatLngToPoint(bounds.getSouthWest());
      const dx = (ne.x - sw.x + 256) % 256, dy = Math.abs(sw.y - ne.y);
      const width = Math.max(1, mapEl.clientWidth - 112), height = Math.max(1, mapEl.clientHeight - 112);
      const fittingZoom = Math.floor(Math.min(Math.log2(width / Math.max(dx, 1e-9)), Math.log2(height / Math.max(dy, 1e-9))));
      const vector = map.getRenderingType && map.getRenderingType() === 'VECTOR' && map.get('isFractionalZoomEnabled');
      const maxStepZoom = vector ? 18 : Math.min(18, Math.floor(map.getZoom()) + 2);
      const zoom = Math.min(maxStepZoom, fittingZoom);
      // No intermediate zoom-out and no endless zoom at unresolvable density.
      if (zoom <= map.getZoom()) { choose(markers); return; }
      const center = literal(projection.fromPointToLatLng(new google.maps.Point((sw.x + dx / 2) % 256, (sw.y + ne.y) / 2)));
      let nativeBounds = bounds;
      if (fittingZoom > zoom) {
        // Expand only the camera bounds, never place coordinates. This caps a
        // native fit without temporary maxZoom options or racing idle resets.
        const middle = projection.fromLatLngToPoint(new google.maps.LatLng(center));
        const halfX = width / (2 * Math.pow(2, zoom)) * .999;
        const halfY = height / (2 * Math.pow(2, zoom)) * .999;
        nativeBounds = new google.maps.LatLngBounds(
          projection.fromPointToLatLng(new google.maps.Point(middle.x - halfX, middle.y + halfY)),
          projection.fromPointToLatLng(new google.maps.Point(middle.x + halfX, middle.y - halfY))
        );
      }
      moveTo({center, zoom}, nativeBounds);
    }

    function select(marker) {
      if (selected && selected.setSelected) selected.setSelected(false);
      selected = marker || null;
      if (selected && selected.setSelected) selected.setSelected(true);
    }
    return {cancel, moveTo, expand, select};
  }

  const labels = {
    az: {choose: 'Məkan seçin', close: 'Bağla', places: 'məkan'},
    ru: {choose: 'Выберите место', close: 'Закрыть', places: 'мест'},
    en: {choose: 'Choose a place', close: 'Close', places: 'places'},
  };
  function languageLabels() { return labels[(document.documentElement.lang || 'az').slice(0, 2)] || labels.az; }
  function clusterTitle(count) {
    let noun = languageLabels().places;
    if ((document.documentElement.lang || '').startsWith('ru')) {
      const last = count % 10, teens = count % 100 >= 11 && count % 100 <= 14;
      noun = !teens && last === 1 ? 'место' : !teens && last >= 2 && last <= 4 ? 'места' : 'мест';
    }
    return count + ' ' + noun;
  }

  // One local, non-modal chooser: no extra InfoWindow and no changed positions.
  function chooser(mapEl, openPlace) {
    let panel = null, trigger = null;
    function close(restore) {
      if (panel) panel.remove();
      panel = null;
      if (restore && trigger && trigger.isConnected) trigger.focus();
    }
    function show(markers, anchor) {
      close(false);
      trigger = anchor?.getElement?.() || document.activeElement;
      panel = document.createElement('section');
      panel.className = 'kidsmap-map-chooser';
      panel.setAttribute('aria-label', languageLabels().choose);
      const header = document.createElement('div'); header.className = 'kidsmap-map-chooser__header';
      const title = document.createElement('strong'); title.textContent = languageLabels().choose;
      const closeButton = document.createElement('button'); closeButton.type = 'button'; closeButton.textContent = '×';
      closeButton.setAttribute('aria-label', languageLabels().close);
      closeButton.addEventListener('click', () => close(true));
      header.append(title, closeButton); panel.append(header);
      const list = document.createElement('ul');
      markers.forEach(marker => {
        const place = marker.__kidsMapPlace;
        if (!place) return;
        const row = document.createElement('li'), button = document.createElement('button'); button.type = 'button';
        if (marker.__kidsMapIcon?.url) {
          const img = document.createElement('img'); img.src = marker.__kidsMapIcon.url; img.alt = ''; button.append(img);
        }
        const name = document.createElement('span'); name.textContent = place.name; button.append(name);
        button.addEventListener('click', () => { close(false); openPlace(place, marker); });
        row.append(button); list.append(row);
      });
      panel.append(list);
      panel.addEventListener('keydown', event => { if (event.key === 'Escape') { event.stopPropagation(); close(true); } });
      // Keep map drag/keyboard handlers out of scrollable place choices.
      ['pointerdown', 'touchstart', 'click', 'wheel', 'keydown'].forEach(name => panel.addEventListener(name, event => event.stopPropagation()));
      mapEl.append(panel); list.querySelector('button')?.focus({preventScroll: true});
    }
    return {show, close};
  }

  window.KidsMapGoogleMotion = {create, membership, chooser, clusterTitle, reduced};
})();
