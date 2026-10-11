# Модуль 06 — подтверждённые дефекты и самостоятельные repair prompts

Дата: 2026-10-10. Checkout `C:\kidsmap`, branch `task33-progress`, LOCAL HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`. Свежий native Chromium, собственные синтетические данные. AUDIT ONLY: исправлений нет. Production не проверялся. Установлена воспроизводимость в текущем локальном baseline; момент появления и регрессия относительно предыдущей версии не установлены.

## PUBLIC-QA-01 — desktop popup общей площадки обрезан, внутреннее закрытие недоступно

- **Статус / класс / уверенность:** OPEN; PRE-EXISTING LOCAL BASELINE; HIGH для геометрии приложения. SDK interface SIMULATED, реальные Google/Leaflet SDK и tiles NOT RUN.
- **Приоритет:** P2. Часть общей карточки и её кнопка закрытия недоступны мышью. Каталог и Escape остаются доступны, потери данных или утечки не выявлено.
- **Роль / URL:** anonymous; `http://localhost:8817/ru/catalog/?category=SPRT`, также AZ `/catalog/` и EN `/en/catalog/`.
- **Матрица:** RU/AZ/EN × 768/1024/1280/1440 — 12 FAIL clipping и 12 FAIL native close. Mobile 360/390 — обе проверки PASS во всех языках.
- **Шаги:** открыть каталог с двумя местами одной confirmed Location → «Карта» → реальным кликом открыть общий marker → проверить верх popup и нажать его внутреннюю `×`. QA заменяет только SDK interface локальным адаптером; popup, позиционирование и CSS приложения не изменены. Никакого force click.
- **Ожидание:** popup и кнопка закрытия помещаются в видимой области карты; контент внутри при необходимости прокручивается.
- **Факт:** при RU 768 popup имеет высоту 560px, карта 400px; `card.y=127.65625`, `map.y=298.65625`, то есть верх popup находится на 171px выше карты. Предок карты имеет `overflow-y:hidden`. Native click перехватывает другой элемент страницы. То же воспроизведено на остальных desktop ширинах.
- **Доказательства:** [36 строк геометрии и кликов](map-geometry.result.txt), [исходный native проход и ошибки клика](map-browser.result.txt), [PC](screenshots/map-geometry-ru-1440.png), [768](screenshots/map-geometry-ru-768.png), [mobile](screenshots/map-geometry-ru-390.png), [локальный SDK adapter](map-adapter.js).
- **Первопричина:** [positionDesktopCard](C:/kidsmap/static/js/catalog_map.js:503) допускает отрицательный `top` во второй ветке при `card.height > map.height`. [Контейнер карты](C:/kidsmap/static/css/site.css:7715) имеет высоту 400px и обрезает overflow; [venue card](C:/kidsmap/static/css/pages/catalog_places.css:3014) допускает 560px. Адаптер задаёт projection, но отрицательный верх и clipping определяются приложением при данных размерах, независимо от точного SDK pixel anchor.
- **Область / зависимости:** public frontend, `catalog_map.js`, CSS карты/venue popup; взаимодействие marker selection, motion, focus restore и breakpoint 760. Реальную SDK совместимость нужно отдельно проверить с разрешённым тестовым окружением.

```text
Исправь только PUBLIC-QA-01 из docs/qa/module06-2026-10-10-r1/FINDINGS.md в текущем KidsMap checkout. Сначала прочитай AGENTS.md и канонические .agents, определи HEAD/WORKTREE/active_run и сохрани чужие изменения. Scope: desktop popup общей площадки в публичном каталоге; static/js/catalog_map.js positionDesktopCard и связанные стили static/css/site.css, static/css/pages/catalog_places.css. Fresh evidence: map-geometry.result.txt, map-browser.result.txt, screenshots/map-geometry-ru-768.png. Карта 400px, popup 560px, top отрицательный, overflow:hidden обрезает верх и кнопку ×. Ограничь размер/размещение popup видимой областью, сохрани прокрутку, доступное закрытие и возврат фокуса. Согласуй конкретный план до реализации, затем проверь native clicks и геометрию RU/AZ/EN × 360/390/768/1024/1280/1440, длинный контент, resize и marker motion. Локальный adapter используй только как SIMULATED interface; реальный SDK укажи отдельно. DJANGO_TESTING=1, отдельные DB/cache/media/email, вымышленные данные. Не менять assertions ради зелёного результата. Без production, commit/push/deploy. Отчёт и fresh PNG; остальные findings не исправлять в этом scope.
```

