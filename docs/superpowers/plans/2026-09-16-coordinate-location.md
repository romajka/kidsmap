# Coordinate-based City / District Implementation Plan

> **For agentic workers:** Execute task-by-task after scope approval. Use available project skills; do not install missing execution skills or dispatch agents automatically.

**Goal:** При выборе координат определять город и административный район, исключить сохранение устаревшего района и исправить привязку Национального музея искусств.

**Architecture:** Один серверный resolver координат по версионированным административным полигонам. Preview в интерфейсе и проверка при сохранении используют один контракт. География принадлежит физической локации; будущий Branch сможет использовать тот же сервис без зависимости от Place.

**Tech Stack:** Существующие Python/Django, GeoJSON, JavaScript, Google/Leaflet map pickers. Новый GIS runtime не требуется до оценки топологии и нагрузки.

**Spec:** Требования пользователя от 2026-09-16 сохранены в критериях ниже.

## Global constraints / статус

- AUDIT / PLAN, реализация ещё не одобрена. Ни application edits, ни commit/push, ни production writes в этом проходе.
- LOCAL HEAD: `f8005bb0a2308588b183a09890f35b659bc3f44f`. WORKTREE уже содержит чужие изменения forms/admin/readiness/volunteer/UI и отчётов; сохранить и перечитать их перед реализацией.
- PRODUCTION: UNKNOWN, подключение и изменение карточки музея не выполнялись.
- Выполнено чтение source, метаданных GeoJSON и официальных web-источников. Codebase Memory доступен, индекс ready для данного root; актуальность dirty файлов не доказана, критические выводы проверены по source. Это не независимый командный аудит.
- Django tests и browser QA не запускались: приложение не менялось. Команда `python` отсутствует; для инспекции JSON использован `python3`.
- Тесты реализации: DJANGO_TESTING=1, отдельная disposable DB/media, LocMem cache/email, без production credentials и внешних интеграций.

## Подтверждённый source и проблемы

1. `src/catalog/services/district_geometry.py:district_for_coordinates` уже читает Polygon/MultiPolygon и учитывает holes. Возвращает первый подходящий район, не различает границу, перекрытие и отсутствие покрытия. P2: результат на спорных координатах не имеет явного контракта.
2. `src/catalog/data/baku_districts.geojson`: 12 районов Баку, source_updated=2025-07-22. Источник — государственный портал: https://opendata.az/en/@azerbaycan-respublikasinin-ekologiya-ve-tebii-servetler-nazirliyi/azerbaycanin-rayonlari . Страница подтверждает GeoJSON и издателя REİS; это ещё не проверка точности каждой границы или лицензии повторного распространения.
3. `services/place_card_validation.py:validate_place_card`: mismatch — warning, только когда ручной район начинается с baku_, и фактический район найден. `domain_admin/place.py` при запросе verification прикладывает warnings; обычное сохранение не получает обязательной географической нормализации. P2: ручное несовпадение остаётся допустимым.
4. `services/locations.py:clean_location_fields` проверяет сочетание region/district, но не координаты. `Place.district` хранит либо район Баку, либо регион; отдельного city нет. Нельзя объявлять любой район Азербайджана городом.
5. `static/admin/js/kidsmap_place_location.js:setPoint` меняет lat/lng и отправляет km:location-change; reverse geocode заполняет адрес. `static/admin/js/kidsmap_place_form.js` прямо помечает district-auto UI как будущую функцию.
6. Owner использует `static/js/owner_place_map_picker.js`; volunteer/edit.html подключает этот же picker. Валидацию нужно подключить также к volunteer revision apply, а не только preview формы.
7. `src/catalog/testcases/place_card_validation.py:test_offline_baku_polygon_lookup_detects_district_mismatch` покрывает один interior point и warning; это не тест автозаполнения или границ.

## Решения для согласования

