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

  function pinElement(p, L) {
    var el = document.createElement('span');
    var now = Date.now();
    el.className = 'km-evpin';
    el.dataset.phase = phaseOf(p, now);
    el.style.setProperty('--km-delay', (Math.random() * 1.2).toFixed(2) + 's');
    el.style.setProperty('--p', progressOf(p, now).toFixed(3));
    el.innerHTML =
      '<span class="km-evpin__shadow" aria-hidden="true"></span>' +
      '<span class="km-evpin__body">' +
        '<span class="km-evpin__progress" aria-hidden="true"></span>' +
        '<span class="km-evpin__ring" aria-hidden="true"></span>' +
        '<span class="km-evpin__ticket">' +
          '<span class="km-evpin__top">' + esc(p.long ? L.until : p.weekday) + '</span>' +
          '<b>' + esc(p.long ? p.end_day : p.day) + '</b>' +
          '<small>' + esc(p.long ? p.end_month : p.month) + '</small>' +
          '<span class="km-evpin__shine" aria-hidden="true"></span>' +
        '</span>' +
        '<span class="km-evpin__tail" aria-hidden="true"></span>' +
        '<span class="km-evpin__sparks" aria-hidden="true"><i></i><i></i><i></i><i></i></span>' +
        '<span class="km-evpin__badge" data-km-evpin-left>' + esc(shortLeft(p, now, L)) + '</span>' +
        ((p.languages || []).length ? '<span class="km-evpin__langs" aria-hidden="true">' + esc(p.languages.join('·')) + '</span>' : '') +
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

  function clusterElement(count, live, points) {
    var el = document.createElement('span');
    el.className = 'km-evcluster' + (live ? ' is-live' : '');
    var fan = (points || []).slice().sort(function (a, b) { return a._start - b._start; }).slice(0, 3).map(function (p, i) {
      return '<span class="km-evcluster__card" style="--n:' + i + '"><b>' + esc(p.long ? p.end_day : p.day) + '</b><small>' + esc(p.long ? p.end_month : p.month) + '</small></span>';
    }).join('');
    el.innerHTML = '<span class="km-evcluster__fan" aria-hidden="true">' + fan + '</span>' +
      '<span class="km-evcluster__orbit" aria-hidden="true"></span>' +
      '<span class="km-evcluster__core"><span class="material-symbols-rounded" aria-hidden="true">confirmation_number</span><b>' + count + '</b></span>';
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

  Layer.prototype.bindToggles = function () {
    var self = this;
    var places = this.section.querySelector('[data-km-layer="places"]');
    var events = this.section.querySelector('[data-km-layer="events"]');
    if (places) places.addEventListener('change', function () {
      self.mapEl.dataset.kmPlaces = places.checked ? 'on' : 'off';
      self.mapEl.dispatchEvent(new CustomEvent('kidsmap:layers-change'));
      if (!places.checked && events && !events.checked) { events.checked = true; self.setVisible(true); }
    });
    if (events) events.addEventListener('change', function () {
      self.setVisible(events.checked);
      if (!events.checked && places && !places.checked) {
        places.checked = true;
        self.mapEl.dataset.kmPlaces = 'on';
        self.mapEl.dispatchEvent(new CustomEvent('kidsmap:layers-change'));
      }
    });
  };

  Layer.prototype.mount = function (detail) {
    if (!detail || this.engine) return;
    this.engine = detail.engine;
    this.map = detail.map;
    var self = this, markers = [];
    var title = this.section.dataset.evCluster || '';
    this.points.forEach(function (p, index) {
      var el = pinElement(p, self.L);
      el.style.setProperty('--km-i', Math.min(index, 12));
      var marker;
      if (self.engine === 'google' && window.kidsMapCreateGoogleMarker) {
        marker = window.kidsMapCreateGoogleMarker({
          position: { lat: p.lat, lng: p.lng }, title: p.name, visual: el,
          icon: { scaledSize: new google.maps.Size(52, 64), anchor: new google.maps.Point(26, 62) },
          publicVisual: true, ownerMap: self.map, mapId: detail.mapId, zIndex: 2000,
        });
        marker.addListener('click', function () { self.open(p, el); });
      } else if (self.engine === 'leaflet' && window.L) {
        marker = window.L.marker([p.lat, p.lng], {
          icon: window.L.divIcon({ className: 'km-evpin-host', html: el, iconSize: [52, 64], iconAnchor: [26, 62] }),
          title: p.name, keyboard: true, zIndexOffset: 1000, riseOnHover: true, kmPhase: p.phase,
        });
        marker.on('click', function () { self.open(p, el); });
      } else {
        return;
      }
      marker.__kmPoint = p;
      markers.push(marker);
      self.items.push({ point: p, marker: marker, el: el });
    });
    this.markers = markers;

    // Afisha pins cluster on their own (coral ticket bubbles), apart from place clusters.
    if (this.engine === 'leaflet' && window.L.markerClusterGroup) {
      this.group = window.L.markerClusterGroup({
        showCoverageOnHover: false, maxClusterRadius: 58, spiderfyOnMaxZoom: true, zoomToBoundsOnClick: true,
        iconCreateFunction: function (cluster) {
          var children = cluster.getAllChildMarkers();
          var live = children.some(function (m) { return m.__kmPoint && phaseOf(m.__kmPoint, Date.now()) === 'running'; });
          return window.L.divIcon({ className: 'km-evpin-host', html: clusterElement(children.length, live, children.map(function (m) { return m.__kmPoint; })), iconSize: [58, 58], iconAnchor: [29, 29] });
        },
      });
      this.group.addLayers(markers);
      this.map.addLayer(this.group);
    } else if (this.engine === 'leaflet') {
      markers.forEach(function (m) { m.addTo(self.map); });
    } else if (window.markerClusterer && window.markerClusterer.MarkerClusterer && !window.markerClusterer.dummy) {
      var mc = window.markerClusterer;
      this.clusterer = new mc.MarkerClusterer({
        map: this.map, markers: markers,
        algorithm: mc.SuperClusterAlgorithm ? new mc.SuperClusterAlgorithm({ maxZoom: 16, radius: 64 }) : undefined,
        renderer: {
          render: function (cluster) {
            var live = cluster.markers.some(function (m) { return m.__kmPoint && phaseOf(m.__kmPoint, Date.now()) === 'running'; });
            return window.kidsMapCreateGoogleMarker({
              position: cluster.position, title: title.replace('{count}', cluster.count),
              icon: { scaledSize: new google.maps.Size(58, 58), anchor: new google.maps.Point(29, 29) },
              publicVisual: true, ownerMap: self.map, visual: clusterElement(cluster.count, live, cluster.markers.map(function (m) { return m.__kmPoint; })), visualKind: 'cluster',
              zIndex: 3000000 + cluster.count, mapId: detail.mapId,
            });
          },
        },
      });
    } else {
      markers.forEach(function (m) { m.setMap(self.map); });
    }
    if (this.engine === 'google' && this.map.addListener) this.map.addListener('click', function () { self.close(); });
    if (this.engine === 'leaflet') this.map.on('click', function () { self.close(); });
    this.mirrorPlacePopups();
  };

  // Places: the map engine still opens its own popup (selection, list sync, phone
  // button…), but it is kept invisible and its content is shown in the same
  // animated side card as events.
  Layer.prototype.mirrorPlacePopups = function () {
    var self = this;
    this.mapEl.classList.add('km-placecards');
    if (this.engine === 'leaflet') {
      this.map.on('popupopen', function (event) {
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

  Layer.prototype.show = function (kind, html) {
    var self = this;
    this.kind = kind;
    this.card.classList.toggle('km-evcard--place', kind === 'place');
    this.card.innerHTML = '<button type="button" class="km-evcard__close" data-km-evcard-close aria-label="' + esc(this.L.close || 'Закрыть') +
      '"><span class="material-symbols-rounded" aria-hidden="true">close</span></button>' + html;
    this.card.querySelector('[data-km-evcard-close]').addEventListener('click', function () { self.close(); });
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

  Layer.prototype.setVisible = function (visible) {
    var self = this;
    this.visible = visible;
    if (!visible) this.close();
    if (this.group) {
      if (visible) this.map.addLayer(this.group); else this.map.removeLayer(this.group);
    } else if (this.clusterer) {
      if (visible) this.clusterer.addMarkers(this.markers); else this.clusterer.clearMarkers();
    } else {
      this.markers.forEach(function (m) {
        if (self.engine === 'google') m.setMap(visible ? self.map : null);
        else if (visible) m.addTo(self.map); else self.map.removeLayer(m);
      });
    }
  };

  Layer.prototype.refreshBadges = function () {
    var now = Date.now(), L = this.L;
    this.items.forEach(function (item) {
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

  Layer.prototype.open = function (p, el) {
    var L = this.L;
    if (this.selected) this.selected.classList.remove('is-selected', 'is-hop');
    this.selected = el;
    el.classList.add('is-selected');
    if (!reduce) {
      void el.offsetWidth;
      el.classList.add('is-hop');
      var ripple = document.createElement('span');
      ripple.className = 'km-evpin__ripple';
      ripple.setAttribute('aria-hidden', 'true');
      el.appendChild(ripple);
      setTimeout(function () { ripple.remove(); }, 900);
    }
    var whenChip = phaseOf(p, Date.now()) === 'running' ? '<span class="km-ev-chip km-ev-chip--live"><i aria-hidden="true"></i>' + esc(L.now) + '</span>'
      : p.when === 'today' ? '<span class="km-ev-chip km-ev-chip--hot">' + esc(L.today) + '</span>'
      : p.when === 'tomorrow' ? '<span class="km-ev-chip km-ev-chip--warm">' + esc(L.tomorrow) + '</span>'
      : p.when === 'weekend' ? '<span class="km-ev-chip km-ev-chip--warm">' + esc(L.weekend) + '</span>' : '';
    var date = p.long ? (p.day + ' ' + p.month + ' – ' + p.end_day + ' ' + p.end_month)
      : (p.weekday + ', ' + p.day + ' ' + p.month + ' · ' + p.time);
    var price = p.free ? L.free : p.price;
    if (this.kind === 'place') this.closeEnginePopup();
    this.show('event',
      '<a class="km-evcard__media" href="' + esc(p.url) + '" tabindex="-1" aria-hidden="true">' +
        (p.image ? '<img src="' + esc(p.image) + '" alt="" decoding="async">' : '<span class="km-evcard__ph material-symbols-rounded">celebration</span>') +
        '<span class="km-evcard__chips">' + whenChip + '</span>' +
        (price ? '<span class="km-evcard__price' + (p.free ? ' is-free' : '') + '">' + esc(price) + '</span>' : '') +
      '</a>' +
      '<div class="km-evcard__body">' +
        '<p class="km-evcard__when"><span class="material-symbols-rounded" aria-hidden="true">' + (p.long ? 'date_range' : 'schedule') + '</span>' + esc(date) + '</p>' +
        '<h3 class="km-evcard__title"><a href="' + esc(p.url) + '">' + esc(p.name) + '</a></h3>' +
        '<p class="km-evcard__meta">' + (p.category ? '<span class="km-ev-card__cat">' + esc(p.category) + '</span>' : '') +
          (p.age ? '<span>' + esc(p.age) + '</span>' : '') +
          ((p.languages || []).length ? '<span class="km-evcard__langs" title="' + esc((p.language_names || []).join(', ')) + '"><span class="material-symbols-rounded" aria-hidden="true">translate</span>' +
            p.languages.map(function (code) { return '<b>' + esc(code) + '</b>'; }).join('') + '</span>' : '') + '</p>' +
        ((p.venue || p.address) ? '<p class="km-evcard__place"><span class="material-symbols-rounded" aria-hidden="true">location_on</span>' + esc(p.venue || p.address) + '</p>' : '') +
        timerMarkup(p, L) +
        '<div class="km-evcard__actions">' +
          '<a class="km-ev-btn km-ev-btn--primary" href="' + esc(p.url) + '"><span>' + esc(L.details) + '</span><span class="material-symbols-rounded" aria-hidden="true">arrow_forward</span></a>' +
          '<a class="km-ev-btn km-ev-btn--ghost" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(p.lat + ',' + p.lng) + '"><span class="material-symbols-rounded" aria-hidden="true">near_me</span><span>' + esc(L.route) + '</span></a>' +
        '</div>' +
      '</div>');
    if (window.KidsMapTimers) window.KidsMapTimers.scan(this.card);
    this.pan(p);
  };

  Layer.prototype.pan = function (p) {
    if (!this.map) return;
    if (this.engine === 'google' && this.map.panTo) this.map.panTo({ lat: p.lat, lng: p.lng });
    else if (this.engine === 'leaflet') this.map.panTo([p.lat, p.lng], { animate: !reduce });
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
