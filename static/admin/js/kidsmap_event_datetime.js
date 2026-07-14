(function () {
  function formatDuration(milliseconds) {
    var totalMinutes = Math.round(milliseconds / 60000);
    if (totalMinutes <= 0) return "";
    var days = Math.floor(totalMinutes / 1440);
    var hours = Math.floor((totalMinutes % 1440) / 60);
    var minutes = totalMinutes % 60;
    var parts = [];
    if (days) parts.push(days + " д.");
    if (hours) parts.push(hours + " ч.");
    if (minutes) parts.push(minutes + " мин.");
    return parts.join(" ");
  }

  function init() {
    var start = document.querySelector('[data-event-datetime="start"]');
    var end = document.querySelector('[data-event-datetime="end"]');
    var summary = document.querySelector('[data-event-datetime-summary]');
    if (!start || !end || start.dataset.eventDateTimeBound === "1") return;

    function sync() {
      var startPicker = start._flatpickr;
      var endPicker = end._flatpickr;
      var startDate = startPicker && startPicker.selectedDates[0];
      var endDate = endPicker && endPicker.selectedDates[0];
      if (endPicker) endPicker.set("minDate", startDate || null);
      if (!summary) return;
      if (!startDate || !endDate) {
        summary.textContent = "Выберите начало и окончание — система покажет продолжительность.";
        return;
      }
      var duration = endDate.getTime() - startDate.getTime();
      summary.textContent = duration > 0 ? "Продолжительность: " + formatDuration(duration) : "Окончание должно быть позже начала.";
      summary.classList.toggle("is-error", duration <= 0);
    }

    [start, end].forEach(function (input) {
      input.addEventListener("change", sync);
      input.addEventListener("input", sync);
    });
    start.dataset.eventDateTimeBound = "1";
    sync();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
