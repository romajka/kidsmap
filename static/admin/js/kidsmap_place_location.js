(function () {
  function parseCoordinate(value, limit) {
    var normalized = String(value == null ? "" : value).trim().replace(",", ".");
    if (!normalized) return null;
    var parsed = Number(normalized);
    return Number.isFinite(parsed) && Math.abs(parsed) <= limit ? parsed : null;
  }

  function formatCoordinate(value) {
    return Number(value).toFixed(6);
  }

  function updateLocationBadges(root, regionSelect, districtSelect, metroSelect) {
    var badgesContainer = root.querySelector("[data-km-location-badges]");
    if (!badgesContainer) return;

    var cityText = badgesContainer.querySelector("[data-km-loc-city-text]");
    var districtBadge = badgesContainer.querySelector("[data-km-loc-district-badge]");
    var districtText = badgesContainer.querySelector("[data-km-loc-district-text]");
    var metroBadge = badgesContainer.querySelector("[data-km-loc-metro-badge]");
    var metroText = badgesContainer.querySelector("[data-km-loc-metro-text]");

    var regionLabel = regionSelect && regionSelect.selectedIndex >= 0 ? regionSelect.options[regionSelect.selectedIndex].text.trim() : "";
    var isBaku = !regionSelect || !regionSelect.value || regionSelect.value === "baku" || /баку|baku|bakı/i.test(regionLabel);

    if (cityText) {
      cityText.textContent = regionLabel && regionSelect.value ? regionLabel : "Баку";
    }

    if (districtBadge && districtText) {
      if (!isBaku) {
        districtBadge.style.display = "none";
      } else {
        districtBadge.style.display = "";
        var distVal = districtSelect ? districtSelect.value : "";
        var distLabel = districtSelect && districtSelect.selectedIndex >= 0 && distVal ? districtSelect.options[districtSelect.selectedIndex].text.trim() : "";
        if (distLabel) {
          districtBadge.classList.add("km-loc-badge--active");
          districtText.textContent = distLabel;
        } else {
          districtBadge.classList.remove("km-loc-badge--active");
          districtText.textContent = "Район не выбран";
        }
      }
    }

    if (metroBadge && metroText) {
      if (!isBaku) {
        metroBadge.style.display = "none";
      } else {
        metroBadge.style.display = "";
        var metroVal = metroSelect ? metroSelect.value : "";
        var metroLabel = metroSelect && metroSelect.selectedIndex >= 0 && metroVal ? metroSelect.options[metroSelect.selectedIndex].text.trim() : "";
        if (metroLabel) {
          metroBadge.classList.add("km-loc-badge--active");
          metroText.textContent = metroLabel;
        } else {
          metroBadge.classList.remove("km-loc-badge--active");
          metroText.textContent = "Метро не выбрано";
        }
      }
    }
  }

  function initRegionCascade(root) {
    var regionSelect = root.querySelector("[data-km-location-region]") || document.getElementById("id_region");
    var districtSelect = root.querySelector("[data-km-location-district]") || document.getElementById("id_district");
    var metroSelect = document.getElementById("id_metro");
    var districtBox = root.querySelector("[data-km-admin-district-box]");
    var metroBox = root.querySelector("[data-km-admin-metro-box]");

    if (!regionSelect || !districtSelect) return;

    function sync() {
      var regionLabel = regionSelect && regionSelect.selectedIndex >= 0 ? regionSelect.options[regionSelect.selectedIndex].text.trim() : "";
      var isBaku = regionSelect.value === "baku" || /баку|baku|bakı/i.test(regionLabel);
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

      updateLocationBadges(root, regionSelect, districtSelect, metroSelect);
    }

    [regionSelect, districtSelect, metroSelect].filter(Boolean).forEach(function (sel) {
      if (sel.dataset.kmLocationCascadeBound) return;
      sel.addEventListener("change", sync);
      sel.dataset.kmLocationCascadeBound = "1";
      if (window.$ && window.$.fn && typeof window.$.fn.select2 !== "undefined") {
        try {
          window.$(sel).on("select2:select select2:unselect select2:clear", sync);
        } catch (error) {}
      }
    });

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
      unavailableNote: root.querySelector("[data-km-place-location-unavailable]"),
      coordBadge: coordBadge,
      mapBadge: mapBadge,
      foundBox: foundBox,
      foundText: foundText,
      applyAddressButton: applyAddressButton,
      coordsDisplay: root.querySelector("[data-km-place-coords-display]"),
      externalMapLink: root.querySelector("[data-km-open-external-map]"),
      copyCoordsBtn: root.querySelector("[data-km-copy-coords]"),
      recenterBtn: root.querySelector("[data-km-place-location-recenter]"),
      _isSettingPoint: false,
      requestVersion: 0,
      currentAddress: addressInput.value.trim(),
      confirmation: root.querySelector('[name="_location_point_confirmed"]'),
      choices: root.querySelector("[data-km-place-location-choices]"),
      policy: root.dataset.geocodingPolicy ? JSON.parse(root.dataset.geocodingPolicy) : null,
      mapProvider: root.dataset.mapProvider || "leaflet",
      offlineOpenLabel: root.dataset.offlineOpenLabel,
      offlineClosedLabel: root.dataset.offlineClosedLabel,
      defaultLat: parseCoordinate(root.dataset.defaultLat, 90) || 40.409264,
      defaultLng: parseCoordinate(root.dataset.defaultLng, 180) || 49.867092,
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

  function invalidateLookup(state) {
    state.requestVersion += 1;
    updateFoundAddress(state, "");
    if (state.choices) {
      state.choices.replaceChildren();
      state.choices.hidden = true;
    }
  }

  function confirmPoint(state, confirmed) {
    if (state.confirmation) state.confirmation.value = confirmed ? "1" : "";
  }

  function updateBadges(state) {
    var lat = parseCoordinate(state.latInput.value, 90);
    var lng = parseCoordinate(state.lngInput.value, 180);
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
    var coordGrid = state.root.querySelector("[data-pf-coord-fields], .km-place-location__coord-grid");
    if (coordGrid) {
      if (coordGrid.hasAttribute("data-pf-coord-fields")) {
        coordGrid.hidden = !expanded;
      } else {
        coordGrid.style.display = expanded ? "grid" : "none";
      }
    }
    if (state.toggleButton) {
      state.toggleButton.setAttribute("aria-expanded", expanded ? "true" : "false");
      var label = state.toggleButton.querySelector("span");
      if (label) {
        var offline = state.unavailableNote && !state.mapAvailable;
        label.textContent = expanded
          ? (offline ? state.offlineOpenLabel : state.mapOpenLabel)
          : (offline ? state.offlineClosedLabel : state.mapClosedLabel);
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
    if (state._isSettingPoint) return;
    state._isSettingPoint = true;
    try {
      var normalizedLat = parseCoordinate(lat, 90);
      var normalizedLng = parseCoordinate(lng, 180);
      if (normalizedLat === null || normalizedLng === null) return;

      invalidateLookup(state);
      if (!options || !options.initial) confirmPoint(state, true);
      var formattedLat = formatCoordinate(normalizedLat);
      var formattedLng = formatCoordinate(normalizedLng);
      state.latInput.value = formattedLat;
      state.lngInput.value = formattedLng;
      state.latInput.dispatchEvent(new Event("input", { bubbles: true }));
      state.lngInput.dispatchEvent(new Event("input", { bubbles: true }));
      state.latInput.dispatchEvent(new Event("change", { bubbles: true }));
      state.lngInput.dispatchEvent(new Event("change", { bubbles: true }));
      updateBadges(state);
      var form = state.root.closest("form");
      if (form) form.dispatchEvent(new CustomEvent("km:location-change", { bubbles: true }));

      if (state.coordsDisplay) {
        state.coordsDisplay.innerHTML = 'Широта: <strong>' + formattedLat + '</strong> · Долгота: <strong>' + formattedLng + '</strong>';
      }
      if (state.externalMapLink) {
        state.externalMapLink.href = 'https://www.google.com/maps?q=' + formattedLat + ',' + formattedLng;
        state.externalMapLink.style.display = 'inline-flex';
      }

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
        var customPinIcon = window.L.divIcon({
          className: "km-admin-map-pin-wrap",
          html: '<div class="km-admin-map-pin"><svg viewBox="0 0 24 24" width="30" height="30" fill="#10b981" stroke="#065f46" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3.2" fill="#ffffff" stroke="none" /></svg></div>',
          iconSize: [30, 38],
          iconAnchor: [15, 38],
          popupAnchor: [0, -38]
        });

        if (!state.marker) {
          state.marker = window.L.marker([normalizedLat, normalizedLng], { draggable: true, icon: customPinIcon }).addTo(state.mapInstance);
          state.marker.bindTooltip("Перетащите маркер для точной настройки", { direction: "top", offset: [0, -38] });
          state.marker.on("dragend", function (event) {
            var pt = event.target.getLatLng();
            setPoint(state, pt.lat, pt.lng, { recenter: false });
          });
        } else {
          state.marker.setLatLng([normalizedLat, normalizedLng]);
        }
        if (!options || options.recenter !== false) {
          state.mapInstance.setView([normalizedLat, normalizedLng], Math.max(state.mapInstance.getZoom(), 15));
        }
      }
    } finally {
      state._isSettingPoint = false;
    }
  }

  function clearPoint(state) {
    if (state._isSettingPoint) return;
    state._isSettingPoint = true;
    try {
      invalidateLookup(state);
      confirmPoint(state, false);
      state.latInput.value = "";
      state.lngInput.value = "";
      state.latInput.dispatchEvent(new Event("input", { bubbles: true }));
      state.lngInput.dispatchEvent(new Event("input", { bubbles: true }));
      state.latInput.dispatchEvent(new Event("change", { bubbles: true }));
      state.lngInput.dispatchEvent(new Event("change", { bubbles: true }));
      if (state.marker) {
        if (state.mapProvider === "google") {
          state.marker.setMap(null);
        } else if (state.mapInstance) {
          state.mapInstance.removeLayer(state.marker);
        }
      }
      state.marker = null;
      if (state.coordsDisplay) {
        state.coordsDisplay.textContent = "Точка не установлена — нажмите на карту";
      }
      if (state.externalMapLink) {
        state.externalMapLink.style.display = "none";
        state.externalMapLink.removeAttribute("href");
      }
      updateBadges(state);
      var form = state.root.closest("form");
      if (form) form.dispatchEvent(new CustomEvent("km:location-change", { bubbles: true }));
    } finally {
      state._isSettingPoint = false;
    }
  }

  function reverseGeocodeGoogle(state, lat, lng) {
    if (!window.google || !window.google.maps) return;
    if (!state.geocoder) {
      state.geocoder = new google.maps.Geocoder();
    }
    var version = state.requestVersion;
    state.geocoder.geocode({ location: { lat: lat, lng: lng } }, function (results, status) {
      if (version !== state.requestVersion || status !== "OK" || !results || !results[0]) return;
      updateFoundAddress(state, results[0].formatted_address || "");
    });
  }

  function resultPoint(place) {
    var location = place && place.geometry && place.geometry.location;
    if (!location || typeof location.lat !== "function" || typeof location.lng !== "function") return null;
    var lat = location.lat(), lng = location.lng();
    if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) return null;
    return {lat: lat, lng: lng};
  }

  function validAddressComponents(place) {
    return place.address_components === undefined || (Array.isArray(place.address_components) &&
      place.address_components.every(component => component && Array.isArray(component.types)));
  }

  function isLocalResult(place, point, bounds) {
    var components = place.address_components || [];
    var foreign = components.some(function (component) {
      return component && Array.isArray(component.types) && component.types.includes("country") &&
        String(component.short_name || "").toUpperCase() !== "AZ";
    });
    return !foreign && point.lat >= bounds[0] && point.lat <= bounds[1] &&
      point.lng >= bounds[2] && point.lng <= bounds[3];
  }

  function resolveSearchResults(results, policy) {
    var choices = new Map();
    var labels = new Set();
    var hasPoint = false;
    results.forEach(function (place) {
      var point = resultPoint(place);
      if (!point || !validAddressComponents(place) || !Array.isArray(place.types) ||
          !place.types.every(type => typeof type === "string")) return;
      hasPoint = true;
      if (!isLocalResult(place, point, policy.bounds)) return;
      if (place.formatted_address) labels.add(place.formatted_address);
      var types = place.types;
      if (place.partial_match || !policy.precision.includes(place.geometry.location_type) ||
          !types.some(type => policy.types.includes(type)) || types.some(type => policy.transit.includes(type))) return;
      var key = formatCoordinate(point.lat) + "," + formatCoordinate(point.lng);
      if (!choices.has(key)) choices.set(key, {place: place, point: point});
    });
    return {choices: Array.from(choices.values()), labels: Array.from(labels), hasPoint: hasPoint};
  }

  function applySearchResult(state, candidate) {
    ensureMapVisible(state);
    setPoint(state, candidate.point.lat, candidate.point.lng, { recenter: true, reverseGeocode: false });
    updateFoundAddress(state, candidate.place.formatted_address || "");
    if (candidate.place.geometry.viewport && state.mapInstance) {
      state.mapInstance.fitBounds(candidate.place.geometry.viewport);
    }
  }

  function showSearchChoices(state, resolved, version) {
    if (!state.choices) return;
    function item(text, candidate) {
      var row = document.createElement("li");
      if (candidate) {
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = text;
        button.addEventListener("click", function () {
          if (version !== state.requestVersion) return;
          applySearchResult(state, candidate);
          (state.confirmButton || state.searchButton).focus({preventScroll: true});
        });
        row.appendChild(button);
      } else {
        row.textContent = text;
      }
      state.choices.appendChild(row);
    }
    if (resolved.choices.length) {
      resolved.choices.forEach(function (candidate) {
        var coordinates = formatCoordinate(candidate.point.lat) + ", " + formatCoordinate(candidate.point.lng);
        var address = candidate.place.formatted_address;
        item(address ? address + " (" + coordinates + ")" : coordinates, candidate);
      });
    } else {
      resolved.labels.forEach(function (label) { item(label); });
    }
    state.choices.hidden = !state.choices.childElementCount;
  }

  function geocodeGoogle(state, query) {
    clearPoint(state);
    var version = state.requestVersion;
    if (!state.geocoder) state.geocoder = new google.maps.Geocoder();
    state.geocoder.geocode({ address: query, region: "az", componentRestrictions: {country: "AZ"} }, function (results, status) {
      if (version !== state.requestVersion || state.addressInput.value.trim() !== query) return;
      var message;
      if (status === "ZERO_RESULTS" || (status === "OK" && Array.isArray(results) && !results.length)) {
        message = state.searchErrorLabel;
      } else if (status !== "OK" || !Array.isArray(results) || !state.policy) {
        message = state.root.dataset.searchUnavailable;
      } else {
        var resolved = resolveSearchResults(results, state.policy);
        if (resolved.choices.length === 1) {
          applySearchResult(state, resolved.choices[0]);
          return;
        }
        showSearchChoices(state, resolved, version);
        message = resolved.hasPoint ? state.root.dataset.searchImprecise : state.root.dataset.searchUnavailable;
      }
      if (state.statusText) state.statusText.textContent = message;
    });
  }

  function bindGoogleAutocomplete(state) {
    if (!window.google || !window.google.maps || !google.maps.places || state.googleAutocomplete) return;

    state.googleAutocomplete = new google.maps.places.Autocomplete(state.addressInput, {
      componentRestrictions: { country: "az" },
      fields: ["formatted_address", "geometry", "name", "address_components"],
    });

    if (state.mapInstance && typeof state.googleAutocomplete.bindTo === "function") {
      state.googleAutocomplete.bindTo("bounds", state.mapInstance);
    }

    state.googleAutocomplete.addListener("place_changed", function () {
      var place = state.googleAutocomplete.getPlace();
      // Pressing Enter on free text can also emit place_changed with only a name.
      if (!place || !place.geometry) return;
      var point = resultPoint(place);
      if (!point || !validAddressComponents(place) || !state.policy || !isLocalResult(place, point, state.policy.bounds)) {
        clearPoint(state);
        if (state.statusText) state.statusText.textContent = state.root.dataset.searchImprecise;
        return;
      }
      state.addressInput.value = place.formatted_address || place.name || state.addressInput.value;
      state.currentAddress = state.addressInput.value.trim();
      applySearchResult(state, {place: place, point: point});
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

    var lat = parseCoordinate(state.latInput.value, 90);
    var lng = parseCoordinate(state.lngInput.value, 180);
    if (lat !== null && lng !== null) {
      state.mapInstance.setView([lat, lng], 15);
      setPoint(state, lat, lng, { recenter: false, initial: true });
    } else {
      state.mapInstance.setView([state.defaultLat, state.defaultLng], 12);
    }
  }

  function initGoogleMap(state) {
    if (!window.google || !window.google.maps || state.mapInstance) return;

    var lat = parseCoordinate(state.latInput.value, 90);
    var lng = parseCoordinate(state.lngInput.value, 180);
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
      setPoint(state, lat, lng, { recenter: false, initial: true });
    }

    bindGoogleAutocomplete(state);
  }

  function updateMapAvailability(state) {
    var available = state.mapProvider === "google"
      ? !!(window.google && window.google.maps)
      : state.mapProvider === "leaflet" && !!window.L;
    state.mapAvailable = available;
    if (state.unavailableNote) {
      state.unavailableNote.hidden = available;
      state.mapCanvas.hidden = !available;
      var hint = state.root.querySelector(".km-pf-mappanel__hint");
      if (hint) hint.hidden = !available;
      if (state.searchButton) {
        state.searchButton.disabled = !available;
        if (available) state.searchButton.removeAttribute("aria-describedby");
        else state.searchButton.setAttribute("aria-describedby", state.unavailableNote.id);
      }
    }
    return available;
  }

  function initMap(state) {
    if (!updateMapAvailability(state)) return;
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

        invalidateLookup(state);
        var version = state.requestVersion;
        navigator.geolocation.getCurrentPosition(
          function (position) {
            if (version !== state.requestVersion) return;
            setPoint(state, position.coords.latitude, position.coords.longitude, { recenter: true, reverseGeocode: true });
          },
          function () {
            if (version !== state.requestVersion) return;
            if (state.statusText) state.statusText.textContent = state.locateErrorLabel;
          },
          { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
      });
      state.locateButton.dataset.kmBound = "1";
    }

    if (state.confirmButton && !state.confirmButton.dataset.kmBound) {
      state.confirmButton.addEventListener("click", function () {
        invalidateLookup(state);
        confirmPoint(state, parseCoordinate(state.latInput.value, 90) !== null && parseCoordinate(state.lngInput.value, 180) !== null);
        updateBadges(state);
        setToggleState(state, false);
        if (state.toggleButton) state.toggleButton.focus();
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
        state.currentAddress = state.addressInput.value.trim();
        confirmPoint(state, true);
        updateBadges(state);
        var form = state.root.closest("form");
        if (form) form.dispatchEvent(new CustomEvent("km:location-change", { bubbles: true }));
      });
      state.applyAddressButton.dataset.kmBound = "1";
    }

    if (!state.latInput.dataset.kmBound) {
      var restoring = false;
      var form = state.root.closest("form");
      if (form) {
        form.addEventListener("km:location-restore-start", function () {
          restoring = true;
          invalidateLookup(state);
          confirmPoint(state, false);
        });
        form.addEventListener("km:location-restore-end", function () {
          restoring = false;
          state.currentAddress = state.addressInput.value.trim();
          updateBadges(state);
        });
      }
      [state.latInput, state.lngInput].forEach(function (input) {
        input.addEventListener("input", function () {
          if (state._isSettingPoint || restoring) return;
          invalidateLookup(state);
          confirmPoint(state, parseCoordinate(state.latInput.value, 90) !== null && parseCoordinate(state.lngInput.value, 180) !== null);
          updateBadges(state);
        });
        input.addEventListener("change", function () {
          if (!state._isSettingPoint && !restoring && !state.mapPanel.hidden) {
            setPoint(state, state.latInput.value, state.lngInput.value, { recenter: false, reverseGeocode: false });
          }
        });
      });
      function addressChanged() {
        var address = state.addressInput.value.trim();
        if (restoring || address === state.currentAddress) return;
        state.currentAddress = address;
        if (state.latInput.value || state.lngInput.value || state.marker) clearPoint(state);
        else {
          invalidateLookup(state);
          confirmPoint(state, false);
          updateBadges(state);
        }
      }
      state.addressInput.addEventListener("input", addressChanged);
      state.addressInput.addEventListener("change", addressChanged);
      if (form) form.addEventListener("submit", addressChanged, true);
      state.latInput.dataset.kmBound = "1";
    }
  }

  function initRoot(root) {
    if (!root) return;
    initRegionCascade(root);
    // The SDK callback may run after the local controls are already bound.
    // Reuse their state instead of creating a second map with stale handlers.
    var state = root._kidsMapAdminPlaceLocationState || buildState(root);
    if (!state) return;
    root._kidsMapAdminPlaceLocationState = state;
    state.mapProvider = root.dataset.mapProvider || "leaflet";
    updateMapAvailability(state);
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
