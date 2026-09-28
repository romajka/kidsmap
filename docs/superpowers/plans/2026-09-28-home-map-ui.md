# Home map UI Implementation Plan

> **For agentic workers:** Execute the approved tasks sequentially in the current session. No delegation is needed.

**Goal:** Сделать блок карты визуально цельным, с понятными фильтрами и спокойной анимацией взаимодействий.

**Architecture:** Сохранить SSR-разметку и существующую клиентскую фильтрацию. Изменить только представление блока и обратную связь существующих обработчиков; использовать текущие CSS tokens и data-атрибуты.

**Tech Stack:** Django templates, CSS, vanilla JavaScript, существующая Google Maps integration.

**Spec:** Визуальный screenshot пользователя и решения ниже.

## Scope и исходное состояние

LOCAL HEAD: `07abeae33ae1deadf8d77dcfd854c54f9566980f`. WORKTREE содержит существующие изменения в home_controller.py, locations.py, public_filter_options.py, home.html, home_redesign.css, home_map.js. Реализация должна сохранить эти изменения. Production UNKNOWN; не обращаться к production.

Сейчас согласуется план. Application code не изменён. По AGENTS.md реализация требует подтверждения конкретного scope. Без commit/push/deploy, backend-изменений и новых библиотек.

## Дизайн

- Белая поверхность, существующий фирменный зелёный, один мягкий внешний контур. Ослабить вложенные рамки и тени.
- Короткий заголовок «Детские места на карте»; описание «Выберите район, занятие и возраст ребёнка». Эквивалентные AZ/EN строки.
- Каталог — вторичная текстовая ссылка со стрелкой. «Показать на карте» — единственная основная зелёная кнопка.
- Поиск: высота 48–52px, спокойный фон, заметный focus. Под ним район, категория и подписанная группа «Возраст»; выбор возраста сохраняет текущий смысл backend-данных.
- Счётчик результатов расположить в отдельной компактной строке перед картой, рядом с подсказкой «Нажмите на метку, чтобы открыть место». Сохранять текущий data-home-map-live-count.
- Сброс сохраняет место в компоновке, выглядит вторичным действием; выбранные фильтры явно выделены.
- На телефоне поиск и основная кнопка занимают полную ширину, район и категория располагаются вертикально, возраст переносится без горизонтального overflow. Минимальная зона нажатия 44px.

## Motion

- Hover/focus: переход цвета и контура 160–180ms; без изменения размеров.
- Dropdown: opacity и translateY до 4px, 160ms. Существующие hidden, keyboard и outside-click должны работать без задержки.
- Выбор возраста: фон/цвет 160ms, без прыжков компоновки.
- Счётчик: одно краткое выделение только при изменении количества, 180ms; не анимировать цифры через промежуточные ложные значения.
- Убрать бесконечную пульсацию статуса. Не скрывать карту при фильтрации, не делать декоративные прыжки маркеров.
- prefers-reduced-motion отключает движение; scrollToMap использует auto вместо smooth при этой настройке.

## Task 1: Композиция и responsive

**Files:** `src/catalog/templates/pages/home.html`, `static/css/pages/home_redesign.css`.

**Interfaces:** Сохранить IDs карты и формы, имена полей, data selectors, form action и существующие dropdown contracts. CSS ограничить home-map-panel; остальные блоки homepage не затрагивать.

- [ ] Обновить header, AZ/RU/EN copy и расположение счётчика.
- [ ] Сделать каталог вторичным действием и выровнять поиск/фильтры по единой сетке.
- [ ] В существующих правилах блока устранить конкурирующие тени/рамки; использовать var(--home-green), var(--home-ink), var(--home-muted).
- [ ] Настроить вертикальную mobile-компоновку и touch targets; сохранить видимые focus indicators.
- [ ] Проверить в браузере длинные labels и открытые меню; исправить обрезание/overflow до следующей задачи.

## Task 2: Анимация и состояния

