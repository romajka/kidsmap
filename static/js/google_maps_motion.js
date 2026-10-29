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
    az: {
      choose: 'Məkan seçin',
      close: 'Bağla',
      places: 'məkan',
      locationTag: 'Bu məkanda',
      placesCount: (n) => `${n} yer`,
      cardHint: 'Xəritədə baxmaq üçün məkana klikləyin',
      details: 'Ətraflı',
    },
    ru: {
      choose: 'Выберите место',
      close: 'Закрыть',
      places: 'мест',
      locationTag: 'В этой локации',
      placesCount: (n) => {
        const last = n % 10, teens = n % 100 >= 11 && n % 100 <= 14;
        const noun = !teens && last === 1 ? 'место' : (!teens && last >= 2 && last <= 4 ? 'места' : 'мест');
        return `${n} ${noun}`;
      },
      cardHint: 'Нажмите на карточку, чтобы посмотреть на карте',
      details: 'Подробнее',
    },
    en: {
      choose: 'Choose a place',
      close: 'Close',
      places: 'places',
      locationTag: 'At this location',
      placesCount: (n) => `${n} ${n === 1 ? 'place' : 'places'}`,
      cardHint: 'Click a card to view on map',
      details: 'Details',
    },
  };
  function languageLabels() { return labels[((typeof document !== 'undefined' && document.documentElement?.lang) || 'az').slice(0, 2)] || labels.az; }
  function clusterTitle(count) {
    let noun = languageLabels().places;
    const lang = (typeof document !== 'undefined' && document.documentElement?.lang) || '';
    if (lang.startsWith('ru')) {
      const last = count % 10, teens = count % 100 >= 11 && count % 100 <= 14;
      noun = !teens && last === 1 ? 'место' : !teens && last >= 2 && last <= 4 ? 'места' : 'мест';
    }
    return count + ' ' + noun;
  }

  // One local, non-modal chooser: rich cards for co-located places
  function chooser(mapEl, openPlace) {
    let panel = null, trigger = null;
    function close(restore) {
      if (panel) panel.remove();
      panel = null;
      if (restore && trigger && trigger.isConnected) trigger.focus();
    }

    function extractEntries(markers) {
      const seen = new Set();
      const entries = [];
      (markers || []).forEach(marker => {
        const rootPlace = marker.__kidsMapPlace;
        if (!rootPlace) return;
        const list = (Array.isArray(rootPlace.members) && rootPlace.members.length > 0)
          ? rootPlace.members
          : [rootPlace];
        list.forEach(place => {
          const key = place.id || place.url || place.name;
          if (key && !seen.has(key)) {
            seen.add(key);
            entries.push({ place, marker, iconUrl: marker.__kidsMapIcon?.url });
          }
        });
      });
      return entries;
    }

    function show(markers, anchor) {
      close(false);
      const entries = extractEntries(markers);
      if (!entries.length) return;
      if (entries.length === 1 && typeof openPlace === 'function') {
        openPlace(entries[0].place, entries[0].marker);
        return;
      }

      trigger = anchor?.getElement?.() || document.activeElement;
      const t = languageLabels();

      panel = document.createElement('section');
      panel.className = 'kidsmap-map-chooser';
      panel.setAttribute('aria-label', `${t.locationTag}: ${t.placesCount ? t.placesCount(entries.length) : entries.length}`);
      panel.setAttribute('role', 'region');

      // Mobile handle bar
      const handle = document.createElement('div');
      handle.className = 'kidsmap-map-chooser__handle';
      handle.setAttribute('aria-hidden', 'true');
      panel.appendChild(handle);

      // Header
      const header = document.createElement('div');
      header.className = 'kidsmap-map-chooser__header';

      const headerText = document.createElement('div');
      headerText.className = 'kidsmap-map-chooser__header-text';

      const tag = document.createElement('div');
      tag.className = 'kidsmap-map-chooser__tag';
      tag.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> <span>' + (t.locationTag || 'В этой локации') + '</span>';
      headerText.appendChild(tag);

      const title = document.createElement('h3');
      title.className = 'kidsmap-map-chooser__title';
      title.textContent = t.placesCount ? t.placesCount(entries.length) : `${entries.length} ${t.places}`;
      headerText.appendChild(title);

      // Shared address / location subtitle if present
      const addresses = entries.map(e => e.place.address || e.place.location).filter(Boolean);
      if (addresses.length > 0) {
        const subtitle = document.createElement('p');
        subtitle.className = 'kidsmap-map-chooser__subtitle';
        subtitle.textContent = addresses[0];
        headerText.appendChild(subtitle);
      }
      header.appendChild(headerText);

      // Accessible Close Button
      const closeButton = document.createElement('button');
      closeButton.type = 'button';
      closeButton.className = 'kidsmap-map-chooser__close-btn';
      closeButton.setAttribute('aria-label', t.close);
      closeButton.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
      closeButton.addEventListener('click', () => close(true));
      header.appendChild(closeButton);

      panel.appendChild(header);

      // Scrollable Cards List
      const listWrap = document.createElement('div');
      listWrap.className = 'kidsmap-map-chooser__list-wrap';
      const list = document.createElement('ul');
      list.className = 'kidsmap-map-chooser__list';

      entries.forEach(entry => {
        const place = entry.place;
        const row = document.createElement('li');
        row.className = 'kidsmap-map-chooser__item';

        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'kidsmap-map-chooser__card';
        card.setAttribute('aria-label', `${place.name || ''}${place.category ? ' · ' + place.category : ''}`);

        // Thumbnail box
        const thumbBox = document.createElement('div');
        thumbBox.className = 'kidsmap-map-chooser__thumb-box';
        if (place.image_url) {
          const img = document.createElement('img');
          img.className = 'kidsmap-map-chooser__thumb';
          img.src = place.image_url;
          img.alt = '';
          img.loading = 'lazy';
          img.decoding = 'async';
          thumbBox.appendChild(img);
        } else {
          thumbBox.classList.add('kidsmap-map-chooser__thumb-box--fallback');
          const bg = place.category_color_bg || '#F0FDF4';
          const color = place.category_color_text || '#087443';
          thumbBox.style.backgroundColor = bg;
          thumbBox.style.color = color;
          if (place.category_icon_svg) {
            const svgSpan = document.createElement('span');
            svgSpan.className = 'kidsmap-map-chooser__thumb-icon';
            svgSpan.innerHTML = String(place.category_icon_svg).replace(/currentColor/g, color);
            thumbBox.appendChild(svgSpan);
          } else if (entry.iconUrl) {
            const pinImg = document.createElement('img');
            pinImg.className = 'kidsmap-map-chooser__thumb-pin';
            pinImg.src = entry.iconUrl;
            pinImg.alt = '';
            thumbBox.appendChild(pinImg);
          } else {
            thumbBox.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>';
          }
        }
        card.appendChild(thumbBox);

        // Body: Category, Title, Meta pills
        const cardBody = document.createElement('div');
        cardBody.className = 'kidsmap-map-chooser__card-body';

        if (place.category) {
          const catSpan = document.createElement('span');
          catSpan.className = 'kidsmap-map-chooser__category';
          catSpan.textContent = place.category;
          if (place.category_color_bg) catSpan.style.backgroundColor = place.category_color_bg;
          if (place.category_color_text) catSpan.style.color = place.category_color_text;
          cardBody.appendChild(catSpan);
        }

        const cardTitle = document.createElement('h4');
        cardTitle.className = 'kidsmap-map-chooser__card-title';
        cardTitle.textContent = place.name || '';
        cardBody.appendChild(cardTitle);

        // Meta row: Age, Price, Rating
        const metaRow = document.createElement('div');
        metaRow.className = 'kidsmap-map-chooser__meta-row';

        if (place.age) {
          const agePill = document.createElement('span');
          agePill.className = 'kidsmap-map-chooser__pill kidsmap-map-chooser__pill--age';
          agePill.innerHTML = '<span aria-hidden="true">👶</span> ' + place.age;
          metaRow.appendChild(agePill);
        }

        if (place.price) {
          const pricePill = document.createElement('span');
          pricePill.className = 'kidsmap-map-chooser__pill kidsmap-map-chooser__pill--price';
          pricePill.textContent = place.price;
          metaRow.appendChild(pricePill);
        }

        if (place.rating) {
          const ratingPill = document.createElement('span');
          ratingPill.className = 'kidsmap-map-chooser__pill kidsmap-map-chooser__pill--rating';
          ratingPill.textContent = '★ ' + Number(place.rating).toFixed(1);
          metaRow.appendChild(ratingPill);
        }

        if (metaRow.hasChildNodes()) {
          cardBody.appendChild(metaRow);
        }

        card.appendChild(cardBody);

        // Arrow indicator
        const arrow = document.createElement('div');
        arrow.className = 'kidsmap-map-chooser__arrow';
        arrow.setAttribute('aria-hidden', 'true');
        arrow.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>';
        card.appendChild(arrow);

        card.addEventListener('click', () => {
          close(false);
          openPlace(place, entry.marker);
        });

        row.appendChild(card);
        list.appendChild(row);
      });

      listWrap.appendChild(list);
      panel.appendChild(listWrap);

      // Keyboard navigation
      panel.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
          event.stopPropagation();
          close(true);
        } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
          const buttons = Array.from(list.querySelectorAll('.kidsmap-map-chooser__card'));
          const currentIdx = buttons.indexOf(document.activeElement);
          if (currentIdx !== -1) {
            event.preventDefault();
            const nextIdx = event.key === 'ArrowDown'
              ? (currentIdx + 1) % buttons.length
              : (currentIdx - 1 + buttons.length) % buttons.length;
            buttons[nextIdx].focus();
          }
        }
      });

      // Keep map drag/keyboard handlers out of scrollable place choices
      ['pointerdown', 'touchstart', 'click', 'wheel', 'keydown'].forEach(name => {
        panel.addEventListener(name, event => event.stopPropagation());
      });

      mapEl.appendChild(panel);
      list.querySelector('.kidsmap-map-chooser__card')?.focus({preventScroll: true});
    }

    return {show, close};
  }

  window.KidsMapGoogleMotion = {create, membership, chooser, clusterTitle, reduced};
})();
