"""Bounded approved patch; each replacement must match the incoming source."""
from pathlib import Path
R=Path(__file__).resolve().parents[3]
p=R/'src/catalog/services/pricing_plans.py';s=p.read_text()
s=s.replace('def normalize_pricing_plans(value, *, strict=True, allow_verified=False):','''def _error_with_path(error, field_path):
    """Retain translated validation errors and add a separate UI address."""
    if getattr(error, 'error_dict', None):
        return ValidationError([
            _error_with_path(item, [*field_path, key])
            for key, errors in error.error_dict.items() for item in errors
        ])
    if len(error.error_list) != 1 or error.error_list[0] is not error:
        return ValidationError([_error_with_path(item, field_path) for item in error.error_list])
    params = dict(error.params or {})
    params['field_path'] = list(field_path)
    return ValidationError(error.message, code=error.code, params=params)


def normalize_pricing_plans(value, *, strict=True, allow_verified=False, error_path=()):''')
s=s.replace('    for index, raw in enumerate(value):\n        try:','    for index, raw in enumerate(value):\n        plan_path = [*error_path, "pricing_plans", index]\n        conversion_field = None\n        try:',1)
s=s.replace('            for price_field in ("price", "price_min", "price_max"):\n','            for price_field in ("price", "price_min", "price_max"):\n                conversion_field = price_field\n',1)
s=s.replace('                if values.get(int_field) not in (None, ""):\n','                conversion_field = int_field\n                if values.get(int_field) not in (None, ""):\n',1)
s=s.replace('                if getattr(exc, "error_dict", None):\n                    field_name', '                field_name = None\n                if getattr(exc, "error_dict", None):\n                    field_name',1)
s=s.replace('params={"number": index + 1, "error": message},','params={"number": index + 1, "error": message, "field_path": plan_path + ([field_name] if field_name else [])},',1)
s=s.replace('params={"number": index + 1, "error": str(exc)},','params={"number": index + 1, "error": str(exc), "field_path": plan_path + ([conversion_field] if conversion_field else [])},',1)
s=s.replace('def _editor_values(model, data, names, *, existing=None):','def _editor_values(model, data, names, *, existing=None, error_path=None):')
a='''        value = field.to_python(value)
        field.validate(value, existing)
        field.run_validators(value)'''
b='''        try:
            value = field.to_python(value)
            field.validate(value, existing)
            field.run_validators(value)
        except ValidationError as exc:
            if error_path is None:
                raise
            raise _error_with_path(exc, [*error_path, name]) from exc'''
assert a in s;s=s.replace(a,b,1)
start=s.index('def validate_nested_pricing(');end=s.index('\n\n@transaction.atomic\ndef replace_nested_pricing',start);n=s[start:end]
n=n.replace("for activity_data in payload['activities']:","for activity_index, activity_data in enumerate(payload['activities']):\n        activity_path = ['activities', activity_index]")
n=n.replace("for group_data in activity_data['groups']:","for group_index, group_data in enumerate(activity_data['groups']):\n            group_path = [*activity_path, 'groups', group_index]")
n=n.replace('ACTIVITY_EDITOR_FIELDS, existing=activity)','ACTIVITY_EDITOR_FIELDS, existing=activity, error_path=activity_path)')
n=n.replace('GROUP_EDITOR_FIELDS, existing=group)','GROUP_EDITOR_FIELDS, existing=group, error_path=group_path)')
n=n.replace('        validate_taxonomy(category_id,subcategory_id)','''        try:
            validate_taxonomy(category_id,subcategory_id)
        except ValidationError as exc:
            raise _error_with_path(exc, activity_path) from exc''')
n=n.replace("normalize_pricing_plans(group_data['pricing_plans'], allow_verified=allow_verified)","normalize_pricing_plans(group_data['pricing_plans'], allow_verified=allow_verified, error_path=group_path)")
n=n.replace('                validate_target_plan_ids(group, plans)','''                try:
                    validate_target_plan_ids(group, plans)
                except ValidationError as exc:
                    raise _error_with_path(exc, group_path) from exc''')
n=n.replace('            for plan in plans:','            for plan_index, plan in enumerate(plans):\n                plan_path = [*group_path, "pricing_plans", plan_index]')
n=n.replace("raise ValidationError(_('Возраст тарифа не пересекается с возрастом группы.'))", "raise ValidationError(_('Возраст тарифа не пересекается с возрастом группы.'), params={'field_path': [*plan_path, 'age_from' if age_to is not None and plan.get('age_from') is not None and plan['age_from'] > age_to else 'age_to']})")
n=n.replace("                row.full_clean(exclude=('offering_group', 'place'))", "                try:\n                    row.full_clean(exclude=('offering_group', 'place'))\n                except ValidationError as exc:\n                    raise _error_with_path(exc, plan_path) from exc")
paths={
'Неверная структура занятия.':'activity_path',
'Занятие не принадлежит карточке или повторяется.':'activity_path',
'Занятие не принадлежит карточке.':'activity_path',
'Общая программа недоступна этому филиалу.':"[*activity_path, 'program_id']",
'Одобренная программа недоступна. Обновите страницу.':"[*activity_path, 'program_id']",
'Укажите название занятия на AZ.':"[*activity_path, 'name_az']",
'Неверная структура группы тарифов.':'group_path',
'Группа тарифов не принадлежит карточке или повторяется.':'group_path',
'Группа тарифов не принадлежит карточке.':'group_path',
'Укажите название группы на AZ.':"[*group_path, 'name_az']",
'Возраст группы указан неверно.':"[*group_path, 'age_to']",
'Новый тариф не может ссылаться на чужой ID.':'group_path',
}
for message,path in paths.items():
 a=f"raise ValidationError(_('{message}'))";b=f"raise ValidationError(_('{message}'), params={{'field_path': {path}}})";assert a in n,message;n=n.replace(a,b)
