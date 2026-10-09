# Мероприятие в кабинете владельца: актуальный аудит и дизайн

## 1. Состояние и границы

2026-10-07, LOCAL dirty WORKTREE, `task33-progress`, HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, `active_run: NONE`. **План и макеты, awaiting user review. Application code не изменялся.** Не выполнялись commit/push/deploy. Production не открывался. Предыдущие dirty/untracked изменения сохранены.

Прочитаны реальные AGENTS.md, registry/каноническая роль orchestrator, architecture/source-of-truth/audit/engineering contract и исходный content-entry audit. Владелец результата один; независимые subagent-аудиты не заявляются. Применены KidsMap UI/design, planning, accessibility и verification skills.

Исследование по source + guarded PostgreSQL tests + rendered Chromium. Основной current stand: `http://localhost:8781`, изолированные QA DB/cache/public media/private media; макет: `127.0.0.1:8782`. Снимок запуска и guards — `.tmp/event-admin-fix-20261006/run.py`. Тесты не используют `.env`/production credentials. Записи в browser — только role sessions/временный sessionStorage, Event POST в браузере не выполнялся. Создание/POST probes проходили в test DB с откатом TestCase.

## 2. Что уже работает

- **Три этапа уже существуют**, draft buttons есть на каждом, первый этап не требует нового процесса.
- Organization и Specialist выбираются отдельно от venue. Server ACL проверяет актуального владельца организации/подтверждённого человека, не legacy Event.owner или владельца площадки.
- Online отключает очные поля в UI и очищает их на сервере; обратное переключение до сохранения сохраняет браузерный ввод.
- Даты уже используют Asia/Baku, отдельную end_date для ночного интервала, защиту точного approved interval. Возраст 0 допускается, пустота проверяется отдельно.
- Черновик сохраняется как canonical Event; повторное открытие подтверждено test HTTP.
- Существуют version lock, immutable venue_snapshot, причины/history отмены и переноса. Public fixtures показывают «Отменено»/«Перенесено» на RU/AZ/EN.
- При отсутствии Maps API карта уже показывает fallback. Карта для Event необязательна. Отсутствие fallback нельзя повторять как текущую общую проблему.
- **Overflow не воспроизведён:** 72 current render contexts: new/edit × 3 этапа × RU/AZ/EN × 360/390/768/1440. Для переходов новая карточка заполнена вымышленными валидными значениями; записи на сервер не было.
- Видимые flatpickr alt-inputs имеют implicit label через родительский label. Отсутствие доступного имени date inputs не подтверждено; отдельно нужен корректный переход с ошибки hidden input на visible altInput.

## 3. Подтверждённые проблемы и причины

