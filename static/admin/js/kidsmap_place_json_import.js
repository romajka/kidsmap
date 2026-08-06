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
      "Собери одну точную и SEO-подготовленную карточку места для KidsMap по данным ниже.",
      "ФОРМАТ ОТВЕТА. Сначала верни один валидный JSON-объект в блоке ```json. После него обязательно добавь раздел «ПРИМЕЧАНИЕ ДЛЯ РЕДАКТОРА» по шаблону ниже. Импорт возьмёт только JSON, примечание останется человеку. До JSON и между его полями не добавляй комментарии.",
      "ДОСТОВЕРНОСТЬ. Не выдумывай факты и не делай догадок. Если значения нет или оно сомнительно, не включай ключ. Не подставляй пустые строки, null, 0, фиктивные телефоны, примерные цены, координаты или расписание вместо неизвестных данных. Противоречия между источниками не решай самостоятельно — вынеси их в примечание.",
      "Локацию заполняй обязательно, когда она есть в исходных данных: город указывай в ключе region, район — в ключе district. Если в адресе или источнике назван район Баку, обязательно добавь и region: 'baku'. Не пропускай region, если город можно надёжно определить из полного адреса; не пропускай district, если район указан. Используй только ключи region и district, не русские названия ключей. Если город или район не указан и его нельзя надёжно установить, не выдумывай его и объясни это в примечании.",
      "КОНТАКТЫ И ЛОКАЦИЯ. Номер телефона приводи к международному формату, например +994501234567. Instagram и website передавай полными ссылками. Координаты — только числа из надёжного источника; не вычисляй и не угадывай их по адресу. Если адрес неполный, телефон не подтверждён или ссылки не открывались, отметь это в примечании.",
      "SEO И ТЕКСТЫ. name_az, name_ru и name_en должны содержать официальное название без рекламных добавок и набивки ключевиками. description_az, description_ru и description_en пиши естественно и уникально для языка, а не механическим дословным переводом: 2–4 конкретные фразы о типе места, занятиях/услугах, подтверждённом возрасте, районе/городе и важных условиях. Не добавляй превосходные степени, обещания результата, неподтверждённые преимущества и списки ключевых слов. Если исходных фактов мало для хорошего SEO-описания или перевод ненадёжен, не сочиняй — укажи это в примечании.",
      "Расписание передавай только в schedule_days: ровно 7 объектов в порядке mon, tue, wed, thu, fri, sat, sun. Для закрытого дня: is_closed: true, is_24_hours: false, intervals: []. Для круглосуточного: is_closed: false, is_24_hours: true, intervals: []. Для обычного дня: is_closed: false, is_24_hours: false и один или несколько интервалов {start: 'HH:MM', end: 'HH:MM'}. Интервалы не пересекаются и не переходят через полночь.",
      "category и subcategory выбирай только из списков ниже: используй точный код или точное название. subcategory должна относиться к выбранной category.",
      "ТАРИФЫ. Если цены известны, добавь pricing_plans: отдельный объект на каждый реальный тариф, максимум 12. Не объединяй разные форматы, возрастные группы или варианты оплаты. Для каждого тарифа обязательны product_type, billing_mode и price_kind; добавляй title_az/title_ru/title_en, если названия можно надёжно перевести. Допустимые product_type: admission, visit, lesson, membership, course, camp, event, excursion, tour, rental, addon, registration_fee, deposit. lesson_format: group, individual или open_visit. billing_mode: one_time, recurring или installment. Для recurring обязательны billing_interval (day/week/month/year) и billing_interval_count; для installment — billing_cycles. price_kind: exact, free, from, range или on_request. Для exact укажи price > 0; для from — price_min > 0; для range — price_min и price_max; для free цена будет 0; для on_request цену не добавляй. Пакет задавай парой quantity + quantity_unit. Валюта — трёхбуквенный код, обычно AZN. Условия тарифа раскладывай по conditions_az/ru/en. Не превращай старую, зачёркнутую или неподтверждённую цену в действующую.",
      "АКТУАЛЬНОСТЬ. Цены, расписание, возраст, адрес и контакты считаются изменяемыми данными. Если в источнике нет даты обновления либо данные выглядят устаревшими, добавь их в JSON только когда они явно указаны, но обязательно пометь необходимость проверки в примечании.",
      "ФОТО. Фото через JSON не импортируются. Если источник содержит фото, логотип или ссылки на изображения, перечисли их наличие в примечании и напиши, что файлы нужно загрузить вручную.",
      [
        "ПРИМЕЧАНИЕ ДЛЯ РЕДАКТОРА:",
        "- НЕ НАЙДЕНО: перечисли важные отсутствующие поля и где их лучше проверить.",
        "- ТРЕБУЕТ ПРОВЕРКИ: перечисли сомнительные, устаревающие или противоречивые данные; укажи конкретное значение и причину.",
        "- SEO: укажи, для каких языков не хватило официального названия или фактов для качественного описания.",
        "- ТАРИФЫ: укажи пропущенные цены/условия, неясный период оплаты, валюту, дату актуальности и расхождения между источниками.",
        "- МЕДИА: укажи, какие фото или логотип нужно загрузить вручную.",
        "- ИТОГ: коротко перечисли, на что редактору обратить внимание перед публикацией.",
        "Если по пункту замечаний нет, напиши «нет замечаний». Не дублируй сюда весь JSON."
      ].join("\n"),
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
        pricing_plans: ["pricing_plans", "tariffs"]
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
