/**
 * KidsMap Place Schedule Editor
 * Rebuilt for Django 6 and modern Jazzmin/owner workflows.
 * Removed Flatpickr, uses custom input mask and dropdown time pickers.
 */
(function () {
  "use strict";

  var DAY_SETS = {
    ru: {
      full: {
        mon: "Понедельник",
        tue: "Вторник",
        wed: "Среда",
        thu: "Четверг",
        fri: "Пятница",
        sat: "Суббота",
        sun: "Воскресенье",
      },
      short: {
        mon: "Пн",
        tue: "Вт",
        wed: "Ср",
        thu: "Чт",
        fri: "Пт",
        sat: "Сб",
        sun: "Вс",
      },
    },
    az: {
      full: {
        mon: "Bazar ertəsi",
        tue: "Çərşənbə axşamı",
        wed: "Çərşənbə",
        thu: "Cümə axşamı",
        fri: "Cümə",
        sat: "Şənbə",
        sun: "Bazar",
      },
      short: {
        mon: "B.e.",
        tue: "Ç.a.",
        wed: "Ç.",
        thu: "C.a.",
        fri: "C.",
        sat: "Ş.",
        sun: "B.",
      },
    },
    en: {
      full: {
        mon: "Monday",
        tue: "Tuesday",
        wed: "Wednesday",
        thu: "Thursday",
        fri: "Friday",
        sat: "Saturday",
        sun: "Sunday",
      },
      short: {
        mon: "Mon",
        tue: "Tue",
        wed: "Wed",
        thu: "Thu",
        fri: "Fri",
        sat: "Sat",
        sun: "Sun",
      },
    },
  };

  var WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
  var activeDropdown = null;

  function defaultDays() {
    return WEEKDAYS.map(function (weekday) {
      return { weekday: weekday, is_closed: true, is_24_hours: false, intervals: [] };
    });
  }

  function localeConfig(root) {
    var lang = ((document.documentElement.lang || "ru").split("-")[0] || "ru").toLowerCase();
    return DAY_SETS[lang] || DAY_SETS.ru;
  }

  function parsePayload(value) {
    if (!value) return defaultDays();
    try {
      var parsed = JSON.parse(value);
      if (Array.isArray(parsed)) return parsed;
      if (parsed && Array.isArray(parsed.days)) return parsed.days;
    } catch (error) {}
    return defaultDays();
  }

  function dumpPayload(days) {
    var cleanDays = days.map(function (d) {
      return {
        weekday: d.weekday,
        is_closed: !!d.is_closed,
        is_24_hours: !!d.is_24_hours,
        intervals: (d.intervals || []).map(function (interval) {
          return {
            start: interval.start || "",
            end: interval.end || "",
          };
        }),
      };
    });
    return JSON.stringify(cleanDays);
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function timeToMins(timeStr) {
    var parts = timeStr.split(":");
    return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
  }

  function parseTimeStr(str) {
    var clean = str.replace(/[^0-9:]/g, "");
    var hh = "";
    var mm = "";

    if (clean.indexOf(":") !== -1) {
      var parts = clean.split(":");
      hh = parts[0];
      mm = parts[1] || "00";
    } else {
      if (clean.length === 1 || clean.length === 2) {
        hh = clean;
        mm = "00";
      } else if (clean.length === 3) {
        hh = clean.substring(0, 1);
        mm = clean.substring(1);
      } else if (clean.length === 4) {
        hh = clean.substring(0, 2);
        mm = clean.substring(2);
      } else {
        return null;
      }
    }

    if (hh.length === 1) hh = "0" + hh;
    if (mm.length === 1) mm = mm + "0";
    if (hh.length !== 2 || mm.length !== 2) return null;

    var h = parseInt(hh, 10);
    var m = parseInt(mm, 10);

    if (h >= 0 && h <= 23 && m >= 0 && m <= 59) {
      return hh + ":" + mm;
    }
    return null;
  }

  function isValidPartialTime(str) {
    if (str.length === 0) return true;

    var c0 = str.charAt(0);
    if (c0 !== "0" && c0 !== "1" && c0 !== "2") return false;

    if (str.length === 1) return true;

    var c1 = str.charAt(1);
    if (c0 === "2") {
      if (c1 < "0" || c1 > "3") return false;
    } else {
      if (c1 < "0" || c1 > "9") return false;
    }

    if (str.length === 2) return true;

    var c2 = str.charAt(2);
    if (c2 !== ":") return false;

    if (str.length === 3) return true;

    var c3 = str.charAt(3);
    if (c3 < "0" || c3 > "5") return false;

    if (str.length === 4) return true;

    var c4 = str.charAt(4);
    if (c4 < "0" || c4 > "9") return false;

    return true;
  }

  function setInputError(input, message) {
    input.classList.add("is-invalid");
    var row = input.closest(".km-schedule-editor__row");
    if (!row) return;

    var errorsContainer = row.querySelector(".km-schedule-editor__row-errors");
    if (!errorsContainer) {
      errorsContainer = document.createElement("div");
      errorsContainer.className = "km-schedule-editor__row-errors";
      var copySection = row.querySelector(".km-schedule-editor__copy");
      if (copySection) {
        row.insertBefore(errorsContainer, copySection);
      } else {
        row.appendChild(errorsContainer);
      }
    }

    var fieldType = input.hasAttribute("data-km-schedule-start") ? "start" : "end";
    var existing = errorsContainer.querySelector('.km-schedule-error-msg[data-field="' + fieldType + '"]');
    if (!existing) {
      existing = document.createElement("small");
      existing.className = "km-schedule-error-msg";
      existing.setAttribute("data-field", fieldType);
      errorsContainer.appendChild(existing);
    }
    existing.textContent = message;
  }

  function clearInputError(input) {
    input.classList.remove("is-invalid");
    var row = input.closest(".km-schedule-editor__row");
    if (!row) return;

    var errorsContainer = row.querySelector(".km-schedule-editor__row-errors");
    if (errorsContainer) {
      var fieldType = input.hasAttribute("data-km-schedule-start") ? "start" : "end";
      var existing = errorsContainer.querySelector('.km-schedule-error-msg[data-field="' + fieldType + '"]');
      if (existing) {
        existing.remove();
      }
      if (!errorsContainer.children.length) {
        errorsContainer.remove();
      }
    }
  }

  function validateRow(row, state) {
    var intervalDivs = row.querySelectorAll("[data-km-schedule-interval]");
    var rowValid = true;
    var weekday = row.getAttribute("data-km-schedule-row");
    var day = dayByWeekday(state, weekday);
    if (!day) return false;

    intervalDivs.forEach(function (intervalDiv, index) {
      var startInput = intervalDiv.querySelector("[data-km-schedule-start]");
      var endInput = intervalDiv.querySelector("[data-km-schedule-end]");
      if (!startInput || !endInput) return;

      var startVal = startInput.value.trim();
      var endVal = endInput.value.trim();

      clearInputError(startInput);
      clearInputError(endInput);

      var startNorm = startVal ? parseTimeStr(startVal) : null;
      var endNorm = endVal ? parseTimeStr(endVal) : null;

      if (startVal && !startNorm) {
        setInputError(startInput, "Неверный формат времени (ЧЧ:ММ)");
        rowValid = false;
      } else if (startVal) {
        startInput.value = startNorm;
      }

      if (endVal && !endNorm) {
        setInputError(endInput, "Неверный формат времени (ЧЧ:ММ)");
        rowValid = false;
      } else if (endVal) {
        endInput.value = endNorm;
      }

      if (rowValid) {
        if (startNorm && !endVal) {
          setInputError(endInput, "Заполните время окончания");
          rowValid = false;
        } else if (!startVal && endNorm) {
          setInputError(startInput, "Заполните время начала");
          rowValid = false;
        } else if (startNorm && endNorm) {
          var startMins = timeToMins(startNorm);
          var endMins = timeToMins(endNorm);
          if (startMins >= endMins) {
            setInputError(startInput, "Начало должно быть раньше окончания");
            rowValid = false;
          }
        }
      }

      if (day.intervals[index]) {
        day.intervals[index].start = startInput.value;
        day.intervals[index].end = endInput.value;
      }
    });

    if (rowValid) {
      var errorsContainer = row.querySelector(".km-schedule-editor__row-errors");
      if (errorsContainer) {
        errorsContainer.remove();
      }
    }

    updateInput(state);
    renderPreview(state);
    return rowValid;
  }

  function handleTimeArrowKeys(input, event, state) {
    event.preventDefault();
    var val = (input.value || "").trim();
    var current = parseTimeStr(val) || "09:00";
    var parts = current.split(":");
    var h = parseInt(parts[0], 10);
    var m = parseInt(parts[1], 10);

    var totalMinutes = h * 60 + m;
    var step = 15;

    if (event.key === "ArrowUp") {
      totalMinutes = (totalMinutes + step) % (24 * 60);
    } else {
      totalMinutes = (totalMinutes - step + 24 * 60) % (24 * 60);
    }

    var newH = Math.floor(totalMinutes / 60);
    var newM = totalMinutes % 60;

    var hh = (newH < 10 ? "0" : "") + newH;
    var mm = (newM < 10 ? "0" : "") + newM;

    input.value = hh + ":" + mm;

    var row = input.closest(".km-schedule-editor__row");
    if (row) {
      validateRow(row, state);
    }
  }

  function closeActiveDropdown() {
    if (activeDropdown) {
      activeDropdown.remove();
      activeDropdown = null;
    }
  }

  function openTimeDropdown(button, input, state) {
    var wrapper = button.closest(".km-schedule-editor__time-wrapper");
    if (!wrapper) return;

    if (activeDropdown && activeDropdown.parentNode === wrapper) {
      closeActiveDropdown();
      return;
    }
    closeActiveDropdown();

    var dropdown = document.createElement("div");
    dropdown.className = "km-schedule-editor__dropdown-list";

    var times = [];
    for (var h = 0; h < 24; h += 1) {
      var hh = (h < 10 ? "0" : "") + h;
      for (var m = 0; m < 60; m += 15) {
        var mm = (m < 10 ? "0" : "") + m;
        times.push(hh + ":" + mm);
      }
    }

    times.forEach(function (timeStr) {
      var item = document.createElement("div");
      item.className = "km-schedule-editor__dropdown-item";
      item.textContent = timeStr;

      if (input.value === timeStr) {
        item.classList.add("is-selected");
      }

      item.addEventListener("click", function (e) {
        e.stopPropagation();
        input.value = timeStr;

        var row = input.closest(".km-schedule-editor__row");
        if (row) {
          validateRow(row, state);
        }

        closeActiveDropdown();
      });
      dropdown.appendChild(item);
    });

    wrapper.appendChild(dropdown);
    activeDropdown = dropdown;

    var currentVal = input.value;
    if (currentVal) {
      var match = Array.from(dropdown.children).find(function (child) {
        return child.textContent === currentVal;
      });
      if (match) {
        dropdown.scrollTop = match.offsetTop - dropdown.clientHeight / 2 + match.clientHeight / 2;
      }
    }
  }

  function buildState(root) {
    var input = root.querySelector("[data-km-schedule-editor-input]") || document.querySelector("[data-km-schedule-editor-input]");
    var daysContainer = root.querySelector("[data-km-schedule-days]");
    var preview = root.querySelector("[data-km-schedule-preview]");
    if (!input || !daysContainer || !preview) {
      console.warn("KidsMap Schedule Editor - buildState failed: required DOM elements are missing", {
        input: input,
        daysContainer: daysContainer,
        preview: preview,
      });
      return null;
    }

    var config = localeConfig(root);
    return {
      root: root,
      input: input,
      daysContainer: daysContainer,
      preview: preview,
      config: config,
      days: normalizeDays(parsePayload(input.value))
    };
  }

  function normalizeDays(days) {
    var byWeekday = {};
    (days || []).forEach(function (day) {
      if (!day || !day.weekday) return;
      byWeekday[day.weekday] = {
        weekday: day.weekday,
        is_closed: !!day.is_closed,
        is_24_hours: !!day.is_24_hours,
        intervals: Array.isArray(day.intervals) ? day.intervals.filter(Boolean).map(function (interval) {
          return {
            start: interval.start || "",
            end: interval.end || "",
          };
        }) : [],
      };
    });

    return WEEKDAYS.map(function (weekday) {
      return byWeekday[weekday] || {
        weekday: weekday,
        is_closed: true,
        is_24_hours: false,
        intervals: [],
      };
    });
  }

  function updateInput(state) {
    state.input.value = dumpPayload(state.days);
    state.input.dispatchEvent(new Event("km:schedule-change", { bubbles: true }));
  }

  function weekdayLabel(state, weekday, mode) {
    return state.config[mode || "full"][weekday] || weekday;
  }

  function signature(day) {
    var intervals = (day.intervals || []).map(function (item) {
      return [item.start, item.end].join("-");
    }).join("|");
    return [day.is_closed ? "1" : "0", day.is_24_hours ? "1" : "0", intervals].join("::");
  }

  function groupedRows(state) {
    var rows = [];
    var current = null;

    state.days.forEach(function (day) {
      var daySignature = signature(day);
      if (!current || current.signature !== daySignature) {
        current = { signature: daySignature, items: [day] };
        rows.push(current);
        return;
      }
      current.items.push(day);
    });

    return rows.map(function (group) {
      var first = group.items[0];
      var daysLabel;
      if (group.items.length === 1) {
        daysLabel = weekdayLabel(state, first.weekday, "short");
      } else {
        daysLabel = weekdayLabel(state, group.items[0].weekday, "short") + "–" + weekdayLabel(state, group.items[group.items.length - 1].weekday, "short");
      }

      if (first.is_closed) {
        return { days: daysLabel, lines: [state.root.dataset.previewClosedLabel || "Закрыто"] };
      }
      if (first.is_24_hours) {
        return { days: daysLabel, lines: [state.root.dataset.allDayLabel || "24 часа"] };
      }
      return {
        days: daysLabel,
        lines: (first.intervals || []).map(function (interval) {
          if (!interval.start || !interval.end) return "??:??–??:??";
          return interval.start + "–" + interval.end;
        }),
      };
    });
  }

  function renderPreview(state) {
    var rows = groupedRows(state).filter(function (row) {
      return row.lines && row.lines.length;
    });
    if (!rows.length) {
      state.preview.innerHTML = '<p class="km-schedule-editor__preview-empty">' + escapeHtml(state.root.dataset.previewEmptyLabel || "") + "</p>";
      return;
    }

    state.preview.innerHTML = rows.map(function (row) {
      return (
        '<div class="km-schedule-editor__preview-row">' +
          '<span class="km-schedule-editor__preview-days">' + escapeHtml(row.days) + "</span>" +
          '<div class="km-schedule-editor__preview-lines">' +
            row.lines.map(function (line) {
              return '<span class="km-schedule-editor__preview-line">' + escapeHtml(line) + "</span>";
            }).join("") +
          "</div>" +
        "</div>"
      );
    }).join("");
  }

  function renderIntervalsHtml(state, day) {
    if (day.is_closed) {
      return '<span class="km-schedule-editor__state-copy">' + escapeHtml(state.root.dataset.closedLabel || "") + "</span>";
    }
    if (day.is_24_hours) {
      return '<span class="km-schedule-editor__state-copy km-schedule-editor__state-copy--active">' + escapeHtml(state.root.dataset.allDayLabel || "") + "</span>";
    }

    var intervals = day.intervals && day.intervals.length ? day.intervals : [{ start: "", end: "" }];
    return (
      '<div class="km-schedule-editor__intervals">' +
        intervals.map(function (interval, index) {
          var hideRemove = intervals.length <= 1 ? ' style="display:none;"' : "";
          var lang = ((document.documentElement.lang || "ru").split("-")[0] || "ru").toLowerCase();
          var startAria = lang === "az" ? "Başlama vaxtı" : (lang === "en" ? "Start time" : "Время начала");
          var endAria = lang === "az" ? "Bitmə vaxtı" : (lang === "en" ? "End time" : "Время окончания");
          var pickerAria = lang === "az" ? "Vaxtı seçin" : (lang === "en" ? "Select time" : "Выбрать время");

          return (
            '<div class="km-schedule-editor__interval" data-km-schedule-interval data-weekday="' + day.weekday + '" data-index="' + index + '">' +
              '<div class="km-schedule-editor__time-wrapper">' +
                '<input type="text" inputmode="numeric" maxlength="5" autocomplete="off" placeholder="09:00" class="km-schedule-editor__time" data-km-schedule-start value="' + escapeHtml(interval.start) + '" aria-label="' + startAria + '">' +
                '<button type="button" class="km-schedule-editor__picker-btn" aria-label="' + pickerAria + '">🕒</button>' +
              '</div>' +
              '<span class="km-schedule-editor__dash">—</span>' +
              '<div class="km-schedule-editor__time-wrapper">' +
                '<input type="text" inputmode="numeric" maxlength="5" autocomplete="off" placeholder="18:00" class="km-schedule-editor__time" data-km-schedule-end value="' + escapeHtml(interval.end) + '" aria-label="' + endAria + '">' +
                '<button type="button" class="km-schedule-editor__picker-btn" aria-label="' + pickerAria + '">🕒</button>' +
              '</div>' +
              '<button type="button" class="km-schedule-editor__icon-btn" data-km-schedule-remove-interval="' + day.weekday + '" data-index="' + index + '" aria-label="' + escapeHtml(state.root.dataset.removeLabel || "") + '"' + hideRemove + '>×</button>' +
            "</div>"
          );
        }).join("") +
      "</div>"
    );
  }

  function syncDayRowDom(state, day) {
    closeActiveDropdown();

    var row = state.daysContainer.querySelector('[data-km-schedule-row="' + day.weekday + '"]');
    if (!row) return;

    var openCheckbox = row.querySelector('[data-km-schedule-open="' + day.weekday + '"]');
    if (openCheckbox) {
      openCheckbox.checked = !day.is_closed;
      openCheckbox.setAttribute("aria-checked", !day.is_closed ? "true" : "false");
    }
    var toggleText = row.querySelector(".km-schedule-editor__toggle-text");
    if (toggleText) {
      toggleText.textContent = day.is_closed ? state.root.dataset.closedLabel : state.root.dataset.openLabel;
    }

    var allDayCheckbox = row.querySelector('[data-km-schedule-24="' + day.weekday + '"]');
    if (allDayCheckbox) {
      allDayCheckbox.checked = day.is_24_hours;
      allDayCheckbox.disabled = day.is_closed;
      var parentLabel = allDayCheckbox.closest(".km-schedule-editor__checkbox");
      if (parentLabel) {
        if (day.is_closed) {
          parentLabel.classList.add("is-disabled");
        } else {
          parentLabel.classList.remove("is-disabled");
        }
      }
    }

    var workDiv = row.querySelector(".km-schedule-editor__work");
    if (workDiv) {
      workDiv.innerHTML = renderIntervalsHtml(state, day);
    }

    var addBtn = row.querySelector('[data-km-schedule-add-interval="' + day.weekday + '"]');
    if (addBtn) {
      addBtn.disabled = day.is_closed || day.is_24_hours;
    }

    var errorsDiv = row.querySelector(".km-schedule-editor__row-errors");
    if (errorsDiv) {
      errorsDiv.remove();
    }
  }

  function syncAllRowsDom(state) {
    state.days.forEach(function (day) {
      syncDayRowDom(state, day);
    });
  }

  function dayByWeekday(state, weekday) {
    for (var i = 0; i < state.days.length; i += 1) {
      if (state.days[i].weekday === weekday) return state.days[i];
    }
    return null;
  }

  function cloneDay(day, targetWeekday) {
    return {
      weekday: targetWeekday || day.weekday,
      is_closed: !!day.is_closed,
      is_24_hours: !!day.is_24_hours,
      intervals: (day.intervals || []).map(function (interval) {
        return { start: interval.start || "", end: interval.end || "" };
      }),
    };
  }

  function applyPreset(state, preset) {
    if (preset === "clear") {
      var confirmMsg = state.root.dataset.confirmClear || "Вы уверены, что хотите очистить расписание?";
      if (!confirm(confirmMsg)) return;
      state.days = defaultDays();
    } else if (preset === "always-open") {
      state.days = WEEKDAYS.map(function (weekday) {
        return { weekday: weekday, is_closed: false, is_24_hours: true, intervals: [] };
      });
    } else if (preset === "all-days") {
      state.days = WEEKDAYS.map(function (weekday) {
        return { weekday: weekday, is_closed: false, is_24_hours: false, intervals: [{ start: "09:00", end: "21:00" }] };
      });
    } else if (preset === "weekdays") {
      state.days = WEEKDAYS.map(function (weekday) {
        if (["mon", "tue", "wed", "thu", "fri"].indexOf(weekday) !== -1) {
          return { weekday: weekday, is_closed: false, is_24_hours: false, intervals: [{ start: "09:00", end: "18:00" }] };
        }
        return { weekday: weekday, is_closed: true, is_24_hours: false, intervals: [] };
      });
    } else if (preset === "weekday-weekend") {
      state.days = WEEKDAYS.map(function (weekday) {
        if (["mon", "tue", "wed", "thu", "fri"].indexOf(weekday) !== -1) {
          return { weekday: weekday, is_closed: false, is_24_hours: false, intervals: [{ start: "09:00", end: "18:00" }] };
        }
        return { weekday: weekday, is_closed: false, is_24_hours: false, intervals: [{ start: "10:00", end: "18:00" }] };
      });
    }

    syncAllRowsDom(state);
    updateInput(state);
    renderPreview(state);
  }

  function bindEvents(state) {
    state.root.addEventListener("click", function (event) {
      var target = event.target.closest("[data-km-schedule-preset], [data-km-schedule-add-interval], [data-km-schedule-remove-interval], [data-km-schedule-copy-day], [data-km-schedule-copy-weekdays], [data-km-schedule-open-copy-picker], [data-km-schedule-close-copy], [data-km-schedule-apply-copy], .km-schedule-editor__picker-btn");
      if (!target) return;

      if (target.closest(".km-schedule-editor__picker-btn")) {
        var pickerBtn = target.closest(".km-schedule-editor__picker-btn");
        event.preventDefault();
        event.stopPropagation();
        var wrapper = pickerBtn.closest(".km-schedule-editor__time-wrapper");
        if (wrapper) {
          var input = wrapper.querySelector("input");
          if (input) {
            openTimeDropdown(pickerBtn, input, state);
          }
        }
        return;
      }

      if (target.hasAttribute("data-km-schedule-preset")) {
        applyPreset(state, target.getAttribute("data-km-schedule-preset"));
        return;
      }

      if (target.hasAttribute("data-km-schedule-add-interval")) {
        var day = dayByWeekday(state, target.getAttribute("data-km-schedule-add-interval"));
        if (!day) return;
        day.is_closed = false;
        day.is_24_hours = false;
        day.intervals.push({ start: "09:00", end: "21:00" });
        syncDayRowDom(state, day);
        updateInput(state);
        renderPreview(state);
        return;
      }

      if (target.hasAttribute("data-km-schedule-remove-interval")) {
        var removeDay = dayByWeekday(state, target.getAttribute("data-km-schedule-remove-interval"));
        var removeIndex = Number(target.getAttribute("data-index"));
        if (!removeDay) return;

        removeDay.intervals.splice(removeIndex, 1);
        syncDayRowDom(state, removeDay);
        updateInput(state);
        renderPreview(state);
        return;
      }

      var copyBtn = target.closest("[data-km-schedule-copy-day]");
      if (copyBtn) {
        var sourceWeekday = copyBtn.getAttribute("data-km-schedule-copy-day");
        openCopyPopover(copyBtn, sourceWeekday, state);
        return;
      }
    });

    state.root.addEventListener("change", function (event) {
      var target = event.target;
      if (target.hasAttribute("data-km-schedule-open")) {
        var openDay = dayByWeekday(state, target.getAttribute("data-km-schedule-open"));
        if (!openDay) return;
        openDay.is_closed = !target.checked;
        if (openDay.is_closed) {
          openDay.is_24_hours = false;
          openDay.intervals = [];
        } else {
          openDay.is_24_hours = false;
          openDay.intervals = [{ start: "09:00", end: "21:00" }];
        }
        syncDayRowDom(state, openDay);
        updateInput(state);
        renderPreview(state);
        return;
      }

      if (target.hasAttribute("data-km-schedule-24")) {
        var allDay = dayByWeekday(state, target.getAttribute("data-km-schedule-24"));
        if (!allDay) return;
        allDay.is_24_hours = !!target.checked;
        if (allDay.is_24_hours) {
          allDay.is_closed = false;
          allDay.intervals = [];
        } else {
          allDay.intervals = [{ start: "09:00", end: "21:00" }];
        }
        syncDayRowDom(state, allDay);
        updateInput(state);
        renderPreview(state);
        return;
      }
    });

    state.root.addEventListener("input", function (event) {
      var target = event.target;
      if (target.hasAttribute("data-km-schedule-start") || target.hasAttribute("data-km-schedule-end")) {
        var oldVal = target._lastValidValue !== undefined ? target._lastValidValue : target.defaultValue || "";
        var val = target.value;
        var sanitized = val.replace(/[^0-9:]/g, "");

        var isDelete = event.inputType && event.inputType.indexOf("delete") !== -1;
        if (!isDelete) {
          if (sanitized.length === 2 && sanitized.indexOf(":") === -1) {
            sanitized = sanitized + ":";
          } else if (sanitized.length === 3 && sanitized.indexOf(":") === -1) {
            sanitized = sanitized.substring(0, 2) + ":" + sanitized.substring(2);
          } else if (sanitized.length === 4 && sanitized.indexOf(":") === -1) {
            sanitized = sanitized.substring(0, 2) + ":" + sanitized.substring(2);
          }
        }

        if (isValidPartialTime(sanitized)) {
          target.value = sanitized;
          target._lastValidValue = sanitized;
        } else {
          target.value = oldVal;
        }

        var intervalRow = target.closest("[data-km-schedule-interval]");
        if (!intervalRow) return;
        var weekday = intervalRow.getAttribute("data-weekday");
        var index = Number(intervalRow.getAttribute("data-index"));
        var intervalDay = dayByWeekday(state, weekday);
        if (!intervalDay || !intervalDay.intervals[index]) return;
        intervalDay.intervals[index].start = intervalRow.querySelector("[data-km-schedule-start]").value || "";
        intervalDay.intervals[index].end = intervalRow.querySelector("[data-km-schedule-end]").value || "";
        updateInput(state);
        renderPreview(state);
      }
    });

    state.root.addEventListener("focusout", function (event) {
      var target = event.target;
      if (target.hasAttribute("data-km-schedule-start") || target.hasAttribute("data-km-schedule-end")) {
        var row = target.closest(".km-schedule-editor__row");
        if (row) {
          validateRow(row, state);
        }
      }
    });

    state.root.addEventListener("keydown", function (event) {
      var target = event.target;
      if (target.hasAttribute("data-km-schedule-start") || target.hasAttribute("data-km-schedule-end")) {
        if (event.key === "ArrowUp" || event.key === "ArrowDown") {
          handleTimeArrowKeys(target, event, state);
        } else if (event.key === "Enter") {
          event.preventDefault();
          var row = target.closest(".km-schedule-editor__row");
          if (row) {
            validateRow(row, state);
          }
          target.blur();
        }
      }
    });
  }

  function openCopyPopover(button, sourceWeekday, state) {
    closePopover();

    var popover = document.createElement("div");
    popover.className = "km-schedule-editor__copy-popover";

    var daysHtml = WEEKDAYS.filter(function (wd) {
      return wd !== sourceWeekday;
    }).map(function (wd) {
      return (
        '<label class="km-schedule-editor__popover-day">' +
          '<input type="checkbox" value="' + wd + '">' +
          '<span>' + escapeHtml(weekdayLabel(state, wd, "full")) + '</span>' +
        '</label>'
      );
    }).join("");

    var lang = ((document.documentElement.lang || "ru").split("-")[0] || "ru").toLowerCase();
    var presetWeekdaysText = lang === "az" ? "Bütün iş günləri" : (lang === "en" ? "All weekdays" : "Все будние дни");
    var presetWeekendsText = lang === "az" ? "Bütün istirahət günləri" : (lang === "en" ? "All weekends" : "Все выходные");
    var presetAllText = lang === "az" ? "Bütün günlər" : (lang === "en" ? "All days" : "Все дни");
    var presetNoneText = lang === "az" ? "Seçimi təmizlə" : (lang === "en" ? "Clear selection" : "Снять выбор");
    var cancelText = lang === "az" ? "Ləğv et" : (lang === "en" ? "Cancel" : "Отмена");
    var applyText = lang === "az" ? "Tətbiq et" : (lang === "en" ? "Apply" : "Применить");

    popover.innerHTML = 
      '<div class="km-schedule-editor__popover-head">' +
        '<strong>' + escapeHtml(getCopyTitle(state, sourceWeekday)) + '</strong>' +
        '<button type="button" class="km-schedule-editor__popover-close" data-popover-close>×</button>' +
      '</div>' +
      '<div class="km-schedule-editor__popover-days">' +
        daysHtml +
      '</div>' +
      '<div class="km-schedule-editor__popover-presets">' +
        '<button type="button" class="km-schedule-editor__popover-preset" data-preset="weekdays">' + escapeHtml(presetWeekdaysText) + '</button>' +
        '<button type="button" class="km-schedule-editor__popover-preset" data-preset="weekends">' + escapeHtml(presetWeekendsText) + '</button>' +
        '<button type="button" class="km-schedule-editor__popover-preset" data-preset="all">' + escapeHtml(presetAllText) + '</button>' +
        '<button type="button" class="km-schedule-editor__popover-preset" data-preset="none">' + escapeHtml(presetNoneText) + '</button>' +
      '</div>' +
      '<div class="km-schedule-editor__popover-buttons">' +
        '<button type="button" class="km-schedule-editor__popover-btn km-schedule-editor__popover-btn--cancel" data-popover-close>' + escapeHtml(cancelText) + '</button>' +
        '<button type="button" class="km-schedule-editor__popover-btn km-schedule-editor__popover-btn--apply">' + escapeHtml(applyText) + '</button>' +
      '</div>';

    popover.addEventListener("click", function (e) {
      var presetBtn = e.target.closest("[data-preset]");
      if (presetBtn) {
        var preset = presetBtn.getAttribute("data-preset");
        var checkboxes = popover.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(function (cb) {
          var wd = cb.value;
          if (preset === "all") {
            cb.checked = true;
          } else if (preset === "none") {
            cb.checked = false;
          } else if (preset === "weekdays") {
            cb.checked = ["mon", "tue", "wed", "thu", "fri"].indexOf(wd) !== -1;
          } else if (preset === "weekends") {
            cb.checked = ["sat", "sun"].indexOf(wd) !== -1;
          }
        });
        return;
      }

      var closeBtn = e.target.closest("[data-popover-close]");
      if (closeBtn) {
        closePopover();
        return;
      }

      var applyBtn = e.target.closest(".km-schedule-editor__popover-btn--apply");
      if (applyBtn) {
        applyCopy(state, sourceWeekday, popover);
      }
    });

    var isMobile = window.innerWidth <= 767;
    if (isMobile) {
      var overlay = document.createElement("div");
      overlay.className = "km-schedule-editor__popover-overlay";
      overlay.addEventListener("click", function () {
        closePopover();
      });
      state.root.appendChild(overlay);
      state.root.appendChild(popover);
    } else {
      state.root.appendChild(popover);
      var rect = button.getBoundingClientRect();
      var editorRect = state.root.getBoundingClientRect();
      var topPos = rect.top - editorRect.top + button.offsetHeight;
      var rightPos = editorRect.right - rect.right;
      
      popover.style.top = topPos + "px";
      popover.style.right = rightPos + "px";
    }
  }

  function getCopyTitle(state, weekday) {
    var lang = ((document.documentElement.lang || "ru").split("-")[0] || "ru").toLowerCase();
    if (lang === "ru") {
      var names = {
        mon: "понедельника",
        tue: "вторника",
        wed: "среды",
        thu: "четверга",
        fri: "пятницы",
        sat: "субботы",
        sun: "воскресенья"
      };
      return "Скопировать расписание " + (names[weekday] || weekday);
    } else if (lang === "az") {
      var namesAz = {
        mon: "Bazar ertəsi",
        tue: "Çərşənbə axşamı",
        wed: "Çərşənbə",
        thu: "Cümə axşamı",
        fri: "Cümə",
        sat: "Şənbə",
        sun: "Bazar"
      };
      return namesAz[weekday] + " cədvəlini kopyala";
    } else {
      var namesEn = {
        mon: "Monday",
        tue: "Tuesday",
        wed: "Wednesday",
        thu: "Thursday",
        fri: "Friday",
        sat: "Saturday",
        sun: "Sunday"
      };
      return "Copy " + (namesEn[weekday] || weekday) + " schedule";
    }
  }

  function formatSuccessMsg(count) {
    var lang = ((document.documentElement.lang || "ru").split("-")[0] || "ru").toLowerCase();
    if (lang === "ru") {
      var word;
      if (count === 1) word = "день";
      else if (count >= 2 && count <= 4) word = "дня";
      else word = "дней";
      return "Расписание скопировано на " + count + " " + word + ".";
    } else if (lang === "az") {
      return "Cədvəl " + count + " günə kopyalandı.";
    } else {
      return "Schedule copied to " + count + " " + (count === 1 ? "day" : "days") + ".";
    }
  }

  function closePopover() {
    var activePopover = document.querySelector(".km-schedule-editor__copy-popover");
    if (activePopover) activePopover.remove();
    var activeOverlay = document.querySelector(".km-schedule-editor__popover-overlay");
    if (activeOverlay) activeOverlay.remove();
  }

  function applyCopy(state, sourceWeekday, popover) {
    var sourceDay = dayByWeekday(state, sourceWeekday);
    if (!sourceDay) return;
    
    var checked = Array.from(popover.querySelectorAll('input[type="checkbox"]:checked'));
    if (checked.length === 0) {
      closePopover();
      return;
    }

    var anyHasSchedule = checked.some(function (item) {
      var targetDay = dayByWeekday(state, item.value);
      return targetDay && (!targetDay.is_closed || targetDay.is_24_hours || targetDay.intervals.length > 0);
    });

    if (anyHasSchedule) {
      var confirmMsg = "Расписание выбранных дней будет заменено. Продолжить?";
      var lang = ((document.documentElement.lang || "ru").split("-")[0] || "ru").toLowerCase();
      if (lang === "az") {
        confirmMsg = "Seçilmiş günlərin cədvəli əvəzlənəcək. Davam edilsin?";
      } else if (lang === "en") {
        confirmMsg = "The schedule for selected days will be overwritten. Continue?";
      }
      if (!confirm(confirmMsg)) return;
    }

    checked.forEach(function (item) {
      var targetDay = dayByWeekday(state, item.value);
      if (targetDay) {
        var clone = cloneDay(sourceDay, item.value);
        targetDay.is_closed = clone.is_closed;
        targetDay.is_24_hours = clone.is_24_hours;
        targetDay.intervals = clone.intervals;
        syncDayRowDom(state, targetDay);
      }
    });

    closePopover();
    updateInput(state);
    renderPreview(state);

    showToast(state, formatSuccessMsg(checked.length));
  }

  function showToast(state, message) {
    var toast = state.root.querySelector("[data-km-schedule-toast]");
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    toast.classList.add("is-show");
    
    if (toast._timeoutId) {
      clearTimeout(toast._timeoutId);
    }
    
    toast._timeoutId = setTimeout(function () {
      toast.classList.remove("is-show");
      setTimeout(function () {
        toast.hidden = true;
      }, 300);
    }, 3000);
  }

  function initEditor(root) {
    if (!root || root.dataset.kmScheduleInitialized === "1") return;
    var state = buildState(root);
    if (!state) return;
    root.dataset.kmScheduleInitialized = "1";
    bindEvents(state);
    renderPreview(state);
  }

  function initAllEditors() {
    document.querySelectorAll("[data-km-schedule-editor]").forEach(initEditor);
  }

  window.kidsMapInitScheduleEditors = initAllEditors;
  window.initScheduleTimePickers = function () {
    // Left as empty stub for backward compatibility. Event delegation handles initialization.
  };

  document.addEventListener("click", function (event) {
    if (activeDropdown && !event.target.closest(".km-schedule-editor__time-wrapper")) {
      closeActiveDropdown();
    }
    var popover = document.querySelector(".km-schedule-editor__copy-popover");
    if (popover && !popover.contains(event.target) && !event.target.closest("[data-km-schedule-copy-day]")) {
      closePopover();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeActiveDropdown();
      closePopover();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAllEditors);
  } else {
    initAllEditors();
  }
})();
