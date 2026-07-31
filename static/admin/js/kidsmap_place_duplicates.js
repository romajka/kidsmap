(() => {
  const form = document.querySelector("[data-duplicate-candidates-url]");
  const alert = document.querySelector("[data-place-duplicate-alert]");
  if (!form || !alert) return;

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
  const fields = ["phone1", "website", "instagram", "address"]
    .map((name) => form.elements.namedItem(name))
    .filter(Boolean);
  if (!endpoint || !fields.length) return;

  let timer;
  let lastRequest = "";

  const hide = () => {
    alert.hidden = true;
    alert.replaceChildren();
  };

  const render = (results) => {
    if (!results.length) return hide();
    const heading = document.createElement("strong");
    heading.textContent = "Проверьте возможные дубли";
    const text = document.createElement("p");
    text.textContent = "Совпали контакты или адрес. Это может быть тот же объект или его филиал.";
    const list = document.createElement("ul");
    results.forEach((result) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = result.url;
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = result.title || `Карточка #${result.id}`;
      item.append(link, document.createTextNode(` — совпали: ${result.matched.join(", ")}`));
      if (result.address) item.append(document.createTextNode(` (${result.address})`));
      list.append(item);
    });
    alert.replaceChildren(heading, text, list);
    alert.hidden = false;
  };

  const check = async () => {
    const params = new URLSearchParams({ exclude: form.dataset.duplicateExclude || "" });
    const phone = form.elements.namedItem("phone1")?.value.trim();
    const website = form.elements.namedItem("website")?.value.trim();
    const instagram = form.elements.namedItem("instagram")?.value.trim();
    const address = form.elements.namedItem("address")?.value.trim();
    if (phone) params.set("phone", phone);
    if (website) params.set("website", website);
    if (instagram) params.set("instagram", instagram);
    if (address && address.length >= 8) params.set("address", address);
    if ([...params.keys()].filter((key) => key !== "exclude").length === 0) return hide();

    const requestKey = params.toString();
    if (requestKey === lastRequest) return;
    lastRequest = requestKey;
    try {
      const response = await fetch(`${endpoint}?${requestKey}`, { credentials: "same-origin" });
      if (!response.ok) return;
      const payload = await response.json();
      if (requestKey === lastRequest) render(payload.results || []);
    } catch (_) {
      // Duplicate hints must never prevent an editor from completing a form.
    }
  };

  fields.forEach((field) => {
    field.addEventListener("input", () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(check, 500);
    });
    field.addEventListener("blur", check);
  });
})();
