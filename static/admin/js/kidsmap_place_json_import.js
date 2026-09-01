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

  function setCheckbox(fieldName, value) {
    if (value === undefined || value === null) return false;
    var input = document.getElementById("id_" + fieldName);
    if (!input || input.type !== "checkbox") return false;
    input.checked = value === true || value === 1 || value === "1" || normalize(value) === "true";
    input.dispatchEvent(new Event("change", { bubbles: true }));
    return true;
  }

  function showEditorReview(review) {
    var notice = document.querySelector("[data-place-json-review]");
    if (!notice) return;
    if (!review || typeof review !== "object") {
      notice.hidden = true;
      notice.textContent = "";
      return;
    }
    var rows = [];
    var missing = Array.isArray(review.missing_fields) ? review.missing_fields.filter(Boolean) : [];
    var verification = Array.isArray(review.needs_verification) ? review.needs_verification.filter(Boolean) : [];
    var conflicts = Array.isArray(review.conflicts) ? review.conflicts.filter(Boolean) : [];
    if (missing.length) rows.push("Не найдено: " + missing.join(", "));
    if (verification.length) rows.push("Проверить: " + verification.join(", "));
    if (conflicts.length) rows.push("Расхождения: " + conflicts.join(", "));
    if (review.map_task) rows.push("Карта: " + review.map_task);
    if (Array.isArray(review.media_to_upload) && review.media_to_upload.length) rows.push("Загрузить вручную: " + review.media_to_upload.join(", "));
    if (!rows.length) {
      notice.hidden = true;
      notice.textContent = "";
      return;
    }
    notice.textContent = "AI-проверка карточки. " + rows.join(". ");
    notice.hidden = false;
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
      age_open_ended: false,
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
      schedule_mode: "regular",
      schedule_note_az: "",
      schedule_note_ru: "",
      schedule_note_en: "",
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
      is_temporary: false,
      temporary_start: null,
      temporary_end: null,
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
      additional_info_en: "",
      custom_price_badge_az: "",
      custom_price_badge_ru: "",
      custom_price_badge_en: "",
      editor_review: {
        status: "incomplete",
        missing_fields: [],
        needs_verification: [],
        conflicts: [],
        generated_translations: [],
        map_task: "",
        media_to_upload: [],
        sources: []
      }
    };
    return [
      "Подготовь ПОЛНУЮ карточку детского места для KidsMap в Азербайджане по материалам ниже.",
      "Сначала изучи все переданные ссылки, сайт, соцсети, Google Maps, прайс и текст. Если доступен поиск, используй только официальные страницы места, его соцсети, Google Maps и надёжные площадки.",
      "НЕ ВЫДУМЫВАЙ факты: адрес, телефон, возраст, расписание, цены, координаты, метро, услуги и ссылки. Неизвестное значение оставляй null, пустой строкой или []. Все ключи из структуры обязательны — не удаляй их.",
      "Если источники расходятся, не выбирай наугад: внеси подтверждённый свежий вариант и опиши конфликт в editor_review. Координаты указывай только если они есть в источнике; иначе оставь null и добавь задачу в editor_review.map_task.",
      "SEO: description_az, description_ru и description_en — 2–4 конкретных предложения, минимум 120 символов. Пиши для родителей: направления, возраст, формат, район и проверенные особенности. Без «лучший», «номер один» и рекламного мусора. Переводы, созданные тобой, перечисли в editor_review.generated_translations.",
      "Расписание: заполняй schedule_days только когда часы работы известны. Для полного недельного графика дай ровно 7 дней в порядке mon,tue,wed,thu,fri,sat,sun. Если занятия по записи — schedule_mode='by_appointment'; если график меняется — 'variable' и заполни schedule_note_* подтверждённым текстом.",
      "Тарифы: каждый подтверждённый вариант цены — отдельный объект pricing_plans, максимум 12. Не объединяй пробный урок, разовое занятие, абонемент и индивидуальные занятия. Используй product_type из: admission, visit, lesson, membership, course, camp, event, excursion, tour, rental, addon, registration_fee, deposit. price_kind: exact (price), free (price: 0), from (price_min), range (price_min и price_max), on_request. on_request допустим только если источник прямо говорит «по запросу»; если цены просто не найдены — pricing_plans: [] и missing_fields: ['prices'].",
      "category и subcategory выбирай строго из списка ниже. Подкатегория должна принадлежать категории. Если подходящей нет — оставь поля пустыми и объясни это в editor_review.",
      "Верни РОВНО один валидный JSON-объект в блоке ```json. После него не пиши текст. editor_review — служебный блок для редактора и не публикуется на сайте.",
      "Полная структура JSON:",
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
        schedule_mode: ["schedule_mode"],
        schedule_note_az: ["schedule_note_az"],
        schedule_note_ru: ["schedule_note_ru"],
        schedule_note_en: ["schedule_note_en"],
        temporary_start: ["temporary_start"],
        temporary_end: ["temporary_end"],
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

      if (setCheckbox("is_temporary", first(data, ["is_temporary"]))) filled += 1;
      if (setCheckbox("age_open_ended", first(data, ["age_open_ended"]))) filled += 1;

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
      showEditorReview(data.editor_review);
      showMessage("Заполнено полей: " + filled + ". Проверьте данные и сохраните карточку.", false);
      dialog.close();
      window.setTimeout(function () { openButton.focus(); }, 0);
    });
  }

  document.addEventListener("DOMContentLoaded", init);
}());
