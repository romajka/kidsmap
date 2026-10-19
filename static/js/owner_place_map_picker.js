(function () {
  function parseCoordinate(value) {
    const normalized = String(value || "").trim();
    if (!normalized) return null;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function formatCoordinate(value) {
    return Number(value).toFixed(6);
  }

  function validPoint(lat, lng) {
    return typeof lat === "number" && typeof lng === "number" &&
      Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
  }

  function buildSharedState(root) {
    if (root._kidsMapShared) return root._kidsMapShared;
    const latInput = root.querySelector('input[name="lat"]');
    const lngInput = root.querySelector('input[name="lng"]');
    const mapEl = root.querySelector("[data-map-canvas]");
    const statusEl = root.querySelector("[data-map-status]");
    const locateBtn = root.querySelector("[data-map-locate]");
    const clearBtn = root.querySelector("[data-map-clear]");
    const searchInput = root.querySelector("[data-map-search-input]");
    const searchBtn = root.querySelector("[data-map-search]");
    const form = root.closest("form");
    const addressInput = form ? form.querySelector('input[name="address"]') : null;

    if (!latInput || !lngInput || !mapEl || !statusEl) return null;

    const defaultLat = parseCoordinate(root.dataset.defaultLat) ?? 40.409264;
    const defaultLng = parseCoordinate(root.dataset.defaultLng) ?? 49.867092;
    const selectedPrefix = root.dataset.selectedPrefix || "";
    const emptyLabel = root.dataset.emptyLabel || "";
    const locateErrorLabel = root.dataset.locateError || "";
    const locateUnsupportedLabel = root.dataset.locateUnsupported || "";
    const searchErrorLabel = root.dataset.searchError || "";
    const searchEmptyLabel = root.dataset.searchEmpty || "";
    const searchUnsupportedLabel = root.dataset.searchUnsupported || "";

    const badgeEl = root.querySelector("[data-geocoding-status-badge]");

    function notifyChange() {
      if (form) form.dispatchEvent(new CustomEvent("km:map-change", { bubbles: true }));
    }

    function updateGeocodingStatus(statusType) {
      if (!badgeEl) return;
      const lang = document.documentElement.lang || "ru";
      badgeEl.className = "km-map-geocoding-status";
      if (statusType === "found") {
        badgeEl.classList.add("is-found");
        badgeEl.textContent = lang === "az" ? "Məkan tapıldı" : (lang === "en" ? "Place found" : "Место найдено");
      } else if (statusType === "refine") {
        badgeEl.classList.add("is-refine");
        badgeEl.textContent = lang === "az" ? "Nöqtəni dəqiqləşdirin" : (lang === "en" ? "Refine point" : "Уточните точку");
      } else {
        badgeEl.textContent = "";
      }
    }

    function updateStatus(lat, lng) {
      if (lat === null || lng === null) {
        statusEl.textContent = emptyLabel;
        return;
      }
      statusEl.textContent = selectedPrefix + " " + formatCoordinate(lat) + ", " + formatCoordinate(lng);
    }

    const shared = {
      latInput: latInput,
      lngInput: lngInput,
      mapEl: mapEl,
      statusEl: statusEl,
      locateBtn: locateBtn,
      clearBtn: clearBtn,
      searchInput: searchInput,
      searchBtn: searchBtn,
      addressInput: addressInput,
      defaultLat: defaultLat,
      defaultLng: defaultLng,
      locateErrorLabel: locateErrorLabel,
      locateUnsupportedLabel: locateUnsupportedLabel,
      searchErrorLabel: searchErrorLabel,
      searchEmptyLabel: searchEmptyLabel,
      searchUnsupportedLabel: searchUnsupportedLabel,
      updateStatus: updateStatus,
      updateGeocodingStatus: updateGeocodingStatus,
      notifyChange: notifyChange,
    };
    if (root.hasAttribute("data-permanent-map")) root._kidsMapShared = shared;
    return shared;
  }

  function bindPermanentControls(root, shared) {
    if (root.dataset.mapControlsBound === "1") return;
    root.dataset.mapControlsBound = "1";
    let generation = 0;
    function finish() {
      if (shared.locateBtn) shared.locateBtn.setAttribute("aria-busy", "false");
    }
    function invalidate() { generation += 1; finish(); }
    function point(lat, lng) {
      if (!validPoint(lat, lng)) return false;
      if (shared.renderer) shared.renderer.setPoint(lat, lng);
      else {
        shared.latInput.value = formatCoordinate(lat);
        shared.lngInput.value = formatCoordinate(lng);
        shared.updateStatus(lat, lng);
        shared.updateGeocodingStatus("refine");
        shared.notifyChange();
      }
      return true;
    }
    if (shared.clearBtn) shared.clearBtn.addEventListener("click", function () {
      invalidate();
      if (shared.renderer) shared.renderer.clearPoint();
      else {
        shared.latInput.value = shared.lngInput.value = "";
        shared.updateStatus(null, null);
        shared.updateGeocodingStatus(null);
        shared.notifyChange();
      }
    });
    [shared.latInput, shared.lngInput].forEach(function (input) {
      input.addEventListener("input", invalidate);
      input.addEventListener("change", function () {
        invalidate();
        const lat = parseCoordinate(shared.latInput.value), lng = parseCoordinate(shared.lngInput.value);
        if (validPoint(lat, lng)) point(lat, lng);
        else if (!shared.latInput.value.trim() && !shared.lngInput.value.trim()) shared.updateStatus(null, null);
      });
    });
    if (shared.locateBtn) shared.locateBtn.addEventListener("click", function () {
      invalidate();
      if (!navigator.geolocation || typeof navigator.geolocation.getCurrentPosition !== "function") {
        shared.statusEl.textContent = shared.locateUnsupportedLabel;
        return;
      }
      const request = generation;
      const captured = shared.latInput.value + "|" + shared.lngInput.value;
      const current = () => request === generation && captured === shared.latInput.value + "|" + shared.lngInput.value;
      shared.statusEl.textContent = root.dataset.locating || shared.locateUnsupportedLabel;
      shared.locateBtn.setAttribute("aria-busy", "true");
      function failed() {
        if (!current()) return;
        finish();
        shared.statusEl.textContent = shared.locateErrorLabel;
      }
      try {
        navigator.geolocation.getCurrentPosition(function (position) {
          if (!current()) return;
          finish();
          if (!position || !position.coords || !point(position.coords.latitude, position.coords.longitude)) failed();
        }, failed, {enableHighAccuracy:true, timeout:10000, maximumAge:0});
      } catch (_) { failed(); }
    });
  }

  function bindOsmSearch(shared, options) {
    if (!shared.searchInput || !options || typeof options.setPoint !== "function") return;

    function search() {
      const rawQuery = (shared.searchInput.value || shared.addressInput?.value || "").trim();
      if (!rawQuery) {
        shared.statusEl.textContent = shared.searchEmptyLabel;
        return;
      }

      shared.statusEl.textContent = document.documentElement.lang === "az" ? "Axtarılır..." : (document.documentElement.lang === "en" ? "Searching..." : "Поиск...");

      const url = "https://nominatim.openstreetmap.org/search?format=json&countrycodes=az&q=" + encodeURIComponent(rawQuery);
      fetch(url)
        .then(function (response) { return response.json(); })
        .then(function (results) {
          if (!results || !results.length) {
            shared.statusEl.textContent = shared.searchErrorLabel;
            return;
          }
          const res = results[0];
          const lat = parseFloat(res.lat);
          const lng = parseFloat(res.lon);
          options.setPoint(lat, lng, { isGeocoded: true });
        })
        .catch(function () {
          shared.statusEl.textContent = shared.searchErrorLabel;
        });
    }

    if (shared.searchBtn) {
      shared.searchBtn.addEventListener("click", search);
    }

    shared.searchInput.addEventListener("keydown", function (event) {
      if (event.key !== "Enter") return;
      event.preventDefault();
      search();
    });
  }

  function bindGoogleSearch(shared, options) {
    if (!shared.searchInput || !options || typeof options.setPoint !== "function") return;

    const geocoder = new google.maps.Geocoder();
    const map = options.map;

    function applyResolvedPlace(place, rawQuery) {
      const geometry = place && place.geometry;
      const location = geometry && geometry.location;
      if (!location) {
        shared.statusEl.textContent = shared.searchErrorLabel;
        return;
      }

      options.setPoint(location.lat(), location.lng(), { isGeocoded: true });
      if (shared.addressInput && place.formatted_address) {
        shared.addressInput.value = place.formatted_address;
        shared.addressInput.dispatchEvent(new Event("input", { bubbles: true }));
      }
      shared.searchInput.value = place.formatted_address || place.name || rawQuery;

      if (!map) return;

      if (geometry.viewport) {
        map.fitBounds(geometry.viewport);
        return;
      }

      map.setCenter({ lat: location.lat(), lng: location.lng() });
      if (map.getZoom() < 15) {
        map.setZoom(15);
      }
    }

    function search() {
      const rawQuery = (shared.searchInput.value || shared.addressInput?.value || "").trim();
      if (!rawQuery) {
        shared.statusEl.textContent = shared.searchEmptyLabel;
        return;
      }

      geocoder.geocode(
        {
          address: rawQuery,
          region: "az",
        },
        function (results, status) {
          if (status !== "OK" || !results || !results.length) {
            shared.statusEl.textContent = shared.searchErrorLabel;
            return;
          }

          applyResolvedPlace(results[0], rawQuery);
        }
      );
    }

    let selectionVersion = 0;
    const canUsePlacesAutocomplete =
      google.maps.places &&
      typeof google.maps.places.Autocomplete === "function";

    if (canUsePlacesAutocomplete) {
      const autocomplete = new google.maps.places.Autocomplete(shared.searchInput, {
        componentRestrictions: { country: "az" },
        fields: ["formatted_address", "geometry", "name"],
      });

      if (map) {
        autocomplete.bindTo("bounds", map);
      }

      autocomplete.addListener("place_changed", function () {
        selectionVersion += 1;
        const place = autocomplete.getPlace();
        if (!place || !place.geometry || !place.geometry.location) {
          search();
          return;
        }
        applyResolvedPlace(place, (shared.searchInput.value || "").trim());
      });
    }

    if (shared.searchBtn) {
      shared.searchBtn.addEventListener("click", search);
    }

    shared.searchInput.addEventListener("keydown", function (event) {
      if (event.key !== "Enter") return;
      event.preventDefault();
      const versionBeforeEnter = selectionVersion;
      window.setTimeout(function () {
        if (selectionVersion !== versionBeforeEnter) return;
        search();
      }, 0);
    });
  }

  function bindLocateButton(shared, setPoint) {
    if (!shared.locateBtn) return;

    shared.locateBtn.addEventListener("click", function () {
      if (!navigator.geolocation) {
        shared.statusEl.textContent = shared.locateUnsupportedLabel;
        return;
      }

      navigator.geolocation.getCurrentPosition(
        function (position) {
          setPoint(position.coords.latitude, position.coords.longitude);
        },
        function () {
          shared.statusEl.textContent = shared.locateErrorLabel;
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    });
  }

  function initLeafletMapPicker(root) {
    if (!root || !window.L || root.dataset.mapInitialized === "1") return;
    const shared = buildSharedState(root);
    if (!shared) return;

    let marker = null;
    const map = L.map(shared.mapEl, {
      scrollWheelZoom: false,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    function setPoint(lat, lng, options) {
      if (!validPoint(lat, lng)) return;
      const recenter = !options || options.recenter !== false;
      const isGeocoded = options && options.isGeocoded;
      shared.latInput.value = formatCoordinate(lat);
      shared.lngInput.value = formatCoordinate(lng);

      if (!marker) {
        marker = L.marker([lat, lng], { draggable: true }).addTo(map);
        marker.on("dragend", function (event) {
          const point = event.target.getLatLng();
          setPoint(point.lat, point.lng, { recenter: false });
        });
      } else {
        marker.setLatLng([lat, lng]);
      }

      shared.updateStatus(lat, lng);
      shared.updateGeocodingStatus(isGeocoded ? "found" : "refine");
      if (!options || !options.silent) shared.notifyChange();
      if (recenter) {
        map.setView([lat, lng], Math.max(map.getZoom(), 15));
      }
    }

    function clearPoint() {
      shared.latInput.value = "";
      shared.lngInput.value = "";
      if (marker) {
        map.removeLayer(marker);
        marker = null;
      }
      shared.updateStatus(null, null);
      shared.updateGeocodingStatus(null);
      shared.notifyChange();
    }

    map.on("click", function (event) {
      setPoint(event.latlng.lat, event.latlng.lng);
    });

    if (!root.hasAttribute("data-permanent-map")) bindLocateButton(shared, setPoint);
    bindOsmSearch(shared, { setPoint: setPoint, map: map });
    if (root.hasAttribute("data-permanent-map")) shared.renderer = {setPoint:setPoint, clearPoint:clearPoint};

    if (shared.clearBtn && !root.hasAttribute("data-permanent-map")) {
      shared.clearBtn.addEventListener("click", function () {
        clearPoint();
      });
    }

    const initialLat = parseCoordinate(shared.latInput.value);
    const initialLng = parseCoordinate(shared.lngInput.value);
    if (initialLat !== null && initialLng !== null) {
      map.setView([initialLat, initialLng], 15);
      setPoint(initialLat, initialLng, { recenter: false, silent: true });
    } else {
      map.setView([shared.defaultLat, shared.defaultLng], 12);
      shared.updateStatus(null, null);
    }

    setTimeout(function () {
      map.invalidateSize();
    }, 0);
    root._kidsMapRefreshMap = function () {
      map.invalidateSize();
    };

    window.addEventListener("resize", function () {
      map.invalidateSize();
    });

    shared.mapEl.addEventListener("mouseenter", function () {
      map.scrollWheelZoom.enable();
    });
    shared.mapEl.addEventListener("mouseleave", function () {
      map.scrollWheelZoom.disable();
    });
    root.dataset.mapInitialized = "1";
  }

  function initGoogleMapPicker(root) {
    if (!root || !window.google || !window.google.maps || root.dataset.mapInitialized === "1") return;
    const shared = buildSharedState(root);
    if (!shared) return;

    let marker = null;
    const initialLat = parseCoordinate(shared.latInput.value);
    const initialLng = parseCoordinate(shared.lngInput.value);
    const hasInitialPoint = initialLat !== null && initialLng !== null;
    const map = new google.maps.Map(shared.mapEl, {
      center: hasInitialPoint
        ? { lat: initialLat, lng: initialLng }
        : { lat: shared.defaultLat, lng: shared.defaultLng },
      zoom: hasInitialPoint ? 15 : 12,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      gestureHandling: "cooperative",
    });

    function setPoint(lat, lng, options) {
      if (!validPoint(lat, lng)) return;
      const recenter = !options || options.recenter !== false;
      const isGeocoded = options && options.isGeocoded;
      shared.latInput.value = formatCoordinate(lat);
      shared.lngInput.value = formatCoordinate(lng);

      if (!marker) {
        marker = new google.maps.Marker({
          position: { lat: lat, lng: lng },
          map: map,
          draggable: true,
        });
        marker.addListener("dragend", function (event) {
          if (!event.latLng) return;
          setPoint(event.latLng.lat(), event.latLng.lng(), { recenter: false });
        });
      } else {
        marker.setPosition({ lat: lat, lng: lng });
      }

      shared.updateStatus(lat, lng);
      shared.updateGeocodingStatus(isGeocoded ? "found" : "refine");
      if (!options || !options.silent) shared.notifyChange();
      if (recenter) {
        map.setCenter({ lat: lat, lng: lng });
        if (map.getZoom() < 15) {
          map.setZoom(15);
        }
      }
    }

    function clearPoint() {
      shared.latInput.value = "";
      shared.lngInput.value = "";
      if (marker) {
        marker.setMap(null);
        marker = null;
      }
      shared.updateStatus(null, null);
      shared.updateGeocodingStatus(null);
      shared.notifyChange();
    }

    map.addListener("click", function (event) {
      if (!event.latLng) return;
      setPoint(event.latLng.lat(), event.latLng.lng());
    });

    if (!root.hasAttribute("data-permanent-map")) bindLocateButton(shared, setPoint);
    bindGoogleSearch(shared, { setPoint: setPoint, map: map });
    if (root.hasAttribute("data-permanent-map")) shared.renderer = {setPoint:setPoint, clearPoint:clearPoint};

    if (shared.clearBtn && !root.hasAttribute("data-permanent-map")) {
      shared.clearBtn.addEventListener("click", function () {
        clearPoint();
      });
    }

    if (hasInitialPoint) {
      setPoint(initialLat, initialLng, { recenter: false, silent: true });
    } else {
      shared.updateStatus(null, null);
    }
    root._kidsMapRefreshMap = function () {
      google.maps.event.trigger(map, "resize");
      const lat = parseCoordinate(shared.latInput.value);
      const lng = parseCoordinate(shared.lngInput.value);
      map.setCenter(lat !== null && lng !== null
        ? { lat: lat, lng: lng }
        : { lat: shared.defaultLat, lng: shared.defaultLng });
    };
    root.dataset.mapInitialized = "1";
  }

  function initMapPicker(root) {
    if (!root) return;
    if (root.hasAttribute("data-permanent-map")) {
      const shared = buildSharedState(root);
      if (!shared) return;
      bindPermanentControls(root, shared);
      if (root.dataset.mapInitialized === "1") return;
      function attach() {
        if (root.dataset.mapInitialized === "1") return;
        shared.mapEl.textContent = "";
        try {
          if (root.dataset.mapProvider === "google" && window.google?.maps) initGoogleMapPicker(root);
          else if (window.L) initLeafletMapPicker(root);
        } catch (_) {
          shared.renderer = null;
          delete root.dataset.mapInitialized;
        }
        const ready = root.dataset.mapInitialized === "1";
        if (shared.searchBtn) shared.searchBtn.disabled = !ready;
        if (shared.searchInput) shared.searchInput.disabled = !ready;
        if (!ready) {
          const placeholder = document.createElement("div");
          placeholder.className = "home-map-empty";
          placeholder.textContent = shared.searchUnsupportedLabel || "Map is temporarily unavailable.";
          shared.mapEl.replaceChildren(placeholder);
        }
      }
      attach();
      if (root.dataset.mapRetryBound !== "1") {
        root.dataset.mapRetryBound = "1";
        document.querySelectorAll('[data-owner-map-sdk="leaflet"]').forEach(function (script) {
          script.addEventListener("load", attach);
          script.addEventListener("error", attach);
        });
        if (root.dataset.mapProvider === "google") setTimeout(attach, 5000);
      }
      return;
    }
    const provider = (root.dataset.mapProvider || "").trim();

    if (provider === "google") {
      initGoogleMapPicker(root);
      if (root.hasAttribute("data-permanent-map") && root.dataset.mapInitialized !== "1") {
        setTimeout(function () {
          if (root.dataset.mapInitialized !== "1") initLeafletMapPicker(root);
        }, 5000);
      }
      return;
    }

    if (provider === "leaflet" && window.L) {
      initLeafletMapPicker(root);
      return;
    }

    const shared = buildSharedState(root);
    if (!shared || root.dataset.mapInitialized === "1") return;
    root.dataset.mapInitialized = "1";
    shared.mapEl.innerHTML = '<div class="home-map-empty"><p>' +
      String(shared.searchUnsupportedLabel || "Map is temporarily unavailable.") +
      "</p></div>";
    if (shared.searchBtn) shared.searchBtn.disabled = true;
  }

  function initAllMapPickers() {
    document.querySelectorAll("[data-owner-map-picker]").forEach(initMapPicker);
  }

  window.kidsMapInitOwnerMapPickers = initAllMapPickers;
  window.kidsMapRefreshOwnerMapPickers = function () {
    initAllMapPickers();
    document.querySelectorAll("[data-owner-map-picker]").forEach(function (root) {
      if (typeof root._kidsMapRefreshMap === "function") {
        root._kidsMapRefreshMap();
      }
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllMapPickers);
  } else {
    initAllMapPickers();
  }
})();
