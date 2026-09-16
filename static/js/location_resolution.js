/* Coordinate preview only. Save-time assignment always runs on the server. */
(function () {
  'use strict';
  function init(root) {
    if (root.dataset.bound) return;
    var form = root.closest('form');
    if (!form) return;
    var lat = form.querySelector('[name="lat"]'), lng = form.querySelector('[name="lng"]');
    var city = form.querySelector('[name="region"]'), district = form.querySelector('[name="district"]');
    var reason = form.querySelector('[name="location_override_reason"]');
    var status = root.querySelector('[role="status"]');
    if (!lat || !lng || !city || !district || !status) return;
    root.dataset.bound = '1';
    var previous = null, serial = 0, timer, controller, applying = false;
    var initialPoint = lat.value.trim() + '|' + lng.value.trim();
    function announce(message, busy) {
      status.textContent = message;
      root.setAttribute('aria-busy', busy ? 'true' : 'false');
    }
    function paint(state) {
      root.dataset.status = state;
      var pointLabel = root.querySelector('[data-location-point]');
      var cityLabel = root.querySelector('[data-location-city]');
      var districtLabel = root.querySelector('[data-location-district]');
      var retry = root.querySelector('[data-location-retry]');
      var ready = state !== 'loading' && state !== 'empty';
      function label(select) { return select.value && select.selectedOptions.length ? select.selectedOptions[0].textContent : '—'; }
      if (pointLabel) pointLabel.textContent = lat.value.trim() && lng.value.trim() ? root.dataset.pointSelected : root.dataset.pointEmpty;
      if (cityLabel) cityLabel.textContent = ready ? label(city) : '—';
      if (districtLabel) districtLabel.textContent = ready ? label(district) : '—';
      if (retry) retry.hidden = state !== 'unavailable';
    }
    function values(cityKey, districtKey, pending) {
      var metro = form.querySelector('[name="metro"]');
      var savedMetro = metro ? metro.value : null;
      applying = true;
      city.value = cityKey || '';
      city.dispatchEvent(new Event('change', {bubbles: true}));
      if (pending && metro) metro.value = savedMetro;
      district.disabled = cityKey !== 'baku';
      district.value = districtKey || '';
      district.dispatchEvent(new Event('change', {bubbles: true}));
      applying = false;
    }
    function update() {
      if (applying) return;
      var point = lat.value.trim() + '|' + lng.value.trim();
      if (point === previous) return;
      var first = previous === null;
      previous = point;
      var requestId = ++serial;
      clearTimeout(timer);
      if (controller) controller.abort();
      // Resolve the dataset version even for a stored exception. It remains
      // valid only for the exact point and version approved by the admin.
      var preserveOverride = first && root.dataset.initialStatus === 'overridden' && point === initialPoint;
      if (reason && !first) reason.value = '';
      // On initial load keep values during lookup, especially legacy values.
      // Moving the pin always clears stale geography immediately.
      if (!first) values('', '', true);
      if (!lat.value.trim() || !lng.value.trim()) {
        if (!first) values('', '');
        paint('empty');
        announce(root.dataset.empty, false);
        return;
      }
      paint('loading');
      announce(root.dataset.loading, true);
      timer = setTimeout(function () {
        controller = new AbortController();
        var activeController = controller;
        var timeout = setTimeout(function () { activeController.abort(); }, 10000);
        var url = new URL(root.dataset.url, window.location.href);
        url.searchParams.set('language', root.dataset.language || document.documentElement.lang || '');
        url.searchParams.set('lat', lat.value.trim());
        url.searchParams.set('lng', lng.value.trim());
        fetch(url.toString(), {credentials: 'same-origin', signal: activeController.signal, headers: {'Accept': 'application/json'}})
          .then(function (response) {
            if (response.redirected) throw new Error('Session expired');
            return response.json();
          })
          .then(function (result) {
            if (requestId !== serial || point !== lat.value.trim() + '|' + lng.value.trim()) return;
            if (preserveOverride && result.dataset_version === root.dataset.initialVersion) {
              announce(root.dataset.overridden || '', false);
              paint('overridden');
              return;
            }
            values(result.city_key, result.district_key);
            var labels = [result.city_label, result.district_label].filter(Boolean).join(' · ');
            announce((labels ? labels + '. ' : '') + result.message, false);
            paint(result.status);
          })
          .catch(function () {
            if (requestId !== serial) return;
            values('', '');
            paint('unavailable');
            announce(root.dataset.error, false);
          })
          .finally(function () { clearTimeout(timeout); });
      }, 180);
    }
    var retry = root.querySelector('[data-location-retry]');
    if (retry) retry.addEventListener('click', function () { previous = null; update(); });
    ['input', 'change'].forEach(function (event) {
      lat.addEventListener(event, update); lng.addEventListener(event, update);
    });
    ['km:map-change', 'km:location-change', 'km:json-imported'].forEach(function (event) { form.addEventListener(event, update); });
    update();
  }
  function boot() { document.querySelectorAll('[data-location-resolution]').forEach(init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
