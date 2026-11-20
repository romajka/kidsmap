(() => {
  'use strict';
  const timers = Array.from(document.querySelectorAll('[data-wait-elapsed]'), element => ({
    element,
    start: Date.parse(element.closest('dl').querySelector('time').dateTime),
  })).filter(timer => Number.isFinite(timer.start));
  if (!timers.length) return;

  const locale = document.documentElement.lang;
  const units = {};
  for (const unit of ['day', 'hour', 'minute']) {
    units[unit] = new Intl.NumberFormat(locale, {style: 'unit', unit, unitDisplay: 'short'});
  }

  function duration(minutes, underMinute) {
    if (minutes < 1) return underMinute;
    const days = Math.floor(minutes / 1440);
    const hours = Math.floor(minutes / 60) % 24;
    const remainder = minutes % 60;
    if (days) return [units.day.format(days), hours && units.hour.format(hours)].filter(Boolean).join(' ');
    if (hours) return [units.hour.format(hours), remainder && units.minute.format(remainder)].filter(Boolean).join(' ');
    return units.minute.format(minutes);
  }

  let timeout;
  function update() {
    clearTimeout(timeout);
    if (document.hidden) return;
    const now = Date.now();
    let delay = 60000;
    for (const {element, start} of timers) {
      const elapsed = Math.max(0, now - start);
      const text = duration(Math.floor(elapsed / 60000), element.dataset.underMinute);
      if (element.textContent !== text) element.textContent = text;
      delay = Math.min(delay, 60000 - elapsed % 60000);
    }
    timeout = setTimeout(update, delay);
  }
  document.addEventListener('visibilitychange', update);
  window.addEventListener('pageshow', update);
  update();
})();
