(function () {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  function currentLanguage() {
    return String(document.documentElement.lang || "az").split("-")[0].toLowerCase();
  }

  function buildLocale(lang) {
    const locales = {
      az: {
        weekdays: {
          shorthand: ["B.", "B.e.", "Ç.a.", "Ç.", "C.a.", "C.", "Ş."],
          longhand: ["Bazar", "Bazar ertəsi", "Çərşənbə axşamı", "Çərşənbə", "Cümə axşamı", "Cümə", "Şənbə"],
        },
        months: {
          shorthand: ["Yan", "Fev", "Mar", "Apr", "May", "İyn", "İyl", "Avq", "Sen", "Okt", "Noy", "Dek"],
          longhand: ["Yanvar", "Fevral", "Mart", "Aprel", "May", "İyun", "İyul", "Avqust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"],
        },
        firstDayOfWeek: 1,
        time_24hr: true,
      },
      ru: {
        weekdays: {
          shorthand: ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],
          longhand: ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"],
        },
        months: {
          shorthand: ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"],
          longhand: ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
        },
        firstDayOfWeek: 1,
        time_24hr: true,
      },
      en: {
        weekdays: {
          shorthand: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
          longhand: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        },
        months: {
          shorthand: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
          longhand: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        },
        firstDayOfWeek: 1,
        time_24hr: true,
      },
    };

    return locales[lang] || locales.az;
  }

  function applyAltInputDecorations(instance, input, config) {
    if (!instance || !instance.altInput) return;
    instance.altInput.classList.add("field", "kidsmap-flatpickr-input");
    if (config && config.noCalendar) {
      instance.altInput.classList.add("kidsmap-flatpickr-time-input");
    }
    if (input.dataset.placeholder || input.getAttribute("placeholder")) {
      instance.altInput.setAttribute("placeholder", input.dataset.placeholder || input.getAttribute("placeholder"));
    }
  }

  function sanitizeTimeDraft(value) {
    const digits = String(value || "").replace(/\D/g, "").slice(0, 4);
    if (digits.length <= 2) return digits;
    return digits.slice(0, 2) + ":" + digits.slice(2);
  }

  function normalizeTimeValue(value) {
    const raw = String(value || "").trim();
    if (!raw) return "";

    const colonMatch = raw.match(/^(\d{1,2}):(\d{1,2})$/);
    if (colonMatch) {
      const hours = Number(colonMatch[1]);
      const minutes = Number(colonMatch[2]);
      if (Number.isNaN(hours) || Number.isNaN(minutes) || hours > 23 || minutes > 59) return null;
      return String(hours).padStart(2, "0") + ":" + String(minutes).padStart(2, "0");
    }

    const digits = raw.replace(/\D/g, "");
    if (digits.length === 3 || digits.length === 4) {
      const hours = Number(digits.length === 3 ? digits.slice(0, 1) : digits.slice(0, 2));
      const minutes = Number(digits.slice(-2));
      if (Number.isNaN(hours) || Number.isNaN(minutes) || hours > 23 || minutes > 59) return null;
      return String(hours).padStart(2, "0") + ":" + String(minutes).padStart(2, "0");
    }

    return null;
  }

  function enhanceManualTimeInput(instance) {
    if (!instance || !instance.altInput || !instance.input) return;
    const visibleInput = instance.altInput;

    visibleInput.removeAttribute("readonly");
    visibleInput.setAttribute("inputmode", "numeric");
    visibleInput.setAttribute("maxlength", "5");
    visibleInput.setAttribute("autocomplete", "off");
    visibleInput.setAttribute("spellcheck", "false");

    visibleInput.addEventListener("focus", function () {
      window.setTimeout(function () {
        visibleInput.select();
      }, 0);
    });

    visibleInput.addEventListener("input", function () {
      const draft = sanitizeTimeDraft(visibleInput.value);
      if (draft !== visibleInput.value) {
        visibleInput.value = draft;
      }
      instance.input.value = draft;
    });

    visibleInput.addEventListener("blur", function () {
      const normalized = normalizeTimeValue(visibleInput.value);
      if (!visibleInput.value.trim()) {
        instance.clear();
        return;
      }
      if (!normalized) {
        visibleInput.value = instance.input.value || "";
        return;
      }
      visibleInput.value = normalized;
      instance.setDate(normalized, true, "H:i");
    });
  }

  function minTodayValue() {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return now;
  }

  function initPicker(input, config) {
    if (!input || input.dataset.flatpickrReady === "1" || typeof window.flatpickr !== "function") return null;
    const lang = currentLanguage();
    const mergedConfig = Object.assign(
      {
        locale: buildLocale(lang),
        disableMobile: true,
        allowInput: input.dataset.allowInput === "1",
        static: false,
        monthSelectorType: "static",
        prevArrow: "<span aria-hidden=\"true\">‹</span>",
        nextArrow: "<span aria-hidden=\"true\">›</span>",
      },
      config || {}
    );

    const originalOnReady = mergedConfig.onReady;
    mergedConfig.onReady = function (selectedDates, dateStr, instanceRef) {
      instanceRef.calendarContainer.classList.add("kidsmap-flatpickr");
      if (mergedConfig.noCalendar) {
        instanceRef.calendarContainer.classList.add("kidsmap-flatpickr-time-only");
      }
      applyAltInputDecorations(instanceRef, input, mergedConfig);
      if (mergedConfig.noCalendar) {
        enhanceManualTimeInput(instanceRef);
      }
      if (typeof originalOnReady === "function") {
        originalOnReady(selectedDates, dateStr, instanceRef);
      }
    };

    const instance = window.flatpickr(input, mergedConfig);
    input.dataset.flatpickrReady = "1";
    return instance;
  }

  function initDatePickers(root) {
    (root || document).querySelectorAll("[data-kidsmap-date-picker]").forEach(function (input) {
      initPicker(input, {
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d.m.Y",
        minDate: input.dataset.minToday === "1" ? minTodayValue() : null,
      });
    });
  }

  function initTimePickers(root) {
    (root || document).querySelectorAll("[data-kidsmap-time-picker]").forEach(function (input) {
      initPicker(input, {
        enableTime: true,
        noCalendar: true,
        dateFormat: "H:i",
        altInput: true,
        altFormat: "H:i",
        time_24hr: true,
        minuteIncrement: 15,
      });
    });
  }

  function initDateTimePickers(root) {
    (root || document).querySelectorAll("[data-kidsmap-datetime-picker]").forEach(function (input) {
      initPicker(input, {
        enableTime: true,
        time_24hr: true,
        dateFormat: "Y-m-d H:i",
        altInput: true,
        altFormat: "d.m.Y H:i",
      });
    });
  }

  function boot(root) {
    initDatePickers(root);
    initTimePickers(root);
    initDateTimePickers(root);
  }

  window.kidsMapInitDateTimePickers = boot;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      boot(document);
    });
  } else {
    boot(document);
  }
})();
