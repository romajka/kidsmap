# MOD-QA-04 — Escape и закрытие административной навигации

**Статус: CONFIRMED OPEN; требуется отдельное одобрение четырёхфайлового плана. Приложение этим PLAN не изменено.**

**Goal:** Escape закрывает открытое меню; на телефоне есть доступная кнопка закрытия внутри панели; после закрытия фокус возвращается к видимой кнопке навигации.

**Architecture:** локальный адаптер использует уже существующую кнопку PushMenu через её обычный `.click()`. Состояние берётся из существующих классов body; accordion-код остаётся отдельным. Шаблон добавляет именованную кнопку, CSS размещает её на мобильном и делает клавиатурный фокус видимым. Vendor/API зависимостей не добавляется.

**Tech Stack:** текущие Django templates/i18n, vanilla JS, действующий Jazzmin/AdminLTE. Внутренние vendor API не используются.

**Spec:** guide PLAN MOD-QA-04; `module08-2026-10-10-r1/findings/MOD-QA-04.md` и `repair-prompts/MOD-QA-04.txt`; fresh `native-recheck.js.result.json` / REPORT.md этого run. Ранее одобренный MOD03 scope не разрешает этот patch. Исполнение в текущем чате по available TDD/debug/UI/verification skills, без новых агентов/commit/push/deploy/production. Новый scope согласуется один раз.

## Fresh recheck и причина

RU/AZ/EN ×360/390/768 ×dashboard/Place =18cells. Нативно закрыть старое меню, фокусировать opener, Enter→Escape. **18sourceFAIL**,38controlPASS; после Escape меню остаётся открытым. На360/390 opener остаётся под sidebar (`elementFromPoint` после settled layout не попадает в кнопку); на768 текущая версия использует persistent sidebar, opener доступен, но Escape также не сворачивает его. Overlay/повторный Enter работают как контроль.

`static/admin/js/kidsmap_admin_sidebar.js` сейчас содержит только accordion и search-clear. Outer PushMenu не получает Escape/restore-focus adapter. Opener объявлен в `templates/admin/base.html`; sidebar — `src/catalog/templates/admin/catalog/includes/sidebar_navigation.html`, кнопки закрытия внутри нет. CSS persistent layout начинается от768px (`kidsmap_admin_layout.css`); мобильный close показывается только ниже768. Сам layout менять не требуется.

В сырых opened snapshots часть768 geometry снята во время transition; вывод о FAIL и блокировке360/390 основан на escaped state после350ms и PNG. Будущие проверки дожидаются settled bounds, а не первого промежуточного width>150.

## Точные файлы — четыре

1. `static/admin/js/kidsmap_admin_sidebar.js`: добавить `initSidebarDismissal`, зарегистрировать рядом с существующим init. Escape, close/overlay focus restoration, aria-controls/expanded opener; остальные accordion/search функции сохранить.
2. `src/catalog/templates/admin/catalog/includes/sidebar_navigation.html`: один button после brand link, до `.sidebar`.
3. `static/admin/css/pages/kidsmap_admin_sidebar.css`: scoped размещение мобильного close + focus-visible opener/close.
4. NEW `src/catalog/testcases/test_admin_sidebar_escape.py`: rendered named-control/localization contract. Browser regression подтверждает фактическое поведение.

Шаблон header, PO, vendor, бизнес-модели/ACL/данные не меняются. Использовать уже существующий перевод «Закрыть» и sprite `kmi-close`. Не вводить sidebar role=dialog или новый focus-trap/inert контракт в этом исправлении.

## Реализация после approval

- [ ] **1. Новый fix snapshot/изоляция и RED.** Перепроверить checkout/HEAD/dirty/active_run/процессы/контейнеры. Проверенный свой профиль допустим только после fresh ownership/source/DB/cache/media/email/sole-locale verification; для устаревшего профиля создать новый. Текущие PO через build_isolated_locales.py в свой новый каталог; manifest до setup. Вымышленные данные, DJANGO_TESTING=1, внешний доступ заблокирован. Existing RED18 и PNG сохранить; свежий failing regression на недостающую кнопку.

Новый backend тест создаёт собственного staff/superuser и через реальные admin GET RU/AZ/EN dashboard/Place проверяет:

```python
self.assertEqual(close['type'], 'button')
self.assertEqual(close['aria-controls'], 'jazzy-sidebar')
self.assertEqual(close['aria-label'], {'ru': 'Закрыть', 'az': 'Bağla', 'en': 'Close'}[lang])
self.assertEqual(len(close_controls), 1)
```

Literals взяты из текущих существующих PO; не вычислять ожидание через production helper. До patch ожидается FAIL отсутствующего control. HTMLParser читает фактический `button[data-km-sidebar-close]`; обычные admin assertions не менять. Отдельный control — staff без доступа к закрытым моделям сохраняет прежние ссылки/ACL.

- [ ] **2. Минимальный template.** После brand-link:

