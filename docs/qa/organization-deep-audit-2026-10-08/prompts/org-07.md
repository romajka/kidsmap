Работай в /home/ramin/kidsmap. Сначала прочитай AGENTS.md, docs/qa/content-entry-audit-2026-10-06.md и docs/qa/organization-deep-audit-2026-10-08.md. Перепроверь дефект на текущем HEAD/WORKTREE: исторические результаты не считать свежим доказательством. Сохрани чужие изменения. Только DJANGO_TESTING=1, изолированные DB/cache/media и вымышленные данные, без внешних интеграций. Без commit/push/deploy/production.

Исправь только ORG-07 (P2): Без JavaScript приглашение передаёт email и CSRF в URL.

Подтверждённое воспроизведение: Отключить JS в изолированном Chromium, авторизоваться через локальный QA POST, ввести вымышленный email и нажать «Пригласить».
Фактический результат: Форма отправляет GET текущего кабинета с email, role, scope и csrfmiddlewaretoken в query. Приглашений0. Токен в доказательствах заменён REDACTED.
Нужный результат: POST на сервер приглашений либо явно недоступная функция с объяснением. Данные и CSRF не попадают в GET.

Область и границы изменения: Security/frontend/backend: безопасный POST fallback с той же авторизацией/CSRF либо явное отключение отправки без JS. Исключить секреты/query email из URL и отчётов.
Первопричина: У form нет method/action; правильный POST существует только в обработчике JS.
Точка входа в код: src/catalog/templates/pages/organization_workspace.html:448.
Доказательства: docs/qa/organization-deep-audit-2026-10-08/evidence/ и screenshots/, файлы browser-nojs-confirmed.json; team-observe.json; screenshots/team-nojs-390.png.

Не меняй правила доступа, владения, актуальности связей и публикации ради исправления интерфейса. Связи выполняй через canonical request_join/confirm_join/detach, не прямое присваивание organization_id. Не расширяй права автора/сотрудника. Проверь позитивный сценарий, отказ, повтор и конфликт; UI — RU/AZ/EN, 360/390/768/1440 и клавиатуру. Для ошибок доступа, потери данных и версий добавь регрессию, которая падает до исправления и проверяет пользовательский результат. Простые CSS и текстовые изменения проверь в rendered browser. В конце покажи локальный diff, точные команды/результаты, скриншоты PC/mobile и NOT RUN. Выполни только эту задачу; остальные findings не исправляй.
