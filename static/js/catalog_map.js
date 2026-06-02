(function () {
  let catalogMapState = null;
  const MOBILE_MEDIA_QUERY = "(max-width: 767px)";
  const LEAFLET_DEFAULTS = {
    cssHref: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
    cssIntegrity: "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=",
    jsHref: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
    jsIntegrity: "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=",
  };
  const CATEGORY_MARKER_STYLES = {
    SPRT: { fill: "#0f9f5b", inner: "#dff7ea", label: "SP" },
    ART: { fill: "#ff8a3d", inner: "#fff0e4", label: "AR" },
    MUS: { fill: "#3f7cff", inner: "#eaf0ff", label: "MU" },
    EDU: { fill: "#7c5cff", inner: "#f0ecff", label: "ED" },
    TECH: { fill: "#00a7a0", inner: "#def7f5", label: "TE" },
    FUN: { fill: "#ff5d73", inner: "#ffe8ed", label: "FU" },
    CAMP: { fill: "#c98a0a", inner: "#fff4d9", label: "CA" },
    DEFAULT: { fill: "#08a05c", inner: "#d9f7e7", label: "KM" },
  };

  function buildMarkerIcon(place) {
    const markerStyle = CATEGORY_MARKER_STYLES[place.category_code] || CATEGORY_MARKER_STYLES.DEFAULT;
    const svg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="44" viewBox="0 0 36 44" fill="none">' +
      '<path d="M18 1.5C9.44 1.5 2.5 8.44 2.5 17c0 11.41 12.35 23.56 14.3 25.39a1.75 1.75 0 0 0 2.4 0C21.15 40.56 33.5 28.41 33.5 17 33.5 8.44 26.56 1.5 18 1.5Z" fill="' + markerStyle.fill + '" stroke="white" stroke-width="3"/>' +
      '<circle cx="18" cy="17" r="8" fill="' + markerStyle.inner + '" stroke="white" stroke-width="2"/>' +
      '<text x="18" y="20.4" text-anchor="middle" font-family="Arial, sans-serif" font-size="6.2" font-weight="700" fill="' + markerStyle.fill + '">' +
      markerStyle.label +
      "</text>" +
      "</svg>";

    return {
      url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
      scaledSize: new google.maps.Size(36, 44),
      anchor: new google.maps.Point(18, 44),
    };
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
      places: parsePlaces().filter(function (place) {
        return typeof place.lat === "number" && typeof place.lng === "number";
      }),
      provider: (panel.dataset.mapProvider || "").trim(),
      detailsLabel: panel.dataset.detailsLabel || "",
      routeLabel: panel.dataset.routeLabel || "",
      callLabel: panel.dataset.callLabel || "",
      closeLabel: panel.dataset.closeLabel || "",
      noRatingLabel: panel.dataset.noRatingLabel || "",
      noAddressLabel: panel.dataset.noAddressLabel || "",
      noImageLabel: panel.dataset.noImageLabel || "",
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

  function closeActiveCard(state) {
    if (!state) return;
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

    state.places.forEach(function (place) {
      const position = { lat: place.lat, lng: place.lng };
      const marker = new google.maps.Marker({
        position: position,
        map: state.googleMap,
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

      state.bounds.extend(position);
    });

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
        closeActiveCard(state);
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

    if (!window.L) {
      renderCatalogMapState(state.mapEl, state.loadingMessage, "catalog-map-loading");
      loadStylesheet(LEAFLET_DEFAULTS.cssHref, LEAFLET_DEFAULTS.cssIntegrity)
        .then(function () {
          return loadScript(LEAFLET_DEFAULTS.jsHref, LEAFLET_DEFAULTS.jsIntegrity);
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

    state.places.forEach(function (place) {
      const markerStyle = CATEGORY_MARKER_STYLES[place.category_code] || CATEGORY_MARKER_STYLES.DEFAULT;
      const marker = L.marker([place.lat, place.lng], {
        icon: L.divIcon({
          className: "catalog-map-leaflet-pin",
          html:
            '<div class="catalog-map-leaflet-pin-core" style="--pin-fill:' +
            markerStyle.fill +
            ";--pin-inner:" +
            markerStyle.inner +
            ';">' +
            '<span>' +
            escapeHtml(markerStyle.label) +
            "</span></div>",
          iconSize: [36, 44],
          iconAnchor: [18, 44],
        }),
      }).addTo(state.leafletMap);

      if (place.url) {
        state.markersByUrl[place.url] = marker;
      }

      marker.on("click", function () {
        openActiveCard(state, place, marker);
      });
    });

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

    if (state.provider === "google") {
      initCatalogGoogleMap();
      if (state.googleMap) {
        google.maps.event.trigger(state.googleMap, "resize");
        fitCatalogMapBounds(state);
        positionDesktopCard(state);
      }
      return;
    }

    initCatalogFallbackState();
    if (state.leafletMap) {
      state.leafletMap.invalidateSize();
      fitCatalogLeafletBounds(state);
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
    });

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
