# Organization management Implementation Plan

**Статус на 2026-10-07:** внедрён согласованный scope кабинета и административного подключения существующих мест. Приёмка локальная и частичная: 142 целевых теста, браузерные сценарии и ограничения приведены в [отчёте внедрения](/home/ramin/kidsmap/docs/qa/organization-management-implementation-2026-10-07.md). Чекбоксы ниже сохранены как исходная спецификация; они не заменяют таблицу фактически выполненных проверок. Без commit/push/deploy.

> **For agentic workers:** выполнить последовательно после явного согласования пользователем этого scope. Указание пользователя «без commit/push/deploy» имеет приоритет над generic execution/commit workflows. План не является разрешением на внедрение. Дополнительные агенты не требуются.

**Goal:** Подключать существующие Place к Organization из кабинета и админки с понятными согласиями, конфликтами, повтором операции и последствиями отвязки.

**Architecture:** Общий coordinator поисковых/preview/batch операций над существующими `organization_ownership.request_join`, `confirm_join`, `approve_informational_join`, `detach`. Новый server receipt хранит результаты по строкам и обеспечивает повтор; ownership/grants/publication остаются в существующих сервисах. UI не пишет organization_id и не выводит права из имени роли.

**Tech Stack:** Текущие Django/PostgreSQL, server-rendered templates, существующий vanilla JS/CSS и gettext RU/AZ/EN. Без новых сторонних библиотек и фоновой инфраструктуры.

**Spec:** [аудит, правила, сценарии и макеты](/home/ramin/kidsmap/docs/qa/organization-management-design-2026-10-06.md). Обязательны разделы 4–5 и acceptance ниже.

## Глобальные границы

- Только локально, DJANGO_TESTING=1, isolated PostgreSQL/cache/media/email, blocked external transport. Production не трогать. Без commit/push/deploy.
- Сохранить текущий dirty WORKTREE, включая Event fixes и отдельный неутверждённый Place form design. Перед реализацией снять новый manifest; не выполнять reset/checkout/cleanup чужих файлов.
- Не менять `_side_owner`, `_reviewer`, consent, affiliation_current, required/publication readiness, Program ownership, grants/actions, role codes, волонтёрские ограничения. Новые запросы передают настоящий request.user.
- Все связь/подтверждение/отвязка — только канонические сервисы. `transfer_owner` не использовать для переноса между сетями. Существующий create_branch сохраняется для **нового** Place; не используется для подключения существующего.
- Business и informational — разные явно выбранные режимы. Staff без владения стороной не получает business bypass. Не понижать/повышать тип текущей связи массово.
- Transfer двухшаговый и явный: detached → новое request/confirm. Автоматического/атомарного переноса, rollback программ или передачи владельца нет.
- Place, Activity, OfferingGroup, PricingPlan и Program сохраняют модельные границы. Часы работы Place не смешивать с расписанием группы.
- Preview TTL 10 min; max 100 явно выбранных ID; page 20. TTL и лимиты — ограничения новой операции, не новые правила публикации.
- Никаких обещаний autosave. Отдельно «Выбрано», «Просмотр ещё не подтверждён», «Выполняется», «Результат сохранён», «Связь ждёт подтверждения владельца».
- RU/AZ/EN, 360/390/768/1440, keyboard, focus/error/live states. Existing logo/tokens; sidebar прототипа не переносить в приложение.

## Карта файлов