**Files:** `static/js/home_map.js`, `static/css/pages/home_redesign.css`.

**Interfaces:** Использовать существующие updateLiveCount, bindFilterListeners, scrollToMap. Сохранить debounce 120ms, фильтрацию, карту, clustering и открытие popup.

- [ ] Добавить ограниченные transitions для hover, выбора и dropdown.
- [ ] В updateLiveCount запускать одно выделение только если текст количества действительно изменился; повторный update с тем же количеством не анимировать.
- [ ] Устранить бесконечную пульсацию; в reduced-motion отключить motion и smooth scroll.
- [ ] Проверить поиск, autocomplete, район, категорию, возраст, reset, submit и открытие маркера. Проверить нулевой результат и existing map fallback.

## Verification / acceptance

- [ ] `node --check static/js/home_map.js`.
- [ ] `git diff --check` и scoped diff: изменения только трёх согласованных application files, существующие изменения сохранены.
- [ ] Rendered browser: AZ/RU/EN на 360, 390, 768, 1024, 1280, 1440px; screenshot desktop/mobile.
- [ ] Проверить keyboard/focus, закрытие меню, отсутствие горизонтального overflow, console и static404.
- [ ] Проверить prefers-reduced-motion: нет пульсации, движущихся dropdown и smooth scroll.
- [ ] Проверки только на изолированном локальном окружении. Для Django checks/tests обязательны DJANGO_TESTING=1, disposable DB/cache/media/email и отключённые external integrations.

Source inspection и screenshot пользователя не заменяют rendered browser verification. На стадии плана runtime проверки не запускались. План требует проверки результата после реализации, а не утверждает готовность интерфейса.

## Реализация и проверка — 2026-09-28

Пользователь подтвердил scope: «давай делай». Локальные изменения этой задачи: home.html, home_redesign.css, home_map.js. Существующие изменения WORKTREE сохранены; backend, production, commit/push/deploy не затронуты.

Реализованы композиция, краткие AZ/RU/EN тексты, вторичная ссылка каталога, строка результатов, подписанный возраст, touch targets, responsive-сетка и focus. Motion ограничен короткими переходами и выделением реально изменившегося числа. Reduced motion отключает CSS-анимации и smooth scroll. Исправлен визуальный reset категории: сброс вызывает существующий change handler, восстанавливающий icon, selected state и aria-selected. До исправления браузерная проверка воспроизвела сохранённое выделение после reset; после исправления проверка проходит.

Проверки (exit 0):

- `node --check static/js/home_map.js`.
- `node .tmp/home-map-ui/motion-check.cjs`: unchanged count, changed count, reduced counter, reduced scroll, normal scroll.
- `git diff --check`.
- `/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/verify.js`: 18 layouts (AZ/RU/EN × 360/390/768/1024/1280/1440), touch targets, overflow, search/empty/reset, age, category selection/reset icon, district menu/Escape, clear, input focus и reduced motion. JS page errors: 0; static404: 0.
- `/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/final-check.js`: mobile dropdown width, marker popup и reduced-motion scroll.

Скриншоты: `output/playwright/home-map-desktop.png`, `output/playwright/home-map-mobile.png`; просмотрены визуально. Локальный preview: `.tmp/home_map_ui_preview.py`, DJANGO_TESTING=1, отдельная копия demonstrational SQLite DB, in-memory cache, fixture media, отключённые Google credentials и IndexNow. Только копия fixture DB приведена к текущим локальным миграциям.

Границы доказательств: Google Maps provider и production не проверялись; полный Django suite не запускался, backend не изменялся. Leaflet проверен с реальной библиотекой и demo-маркерами; CDN-файлы поданы через browser fixture с сохранением исходных байтов для integrity. В существующем fallback bootstrap Leaflet data attributes читаются с map element, а template размещает их на script; тестовая HTML fixture копирует конфигурацию на map element до bootstrap. Этот ранее существовавший дефект подключения не исправлялся в визуальном scope. Поэтому browser PASS доказывает дизайн и работу фильтров/кластеров с provider fixture, но не самостоятельный запуск fallback из исходной страницы без Google key.

