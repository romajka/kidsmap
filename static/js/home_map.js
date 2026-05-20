(function () {
  const DEFAULT_CENTER = { lat: 40.4093, lng: 49.8671 };
  const DEFAULT_ZOOM = 11;
  const LEAFLET_DEFAULTS = {
    cssHref: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
    cssIntegrity: "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=",
    jsHref: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
    jsIntegrity: "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=",
  };

  const SCRIPT_CONFIG = (function () {
    const scriptEl = document.currentScript;
    if (!scriptEl) return {};

    return {
      googleMapsApiKey: (scriptEl.dataset.homeMapGoogleKey || "").trim(),
      leafletCssHref: (scriptEl.dataset.homeMapLeafletCss || LEAFLET_DEFAULTS.cssHref).trim(),
      leafletCssIntegrity: (scriptEl.dataset.homeMapLeafletCssIntegrity || LEAFLET_DEFAULTS.cssIntegrity).trim(),
      leafletJsHref: (scriptEl.dataset.homeMapLeafletJs || LEAFLET_DEFAULTS.jsHref).trim(),
      leafletJsIntegrity: (scriptEl.dataset.homeMapLeafletJsIntegrity || LEAFLET_DEFAULTS.jsIntegrity).trim(),
    };
  })();

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

  function normalizeValue(value) {
    return String(value || "").trim();
  }

  function normalizeSearch(value) {
    return normalizeValue(value).toLocaleLowerCase();
  }

  function getDistrictOptions(form) {
    const districtOptionsEl = form.querySelector("#home-district-options");
    if (!districtOptionsEl) return [];

    return Array.from(districtOptionsEl.querySelectorAll("option"))
      .map(function (option) {
        return normalizeValue(option.value);
      })
      .filter(Boolean);
  }

  function resolveDistrictValue(value, options) {
    const current = normalizeValue(value);
    if (!current) return "";

    const normalizedCurrent = normalizeSearch(current);
    const exactMatch = options.find(function (option) {
      return normalizeSearch(option) === normalizedCurrent;
    });
    if (exactMatch) return exactMatch;

    const prefixMatches = options.filter(function (option) {
      return normalizeSearch(option).startsWith(normalizedCurrent);
    });
    if (prefixMatches.length === 1) {
      return prefixMatches[0];
    }

    return "";
  }

  function getAgeInput(form) {
    return form.querySelector('[name="age"]');
  }

  function getAgeButtons(form) {
    return Array.from(form.querySelectorAll("[data-home-age-chip]"));
  }

  function syncAgeButtons(form) {
    const ageInput = getAgeInput(form);
    if (!ageInput) return;

    const currentValue = normalizeValue(ageInput.value);
    getAgeButtons(form).forEach(function (button) {
      const isActive = normalizeValue(button.dataset.ageValue) === currentValue;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function setAgeValue(form, nextValue) {
    const ageInput = getAgeInput(form);
    if (!ageInput) return;

    ageInput.value = nextValue;
    syncAgeButtons(form);
  }

  function parsePlaces() {
    const dataEl = document.getElementById("home-map-data");
    if (!dataEl) return [];

    try {
      return JSON.parse(dataEl.textContent || "[]");
    } catch (_error) {
      return [];
    }
  }

  function getFilterState() {
    const form = document.querySelector("[data-home-map-filter-form]");
    if (!form) {
      return {
        query: "",
        category: "",
        district: "",
        metro: "",
        age: "",
      };
    }

    return {
      query: normalizeSearch(form.querySelector('[name="q"]')?.value),
      category: normalizeValue(form.querySelector('[name="category"]')?.value),
      district: normalizeValue(form.querySelector('[name="district"]')?.value),
      metro: normalizeValue(form.querySelector('[name="metro"]')?.value),
      age: normalizeValue(form.querySelector('[name="age"]')?.value),
    };
  }

  function placeMatchesFilters(place, filters) {
    if (filters.category && place.category_code !== filters.category) {
      return false;
    }

    if (filters.district && normalizeValue(place.district) !== filters.district) {
      return false;
    }

    if (filters.metro && normalizeValue(place.metro) !== filters.metro) {
      return false;
    }

    if (filters.age) {
      const selectedAge = Number(filters.age);
      const ageFrom = place.age_from === null || place.age_from === undefined ? null : Number(place.age_from);
      const ageTo = place.age_to === null || place.age_to === undefined ? null : Number(place.age_to);

      if ((ageFrom !== null && selectedAge < ageFrom) || (ageTo !== null && selectedAge > ageTo)) {
        return false;
      }

      if (ageFrom === null && ageTo === null) {
        return false;
      }
    }

    if (filters.query && !normalizeSearch(place.search_text || place.name).includes(filters.query)) {
      return false;
    }

    return true;
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
        '" loading="lazy" decoding="async" />' +
        "</a>"
      : "";

    return (
      '<div class="home-map-popup">' +
      image +
      '<div class="home-map-popup-body">' +
      '<strong class="home-map-popup-title">' +
      escapeHtml(place.name) +
      "</strong>" +
      '<span class="home-map-popup-category">' +
      escapeHtml(place.category) +
      "</span>" +
      '<a class="home-map-popup-link" href="' +
      escapeHtml(place.url || "") +
      '">' +
      escapeHtml(detailsLabel) +
      "</a>" +
      "</div>" +
      "</div>"
    );
  }

  function renderFallback(mapEl, mapNoteEl) {
    if (!mapEl) return;

    if (mapNoteEl) {
      mapNoteEl.hidden = true;
      mapNoteEl.textContent = "";
    }

    const title = mapEl.dataset.fallbackTitle || "Map";
    mapEl.innerHTML =
      '<iframe class="home-map home-map-fallback" src="https://maps.google.com/maps?q=Baku%2C%20Azerbaijan&z=11&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="' +
      escapeHtml(title) +
      '"></iframe>';
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

  function buildSharedState(mapEl, mapNoteEl) {
    const places = parsePlaces();
    const validPlaces = places.filter(function (place) {
      return typeof place.lat === "number" && typeof place.lng === "number";
    });

    if (!validPlaces.length) {
      renderFallback(mapEl, mapNoteEl);
      return null;
    }

    return {
      places: validPlaces,
      detailsLabel: mapEl.dataset.detailsLabel || "Details",
      mapEl: mapEl,
      mapNoteEl: mapNoteEl,
    };
  }

  function setMapNote(mapNoteEl, emptyLabel, hasVisiblePlaces) {
    if (!mapNoteEl) return;
    mapNoteEl.hidden = hasVisiblePlaces;
    mapNoteEl.textContent = hasVisiblePlaces ? "" : emptyLabel || "";
  }

  function bindFilterListeners(updateMap) {
    const form = document.querySelector("[data-home-map-filter-form]");
    if (!form || typeof updateMap !== "function") return;

    let searchTimer = null;
    const queryInput = form.querySelector('[name="q"]');
    const districtInput = form.querySelector('[name="district"]');
    const districtOptions = getDistrictOptions(form);
    const categorySelect = form.querySelector('select[name="category"]');
    const ageInput = getAgeInput(form);
    const ageButtons = getAgeButtons(form);

    function scheduleUpdate() {
      if (searchTimer) {
        window.clearTimeout(searchTimer);
      }
      searchTimer = window.setTimeout(updateMap, 120);
    }

    if (queryInput) {
      queryInput.addEventListener("input", scheduleUpdate);
    }

    if (districtInput) {
      districtInput.addEventListener("input", function () {
        const resolvedValue = resolveDistrictValue(districtInput.value, districtOptions);
        if (!normalizeValue(districtInput.value) || resolvedValue) {
          scheduleUpdate();
        }
      });

      districtInput.addEventListener("change", function () {
        districtInput.value = resolveDistrictValue(districtInput.value, districtOptions);
        scheduleUpdate();
      });

      form.addEventListener("submit", function () {
        districtInput.value = resolveDistrictValue(districtInput.value, districtOptions);
      });
    }

    if (categorySelect) {
      categorySelect.addEventListener("change", updateMap);
    }

    if (ageInput && ageButtons.length) {
      syncAgeButtons(form);

      ageButtons.forEach(function (button) {
        button.addEventListener("click", function () {
          const nextValue = normalizeValue(button.dataset.ageValue);
          const currentValue = normalizeValue(ageInput.value);
          setAgeValue(form, currentValue === nextValue ? "" : nextValue);
          updateMap();
        });
      });
    }
  }

  function mountGoogleMap(sharedState) {
    if (!window.google || !window.google.maps || !sharedState) return false;

    const { mapEl, mapNoteEl, places, detailsLabel } = sharedState;
    if (mapEl.dataset.mapInitialized === "1") return true;

    mapEl.dataset.mapInitialized = "1";

    const map = new google.maps.Map(mapEl, {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      gestureHandling: "cooperative",
    });
    const infoWindow = new google.maps.InfoWindow();
    const markerItems = [];

    places.forEach(function (place) {
      const position = { lat: place.lat, lng: place.lng };
      const marker = new google.maps.Marker({
        position: position,
        map: null,
        title: place.name || "",
      });

      marker.addListener("click", function () {
        infoWindow.setContent(renderPopupContent(place, detailsLabel));
        infoWindow.open({
          anchor: marker,
          map: map,
        });
      });

      markerItems.push({
        marker: marker,
        place: place,
        position: position,
      });
    });

    function syncVisibleMarkers() {
      const filters = getFilterState();
      const visibleItems = [];
      const bounds = new google.maps.LatLngBounds();

      infoWindow.close();

      markerItems.forEach(function (item) {
        const shouldShow = placeMatchesFilters(item.place, filters);
        item.marker.setMap(shouldShow ? map : null);
        if (shouldShow) {
          visibleItems.push(item);
          bounds.extend(item.position);
        }
      });

      if (!visibleItems.length) {
        map.setCenter(DEFAULT_CENTER);
        map.setZoom(DEFAULT_ZOOM);
        setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", false);
        return;
      }

      if (visibleItems.length === 1) {
        map.setCenter(visibleItems[0].position);
        map.setZoom(13);
        setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", true);
        return;
      }

      map.fitBounds(bounds, { top: 32, right: 32, bottom: 32, left: 32 });
      setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", true);
    }

    bindFilterListeners(syncVisibleMarkers);
    syncVisibleMarkers();

    window.setTimeout(function () {
      if (window.google && window.google.maps) {
        google.maps.event.trigger(map, "resize");
      }
    }, 0);

    return true;
  }

  function mountLeafletMap(sharedState) {
    if (!window.L || !sharedState) return false;

    const { mapEl, mapNoteEl, places } = sharedState;
    if (mapEl.dataset.mapInitialized === "1") return true;

    mapEl.dataset.mapInitialized = "1";

    const map = L.map(mapEl, {
      scrollWheelZoom: false,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    const markerItems = [];

    places.forEach(function (place) {
      const position = [place.lat, place.lng];
      const marker = L.circleMarker(position, {
        radius: 8,
        color: "#ffffff",
        weight: 2,
        fillColor: "#1f8640",
        fillOpacity: 0.9,
      });

      marker.bindPopup(renderPopupContent(place, mapEl.dataset.detailsLabel || "Details"));
      markerItems.push({
        marker: marker,
        place: place,
        position: position,
      });
    });

    function syncVisibleMarkers() {
      const filters = getFilterState();
      const visibleItems = [];
      const bounds = L.latLngBounds([]);

      map.closePopup();

      markerItems.forEach(function (item) {
        const shouldShow = placeMatchesFilters(item.place, filters);
        if (shouldShow) {
          if (!map.hasLayer(item.marker)) {
            item.marker.addTo(map);
          }
          visibleItems.push(item);
          bounds.extend(item.position);
        } else if (map.hasLayer(item.marker)) {
          map.removeLayer(item.marker);
        }
      });

      if (!visibleItems.length) {
        map.setView([DEFAULT_CENTER.lat, DEFAULT_CENTER.lng], DEFAULT_ZOOM);
        setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", false);
        return;
      }

      if (visibleItems.length === 1) {
        map.setView(visibleItems[0].position, 13);
        setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", true);
        return;
      }

      map.fitBounds(bounds, { padding: [24, 24] });
      setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", true);
    }

    bindFilterListeners(syncVisibleMarkers);
    syncVisibleMarkers();

    window.setTimeout(function () {
      map.invalidateSize();
    }, 0);

    mapEl.addEventListener("mouseenter", function () {
      map.scrollWheelZoom.enable();
    });
    mapEl.addEventListener("mouseleave", function () {
      map.scrollWheelZoom.disable();
    });

    return true;
  }

  function startMapBootstrap() {
    const mapSection = document.getElementById("home-map-section");
    const mapEl = document.getElementById("home-map");
    const mapNoteEl = document.getElementById("home-map-note");
    if (!mapSection || !mapEl || mapEl.dataset.mapBootstrapStarted === "1") return;

    mapEl.dataset.mapBootstrapStarted = "1";

    const sharedState = buildSharedState(mapEl, mapNoteEl);
    if (!sharedState) return;

    function tryMount() {
      if (mountGoogleMap(sharedState)) return true;
      if (mountLeafletMap(sharedState)) return true;
      return false;
    }

    function loadGoogleProvider() {
      if (!SCRIPT_CONFIG.googleMapsApiKey) return Promise.reject(new Error("Missing Google Maps API key"));
      window.kidsMapHomeMapGoogleLoaded = function () {
        tryMount();
      };

      const src =
        "https://maps.googleapis.com/maps/api/js?key=" +
        encodeURIComponent(SCRIPT_CONFIG.googleMapsApiKey) +
        "&callback=kidsMapHomeMapGoogleLoaded";

      return loadScript(src).then(function () {
        tryMount();
      });
    }

    function loadLeafletProvider() {
      return loadStylesheet(SCRIPT_CONFIG.leafletCssHref, SCRIPT_CONFIG.leafletCssIntegrity).then(function () {
        return loadScript(SCRIPT_CONFIG.leafletJsHref, SCRIPT_CONFIG.leafletJsIntegrity);
      }).then(function () {
        tryMount();
      });
    }

    let loadStarted = false;
    let fallbackTimer = null;

    function clearFallbackTimer() {
      if (!fallbackTimer) return;
      window.clearTimeout(fallbackTimer);
      fallbackTimer = null;
    }

    function loadAndMount() {
      if (mapEl.dataset.mapInitialized === "1" || loadStarted) return;
      loadStarted = true;

      fallbackTimer = window.setTimeout(function () {
        if (mapEl.dataset.mapInitialized !== "1") {
          renderFallback(mapEl, mapNoteEl);
        }
      }, 5000);

      if (SCRIPT_CONFIG.googleMapsApiKey) {
        loadGoogleProvider().catch(function () {
          clearFallbackTimer();
          renderFallback(mapEl, mapNoteEl);
        });
        return;
      }

      loadLeafletProvider().catch(function () {
        clearFallbackTimer();
        renderFallback(mapEl, mapNoteEl);
      });
    }

    function triggerLoad() {
      loadAndMount();
      mapSection.removeEventListener("mouseenter", triggerLoad);
      mapSection.removeEventListener("touchstart", triggerLoad);
      window.removeEventListener("scroll", triggerLoad, true);
    }

    if (!("IntersectionObserver" in window)) {
      loadAndMount();
      return;
    }

    const observer = new IntersectionObserver(
      function (entries) {
        if (entries.some(function (entry) {
          return entry.isIntersecting;
        })) {
          observer.disconnect();
          triggerLoad();
        }
      },
      {
        rootMargin: "280px 0px",
        threshold: 0.01,
      }
    );

    observer.observe(mapSection);
    mapSection.addEventListener("mouseenter", triggerLoad, { passive: true });
    mapSection.addEventListener("touchstart", triggerLoad, { passive: true, once: true });
    window.addEventListener("scroll", triggerLoad, { passive: true, capture: true, once: true });
    window.setTimeout(triggerLoad, 900);
  }

  startMapBootstrap();
})();