| Файл | Ответственность |
|---|---|
| New `src/catalog/services/organization_connections.py` | Видимый поиск, eligibility, серверный preview, выполнение по строкам и результаты; вызывает существующие transitions |
| New `src/catalog/models/organization_connection_operation.py` + export в `models/__init__.py` | Operation и Item, key/fingerprint/snapshots/status; без PII payload и admin CRUD |
| New `src/catalog/migrations/0137_organization_connection_operation.py` | Additive receipt tables/constraints; перед внедрением проверить номер/leaf, чужие миграции не переписывать |
| `src/catalog/controllers/organization_workspace.py`, `src/catalog/urls.py` | Поиск/preview/confirm/result/detach-preview в кабинете с existing ACL |
| New `src/catalog/domain_admin/organization_connections.py`, узкая регистрация action/get_urls в `domain_admin/place.py` | Массовая операция поверх текущего списка Place; не меняет existing publication actions |
| New `templates/pages/organization_connections.html`, `templates/pages/organization_detach.html`, `templates/admin/catalog/place/organization_connections.html` | Семантические страницы owner/admin, общие partials строк и результата |
| `templates/pages/organization_workspace.html`, `templates/pages/organization_create.html`, `static/js/organization_workspace.js`, `static/css/pages/organization_workspace.css` | Раздельные connect/create entrypoints, связь/status/copy/roles, предупреждение о дублях; сохранение существующих form blocks |
| New `static/js/organization_connections.js`, `static/css/pages/organization_connections.css` | Выбор/поиск/preview feedback/focus/mobile; backend остаётся источником итогов |
| `domain_admin/business.py`, organization-specific block `templates/admin/catalog/business/change_form.html` | Подписи OrganizationForm и ясные draft/review кнопки только Organization |
| `services/place_access.py`, `models/business_team.py`, точечные потребители roles/scopes | Human labels, enum/action values неизменны; проверить metadata migration для choices, не создавать data migration |
| `locale/{ru,az,en}/LC_MESSAGES/django.po` и `.mo` | Новые/исправленные UI строки; проверить соседние consumers общих role strings |
| New `testcases/test_organization_connections.py`, New `testcases/test_organization_connections_concurrency.py`, existing workspace/permissions/public_details tests | Domain/action/transport/retry/race/security/public-preservation acceptance |

Номер 0137 предложен по текущему leaf 0136; при параллельной новой миграции выбрать следующий свободный номер и актуальную dependency. Схему Place/Program/Activity менять не требуется. Если надёжный receipt исключается из согласования, требования повторного запроса/перезапуска нельзя заявить выполненными.

## Task 1: Поиск, состояния, preview

**Files:** organization_connections service, shared row partial, new tests.

**Interfaces:** `search_places(actor, organization_id, query, cursor)`; `preview_connections(actor, organization_id, relationship_kind, place_ids)` → server-held manifest + per-row decision; `preview_detach(actor, place_id, organization_id)` → actual impact + versions. Returned decisions — UI model, не новая независимая ACL.

- [ ] Написать meaningful tests: поиск AZ/RU/EN/address, одинаковые названия с разными адресами, pagination/выбор ID, private foreign draft и aggregate/count не выдаются, current org name раскрывается только при допустимой видимости.
- [ ] Написать decision tests: own-both immediate, one-side pending, staff neither denied, informational reviewer only, no owner, current same, different network, changed ownership, archived/deleted, foreign Program, pending другого типа, stale content request.
- [ ] Запустить red tests в guarded isolated DB; убедиться, что failure относится к новой функции.
- [ ] Реализовать только adapter чтения; использовать existing resolver/permissions. Не расширять queryset, опираясь на name/email совпадение.
- [ ] Preview с actor/target/mode/ID/version/request/program state и TTL; stale/foreign preview отвергается. Preview без mutations и без отправки уведомлений.
- [ ] Проверить source/public ACL и tests; отдельно negative direct request с подменой IDs/actor/kind.

**Готовый результат:** сервер умеет объяснить, какие строки подключатся, какие останутся pending и какие заблокированы, ничего не изменяя.

## Task 2: Durable per-row coordinator

**Files:** new receipt models/export/migration, service, concurrency tests.

**Interfaces:** `execute_connections(actor, preview_id, idempotency_key)` и `execute_detach(actor, preview_id, idempotency_key)` → operation ID/status; `connection_result(actor, operation_id)` → видимые current result rows. Receipt action различает connect/detach; detach содержит одну строку. Item codes: connected, requested, already_connected, waiting_owner, detached, already_detached, other_network, kind_conflict, no_rights, owner_required, changed, archived, program_conflict, manual_review, unavailable, failed.