### Follow-up: dropdown перекрывался картой

Пользователь прислал screenshot с категорией за Google Maps. В изолированном браузере воспроизведено перекрытие: `elementFromPoint` на видимой нижней части category menu возвращал элемент другого слоя; regression `layer-check.js` упал на 390px. Причина: stacking context строки фильтров (transform/backdrop effects) и следующий позиционированный map container. Исправление только в presentation: search deck получает position:relative/z-index:2, map получает z-index:0; карта изолирует внутренние provider layers. CSS cache version обновлена.

Проверка: `/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/layer-check.js` — exit0, category и district menus видимы и доступны для hit-testing на 1440/1024/390/360px. `git diff --check` — exit0. Screenshot: `output/playwright/home-map-menu-layers.png`. Google provider на пользовательском localhost не использован; проверка на ранее описанной Leaflet fixture.

### Follow-up: двойная очистка поиска

Screenshot пользователя показал нативный cancel control input[type=search] рядом с custom clear button. Scoped CSS скрывает WebKit search decorations; custom clear использует SVG того же stroke-семейства, 44px touch target, нейтральное состояние и зелёный hover. Input focus теперь использует один 3px мягкий ring вместо одновременных outline и shadow. CSS cache version обновлена.

`playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/clear-check.js` — exit0 на 1440/390px: одна custom SVG, suppression rule, единый focus ring, mouse clear, скрытие пустой кнопки, возврат фокуса в input, Tab и Enter для keyboard clear. `getComputedStyle` внутреннего browser search decoration не отражал suppression; наличие единственной иконки проверено визуально по `output/playwright/home-search-input.png` и desktop/mobile screenshots `home-search-1440.png`, `home-search-390.png`. На локальном preview отключён template autoreload, поэтому только этот изолированный процесс перезапущен для загрузки свежей SVG-разметки. Production и пользовательский процесс 8000 не затронуты. `git diff --check` — exit0; JavaScript не менялся в этом follow-up.

### Follow-up: поднять карту

Убрано суммирование унаследованного grid gap:18px и собственных нижних margins header/search/results. Scoped home-map-panel теперь gap:0; внутренние margins и размеры controls сохранены. CSS cache version обновлена. Browser измерение на 1440px: map offset относительно панели 469.296875 → 415.296875px, карта поднялась на54px. Проверены 1440/390px: gap0, horizontal overflow false. Screenshot `output/playwright/home-map-compact.png` просмотрен. `git diff --check` — exit0.

### Read-only проверка логики фильтров

Запрос пользователя: проверить полную корректность category/district/age. Application code в этом follow-up не менялся. Snapshot тот же LOCAL HEAD с ранее указанным dirty WORKTREE; production UNKNOWN.

`node .tmp/home-map-ui/filter-audit.cjs` — exit0: 10 стандартных assertions на реальные функции из home_map.js (без переписывания predicate), включая exact category, AND-комбинацию, границы возраста и открытые диапазоны. Воспроизведены расхождения на synthetic данных:

- `isPlaceInBaku` допускает координатный rectangle 40.20–40.70 /49.50–50.50 даже при явно указанном другом городе. Synthetic Sumgait (40.589/49.668, district=sumgait) проходит filter district=baku. Source: home_map.js:isPlaceInBaku/placeMatchesFilters.
- Явный district=baku_yasamal не защищает от совпадения другого района по search_text. Synthetic адрес с Narimanov street проходит filter baku_narimanov. Source: placeMatchesFilters, matchesText/matchesLabel OR exact key.
- Age chip «6+» проверяет возраст ровно6 (selectedAge внутри [age_from,age_to]); synthetic диапазон8–12 исключается. Точное совпадение возраста соответствует catalog filtering.py:_normalized_age_bounds, но label «от6»/«6+» вводит в заблуждение.
- Если оба возрастных предела отсутствуют, карта исключает место при возрастном фильтре. Backend PlaceListFilters.apply допускает null bounds. Это различие требует решения о значении неизвестного возраста; не объявлено автоматически ошибкой данных.

`playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/filter-combinations.js` — exit0: 18 combinations (без filters, category, district, age6, age16, category+district+age6 × AZ/RU/EN) на demo fixture, сравнение live count с независимым ожидаемым количеством. Это подтверждает обычные случаи, но не отменяет воспроизведённые edge cases и не доказывает корректность реальных62 записей пользователя.

Рекомендация: приоритет явному canonical district/city; эвристики применять только при отсутствии местоположения и согласовать с backend. Age UX должен явно выбирать возраст ребёнка (например «6 лет») либо получить отдельно согласованную interval-семантику «6+». Unknown ages должны иметь единую политику между картой и каталогом. Исправления бизнес-логики не выполнялись в рамках вопроса о корректности.

### Follow-up: компактная мобильная композиция

Разрешение пользователя: переделать мобильный блок красивее и компактнее. Изменены presentation home.html/home_redesign.css. Mobile: поиск и accessible icon map action в одной строке; район/категория в двух колонках; возраст и reset в одной группе; короткая catalog link рядом с eyebrow; счётчик и короткая подсказка в одной строке. Минимальная target height44px сохранена. Меню шире половинных triggers, остаются в viewport и выше карты. Сокращены mobile отступы; перебиты прежние important padding-inline rules только внутри map panel. Transitions у triggers ограничены background/border160ms, reduced-motion override сохранён.

Age presentation уточнён под существующую exact-age логику: label «Возраст ребёнка», chips0/6/9/12/16, aria labels «Для ребёнка N лет» и AZ/EN equivalents. Predicate, backend и district fixes из аудита не изменены. Placeholder сокращён. Desktop controls сохраняют прежнюю композицию с уточнёнными age labels.

Проверки exit0:
- `playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/mobile-layout.js`: AZ/RU/EN ×320/360/390/430/768, overflow false, targets≥44px, inline search и отсутствие reset/age label overlap, оба меню в viewport. На390px map offset426px вместо ранее измеренных740.8px (~315px выше).
- `playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/layer-check.js`: category/district доступны для hit-testing на1440/1024/390/360.
- `playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/mobile-controls.js`: длинная selected category, age selection, reset, clear, accessible name icon CTA, reduced-motion transition0s.
- `git diff --check`; `node --check static/js/home_map.js`.

Screenshots просмотрены: `output/playwright/home-map-mobile-compact.png`, `output/playwright/home-map-desktop-final.png`. Browser использует изолированную fixture как описано выше. Текущая Google/production логика не заявлена проверенной. Без commit/push/deploy.

### Follow-up: мобильный hero

Пользователь разрешил улучшить hero и убрать ощущение пустоты сверху. Mobile-only CSS: отступ от шапки до eyebrow уменьшен с44 до24px, заголовок и описание выровнены слева, коллаж компактнее и без постоянного покачивания; один основной CTA, каталог как secondary text link; статистика в общей полосе. Сохранены admin title/subtitle, реальные фотографии/числа и slider JS. Области нажатия dots44×44px, visible indicator через pseudo-element; reduced-motion отключает transition. Декоративные плавающие точки скрыты на mobile. Desktop presentation не изменена. Cache version обновлена.

Проверено на изолированной fixture: `playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/hero-check.js` — passed true, RU/AZ/EN ×320/360/390/430/768/1440, без горизонтального overflow и text overflow, изображения загружены, mobile targets≥44px, gap≤30px. Проверены click/Enter на dots, reduced-motion и primary CTA hash. На390px высота hero628 вместо674px, начало82 вместо92px. `git diff --check` exit0. Screenshot `output/playwright/home-hero-mobile.png` просмотрен. Production/Google не использованы, Django/backend тесты для CSS не запускались. Без commit/push/deploy.