- При однозначном результате город/район заполняются автоматически; сервер пересчитывает их из фактически сохраняемых координат независимо от POST preview.
- Обычный пользователь/волонтёр не может сохранить противоречащий географии ручной выбор. Возвратить field error с найденным районом; без ручного конфликта автоматически записать результат.
- Исключение разрешено только отдельным permission администратора, с обязательной причиной и audit trail: actor/time, координаты, автоматический результат, ручные значения, версия dataset. Любая смена координат аннулирует исключение; обновление dataset помечает исключения для пересмотра.
- Состояния: resolved, ambiguous, outside_coverage, invalid_coordinates, unavailable. На общей границе или при нескольких совпадениях — ambiguous, без выбора первого полигона. Геометрическая численная погрешность и точность исходных границ должны быть описаны отдельно.
- При переносе точки сразу сбрасывать автоматические значения и старое исключение. Пока запрос идёт: «Определяем город и район…». Поздний ответ на старые координаты игнорировать.
- Если район неизвестен: «Не удалось определить район. Проверьте точку или отправьте на проверку». Черновик сохраняется без старого района; публикация новой/изменённой локации требует resolved либо административного исключения. Для существующих опубликованных мест не запускать массовую блокировку при редактировании несвязанных полей; legacy состояние показывать явно, а изменение координат всегда включает новый контракт.
- Подтверждённое покрытие первой поставки — Баку. Для остальных городов добавить проверенные городские и районные полигоны как отдельный dataset, с parent mapping; отсутствие покрытия не скрывать под обещанием определения города. Полное покрытие страны пока не подтверждено.
- Добавить `Place.city` (канонический ключ, blank допустим для неизвестного), `location_resolution_status`, `location_dataset_version`. Сохранить существующее district-хранилище/фильтры совместимыми; не мигрировать весь каталог автоматически. Override хранить отдельной записью с permission и причиной. Физический Branch не создавать в этой задаче.

## Task 1 — Достоверность и контракт геометрии

Files: modify `src/catalog/services/district_geometry.py`; create `src/catalog/data/administrative_boundaries_manifest.json`, `src/catalog/testcases/location_resolution.py`.

Interface: `resolve_location(lat, lng) -> LocationResolution(status, city_key, district_key, candidates, dataset_version)`; result immutable. Existing `district_for_coordinates` remains compatibility wrapper returning district only for resolved.

- [ ] Проверить все 12 нормализованных keys, закрытые кольца, holes, MultiPolygon, самопересечения и перекрытия; manifest содержит источник, дату получения, checksum, CRS, покрытие и условия использования. Не заменять реальные полигоны прямоугольниками.
- [ ] Написать failing unit cases: interior двух районов, hole, остров, общая вершина, shared edge, overlapping polygons, outside coverage, missing/NaN/infinity/out-of-range/reversed input.
- [ ] В synthetic fixtures использовать два смежных квадрата и точку на общей границе; результат должен быть ambiguous независимо от порядка features.

```python
# Контракт тестов будущего resolver, без обращения к БД.
r = resolve_location(40.4093, 49.8671)
assert (r.status, r.city_key, r.district_key) == (
    'resolved', 'baku', 'baku_narimanov')
assert resolve_location(float('nan'), 49.8).status == 'invalid_coordinates'
assert resolve_location(0, 0).status == 'outside_coverage'
```

- [ ] Реализовать сбор всех совпадений и явную обработку point-on-segment до ray casting. Ошибка загрузки набора возвращает unavailable, не случайный район.
- [ ] Выполнить unit cases; отдельно зафиксировать лицензию и точность. Если источник нельзя подтвердить, не включать автоматическую авторитетную запись до устранения проблемы.

## Task 2 — Серверный контракт и схема

Files: modify `src/catalog/models/place.py`, `src/catalog/services/locations.py`, `src/catalog/services/place_card_validation.py`, `src/catalog/forms.py`, `src/catalog/domain_admin/place.py`, `src/catalog/volunteer_forms.py`, `src/catalog/services/volunteer_editor.py`; create `src/catalog/services/location_assignment.py`, `src/catalog/models/location_override.py`; expose model in `src/catalog/models/__init__.py`. Generate next migration after inspecting current migration leaves; do not reserve a colliding number.

Interface: `prepare_location_assignment(*, lat, lng, submitted_city, submitted_district, actor, override_reason, previous_location) -> assignment`; actor/permission supplied by server, never trusted POST. Assignment includes resolution and canonical persisted values.

