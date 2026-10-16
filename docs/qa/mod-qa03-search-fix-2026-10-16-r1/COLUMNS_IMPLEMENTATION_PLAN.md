# Колонки очередей MOD-QA-03 — Implementation Plan

**Статус: отдельный scope, требуется одобрение. Код приложения для колонок ещё не менялся.**

**Goal:** галочки в меню «Колонки» скрывают и возвращают реальные колонки текущего списка мест, событий или специалистов.

**Architecture:** строить варианты из уже разрешённого `cl.list_display`; подписи брать из тех же admin metadata, что и заголовки таблицы. JS связывает controls с фактическими ячейками по индексу из этого же разрешённого list_display, сохраняет настройки отдельно для каждой модели и оставляет колонку названия видимой.

**Tech Stack:** текущие Django6.0.2 templates/admin, существующий JavaScript без новых зависимостей.

**Spec:** пользовательский staged PLAN → approval → implementation; исторический MOD-QA-03, свежий `native-columns-recheck.js.result.json`. Исполнитель работает в этом чате; новых агентов и коммитов этот план не разрешает. Применять доступные TDD/systematic-debugging/verification-before-completion/kidsmap-ui-design skills. Пользовательский запрет commit/push/deploy и отдельное одобрение scope выше generic skill-шаблонов.

## Причина и подтверждение

Общий `km_changelist_search_panel.html:212–238` всегда выводит `column-col_place`, `column-col_location`, `column-col_state`, `column-col_marks`, `column-col_updated`. Они соответствуют основной таблице Place. В Event реальные поля называются `display_name`, `category`, `start_datetime`, `end_datetime`, `owner`, `lifecycle_status_display`, `updated_at`, `row_actions`. В Specialist — `profile_column`, `directions_column`, `owner`, `format_badge`, `status_badge`, разрешённый `documents_count`, `rating_column`, `updated_at`.

JS `kidsmap_place_changelist.js:847` ищет заголовок по указанному классу и тихо ничего не делает, если его нет. Дополнительно свежий DOM показывает: Jazzmin не выводит `column-*` классы у Event/Specialist th вообще (`header_class` в vendor change_list_results.html). Поэтому одной замены имён недостаточно. Минимальный план передаёт фактический индекс из полного разрешённого `cl.list_display` в общий JS; vendor и таблицы не переписываются. Свежий read-only браузерный recheck: RU1024, нативно снять/поставить «Обновлено / Создано», сравнить реальный заголовок; Place контроль, Event/Specialist воспроизведение. JSON и три `screenshots/columns-red-*.png` — доказательство, не HTML200/source-only приёмка.

Подтверждённый ID: **MOD-QA-03 остаётся OPEN**. Новый исторический ID не вводится. Search/SORT/CSS/menu результаты сохраняются. Неверные targets в корзине Place следуют той же причине жёсткого списка; включить её в целевую проверку фактического `list_display`.

## Точные файлы — четыре

1. `src/catalog/templatetags/admin_dashboard_tags.py`: добавить только `km_column_options(cl)` и импорты `label_for_field`, `capfirst`.
2. `src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html`: заменить пять жёстко заданных checkbox на цикл; добавить `data-column-index` к controls и ключ настроек к существующему `#km-columns-menu`.
3. `static/admin/js/kidsmap_place_changelist.js`: только блок Column Visibility Toggler. Предыдущие row-menu/focus/resize/search/sort обработчики не переписывать.
4. NEW `src/catalog/testcases/test_admin_queue_columns.py`: rendered metadata/labels/ACL regression. Existing assertions не менять.

Отчёт, scripts/JSON/PNG — в новом уникальном QA run. CSS/PO/models/migrations/запросы/ACL/actions не входят в patch. Приватная колонка появляется в меню только когда уже разрешена текущим `cl.list_display`.

## Один цикл исправления

