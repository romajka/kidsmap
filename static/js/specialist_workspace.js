/* Presentation/accessibility only; all permissions and validation remain on the server. */
(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.km-specialist-owner-form');
    if (!form) return;
    form.querySelectorAll('label').forEach(function (label) {
      const field = label.querySelector('input:not([type=hidden]),select,textarea');
      if (!field || !field.id) return;
      const errors = Array.from(label.querySelectorAll('.auth-field-error'));
      if (errors.length) {
        const ids = errors.map(function (error, index) {
          error.id = field.id + '-error-' + index;
          return error.id;
        });
        field.setAttribute('aria-invalid', 'true');
        field.setAttribute('aria-describedby', ids.join(' '));
      }
    });
    const tabs = Array.from(form.querySelectorAll('[data-owner-lang-tab]'));
    const panels = Array.from(form.querySelectorAll('[data-owner-lang-panel]'));
    tabs.forEach(function (tab, index) {
      const language = tab.dataset.ownerLangTab;
      const panel = panels.find(function (item) { return item.dataset.ownerLangPanel === language; });
      tab.id = 'bio-tab-' + language;
      tab.setAttribute('role', 'tab');
      if (panel) {
        panel.id = 'bio-panel-' + language;
        panel.setAttribute('role', 'tabpanel');
        panel.setAttribute('aria-labelledby', tab.id);
        tab.setAttribute('aria-controls', panel.id);
      }
      tab.addEventListener('keydown', function (event) {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next === undefined) return;
        event.preventDefault();
        tabs[next].click();
        tabs[next].focus();
      });
    });
    const invalidBio = panels.find(function (panel) { return panel.querySelector('.auth-field-error'); });
    if (invalidBio) {
      const tab = tabs.find(function (item) { return item.dataset.ownerLangTab === invalidBio.dataset.ownerLangPanel; });
      if (tab) tab.click();
    }
  });
})();
