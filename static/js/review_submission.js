/* Progressive enhancement: the same endpoints still support ordinary POST/redirect. */
(function () {
  "use strict";
  document.querySelectorAll("[data-review-submission]").forEach(function (form) {
    const section = form.closest("section");
    const feedback = section && section.querySelector("[data-review-feedback]");
    if (!feedback) return;
    const composer = form.closest("[data-review-composer]") || form;
    const live = feedback.querySelector("[data-review-live]");
    let busy = false;
    let submitted = false;
    const cooldown = section.querySelector("[data-review-cooldown]");
    let cooldownInterval;
    function showCooldown(payload) {
      if (!cooldown || !payload || !payload.active) return false;
      const duration = Math.max(1, Number(payload.duration_seconds) || 120);
      const remainingMs = Date.parse(payload.next_allowed_at) - Date.parse(payload.server_now);
      if (!Number.isFinite(remainingMs) || remainingMs <= 0) return false;
      const started = performance.now();
      window.clearInterval(cooldownInterval);
      cooldown.hidden = false;
      composer.hidden = true;
      submitted = true;
      const count = cooldown.querySelector("[data-review-countdown]");
      const progress = cooldown.querySelector("[data-review-cooldown-progress]");
      progress.max = duration;
      function tick() {
        // Calibrated against server time; changing the computer clock cannot skip the wait.
        const seconds = Math.max(0, Math.ceil((remainingMs - (performance.now() - started)) / 1000));
        count.textContent = String(Math.floor(seconds / 60)).padStart(2, "0") + ":" + String(seconds % 60).padStart(2, "0");
        progress.value = Math.min(duration, seconds);
        if (seconds === 0) {
          window.clearInterval(cooldownInterval);
          cooldown.hidden = true;
          composer.hidden = false;
          submitted = false;
          if (live.dataset.validation === "cooldown") {
            live.hidden = true;
            delete live.dataset.validation;
          }
          feedback.querySelectorAll("[data-review-notice].flash-warning").forEach(function (item) { item.remove(); });
          const button = form.querySelector('[type="submit"]');
          if (button) button.disabled = false;
          form.dispatchEvent(new Event("review:state-change"));
        }
      }
      tick();
      cooldownInterval = window.setInterval(tick, 250);
      return true;
    }

    function notify(message, title, ok, options) {
      const config = options || {};
      const variant = config.variant || (ok ? "success" : "error");
      feedback.querySelectorAll("[data-review-notice]").forEach(function (item) { item.remove(); });
      live.className = "flash-message flash-" + variant;
      live.setAttribute("role", ok ? "status" : "alert");
      live.setAttribute("aria-live", ok ? "polite" : "assertive");
      const heading = live.querySelector("[data-review-title]");
      heading.textContent = title || "";
      heading.hidden = !title;
      live.querySelector("[data-review-message]").textContent = (title ? " " : "") + message;
      live.querySelector("[data-review-icon]").setAttribute("d", ok ? "m7 12 3 3 7-7" : "M12 7v6m0 3v1");
      live.hidden = false;
      const focusTarget = config.focusTarget || live;
      focusTarget.focus({ preventScroll: true });
      focusTarget.scrollIntoView({ block: "nearest", behavior: "auto" });
      window.dispatchEvent(new CustomEvent("kidsmap:notification", {
        detail: { message: title ? title + "\n" + message : message, variant: variant, duration: 9000 }
      }));
    }

    const initial = feedback.querySelector("[data-review-notice]");
    if (initial) {
      if (initial.classList.contains("flash-success")) {
        submitted = true;
        composer.hidden = true;
      }
      initial.focus({ preventScroll: true });
      window.dispatchEvent(new CustomEvent("kidsmap:notification", {
        detail: { message: initial.innerText, variant: submitted ? "success" : "error", duration: 9000 }
      }));
    }

    if (cooldown) {
      const active = showCooldown({
        active: true,
        next_allowed_at: cooldown.dataset.nextAllowedAt,
        server_now: cooldown.dataset.serverNow,
        duration_seconds: cooldown.dataset.durationSeconds
      });
      if (!active) {
        cooldown.hidden = true;
        composer.hidden = false;
        submitted = false;
      }
    }

    const ratingInput = form.querySelector("[data-review-rating-input]");
    const ratingGroup = form.querySelector("[data-review-stars] [role=radiogroup], fieldset[data-review-stars]");
    const loginLink = section.querySelector("[data-review-login]");
    function hasRating() {
      const selected = ratingInput && ratingInput.type === "radio"
        ? form.querySelector('input[type="radio"][name="rating"][data-review-rating-input]:checked')
        : ratingInput;
      const value = Number(selected && selected.value);
      return Number.isInteger(value) && value >= 1 && value <= 5;
    }
    form.addEventListener("change", function () {
      if (ratingGroup && hasRating()) {
        ratingGroup.removeAttribute("aria-invalid");
        if (live.dataset.validation === "rating") {
          live.hidden = true;
          delete live.dataset.validation;
        }
      }
    });

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      if (busy || submitted) return;
      if (ratingInput && !hasRating()) {
        if (ratingGroup) ratingGroup.setAttribute("aria-invalid", "true");
        live.dataset.validation = "rating";
        notify(feedback.dataset.ratingRequired, "", false, {
          variant: "warning",
          focusTarget: form.querySelector('[data-review-stars] input[type="radio"], [data-review-stars] [role=radio]')
        });
        return;
      }
      delete live.dataset.validation;
      const data = new FormData(form);
      // Login in another tab rotates Django's CSRF token; keep the current draft.
      const csrfCookie = document.cookie.split(";").map(function (item) { return item.trim(); })
        .find(function (item) { return item.startsWith("csrftoken="); });
      if (csrfCookie && data.has("csrfmiddlewaretoken")) {
        try { data.set("csrfmiddlewaretoken", decodeURIComponent(csrfCookie.slice(10))); } catch (_) { /* Keep the form token. */ }
      }
      const button = event.submitter || form.querySelector('[type="submit"]');
      const originalContent = button ? Array.from(button.childNodes) : [];
      busy = true;
      form.setAttribute("aria-busy", "true");
      if (button) { button.disabled = true; button.textContent = feedback.dataset.sending; }
      form.dispatchEvent(new Event("review:state-change"));
      const controller = new AbortController();
      const timeout = window.setTimeout(function () { controller.abort(); }, 30000);
      try {
        const response = await fetch(form.action, {
          method: "POST", mode: "same-origin", body: data, credentials: "same-origin", signal: controller.signal,
          headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" }
        });
        let payload;
        try { payload = await response.json(); } catch (_) { payload = null; }
        if (!response.ok || !payload || payload.ok !== true) {
          if (loginLink && (response.status === 401 || (payload && payload.auth_required === true))) {
            loginLink.hidden = false;
          }
          const limited = response.status === 429 && payload && payload.code === "review_cooldown";
          notify((response.status < 500 && payload && payload.message) || feedback.dataset.serverError, "", false,
            limited ? { variant: "warning" } : undefined);
          if (limited) {
            live.dataset.validation = "cooldown";
            showCooldown(payload.cooldown);
          }
          return;
        }
        submitted = true;
        if (loginLink) loginLink.hidden = true;
        form.reset();
        composer.hidden = true;
        notify(payload.message, payload.title, true);
        showCooldown(payload.cooldown);
      } catch (_) {
        notify(feedback.dataset.networkError, "", false);
      } finally {
        window.clearTimeout(timeout);
        busy = false;
        form.removeAttribute("aria-busy");
        if (button) { button.disabled = submitted; button.replaceChildren(...originalContent); }
        form.dispatchEvent(new Event("review:state-change"));
      }
    });
  });
})();
