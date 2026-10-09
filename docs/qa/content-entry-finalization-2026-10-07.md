# KidsMap: локальное завершение заполнения карточек

Начало: 7 октября 2026. Завершение проверки: **8 октября 2026, Asia/Baku**. Исполнитель: один kidsmap-orchestrator; роли backend/security/browser/release выполнены последовательно, независимых исполнителей не было.

Согласованные формы уже находились в dirty WORKTREE. В этом запуске выполнены оставшиеся подтверждённые исправления и новая приёмка. Исторические отчёты и вставленный пользователем отчёт не использованы как свежие доказательства. Scope разрешён сообщениями «локально … продолжи окончательно делать» и «продолжи этот промт»; [план завершения](/home/ramin/kidsmap/docs/superpowers/plans/2026-10-07-content-entry-finalization.md).

**Результат: подтверждённые ниже дефекты исправлены локально. Выполненные сценарии PASS; непроверенные сценарии перечислены отдельно.** Commit, push, deploy, production, реальные записи и внешняя доставка сообщений не выполнялись.

## Что именно проверялось

- LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`; HEAD не изменён.
- Проверялся WORKTREE, включающий прежние незакоммиченные реализации. Исходный манифест содержит **5149 файлов**. Из исходного набора изменены только **34 разрешённых файла**; вне разрешённого списка изменений исходных файлов нет. Новые собственные helper/test/report файлы перечислены отдельно в материалах запуска. Общий Git diff нельзя приписывать этому запуску.
- Финальный SHA256 набора 2756 файлов `src/static/locale/config`: `c0acc75bdb30a2fd13d87d41f6038e877f6b299d1c3e23b94bf6380b78b10c9c`. Скомпилированные MO учтены дополнительными хешами.
- Изолированный стенд [localhost:8788/qa/](http://localhost:8788/qa/), собственная PostgreSQL17, network=none, без опубликованных портов БД, отдельные socket/cache/media/private-media. `DJANGO_TESTING=1`; внешний credential отсутствует; почта и cache LocMem. Unit suite использовал вторую собственную БД, чтобы не разрушать браузерные данные.
- [Версия стенда и сохранность исходных файлов](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/version-summary.json), [состояние вымышленных карточек](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/final-state.json). Endpoint `/qa/acceptance-version/` сверяется с source manifest; пользовательские стенды 8780–8787 не перезапускались.
- Роли только вымышленные: demo_owner, demo_person, demo_moderator, demo_outsider. Вход через кнопки `/qa/`, без публикации паролей.

## Исправления и первопричины

Каждая строка — отдельный дефект. URL относительные к изолированному стенду. Статус всех строк: **FIXED / повторная проверка PASS**. P1 — потеря данных, отказ формы или обход версий; P2 — неверное отображение или навигация.

| ID / приоритет | Роль, URL, воспроизведение | Ожидание → фактический дефект до исправления | Причина и область изменения | Новое доказательство |
|---|---|---|---|---|
| PP-01 / P1 | Владелец, `/ru/account/places/18/edit/`; сохранить фото редакции → открыть → сохранить текст | Обложка сохраняется → бралась обложка live вместо сохранённого candidate | OwnerPlaceEditForm проецирует server candidate также в bound POST; сохранена семантика clear/upload | CandidateMediaTests; owner gallery save/reload/review |
| PP-03 / P1 | Владелец, тот же URL; после reload удалить/переставить сохранённое фото, добавить новое | Управляемая сохранённая галерея → candidate-файлы были вне штатных controls | Стабильные server keys saved/candidate/new, allowlist удаления/порядка и версия редакции; нет выдуманных ID | 9 CandidateMediaTests; 6 browser gallery checks |
| PP-02 / P1 | Модератор, `/admin/volunteer/review/20/`; место с ценами только групп → одобрить | Действующие требования publication → старый адаптер не передавал nature/operating_state/nested pricing | Только проекция сохранённого candidate в существующий readiness, не ослабление publication | LegacyReviewProjectionTests; места20/21 одобрены и публичны |
| ACE-21 / P1 | Админ, `/admin/catalog/event/7/change/`; две вкладки, сохранить A затем B | B получает конфликт, A сохраняется → устаревшее B могло перезаписать запись | Original updated_at token, atomic POST и проверка под lock до parent/inlines/publication | EventAdminVersionTests; 3 browser fresh/stale checks |
| CE-GET / P1 | Админ, GET `/admin/catalog/event/7/change/` | Страница открывается без записи → readonly readiness пытался брать lock вне транзакции | Внутренний readonly probe без проверки версии; защита всех POST сохранена | TransactionTestCase GET200, без записи; финальная visual matrix |
| PP-04 / P2 | Общие админские поля и страницы RU/AZ/EN | Владелец/площадка/JSON/карта имеют правильную подпись → ошибочные/fuzzy общие переводы | Точечные PO-значения и локальная MO-компиляция, проверены другие потребители; не массовая перепись PO | Admin add/edit и shared consumers в matrix, scoped backend tests |
| ORG-VIS-01 / P2 | Владелец/публичные страницы; внешний интернет запрещён | Иконки отображаются → внешний Google font недоступен | Уже имеющийся bundled Material Symbols font через scoped icons.css | Загруженный local font в matrix; footer screenshot |
| ACE-09/10 / P2 | Аноним, RU/EN карточки Event/Specialist с AZ-текстом | Доступный текст с понятным языком → пустое описание/биография | Allowlisted display helper с фактическим языком и подписью fallback; поля БД и прежний RU-приоритет специалиста сохранены | SourceLanguageDisplayTests; public smoke12; browser публичные карточки |
| ACE-06/07 / P1 | Владелец, форма события шаг2; площадка KidsMap → черновик → reload | Канонический адрес/координаты/город/район → локализованные числа и неполная география | Machine numbers; existing init_location_fields; правильная последовательность JS | EventVenueMetadataTests; 6 проверок RU/AZ/EN |
| CE-NULL / P1 | Владелец, площадка17 с пустой географией; полное событие → отправка | Разрешённая сервером пустая география → литерал `None` давал ошибку числа | default_if_none перед unlocalize; ноль не теряется. Регион/точка события остаются необязательными | Null-coordinate regressions; optional venue draft/reload/submit2PASS, событие14 pending |
| ACE-11 / P1 | Аноним, `/ru/specialists/`; специалист принимает на KidsMap-площадке со строковым районом | Каталог200 → вызов `.district.name_i18n` приводил к500 | Использован Place.district_i18n для действующего строкового поля | SpecialistCatalogVenueTests; каталог RU/AZ/EN200 |
| CE-GALLERY-FIRST / P1 | Админ, Event add/edit; выбрать сразу2 фото → сохранить → открыть | Сохраняются2 → первый получал имя `__prefix__`, сохранялся1 | Django empty_form оставлен только внутри template, реальный список его пропускает | HTMLParser RED→GREEN; admin gallery browser5PASS |
| CE-GALLERY-KEYS / P2 | Админ, Place/Event gallery; фокус на маркере → стрелка → сохранить | Порядок меняется клавиатурой → работало только перетаскивание | tabindex/role/aria, стрелки, сохранение фокуса и существующий renumber | Реальное keyboard reorder + save/reload в обоих редакторах |
| CE-ADMIN-CANDIDATE / P1 | Админ, `/admin/catalog/place/18/change/`; candidate → reload → два последовательных delete/add/reorder | Редактируется сохранённая редакция → показывались live фото; main adapter сбрасывал gallery до inline-save | Extra unsaved forms из server candidate, trusted row keys; запрет чужого ID/management tampering; main adapter не обнуляет inline gallery | 5 AdminCandidateGalleryTests; 2 полных browser edit/reload + review/public,4фото |
| CE-SPEC-JS / P2 | Админ, Specialist add/edit | Штатный Django JS без ошибок → `null.dataset` на36 сочетаниях | В change_form добавлен обязательный Django script ID | Повторная matrix,0 pageerrors; отдельный JS probe |
| CE-TARIFF-LOOP / P1 | Админ, Place edit; режим «Бесплатно» или «Цена по мероприятию» | Форма отзывчива → microtask loop зависал | Observer следил за hidden, обработчик снова безусловно писал hidden. Теперь запись только при изменении значения | 3 реальные смены free/events/tariffs с подтверждением сохранения отключённых тарифов; repeat gallery |
| CE-SPEC-NAV / P2 | Админ, Specialist PC sidebar | Полное название раздела читается → длинные подписи обрезались; legacy CSS конфликтовал на901–1024 | Scoped CSS: вертикальный список и перенос текста от901px; mobile select до900 сохранён | Финальная matrix проверяет clipping текста отдельно;9keyboard проверок RU/AZ/EN на901/1024/1440; свежие PC/mobile screenshots |

Основные изменения: forms.py; photo_gallery.py; publication_forms.py; volunteer_places.py; EventAdmin и candidate formset в domain_admin/place.py; owner event controller/JS/template; views.py; методы отображения Event/Specialist и localized_content; gallery templates/JS; specialist template/CSS; scoped locale/base font. Новых миграций в этом запуске нет. Правила организатора, площадки, дат, требований публикации и доступа не изменены. request_join/confirm_join/detach не заменялись прямым присваиванием organization_id. Физические файлы не удалялись.

## Функциональная приёмка

PASS означает фактически выполненный локальный сценарий с указанным доказательством. Основные цепочки выполнены в RU; отдельные проверки локализации перечислены ниже. Это не означает полный прогон всех действий на каждом языке и каждой ширине.

| Сценарий | Места | Организации | Специалисты | Мероприятия |
|---|---|---|---|---|
| Создание, частичное заполнение, черновик | PASS: студия18, центр20, площадка21 | PASS: организация4 без филиалов | PASS: предложение4, черновик с первого и следующих шагов | PASS: штатные3 шага, очно/онлайн |
| Обновление, явное восстановление и продолжение | PASS: текст/цены/часы/группы/фото | PASS: серверный черновик4 | PASS: явное восстановление,3места приёма | PASS: новый/существующий, дата/место/фото |
| Ошибки, сохранение ввода, переход к полю | PASS: возраст13–12,422 и keyboard focus | PASS: некорректный URL | PASS: обязательные поля400, focus и нужный шаг | PASS: телефон/даты/файл, видимое поле ошибки |
| Отправка и скрытость до проверки | PASS | PASS | PASS: повторная отправка того же предложения | PASS: очное9/онлайн10; optional geography14 pending |
| Модерация и публичная карточка | PASS:18/20/21 | PASS:4 | PASS:4 | PASS:9/10 |
| Изменение опубликованного | PASS: новая редакция фото, live до одобрения | PASS: старый live до review, новый после | PASS: кабинет самого специалиста и админка | PASS: админское редактирование; владелец переносит/отменяет опубликованное событие |
| Две вкладки / устаревшая версия | PASS: local B сохранён, чужой A не перезаписан | PASS: организация изменилась после preview → новый review | PASS: кабинет409 и stale admin | PASS: owner409 и stale admin без overwrite; pending14 закрыт для обычного edit |
| Чужие права | PASS: draft403, редактор не открыт | PASS: чужой workspace/receipt404, нужно подтверждение владельца места | PASS: автор предложения без прав человека; чужие документы закрыты | PASS: чужой организатор/событие403 |

[Структурированные функциональные доказательства](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/functional-evidence.json) сохраняют оригинальные результаты и явные ссылки на повторные проверки. Ранние ложные результаты harness не переписаны: ожидание навигации/POST, два видимых `_continue`, подтверждающий modal и исходное число фото исправлялись в проверочном коде. Ошибка null geography и потеря gallery были настоящими дефектами приложения и исправлены отдельно.

| Отдельный сценарий | Статус | Что проверено |
|---|---|---|
| Фото и порядок | PASS | Owner: reorder/delete/add/replace/save/reload/review/public. Admin Event:2загрузки и keyboard order. Admin Place:2последовательные редакции и4сохранённых фото после review |
| Занятия/группы/тарифы/расписание | PASS | Место20:2группы3–7/8–15, цены15/25, занятия Ср/Пт, часы места9–18 отдельно;21:билет30. Публичные цены/группы/расписание после модерации |
| Подключить10 готовых мест | PASS | Owner: места4–13 без пересоздания, повторный receipt; Admin:22–31 через selection → target → review → result |
| Частичный отказ и чужая сеть | PASS | already_connected / other_network / requested по каждой строке,15 подтверждает собственный владелец; явный перенос4 из сети2 в3 отдельно |
| Отвязка | PASS | Явное согласие с последствиями, отсоединение, повтор действия; RU/AZ/EN ×360/390/768/1440. Свежий UI-прогон полного сотруднического/общепрограммного графа после отвязки NOT RUN; backend контракты входили в1819 |
| Сохранность подключённых мест | PASS | После подключений/отвязки/переноса сравнение исходных10: ID, photo, gallery, activity, groups, prices, schedule полностью совпадают; organisation link проверяется отдельно |
| Сотрудничество и места приёма специалиста | PASS | Организация приглашает, сам человек подтверждает.3места приёма, отдельные35/60/0 и телефоны филиалов; общий edit не сбрасывает их |
| Пустой стаж /0лет | PASS | Раздельные server/render проверки NULL и0; административное сохранение пустого значения |
| Личность и документы | PASS | Запрос/одобрение личности; права человека только после проверки; identity закрыт анониму/владельцу сети; certificate требует согласия+review, аноним200после одобрения и404после отзыва |
| Организатор / площадка события | PASS | Организация и подтверждённый специалист, очно/онлайн, own address и KidsMap venue; телефон площадки берётся отдельным действием |
| Asia/Baku /полночь /перенос /отмена | PASS |23:30→00:30 следующего дня, перенос на4–5февраля2035, отмена occurrence, публичная карточка200 с новым состоянием; чужой manage403 |
| Публичные разделы OFF/ON | PASS |18комбинаций для организаций/специалистов/событий ×3языка,54GET. Event OFF410, другие OFF404 по действующему контракту; админка200; в конце все3флагаTRUE |
| Переводы / фактический язык | PASS | Fallback-текст помечен исходным языком; автоматические переводы в БД не создаются |
| Клавиатура | PASS, выборочно | Выбор формата, шаги/разделы, error links, consent, gallery order, обычные кнопки. Полный обход каждого элемента и screen reader NOT RUN |

## Серверные проверки и границы их свежести

| Проверка | Результат | Граница доказательства |
|---|---|---|
| Полный `catalog` в стандартном изолированном QA04 | **1819 tests / OK**,951.810s | Завершился до последних candidate-admin adapter,5новых regression tests и финальных JS/template/CSS поправок. Это не полный suite финального снимка |
| Финальный серверный scope | **338 tests / OK**,87.050s | После последнего Python исправления; включает26новых regressions, admin/publication/concurrency/owner safety/place continuous/Event/Specialist admin |
| Отдельные новые регрессии | **26 tests / OK**,7.972s | Сохранение/удаление/замена/ключи/лимиты/чужие ключи/stale галереи; admin candidate и tampering; readonly GET; версии; fallback; geography; каталог |
| Последние JS и template изменения | PASS | Реальный Chromium:3режима тарифов,2редакции галереи, review/public; specialist JS; финальная matrix |
| Полный проект вне catalog / полный catalog после последних поправок | **NOT RUN** | Не выдаётся за1819 или1824финальных зелёных теста |

Точные команды (из `/home/ramin/kidsmap`):

```bash
.venv/bin/python .tmp/content-entry-final-20261007/run_unit.py catalog
.venv/bin/python .tmp/content-entry-final-20261007/run.py catalog.testcases.test_content_entry_final
.venv/bin/python .tmp/content-entry-final-20261007/run.py catalog.testcases.admin catalog.testcases.auth_access catalog.testcases.auth_flow catalog.testcases.test_content_entry_final catalog.testcases.test_event_admin_readiness catalog.testcases.test_specialist_entry_admin catalog.testcases.test_task33_event_owner_contract catalog.testcases.test_task33_place_continuous catalog.testcases.test_task33_publication catalog.testcases.test_task33_r1_owner_safety catalog.testcases.tracking
.venv/bin/python .tmp/content-entry-final-20261007/run.py --script snapshot_connections.py
```

Helpers очищают inherited env и устанавливают DJANGO_TESTING/изолированные settings/socket/media/cache. Одновременные тестовые процессы в одной БД не использовались. Assertion changes ради зелёного прогона не делались: существующие payload обновлены для обязательного исходного token, проверка прежнего текста — для актуальной утверждённой копии, fallback — для явного фактического языка.

Исходные RED, неверный первый manual profile, устаревшие fixture-copy assertions, ошибочные ожидания browser harness и прерванный ночной прогон сохранены отдельно; они не засчитаны как PASS. Полный успешный лог с ожидаемыми тестовыми traceback завершается `Ran1819 / OK`; ожидаемые traceback внутри negative tests не являются итоговым падением suite.

## Браузер и скриншоты

Chromium, только localhost, внешние origins заблокированы. RU/AZ/EN × **360/390/768/1024/1280/1440**. Проверены21страница и все3шага мероприятия/5шагов предложения специалиста. Матрица этапов переключает существующий wizard API и проверяет отображение; сохранение/модерацию подтверждают отдельные реальные workflow прогоны.

- [Матрица страниц](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/matrix.json):378/378PASS — HTTP, document overflow, pageerrors, доступность локального font; дополнительно отсутствие обрезания specialist nav.
- [Матрица этапов](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/stage-matrix.json):144/144PASS — один верный видимый шаг, отсутствие pageerrors/переполнения.
- Это не522полных пользовательских цепочки. Отсутствие scroll overflow само по себе не доказывает удобство/полноту всех элементов; основные свежие screenshots дополнительно просмотрены глазами.

| Экран | PC | Mobile |
|---|---|---|
| Место: кабинет | [1440](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/owner-place-edit-ru-1440.png) | [390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/owner-place-edit-ru-390.png) |
| Место: админка | [1440](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/admin-place-edit-ru-1440.png) | [390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/admin-place-edit-ru-390.png) |
| Организация: кабинет | [1440](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/owner-organization-edit-ru-1440.png) | [390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/owner-organization-edit-ru-390.png) |
| Организация:10готовых мест | [Результат PC](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/owner-connect10-result-1440.png) | [Результат390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/owner-connect10-result-390.png) |
| Специалист: админка | [1440](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/admin-specialist-edit-ru-1440.png) | [390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/admin-specialist-edit-ru-390.png) |
| Специалист: предложение, шаг3 | [1440](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/stages-specialist-ru-1440-3.png) | [390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/stages-specialist-ru-390-3.png) |
| Событие: кабинет, шаг2 | [1440](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/stages-event-ru-1440-2.png) | [390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/stages-event-ru-390-2.png) |
| Событие: админка | [1440](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/admin-event-edit-ru-1440.png) | [390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/admin-event-edit-ru-390.png) |
| Конфликт места | [1440](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/conflict-1440.png) | [390](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/conflict-390.png) |

Дополнительный [возраст422 и фокус](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/screenshots/place-age-error-390.png). Скриншоты отдельных workflow относятся к моменту выполнения своего сценария; скриншоты финальной общей матрицы пересняты после последнего CSS исправления.

## NOT RUN и остаток

- Google Maps/geocoding, внешняя карта с настоящим ключом, реальные OAuth/почта/регистрация участников/рассылки. Проверены локальное сообщение недоступности карты и сохранение адреса; интеграционная работоспособность не заявляется.
- Настоящие телефоны/Safari/Firefox, screen reader, полный Tab обход каждого поля на каждой комбинации. Mobile здесь Chromium viewport.
- Полная функциональная цепочка всех ролей во всех18языково-размерных комбинациях; проверка длинных текстов/всех категорий/всех допустимых файлов и максимальных объёмов.
- Весь граф общих программ и доступа сотрудников после detach в rendered UI; текущий backend контракт покрыт полным catalog, дополнительный UI прогон не выполнен.
- Содержимое настоящих удостоверений/сертификатов, настоящая верификация личности. Проверены ACL и согласия только вымышленных документов.
- Полный проект и повтор1819 после последних локальных поправок; production readiness/миграции/deploy. В пределах выполненных финальных проверок открытых FAIL нет; NOT RUN остаётся NOT RUN.

Стенд оставлен доступным на8788. Перезапуск **только своего** стенда:

```bash
.venv/bin/python .tmp/content-entry-final-20261007/capture_runtime.py
.venv/bin/python .tmp/content-entry-final-20261007/launch.py
```

Raw логи, browser scripts и успешные test suites: `/home/ramin/.local/share/kidsmap-qa/content-entry-final-2026-10-07/`. Исходные диагностические материалы сохранены в собственной `.tmp/content-entry-final-20261007/`; чужие файлы/стенды не очищались. [SHA256 доказательств](/home/ramin/kidsmap/docs/qa/content-entry-finalization-2026-10-07/evidence-sha256.json). Собственный active_run закрыт; новые действия с production требуют отдельного поручения.
