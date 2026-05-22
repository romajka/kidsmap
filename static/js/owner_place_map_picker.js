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

  function buildSharedState(root) {
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

    function updateStatus(lat, lng) {
      if (lat === null || lng === null) {
        statusEl.textContent = emptyLabel;
        return;
      }
      statusEl.textContent = selectedPrefix + " " + formatCoordinate(lat) + ", " + formatCoordinate(lng);
    }

    return {
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
    };
  }

  function bindUnsupportedSearch(shared) {
    function showUnsupported() {
      shared.statusEl.textContent = shared.searchUnsupportedLabel;
    }

    if (shared.searchBtn) {
      shared.searchBtn.addEventListener("click", showUnsupported);
    }

    if (shared.searchInput) {
      shared.searchInput.addEventListener("keydown", function (event) {
        if (event.key !== "Enter") return;
        event.preventDefault();
        showUnsupported();
      });
    }
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

      options.setPoint(location.lat(), location.lng());
      if (shared.addressInput && place.formatted_address) {
        shared.addressInput.value = place.formatted_address;
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

    root.dataset.mapInitialized = "1";

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
      const recenter = !options || options.recenter !== false;
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
    }

    map.on("click", function (event) {
      setPoint(event.latlng.lat, event.latlng.lng);
    });

    bindLocateButton(shared, setPoint);
    bindUnsupportedSearch(shared);

    if (shared.clearBtn) {
      shared.clearBtn.addEventListener("click", function () {
        clearPoint();
      });
    }

    const initialLat = parseCoordinate(shared.latInput.value);
    const initialLng = parseCoordinate(shared.lngInput.value);
    if (initialLat !== null && initialLng !== null) {
      map.setView([initialLat, initialLng], 15);
      setPoint(initialLat, initialLng, { recenter: false });
    } else {
      map.setView([shared.defaultLat, shared.defaultLng], 12);
      shared.updateStatus(null, null);
    }

    setTimeout(function () {
      map.invalidateSize();
    }, 0);

    window.addEventListener("resize", function () {
      map.invalidateSize();
    });

    shared.mapEl.addEventListener("mouseenter", function () {
      map.scrollWheelZoom.enable();
    });
    shared.mapEl.addEventListener("mouseleave", function () {
      map.scrollWheelZoom.disable();
    });
  }

  function initGoogleMapPicker(root) {
    if (!root || !window.google || !window.google.maps || root.dataset.mapInitialized === "1") return;
    const shared = buildSharedState(root);
    if (!shared) return;

    root.dataset.mapInitialized = "1";

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
      const recenter = !options || options.recenter !== false;
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
    }

    map.addListener("click", function (event) {
      if (!event.latLng) return;
      setPoint(event.latLng.lat(), event.latLng.lng());
    });

    bindLocateButton(shared, setPoint);
    bindGoogleSearch(shared, { setPoint: setPoint, map: map });

    if (shared.clearBtn) {
      shared.clearBtn.addEventListener("click", function () {
        clearPoint();
      });
    }

    if (hasInitialPoint) {
      setPoint(initialLat, initialLng, { recenter: false });
    } else {
      shared.updateStatus(null, null);
    }
  }

  function initMapPicker(root) {
    if (!root) return;
    const provider = (root.dataset.mapProvider || "").trim();

    if (provider === "google") {
      initGoogleMapPicker(root);
      return;
    }

    initLeafletMapPicker(root);
  }

  function initAllMapPickers() {
    document.querySelectorAll("[data-owner-map-picker]").forEach(initMapPicker);
  }

  window.kidsMapInitOwnerMapPickers = initAllMapPickers;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllMapPickers);
  } else {
    initAllMapPickers();
  }
})();
