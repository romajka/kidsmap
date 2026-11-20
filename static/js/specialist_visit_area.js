(function () {
  'use strict';

  function init(area) {
    var form = area.closest('form');
    var region = area.querySelector('[name="visit_region"]');
    var whole = area.querySelector('[name="visit_citywide"]');
    var districts = area.querySelector('[data-visit-districts]');
    var empty = area.querySelector('[data-visit-no-districts]');
    if (!form || !region || !whole || !districts) return;

    function sync() {
      var enabled = Boolean(form.querySelector('[name="session_formats"][value="visit"]:checked'));
      area.hidden = !enabled;
      area.disabled = !enabled;
      districts.hidden = !region.value || whole.checked;
      districts.disabled = districts.hidden;
      var matches = 0;
      districts.querySelectorAll('input[name="visit_districts"]').forEach(function (input) {
        var sameRegion = Boolean(region.value && input.dataset.region === region.value);
        input.closest('label').hidden = !sameRegion;
        input.disabled = !sameRegion;
        if (sameRegion) matches++;
        else input.checked = false;
      });
      if (empty) empty.hidden = matches > 0;
    }

    sync();
    form.addEventListener('change', sync);
    window.addEventListener('pageshow', sync);
  }

  document.querySelectorAll('[data-specialist-visit-area]').forEach(init);
})();
