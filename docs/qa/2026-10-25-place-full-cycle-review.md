# Полный цикл мест: локальная проверка и исправления

> После этого аудита внесены согласованные правки формы: помощник, отступы, пустой выбор расписания и привязка ошибок часов. Их новый срез и целевые проверки описаны в [отдельном отчёте](2026-10-25-owner-editor-ui-feedback.md). Широкие результаты ниже относятся к указанным здесь прежним срезам.

Дата: 25 октября 2026. Исполнитель: один агент, без делегирования. Режим: согласованные локальные исправления и повторная проверка. Рабочая папка `C:/kidsmap`; сервер `http://127.0.0.1:8898/` оставлен работающим.

LOCAL HEAD: `3c1e383bd81d3cd0a26657ef3b79e768e2fc5858`. Проверялось грязное WORKTREE, а не только HEAD. В начале `git status --short` содержал 149 путей. Существующие изменения не откатывались; commit/push/deploy не выполнялись. Production и production env не использовались. Доступы прочитаны из указанного пользователем файла; пароли не включены в отчёт и доказательства.

## Версии и доказательства

Начальный стенд совпал с диском по 1134 исходникам. После исправлений использовались четыре явно различаемых среза:

| Срез | Файлов | Что проверялось |
|---|---:|---|
| Initial | 1134 | Создание и публикация AZ/RU/EN, полный цикл ролей, первое воспроизведение JSON/legacy |
| Final1 | 1135 | Вёрстка, тарифы, валидация, сеть/retry, рабочие копии, staff media, legacy после исправления |
| Final2 | 1136 | `null`, числовые типы/ID, JSON и группы, owner contacts; основной backend-набор |
| Final3 | 1137 | Экспорт сохранённого кандидата, его версия, JSON своей карточки волонтёра; owner media, 12 примеров инструкции, AZ/EN волонтёра |
| Final4 | 1139 | Публичные периоды, количества, безлимит, сроки, рассрочка, условия, группы и обязательные услуги |

Final3 → Final4: только formatter публичных условий, его вызов, публичный шаблон и регрессия. JS после Final3 не менялся. Старые прогоны не выдаются за повторение всей матрицы на Final4. Полные списки изменений между срезами: [source-deltas.json](2026-10-25-place-full-cycle/source-deltas.json). Финальные хеши: [sources-final4.json](2026-10-25-place-full-cycle/sources-final4.json). Сводка результатов и хеши browser-артефактов: [summary.json](2026-10-25-place-full-cycle/summary.json).

Codebase Memory: проект `C-kidsmap`, правильный root, индекс от `2026-10-16T18:56:53Z`, 120 частичных файлов, 0 полностью пропущенных файлов. Изменённые файлы отмечены `metadata_changed`, новые файлы отсутствуют в покрытии; публичный шаблон частично разобран в том числе около групп тарифов. Использованы architecture/search/trace/coverage; связи normalizer → owner/admin/volunteer/publication и public summary → detail сверены с исходниками. Граф не считался актуальным доказательством полноты; шаблоны, миграции и динамические ORM-связи проверены непосредственно.

## Что исправлено

