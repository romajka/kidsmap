# MOD-QA-08 — Панели фильтров мероприятий и специалистов открываются пустыми

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6 · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: admin. URL/endpoint: `/ru/admin/catalog/event/; /ru/admin/catalog/specialist/`. Проверенные cells: RU/AZ/EN × все 6 ширин, 36 открытых panels.

Шаги: Открыть очередь, кнопкой Filter/Enter раскрыть панель. Попытаться выбрать статус, дату события или формат консультации. Сравнить с конфигурацией admin и настоящими filter_specs.

Ожидание: Поля применимых фильтров, определённых для данной сущности; выбор и применение меняют GET и список.

Факт: Панель содержит пустую область, заголовок качества данных, Reset/Apply и счётчик, но не содержит native select. Для специалиста доступны в server filter_specs status/is_active/consultation_format/specializations; для события status/start_datetime/owner, но UI их не выводит.

Причина / границы гипотезы: Общий search_panel фильтрует spec.field_path по фиксированному whitelist мест created_by/created_date/category/district/is_verified и place quality fields. km_primary_filters Event и Specialist не используется в этом rendering. В фикстуре Event единственная категория поэтому Django законно не выводит category; остальные доступные specs также проигнорированы.

Source: src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html:280–315; src/catalog/domain_admin/place.py:938,1549; src/catalog/domain_admin/specialist.py:451–455. Доказательства: [drawers.result.txt](../drawers.result.txt), [filter-contract.json](../filter-contract.json), [filters-open-event-ru-390.png](../screenshots/filters-open-event-ru-390.png), [filters-open-specialist-en-1440.png](../screenshots/filters-open-specialist-en-1440.png), [filters-en.png](../contacts/filters-en.png). Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: Обещанные дополнительные фильтры отсутствуют; часть отбора приходится делать вручную. Status tabs остаются отдельным работающим способом. Критическая потеря данных/компрометация этим evidence не установлена.

Область: Shared filter renderer по entity-specific config/filter_specs; preserve query, chips, counts и reset/apply behavior. Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; SimpleListFilter и стандартные FieldListFilter; связанные очереди других сущностей; не менять бизнес-фильтрацию и права.

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/MOD-QA-08.txt).
