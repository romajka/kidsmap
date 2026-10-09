# KidsMap — завершение локальной приёмки, 2026-10-09

Роль: kidsmap-orchestrator; исполнитель: один Codex `/root`, последовательная работа, без независимых подагентов. Определение: `.agents/agents/kidsmap-orchestrator/agent.md`, canonical registry. Scope принят сообщением «делай»: исправить CE-RA-01 и пройти оставшиеся проверки из `content-reacceptance-2026-10-09.md`. Новые находки не исправлять автоматически.

LOCAL HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`, исходный dirty WORKTREE:217 записей. PRODUCTION не открывалась. Исторический аудит использован как список сценариев, не как новое доказательство.

## 1. Состояние области

CE-RA-01 исправлен. Дополнительная приёмка — **FAIL: подтверждён CE-C-01, потеря главного фото при публикации административного черновика**. Остальные выполненные сценарии PASS; NOT RUN перечислены ниже. [Доказательства](content-completion-2026-10-09/evidence.json), [снимок версии](content-completion-2026-10-09/version-snapshot.json), [собственный diff](content-completion-2026-10-09/local.diff).

Стенд: http://localhost:8790/qa/ ; дополнительные вымышленные роли: http://localhost:8790/qa/extra/ . PostgreSQL17 контейнер `kidsmap-reacceptance-20261009`, network=none, без опубликованных DB-портов; клонированная synthetic DB предыдущей локальной приёмки, отдельные media/private-media, LocMem cache/email, очищенное окружение, guards сети/libpq. Прежний стенд8788 не изменялся. Реальные email, OAuth, геокодирование и рассылки не подключались. QA-only маршруты находятся в ignored `.tmp/`, не в приложении.

Версии: исходный source2766 SHA `2103684f9e10e93c0fe4fed68c79ffd7215b15804124537abf3fdcc18f22e989`; основная браузерная приёмка после перевода —2767 SHA `4497f48ba7e2a48e709edc067a85f7b761081ef3d37dc8c656aef6d9c490cb01`. Финальный snapshot после сохранения исходного форматирования даты —2767 SHA `bef506f4c30f9c658a8fe2f762a6148aa7e5337bc9ed9ddca08750c2bf25bfbb`; на нём повторены целевые серверные тесты и24 браузерные проверки подписи. Остальные сценарии на последней косметической поправке заново не выполнялись. Запущенный сервер сверяет hashes файлов при старте, `/qa/acceptance-version/` сообщает snapshot. Все прежние файлы приложения, кроме четырёх явно изменённых ниже, побайтно сохранены.

| Сценарий | Итог | Свежие действия и границы |
|---|---|---|
| CE-RA-01, Specialist admin add/edit | PASS | RU/AZ/EN ×360/390/768/1440:24 проверки; подпись локализована, поле readonly |
| Десять готовых бизнес-мест разных владельцев | PASS | Preview/confirm сети оставляет запросы; каждый из10 владельцев отдельно соглашается; связь business только после обоих согласий. Два набора по10, второй со снимком до первого подключения |
| Повтор массового запроса | PASS | Повтор того же POST/operation не создаёт дополнительные связи и не заменяет согласия |
| Сохранность готовых карточек при подключении | PASS | Вторые10: hashes полей, владельцев, фото/галереи, PricingPlan, дней/интервалов работы совпали до/после подключения. Затем намеренно добавлен отдельный fixture общей программы для отвязки |
| Отвязка с общей программой и доступами | PASS | Place138: программа превращается в локальный снимок; группа, тариф, фото, часы и владелец сохранены. Сетевой grant теряет edit, прямой grant сохраняет edit. Публичная карточка остаётся200 |
| Онлайн-событие владельца → модерация → публикация | PASS | Event16: опубликовано без физического адреса, Specialist организатор; публичная карточка RU/AZ/EN200 |
| Две вкладки: место | PASS | Два независимых browser contexts одного владельца: CAS-конфликт, stale ввод сохранён, первая версия не перезаписана |
| Две вкладки: организация | PASS | Первый submit сохраняет candidate, второй возвращает409 с bound вводом; повторное чтение подтверждает первую версию |
| Создание места через админку | **FAIL: фото** | Place148: название/описание AZ, категория/подкатегория, район/адрес/телефон, возраст, часы always_open, бесплатный вход, фото → draft → reload → readiness10/10 → модальное подтверждение → published; сохранённое главное фото теряется — CE-C-01 |
| Создание организации через админку | PASS | Organization72 без филиалов: draft → reload → описание → pending → отдельное approve → публичный каталог и карточка |
| Создание события через админку | PASS | Event17: online, Organization72 организатор, даты2035-03-12 18–19 Asia/Baku, цена/телефон/фото → draft → reload → pending → published |
| Публичные карточки трёх admin-created объектов | PASS | RU/AZ/EN:9 GET200; PC/mobile снимки. Не заменяет проверку всех языковых полей каждого объекта |
| Ошибки фото места | PASS |12 browser checks: RU/AZ/EN × wrong extension/empty/>15MiB/corrupt. Ошибка видна; старый cover не удалён; удаление ошибочного replacement возвращает cover |
| Повреждённое фото события, обход клиентской проверки | PASS |3 реальных multipart POST на create RU/AZ/EN: сервер отклоняет изображение, возвращает ошибки и введённое название; карточка с маркером не создана |
| Клавиатура и геометрия форм создания | PASS в указанном объёме |96 экранов: owner/admin ×4 сущности ×3 языка ×4 ширины.15 Tab на экран; мобильные next/prev и desktop stepper specialist/event через Enter; native event format через ArrowRight/Left. Нет document overflow/pageerror. Это не обход каждого поля/диалога |
| Регрессии CE-RA-01, specialist admin, gallery и uploads | PASS |48 серверных тестов после финальной поправки,13.961s, exit0; точная команда ниже |
| Полный catalog1909 и JS38 | NOT RUN повторно | Они выполнены в предыдущей приёмке на исходной версии; не выдаются за свежий прогон этой задачи |

## 2. Сильные стороны

Canonical request/confirm/detach сохраняет необходимость согласий. Тестовые связи созданы через пользовательские операции, без прямого присваивания organization_id. Прямые и сетевые права расходятся после отвязки правильно. Конфликты не затирают новую версию. Публичное существование проверено HTTP и rendered browser, а не только статусом модели.

## 3. Реальные проблемы

**CE-RA-01 · P3 · закрыт локально.** RU/AZ показывали `Person verified at:`. Источник — readonly person_verified_at без локализованной подписи. Изменён только admin adapter: локализованная `identity_verification_date`, три перевода и регрессия. Значение получает прежний `display_for_field` для того же DateTimeField: сохраняются локальная дата и пустое `-`. Нет модели/миграции, изменений личности, публикации или ACL.

Первый RED:1 тест,6 failing subtests add/edit RU/AZ/EN до исправления; промежуточный GREEN33. Дополнительная проверка обнаружила, что необработанное возвращение datetime из admin method меняет формат и пустое значение: RED2 теста/2 failing subtests. Адаптер исправлен в собственном scope; финальные48 PASS. Исходные PO/MO восстановлены по первоначальным hashes после обнаруженного переформатирования инструментом, затем добавлена ровно одна запись на язык. [Сверка прежних переводов](content-completion-2026-10-09/translation-preservation.json): RU4264/AZ2662/EN2662 прежних runtime entries неизменны.

### CE-C-01 · P2 · Административное фото черновика исчезает при публикации

- Роль: demo_moderator, LOCAL final WORKTREE. URL: http://localhost:8790/admin/catalog/place/149/change/ (повторы — новые вымышленные карточки150/151).
- Шаги: создать permanent EDU через admin add → заполнить минимальные публикационные поля → выбрать корректное PNG96×96 как главное фото → сохранить → обновить страницу → убедиться, что фото показано из storage → нажать «Опубликовать» и подтвердить в модальном окне, без нового выбора файла → открыть редактор и публичную карточку.
- Ожидание: сохранённая обложка переходит из candidate в published; отсутствие нового upload не означает удалить сохранённый файл.
- Факт: draft/reload показывает сохранённое фото; после публикации `Place.photo` пуст, revision photo пуст, на публичной карточке placeholder «У этого места пока нет фотографий». Опубликованный status и HTTP200 не закрывают этот дефект. Ранний Place148 дал тот же результат; Place149 воспроизведён с явным контролем до/после; повтор151 со скриншотами.
- Доказательство: runs `admin-new-photo`/`admin-new-photo-first`, `admin_photo_probe`; screenshots `admin-photo-before-publish-390.png`, `admin-photo-after-publish-390.png` и PC1440; `admin-created-public-place-1440.png` показывает публичный placeholder. File multipart транспорт отдельно подтверждён в `admin-media`; загрузка/обычный draft save работает.
- Первопричина: `src/catalog/domain_admin/place.py:373`, `PlaceAdminForm.__init__`: candidate_for_edit применяется только для unbound GET. На bound POST instance содержит live photo (у нового draft пусто). `src/catalog/services/publication_forms.py:save_form` snapshot этого instance включает пустой photo; новый upload отсутствует, поэтому ранее сохранённая candidate обложка заменяется пустым значением до publish.
- Влияние: теряется ссылка на выбранную обложку, её приходится выбирать повторно. Удаление байтов storage не подтверждено. Gallery/ACL/network ownership этим кейсом не затронуты. Сценарий изменения обложки уже опубликованного места этим дефектом ещё не доказан.
- Confidence high; owner Django/publication forms; dependencies admin candidate binding. Приоритет P2 за ограниченную потерю одного media-поля в конкретном административном переходе. **Не исправлено: новый scope требует отдельного решения.**

Готовый промпт:

```text
Работай в /home/ramin/kidsmap. Прочитай AGENTS.md, docs/qa/content-entry-audit-2026-10-06.md и docs/qa/content-completion-2026-10-09.md. Исправь только CE-C-01: главное фото сохранённого административного черновика исчезает при публикации без нового upload. Перепроверь на текущем HEAD/WORKTREE; не считать исторический отчёт свежим доказательством. Сохрани чужие изменения. Только DJANGO_TESTING=1, isolated DB/cache/media, вымышленные данные, без внешних интеграций/production/commit/push/deploy.

