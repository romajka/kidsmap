# SITE-QA-09 — OFF мероприятий оставляет публичный direct URL legacy temporary Place

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application visibility failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin / guest. **URL/endpoint:** `/admin/catalog/sitevisibilitysettings/1/change/; canonical /place/6-…/`.

**Шаги:** На начальной вымышленной опубликованной temporary Place включить events OFF через settings UI. Каталог/map скрывают Place6; открыть его canonical URL RU/AZ/EN во всех ширинах. Вернуть ON.

**Ожидание:** Публичный direct URL также скрыт при OFF, как каталог и map.

**Факт:** Все 18 OFF direct checks получают 200; каталог/map корректно исключают ID6. ON снова показывает карточку. Данные объектов сохраняются.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: скрытый раздел остаётся доступен по прямой ссылке, контракт публичной видимости непоследователен.

**Первопричина / гипотеза:** Подтверждено: public detail использует published_place_queryset без events flag; strict catalog/map queryset исключает is_temporary при OFF.

**Source:** `src/catalog/controllers/place_controller.py:678`; `src/catalog/services/content_quality.py:278`; `src/catalog/services/content_quality.py:361`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [flags.result.txt](../flags.result.txt)
- [extra-fixtures.json](../extra-fixtures.json)
- [current-boundary.result.txt](../current-boundary.result.txt)

**Область исправления:** Единый flag/availability contract для legacy temporary detail без смешения OFF с unpublish/archive/delete. Не менять данные карточки для имитации скрытия.

**Владелец / зависимости:** Features/public queryset/canonical URL; map/catalog/direct + ON roundtrip, исторические legacy правила.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-09-repair.txt). Аудит ничего не исправляет.
