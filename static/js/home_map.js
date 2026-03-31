(function () {
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

  function renderFallback() {
    const mapEl = document.getElementById("home-map");
    if (!mapEl) return;

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

  function initHomeMap() {
    const mapEl = document.getElementById("home-map");
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
      center: { lat: validPlaces[0].lat, lng: validPlaces[0].lng },
      zoom: validPlaces.length === 1 ? 12 : 10,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      gestureHandling: "cooperative",
    });
    const bounds = new google.maps.LatLngBounds();
    const infoWindow = new google.maps.InfoWindow();

    validPlaces.forEach(function (place) {
      const position = { lat: place.lat, lng: place.lng };
      const marker = new google.maps.Marker({
        position: position,
        map: map,
        title: place.name || "",
      });

      marker.addListener("click", function () {
        infoWindow.setContent(
          "<strong>" +
            escapeHtml(place.name) +
            "</strong><br>" +
            escapeHtml(place.category) +
            "<br>" +
            '<a href="' +
            encodeURI(place.url || "") +
            '">' +
            escapeHtml(detailsLabel) +
            "</a>"
        );
        infoWindow.open({
          anchor: marker,
          map: map,
        });
      });

      bounds.extend(position);
    });

    if (validPlaces.length === 1) {
      map.setCenter(bounds.getCenter());
      map.setZoom(12);
      return;
    }

    map.fitBounds(bounds);
  }

  window.kidsMapInitHomeMap = initHomeMap;
  window.kidsMapRenderHomeMapFallback = renderFallback;
})();
