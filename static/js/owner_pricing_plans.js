(function () {
  const MAX_PRICING_PLANS = 12;
  const editor = document.querySelector("[data-tariff-editor]");
  if (!editor) return;
  const ownerForm = editor.closest("form");
  const input = editor.querySelector("[data-tariff-input]")
    || (ownerForm && ownerForm.querySelector("[data-tariff-input]"))
    || document.getElementById("id_pricing_plans");
  const list = editor.querySelector("[data-tariff-list]");
  const emptyState = editor.querySelector("[data-tariff-empty]");
  const emptyTitle = editor.querySelector("[data-tariff-empty-title]");
  const emptyDesc = editor.querySelector("[data-tariff-empty-desc]");
  const add = editor.querySelector("[data-tariff-add]");
  const foot = editor.querySelector(".km-pf-tariffs__foot");
  const computedBadge = editor.querySelector("[data-tariff-computed-value]");
  const policyButtons = editor.querySelectorAll("[data-price-policy]");
  const policyHint = editor.querySelector("[data-price-policy-hint]");
  const azBadgeInput = document.getElementById("id_custom_price_badge_az");
  const ruBadgeInput = document.getElementById("id_custom_price_badge_ru");
  const enBadgeInput = document.getElementById("id_custom_price_badge_en");
  const priceModeInput = document.getElementById("id_price_mode");
  const canVerify = editor.dataset.canVerify === "1";
  if (!input || !list || !add) return;

  const langKey = (document.documentElement.lang || "ru").split("-")[0].toLowerCase();

  const pricingI18n = {
    az: {
      tariff: "Tarif",
      chooseType: "Növü seçin",
      noPrice: "Qiymət göstərilməyib",
      free: "Pulsuz",
      from: "başlayaraq",
      onRequest: "Sorğu ilə",
      format: "Format",
      group: "Qrup",
      individual: "Fərdi",
      openVisit: "Sərbəst giriş",
      paymentType: "Ödəniş növü",
      perLesson: "Dərs üzrə",
      perMonth: "Aylıq",
      package: "Paket",
      admission: "Giriş bileti",
      visit: "Tək ziyarət",
      course: "Kurs",
      camp: "Düşərgə",
      event: "Tədbir",
      periodMonth: "ay",
      periodLesson: "dərs",
      periodLessons: "dərs",
      periodPackage: "paket",
      periodTicket: "bilet",
      periodVisit: "ziyarət",
      periodCourse: "kurs",
      sessionsMonth: "Aylıq dərs sayı",
      sessionsWeek: "Həftəlik dərs sayı",
      sessionsPackage: "Paketdə dərs sayı",
      sessionsCourse: "Kursda dərs sayı",
      price: "Qiymət (AZN)",
      titleAz: "Tarifin adı (AZ)",
      titleRu: "Tarifin adı (RU)",
      titleEn: "Tarifin adı (EN)",
      conditionsAz: "Qısa təsvir / qeyd (AZ)",
      conditionsRu: "Qısa təsvir / qeyd (RU)",
      conditionsEn: "Qısa təsvir / qeyd (EN)",
      collapse: "Yığcamlaşdır",
      edit: "Düzəliş et",
      copy: "Kopyala",
      delete: "Sil",
      active: "Aktivdir",
      statusActive: "Aktiv",
      statusInactive: "Qeyri-aktiv",
      moveUp: "Yuxarı",
      moveDown: "Aşağı",
      advanced: "Əlavə şərtlər",
      advancedHint: "auditoriya, müddət, yaş, mənbə",
      translationsTitle: "Tərcümələr (RU / EN)",
      priceKind: "Qiymət növü",
      exact: "Dəqiq",
      range: "Aralıq",
      priceMin: "Qiymət min",
      priceMax: "Qiymət max",
      currency: "Valyuta",
      validity: "Qüvvədə olma müddəti",
      ageFrom: "Yaş min",
      ageTo: "Yaş max",
      sourceUrl: "Mənbə linki",
      calculatedCardPrice: "Kartda qiymət:",
      freeAdmission: "Giriş pulsuzdur",
      dependsOnEvent: "Qiymət tədbirdən asılıdır",
      hintFree: "Məkan ziyarət üçün tamamilə pulsuzdur. Tarif tələb olunmur.",
      hintTariffs: "Əsas tarifləri və qiymətləri qeyd edin.",
      hintFreeWithPaid: "Məkana giriş pulsuzdur. Lazım olduqda ödənişli xidmət və ya attraksionların qiymətlərini əlavə edə bilərsiniz (məcburi deyil).",
      hintEvents: "Bu məkanın daimi qiyməti yoxdur. Qiymət hər tədbir üçün ayrıca göstərilir.",
      emptyDefaultTitle: "Tariflər əlavə edilməyib",
      emptyDefaultDesc: "Ən azı bir tarif əlavə edin və ya məkanı pulsuz olaraq qeyd edin.",
      emptyFreeWithPaidDesc: "Ödənişli xidmətlər əlavə edilməyib (məcburi deyil, çünki giriş pulsuzdur).",
    },
    en: {
      tariff: "Plan",
      chooseType: "Choose type",
      noPrice: "Price not specified",
      free: "Free",
      from: "from",
      onRequest: "On request",
      format: "Format",
      group: "Group",
      individual: "Individual",
      openVisit: "Open visit",
      paymentType: "Payment type",
      perLesson: "Per lesson",
      perMonth: "Monthly",
      package: "Package",
      admission: "Admission",
      visit: "Single visit",
      course: "Course",
      camp: "Camp",
      event: "Event",
      periodMonth: "month",
      periodLesson: "lesson",
      periodLessons: "sessions",
      periodPackage: "package",
      periodTicket: "ticket",
      periodVisit: "visit",
      periodCourse: "course",
      sessionsMonth: "Sessions / month",
      sessionsWeek: "Sessions / week",
      sessionsPackage: "Sessions in package",
      sessionsCourse: "Sessions in course",
      price: "Price (AZN)",
      titleAz: "Plan title (AZ)",
      titleRu: "Plan title (RU)",
      titleEn: "Plan title (EN)",
      conditionsAz: "Short note / description (AZ)",
      conditionsRu: "Short note / description (RU)",
      conditionsEn: "Short note / description (EN)",
      collapse: "Collapse",
      edit: "Edit",
      copy: "Duplicate",
      delete: "Delete",
      active: "Active",
      statusActive: "Active",
      statusInactive: "Inactive",
      moveUp: "Move up",
      moveDown: "Move down",
      advanced: "Additional terms",
      advancedHint: "audience, validity, age, source",
      translationsTitle: "Translations (RU / EN)",
      priceKind: "Price kind",
      exact: "Exact",
      range: "Range",
      priceMin: "Price from",
      priceMax: "Price to",
      currency: "Currency",
      validity: "Validity duration",
      ageFrom: "Age from",
      ageTo: "Age to",
      sourceUrl: "Source URL",
      calculatedCardPrice: "Card price:",
      freeAdmission: "Free admission",
      dependsOnEvent: "Price depends on event",
      hintFree: "The venue is completely free to visit. No pricing plans required.",
      hintTariffs: "Specify primary pricing plans and admission rates.",
      hintFreeWithPaid: "Entrance is free. You can add pricing for optional paid services or attractions below (optional).",
      hintEvents: "This place has no fixed price. Pricing is specified separately for each event.",
      emptyDefaultTitle: "No plans added",
      emptyDefaultDesc: "Add at least one plan or mark the place as free.",
      emptyFreeWithPaidDesc: "No paid services added (optional, as admission is free).",
    },
    ru: {
      tariff: "Тариф",
      chooseType: "Выберите тип",
      noPrice: "Цена не указана",
      free: "Бесплатно",
      from: "от",
      onRequest: "По запросу",
      format: "Формат",
      group: "Групповые",
      individual: "Индивидуальные",
      openVisit: "Свободное посещение",
      paymentType: "Тип оплаты",
      perLesson: "За занятие",
      perMonth: "За месяц",
      package: "Пакет",
      admission: "Входной билет",
      visit: "Разовое посещение",
      course: "Курс",
      camp: "Лагерь",
      event: "Событие",
      periodMonth: "месяц",
      periodLesson: "занятие",
      periodLessons: "занятий",
      periodPackage: "пакет",
      periodTicket: "билет",
      periodVisit: "посещение",
      periodCourse: "курс",
      sessionsMonth: "Занятий в месяц",
      sessionsWeek: "Занятий в неделю",
      sessionsPackage: "Занятий в пакете",
      sessionsCourse: "Занятий в курсе",
      price: "Цена (AZN)",
      titleAz: "Название тарифа (AZ)",
      titleRu: "Название тарифа (RU)",
      titleEn: "Название тарифа (EN)",
      conditionsAz: "Краткое описание / примечание (AZ)",
      conditionsRu: "Краткое описание / примечание (RU)",
      conditionsEn: "Краткое описание / примечание (EN)",
      collapse: "Свернуть",
      edit: "Редактировать",
      copy: "Дублировать",
      delete: "Удалить",
      active: "Активен",
      statusActive: "Активен",
      statusInactive: "Неактивен",
      moveUp: "Выше",
      moveDown: "Ниже",
      advanced: "Дополнительные условия",
      advancedHint: "аудитория, сроки, возраст, источник",
      translationsTitle: "Переводы названия и описания (RU / EN)",
      priceKind: "Как указана цена",
      exact: "Точная",
      range: "Диапазон",
      priceMin: "Цена от",
      priceMax: "Цена до",
      currency: "Валюта",
      validity: "Срок действия",
      ageFrom: "Возраст от",
      ageTo: "Возраст до",
      sourceUrl: "Источник",
      calculatedCardPrice: "Цена на карточке:",
      freeAdmission: "Вход бесплатный",
      dependsOnEvent: "Цена зависит от мероприятия",
      hintFree: "Место полностью бесплатное для посещения. Тарифы не требуются.",
      hintTariffs: "Укажите основные тарифы и стоимость посещения.",
      hintFreeWithPaid: "Вход на территорию бесплатный. Ниже вы можете указать тарифы на платные услуги или аттракционы (необязательно).",
      hintEvents: "У этого места нет постоянной цены. Стоимость указывается отдельно для каждого мероприятия.",
      emptyDefaultTitle: "Тарифы не добавлены",
      emptyDefaultDesc: "Добавьте хотя бы один тариф или отметьте место как бесплатное — без этого карточку нельзя опубликовать.",
      emptyFreeWithPaidDesc: "Платные услуги не добавлены (необязательно, так как вход бесплатный).",
    },
  };

  const labels = pricingI18n[langKey] || pricingI18n.ru;

  function makeSvgIcon(id, className) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", className || "km-i");
    svg.setAttribute("viewBox", "0 0 960 960");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", "#kmi-" + id);
    svg.appendChild(use);
    return svg;
  }

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

  function normalizeKind(plan) {
    if (!plan.editor_kind) {
      if (plan.payment_type === "package" || (plan.product_type === "lesson" && Number(plan.quantity) > 1)) {
        plan.editor_kind = "package";
      } else {
        plan.editor_kind = plan.product_type || ({
          per_lesson: "lesson",
          per_month: "membership",
          per_visit: "visit",
          entry_ticket: "admission",
        }[plan.payment_type]) || "lesson";
      }
    }
    if (!plan.lesson_format) {
      plan.lesson_format = "group";
    }
    plan.product_type = plan.editor_kind === "package" ? "lesson" : plan.editor_kind;
    plan.charge_role = ["addon", "registration_fee", "deposit"].indexOf(plan.product_type) >= 0 ? plan.product_type : "primary";

    if (plan.editor_kind === "package") {
      plan.quantity_unit = "lesson";
      if (!plan.quantity && plan.package_sessions) plan.quantity = plan.package_sessions;
    }
    if (!plan.price_kind) plan.price_kind = String(plan.price) === "0" ? "free" : "exact";
    if (!plan.billing_mode) plan.billing_mode = plan.editor_kind === "membership" || plan.payment_type === "per_month" ? "recurring" : "one_time";
    if (plan.billing_mode === "recurring" && !plan.billing_interval) {
      plan.billing_interval = "month";
      plan.billing_interval_count = 1;
    }
    if (plan.price_kind === "exact") { plan.price_min = null; plan.price_max = null; }
    if (plan.price_kind === "free") { plan.price = "0"; plan.price_min = null; plan.price_max = null; }
    if (plan.price_kind === "from") { plan.price = null; plan.price_max = null; }
    if (plan.price_kind === "range") { plan.price = null; }
    if (plan.price_kind === "on_request") { plan.price = null; plan.price_min = null; plan.price_max = null; }
    if (!plan.currency) plan.currency = "AZN";

    delete plan.payment_type;
    delete plan.package_sessions;
  }

  plans.forEach(normalizeKind);

  function sync() {
    plans.forEach((plan, index) => { plan.sort_order = index; });
    plans.forEach(normalizeKind);
    const contentKeys = [
      "editor_kind", "product_type", "price_kind", "price", "price_min", "price_max",
      "title_az", "title_ru", "title_en", "conditions_az", "conditions_ru", "conditions_en",
      "sessions_per_week", "sessions_per_month", "quantity", "quantity_unit",
      "age_from", "age_to", "source_url", "lesson_format", "billing_mode"
    ];
    const cleanPlans = plans
      .filter((plan) => contentKeys.some((key) => plan[key] !== "" && plan[key] !== null && plan[key] !== undefined))
      .map((plan) => Object.fromEntries(Object.entries(plan).filter(([key]) => !key.startsWith("_"))));

    input.value = JSON.stringify(cleanPlans);
    input.dispatchEvent(new Event("change", { bubbles: true }));
    updateComputedPrice();
  }

  function getKindLabel(kind) {
    const map = {
      lesson: labels.perLesson,
      membership: labels.perMonth,
      package: labels.package,
      admission: labels.admission,
      visit: labels.visit,
      course: labels.course,
      camp: labels.camp,
      event: labels.event,
    };
    return map[kind] || labels.perLesson;
  }

  function getFormatLabel(format) {
    const map = {
      group: labels.group,
      individual: labels.individual,
      open_visit: labels.openVisit,
    };
    return map[format] || labels.group;
  }

  function formatPriceWithPeriod(plan) {
    if (plan.price_kind === "free" || String(plan.price).trim() === "0") {
      return labels.free;
    }
    if (plan.price_kind === "on_request") {
      return labels.onRequest;
    }
    let pStr = "";
    if (plan.price_kind === "range" && plan.price_min && plan.price_max) {
      pStr = plan.price_min + "–" + plan.price_max + " ₼";
    } else if (plan.price_kind === "from" && plan.price_min) {
      pStr = labels.from + " " + plan.price_min + " ₼";
    } else if (plan.price !== "" && plan.price !== null && plan.price !== undefined && !isNaN(Number(plan.price))) {
      pStr = Number(plan.price) + " ₼";
    } else {
      return labels.noPrice;
    }

    const periods = {
      membership: "/ " + labels.periodMonth,
      lesson: "/ " + labels.periodLesson,
      package: plan.quantity ? ("/ " + plan.quantity + " " + labels.periodLessons) : ("/ " + labels.periodPackage),
      admission: "/ " + labels.periodTicket,
      visit: "/ " + labels.periodVisit,
      course: "/ " + labels.periodCourse,
    };
    const suffix = periods[plan.editor_kind] || "";
    return suffix ? (pStr + " " + suffix) : pStr;
  }

  function tariffSummary(plan, index) {
    let title = plan.title_az || plan.title_ru || plan.title_en;
    if (!title) {
      if (plan.editor_kind === "membership") title = "Абонемент на месяц";
      else if (plan.editor_kind === "package") title = "Пакет занятий";
      else if (plan.editor_kind === "lesson") title = "Пробное / разовое занятие";
      else title = labels.tariff + " #" + (index + 1);
    }

    let meta = "";
    if (plan.conditions_ru || plan.conditions_az || plan.conditions_en) {
      meta = plan.conditions_ru || plan.conditions_az || plan.conditions_en;
    } else if (plan.editor_kind === "membership") {
      if (plan.sessions_per_month) meta = plan.sessions_per_month + " занятий";
      else if (plan.sessions_per_week) meta = plan.sessions_per_week + " раза в неделю";
    } else if (plan.editor_kind === "package") {
      if (plan.quantity) meta = plan.quantity + " занятий";
    } else if (plan.editor_kind === "lesson") {
      meta = "1 занятие";
    }

    return {
      title: title,
      format: getFormatLabel(plan.lesson_format),
      kind: getKindLabel(plan.editor_kind),
      meta: meta,
      price: formatPriceWithPeriod(plan),
    };
  }

  function detectPricePolicy() {
    if (priceModeInput && priceModeInput.value) {
      const mode = priceModeInput.value.trim();
      if (mode === "free") return "free";
      if (mode === "free_entry_paid_services" || mode === "free_admission_with_paid") return "free_entry_paid_services";
      if (mode === "events") return "events";
      if (mode === "tariffs") return "tariffs";
    }

    const az = (azBadgeInput ? azBadgeInput.value : "").trim();
    const ru = (ruBadgeInput ? ruBadgeInput.value : "").trim();
    const en = (enBadgeInput ? enBadgeInput.value : "").trim();

    if (ru === "Бесплатно" || az === "Pulsuz" || en === "Free") {
      return "free";
    }
    if (ru === "Вход бесплатный" || az === "Giriş pulsuzdur" || en === "Free admission") {
      return "free_entry_paid_services";
    }
    if (ru === "Цена зависит от мероприятия" || az === "Qiymət tədbirdən asılıdır" || en === "Price depends on event") {
      return "events";
    }
    return "tariffs";
  }

  let currentPolicy = detectPricePolicy();

  function setBadgeInputs(az, ru, en) {
    if (azBadgeInput) azBadgeInput.value = az;
    if (ruBadgeInput) ruBadgeInput.value = ru;
    if (enBadgeInput) enBadgeInput.value = en;
    if (azBadgeInput) azBadgeInput.dispatchEvent(new Event("input", { bubbles: true }));
    if (ruBadgeInput) ruBadgeInput.dispatchEvent(new Event("input", { bubbles: true }));
    if (enBadgeInput) enBadgeInput.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function applyPricePolicy(policy, userTriggered) {
    if (policy === "free_admission_with_paid") {
      policy = "free_entry_paid_services";
    }
    currentPolicy = policy;
    if (priceModeInput && priceModeInput.value !== policy) {
      priceModeInput.value = policy;
      priceModeInput.dispatchEvent(new Event("input", { bubbles: true }));
      priceModeInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
    policyButtons.forEach((btn) => {
      const btnPolicy = btn.dataset.pricePolicy === "free_admission_with_paid" ? "free_entry_paid_services" : btn.dataset.pricePolicy;
      btn.classList.toggle("is-active", btnPolicy === policy);
    });

    if (policy === "free") {
      if (policyHint) policyHint.textContent = labels.hintFree;
      if (list) list.hidden = true;
      if (emptyState) emptyState.hidden = true;
      if (foot) foot.hidden = true;
    } else if (policy === "free_entry_paid_services") {
      if (policyHint) policyHint.textContent = labels.hintFreeWithPaid;
      if (list) list.hidden = false;
      if (emptyDesc) emptyDesc.textContent = labels.emptyFreeWithPaidDesc;
      if (emptyState) emptyState.hidden = plans.length > 0;
      if (foot) foot.hidden = false;
    } else if (policy === "events") {
      if (policyHint) policyHint.textContent = labels.hintEvents;
      if (list) list.hidden = true;
      if (emptyState) emptyState.hidden = true;
      if (foot) foot.hidden = true;
    } else {
      // Tariffs
      if (policyHint) policyHint.textContent = labels.hintTariffs;
      if (list) list.hidden = false;
      if (emptyDesc) emptyDesc.textContent = labels.emptyDefaultDesc;
      if (emptyState) emptyState.hidden = plans.length > 0;
      if (foot) foot.hidden = false;
    }

    updateComputedPrice();
  }

  function planHasData(plan) {
    if (!plan) return false;
    return Boolean(
      (plan.price !== undefined && plan.price !== null && String(plan.price).trim() !== "") ||
      (plan.price_min !== undefined && plan.price_min !== null && String(plan.price_min).trim() !== "") ||
      (plan.price_max !== undefined && plan.price_max !== null && String(plan.price_max).trim() !== "") ||
      (plan.title_az && plan.title_az.trim()) ||
      (plan.title_ru && plan.title_ru.trim()) ||
      (plan.title_en && plan.title_en.trim()) ||
      (plan.conditions_az && plan.conditions_az.trim()) ||
      (plan.conditions_ru && plan.conditions_ru.trim()) ||
      (plan.conditions_en && plan.conditions_en.trim()) ||
      plan.id
    );
  }

  function confirmDeletePlan(index) {
    const plan = plans[index];
    if (!plan) return;
    if (!planHasData(plan)) {
      plans.splice(index, 1);
      sync();
      render();
      return;
    }

    if (window.kmModal) {
      window.kmModal.show({
        icon: "delete",
        iconTone: "danger",
        title: "Удалить тариф?",
        message: "Данные этого тарифа будут удалены.",
        actions: [
          { label: "Отмена", tone: "quiet" },
          {
            label: "Удалить",
            tone: "danger-filled",
            onClick: function () {
              plans.splice(index, 1);
              sync();
              render();
              if (window.kmToast) window.kmToast.info("Тариф удалён");
            }
          }
        ]
      });
    } else {
      plans.splice(index, 1);
      sync();
      render();
    }
  }

  policyButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const rawPolicy = btn.dataset.pricePolicy;
      const targetPolicy = rawPolicy === "free_admission_with_paid" ? "free_entry_paid_services" : rawPolicy;
      if (targetPolicy === currentPolicy) return;

      if ((targetPolicy === "free" || targetPolicy === "events") && plans.length > 0) {
        var count = plans.length;
        var countText = count + (count === 1 ? " тариф." : (count < 5 ? " тарифа." : " тарифов."));
        if (window.kmModal) {
          window.kmModal.show({
            icon: "help",
            iconTone: "warn",
            title: "Что сделать с существующими тарифами?",
            message: "В карточке уже есть " + countText,
            actions: [
              {
                label: "Отмена",
                tone: "quiet"
              },
              {
                label: "Сохранить тарифы, но отключить",
                tone: "primary",
                onClick: function () {
                  plans.forEach(function (p) { p.is_active = false; });
                  sync();
                  render();
                  applyPricePolicy(targetPolicy, true);
                  if (window.kmToast) window.kmToast.info("Тарифы отключены и сохранены");
                }
              },
              {
                label: "Удалить тарифы",
                tone: "danger-filled",
                onClick: function () {
                  plans = [];
                  sync();
                  render();
                  applyPricePolicy(targetPolicy, true);
                  if (window.kmToast) window.kmToast.info("Тарифы удалены");
                }
              }
            ]
          });
          return;
        }
      }

      applyPricePolicy(targetPolicy, true);
    });
  });

  if (priceModeInput) {
    priceModeInput.addEventListener("change", () => {
      const val = priceModeInput.value.trim();
      const target = val === "free_admission_with_paid" ? "free_entry_paid_services" : val;
      if (target && target !== currentPolicy) {
        applyPricePolicy(target, false);
      }
    });
  }

  function updateComputedPrice() {
    if (!computedBadge) return;

    if (currentPolicy === "free") {
      computedBadge.textContent = labels.free;
      syncPreviewPrice(labels.free);
      return;
    }

    if (currentPolicy === "free_entry_paid_services" || currentPolicy === "free_admission_with_paid") {
      computedBadge.textContent = labels.freeAdmission;
      syncPreviewPrice(labels.freeAdmission);
      return;
    }

    if (currentPolicy === "events") {
      computedBadge.textContent = labels.dependsOnEvent;
      syncPreviewPrice(labels.dependsOnEvent);
      return;
    }

    const activePlans = plans.filter((p) => p.is_active !== false);
    if (!activePlans.length) {
      computedBadge.textContent = "—";
      syncPreviewPrice("—");
      return;
    }

    const prices = [];
    let hasFree = false;
    let hasOnRequest = false;

    activePlans.forEach((p) => {
      if (p.price_kind === "free" || String(p.price).trim() === "0") {
        hasFree = true;
        prices.push(0);
      } else if (p.price_kind === "on_request") {
        hasOnRequest = true;
      } else if (p.price_kind === "range" && p.price_min && p.price_max) {
        const minVal = parseFloat(p.price_min);
        const maxVal = parseFloat(p.price_max);
        if (!isNaN(minVal)) prices.push(minVal);
        if (!isNaN(maxVal)) prices.push(maxVal);
      } else if (p.price_kind === "from" && p.price_min) {
        const minVal = parseFloat(p.price_min);
        if (!isNaN(minVal)) prices.push(minVal);
      } else if (p.price !== "" && p.price !== null && p.price !== undefined) {
        const val = parseFloat(p.price);
        if (!isNaN(val)) {
          if (val === 0) hasFree = true;
          prices.push(val);
        }
      }
    });

    let computedText = "—";
    if (!prices.length) {
      if (hasFree) computedText = labels.free;
      else if (hasOnRequest) computedText = labels.onRequest;
      else computedText = "—";
    } else {
      const min = Math.min.apply(null, prices);
      const max = Math.max.apply(null, prices);

      if (min === max) {
        if (min === 0) {
          computedText = labels.free;
        } else {
          computedText = min + " ₼";
        }
      } else {
        computedText = min + "–" + max + " ₼";
      }
    }

    computedBadge.textContent = computedText;
    syncPreviewPrice(computedText);
  }

  function syncPreviewPrice(computedText) {
    const previewPriceEl = document.querySelector("[data-pf-preview-price]");
    if (previewPriceEl) {
      const customAz = (azBadgeInput || {}).value;
      const customRu = (ruBadgeInput || {}).value;
      const customEn = (enBadgeInput || {}).value;
      const custom = (langKey === "az" ? customAz : (langKey === "en" ? customEn : customRu)) || customAz || customRu || customEn;
      previewPriceEl.textContent = custom || (computedText !== "—" ? computedText : previewPriceEl.dataset.default || "—");
    }
  }

  function render() {
    list.innerHTML = "";
    if (emptyState) {
      emptyState.hidden = plans.length > 0 || currentPolicy === "free" || currentPolicy === "events";
    }

    plans.forEach((plan, index) => {
      normalizeKind(plan);
      const summary = tariffSummary(plan, index);
      const row = document.createElement("div");
      row.className = "owner-tariff-row";

      if (plan._is_open !== true) {
        // Collapsed state
        row.classList.add("is-collapsed");
        if (plan.is_active === false) {
          row.classList.add("is-inactive");
        }

        const drag = document.createElement("span");
        drag.className = "owner-tariff-drag";
        drag.appendChild(makeSvgIcon("drag_indicator"));
        row.appendChild(drag);

        const titleBox = document.createElement("div");
        titleBox.className = "owner-tariff-title-box";
        const titleStrong = document.createElement("strong");
        titleStrong.className = "owner-tariff-title";
        titleStrong.textContent = summary.title;
        const formatSmall = document.createElement("small");
        formatSmall.className = "owner-tariff-format";
        formatSmall.textContent = summary.format;
        titleBox.append(titleStrong, formatSmall);
        row.appendChild(titleBox);

        const kindBadge = document.createElement("span");
        kindBadge.className = "owner-tariff-kind-badge";
        kindBadge.textContent = summary.kind;
        row.appendChild(kindBadge);

        const metaSpan = document.createElement("span");
        metaSpan.className = "owner-tariff-meta";
        metaSpan.textContent = summary.meta;
        row.appendChild(metaSpan);

        const statusTag = document.createElement("span");
        statusTag.className = "owner-tariff-status " + (plan.is_active !== false ? "is-active" : "is-inactive");
        statusTag.textContent = plan.is_active !== false ? labels.statusActive : labels.statusInactive;
        row.appendChild(statusTag);

        const priceStrong = document.createElement("strong");
        priceStrong.className = "owner-tariff-price";
        priceStrong.textContent = summary.price;
        row.appendChild(priceStrong);

        const actions = document.createElement("div");
        actions.className = "owner-tariff-actions";

        const editBtn = document.createElement("button");
        editBtn.type = "button";
        editBtn.className = "owner-tariff-btn";
        editBtn.title = labels.edit;
        editBtn.appendChild(makeSvgIcon("edit"));
        editBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          plan._is_open = true;
          render();
        });
        actions.appendChild(editBtn);

        const copyBtn = document.createElement("button");
        copyBtn.type = "button";
        copyBtn.className = "owner-tariff-btn";
        copyBtn.title = labels.copy;
        copyBtn.appendChild(makeSvgIcon("content_copy"));
        copyBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          if (plans.length < MAX_PRICING_PLANS) {
            const clone = JSON.parse(JSON.stringify(plan));
            clone._is_open = true;
            if (clone.title_az) clone.title_az += " (копия)";
            plans.splice(index + 1, 0, clone);
            sync();
            render();
          }
        });
        actions.appendChild(copyBtn);

        const deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.className = "owner-tariff-btn owner-tariff-btn--danger";
        deleteBtn.title = labels.delete;
        deleteBtn.appendChild(makeSvgIcon("delete"));
        deleteBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          confirmDeletePlan(index);
        });
        actions.appendChild(deleteBtn);

        row.appendChild(actions);

        row.addEventListener("click", () => {
          plan._is_open = true;
          render();
        });

      } else {
        // Expanded state
        row.classList.add("is-expanded");

        const head = document.createElement("div");
        head.className = "owner-tariff-head";

        const drag = document.createElement("span");
        drag.className = "owner-tariff-drag";
        drag.appendChild(makeSvgIcon("drag_indicator"));
        head.appendChild(drag);

        const headTitle = document.createElement("strong");
        headTitle.className = "owner-tariff-head-title";
        headTitle.textContent = summary.title;
        head.appendChild(headTitle);

        const collapseBtn = document.createElement("button");
        collapseBtn.type = "button";
        collapseBtn.className = "owner-tariff-collapse-btn";
        collapseBtn.appendChild(makeSvgIcon("expand_less"));
        collapseBtn.appendChild(document.createTextNode(" " + labels.collapse));
        collapseBtn.addEventListener("click", () => {
          plan._is_open = false;
          render();
        });
        head.appendChild(collapseBtn);
        row.appendChild(head);

        const body = document.createElement("div");
        body.className = "owner-tariff-body";

        // Format selector
        const formatGroup = document.createElement("div");
        formatGroup.className = "owner-tariff-control-group";
        const formatLabel = document.createElement("span");
        formatLabel.className = "owner-tariff-group-label";
        formatLabel.textContent = labels.format;
        formatGroup.appendChild(formatLabel);

        const formatSegmented = document.createElement("div");
        formatSegmented.className = "km-pf-segmented";
        [
          ["group", labels.group],
          ["individual", labels.individual],
          ["open_visit", labels.openVisit],
        ].forEach(([fKey, fName]) => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "km-pf-segmented__item" + (plan.lesson_format === fKey ? " is-active" : "");
          btn.textContent = fName;
          btn.addEventListener("click", () => {
            plan.lesson_format = fKey;
            sync();
            render();
          });
          formatSegmented.appendChild(btn);
        });
        formatGroup.appendChild(formatSegmented);

        // Payment type selector
        const kindGroup = document.createElement("div");
        kindGroup.className = "owner-tariff-control-group";
        const kindLabel = document.createElement("span");
        kindLabel.className = "owner-tariff-group-label";
        kindLabel.textContent = labels.paymentType;
        kindGroup.appendChild(kindLabel);

        const kindSegmented = document.createElement("div");
        kindSegmented.className = "km-pf-segmented";
        [
          ["lesson", labels.perLesson],
          ["membership", labels.perMonth],
          ["package", labels.package],
          ["admission", labels.admission],
          ["visit", labels.visit],
          ["course", labels.course],
        ].forEach(([kKey, kName]) => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "km-pf-segmented__item" + (plan.editor_kind === kKey ? " is-active" : "");
          btn.textContent = kName;
          btn.addEventListener("click", () => {
            plan.editor_kind = kKey;
            normalizeKind(plan);
            sync();
            render();
          });
          kindSegmented.appendChild(btn);
        });
        kindGroup.appendChild(kindSegmented);

        const controlRow = document.createElement("div");
        controlRow.className = "owner-tariff-control-row";
        controlRow.append(formatGroup, kindGroup);
        body.appendChild(controlRow);

        // Dynamic relevant core inputs row
        const inputsRow = document.createElement("div");
        inputsRow.className = "owner-tariff-inputs-row";

        // Conditional numeric session / quantity field
        if (plan.editor_kind === "membership") {
          const sessField = document.createElement("label");
          sessField.className = "owner-tariff-field owner-tariff-field--num";
          sessField.innerHTML = "<span>" + labels.sessionsMonth + "</span>";
          const sessInput = document.createElement("input");
          sessInput.type = "number";
          sessInput.min = "1";
          sessInput.placeholder = "12";
          sessInput.value = plan.sessions_per_month || "";
          sessInput.addEventListener("input", () => {
            plan.sessions_per_month = sessInput.value;
            sync();
            headTitle.textContent = tariffSummary(plan, index).title;
          });
          sessField.appendChild(sessInput);
          inputsRow.appendChild(sessField);
        } else if (plan.editor_kind === "package") {
          const packField = document.createElement("label");
          packField.className = "owner-tariff-field owner-tariff-field--num";
          packField.innerHTML = "<span>" + labels.sessionsPackage + "</span>";
          const packInput = document.createElement("input");
          packInput.type = "number";
          packInput.min = "1";
          packInput.placeholder = "10";
          packInput.value = plan.quantity || "";
          packInput.addEventListener("input", () => {
            plan.quantity = packInput.value;
            sync();
            headTitle.textContent = tariffSummary(plan, index).title;
          });
          packField.appendChild(packInput);
          inputsRow.appendChild(packField);
        } else if (plan.editor_kind === "course") {
          const courseField = document.createElement("label");
          courseField.className = "owner-tariff-field owner-tariff-field--num";
          courseField.innerHTML = "<span>" + labels.sessionsCourse + "</span>";
          const courseInput = document.createElement("input");
          courseInput.type = "number";
          courseInput.min = "1";
          courseInput.placeholder = "24";
          courseInput.value = plan.quantity || plan.sessions_per_month || "";
          courseInput.addEventListener("input", () => {
            plan.quantity = courseInput.value;
            sync();
            headTitle.textContent = tariffSummary(plan, index).title;
          });
          courseField.appendChild(courseInput);
          inputsRow.appendChild(courseField);
        }

        // Price input
        const priceField = document.createElement("label");
        priceField.className = "owner-tariff-field owner-tariff-field--price";
        priceField.innerHTML = "<span>" + labels.price + "</span>";
        const priceInput = document.createElement("input");
        priceInput.type = "number";
        priceInput.min = "0";
        priceInput.step = "0.01";
        priceInput.placeholder = "120";
        priceInput.value = plan.price || "";
        priceInput.addEventListener("input", () => {
          plan.price = priceInput.value;
          sync();
        });
        priceField.appendChild(priceInput);
        inputsRow.appendChild(priceField);

        // Title AZ input
        const titleAzField = document.createElement("label");
        titleAzField.className = "owner-tariff-field owner-tariff-field--title";
        titleAzField.innerHTML = "<span>" + labels.titleAz + "</span>";
        const titleAzInput = document.createElement("input");
        titleAzInput.type = "text";
        titleAzInput.placeholder = "Aylıq abunə (12 dərs)";
        titleAzInput.value = plan.title_az || "";
        titleAzInput.addEventListener("input", () => {
          plan.title_az = titleAzInput.value;
          sync();
          headTitle.textContent = tariffSummary(plan, index).title;
        });
        titleAzField.appendChild(titleAzInput);
        inputsRow.appendChild(titleAzField);

        body.appendChild(inputsRow);

        // Short description / conditions (AZ) row
        const condRow = document.createElement("div");
        condRow.className = "owner-tariff-desc-row";
        const condAzField = document.createElement("label");
        condAzField.className = "owner-tariff-field";
        condAzField.innerHTML = "<span>" + labels.conditionsAz + "</span>";
        const condAzInput = document.createElement("input");
        condAzInput.type = "text";
        condAzInput.placeholder = "məsələn, Həftədə 3 dəfə, 45 dəqiqə, inventar daxildir";
        condAzInput.value = plan.conditions_az || "";
        condAzInput.addEventListener("input", () => {
          plan.conditions_az = condAzInput.value;
          sync();
        });
        condAzField.appendChild(condAzInput);
        condRow.appendChild(condAzField);
        body.appendChild(condRow);

        // Translations block (RU & EN)
        const transDetails = document.createElement("details");
        transDetails.className = "owner-tariff-translations";
        const hasTransData = plan.title_ru || plan.conditions_ru || plan.title_en || plan.conditions_en;
        transDetails.open = plan._trans_open === true || !!hasTransData;
        transDetails.innerHTML = `
          <summary>
            <svg class="km-i" viewBox="0 0 960 960"><use href="#kmi-language"></use></svg>
            <span>${labels.translationsTitle}</span>
          </summary>
        `;
        transDetails.addEventListener("toggle", () => {
          plan._trans_open = transDetails.open;
        });

        const transGrid = document.createElement("div");
        transGrid.className = "owner-tariff-trans-grid";

        // Title RU
        const titleRuField = document.createElement("label");
        titleRuField.className = "owner-tariff-field";
        titleRuField.innerHTML = "<span>" + labels.titleRu + "</span>";
        const titleRuInput = document.createElement("input");
        titleRuInput.type = "text";
        titleRuInput.placeholder = "Абонемент на месяц (12 занятий)";
        titleRuInput.value = plan.title_ru || "";
        titleRuInput.addEventListener("input", () => { plan.title_ru = titleRuInput.value; sync(); headTitle.textContent = tariffSummary(plan, index).title; });
        titleRuField.appendChild(titleRuInput);
        transGrid.appendChild(titleRuField);

        // Conditions RU
        const condRuField = document.createElement("label");
        condRuField.className = "owner-tariff-field";
        condRuField.innerHTML = "<span>" + labels.conditionsRu + "</span>";
        const condRuInput = document.createElement("input");
        condRuInput.type = "text";
        condRuInput.placeholder = "например, 3 раза в неделю по 45 мин";
        condRuInput.value = plan.conditions_ru || "";
        condRuInput.addEventListener("input", () => { plan.conditions_ru = condRuInput.value; sync(); });
        condRuField.appendChild(condRuInput);
        transGrid.appendChild(condRuField);

        // Title EN
        const titleEnField = document.createElement("label");
        titleEnField.className = "owner-tariff-field";
        titleEnField.innerHTML = "<span>" + labels.titleEn + "</span>";
        const titleEnInput = document.createElement("input");
        titleEnInput.type = "text";
        titleEnInput.placeholder = "Monthly subscription (12 sessions)";
        titleEnInput.value = plan.title_en || "";
        titleEnInput.addEventListener("input", () => { plan.title_en = titleEnInput.value; sync(); headTitle.textContent = tariffSummary(plan, index).title; });
        titleEnField.appendChild(titleEnInput);
        transGrid.appendChild(titleEnField);

        // Conditions EN
        const condEnField = document.createElement("label");
        condEnField.className = "owner-tariff-field";
        condEnField.innerHTML = "<span>" + labels.conditionsEn + "</span>";
        const condEnInput = document.createElement("input");
        condEnInput.type = "text";
        condEnInput.placeholder = "e.g., 3 times a week, 45 minutes";
        condEnInput.value = plan.conditions_en || "";
        condEnInput.addEventListener("input", () => { plan.conditions_en = condEnInput.value; sync(); });
        condEnField.appendChild(condEnInput);
        transGrid.appendChild(condEnField);

        transDetails.appendChild(transGrid);
        body.appendChild(transDetails);

        // Advanced accordion
        const advanced = document.createElement("details");
        advanced.className = "owner-tariff-advanced";
        advanced.open = plan._advanced_open === true;
        advanced.innerHTML = `
          <summary>
            <svg class="km-i" viewBox="0 0 960 960"><use href="#kmi-tune"></use></svg>
            <span>${labels.advanced}</span>
            <small>${labels.advancedHint}</small>
          </summary>
        `;
        advanced.addEventListener("toggle", () => {
          plan._advanced_open = advanced.open;
        });

        const advGrid = document.createElement("div");
        advGrid.className = "owner-tariff-advanced-grid";

        // Price kind
        const priceKindField = document.createElement("label");
        priceKindField.className = "owner-tariff-field";
        priceKindField.innerHTML = "<span>" + labels.priceKind + "</span>";
        const priceKindSelect = document.createElement("select");
        priceKindSelect.innerHTML = `
          <option value="exact">${labels.exact}</option>
          <option value="free">${labels.free}</option>
          <option value="from">${labels.from}</option>
          <option value="range">${labels.range}</option>
          <option value="on_request">${labels.onRequest}</option>
        `;
        priceKindSelect.value = plan.price_kind || "exact";
        priceKindSelect.addEventListener("change", () => {
          plan.price_kind = priceKindSelect.value;
          normalizeKind(plan);
          sync();
          render();
        });
        priceKindField.appendChild(priceKindSelect);
        advGrid.appendChild(priceKindField);

        // Price min / max if range
        if (plan.price_kind === "range" || plan.price_kind === "from") {
          const priceMinField = document.createElement("label");
          priceMinField.className = "owner-tariff-field";
          priceMinField.innerHTML = "<span>" + labels.priceMin + "</span>";
          const priceMinInput = document.createElement("input");
          priceMinInput.type = "number";
          priceMinInput.min = "0";
          priceMinInput.value = plan.price_min || "";
          priceMinInput.addEventListener("input", () => { plan.price_min = priceMinInput.value; sync(); });
          priceMinField.appendChild(priceMinInput);
          advGrid.appendChild(priceMinField);
        }
        if (plan.price_kind === "range") {
          const priceMaxField = document.createElement("label");
          priceMaxField.className = "owner-tariff-field";
          priceMaxField.innerHTML = "<span>" + labels.priceMax + "</span>";
          const priceMaxInput = document.createElement("input");
          priceMaxInput.type = "number";
          priceMaxInput.min = "0";
          priceMaxInput.value = plan.price_max || "";
          priceMaxInput.addEventListener("input", () => { plan.price_max = priceMaxInput.value; sync(); });
          priceMaxField.appendChild(priceMaxInput);
          advGrid.appendChild(priceMaxField);
        }

        // Age limits
        const ageFromField = document.createElement("label");
        ageFromField.className = "owner-tariff-field";
        ageFromField.innerHTML = "<span>" + labels.ageFrom + "</span>";
        const ageFromInput = document.createElement("input");
        ageFromInput.type = "number";
        ageFromInput.min = "0";
        ageFromInput.value = plan.age_from || "";
        ageFromInput.addEventListener("input", () => { plan.age_from = ageFromInput.value; sync(); });
        ageFromField.appendChild(ageFromInput);
        advGrid.appendChild(ageFromField);

        const ageToField = document.createElement("label");
        ageToField.className = "owner-tariff-field";
        ageToField.innerHTML = "<span>" + labels.ageTo + "</span>";
        const ageToInput = document.createElement("input");
        ageToInput.type = "number";
        ageToInput.min = "0";
        ageToInput.value = plan.age_to || "";
        ageToInput.addEventListener("input", () => { plan.age_to = ageToInput.value; sync(); });
        ageToField.appendChild(ageToInput);
        advGrid.appendChild(ageToField);

        // Source URL
        const srcField = document.createElement("label");
        srcField.className = "owner-tariff-field";
        srcField.innerHTML = "<span>" + labels.sourceUrl + "</span>";
        const srcInput = document.createElement("input");
        srcInput.type = "url";
        srcInput.placeholder = "https://...";
        srcInput.value = plan.source_url || "";
        srcInput.addEventListener("input", () => { plan.source_url = srcInput.value; sync(); });
        srcField.appendChild(srcInput);
        advGrid.appendChild(srcField);

        advanced.appendChild(advGrid);
        body.appendChild(advanced);

        // Footer
        const footer = document.createElement("div");
        footer.className = "owner-tariff-footer";

        const activeLabel = document.createElement("label");
        activeLabel.className = "owner-tariff-active";
        const activeCheck = document.createElement("input");
        activeCheck.type = "checkbox";
        activeCheck.checked = plan.is_active !== false;
        activeCheck.addEventListener("change", () => {
          plan.is_active = activeCheck.checked;
          sync();
        });
        activeLabel.append(activeCheck, document.createTextNode(" " + labels.active));
        footer.appendChild(activeLabel);

        const footActions = document.createElement("div");
        footActions.className = "owner-tariff-foot-actions";

        // Show Move Up/Down buttons only if there are multiple plans
        if (plans.length > 1) {
          const upBtn = document.createElement("button");
          upBtn.type = "button";
          upBtn.className = "owner-tariff-foot-btn";
          upBtn.title = labels.moveUp;
          upBtn.disabled = index === 0;
          upBtn.appendChild(makeSvgIcon("arrow_upward"));
          upBtn.addEventListener("click", () => {
            if (index > 0) {
              const tmp = plans[index];
              plans[index] = plans[index - 1];
              plans[index - 1] = tmp;
              sync();
              render();
            }
          });
          footActions.appendChild(upBtn);

          const downBtn = document.createElement("button");
          downBtn.type = "button";
          downBtn.className = "owner-tariff-foot-btn";
          downBtn.title = labels.moveDown;
          downBtn.disabled = index === plans.length - 1;
          downBtn.appendChild(makeSvgIcon("arrow_downward"));
          downBtn.addEventListener("click", () => {
            if (index < plans.length - 1) {
              const tmp = plans[index];
              plans[index] = plans[index + 1];
              plans[index + 1] = tmp;
              sync();
              render();
            }
          });
          footActions.appendChild(downBtn);
        }

        const delBtn = document.createElement("button");
        delBtn.type = "button";
        delBtn.className = "owner-tariff-foot-btn owner-tariff-foot-btn--delete";
        delBtn.title = labels.delete;
        delBtn.appendChild(makeSvgIcon("delete"));
        delBtn.appendChild(document.createTextNode(" " + labels.delete));
        delBtn.addEventListener("click", () => {
          confirmDeletePlan(index);
        });
        footActions.appendChild(delBtn);

        footer.appendChild(footActions);
        body.appendChild(footer);

        row.appendChild(body);
      }

      list.appendChild(row);
    });

    updateComputedPrice();
  }

  add.addEventListener("click", () => {
    if (plans.length < MAX_PRICING_PLANS) {
      plans.forEach((p) => { p._is_open = false; });
      plans.push({
        editor_kind: "membership",
        lesson_format: "group",
        title_az: "",
        title_ru: "",
        title_en: "",
        conditions_az: "",
        conditions_ru: "",
        conditions_en: "",
        billing_mode: "recurring",
        price_kind: "exact",
        price: "",
        currency: "AZN",
        is_active: true,
        _is_open: true,
      });
      sync();
      render();
      const last = list.lastElementChild;
      if (last) {
        last.scrollIntoView({ behavior: "smooth", block: "nearest" });
        const firstIn = last.querySelector("input");
        if (firstIn) firstIn.focus();
      }
    }
  });

  const presetButtons = editor.querySelectorAll("[data-badge-preset-az], [data-badge-preset]");
  presetButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setBadgeInputs(
        button.dataset.badgePresetAz || "",
        button.dataset.badgePresetRu || "",
        button.dataset.badgePresetEn || ""
      );
      applyPricePolicy(detectPricePolicy(), false);
    });
  });

  input.addEventListener("input", () => {
    plans = parsePlans(input.value);
    render();
  });

  applyPricePolicy(currentPolicy, false);
  render();
})();
