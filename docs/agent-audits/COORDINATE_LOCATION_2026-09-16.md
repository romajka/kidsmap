# Координаты → город и район: реализация 2026-09-16

Mode: APPROVED IMPLEMENT, авторизация пользователя «делай» после согласования плана. Execution: основной агент, без независимых специалистов. Исходный LOCAL HEAD `f8005bb0a2308588b183a09890f35b659bc3f44f`; изменения приложения находятся в dirty WORKTREE. Предыдущие изменения readiness, форм, CSS и SEO-отчётов сохранены. Commit/push/deploy не выполнялись. PRODUCTION: версия и запись музея не проверены; записей на production нет.

## Что изменено

- `services/district_geometry.py`: immutable LocationResolution и единая offline-проверка Polygon/MultiPolygon, holes, границ, перекрытий, NaN/Infinity и покрытия. Совпадение нескольких районов и близость к сегменту до 1e-6 градуса дают ambiguous. Порядок features больше не выбирает район. Погрешность алгоритма не объявляется геодезической точностью источника.
- `services/location_assignment.py`, `models/place.py`, `services/locations.py`: серверная нормализация города/района; частичные сохранения lat/lng используют фактически записываемую пару. Перенос точки аннулирует прежнюю привязку. Формы отклоняют явно противоречащий ручной выбор; неизменённое старое значение при переносе заменяется автоматически. Обход браузера не позволяет сохранить старый район с новой точкой.
- `0114_coordinate_location`: отдельные city, resolution status/version; журнал PlaceLocationOverride с одним текущим исключением. Legacy строки не массово переписываются. Существующие district keys и фильтры сохранены. Resolver не зависит от Place и пригоден для будущего Branch; модель Branch не вводилась.
- Ручное исключение требует `catalog.override_place_location`, active staff, отсутствия volunteer-role, причины и корректных координат. Actor берётся из request, а не POST. Запись исключения и Place сохраняются в одной транзакции. Перенос точки отменяет исключение; новая версия геоданных делает прежнее исключение недействительным при перепроверке.
- Owner/admin/volunteer формы используют общий контракт. Предложение волонтёра остаётся приватным и может быть неполным; модерация повторно проверяет географию перед публикацией. Существующая защита версии volunteer revision сохранена.
- `controllers/location_resolution.py` и `static/js/location_resolution.js`: авторизованный preview без записи, отдельный admin URL для корректной работы разных доменов. UI обновляется на события обоих map pickers, ручной ввод и импорт; есть loading, unknown, boundary, network failure. Порядковый номер запроса и abort защищают от позднего ответа. Причина исключения сбрасывается при переносе. Метро не стирается промежуточным состоянием загрузки.
- Переводы AZ/RU/EN, status/aria-live; ручное исключение спрятано в доступный с клавиатуры details. Язык preview задаётся языком редактора, поэтому английский admin не получает русские подписи.
- Server geocoding опубликованного места не переносит точку за известное покрытие с устаревшим районом: возвращает location_unresolved, сохраняя прежнюю пару координат. Черновики могут иметь неопределённую географию; новая публикация/перенос опубликованной точки требует определённого района либо привилегированного исключения.

## Геоданные

Покрытие: **12 районов Баку**, а не все города страны. Другие территории возвращают outside_coverage; город не угадывается по адресу. Для дальнейшего покрытия нужны проверенные городские полигоны и иерархия территорий.

