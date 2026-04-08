(function () {
  let catalogMapState = null;

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

  function parsePlaces() {
    const dataEl = document.getElementById("catalog-map-data");
    if (!dataEl) return [];

    try {
      return JSON.parse(dataEl.textContent || "[]");
    } catch (_error) {
      return [];
    }
  }

  function renderPopupContent(place, detailsLabel) {
    const image = place.image_url
      ? '<a class="home-map-popup-thumb-link" href="' +
        escapeHtml(place.url || "") +
        '">' +
        '<img class="home-map-popup-thumb" src="' +
        escapeHtml(place.image_url) +
        '" alt="' +
        escapeHtml(place.name || "") +
        '" loading="lazy" />' +
        "</a>"
      : "";

    const location = place.location
      ? '<span class="home-map-popup-category">' + escapeHtml(place.location) + "</span>"
      : "";

    return (
      '<div class="home-map-popup">' +
      image +
      '<div class="home-map-popup-body">' +
      '<strong class="home-map-popup-title">' +
      escapeHtml(place.name || "") +
      "</strong>" +
      '<span class="home-map-popup-category">' +
      escapeHtml(place.category || "") +
      "</span>" +
      location +
      '<a class="home-map-popup-link" href="' +
      escapeHtml(place.url || "") +
      '">' +
      escapeHtml(detailsLabel) +
      "</a>" +
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
      detailsLabel: panel.dataset.detailsLabel || "Details",
      emptyMessage: panel.dataset.emptyMessage || "No map points found.",
      fallbackMessage: panel.dataset.fallbackMessage || "Map is not available.",
      loadingMessage: panel.dataset.loadingMessage || "Loading map...",
      initialized: false,
      bound: false,
      googleMap: null,
      bounds: null,
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
    });

    state.bounds = new google.maps.LatLngBounds();
    const infoWindow = new google.maps.InfoWindow();

    state.places.forEach(function (place) {
      const position = { lat: place.lat, lng: place.lng };
      const marker = new google.maps.Marker({
        position: position,
        map: state.googleMap,
        title: place.name || "",
      });

      marker.addListener("click", function () {
        infoWindow.setContent(renderPopupContent(place, state.detailsLabel));
        infoWindow.open({
          anchor: marker,
          map: state.googleMap,
        });
      });

      state.bounds.extend(position);
    });

    state.initialized = true;
    fitCatalogMapBounds(state);
  }

  function initCatalogFallbackState() {
    const state = ensureCatalogMapState();
    if (!state || state.initialized) return;
    const message = state.places.length ? state.fallbackMessage : state.emptyMessage;
    renderCatalogMapState(state.mapEl, message, "catalog-map-empty");
    state.initialized = true;
  }

  function ensureCatalogMapInitialized() {
    const state = ensureCatalogMapState();
    if (!state) return;

    if (state.provider === "google") {
      initCatalogGoogleMap();
      if (state.googleMap) {
        google.maps.event.trigger(state.googleMap, "resize");
        fitCatalogMapBounds(state);
      }
      return;
    }

    initCatalogFallbackState();
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
    }
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
  }

  window.kidsMapInitCatalogResultsMap = function () {
    initCatalogMapUi();
    const state = ensureCatalogMapState();
    if (!state || state.panel.hidden) return;
    ensureCatalogMapInitialized();
  };

  initCatalogMapUi();
})();