| Приоритет | Проблема | Причина и доказательство | Предлагаемое исправление |
|---|---|---|---|
| P1 | Черновик без категории вызывает IntegrityError | OwnerEventForm draft снимает required со всех полей; Event.category NOT NULL. Probe: form valid, POST падает, Event count не изменяется | Category draft validation и адресуемая ошибка; сохранить NOT NULL |
| P1 | Текст новой карточки появляется после смены аккаунта | sessionStorage key содержит URL, но не actor. Live browser: owner new title восстановился у outsider. Existing edit title после refresh не восстановился | Account/entity/schema/base-version scoped recovery, без восстановления прежних unscoped keys |
| P1 | Восстановление неполно, локальная копия очищается до результата | restore только если title пуст; не применяет сохранённый format, не сохраняет related_place/region/coordinates/venue choice; clearStorage вызывается при submit | Полный allowlist scalar values; clear после server acknowledgement; existing edits/version-aware comparison |
| P1 | Недоступен клавиатурный выбор формата | Две `.km-format-card` — div без role/tabindex; настоящий select скрыт. RU/AZ/EN: `.focus()` не выбирает card, native format radios = 0 | Native radio, fieldset/legend; не имитировать radio через div |
| P1 | Специальный conflict UI может не появиться | Controller теряет `ValidationError.code`; JS ищет слова. Реальный текст «Событие изменилось…» не совпадает с проверкой «изменен». Test stale POST: HTTP200/nonfield, сервер не перезаписал запись | Передать `stale_version`; inline conflict + введённые значения + сравнение, без автоматического retry |
| P2 | Проход ко второму этапу требует все publish поля первого | `validateCurrentStep` блокирует organizer/name/category/date/age/price/phone/description. Невозможно сначала выбрать площадку/её телефон и продолжить неполный draft | Разделить переход, сохранение draft и отправку; серверную проверку оставить |
| P2 | Телефон площадки ошибочно обещан как замена пустого телефона | `clean_phone` добавляет field error раньше `clean` fallback. Probe с valid venue phone и пустым event.phone FAIL. Заполненный cleaned phone не удаляет field error | Явно копировать телефон по действию владельца; убрать противоречивую подсказку, не смягчать required |
| P2 | Клиент запрещает часть допустимых фотографий | JS max 2 MB + JPG/PNG/WEBP; pipeline source 15 MiB, HEIF, output 2 MiB. Browser rejects 2.1 MB; отдельный valid PNG >2 MiB accepted/normalized сервером | Использовать shared image config для ограничений/текста; сохранить pipeline |
| P2 | Адрес предпросмотра может отличаться от published snapshot площадки | На выбранной Place можно править Event.address; JS preview читает address input, capture_venue_snapshot читает фактическую Place.address | Показывать источник адреса; own address — явный выбор. Расхождение установлено по source, отдельный browser publish кейс ещё не выполнялся |
| P2 | «Подтверждённый профиль обеспечивает доверие» вводит в заблуждение | Organization queryset не требует проверки качества/публикации. Specialist identity — связь человека с профилем, не гарантия услуги. Copy обещает больше контракта | Объяснить реальные права организатора и identity отдельно от качества |
| P2 | Online copy обещает регистрацию и отправку ссылки | Текст формы говорит о зарегистрированных участниках/ссылке по телефону; в проверенных owner Event form/controller/routes нет процесса регистрации/рассылки | Связаться с организатором по контакту, без обещания механизма |
| P2 | Нет owner кнопок/HTTP adapters отмены и переноса | Есть domain services и tests, current owner routes — create/edit/submit/delete. Опубликованная карточка не открывается ordinary edit | Тонкие POST adapters существующих сервисов с прежними ACL/version/reason |
| P3 | Публикационные «звёздочки» не объясняют черновик; пустые тексты preview частично RU | UI не разделяет draft minimum и submit checklist, некоторые placeholder строки жёстко RU | Два списка требований и локализованные состояния RU/AZ/EN |

Даты через полночь сами по себе **не сломаны**: нужен явный следующий end_date. Основная UX задача — объяснить и сфокусировать ошибку. Map provider=unavailable fallback подтверждён; сетевой сбой подключённого Google Maps отдельно не воспроизведён. Cancel/reschedule backend не считаются отсутствующими: отсутствует owner HTTP/UI.

## 4. Технический долг и карта источников

| Источник | Роль |
|---|---|
| [OwnerEventForm](/home/ramin/kidsmap/src/catalog/forms.py:1818) | Querysets, phone/date/draft/image validation, Baku round-trip |
| [Owner controller](/home/ramin/kidsmap/src/catalog/controllers/owner_events_controller.py:16) | Missing submit fields, create/edit/submit, loss of validation code |
| [event_domain](/home/ramin/kidsmap/src/catalog/services/event_domain.py:17) | Fresh organizer permission, locking/version, snapshot, submit/publish/cancel/reschedule |
| [Owner views](/home/ramin/kidsmap/src/catalog/views.py:1130), [routes](/home/ramin/kidsmap/src/catalog/urls.py:201) | Feature-gated HTTP adapters; pending/published redirects |
| [Owner template](/home/ramin/kidsmap/src/catalog/templates/pages/owner_event_form.html:122) | Existing 3 steps, unsupported copy, DIV formats, preview/file help |
| [Owner JS](/home/ramin/kidsmap/static/js/owner_event_form.js:142) | Navigation gate, local recovery, file limit, language-word conflict detection |
| [Map picker](/home/ramin/kidsmap/static/js/owner_place_map_picker.js:455) | Existing no-provider fallback; Google fallback retry restricted to permanent-map option |
| [Image pipeline](/home/ramin/kidsmap/src/catalog/services/image_uploads.py:21) | Existing input/output limits and normalization; не изменяем |
| [Public Event](/home/ramin/kidsmap/src/catalog/templates/catalog/event_detail.html:18) | Existing occurrence state and public venue presentation |

