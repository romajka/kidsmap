# Кабинет владельца: мероприятие — реализация и локальная приёмка

Дата: 2026-10-07. Реализован scope [согласованного плана](../superpowers/plans/2026-10-07-owner-event-entry.md). Это свежая проверка приложения, не приёмка исторического прототипа. Production не проверялся. Работу выполнил один исполнитель, без независимых субагентов.

## Версия и изоляция

- LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`; HEAD не изменён.
- До работы: dirty WORKTREE, 158 строк `git status --porcelain`, снимок 5121 Git-visible файлов в `baseline.json`. Сравнение выполнялось с начальным WORKTREE, а не только с HEAD.
- Последний запущенный стенд: <http://localhost:8787/qa/>. Его endpoint `/qa/acceptance-version/` возвращает digest исходников `d27c531cbd45cd5b3c66d1f2cd5619e7a30dc77ed775306ad1271adc5f9b1adb`, запуск `2026-10-07T13:42:50.351194+00:00`, `DJANGO_TESTING=true`, отсутствие внешних credentials, LocMem cache/email. Проверено из браузера.
- PostgreSQL: собственный контейнер `kidsmap-owner-event-implementation-20261007`, отдельный volume и Unix socket; network `none`, опубликованных DB-портов нет. Собственные DB/cache/media/private-media, guards сети и libpq, очищенное окружение. Остальные локальные стенды не перезапускались.
- Только seed-пользователи `demo_owner`, `demo_person`, `demo_moderator`, `demo_outsider` и вымышленные записи `QA 20261007`. Вход кнопками на `/qa/`; эти пользователи относятся только к этому стенду.
- Commit/push/deploy не выполнялись. `active_run` при начале отсутствовал.

Исходные снимки, команды, browser scripts, результаты и журнал ошибок сохранены вне Git: [/home/ramin/.local/share/kidsmap-qa/owner-event-entry-2026-10-07/](/home/ramin/.local/share/kidsmap-qa/owner-event-entry-2026-10-07/). Scratch: `/home/ramin/kidsmap/.tmp/owner-event-implementation-20261007/`.

## Исправления и первопричины

| Проблема | Причина | Исправление |
|---|---|---|
| Пустая форма не давала посмотреть следующий этап; индикаторы путали переход и готовность | Клиентские ограничения и отдельная модель «завершённого этапа» | Сохранены существующие 3 этапа; свободные переходы, видимый активный этап, фокус заголовка. Требования отправки поступают из owner-формы на сервере |
| Формат нельзя было нормально переключать клавиатурой | Кликабельные карточки без native radio semantics | Fieldset/radio, Space и стрелки, видимый focus. Мобильные стрелки переходов имеют текстовые знаки и доступные имена |
| Выбор организатора, площадки и телефона смешивал разные роли | Недостаточные пояснения и неявное заполнение телефона из Place | Организатор отдельно от места; закреплённый организатор в editor. Телефон события вводится явно либо отдельной кнопкой берётся у площадки. Ссылка создания организации ведёт в её workspace |
| Несохранённое называлось сохранённым; восстановление могло использовать старую версию | Нет подтверждения явного server-save и actor/entity/version границ локальной копии | Статусы loaded/unsaved/dirty/saving/saved/error/conflict; saved только после успешного ответа. SessionStorage-копия, явное сравнение/восстановление, привязка к пользователю и карточке. При stale version восстановление поверх свежей записи блокируется |
| Ошибки draft/dates могли становиться 500 | Категория обязательна в БД, а неполная пара дат доходила до domain без адресуемых ошибок | Ошибки категории и отсутствующей части интервала прикреплены к полям. Полностью пустой интервал draft разрешён по прежнему контракту |
| Неверная календарная дата и ошибка утверждённой истории давали 500 | `parse_datetime` выбрасывал ValueError; обработчик считал, что у любого ValidationError есть error_list | Неверная дата превращается в form error; поддержаны error_list/error_dict. `stale_version` определяется по коду, не словам перевода |
| Фото отклонялось клиентом при разрешённых сервером 2–15 MiB | Клиент имел отдельный лимит 2 MB/JPG-only | Limits/help берутся из действующей image pipeline. Видимый native input с label, ошибка файла сохраняет остальные поля. Одна главная фотография |
| Карта/недоступная площадка оставляли неясное состояние | Отсутствовал явный fallback | Необязательная карта; при её недоступности остаётся ввод адреса. Закрытая площадка не подменяется и её приватный адрес не раскрывается |
| Отмена и перенос были domain-операциями без owner UI | Не было adapters и экрана последствий | Отдельная страница управления и POST-операции поверх существующих cancel_event/reschedule_event; причина, версия, интервал Asia/Baku, подтверждение, состояния на dashboard |
| Тексты обещали качество, регистрацию, рассылку и фиксированный срок | Копирайт не соответствовал реализованным возможностям | Убраны эти обещания; подтверждение связи Specialist объяснено отдельно от оценки качества. Название/описание явно AZ, язык UI не создаёт перевод |

Чужие изменения сохранены: вне разрешённых файлов нет изменений относительно начального снимка. В `forms.py` изменён только `OwnerEventForm`; в прежних top-level definitions `views.py` изменены только `owner_event_create`/`owner_event_edit`, добавлены owner Event adapters. Политики `event_domain`, модели, миграции, access/publication, join/detach организаций, Place/Activity/Group/PricingPlan не менялись. Подтверждение фото/ограничения codec сохранены. Общий map picker получил только event-specific attribute; его JS не изменён.

В PO добавлены активные owner Event строки (RU: 40, AZ/EN: 41). Существующие активные переводы не заменялись; ключ «Перед отправкой» ранее был obsolete. Общие переводимые строки других форм сохранены.

## Проверки

PASS относится только к указанному виду проверки. Функциональные сценарии выполнялись на RU, языковая матрица — создание/editor/управление и навигация; все бизнес-сценарии на каждом языке не повторялись.

| Сценарий | Результат | Свежие доказательства / границы |
|---|---|---|
| Targeted backend/domain/security/concurrency/public/schema/image regression | PASS | 95 tests, 37.318 s, 0 failures/errors; `targeted-final.log`. После этого Python source не менялся, hash comparison PASS |
| Три этапа, пустая/заполненная форма, черновик с каждого этапа | PASS | Browser: реальный POST, redirect в editor, reload; фото и собственный адрес сохранились |
| Продолжение new/edit после refresh | PASS | Явное восстановление локальной копии; file не восстанавливается, его нужно выбрать заново |
| Организация / Specialist / нет организатора | PASS | Browser и backend: организация 1, подтверждённый Specialist 1, outsider без вариантов, чужой event GET/POST 403 |
| Очное, свой адрес без точки, площадка KidsMap | PASS | Browser POST/reload: свой адрес без координат; чужая публичная площадка 4, фактический адрес, явный телефон. Подтверждённый snapshot в опубликованном Event 10 |
| Онлайн | PASS | Specialist Event 11: draft→reload→submit→pending→domain approval→публичный GET. Нет related_place/physical address, фотография сохранена |
| Возраст 0, цена, контакты, AZ description | PASS | Event 10: age_from=0 сохранён, поля реального POST проверены; отсутствие телефона отклонено без потери ввода |
| Полночь Asia/Baku | PASS | 2035-02-04 23:30→2035-02-05 00:30: 60 минут в UTC и America/New_York browser; backend UTC 19:30→20:30, exact seconds/microseconds round-trip |
| Неполные/неверные даты, история утверждённого события | PASS | Backend regression: адресуемые ошибки вместо 500, начало/конец сохранены в bound form |
| Фото 3 MiB, неверный файл, >15 MiB | PASS | Browser 3 MiB→server normalization→reload, 16 MiB source error без потери текста; backend bad-file/oversize и existing image suite |
| Ошибка публикации → переход к полю | PASS | Browser: missing phone, поле не потеряно; ссылка раскрывает этап и фокусирует телефон |
| Отправка и публичная карточка нового события | PASS | Event 10/11: owner UI submit, approval через действующий domain service synthetic moderator, свежий public GET. Модераторский UI здесь НЕ проходился |
| Pending/published обычный editor закрыт | PASS | Browser redirect и backend assertions; content editor не разблокирован ради UI |
| Конфликт двух вкладок | PASS | Browser: свежий save, второй stale POST, сохранённый текст, code stale_version, reload и запрещённый stale restore. Existing real PostgreSQL contenders PASS |
| Повтор / чужие права отмены-переноса | PASS | Browser: повтор старого POST получает conflict, foreign GET 403; backend foreign POST, feature gate/POST-only, concurrent contenders |
| Отмена и перенос опубликованного | PASS | Event 7: новый интервал, затем отмена. ID/photo/snapshot сохранены, 2 history entries, deleted=false; публичные статусы сняты в браузере |
| Оборванный POST | PASS | Browser route.abort: после возврата в editor копия доступна и явно восстанавливается. Успех сохранения не показан |
| RU/AZ/EN × 360/390/768/1440 | PASS | 84 browser assertions: new/edit × 3 этапа × 12 сочетаний + 12 management. ScrollWidth ≤ viewport, 3 этапа, 1 видимый, Space/arrows для формата; 0 page errors |
| Клавиатура и доступные имена | PASS (ограниченно) | Space/ArrowLeft, Tab/Shift+Tab, focus error link, label photo. Enter открывает native chooser; его завершение через CLI вызвало ошибку automation context, поэтому полный native chooser upload cycle НЕ засчитан. Реальная загрузка проверена setInputFiles |
| System check | PASS | 0 issues; `checks.log`; own stand тоже выполняет check при старте |
| Makemigrations dry-run всего catalog | FAIL — ранее существовавший drift | Требует Meta options Activity/OfferingGroup/Organization/Program. Их модели и миграции этой задачей не менялись; migration не создана. Это не чистый общий check проекта |
| Полный репозиторный diff --check | FAIL — существующие чужие пробелы | Чужие файлы не чистились. Собственный добавленный trailing blank в Event template удалён |
| Реальный screen reader / мобильное устройство | NOT RUN | Только Chromium responsive и keyboard/accessibility semantics; NVDA/VoiceOver не запускались |
| Живая внешняя карта, геокодер и API key | NOT RUN | Внешние credentials отсутствуют; fallback проверен, провайдерная интеграция не проверялась |
| Реальный HEIF upload в браузере, квота/запрет sessionStorage | NOT RUN | Pipeline limits/codec branch проверены backend suite; реальные устройства/файлы и browser storage denial не имитировались |
| Отзыв organizer connection / закрытие venue конкурентным редактором в UI | NOT RUN (UI race) | Domain/security coverage PASS, закрытая площадка form-test PASS; такой race не воспроизводился двумя реальными браузерами |
| Rejected→исправление→повторная отправка, весь moderator UI | NOT RUN (полный browser cycle) | Existing backend Event contracts включены; новый browser acceptance этот цикл целиком не проходил |
| Повтор вручную воспроизведённого CREATE POST | NOT RUN | UI блокирует повторное нажатие во время запроса. Серверная идемпотентность создания этим scope не добавлялась; stale protection относится к редактированию/действиям |
| Весь тестовый suite, остальные сущности/production | NOT RUN | Только owner Event scope и нужные existing regressions |

Browser results: 18 functional checks, 6 management, 7 extra checks, 4 final checks, 84 matrix assertions — PASS. Это разные assertions, а не 119 полных end-to-end сценариев.

Команда серверной проверки (из `/home/ramin/kidsmap`):

```sh
.venv/bin/python .tmp/owner-event-implementation-20261007/run.py \
  catalog.testcases.test_owner_event_entry \
  catalog.testcases.test_task33_event_domain \
  catalog.testcases.test_task33_event_security \
  catalog.testcases.test_task33_event_concurrency \
  catalog.testcases.test_task33_event_owner_contract \
  catalog.testcases.test_task33_event_public \
  catalog.testcases.test_task33_event_dashboard \
  catalog.testcases.test_task33_event_schema \
  catalog.testcases.events_feature \
  catalog.testcases.image_uploads
