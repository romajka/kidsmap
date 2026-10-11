# MOD-QA-03 — Панель очередей выходит за экран при ширине 1024

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6 · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: admin. URL/endpoint: `/ru/admin/catalog/place/; /ru/admin/catalog/event/; /ru/admin/catalog/specialist/`. Проверенные cells: RU/AZ/EN × 1024; повторная проверка всех трёх очередей.

Шаги: Открыть очередь на 1024px с обычным sidebar. Дождаться settled layout. Сравнить viewport и правый край toolbar, раскрыть сортировку/колонки. Посмотреть строки мест.

Ожидание: Панель поиска/сортировки/колонок помещается в доступную ширину; таблица прокручивается в своём контейнере и остаётся читаемой.

Факт: Root scrollWidth=1162 в RU/AZ и 1099 в EN при viewport=1024. .km-toolbar-right выходит до x=1162.31/1099.09. Кнопки справа обрезаны; у мест первые строки достигают 548px, колонка обновления сжимается до почти нулевой ширины.

Причина / границы гипотезы: Подтверждён источник общего overflow: nowrap в search form, min-width:280px у поиска и toolbar-right при sidebar; wrapping breakpoint только max-width:900. Причина сжатия отдельных table columns/548px row требует дополнительного CSS разбора — гипотеза, не доказанная общая первопричина.

Source: static/admin/css/pages/kidsmap_changelist.css:445–491,731,989–998,2862; src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html:95. Доказательства: [final-proof.result.txt](../final-proof.result.txt), [supplement.result.txt](../supplement.result.txt), [queue-place-settled-ru-1024.png](../screenshots/queue-place-settled-ru-1024.png), [queue-event-settled-en-1024.png](../screenshots/queue-event-settled-en-1024.png), [queue-specialist-settled-az-1024.png](../screenshots/queue-specialist-settled-az-1024.png). Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: На планшетной ширине часть управляющих элементов недоступна без горизонтального перемещения, строки мест плохо читаются. Критическая потеря данных/компрометация этим evidence не установлена.

Область: Shared changelist toolbar responsive layout и scoped table column rules. Не менять данные/фильтрацию. Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; sidebar available content width; Place/Event/Specialist shared template; модули01/03/04.

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/MOD-QA-03.txt).