## PUBLIC-QA-02 — отказ загрузки настроенного SDK оставляет вечный loading

- **Статус / класс / уверенность:** OPEN; PRE-EXISTING LOCAL BASELINE; HIGH для failure handling. SIMULATED transport abort на реальной configured Google branch, без исполнения SDK.
- **Приоритет:** P2. Пользователь не получает сообщения об отказе и способа повторить загрузку. Каталог остаётся доступен после Escape; данных не теряет.
- **Роль / URL:** anonymous; собственный companion `http://localhost:8818/ru/catalog/?q=Aurora` и AZ/EN. Отличие companion: только изолированные QA settings с явно недействительным dummy map key; реальные ключи отсутствуют.
- **Матрица:** RU/AZ/EN × 360/390/768/1024/1280/1440: terminal failure UI 18 FAIL, Escape/list usable 18 PASS. Дополнительные 6 свежих PC/mobile изображений показывают loading в области видимости.
- **Шаги:** загрузить каталог на companion → браузером локально abort внешнего SDK request → открыть карту → ждать. Во всех 18 случаях 2200ms, RU390 дополнительно 15000ms; отдельный visible evidence проход повторяет RU390 15000ms.
- **Ожидание:** при событии script load error показывается понятный terminal error/fallback и доступное закрытие/повтор; loading не остаётся единственным бессрочным состоянием.
- **Факт:** после подтверждённого `requestfailed` отображается «Загружаем карту…» / «Xəritə yüklənir…» / «Loading map…». Нет error/retry состояния.
- **Доказательства:** [18 combinations и network failure](sdk-failure.result.txt), [visible повтор](error-evidence.result.txt), [mobile loading](screenshots/sdk-error-visible-ru-390.png), [desktop loading](screenshots/sdk-error-visible-en-1440.png), [companion launcher](run-configured.py). Query параметры SDK в network evidence удалены.
- **Первопричина:** [script tag](C:/kidsmap/src/catalog/templates/catalog/place_list.html:1210) не обрабатывает `onerror`; [initCatalogGoogleMap](C:/kidsmap/static/js/catalog_map.js:624) при отсутствии `window.google.maps` рендерит loading и возвращает управление без terminal timeout. Успешная загрузка Google SDK в этом запуске NOT RUN.
- **Область / зависимости:** public map bootstrap и сообщения/повтор; не обходить серверные фильтры, не затрагивать публикацию. Проверить поздний callback после ошибки, отсутствие дублирования marker/listener, disabled integrations.

```text
Исправь только PUBLIC-QA-02 из docs/qa/module06-2026-10-10-r1/FINDINGS.md. Прочитай AGENTS.md/.agents, зафиксируй checkout/HEAD/WORKTREE/active_run, сохрани чужую работу. Scope: configured Google SDK failure handling публичного каталога, script tag в src/catalog/templates/catalog/place_list.html и bootstrap static/js/catalog_map.js. Native evidence sdk-failure.result.txt и error-evidence.result.txt: SDK request aborted, через 15s карта всё ещё Loading map/Загружаем карту без terminal error или retry. Подготовь конкретный план, согласуй его и реализуй обработку отказа/ограниченное ожидание/повтор с понятным RU/AZ/EN состоянием. Сохрани доступность списка, Escape, фокус и корректный поздний callback; не создавай дубликаты markers/listeners при retry. Проверь настоящий rendered browser RU/AZ/EN × 360/390/768/1024/1280/1440 с локальным transport abort и delayed callback. Dummy/local adapter — SIMULATED; реальные SDK/credentials без разрешённого тестового окружения NOT RUN. Только DJANGO_TESTING=1 и изолированные вымышленные данные, без production/commit/push/deploy. Сохрани fresh screenshots, команды и exit codes; не исправляй другие findings.
```

