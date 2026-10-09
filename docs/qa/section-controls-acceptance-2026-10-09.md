# Управление публичными разделами: свежая проверка 2026-10-09

Решение: backend и сохранение на desktop работают; полная приёмка FAIL из-за отсутствия мобильного сохранения. Production/deploy NOT RUN.

## Снимок и границы

- LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, `task33-progress`; проверен текущий dirty WORKTREE, не чистый HEAD.
- Локальный стенд: `http://localhost:8792`; синтетический `demo_moderator`.
- Форма: `/admin/catalog/sitevisibilitysettings/1/change/`.
- Код приложения, тесты, production, commit/push не изменялись. Изменялись только локальные переключатели для проверки; исходные значения восстановлены через UI save/reload.

## Реальное сохранение и публичные страницы

Проверка выполнена через native checkbox controls и «Сохранить и продолжить», не через подмену DOM или прямую запись в БД.

| Сохранённая конфигурация | Организации | Специалисты | Афиша |
|---|---:|---:|---:|
| Все выключены | 404 | 404 | 410 |
| Только организации | 200 | 404 | 410 |
| Только специалисты | 404 | 200 | 410 |
| Только афиша | 404 | 404 | 200 |
| Все включены, исходное состояние восстановлено | 200 | 200 | 200 |

При полном отключении detail URLs организации/специалиста/мероприятия вернули соответственно 404/404/410. После восстановления — 200/200/200. Постоянное место `/ru/place/1-otkrytie-yasamal/` и занятие `/ru/activities/1/` при отключении возвращали 200.

На главной исчезли ссылки на все три раздела, включая footer и реально открытое мобильное меню. В админке ссылки остаются доступными, accessibility label содержит «Скрыто на сайте», визуально показан перечёркнутый глаз. Счётчики событий 17 и специалистов 7 сохранились. Запись/редактирование каждой отдельной сущности в этом browser-прогоне NOT RUN; сохранность и admin feature contracts покрывались выбранными backend tests.

После финального save/reload: `events_section_enabled=true`, `specialists_section_enabled=true`, `organizations_section_enabled=true`; `public_favorites_count_enabled=false`, `public_favorites_minimum=''`, как до проверки. Язык интерфейса возвращён RU; viewport override сброшен.

## Визуальные результаты

- Desktop 1440: PASS. Три отдельные строки, зелёный включённый/серый выключенный switch, пояснение и обе кнопки сохранения видны. Нет горизонтального overflow (scrollWidth 1425 при viewport 1440).
- Mobile 390: FAIL сохранения; строки и переключатели читаются, горизонтального overflow нет (375/390), но обе submit-кнопки имеют rect 0×0 и отсутствуют в доступном UI.
- Точная граница: width 760 — save height 0; width 761 — save height 44. При 768 кнопки видны.
- RU: подписи понятны. AZ/EN: FAIL локализации; названия трёх switches, инструкции, help, обратная ссылка и заголовок «Публичное избранное» остались русскими внутри локализованного интерфейса.
- Снимки: [desktop](section-controls-2026-10-09/desktop.jpg), [mobile](section-controls-2026-10-09/mobile.jpg). Mobile снимок сделан после восстановления всех трёх флагов.

## Подтверждённые findings

### SECTIONS-01, P1: на телефоне нельзя сохранить

Общий `static/admin/css/pages/kidsmap_admin_form_shell.css:3112` вводит breakpoint max-width 760. На строке 3194 `.km-place-sidebar-card--actions { display:none; }`, рассчитывая на `.km-place-form-mobile-actions`. В `src/catalog/templates/admin/catalog/shared_settings_change_form.html:102` submit-кнопки находятся только в этом скрытом блоке; альтернативного мобильного блока нет. Scoped `site_sections.css` не восстанавливает actions. Repro: открыть форму при 390, изменить switch, попытаться сохранить — доступной кнопки нет. Desktop сохраняет нормально.

### SECTIONS-02, P2: неполные AZ/EN переводы

Переключить язык через реальное меню RU → EN → AZ. Общая оболочка переводится, подписи и инструкции feature controls остаются RU. Не связано с состоянием флагов.

## Backend verification

Команда:

```sh
PATH="$PATH:/snap/bin" python3 docs/task33/qa04/run.py --output /tmp/kidsmap-sections-review-20261009-current --label catalog.testcases.test_public_section_switches --label catalog.testcases.events_feature --label catalog.testcases.specialists --label catalog.testcases.test_organization_directory --label catalog.testcases.test_task33_public_details
```

Изолированный disposable PostgreSQL 17, network none, `DJANGO_TESTING=1`, изолированные media/cache; production credentials не использовались. 44 tests за 19.616s: 43 PASS, 1 FAIL; system check без ошибок. Safety preflight PASS.

Fail: `catalog.testcases.specialists.TestSpecialistsFeatureFlag.test_feature_enabled_by_default`, `specialists.py:407`, ожидает GET старого owner creation route → 200, получил 302. Текущий `controllers/specialist_workspace.py:302` явно перенаправляет GET без pk на `specialist_workspace_proposal`. Public endpoints того же теста прошли до этого assertion. Это подтверждённое расхождение тестового ожидания и текущего routing; тест не исправлялся и полный прогон не объявляется зелёным.

## Предлагаемый ограниченный scope исправления

1. Только для формы разделов восстановить видимое сохранение до 760 px в `static/admin/css/pages/site_sections.css`; не менять глобальное скрытие actions, используемое другими формами. Проверить порядок кнопок/полей в grid и доступ с клавиатуры.
2. Дополнить отсутствующие AZ/EN переводы в существующих catalog `.po` и штатно обновить их `.mo`. Подписи и пояснения должны соответствовать выбранному языку.
3. Повторить UI POST/save/reload на 390/760/761/1440 и RU/AZ/EN, отрицательные public routes и восстановление настроек. Отдельно согласовать canonical redirect contract для устаревшего specialist test, не менять assertion ради зелёного результата.

Это план на рассмотрение. Application implementation и deployment пока не выполнялись.
