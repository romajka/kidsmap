/* Public site-settings input recovery. No tokens, credentials or files. */
(function () {
  "use strict";
  function init() {
    const form = document.querySelector("form[data-settings-draft-owner]");
    const notice = form && form.querySelector("[data-settings-draft-notice]");
    if (!form || !notice) return;
    const owner = form.dataset.settingsDraftOwner;
    if (!owner) return;
    const key = "km-settings-draft:v1:" + owner + ":" + location.pathname;
    const ttl = 30 * 60 * 1000;
    const maxBytes = 250000;
    const allowed = new Set([
      "brand_name", "home_hero_show_decor", "home_recommendations_limit",
      "footer_phone", "footer_email", "footer_instagram", "footer_telegram",
      "footer_youtube", "footer_tiktok", "footer_facebook", "footer_linkedin", "footer_whatsapp",
      "events_section_enabled", "specialists_section_enabled", "organizations_section_enabled",
      "public_favorites_count_enabled", "public_favorites_minimum"
    ]);
    for (const prefix of ["home_title", "home_subtitle", "home_search_label", "home_search_placeholder", "home_cta_text", "about_text", "contacts_text", "empty_results_text"]) {
      for (const lang of ["az", "ru", "en"]) allowed.add(prefix + "_" + lang);
    }
    const controls = Array.from(form.elements).filter(el => allowed.has(el.name) && !el.disabled &&
      (el.tagName === "TEXTAREA" || ["text", "email", "tel", "url", "number", "checkbox"].includes(el.type)));
    if (!controls.length) return;
    const byName = new Map(controls.map(el => [el.name, el]));
    let restoring = false;
    const collect = () => Object.fromEntries(controls.map(el => [el.name, el.type === "checkbox" ? el.checked : el.value]));
    const remove = () => { try { sessionStorage.removeItem(key); } catch (_) {} notice.hidden = true; };
    const same = (a, b) => Object.keys(a).length === Object.keys(b).length && Object.keys(a).every(name =>
      typeof a[name] === "string" ? typeof b[name] === "string" && a[name].trim() === b[name].trim() : a[name] === b[name]);
    function read() {
      try {
        const raw = sessionStorage.getItem(key);
        if (!raw) return null;
        if (raw.length > maxBytes) { remove(); return null; }
        const record = JSON.parse(raw);
        if (record.version !== 1 || !Number.isFinite(record.savedAt) || record.savedAt > Date.now() + 60000 || Date.now() - record.savedAt > ttl ||
            !record.fields || Array.isArray(record.fields) || typeof record.fields !== "object" || !Object.keys(record.fields).length ||
            Object.keys(record.fields).some(name => !byName.has(name) || typeof record.fields[name] !== (byName.get(name).type === "checkbox" ? "boolean" : "string"))) {
          remove(); return null;
        }
        return record;
      } catch (_) { remove(); return null; }
    }
    function persist() {
      if (restoring) return;
      try {
        const raw = JSON.stringify({ version: 1, savedAt: Date.now(), fields: collect() });
        if (raw.length <= maxBytes) sessionStorage.setItem(key, raw);
      } catch (_) { /* Storage failure must never block normal native saving. */ }
    }
    const stored = read();
    if (stored) {
      const matching = same(stored.fields, collect());
      if (matching && form.dataset.settingsDraftCanClear === "true") remove();
      else if (!matching) notice.hidden = false;
    }
    controls.forEach(el => { el.addEventListener("input", persist); el.addEventListener("change", persist); });
    form.addEventListener("submit", persist, true);
    notice.querySelector("[data-settings-draft-discard]").addEventListener("click", remove);
    notice.querySelector("[data-settings-draft-restore]").addEventListener("click", function () {
      const record = read();
      if (!record) return;
      restoring = true;
      let first = null;
      for (const [name, value] of Object.entries(record.fields)) {
        const el = byName.get(name);
        if (!first && (el.type === "checkbox" ? el.checked !== value : el.value !== value)) first = el;
        if (el.type === "checkbox") el.checked = value; else el.value = value;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
      }
      restoring = false;
      notice.hidden = true;
      persist();
      if (first) first.focus();
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
}());
