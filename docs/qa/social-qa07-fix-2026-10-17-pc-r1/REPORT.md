# SOCIAL-QA-07 — CLOSED LOCAL, scoped PASS

На текущем dirty WORKTREE исправлено техническое имя Activity object (pk) в заголовке отзывов. Контроллер получает название Activity из того же public presentation resolver, что и карточка занятия, с текущей локалью и разрешённым AZ fallback/snapshot/live Program. Другие виды объектов сохраняют прежний путь. Пустое каноническое имя остаётся пустым; скрытое имя draft не раскрывается даже в разрешённом staff просмотре. Повторный вызов resolver добавляет read-only чтения; оптимизация вне scope.

Пользователь «одобряю» одобрил точный двухфайловый IMPLEMENTATION_PLAN предыдущего PLAN07. Применены только controller expression и новый test_social_qa07_activity_review_title.py. Существующие dirty03 hunks сохранены. 1022 source files: один новый, один изменённый, остальные 1020 побайтно прежние. Снимок HEAD852938d96764ae315b92859e3651e5ea62054a36; ветка codex/module09-transfer-2026-10-16-r1. LOCAL HEAD, dirty WORKTREE и production различаются; production не проверялся и не изменялся.

## RED → GREEN

Неизменившийся RED сохранён в ../social-qa07-recheck-2026-10-17-pc-r1/: 9 новых методов, 7failed/2passed, 18 failing assertions/subtests; native66cells:540controlPASS/144sourceFAIL. Патч и assertions совпадают с одобренными кандидатами, старые assertions не редактировались.

После патча один успешный targeted запуск: 11 уникальных методов (9 новых + 2 affected03), 5.415s, 0 failures/errors, exit0. Проверены requested names для guest/author, RU/AZ/EN, AZ fallback, snapshot, live Program, escaping, canonical empty, другие kinds, hidden404, staff privacy, existing conflict409 render/CAS. tests.log содержит точные результаты; 409/404 строки ожидаемы в целевых тестах.

Неизменённая native матрица: 66cells,540controlPASS/144sourcePASS/0FAIL,114PNG. Localized Activity: guest/author×RU/AZ/EN×360/390/768/1024/1280/1440 (36cells); fallback/snapshot12cells390; Place/Specialist/Event18cells390. Реальный detail→native reviews link→reload, h1/title, роль формы, overflow и business aggregates. Дополнительные 28rows (27cases+aggregate): escaping/empty/live Program guest+author, hidden guest+author404/staff200 на трёх локалях,21PNG. Legacy /az/ redirect для guest/author:2rows,10checks,301→canonical200. Точные дополнительные counts — results.json. Ожидаемые hidden404 отдельно от unexpected HTTP failures. Pageerrors/requestfailed0; основная матрица HTTP failures0. Новые локальные PNG доступны, старые не догружались.

## Изоляция и сохранность

Новый own m09s07-fix-r1-app, Chromium155.0.8059.12/session social07-pc-fix-r1, loopback33348; проверенный внутренний PLAN07 network/fictional PostgreSQL17.11 переиспользован по ownership proof. App mount repository RO, только own scratch RW; Python3.12.15/Django6.0.2, DJANGO_TESTING1, env очищен, собственные cache/media/private-media/email. TestDB test_m09s07_fix_r1 отдельна от normal fictionalDB. В normal ownDB добавлены только fictional edge fixtures; браузерные GET не изменили business aggregates, reviews0. До setup свежая native компиляция RU/AZ/EN в own MO, manifest verify, sole LOCALE_PATHS. Внешние browser requests блокируются allowlist localhost; реальные сервисы не проверялись.

Все 40 входных container ID/name/state сохранены, добавлен один own app (итого41); это не доказательство непрерывности всех процессов компьютера. Предыдущие 8 packages и все151 files PLAN07 неизменны. SharedMO, .cbmignore, HEAD/index/task33-progress и active_run:NONE сохранены. Guide получает отдельную append note с обратной hash-проверкой старых bytes. Без reset/clean/stash/checkout switching/commit/push/deploy/production.

## Ошибки подготовки

До патча WSL git status -uall работал медленно; остановлен только собственный child git и использован Windows git. Начальный apply-check без предусмотренного планом ignore-space-change дал newline/whitespace mismatch, без mutation; точный diff затем прошёл check и применён с одобренным flag. Первый seed/test gate остановился до тестов из-за ошибочно переименованного QA PG hostname; исправлен только own QA profile, исходники/assertions прежние. Failed logs сохранены. Один составной запуск proxy/readiness отклонён автоматической проверкой без подробной причины (blocked by policy); раздельные узкие команды успешно выполнены. Ни один из этих запусков не засчитан как application test failure или PASS.

## Границы

Закрыт только SOCIAL-QA-07 в указанном LOCAL snapshot. SOCIAL08–09, full ACCEPT09, global tests, realSR/fullWCAG, physical devices, другие браузеры, production/external services NOT RUN. Следующий шаг — отдельный свежий PLAN SOCIAL-QA-08; автоматическое начало не разрешено. Никаких новых approvals для уже исполненного07 не требуется.