s=s[:start]+n+s[end:];p.write_text(s)
p=R/'src/catalog/photo_views.py';s=p.read_text();a="            payload = {'ok': False, 'errors': errors}\n";assert a in s;s=s.replace(a,a+'''            if result.form is not None:
                payload['error_targets'] = {
                    name: [(error.params or {}).get('field_path') for error in values]
                    for name, values in result.form.errors.as_data().items()
                }
''');p.write_text(s)
p=R/'static/js/permanent_place_photos.js';s=p.read_text();s=s.replace('errors:body.errors, conflict:body.conflict','errors:body.errors, error_targets:body.error_targets, conflict:body.conflict').replace('errors:result.errors, conflict:result.conflict','errors:result.errors, error_targets:result.error_targets, conflict:result.conflict').replace('errors:error.errors || {gallery_images:[copy.saveFailed]}, conflict:error.conflict','errors:error.errors || {gallery_images:[copy.saveFailed]}, error_targets:error.error_targets, conflict:error.conflict');p.write_text(s)
p=R/'static/js/owner_place_continuous.js';s=p.read_text();start=s.index('  function fieldTarget(');end=s.index('\n  function goTo(',start)
s=s[:start]+'''  function fieldTarget(name, path = null) {
    if (name === 'nested_pricing') {
      const root = form.querySelector('[data-pc-offerings]');
      const fallback = () => root?.querySelector('input,select,textarea') || form.querySelector('[data-pc-add-activity]');
      if (!Array.isArray(path)) return fallback();
      const keys = new Set(['program_id', 'category_id', 'subcategory_id', 'name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en', 'supplement_az', 'age_from', 'age_to', 'language', 'schedule_text', 'lesson_format', 'teachers_text', 'conditions_az', 'title_az', 'title_ru', 'title_en', 'product_type', 'price_kind', 'price', 'price_min', 'price_max', 'currency', 'charge_role', 'billing_mode', 'billing_interval', 'billing_interval_count', 'billing_cycles', 'quantity', 'quantity_unit', 'is_trial', 'is_required']);
      let scope = root, offset = 0;
      for (const [segment, attribute] of [['activities', 'activity'], ['groups', 'group'], ['pricing_plans', 'plan']]) {
        if (path[offset] !== segment) break;
        const index = path[offset + 1];
        if (!Number.isSafeInteger(index) || index < 0) return fallback();
        scope = scope?.querySelector(`[data-${attribute}-index="${index}"]`);
        if (!scope) return fallback();
        offset += 2;
      }
      if (offset === 0 || (path.length !== offset && path.length !== offset + 1)) return fallback();
      const key = path[offset];
      if (key !== undefined && !keys.has(key)) return scope.querySelector(':scope > summary') || fallback();
      const input = key === undefined ? scope.querySelector(':scope > summary') : scope.querySelector(`[data-offering-key="${key}"]`);
      // A billing input can intentionally be hidden after changing billing mode.
      return (input?.closest('[hidden]') ? scope.querySelector('[data-offering-key="billing_mode"]') : input) || scope.querySelector(':scope > summary') || fallback();
    }
    const input = [...form.querySelectorAll('[name]')].find(node => node.name === name);
    if (input?.type === 'hidden') return input.closest('[data-pw-field]')?.parentElement?.querySelector('input:not([type=hidden]),select,textarea,button') || input;
    return input;
  }'''+s[end:]
start=s.index('  function showErrors(');end=s.index('\n  for (const wrapper',start)
s=s[:start]+'''  const summaryAttributes = new Map();
  function showErrors(errors, targets = {}) {
    for (const [input, attributes] of summaryAttributes) {
      for (const [name, value] of Object.entries(attributes)) {
        if (value === null) input.removeAttribute(name); else input.setAttribute(name, value);
      }
    }
    summaryAttributes.clear();
    const box = form.querySelector('[data-pc-errors]'); box.replaceChildren();
    if (!Object.keys(errors).length) { box.hidden = true; return; }
    box.hidden = false; const heading = document.createElement('strong'); heading.textContent = ui.errors_title; box.append(heading);
    const list = document.createElement('ul');
    Object.entries(errors).forEach(([name, messages]) => {
      (Array.isArray(messages) ? messages : [messages]).forEach((text, index) => {
        const input = fieldTarget(name, targets?.[name]?.[index]), wrapper = input?.closest('[data-pw-field]');
        const item = document.createElement('li'), button = document.createElement('button');
        let message = String(text);
        if (message.includes('Candidate version conflict')) message = ui.server_conflict;
        const label = name === 'nested_pricing' ? ui.section_offer : wrapper?.querySelector('label')?.textContent?.trim() || input?.getAttribute('aria-label') || ui.errors_title;
        button.type = 'button'; button.textContent = `${label}: ${message}`;
        button.addEventListener('click', () => goTo(input));
        item.append(button); list.append(item);
        if (input) {
          if (!summaryAttributes.has(input)) summaryAttributes.set(input, {'aria-invalid': input.getAttribute('aria-invalid'), 'aria-describedby': input.getAttribute('aria-describedby')});
          input.setAttribute('aria-invalid','true');
          item.id = `pc-error-${list.children.length}`;
          input.setAttribute('aria-describedby', `${input.getAttribute('aria-describedby') || ''} ${item.id}`.trim());
        }
      });
    });
    box.append(list); box.focus({preventScroll:true}); box.scrollIntoView({block:'center'});
  }'''+s[end:]
s=s.replace('showErrors(result.errors || {});','showErrors(result.errors || {}, result.error_targets || {});');p.write_text(s)
print('Approved four-file patch applied')
