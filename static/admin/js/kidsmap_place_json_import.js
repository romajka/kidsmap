(function () {
  "use strict";

  function normalize(value) {
    return String(value || "").trim().toLocaleLowerCase();
  }

  function readTaxonomy() {
    var node = document.getElementById("km-place-taxonomy-config");
    if (!node) return { categories: [], subcategories: [] };
    try { return JSON.parse(node.textContent || "{}"); } catch (error) { return { categories: [], subcategories: [] }; }
  }

  function setValue(fieldName, value) {
    if (value === undefined || value === null || value === "") return false;
    var input = document.getElementById("id_" + fieldName);
    if (!input) return false;
    input.value = Array.isArray(value) || (value && typeof value === "object") ? JSON.stringify(value) : String(value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function setSelectByValueOrLabel(fieldName, value) {
    if (value === undefined || value === null || value === "") return false;
    var select = document.getElementById("id_" + fieldName);
    if (!select) return false;
    var wanted = normalize(value);
    var option = Array.prototype.find.call(select.options, function (item) {
      return normalize(item.value) === wanted || normalize(item.textContent) === wanted;
    });
    if (!option) return false;
    select.value = option.value;
    select.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function setDistrictSelect(value) {
    if (value === undefined || value === null || value === "") return false;
    var select = document.getElementById("id_district");
    if (!select) return false;
    var raw = normalize(value);
    var clean = raw.replace(/^baku_/, "").replace(/район|rayonu|rayon/g, "").trim();

    var districtAliasMap = {
      "narimanov": "baku_narimanov", "нариманов": "baku_narimanov", "наримановский": "baku_narimanov", "nərimanov": "baku_narimanov",
      "yasamal": "baku_yasamal", "ясамал": "baku_yasamal", "ясамальский": "baku_yasamal",
      "khatai": "baku_khatai", "хатаи": "baku_khatai", "хатаинский": "baku_khatai", "xətai": "baku_khatai",
      "binagadi": "baku_binagadi", "бинагади": "baku_binagadi", "бинагадинский": "baku_binagadi", "binəqədi": "baku_binagadi",
      "nasimi": "baku_nasimi", "насими": "baku_nasimi", "насиминский": "baku_nasimi", "nəsimi": "baku_nasimi",
      "nizami": "baku_nizami", "низами": "baku_nizami", "низаминский": "baku_nizami",
      "sabail": "baku_sabail", "сабаил": "baku_sabail", "сабаильский": "baku_sabail", "səbail": "baku_sabail",
      "sabunchu": "baku_sabunchu", "сабунчи": "baku_sabunchu", "сабунчинский": "baku_sabunchu", "sabunçu": "baku_sabunchu",
      "surakhani": "baku_surakhani", "сураханы": "baku_surakhani", "сураханский": "baku_surakhani", "suraxanı": "baku_surakhani",
      "khazar": "baku_khazar", "хазар": "baku_khazar", "хазарский": "baku_khazar", "xəzər": "baku_khazar",
      "garadagh": "baku_garadagh", "гарадаг": "baku_garadagh", "карадаг": "baku_garadagh", "гарадагский": "baku_garadagh", "qaradağ": "baku_garadagh",
      "pirallahi": "baku_pirallahi", "пираллахи": "baku_pirallahi", "пираллахинский": "baku_pirallahi", "pirallahı": "baku_pirallahi"
    };

    var targetKey = districtAliasMap[clean] || districtAliasMap[raw] || raw;

    var option = Array.prototype.find.call(select.options, function (item) {
      var val = normalize(item.value);
      var txt = normalize(item.textContent);
      return val === targetKey 
        || val.replace(/^baku_/, "") === clean
        || txt === targetKey
        || txt === clean
        || (clean.length >= 4 && txt.indexOf(clean) !== -1);
    });
    if (!option) return false;
    select.value = option.value;
    select.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function setStructuredSchedule(value) {
    if (value === undefined || value === null || value === "") return false;
    var days = value;
    if (typeof days === "string") {
      try { days = JSON.parse(days); } catch (error) { return false; }
    }
    if (days && !Array.isArray(days) && Array.isArray(days.days)) days = days.days;
    if (!Array.isArray(days)) return false;
    var input = document.getElementById("id_structured_schedule");
    if (!input) return false;
    input.value = JSON.stringify(days);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    input.dispatchEvent(new Event("km:schedule-import", { bubbles: true }));
    return true;
  }

  function first(data, keys) {
    for (var index = 0; index < keys.length; index += 1) {
      if (data[keys[index]] !== undefined && data[keys[index]] !== null && data[keys[index]] !== "") return data[keys[index]];
    }
    return undefined;
  }

  function parsePlaceJson(value) {
    var text = String(value || "").trim();
    try { return JSON.parse(text); } catch (error) {}

    var fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
    if (fenced) {
      try { return JSON.parse(fenced[1].trim()); } catch (error) {}
    }

    var start = text.indexOf("{");
    if (start === -1) throw new Error("no-json");
    var depth = 0;
    var inString = false;
    var escaped = false;
    for (var index = start; index < text.length; index += 1) {
      var character = text.charAt(index);
      if (inString) {
        if (escaped) escaped = false;
        else if (character === "\\") escaped = true;
        else if (character === '"') inString = false;
        continue;
      }
      if (character === '"') inString = true;
      else if (character === "{") depth += 1;
      else if (character === "}") {
        depth -= 1;
        if (depth === 0) return JSON.parse(text.slice(start, index + 1));
      }
    }
    throw new Error("no-json");
  }

  function buildChatGptPrompt(taxonomy) {
    var categories = (taxonomy.categories || []).map(function (item) {
      return item.code + " — " + item.label;
    }).join("\n");
    var subcategories = (taxonomy.subcategories || []).map(function (item) {
      return item.code + " — " + item.label + " (категория: " + item.category + ")";
    }).join("\n");
    var example = {
      name_az: "",
      name_ru: "",
      name_en: "",
      description_az: "",
      description_ru: "",
      description_en: "",
      category: "",
      subcategory: "",
      age_from: 0,
      age_to: 18,
      offers_adult_classes: false,
      region: "",
      district: "",
      metro: "",
      address: "",
      phone1: "",
      phone2: "",
      phone3: "",
      instagram: "",
      website: "",
      schedule_days: [
        { weekday: "mon", is_closed: false, is_24_hours: false, intervals: [{ start: "09:00", end: "18:00" }] },
        { weekday: "tue", is_closed: false, is_24_hours: false, intervals: [{ start: "09:00", end: "18:00" }] },
        { weekday: "wed", is_closed: false, is_24_hours: false, intervals: [{ start: "09:00", end: "18:00" }] },
        { weekday: "thu", is_closed: false, is_24_hours: false, intervals: [{ start: "09:00", end: "18:00" }] },
        { weekday: "fri", is_closed: false, is_24_hours: false, intervals: [{ start: "09:00", end: "18:00" }] },
        { weekday: "sat", is_closed: true, is_24_hours: false, intervals: [] },
        { weekday: "sun", is_closed: true, is_24_hours: false, intervals: [] }
      ],
      lat: null,
      lng: null,
      lesson_duration_minutes: null,
      lesson_format: "group",
      lessons_per_week: null,
      lessons_per_month: null,
      pricing_plans: [{
        product_type: "membership",
        lesson_format: "group",
        billing_mode: "recurring",
        billing_interval: "month",
        billing_interval_count: 1,
        price_kind: "exact",
        price: 120,
        currency: "AZN",
        title_az: "",
        title_ru: "",
        title_en: "",
        is_active: true,
        sort_order: 0
      }],
      extra_conditions: "",
      additional_info: "",
      extra_conditions_az: "",
      extra_conditions_ru: "",
      extra_conditions_en: "",
      additional_info_az: "",
      additional_info_ru: "",
      additional_info_en: ""
    };
    return [
      "Собери ПОЛНУЮ, ТОЧНУЮ и SEO-ОПТИМИЗИРОВАННУЮ карточку места для каталога KidsMap по исходным данным ниже.",
      "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО 1 (ПОЛНОТА И БЕЗ ПОТЕРЬ): Все имеющиеся в источнике данные (названия, контакты, адрес, расписание, возрастной диапазон, форматы занятий, доп. условия и ВСЕ варианты тарифов/цен) ДОЛЖНЫ быть 100% перенесены в соответствующие ключи JSON. Никакая информация из источника не должна быть упущена.",
      "ОБЯЗАТЕЛЬНОЕ ПРАВИЛО 2 (СТРОГО БЕЗ ВЫДУМЫВАНИЯ): Категорически запрещено выдумывать факты, угадывать координаты, придумывать фиктивные телефоны, неточные адреса или вымышленные цены, если их НЕТ в источнике. Если конкретного поля нет в источнике, не включай этот ключ в JSON (или задай null) и перенеси вопрос в раздел «ПРИМЕЧАНИЕ ДЛЯ РЕДАКТОРА».",
      "ФОРМАТ ОТВЕТА: Верни сначала один валидный JSON-объект в блоке ```json ... ``` (без комментариев до и внутри JSON), а после него раздел «ПРИМЕЧАНИЕ ДЛЯ РЕДАКТОРА».",
      "СТРУКТУРА ПОЛЕЙ И ТРЕБОВАНИЯ К ДАННЫМ:",
      "1. НАЗВАНИЯ И ОПИСАНИЯ:",
      "   - name_az, name_ru, name_en: точные официальные наименования места на 3 языках.",
      "   - description_az, description_ru, description_en: информативное SEO-описание из 2-4 конкретных предложений (для кого место, какие направления/занятия, особенности и район). Без клише 'лучший' и рекламного мусора.",
      "2. ЛОКАЦИЯ И КОНТАКТЫ:",
      "   - region: код/название города. Если в источнике упомянут Баку или район Баку, ставь 'baku'.",
      "   - district: название района города.",
      "   - address: улицу, дом, корпус.",
      "   - metro: ближайшая станция метро.",
      "   - phone1, phone2, phone3: телефоны в международном формате (+994...).",
      "   - instagram, website: полные ссылки.",
      "   - lat, lng: числовые координаты (Широта, Долгота) ТОЛЬКО если они явно даны в источнике.",
      "3. ВОЗРАСТ И УСЛОВИЯ:",
      "   - age_from, age_to: минимальный и максимальный возраст детей (числа).",
      "   - offers_adult_classes: true если есть программы/занятия для взрослых, иначе false.",
      "   - lesson_duration_minutes, lessons_per_week, lessons_per_month: параметры занятий.",
      "   - extra_conditions_az/ru/en, additional_info_az/ru/en: доп. условия и инфо.",
      "4. РАСПИСАНИЕ (schedule_days):",
      "   - Ровно 7 объектов по дням недели в порядке: mon, tue, wed, thu, fri, sat, sun.",
      "   - Для обычного дня: { weekday: 'mon', is_closed: false, is_24_hours: false, intervals: [{ start: '09:00', end: '18:00' }] }.",
      "   - Для закрытого дня: { weekday: 'sat', is_closed: true, is_24_hours: false, intervals: [] }.",
      "   - Для круглосуточного: { weekday: 'sun', is_closed: false, is_24_hours: true, intervals: [] }.",
      "5. ТАРИФЫ И ЦЕНЫ (pricing_plans):",
      "   - ВНИМАНИЕ: Ключ pricing_plans КРАЙНЕ ВАЖЕН! Если в источнике есть ЛЮБЫЕ упоминания цен, абонементов, занятий или их вариантов, выдели КАЖДЫЙ вариант в отдельный объект массива pricing_plans (до 12 штук).",
      "   - Если цены в тексте не указаны вовсе, обязательно добавь 1 тариф с price_kind: 'on_request' (по запросу).",
      "   - product_type: admission (входной билет), visit (посещение), lesson (занятие), membership (абонемент), course (курс), camp (лагерь), event (мероприятие), excursion (экскурсия), tour (тур), rental (аренда), addon (доп. услуга), registration_fee (взнос), deposit (депозит).",
      "   - lesson_format: group (групповой), individual (индивидуальный), open_visit (свободное посещение).",
      "   - billing_mode: one_time (разовый), recurring (регулярный), installment (частями).",
      "   - Для recurring обязательны: billing_interval ('day'|'week'|'month'|'year') и billing_interval_count (>0).",
      "   - Для installment обязательны: billing_cycles (>0).",
      "   - price_kind: exact (передавай price), free (цена 0), from (передавай price_min), range (передавай price_min и price_max), on_request (по запросу).",
      "   - quantity и quantity_unit: например quantity: 12, quantity_unit: 'lesson'.",
      "   - title_az, title_ru, title_en: понятное название тарифа (например 'Пробное занятие', 'Абонемент на месяц').",
      "   - conditions_az, conditions_ru, conditions_en: условия тарифа.",
      "   - currency: по умолчанию 'AZN'.",
      "   - is_active: true, sort_order: 0, 1, 2...",
      "6. КАТЕГОРИИ:",
      "   - category и subcategory выбери строго из предоставленного ниже списка.",
      [
        "ПРИМЕЧАНИЕ ДЛЯ РЕДАКТОРА:",
        "- НЕ НАЙДЕНО: укажи, каких важных данных (телефоны, цены, расписание) не было в источнике.",
        "- ТРЕБУЕТ ПРОВЕРКИ: укажи сомнительные или устаревающие сведения.",
        "- ТАРИФЫ: укажи нюансы по расхождению цен или периодам оплаты.",
        "- МЕДИА: перечисли фото/логотипы для ручной загрузки."
      ].join("\n"),
      "Пример полной структуры поддерживаемого JSON (незаполненные поля нужно убрать):",
      JSON.stringify(example, null, 2),
      "Доступные категории:",
      categories || "Нет доступных категорий.",
      "Доступные подкатегории:",
      subcategories || "Нет доступных подкатегорий."
    ].join("\n\n");
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    return new Promise(function (resolve, reject) {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      try { document.execCommand("copy") ? resolve() : reject(); } catch (error) { reject(error); }
      document.body.removeChild(textarea);
    });
  }

  function init() {
    var dialog = document.querySelector("[data-place-json-import-dialog]");
    var openButton = document.querySelector("[data-place-json-import-open]");
    var taxonomy = readTaxonomy();
    var promptButton = document.querySelector("[data-place-json-prompt-copy]");
    var promptDialog = document.querySelector("[data-place-json-prompt-dialog]");
    var promptInput = promptDialog && promptDialog.querySelector("[data-place-json-prompt-input]");
    var promptMessage = promptDialog && promptDialog.querySelector("[data-place-json-prompt-message]");

    if (promptButton && promptDialog && promptInput && window.HTMLDialogElement) {
      promptButton.addEventListener("click", function () {
        if (!promptInput.value.trim()) promptInput.value = buildChatGptPrompt(taxonomy);
        promptMessage.textContent = "";
        promptDialog.showModal();
        promptInput.focus();
      });
      promptDialog.querySelectorAll("[data-place-json-prompt-close]").forEach(function (button) {
        button.addEventListener("click", function () { promptDialog.close(); });
      });
      promptDialog.addEventListener("click", function (event) {
        if (event.target === promptDialog) promptDialog.close();
      });
      promptDialog.querySelector("[data-place-json-prompt-reset]").addEventListener("click", function () {
        promptInput.value = buildChatGptPrompt(taxonomy);
        promptMessage.textContent = "Исходный шаблон восстановлен.";
      });
      promptDialog.querySelector("[data-place-json-prompt-copy-text]").addEventListener("click", function () {
        copyText(promptInput.value).then(function () {
          promptMessage.textContent = "Инструкция скопирована. Вставьте её в ChatGPT вместе с данными о месте.";
        }).catch(function () {
          promptMessage.textContent = "Не удалось скопировать. Разрешите доступ к буферу обмена и повторите.";
        });
      });
    }

    if (!dialog || !openButton || !window.HTMLDialogElement) return;
    var input = dialog.querySelector("[data-place-json-import-input]");
    var message = dialog.querySelector("[data-place-json-import-message]");

    function showMessage(text, isError) {
      message.textContent = text;
      message.classList.toggle("is-error", Boolean(isError));
    }

    openButton.addEventListener("click", function () {
      showMessage("", false);
      dialog.showModal();
      input.focus();
    });
    dialog.querySelectorAll("[data-place-json-import-close]").forEach(function (button) {
      button.addEventListener("click", function () { dialog.close(); });
    });
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) dialog.close();
    });

    dialog.querySelector("[data-place-json-import-apply]").addEventListener("click", async function () {
      var data;
      try {
        data = parsePlaceJson(input.value);
      } catch (error) {
        showMessage("Не удалось найти JSON. Проверьте блок ```json, кавычки, запятые и скобки.", true);
        return;
      }
      if (!data || Array.isArray(data) || typeof data !== "object") {
        showMessage("Нужен один объект JSON с данными места.", true);
        return;
      }

      var validateUrl = dialog.dataset.pricingValidateUrl;
      if (validateUrl) {
        try {
          var csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
          var validationResponse = await fetch(validateUrl, {
            method: "POST",
            credentials: "same-origin",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrfInput ? csrfInput.value : ""},
            body: JSON.stringify(data)
          });
          var validation = await validationResponse.json();
          if (!validationResponse.ok || !validation.ok) {
            showMessage(validation.error || "Не удалось проверить тарифы.", true);
            return;
          }
          data.pricing_plans = validation.pricing_plans;
          if (validation.warnings && validation.warnings.length) showMessage(validation.warnings.join(" "), false);
        } catch (error) {
          showMessage("Не удалось проверить тарифы на сервере.", true);
          return;
        }
      }

      var filled = 0;
      var fields = {
        name_az: ["name_az", "название_аз"],
        name_ru: ["name_ru", "название", "name"],
        name_en: ["name_en"],
        description_az: ["description_az"],
        description_ru: ["description_ru", "description", "описание"],
        description_en: ["description_en"],
        age_from: ["age_from", "возраст_от"],
        age_to: ["age_to", "возраст_до"],
        address: ["address", "адрес"],
        metro: ["metro", "метро"],
        phone1: ["phone1", "phone", "телефон"],
        phone2: ["phone2", "additional_phone", "дополнительный_телефон"],
        phone3: ["phone3", "other_phone", "ещё_один_телефон"],
        instagram: ["instagram"],
        website: ["website", "site", "сайт"],
        lat: ["lat", "latitude", "широта"],
        lng: ["lng", "longitude", "долгота"],
        lesson_duration_minutes: ["lesson_duration_minutes", "длительность_минуты"],
        lessons_per_week: ["lessons_per_week", "занятий_в_неделю"],
        lessons_per_month: ["lessons_per_month", "занятий_в_месяц"],
        extra_conditions: ["extra_conditions", "дополнительные_условия"],
        additional_info: ["additional_info", "что_есть_на_месте", "дополнительная_информация"],
        extra_conditions_az: ["extra_conditions_az"],
        extra_conditions_ru: ["extra_conditions_ru"],
        extra_conditions_en: ["extra_conditions_en"],
        additional_info_az: ["additional_info_az"],
        additional_info_ru: ["additional_info_ru"],
        additional_info_en: ["additional_info_en"],
        custom_price_badge_az: ["custom_price_badge_az", "плашка_цены_az", "надпись_цены_az"],
        custom_price_badge_ru: ["custom_price_badge_ru", "custom_price_badge", "плашка_цены", "надпись_цены"],
        custom_price_badge_en: ["custom_price_badge_en", "плашка_цены_en"],
        pricing_plans: ["pricing_plans", "tariffs"]
      };
      Object.keys(fields).forEach(function (fieldName) {
        if (setValue(fieldName, first(data, fields[fieldName]))) filled += 1;
      });

      if (setStructuredSchedule(first(data, ["schedule_days", "structured_schedule", "расписание_по_дням"]))) filled += 1;

      if (setSelectByValueOrLabel("region", first(data, ["region", "город", "регион"]))) filled += 1;
      if (setDistrictSelect(first(data, ["district", "район"])) || setSelectByValueOrLabel("district", first(data, ["district", "район"]))) filled += 1;
      if (setSelectByValueOrLabel("lesson_format", first(data, ["lesson_format", "формат_занятий"]))) filled += 1;

      var adultClasses = first(data, ["offers_adult_classes", "занятия_для_взрослых"]);
      var adultClassesInput = document.getElementById("id_offers_adult_classes");
      if (adultClasses !== undefined && adultClassesInput) {
        adultClassesInput.checked = adultClasses === true || adultClasses === 1 || adultClasses === "1" || normalize(adultClasses) === "true";
        adultClassesInput.dispatchEvent(new Event("change", { bubbles: true }));
        filled += 1;
      }

      var categoryValue = first(data, ["category", "категория"]);
      var category = Array.prototype.find.call(taxonomy.categories || [], function (item) {
        return normalize(item.code) === normalize(categoryValue) || normalize(item.label) === normalize(categoryValue);
      });
      if (category && setSelectByValueOrLabel("category", category.code)) filled += 1;

      var subcategoryValue = first(data, ["subcategory", "подкатегория"]);
      var subcategory = Array.prototype.find.call(taxonomy.subcategories || [], function (item) {
        return normalize(item.code) === normalize(subcategoryValue) || normalize(item.label) === normalize(subcategoryValue);
      });
      if (subcategory) {
        if (setSelectByValueOrLabel("subcategory", subcategory.id)) {
          filled += 1;
        } else if (setSelectByValueOrLabel("subcategory", subcategory.code)) {
          filled += 1;
        }
      } else if (subcategoryValue && setSelectByValueOrLabel("subcategory", subcategoryValue)) {
        filled += 1;
      }

      if (!filled) {
        showMessage("Поля не найдены. Используйте ключи из подсказки под полем JSON.", true);
        return;
      }
      showMessage("Заполнено полей: " + filled + ". Проверьте данные и сохраните карточку.", false);
      dialog.close();
      window.setTimeout(function () { openButton.focus(); }, 0);
    });
  }

  document.addEventListener("DOMContentLoaded", init);
}());
