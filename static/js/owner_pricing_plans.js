(function () {
  const editor = document.querySelector("[data-tariff-editor]");
  if (!editor) return;
  const input = editor.querySelector("[data-tariff-input]");
  const list = editor.querySelector("[data-tariff-list]");
  const add = editor.querySelector("[data-tariff-add]");
  if (!input || !list || !add) return;

  let plans = [];
  try { plans = JSON.parse(input.value || "[]"); } catch (error) { plans = []; }
  if (!Array.isArray(plans)) plans = [];

  const labels = {
    format: editor.dataset.formatLabel || "Format",
    group: editor.dataset.groupLabel || "Group",
    individual: editor.dataset.individualLabel || "Individual",
    payment: editor.dataset.paymentLabel || "Payment",
    perLesson: editor.dataset.perLessonLabel || "Per lesson",
    perMonth: editor.dataset.perMonthLabel || "Per month",
    package: editor.dataset.packageLabel || "Package",
    week: editor.dataset.weekLabel || "Sessions/week",
    month: editor.dataset.monthLabel || "Sessions/month",
    packageSessions: editor.dataset.packageSessionsLabel || "Package sessions",
    price: editor.dataset.priceLabel || "Price",
    titleAz: editor.dataset.titleAzLabel || "Plan title (AZ)",
    titleRu: editor.dataset.titleRuLabel || "Plan title (RU)",
    titleEn: editor.dataset.titleEnLabel || "Plan title (EN)",
    active: editor.dataset.activeLabel || "Active",
    remove: editor.dataset.removeLabel || "Remove",
    up: editor.dataset.upLabel || "Move up",
    down: editor.dataset.downLabel || "Move down",
    addTranslation: editor.dataset.addTranslationLabel || "Добавить перевод (RU, EN)",
    egSessionsWeek: editor.dataset.egSessionsWeek || "например, 3",
    egSessionsMonth: editor.dataset.egSessionsMonth || "например, 12",
    egPackageSessions: editor.dataset.egPackageSessions || "например, 10",
    egPrice: editor.dataset.egPrice || "например, 120",
  };

  const fields = [
    ["title_az", labels.titleAz, "text", null, true],
    ["title_ru", labels.titleRu, "text", null, false],
    ["title_en", labels.titleEn, "text", null, false],
    ["lesson_format", labels.format, "select", [["group", labels.group], ["individual", labels.individual]], true],
    ["payment_type", labels.payment, "select", [["per_lesson", labels.perLesson], ["per_month", labels.perMonth], ["package", labels.package]], true],
    ["price", labels.price, "number", null, true],
    ["sessions_per_week", labels.week, "number", null, false],
    ["sessions_per_month", labels.month, "number", null, false],
    ["package_sessions", labels.packageSessions, "number", null, false],
  ];

  function sync() {
    plans.forEach((plan, index) => { plan.sort_order = index; });
    const contentKeys = ["lesson_format", "sessions_per_week", "sessions_per_month", "payment_type", "package_sessions", "price", "title_az", "title_ru", "title_en", "name", "frequency"];
    input.value = JSON.stringify(plans.filter((plan) => contentKeys.some((key) => plan[key] !== "" && plan[key] !== null && plan[key] !== undefined)));
  }

  function addField(row, plan, key, label, type, options, required) {
    const wrapper = document.createElement("label");
    wrapper.className = "owner-tariff-field owner-tariff-field--" + key;
    
    // Hide RU and EN translation fields by default if they are empty
    if ((key === "title_ru" || key === "title_en") && !plan[key] && !plan._show_translations) {
      wrapper.classList.add("owner-tariff-field--hidden");
    }

    const labelHtml = required ? label + ' <span style="color: #ef4444; font-weight: bold;">*</span>' : label;
    wrapper.innerHTML = "<span>" + labelHtml + "</span>";
    
    let field;
    if (type === "select") {
      field = document.createElement("select");
      field.innerHTML = '<option value=""></option>' + options.map((item) => '<option value="' + item[0] + '">' + item[1] + '</option>').join("");
    } else {
      field = document.createElement("input");
      field.type = type;
      if (type === "number") { 
        field.min = "1"; 
        field.step = key === "price" ? "0.01" : "1"; 
      }
      const placeholders = {
        sessions_per_week: labels.egSessionsWeek,
        sessions_per_month: labels.egSessionsMonth,
        package_sessions: labels.egPackageSessions,
        price: labels.egPrice,
        title_az: "məsələn, Aylıq abunə (12 dərs)",
        title_ru: "например, Абонемент на месяц (12 занятий)",
        title_en: "e.g., Monthly subscription (12 sessions)",
      };
      if (placeholders[key]) {
        field.placeholder = placeholders[key];
      }
    }
    field.className = "field";
    field.value = plan[key] == null ? "" : plan[key];
    field.dataset.tariffKey = key;
    field.addEventListener("input", () => { plan[key] = field.value; sync(); });
    field.addEventListener("change", () => { plan[key] = field.value; sync(); render(); });
    wrapper.appendChild(field);
    row.appendChild(wrapper);
  }
 
  function render() {
    list.innerHTML = "";
    plans.forEach((plan, index) => {
      const row = document.createElement("div");
      const cleanType = (plan.payment_type || "empty").replace("_", "-");
      const hasTranslations = plan.title_ru || plan.title_en || plan._show_translations;
      row.className = "owner-tariff-row payment-type--" + cleanType + (hasTranslations ? "" : " translations--hidden");
      
      fields.forEach((field) => {
        addField(row, plan, field[0], field[1], field[2], field[3], field[4]);
        
        // Render translations toggle link directly after default AZ title
        if (field[0] === "title_az" && !hasTranslations) {
          const toggleWrapper = document.createElement("div");
          toggleWrapper.className = "owner-tariff-translation-toggle";
          
          const toggleBtn = document.createElement("button");
          toggleBtn.type = "button";
          toggleBtn.className = "km-btn-link";
          toggleBtn.innerHTML = "<i class='fas fa-language'></i> + " + labels.addTranslation;
          toggleBtn.addEventListener("click", () => {
            plan._show_translations = true;
            render();
          });
          
          toggleWrapper.appendChild(toggleBtn);
          row.appendChild(toggleWrapper);
        }
      });
      
      const footer = document.createElement("div");
      footer.className = "owner-tariff-footer";

      const active = document.createElement("label");
      active.className = "owner-tariff-active";
      active.innerHTML = '<input type="checkbox" class="field-check"> <span>' + labels.active + '</span>';
      const checkbox = active.querySelector("input");
      checkbox.checked = plan.is_active !== false;
      checkbox.addEventListener("change", () => { plan.is_active = checkbox.checked; sync(); });
      footer.appendChild(active);

      const actions = document.createElement("div");
      actions.className = "owner-tariff-actions";
      [["<i class='fas fa-chevron-up'></i>", labels.up, -1], ["<i class='fas fa-chevron-down'></i>", labels.down, 1]].forEach((item) => {
        const button = document.createElement("button");
        button.type = "button"; 
        button.className = "owner-tariff-move"; 
        button.title = item[1]; 
        button.innerHTML = item[0];
        button.disabled = index + item[2] < 0 || index + item[2] >= plans.length;
        button.addEventListener("click", () => { const target = index + item[2]; [plans[index], plans[target]] = [plans[target], plans[index]]; render(); sync(); });
        actions.appendChild(button);
      });
      
      const remove = document.createElement("button");
      remove.type = "button"; 
      remove.className = "owner-tariff-remove"; 
      remove.title = labels.remove; 
      remove.innerHTML = "<i class='fas fa-trash-alt'></i>";
      remove.addEventListener("click", () => { plans.splice(index, 1); render(); sync(); });
      actions.appendChild(remove);
      
      footer.appendChild(actions);
      row.appendChild(footer);
      list.appendChild(row);
    });
    sync();
  }

  add.addEventListener("click", () => { if (plans.length < 12) { plans.push({ lesson_format: "", payment_type: "", price: "", currency: "AZN", is_active: true }); render(); } });
  render();
})();
