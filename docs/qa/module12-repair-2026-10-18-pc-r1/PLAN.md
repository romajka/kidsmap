# Module 12 Implementation Plan

**Goal:** проверить и завершить локально аналитику KidsMap, исправляя все подтверждённые исходные и новые связанные дефекты.

**Architecture:** сохранить существующие определения просмотров, уникальных посетителей и действий; исправлять границы доступа, записи и отчётности без миграции истории. Локальные агрегаты и GA4 имеют отдельные источники и состояния доступности.

**Tech Stack:** Django/PostgreSQL, существующие шаблоны/PO, Chromium через Playwright CLI.

**Spec:** текущий запрос пользователя и разделы PLAN/ACCEPT-12 в `docs/qa/continuation-and-repair-prompts-2026-10-11.md`. Пользователь заранее разрешил реализацию всего модуля и новых связанных исправлений. Исполнение последовательно основным агентом, без повторного согласования того же объёма и без заявления независимой проверки.

## Ограничения

Сохранить 1058 исходных файлов начального снимка, исходные assertions и 43 предыдущих QA-пакета. DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, актуальные изолированные переводы до django.setup. Production, реальные GA credentials/события, commit/push/deploy, удаление истории и изменение чужих стендов исключены. Исходные 8 находок — чек-лист для нового воспроизведения. Общие MO не переписывать.

## 1. Ingress, доступ и отказ записи

Файлы: `src/catalog/domain_admin/site.py` (SiteAnalyticsAdmin.changelist_view); `src/catalog/views.py` (_allowed_tracking_hosts и track_event); `src/catalog/repositories/tracking_repositories.py` (find_active_for_event); `src/catalog/services/tracking.py` (запись событий и subject views); `src/catalog/services/analytics_quality.py`; новый узкий helper `src/catalog/services/analytics_persistence.py`, если воспроизведение подтвердит необходимость общей транзакционной границы; новый `src/catalog/testcases/test_module12_ingress.py`.

- [x] Новые тесты сначала в собственном scratch-модуле: staff без прав получает 403 до построения отчёта; view/change analytics и superuser сохраняют доступ; чужое permission не подходит.
- [x] Проверить опубликованное/неактивное/удалённое/draft/pending место, legacy/canonical CTA, отсутствие ложных записей.
- [x] Проверить same-origin с фактическим портом, явно доверенный origin с портом, чужой порт/host и HTTPS downgrade. Сохранять полную authority, например `request.get_host().lower()` вместо удаления порта.
- [x] При здоровом чтении каталога смоделировать DatabaseError фактического репозитория: публичные Place/Organization/Activity и каталог остаются доступны. Запись должна иметь собственный `transaction.atomic()`/savepoint; исключение перехватывается снаружи, без payload/secret в логах.
- [x] API при отказе записи возвращает честный 503, а не успех; отдельный сбой служебного счётчика ingress не ломает уже выполненное действие. Ошибки основного каталога и программирования не скрывать.
- [x] Сохранить свежий RED, затем применить минимальные подтверждённые исправления и неизменные новые тесты; свежий GREEN вместе с существующими tracking/AI/event/owner suites.

## 2. Периоды GA4 и состояния отчётов

Файлы: `src/catalog/services/admin_analytics.py`, `src/catalog/services/google_analytics_reporting.py`, `templates/admin/catalog/site_analytics.html`; новый `src/catalog/testcases/test_module12_reporting.py`. Переводы новых сообщений — только конкретные записи AZ/RU/EN.

- [x] Тест 90 дней должен отличать квартальные KPI от годовых; literal ожидаемый start `89daysAgo`, end `today`. Сохранить текущие 7/30/365 и явно подписанные фиксированные 30-дневные графики/таблицы.
- [x] Проверить реальные builder/шаблон для disabled/error/частично полученного отчёта/successful empty/loaded. Недоступное число — None/прочерк, успешный пустой отчёт — 0. Текст успешного обновления только после подтверждённой загрузки.
- [x] В UI использовать безопасный локализованный статус и обычную ссылку повторения; не показывать raw provider error, credentials path или identifiers. Сбой после одного успешного вызова не должен выдавать частичные данные за полный успешный снимок.
- [x] Сохранить RED → минимальные исправления → GREEN без изменения исходных тестов и существующего контракта GA-контекста.

## 3. Локализация и UI

Файлы: `src/catalog/templates/pages/owner_analytics.html`, только относящиеся к аналитике записи `locale/az/LC_MESSAGES/django.po`, новые RU/AZ/EN сообщения из предыдущего этапа; новый `src/catalog/testcases/test_module12_localization.py`.

- [x] Воспроизвести AZ сравнение с прошлым периодом и административные labels на свежих MO. Ранее исправленные сообщения отметить повторно проверенными; не править весь PO/fuzzy массив.
- [x] Проверить реальные сохранённые агрегаты/доступность и итоговое отображение RU/AZ/EN, шесть ширин, long/empty/error/filled. Минимальные исправления markup/CSS только при подтверждённом дефекте с отдельной записью scope.
- [x] Native клавиатура/ссылки периода/retry/права, снимки, overflow, console/network. Использовать текущие правила kidsmap-ui-design, frontend-design и accessibility.

## 4. Полная локальная приёмка

- [x] Определить actual view/unique/session/action и исключения по source и независимым ожидаемым delta: guest/login/owner/staff/bot/excluded, повтор/reload/back/forward/two tabs, язык/query/rename/redirect, hidden/restore/history.
- [x] Проверить phone/WhatsApp/website/social/directions и существующие favorites/reviews, запреты чужого owner dashboard, feature flags и отключённое хранилище. Не добавлять отсутствующие в продукте отчёты Event/Specialist.
- [x] Сопоставить DB aggregates, owner UI, выбранные периоды и GA-stub reporting. Mock GA и SIMULATED faults явно отделить от реального подключения.
- [x] Выполнить существующие подходящие backend/Node suites и новые регрессии на свежей БД, затем общую проверку затронутых модулей 10/11.
- [x] Новые связанные дефекты: записать trigger/root cause/точные файлы и ожидаемое поведение, сначала RED, затем исправить и проверить в действующем разрешении пользователя.
- [x] Проверить сохранность и контрольные суммы, собрать девятичастный REPORT с точными командами/результатами/NOT RUN, добавить итог в guide и MASTER, запечатать новый QA-пакет.

Выполнены также отдельные планы readfailure и beacon. Отмеченные пункты относятся к локальному документированному объёму; ограничения внешних интеграций/physical dialer/других браузеров сохранены в REPORT.
