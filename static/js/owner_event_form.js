(function () {
  const form = document.querySelector("[data-event-form]");
  if (!form) return;

  const relatedSelect = form.querySelector("[data-event-related-place]");
  const formatSelect = form.querySelector('[name="event_format"]');
  const addressInput = form.querySelector('[name="address"]');
  const phoneInput = form.querySelector('[name="phone"]');
  const latInput = form.querySelector('[name="lat"]');
  const lngInput = form.querySelector('[name="lng"]');
  const districtInput = form.querySelector('[name="district"]');
  const metroInput = form.querySelector('[name="metro"]');
  const descriptionInput = form.querySelector('[name="description_az"]');
  const counter = document.getElementById("event-description-counter");
  const eventDateInput = form.querySelector('[name="event_date"]');
  const startTimeInput = form.querySelector('[name="start_time_input"]');
  const endDateInput = form.querySelector('[name="end_date"]');
  const endTimeInput = form.querySelector('[name="end_time_input"]');
  const pastDateMessage = form.dataset.pastDateMessage || "";
  const endBeforeStartMessage = form.dataset.endBeforeStartMessage || "";
  const durationSummary = form.querySelector("[data-owner-event-datetime-summary]");

  function formatDuration(milliseconds) {
    const minutes = Math.round(milliseconds / 60000);
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    const parts = [];
    if (hours) parts.push(hours + " " + (form.dataset.durationHour || ""));
    if (remainingMinutes) parts.push(remainingMinutes + " " + (form.dataset.durationMinute || ""));
    return parts.join(" ");
  }

  function updateDurationSummary() {
    if (!durationSummary) return;
    const start = parseDateTime(eventDateInput && eventDateInput.value, startTimeInput && startTimeInput.value);
    const end = parseDateTime((endDateInput && endDateInput.value) || (eventDateInput && eventDateInput.value), endTimeInput && endTimeInput.value);
    if (!start || !end) {
      durationSummary.textContent = durationSummary.dataset.emptyLabel || "";
      durationSummary.classList.remove("is-error");
      return;
    }
    const duration = end.getTime() - start.getTime();
    durationSummary.textContent = duration > 0 ? (durationSummary.dataset.durationLabel || "") + ": " + formatDuration(duration) : (durationSummary.dataset.invalidLabel || "");
    durationSummary.classList.toggle("is-error", duration <= 0);
  }

  function syncRelatedPlaceDetails() {
    if (formatSelect && formatSelect.value === form.dataset.onlineFormat) return;
    if (!relatedSelect) return;
    const option = relatedSelect.options[relatedSelect.selectedIndex];
    if (!option) return;
    const address = option.getAttribute("data-address") || "";
    const phone = option.getAttribute("data-phone") || "";
    const lat = option.getAttribute("data-lat") || "";
    const lng = option.getAttribute("data-lng") || "";
    const district = option.getAttribute("data-district") || "";
    const metro = option.getAttribute("data-metro") || "";
    if (addressInput && !addressInput.value.trim() && address) {
      addressInput.value = address;
      addressInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
    if (phoneInput && !phoneInput.value.trim() && phone) {
      phoneInput.value = phone;
      phoneInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
    if (latInput && !latInput.value && lat) latInput.value = lat;
    if (lngInput && !lngInput.value && lng) lngInput.value = lng;
    if (districtInput && !districtInput.value && district) {
      districtInput.value = district;
      districtInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
    if (metroInput && !metroInput.value && metro) {
      metroInput.value = metro;
      metroInput.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }

  function syncEventFormat() {
    const online = formatSelect && formatSelect.value === form.dataset.onlineFormat;
    form.querySelectorAll('[data-event-physical]').forEach(function (section) {
      section.hidden = online;
      section.style.display = online ? 'none' : '';
      section.querySelectorAll('input, select, textarea, button').forEach(function (field) {
        if (!field.hasAttribute('data-event-physical-required')) {
          field.dataset.eventPhysicalRequired = field.required ? '1' : '0';
        }
        field.disabled = online;
        field.required = !online && field.dataset.eventPhysicalRequired === '1';
      });
    });
  }

  function updateCounter() {
    if (!descriptionInput || !counter) return;
    counter.textContent = String(descriptionInput.value.length);
  }

  function parseDateTime(dateValue, timeValue) {
    if (!dateValue || !timeValue) return null;
    const parsed = new Date(dateValue + "T" + timeValue + ":00" + form.dataset.eventUtcOffset);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function bakuToday() {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: form.dataset.eventTimezone, year: 'numeric', month: '2-digit', day: '2-digit',
    }).formatToParts(new Date());
    const values = Object.fromEntries(parts.map(function (part) { return [part.type, part.value]; }));
    return values.year + '-' + values.month + '-' + values.day;
  }

  function startOfToday() {
    return new Date(bakuToday() + 'T00:00:00' + form.dataset.eventUtcOffset);
  }

  function syncEndDateMin() {
    if (eventDateInput && eventDateInput._flatpickr) eventDateInput._flatpickr.set('minDate', bakuToday());
    if (!endDateInput || !endDateInput._flatpickr) return;
    endDateInput._flatpickr.set("minDate", eventDateInput && eventDateInput.value ? eventDateInput.value : bakuToday());
  }

  function setFieldValidity(field, message) {
    if (!field) return;
    field.setCustomValidity(message || "");
    if (field._flatpickr && field._flatpickr.altInput) {
      field._flatpickr.altInput.setCustomValidity(message || "");
    }
  }

  function validateEventDateTime() {
    if (!eventDateInput || !startTimeInput || !endTimeInput) return;

    setFieldValidity(eventDateInput, "");
    setFieldValidity(startTimeInput, "");
    setFieldValidity(endTimeInput, "");
    setFieldValidity(endDateInput, "");

    const selectedDate = eventDateInput.value;
    const selectedEndDate = (endDateInput && endDateInput.value) || selectedDate;

    if (selectedDate) {
      const dateOnly = new Date(selectedDate + "T00:00:00" + form.dataset.eventUtcOffset);
      if (!Number.isNaN(dateOnly.getTime()) && dateOnly < startOfToday()) {
        setFieldValidity(eventDateInput, pastDateMessage);
      }
    }

    const startDateTime = parseDateTime(selectedDate, startTimeInput.value);
    const endDateTime = parseDateTime(selectedEndDate, endTimeInput.value);

    if (startDateTime && startDateTime < new Date()) {
      setFieldValidity(eventDateInput, pastDateMessage);
    }

    if (startDateTime && endDateTime && endDateTime <= startDateTime) {
      setFieldValidity(endTimeInput, endBeforeStartMessage);
    }
  }

  relatedSelect?.addEventListener("change", syncRelatedPlaceDetails);
  formatSelect?.addEventListener('change', syncEventFormat);
  form.querySelectorAll('[data-map-search-input]').forEach(function (input) {
    input.setAttribute('aria-label', form.dataset.mapSearchLabel || '');
  });
  descriptionInput?.addEventListener("input", updateCounter);
  [eventDateInput, startTimeInput, endDateInput, endTimeInput].forEach(function (field) {
    field?.addEventListener("change", function () {
      syncEndDateMin();
      validateEventDateTime();
      updateDurationSummary();
    });
    field?.addEventListener("input", validateEventDateTime);
  });

  form.addEventListener("submit", function () {
    syncEndDateMin();
    validateEventDateTime();
  });

  syncEndDateMin();
  document.addEventListener('DOMContentLoaded', syncEndDateMin, { once: true });
  syncEventFormat();
  validateEventDateTime();
  updateDurationSummary();
  updateCounter();
})();
