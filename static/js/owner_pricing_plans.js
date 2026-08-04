(function () {
  const MAX_PRICING_PLANS = 20;
  const editor = document.querySelector("[data-tariff-editor]");
  if (!editor) return;
  const ownerForm = editor.closest("form");
  const input = editor.querySelector("[data-tariff-input]")
    || (ownerForm && ownerForm.querySelector("[data-tariff-input]"));
  const list = editor.querySelector("[data-tariff-list]");
  const add = editor.querySelector("[data-tariff-add]");
  const canVerify = editor.dataset.canVerify === "1";
  if (!input || !list || !add) return;

  const interfaceLanguage = (document.documentElement.lang || "ru").split("-")[0];
  const interfaceCopy = {
    az: {
      tariff: "Tarif", chooseType: "Növü seçin", noPrice: "Qiymət göstərilməyib",
      advanced: "Əlavə şərtlər", advancedHint: "auditoriya, müddət, tərcümələr, mənbə",
    },
    en: {
      tariff: "Plan", chooseType: "Choose a type", noPrice: "Price not specified",
      advanced: "Additional terms", advancedHint: "audience, validity, translations, source",
    },
    ru: {
      tariff: "Тариф", chooseType: "Выберите тип", noPrice: "Цена не указана",
      advanced: "Дополнительные условия", advancedHint: "аудитория, сроки, переводы, источник",
    },
  }[interfaceLanguage] || {
    tariff: "Тариф", chooseType: "Выберите тип", noPrice: "Цена не указана",
    advanced: "Дополнительные условия", advancedHint: "аудитория, сроки, переводы, источник",
  };
  const icons = {
    tag: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 13 13 20a2 2 0 0 1-3 0l-6-6a2 2 0 0 1 0-3V5a1 1 0 0 1 1-1h6a2 2 0 0 1 1 .5l8 8a1 1 0 0 1 0 1.5Z"/><circle cx="8" cy="8" r="1.5"/></svg>',
    sliders: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h10M18 7h2M4 17h2M10 17h10M14 4v6M6 14v6"/></svg>',
    language: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h9M8.5 3v2c0 5-2.5 8-5.5 10M6 10c1.5 2 3 3.5 5 4.5M14 20l3.5-9 3.5 9M15.3 17h4.4"/></svg>',
    up: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 14 5-5 5 5"/></svg>',
    down: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m7 10 5 5 5-5"/></svg>',
    trash: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M9 3h6l1 4H8l1-4ZM7 7l1 14h8l1-14M10 11v6M14 11v6"/></svg>',
  };

  function parsePlans(value) {
    try {
      const parsed = JSON.parse(value || "[]");
      if (!Array.isArray(parsed)) return [];
      return parsed
        .filter((plan) => plan && typeof plan === "object" && !Array.isArray(plan))
        .map((plan, index) => ({
          plan: plan,
          index: index,
          order: plan.sort_order !== null && plan.sort_order !== undefined && plan.sort_order !== ""
            && Number.isInteger(Number(plan.sort_order)) && Number(plan.sort_order) >= 0
            ? Number(plan.sort_order)
            : index,
        }))
        .sort((left, right) => left.order - right.order || left.index - right.index)
        .map((item) => item.plan);
    } catch (error) {
      return [];
    }
  }

  let plans = parsePlans(input.value);

  const labels = {
    format: editor.dataset.formatLabel || "Format",
    group: editor.dataset.groupLabel || "Group",
    individual: editor.dataset.individualLabel || "Individual",
    openVisit: editor.dataset.openVisitLabel || "Open visit",
    payment: editor.dataset.paymentLabel || "Payment",
    perLesson: editor.dataset.perLessonLabel || "Per lesson",
    perMonth: editor.dataset.perMonthLabel || "Per month",
    package: editor.dataset.packageLabel || "Package",
    perVisit: editor.dataset.perVisitLabel || "Per visit",
    entryTicket: editor.dataset.entryTicketLabel || "Entry ticket",
    week: editor.dataset.weekLabel || "Sessions/week",
    month: editor.dataset.monthLabel || "Sessions/month",
    packageSessions: editor.dataset.packageSessionsLabel || "Package sessions",
    price: editor.dataset.priceLabel || "Price",
    titleAz: editor.dataset.titleAzLabel || "Plan title (AZ)",
    titleRu: editor.dataset.titleRuLabel || "Plan title (RU)",
    titleEn: editor.dataset.titleEnLabel || "Plan title (EN)",
    active: editor.dataset.activeLabel || "Active",
    remove: editor.dataset.removeLabel || "Remove",
    up: editor.dataset.upLabel || "Move up",
    down: editor.dataset.downLabel || "Move down",
    addTranslation: editor.dataset.addTranslationLabel || "Добавить перевод (RU, EN)",
    egSessionsWeek: editor.dataset.egSessionsWeek || "например, 3",
    egSessionsMonth: editor.dataset.egSessionsMonth || "например, 12",
    egPackageSessions: editor.dataset.egPackageSessions || "например, 10",
    egPrice: editor.dataset.egPrice || "например, 120",
    choose: editor.dataset.chooseLabel || "Choose",
    kind: "Тип тарифа", priceKind: "Как указана цена", exact: "Точная", free: "Бесплатно",
    from: "От", range: "Диапазон", onRequest: "По запросу", priceMin: "Цена от", priceMax: "Цена до",
    billingMode: "Оплата", oneTime: "Разовая", recurring: "Регулярная", installment: "Частями",
    interval: "Период", intervalCount: "Количество периодов", cycles: "Количество платежей",
    quantity: "Количество", quantityUnit: "Единица", audience: "Аудитория", ageFrom: "Возраст от", ageTo: "Возраст до",
    conditionsAz: "Условия (AZ)", conditionsRu: "Условия (RU)", conditionsEn: "Условия (EN)", sourceUrl: "Источник",
    verifiedAt: "Подтверждено сотрудником",
    currency: "Валюта", unlimited: "Без ограничений", validity: "Срок действия", validityCount: "Срок",
    validFrom: "Действует с", validUntil: "Действует до", minPeople: "Минимум людей", maxPeople: "Максимум людей",
    dayType: "Дни", required: "Обязательный платёж",
  };

  const fields = [
    ["editor_kind", labels.kind, "select", [["admission", "Входной билет"], ["visit", "Разовое посещение"], ["lesson", "Одно занятие"], ["package", "Пакет занятий"], ["membership", "Абонемент"], ["course", "Курс или семестр"], ["camp", "Лагерь"], ["event", "Событие"], ["excursion", "Экскурсия"], ["tour", "Тур"], ["rental", "Аренда"], ["addon", "Дополнительная услуга"], ["registration_fee", "Регистрационный взнос"], ["deposit", "Депозит"]], true],
    ["title_az", labels.titleAz, "text", null, false],
    ["title_ru", labels.titleRu, "text", null, false],
    ["title_en", labels.titleEn, "text", null, false],
    ["lesson_format", labels.format, "select", [["group", labels.group], ["individual", labels.individual], ["open_visit", labels.openVisit]], true],
    ["billing_mode", labels.billingMode, "select", [["one_time", labels.oneTime], ["recurring", labels.recurring], ["installment", labels.installment]], true],
    ["billing_interval", labels.interval, "select", [["day", "День"], ["week", "Неделя"], ["month", "Месяц"], ["year", "Год"]], false],
    ["billing_interval_count", labels.intervalCount, "number", null, false],
    ["billing_cycles", labels.cycles, "number", null, false],
    ["price_kind", labels.priceKind, "select", [["exact", labels.exact], ["free", labels.free], ["from", labels.from], ["range", labels.range], ["on_request", labels.onRequest]], true],
    ["price", labels.price, "number", null, false],
    ["price_min", labels.priceMin, "number", null, false],
    ["price_max", labels.priceMax, "number", null, false],
    ["currency", labels.currency, "select", [["AZN", "AZN"], ["USD", "USD"], ["EUR", "EUR"], ["RUB", "RUB"]], true],
    ["quantity", labels.quantity, "number", null, false],
    ["quantity_unit", labels.quantityUnit, "select", [["entry", "Вход"], ["visit", "Посещение"], ["lesson", "Занятие"], ["minute", "Минута"], ["hour", "Час"], ["day", "День"], ["week", "Неделя"], ["month", "Месяц"], ["course", "Курс"], ["event", "Событие"], ["camp_shift", "Смена"], ["person", "Человек"], ["family", "Семья"], ["group", "Группа"]], false],
    ["sessions_per_week", labels.week, "number", null, false],
    ["sessions_per_month", labels.month, "number", null, false],
    ["is_unlimited", labels.unlimited, "checkbox", null, false],
    ["validity_interval", labels.validity, "select", [["day", "День"], ["week", "Неделя"], ["month", "Месяц"], ["year", "Год"]], false],
    ["validity_interval_count", labels.validityCount, "number", null, false],
    ["valid_from", labels.validFrom, "date", null, false], ["valid_until", labels.validUntil, "date", null, false],
    ["audience_type", labels.audience, "select", [["all", "Все"], ["child", "Дети"], ["adult", "Взрослые"], ["family", "Семья"], ["group", "Группа"]], false],
    ["age_from", labels.ageFrom, "number", null, false], ["age_to", labels.ageTo, "number", null, false],
    ["min_people", labels.minPeople, "number", null, false], ["max_people", labels.maxPeople, "number", null, false],
    ["day_type", labels.dayType, "select", [["any", "Любой день"], ["weekday", "Будни"], ["weekend", "Выходные"], ["holiday", "Праздники"]], false],
    ["is_required", labels.required, "checkbox", null, false],
    ["conditions_az", labels.conditionsAz, "text", null, false], ["conditions_ru", labels.conditionsRu, "text", null, false], ["conditions_en", labels.conditionsEn, "text", null, false],
    ["source_url", labels.sourceUrl, "url", null, false],
    ["verified_at", labels.verifiedAt, "datetime-local", null, false],
  ];

  function normalizeKind(plan) {
    if (!plan.editor_kind) {
      if (plan.payment_type === "package" || (plan.product_type === "lesson" && Number(plan.quantity) > 1)) plan.editor_kind = "package";
      else plan.editor_kind = plan.product_type || ({per_lesson:"lesson", per_month:"membership", per_visit:"visit", entry_ticket:"admission"}[plan.payment_type]) || "";
    }
    plan.product_type = plan.editor_kind === "package" ? "lesson" : plan.editor_kind;
    plan.charge_role = ["addon", "registration_fee", "deposit"].indexOf(plan.product_type) >= 0 ? plan.product_type : "primary";
    if (plan.editor_kind === "package") { plan.quantity_unit = "lesson"; if (!plan.quantity && plan.package_sessions) plan.quantity = plan.package_sessions; }
    if (!plan.price_kind) plan.price_kind = String(plan.price) === "0" ? "free" : "exact";
    if (!plan.billing_mode) plan.billing_mode = plan.payment_type === "per_month" ? "recurring" : "one_time";
    if (plan.billing_mode === "recurring" && !plan.billing_interval) { plan.billing_interval = "month"; plan.billing_interval_count = 1; }
    if (plan.price_kind === "exact") { plan.price_min = null; plan.price_max = null; }
    if (plan.price_kind === "free") { plan.price = "0"; plan.price_min = null; plan.price_max = null; }
    if (plan.price_kind === "from") { plan.price = null; plan.price_max = null; }
    if (plan.price_kind === "range") plan.price = null;
    if (plan.price_kind === "on_request") { plan.price = null; plan.price_min = null; plan.price_max = null; }
    if (plan.billing_mode === "recurring") plan.billing_cycles = null;
    else if (plan.billing_mode === "installment") { plan.billing_interval = ""; plan.billing_interval_count = null; }
    else { plan.billing_interval = ""; plan.billing_interval_count = null; plan.billing_cycles = null; }
    if (["package", "membership", "course", "camp"].indexOf(plan.editor_kind) < 0) {
      plan.validity_interval = ""; plan.validity_interval_count = null; plan.is_unlimited = false;
    }
    if (["addon", "registration_fee", "deposit"].indexOf(plan.editor_kind) < 0) plan.is_required = false;
    if (!plan.currency) plan.currency = "AZN";
    delete plan.payment_type; delete plan.package_sessions;
  }

  plans.forEach(normalizeKind);

  function sync() {
    plans.forEach((plan, index) => { plan.sort_order = index; });
    plans.forEach(normalizeKind);
    const contentKeys = ["editor_kind", "product_type", "price_kind", "price", "price_min", "price_max", "title_az", "title_ru", "title_en"];
    const cleanPlans = plans
      .filter((plan) => contentKeys.some((key) => plan[key] !== "" && plan[key] !== null && plan[key] !== undefined))
      .map((plan) => Object.fromEntries(Object.entries(plan).filter(([key]) => !key.startsWith("_"))));
    input.value = JSON.stringify(cleanPlans);
  }

  function addField(target, row, plan, key, label, type, options, required) {
    const wrapper = document.createElement("label");
    wrapper.className = "owner-tariff-field owner-tariff-field--" + key;
    var kind = plan.editor_kind || "";
    var priceKind = plan.price_kind || "exact";
    var billingMode = plan.billing_mode || "one_time";
    var lessonKinds = ["lesson", "package", "membership", "course"];
    var visible = true;
    if (key === "lesson_format") visible = lessonKinds.indexOf(kind) >= 0 || kind === "admission" || kind === "visit";
    if (["sessions_per_week", "sessions_per_month"].indexOf(key) >= 0) visible = lessonKinds.indexOf(kind) >= 0;
    if (["quantity", "quantity_unit"].indexOf(key) >= 0) visible = ["package", "rental", "camp", "course", "admission", "visit"].indexOf(kind) >= 0;
    if (["billing_interval", "billing_interval_count"].indexOf(key) >= 0) visible = billingMode === "recurring";
    if (key === "billing_cycles") visible = billingMode === "installment";
    if (key === "price") visible = priceKind === "exact";
    if (key === "price_min") visible = priceKind === "from" || priceKind === "range";
    if (key === "price_max") visible = priceKind === "range";
    if (key === "currency") visible = priceKind !== "free" && priceKind !== "on_request";
    if (["is_unlimited", "validity_interval", "validity_interval_count"].indexOf(key) >= 0) visible = ["package", "membership", "course", "camp"].indexOf(kind) >= 0;
    if (key === "is_required") visible = ["addon", "registration_fee", "deposit"].indexOf(kind) >= 0;
    if (key === "verified_at") visible = canVerify;
    wrapper.hidden = !visible;
    
    // Hide RU and EN translation fields by default if they are empty
    if ((key === "title_ru" || key === "title_en") && !plan[key] && !plan._show_translations) {
      wrapper.classList.add("owner-tariff-field--hidden");
    }

    const labelHtml = required ? label + ' <span style="display: inline; color: #ef4444; font-weight: bold;">*</span>' : label;
    wrapper.innerHTML = "<span>" + labelHtml + "</span>";
    
    let field;
    if (type === "select") {
      field = document.createElement("select");
      field.innerHTML = '<option value="">' + labels.choose + '</option>' + options.map((item) => '<option value="' + item[0] + '">' + item[1] + '</option>').join("");
    } else {
      field = document.createElement("input");
      field.type = type;
      if (type === "number") {
        const isMoney = ["price", "price_min", "price_max"].indexOf(key) >= 0;
        field.min = isMoney ? "0" : "1";
        field.step = isMoney ? "0.01" : "1";
      }
      const placeholders = {
        sessions_per_week: labels.egSessionsWeek,
        sessions_per_month: labels.egSessionsMonth,
        package_sessions: labels.egPackageSessions,
        price: labels.egPrice,
        title_az: "məsələn, Aylıq abunə (12 dərs)",
        title_ru: "например, Абонемент на месяц (12 занятий)",
        title_en: "e.g., Monthly subscription (12 sessions)",
      };
      if (placeholders[key]) {
        field.placeholder = placeholders[key];
      }
    }
    field.className = "field";
    field.required = !!required;
    if (type === "checkbox") field.checked = plan[key] === true;
    else field.value = plan[key] == null ? "" : (key === "verified_at" ? String(plan[key]).slice(0, 16) : plan[key]);
    field.dataset.tariffKey = key;
    field.addEventListener("input", () => {
      plan[key] = type === "checkbox" ? field.checked : field.value;
      sync();
      updateCardSummary(row, plan);
    });
    field.addEventListener("change", () => {
      plan[key] = type === "checkbox" ? field.checked : field.value;
      sync();

      // Rebuilding the whole row here can reset a native <select> before the
      // browser has committed its selected option. Update only the CSS state.
      if (["editor_kind", "price_kind", "billing_mode"].indexOf(key) >= 0) {
        normalizeKind(plan);
        render();
        return;
      }
      if (key === "payment_type") {
        ["empty", "per-lesson", "per-month", "package", "per-visit", "entry-ticket"].forEach((typeName) => {
          row.classList.remove("payment-type--" + typeName);
        });
        row.classList.add("payment-type--" + (field.value || "empty").replace("_", "-"));
        const packageSessions = row.querySelector('[data-tariff-key="package_sessions"]');
        if (packageSessions) {
          packageSessions.required = field.value === "package";
        }
      }
    });
    wrapper.appendChild(field);
    target.appendChild(wrapper);
  }

  function tariffSummary(plan, index) {
    const kindLabels = {
      admission: "Билет", visit: "Посещение", lesson: "Занятие", package: "Пакет",
      membership: "Абонемент", course: "Курс", camp: "Лагерь", event: "Событие",
      excursion: "Экскурсия", tour: "Тур", rental: "Аренда", addon: "Доплата",
      registration_fee: "Регистрация", deposit: "Депозит"
    };
    let price = interfaceCopy.noPrice;
    if (plan.price_kind === "free") price = labels.free;
    else if (plan.price_kind === "on_request") price = labels.onRequest;
    else if (plan.price_kind === "range" && plan.price_min && plan.price_max) price = plan.price_min + "–" + plan.price_max + " " + (plan.currency || "AZN");
    else if (plan.price_kind === "from" && plan.price_min) price = labels.from + " " + plan.price_min + " " + (plan.currency || "AZN");
    else if (plan.price) price = plan.price + " " + (plan.currency || "AZN");
    return {
      title: plan.title_az || plan.title_ru || kindLabels[plan.editor_kind] || (interfaceCopy.tariff + " " + (index + 1)),
      meta: (kindLabels[plan.editor_kind] || interfaceCopy.chooseType) + " · " + price,
    };
  }

  function updateCardSummary(row, plan, index) {
    const cardIndex = index === undefined ? Array.prototype.indexOf.call(list.children, row) : index;
    const summary = tariffSummary(plan, cardIndex < 0 ? 0 : cardIndex);
    const title = row.querySelector(".owner-tariff-card-copy strong");
    const meta = row.querySelector(".owner-tariff-card-copy small");
    if (title) title.textContent = summary.title;
    if (meta) meta.textContent = summary.meta;
  }
 
  function render() {
    list.innerHTML = "";
    plans.forEach((plan, index) => {
      const row = document.createElement("div");
      normalizeKind(plan);
      const cleanType = (plan.editor_kind || "empty").replace("_", "-");
      const hasTranslations = plan.title_ru || plan.title_en || plan._show_translations;
      row.className = "owner-tariff-row payment-type--" + cleanType;

      const summary = tariffSummary(plan, index);
      const cardHead = document.createElement("div");
      cardHead.className = "owner-tariff-card-head";
      const cardIcon = document.createElement("span");
      cardIcon.className = "owner-tariff-card-icon";
      cardIcon.setAttribute("aria-hidden", "true");
      cardIcon.innerHTML = icons.tag;
      const cardCopy = document.createElement("span");
      cardCopy.className = "owner-tariff-card-copy";
      const cardTitle = document.createElement("strong");
      cardTitle.textContent = summary.title;
      const cardMeta = document.createElement("small");
      cardMeta.textContent = summary.meta;
      cardCopy.append(cardTitle, cardMeta);
      const cardNumber = document.createElement("span");
      cardNumber.className = "owner-tariff-card-number";
      cardNumber.textContent = "#" + (index + 1);
      cardHead.append(cardIcon, cardCopy, cardNumber);
      row.appendChild(cardHead);

      const mainGrid = document.createElement("div");
      mainGrid.className = "owner-tariff-grid owner-tariff-grid--main";
      row.appendChild(mainGrid);

      const advanced = document.createElement("details");
      advanced.className = "owner-tariff-advanced";
      advanced.open = plan._advanced_open === true;
      advanced.innerHTML = '<summary><span>' + icons.sliders + ' ' + interfaceCopy.advanced + '</span><small>' + interfaceCopy.advancedHint + '</small></summary>';
      advanced.addEventListener("toggle", () => { plan._advanced_open = advanced.open; });
      const advancedGrid = document.createElement("div");
      advancedGrid.className = "owner-tariff-grid owner-tariff-grid--advanced";
      advanced.appendChild(advancedGrid);
      row.appendChild(advanced);

      const mainKeys = new Set(["editor_kind", "title_az", "billing_mode", "billing_interval", "billing_interval_count", "billing_cycles", "price_kind", "price", "price_min", "price_max", "currency", "quantity", "quantity_unit"]);
      fields.forEach((field) => {
        const target = mainKeys.has(field[0]) ? mainGrid : advancedGrid;
        addField(target, row, plan, field[0], field[1], field[2], field[3], field[4]);
        
        // Render translations toggle link directly after default AZ title
        if (field[0] === "title_az" && !hasTranslations) {
          const toggleWrapper = document.createElement("div");
          toggleWrapper.className = "owner-tariff-translation-toggle";
          
          const toggleBtn = document.createElement("button");
          toggleBtn.type = "button";
          toggleBtn.className = "km-btn-link";
          toggleBtn.innerHTML = icons.language + " + " + labels.addTranslation;
          toggleBtn.addEventListener("click", () => {
            plan._show_translations = true;
            render();
          });
          
          toggleWrapper.appendChild(toggleBtn);
          mainGrid.appendChild(toggleWrapper);
        }
      });

      const footer = document.createElement("div");
      footer.className = "owner-tariff-footer";

      const active = document.createElement("label");
      active.className = "owner-tariff-active";
      active.innerHTML = '<input type="checkbox" class="field-check"> <span>' + labels.active + '</span>';
      const checkbox = active.querySelector("input");
      checkbox.checked = plan.is_active !== false;
      checkbox.addEventListener("change", () => { plan.is_active = checkbox.checked; sync(); });
      footer.appendChild(active);

      const actions = document.createElement("div");
      actions.className = "owner-tariff-actions";
      [[icons.up, labels.up, -1], [icons.down, labels.down, 1]].forEach((item) => {
        const button = document.createElement("button");
        button.type = "button"; 
        button.className = "owner-tariff-move"; 
        button.title = item[1]; 
        button.innerHTML = item[0];
        button.disabled = index + item[2] < 0 || index + item[2] >= plans.length;
        button.addEventListener("click", () => { const target = index + item[2]; [plans[index], plans[target]] = [plans[target], plans[index]]; render(); sync(); });
        actions.appendChild(button);
      });
      
      const remove = document.createElement("button");
      remove.type = "button"; 
      remove.className = "owner-tariff-remove"; 
      remove.title = labels.remove; 
      remove.innerHTML = icons.trash;
      remove.addEventListener("click", () => { plans.splice(index, 1); render(); sync(); });
      actions.appendChild(remove);
      
      footer.appendChild(actions);
      row.appendChild(footer);
      list.appendChild(row);
    });
    sync();
  }

  add.addEventListener("click", () => {
    if (plans.length < MAX_PRICING_PLANS) {
      plans.push({
        editor_kind: "",
        title_az: "",
        title_ru: "",
        title_en: "",
        lesson_format: "",
        billing_mode: "one_time",
        price_kind: "exact",
        price: "",
        currency: "AZN",
        is_active: true
      });
      render();
      const firstField = list.lastElementChild && list.lastElementChild.querySelector("[data-tariff-key]");
      if (firstField) firstField.focus();
    }
  });

  // JSON import and other form helpers update the hidden field after this
  // editor has already loaded. Rehydrate the editor instead of letting its
  // stale in-memory copy overwrite the imported tariffs on the next action.
  input.addEventListener("input", () => {
    plans = parsePlans(input.value);
    render();
  });
  render();
})();