- [ ] **1. Снять новый snapshot и RED.** Сохранить HEAD/branch/dirty/active_run, hashes четырёх paths/чужих файлов/стендов. Собственный DJANGO_TESTING=1 PostgreSQL/cache/media/private-media/email, fictional fixtures, внешний доступ заблокирован. Текущие RU/AZ/EN PO собрать отдельным build_isolated_locales.py, manifest проверить до setup, единственный LOCALE_PATHS, подтвердить source процесса. Новый тест разбирает фактические `th` и `input[data-toggle-col]` через HTMLParser и проверяет, что индекс каждого control соответствует фактическому заголовку и field-ячейке, identity disabled, лишних/приватных controls нет. RED ожидается на Event/Specialist и Place trash по targets.

Минимальные реальные утверждения в новом тесте (парсер хранит список controls с `target`, `index`, `disabled`, `label`; заголовки — упорядоченный список текста; first_row_cell_classes — классы реальных ячеек первой строки):

```python
for control in controls:
    self.assertLess(control['index'], len(headers))
    self.assertEqual(control['label'], headers[control['index']])
    self.assertIn(control['target'].replace('column-', 'field-'),
                  first_row_cell_classes[control['index']])
self.assertTrue(controls[0]['disabled'])
self.assertNotIn('column-action_checkbox', [c['target'] for c in controls])
self.assertNotIn('column-row_actions', [c['target'] for c in controls])
self.assertNotIn('column-col_actions', [c['target'] for c in controls])
```

Тесты: Place/Event/Specialist × RU/AZ/EN; Place `deleted_state=deleted`; Specialist superuser и обычный admin без права documents (второму `column-documents_count` не выводить), anon redirect; одинаковый DOM target/label контракт до и после patch. Реальные admin responses и fake rows, не отдельный тест копии helper.

- [ ] **2. Добавить metadata helper.** Контракт: `km_column_options(cl) -> {'storage_key': str, 'options': list[dict]}`. Источник — `cl.list_display`, сформированный текущим ModelAdmin и permissions; не `model._meta.fields` и не прямой список документов. Для имеющихся трёх очередей все отображаемые поля именованные строки. Реализация:

```python
from django.contrib.admin.utils import label_for_field
from django.utils.text import capfirst

@register.simple_tag
def km_column_options(cl):
    excluded = {'action_checkbox', 'col_actions', 'row_actions'}
    options = []
    for index, name in enumerate(cl.list_display):
        if not isinstance(name, str) or name in excluded:
            continue
        options.append({
            'target': 'column-' + name,
            'index': index,
            'label': capfirst(label_for_field(name, cl.model, cl.model_admin)),
            'required': not options,
        })
    key = ('km_hidden_columns' if cl.model._meta.label_lower == 'catalog.place'
           else 'km_hidden_columns:' + cl.model._meta.label_lower)
    return {'storage_key': key, 'options': options}
```

Place сохраняет старый ключ и текущие переводы admin display. Event/Specialist получают отдельные ключи, чтобы одинаковый `updated_at` не переносил пользовательский выбор между разными очередями. Это часть данного явно предложенного scope.

- [ ] **3. Подключить metadata к существующему menu.** Существующие summary/SVG/text и классы сохраняются; меняется только источник controls:

```django
{% km_column_options cl as column_menu %}
<details class="km-columns-details" id="km-columns-menu" data-storage-key="{{ column_menu.storage_key }}">
  {# existing summary retained verbatim #}
  <div class="km-columns-dropdown">
    {% for column in column_menu.options %}
      <label class="km-column-option">
        <input type="checkbox" data-toggle-col="{{ column.target }}" data-column-index="{{ column.index }}" checked{% if column.required %} disabled{% endif %}>
        <span>{{ column.label }}</span>
      </label>
    {% endfor %}
  </div>
</details>
```

- [ ] **4. Исправить только блок toggler.** Ключи и индексы формирует сервер из текущего `cl.list_display`, включая action-checkbox при расчёте индекса. Поэтому скрытый для ordinary admin documents_count не сдвигает неправильную колонку. Не искать по translated label и не предполагать Jazzmin column classes. Таблица отсутствует на empty results — controls не вызывают ошибок и не затирают предпочтения. Non-array/битый JSON трактовать как `[]`, устаревшие ключи игнорировать. Required колонку всегда показывать.

Замена внутреннего блока:

