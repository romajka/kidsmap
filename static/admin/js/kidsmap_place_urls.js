(function () {
  'use strict';
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-place-localized-urls]').forEach(function (block) {
      var status = block.querySelector('[data-url-status]');
      var list = block.querySelector('[data-url-list]');
      var labels = block.dataset;
      var sequence = 0;
      var timer;
      async function refresh() {
        var current = ++sequence;
        var payload = {};
        var token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (block.dataset.placePk) payload.pk = block.dataset.placePk;
        ['az', 'ru', 'en'].forEach(function (language) {
          var field = document.getElementById('id_name_' + language);
          payload['name_' + language] = field ? field.value : '';
        });
        status.textContent = labels.labelLoading;
        try {
          var response = await fetch(block.dataset.previewUrl, {
            method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': token ? token.value : ''},
            body: JSON.stringify(payload)
          });
          if (!response.ok) throw new Error('preview');
          var data = await response.json();
          if (current !== sequence) return;
          list.replaceChildren();
          ['az', 'ru', 'en'].forEach(function (language) {
            var item = data.urls[language];
            var title = document.createElement('dt');
            title.textContent = language.toUpperCase();
            var detail = document.createElement('dd');
            var text = document.createElement('code');
            text.textContent = item.path || item.slug || labels.labelEmpty;
            detail.appendChild(text);
            if (item.path) {
              var copy = document.createElement('button');
              copy.type = 'button';
              copy.className = 'km-pf-btn km-pf-btn--ghost';
              copy.textContent = labels.labelCopy;
              copy.setAttribute('aria-label', labels.labelCopyLabel + ' ' + language.toUpperCase());
              copy.addEventListener('click', async function () {
                try {
                  await navigator.clipboard.writeText(item.url);
                  status.textContent = labels.labelCopied;
                } catch (error) { status.textContent = labels.labelCopyError; }
              });
              detail.appendChild(copy);
              if (data.public) {
                var link = document.createElement('a');
                link.href = item.url;
                link.target = '_blank';
                link.rel = 'noopener';
                link.textContent = labels.labelOpen + ' ' + language.toUpperCase();
                detail.appendChild(link);
              }
            }
            list.append(title, detail);
          });
          status.textContent = payload.pk ? labels.labelSaved : labels.labelNew;
        } catch (error) {
          if (current === sequence) status.textContent = labels.labelError;
        }
      }
      ['az', 'ru', 'en'].forEach(function (language) {
        var field = document.getElementById('id_name_' + language);
        if (field) ['input', 'change'].forEach(function (event) {
          field.addEventListener(event, function () { clearTimeout(timer); timer = setTimeout(refresh, 300); });
        });
      });
      refresh();
    });
  });
}());