- [ ] Написать tests на уникальный actor/key, fingerprint mismatch, duplicate ID, bool/invalid ID, batch limit, missing/expired preview, inactive actor и отзыв прав между preview/execute.
- [ ] Написать transactional race tests: два submit одного ключа; два независимых действия на один Place с разными целями; редактор меняет content/owner/Program; owner меняется и возвращается; конкурентная detach/confirm.
- [ ] Написать partial result test: 10 selected с eligible/pending/already/conflict/changed; успехи сохраняются, конфликтные строки не записаны. Новое подтверждение только проблемных ID.
- [ ] Создать Operation/Item с уникальным actor/key и operation/place; один проход строк не держит batch transaction над всеми Place.
- [ ] На строку: lock receipt item; locks domain Organization→Place→Program→Activity→request; compare server snapshot; nested service call с настоящим actor; result фиксируется в том же outer transaction. Ошибка service внутри savepoint оставляет только error result, без частичного transition.
- [ ] `business`: request_join; current approved повтор возвращает already; existing pending нужной стороны — confirm_join только после explicit consent. `informational`: request_join → approve_informational_join только после явного разрешённого review. Same-target different-current-kind блокируется в coordinator, без overwrite типа.
- [ ] Повтор same key возвращает существующий результат; same key/different payload — conflict. Interrupted operation возобновляет незавершённые items с тем же исходным snapshot и текущим ACL. Не повторяет committed items.
- [ ] Не копировать уведомления в coordinator; сохранить канонический outbox dedupe. Проверить число OrganizationPlaceRequest/WorkflowNotification/EmailOutbox до/после repeat и retry.
- [ ] Применить migration только на isolated DB; проверить rollback/schema constraints локально. Прогнать tests и доказать journal/transition atomicity при исключении и разрыве исполнения.

**Готовый результат:** надёжная массовая операция поверх существующих transitions, включая partial failure и resume; права/публикация не расширены.

## Task 3: Кабинет организации и существующие места

**Files:** workspace controller/routes/templates, connections JS/CSS, workspace tests.

- [ ] Вместо одиночного select дать отдельный экран поиска/выбора. Название+адрес+current organization+publication+connection/request state. Выбранные ID сохранять при фильтрации/переходе страницы до отправки.
- [ ] Разделить две кнопки: «Подключить существующие места» / «Создать новый филиал». Для пустой организации показать обе; наличие филиалов не required создания.
- [ ] Оставить поиск подключённых филиалов, добавить адрес и явное stale/informational состояние. Не выводить все FK-branches как confirmed business.
- [ ] Owner connection review с итогом immediate/request/no-change/conflict, consent последствий доступа. Сотруднику без владения не показывать join permission; branch.create отдельно.
- [ ] Pending показывает, чьё подтверждение нужно. Владельцу Place оставить возможность подтвердить без organization workspace.view, как сейчас. Другому владельцу не открывать кабинет сети.
- [ ] Устаревший content-request — объяснение и путь проверки, не фиктивная кнопка cancel/resend. Повтор successful join — result без дубля.
- [ ] New branch duplicate checkbox скрыть до possible_duplicate; вывести проверяемые существующие совпадения с адресом/доступными действиями. Не менять duplicate detection и разрешённое allow_separate.
- [ ] Проверить no-JS server fallback, focus возврат после ошибки, live count/status, mobile rows и keyboard Space/Tab/Enter.

**Готовый результат:** владелец находит и подключает 10 уже созданных мест, отличает запрос от готовой связи и не пересоздаёт данные.

## Task 4: Административная массовая операция

**Files:** new admin adapter/templates + узкая action/get_urls в PlaceAdmin.

- [ ] Action «Подключить к организации»: брать выбранный queryset ID только после current admin visibility/permission check; список не заменять raw posted IDs без проверки.
- [ ] Выбор одной организации и явного режима. Staff neither-side business disabled; informational появляется только у reviewer. Никакой имитации владельца/смены mode при отказе.
- [ ] Review с количеством eligible/request/no-change/blocked и причиной каждой строки; current network/title/address, где допустимо. Конфликты другой сети явно «пропустим», без переноса.
- [ ] Подтверждение отображает только executable count; button disabled при pending submit, но server receipt — основной механизм повторов. При timeout показать operation status/result, не «успешно».
- [ ] Per-row result с ID запроса/операции, connected vs waiting, partial errors; сохранять successful rows и не отправлять их повторно. Retry выбранных ошибочных — новый preview/new key.
- [ ] Прямой crafted POST не обходит disabled controls, AdminSite gate, `_side_owner`/`_reviewer`, ACL/versions. После отзыва прав result redacted.
- [ ] Проверить selected page/selected across pages, 10 cards/100 cap, все locales/widths и keyboard; не менять текущие publish/draft/delete actions.

**Готовый результат:** пять видимых стадий пользователя: выбор карточек → цель → просмотр конфликтов → подтверждение → результат каждой карточки. В stepper четыре экранных шага: confirm находится в review, без фиктивного дополнительного wizard-экрана.