Graph использован для структурного поиска и callers, затем прочитан актуальный source. Coverage best effort: owner HTML partial range 1–538, public template partial 46/106; соответствующие участки перепроверены напрямую. Python/JS cited paths metadata match. Не заявляется полнота всего проекта или отсутствие регистрации вне ограниченного owner Event flow.

## 5. Риски

- Нельзя расширять права автора предложения Specialist, staff, venue owner или legacy Event.owner ради удобства выбора.
- Новый UI обязан соблюдать неизменность organiser/approved format/snapshot, разделять status публикации и occurrence state. Отмена не soft-delete, перенос не ordinary content edit.
- Recovery должен исключить чужой аккаунт и stale base version, не хранить file/CSRF и не обещать сохранение файла после refresh.
- Не менять category nullability, domain date validation, publish policy или лимиты image pipeline ради «меньше ошибок».
- Shared map/datetime/image helpers и gettext уже используются другими страницами: после точечного изменения требуется consumer impact check, а не массовая подмена переводов.

## 6. Legacy и сохранение изменений

Resolved Event ACL и unresolved исторические Event различаются; не разрешать unresolved права через legacy owner. Unknown organizer/snapshot не достраивать по текущей площадке. Cancel/reschedule сохраняют immutable occurrence history и исходные фотографии/площадку.

Перед работой сохранён SHA256 manifest 4488 существовавших Git-visible файлов в `.tmp/owner-event-design-20261007/before-manifest.json`. Финальная сверка описана в `owner-event-design-2026-10-07/preservation-results.json`. Правки application и чужих QA/design файлов не входят в эту задачу.

## 7. Выполненные проверки и ограничения

### PostgreSQL / source

Точные команды из `/home/ramin/kidsmap`:

```bash
.venv/bin/python .tmp/event-admin-fix-20261006/run.py catalog.testcases.test_task33_event_domain catalog.testcases.test_task33_event_owner_contract catalog.testcases.test_task33_event_public catalog.testcases.test_task33_event_schema catalog.testcases.test_task33_event_concurrency catalog.testcases.test_task33_event_dashboard catalog.testcases.test_task33_event_security
.venv/bin/python .tmp/owner-event-design-20261007/run.py catalog.testcases.test_task33_event_domain catalog.testcases.test_task33_event_owner_contract catalog.testcases.test_task33_event_public catalog.testcases.test_task33_event_schema catalog.testcases.test_task33_event_concurrency catalog.testcases.test_task33_event_dashboard catalog.testcases.test_task33_event_security probes
.venv/bin/python .tmp/owner-event-design-20261007/run.py catalog.testcases.test_task33_event_domain catalog.testcases.test_task33_event_owner_contract catalog.testcases.test_task33_event_public catalog.testcases.test_task33_event_schema catalog.testcases.test_task33_event_concurrency catalog.testcases.test_task33_event_dashboard catalog.testcases.test_task33_event_security
.venv/bin/python .tmp/owner-event-design-20261007/run.py image_probe
```

| Запуск | Результат | Ограничение |
|---|---|---|
| Original runner, 62 tests | 19 errors / 36.105 s | Security fixtures создают Place с EDU без Category EDU; teardown FK violation. Это неисправность fixture, не доказанная регрессия ACL |
| Scratch runner, 62 existing + 10 probes | 71 passed, 1 failure / 35.464 s | В synthetic setUp добавлена Category EDU, assertions/source не менялись. Единственный FAIL — ожидаемое наследование venue phone, подтверждённый текущий bug |
| Scratch runner, 62 existing | **62 passed / 35.342 s**, exit 0 | Та же явно описанная fixture correction. Не выдаётся за unmodified original-runner green |
| Source image probe | **1 passed / 0.094 s**, exit 0 | Валидный PNG >2 MiB принят существующим normalizer и уменьшен ≤2 MiB. Не новый frontend fix |

9 успешных диагностических probes: category IntegrityError воспроизведён; minimum organiser+category draft/reopen; partial dates rejected; physical own address без map; online overnight при timezone override America/New_York; stale POST не перезаписывает; verified-person vs author; interval/age/file field errors; organiser edit forbidden. Probe, проверяющий существующий дефект, может проходить потому, что фиксирует его наличие; это не доказательство исправления.