## PUBLIC-QA-03 — локальные compiled locale дают русский текст переключателей на AZ/EN

- **Статус / класс / уверенность:** OPEN; ENVIRONMENT FAILURE, существующие ignored `.mo`; HIGH. Не установлен дефект отсутствующего перевода в tracked `.po`. Production locale UNKNOWN.
- **Приоритет:** P3. Неверный язык трёх административных подписей, функция переключения разделов работоспособна.
- **Роль / URL:** admin; `http://localhost:8817/admin/catalog/sitevisibilitysettings/1/change/`, выбран AZ/EN через настоящий language selector.
- **Матрица:** RU390/1440 — PASS; AZ/EN390/1440 — 4 FAIL. Fresh unchanged Django: одна test method с двумя failing subtests EN/AZ.
- **Шаги:** войти синтетическим qa_admin → настройки разделов → переключить интерфейс на AZ/EN → проверить три checkbox labels.
- **Ожидание:** локализованные labels выбранного языка.
- **Факт:** `html lang` переключён, подписи «Показывать «Афишу»», «Показывать «Педагогов и специалистов»», «Показывать «Организации»» остаются русскими.
- **Доказательства:** [native labels](admin-functional.result.txt), [EN PC](screenshots/admin-sections-en-1440.png), [AZ mobile](screenshots/admin-sections-az-390.png), [runtime MO vs source PO](locale-proof.json), [неизменённые Django tests](tests.log), [command/exit 1](tests-command.json).
- **Первопричина:** текущие локальные `.mo` для AZ/EN возвращают исходную русскую строку; `.po` содержат перевод, `.mo` не отслеживаются Git. Их hashes сохранены, компиляция не выполнялась, файлы не изменялись. [EN исходный перевод](C:/kidsmap/locale/en/LC_MESSAGES/django.po:22787), [административные labels](C:/kidsmap/src/catalog/domain_admin/site.py:444).
- **Область / зависимости:** local environment/release localization build и freshness проверки. Сначала проверить сборку `.mo`, не заменять ожидаемые английские/азербайджанские assertions русскими.

```text
Разбери и исправь только локальную locale проблему PUBLIC-QA-03 из docs/qa/module06-2026-10-10-r1/FINDINGS.md. Прочитай AGENTS.md/.agents, сохрани чужие изменения/active_run/стенды. Evidence locale-proof.json: AZ/EN ignored django.mo возвращают русские labels переключателей разделов, хотя tracked django.po содержат переводы. admin-functional.result.txt подтверждает rendered UI, tests-command.json/tests.log — два subtest FAIL одного метода. Согласуй конкретный scope синхронизации локальных compiled catalogs и проверки процесса сборки; не меняй application semantics и assertions для получения green. Используй новый изолированный DJANGO_TESTING=1 стенд, собери locales в согласованной области, проверь native admin AZ/RU/EN PC/mobile и catalog locale regressions. Production состояние UNKNOWN и не входит в scope. Зафиксируй before/after PO/MO hashes, команды, exit codes и свежие screenshots. Без production credentials, commit/push/deploy и без исправлений других PUBLIC-QA.
```

## PUBLIC-QA-04 — hero перекрывает фильтры и перехватывает клик по категории