- [ ] Add failing create/edit tests for staff, owner and volunteer; forged district, city, status, version and override permission; draft and publication tested separately.
- [ ] Add nullable/blank-compatible metadata, explicit override permission and audit model; migrate only schema, no guessed city backfill.
- [ ] Route each form save and volunteer revision acceptance through shared assignment. Readiness and verification consume its result, not a second geometry implementation. Inspect CSV/JSON import and geocode_places coordinate writes; integrate the same contract there so they cannot leave stale district.
- [ ] Test save without JavaScript and direct POST; changing coordinates cannot persist previous district. On validation error no partial coordinate or override writes.
- [ ] Test stale volunteer revision and concurrent edit: compare current coordinate/version under transaction before accepting revision. Changed dataset requires recomputation.
- [ ] Check migration reversal, filters using legacy district keys, and unrelated legacy edit compatibility on isolated DB.

## Task 3 — Preview и интерфейсы

Files: create `src/catalog/controllers/location_resolution.py`, `static/js/location_resolution.js`; modify `src/catalog/urls.py`, `static/admin/js/kidsmap_place_location.js`, `static/js/owner_place_map_picker.js`, `static/admin/js/kidsmap_place_form.js`, `src/catalog/templates/admin/catalog/place/form/section_location.html`, `src/catalog/templates/pages/includes/owner_place_wizard.html`, `src/catalog/templates/admin/volunteer/edit.html`; add AZ/RU/EN translations in existing locale catalogs.

Interface: authenticated GET `/location/resolve/?lat=…&lng=…` returns status, canonical keys, translated labels, dataset_version and echoed coordinates. No writes, arbitrary outbound URL or address-text district inference.

- [ ] Test permission parity with editors, malformed input, unavailable dataset and absence of writes.
- [ ] Implement shared request controller with abort plus sequence counter; attach all click/drag/search/geolocation/manual-coordinate/clear/import paths in both map pickers.
- [ ] Display loading/resolved/ambiguous/unknown/network-error states in an aria-live region; preserve keyboard access, show override only for authorized admin. City and district update together.
- [ ] Test A→B rapid drag with A response arriving last; submit while preview pending must still use server resolution for B.
- [ ] Browser acceptance: add/edit in staff, owner, volunteer; AZ/RU/EN and widths 390/768/1024/1280/1440; inspect console/network, focus and error rendering. Source inspection does not count as browser QA.

## Task 4 — Музей и проверка данных

Files: create `src/catalog/management/commands/correct_place_location.py`, `src/catalog/testcases/location_correction.py`.

Verified intended target: Баку / Сабаильский, canonical district `baku_sabail` (verify spelling against locations map before implementation). Official district administration lists Art Museum at Niyazi 9/11: https://sabail-ih.gov.az/page/16.html . Museum confirms Baku and Niyazi 11/9: https://www.nationalartmuseum.az/?lang=ru . This is evidence for this specific correction, not a text-based resolver.

- [ ] Read-only identify actual catalog record using name + address + coordinates; design mock ID 320 is not production identity evidence. Multiple matches → manual review.
- [ ] Prepare exact before/after district/city/coordinates and resolver result. If map point is wrong, verify museum point before proposing coordinate correction; do not invent it from address.
- [ ] Command defaults to zero-write preview. Apply requires explicit ID and expected previous values; transaction checks match and modifies only location fields/metadata, with audit record. Repeated apply is a no-op; concurrent change stops it.
- [ ] Test no-match, duplicate identity, expected-value conflict, idempotency and rollback on isolated fixtures.
- [ ] Production correction is pending separate authorization lifting current read-only restriction; after apply verify public labels and district filter. No mass backfill or mass unpublish in this scope.

## Acceptance / handoff

All user requirements map to Tasks 1–4: point-based city/district, recomputation, visible results, controlled exception, stale district prevention, create/edit, Branch-compatible service, boundaries and unknown coverage, museum correction. Countrywide city accuracy is a data coverage dependency, not an implemented guarantee.

Next: approve this concrete scope, then implementation with failing regression tests first. Before completion record exact isolated commands/results, migrations, browser evidence, actual dataset coverage and museum correction status. Commit/push/deploy are outside approval of local implementation unless expressly included.

## Реализация после согласования

2026-09-16 пользователь подтвердил scope сообщением «делай». Локальная реализация и проверки описаны в [отчёте](../../agent-audits/COORDINATE_LOCATION_2026-09-16.md). Production read-only сохранён: live-исправление музея и release не выполнялись. Точная production запись музея не установлена; команда исправления готова и протестирована. Чекбоксы выше — исходный план, фактические результаты и ограничения находятся в отчёте.