| Ошибка и воспроизведение | Локальное исправление | Повторная проверка |
|---|---|---|
| Старый `{name, price, frequency}` открывался, но изменение website возвращало ошибку `product_type`; кандидат не сохранялся | Exact unchanged legacy fallback сохраняется сырым в трёх формах и publication pipeline. Продукт/единица/период не угадываются, relational plans не создаются | RED в трёх формах и native admin; затем GREEN, реальное сохранение/одобрение, read-only сравнение БД |
| Экспорт не содержал scalar-цены и исходный JSON | Экспорт сохраняет исходные поля для сверки; изменение этих полей в полном экспорте не подменяет тарифы молча | Экспорт и его валидатор; legacy preservation; повторное открытие |
| Явный `website: ""` не очищал поле; `schedule` из собственного экспорта пропускался | Пустой текст применяется; `null`/пропущенные значения остаются неизвестными. Исторический текст расписания импортируется | DOM RED → GREEN и реальные JSON-сохранения |
| `pricing_plans: null`/`tariffs: null` превращались в пустой список после серверной проверки | Только явный непустой/пустой список заменяет тарифы; `null` их сохраняет | RED → GREEN, браузерный импорт → save → reopen |
| Некорректный `place_id` мог вызывать исключение; `true`/дробь превращались в количество или ID тарифа, Infinity давала OverflowError | Строгая проверка идентичности/версий; булевы и дробные counts/IDs отклоняются, overflow становится ошибкой валидации. Целые строки совместимы | Отрицательная матрица и HTTP400/409 с текстом ошибки; положительные примеры |
| Экспорт черновика/ожидающих правок читал базовую Place, а не сохранённый кандидат | Экспортирует сохранённые тексты, тарифы, structured schedule и nested pricing кандидата; добавлены `export_scope` и `candidate_version`, проверяется устаревшая версия | RED → GREEN, реальный новый admin draft → export → import → save → reopen; старый экспорт409 без потери ввода |
| Волонтёрский JSON с `place_id` блокировался даже для своей карточки | Форма передаёт свой ID; валидатор использует существующий `own_places` ACL. Чужая карточка и обычная admin change page остаются недоступны | Положительный native save/reopen; отрицательные permission-тесты |
| Не все неизвестные JSON-ключи показывались пользователю | Перечисляются все пропущенные ключи; серверные предупреждения сохраняются в результате импорта | Регрессия с четырьмя неизвестными ключами |
| Публично терялись немесячный период, количество, безлимит, срок использования, даты и число платежей; conditions заменяли вычисленные детали; группы не выводили details | Backend formatter показывает сохранённые условия отдельно от суммы и объединяет их с текстом. Group options и обязательные fees выводят свои details. Цена не делится на число платежей | 9 RED-подслучаев → GREEN; 110 затронутых тестов; 18 rendered комбинаций AZ/RU/EN × 390/1440, без overflow/JS/network ошибок |
| Свободный `frequency` старого JSON не доходил до публичных деталей | Показан дословно, без преобразования в enum/количество/период | Unit regression и 6 rendered комбинаций AZ/RU/EN × 390/1440 |

Основные исходники: `src/catalog/services/pricing_plans.py:198`, `pricing_terms.py`, `publication.py`, формы owner/admin/volunteer, `domain_admin/place.py:4452` и `:4549`, `static/admin/js/kidsmap_place_json_import.js`, публичный `place_detail.html`.

Обновлена документация: [актуальный JSON-контракт](../ui/place-json-contract.md). Старый [field matrix](../PERMANENT_PLACE_FIELD_MATRIX.md) помечен историческим, поскольку его утверждения о price/schedule modes больше не описывают текущую реализацию. Изменений моделей, миграций и массового преобразования данных нет.

## Реальные браузерные сценарии

- Owner/admin: создание, реальные загрузки, native draft save/reopen, отправка/публикация и анонимные каталог/карточка в AZ/RU/EN. Initial full остановился позже на неверной классификации ожидаемого422; уже выполненные создания сохранены как отдельные доказательства.
- Волонтёр и владелец: сохранение, приватный кандидат, полное preview, очередь модерации, отказ без причины, возврат с причиной, исправление, повторная отправка, одобрение. Изменение опубликованного названия остаётся приватным до одобрения; отклонение не меняет публичный оригинал. Admin edit проходит тот же candidate boundary. 29 событий role journey.
- Пустая/неполная рабочая копия, автосохранение, явное сохранение, выход в кабинет, новый browser context, восстановление текста/цен/расписания/фото, неудачный save-and-exit и retry. Рабочая копия и native Place draft различаются; пустой native Place не заявлен принятым во всех формах.
- Контакты: местный телефон и международный WhatsApp, три режима WhatsApp, сохранение скрытой страны/старой валюты, необязательные поля, Instagram, обязательные зависимости. Owner/admin contact-only изменения проходят реальные публикацию и публичную проверку; USD/EUR сохраняются.
- 52 ценовых сценария owner/admin: canonical products, четыре price modes, диапазон/from/request/free/trial, обязательные услуги, рассрочка, количество/единица, безлимит, периодичность, срок использования, даты и переводы. Дополнительно лимит12, перестановка/удаление тарифов, исправление ошибочного диапазона и keyboard controls.
- Фото owner: добавление, порядок, выбор главного, удаление gallery, замена главного, clear → save → reopen, повторная загрузка. Последнее главное фото после повторного открытия декодировано и проверено по цвету тестового изображения. Staff/volunteer: смешанные старые/новые фото, порядок, подписи, удаление, make-main, восстановление рабочей копии, настоящий preview и native save. Файлы и текст после невалидного upload сохраняются.
- Сетевой обрыв,503 и ответ200 с невалидной структурой: все три роли,390px; отсутствует ложный success, ввод остаётся, retry сохраняет. Потеря уже принятого text/media ответа проверена с прежним UUID, без дополнительной копии. Реальный double click native create дал один запрос и одну карточку на попытку.
- Собственная тестовая карточка326 снята с публикации, анонимно недоступна и перемещена в удалённые через native admin confirmation. Это soft delete; чужие записи не удалялись.
- 42 layout-комбинации owner/admin: AZ/RU/EN и320/360/390/768/1024/1280/1440. Live validation: owner AZ/RU/EN на390/1440, staff RU на390/1440, дополнительно volunteer AZ/EN на390/1440. Проверялись DOM, доступные ошибки, focus, summary identity, отсутствие программного скролла, debounce/stale response, ширина и локальные HTTP/uncaught errors. Увеличение высоты из-за ошибок не названо отсутствием layout reflow.

