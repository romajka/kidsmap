# MOD-QA-01 — В центре модерации нет перехода к следующим страницам

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6 · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: admin / content reviewer. URL/endpoint: `/ru/admin/volunteer/moderation/?status=pending`. Проверенные cells: RU/AZ/EN × 360/390/768/1024/1280/1440.

Шаги: Открыть очередь с более чем 25 предложениями. Прокрутить таблицу и найти переход на страницу 2. Затем сравнить с реально отрисованной страницей ?page=2.

Ожидание: Доступные с клавиатуры предыдущая/следующая страница, номер страницы и сохранение выбранных фильтров.

Факт: На первой странице 25 строк, ссылок page=2 нет. Pending counter показывает 32. Страница 2 существует и содержит другие предложения, но попасть на неё из очереди нельзя.

Причина / границы гипотезы: View передаёт Paginator(rows,25).get_page(...), а hub_index.html завершает таблицу без pagination controls. Подтверждено source и 18 rendered cells.

Source: src/catalog/domain_admin/volunteer.py:282–296; src/catalog/templates/admin/volunteer/hub_index.html:19–23. Доказательства: [matrix.result.txt](../matrix.result.txt), [supplement.result.txt](../supplement.result.txt), [hub-ru-1440.png](../screenshots/hub-ru-1440.png), [hub-page2-ru-1440.png](../screenshots/hub-page2-ru-1440.png). Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: Часть очереди недоступна через штатную навигацию; обход требует ручного изменения URL. Критическая потеря данных/компрометация этим evidence не установлена.

Область: hub_index.html / moderation_hub_index; сохранить ACL, counts, GET-фильтры и порядок. Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; Django moderation hub; общая доступная навигация страниц.

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/MOD-QA-01.txt).