Источник: [государственный портал IDDA / REİS](https://opendata.az/en/@azerbaycan-respublikasinin-ekologiya-ve-tebii-servetler-nazirliyi/azerbaycanin-rayonlari), resource updated 2025-07-22. CKAN package metadata проверены 2026-09-16: `license_id=cc-by`, Creative Commons Attribution. Метаданные источника и SHA256 исходного/нормализованного файла сохранены в `src/catalog/data/administrative_boundaries_manifest.json`.

QA геометрии через отдельную scratch-установку Shapely выявил self-touching rings у Qaradağ, Səbail, Xətai. `make_valid` применён только к этим features; изменение площади на уровне машинного округления. Проверены все 12 результирующих геометрий. Реальные перекрытия между районами сохранены и перечислены в manifest; runtime возвращает ambiguous, а не присваивает такие зоны произвольно. Shapely не добавлен в production dependencies.

Воспроизводимость нормализации: взять исходный GeoJSON из указанного LOCAL HEAD, сверить source_sha256, для каждого невалидного `shape(feature['geometry'])` применить `mapping(make_valid(geometry))`, сериализовать JSON с `ensure_ascii=False, separators=(',', ':')` и завершающим LF. Сверить итоговый sha256 из manifest. Не упрощать контуры и не удалять перекрытия без отдельного исследования.

## Проверки

Окружение изолировано: env -i, DJANGO_TESTING=1, disposable SQLite и отдельный PostgreSQL 17 в контейнере `kidsmap-geo-tests-20260916`, tmpfs DB; собственные тестовые credentials, LocMem cache/email, отдельный MEDIA_ROOT, внешние интеграции выключены. Реальный Google API не вызывался. Scratch runners и логи находятся в ignored `.tmp/coordinate-location/`.

Выполнено:

- RED → GREEN для resolver, сохранения/форм, authenticated preview, корректировки записи, языка admin preview, поздних ответов JS и проверки версии исключения.
- `.tmp/coordinate-location/run-postgres test catalog.testcases.test_location_resolution catalog.testcases.test_location_assignment catalog.testcases.test_location_correction --noinput`: финальный результат см. execution footer ниже.
- PostgreSQL: 112 тестов resolver/assignment/correction/card validation/volunteer/JSON integration — PASS. После последующих исправлений отдельно 66 тестов location + volunteer + location readiness — PASS. Эти прогоны перекрываются; их числа не суммируются.
- HTTP admin round-trip: привилегированное исключение с причиной сохраняется, следующий перенос точки отменяет его. Недостаточный permission не показывает override control. Проверен единственный control в add/edit (исправлен обнаруженный duplicate).
- `node --test scripts/test_location_resolution.cjs`: 4 PASS. jsdom установлен только в ignored scratch; можно задать KIDSMAP_JSDOM с путём к своей установке.
- `.tmp/coordinate-location/run-postgres test catalog.testcases.owner catalog.testcases.place_readiness --noinput`: 186 тестов, 6 failures, совпадают с воспроизведённым исходным WORKTREE. Пять проверок ожидают русские строки при активном AZ; одна ожидает прежнее обязательное description_az. Assertions этих baseline failures не менялись.
- Для baseline создан отдельный scratch source snapshot без этой функции, с сохранёнными предшествующими dirty readiness/form/test правками и теми же locale catalogs. На нём воспроизведены те же шесть failures. Новые contract fixtures приведены в соответствие географии; координатные assertions и проверки доступа сохранены. Старый тест разрешения чужого города волонтёру заменён тестом отказа и автопереназначения района по новой точке.
- `makemigrations --check --dry-run`: no changes; `check`: no issues; `git diff --check`: PASS.
- PostgreSQL migrations: полный migrate, обратный `migrate catalog 0113`, повторный `migrate catalog 0114` — PASS на disposable DB. Откат production потребует отдельного решения о сохранении нового журнала исключений.

Browser QA: Playwright/Chromium, настоящий локальный сервер и fixture users; проверены редакторы admin/owner/volunteer, смена координат и unknown, языковые маршруты AZ/RU/EN, ширины 390/768/1024/1280/1440. Существующая admin language policy выводит RU на unprefixed/AZ admin; EN теперь отдаёт английские подписи. Runtime JS exceptions: 0. Проверено отсутствие override у owner/volunteer. Просмотрены desktop admin и mobile owner/volunteer screenshots. Для тестирования координат использованы DOM input/change events; drag Google/Leaflet с живым провайдером не проверялся (ключи отключены).

Известная граница browser QA: на owner AZ/RU при 1024 px шапка сайта шириной 1049 px. При скрытии нового resolver-блока ширина остаётся 1049 px; выступают существующие `.km-header-inner` / `.km-header-actions`. Новые блоки не выходят за экран. Шапка не менялась в этой задаче. Начальные 404 fixture photo устранены созданием тестового изображения; это не production media issue.

## Музей: исправление подготовлено, не применено

Нужная привязка — **Баку / Сабаильский (`baku_sabail`)**. [Сайт Сабаильской администрации](https://sabail-ih.gov.az/page/16.html) перечисляет музей по Niyazi 9/11; [официальный сайт музея](https://www.nationalartmuseum.az/?lang=ru) подтверждает адрес в Баку.

В локальной SQLite и локальном kidsmap-postgres целевая запись не найдена по вариантам названия. PostgreSQL проверялся явной READ ONLY transaction с statement_timeout=15s и lock_timeout=2s. Мокапный ID 320 не использован как идентичность настоящей записи. Фактические production ID/координаты/старый район остаются UNKNOWN.

`correct_place_location` реализован с нулевой записью по умолчанию. Требует точный place-id и ожидаемые прежние city/district/lat/lng. `--apply` дополнительно требует staff actor с change_place; повторное применение — no-op, конкурентное изменение — отказ. Применение меняет только привязку и создаёт audit; активное ручное исключение не перезаписывается.

Следующий разрешённый шаг для live-исправления: сначала установить точную запись и её координаты через read-only проверку, получить before/after preview; затем отдельное разрешение на production изменение, поскольку согласованный план сохраняет production read-only. Автоматически менять координаты музея по тексту адреса команда не пытается.

## Остаток и выпуск

- Локальная реализация требует migration 0114, доставки обновлённых static и компиляции переводов при отдельном согласованном release.
- Нет массового backfill/массового снятия legacy карточек с публикации.
- Нет deployment, production correction, live map provider QA или полного национального покрытия.
- Обычные QuerySet.update/bulk_update из доверенных внутренних скриптов не вызывают Model.save: новым импортерам следует пользоваться save/shared assignment. Действующие UI/save/геокодирование пути проверены; прямой SQL не объявляется защищённым ORM-hook.

## Execution footer

Финальный targeted прогон на PostgreSQL: **22/22 PASS**, Node: **4/4 PASS**. Все 12 нормализованных геометрий повторно проверены Shapely, SHA256 совпадает с manifest. Browser add-flow отдельно проверен в EN для admin/owner/volunteer: новая точка → Baku/Sabail, затем outside_coverage → пустой district; override отсутствует у owner/volunteer. Фактический drag живого map provider остаётся NOT RUN. Последний широкий owner/readiness прогон имеет только шесть воспроизведённых baseline failures.

## Visual follow-up — shared location explanation

User authorized a visual and accessible explanation across owner/public, volunteer and staff editors, with targeted verification only.

- Shared `location_resolution.html` now shows a three-step map pin → city → district result, with responsive layout and localized AZ/RU/EN instructions.
- Scoped `static/css/components/location_resolution.css` uses the KidsMap green token, a subtle loading spinner and step pulse, explicit textual unresolved/override states, and `prefers-reduced-motion` support.
- Preview JS clears displayed values while resolving a moved point and offers an accessible retry button on service/network failure. Existing server assignment and permissions are unchanged.
- Compact admin navigation no longer sticks over the location result when its links wrap into a grid.
- Browser inspection caught an existing translation-key collision for “Точка на карте”; the new component uses the unambiguous “Метка на карте” key instead.

Targeted verification (isolated local SQLite fixture server, no production credentials):

- `node --test scripts/test_location_resolution.cjs`: 5 passed, including stale responses, cleared coordinates, unknown coverage, override version and visual clearing/network retry.
- `node --check static/js/location_resolution.js`, `git diff --check`: passed.
- `.tmp/coordinate-location/browser-polish.cjs`: all three create editors, AZ/RU/EN, widths 375/768/1024/1440; block fits every viewport, unknown result clears district, no JS page errors.
- `.tmp/coordinate-location/browser-polish-edit.cjs`: all three edit editors in RU at the same widths; loading animation is `km-location-spin`, reduced-motion animation is `none`; no JS page errors. Mobile screenshots inspected directly.
- Existing unrelated owner header overflow at 1024 in AZ/RU persists (previously reproduced with the location block hidden); the location component itself has no overflow.
- Actual Google map dragging remains untested because the isolated fixture has no map API key; coordinate input/change events exercise the real resolution endpoint.

No full test suite, production changes, deployment or museum data mutation in this visual follow-up.
