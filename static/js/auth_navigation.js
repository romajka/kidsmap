(function () {
  document.querySelectorAll('form[data-auth-navigation]').forEach(function (form) {
    form.addEventListener('submit', function () {
      // Another tab may have logged in and rotated Django's CSRF cookie.
      const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]');
      const cookie = document.cookie.split(';').map(function (item) { return item.trim(); })
        .find(function (item) { return item.startsWith('csrftoken='); });
      if (csrf && cookie) {
        try { csrf.value = decodeURIComponent(cookie.slice(10)); } catch (_) { /* Keep the form token. */ }
      }
      if (!form.hasAttribute('data-preserve-current-hash')) return;
      const next = form.querySelector('input[name="next"]');
      if (!next || !next.value) return;
      try {
        const target = new URL(next.value, window.location.origin);
        if (target.origin !== window.location.origin) return;
        target.hash = window.location.hash;
        next.value = target.pathname + target.search + target.hash;
      } catch (_) { /* The server validates the original return target. */ }
    });
  });
})();
