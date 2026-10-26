# Организации: исправления и приёмка, 26.10.2026

**LOCAL WORKTREE — реализовано и проверено. PRODUCTION / GitHub — не изменялись.**

Основание: пользователь согласовал исправление всех описанных пунктов после [аудита](organization-flow-audit-2026-10-26.md) и [плана](../plans/organization-flow-2026-10-26.md). Один исполнитель `/root`, без независимых подагентов. HEAD при начале: `1b0acf8c6d03e71d8516cfb92c19018db1426ebf`, ветка `codex/admin-draft-recovery-2026-10-26`. Существующее dirty дерево сохранено; копии затронутых файлов до изменений находятся в `/tmp/kidsmap-org-fixes-20261026/before/`.

## Что исправлено

| Finding | Результат LOCAL |
|---|---|
| ORG-A01: завышенные счётчики | CLOSED. Distinct counts, одинаковые predicates для counts/filters. Фильтр «Без филиалов» также исключает сеть с действующим филиалом при наличии удалённых связей |
| ORG-A02: невидимые ожидающие версии | CLOSED. Pending revision попадает в очередь; опубликованная организация с pending edits остаётся в опубликованных и появляется в очереди изменений. Архивные записи не попадают в активную очередь |
| ORG-A03: ложная bulk publication | CLOSED. Массовые действия используют `publication.review` / `unpublish`, сохраняют права, версии и проверку автора. Неотправленный draft пропускается с объяснением. Mixed batch, недостаточные права, source conflict, архив и pending candidate при снятии проверены |
| ORG-A04: скрытое required AZ / потеря ввода | CLOSED. AZ явно обязательно; service errors возвращаются на bound form без redirect, значения сохраняются. Удалена пустая техническая вкладка, transport versions сохранены |
| ORG-A05: разные контакты create/edit | CLOSED. Создание Organization использует канонические нормализаторы, owner forms — общий contact mixin. Ошибки относятся к полю. Неизменённые legacy-контакты не требуют произвольного переписывания |
| ORG-A06: перегруженный workspace | CLOSED. Три настоящие вкладки «Филиалы / Профиль / Дополнительно», roving keyboard focus, hash navigation, открытие раздела ошибки. Сведения сохраняются при переключении. Создание филиала раскрывается по запросу; команда/программы исключены из обязательного запуска |
| ORG-A07: ложная stale-связь standalone | CLOSED. Предупреждение осталось для реальных устаревших связей, убрано у самостоятельного места |
| ORG-A08: подтверждение без контекста | CLOSED. Уведомление показывает обе стороны; отдельный read-only preview объясняет доступ, владение и публикацию. Финальное подтверждение остаётся POST+CSRF через прежний ownership service |
| ORG-A09: дублирование / техническая вкладка / языки | CLOSED в проверенных маршрутах. Один ряд filters/counts; телефон и программы скрыты по умолчанию с сохранением column chooser. Убрано двойное empty state. Исправлены подписи, пагинация и ошибочный перевод «Не опубликовано» = «Published» на AZ/EN |

Дополнительно: явный checkbox «WhatsApp на этом же номере» сохраняет существующее поле whatsapp. Публичная Organization больше не рекламирует WhatsApp только по телефону. Историческая политика контактов Place не переписана. В админском создании явно показан назначаемый владелец; передача другому владельцу остаётся отдельным подтверждаемым процессом. Организация имеет читаемое название в breadcrumbs/checkbox labels вместо `Organization object`.

При создании по-прежнему нужно одно поле. На 390×900 px поле начинается примерно на y=529, кнопка целиком помещается до y=899; длинное объяснение раскрывается по запросу. В проверенном workspace на 1280 px основной раздел имеет высоту 1731 px и одно поле поиска, профиль и дополнительные формы показываются отдельно. Это сравнение конкретных состояний fixture, а не performance benchmark.

## Архитектурные границы

- `domain_admin/business.py`: общие predicates статусов, безопасные bulk transitions, bound errors, required AZ, отсутствие пустой вкладки.
- `organization_ownership.py`: каноническая нормализация новых Organization contacts; существующие чужие изменения в сервисе сохранены.
- `organization_workspace.py`: contact forms, preview, состояния публичности, сохранение раздела после submit.
- `workflow_notifications.py` + templates: контекст и ссылка на preview.
- `public_presentation.py`: explicit Organization WhatsApp; Place legacy behavior сохранён.
- `organization_workspace.js/.css`: disclosure, tabs, keyboard/hash/error behavior; CSRF из текущей формы имеет приоритет перед cookie с фиксированным именем.
- `admin_dashboard_tags.py`: локализованная подпись диапазона; общий changelist JS сохраняет пользовательские настройки столбцов.
- `catalog_structure.py`: только `Organization.__str__`, без изменения модели данных.

## Автоматическая приёмка

**269 тестов PASS** в чистой изолированной БД, 63.227 s, exit 0. **Отдельный migration test PASS**, 2.703 s. Всего 270 различных тестов. После последних backend-правок также проходил целевой набор из 59 тестов; итоговый corpus запущен после него.

Новые regression tests: `src/catalog/testcases/test_organization_flow_consistency.py` — 24 сценария. Проверены первоначальные FAIL до исправлений: counts, pending queue, bulk approval/denial/withdrawal, contacts, input retention, standalone copy, explicit WhatsApp, preview ACL, archived queue, owner status и возврат в профиль, различие public/unpublished переводов.

