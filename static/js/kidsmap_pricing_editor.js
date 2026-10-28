(function () {
  const configNode = document.getElementById('km-pricing-editor-contract');
  const contract = configNode ? JSON.parse(configNode.textContent) : null;
  const MAX_PRICING_PLANS = contract?.max_plans || 12;
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
  let indexForHint = 0;

  const langKey = (document.documentElement.lang || "ru").split("-")[0].toLowerCase();
  const pricingI18n = {
    az: {
      addTranslation: "Tərcümə əlavə et (RU, EN)",
      egSessionsWeek: "məsələn, 3",
      egSessionsMonth: "məsələn, 12",
      egPackageSessions: "məsələn, 10",
      egPrice: "məsələn, 120",
      kind: "Tarif növü", priceKind: "Qiymət növü", exact: "Dəqiq", free: "Pulsuz",
      from: "Başlayır", range: "Aralıq", onRequest: "Sorğu ilə", priceMin: "Qiymət min", priceMax: "Qiymət max",
      billingMode: "Ödəniş forması", oneTime: "Birdəfəlik", recurring: "Daimi", installment: "Hissə-hissə",
      interval: "Dövr", intervalCount: "Dövr sayı", cycles: "Ödəniş sayı",
      quantity: "Miqdar", quantityUnit: "Vahid", audience: "Auditoriya", ageFrom: "Yaş min", ageTo: "Yaş max",
      conditionsAz: "Şərtlər (AZ)", conditionsRu: "Şərtlər (RU)", conditionsEn: "Şərtlər (EN)", sourceUrl: "Mənbə linki",
      verifiedAt: "Təsdiq tarixi",
      currency: "Valyuta", unlimited: "Limitsiz", validity: "Qüvvədə olma müddəti", validityCount: "Müddət",
      validFrom: "Başlama tarixi", validUntil: "Bitmə tarixi", minPeople: "Min. nəfər", maxPeople: "Max. nəfər",
      dayType: "Günlər", required: "Məcburi ödəniş",
      kinds: [
        ["admission", "Giriş bileti"], ["visit", "Birdəfəlik ziyarət"], ["lesson", "Bir dərslik məşğələ"],
        ["package", "Dərs paketi"], ["membership", "Abonement"], ["course", "Kurs və ya semestr"],
        ["camp", "Düşərgə"], ["event", "Tədbir"], ["excursion", "Ekskursiya"], ["tour", "Tur"],
        ["rental", "İcarə"], ["addon", "Əlavə xidmət"], ["registration_fee", "Qeydiyyat haqqı"], ["deposit", "Depozit"]
      ],
      intervals: [["day", "Gün"], ["week", "Həftə"], ["month", "Ay"], ["year", "İl"]],
      quantityUnits: [
        ["entry", "Giriş"], ["visit", "Ziyarət"], ["lesson", "Dərs"], ["minute", "Dəqiqə"], ["hour", "Saat"],
        ["day", "Gün"], ["week", "Həftə"], ["month", "Ay"], ["course", "Kurs"], ["event", "Tədbir"],
        ["camp_shift", "Növbə"], ["person", "Nəfər"], ["family", "Ailə"], ["group", "Qrup"]
      ],
      audiences: [["all", "Hamı"], ["child", "Uşaqlar"], ["adult", "Böyüklər"], ["family", "Ailə"], ["group", "Qrup"]],
      dayTypes: [["any", "İstənilən gün"], ["weekday", "İş günləri"], ["weekend", "Həftəsonu"], ["holiday", "Bayram günləri"]],
    },
    en: {
      addTranslation: "Add translation (RU, EN)",
      egSessionsWeek: "e.g., 3",
      egSessionsMonth: "e.g., 12",
      egPackageSessions: "e.g., 10",
      egPrice: "e.g., 120",
      kind: "Plan type", priceKind: "Price type", exact: "Exact", free: "Free",
      from: "From", range: "Range", onRequest: "On request", priceMin: "Price from", priceMax: "Price to",
      billingMode: "Billing", oneTime: "One-time", recurring: "Recurring", installment: "Installments",
      interval: "Period", intervalCount: "Period count", cycles: "Billing cycles",
      quantity: "Quantity", quantityUnit: "Unit", audience: "Audience", ageFrom: "Age from", ageTo: "Age to",
      conditionsAz: "Terms (AZ)", conditionsRu: "Terms (RU)", conditionsEn: "Terms (EN)", sourceUrl: "Source URL",
      verifiedAt: "Verified by staff",
      currency: "Currency", unlimited: "Unlimited", validity: "Validity period", validityCount: "Duration",
      validFrom: "Valid from", validUntil: "Valid until", minPeople: "Min people", maxPeople: "Max people",
      dayType: "Days", required: "Required payment",
      kinds: [
        ["admission", "Admission ticket"], ["visit", "Single visit"], ["lesson", "Single lesson"],
        ["package", "Lesson package"], ["membership", "Membership"], ["course", "Course or semester"],
        ["camp", "Camp"], ["event", "Event"], ["excursion", "Excursion"], ["tour", "Tour"],
        ["rental", "Rental"], ["addon", "Add-on service"], ["registration_fee", "Registration fee"], ["deposit", "Deposit"]
      ],
      intervals: [["day", "Day"], ["week", "Week"], ["month", "Month"], ["year", "Year"]],
      quantityUnits: [
        ["entry", "Entry"], ["visit", "Visit"], ["lesson", "Lesson"], ["minute", "Minute"], ["hour", "Hour"],
        ["day", "Day"], ["week", "Week"], ["month", "Month"], ["course", "Course"], ["event", "Event"],
        ["camp_shift", "Shift"], ["person", "Person"], ["family", "Family"], ["group", "Group"]
      ],
      audiences: [["all", "All"], ["child", "Children"], ["adult", "Adults"], ["family", "Family"], ["group", "Group"]],
      dayTypes: [["any", "Any day"], ["weekday", "Weekdays"], ["weekend", "Weekends"], ["holiday", "Holidays"]],
    },
    ru: {
      addTranslation: "Добавить перевод (RU, EN)",
      egSessionsWeek: "например, 3",
      egSessionsMonth: "например, 12",
      egPackageSessions: "например, 10",
      egPrice: "например, 120",
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
      kinds: [
        ["admission", "Входной билет"], ["visit", "Разовое посещение"], ["lesson", "Одно занятие"],
        ["package", "Пакет занятий"], ["membership", "Абонемент"], ["course", "Курс или семестр"],
        ["camp", "Лагерь"], ["event", "Событие"], ["excursion", "Экскурсия"], ["tour", "Тур"],
        ["rental", "Аренда"], ["addon", "Дополнительная услуга"], ["registration_fee", "Регистрационный взнос"], ["deposit", "Депозит"]
      ],
      intervals: [["day", "День"], ["week", "Неделя"], ["month", "Месяц"], ["year", "Год"]],
      quantityUnits: [
        ["entry", "Вход"], ["visit", "Посещение"], ["lesson", "Занятие"], ["minute", "Минута"], ["hour", "Час"],
        ["day", "День"], ["week", "Неделя"], ["month", "Месяц"], ["course", "Курс"], ["event", "Событие"],
        ["camp_shift", "Смена"], ["person", "Человек"], ["family", "Семья"], ["group", "Группа"]
      ],
      audiences: [["all", "Все"], ["child", "Дети"], ["adult", "Взрослые"], ["family", "Семья"], ["group", "Группа"]],
      dayTypes: [["any", "Любой день"], ["weekday", "Будни"], ["weekend", "Выходные"], ["holiday", "Праздники"]],
    },
  };

  const currentDict = pricingI18n[langKey] || pricingI18n.ru;

  const labels = {
    format: editor.dataset.formatLabel || (langKey === "az" ? "Format" : (langKey === "en" ? "Format" : "Формат")),
    group: editor.dataset.groupLabel || (langKey === "az" ? "Qrup" : (langKey === "en" ? "Group" : "Группа")),
    individual: editor.dataset.individualLabel || (langKey === "az" ? "Fərdi" : (langKey === "en" ? "Individual" : "Индивидуально")),
    openVisit: editor.dataset.openVisitLabel || (langKey === "az" ? "Sərbəst giriş" : (langKey === "en" ? "Open visit" : "Свободное посещение")),
    payment: editor.dataset.paymentLabel || (langKey === "az" ? "Ödəniş" : (langKey === "en" ? "Payment" : "Оплата")),
    perLesson: editor.dataset.perLessonLabel || (langKey === "az" ? "Dərs üzrə" : (langKey === "en" ? "Per lesson" : "За занятие")),
    perMonth: editor.dataset.perMonthLabel || (langKey === "az" ? "Aylıq" : (langKey === "en" ? "Per month" : "В месяц")),
    package: editor.dataset.packageLabel || (langKey === "az" ? "Paket" : (langKey === "en" ? "Package" : "Пакет")),
    perVisit: editor.dataset.perVisitLabel || (langKey === "az" ? "Ziyarət üzrə" : (langKey === "en" ? "Per visit" : "За посещение")),
    entryTicket: editor.dataset.entryTicketLabel || (langKey === "az" ? "Giriş bileti" : (langKey === "en" ? "Entry ticket" : "Входной билет")),
    week: editor.dataset.weekLabel || (langKey === "az" ? "Dərs/həftə" : (langKey === "en" ? "Sessions/week" : "Занятий в неделю")),
    month: editor.dataset.monthLabel || (langKey === "az" ? "Dərs/ay" : (langKey === "en" ? "Sessions/month" : "Занятий в месяц")),
    packageSessions: editor.dataset.packageSessionsLabel || (langKey === "az" ? "Paketdə dərs sayı" : (langKey === "en" ? "Package sessions" : "Занятий в пакете")),
    price: editor.dataset.priceLabel || (langKey === "az" ? "Qiymət" : (langKey === "en" ? "Price" : "Цена")),
    titleAz: editor.dataset.titleAzLabel || (langKey === "az" ? "Tarif adı (AZ)" : langKey === "en" ? "Plan title (AZ)" : "Название тарифа (AZ)"),
    titleRu: editor.dataset.titleRuLabel || (langKey === "az" ? "Tarif adı (RU)" : langKey === "en" ? "Plan title (RU)" : "Название тарифа (RU)"),
    titleEn: editor.dataset.titleEnLabel || (langKey === "az" ? "Tarif adı (EN)" : langKey === "en" ? "Plan title (EN)" : "Название тарифа (EN)"),
    active: editor.dataset.activeLabel || (langKey === "az" ? "Aktiv" : (langKey === "en" ? "Active" : "Активен")),
    remove: editor.dataset.removeLabel || (langKey === "az" ? "Sil" : (langKey === "en" ? "Remove" : "Удалить")),
    up: editor.dataset.upLabel || (langKey === "az" ? "Yuxarı" : (langKey === "en" ? "Move up" : "Вверх")),
    down: editor.dataset.downLabel || (langKey === "az" ? "Aşağı" : (langKey === "en" ? "Move down" : "Вниз")),
    addTranslation: editor.dataset.addTranslationLabel || currentDict.addTranslation,
    egSessionsWeek: editor.dataset.egSessionsWeek || currentDict.egSessionsWeek,
    egSessionsMonth: editor.dataset.egSessionsMonth || currentDict.egSessionsMonth,
    egPackageSessions: editor.dataset.egPackageSessions || currentDict.egPackageSessions,
    egPrice: editor.dataset.egPrice || currentDict.egPrice,
    choose: editor.dataset.chooseLabel || (langKey === "az" ? "Seçin" : (langKey === "en" ? "Choose" : "Выберите")),
    kind: currentDict.kind, priceKind: currentDict.priceKind, exact: currentDict.exact, free: currentDict.free,
    from: currentDict.from, range: currentDict.range, onRequest: currentDict.onRequest, priceMin: currentDict.priceMin, priceMax: currentDict.priceMax,
    billingMode: currentDict.billingMode, oneTime: currentDict.oneTime, recurring: currentDict.recurring, installment: currentDict.installment,
    interval: currentDict.interval, intervalCount: currentDict.intervalCount, cycles: currentDict.cycles,
    quantity: currentDict.quantity, quantityUnit: currentDict.quantityUnit, audience: currentDict.audience, ageFrom: currentDict.ageFrom, ageTo: currentDict.ageTo,
    conditionsAz: currentDict.conditionsAz, conditionsRu: currentDict.conditionsRu, conditionsEn: currentDict.conditionsEn, sourceUrl: currentDict.sourceUrl,
    verifiedAt: currentDict.verifiedAt,
    currency: currentDict.currency, unlimited: currentDict.unlimited, validity: currentDict.validity, validityCount: currentDict.validityCount,
    validFrom: currentDict.validFrom, validUntil: currentDict.validUntil, minPeople: currentDict.minPeople, maxPeople: currentDict.maxPeople,
    dayType: currentDict.dayType, required: currentDict.required,
  };

  // The server owns the allowed values. Legacy callers retain the existing
  // translation dictionary until they migrate to the shared include.
  if (contract) {
    const choices = key => contract[key];
    currentDict.kinds = choices('product_types').flatMap(item => item[0] === 'lesson'
      ? [item, ['package', ({az:'Dərs paketi',en:'Lesson package',ru:'Пакет занятий'})[langKey] || 'Lesson package']]
      : [item]);
    currentDict.intervals = choices('intervals');
    currentDict.quantityUnits = choices('quantity_units');
    currentDict.audiences = choices('audiences');
    currentDict.dayTypes = choices('day_types');
  }
  const fields = [
    ["editor_kind", labels.kind, "select", currentDict.kinds, true],
    ["billing_mode", labels.billingMode, "select", contract?.billing_modes || [["one_time", labels.oneTime], ["recurring", labels.recurring], ["installment", labels.installment]], true],
    ["title_az", labels.titleAz, "text", null, false],
    ["quantity", labels.quantity, "number", null, false],
    ["quantity_unit", labels.quantityUnit, "select", currentDict.quantityUnits, false],
    ["price_kind", labels.priceKind, "select", contract?.price_kinds || [["exact", labels.exact], ["free", labels.free], ["from", labels.from], ["range", labels.range], ["on_request", labels.onRequest]], true],
    ["price", labels.price, "number", null, false],
    ["price_min", labels.priceMin, "number", null, false],
    ["price_max", labels.priceMax, "number", null, false],
    ["currency", labels.currency, "select", [["AZN", "AZN"], ["USD", "USD"], ["EUR", "EUR"], ["RUB", "RUB"]], true],
    ["billing_interval", labels.interval, "select", currentDict.intervals, false],
    ["billing_interval_count", labels.intervalCount, "number", null, false],
    ["billing_cycles", labels.cycles, "number", null, false],
    ["title_ru", labels.titleRu, "text", null, false],
    ["title_en", labels.titleEn, "text", null, false],
    ["lesson_format", labels.format, "select", contract?.lesson_formats || [["group", labels.group], ["individual", labels.individual], ["open_visit", labels.openVisit]], false],
    ["sessions_per_week", labels.week, "number", null, false],
    ["sessions_per_month", labels.month, "number", null, false],
    ["is_unlimited", labels.unlimited, "checkbox", null, false],
    ["validity_interval", labels.validity, "select", currentDict.intervals, false],
    ["validity_interval_count", labels.validityCount, "number", null, false],
    ["valid_from", labels.validFrom, "date", null, false], ["valid_until", labels.validUntil, "date", null, false],
    ["audience_type", labels.audience, "select", currentDict.audiences, false],
    ["age_from", labels.ageFrom, "number", null, false], ["age_to", labels.ageTo, "number", null, false],
    ["min_people", labels.minPeople, "number", null, false], ["max_people", labels.maxPeople, "number", null, false],
    ["day_type", labels.dayType, "select", currentDict.dayTypes, false],
    ["is_required", labels.required, "checkbox", null, false],
    ["is_trial", ({az:"Sınaq dərsi",en:"Trial",ru:"Пробное"})[langKey] || "Trial", "checkbox", null, false],
    ["conditions_az", labels.conditionsAz, "text", null, false], ["conditions_ru", labels.conditionsRu, "text", null, false], ["conditions_en", labels.conditionsEn, "text", null, false],
    ["source_url", labels.sourceUrl, "url", null, false],
    ["verified_at", labels.verifiedAt, "datetime-local", null, false],
  ];

  const monthlyLabel = ({az:'Aylıq ödəniş',en:'Monthly payment',ru:'Ежемесячная оплата'})[langKey] || 'Monthly payment';
  const workflowCopy = ({
    ru:{product:'За что платят',payment:'Цена и оплата',included:'Что входит и на какой срок',validity:'Использовать в течение',count:'Количество',unit:'Единица срока',validityHelp:'Необязательно. Например, 8 занятий нужно использовать за 1 месяц. Это срок использования, а не частота оплаты.',dates:'Даты предложения · необязательно',datesHelp:'Например, летняя акция с 1 июня по 31 августа. Эти даты не заменяют срок использования купленных посещений.',from:'Предложение действует с',until:'Предложение действует до',once:'Один платёж',recurring:'Оплата каждые',installments:'Количество платежей',unlimited:'Безлимит посещений',useWithin:'Использовать за',paymentHelp:'Один платёж может покрывать месяц или весь курс. Регулярные платежи повторяются через выбранный период.'},
    az:{product:'Nə üçün ödəniş edilir',payment:'Qiymət və ödəniş',included:'Nələr daxildir və hansı müddətə',validity:'İstifadə müddəti',count:'Miqdar',unit:'Müddət vahidi',validityHelp:'Məcburi deyil. Məsələn, 8 dərsdən 1 ay ərzində istifadə edin. Bu, ödəniş tezliyi deyil, istifadə müddətidir.',dates:'Təklifin tarixləri · məcburi deyil',datesHelp:'Məsələn, 1 iyundan 31 avqusta qədər yay kampaniyası. Bu tarixlər alınmış ziyarətlərin istifadə müddətini əvəz etmir.',from:'Təklifin başlanğıcı',until:'Təklifin sonu',once:'Bir ödəniş',recurring:'Ödəniş hər',installments:'Ödənişlərin sayı',unlimited:'Limitsiz ziyarət',useWithin:'İstifadə müddəti',paymentHelp:'Bir ödəniş bir ayı və ya bütün kursu əhatə edə bilər. Müntəzəm ödənişlər seçilmiş dövrlə təkrarlanır.'},
    en:{product:'What people pay for',payment:'Price and payment',included:'What is included and for how long',validity:'Use within',count:'Number',unit:'Time unit',validityHelp:'Optional. For example, use 8 lessons within 1 month. This is the usage period, not payment frequency.',dates:'Offer dates · optional',datesHelp:'For example, a summer offer from June 1 to August 31. These dates do not replace the usage period for purchased visits.',from:'Offer starts on',until:'Offer ends on',once:'One payment',recurring:'Pay every',installments:'Number of payments',unlimited:'Unlimited visits',useWithin:'Use within',paymentHelp:'One payment can cover a month or a whole course. Recurring payments repeat at the selected interval.'}
  })[langKey] || null;
  currentDict.kinds.splice(currentDict.kinds.findIndex(item => item[0] === 'membership'), 0, ['monthly', monthlyLabel]);

  function prepareView(plan) {
    const kind = plan.editor_kind || (plan.payment_type === 'package' ||
      (plan.product_type === 'lesson' && plan.quantity_unit === 'lesson' && Number(plan.quantity) > 1)
      ? 'package' : plan.product_type === 'membership' && plan.billing_mode === 'recurring' && plan.billing_interval === 'month' && Number(plan.billing_interval_count) === 1
      ? 'monthly' : plan.product_type || ({per_lesson:'lesson',per_month:'membership',per_visit:'visit',entry_ticket:'admission'}[plan.payment_type]) || '');
    // UI metadata never rewrites the stored tariff when the editor opens.
    Object.defineProperty(plan, 'editor_kind', {value:kind,writable:true,configurable:true,enumerable:false});
    return plan;
  }
  function normalizeKind(plan, changed) {
    if (changed === 'editor_kind') {
      plan.product_type = plan.editor_kind === 'package' ? 'lesson' : plan.editor_kind === 'monthly' ? 'membership' : plan.editor_kind;
      plan.charge_role = ['addon','registration_fee','deposit'].includes(plan.product_type) ? plan.product_type : 'primary';
      if (plan.editor_kind === 'package') { plan.quantity_unit = 'lesson'; plan.billing_mode = 'one_time'; }
      if (plan.editor_kind === 'monthly') {
        plan.billing_mode = 'recurring'; plan.billing_interval = 'month'; plan.billing_interval_count = 1; plan.billing_cycles = null;
      }
    }
    if (changed === 'price_kind') {
      if (plan.price_kind === 'exact') { plan.price_min = null; plan.price_max = null; }
      if (plan.price_kind === 'free') { plan.price = '0'; plan.price_min = null; plan.price_max = null; }
      if (plan.price_kind === 'from') { plan.price = null; plan.price_max = null; }
      if (plan.price_kind === 'range') plan.price = null;
      if (plan.price_kind === 'on_request') { plan.price = null; plan.price_min = null; plan.price_max = null; }
    }
    if (changed === 'billing_mode' || (changed === 'editor_kind' && plan.editor_kind === 'package')) {
      if (plan.billing_mode === 'recurring') { plan.billing_cycles = null; }
      else if (plan.billing_mode === 'installment') { plan.billing_interval = ''; plan.billing_interval_count = null; }
      else { plan.billing_interval = ''; plan.billing_interval_count = null; plan.billing_cycles = null; }
    }
    if (changed === 'quantity' && plan.editor_kind === 'monthly') {
      if (plan.quantity && !plan.quantity_unit) plan.quantity_unit = 'lesson';
      else if (!plan.quantity && plan.quantity_unit === 'lesson') plan.quantity_unit = '';
    }
    if (changed === 'is_unlimited' && plan.is_unlimited) { plan.quantity = null; plan.quantity_unit = ''; }
    if (['billing_mode','billing_interval','billing_interval_count'].includes(changed) &&
        plan.editor_kind === 'monthly' && !(plan.billing_mode === 'recurring' &&
          plan.billing_interval === 'month' && Number(plan.billing_interval_count) === 1)) {
      plan.editor_kind = 'membership';
    }
  }
  plans.forEach(prepareView);

  function sync() {

    const contentKeys = ["editor_kind", "product_type", "price_kind", "price", "price_min", "price_max", "title_az", "title_ru", "title_en"];
    const cleanPlans = plans
      .map((plan) => Object.fromEntries(Object.entries(plan).filter(([key]) => !key.startsWith("_"))));
    input.value = JSON.stringify(cleanPlans);
    input.dispatchEvent(new CustomEvent("km:pricing-change", { bubbles: true }));
    input.dispatchEvent(new Event("change", {bubbles:true}));
  }

  function addField(target, row, plan, key, label, type, options, required) {
    if (workflowCopy) label = ({is_unlimited:workflowCopy.unlimited,validity_interval:workflowCopy.unit,validity_interval_count:workflowCopy.count,valid_from:workflowCopy.from,valid_until:workflowCopy.until})[key] || label;
    if (['price','price_min','price_max'].includes(key)) label = ({az:{price:'Məbləğ',price_min:'Minimum məbləğ',price_max:'Maksimum məbləğ'},en:{price:'Amount',price_min:'Minimum amount',price_max:'Maximum amount'},ru:{price:'Стоимость',price_min:'Стоимость от',price_max:'Стоимость до'}})[langKey]?.[key] || label;
    if (key === 'quantity' && ['monthly','package'].includes(plan.editor_kind) && (!plan.quantity_unit || plan.quantity_unit === 'lesson')) label = ({az:'Dərs sayı',en:'Lessons included',ru:'Занятий включено'})[langKey] || label;
    const wrapper = document.createElement(key === "price_kind" ? "div" : "label");
    wrapper.className = "owner-tariff-field owner-tariff-field--" + key;
    if (key === 'currency') {
      const storedCurrency = document.createElement('input');
      storedCurrency.type = 'hidden'; storedCurrency.dataset.tariffKey = key;
      storedCurrency.value = plan.currency || 'AZN';
      wrapper.hidden = true; wrapper.append(storedCurrency); target.append(wrapper);
      return;
    }
    var kind = plan.editor_kind || "";
    var priceKind = plan.price_kind || "exact";
    var billingMode = plan.billing_mode || "one_time";
    var lessonKinds = ["lesson", "package", "membership", "monthly", "course"];
    var visible = true;
    if (key === "lesson_format") visible = lessonKinds.includes(kind) || !!plan[key];
    if (["sessions_per_week", "sessions_per_month"].includes(key)) visible = lessonKinds.includes(kind) || !!plan[key];
    if (["quantity", "quantity_unit"].indexOf(key) >= 0) visible = true;
    if (["billing_interval", "billing_interval_count"].indexOf(key) >= 0) visible = billingMode === "recurring";
    if (key === "billing_cycles") visible = billingMode === "installment";
    if (key === "price") visible = priceKind === "exact";
    if (key === "price_min") visible = priceKind === "from" || priceKind === "range";
    if (key === "price_max") visible = priceKind === "range";
    if (key === "currency") visible = priceKind !== "free" && priceKind !== "on_request";
    if (key === 'quantity' && plan.is_unlimited === true) visible = false;
    if (key === 'quantity_unit' && plan.is_unlimited === true && !plan.quantity) visible = false;
    if (["is_unlimited", "validity_interval", "validity_interval_count"].indexOf(key) >= 0) visible = true;
    if (key === "is_required") visible = ["addon", "registration_fee", "deposit"].includes(kind) || !!plan[key];
    if (key === "verified_at") visible = canVerify;
    if (key === 'billing_mode' && priceKind === 'free' && billingMode === 'one_time') visible = false;
    wrapper.hidden = !visible;

    // Hide RU and EN translation fields by default if they are empty
    if ((key === "title_ru" || key === "title_en") && !plan[key] && !plan._show_translations) {
      wrapper.classList.add("owner-tariff-field--hidden");
    }

    const labelHtml = required ? label + ' <span style="display: inline; color: #ef4444; font-weight: bold;">*</span>' : label;
    const visuallyRequired = Boolean(visible && (required || ['price','price_min','price_max'].includes(key) ||
      (billingMode === 'recurring' && ['billing_interval','billing_interval_count'].includes(key)) ||
      (billingMode === 'installment' && key === 'billing_cycles') ||
      (plan.validity_interval && key === 'validity_interval_count') ||
      (plan.validity_interval_count && key === 'validity_interval')));
    wrapper.dataset.kmRequired = String(visuallyRequired);
    wrapper.innerHTML = "<span class=\"owner-tariff-label\">" + (visuallyRequired && !required ? labelHtml + ' <span class="owner-tariff-required" aria-hidden="true">*</span>' : labelHtml) + "</span>";

    let field;
    if (type === "select") {
      field = document.createElement("select");
      field.innerHTML = '<option value="">' + labels.choose + '</option>' + options.map((item) => '<option value="' + item[0] + '">' + item[1] + '</option>').join("");
    } else {
      field = document.createElement("input");
      field.type = type;
      if (type === "number") {
        const isMoney = ["price", "price_min", "price_max"].indexOf(key) >= 0;
        field.min = isMoney || key === "age_from" || key === "age_to" ? "0" : "1";
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
    if (contract?.max_lengths?.[key] && ['text','url','textarea'].includes(type)) field.maxLength = contract.max_lengths[key];
    field.required = !!required && visible;
    if (visuallyRequired) field.setAttribute('aria-required','true');
    if (type === "checkbox") field.checked = plan[key] === true;
    else {
      const value = plan[key] == null ? '' : (key === 'verified_at' ? String(plan[key]).slice(0,16) : plan[key]);
      if (type === 'select' && value && !Array.from(field.options).some(o => o.value === String(value))) {
        const saved = document.createElement('option'); saved.value = value; saved.textContent = value; field.append(saved);
      }
      field.value = value;
    }
    field.dataset.tariffKey = key;
    const fieldHints={ru:{editor_kind:'За урок — одно занятие. Пакет — несколько занятий, например 8. Абонемент — оплата за неделю или месяц.',quantity:'Сколько входит в эту цену: например 8 занятий или 2 часа.',billing_mode:'Разово — один платёж; регулярно — каждую неделю или месяц; рассрочка — несколько платежей за весь курс.',billing_interval:'Как часто повторяется оплата: например раз в неделю или месяц.',billing_interval_count:'Например, 1 — каждый период, 2 — раз в два периода.',validity_interval:'За какое время нужно использовать купленные посещения.',validity_interval_count:'Например, 2 месяца с даты покупки.',source_url:'Необязательно: публичная страница с подтверждением цены.',is_unlimited:'Количество посещений не ограничено в пределах срока действия.'},az:{editor_kind:'Dərs — bir məşğələ. Paket — məsələn 8 məşğələ. Abunə — həftəlik və ya aylıq ödəniş.',quantity:'Bu qiymətə daxil olan miqdar: məsələn 8 məşğələ və ya 2 saat.',billing_mode:'Birdəfəlik — bir ödəniş; müntəzəm — həftəlik və ya aylıq; hissəli — bütün kurs üçün bir neçə ödəniş.',billing_interval:'Ödəniş nə vaxt təkrarlanır: həftə və ya ay.',billing_interval_count:'1 — hər dövr, 2 — iki dövrdən bir.',validity_interval:'Alınmış ziyarətlərdən istifadə müddəti.',validity_interval_count:'Məsələn, alışdan sonra 2 ay.',source_url:'Məcburi deyil: qiyməti təsdiqləyən açıq səhifə.',is_unlimited:'Etibarlılıq müddətində ziyarət sayı məhdud deyil.'},en:{editor_kind:'Lesson means one session. A package can contain 8 lessons. Membership supports weekly or monthly payments.',quantity:'What this price includes: for example 8 lessons or 2 hours.',billing_mode:'One-time: a single payment. Recurring: weekly or monthly. Installments: several payments for the whole course.',billing_interval:'How often the payment repeats, such as weekly or monthly.',billing_interval_count:'1 means every period; 2 means every two periods.',validity_interval:'How long purchased visits can be used.',validity_interval_count:'For example, 2 months from purchase.',source_url:'Optional: a public page confirming the price.',is_unlimited:'Unlimited visits during the validity period.'}};
    const hint=(fieldHints[document.documentElement.lang?.split('-')[0]]||fieldHints.az)[key];
    if(hint){const help=document.createElement('small');help.className='owner-tariff-field-help';help.id=`tariff-help-${indexForHint++}`;help.textContent=hint;field.setAttribute('aria-describedby',help.id);wrapper.append(help);}
    const commit = () => {
      const next = type === 'checkbox' ? field.checked : field.value;
      const previous = plan[key];
      if (next === previous) return;
      if (key === 'is_unlimited' && next && plan.quantity && !window.confirm(({az:'Dərs sayını limitsizlə əvəz et?',en:'Replace the included quantity with unlimited?',ru:'Заменить количество занятий безлимитом?'})[langKey])) { field.checked = previous === true; return; }
      if (['price_kind','billing_mode','editor_kind'].includes(key) && previous &&
          (plan.id || plan.price || plan.price_min || plan.price_max || plan.quantity || plan.billing_interval)) {
        const warning = ({az:'Növün dəyişməsi bəzi məbləğ və dövrləri silə bilər. Davam edilsin?',en:'Changing the type may clear amounts or periods. Continue?',ru:'Смена типа может очистить суммы или периоды. Продолжить?'})[langKey];
        if (!window.confirm(warning)) { field.value = previous; return; }
      }
      plan[key] = next;
      normalizeKind(plan,key);
      sync();
      // Update the existing controls. Replacing the list moved the user's focus
      // and promoted filled fields to different sections midway through input.
      row.querySelectorAll('.owner-tariff-field').forEach(node => node.refreshTariffField?.());
      updateCardSummary(row,plan);
    };
    if (!['select','checkbox'].includes(type)) field.addEventListener('input',commit);
    field.addEventListener('change',commit);
    if (['price','price_min','price_max'].includes(key)) {
      const currency = plan.currency || 'AZN';
      const money = document.createElement('div'); money.className = 'owner-tariff-money';
      const unit = document.createElement('span'); unit.dataset.moneyCurrency = '';
      unit.textContent = currency === 'AZN' ? '₼' : currency; unit.setAttribute('aria-hidden','true');
      field.setAttribute('aria-label',`${label}, ${currency}`);
      money.append(field,unit); wrapper.append(money);
    } else if(type === 'checkbox') {
      const copy=document.createElement('span');copy.className='owner-tariff-check-copy';
      while(wrapper.firstChild)copy.append(wrapper.firstChild);
      wrapper.classList.add('owner-tariff-field--check');wrapper.append(field,copy);
    } else wrapper.appendChild(field);
    if (key === "price_kind") {
      const choices = document.createElement("div");
      choices.className = "pw-price-choices";
      choices.setAttribute("role", "group"); choices.setAttribute("aria-label", label);
      const priceIcons = {
        exact: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><circle cx="7" cy="7" r="1.5"/></svg>',
        free: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="8" width="18" height="4" rx="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 8a2.5 2.5 0 0 1 0-5A4.8 8 0 0 1 12 8a4.8 8 0 0 1 4.5-5 2.5 2.5 0 0 1 0 5"/></svg>',
        from: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17l10-10M17 17V7H7"/></svg>',
        range: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h16M8 8l-4 4 4 4M16 8l4 4-4 4"/></svg>',
        on_request: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/><circle cx="12" cy="12" r="1"/></svg>'
      };
      options.forEach(([value, caption]) => {
        const button = document.createElement("button");
        button.type = "button";
        const iconSpan = document.createElement("span");
        iconSpan.className = "pw-price-choice-icon";
        iconSpan.innerHTML = priceIcons[value] || "";
        const textSpan = document.createElement("span");
        textSpan.className = "pw-price-choice-label";
        textSpan.textContent = caption;
        button.append(iconSpan, textSpan);
        button.dataset.priceKind = value;
        button.setAttribute("aria-pressed", field.value === value ? "true" : "false");
        button.addEventListener("click", () => {
          field.value = value;
          field.dispatchEvent(new Event("change", { bubbles: true }));
        });
        choices.append(button);
      });
      field.hidden = true; wrapper.append(choices);

      for (const noticeKind of ['free','on_request']) {
        const hint = document.createElement("div");
        hint.className = `owner-tariff-price-notice owner-tariff-price-notice--${noticeKind}`;
        hint.dataset.priceNotice = noticeKind;
        hint.hidden = field.value !== noticeKind;
        if (noticeKind === "free") {
          hint.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg><span>' +
            (langKey === "az" ? "Bu tarif üzrə xidmət pulsuzdur (0 ₼)" : langKey === "en" ? "This service is free of charge (0 ₼)" : "Этот тариф предоставляется бесплатно (0 ₼)") +
            '</span>';
        } else {
          hint.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><circle cx="12" cy="8" r="0.8" fill="currentColor"/></svg><span>' +
            (langKey === "az" ? "Qiymət fərdi sorğu əsasında razılaşdırılır" : langKey === "en" ? "Price is agreed upon customer request" : "Цена согласуется по запросу клиента") +
            '</span>';
        }
        wrapper.append(hint);
      }
    }
    wrapper.refreshTariffField = () => {
      const currentKind = plan.editor_kind || '';
      const currentPrice = plan.price_kind || 'exact';
      const billing = plan.billing_mode || 'one_time';
      let shown = true;
      if (['lesson_format','sessions_per_week','sessions_per_month'].includes(key)) shown = ['lesson','package','membership','monthly','course'].includes(currentKind) || !!plan[key];
      if (key === 'billing_mode') shown = currentPrice !== 'free' || billing !== 'one_time';
      if (['billing_interval','billing_interval_count'].includes(key)) shown = billing === 'recurring';
      if (key === 'billing_cycles') shown = billing === 'installment';
      if (key === 'price') shown = currentPrice === 'exact';
      if (key === 'price_min') shown = ['from','range'].includes(currentPrice);
      if (key === 'price_max') shown = currentPrice === 'range';
      if (['quantity','quantity_unit'].includes(key)) shown = !plan.is_unlimited;
      if (key === 'is_required') shown = ['addon','registration_fee','deposit'].includes(currentKind) || !!plan[key];
      if (key === 'verified_at') shown = canVerify;
      wrapper.hidden = !shown;
      const needed = Boolean(shown && (required || ['price','price_min','price_max'].includes(key) ||
        (billing === 'recurring' && ['billing_interval','billing_interval_count'].includes(key)) ||
        (billing === 'installment' && key === 'billing_cycles') ||
        (plan.quantity_unit && key === 'quantity') ||
        (plan.validity_interval && key === 'validity_interval_count') ||
        (plan.validity_interval_count && key === 'validity_interval')));
      wrapper.dataset.kmRequired = String(needed);
      field.required = needed;
      if (needed) field.setAttribute('aria-required','true'); else field.removeAttribute('aria-required');
      const labelNode = wrapper.querySelector('.owner-tariff-label');
      labelNode.textContent = label;
      if (needed) { const star=document.createElement('span');star.className='owner-tariff-required';star.setAttribute('aria-hidden','true');star.textContent=' *';labelNode.append(star); }
      if (type === 'checkbox') field.checked = plan[key] === true;
      else {
        const value = plan[key] == null ? '' : (key === 'verified_at' ? String(plan[key]).slice(0,16) : String(plan[key]));
        if (field.value !== value) field.value = value;
      }
      if (key === 'price_kind') {
        wrapper.querySelectorAll('[data-price-kind]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.priceKind === currentPrice)));
        wrapper.querySelectorAll('[data-price-notice]').forEach(notice => { notice.hidden = notice.dataset.priceNotice !== currentPrice; });
      }
    };
    wrapper.refreshTariffField();
    target.appendChild(wrapper);
  }

  function tariffSummary(plan, index) {
    const kindLabels = Object.fromEntries(currentDict.kinds);
    const currency = !plan.currency || plan.currency === 'AZN' ? '₼' : plan.currency;
    let price = interfaceCopy.noPrice;
    if (plan.price_kind === "free") price = labels.free;
    else if (plan.price_kind === "on_request") price = labels.onRequest;
    else if (plan.price_kind === "range" && plan.price_min && plan.price_max) price = plan.price_min + "–" + plan.price_max + " " + currency;
    else if (plan.price_kind === "from" && plan.price_min) price = labels.from + " " + plan.price_min + " " + currency;
    else if (plan.price) price = plan.price + " " + currency;
    const period = (count, unit) => {
      const number=Number(count), ru={day:['день','дня','дней'],week:['неделя','недели','недель'],month:['месяц','месяца','месяцев'],year:['год','года','лет']};
      let word=Object.fromEntries(currentDict.intervals)[unit] || '?';
      if (langKey === 'ru' && ru[unit] && number) { const tail=number%100;word=ru[unit][tail>=11&&tail<=14?2:number%10===1?0:number%10>=2&&number%10<=4?1:2]; }
      else if(langKey==='en' && ['day','week','month','year'].includes(unit))word=unit+(number===1?'':'s');
      return `${count || '?'} ${word}`;
    };
    const payment = plan.price_kind === 'free' ? '' : plan.billing_mode === 'recurring'
      ? `${workflowCopy?.recurring || labels.recurring} ${period(plan.billing_interval_count,plan.billing_interval)}`
      : plan.billing_mode === 'installment' ? `${workflowCopy?.installments || labels.cycles}: ${plan.billing_cycles || '?'}` : workflowCopy?.once || labels.oneTime;
    return {
      title: plan.title_az || plan.title_ru || kindLabels[plan.editor_kind] || (interfaceCopy.tariff + " " + (index + 1)),
      meta: [kindLabels[plan.editor_kind] || interfaceCopy.chooseType, price,
        payment,
        plan.quantity ? `${plan.quantity} ${Object.fromEntries(currentDict.quantityUnits)[plan.quantity_unit] || '?'}` : '',
        plan.is_unlimited ? workflowCopy?.unlimited || labels.unlimited : '',
        plan.validity_interval ? `${workflowCopy?.useWithin || labels.validity}: ${period(plan.validity_interval_count,plan.validity_interval)}` : '',
        plan.valid_from ? `${workflowCopy?.from || labels.validFrom}: ${plan.valid_from}` : '',
        plan.valid_until ? `${workflowCopy?.until || labels.validUntil}: ${plan.valid_until}` : '',
        plan.conditions_az || plan.conditions_ru || plan.conditions_en || '',
        plan.is_active === false ? labels.active + ': —' : ''
      ].filter(Boolean).join(' · '),
    };
  }

  function updateEditorWarnings(row, plan) {
    const currency = plan.currency || 'AZN';
    const warning = row.querySelector('[data-tariff-currency-warning]');
    if (warning) {
      warning.hidden = currency === 'AZN' || ['free', 'on_request'].includes(plan.price_kind);
      warning.textContent = ({ru:`Цена сохранена в ${currency}. В бюджетном фильтре AZN этот тариф не участвует. Автоматической конвертации нет; добавьте отдельный тариф AZN только при подтверждённой цене.`, az:`Qiymət ${currency} ilə saxlanılır. Bu tarif AZN büdcə filtrinə daxil deyil. Avtomatik konvertasiya yoxdur; yalnız təsdiqlənmiş qiymət üçün ayrıca AZN tarifi əlavə edin.`,en:`This price is stored in ${currency} and is excluded from the AZN budget filter. There is no automatic conversion; add a separate AZN plan only for a confirmed price.`})[langKey];
    }
    const missing = ['title', 'conditions'].flatMap(prefix => {
      const languages = ['az','ru','en'];
      if (!languages.some(language => String(plan[prefix+'_'+language] || '').trim())) return [];
      const absent = languages.filter(language => !String(plan[prefix+'_'+language] || '').trim());
      const label = prefix === 'title' ? ({ru:'название',az:'ad',en:'title'})[langKey] : ({ru:'условия',az:'şərtlər',en:'conditions'})[langKey];
      return absent.length ? [label+': '+absent.map(language=>language.toUpperCase()).join(', ')] : [];
    });
    const translations = row.querySelector('[data-tariff-translation-warning]');
    if (translations) { translations.hidden = !missing.length; translations.textContent = ({ru:'Не заполнены переводы — ',az:'Tərcümələr çatışmır — ',en:'Missing translations — '})[langKey]+missing.join('; '); }
  }

  function updateCardSummary(row, plan, index) {
    updateEditorWarnings(row, plan);
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
      const cleanType = (plan.editor_kind || "empty").replace("_", "-");
      const hasTranslations = plan.title_ru || plan.title_en || plan._show_translations;
      row.className = "owner-tariff-row payment-type--" + cleanType;
      row.dataset.tariffRow = index;

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
      for (const name of ['currency', 'translation']) {
        const notice = document.createElement('p'); notice.className = 'owner-tariff-price-notice';
        notice.setAttribute('data-tariff-'+name+'-warning',''); notice.setAttribute('role','status');
        notice.setAttribute('aria-live','polite'); row.append(notice);
      }
      updateEditorWarnings(row, plan);

      const mainGrid = document.createElement("div");
      mainGrid.className = "owner-tariff-main";
      row.appendChild(mainGrid);
      function section(parent, title, help, attribute) {
        const group=document.createElement('fieldset');group.className='owner-tariff-section';
        if(attribute)group.setAttribute(attribute,'');
        const legend=document.createElement('legend');legend.textContent=title;group.append(legend);
        if(help){const note=document.createElement('p');note.className='owner-tariff-section-help';note.textContent=help;group.append(note);}
        const grid=document.createElement('div');grid.className='owner-tariff-grid';group.append(grid);parent.append(group);return grid;
      }
      const productGrid=section(mainGrid,workflowCopy?.product || labels.kind);
      const paymentGrid=section(mainGrid,workflowCopy?.payment || labels.billingMode,workflowCopy?.paymentHelp);
      const includedGrid=section(mainGrid,workflowCopy?.included || labels.quantity);
      const validityGrid=section(includedGrid,workflowCopy?.validity || labels.validity,workflowCopy?.validityHelp,'data-tariff-validity');
      const unlimitedSlot=document.createElement('div');unlimitedSlot.className='owner-tariff-unlimited-slot';includedGrid.prepend(unlimitedSlot);

      const advanced = document.createElement("details");
      advanced.className = "owner-tariff-advanced";
      advanced.open = plan._advanced_open === true;
      advanced.innerHTML = '<summary><span>' + icons.sliders + ' ' + interfaceCopy.advanced + '</span><small>' + interfaceCopy.advancedHint + '</small></summary>';
      advanced.addEventListener("toggle", () => { plan._advanced_open = advanced.open; });
      const advancedGrid = document.createElement("div");
      advancedGrid.className = "owner-tariff-grid owner-tariff-grid--advanced";
      advanced.appendChild(advancedGrid);
      row.appendChild(advanced);

      const productKeys=new Set(['editor_kind','lesson_format']);
      const paymentKeys=new Set(['price_kind','price','price_min','price_max','currency','billing_mode','billing_interval','billing_interval_count','billing_cycles','is_required']);
      const includedKeys=new Set(['quantity','quantity_unit','is_unlimited']);
      const calendarGrid=section(advancedGrid,workflowCopy?.dates || labels.validFrom,workflowCopy?.datesHelp,'data-tariff-offer-dates');
      const conditions=document.createElement('div');conditions.dataset.kmLanguageGroup='';conditions.className='owner-tariff-conditions';
      const languages=document.createElement('div');languages.className='km-editor-languages';languages.setAttribute('role','group');languages.setAttribute('aria-label',labels.conditionsAz.replace(/\s*\(AZ\)/,''));conditions.append(languages);
      const conditionPanels={};['az','ru','en'].forEach(language=>{const button=document.createElement('button');button.type='button';button.dataset.kmLanguage=language;button.textContent=language.toUpperCase();languages.append(button);const panel=document.createElement('div');panel.dataset.kmLanguagePanel=language;conditionPanels[language]=panel;conditions.append(panel);});
      fields.forEach((field) => {
        const conditionLanguage=field[0].match(/^conditions_(az|ru|en)$/)?.[1];
        if(conditionLanguage&&!conditions.parentElement)advancedGrid.append(conditions);
        const key=field[0];
        const target = conditionLanguage ? conditionPanels[conditionLanguage] : productKeys.has(key) ? productGrid : paymentKeys.has(key) ? paymentGrid : key==='is_unlimited' ? unlimitedSlot : includedKeys.has(key) ? includedGrid : key.startsWith('validity_') ? validityGrid : ['valid_from','valid_until'].includes(key) ? calendarGrid : advancedGrid;
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
            row.querySelectorAll('.owner-tariff-field--title_ru,.owner-tariff-field--title_en').forEach(node=>node.classList.remove('owner-tariff-field--hidden'));
            toggleWrapper.hidden=true;
            row.querySelector('[data-tariff-key=title_ru]')?.focus({preventScroll:true});
          });

          toggleWrapper.appendChild(toggleBtn);
          advancedGrid.appendChild(toggleWrapper);
        }
      });
      // Keep the quantity pair before the grouped usage period without moving
      // any field in response to an entered value.
      includedGrid.append(validityGrid.parentElement);
      validityGrid.prepend(validityGrid.querySelector('.owner-tariff-field--validity_interval_count'));
      advancedGrid.append(calendarGrid.parentElement);
      ['price_kind','price','price_min','price_max','currency','billing_mode','billing_interval','billing_interval_count','billing_cycles','is_required'].forEach(key=>paymentGrid.append(paymentGrid.querySelector('.owner-tariff-field--'+key)));

      const footer = document.createElement("div");
      footer.className = "owner-tariff-footer";

      const active = document.createElement("label");
      active.className = "owner-tariff-active";
      active.innerHTML = '<input type="checkbox"> <span>' + labels.active + '</span>';
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
        button.setAttribute("aria-label", item[1]);
        button.innerHTML = item[0];
        button.disabled = index + item[2] < 0 || index + item[2] >= plans.length;
        button.addEventListener("click", () => { const target = index + item[2]; [plans[index], plans[target]] = [plans[target], plans[index]]; plans.forEach((p,i)=>p.sort_order=i); render(); sync(); });
        actions.appendChild(button);
      });

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "owner-tariff-remove";
      remove.title = labels.remove;
      remove.setAttribute("aria-label", labels.remove);
      remove.innerHTML = icons.trash;
      remove.addEventListener('click', () => {
        const warning = ({az:'Bu tarifi silmək?',en:'Remove this plan?',ru:'Удалить этот тариф?'})[langKey];
        if (!window.confirm(warning)) return;
        plans.splice(index,1); render(); sync();
      });
      actions.appendChild(remove);

      footer.appendChild(actions);
      row.appendChild(footer);
      list.appendChild(row);
    });
    add.disabled = plans.length >= MAX_PRICING_PLANS;
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
      prepareView(plans[plans.length-1]);
      sync();
      render();
      const firstField = list.lastElementChild && list.lastElementChild.querySelector("[data-tariff-key]");
      if (firstField) firstField.focus();
    }
  });

  // JSON import and other form helpers update the hidden field after this
  // editor has already loaded. Rehydrate the editor instead of letting its
  // stale in-memory copy overwrite the imported tariffs on the next action.
  const presetButtons = editor.querySelectorAll("[data-badge-preset-az], [data-badge-preset]");
  presetButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const azInput = document.getElementById("id_custom_price_badge_az");
      const ruInput = document.getElementById("id_custom_price_badge_ru");
      const enInput = document.getElementById("id_custom_price_badge_en");
      if (azInput) azInput.value = button.dataset.badgePresetAz || "";
      if (ruInput) ruInput.value = button.dataset.badgePresetRu || "";
      if (enInput) enInput.value = button.dataset.badgePresetEn || "";
    });
  });

  input.addEventListener("input", () => {
    plans = parsePlans(input.value).map(prepareView);
    render();
  });
  const modeInput = ownerForm?.querySelector('[name="price_mode"]');
  editor.kidsmapPricingSummary = () => plans.filter(p => p.is_active !== false && !p.is_trial && (!p.charge_role || p.charge_role === 'primary')).map((p,i)=>tariffSummary(p,i).meta).join('; ') || '—';
  const policyButtons = editor.querySelectorAll('[data-price-policy]');
  const policyCopy = {
    ru:{heading:'Тарифы места',paid:'Платные услуги',add:'Добавить тариф',addPaid:'Добавить платную услугу',paidHint:'Вход бесплатный. Добавьте цены только на платные услуги: например аттракцион, прокат или занятие. У каждой услуги — свои цена, период оплаты и условия.'},
    az:{heading:'Məkanın tarifləri',paid:'Ödənişli xidmətlər',add:'Tarif əlavə et',addPaid:'Ödənişli xidmət əlavə et',paidHint:'Giriş pulsuzdur. Yalnız ödənişli xidmətlərin qiymətlərini əlavə edin: məsələn attraksion, icarə və ya məşğələ. Hər xidmətin öz qiyməti, ödəniş dövrü və şərtləri var.'},
    en:{heading:'Place pricing plans',paid:'Paid services',add:'Add a plan',addPaid:'Add a paid service',paidHint:'Entry is free. Add prices only for paid services, such as a ride, rental or lesson. Each service has its own price, billing period and conditions.'},
  }[langKey];
  const heading=editor.querySelector('[data-tariff-heading]'),description=editor.querySelector('[data-tariff-description]'),defaultDescription=description?.textContent||'';
  const eventCopy={
    ru:{title:'Цена зависит от мероприятия',description:'У места нет постоянного тарифа. Стоимость указывается отдельно для каждого мероприятия.',badgeNote:'Необязательно: свой текст о стоимости мероприятий',badgeHint:'Оставьте поля пустыми — посетители увидят «Цена зависит от мероприятия». Свой текст нужен только для дополнительного пояснения; стоимость каждого мероприятия укажите в его карточке.',automatic:'Автоматически по режиму цены',preserved:'Ранее добавленные тарифы сохранены. Их можно снова показать, выбрав режим «Есть тарифы».'},
    az:{title:'Qiymət tədbirdən asılıdır',description:'Məkanın daimi tarifi yoxdur. Qiymət hər tədbir üçün ayrıca göstərilir.',badgeNote:'Məcburi deyil: tədbirlərin qiyməti haqqında öz mətniniz',badgeHint:'Sahələri boş saxlayın — ziyarətçilər «Qiymət tədbirdən asılıdır» görəcəklər. Öz mətniniz yalnız əlavə izah üçündür; hər tədbirin qiymətini onun səhifəsində göstərin.',automatic:'Qiymət rejiminə uyğun avtomatik',preserved:'Əvvəlki tariflər saxlanılıb. Onları yenidən göstərmək üçün «Tariflər var» rejimini seçin.'},
    en:{title:'Price depends on the event',description:'This place has no permanent pricing plan. The price is specified separately for each event.',badgeNote:'Optional: your own text about event prices',badgeHint:'Leave these fields blank to show “Price depends on the event”. Use custom text only for an additional explanation; enter each event’s price on its own page.',automatic:'Automatic for this pricing mode',preserved:'Previously added plans are preserved. Choose the pricing plans mode to show them again.'}
  }[langKey];
  const badgeNote=editor.querySelector('[data-price-badge-note]'),badgeHint=editor.querySelector('[data-price-badge-hint]'),automaticBadge=editor.querySelector('[data-badge-preset]');
  const defaultBadgeNote=badgeNote?.textContent||'',defaultAutomaticBadge=automaticBadge?.textContent||'';
  const badgeInputs=['az','ru','en'].map(code=>({code,input:ownerForm?.querySelector(`[name="custom_price_badge_${code}"]`)})).filter(row=>row.input);
  badgeInputs.forEach(row=>row.placeholder=row.input.getAttribute('placeholder'));
  const eventPlaceholders={az:'Məsələn: Qiyməti tədbirin səhifəsində yoxlayın',ru:'Например: Стоимость уточняйте в карточке мероприятия',en:'For example: See the event page for its price'};
  let addLabel=add.querySelector('[data-tariff-add-label]');
  if(!addLabel){addLabel=document.createElement('span');addLabel.dataset.tariffAddLabel='';[...add.childNodes].filter(node=>node.nodeType===3).forEach(node=>node.remove());add.append(addLabel);}
  function updatePolicy() {
    const mode = modeInput?.value || 'tariffs';
    policyButtons.forEach(button => {const selected = button.dataset.pricePolicy === mode; button.classList.toggle('is-active',selected); button.setAttribute('aria-pressed',String(selected));});
    const noTariffs = mode === 'free' || mode === 'events';
    const paidServices = mode === 'free_entry_paid_services';
    if(heading){heading.textContent=paidServices?policyCopy.paid:policyCopy.heading;heading.hidden=noTariffs;}
    if(description){description.textContent=paidServices?policyCopy.paidHint:defaultDescription;description.hidden=noTariffs;}
    addLabel.textContent=paidServices?policyCopy.addPaid:policyCopy.add;
    list.hidden = noTariffs;
    add.hidden = noTariffs;
    editor.querySelectorAll('[data-tariff-free-state]').forEach(el => el.hidden = mode !== 'free');
    editor.querySelectorAll('[data-tariff-events-state]').forEach(el => el.hidden = mode !== 'events');
    const eventTitle=editor.querySelector('[data-price-events-title]'),eventDescription=editor.querySelector('[data-price-events-description]');
    if(eventTitle)eventTitle.textContent=eventCopy.title;
    if(eventDescription)eventDescription.textContent=eventCopy.description+(mode==='events'&&plans.length?' '+eventCopy.preserved:'');
    editor.querySelectorAll('[data-tariff-computed]').forEach(el=>el.hidden=noTariffs);
    if(badgeNote)badgeNote.textContent=mode==='events'?eventCopy.badgeNote:defaultBadgeNote;
    if(badgeHint){badgeHint.hidden=mode!=='events';badgeHint.textContent=eventCopy.badgeHint;}
    if(automaticBadge)automaticBadge.textContent=mode==='events'?eventCopy.automatic:defaultAutomaticBadge;
    badgeInputs.forEach(row=>{if(mode==='events')row.input.setAttribute('placeholder',eventPlaceholders[row.code]);else if(row.placeholder===null)row.input.removeAttribute('placeholder');else row.input.setAttribute('placeholder',row.placeholder);});
    presetButtons.forEach(button=>button.hidden=mode==='events'&&!button.hasAttribute('data-badge-preset')&&!['Цена зависит от мероприятия','Цена уточняется'].includes(button.dataset.badgePresetRu));
    editor.querySelectorAll('[data-tariff-empty]').forEach(el => el.hidden = noTariffs || plans.length > 0);
    const hint = editor.querySelector('[data-price-policy-hint]');
    if (hint) {hint.textContent = mode==='free' && plans.length ? ({az:'Saxlanmış tariflər silinmir.',en:'Saved plans are preserved.',ru:'Сохранённые тарифы не удаляются.'})[langKey] : '';hint.hidden=!hint.textContent;}
  }
  policyButtons.forEach(button => button.addEventListener('click',()=>{
    if (!modeInput) return;
    modeInput.value = button.dataset.pricePolicy;
    modeInput.dispatchEvent(new Event('input',{bubbles:true}));
    modeInput.dispatchEvent(new Event('change',{bubbles:true}));
    updatePolicy();
  }));
  modeInput?.addEventListener('change',updatePolicy);
  input.addEventListener('km:pricing-change',()=>{
    const summary = editor.querySelector('[data-tariff-computed-value]');
    if (summary) summary.textContent = plans.map((p,i)=>tariffSummary(p,i).meta).join(' · ') || '—';
    updatePolicy();
  });
  render();
  updatePolicy();
  const initialSummary = editor.querySelector('[data-tariff-computed-value]');
  if (initialSummary) initialSummary.textContent = editor.kidsmapPricingSummary();
})();