## Task 5: Последствия отвязки и двухшаговый перенос

**Files:** shared preview/service, detach controller/template, public-details/ACL tests.

- [ ] Перед detach сервер считает live Program dependencies, утверждённые snapshots/версии, inherited contacts и действующий network/direct access. Без выгрузки имён/email чужих сотрудников.
- [ ] Preview показывает сохраняемые Place/медиа/группы/тарифы/часы, остановку live Program updates, потерю inherited contacts и network access, сохранение direct grants и возможный возврат network access при rejoin.
- [ ] Confirm содержит собственный receipt/key и полный snapshot check; вызывает только detach(expected_ownership_version). Same receipt повтор — прежний результат даже если FK уже пуст; не новая ошибка старого route lookup.
- [ ] Missing approved snapshot / stale dependency — отказ без удаления Program/групп/цен; manual review. Перепроверить published/pending Program и local supplements.
- [ ] После явной отвязки дать переход «Подключить к другой организации» с новым отдельным preview. Показывать самостоятельное место, пока новая сторона не согласилась. Не связывать Program новой сети автоматически.
- [ ] Проверить прямой владелец Place без доступа к кабинету организации; владелец организации; staff без владения; архивная организация; concurrent edit/detach; повтор; failed new connection после successful detach.

**Готовый результат:** отвязка и перенос объяснены и проверяемы; нет скрытого переноса/смены владельца или обещания недостижимого атомарного move.

## Task 6: Названия, создание/редактирование организации и приёмка

**Files:** OrganizationForm/template, role/scopes consumers, locale files, acceptance report.

- [ ] Локализовать Name az/ru/en → названия организации и уточнить общие/локальные контакты. Не удалять существующие поля create/edit, не менять required/validators/publication.
- [ ] Только для Organization убрать конкурирующее Save×3 визуальное меню: черновик и отправка на проверку; existing candidate/live guards и reviewer actions сохранить. Program/Activity/OfferingGroup не перерабатывать.
- [ ] Редактор/Менеджер локализованы, actual permissions явно видны. Legacy business MODERATOR → Наблюдатель (code/preset прежние). Все consumers проверены; platform role не переименована. Scope labels локализованы, all_network/new future branch consequence ясна.
- [ ] UI объясняет: selected_places ограничивает Place-actions; organization.view/edit и program.manage отдельно действуют для всей организации. Не скрывать это следствие за выбором филиалов.
- [ ] Meaningful tests показывают неизменные role codes/actions, selected/all scope, team.manage owner-only и platform-only publication/moderation. Никаких assertions ради зелёного результата.
- [ ] Final browser acceptance RU/AZ/EN × 360/390/768/1440: desktop/mobile screenshots, реальные POST новых UI на синтетических объектах, keyboard focus/errors/result. Полная фактическая загрузка фото; PK/storage path и byte hash до/после 10 joins/repeats/detach.
- [ ] Создать организацию без Place; добавить отдельно новый филиал; подключить 10 ready existing Place без пересоздания; разные владельцы → pending → второе согласие; foreign network/foreign rights/archive/content/owner/program conflicts; partial result; repeat/double-click/restart; detach/common programs/team/inherited contacts.
- [ ] Проверить публичные Place до/после: те же URL, фотографии, занятия, группы, тарифы, opening hours; правильные сетевые ссылки/контакты. Проверить published/pending/rejected/draft карточки без изменения publication state от join/detach.
- [ ] Повторить existing ownership/permissions/workspace/public-details и новые targeted tests. Workspace fixture создаёт Category явно; не объявлять исходный stock run зелёным, если независимость не исправлена в отдельном согласованном test scope.
- [ ] Итоговый отчёт: exact commands/HEAD/WORKTREE, пройденное/ошибки/not tested, screenshots, manifest сохранности. Не утверждать production-ready/full-suite, если таких проверок нет.

## Что намеренно не включено

Blanket staff business override; назначение владельца; изменение publication/required fields; Program→Program remap между сетями; массовая смена типа существующей связи; новые cancel/reject lifecycle для stale-content pending; миграция/исправление всех старых связей; общий редизайн Place/Event/Program/team ACL; production/commit/push/deploy.

Если при внедрении обнаружится необходимость изменить один из этих контрактов, остановить зависимую часть и представить отдельный конкретный scope. Уже согласованные задачи этого плана продолжать без повторных разрешений.
