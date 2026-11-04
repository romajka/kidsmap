/* Public map only. Coordinates are JSON; user-provided labels are always text. */
(function () {
  'use strict';

  function initSpecialistMap() {
    const element = document.getElementById('specialist-map');
    const payload = document.getElementById('specialist-map-locations');
    const fallback = document.querySelector('[data-specialist-map-fallback]');
    if (!element || !payload || element.dataset.mapInitialized === '1') return;
    let locations;
    try { locations = JSON.parse(payload.textContent); } catch (_) { return; }
    if (!Array.isArray(locations)) return;
    locations = locations.filter(function (location) {
      return location && typeof location.lat === 'number' && typeof location.lng === 'number' &&
        Number.isFinite(location.lat) && Number.isFinite(location.lng) &&
        Math.abs(location.lat) <= 90 && Math.abs(location.lng) <= 180;
    });
    if (!locations.length || !window.google || !window.google.maps ||
        typeof window.kidsMapCreateGoogleMarker !== 'function') return;

    try {
      element.hidden = false;
      const mapId = (element.dataset.googleMapId || '').trim();
      const options = {
        center: {lat: locations[0].lat, lng: locations[0].lng}, zoom: 14,
        mapTypeControl: false, streetViewControl: false, fullscreenControl: false,
        gestureHandling: 'cooperative'
      };
      if (mapId) options.mapId = mapId;
      const map = new window.google.maps.Map(element, options);
      const bounds = new window.google.maps.LatLngBounds();
      locations.forEach(function (location) {
        const position = {lat: location.lat, lng: location.lng};
        const title = String(location.place_name || '');
        const marker = window.kidsMapCreateGoogleMarker({position: position, map: map, title: title, mapId: mapId});
        const content = document.createElement('div');
        content.className = 'sp-map-popup';
        const name = document.createElement('strong');
        name.textContent = title;
        const address = document.createElement('p');
        address.textContent = String(location.address || '');
        content.append(name, address);
        const info = new window.google.maps.InfoWindow({content: content});
        marker.addListener('click', function () { info.open({map: map, anchor: marker}); });
        bounds.extend(position);
      });
      if (locations.length > 1) map.fitBounds(bounds, 30);
      element.dataset.mapInitialized = '1';
      if (fallback) fallback.hidden = true;
    } catch (_) {
      element.hidden = true;
      if (fallback) fallback.hidden = false;
    }
  }

  // Defined before the async provider script; also handles an already-loaded provider.
  window.kidsMapInitSpecialistMap = initSpecialistMap;
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initSpecialistMap, {once: true});
  else initSpecialistMap();
})();
