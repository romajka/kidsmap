(() => {
  'use strict';
  const root = document.querySelector('[data-pc-offerings]');
  const input = root?.querySelector('[name="nested_pricing"]');
  if (!root || !input) return;
  const ui = JSON.parse(document.getElementById('pw-copy').textContent);
  const choices = JSON.parse(document.getElementById('pc-offering-choices').textContent);
  const language = ['az', 'ru', 'en'].includes(document.documentElement.lang) ? document.documentElement.lang : 'az';
  const list = root.querySelector('[data-pc-activity-list]');
  const empty = () => ({pricing_schema_version: 2, activities: []});
  const parse = () => { try { const value = JSON.parse(input.value || 'null'); return value?.pricing_schema_version === 2 && Array.isArray(value.activities) ? value : empty(); } catch { return empty(); } };
  let tree = parse();
  const newPlan = () => ({product_type: 'lesson', price_kind: 'exact', charge_role: 'primary', billing_mode: 'one_time', currency: 'AZN', price: '', title_az: '', is_active: true});
  const newGroup = () => ({id: null, name_az: '', age_from: null, age_to: null, lesson_format: 'group', language: '', schedule_text: '', pricing_plans: [newPlan()]});
  const newActivity = () => ({id: null, program_id: null, name_az: '', description_az: '', supplement_az: '', groups: [newGroup()]});
  let sequence = 0;
  function node(tag, className, text) { const element = document.createElement(tag); if (className) element.className = className; if (text) element.textContent = text; return element; }
  function sync() { input.value = tree.activities.length ? JSON.stringify(tree) : ''; input.dispatchEvent(new Event('input', {bubbles: true})); root.dispatchEvent(new CustomEvent('km:offerings-change', {bubbles: true})); }
  function field(parent, object, key, label, kind = 'text', config = {}) {
    const wrap = node('label', 'pc-offering-field'); wrap.append(node('span', '', label));
    const control = node(kind === 'textarea' ? 'textarea' : kind === 'select' ? 'select' : 'input');
    if (kind !== 'textarea' && kind !== 'select') control.type = kind === 'number' ? 'number' : kind === 'checkbox' ? 'checkbox' : 'text';
    if (kind === 'select') for (const [value, title] of config.choices || []) { const option = node('option', '', title); option.value = value; control.append(option); }
    if (kind === 'number') { control.min = '0'; if (key === 'price') control.step = '0.01'; else control.step = '1'; }
    if (kind === 'checkbox') control.checked = Boolean(object[key]); else control.value = object[key] ?? '';
    control.id = `pc-offer-${++sequence}`; control.setAttribute('aria-label', label);
    const update = () => { object[key] = kind === 'checkbox' ? control.checked : kind === 'number' || key === 'program_id' || key === 'subcategory_id' ? (control.value === '' ? null : Number(control.value)) : key === 'category_id' ? (control.value || null) : control.value; sync(); };
    control.addEventListener(kind === 'checkbox' || kind === 'select' ? 'change' : 'input', update);
    wrap.append(control); parent.append(wrap); return control;
  }
  function button(parent, title, action) { const item = node('button', 'pw-add', title); item.type = 'button'; item.addEventListener('click', action); parent.append(item); return item; }
  function translations(parent, object, prefix, includeDescription = false) {
    const details = node('details', 'pc-offering-translations'); const summary = node('summary', '', ui.translations); details.append(summary);
    const grid = node('div', 'pc-offering-grid');
    for (const lang of ['ru', 'en']) {
      field(grid, object, `${prefix}_${lang}`, `${(prefix === 'title' ? ui.plan_title : ui.activity_name).replace('(AZ)', `(${lang.toUpperCase()})`)}`);
      if (includeDescription) field(grid, object, `description_${lang}`, ui.activity_description.replace('(AZ)', `(${lang.toUpperCase()})`), 'textarea');
    }
    details.append(grid); parent.append(details);
  }
  function taxonomy(parent, activity) {
    const category = field(parent, activity, 'category_id', ui.category, 'select', {choices: [['', '—'], ...(choices.categories || []).map(item => [String(item.id), item.label])]});
    category.dataset.activityCategory = '';
    const subcategory = field(parent, activity, 'subcategory_id', ui.subcategory, 'select');
    subcategory.dataset.activitySubcategory = '';
    const status = node('p', 'pc-note'); status.dataset.taxonomyStatus = ''; status.setAttribute('role', 'status'); parent.append(status);
    function rebuild(announce = false) {
      const previous = activity.subcategory_id;
      const available = (choices.subcategories || []).filter(item => String(item.category_id) === String(activity.category_id || ''));
      subcategory.replaceChildren();
      for (const item of [{id:'', label:'—'}, ...available]) {const option = node('option', '', item.label); option.value = String(item.id); subcategory.append(option);}
      if (previous != null && !available.some(item => Number(item.id) === Number(previous))) {
        activity.subcategory_id = null;
        if (announce) status.textContent = ui.taxonomy_reset;
      }
      subcategory.value = activity.subcategory_id ?? '';
      subcategory.disabled = !activity.category_id || !available.length;
    }
    category.addEventListener('change', () => {status.textContent = ''; rebuild(true); sync();});
    rebuild();
    if (choices.place_taxonomy) {
      const copy = button(parent, ui.copy_place_taxonomy, () => {
        const form = root.closest('form');
        const currentCategory = form?.querySelector('select[name="category"]');
        const currentSubcategory = form?.querySelector('select[name="subcategory"]');
        activity.category_id = currentCategory ? currentCategory.value || null : choices.place_taxonomy.category_id || null;
        activity.subcategory_id = currentSubcategory ? Number(currentSubcategory.value) || null : choices.place_taxonomy.subcategory_id || null;
        category.value = activity.category_id || ''; rebuild(); sync();
      });
      copy.dataset.copyPlaceTaxonomy = '';
    }
  }
  function render() {
    list.replaceChildren(); sequence = 0;
    tree.activities.forEach((activity, activityIndex) => {
      const card = node('section', 'pc-activity-card');
      const heading = node('h4', '', `${ui.add_activity} ${activityIndex + 1}`); card.append(heading);
      const basic = node('div', 'pc-offering-grid');
      const programs = choices.programs || [];
      field(basic, activity, 'program_id', ui.shared_program, 'select', {choices: [['', ui.local_activity], ...programs.map(p => [String(p.id), p[`name_${language}`] || p.name_az])]})
        .addEventListener('change', render);
      const selected = programs.find(p => p.id === activity.program_id);
      if (selected) {
        const preview = node('p', 'pc-note', `${selected[`name_${language}`] || selected.name_az} · ${selected[`description_${language}`] || selected.description_az || ''}`);
        basic.append(preview);
        field(basic, activity, 'supplement_az', ui.local_supplement, 'textarea');
      } else {
        field(basic, activity, 'name_az', ui.activity_name);
        field(basic, activity, 'description_az', ui.activity_description, 'textarea');
        taxonomy(basic, activity);
      }
      card.append(basic);
      if (!selected) translations(card, activity, 'name', true);
      activity.groups.forEach((group, groupIndex) => {
        const block = node('div', 'pc-group-card'); block.append(node('h5', '', `${ui.add_group} ${groupIndex + 1}`));
        const grid = node('div', 'pc-offering-grid');
        field(grid, group, 'name_az', ui.group_name);
        field(grid, group, 'age_from', ui.group_age_from, 'number');
        field(grid, group, 'age_to', ui.group_age_to, 'number');
        field(grid, group, 'language', ui.group_language);
        field(grid, group, 'schedule_text', ui.group_schedule, 'textarea');
        field(grid, group, 'lesson_format', ui.group_format, 'select', {choices: choices.lesson_formats});
        field(grid, group, 'teachers_text', ui.group_teachers, 'textarea');
        field(grid, group, 'conditions_az', ui.group_conditions, 'textarea');
        block.append(grid); translations(block, group, 'name');
        group.pricing_plans.forEach((plan, planIndex) => {
          const planBlock = node('div', 'pc-plan-card'); planBlock.append(node('h6', '', `${ui.add_plan} ${planIndex + 1}`));
          const planGrid = node('div', 'pc-offering-grid');
          field(planGrid, plan, 'title_az', ui.plan_title);
          field(planGrid, plan, 'product_type', ui.plan_type, 'select', {choices: choices.product_types});
          field(planGrid, plan, 'price_kind', ui.plan_price_kind, 'select', {choices: choices.price_kinds});
          field(planGrid, plan, 'price', ui.plan_price, 'number');
          planBlock.append(planGrid);
          const advanced = node('details', 'pc-offering-translations'); advanced.append(node('summary', '', ui.plan_advanced));
          const extra = node('div', 'pc-offering-grid');
          field(extra, plan, 'price_min', ui.plan_price_min, 'number');
          field(extra, plan, 'price_max', ui.plan_price_max, 'number');
          field(extra, plan, 'currency', ui.plan_currency);
          field(extra, plan, 'charge_role', ui.plan_role, 'select', {choices: choices.charge_roles});
          field(extra, plan, 'billing_mode', ui.plan_billing, 'select', {choices: choices.billing_modes});
          field(extra, plan, 'billing_interval', ui.plan_interval, 'select', {choices: [['', '—'], ...choices.billing_intervals]});
          field(extra, plan, 'age_from', ui.group_age_from, 'number');
          field(extra, plan, 'age_to', ui.group_age_to, 'number');
          field(extra, plan, 'is_trial', ui.plan_trial, 'checkbox');
          field(extra, plan, 'is_required', ui.plan_required, 'checkbox');
          advanced.append(extra); planBlock.append(advanced); translations(planBlock, plan, 'title');
          button(planBlock, ui.remove_plan, () => { group.pricing_plans.splice(planIndex, 1); sync(); render(); });
          block.append(planBlock);
        });
        button(block, ui.add_plan, () => { group.pricing_plans.push(newPlan()); sync(); render(); });
        button(block, ui.remove_group, () => { activity.groups.splice(groupIndex, 1); sync(); render(); });
        card.append(block);
      });
      button(card, ui.add_group, () => { activity.groups.push(newGroup()); sync(); render(); });
      button(card, ui.remove_activity, () => { tree.activities.splice(activityIndex, 1); sync(); render(); });
      list.append(card);
    });
  }
  root.querySelector('[data-pc-add-activity]').addEventListener('click', () => { tree.activities.push(newActivity()); sync(); render(); list.lastElementChild?.querySelector('input')?.focus(); });
  input.addEventListener('change', () => { tree = parse(); render(); });
  render();
})();
