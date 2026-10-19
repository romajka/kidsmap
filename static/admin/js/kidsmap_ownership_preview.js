(function () {
  'use strict';
  var root = document.getElementById('km-inspection');
  if (!root) return;
  root.querySelectorAll('[data-preview-controls]').forEach(function (element) { element.hidden = false; });
  root.querySelectorAll('[data-preview-filter]').forEach(function (button) {
    button.addEventListener('click', function () {
      var language = button.getAttribute('data-preview-filter');
      root.querySelectorAll('[data-preview-language]').forEach(function (block) {
        block.hidden = language !== 'all' && block.getAttribute('data-preview-language') !== language;
      });
      root.querySelectorAll('[data-preview-filter]').forEach(function (control) {
        control.setAttribute('aria-pressed', control === button ? 'true' : 'false');
      });
    });
  });
  var currentLanguage = document.documentElement.lang.split('-')[0];
  var languageControl = root.querySelector('[data-preview-filter="' + currentLanguage + '"]');
  if (languageControl) languageControl.click();
  var expand = root.querySelector('[data-preview-expand]');
  expand.addEventListener('click', function () {
    var details = Array.from(root.querySelectorAll('[data-preview-details]'));
    var open = details.some(function (element) { return !element.open; });
    details.forEach(function (element) { element.open = open; });
    expand.querySelector('[data-expand-label]').textContent = expand.getAttribute(open ? 'data-collapse-label' : 'data-expand-label');
  });
  var navigation = root.querySelector('.km-inspection-sections');
  if (navigation && 'IntersectionObserver' in window) {
    var navLinks = Array.from(navigation.querySelectorAll('a'));
    var visible = new Map();
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { visible.set(entry.target.id, entry.isIntersecting); });
      var current = navLinks.find(function (link) { return visible.get(link.hash.slice(1)); });
      if (current) navLinks.forEach(function (link) {
        if (link === current) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }, {rootMargin: '-140px 0px -35% 0px'});
    navLinks.forEach(function (link) {
      var section = document.getElementById(link.hash.slice(1));
      if (section) observer.observe(section);
      link.addEventListener('click', function () {
        if (section) {
          section.setAttribute('tabindex', '-1');
          section.focus({preventScroll: true});
        }
      });
    });
  }
  var dialog = root.querySelector('[data-preview-dialog]');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  var links = Array.from(root.querySelectorAll('[data-preview-photo]'));
  var current = 0, opener = null;
  var image = dialog.querySelector('[data-preview-dialog-image]');
  var status = dialog.querySelector('[data-preview-photo-status]');
  function loaded() {
    image.style.visibility = 'visible'; status.hidden = true;
    dialog.setAttribute('aria-busy', 'false');
  }
  image.addEventListener('load', loaded);
  image.addEventListener('error', function () {
    status.textContent = dialog.getAttribute('data-error-label'); status.hidden = false;
    dialog.setAttribute('aria-busy', 'false');
  });
  function showPhoto(index) {
    current = (index + links.length) % links.length;
    var link = links[current];
    status.textContent = dialog.getAttribute('data-loading-label'); status.hidden = false;
    image.style.visibility = 'hidden'; dialog.setAttribute('aria-busy', 'true');
    image.src = link.href;
    if (image.complete && image.naturalWidth) loaded();
    image.alt = link.getAttribute('data-preview-caption') || '';
    dialog.querySelector('[data-preview-dialog-caption]').textContent = image.alt;
    dialog.querySelector('[data-preview-dialog-count]').textContent = (current + 1) + ' / ' + links.length;
    dialog.querySelectorAll('[data-preview-previous], [data-preview-next]').forEach(function (button) { button.disabled = links.length < 2; });
  }
  links.forEach(function (link, index) {
    link.addEventListener('click', function (event) {
      event.preventDefault(); opener = link; showPhoto(index); dialog.showModal();
      dialog.querySelector('[data-preview-close]').focus();
    });
  });
  dialog.querySelector('[data-preview-close]').addEventListener('click', function () { dialog.close(); });
  dialog.querySelector('[data-preview-previous]').addEventListener('click', function () { showPhoto(current - 1); });
  dialog.querySelector('[data-preview-next]').addEventListener('click', function () { showPhoto(current + 1); });
  dialog.addEventListener('keydown', function (event) {
    if (event.key === 'Tab') {
      var buttons = Array.from(dialog.querySelectorAll('button:not([disabled])'));
      var first = buttons[0], last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault(); showPhoto(current + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  dialog.addEventListener('click', function (event) {
    var rect = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
  });
  dialog.addEventListener('close', function () { if (opener) opener.focus(); });
})();
