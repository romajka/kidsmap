(function () {
  const DEFAULT_CENTER = { lat: 40.4093, lng: 49.8671 };
  const DEFAULT_ZOOM = 11;

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

  function renderFallback() {
    const mapEl = document.getElementById("home-map");
    const mapNoteEl = document.getElementById("home-map-note");
    if (!mapEl) return;

    if (mapNoteEl) {
      mapNoteEl.hidden = true;
      mapNoteEl.textContent = "";
    }

    const title = mapEl.dataset.fallbackTitle || "Map";
    mapEl.innerHTML =
      '<iframe class="home-map home-map-fallback" src="https://maps.google.com/maps?q=Azerbaijan&z=7&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="' +
      escapeHtml(title) +
      '"></iframe>';
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

  function bindFilterListeners(updateMap) {
    const form = document.querySelector("[data-home-map-filter-form]");
    if (!form || typeof updateMap !== "function") return;

    let searchTimer = null;
    const queryInput = form.querySelector('[name="q"]');
    const selectControls = form.querySelectorAll('select[name="category"], select[name="district"], select[name="metro"], select[name="age"]');

    function scheduleUpdate() {
      if (searchTimer) {
        window.clearTimeout(searchTimer);
      }
      searchTimer = window.setTimeout(updateMap, 120);
    }

    if (queryInput) {
      queryInput.addEventListener("input", scheduleUpdate);
    }

    selectControls.forEach(function (control) {
      control.addEventListener("change", updateMap);
    });
  }

  function initHomeMap() {
    const mapEl = document.getElementById("home-map");
    const mapNoteEl = document.getElementById("home-map-note");
    if (!mapEl || mapEl.dataset.mapInitialized === "1") return;
    if (!window.google || !window.google.maps) {
      renderFallback();
      return;
    }

    const places = parsePlaces();
    const validPlaces = places.filter(function (place) {
      return typeof place.lat === "number" && typeof place.lng === "number";
    });

    if (!validPlaces.length) {
      renderFallback();
      return;
    }

    mapEl.dataset.mapInitialized = "1";

    const detailsLabel = mapEl.dataset.detailsLabel || "Details";
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

    function setMapNote(hasVisiblePlaces) {
      if (!mapNoteEl) return;
      mapNoteEl.hidden = hasVisiblePlaces;
      mapNoteEl.textContent = hasVisiblePlaces ? "" : (mapEl.dataset.emptyLabel || "");
    }

    validPlaces.forEach(function (place) {
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
        setMapNote(false);
        return;
      }

      if (visibleItems.length === 1) {
        map.setCenter(visibleItems[0].position);
        map.setZoom(13);
        setMapNote(true);
        return;
      }

      map.fitBounds(bounds, { top: 32, right: 32, bottom: 32, left: 32 });
      setMapNote(true);
    }

    bindFilterListeners(syncVisibleMarkers);
    syncVisibleMarkers();
  }

  window.kidsMapInitHomeMap = initHomeMap;
  window.kidsMapRenderHomeMapFallback = renderFallback;
})();
