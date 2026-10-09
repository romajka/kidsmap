# Постоянные места KidsMap — реализация и приёмка, 2026-10-07

**Изменения согласованного интерфейса внедрены. Полная приёмка не пройдена:** остаются потеря сохранённого главного фото при отправке и неверная проверка в старом экране модерации. Эти серверные проблемы вынесены отдельно; правила сохранения и публикации не изменялись.

Исполнитель: один Codex /root, последовательно, без независимых подагентов. Основание: пользователь согласовал [план постоянных мест](/home/ramin/kidsmap/docs/superpowers/plans/2026-10-06-permanent-place-form-design.md). Планы организаций, специалистов и кабинета мероприятий в этой реализации не выполнялись. AGENTS.md, canonical agent instructions, исходный аудит и design/spec прочитаны. Исторические отчёты не использованы как доказательство новой приёмки.

## Версия, среда и сохранность

- LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`; HEAD не изменён.
- Старт работы: `2026-10-07T08:21:55.400705+00:00` (12:21 Asia/Baku). Стартовый WORKTREE: 110 записей статуса, SHA256 4924 Git-visible файлов, включая чужие dirty/untracked изменения.
- Финальный исходный код: HEAD + WORKTREE; digest `30ed04103232e9a0c1ed69a8f9a98a0370b57b3454073952b5e00cbd4c737aa6`. CSS/JS версии `20261007_place_r5`.
- Финальный процесс стенда запущен `2026-10-07T09:53:17.418177+00:00` (13:53 Asia/Baku), PID 3003976, без autoreload. Версия прочитана из [локального endpoint](http://localhost:8784/qa/acceptance-version/) и сохранена в [runtime-version.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/runtime-version.json).
- Новый стенд: [localhost:8784/qa/](http://localhost:8784/qa/). PostgreSQL 17, контейнер `kidsmap-place-form-implementation-20261007`, volume `kidsmap-place-form-implementation-20261007-data`, network=none, без опубликованных DB-портов. 170 миграций применены только в новой QA БД.
- `DJANGO_TESTING=1`, отдельные DB/cache/media/private-media, LocMem email, внешние credentials отсутствуют; сетевые и libpq guards. Браузерные данные в `qa_stage04`, тесты создавали и удаляли только `test_qa_stage04`. Seed выполнен один раз; перезапуски сохраняли fixtures.
- Только вымышленные роли и карточки. Старые стенды 8780–8783 не изменялись; 8783 использовался в начале только для чтения исходных RED-сценариев. PRODUCTION не проверялась и не изменялась. Commit/push/deploy не выполнялись.
- Из начальных файлов изменены 24 разрешённых application-файла; остальные 4900 совпали с исходными хешами перед записью финальных документов. [preservation.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/preservation.json) содержит список. AST-сверка: 35 методов `clean*`/`save*` форм не изменены; EventAdmin, EventAdminForm и остальные Event-классы в общем модуле не изменены. В PlaceAdmin изменены только два presentation-метода; существующие функции readiness не изменены. Модели, миграции, контроллеры, ACL и бизнес-сервисы сохранения не тронуты этой работой.
- После этой сверки отдельно обновлены статус/checkboxes согласованного плана и добавлено уточнение в предыдущий отчёт приёмки. Исходный текст предыдущего отчёта сохранён целиком. [Финальная сверка](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/final-preservation.json): 24 application-файла + 2 документа, остальные 4898 исходных файлов без изменений; frozen source совпадает. Компилированные игнорируемые `.mo` обновлены локально; их стартовые хеши не были сняты, поэтому сохранность старых `.mo` не заявляется.

## Что исправлено и почему

| Область | Первопричина | Изменение |
| --- | --- | --- |
| Общий билет/вход | Неверная кавычка в `data-tariff-editor` мешала инициализации редактора | Исправлен атрибут существующего редактора. Строки тарифов создаются, сохраняются и восстанавливаются. |
| Новая форма после reload | `fresh=1` повторно трактовался как начало; отсутствовала точная ссылка на сохранённый ServerDraft | В URL сохраняются draft session/ID, `fresh` убирается после первого сохранения. Восстанавливается именно текущий черновик. |
| Быстрый ввод/конфликт | Старый ответ мог обозначить новый ввод сохранённым; после reload конфликт терялся | Сохранение сериализовано с повтором актуального ввода; 409 сохраняет локальный ввод и блокирует дальнейшие записи. Актуальная версия открывается отдельно, без автоматического слияния. |
| Фото при явном сохранении | Кнопка сохраняла только JSON текста | Подключён существующий `KidsMapPhotoEditor.save` и его штатные RPC. Выбранные файлы требуют явного сохранения. При потере ответа повтор использует прежний request ID. |
| Кандидат при повторном открытии | Часть presentation брала live nature/расписание/главное фото вместо редакции | Для unbound GET используются сохранённые значения редакции и безопасный preview галереи. Bound validation/save оставлены прежними; их дефект PP-01 остаётся. |
| Готовность | Представление админки не подгружало существующие nested groups, поэтому цена группы считалась отсутствующей | Read-only adapter получает текущий снимок формы и существующий результат readiness. Админка подгружает сериализацию существующих Group/Plan; центр с двумя тарифами показывает 10/10. |
| Неверные переводы | AZ/EN каталоги переводили «Описание (AZ/RU/EN)» как «Расписание»; RU «Удалить» — как «Удалил» | Исправлены соответствующие записи PO. Общие потребители проверены по исходникам: Place/Event description, фото Event/Place, Specialist delete, schedule editor; targeted tests включают общие тарифы, фото и Volunteer. Полный браузерный проход Event/Specialist в этой работе не выполнен. |
| Длинная форма и телефон | Не было компактного выбора раздела; общий `overflow-x:hidden` делал предка фиктивным scroll container и ломал sticky | PC-навигация, native select на телефоне, видимое сохранение и действия. Scoped `overflow-x:clip` исправляет sticky; редакторы Activity/Group/Plan сворачиваются с summary. Общая Program подписана отдельно от местного занятия. |
| Ошибки/клавиатура | Ошибки не имели надёжного фокуса и связей с полями; языковые tabs не поддерживали полную клавиатурную навигацию | Сводка ошибок, раскрытие секций/details, фокус поля, `aria-invalid`/`aria-describedby`; Arrow/Home/End и roving tabindex в языковых tabs админки. |
| Ложный native blocker | Скрытые advanced controls тарифа блокировали валидную бесплатную карточку | Перед существующим photo RPC убран общий `checkValidity()` по скрытым controls. Финальная серверная валидация остаётся и возвращает локализованные ошибки. |

В кабинете остаётся одна непрерывная форма с **4 свободными разделами**. В админке — **5 разделов** той же формы. Нового параллельного процесса или обязательного Next/Back нет. В админке автосохранение не добавлено.

Четыре противоречия разрешены так:

- **Точка на карте необязательна.** Адрес нужен для отправки; указанные координаты по-прежнему валидируются. Фото — рекомендация, а 1200×1200 — рекомендация размера. Действующие ограничения файла сохранены.
- **Переводы автоматически не создаются.** Preview/public используют выбранный язык → AZ → существующий legacy fallback. Пустые RU/EN не заполняются чужим текстом в базе.
- **Разделы не этапы.** Можно свободно переходить между четырьмя owner-разделами; старое обещание пяти этапов исправлено.
- **Текстовый черновик и отправка различаются.** Неполный owner ServerDraft сохраняется; файлы — только явным действием. Для отправки отображаются текущие **10 серверных пунктов**, условный район Баку и контакты «одно из допустимых средств». Public space и подтверждённое наследование контакта учитываются. После изменения данных старый checklist не выдаётся за новую серверную проверку. Сохранение не обещает публикацию.

Добавлены понятные подписи New/Draft/Pending/Published/Rejected/Changes requested. Реально пройдены New/Draft/Pending/Published; отклонение и возврат на доработку в этом запуске отдельно не воспроизводились. Live и candidate показываются раздельно.

## Проверки

PASS относится только к указанному действию; успешные тесты и матрица не отменяют PP-01/02.

| Сценарий | Результат | Свежие доказательства и предел |
| --- | --- | --- |
| Create/edit owner и admin, RU/AZ/EN, 360/390/768/1440 | **PASS 48/48** | [owner-matrix.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/owner-matrix.json), [admin-matrix.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/admin-matrix.json). HTTP 200, реальная форма, правильный html lang, navigation, отсутствие горизонтального overflow; 48 screenshots. Финальная версия r5. Это базовая матрица страниц, не 48 полных публикационных циклов. |
| Клавиатура и возрастная ошибка, оба интерфейса × языки × ширины | **PASS 24/24** | [owner-keyboard.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/owner-keyboard.json), [admin-keyboard.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/admin-keyboard.json). Summary → Enter → `id_age_to`, Tab/Shift+Tab; поле видно между sticky панелями; ARIA-связи. Admin ArrowRight/Home/End проверены. Reduced motion. |
| Пустая owner-форма → частичный текст → ServerDraft → reload → продолжение | **PASS** | Парк, студия, центр, событийная площадка; отдельные workflow JSON. Восстановление exact draft с `fresh=1` исправлено. |
| Общественный парк №4 без контакта/координат, возраст 0–18, общий бесплатный вход | **PASS для текста/публикации; FAIL для главного фото** | Черновик/reload, возрастная ошибка, исправление, отправка, approval UI центра модерации, public. Галерея сохранилась; главное фото потерялось на последующей отправке. |
| Студия №5 без Activity, входной билет 12 AZN | **PASS** | [studio-workflow.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/studio-workflow.json). Первоначальный текст с `test` правильно отклонён; после исправления отправка и approval выполнены. Исходный FAIL-ответ оставлен в evidence. |
| Центр №6: Activity, две Group и два PricingPlan | **PASS** | [center-workflow.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/center-workflow.json). Часы Place Пн–Пт 09–18 отдельно от групп Ср 14–15 / Пт 16–17. После approval созданы отдельные ID. В owner/admin после reload видны обе группы; готовность 10/10. |
| Событийная площадка №7, schedule_mode=events, тариф event 30 AZN | **PASS в доступном owner-редакторе** | [venue-workflow.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/venue-workflow.json). Никакое Event не создавалось. Отдельный `price_mode=events` в owner не выставлялся: такого control там нет; этот вариант NOT RUN. |
| Четыре новых карточки → модерация → public | **PASS через существующий центр модерации** | Реальные UI-кнопки `/admin/volunteer/moderation/content/1…4/`, затем public №4–7. Прямого approval API/SQL для обхода не было. Старый `/admin/volunteer/review/` проверяется отдельной строкой ниже. |
| Published owner-edit №6: цены 15/25 → draft 17/27 → отправка → approval | **PASS** | [pre-approval-place-state.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/pre-approval-place-state.json): live 15/25 до решения. [final-place-state.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/final-place-state.json): 17/27 после approval, прежние Group ID 5/6 и Plan ID 10/11. Atomic/concurrency контракт дополнительно покрыт targeted tests. |
| Филиал №1 подтверждённой организации, наследуемый контакт и Program | **PASS** | [confirmed-branch.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/confirmed-branch.json). Собственный phone1 очищен, 10/10; draft/reload, отправка owner, approval UI content/7. Organization 1, Activity 1 → Program 1, Group 1 → Plan 4 сохранились; локальные Activity/Group/Plan тоже остались. |
| Public №4–7: RU/AZ/EN × 390/1440 | **PASS 24/24** | [public-matrix.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/public-matrix.json): HTTP 200, AZ fallback и без overflow. В новых записях RU/EN остаются пустыми, не создаются «переводы». |
| Явный photo draft + reload, смена главного файла, порядок галереи | **PASS для первого сохранения; FAIL для следующей отправки** | [photo-regression.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/photo-regression.json), №9. Главное фото и две gallery-строки видны до submit. Парк №4 опубликовал gallery-two → gallery-one; persisted IDs и порядок сохранены. PP-01/03. |
| Сервер сохранил фото, ответ потерян; повтор кнопки | **PASS** | Для №9 после успешного server fetch искусственно возвращён 503. UI сохранил выбранные файлы; повтор вернул тот же Place №9. В DB одна карточка с этим synthetic названием. Это transport-fault injection, не реальная авария внешнего сервиса. |
| Две вкладки: stale 409 → reload → повтор сохранения → открыть актуальную | **PASS** | [recovery.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/recovery.json). B остаётся conflict, локальный B-ввод сохранён; POST заблокирован; отдельная вкладка показывает A. |
| Быстрый ввод с задержанным ответом / offline / blocked localStorage | **PASS с указанным пределом** | recovery.json: отправлены первая и последняя версии, сохранена последняя; offline-ввод восстановился после подключения. С blocked localStorage exact server draft восстановился по URL; остаётся честное предупреждение о недоступности browser fallback. |
| Чужие права | **PASS для owner Place и ServerDraft** | demo_outsider получил 403 на чужой draft; чужой редактор №6 не показан, redirect к списку. Матрица всех ролей/приватных документов других сущностей в этот scope не входила. |
| Admin: новая неполная карточка №8 → ручной draft → reload → ошибка возраста → исправить/сохранить | **PASS** | Сохранённая редакция №5 содержит name_az и возраст 9–12; после reload UI показывает сохранённый candidate и «Все изменения сохранены». Ошибочный 9–1 получает summary/focus; исправление проверено. Базовый Place остаётся draft, кандидат хранится отдельно. |
| Admin: полный ручной publish и изменение опубликованного этим же UI | **NOT RUN до успешного завершения** | Дополнительная попытка остановилась на таймаутах браузерного инструмента. Последняя DB-сверка: №8 draft, редакция draft; публикация этим путём не заявляется. Контракт admin/publication покрыт targeted tests, что не заменяет UI-приёмку. |
| Старый экран volunteer review | **FAIL** | PP-02: текущий №6 с групповыми ценами всё ещё получает «Перенесите существующую цену в тарифы…». Рабочий центр модерации не отменяет этот дефект. |
| Серверные targeted tests | **PASS 183/183** | Финальный запуск 43.639 s, exit 0, system check 0 issues; [final-tests.log](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/final-tests.log). Это не весь suite. |

Команда финального тестового запуска из `/home/ramin/kidsmap`:

```bash
.venv/bin/python .tmp/place-form-implementation-20261007/run.py \
  catalog.testcases.test_task33_place_continuous \
  catalog.testcases.permanent_place_wizard \
  catalog.testcases.place_readiness \
  catalog.testcases.test_localized_place_admin \
  catalog.testcases.test_task33_drafts \
  catalog.testcases.test_task33_pricing \
  catalog.testcases.test_task33_publication \
  catalog.testcases.test_task33_public_details \
  catalog.testcases.photo_workflow \
  catalog.testcases.test_volunteer_dashboard