- **Статус / класс / уверенность:** OPEN; PRE-EXISTING LOCAL BASELINE; HIGH. Это настоящий DOM/hit-test/native pointer, SDK adapter не используется.
- **Приоритет:** P2. Часть выбора фильтров недоступна мышью/касанием. Keyboard Enter и прямые URL позволяют продолжить, но не устраняют основной touch сценарий.
- **Роль / URL:** anonymous; обычный `http://localhost:8817/ru/catalog/`, AZ `/catalog/`, EN `/en/catalog/`.
- **Воспроизведено:** окончательный visible-control проход: RU/AZ360/390 и EN360 — 5 native pointer FAIL. EN390 и все языки768/1024/1280/1440 — PASS. Ранний hidden desktop locator на768 исключён; свежий проход открывает нужный фильтр и выбирает реально видимый responsive chip. Не распространять на все ширины без доказательств.
- **Шаги:** на mobile открыть «Фильтры» → нажать «Творчество» в самой панели. Дождаться завершения transition и animation; финальный проход также использует reduced motion. Реальный `locator.click`, без force/dispatchEvent.
- **Ожидание:** открытая панель и её controls находятся поверх обычного контента; клик выбирает категорию.
- **Факт:** клик перехватывает `.hero.catalog-faq-hero` / её tag button; верх drawer визуально под hero. RU390: control `(29,447,332,48)`, `elementFromPoint(center)` возвращает hero SECTION; drawer z-index2601 находится в нижнем stacking context. EN390 короче hero и выбранный chip не перекрыт, поэтому PASS.
- **Доказательства:** [native click / hit geometry](pointer-final.result.txt), [RU mobile](screenshots/pointer-final-ru-390.png), [AZ mobile](screenshots/pointer-final-az-360.png), [768 PASS boundary](screenshots/pointer-final-ru-768.png). Комбинированные фильтры отдельно перепроверены: 54/54 PASS в [filter-settled.result.txt](filter-settled.result.txt); они не отменяют воспроизводимое перекрытие исходной панели.
- **Первопричина:** [catalog layout](C:/kidsmap/static/css/pages/catalog_places.css:22) создаёт `position:relative;z-index:1!important` stacking context, [hero](C:/kidsmap/static/css/pages/catalog_places.css:1989) имеет z-index100!important. [Drawer overrides](C:/kidsmap/static/css/site.css:24475) пытаются снять stacking context, но проигрывают более позднему `!important` правилу layout. Число z-index самого drawer не выводит его из родительского context. Hit-test подтверждает фактическое перекрытие.
- **Область / зависимости:** public catalog responsive CSS, stacking contexts drawer/sidebar/hero, sticky header, backdrop, popup и keyboard focus. Исключить повышение z-index без проверки всех предков и соседних overlays.

```text
Исправь только PUBLIC-QA-04 из docs/qa/module06-2026-10-10-r1/FINDINGS.md. Прочитай AGENTS.md/.agents и kidsmap-ui-design, зафиксируй HEAD/WORKTREE/active_run, сохрани чужие изменения. Scope: stacking contexts responsive фильтров каталога в static/css/pages/catalog_places.css и static/css/site.css. Fresh native evidence pointer-final.result.txt, screenshots/pointer-final-ru-390.png; pointer-final-ru-768.png — проверенная PASS граница. Catalog layout z-index1!important держит drawer ниже hero z-index100!important; настоящий клик по категории перехватывает hero. Подготовь и согласуй конкретный план, затем обеспечь видимость и pointer доступность drawer/sidebar с правильным backdrop и фокусом. Проверь RU/AZ/EN × 360/390/768/1024/1280/1440, длинные hero headings, открытие/закрытие/Escape/Tab/Shift+Tab, scroll и hit-test controls, а также map popup и sticky header. Не использовать force click как acceptance proof. Только изолированный DJANGO_TESTING=1 стенд с вымышленными данными. Без production/commit/push/deploy; fresh screenshots и отдельный отчёт. Другие PUBLIC-QA не входят в scope.
```