Точные результаты находятся под `output/playwright/place-full-cycle-20261025/`; пути/хеши принятых наборов перечислены в evidence summary. Примеры: [период и количество на телефоне](../../output/playwright/place-full-cycle-20261025/final4-public-terms/foreign-ru-390.png), [группа и обязательная услуга](../../output/playwright/place-full-cycle-20261025/final4-public-terms/group-en-390.png), [photo restore](../../output/playwright/place-full-cycle-20261025/final3-owner-photos/restored-main-390.png).

## Совместимость старых форматов

Форматы найдены в Place/pricing models, миграциях0062/0084/0100/0123, legacy migration/parser и import-коде, тестах. Использовались новые синтетические копии этих форматов в изолированной локальной БД. Это не аудит реальных production-строк.

| Формат / локальный пример | Каталог и карточка | Новый редактор | Постороннее поле → сохранение/одобрение | Цена, единица, период |
|---|---|---|---|---|
| Scalar `price_per_lesson=35`, from/to35, без plans;306 | Видим; headline «от35» | Тарифов нет, scalar не переписывается | Полные значения/ID/расписание/галерея сохранены | Плашка payment-neutral; единица не превращена автоматически в новый тариф |
| Scalar range25–70, без известного продукта;327 | Видим;25–70₼ | Без выдуманного тарифа | Website сохранён и одобрен; значения неизменны | Единица/период неизвестны: manual_review |
| `{name,price,frequency}`;328 | Видим; JSON-строка120AZN и дословная frequency | Старый тип не угадывается; raw JSON сохранён | Ранее edit блокировался, теперь approved;0 новых relational plans | В копии также есть scalar80: headline80 и JSON120 требуют ручной сверки источников |
| Старый JSON `payment_type=per_month`,140,8 sessions;329 | Видим; детали140AZN/месяц и8 раз/месяц | Alias поддержан, unrelated save не мигрирует JSON | Approved; raw JSON/остальные поля сохранены | Scalar80 и JSON140 могут обозначать разные предложения; не выбран новый primary автоматически |
| Relational USD, каждые2 недели,7 visits;305 | Видим;80USD, после fix видны период/количество/conditions | Все сложные поля и ID сохраняются | No-op, contacts и JSON round trip без потерь | Валюта не пересчитана; период не заменён месяцем |
| Structured week + multilingual contacts/categories | Публичная неделя и контакты сохранены | Открываются и восстанавливаются | Read-only equality до/после | Legacy и canonical данные не смешиваются автоматически |
| Только текст «Пн-Пт10:00–19:00»;330 | Текст виден | Старый текст сохранён; не объявлены неизвестные дни | Approved,0 новых ScheduleDay | Автоматической конвертации в неделю не выполнялось |
| Частично заполненная опубликованная карточка;331 | Прямой URL200, в каталоге отсутствует | Открывается, missing requirements видны | Unrelated edit approved по published compatibility; поля сохранены | «Цена уточняется»; неизвестные значения не подставлены |
| Draft / pending / rejected / published | Draft308 анонимно404; опубликованный оригинал остаётся до решения | Видна своя сохранённая рабочая версия | Модерация/повторная отправка проверены | Новый экспорт содержит saved candidate и версию, без утечки в public |
| Group pricing;345/group1/plan190 | Группа,90, каждые2 недели,7 занятий и отдельная обязательная услуга видны | Direct и nested scopes различаются | Version2 export/import/save/reopen сохраняет IDs/период/цену | Version1 намеренно не экспортирует всю группу |

[Read-only итог БД](2026-10-25-place-full-cycle/final-state.json): пять legacy-копий approved, бизнес-поля и schedule сохранены, relational tariffs не созданы; пять исходных controlled fixtures сохранили защищённые поля/IDs/gallery. Owner325 published, volunteer324 published с новой приватной JSON-правкой, admin326 deleted/inactive. Две отдельные double-click попытки дали по одной карточке.