```django
<button type="button" class="km-admin-sidebar__close km-admin-header__toggle"
        data-km-sidebar-close aria-controls="jazzy-sidebar"
        aria-label="{% translate 'Закрыть' %}">
  <svg class="km-i" viewBox="0 0 960 960" aria-hidden="true" focusable="false"><use href="#kmi-close"></use></svg>
</button>
```

Close не получает data-widget: адаптер сам вызывает существующий opener один раз, исключая двойной toggle. Native button Enter/Space не нуждаются в дополнительной обработке клавиш.

- [ ] **3. Scoped CSS.** Использовать текущие tokens и стили кнопки header; вне мобильного close скрыт. Добавить видимый keyboard focus:

```css
.km-admin-sidebar__close { display: none; }
.km-admin-header__toggle:focus-visible,
.km-admin-sidebar__close:focus-visible {
  outline: 2px solid var(--km-admin-primary);
  outline-offset: 3px;
}
@media (max-width: 767px) {
  .km-admin-sidebar .km-admin-sidebar__close {
    display: inline-flex;
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 2;
    background: var(--km-admin-surface);
    color: var(--km-admin-text);
  }
}
```

Проверить реальный hit target, контраст focus и отсутствие пересечения логотипа на360/390. Любая дополнительная переделка header/layout требует отдельного расширения scope.

- [ ] **4. Локальный JS adapter.** Добавить функцию и вызвать при DOM ready вместе с существующими init:

```javascript
function initSidebarDismissal() {
  var sidebar = document.querySelector('.main-sidebar');
  var opener = document.querySelector('.km-admin-header__toggle[data-widget="pushmenu"]');
  if (!sidebar || !opener) return;
  var close = sidebar.querySelector('[data-km-sidebar-close]');
  function expanded() {
    return window.innerWidth < 768
      ? document.body.classList.contains('sidebar-open')
      : !document.body.classList.contains('sidebar-collapse');
  }
  function sync() {
    opener.setAttribute('aria-expanded', expanded() ? 'true' : 'false');
  }
  function restoreFocus() {
    window.requestAnimationFrame(function () {
      opener.focus({preventScroll: true});
    });
  }
  function dismiss() {
    if (!expanded()) return;
    opener.click();
    restoreFocus();
  }
  opener.setAttribute('aria-controls', sidebar.id);
  if (close) close.addEventListener('click', dismiss);
  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape' || event.defaultPrevented || !expanded()) return;
    if (window.innerWidth >= 768 && !sidebar.contains(document.activeElement)
        && document.activeElement !== opener) return;
    event.preventDefault();
    dismiss();
  });
  document.addEventListener('click', function (event) {
    if (event.target.id === 'sidebar-overlay') restoreFocus();
  });
  new MutationObserver(sync).observe(document.body, {attributes: true, attributeFilter: ['class']});
  window.addEventListener('resize', sync);
  sync();
}
```

Существующий PushMenu остаётся владельцем body/sidebar transitions; адаптер не меняет эти классы вручную. На persistent desktop Escape при фокусе в редакторе/таблице не закрывает навигацию. Вложенный обработчик, уже отменивший Escape, имеет приоритет. На mobile открытый overlay закрывается Escape даже при оставшемся на opener фокусе.

- [ ] **5. Только targeted GREEN.** Новый test module + `catalog.testcases.test_admin_sidebar_navigation.AdminSidebarNavigationTests.test_account_group_does_not_expose_models_to_limited_staff` и `test_every_menu_icon_references_an_existing_vector_symbol`. Full module08/CSS/search/sort suites не запускать здесь. Existing assertion scope сохранить. Browser RED18→GREEN на исходном trigger обязательно.

- [ ] **6. Native acceptance и representative shared checks.** RU/AZ/EN×360/390/768×dashboard/Place; Tab/Shift+Tab/Enter/Space/Escape, focus из sidebar и opener, видимый click close/overlay, restore opener и aria state, reopen/reload. Для desktop1024/1280/1440 — только выборочный guard: Escape из редактора/row menu не сворачивает persistent navigation; normal opener toggle по-прежнему работает. Один staff с ограниченными правами + accordion open/close/persistence/icons как shared sample. Не повторять ранее принятые полные матрицы колонок/поиска/таблиц. Settled geometry, console/network, actual PNG/manifest, domain before/after hash.

- [ ] **7. Финал.** Проверить source процесса/свои каталоги/чужие файлы/active_run/стенды. Отдельно показать ограничения continuity после обнаруженного сбоя окружения, без чужих restart. Новый unique fix REPORT и verification с exact commands/exits/counts; обновить только свежий статус MOD04. Полный ACCEPT08 — один раз после всех его задач. MOD05–08 отдельные планы; module09 не начинать.

## Самопроверка

Текущий дефект подтверждён18nativeFAIL, source ownership установлен; четыре app paths заданы. Close button, Escape и focus относятся к одной заявленной sidebar-интеграции. Локализация использует существующий ключ; private ACL/source/layout не переписываются. Это не approval и не GREEN исправления.
