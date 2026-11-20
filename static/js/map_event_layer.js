/* KidsMap: afisha (events) layer for the home map.
   Works with both engines home_map.js can mount (Google Maps / Leaflet):
   - animated ticket pins with a live "time left" badge;
   - a mini card on tap (bottom sheet on phones) with a ticking countdown;
   - "Места / Афиша" toggles that show or hide each layer.
   home_map.js only announces the mounted map ("kidsmap:map-mounted") and
   honours mapEl.dataset.kmPlaces on "kidsmap:layers-change". */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var HOUR = 3600000, DAY = 86400000;

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function phaseOf(p, now) {
    if (now >= p._end) return 'ended';
    if (now >= p._start) return 'running';
    return p._start - now <= DAY ? 'soon' : 'upcoming';
  }

  function shortLeft(p, now, L) {
    var phase = phaseOf(p, now);
    if (phase === 'running') return L.live;
    if (phase === 'ended') return L.ended;
    var ms = p._start - now;
    if (ms < HOUR) return Math.max(1, Math.ceil(ms / 60000)) + ' ' + L.m;
    if (ms < DAY) return Math.floor(ms / HOUR) + ' ' + L.h;
    return Math.floor(ms / DAY) + ' ' + L.d;
  }

  function progressOf(p, now) {
    // Fraction of the last 24 hours before the start that has already passed.
    var left = p._start - now;
    return Math.max(0, Math.min(1, 1 - left / DAY));
  }

  var UI = {
    ru: { about: 'О месте', here: 'Афиша здесь', places: 'Места здесь', back: 'Все события здесь', open: 'Открыть', noLang: '',
      ev: function (n) { var a = n % 10, b = n % 100; return n + ' ' + (b > 10 && b < 15 ? 'событий' : a === 1 ? 'событие' : a > 1 && a < 5 ? 'события' : 'событий'); },
      pl: function (n) { var a = n % 10, b = n % 100; return n + ' ' + (b > 10 && b < 15 ? 'мест' : a === 1 ? 'место' : a > 1 && a < 5 ? 'места' : 'мест'); } },
    az: { about: 'Məkan haqqında', here: 'Burada afişa', places: 'Burada məkanlar', back: 'Buradakı bütün tədbirlər', open: 'Aç', noLang: '',
      ev: function (n) { return n + ' tədbir'; }, pl: function (n) { return n + ' məkan'; } },
    en: { about: 'About the place', here: 'Events here', places: 'Places here', back: 'All events here', open: 'Open', noLang: '',
      ev: function (n) { return n + (n === 1 ? ' event' : ' events'); }, pl: function (n) { return n + (n === 1 ? ' place' : ' places'); } },
  };
  function ui() { return UI[(document.documentElement.lang || 'az').slice(0, 2)] || UI.az; }

  function langChips(p, cls) {
    var codes = p.languages || [];
    if (!codes.length) return '';
    return '<span class="' + cls + '" title="' + esc((p.language_names || []).join(', ')) + '">' +
      '<span class="material-symbols-rounded" aria-hidden="true">translate</span>' +
      codes.map(function (code) { return '<b>' + esc(code) + '</b>'; }).join('') +
      '<span class="visually-hidden">' + esc((p.language_names || []).join(', ')) + '</span></span>';
  }

  // One pin per venue: several events at the same point become a ticket stack.
  function pinElement(group, L) {
    var p = group.points[0];
    var many = group.points.length > 1;
    var el = document.createElement('span');
    var now = Date.now();
    el.className = 'km-evpin' + (many ? ' km-evpin--stack' : '');
    el.dataset.phase = phaseOf(p, now);
    el.style.setProperty('--km-delay', (Math.random() * 1.2).toFixed(2) + 's');
    el.style.setProperty('--p', progressOf(p, now).toFixed(3));
    el.innerHTML =
      '<span class="km-evpin__shadow" aria-hidden="true"></span>' +
      '<span class="km-evpin__body">' +
        '<span class="km-evpin__progress" aria-hidden="true"></span>' +
        '<span class="km-evpin__ring" aria-hidden="true"></span>' +
        (many ? '<span class="km-evpin__stack" aria-hidden="true"><i></i><i></i></span>' : '') +
        '<span class="km-evpin__ticket">' +
          '<span class="km-evpin__top">' + esc(p.long ? L.until : p.weekday) + '</span>' +
          '<b>' + esc(p.long ? p.end_day : p.day) + '</b>' +
          '<small>' + esc(p.long ? p.end_month : p.month) + '</small>' +
          '<span class="km-evpin__shine" aria-hidden="true"></span>' +
        '</span>' +
        '<span class="km-evpin__tail" aria-hidden="true"></span>' +
        '<span class="km-evpin__sparks" aria-hidden="true"><i></i><i></i><i></i><i></i></span>' +
        (many ? '<span class="km-evpin__count">' + group.points.length + '</span>'
              : '<span class="km-evpin__badge" data-km-evpin-left>' + esc(shortLeft(p, now, L)) + '</span>') +
      '</span>';
    if (!reduce && window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      // Tilt the ticket toward the cursor.
      el.addEventListener('pointermove', function (event) {
        var r = el.getBoundingClientRect();
        el.style.setProperty('--ry', (((event.clientX - r.left) / r.width - 0.5) * 26).toFixed(1) + 'deg');
        el.style.setProperty('--rx', (-((event.clientY - r.top) / r.height - 0.5) * 22).toFixed(1) + 'deg');
      });
      el.addEventListener('pointerleave', function () { el.style.removeProperty('--rx'); el.style.removeProperty('--ry'); });
    }
    return el;
  }

  function timerMarkup(p, L) {
    return '<div class="km-timer km-timer--card" data-km-timer data-state="' + esc(p.phase) + '"' +
      ' data-start="' + esc(p.start) + '" data-end="' + esc(p.end) + '"' +
      ' data-l-upcoming="' + esc(L.tUpcoming) + '" data-l-soon="' + esc(L.tSoon) + '"' +
      ' data-l-running="' + esc(L.tRunning) + '" data-l-ended="' + esc(L.tEnded) + '">' +
      '<span class="km-timer__label"><span class="km-timer__pulse" aria-hidden="true"></span><span data-km-timer-label>' +
        esc({ upcoming: L.tUpcoming, soon: L.tSoon, running: L.tRunning, ended: L.tEnded }[p.phase] || '') + '</span></span>' +
      '<span class="km-timer__clock" aria-hidden="true">' +
        ['d', 'h', 'm', 's'].map(function (u) {
          return '<span class="km-timer__seg" data-unit="' + u + '"><span class="km-timer__num">00</span><span class="km-timer__unit">' + esc(L['u' + u]) + '</span></span>';
        }).join('') +
      '</span></div>';
  }

  function Layer(section) {
    this.section = section;
    this.mapEl = section.querySelector('#home-map');
    var source = document.getElementById('home-map-events');
    this.points = source ? JSON.parse(source.textContent || '[]') : [];
    var d = section.dataset;
    this.L = {
      live: d.evLive, ended: d.evEnded, until: d.evUntil, m: d.evM, h: d.evH, d: d.evD,
      tUpcoming: d.evTUpcoming, tSoon: d.evTSoon, tRunning: d.evTRunning, tEnded: d.evTEnded,
      ud: d.evUd, uh: d.evUh, um: d.evUm, us: d.evUs,
      today: d.evToday, tomorrow: d.evTomorrow, weekend: d.evWeekend, now: d.evNow,
      details: d.evDetails, route: d.evRoute, close: d.evClose, free: d.evFree, open: d.evOpen,
    };
    this.items = [];
    this.selected = null;
    this.visible = true;
    var now = Date.now();
    this.points.forEach(function (p) { p._start = Date.parse(p.start); p._end = Date.parse(p.end); p.phase = phaseOf(p, now); });
    this.points = this.points.filter(function (p) { return p.phase !== 'ended'; });
  }

  Layer.prototype.init = function () {
    if (!this.mapEl) return;
    var self = this;
    this.container = this.mapEl.closest('.home-map-container') || this.mapEl.parentElement;
    this.card = document.createElement('aside');
    this.card.className = 'km-evcard';
    this.card.hidden = true;
    this.card.setAttribute('aria-live', 'polite');
    this.container.appendChild(this.card);
    this.bindToggles();
    this.mapEl.addEventListener('kidsmap:map-mounted', function (event) { self.mount(event.detail); });
    if (this.mapEl.__kidsMapMounted) this.mount(this.mapEl.__kidsMapMounted);
    document.addEventListener('keydown', function (event) { if (event.key === 'Escape') self.close(); });
    setInterval(function () { self.refreshBadges(); }, 20000);
  };

  // "Всё / Места / Афиша": one segmented switch drives both layers.
  Layer.prototype.bindToggles = function () {
    var self = this;
    var radios = this.section.querySelectorAll('[data-km-mode]');
    Array.prototype.forEach.call(radios, function (radio) {
      radio.addEventListener('change', function () { if (radio.checked) self.setMode(radio.value); });
    });
    var checked = this.section.querySelector('[data-km-mode]:checked');
    if (checked && checked.value !== 'all') this.setMode(checked.value);
    else this.placeThumb();
    window.addEventListener('resize', function () { self.placeThumb(); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { self.placeThumb(); });
  };

  // The white thumb slides under the chosen segment.
  Layer.prototype.placeThumb = function () {
    var switcher = this.section.querySelector('[data-km-modes]');
    var checked = switcher && switcher.querySelector('[data-km-mode]:checked');
    if (!checked) return;
    var label = checked.closest('label');
    switcher.style.setProperty('--x', (label.offsetLeft - 4) + 'px');
    switcher.style.setProperty('--w', label.offsetWidth + 'px');
  };

  Layer.prototype.setMode = function (mode) {
    var switcher = this.section.querySelector('[data-km-modes]');
    if (switcher) switcher.dataset.mode = mode;
    this.section.classList.toggle('is-events-mode', mode === 'events');
    if (mode === 'events') this.renderList();
    this.placeThumb();
    this.mapEl.dataset.kmPlaces = mode === 'events' ? 'off' : 'on';
    this.visible = mode !== 'places';
    if (!this.visible || mode === 'events') this.close();
    this.mapEl.dispatchEvent(new CustomEvent('kidsmap:layers-change'));
  };

  // Events at the same venue (±10 m) share one marker.
  Layer.prototype.groups = function () {
    var byKey = new Map();
    this.points.slice().sort(function (a, b) { return a._start - b._start; }).forEach(function (p) {
      var key = (+p.lat).toFixed(4) + ',' + (+p.lng).toFixed(4);
      if (!byKey.has(key)) byKey.set(key, { key: key, lat: p.lat, lng: p.lng, points: [] });
      byKey.get(key).points.push(p);
    });
    return Array.from(byKey.values());
  };

  Layer.prototype.mount = function (detail) {
    if (!detail || this.engine) return;
    this.engine = detail.engine;
    this.map = detail.map;
    var self = this, markers = [];
    this.groups().forEach(function (group, index) {
      var el = pinElement(group, self.L);
      el.style.setProperty('--km-i', Math.min(index, 12));
      var label = group.points.length > 1 ? (group.points[0].venue || group.points[0].name) + ' · ' + ui().ev(group.points.length) : group.points[0].name;
      var marker;
      if (self.engine === 'google' && window.kidsMapCreateGoogleMarker) {
        marker = window.kidsMapCreateGoogleMarker({
          position: { lat: group.lat, lng: group.lng }, title: label, visual: el,
          icon: { scaledSize: new google.maps.Size(52, 64), anchor: new google.maps.Point(26, 62) },
          publicVisual: true, ownerMap: self.map, mapId: detail.mapId, zIndex: 2000,
        });
        marker.addListener('click', function () { self.openMarker(marker); });
      } else if (self.engine === 'leaflet' && window.L) {
        marker = window.L.marker([group.lat, group.lng], {
          icon: window.L.divIcon({ className: 'km-evpin-host', html: el, iconSize: [52, 64], iconAnchor: [26, 62] }),
          title: label, keyboard: true, zIndexOffset: 1000, riseOnHover: true,
        });
        marker.on('click', function () { self.openMarker(marker); });
      } else {
        return;
      }
      // Read by home_map.js (shared clusterer) and kidsmap_map_pins.js (cluster ring).
      marker.__kmEvents = group.points;
      marker.__kmGroup = group;
      marker.__kmPin = el;
      markers.push(marker);
      group.points.forEach(function (p) { self.items.push({ point: p, marker: marker, el: el }); });
    });
    this.items.sort(function (a, b) { return a.point._start - b.point._start; });
    this.markers = markers;
    this.mapEl.__kmEventLayer = this;
    this.mapEl.dispatchEvent(new CustomEvent('kidsmap:events-ready'));
    if (this.engine === 'google' && this.map.addListener) this.map.addListener('click', function () { self.close(); });
    if (this.engine === 'leaflet') this.map.on('click', function () { self.close(); });
    this.mirrorPlacePopups();
  };

  // "Афиша" mode: the side list shows upcoming events instead of places.
  Layer.prototype.renderList = function () {
    var self = this, L = this.L, now = Date.now();
    var panel = this.section.querySelector('[data-home-explorer-list]');
    if (!panel) return;
    if (!this.list) {
      this.list = document.createElement('ol');
      this.list.className = 'km-evlist';
      this.list.setAttribute('aria-label', ui().here);
      panel.appendChild(this.list);
      this.list.addEventListener('click', function (event) {
        var row = event.target.closest('[data-km-evlist]');
        if (!row) return;
        var item = self.items[+row.dataset.kmEvlist];
        if (!item) return;
        self.select(item.marker.__kmPin);
        self.open(item.point);
      });
    }
    this.list.innerHTML = this.items.map(function (item, index) {
      var p = item.point, phase = phaseOf(p, now);
      return '<li style="--n:' + Math.min(index, 10) + '"><button type="button" class="km-venue__row km-evlist__row" data-km-evlist="' + index + '" data-phase="' + esc(phase) + '">' +
        '<span class="km-venue__stamp"><small>' + esc(p.long ? L.until : p.weekday) + '</small><b>' + esc(p.long ? p.end_day : p.day) + '</b><small>' + esc(p.long ? p.end_month : p.month) + '</small></span>' +
        '<span class="km-venue__info"><span class="km-venue__name">' + esc(p.name) + '</span>' +
          '<span class="km-venue__meta"><span>' + esc(p.long ? (p.day + ' ' + p.month + ' – ' + p.end_day + ' ' + p.end_month) : p.time) + '</span>' +
          ((p.venue || p.address) ? '<span>' + esc(p.venue || p.address) + '</span>' : '') + '</span>' +
          langChips(p, 'km-venue__langs') + '</span>' +
        '<span class="km-venue__left">' + esc(shortLeft(p, now, L)) + '</span>' +
      '</button></li>';
    }).join('');
  };

  // Event venues that sit on a shown place (±~40 m) are not drawn as a second
  // pin: the place pin gets a ticket badge and opens the shared venue sheet.
  Layer.prototype.visibleMarkers = function (placeMarkers) {
    var self = this;
    (this.hosts || []).forEach(function (host) { self.detach(host); });
    this.hosts = [];
    if (!this.visible) return [];
    var shown = [];
    (this.markers || []).forEach(function (marker) {
      var group = marker.__kmGroup, best = null, bestDistance = Infinity;
      (placeMarkers || []).forEach(function (place) {
        var pos = markerPosition(place);
        if (!pos) return;
        var dLat = Math.abs(pos.lat - group.lat), dLng = Math.abs(pos.lng - group.lng);
        if (dLat > 0.0004 || dLng > 0.0005) return;
        if (dLat + dLng < bestDistance) { bestDistance = dLat + dLng; best = place; }
      });
      if (best && !best.__kmAttached) { self.attach(best, marker); return; }
      shown.push(marker);
    });
    return shown;
  };

  function hostElement(marker) {
    var el = marker.getElement ? marker.getElement() : null;
    if (!el) return null;
    return el.querySelector('.km-pin') || el.querySelector('.kidsmap-marker-visual') || el;
  }

  Layer.prototype.decorate = function (place) {
    var el = hostElement(place), attached = place.__kmAttached;
    if (!el || !attached) return;
    var badge = el.querySelector(':scope > .km-pin__events');
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'km-pin__events';
      badge.setAttribute('aria-hidden', 'true');
      el.appendChild(badge);
    }
    badge.innerHTML = '<span class="material-symbols-rounded">confirmation_number</span>' + attached.__kmEvents.length;
    el.classList.add('has-events');
    var host = el.closest('.leaflet-marker-icon, .kidsmap-marker-button');
    if (host) host.setAttribute('aria-label', (host.getAttribute('aria-label') || '').replace(/ · .*$/, '') + ' · ' + ui().ev(attached.__kmEvents.length));
  };

  Layer.prototype.attach = function (place, eventMarker) {
    var self = this;
    place.__kmAttached = eventMarker;
    eventMarker.__kmHost = place;
    this.hosts.push(place);
    this.decorate(place);
    if (place.on && !place.__kmDecorateOnAdd) {
      // Leaflet rebuilds the icon whenever the marker leaves and re-enters a cluster.
      place.__kmDecorateOnAdd = function () { setTimeout(function () { self.decorate(place); }, 0); };
      place.on('add', place.__kmDecorateOnAdd);
    }
  };

  Layer.prototype.detach = function (place) {
    if (place.__kmAttached) place.__kmAttached.__kmHost = null;
    place.__kmAttached = null;
    var el = hostElement(place);
    if (!el) return;
    var badge = el.querySelector(':scope > .km-pin__events');
    if (badge) badge.remove();
    el.classList.remove('has-events');
  };

  // Places: the map engine still opens its own popup (selection, list sync, phone
  // button…), but it is kept invisible and its content is shown in the same
  // animated side card as events.
  Layer.prototype.mirrorPlacePopups = function () {
    var self = this;
    this.mapEl.classList.add('km-placecards');
    if (this.engine === 'leaflet') {
      this.map.on('popupopen', function (event) {
        var source = event.popup._source;
        if (source && source.__kmAttached) {
          // A place that also hosts afisha opens the shared venue sheet.
          self.switching = true;
          self.map.closePopup();
          self.switching = false;
          self.openVenue([source.__kmAttached], [source]);
          return;
        }
        var content = event.popup.getContent();
        self.openPlace(typeof content === 'string' ? content : (content && content.outerHTML) || '');
      });
      this.map.on('popupclose', function () { if (!self.switching) self.close(true); });
      return;
    }
    var shown = null;
    var observer = new MutationObserver(function () {
      var popup = self.mapEl.querySelector('.gm-style-iw-d .home-map-popup, .gm-style-iw-d .home-map-popup-members');
      var host = popup && popup.closest('.gm-style-iw-d');
      if (host && host !== shown) {
        shown = host;
        self.openPlace(host.innerHTML);
      } else if (!host && shown) {
        shown = null;
        if (!self.switching) self.close(true);
      }
    });
    observer.observe(this.mapEl, { childList: true, subtree: true });
  };

  Layer.prototype.closeEnginePopup = function () {
    this.switching = true;
    if (this.engine === 'leaflet' && this.map) this.map.closePopup();
    else {
      var button = this.mapEl.querySelector('.gm-style-iw-chr button, button.gm-ui-hover-effect');
      if (button) button.click();
    }
    var self = this;
    setTimeout(function () { self.switching = false; }, 0);
  };

  Layer.prototype.show = function (kind, html, prepare) {
    var self = this;
    this.kind = kind;
    this.card.classList.toggle('km-evcard--place', kind === 'place');
    this.card.classList.toggle('km-evcard--venue', kind === 'venue');
    if (kind !== 'venue') this.card.classList.remove('km-evcard--host');
    this.card.innerHTML = '<button type="button" class="km-evcard__close" data-km-evcard-close aria-label="' + esc(this.L.close || 'Закрыть') +
      '"><span class="material-symbols-rounded" aria-hidden="true">close</span></button>' + html;
    this.card.querySelector('[data-km-evcard-close]').addEventListener('click', function () { self.close(); });
    if (prepare) prepare(this.card);
    this.card.hidden = false;
    this.card.classList.remove('is-open');
    void this.card.offsetWidth;
    this.card.classList.add('is-open');
    this.card.scrollTop = 0;
    this.container.classList.add('has-evcard');
  };

  Layer.prototype.openPlace = function (html) {
    if (!html) return;
    if (this.selected) this.selected.classList.remove('is-selected', 'is-hop');
    this.selected = null;
    this.show('place', '<div class="km-evcard__placebody">' + html + '</div>');
  };

  Layer.prototype.refreshBadges = function () {
    var now = Date.now(), L = this.L, seen = new Set();
    this.items.forEach(function (item) {
      if (seen.has(item.el)) return;
      seen.add(item.el);
      item.el.dataset.phase = phaseOf(item.point, now);
      item.el.style.setProperty('--p', progressOf(item.point, now).toFixed(3));
      var badge = item.el.querySelector('[data-km-evpin-left]');
      var text = shortLeft(item.point, now, L);
      if (!badge || badge.textContent === text) return;
      badge.textContent = text;
      if (reduce) return;
      badge.classList.remove('is-tick');
      void badge.offsetWidth;
      badge.classList.add('is-tick');
    });
  };

  function markerPosition(marker) {
    if (marker.getLatLng) { var ll = marker.getLatLng(); return { lat: ll.lat, lng: ll.lng }; }
    var pos = marker.getPosition && marker.getPosition();
    if (!pos) return null;
    return typeof pos.lat === 'function' ? { lat: pos.lat(), lng: pos.lng() } : { lat: pos.lat, lng: pos.lng };
  }

  // Places within ~25 m of a venue are shown in the same sheet.
  Layer.prototype.placesNear = function (lat, lng) {
    var list = this.mapEl.__kmPlaceMarkerList || [];
    return list.filter(function (marker) {
      var pos = markerPosition(marker);
      return pos && Math.abs(pos.lat - lat) < 0.00025 && Math.abs(pos.lng - lng) < 0.0003;
    });
  };

  Layer.prototype.select = function (el) {
    if (this.selected) this.selected.classList.remove('is-selected', 'is-hop');
    this.selected = el || null;
    if (!el) return;
    el.classList.add('is-selected');
    if (reduce) return;
    void el.offsetWidth;
    el.classList.add('is-hop');
    var ripple = document.createElement('span');
    ripple.className = 'km-evpin__ripple';
    ripple.setAttribute('aria-hidden', 'true');
    el.appendChild(ripple);
    setTimeout(function () { ripple.remove(); }, 900);
  };

  Layer.prototype.openMarker = function (marker) {
    var group = marker.__kmGroup;
    var places = this.mapEl.dataset.kmPlaces === 'off' ? [] : this.placesNear(group.lat, group.lng);
    if (group.points.length === 1 && !places.length) {
      this.select(marker.__kmPin);
      this.open(group.points[0]);
      return;
    }
    this.openVenue([marker], places);
  };

  // Venue sheet: every event at this point (and places there), newest first.
  Layer.prototype.openVenue = function (eventMarkers, placeMarkers) {
    var self = this, L = this.L, t = ui(), now = Date.now();
    var points = [];
    eventMarkers.forEach(function (m) { points = points.concat(m.__kmEvents || []); });
    points.sort(function (a, b) { return a._start - b._start; });
    var places = [];
    (placeMarkers || []).forEach(function (m) {
      var place = m.__kidsMapPlace;
      if (!place) return;
      (Array.isArray(place.members) && place.members.length ? place.members : [place]).forEach(function (member) { places.push(member); });
    });
    if (!points.length) return;
    if (points.length === 1 && !places.length) { this.select(eventMarkers[0].__kmPin); this.open(points[0]); return; }
    this.select(eventMarkers[0].__kmPin);
    var first = points[0];
    var host = places.length === 1 ? places[0] : null;
    var title = host ? host.name : (first.venue || first.address || first.name);
    var subtitle = [t.ev(points.length)].concat(places.length ? [t.pl(places.length)] : []).join(' · ');
    var rows = points.map(function (p, index) {
      var phase = phaseOf(p, now);
      return '<li style="--n:' + index + '"><button type="button" class="km-venue__row" data-km-venue-event="' + index + '" data-phase="' + esc(phase) + '">' +
        '<span class="km-venue__stamp"><small>' + esc(p.long ? L.until : p.weekday) + '</small><b>' + esc(p.long ? p.end_day : p.day) + '</b><small>' + esc(p.long ? p.end_month : p.month) + '</small></span>' +
        '<span class="km-venue__info"><span class="km-venue__name">' + esc(p.name) + '</span>' +
          '<span class="km-venue__meta"><span>' + esc(p.long ? (p.day + ' ' + p.month + ' – ' + p.end_day + ' ' + p.end_month) : p.time) + '</span>' +
          (p.age ? '<span>' + esc(p.age) + '</span>' : '') + '</span>' +
          langChips(p, 'km-venue__langs') + '</span>' +
        '<span class="km-venue__left">' + esc(shortLeft(p, now, L)) + '</span>' +
      '</button></li>';
    }).join('');
    var placeRows = places.map(function (place, index) {
      return '<li style="--n:' + (points.length + index) + '"><a class="km-venue__row km-venue__row--place" href="' + esc(place.url || '#') + '">' +
        (place.image_url ? '<img class="km-venue__thumb" src="' + esc(place.image_url) + '" alt="" loading="lazy">' : '<span class="km-venue__thumb material-symbols-rounded" aria-hidden="true">storefront</span>') +
        '<span class="km-venue__info"><span class="km-venue__name">' + esc(place.name) + '</span>' +
          '<span class="km-venue__meta">' + (place.category ? '<span>' + esc(place.category) + '</span>' : '') + (place.age ? '<span>' + esc(place.age) + '</span>' : '') + '</span></span>' +
        '<span class="km-venue__go material-symbols-rounded" aria-hidden="true">arrow_forward</span></a></li>';
    }).join('');
    if (this.kind === 'place') this.closeEnginePopup();
    var head = host
      // One place hosts the events: the place leads, its afisha follows.
      ? '<header class="km-venue__hero">' +
          '<a class="km-venue__photo" href="' + esc(host.url || '#') + '" tabindex="-1" aria-hidden="true">' +
            (host.image_url ? '<img src="' + esc(host.image_url) + '" alt="" decoding="async">' : '<span class="material-symbols-rounded">storefront</span>') +
            '<span class="km-venue__badge"><span class="material-symbols-rounded" aria-hidden="true">confirmation_number</span>' + esc(t.ev(points.length)) + '</span>' +
          '</a>' +
          '<div class="km-venue__about">' +
            (host.category ? '<span class="km-venue__cat" style="--cat:' + esc(host.category_color_text || '#136f38') + '">' + esc(host.category) + '</span>' : '') +
            '<h3 class="km-venue__title"><a href="' + esc(host.url || '#') + '">' + esc(host.name) + '</a></h3>' +
            '<p class="km-venue__facts">' + (host.age ? '<span><span class="material-symbols-rounded" aria-hidden="true">child_care</span>' + esc(host.age) + '</span>' : '') +
              (host.price ? '<span><span class="material-symbols-rounded" aria-hidden="true">payments</span>' + esc(host.price) + '</span>' : '') + '</p>' +
            '<div class="km-venue__actions">' +
              '<a class="km-ev-btn km-ev-btn--primary" href="' + esc(host.url || '#') + '"><span>' + esc(t.about) + '</span><span class="material-symbols-rounded" aria-hidden="true">arrow_forward</span></a>' +
              '<a class="km-ev-btn km-ev-btn--ghost" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(first.lat + ',' + first.lng) + '"><span class="material-symbols-rounded" aria-hidden="true">near_me</span><span>' + esc(L.route) + '</span></a>' +
            '</div>' +
          '</div>' +
        '</header>' +
        '<p class="km-venue__section km-venue__section--events"><span class="material-symbols-rounded" aria-hidden="true">confirmation_number</span>' + esc(t.here) + ' · ' + points.length + '</p>'
      : '<header class="km-venue__head">' +
          '<span class="km-venue__icon material-symbols-rounded" aria-hidden="true">confirmation_number</span>' +
          '<span><span class="km-venue__tag">' + esc(t.here) + '</span><h3 class="km-venue__title">' + esc(title) + '</h3><span class="km-venue__sub">' + esc(subtitle) + '</span></span>' +
        '</header>';
    this.card.classList.toggle('km-evcard--host', !!host);
    this.show('venue',
      head +
      '<ul class="km-venue__list">' + rows + '</ul>' +
      (places.length && !host ? '<p class="km-venue__section">' + esc(t.places) + '</p><ul class="km-venue__list">' + placeRows + '</ul>' : ''));
    Array.prototype.forEach.call(this.card.querySelectorAll('[data-km-venue-event]'), function (button) {
      button.addEventListener('click', function () {
        self.open(points[+button.dataset.kmVenueEvent], function () { self.openVenue(eventMarkers, placeMarkers); });
      });
    });
    this.pan(first);
  };

  Layer.prototype.open = function (p, back) {
    var L = this.L, self = this;
    var whenChip = phaseOf(p, Date.now()) === 'running' ? '<span class="km-ev-chip km-ev-chip--live"><i aria-hidden="true"></i>' + esc(L.now) + '</span>'
      : p.when === 'today' ? '<span class="km-ev-chip km-ev-chip--hot">' + esc(L.today) + '</span>'
      : p.when === 'tomorrow' ? '<span class="km-ev-chip km-ev-chip--warm">' + esc(L.tomorrow) + '</span>'
      : p.when === 'weekend' ? '<span class="km-ev-chip km-ev-chip--warm">' + esc(L.weekend) + '</span>' : '';
    var date = p.long ? (p.day + ' ' + p.month + ' – ' + p.end_day + ' ' + p.end_month)
      : (p.weekday + ', ' + p.day + ' ' + p.month + ' · ' + p.time);
    var price = p.free ? L.free : p.price;
    if (this.kind === 'place') this.closeEnginePopup();
    var html =
      (back ? '<button type="button" class="km-evcard__back" data-km-evcard-back><span class="material-symbols-rounded" aria-hidden="true">arrow_back</span><span>' + esc(ui().back) + '</span></button>' : '') +
      '<a class="km-evcard__media" href="' + esc(p.url) + '" tabindex="-1" aria-hidden="true">' +
        (p.image ? '<img src="' + esc(p.image) + '" alt="" decoding="async">' : '<span class="km-evcard__ph material-symbols-rounded">celebration</span>') +
        '<span class="km-evcard__chips">' + whenChip + '</span>' +
        langChips(p, 'km-evcard__langs km-evcard__langs--photo') +
        (price ? '<span class="km-evcard__price' + (p.free ? ' is-free' : '') + '">' + esc(price) + '</span>' : '') +
      '</a>' +
      '<div class="km-evcard__body">' +
        '<p class="km-evcard__when"><span class="material-symbols-rounded" aria-hidden="true">' + (p.long ? 'date_range' : 'schedule') + '</span>' + esc(date) + '</p>' +
        '<h3 class="km-evcard__title"><a href="' + esc(p.url) + '">' + esc(p.name) + '</a></h3>' +
        '<p class="km-evcard__meta">' + (p.category ? '<span class="km-ev-card__cat">' + esc(p.category) + '</span>' : '') +
          (p.age ? '<span>' + esc(p.age) + '</span>' : '') + '</p>' +
        ((p.venue || p.address) ? '<p class="km-evcard__place"><span class="material-symbols-rounded" aria-hidden="true">location_on</span>' + esc(p.venue || p.address) + '</p>' : '') +
        timerMarkup(p, L) +
        '<div class="km-evcard__actions">' +
          '<a class="km-ev-btn km-ev-btn--primary" href="' + esc(p.url) + '"><span>' + esc(L.details) + '</span><span class="material-symbols-rounded" aria-hidden="true">arrow_forward</span></a>' +
          '<a class="km-ev-btn km-ev-btn--ghost" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(p.lat + ',' + p.lng) + '"><span class="material-symbols-rounded" aria-hidden="true">near_me</span><span>' + esc(L.route) + '</span></a>' +
        '</div>' +
      '</div>';
    var reveal = function () {
      self.show('event', html, function (card) {
        // Fill the countdown before the card becomes visible: no "00:00" flash.
        if (window.KidsMapTimers) window.KidsMapTimers.scan(card);
        var backButton = card.querySelector('[data-km-evcard-back]');
        if (backButton && back) backButton.addEventListener('click', back);
      });
      self.pan(p);
    };
    // Wait briefly for the photo so the card never opens with an empty frame.
    if (!p.image) { reveal(); return; }
    var image = new Image(), done = false;
    var go = function () { if (done) return; done = true; reveal(); };
    image.onload = image.onerror = go;
    image.src = p.image;
    if (image.complete) go(); else setTimeout(go, 350);
  };

  // Keep the pin visible beside the card (desktop) or above the sheet (phone).
  Layer.prototype.pan = function (p) {
    if (!this.map) return;
    var phone = this.container.clientWidth <= 640;
    var dx = phone ? 0 : Math.min(190, (this.card.offsetWidth || 340) / 2 + 10);
    var dy = phone ? -Math.round(this.container.clientHeight * 0.24) : 0;
    if (this.engine === 'google' && this.map.panTo) {
      this.map.panTo({ lat: p.lat, lng: p.lng });
      if ((dx || dy) && this.map.panBy) this.map.panBy(-dx, -dy);
    } else if (this.engine === 'leaflet') {
      var zoom = this.map.getZoom();
      var point = this.map.project([p.lat, p.lng], zoom).subtract([dx, dy]);
      this.map.panTo(this.map.unproject(point, zoom), { animate: !reduce });
    }
  };

  Layer.prototype.close = function (fromEngine) {
    if (!this.card || this.card.hidden) return;
    if (this.kind === 'place' && !fromEngine) this.closeEnginePopup();
    if (this.selected) this.selected.classList.remove('is-selected', 'is-hop');
    this.selected = null;
    var card = this.card, container = this.container;
    card.classList.remove('is-open');
    container.classList.remove('has-evcard');
    setTimeout(function () { if (!card.classList.contains('is-open')) card.hidden = true; }, reduce ? 0 : 220);
  };

  function boot() {
    var section = document.querySelector('[data-home-map-explorer]');
    if (section) new Layer(section).init();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
