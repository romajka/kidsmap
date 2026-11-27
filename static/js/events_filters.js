(function () {
  'use strict';
  const form = document.querySelector('.events-filters__body');
  if (!form) return;
  const period = form.elements.namedItem('date_filter');
  const dates = ['date_from', 'date_to'].map(name => form.elements.namedItem(name));
  // A quick period and a custom range are alternative ways of choosing dates.
  period?.addEventListener('change', () => { if (period.value) dates.forEach(input => { input.value = ''; }); });
  dates.forEach(input => input?.addEventListener('change', () => { if (input.value && period) period.value = ''; }));
  const age = form.elements.namedItem('age');
  const bounds = ['age_from', 'age_to'].map(name => form.elements.namedItem(name));
  age?.addEventListener('input', () => { if (age.value) bounds.forEach(input => { input.value = ''; }); });
  bounds.forEach(input => input?.addEventListener('input', () => { if (input.value && age) age.value = ''; }));
})();
