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
      price_from: null,
      price_to: null,
      price_per_lesson: null,
      price_per_month: null,
      price_per_8_lessons: null,
      pricing_plans: [{
        lesson_format: "group",
        sessions_per_week: null,
        sessions_per_month: null,
        payment_type: "per_month",
        package_sessions: null,
        price: 0,
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
      "Собери одну карточку места для KidsMap по данным ниже.",
      "Сначала верни один валидный JSON-объект в блоке ```json. Сразу после блока обязательно напиши раздел «ПРИМЕЧАНИЕ:» с коротким списком: какие поля не добавлены, почему, что нужно уточнить и как это можно заполнить. Если всё добавлено, так и напиши. Импорт возьмёт JSON из блока, а примечание останется для человека.",
      "Не выдумывай факты. Если данных нет, не включай ключ. Не ставь пустые строки, null или 0 вместо неизвестных значений.",
      "Локацию заполняй обязательно, когда она есть в исходных данных: город указывай в ключе region, район — в ключе district. Если в адресе или источнике назван район Баку, обязательно добавь и region: 'baku'. Не пропускай region, если город можно надёжно определить из полного адреса; не пропускай district, если район указан. Используй только ключи region и district, не русские названия ключей. Если город или район не указан и его нельзя надёжно установить, не выдумывай его и объясни это в примечании.",
      "Названия и описания заполняй по языкам только если есть надёжный перевод. Номер телефона — международный, например +994501234567. Координаты — числа. Фото через JSON не импортируются — обязательно укажи это в примечании, если фото было в источнике.",
      "Описание делай полезным для каталога и SEO: 2–4 естественные, конкретные фразы без воды и набивки ключевиками. Укажи, что это за место, для какого возраста, какие занятия или услуги есть, район/город и важные условия — только если это подтверждено в источнике. Не пиши рекламные обещания и не придумывай факты.",
      "Расписание передавай только в schedule_days: ровно 7 объектов в порядке mon, tue, wed, thu, fri, sat, sun. Для закрытого дня: is_closed: true, is_24_hours: false, intervals: []. Для круглосуточного: is_closed: false, is_24_hours: true, intervals: []. Для обычного дня: is_closed: false, is_24_hours: false и один или несколько интервалов {start: 'HH:MM', end: 'HH:MM'}. Интервалы не пересекаются и не переходят через полночь.",
      "category и subcategory выбирай только из списков ниже: используй точный код или точное название. subcategory должна относиться к выбранной category.",
      "Если известны тарифы, добавь pricing_plans: один объект на каждый реальный вариант оплаты. Для каждого обязательны lesson_format, payment_type и price. lesson_format: group, individual или open_visit. payment_type: per_lesson, per_month, package, per_visit или entry_ticket. Для package обязательно package_sessions. currency — AZN. Не добавляй больше 20 тарифов и не выдумывай цену или тип оплаты. Если тариф неполный, не добавляй его в JSON и объясни в примечании, чего не хватает.",
      "Полная структура поддерживаемого JSON (это образец типов; незаполненные поля нужно убрать):",
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

    dialog.querySelector("[data-place-json-import-apply]").addEventListener("click", function () {
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
        price_from: ["price_from", "цена_от"],
        price_to: ["price_to", "цена_до"],
        price_per_lesson: ["price_per_lesson", "цена_за_занятие"],
        price_per_month: ["price_per_month", "цена_за_месяц"],
        price_per_8_lessons: ["price_per_8_lessons", "цена_за_8_занятий"],
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
        pricing_plans: ["pricing_plans"]
      };
      Object.keys(fields).forEach(function (fieldName) {
        if (setValue(fieldName, first(data, fields[fieldName]))) filled += 1;
      });

      if (setStructuredSchedule(first(data, ["schedule_days", "structured_schedule", "расписание_по_дням"]))) filled += 1;

      if (setSelectByValueOrLabel("region", first(data, ["region", "город", "регион"]))) filled += 1;
      if (setSelectByValueOrLabel("district", first(data, ["district", "район"]))) filled += 1;
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
      if (subcategory && setSelectByValueOrLabel("subcategory", subcategory.id)) filled += 1;

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
