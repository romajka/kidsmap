(function () {
  function parseCoordinate(value) {
    var normalized = String(value || "").trim().replace(",", ".");
    if (!normalized) return null;
    var parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : null;
  }

  function formatCoordinate(value) {
    return Number(value).toFixed(6);
  }

  function initRegionCascade(root) {
    var regionSelect = root.querySelector("[data-km-location-region]") || document.getElementById("id_region");
    var districtSelect = root.querySelector("[data-km-location-district]") || document.getElementById("id_district");
    var metroSelect = document.getElementById("id_metro");
    var districtBox = root.querySelector("[data-km-admin-district-box]");
    var metroBox = root.querySelector("[data-km-admin-metro-box]");

    if (!regionSelect || !districtSelect) return;

    function sync() {
      var isBaku = regionSelect.value === "baku";
      if (districtBox) {
        districtBox.style.display = isBaku ? "" : "none";
      }
      districtSelect.disabled = !isBaku;
      if (!isBaku) {
        districtSelect.value = "";
      }

      if (metroBox && metroSelect) {
        metroBox.style.display = isBaku ? "" : "none";
        metroSelect.disabled = !isBaku;
        if (!isBaku) {
          metroSelect.value = "";
        }
      }
    }

    if (!regionSelect.dataset.kmLocationCascadeBound) {
      regionSelect.addEventListener("change", sync);
      regionSelect.dataset.kmLocationCascadeBound = "1";
      if (window.$ && window.$.fn && typeof window.$.fn.select2 !== "undefined") {
        try {
          window.$(regionSelect).on("select2:select select2:unselect select2:clear", sync);
        } catch (error) {}
      }
    }

    sync();
  }

  function buildState(root) {
    var latInput = document.getElementById("id_lat");
    var lngInput = document.getElementById("id_lng");
    var addressInput = document.getElementById("id_address");
    var mapPanel = root.querySelector("[data-km-place-location-panel]");
    var mapCanvas = root.querySelector("[data-km-place-location-map]");
    var toggleButton = root.querySelector("[data-km-place-location-toggle]");
    var searchButton = root.querySelector("[data-km-place-location-search]");
    var locateButton = root.querySelector("[data-km-place-location-locate]");
    var confirmButton = root.querySelector("[data-km-place-location-confirm]");
    var clearButton = root.querySelector("[data-km-place-location-clear]");
    var fallbackSubmit = root.querySelector("[data-km-place-location-refresh-submit]");
    var statusText = root.querySelector("[data-km-place-location-status]");
    var coordBadge = root.querySelector("[data-location-coordinates-badge]");
    var mapBadge = root.querySelector("[data-location-map-badge]");
    var foundBox = root.querySelector("[data-km-place-location-found]");
    var foundText = root.querySelector("[data-km-place-location-found-text]");
    var applyAddressButton = root.querySelector("[data-km-place-location-apply-address]");

    if (!latInput || !lngInput || !addressInput || !mapPanel || !mapCanvas) {
      return null;
    }

    return {
      root: root,
      latInput: latInput,
      lngInput: lngInput,
      addressInput: addressInput,
      mapPanel: mapPanel,
      mapCanvas: mapCanvas,
      toggleButton: toggleButton,
      searchButton: searchButton,
      locateButton: locateButton,
      confirmButton: confirmButton,
      clearButton: clearButton,
      fallbackSubmit: fallbackSubmit,
      statusText: statusText,
      coordBadge: coordBadge,
      mapBadge: mapBadge,
      foundBox: foundBox,
      foundText: foundText,
      applyAddressButton: applyAddressButton,
      mapProvider: root.dataset.mapProvider || "leaflet",
      defaultLat: parseCoordinate(root.dataset.defaultLat) || 40.409264,
      defaultLng: parseCoordinate(root.dataset.defaultLng) || 49.867092,
      selectedPrefix: root.dataset.selectedPrefix || "Выбрана точка:",
      emptyLabel: root.dataset.emptyLabel || "Точка на карте не выбрана.",
      locateErrorLabel: root.dataset.locateError || "",
      locateUnsupportedLabel: root.dataset.locateUnsupported || "",
      searchErrorLabel: root.dataset.searchError || "",
      searchEmptyLabel: root.dataset.searchEmpty || "",
      searchFallbackLabel: root.dataset.searchFallback || "",
      coordFilledLabel: root.dataset.coordinatesFilledLabel || "Координаты указаны",
      coordMissingLabel: root.dataset.coordinatesMissingLabel || "Координаты не указаны",
      mapReadyLabel: root.dataset.mapReadyLabel || "Готово для карты",
      mapNotReadyLabel: root.dataset.mapNotReadyLabel || "Не готово для карты",
      mapOpenLabel: root.dataset.mapOpenLabel || "Скрыть карту",
      mapClosedLabel: root.dataset.mapClosedLabel || "Указать на карте",
      mapInstance: null,
      marker: null,
      geocoder: null,
      googleAutocomplete: null,
      pendingAddress: "",
    };
  }

  function updateFoundAddress(state, address) {
    var normalized = String(address || "").trim();
    state.pendingAddress = normalized;
    if (!state.foundBox || !state.foundText) return;

    if (!normalized) {
      state.foundBox.hidden = true;
      state.foundText.textContent = "";
      return;
    }

    state.foundBox.hidden = false;
    state.foundText.textContent = normalized;
  }

  function updateBadges(state) {
    var lat = parseCoordinate(state.latInput.value);
    var lng = parseCoordinate(state.lngInput.value);
    var hasCoordinates = lat !== null && lng !== null;
    var addressValue = String(state.addressInput.value || "").trim();
    var isReady = hasCoordinates && !!addressValue;

    var compactBadge = document.getElementById("km-location-status-compact-badge");
    var compactIcon = document.getElementById("km-location-status-compact-icon");
    var compactText = document.getElementById("km-location-status-compact-text");
    var compactCoords = document.getElementById("km-location-status-compact-coords");
    var compactCoordsVal = document.getElementById("km-location-status-compact-coords-val");

    if (compactBadge && compactText && compactIcon) {
      if (!addressValue) {
        compactBadge.className = "km-location-status-compact__badge km-location-status-compact__badge--danger";
        compactIcon.className = "fas fa-exclamation-triangle";
        compactText.textContent = "Нужен адрес";
      } else if (!hasCoordinates) {
        compactBadge.className = "km-location-status-compact__badge km-location-status-compact__badge--warn";
        compactIcon.className = "fas fa-map-pin";
        compactText.textContent = "Нет координат";
      } else {
        compactBadge.className = "km-location-status-compact__badge km-location-status-compact__badge--good";
        compactIcon.className = "fas fa-check-circle";
        compactText.textContent = "На карте";
      }
    }

    if (compactCoords && compactCoordsVal) {
      if (hasCoordinates) {
        compactCoords.style.display = "inline-flex";
        compactCoordsVal.textContent = formatCoordinate(lat) + ", " + formatCoordinate(lng);
      } else {
        compactCoords.style.display = "none";
        compactCoordsVal.textContent = "";
      }
    }

    if (state.coordBadge) {
      state.coordBadge.className = "km-location-badge km-location-badge--" + (hasCoordinates ? "good" : "warn");
      state.coordBadge.textContent = hasCoordinates ? state.coordFilledLabel : state.coordMissingLabel;
    }

    if (state.mapBadge) {
      state.mapBadge.className = "km-location-badge km-location-badge--" + (isReady ? "good" : "muted");
      state.mapBadge.textContent = isReady ? state.mapReadyLabel : state.mapNotReadyLabel;
    }

    if (state.statusText) {
      state.statusText.textContent = hasCoordinates
        ? state.selectedPrefix + " " + formatCoordinate(lat) + ", " + formatCoordinate(lng)
        : state.emptyLabel;
    }
  }

  function setToggleState(state, expanded) {
    state.mapPanel.hidden = !expanded;
    var coordGrid = state.root.querySelector(".km-place-location__coord-grid");
    if (coordGrid) {
      coordGrid.style.display = expanded ? "grid" : "none";
    }
    if (state.toggleButton) {
      state.toggleButton.setAttribute("aria-expanded", expanded ? "true" : "false");
      var label = state.toggleButton.querySelector("span");
      if (label) {
        label.textContent = expanded ? state.mapOpenLabel : state.mapClosedLabel;
      }
    }
  }

  function ensureMapVisible(state) {
    setToggleState(state, true);
    initMap(state);
    if (state.mapProvider === "leaflet" && state.mapInstance && typeof state.mapInstance.invalidateSize === "function") {
      window.setTimeout(function () {
        state.mapInstance.invalidateSize();
      }, 0);
    }
    if (state.mapCanvas) {
      state.mapCanvas.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  function setPoint(state, lat, lng, options) {
    var normalizedLat = parseCoordinate(lat);
    var normalizedLng = parseCoordinate(lng);
    if (normalizedLat === null || normalizedLng === null) return;

    state.latInput.value = formatCoordinate(normalizedLat);
    state.lngInput.value = formatCoordinate(normalizedLng);
    updateBadges(state);
    var form = state.root.closest("form");
    if (form) form.dispatchEvent(new CustomEvent("km:location-change", { bubbles: true }));

    if (state.mapProvider === "google" && state.mapInstance && window.google && window.google.maps) {
      var point = { lat: normalizedLat, lng: normalizedLng };
      if (!state.marker) {
        state.marker = new google.maps.Marker({ position: point, map: state.mapInstance, draggable: true });
        state.marker.addListener("dragend", function (event) {
          if (!event.latLng) return;
          setPoint(state, event.latLng.lat(), event.latLng.lng(), { recenter: false, reverseGeocode: true });
        });
      } else {
        state.marker.setPosition(point);
      }
      if (!options || options.recenter !== false) {
        state.mapInstance.setCenter(point);
        if (state.mapInstance.getZoom() < 15) {
          state.mapInstance.setZoom(15);
        }
      }
      if (!options || options.reverseGeocode !== false) {
        reverseGeocodeGoogle(state, normalizedLat, normalizedLng);
      }
      return;
    }

    if (state.mapProvider === "leaflet" && state.mapInstance && window.L) {
      if (!state.marker) {
        state.marker = window.L.marker([normalizedLat, normalizedLng], { draggable: true }).addTo(state.mapInstance);
        state.marker.on("dragend", function (event) {
          var point = event.target.getLatLng();
          setPoint(state, point.lat, point.lng, { recenter: false });
        });
      } else {
        state.marker.setLatLng([normalizedLat, normalizedLng]);
      }
      if (!options || options.recenter !== false) {
        state.mapInstance.setView([normalizedLat, normalizedLng], Math.max(state.mapInstance.getZoom(), 15));
      }
    }
  }

  function clearPoint(state) {
    state.latInput.value = "";
    state.lngInput.value = "";
    if (state.marker) {
      if (state.mapProvider === "google") {
        state.marker.setMap(null);
      } else if (state.mapInstance) {
        state.mapInstance.removeLayer(state.marker);
      }
    }
    state.marker = null;
    updateFoundAddress(state, "");
    updateBadges(state);
    var form = state.root.closest("form");
    if (form) form.dispatchEvent(new CustomEvent("km:location-change", { bubbles: true }));
  }

  function reverseGeocodeGoogle(state, lat, lng) {
    if (!window.google || !window.google.maps) return;
    if (!state.geocoder) {
      state.geocoder = new google.maps.Geocoder();
    }
    state.geocoder.geocode({ location: { lat: lat, lng: lng } }, function (results, status) {
      if (status !== "OK" || !results || !results.length) return;
      updateFoundAddress(state, results[0].formatted_address || "");
    });
  }

  function geocodeGoogle(state, query) {
    if (!window.google || !window.google.maps) return;
    if (!state.geocoder) {
      state.geocoder = new google.maps.Geocoder();
    }

    state.geocoder.geocode({ address: query, region: "az" }, function (results, status) {
      if (status !== "OK" || !results || !results.length) {
        if (state.statusText) {
          state.statusText.textContent = state.searchErrorLabel;
        }
        return;
      }

      var place = results[0];
      var location = place.geometry && place.geometry.location;
      if (!location) return;

      ensureMapVisible(state);
      setPoint(state, location.lat(), location.lng(), { recenter: true, reverseGeocode: false });
      updateFoundAddress(state, place.formatted_address || query);

      if (place.geometry.viewport && state.mapInstance && typeof state.mapInstance.fitBounds === "function") {
        state.mapInstance.fitBounds(place.geometry.viewport);
      }
    });
  }

  function bindGoogleAutocomplete(state) {
    if (!window.google || !window.google.maps || !google.maps.places || state.googleAutocomplete) return;

    state.googleAutocomplete = new google.maps.places.Autocomplete(state.addressInput, {
      componentRestrictions: { country: "az" },
      fields: ["formatted_address", "geometry", "name"],
    });

    if (state.mapInstance && typeof state.googleAutocomplete.bindTo === "function") {
      state.googleAutocomplete.bindTo("bounds", state.mapInstance);
    }

    state.googleAutocomplete.addListener("place_changed", function () {
      var place = state.googleAutocomplete.getPlace();
      if (!place || !place.geometry || !place.geometry.location) return;
      ensureMapVisible(state);
      state.addressInput.value = place.formatted_address || place.name || state.addressInput.value;
      var form = state.root.closest("form");
      if (form) form.dispatchEvent(new CustomEvent("km:location-change", { bubbles: true }));
      updateFoundAddress(state, state.addressInput.value);
      setPoint(state, place.geometry.location.lat(), place.geometry.location.lng(), { recenter: true, reverseGeocode: false });
      if (place.geometry.viewport && state.mapInstance && typeof state.mapInstance.fitBounds === "function") {
        state.mapInstance.fitBounds(place.geometry.viewport);
      }
    });
  }

  function initLeafletMap(state) {
    if (!window.L || state.mapInstance) return;

    state.mapInstance = window.L.map(state.mapCanvas, {
      scrollWheelZoom: false,
      zoomControl: true,
    });

    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(state.mapInstance);

    state.mapInstance.on("click", function (event) {
      setPoint(state, event.latlng.lat, event.latlng.lng, { recenter: true });
    });

    state.mapCanvas.addEventListener("mouseenter", function () {
      state.mapInstance.scrollWheelZoom.enable();
    });
    state.mapCanvas.addEventListener("mouseleave", function () {
      state.mapInstance.scrollWheelZoom.disable();
    });

    window.addEventListener("resize", function () {
      if (state.mapInstance && typeof state.mapInstance.invalidateSize === "function") {
        state.mapInstance.invalidateSize();
      }
    });

    var lat = parseCoordinate(state.latInput.value);
    var lng = parseCoordinate(state.lngInput.value);
    if (lat !== null && lng !== null) {
      state.mapInstance.setView([lat, lng], 15);
      setPoint(state, lat, lng, { recenter: false });
    } else {
      state.mapInstance.setView([state.defaultLat, state.defaultLng], 12);
    }
  }

  function initGoogleMap(state) {
    if (!window.google || !window.google.maps || state.mapInstance) return;

    var lat = parseCoordinate(state.latInput.value);
    var lng = parseCoordinate(state.lngInput.value);
    var hasPoint = lat !== null && lng !== null;
    state.mapInstance = new google.maps.Map(state.mapCanvas, {
      center: hasPoint ? { lat: lat, lng: lng } : { lat: state.defaultLat, lng: state.defaultLng },
      zoom: hasPoint ? 15 : 12,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      gestureHandling: "cooperative",
    });

    state.mapInstance.addListener("click", function (event) {
      if (!event.latLng) return;
      setPoint(state, event.latLng.lat(), event.latLng.lng(), { recenter: true, reverseGeocode: true });
    });

    if (hasPoint) {
      setPoint(state, lat, lng, { recenter: false });
    }

    bindGoogleAutocomplete(state);
  }

  function initMap(state) {
    if (state.mapProvider === "google") {
      initGoogleMap(state);
      return;
    }
    initLeafletMap(state);
  }

  function bindActions(state) {
    if (state.toggleButton && !state.toggleButton.dataset.kmBound) {
      state.toggleButton.addEventListener("click", function () {
        var expanded = state.toggleButton.getAttribute("aria-expanded") === "true";
        if (expanded) {
          setToggleState(state, false);
          return;
        }
        ensureMapVisible(state);
      });
      state.toggleButton.dataset.kmBound = "1";
    }

    if (state.searchButton && !state.searchButton.dataset.kmBound) {
      state.searchButton.addEventListener("click", function () {
        var query = String(state.addressInput.value || "").trim();
        if (!query) {
          if (state.statusText) state.statusText.textContent = state.searchEmptyLabel;
          return;
        }

        if (state.mapProvider === "google" && window.google && window.google.maps) {
          geocodeGoogle(state, query);
          return;
        }

        if (state.statusText) {
          state.statusText.textContent = state.searchFallbackLabel;
        }
        if (state.fallbackSubmit) {
          state.fallbackSubmit.click();
        }
      });
      state.searchButton.dataset.kmBound = "1";
    }

    if (state.addressInput && !state.addressInput.dataset.kmBound) {
      state.addressInput.addEventListener("keydown", function (event) {
        if (event.key !== "Enter") return;
        event.preventDefault();
        if (state.searchButton) {
          state.searchButton.click();
        }
      });
      state.addressInput.dataset.kmBound = "1";
    }

    if (state.locateButton && !state.locateButton.dataset.kmBound) {
      state.locateButton.addEventListener("click", function () {
        ensureMapVisible(state);
        if (!navigator.geolocation) {
          if (state.statusText) state.statusText.textContent = state.locateUnsupportedLabel;
          return;
        }

        navigator.geolocation.getCurrentPosition(
          function (position) {
            setPoint(state, position.coords.latitude, position.coords.longitude, { recenter: true, reverseGeocode: true });
          },
          function () {
            if (state.statusText) state.statusText.textContent = state.locateErrorLabel;
          },
          { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
      });
      state.locateButton.dataset.kmBound = "1";
    }

    if (state.confirmButton && !state.confirmButton.dataset.kmBound) {
      state.confirmButton.addEventListener("click", function () {
        updateBadges(state);
        setToggleState(state, false);
      });
      state.confirmButton.dataset.kmBound = "1";
    }

    if (state.clearButton && !state.clearButton.dataset.kmBound) {
      state.clearButton.addEventListener("click", function () {
        clearPoint(state);
      });
      state.clearButton.dataset.kmBound = "1";
    }

    if (state.applyAddressButton && !state.applyAddressButton.dataset.kmBound) {
      state.applyAddressButton.addEventListener("click", function () {
        if (!state.pendingAddress) return;
        state.addressInput.value = state.pendingAddress;
        updateBadges(state);
        var form = state.root.closest("form");
        if (form) form.dispatchEvent(new CustomEvent("km:location-change", { bubbles: true }));
      });
      state.applyAddressButton.dataset.kmBound = "1";
    }

    if (!state.latInput.dataset.kmBound) {
      state.latInput.addEventListener("input", function () {
        updateBadges(state);
        if (!state.mapPanel.hidden) {
          setPoint(state, state.latInput.value, state.lngInput.value, { recenter: false, reverseGeocode: false });
        }
      });
      state.lngInput.addEventListener("input", function () {
        updateBadges(state);
        if (!state.mapPanel.hidden) {
          setPoint(state, state.latInput.value, state.lngInput.value, { recenter: false, reverseGeocode: false });
        }
      });
      state.addressInput.addEventListener("input", function () {
        updateBadges(state);
      });
      state.latInput.dataset.kmBound = "1";
    }
  }

  function initRoot(root) {
    if (!root) return;
    initRegionCascade(root);
    var state = buildState(root);
    if (!state) return;
    bindActions(state);
    updateBadges(state);
    updateFoundAddress(state, "");

    setToggleState(state, !state.mapPanel.hidden);

    if (!state.mapPanel.hidden) {
      initMap(state);
    }
  }

  function initAll() {
    document.querySelectorAll("[data-km-place-location]").forEach(initRoot);
  }

  window.kidsMapInitAdminPlaceLocation = initAll;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