```javascript
var menu = document.getElementById('km-columns-menu');
var table = document.getElementById('result_list');
if (columnCheckboxes.length && menu && table && table.tHead) {
  var storageKey = menu.getAttribute('data-storage-key') || 'km_hidden_columns';
  var savedHidden;
  try {
    savedHidden = JSON.parse(localStorage.getItem(storageKey) || '[]');
    if (!Array.isArray(savedHidden)) savedHidden = [];
  } catch (err) { savedHidden = []; }
  var valid = columnCheckboxes.filter(function (cb) {
    var index = Number(cb.getAttribute('data-column-index'));
    return Number.isInteger(index) && index >= 0 &&
      table.tHead.rows[0].cells[index];
  });
  function applyColumnVisibility(cb) {
    var index = Number(cb.getAttribute('data-column-index'));
    Array.prototype.forEach.call(table.rows, function (row) {
      if (row.cells[index]) {
        row.cells[index].classList.toggle('is-hidden-column', !cb.checked);
      }
    });
  }
  valid.forEach(function (cb) {
    cb.checked = cb.disabled || savedHidden.indexOf(cb.getAttribute('data-toggle-col')) === -1;
    applyColumnVisibility(cb);
    cb.addEventListener('change', function () {
      if (cb.disabled) cb.checked = true;
      applyColumnVisibility(cb);
      var hidden = valid.filter(function (item) {
        return !item.disabled && !item.checked;
      }).map(function (item) { return item.getAttribute('data-toggle-col'); });
      try { localStorage.setItem(storageKey, JSON.stringify(hidden)); } catch (err) {}
    });
  });
}
```

Все th/td данной колонки получают существующий `is-hidden-column`; CSS уже используется Place. Проверить наличие класса у cell types в реальном браузере. Никакого HTML/style/response injection в acceptance. Остальной JS не менять.

- [ ] **5. Targeted GREEN.** Запуск через новый isolated runtime: `runtime.py test catalog.testcases.test_admin_queue_columns catalog.testcases.test_admin_queue_search_state catalog.testcases.test_mod_qa03_queue_sorting catalog.testcases.test_specialist_entry_admin.SpecialistEntryAdminTests.test_plain_editor_has_no_private_document_inline_or_count catalog.testcases.test_task33_specialist_security_review.IndependentSpecialistSecurityTests.test_ordinary_admin_cannot_observe_private_document_count`. Новые методы +14 затронутых existing методов; полный08 не повторять здесь.

- [ ] **6. Реальный браузер и evidence.** Все три очереди RU/AZ/EN×360/390/768/1024/1280/1440. Native menu→Tab/Space toggles: реальный th/все его td скрываются и возвращаются; заголовок/имя всегда доступно; reload сохраняет выбор; переход Event↔Specialist не переносит выбор. Existing Place preferences сохраняются. Корзина Place, пустые результаты, ordinary Specialist admin без documents, malformed JSON/не-массив/устаревший target/identity в storage. Для намеренно повреждённых storage-состояний пометка SIMULATED; основные потоки без подмены browser state. Sidebar expanded/collapsed, mobile overlay закрывать штатно перед фоновыми controls. Проверить console/network, visible keyboard focus, menu помещается в viewport; PNG. На мобиле открытый overlay — явный boundary, не обход кликом сквозь него.

- [ ] **7. Проверить сохранность и оформить LOCAL результат.** Сверить fingerprint всех domain rows до/после; source процесса/свежие собственные MO; foreign WORKTREE/active_run/стенды. Semantic gate, точные команды/exits/counts, PNG hash manifest, NOT RUN. Если появляются новые причины/существенное расширение — отдельный PLAN, никакого молчаливого CSS/ACL/PO исправления. После фактического закрытия колонок оценить оставшийся MOD03; MOD04–08 выполнять отдельными планами. Полный ACCEPT08 один раз после задач. Module09/production/commit/push/deploy запрещены.

## Самопроверка плана

Причина — контракт общего меню не соответствует реальным колонкам и Jazzmin header markup. План учитывает обе стороны связи controls→cells в тех же четырёх файлах. Четыре paths заданы; data contract helper/template/JS согласован; повторно реализовывать search/sort/menu fixes не требуется. Изоляция, keyboard, locales, private-column ACL и сохранность явно включены. Это план будущих изменений, не готовый GREEN и не одобрение.
