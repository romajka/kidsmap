(function () {
  let catalogMapState = null;
  let catalogMapDocumentListenersBound = false;
  const MOBILE_MEDIA_QUERY = "(max-width: 767px)";
  const LEAFLET_DEFAULTS = {
    cssHref: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
    cssIntegrity: "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=",
    jsHref: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
    jsIntegrity: "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=",
  };
  const CATEGORY_SVGS = {
    CAMP: '<path d="m3 21 8.5-16.5a1 1 0 0 1 1 0L21 21"></path><path d="m8 12 4 8"></path><path d="m16 12-4 8"></path>',
    SPRT: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7c0 6 4 9 6 9s6-3 6-9V2Z"></path>',
    MUS: '<path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>',
    TECH: '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>',
    EDU: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>',
    ART: '<circle cx="13.5" cy="6.5" r=".5"></circle><circle cx="17.5" cy="10.5" r=".5"></circle><circle cx="8.5" cy="7.5" r=".5"></circle><circle cx="6.5" cy="12.5" r=".5"></circle><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"></path>',
    FUN: '<rect x="2" y="6" width="20" height="12" rx="2"></rect><path d="M6 12h4"></path><path d="M8 10v4"></path><circle cx="15" cy="13" r="1"></circle><circle cx="18" cy="11" r="1"></circle>',
    'early-development': '<path d="M12 22V12"></path><path d="M12 12C12 12 10 6 5 6C5 6 4 10 12 12Z"></path><path d="M12 16C12 16 15 10 19 10C19 10 20 14 12 16Z"></path>',
    dance: '<circle cx="12" cy="4" r="2" /><path d="M6 10c2-3 4-4 6-4s4 1 6 4" /><path d="M12 8c-3 4-5 7-6 11h12c-1-4-3-7-6-11z" /><path d="M10 19v3" /><path d="M14 19v3" />',
    'intellect-skills': '<path d="M20 7H17.8486C17.3511 7 17 6.49751 17 6C17 4.34315 15.6569 3 14 3C12.3431 3 11 4.34315 11 6C11 6.49751 10.6488 7 10.1513 7H8C7.44771 7 7 7.44772 7 8V10.1513C7 10.6488 6.49751 11 6 11C4.34315 11 3 12.3431 3 14C3 15.6569 4.34315 17 6 17C6.49751 17 7 17.3511 7 17.8486V20C7 20.5523 7.44771 21 8 21L20 21C20.5523 21 21 20.5523 21 20V17.8486C21 17.3511 20.4975 17 20 17C18.3431 17 17 15.6569 17 14C17 12.3431 18.3431 11 20 11C20.4975 11 21 10.6488 21 10.1513L21 8C21 7.44772 20.5523 7 20 7Z"/>',
    PARK: '<path d="M10 22v-6.5M18 22v-5M10 15.5a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9Z" /><path d="M18 17a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7Z" />',
    BEACH: '<path d="M4 11c1.8-3.7 5.1-6 8-6s6.2 2.3 8 6" /><path d="M12 5v14" /><path d="M8 11c.8-2.3 2.2-4.2 4-6 1.8 1.8 3.2 3.7 4 6" /><path d="M4 18c1.4-1 2.8-.5 4 0s2.6 1 4 0 2.8-1 4 0 2.6 1 4 0" />',
    WATERPARK: '<path d="M4 17V3h3"></path><path d="M4 7h3M4 11h3M4 15h3"></path><path d="M7 3c1.5 0 3 .5 4 2l4 6c1 1.5 2.5 2.5 4.5 2.5h2.5"></path><path d="M2 20c1.5-1 3.5-1 5 0s3.5 1 5 0s3.5-1 5 0s3.5 1 5 0"></path>',
    ZOO: '<circle cx="8" cy="8" r="2"></circle><circle cx="16" cy="8" r="2"></circle><circle cx="6" cy="15" r="1.5"></circle><circle cx="18" cy="15" r="1.5"></circle><path d="M8.5 18.5c.8-2.2 2.1-3.5 3.5-3.5s2.7 1.3 3.5 3.5c.5 1.3-.4 2.5-1.8 2.5h-3.4c-1.4 0-2.3-1.2-1.8-2.5Z"></path>'
  };

  function buildMarkerGlyph(place, colorText) {
    const categoryCode = place && place.category_code;
    const iconSvgContent = CATEGORY_SVGS[categoryCode] || '<rect x="3" y="3" width="7" height="7" rx="1.5"></rect><rect x="14" y="3" width="7" height="7" rx="1.5"></rect><rect x="14" y="14" width="7" height="7" rx="1.5"></rect><rect x="3" y="14" width="7" height="7" rx="1.5"></rect>';
    return (
      '<g transform="translate(11, 10) scale(0.667)">' +
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="' + colorText + '" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
      iconSvgContent +
      "</svg>" +
      "</g>"
    );
  }

  function buildDynamicMarkerSvg(place) {
    const bg = (place && place.category_color_bg) || "#F3F4F6";
    const text = (place && place.category_color_text) || "#6B7280";

    return '<svg xmlns="http://www.w3.org/2000/svg" width="38" height="48" viewBox="0 0 38 48" fill="none">' +
      '<path d="M19 47C13.5 39 3 31 3 18C3 8.5 10 1 19 1C28 1 35 8.5 35 18C35 31 24.5 39 19 47Z" fill="' + text + '" stroke="white" stroke-width="2.2"/>' +
      '<circle cx="19" cy="18" r="11" fill="white" />' +
      buildMarkerGlyph(place, text) +
      '</svg>';
  }

  function buildMarkerIcon(place) {
    const svg = buildDynamicMarkerSvg(place);
    return {
      url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
      scaledSize: new google.maps.Size(38, 48),
      anchor: new google.maps.Point(19, 48),
    };
  }

  function buildGoogleClusterSvg(count) {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="54" height="54" viewBox="0 0 54 54" fill="none">' +
      '<circle cx="27" cy="27" r="27" fill="rgba(17, 117, 67, 0.10)"/>' +
      '<circle cx="27" cy="27" r="25" fill="rgba(17, 117, 67, 0.18)"/>' +
      '<circle cx="27" cy="27" r="19" fill="#087443" stroke="white" stroke-width="3"/>' +
      '<text x="27" y="27" text-anchor="middle" dominant-baseline="central" fill="white" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="15px" font-weight="800">' + count + '</text>' +
      '</svg>';
  }

  function expandGoogleCluster(event, cluster, map) {
    if (!cluster || !cluster.bounds || !map) return;

    const currentZoom = map.getZoom() || 11;
    map.fitBounds(cluster.bounds, { top: 48, right: 48, bottom: 48, left: 48 });
    google.maps.event.addListenerOnce(map, "idle", function () {
      const zoomAfterFit = map.getZoom() || currentZoom;
      if (zoomAfterFit <= currentZoom && currentZoom < 18) {
        map.setZoom(Math.min(18, currentZoom + 2));
      }
    });
  }

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, function (char) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char];
    });
  }

  function loadStylesheet(href, integrity) {
    return new Promise(function (resolve, reject) {
      const existing = document.querySelector('link[rel="stylesheet"][href="' + href + '"]');
      if (existing) {
        if (existing.dataset.kmLoaded === "1") {
          resolve(existing);
          return;
        }
        existing.addEventListener("load", function () {
          existing.dataset.kmLoaded = "1";
          resolve(existing);
        }, { once: true });
        existing.addEventListener("error", function () {
          reject(new Error("Failed to load stylesheet: " + href));
        }, { once: true });
        return;
      }

      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      if (integrity) {
        link.integrity = integrity;
        link.crossOrigin = "anonymous";
      }
      link.addEventListener("load", function () {
        link.dataset.kmLoaded = "1";
        resolve(link);
      }, { once: true });
      link.addEventListener("error", function () {
        reject(new Error("Failed to load stylesheet: " + href));
      }, { once: true });
      document.head.appendChild(link);
    });
  }

  function loadScript(href, integrity) {
    return new Promise(function (resolve, reject) {
      const existing = document.querySelector('script[src="' + href + '"]');
      if (existing) {
        if (existing.dataset.kmLoaded === "1") {
          resolve(existing);
          return;
        }
        existing.addEventListener("load", function () {
          existing.dataset.kmLoaded = "1";
          resolve(existing);
        }, { once: true });
        existing.addEventListener("error", function () {
          reject(new Error("Failed to load script: " + href));
        }, { once: true });
        return;
      }

      const script = document.createElement("script");
      script.src = href;
      if (integrity) {
        script.integrity = integrity;
        script.crossOrigin = "anonymous";
      }
      script.addEventListener("load", function () {
        script.dataset.kmLoaded = "1";
        resolve(script);
      }, { once: true });
      script.addEventListener("error", function () {
        reject(new Error("Failed to load script: " + href));
      }, { once: true });
      document.head.appendChild(script);
    });
  }

  function parsePlaces() {
    const dataEl = document.getElementById("catalog-map-data");
    if (!dataEl) return [];

    try {
      return JSON.parse(dataEl.textContent || "[]");
    } catch (_error) {
      return [];
    }
  }

  function hasValidCoordinates(place) {
    return (
      place &&
      Number.isFinite(place.lat) &&
      Number.isFinite(place.lng) &&
      place.lat >= -90 &&
      place.lat <= 90 &&
      place.lng >= -180 &&
      place.lng <= 180
    );
  }

  function isMobileViewport() {
    return window.matchMedia(MOBILE_MEDIA_QUERY).matches;
  }

  function formatRating(place, noRatingLabel) {
    const rating = Number(place.rating);
    const reviewsCount = Number(place.reviews_count || 0);
    if (!Number.isFinite(rating) || rating <= 0 || reviewsCount <= 0) {
      return {
        isEmpty: true,
        text: noRatingLabel,
      };
    }

    return {
      isEmpty: false,
      text: rating.toFixed(1) + " (" + reviewsCount + ")",
    };
  }

  function getAddressText(place, noAddressLabel) {
    return place.address || place.location || noAddressLabel;
  }

  function getRouteUrl(place) {
    if (typeof place.lat !== "number" || typeof place.lng !== "number") return "";
    return "https://www.google.com/maps/dir/?api=1&destination=" + encodeURIComponent(place.lat + "," + place.lng);
  }

  function getPhoneHref(place) {
    const rawPhone = String(place.phone || "").trim();
    if (!rawPhone) return "";
    return "tel:" + rawPhone.replace(/\s+/g, "");
  }

  function renderActionButton(options) {
    const classes = ["catalog-map-card-action", options.kind ? "is-" + options.kind : ""];
    if (options.iconOnly) {
      classes.push("is-icon-only");
    }

    const attrs = [];
    if (options.href) {
      attrs.push('href="' + escapeHtml(options.href) + '"');
    }
    if (options.targetBlank) {
      attrs.push('target="_blank" rel="noopener"');
    }
    if (options.disabled) {
      attrs.push('aria-disabled="true" tabindex="-1"');
    }
    if (options.ariaLabel) {
      attrs.push('aria-label="' + escapeHtml(options.ariaLabel) + '"');
    }

    const tagName = options.href && !options.disabled ? "a" : "span";
    return (
      "<" +
      tagName +
      ' class="' +
      classes.join(" ") +
      (options.disabled ? " is-disabled" : "") +
      '" ' +
      attrs.join(" ") +
      ">" +
      (options.icon || "") +
      (options.label ? '<span class="catalog-map-card-action-label">' + escapeHtml(options.label) + "</span>" : "") +
      "</" +
      tagName +
      ">"
    );
  }

  function renderMapCard(place, labels, isMobile) {
    const rating = formatRating(place, labels.noRatingLabel);
    const address = getAddressText(place, labels.noAddressLabel);
    const routeUrl = getRouteUrl(place);
    const phoneHref = getPhoneHref(place);
    const image = place.image_url
      ? '<img class="catalog-map-card-image" src="' +
        escapeHtml(place.image_url) +
        '" alt="' +
        escapeHtml(place.name || "") +
        '" loading="lazy" decoding="async" />'
      : '<div class="catalog-map-card-image catalog-map-card-image-placeholder">' +
        '<span>' +
        escapeHtml(labels.noImageLabel) +
        "</span>" +
        "</div>";

    const detailsButton = renderActionButton({
      href: place.url || "",
      label: labels.detailsLabel,
      kind: "primary",
    });
    const routeButton = renderActionButton({
      href: routeUrl,
      label: labels.routeLabel,
      kind: "secondary",
      targetBlank: true,
      disabled: !routeUrl,
    });
    const phoneButton = renderActionButton({
      href: phoneHref,
      label: isMobile ? labels.callLabel : "",
      ariaLabel: labels.callLabel,
      kind: isMobile ? "secondary" : "icon",
      iconOnly: !isMobile,
      disabled: !phoneHref,
      icon:
        '<svg class="catalog-map-card-action-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M6.6 10.8c1.8 3.53 3.08 4.82 6.6 6.6l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.32.57 3.58.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1C10.61 21 3 13.39 3 4c0-.55.45-1 1-1h3.49c.55 0 1 .45 1 1 0 1.26.2 2.46.57 3.58.12.35.03.75-.24 1.02l-2.22 2.2Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    });

    return (
      '<div class="catalog-map-card-shell">' +
      (isMobile ? '<div class="catalog-map-card-handle" aria-hidden="true"></div>' : "") +
      '<button type="button" class="catalog-map-card-close" data-map-card-close aria-label="' +
      escapeHtml(labels.closeLabel) +
      '">×</button>' +
      '<div class="catalog-map-card-main">' +
      '<div class="catalog-map-card-media">' +
      image +
      "</div>" +
      '<div class="catalog-map-card-body">' +
      '<strong class="catalog-map-card-title">' +
      escapeHtml(place.name || "") +
      "</strong>" +
      (place.category
        ? '<span class="catalog-map-card-category">' + escapeHtml(place.category) + "</span>"
        : "") +
      '<div class="catalog-map-card-rating' +
      (rating.isEmpty ? " is-empty" : "") +
      '">' +
      '<span class="catalog-map-card-rating-star" aria-hidden="true">★</span>' +
      '<span>' +
      escapeHtml(rating.text) +
      "</span>" +
      "</div>" +
      '<div class="catalog-map-card-address">' +
      '<svg class="catalog-map-card-address-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 21s6-5.69 6-11a6 6 0 1 0-12 0c0 5.31 6 11 6 11Z" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="10" r="2.4" stroke="currentColor" stroke-width="1.8"/></svg>' +
      '<span>' +
      escapeHtml(address) +
      "</span>" +
      "</div>" +
      "</div>" +
      "</div>" +
      '<div class="catalog-map-card-actions">' +
      detailsButton +
      routeButton +
      phoneButton +
      "</div>" +
      "</div>"
    );
  }

  function renderCatalogMapState(mapEl, message, className) {
    if (!mapEl) return;
    const body =
      className === "catalog-map-loading"
        ? '<div class="catalog-map-loading-content"><span class="ui-loader ui-loader-dark" aria-hidden="true"></span><p>' +
          escapeHtml(message) +
          "</p></div>"
        : "<p>" + escapeHtml(message) + "</p>";
    mapEl.innerHTML =
      '<div class="' +
      className +
      '">' +
      body +
      "</div>";
  }

  function ensureCatalogMapState() {
    if (catalogMapState) return catalogMapState;

    const panel = document.querySelector("[data-catalog-map-panel]");
    const mapEl = document.querySelector("[data-catalog-map]");
    const openBtn = document.querySelector("[data-catalog-map-open]");
    const closeBtn = document.querySelector("[data-catalog-map-close]");
    if (!panel || !mapEl || !openBtn || !closeBtn) return null;

    catalogMapState = {
      panel: panel,
      mapEl: mapEl,
      openBtn: openBtn,
      closeBtn: closeBtn,
      places: parsePlaces().filter(hasValidCoordinates),
      provider: (panel.dataset.mapProvider || "").trim(),
      detailsLabel: panel.dataset.detailsLabel || "",
      routeLabel: panel.dataset.routeLabel || "",
      callLabel: panel.dataset.callLabel || "",
      closeLabel: panel.dataset.closeLabel || "",
      noRatingLabel: panel.dataset.noRatingLabel || "",
      noAddressLabel: panel.dataset.noAddressLabel || "",
      noImageLabel: panel.dataset.noImageLabel || "",
      markerLabel: panel.dataset.markerLabel || "{name}",
      emptyMessage: panel.dataset.emptyMessage || "",
      fallbackMessage: panel.dataset.fallbackMessage || "",
      loadingMessage: panel.dataset.loadingMessage || "",
      initialized: false,
      bound: false,
      googleMap: null,
      leafletMap: null,
      bounds: null,
      projectionHelper: null,
      markersByUrl: {},
      activePlace: null,
      activeMarker: null,
      desktopCardEl: null,
      mobileSheetEl: null,
      activeListeners: [],
      mobileMedia: window.matchMedia(MOBILE_MEDIA_QUERY),
    };

    return catalogMapState;
  }

  function fitCatalogMapBounds(state) {
    if (!state || !state.googleMap || !state.bounds) return;
    if (state.places.length === 1) {
      state.googleMap.setCenter(state.bounds.getCenter());
      state.googleMap.setZoom(15);
      return;
    }
    state.googleMap.fitBounds(state.bounds);
  }

  function fitCatalogLeafletBounds(state) {
    if (!state || !state.leafletMap || !state.places.length) return;
    if (state.places.length === 1) {
      state.leafletMap.setView([state.places[0].lat, state.places[0].lng], 15);
      return;
    }
    const bounds = L.latLngBounds(
      state.places.map(function (place) {
        return [place.lat, place.lng];
      })
    );
    state.leafletMap.fitBounds(bounds, { padding: [24, 24] });
  }

  function ensureMapChrome(state) {
    if (!state || !state.mapEl) return;

    let desktopCardEl = state.mapEl.querySelector("[data-map-desktop-card]");
    if (!desktopCardEl) {
      desktopCardEl = document.createElement("div");
      desktopCardEl.className = "catalog-map-desktop-card";
      desktopCardEl.setAttribute("data-map-desktop-card", "");
      desktopCardEl.hidden = true;
      state.mapEl.appendChild(desktopCardEl);
    }

    let mobileSheetEl = state.mapEl.querySelector("[data-map-mobile-sheet]");
    if (!mobileSheetEl) {
      mobileSheetEl = document.createElement("div");
      mobileSheetEl.className = "catalog-map-mobile-sheet";
      mobileSheetEl.setAttribute("data-map-mobile-sheet", "");
      mobileSheetEl.hidden = true;
      state.mapEl.appendChild(mobileSheetEl);
    }

    state.desktopCardEl = desktopCardEl;
    state.mobileSheetEl = mobileSheetEl;
  }

  function closeActiveCard(state, restoreMarkerFocus) {
    if (!state) return;
    const marker = state.activeMarker;
    state.activePlace = null;
    state.activeMarker = null;
    if (state.desktopCardEl) {
      state.desktopCardEl.hidden = true;
      state.desktopCardEl.innerHTML = "";
      state.desktopCardEl.classList.remove("is-below");
    }
    if (state.mobileSheetEl) {
      state.mobileSheetEl.hidden = true;
      state.mobileSheetEl.innerHTML = "";
      state.mobileSheetEl.classList.remove("is-open");
    }
    if (restoreMarkerFocus && marker) {
      const markerEl = typeof marker.getElement === "function" ? marker.getElement() : null;
      if (markerEl) markerEl.focus();
    }
  }

  function positionDesktopCard(state) {
    if (!state || !state.activeMarker || !state.desktopCardEl || isMobileViewport()) {
      return;
    }

    let point = null;
    if (state.googleMap && state.projectionHelper) {
      const projection = state.projectionHelper.getProjection();
      if (!projection) return;
      point = projection.fromLatLngToContainerPixel(state.activeMarker.getPosition());
    } else if (state.leafletMap) {
      const latLng = state.activeMarker.getLatLng();
      point = state.leafletMap.latLngToContainerPoint(latLng);
    }
    if (!point) return;

    const mapRect = state.mapEl.getBoundingClientRect();
    const cardRect = state.desktopCardEl.getBoundingClientRect();
    const left = Math.max(12, Math.min(point.x + 18, mapRect.width - cardRect.width - 12));
    let top = point.y - cardRect.height - 20;
    let placeBelow = false;

    if (top < 12) {
      top = Math.min(point.y + 20, mapRect.height - cardRect.height - 12);
      placeBelow = true;
    }

    state.desktopCardEl.style.left = left + "px";
    state.desktopCardEl.style.top = top + "px";
    state.desktopCardEl.classList.toggle("is-below", placeBelow);
  }

  function openActiveCard(state, place, marker) {
    if (!state || !place || !marker) return;

    ensureMapChrome(state);
    state.activePlace = place;
    state.activeMarker = marker;

    const labels = {
      detailsLabel: state.detailsLabel,
      routeLabel: state.routeLabel,
      callLabel: state.callLabel,
      closeLabel: state.closeLabel,
      noRatingLabel: state.noRatingLabel,
      noAddressLabel: state.noAddressLabel,
      noImageLabel: state.noImageLabel,
    };

    if (isMobileViewport()) {
      state.desktopCardEl.hidden = true;
      state.desktopCardEl.innerHTML = "";
      state.mobileSheetEl.innerHTML = renderMapCard(place, labels, true);
      state.mobileSheetEl.hidden = false;
      state.mobileSheetEl.classList.add("is-open");
      window.requestAnimationFrame(function () {
        if (state.googleMap) {
          state.googleMap.panTo(marker.getPosition());
          state.googleMap.panBy(0, 140);
        } else if (state.leafletMap) {
          state.leafletMap.panTo(marker.getLatLng(), { animate: true });
        }
      });
      return;
    }

    state.mobileSheetEl.hidden = true;
    state.mobileSheetEl.innerHTML = "";
    state.mobileSheetEl.classList.remove("is-open");
    state.desktopCardEl.innerHTML = renderMapCard(place, labels, false);
    state.desktopCardEl.hidden = false;
    positionDesktopCard(state);
  }

  function initCatalogGoogleMap() {
    const state = ensureCatalogMapState();
    if (!state || state.initialized) return;

    if (!state.places.length) {
      renderCatalogMapState(state.mapEl, state.emptyMessage, "catalog-map-empty");
      state.initialized = true;
      return;
    }

    if (!window.google || !window.google.maps) {
      renderCatalogMapState(state.mapEl, state.loadingMessage, "catalog-map-loading");
      return;
    }

    if (!window.markerClusterer) {
      renderCatalogMapState(state.mapEl, state.loadingMessage, "catalog-map-loading");
      loadScript("https://unpkg.com/@googlemaps/markerclusterer/dist/index.min.js")
        .then(function () {
          initCatalogGoogleMap();
        })
        .catch(function () {
          window.markerClusterer = { dummy: true };
          initCatalogGoogleMap();
        });
      return;
    }

    state.googleMap = new google.maps.Map(state.mapEl, {
      center: { lat: state.places[0].lat, lng: state.places[0].lng },
      zoom: state.places.length === 1 ? 15 : 11,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      gestureHandling: "cooperative",
      clickableIcons: false,
    });

    state.bounds = new google.maps.LatLngBounds();
    ensureMapChrome(state);

    state.projectionHelper = new google.maps.OverlayView();
    state.projectionHelper.onAdd = function () {};
    state.projectionHelper.draw = function () {
      positionDesktopCard(state);
    };
    state.projectionHelper.onRemove = function () {};
    state.projectionHelper.setMap(state.googleMap);

    const activeMarkers = [];
    // Track coordinate pairs to detect duplicates and jitter them slightly
    const coordCount = {};
    state.places.forEach(function (place) {
      const key = place.lat + ',' + place.lng;
      coordCount[key] = (coordCount[key] || 0) + 1;
    });
    const coordIndex = {};
    state.places.forEach(function (place) {
      const key = place.lat + ',' + place.lng;
      const total = coordCount[key];
      const idx = coordIndex[key] = (coordIndex[key] || 0);
      coordIndex[key]++;
      // If multiple places share exact coordinates, spiral them slightly apart
      var jitterLat = 0, jitterLng = 0;
      if (total > 1 && idx > 0) {
        var angle = (idx / total) * 2 * Math.PI;
        var radius = 0.00012 * Math.ceil(idx / 6);
        jitterLat = radius * Math.cos(angle);
        jitterLng = radius * Math.sin(angle) * 1.5;
      }
      const position = { lat: place.lat + jitterLat, lng: place.lng + jitterLng };
      const marker = new google.maps.Marker({
        position: position,
        title: place.name || "",
        icon: buildMarkerIcon(place),
      });

      if (place.url) {
        state.markersByUrl[place.url] = marker;
      }

      marker.addListener("click", function () {
        openActiveCard(state, place, marker);
      });

      marker.addListener("mouseover", function () {
        if (!place.url) return;
        const cardLink = document.querySelector('a[href="' + place.url + '"]');
        if (!cardLink) return;
        const card = cardLink.closest(".card");
        if (!card) return;
        card.style.transform = "translateY(-4px)";
        card.style.boxShadow = "0 16px 32px rgba(34, 61, 73, 0.12)";
      });

      marker.addListener("mouseout", function () {
        if (!place.url) return;
        const cardLink = document.querySelector('a[href="' + place.url + '"]');
        if (!cardLink) return;
        const card = cardLink.closest(".card");
        if (!card) return;
        card.style.transform = "";
        card.style.boxShadow = "";
      });

      activeMarkers.push(marker);
      state.bounds.extend(position);
    });

    if (window.markerClusterer && window.markerClusterer.MarkerClusterer && !window.markerClusterer.dummy) {
      var clusterAlgorithm = (window.markerClusterer.SuperClusterAlgorithm)
        ? new window.markerClusterer.SuperClusterAlgorithm({ maxZoom: 18, radius: 100 })
        : undefined;
      state.markerCluster = new window.markerClusterer.MarkerClusterer({
        map: state.googleMap,
        markers: activeMarkers,
        algorithm: clusterAlgorithm,
        renderer: {
          render: function (cluster, stats, mapInstance) {
            const count = cluster.count;
            const position = cluster.position;
            const svg = buildGoogleClusterSvg(count);
            return new google.maps.Marker({
              position: position,
              icon: {
                url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
                scaledSize: new google.maps.Size(54, 54),
                anchor: new google.maps.Point(27, 27),
              },
              zIndex: Number(google.maps.Marker.MAX_ZINDEX) + count,
            });
          }
        },
        onClusterClick: expandGoogleCluster,
      });
    } else {
      activeMarkers.forEach(function (marker) {
        marker.setMap(state.googleMap);
      });
    }

    state.activeListeners.push(
      state.googleMap.addListener("click", function () {
        closeActiveCard(state);
      })
    );
    state.activeListeners.push(
      state.googleMap.addListener("idle", function () {
        positionDesktopCard(state);
      })
    );

    document.querySelectorAll(".card").forEach(function (card) {
      card.addEventListener("mouseenter", function () {
        const link = card.querySelector("a");
        if (link && link.getAttribute("href") && state.markersByUrl[link.getAttribute("href")]) {
          const marker = state.markersByUrl[link.getAttribute("href")];
          marker.setAnimation(google.maps.Animation.BOUNCE);
          window.setTimeout(function () {
            marker.setAnimation(null);
          }, 700);
        }
      });

      card.addEventListener("mouseleave", function () {
        const link = card.querySelector("a");
        if (link && link.getAttribute("href") && state.markersByUrl[link.getAttribute("href")]) {
          state.markersByUrl[link.getAttribute("href")].setAnimation(null);
        }
      });
    });

    state.mapEl.addEventListener("click", function (event) {
      if (event.target.closest("[data-map-card-close]")) {
        event.preventDefault();
        closeActiveCard(state, true);
      }
    });

    state.initialized = true;
    fitCatalogMapBounds(state);
  }

  function initCatalogFallbackState() {
    const state = ensureCatalogMapState();
    if (!state || state.initialized) return;
    if (!state.places.length) {
      renderCatalogMapState(state.mapEl, state.emptyMessage, "catalog-map-empty");
      state.initialized = true;
      return;
    }

    if (!window.L || !window.L.markerClusterGroup) {
      renderCatalogMapState(state.mapEl, state.loadingMessage, "catalog-map-loading");
      const leafletReady = window.L
        ? Promise.resolve()
        : loadStylesheet(LEAFLET_DEFAULTS.cssHref, LEAFLET_DEFAULTS.cssIntegrity).then(function () {
            return loadScript(LEAFLET_DEFAULTS.jsHref, LEAFLET_DEFAULTS.jsIntegrity);
          });
      leafletReady
        .then(function () {
          if (window.L && window.L.markerClusterGroup) return;
          return Promise.all([
            loadStylesheet("https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css"),
            loadStylesheet("https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css"),
            loadScript("https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js")
          ]);
        })
        .then(function () {
          catalogMapState.initialized = false;
          initCatalogFallbackState();
        })
        .catch(function () {
          renderCatalogMapState(state.mapEl, state.fallbackMessage, "catalog-map-empty");
          state.initialized = true;
        });
      return;
    }

    state.mapEl.innerHTML = "";
    ensureMapChrome(state);
    state.leafletMap = L.map(state.mapEl, {
      scrollWheelZoom: false,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(state.leafletMap);

    function buildLeafletMarkerHtml(place) {
      const categoryCode = place && place.category_code;
      const iconSvgContent = CATEGORY_SVGS[categoryCode] || '<rect x="3" y="3" width="7" height="7" rx="1.5"></rect><rect x="14" y="3" width="7" height="7" rx="1.5"></rect><rect x="14" y="14" width="7" height="7" rx="1.5"></rect><rect x="3" y="14" width="7" height="7" rx="1.5"></rect>';
      const colorBg = (place && place.category_color_bg) || "#F3F4F6";
      const colorText = (place && place.category_color_text) || "#6B7280";

      const svg = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="' + colorBg + '" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="width: 100%; height: 100%;">' +
        iconSvgContent +
        '</svg>';

      return `
        <div class="custom-animated-pin-wrapper">
          <div class="pin-pulse" style="--accent: ${colorText};"></div>
          <div class="pin-body" style="background-color: ${colorText}; color: ${colorBg};">
            <div class="pin-icon-wrap">
              ${svg}
            </div>
            <div class="pin-pointer" style="border-top-color: ${colorText};"></div>
          </div>
        </div>
      `;
    }

    state.markerClusterGroup = L.markerClusterGroup({
      showCoverageOnHover: false,
      zoomToBoundsOnClick: false,
      spiderfyOnMaxZoom: true,
      disableClusteringAtZoom: 14,
      maxClusterRadius: function (zoom) {
        if (zoom >= 12) return 30;
        if (zoom >= 10) return 40;
        return 48;
      },
      iconCreateFunction: function (cluster) {
        const count = cluster.getChildCount();
        return L.divIcon({
          className: "kidsmap-map-cluster",
          html: "<span class=\"kidsmap-map-cluster__count\">" + count + "</span>",
          iconSize: [54, 54],
          iconAnchor: [27, 27],
        });
      }
    });
    state.leafletMap.addLayer(state.markerClusterGroup);
    function handleCatalogClusterClick(event) {
      const childMarkers = event.layer.getAllChildMarkers();

      let allSameCoords = true;
      if (childMarkers.length > 0) {
        const firstLatLng = childMarkers[0].getLatLng();
        for (let i = 1; i < childMarkers.length; i++) {
          const latLng = childMarkers[i].getLatLng();
          if (latLng.lat !== firstLatLng.lat || latLng.lng !== firstLatLng.lng) {
            allSameCoords = false;
            break;
          }
        }
      }

      if (allSameCoords && childMarkers.length > 0) {
        state.leafletMap.setView(childMarkers[0].getLatLng(), 18, { animate: true });
        event.layer.spiderfy();
      } else {
        state.leafletMap.fitBounds(event.layer.getBounds(), {
          padding: [24, 24],
          animate: true,
          duration: 0.35
        });
      }
    }

    state.markerClusterGroup.on("clusterclick", handleCatalogClusterClick);

    const layersToAdd = [];
    state.places.forEach(function (place) {
      const htmlContent = buildLeafletMarkerHtml(place);
      const marker = L.marker([place.lat, place.lng], {
        title: place.name || "",
        alt: state.markerLabel.replace("{name}", place.name || ""),
        icon: L.divIcon({
          className: "custom-map-pin",
          html: htmlContent,
          iconSize: [44, 46],
          iconAnchor: [22, 46],
          popupAnchor: [0, -44]
        }),
      });

      window.requestAnimationFrame(function () {
        const markerEl = marker.getElement();
        if (!markerEl) return;
        const markerLabel = state.markerLabel.replace("{name}", place.name || "");
        markerEl.setAttribute("role", "button");
        markerEl.setAttribute("aria-label", markerLabel);
        markerEl.setAttribute("title", markerLabel);
      });

      if (place.url) {
        state.markersByUrl[place.url] = marker;
      }

      marker.on("click", function () {
        openActiveCard(state, place, marker);
      });

      layersToAdd.push(marker);
    });

    if (layersToAdd.length) {
      state.markerClusterGroup.addLayers(layersToAdd);
      state.markerClusterGroup.refreshClusters();
    }

    state.leafletMap.on("click", function () {
      closeActiveCard(state);
    });
    state.leafletMap.on("move zoom resize", function () {
      positionDesktopCard(state);
    });

    state.mapEl.addEventListener("mouseenter", function () {
      if (state.leafletMap) {
        state.leafletMap.scrollWheelZoom.enable();
      }
    });
    state.mapEl.addEventListener("mouseleave", function () {
      if (state.leafletMap) {
        state.leafletMap.scrollWheelZoom.disable();
      }
    });

    state.initialized = true;
    fitCatalogLeafletBounds(state);
    window.setTimeout(function () {
      if (state.leafletMap) {
        state.leafletMap.invalidateSize();
      }
    }, 0);
  }

  function ensureCatalogMapInitialized() {
    const state = ensureCatalogMapState();
    if (!state) return;

    if (state.provider !== "google") {
      renderCatalogMapState(state.mapEl, state.fallbackMessage, "catalog-map-empty");
      state.initialized = true;
      return;
    }

    initCatalogGoogleMap();
    if (state.googleMap) {
      google.maps.event.trigger(state.googleMap, "resize");
      fitCatalogMapBounds(state);
      positionDesktopCard(state);
    }
  }

  function setCatalogMapOpen(isOpen) {
    const state = ensureCatalogMapState();
    if (!state) return;

    state.panel.hidden = !isOpen;
    state.openBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
    state.openBtn.classList.toggle("is-active", isOpen);

    if (isOpen) {
      requestAnimationFrame(function () {
        ensureCatalogMapInitialized();
      });
      return;
    }

    closeActiveCard(state);
  }

  function initCatalogMapUi() {
    const state = ensureCatalogMapState();
    if (!state || state.bound) return;
    state.bound = true;

    state.openBtn.addEventListener("click", function () {
      setCatalogMapOpen(state.panel.hidden);
    });

    state.closeBtn.addEventListener("click", function () {
      setCatalogMapOpen(false);
      state.openBtn.focus();
    });

    if (!catalogMapDocumentListenersBound) {
      catalogMapDocumentListenersBound = true;
      document.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") return;
        const currentState = ensureCatalogMapState();
        if (!currentState) return;
        if (currentState.activePlace) {
          closeActiveCard(currentState, true);
          return;
        }
        if (!currentState.panel.hidden) {
          setCatalogMapOpen(false);
          currentState.openBtn.focus();
        }
      });
    }

    const handleViewportChange = function () {
      if (!state.activePlace || !state.activeMarker) return;
      openActiveCard(state, state.activePlace, state.activeMarker);
    };

    if (typeof state.mobileMedia.addEventListener === "function") {
      state.mobileMedia.addEventListener("change", handleViewportChange);
    } else if (typeof state.mobileMedia.addListener === "function") {
      state.mobileMedia.addListener(handleViewportChange);
    }
  }

  window.kidsMapInitCatalogResultsMap = function () {
    initCatalogMapUi();
    const state = ensureCatalogMapState();
    if (!state || state.panel.hidden) return;
    ensureCatalogMapInitialized();
  };

  window.kidsMapRefreshCatalogResultsMap = function () {
    catalogMapState = null;
    initCatalogMapUi();
    const state = ensureCatalogMapState();
    if (!state || state.panel.hidden) return;
    ensureCatalogMapInitialized();
  };

  initCatalogMapUi();
})();