Воспроизведение: admin permanent-place add → корректный PNG → сохранить → reload (обложка есть) → publish + modal confirm без нового файла → published/public (обложка исчезла). Источник: PlaceAdminForm.__init__ накладывает candidate только на GET, тогда как bound POST строится из live; publication_forms.save_form snapshot перезаписывает candidate photo пустым live значением.

Сначала падающая регрессия реального admin POST/user-visible public result. Минимально сохрани candidate photo/cover_photo на bound POST при отсутствии нового файла; явное удаление и новый upload должны продолжать работать. Не отключай CAS/token и права, не расширяй ACL, не меняй требования публикации. Не смешивай обложку и gallery. Проверь create draft → reload → publish, обычное повторное сохранение, изменение фото опубликованного → draft → publish, явное удаление, replacement, stale conflict, storage failure. RU/AZ/EN,360/390/768/1440, Enter/modal confirmation. Покажи собственный diff, exact commands, PC/mobile screenshots, PASS/FAIL/NOT RUN. Остальные findings не исправляй.
```

Диагностические ошибки harness не записаны как баги: ожидание slug input вместо readonly; неверные fixture fields; hidden native selects вместо существующих taxonomy pickers; попытка Enter по скрытому desktop stepper; пропуск модального подтверждения публикации. Дополнительные корректные прогоны перечислены в evidence. Первоначальный FAIL сетевого доступа после detach ожидал403/404, а приложение перенаправляет на dashboard200: свежий `network-access` подтвердил отсутствие редактора; service `has_action` возвращает false. Этот raw FAIL сохранён в evidence с объяснением, не скрыт и не считается уязвимостью.


### CE-C-02 · P3 · Подсказка карты противоречит серверной готовности

- Роль demo_moderator; URL http://localhost:8790/admin/catalog/place/151/change/ ; текущий final LOCAL WORKTREE.
- Шаги: открыть адрес/карту → прочитать «Адрес и точка на карте — два разных обязательных пункта» → увидеть «Координаты не указаны» → карточка всё равно опубликована, готовность10/10.
- Ожидание: интерфейс точно описывает действующее серверное требование. Факт: подсказка называет необязательную точку обязательной.
- Источник: `src/catalog/templates/admin/catalog/place/form/section_location.html:59`; `src/catalog/services/place_readiness.py:462` исключает coordinates/photo из blocking requirements. Четыре новые опубликованные QA карточки148–151 имеют lat/lng=NULL.
- Доказательство: map-copy browser FAIL, screenshots `map-required-copy-390.png`/`map-required-copy-1440.png`; map_probe aggregates. Ошибка подтверждена RU; смысл AZ/EN этой строки отдельно не сверялся.
- Влияние: вводит редактора в заблуждение о возможности публикации при неработающей карте. Confidence high, owner admin UX/i18n. **Не исправлено**, серверные требования не менять.

Готовый промпт:

```text
Работай в /home/ramin/kidsmap. Прочитай AGENTS.md и docs/qa/content-completion-2026-10-09.md. Исправь только CE-C-02: подсказка карты административного места называет точку обязательной, хотя серверные blocking requirements исключают coordinates. Перепроверь текущие HEAD/WORKTREE и оба условия. Меняй только подтверждённый текст/переводы/его другие использования, а не требования адреса, координат, публикации и доступа. Объясни точку как необязательную рекомендацию и возможность вернуться к карте позже. Сохрани чужие изменения; DJANGO_TESTING=1, изолированные DB/cache/media и вымышленные данные, без внешних интеграций/production/commit/push/deploy. Проверка RU/AZ/EN,360/390/768/1440 и клавиатура, карта недоступна, адрес без точки и сохранённая точка; rendered screenshots и точный PASS/FAIL/NOT RUN. Другие findings не исправляй.
```

## 4. Tech debt

Дата получила минимальный admin adapter вместо изменения model verbose_name и миграции. Общая очистка существующих PO/duplicate entries не проводилась; сохранены прежние переводы. QA launcher/fixtures/browser harness локальны и не являются штатной production-инфраструктурой.

## 5. Risks

Два browser contexts имитируют независимые вкладки/сессии без общей localStorage; конфликт с общей localStorage отдельно наблюдался, но финальный детерминированный CAS-прогон изолирует её. Это ограничивает вывод о восстановлении во всех сочетаниях вкладок. Внешние карты заблокированы; email приглашения остаётся LocMem. Изолированная QA не доказывает production-конфигурацию или реальные устройства.

## 6. Dead/legacy candidates

Новые кандидаты на удаление не установлены. Legacy join/detach и другие transports не удалялись. Никаких cleanup/migrations по результатам этой задачи.

## 7. Tests gaps — NOT RUN

- Полный повтор catalog/JS-suite после финальной косметической поправки; вместо него выполнен релевантный набор48.
- Полный клавиатурный обход каждого поля, taxonomy/practice selectors, всех nested tariff/group dialogs во всех языках/ширинах. Выполнены15 Tab на экран, шаги и формат; это отдельная ограниченная проверка.
- Настоящие NVDA/VoiceOver/TalkBack, физические телефоны, Safari/Firefox; измерение всего контраста автоматическим accessibility engine.
- Исчерпывающая файловая матрица: все поддерживаемые HEIC/HEIF/WEBP/EXIF,50MP/12000px, десятое/одиннадцатое фото,22MiB batch, identity/PDF certificate malformed и все комбинации ролей именно в этом прогоне. Серверный набор покрывает corrupt/MIME/>15MiB/storage failure/foreign gallery; приватность документов была проверена предыдущей приёмкой, заново все роли не проходились.
- Полный позитивный ввод каждого типа места и языковых вариантов через каждую форму; admin lifecycle этого прогона — один permanent EDU, одна сеть и один online event.
- Production, реальные карты/geocoding, внешние email/OAuth, реальные consent/employment integrations. Нет commit/push/deploy.

## 8. Recommendations и воспроизведение

CE-RA-01 готов к локальному просмотру. CE-C-01/CE-C-02 оформлены выше отдельными исправительными scope. Для полного sign-off нужен отдельный ручной accessibility/device проход и файловая матрица из раздела7.

Команды этой сессии, всё с изоляцией через runner:

```bash
.venv/bin/python .tmp/content-completion-20261009/launch.py
.venv/bin/python .tmp/content-completion-20261009/run_unit.py catalog.testcases.test_specialist_identity_date_label catalog.testcases.test_specialist_entry_admin catalog.testcases.test_content_entry_final catalog.testcases.image_uploads
.venv/bin/python .tmp/content-completion-20261009/run_browser.py labels
.venv/bin/python .tmp/content-completion-20261009/run_browser.py business-ten-preserved
.venv/bin/python .tmp/content-completion-20261009/run.py --script ten_preservation.py
.venv/bin/python .tmp/content-completion-20261009/run_browser.py detach-shared
.venv/bin/python .tmp/content-completion-20261009/run.py --script program_verify.py
.venv/bin/python .tmp/content-completion-20261009/run_browser.py two-tabs
.venv/bin/python .tmp/content-completion-20261009/run_browser.py admin-public
.venv/bin/python .tmp/content-completion-20261009/run_browser.py files
.venv/bin/python .tmp/content-completion-20261009/run_browser.py event-files
.venv/bin/python .tmp/content-completion-20261009/run_browser.py keyboard
.venv/bin/python .tmp/content-completion-20261009/package.py
```

Это перечень выполненных команд, не инструкция слепо повторять их поверх существующих fixtures: ten_preservation относится к состоянию до последующего program fixture/detach, lifecycle меняет тестовые статусы. Точные browser runs/results в evidence; детальные локальные logs в ignored scratch. Stand8790 оставлен для просмотра, restart только собственным launcher. Пароли/CSRF/operation tokens в отчёт не копировались.

Скриншоты: [Specialist PC](content-completion-2026-10-09/screenshots/identity-label-1440.png), [mobile](content-completion-2026-10-09/screenshots/identity-label-390.png), [подключение mobile](content-completion-2026-10-09/screenshots/business-ten-mobile.png), [отвязка](content-completion-2026-10-09/screenshots/detach-shared-mobile.png), [конфликт](content-completion-2026-10-09/screenshots/place-conflict-mobile.png), [ошибки фото](content-completion-2026-10-09/screenshots/file-errors-mobile.png), [публичное место PC](content-completion-2026-10-09/screenshots/admin-created-public-place-1440.png), [mobile](content-completion-2026-10-09/screenshots/admin-created-public-place-390.png). Все снимки перечислены в evidence. Вручную просмотрены PC/mobile исправленного специалиста, публичное место PC и mobile фото до/после публикации; остальные снимки не означают поэлементную экспертную оценку всей формы.

## 9. P0/P1/P2/P3 и решение

P0/P1: новых подтверждённых находок нет. P2 CE-C-01 — OPEN, отдельный промпт выше. P3 CE-C-02 — OPEN, CE-RA-01 — FIXED LOCAL. Решение: **FAIL административной обложки; остальные выполненные сценарии PASS, NOT RUN сохраняются**. Чужие изменения сохранены; собственный active_run завершён. Следующий исправительный scope — CE-C-01 по отдельному решению; ручной проход раздела7 остаётся открытым.