### Manual review данных

Не изменял выбор основной цены для конфликтующих scalar/JSON источников. Конкретные примеры328 и329 сохраняют scalar80 одновременно с JSON120/140. Нужно установить, одно ли это предложение, какой источник актуален и какую единицу/период подтверждает организация; затем отдельно согласовать переход к явным тарифам. Для327 неизвестен продукт диапазона25–70. Для328 свободная frequency не считается подтверждением canonical package/recurrence. Массовая миграция и изменение бизнес-смысла не выполнялись.

## JSON-инструкции и границы

Активная пользовательская инструкция одна: `kidsmap_place_json_import.js` + shared prompt/import dialogs; admin и volunteer используют её с backend taxonomy/pricing contract. Проверены режимы search/new JSON/update, действующие подсказки, endpoint validation, direct/v2 export, import aliases и финальные формы. Owner не имеет этого JSON-диалога. `import_places` — отдельный CSV importer, не JSON upload. `json_script` с конфигурацией формы и публичный JSON-LD не являются инструкциями для импорта карточки.

**Все12 актуальных примеров** из реально открытого диалога прошли import → native draft save → reopen на Final3: ticket, lesson, package, monthly, prepaid, prepaid_unlimited, offer_dates, unlimited, range, trial, deposit, request. Сверялись цена, единица, billing mode/count, quantity, unlimited, validity/dates, role/trial. [Результаты и тексты инструкции](../../output/playwright/place-full-cycle-20261025/final3-instruction-examples/results.json), [JSON prompt](../../output/playwright/place-full-cycle-20261025/final3-instruction-examples/prompt-json.txt), [update prompt](../../output/playwright/place-full-cycle-20261025/final3-instruction-examples/prompt-update.txt).

Проверены malformed JSON, массив вместо объекта, неизвестный enum, неверный/булев ID, булева schema, bool/fraction/Infinity quantity, stale source/candidate, чужая карточка, отмена destructive empty list, явные `[]`, `null`, отсутствующие поля и неизвестные ключи. Ответы400/409 содержат ошибку, rejected import не мутирует форму. Финальные form/publication validators остаются последним барьером; нормализатор tariff/contact endpoint не заменяет весь form validation.

Фото в JSON не экспортируются как бинарные файлы и не загружаются по внешним URL. `editor_review.media_to_upload` — задача ручной загрузки. Проверенный round trip сохраняет уже привязанные фото, но не является переносом медиа на другую карточку. Полный v2 экспорт нужен для групп; неизвестные nested поля не изобретаются. Новые экспорты защищены `candidate_version`; старые форматы без неё совместимы, но не дают этой дополнительной гарантии от устаревшего кандидата. Unsaved browser edits не входят в экспорт.

## Команды и результаты

Тесты выполнялись с `DJANGO_TESTING=1`, очищенным окружением, отдельными PostgreSQL17 socket-only DB, LocMem cache, media/private-media и in-memory email; external integrations отключены. Production credentials не наследовались. Browser contexts разрешали только synthetic localhost.

| Команда / срез | Результат |
|---|---|
| `quality.sh fullcycle-final <labels>` / Final2 |318 PASS,127.357s,exit0; system check clean, migrations dry-run без изменений |
| `rerun.sh fullcycle-json-red fullcycle-scope-fresh <labels>` / Final3 |21 PASS,5.189s,exit0; новая тестовая БД после flush старого набора |
| `rerun.sh fullcycle-json-red fullcycle-public-terms-green <labels>` / Final4 |110 PASS,28.574s,exit0 |
| `node --test --test-timeout=120000 $unitFiles` / Final3 |363 PASS,0 FAIL,0 SKIP,19.152s,exit0 |
| Browser roles / Initial |29 PASS records; три роли и actual public state |
| Browser Final1 |42 layouts,52 pricing cases,11 JSON records,10 preservation/retry records,8 limits,36 guidance records; accepted sets без failure |
| Validation |10 полных сценариев +15 доп. layout observations; ещё4 volunteer AZ/EN сценария |
| Final3 |12/12 instruction examples;4 JSON candidate/volunteer/source records; owner media3/3 |
| Final4 public |18/18 canonical conditions layouts +6/6 legacy-frequency layouts; no overflow/uncaught/local HTTP failures |
| Финальные `check`, `makemigrations --check --dry-run`, `git -c core.whitespace=cr-at-eol diff --check` |PASS |

