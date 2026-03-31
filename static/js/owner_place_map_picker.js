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

  function initMapPicker(root) {
    if (!root || !window.L) return;

    const latInput = root.querySelector('input[name="lat"]');
    const lngInput = root.querySelector('input[name="lng"]');
    const mapEl = root.querySelector("[data-map-canvas]");
    const statusEl = root.querySelector("[data-map-status]");
    const locateBtn = root.querySelector("[data-map-locate]");
    const clearBtn = root.querySelector("[data-map-clear]");

    if (!latInput || !lngInput || !mapEl || !statusEl) return;

    const defaultLat = parseCoordinate(root.dataset.defaultLat) ?? 40.409264;
    const defaultLng = parseCoordinate(root.dataset.defaultLng) ?? 49.867092;
    const selectedPrefix = root.dataset.selectedPrefix || "Selected point:";
    const emptyLabel = root.dataset.emptyLabel || "No point selected.";
    const locateErrorLabel = root.dataset.locateError || "Unable to detect your location.";
    const locateUnsupportedLabel = root.dataset.locateUnsupported || "Geolocation is not supported.";

    let marker = null;

    const map = L.map(mapEl, {
      scrollWheelZoom: false,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    function updateStatus(lat, lng) {
      if (lat === null || lng === null) {
        statusEl.textContent = emptyLabel;
        return;
      }
      statusEl.textContent = selectedPrefix + " " + formatCoordinate(lat) + ", " + formatCoordinate(lng);
    }

    function setPoint(lat, lng, options) {
      const recenter = !options || options.recenter !== false;
      latInput.value = formatCoordinate(lat);
      lngInput.value = formatCoordinate(lng);

      if (!marker) {
        marker = L.marker([lat, lng], { draggable: true }).addTo(map);
        marker.on("dragend", function (event) {
          const point = event.target.getLatLng();
          setPoint(point.lat, point.lng, { recenter: false });
        });
      } else {
        marker.setLatLng([lat, lng]);
      }

      updateStatus(lat, lng);
      if (recenter) {
        map.setView([lat, lng], Math.max(map.getZoom(), 15));
      }
    }

    function clearPoint() {
      latInput.value = "";
      lngInput.value = "";
      if (marker) {
        map.removeLayer(marker);
        marker = null;
      }
      updateStatus(null, null);
    }

    map.on("click", function (event) {
      setPoint(event.latlng.lat, event.latlng.lng);
    });

    if (locateBtn) {
      locateBtn.addEventListener("click", function () {
        if (!navigator.geolocation) {
          statusEl.textContent = locateUnsupportedLabel;
          return;
        }

        navigator.geolocation.getCurrentPosition(
          function (position) {
            setPoint(position.coords.latitude, position.coords.longitude);
          },
          function () {
            statusEl.textContent = locateErrorLabel;
          },
          { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        clearPoint();
      });
    }

    const initialLat = parseCoordinate(latInput.value);
    const initialLng = parseCoordinate(lngInput.value);
    if (initialLat !== null && initialLng !== null) {
      map.setView([initialLat, initialLng], 15);
      setPoint(initialLat, initialLng, { recenter: false });
    } else {
      map.setView([defaultLat, defaultLng], 12);
      updateStatus(null, null);
    }

    setTimeout(function () {
      map.invalidateSize();
    }, 0);

    window.addEventListener("resize", function () {
      map.invalidateSize();
    });

    mapEl.addEventListener("mouseenter", function () {
      map.scrollWheelZoom.enable();
    });
    mapEl.addEventListener("mouseleave", function () {
      map.scrollWheelZoom.disable();
    });
  }

  function initAllMapPickers() {
    document.querySelectorAll("[data-owner-map-picker]").forEach(initMapPicker);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllMapPickers);
  } else {
    initAllMapPickers();
  }
})();
