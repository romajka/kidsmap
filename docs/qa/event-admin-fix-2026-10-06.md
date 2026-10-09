# Исправление административной формы мероприятий — 06.10.2026

Режим: локальная реализация, scope прямо разрешён текущим запросом пользователя. Исполнитель root, последовательно, без независимых subagents. Проверена текущая dirty WORKTREE поверх LOCAL HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`. Production не подключался. Commit/push/deploy не выполнялись.

## Первопричины и изменения

1. **Переводы:** `locale/ru/LC_MESSAGES/django.po` содержал чужие `msgstr` для строк «Владелец мероприятия», «Связанное место», «Нужна доработка», «Готово к публикации», «Дата окончания», «Завершено». Исправлены глобальные записи; `.mo` пересобраны для локальной проверки. Подмена подписей в одном шаблоне не использовалась. Как именно возникла порча каталога, не установлено.
2. **0 из 0:** Event передавал JSON `km-admin-progress-config`, а общий обработчик ожидал `km-place-progress-config` и другой формат элементов. Общий обработчик обнулял серверные значения. Event получил отдельный маленький адаптер; общие обработчики фото, галереи и навигации сохранены. Place adapter пропускает только Event readiness.
3. **Готовность:** прежняя сводка дублировала часть требований, засчитывала RU-название вместо обязательного AZ и требовала адрес онлайн-событию. Список административных требований вынесен в `EventAdminForm.PUBLICATION_CHECKLIST` без изменения валидации. Окончательный verdict даёт `is_valid()` копии той же формы с действием публикации: это включает текущие правила организатора, площадки, дат, модели и URL. Probe только читает, не сохраняет. Форма отдельно показывает полный список ошибок проверки публикации.
4. **Статусы:** несохранённая форма показывает «Новая карточка»; сохранённая карточка — черновик / модерация / публикация / отказ. После неудачного POST сводка берёт статус сохранённой записи, а не изменённого в памяти ModelForm instance. Готовность данных и жизненный статус показаны отдельно: заполненный отклонённый объект может иметь готовые поля, но остаётся отклонённым.
5. **Live progress:** список и условность физического адреса приходят с сервера. После изменения формы полная заполненность ограничена 99% и подписана «Требуется серверная проверка». Серверные ошибки дают «Нужна доработка». После успешного сохранения/повторного открытия валидная карточка получает 100%. Browser не повторяет ACL, парсинг дат и правила опубликованного occurrence. Изменение галереи не сбрасывает проверку основных полей.
6. **Mobile:** воспроизведено переполнение 685px на 360/390 при редактировании; при загрузке формы сразу на узком viewport выявлена также inline-ширина Select2 600px у формата. `published_at` создавал intrinsic minimum медиаблока. Новый CSS ограничен `#event_form`: min-width медиаблока и доступная ширина Select2/input. Глобальный CSS чужих страниц не переписывался.
7. **Отсутствующие контакты:** специальный `event/location_section.html` не выводил существующие `phone`, `instagram`, `website`, `moderation_note`. Телефон был обязательным для публикации, но отсутствовал в UI. Восстановлен только вывод полей и ошибок.
8. **Неудачная загрузка:** preview использовал `form.instance.photo`, уже заменённое несохранённым upload. Браузер запрашивал `/media/synthetic.png` и получал 404. Preview теперь использует сохранённое `form.initial.photo`; live checklist отличает сохранённое фото от нового выбора. После ошибки браузер по-прежнему требует повторно выбрать новый файл.

Правила организатора, площадки, дат, публикации и прав доступа не изменены. Модели, сервисы Event domain, миграции и ACL не редактировались.

## Другие потребители переводов

- Event model verbose names используются административной формой/списками и ModelForms.
- `OwnerEventForm.related_place` и `end_date` используют исправленные строки. Текущий owner template подписывает площадку и дату собственными RU/AZ/EN строками: они не подменялись.
- `Place.STATUS_NEEDS_CHANGES`, административная сводка и `PlaceAdmin.quality_status_display` используют readiness-переводы. Свежий browser GET `/admin/catalog/place/1/change/` показал «Готово к публикации»; ложной «Заявка уже обработана» нет.
- Volunteer dashboard использует отдельный `msgctxt`, который уже был корректным и оставлен без изменения.
- «Завершено» используется также административным состоянием истёкшего события и статусом завершённого удаления аккаунта.
- Общие потребители покрыты отдельным regression test, вместе с gettext-проверкой шести исправленных строк.

## Автоматическая проверка

**58 tests, 0 failures, 0 errors, exit 0.** Свежий финальный запуск, PostgreSQL17, отдельная `test_qa_stage04`, `DJANGO_TESTING=1`, LocMem cache/email, отдельные media, sanitized environment, network/libpq guards. Production credentials отсутствуют. Тестовая база отделена от браузерной `qa_stage04`.

```bash
.venv/bin/python .tmp/event-admin-fix-20261006/run.py \
  catalog.testcases.test_event_admin_readiness \
  catalog.testcases.test_task33_event_admin_precision \
  catalog.testcases.test_task33_event_domain \
  catalog.testcases.test_task33_event_security \
  catalog.testcases.test_task33_event_public \
  catalog.testcases.admin.TestAdminOwnershipModerationUX.test_event_admin_can_publish_from_change_form \
  catalog.testcases.admin.TestAdminOwnershipModerationUX.test_event_admin_can_save_draft_and_continue_later \
  catalog.testcases.admin.TestAdminOwnershipModerationUX.test_event_admin_change_form_uses_step_layout \
  catalog.testcases.admin.TestAdminOwnershipModerationUX.test_event_admin_bulk_publish_action_updates_status
```