Tests используют DJANGO_TESTING=1, guarded settings, isolated `test_qa_stage04`, LocMem cache/mail и отдельные media. `keepdb` сохраняет исключительно test DB. Existing model/migration drift warning оставлен; `makemigrations` не запускался. Полный suite не запускался. Logs и scratch fixture/probes находятся в `.tmp/owner-event-design-20261007/` и не включают production данные.

### Browser

- Current: 72 contexts new/edit × 3 steps × RU/AZ/EN × 4 widths, overflow 0, active step и locale совпали; synthetic input только в browser.
- Current: keyboard format недоступен на 3 языках; mouse online скрывает/отключает physical inputs, обратное переключение сохраняет venue/address.
- Current: source 2.1 MB file отвергнут frontend на 3 языках; no upload/POST. Файл был диагностическим буфером для size gate, не использовался как доказательство нормального декодирования.
- Current: local recovery owner new→refresh работает, existing edit→refresh не восстанавливает unsaved title; owner→outsider восстанавливает чужой текст. Тестовые storage keys очищены.
- Current public: 6 GETs — cancelled/rescheduled × RU/AZ/EN; существующие state labels отображены. Это не browser end-to-end нового owner action.
- Prototype: **240 render contexts** — 14 states × 3 languages × 4 widths и отдельно 3 steps × new/edit × languages × widths; overflow 0, JS page errors 0. **39 interaction checks**: radio ArrowRight/Space, Tab skips hidden controls, step Enter→heading, draft demo с каждого этапа, error→field, overnight correction, phone copy, conflict retains input, cancel/reschedule reason и защита повторной кнопки. Клавиатура проверяется в HTML макете; все сохранения/переносы в нём демонстрационные.

Результаты browser и макета — JSON рядом со скриншотами. Геометрические проверки не заменяют ручную оценку каждого текста/состояния или реальный screen-reader smoke test.

**Не проверено:** реализация предложенного scope; живое сохранение/отправка с каждого этапа в браузере; actual maps API/network failure; реальный screen reader/iOS/Android; HEIF codec по ролям/устройствам; browser concurrent editors; новый owner cancel/reschedule POST и полный public after approval. Эти проверки обязательны после согласования и реализации. Production/полный suite не входят в текущую приёмку.

## 8. Рекомендация и макеты

Лучший вариант — улучшить существующий wizard, нормализовать его validation/recovery и подключить существующие occurrence services. Подробный scope, сохранённые правила, перечень файлов и post-implementation acceptance: [план](/home/ramin/kidsmap/docs/superpowers/plans/2026-10-07-owner-event-entry.md).

[Интерактивный макет](http://localhost:8782/docs/qa/owner-event-design-2026-10-07/prototype.html?lang=ru&step=2). Переключатель состояния включает новую карточку, editing, online, empty organiser, unavailable venue/map, date/file error, conflict, pending/rejected, cancel/reschedule. Кнопки не обращаются к API. Макет не является запущенной новой формой приложения.

Основные изображения: `owner-event-design-2026-10-07/proposed-pc.png`, `proposed-mobile-viewport.png`; дополнительные PC/mobile для этапов/ошибок/действий в той же папке. До: `current-step1-pc.png`, `current-step1-mobile.png`, `current-step2-mobile.png`, `current-physical-mobile.png`.

Проверка static макета после перезапуска сервера:

```bash
cd /home/ramin/kidsmap
python3 -m http.server 8782 --bind 127.0.0.1
```

Сервер локальный, не открывать его на внешнем интерфейсе. Приложение 8781 использует существующий guarded QA launcher; ничего не менять в production.

## 9. Приоритеты и следующий шаг

P1: draft category error вместо 500, keyboard radio, безопасное account/version recovery, явный conflict state. P2: navigation vs publish, venue phone, source image limits, честные тексты, preview/address consistency, owner cancel/reschedule. P3: локализация подсказок и визуальная иерархия.

Остановиться на этих артефактах. Реализацию выполнять только после согласования плана пользователем. Scope других форм из предыдущих запросов не считается согласованным этим аудитом.