318/21/110 и browser records **пересекаются**; это не449 уникальных тестов и не470 независимых E2E-сценариев. Срез и точные команды, labels, пути логов: [commands.md](2026-10-25-place-full-cycle/commands.md).

Первые неуспешные результаты сохранены. В частности: visual считал ожидаемый check-only422 ошибкой — теперь проверяется структура errors, а прочие HTTP failures по-прежнему запрещены; compact harness ожидал старый disclosure/класс age toggle — сохранены проверки видимости и реального переключения на текущем контроле. Устаревшее ожидание `price_max` в пользовательском тексте заменено проверкой локализованной подписи и отсутствия machine key; export-тест теперь проверяет точное значение сохранённого scalar вместо требования его отсутствия. Это приведение к проверяемому контракту, не ослабление ценовой валидации.

Первый широкий Node run не нашёл `jsdom` в дочерних процессах; исправлен `NODE_PATH`, после чего набор прошёл. Повторное использование test DB после TransactionTestCase flush оставило её без migration seed categories; это дало FK errors. Свежие изолированные DB восстановили корректный test baseline. Исходные failing логи остаются в `.tmp/place-full-cycle-20261025/` и `.tmp/place-implementation-20261023/fullcycle-*.log`.

## Ограничения и оставшиеся наблюдения

- Chromium151; desktop/mobile — эмуляция viewport. Firefox/WebKit, физические телефоны, системная клавиатура/file picker не проверялись.
- Google Maps оставлена отложенной, внешние transport/OAuth/Instagram account-existence проверки не выполнялись.
- Не полный Cartesian product всех тарифов, ролей, языков и ширин: точные сочетания выше. Полная модерация — RU; AZ/EN покрыты созданием owner/admin, layout/validation, волонтёрской валидацией и публичными условиями.
- Один owner-переход в большой synthetic кабинет превысил15s: trace показывал toast interception и ожидание navigation. Неизменённый сценарий прошёл с45s action timeout. Причина задержки не установлена; это не объявлено исправлением производительности.
- Оригиналы обычных FileField media по действующему контракту могут быть публичными. Не заявляется полная секретность исходных файлов черновика. Private preview/card ACL и доступность картинки — разные проверки.
- Автоматическое скрытие по offer dates и перевод свободных исторических условий в новые бизнес-правила не вводились. Конфликтующие legacy источники требуют manual_review.
- Production, полный тестовый набор всего продукта и сторонние review/favorite flows не проверялись. Это доказательства перечисленных локальных сценариев, не обещание отсутствия всех багов.

## Ссылки для ручной проверки

- [Создать место владельцем](http://127.0.0.1:8898/ru/account/places/create/?type=permanent&fresh=1), [кабинет](http://127.0.0.1:8898/ru/account/places/).
- [Добавить в админке](http://127.0.0.1:8898/admin/catalog/place/add/?type=permanent), [модерация](http://127.0.0.1:8898/admin/volunteer/moderation/), [форма волонтёра](http://127.0.0.1:8898/admin/volunteer/324/edit/).
- [Опубликованная карточка владельца325](http://127.0.0.1:8898/ru/place/325-place-e2e-owner-ru-1792930079405/).
- [Старый JSON328 в редакторе](http://127.0.0.1:8898/admin/catalog/place/328/change/), [group JSON v2](http://127.0.0.1:8898/admin/catalog/place/345/export-json/?pricing_schema_version=2).
- [Публичная группа345](http://127.0.0.1:8898/ru/place/345-place-qa-fullcycle-grouped-json/), [безлимит/срок/рассрочка351](http://127.0.0.1:8898/ru/place/351-place-qa-fullcycle-public-terms/).
- [AZ каталог](http://127.0.0.1:8898/catalog/), [RU каталог](http://127.0.0.1:8898/ru/catalog/), [EN каталог](http://127.0.0.1:8898/en/catalog/).

Использовать существующие локальные доступы из `C:/Users/Ramin/KidsMap-local-review/Доступы.txt`. Финальная проверка совпадения исходников и HTTP health: [final-gate.json](2026-10-25-place-full-cycle/final-gate.json).

После проверок остановлены только два созданных в этой задаче disposable PostgreSQL-контейнера (`fullcycle-final` и `fullcycle-json-red`). Web-процесс и БД стенда на8898 продолжают работать; HTTP health проверен повторно после остановки тестовых контейнеров.