До соответствующих исправлений воспроизведены failing tests: переводы/new state/missing server verdict; отсутствующие контакты; несохранённый upload preview; ложная публикация после отклонённого POST. Сырые логи остаются в ignored `.tmp/event-admin-fix-20261006/`, не скопированы в Git artifacts. Финальный лог `final-tests.log`.

Дополнительно: `node --check` обоих затронутых JS; `msgfmt --check` RU/AZ/EN; scoped `git diff --check` — exit0. Django system check — 0 issues. При тестовом migrate сообщён существующий warning о несинхронизированных моделях dirty WORKTREE; новые миграции не создавались. Общий `git diff --check` показывает whitespace в чужих исходных изменениях, они не исправлялись.

## Браузерная проверка

Playwright MCP, настоящий Chromium, http://localhost:8781, синтетическая роль администратора. Используется изолированный PostgreSQL container `kidsmap-local-20261006`, Unix socket, NetworkMode=none, без опубликованных DB-портов; локальная почта и кеш в памяти. Preview слушает loopback. На8780 обнаружен другой старый manual-portable процесс; он сохранён. Для текущего кода создан отдельный HTTP process8781 без seed/reset.

[Полная матрица](event-admin-fix-2026-10-06/browser-results.json): **72 сочетания** — RU/AZ/EN ×360/390/768/1440 ×6 состояний: add physical, add online, published online, pending physical, rejected physical, draft physical. Во всех scrollWidth=viewport, total>0. JavaScript pageerror=0, локальные HTTP4xx/5xx=0 в финальном проходе. Это геометрическая и state-проверка всех сочетаний, не72 независимых POST сценария.

Реальные POST/перезагрузки:

- Пустая форма: ошибки обязательных полей, карточка не создана.
- Создание неполного онлайн-черновика → ID6 → повторное открытие → заполнение описания/контактов/фото/дат → сохранение. Адрес пустой и не требуется; 9 пунктов.
- Даты через реальные видимые picker inputs:26.10.2026 23:30 →27.10.2026 01:00, Asia/Baku; сохранены после reload.
- Некорректное окончание: picker не допускает более ранний конец; POST непарных дат даёт серверную ошибку, ввод сохранён. Прямой невалидный интервал также проверен серверным regression test.
- Новая очная карточка: попытка публикации без телефона → серверная ошибка «Телефон», без сохранения. Затем исправление/повторный выбор файла → черновик ID7; 10 пунктов,100%.
- Онлайн ID6 опубликован через admin Save; состояние «Опубликовано». ID7 сохранён на модерацию, отклонён с синтетической причиной, возвращён в черновик.
- POST draft ID7 с status=published и неверным website → ошибка URL, введённые значения в форме сохранены; сводка остаётся «Черновик»/«Нужна доработка». DB не публикуется.
- Главное фото сохранено и загружается после reload. После invalid URL + новый upload прежнее фото остаётся в preview, новых локальных404 нет.
- Дополнительное фото добавлено через настоящий file chooser и сохранено: gallery INITIAL_FORMS=1 после reload. Заполненная галерея также проверена на360/390/768/1440, переполнения нет.
- Select2 формата и date calendar раскрыты на360 во всех трёх языках: dropdown226px, календарь около308px и внутри viewport. Escape закрывает их.

Синтетические карточки6/7 созданы этой проверкой;7 оставлена черновиком,6 опубликована только в локальной тестовой БД. Исходные fixtures не редактировались.

## Скриншоты

- [PC1440](event-admin-fix-2026-10-06/screenshots/desktop.png), [mobile390](event-admin-fix-2026-10-06/screenshots/mobile.png), [mobile media](event-admin-fix-2026-10-06/screenshots/mobile-media.png), [mobile errors](event-admin-fix-2026-10-06/screenshots/mobile-errors.png).
- Полная новая пустая форма: [PC](event-admin-fix-2026-10-06/screenshots/ru-add-1440.png), [mobile](event-admin-fix-2026-10-06/screenshots/ru-add-390.png).
- Полные заполненные формы RU/AZ/EN: файлы `*-draft-1440.png` / `*-draft-390.png` в той же папке. Фотографии и контакты синтетические.

## Сохранение чужой работы и границы

Перед изменениями сохранены baseline hashes171 ранее изменённых/untracked файлов и копии затронутых исходников в ignored `.tmp/event-admin-fix-20261006/before/`. Из ранее dirty файлов изменён только `src/catalog/domain_admin/place.py`; все остальные совпадают с baseline. В этом файле код вне `EventAdminForm`/`EventAdmin` совпадает побайтово. Никаких reset/checkout/stash/delete чужих изменений.

NOT RUN: full suite, полная клавиатурная/screenreader-приёмка, 10 фото/drag reorder, все длинные значения всех FK, внешние Google maps/geocoding/OAuth/почта, production. Базовые формы и раскрытые picker/select2 проверены; это не полный accessibility audit.

Сохранённые ограничения текущего кода: в AZ/EN datetime duration helper по-прежнему содержит русские подписи; RU gallery heading и district placeholder местами остаются на AZ. Это отдельная COMMON-01 из исходного отчёта, без глобального расширения scope. В admin publication validation при edit пустое значение может проверяться через сохранённое значение экземпляра; существующий fallback оставлен по требованию не менять правила публикации. На новой карточке обязательность телефона подтверждена POST.

Текущий локальный preview: http://localhost:8781/admin/catalog/event/add/. Запуск на этой машине: `.venv/bin/python .tmp/event-admin-fix-20261006/run.py --serve`; скрипт ignored, fail-closed settings и guards внутри. Без commit/push/deploy.
