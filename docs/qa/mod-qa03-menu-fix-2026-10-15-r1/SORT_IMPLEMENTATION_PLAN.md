# PLAN: MOD-QA-03 follow-up SORT-REQUEST — approval pending

2026-10-15. Это отдельная причина вне уже одобренных CSS и JS-menu scopes. Backend приложения в этом run не менялся. Исторические MOD04–08 не начинались; прочитаны только их заголовки для сопоставления — сортировка не совпадает с ними. Новый исторический ID не присваивается автоматически.

## Fresh recheck

[native-sort-current-recheck.js.result.json](native-sort-current-recheck.js.result.json):2native source FAIL на текущем menu-fixed WORKTREE, RU1024, Event/Specialist. Поиск `QA Queue 2` сначала даёт1строку. Реальный sort href `?q=QA+Queue+2&sort=created_desc` после native выбора приводит к `?e=1`, q теряется. Синтетические данные не меняются. Подмена CSS/JS отсутствует. Прежний отчёт24functionalFAIL/12dependentNOTRUN сохранён; его полный набор не повторялся. Текущий menu fix1191PASS эту причину не закрывает.

Причина подтверждена source: shared `cl_sort_url` добавляет `sort`, но у EventAdmin/SpecialistAdmin этот служебный параметр не объявлен в list_filter. Django рассматривает его как lookup поля и отклоняет. Рабочий Place уже объявляет PlaceSortFilter с parameter_name=`sort` и имеет get_ordering + current label. У Event/Specialist нет соответствующего mapping/context. SimpleListFilter потребляет параметр; безопасный order mapping должен быть отдельным от ORM lookup. Нет причины менять CSS/JS/HTML/PO либо permissions.

## Точные четыре файла proposed implementation scope

1. **NEW** `/home/ramin/kidsmap/src/catalog/domain_admin/queue_sorting.py` — один helper для двух очередей: служебный filter параметра `sort` без второго видимого сортировочного UI, whitelist6ключей, normalized key/default, ordering и context label/active option. Не импортировать модели/другие admin-модули и не строить order_by из пользовательского текста.
2. `/home/ramin/kidsmap/src/catalog/domain_admin/place.py` — только EventAdmin: подключить helper/mixin и служебный filter к существующим фильтрам, сохранить текущие dashboard/ACL/queryset/quick filters/actions. PlaceAdmin и PlaceSortFilter не изменять.
3. `/home/ramin/kidsmap/src/catalog/domain_admin/specialist.py` — только SpecialistAdmin: то же подключение, сохранить select_related/prefetch/доступ к приватным документам и прочие admin классы.
4. **NEW** `/home/ramin/kidsmap/src/catalog/testcases/test_mod_qa03_queue_sorting.py` —6meaningful regression methods, реальные isolated Django GET/queryset/context, не зеркальные тесты реализационных строк.

## Предлагаемое поведение

- `created_desc/created_asc`: `created_at` в соответствующем направлении; `updated_desc/updated_asc`: `updated_at`; стабильный tie-break по pk в том же направлении.
- `name_asc/name_desc`: каноническое поле `name` соответствующей модели, стабильный pk. Это явное правило данного плана; локализованные display labels и содержимое имён не меняются.
- Default/неизвестный sort: `updated_desc`, как обещает нынешняя подпись общей панели. Это также исправит несовпадение default ordering и label у Event. Некорректный ключ не должен превращаться в ORM field lookup или `?e=1`.
- Активный пункт и текущая подпись соответствуют фактической сортировке. Строки labels использовать уже существующие из Place sort catalogues; без новых msgid/PO/MO в checkout.
- `q`, разрешённые штатные фильтры и scope queryset сохраняются; выбор новой сортировки сбрасывает только pagination через существующий cl_sort_url. Pagination/reload сохраняют валидный sort. Не затрагивать unpublish/publish/dialogs/row menus.

## Проверка после approval

1. Fresh snapshot/active_run/source; сохранить чужой dirty WORKTREE. Проверить принадлежность/изоляцию своего QA profile, source953+own3MO. При stale profile создать новый; production/.env не использовать.
2. До patch написать и выполнить6тестовых методов. Seed fictional rows с независимо заданными created/updated dates и canonical names, неодинаковым порядком и ties. Проверить6ключей×2модели; q+status filters; active labels RU/AZ/EN; default+invalid fallback; pagination reset/preservation; view/no-view ACL и неизменность данных. Зафиксировать ожидаемый RED, исправлять fixture/harness отдельно от source assertion.
3. Применить минимальный helper и точечное подключение двух admins. Проверить GREEN targeted methods + затронутые существующие admin/read-only/private-document ACL scenarios. Точный перечень существующих labels выбрать по impact, не весь корпус модуля.
4. Native keyboard/click search→6sort choices→pagination/reload→reset, RU/AZ/EN ×360/390/768/1024/1280/1440, expanded/collapsed sidebar там, где фон доступен. Сравнивать реальные visible IDs/order, q/filters/current label, не только HTTP200. Console/network/PNG manifest/source process/domain unchanged.
5. Краткий smoke row menus после изменений admin response context, не повторять без причины весь1121CSS/1191menu корпус. Старые source FAIL сохранять, закрывать только фактически проверенную причину. Новая причина/расширение требует отдельного согласования.

Unmatched column controls Event/Specialist остаются отдельным OPEN/NOTRUN support gap, не входят в этот patch. MOD04–08/full08/global/production/commit/push/deploy не разрешаются этим планом. Полный модуль08 — один раз после всех его задач.

До отдельного approval: **implementation/test module creation/postpatch GREEN NOT RUN**, приложение backend0changes. Нужен approval только нового4file scope, ранее одобренные CSS/JS-menu повторно не согласовывать.