```

`node --check` прошёл для owner_place_continuous.js, owner_place_offerings.js, kidsmap_place_form.js и kidsmap_place_media.js. Проверены только добавленные строки относительно исходного WORKTREE: новых trailing whitespace нет; старые чужие строки не чистились. Содержательные RED/green регрессии включают readiness/group-only pricing, candidate presentation, фактический admin GET nested groups. [admin-render-red.log](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/admin-render-red.log) сохранён. Один промежуточный запуск с keepdb попал в оставшуюся пустую test DB после flush и дал taxonomy FK-ошибки; исправлена изоляция launcher (`keepdb=False`), assertions приложения не ослаблялись.

## Отдельные оставшиеся задачи

### PP-01 — P1: потеря сохранённого главного фото при отправке

- Роль: владелец. URL: [Place №9 edit](http://localhost:8784/ru/account/places/9/edit/).
- Шаги: создать карточку с cover и двумя gallery-фото → явно сохранить черновик → reload → убедиться, что cover отображается → отправить без повторного выбора cover.
- Ожидание: сохранённое главное фото входит в pending candidate и последующую публикацию.
- Факт: до отправки `/media/places/cover_AicmRl2.webp` показан; после отправки revision payload `photo: null`, gallery содержит оба файла. База новой карточки ещё без live photo, поэтому сохранённый кандидат теряется.
- Доказательства: [photo-regression.json](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/photo-regression.json), [до отправки, PC](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/photo-draft-before-submit-1440.png), final-place-state.json → Place 9 → revision.payload.photo/gallery.
- Причина: `OwnerPlaceEditForm.__init__` подставляет фото редакции лишь в unbound GET; bound отправка без нового файла использует пустое live photo, которое save adapter снимает в новый payload.
- Область исправления: серверная проекция сохранённого candidate в bound form/photo-save adapter с regression test сохранения без нового upload. Validation/ACL не расширять. **В текущем плане validation/save исключены — не исправлено.**

### PP-02 — P1: legacy moderation неправильно проверяет цену группы/тип места

- Роль: модератор/волонтёр. URL: [legacy review №6](http://localhost:8784/admin/volunteer/review/6/).
- Шаги: owner заполняет центр с тарифами внутри Group → отправляет → открыть legacy review; сравнить с PlaceAdmin/owner 10/10 и центром модерации.
- Ожидание: все экраны читают одну и ту же публикационную редакцию и серверную готовность.
- Факт: legacy review требует переносить цену в тарифы, хотя обе группы уже имеют активные PricingPlan. При первом новом public-space парке также наблюдалось ложное требование контакта. Филиал/парк после approval имеют другое текущее состояние; прежнее наблюдение не выдаётся за повтор текущей pending-проверки.
- Доказательства: [legacy review, PC](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/legacy-moderation-groups-1440.png), admin-edit-en-1440.png (10/10), final-place-state.json. Соответствует прежней ACE-03, но групповая цена повторно проверена в этой работе.
- Причина/область: legacy review adapter не передаёт nature/nested_pricing редакции в тот же readiness-контракт. Отдельный серверный scope; действующий moderation hub не заменять и ACL не менять. **Не исправлено.**

### PP-03 — P2: после reload новые gallery-фото кандидата нельзя полноценно переставлять/удалять

- Роль: владелец. URL: photo-draft edit №9 до отправки, либо новый photo draft.
- Шаги: загрузить новые gallery-файлы → явно сохранить → reload → попробовать изменить их порядок/удалить до approval.
- Ожидание: редактор оперирует сохранёнными фото кандидата так же надёжно, как persisted photo IDs.
- Факт: файлы сохранены в revision с `id: null`, существующий редактор принимает реальные gallery IDs. Добавлен честный readonly preview таких файлов; он не обещает их редактирование. Для уже опубликованной галереи реальный порядок подхватывается.
- Доказательства: photo-regression.json, final-place-state.json → Place 9 gallery payload; фото до отправки.
- Область: стабильная идентичность candidate photos и штатный gallery update protocol. Не создавать вымышленные DB IDs и не пересоздавать Place. **Выходит за подключение существующего workflow; не исправлено.**

### PP-04 — P3: часть старых admin-подписей остаётся на русском в AZ/EN

- Роль: администратор. URL: [PlaceAdmin №6](http://localhost:8784/admin/catalog/place/6/change/) при EN/AZ.
- Шаги: переключить язык; проверить owner badge, «JSON с группами», сообщение о неактивной карте/геокодировании и существующие служебные подписи.
- Ожидание: понятный единый язык интерфейса; технические настройки не подменяют подсказку редактору.
- Факт: новые navigation/save/readiness/photo labels локализованы, конкретные испорченные переводы исправлены; указанные старые фрагменты остаются смешанными.
- Доказательство: admin-edit-en-1440.png.
- Область: отдельная точечная локализация существующей admin-copy и подсказок map config. **Не объявляется полной локализацией админки.**

## Скриншоты

Это реальные страницы локального приложения, не design-прототип. Сохранено 102 PNG, включая 48 базовых форм, 24 keyboard-состояния и 24 public-страницы.

| Экран | PC | Mobile |
| --- | --- | --- |
| Кабинет владельца, опубликованное место | [1440 RU](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/owner-edit-ru-1440.png) | [390 RU](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/owner-edit-ru-390.png) |
| Admin, создание | [1440 RU](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/admin-new-ru-1440.png) | [390 RU](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/admin-new-ru-390.png) |
| Admin, группы и корректная готовность | [1440 EN](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/admin-edit-en-1440.png) | [390 RU](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/admin-edit-ru-390.png) |
| Ошибка/фокус поля owner | [1440 RU](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/keyboard-owner-ru-1440.png) | [390 RU](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/keyboard-owner-ru-390.png) |
| Конфликт двух вкладок | [1440](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/conflict-1440.png) | [390](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/conflict-390.png) |
| Публичный центр | [1440 EN](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/public-6-en-1440.png) | [390 EN](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/public-6-en-390.png) |

[Свёрнутые группы, 390](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/owner-groups-ru-390.png) · [Общая программа филиала, 390](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07/screenshots/confirmed-branch-390.png).

## Что осталось непроверенным

- Успешный полный admin UI publish/edit цикл после дополнительной попытки с таймаутом; создание всех четырёх типов именно админкой. Owner → hub → public для четырёх типов выполнен отдельно.
- Реальная внешняя карта, геокодирование и разрешение браузерной геопозиции: внешние credentials намеренно отсутствуют. Ручной адрес и сообщение о недоступной карте проверены.
- Физические iOS/Android, Safari, экранный диктор, HEIC/HEIF с реального телефона, codec-различия; Chromium viewport и клавиатура не заменяют эти проверки.
- Keyboard Escape в каждом custom dropdown, полный проход всех дополнительных controls и переход к каждой возможной вложенной group/plan ошибке; подтверждённая matrix error focus использует возраст Place.
- Реальные rejected/needs_changes циклы, все admin/employee роли и приватные документы других сущностей, переключение публичных разделов, bulk organization links: за пределами этой реализации.
- Галерея provisional candidate полностью — PP-03; сохранение главного фото до публикации — PP-01. Остатки смешанной admin-copy — PP-04.
- Весь project test suite и PRODUCTION. Зелёными объявлены только 183 перечисленных targeted tests.

Для просмотра используйте QA-переключатель ролей на localhost:8784/qa/ и ссылки в отчёте. Локальный перезапуск с сохранением fixture volume: `.venv/bin/python .tmp/place-form-implementation-20261007/launch.py`; он проверяет frozen source и управляет только собственным PID. Полные manifests, исходные browser scripts и тестовый log лежат в папке evidence рядом с отчётом.
