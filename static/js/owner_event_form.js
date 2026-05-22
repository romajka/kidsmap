(function () {
  const form = document.querySelector("[data-event-form]");
  if (!form) return;

  const relatedSelect = form.querySelector("[data-event-related-place]");
  const addressInput = form.querySelector('[name="address"]');
  const phoneInput = form.querySelector('[name="phone"]');
  const descriptionInput = form.querySelector('[name="description_az"]');
  const counter = document.getElementById("event-description-counter");
  const eventDateInput = form.querySelector('[name="event_date"]');
  const startTimeInput = form.querySelector('[name="start_time_input"]');
  const endDateInput = form.querySelector('[name="end_date"]');
  const endTimeInput = form.querySelector('[name="end_time_input"]');
  const pastDateMessage = form.dataset.pastDateMessage || "";
  const endBeforeStartMessage = form.dataset.endBeforeStartMessage || "";

  function syncRelatedPlaceDetails() {
    if (!relatedSelect) return;
    const option = relatedSelect.options[relatedSelect.selectedIndex];
    if (!option) return;
    const address = option.getAttribute("data-address") || "";
    const phone = option.getAttribute("data-phone") || "";
    if (addressInput && !addressInput.value.trim() && address) {
      addressInput.value = address;
      addressInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
    if (phoneInput && !phoneInput.value.trim() && phone) {
      phoneInput.value = phone;
      phoneInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }

  function updateCounter() {
    if (!descriptionInput || !counter) return;
    counter.textContent = String(descriptionInput.value.length);
  }

  function parseDateTime(dateValue, timeValue) {
    if (!dateValue || !timeValue) return null;
    const parsed = new Date(dateValue + "T" + timeValue + ":00");
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function startOfToday() {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return now;
  }

  function syncEndDateMin() {
    if (!endDateInput || !endDateInput._flatpickr) return;
    endDateInput._flatpickr.set("minDate", eventDateInput && eventDateInput.value ? eventDateInput.value : "today");
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
      const dateOnly = new Date(selectedDate + "T00:00:00");
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
  descriptionInput?.addEventListener("input", updateCounter);
  [eventDateInput, startTimeInput, endDateInput, endTimeInput].forEach(function (field) {
    field?.addEventListener("change", function () {
      syncEndDateMin();
      validateEventDateTime();
    });
    field?.addEventListener("input", validateEventDateTime);
  });

  form.addEventListener("submit", function () {
    syncEndDateMin();
    validateEventDateTime();
  });

  syncEndDateMin();
  validateEventDateTime();
  updateCounter();
})();
