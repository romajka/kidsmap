(function () {
  "use strict";
  const form = document.querySelector("[data-duplicate-candidates-url]");
  const alert = document.querySelector("[data-place-duplicate-alert]");
  if (!form || !alert) return;
  alert.setAttribute("aria-live", "polite");
  const defaults = {
    title: "Проверка дублей", not_found: "Совпадений в доступных версиях не найдено.",
    scope_hint: "Проверены только доступные вам записи. Личные черновики других пользователей исключены.",
    checking: "Проверяем доступные версии…", failed: "Проверка дублей не выполнена.",
    retry: "Повторить проверку", show_all: "Все результаты и версии", generated: "Срез данных", results: "Совпадений"
  };
  let localized = {};
  try { localized = JSON.parse(document.getElementById("km-identity-copy")?.textContent || "{}"); } catch (_) {}
  const ui = { ...defaults, ...localized };
  const ageOpenEnded = form.elements.namedItem("age_open_ended");
  const ageTo = form.elements.namedItem("age_to");
  if (ageOpenEnded && ageTo) {
    const syncAgeFields = () => {
      ageTo.disabled = ageOpenEnded.checked;
      ageTo.closest(".form-row, .km-place-form-field")?.classList.toggle("is-disabled", ageOpenEnded.checked);
      if (ageOpenEnded.checked) ageTo.value = "";
    };
    ageOpenEnded.addEventListener("change", syncAgeFields);
    syncAgeFields();
  }

  const endpoint = form.dataset.duplicateCandidatesUrl;
  if (!endpoint) return;
  const names = ["name_az", "name_ru", "name_en", "phone1", "phone2", "phone3", "website", "instagram", "address", "lat", "lng", "public_links"];
  const fields = names.map(name => form.elements.namedItem(name)).filter(Boolean);
  let timer, generation = 0, lastSuccessKey = "", pending;
  const safeLink = (url, label) => {
    const link = document.createElement("a");
    try {
      const target = new URL(url, window.location.href);
      if (target.origin !== window.location.origin || !/^https?:$/.test(target.protocol)) return document.createTextNode(label);
      link.href = target.pathname + target.search;
    } catch (_) { return document.createTextNode(label); }
    link.target = "_blank"; link.rel = "noopener"; link.textContent = label;
    return link;
  };
  const paragraph = text => { const node = document.createElement("p"); node.textContent = text; return node; };
  const footer = (payload = {}) => {
    const scope = paragraph(ui.scope_hint);
    if (payload.generated_at) scope.append(document.createTextNode(` ${ui.generated}: ${payload.generated_at}`));
    alert.append(scope);
    const retry = document.createElement("button"); retry.type = "button"; retry.dataset.identityRetry = "";
    retry.textContent = ui.retry; retry.addEventListener("click", () => { generation++; check(true); });
    alert.append(retry, document.createTextNode(" · "), safeLink(payload.registry_url || localized.registry_url || "/admin/catalog/place/duplicate-registry/", ui.show_all));
  };
  const show = payload => {
    alert.replaceChildren(); alert.hidden = false; alert.removeAttribute("aria-busy");
    const rows = payload.results || [];
    if (!rows.length) alert.append(paragraph(ui.not_found));
    else {
      const heading = document.createElement("strong"); heading.textContent = ui.title; alert.append(heading);
      alert.append(paragraph(`${ui.results}: ${rows.length} / ${payload.total ?? rows.length}`));
      const list = document.createElement("ul");
      rows.forEach(row => {
        const item = document.createElement("li");
        item.append(safeLink(row.compare_url || row.url, row.title || `#${row.id}`));
        if (row.classification_label) item.append(document.createTextNode(` — ${row.classification_label}`));
        if (row.address) item.append(document.createTextNode(` (${row.address})`));
        (row.evidence || []).forEach(e => item.append(paragraph(`${e.source_label || e.source} · v${e.version}: ${e.signal_labels || e.signals?.join(", ") || ""}`)));
        list.append(item);
      });
      alert.append(list);
    }
    footer(payload);
  };
  const check = async (force = false) => {
    const params = new URLSearchParams({ exclude: form.dataset.duplicateExclude || "", page_size: "8" });
    let entered = false;
    fields.forEach(field => {
      const value = field.value.trim();
      if (!value) return;
      if (field.name === "public_links") {
        try { if (!JSON.parse(value)?.length) return; } catch (_) {}
      }
      params.set(field.name, value); entered = true;
    });
    const ownDraft = form.elements.namedItem("server_draft_id")?.value;
    if (ownDraft) params.set("exclude_draft_id", ownDraft);
    if (!entered) { pending?.abort(); alert.hidden = true; alert.replaceChildren(); lastSuccessKey = ""; return; }
    const key = params.toString(), current = generation;
    if (!force && key === lastSuccessKey) return;
    pending?.abort(); pending = new AbortController();
    alert.replaceChildren(paragraph(ui.checking)); alert.hidden = false; alert.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(`${endpoint}?${key}`, { credentials: "same-origin", signal: pending.signal });
      if (!response.ok) throw new Error("duplicate-check-failed");
      const payload = await response.json();
      if (!payload.coverage || payload.decision === "not_checked") throw new Error("missing-coverage");
      if (current === generation) { lastSuccessKey = key; show(payload); }
    } catch (error) {
      if (current !== generation || error.name === "AbortError") return;
      lastSuccessKey = ""; alert.replaceChildren(paragraph(ui.failed)); alert.hidden = false;
      alert.removeAttribute("aria-busy"); footer();
    }
  };
  fields.forEach(field => {
    field.addEventListener("input", () => { generation++; lastSuccessKey = ""; window.clearTimeout(timer); timer = window.setTimeout(() => check(), 500); });
    field.addEventListener("blur", () => { generation++; window.clearTimeout(timer); check(); });
    field.addEventListener("change", () => { generation++; lastSuccessKey = ""; check(); });
  });
  check();
})();