### Follow-up: исправление бизнес-логики фильтров (разрешено пользователем)

План: район только из canonical district (точное совпадение, Baku объединяет baku и baku_*), убрать address/search_text/широкий bbox в JS и homepage payload. Возраст — возраст ребёнка, существующие chips без плюса и accessible labels сохраняются; inclusive exact-age predicate. При выбранном возрасте/диапазоне полностью неизвестный возраст исключается и в каталоге, открытые границы поддерживаются. Без фильтра неизвестный возраст остаётся. Регрессионные тесты сначала воспроизводят ложные district matches и unknown-age расхождение; затем isolated Django и Node tests плюс browser combination checks. Никаких data migrations/production/commit/deploy.

Исправлено в LOCAL dirty WORKTREE: JS district predicate строго сравнивает canonical key; Baku объединяет baku/baku_*. Homepage resolver больше не назначает район по bbox/address/неpersisted геометрии. Public filter option Baku count также исключает неизвестный district (удалено прежнее heuristic добавление). PlaceListFilters и event queryset исключают полностью неизвестные age bounds только при активном возрасте/диапазоне; одна неизвестная граница остаётся открытой. Age chips уже были уточнены в UI предыдущим изменением, exact-age semantics сохраняется. FAQ RU/AZ/EN теперь объясняет точный возраст и unknown-age policy. JS cache version обновлена. Существующие остальные WORKTREE изменения сохранены.

Регрессии до исправления:
- `node --test scripts/tests/home_map_filters.test.cjs`: 6 failed /2 passed; ложные Sumgait/Baku, street/district и missing canonical district.
- `.venv/bin/python .tmp/home-map-ui/run-filter-tests.py`: unknown-age и missing district regressions failed; дополнительные event и option count tests также воспроизвели дефекты (unknown event included; Baku count2 вместо1).

Свежая проверка после исправления:
- `node --test scripts/tests/home_map_filters.test.cjs`:8 passed,0 failed.
- `.venv/bin/python .tmp/home-map-ui/run-filter-tests.py catalog.testcases.test_public_filter_consistency catalog.testcases.events_feature catalog.testcases.test_home_public_metrics`:13 passed,0 failed; isolated DJANGO_TESTING=1, cleared environment, memory test DB, locmem cache, isolated media, без production credentials.
- `playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/filter-combinations.js`:27 combinations RU/AZ/EN passed на synthetic local fixture; browser age labels дополнительно проверены на3languages. Расширенный browser probe с отсутствующим в fixture dropdown value Sumgait был некорректен: существующий tree handler сбрасывает недоступный value. Повторный прогон использует доступные options; Sumgait false positives покрыты real-predicate Node regression tests.
- `node --check static/js/home_map.js`; `git diff --check`:exit0.

Broader run `.venv/bin/python .tmp/home-map-ui/run-filter-tests.py catalog.testcases.test_public_filter_consistency catalog.testcases.catalog catalog.testcases.events_feature catalog.testcases.test_home_public_metrics`:129 tests,2 failures (не объявляется green). `CatalogSubcategoryFilterTests.test_subcategory_combines_with_other_filters`: fixture Ganja использует Baku coordinates, модель автоматически присваивает Baku district. `TestGeocodePlacesCommand.test_command_backfills_coordinates_for_existing_place`:lat остаётся None. Оба падения отдельно воспроизведены `.venv/bin/python .tmp/home-map-ui/run-baseline-controls.py catalog.testcases.catalog.CatalogSubcategoryFilterTests.test_subcategory_combines_with_other_filters catalog.testcases.catalog.TestGeocodePlacesCommand.test_command_backfills_coordinates_for_existing_place` с исходными apply/selected из HEAD filtering.py (2 failed). Assertions не изменялись ради green. Не исправлялись несвязанные geocoding/model fixture задачи. Production, Google provider и полный suite не проверялись; deploy/commit/push не выполнялись.