```

Браузерная команда, отдельно для `browser_functional.js`, `browser_management.js`, `browser_extra.js`, `browser_final.js`, `browser_matrix.js`:

```sh
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh \
  --session owner-event-20261007 run-code \
  --filename .tmp/owner-event-implementation-20261007/browser_matrix.js
```

Сохранены и промежуточные неуспешные результаты: исходные regression RED, исправленный stale recovery FAIL, неверная wiring import, конфликт одновременного старта двух тестовых процессов в собственной test DB и native chooser automation error. Финальные server tests выполнялись последовательно и прошли; ошибки инструмента не выданы за ошибки приложения или успешные сценарии.

## Скриншоты

Файлы сняты с реального приложения на этом стенде. Full-page кадры имеют вертикальную прокрутку; это не горизонтальное переполнение. В Chromium scrollbar занимает 15 px: например, viewport 390 и document width 375.

| Кадр | Ссылка |
|---|---|
| PC, новое мероприятие, данные и дата | [1440](owner-event-design-2026-10-07/acceptance-2026-10-07/after-new-step1-1440.png) |
| Mobile, формат/площадка | [390](owner-event-design-2026-10-07/acceptance-2026-10-07/after-new-step2-390.png) |
| PC, фото и требования отправки | [1440](owner-event-design-2026-10-07/acceptance-2026-10-07/after-new-step3-1440.png) |
| Mobile, заполненный предпросмотр | [390](owner-event-design-2026-10-07/acceptance-2026-10-07/event-review-mobile.png) |
| Mobile, конфликт версии | [390](owner-event-design-2026-10-07/acceptance-2026-10-07/event-conflict-mobile.png) |
| Mobile, ошибка большого файла | [390](owner-event-design-2026-10-07/acceptance-2026-10-07/photo-error-mobile.png) |
| Управление опубликованным событием | [Mobile](owner-event-design-2026-10-07/acceptance-2026-10-07/manage-mobile.png) |
| Публичная карточка после переноса / отмены | [Перенос](owner-event-design-2026-10-07/acceptance-2026-10-07/public-rescheduled-mobile.png), [отмена](owner-event-design-2026-10-07/acceptance-2026-10-07/public-cancelled-mobile.png) |
| Новое очное после approval | [PC](owner-event-design-2026-10-07/acceptance-2026-10-07/new-public-pc.png) |
| Онлайн после approval | [Mobile](owner-event-design-2026-10-07/acceptance-2026-10-07/online-public-mobile.png) |
| Исходная форма | [PC](owner-event-design-2026-10-07/acceptance-2026-10-07/before-pc.png), [mobile](owner-event-design-2026-10-07/acceptance-2026-10-07/before-mobile.png) |

Для продолжения проверки стенда:

```sh
.venv/bin/python .tmp/owner-event-implementation-20261007/capture_runtime.py
.venv/bin/python .tmp/owner-event-implementation-20261007/launch.py
```

Launch проверяет ownership контейнера/PID, перезапускает только собственный localhost:8787 и сохраняет собственный fixture volume. Не запускайте два `run.py` test процесса одновременно: они используют одну собственную test DB. Общая приёмка всех типов карточек и production release остаются отдельными задачами.