В `test_phone_forms.py` у fixture admin Organization добавлено обязательное AZ-название. Проверки нормализации и их assertions сохранены; отдельный regression подтверждает отказ при отсутствии AZ.

Итоговая команда из `/home/ramin/kidsmap`:

```bash
.venv/bin/python /tmp/kidsmap-org-audit-20261026/run.py acceptance_final \
  catalog.testcases.phone_reveal \
  catalog.testcases.test_mod_publication_toast_localization \
  catalog.testcases.test_organization_admin_labels \
  catalog.testcases.test_organization_connections \
  catalog.testcases.test_organization_connections_concurrency \
  catalog.testcases.test_organization_creation_confirmation \
  catalog.testcases.test_organization_detach_transport \
  catalog.testcases.test_organization_directory \
  catalog.testcases.test_organization_editor_errors \
  catalog.testcases.test_organization_flow_consistency \
  catalog.testcases.test_organization_form_copy \
  catalog.testcases.test_organization_invitation_result \
  catalog.testcases.test_organization_invitation_transport \
  catalog.testcases.test_organization_join_recovery \
  catalog.testcases.test_organization_join_visibility \
  catalog.testcases.test_phone_forms \
  catalog.testcases.test_phone_inheritance \
  catalog.testcases.test_phone_numbers \
  catalog.testcases.test_phone_public_contract \
  catalog.testcases.test_phone_publication \
  catalog.testcases.test_publication_request_completion \
  catalog.testcases.test_task33_organization_workspace \
  catalog.testcases.test_task33_publication

.venv/bin/python /tmp/kidsmap-org-audit-20261026/run.py migration_only \
  catalog.testcases.test_phone_migration
```

Все тесты используют очищенное окружение, `DJANGO_TESTING=1`, отдельные PostgreSQL/cache/media, LocMem email; реальные интеграции выключены. Для повторного запуска после TransactionTestCase нужен новый disposable DB key: повторное использование уже flushed БД теряет taxonomy seed. Migration test отдельно: он откатывает схему до 0145 и не восстанавливает последующие миграции; в общем запуске это ломало чужие concurrency tests отсутствующим столбцом. Его assertions и код не менялись. Ошибки настройки и промежуточные FAIL сохранены в evidence, не объявлены product regressions.

`manage.py check`, `makemigrations --check --dry-run`, `msgfmt --check` для RU/AZ/EN, `node --check` двух изменённых JS — PASS; новых миграций нет.

## Реальный браузер: выполнено

1. Создание сети с одним названием; ошибка неверного телефона показывает поле и сохраняет ввод/фокус.
2. Создание нового филиала → persisted draft с правильной организацией.
3. Выбор своего и чужого существующих мест → preview → consent → своё подключено, чужое ожидает владельца.
4. Второй владелец: уведомление с названиями → preview последствий → подтверждение → место подключено.
5. Создание общей программы; возврат по `#org-programs` открывает «Дополнительно».
6. Приглашение синтетического сотрудника через JSON transport → pending list → принятие в уведомлениях. Проверен фактический доступ к трём филиалам; управление Organization для этой роли остаётся закрытым. Проверка не означает реальную доставку email.
7. Заполнение phone/explicit WhatsApp/description → keyboard switching вкладок → submit → pending revision.
8. Staff queue содержит эту заявку; bulk Publish одобряет её, счётчик pending становится 0, published — 2.
9. Настоящий logout staff → гостевые каталог и карточка. Два опубликованных филиала видны; созданный draft-филиал не показан.
10. Admin RU-only submit: required AZ, server error, исходное RU сохранено, пустой General tab отсутствует.

**105 уникальных responsive-состояний PASS:** семь поверхностей × RU/AZ/EN × 390/768/1024/1280/1440 px. Поверхности: public detail, owner create, workspace branches/profile/extra, admin list/add. Измерены document overflow, язык, активный panel и видимые поля. Повторные 30 замеров создания после компактных мобильных отступов сохранены отдельно; финальная matrix содержит последние значения каждого состояния.

## Финальные факты fixture

`final-probe.json`: реальные организации = 4; counters total=4, published=2, pending=0, draft=2, with_places=2. Созданная сеть: revision approved, approved_at установлен, guest detail=200, foreign confirmation approved. Международные контакты нормализованы; explicit WhatsApp сохранён. У сотрудника есть place.edit и нет organization.edit. Draft branch остаётся private.

Evidence: `/tmp/kidsmap-org-fixes-20261026/evidence/` — `acceptance-complete.log`, `migration-isolated.log`, `final-targeted.log`, `final-probe.json`, `functional.json`, `responsive.json`, `responsive-runs.json`, `screenshots/`. Временные QA-файлы не являются production config или данными реальных пользователей.

## Оценка и ограничения

**После локальных исправлений — 8.5/10** по проверенному сценарию против 5/10 до них. Это экспертная оценка удобства и согласованности, не измерение конверсии или результат исследования пользователей.

NOT RUN: production/deployed schema, реальная регистрация/OAuth, доставка реальной почты, нагрузка, полный WCAG/screen reader аудит, весь корпус других модулей KidsMap. Старые данные и назначение владельцев массово не менялись; автоматического перевода всех исторических контактов нет. Самостоятельная публикация филиалов по-прежнему проходит свой существующий контракт.

Commit/push/deploy не выполнялись. Временные сервер и PostgreSQL-контейнер после проверки остановлены; evidence и pre-edit snapshots сохранены.
