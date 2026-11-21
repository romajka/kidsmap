(function () {
  "use strict";

  // Optional subscription/package rows for a specialist's lesson price.
  // Server validation is the source of truth; this only keeps rows tidy and
  // shows the per-lesson price, compared with the single lesson price.
  function initPackages(editor) {
    const container = editor.querySelector("[data-package-rows]");
    const template = editor.querySelector("template");
    const add = editor.querySelector("[data-package-add]");
    const form = editor.closest("form");
    const base = form && form.querySelector('[name="lesson_price"]');
    const limit = parseInt(editor.dataset.limit, 10) || 10;
    const locale = document.documentElement.lang || undefined;
    const money = new Intl.NumberFormat(locale, {minimumFractionDigits: 0, maximumFractionDigits: 2});
    const text = Object.assign({
      unitLabel: "", rowTitle: "", saving: "-{value}%", same: "", pricier: "",
    }, editor.dataset);

    function rows() {
      return Array.from(container.querySelectorAll("[data-package-row]"));
    }

    function formatMoney(value) {
      // Show gapiks only when there are any: 25 ₼, 27,50 ₼.
      const rounded = Math.round(value * 100) / 100;
      return Number.isInteger(rounded)
        ? money.format(rounded)
        : new Intl.NumberFormat(locale, {minimumFractionDigits: 2, maximumFractionDigits: 2}).format(rounded);
    }

    function baseValue() {
      if (!base || base.value === "" || !base.validity.valid) return null;
      const value = base.valueAsNumber;
      return Number.isFinite(value) && value > 0 ? value : null;
    }

    function summary(row, unit) {
      const out = row.querySelector("[data-package-unit]");
      out.className = "km-package-summary";
      out.textContent = "";
      if (unit === null) return;
      const strong = document.createElement("strong");
      strong.textContent = "= " + formatMoney(unit) + " " + text.unitLabel;
      out.appendChild(strong);
      const single = baseValue();
      if (single === null) return;
      const cents = Math.round(unit * 100) - Math.round(single * 100);
      let note;
      if (cents < 0) {
        const percent = Math.round((single - unit) * 100 / single);
        if (percent >= 1) {
          note = text.saving.replace("{value}", percent);
          out.classList.add("is-saving");
        }
      } else if (cents === 0) {
        note = text.same;
      } else {
        note = text.pricier;
        out.classList.add("is-pricier");
      }
      if (note) {
        const span = document.createElement("span");
        span.textContent = note;
        out.appendChild(span);
      }
    }

    function syncRow(row, index, all) {
      const period = row.querySelector('[name="package_period"]');
      const amount = row.querySelector('[name="package_amount"]');
      const sessions = row.querySelector('[name="package_sessions"]');
      const fields = [period, amount, sessions];
      const started = fields.some(field => field.value !== "" || field.validity.badInput);
      row.toggleAttribute("data-package-started", started);
      fields.forEach(field => { field.required = started; });
      const complete = started && fields.every(field => field.value !== "" && field.validity.valid);

      const title = row.querySelector("[data-package-title]");
      if (title && text.rowTitle) title.textContent = text.rowTitle.replace("{n}", index + 1);
      const hint = row.querySelector("[data-package-hint]");
      if (hint) hint.hidden = !started || complete;

      const label = row.querySelector("[data-sessions-label]");
      if (label) {
        if (!label.dataset.labelDefault) label.dataset.labelDefault = label.textContent.trim();
        label.textContent = period.value === "month" ? label.dataset.labelMonth
          : period.value === "package" ? label.dataset.labelPackage : label.dataset.labelDefault;
      }

      summary(row, complete ? amount.valueAsNumber / sessions.valueAsNumber : null);
      // A single untouched row is the empty starting point; nothing to remove.
      row.querySelector("[data-package-remove]").hidden = !started && all.length === 1;
    }

    function refresh() {
      const all = rows();
      all.forEach((row, index) => syncRow(row, index, all));
      const free = all.some(row => !row.hasAttribute("data-package-started"));
      // "Add another" only makes sense once every visible row is in use.
      add.hidden = free || all.length >= limit;
    }

    function appendRow() {
      const row = template.content.firstElementChild.cloneNode(true);
      container.appendChild(row);
      return row;
    }

    editor.setRecoveryRowCount = function (count) {
      const size = Math.min(limit, Math.max(1, count));
      while (container.children.length < size) appendRow();
      while (container.children.length > size) container.lastElementChild.remove();
      refresh();
    };

    add.addEventListener("click", function () {
      let row = container.querySelector("[data-package-row]:not([data-package-started])");
      if (!row) {
        if (rows().length >= limit) return;
        row = appendRow();
        editor.dispatchEvent(new Event("change", {bubbles: true}));
      }
      refresh();
      // The styled dropdown (if any) replaces the native select for focus.
      const target = row.querySelector(".kmfx-select__button") || row.querySelector("select");
      target.focus();
    });

    container.addEventListener("click", function (event) {
      const remove = event.target.closest("[data-package-remove]");
      if (!remove) return;
      const row = remove.closest("[data-package-row]");
      const next = row.nextElementSibling || row.previousElementSibling;
      row.remove();
      if (!next) appendRow();
      editor.dispatchEvent(new Event("change", {bubbles: true}));
      refresh();
      const target = next || container.querySelector("[data-package-row]");
      const focus = target && (target.querySelector(".kmfx-select__button") || target.querySelector("select"));
      (focus || add).focus();
    });

    function changed(event) {
      if (event.target === form || event.target === base || editor.contains(event.target)) refresh();
    }
    form.addEventListener("input", changed, true);
    form.addEventListener("change", changed, true);
    form.addEventListener("reset", function () { window.setTimeout(refresh, 0); });
    refresh();
  }

  document.querySelectorAll("[data-pricing-packages]").forEach(initPackages);
})();
