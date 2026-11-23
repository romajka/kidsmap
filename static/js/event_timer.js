/* KidsMap afisha countdown: one shared ticker for every [data-km-timer] on the page.
   Phases: upcoming (>24h) · soon (<24h) · running (counts to the end) · ended.
   Each digit rolls like a slot counter when it changes; the seconds tile shows
   how much of the minute has passed; under an hour the timer turns "urgent". */
(function () {
  'use strict';
  var DAY = 86400000, HOUR = 3600000;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var timers = [];

  function pad(n) { return n < 10 ? '0' + n : String(n); }

  function digitize(num) {
    // "05" -> <span class="km-timer__digit"><i>0</i></span><span …><i>5</i></span>
    var text = (num.textContent || '').trim() || '00';
    num.textContent = '';
    var digits = [];
    for (var i = 0; i < text.length; i++) {
      var d = document.createElement('span');
      d.className = 'km-timer__digit';
      var face = document.createElement('i');
      face.textContent = text.charAt(i);
      d.appendChild(face);
      num.appendChild(d);
      digits.push(d);
    }
    return digits;
  }

  function roll(digit, value) {
    var current = digit.lastElementChild;
    if (current && current.textContent === value) return;
    if (reduce || !current) {
      digit.textContent = '';
      var only = document.createElement('i');
      only.textContent = value;
      digit.appendChild(only);
      return;
    }
    // Drop faces left over from a roll that is still running.
    while (digit.children.length > 1) digit.removeChild(digit.firstElementChild);
    var next = document.createElement('i');
    next.textContent = value;
    next.className = 'is-in';
    current.className = 'is-out';
    digit.appendChild(next);
    setTimeout(function () { if (current.parentNode === digit) digit.removeChild(current); next.className = ''; }, 460);
  }

  function setDigits(seg, text) {
    if (seg.digits.length !== text.length) {  // e.g. 99 -> 100 days: rebuild the tiles
      seg.num.textContent = text;
      seg.digits = digitize(seg.num);
      return;
    }
    for (var i = 0; i < text.length; i++) roll(seg.digits[i], text.charAt(i));
  }

  function setup(root) {
    if (root.__kmTimer) return;
    var start = Date.parse(root.dataset.start);
    var end = Date.parse(root.dataset.end);
    if (isNaN(start) || isNaN(end)) return;
    var segs = {};
    Array.prototype.forEach.call(root.querySelectorAll('[data-unit]'), function (seg) {
      var num = seg.querySelector('.km-timer__num');
      segs[seg.dataset.unit] = { seg: seg, num: num, digits: digitize(num) };
    });
    // blinking colons between the tiles
    var tiles = root.querySelectorAll('.km-timer__seg');
    for (var i = 0; i < tiles.length - 1; i++) {
      var colon = document.createElement('span');
      colon.className = 'km-timer__colon';
      colon.setAttribute('aria-hidden', 'true');
      colon.textContent = ':';
      tiles[i].after(colon);
    }
    root.classList.add('is-live');
    root.__kmTimer = { root: root, start: start, end: end, segs: segs, label: root.querySelector('[data-km-timer-label]'), short: root.querySelector('[data-km-timer-short]') };
    timers.push(root.__kmTimer);
  }

  function phaseOf(t, now) {
    if (now >= t.end) return 'ended';
    if (now >= t.start) return 'running';
    return t.start - now <= DAY ? 'soon' : 'upcoming';
  }

  function render(t, now) {
    var phase = phaseOf(t, now);
    var root = t.root;
    if (root.dataset.state !== phase) {
      root.dataset.state = phase;
      if (t.label) t.label.textContent = root.dataset['l' + phase.charAt(0).toUpperCase() + phase.slice(1)] || '';
      if (t.short) t.short.textContent = root.dataset['s' + phase.charAt(0).toUpperCase() + phase.slice(1)] || '';
      var card = root.closest('[data-event-card]');
      if (card) card.dataset.phase = phase;
    }
    if (phase === 'ended') return;
    var target = phase === 'running' ? t.end : t.start;
    var leftMs = Math.max(0, target - now);
    var left = Math.floor(leftMs / 1000);
    var values = { d: Math.floor(left / 86400), h: Math.floor(left % 86400 / 3600), m: Math.floor(left % 3600 / 60), s: left % 60 };
    root.classList.toggle('is-urgent', phase !== 'running' && leftMs < HOUR);
    // seconds tile: share of the current minute that has passed (0..1)
    root.style.setProperty('--km-sec', ((60 - values.s) % 60 / 60).toFixed(3));
    // whole-event progress for running events (0..1)
    if (phase === 'running') root.style.setProperty('--km-run', Math.min(1, (now - t.start) / Math.max(1, t.end - t.start)).toFixed(3));
    Object.keys(values).forEach(function (unit) {
      var s = t.segs[unit];
      if (!s) return;
      if (unit === 'd') s.seg.classList.toggle('is-zero', values.d === 0);
      setDigits(s, pad(values[unit]));
    });
  }

  function tick() {
    var now = Date.now();
    for (var i = 0; i < timers.length; i++) {
      if (timers[i].root.isConnected) render(timers[i], now);
    }
  }

  function scan(scope) {
    Array.prototype.forEach.call((scope || document).querySelectorAll('[data-km-timer]'), setup);
    tick();
  }

  var started = false;
  function boot() {
    scan(document);
    if (started) return;
    started = true;
    // Align ticks to wall-clock seconds so all timers roll together.
    setTimeout(function () { tick(); setInterval(tick, 1000); }, 1000 - (Date.now() % 1000));
  }

  window.KidsMapTimers = { scan: scan };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
