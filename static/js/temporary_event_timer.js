(function () {
  function parseDate(value) {
    if (!value) return null;
    var date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function formatRemaining(milliseconds, labels) {
    var safeMs = Math.max(milliseconds, 0);
    var totalSeconds = Math.max(Math.ceil(safeMs / 1000), 1);
    var totalMinutes = Math.ceil(totalSeconds / 60);
    var days = Math.floor(totalMinutes / 1440);
    var hours = Math.floor((totalMinutes % 1440) / 60);
    var minutes = totalMinutes % 60;
    var seconds = totalSeconds % 60;
    var parts = [];

    if (days === 0 && totalSeconds < 86400) {
      parts.push(hours + " " + labels.hours);
      parts.push(minutes + " " + labels.minutes);
      parts.push(seconds + " " + labels.seconds);
      return parts.join(" ");
    }

    if (days > 0) parts.push(days + " " + labels.days);
    if (hours > 0 || days > 0) parts.push(hours + " " + labels.hours);
    if (days === 0) parts.push(minutes + " " + labels.minutes);
    return parts.join(" ");
  }

  function updateTimer(root) {
    var start = parseDate(root.dataset.temporaryStart || "");
    var end = parseDate(root.dataset.temporaryEnd || "");
    var text = root.querySelector("[data-temporary-event-timer-text]");
    if (!text) return;

    var now = new Date();
    var labels = {
      upcoming: root.dataset.labelUpcoming || "Starts in",
      running: root.dataset.labelRunning || "Now",
      ending: root.dataset.labelEnding || "Ends in",
      ended: root.dataset.labelEnded || "Ended",
      days: root.dataset.labelDays || "d",
      hours: root.dataset.labelHours || "h",
      minutes: root.dataset.labelMinutes || "min",
      seconds: root.dataset.labelSeconds || "sec"
    };

    if (end && now > end) {
      root.dataset.temporaryState = "ended";
      text.textContent = labels.ended;
      return;
    }

    if (start && now < start) {
      root.dataset.temporaryState = "upcoming";
      text.textContent = labels.upcoming + ": " + formatRemaining(start - now, labels);
      return;
    }

    root.dataset.temporaryState = "running";
    if (end) {
      text.textContent = labels.running + " · " + labels.ending + ": " + formatRemaining(end - now, labels);
    } else {
      text.textContent = labels.running;
    }
  }

  function boot() {
    var timers = Array.prototype.slice.call(document.querySelectorAll("[data-temporary-event-timer]"));
    if (!timers.length) return;

    timers.forEach(updateTimer);
    window.setInterval(function () {
      timers.forEach(updateTimer);
    }, 1000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
