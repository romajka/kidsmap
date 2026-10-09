# Профиль специалиста: текущая проверка и дизайн

Дата: 2026-10-06. Статус: **план и макеты готовы к согласованию; реализация приложения не начата**.

## 1. Состояние и границы

Прочитаны AGENTS.md, каноническая система .agents и исходный отчёт `docs/qa/content-entry-audit-2026-10-06.md`. Работа выполнена последовательно одним агентом. Использованы kidsmap-ui-design, frontend-design, writing-plans и verification-before-completion.

LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`; исследован dirty WORKTREE. Начальный манифест: 4457 существующих файлов. Чужие изменения, предыдущие макеты места/организации и исправления мероприятий сохраняются. Итоговая сверка — в `specialist-design-2026-10-06/preservation.json`.

Текущие формы: локальный стенд http://localhost:8781/qa/. Статический макет: http://localhost:8782/docs/qa/specialist-design-2026-10-06/prototype.html?view=admin&lang=ru. База тестов `test_qa_stage04`, отдельные cache/media/private-media, DJANGO_TESTING=1, сетевые и libpq guards, без production credentials. Запись анкет в браузере не выполнялась; тестовые POST и изменения выполнялись в тестовой базе. Browser logins и sessionStorage — только синтетические роли/маркеры.

Изменены только новые документы, макеты и локальные scratch-проверки. Без commit/push/deploy. PRODUCTION NOT RUN. Браузерные результаты относятся к запущенному локальному стенду; тесты импортировали текущий WORKTREE. Побайтовая сверка импортированных модулей процесса и всей конфигурации стенда не выполнялась.

## 2. Что уже работает

- В кабинете действительно **5 шагов**, в админке — **12 разделов**. Административная навигация уже существует; задача — улучшить её, а не создавать с нуля.
- На первом шаге новой анкеты есть видимая кнопка «Сохранить черновик» с formnovalidate.
- 29 checkbox направлений имеют 29 уникальных значений. Поиск, группировка и выбранные элементы в кабинете уже работают. На 390 px поиск «логопед» оставляет одно направление; Space переключает checkbox.
- Пустой стаж сохраняется как NULL, 0 как число 0. На публичной карточке 0 лет отображается, пустой стаж скрывается. Ошибки потери нулевого стажа здесь нет.
- Авторство, подтверждённая личность, сотрудничество и место приёма уже разделены сервером. Приглашение от организации не даёт личных прав. Документы имеют отдельные разрешения и согласия.
- В 48 текущих сочетаниях RU/AZ/EN ×360/390/768/1440 для предложения, собственного редактора и admin add/change: HTTP200, ширина документа не превышает viewport.

Эти исправления и правила сохраняются.

## 3. Подтверждённые проблемы и первопричины

| Приоритет | Наблюдение | Причина и доказательство | Предложенное исправление |
|---|---|---|---|
| P1 | В admin add/change на AZ/EN отсутствуют имя, стаж и направления, на всех четырёх ширинах | `src/catalog/templates/admin/catalog/specialist/change_form.html:109,175` ищет русские подстроки в переведённых `fieldset.name`; `SpecialistAdmin.fieldsets` использует gettext. DOM name/experience/directions=0 для AZ/EN, RU=1/1/1 | Идентификация разделов по стабильным ключам, независимым от языка. Проверять точный набор полей, а не только заголовки |
| P1 | Изменение общей анкеты заменяет отдельные цену/телефон основного приёма | `_sync_primary_location`, `src/catalog/services/owner_specialist_use_cases.py:21`: строит location из profile.price_from и общего phone/WhatsApp. Проверка: 35 →20 AZN, номер филиала → общий; прежняя строка уходит в историю, второй адрес сохраняется | Явный набор мест с собственными полями. Сохранение общей анкеты не должно синхронизировать эти значения обратно |
| P1 | Несохранённые изменения существующей анкеты не восстанавливаются после refresh | `static/js/specialists.js:507`: восстановление разрешено только при пустом name; в существующем профиле имя заполнено | Account/profile/schema/base-version scoped рабочая копия с предложением сравнить и восстановить |
| P1 | Текст новой анкеты одного аккаунта восстанавливается в другом аккаунте того же браузера | Общий ключ `kidsmap_spec_draft_new`; browser-проверка demo_person → demo_owner подтвердила перенос маркера | Ключ с actor и draft/profile ID; не переносить legacy-копию между аккаунтами; не хранить документы/файлы/секреты |
| P1 | Admin проверка очного формата принимает единственный выключенный адрес как активный | `src/catalog/domain_admin/specialist.py:51`: отсутствующий checkbox value не входит в off/false/0 и трактуется как True. Parent form valid, inline cleaned is_active=False | Проверять активность по валидированным inline данным. Сохранить действующее требование хотя бы одного активного очного адреса |
| P2 | Сохранённый черновик предложения нельзя продолжить автору без claim | POST сохраняет Specialist.created_by, не verified_person_user; GET собственного редактора возвращает404, claims200 | Отдельная приватная рабочая копия предложения до отправки. Не разрешать автору редактировать Specialist |
| P2 | Места в mobile admin требуют широкого внутреннего скролла | 390px: practice_locations group client284, scroll2021 RU /1861 AZ /1920 EN. Это внутренний overflow, не выход страницы за экран | Карточки строк formset на телефоне; сохранить IDs, DELETE/active/primary и серверную обработку |
| P2 | Клавиатурная ссылка на раздел не переводит фокус в него | Enter на admin «Места…» оставляет activeElement на навигационном A | Фокус на заголовок или конкретное поле ошибки, отступ от закреплённых панелей |
| P2 | Нулевая цена скрывается на публичной карточке | `src/catalog/templates/catalog/specialist_detail.html:349,424` проверяет truthiness. Изолированный HTTP200: 0 лет есть, 0 AZN отсутствует при явно заданных нулевых общей и локальной ценах | Различать NULL и 0. Не подставлять «бесплатно» для пустой цены |
| P2 | Образование/опыт доступны в модели и админке, но отсутствуют в OwnerSpecialistForm | `src/catalog/forms.py:2255`; education_* / experience_info_* / name_alt не входят в fields | Добавить необязательные публичные тексты; документы и подтверждение личности оставить отдельными |

Не подтверждено общее горизонтальное переполнение страницы. Не подтверждена потеря нулевого стажа. В кабинете уже есть поиск направлений и первый черновик — их повторно «исправлять» не нужно.

## 4. Контракт полей и технический долг

| Блок | Текущее правило | Дизайн |
|---|---|---|
| Имя / фото | Для отправки из кабинета имя обязательно; фото необязательно, до2МБ, текущий валидатор изображения | «Имя и фамилия», альтернативное написание отдельно; фотография с явным лимитом |
| Стаж | Nullable PositiveSmallInteger; 0 допустим | «Полных лет». Пусто — не указан; 0 — нет полных лет. Не вычислять стаж по образованию |
| Направления | ≥1 для отправки; активный справочник, существующая группировка без дублей | Сохранить поиск кабинета. Admin mobile: одна колонка checkbox, поиск, выбранные элементы; название удаляемого элемента в aria-label |
| Возраст детей | Обе границы необязательны; submit проверяет from≤to | От/до с единицей «лет», пустые границы допустимы. Не делать возраст обязательным |
| Языки | ≥1 рабочий язык при submit из кабинета | Отдельно от языков текстов анкеты |
| Формат | online / offline / both; очный требует активное место или собственный адрес и регион | Формат специалиста, а не трудоустройство. Онлайн не требует места или координат |
| Места приёма | Model поддерживает несколько, кабинет редактирует только primary | Повторяемые карточки. Place либо собственный адрес, регион; район/метро/координаты необязательны; свои price/phone/schedule; primary и active отдельно |
| Цена | Общие price_from/price_to + локальная price_per_session; nullable, 0 допустим | Общая стоимость — ориентир профиля; цена здесь — конкретный приём. Не копировать при обычном сохранении |
| Контакты | Телефон или WhatsApp для submit из кабинета; ссылки необязательны | Общий контакт специалиста отдельно от записи в конкретное место |
| Описание | Хотя бы один bio AZ/RU/EN для submit | Языковые вкладки с индикатором заполнения. Fallback отображения не создаёт переводы |
| Образование / опыт | Публичные тексты education_*/experience_info_* отдельны от лет стажа и файлов | Необязательные публичные поля; переводы вводятся вручную |
| Документы | Личные файлы в private storage; identity всегда private; certificate/diploma через проверку и consent | Автор предложения не видит загрузку личных документов. Личность, статус файла и разрешение публичного показа — три разные состояния |

Долг: правила отправки OwnerSpecialistForm и административной публикации различаются. В admin обязательны модельные поля name/specializations/consultation_format и очное место по форме; owner-проверки bio/контактов/языков не являются общим publish guard. Admin action mark_published также не вызывает owner-readiness. В этом scope **не унифицировать серверную политику**. Индикация должна честно различать обязательные правила конкретного действия и рекомендации.

Долг: старые owner_specialist_create/edit определения в views.py существуют, но актуальные URL направлены в controllers/specialist_workspace.py. Их не удалять и не расширять охват рефакторинга.

## 5. Правила, которые сохраняются, и риски

| Сущность / действие | Граница |
|---|---|
| Автор предложения | created_by — происхождение анкеты. Не даёт редактирования человека, claim approval или документов |
| Сам специалист | verified_person_user + person_verified_at. Только текущий подтверждённый человек управляет кабинетом и своим согласием |
| Legacy owner | Не является подтверждением личности. В admin — отдельная readonly подпись и объяснение |
| Подтверждение личности | Отдельная заявка/решение reviewer с review_specialist_claim. Проверка файла сама по себе claim не подтверждает |
| Сотрудничество | Organization employment: две явные стороны, даты, статусы, версии и актуальность ownership. Даже один аккаунт для обеих сторон подтверждает их отдельно |
| Место приёма | Адрес/карточка визита. Не подтверждает employment и не даёт права редактирования Place/Organization |
| Личные документы | Person или active reviewer с review_specialist_documents; обычный staff/change_specialist, автор, Place/Organization owner/grantee не получают доступ |
| Публикация сертификата | Approved + explicit consent текущего verified person + опубликованный активный профиль + активный person account. Проверяющий не выбирает публичность за человека |
| Identity документ | Всегда private; не появляется в предпросмотре, восстановлении или публичной карточке |
| Отмена/история | Не удалять историю приёма или employment. Текущий переход в online выключает активные места; не обещать автоматическое включение всех при возвращении |
| Опубликованная анкета | Существующий owner-save прямо меняет status на draft/pending. Карточка исчезает из каталога до проверки. В этом scope не вводить candidate/live механизм и не обещать сохранение публичной прежней версии |
| Конфликт | Existing expected_updated_at, claim/employment versions, document token/epoch сохраняются. Не заменять stale conflict повторной записью |

Документы выдаются через guarded download, с attachment, private/no-store и защитными заголовками; не использовать file.url. Новая форма не должна обходить specialist_domain/specialist_documents.

Риск отдельного черновика предложения: потребуется новый узкий механизм рабочей копии. Это **отдельный явно предложенный пункт согласования**, а не разрешение автору редактировать сохранённый Specialist. Нельзя мигрировать старые proposal-профили в собственность автора или использовать общий server_drafts, который не содержит Specialist в текущем target contract.

Риск поиска мест: текущий ModelChoice queryset перечисляет все non-deleted Place. Полный аудит видимости этого справочника не выполнен. Новый поиск не должен расширять доступ; проверка публичных/доступных приватных карточек входит в предреализационную проверку scope.

## 6. Legacy и совместимость

Сохранять модельные IDs, specialization codes, пять шагов кабинета, 12 admin-групп, multilingual данные, slugs/URL, authority/version anchors и историю. Не переносить текст без согласия между языками. Не объединять organization employment и practice_locations.

Новые стабильные ключи admin fieldsets должны отображать **все существующие поля**, включая status, is_active, rejection_reason и служебные readonly сведения; локализованные заголовки — только отображение. Новый responsive formset не меняет значения management form, границы прав и модельные связи.

## 7. Выполненные проверки и ограничения

### Сервер

Первый запуск stock suites: **92 tests, 33.304s, exit1**. Один ERROR при проверке FK: Category EDU отсутствует в existing test IndependentSpecialistSecurityTests.test_live_place_owner_and_organization_grantee_cannot_read_person_documents. Это ошибка тестового setup, не подтверждение нарушения ACL.

Повтор: **98 tests, 41.894s, exit0**. 92 существующих теста +6 scratch-probes. Runner добавляет только синтетическую Category EDU в isolated setUp; исходники и assertions штатных тестов не изменены.

Дополнительный запуск: **8 probes, 0.401s, exit0**. Это6 повторов и2 новых проверки: снятый is_active в admin и нулевая публичная цена. Всего **100 различных прошедших проверок**, не один запуск на100 и не full-suite.

Проверялись claims, две стороны employment, stale версии и ownership, отозванные permissions, inactive accounts, file privacy, consent/withdrawal, purpose immutable, identity tamper, nested IDs, CSRF, account deletion, transfer/retention и concurrency. Scratch-probes воспроизводят текущие дефекты; их зелёный результат **не означает, что дефекты исправлены**.

Точные команды:

```bash
cd /home/ramin/kidsmap
.venv/bin/python .tmp/event-admin-fix-20261006/run.py \
  catalog.testcases.test_task33_specialist_domain \
  catalog.testcases.test_task33_specialist_privacy \
  catalog.testcases.test_task33_specialist_workspace \
  catalog.testcases.test_task33_specialist_screens \
  catalog.testcases.test_task33_specialist_screens_security \
  catalog.testcases.test_task33_specialist_security_review \
  catalog.testcases.test_task33_specialist_transfer \
  catalog.testcases.test_task33_specialist_retention \
  > .tmp/specialist-design-20261006/domain-tests.log 2>&1
# Первый запуск: exit1, отсутствует синтетическая Category EDU.
.venv/bin/python .tmp/specialist-design-20261006/run.py \
  catalog.testcases.test_task33_specialist_domain \
  catalog.testcases.test_task33_specialist_privacy \
  catalog.testcases.test_task33_specialist_workspace \
  catalog.testcases.test_task33_specialist_screens \
  catalog.testcases.test_task33_specialist_screens_security \
  catalog.testcases.test_task33_specialist_security_review \
  catalog.testcases.test_task33_specialist_transfer \
  catalog.testcases.test_task33_specialist_retention probes \
  > .tmp/specialist-design-20261006/verified-tests.log 2>&1
.venv/bin/python .tmp/specialist-design-20261006/run.py probes \
  > .tmp/specialist-design-20261006/additional-probes.log 2>&1
```

После первого повторного запуска probes содержал6 тестов; после добавления двух проверок их8. Текущий повтор полной команды найдёт100 тестов. Логи сохранены локально; production logs/dumps в документацию не копировались. Runner предупреждает о существующих WORKTREE model/migration отличиях; миграции приложения не создавались и не исправлялись.

### Браузер

- Current: **48 сочетаний** =4 формы ×3 языка ×4 ширины. Proposal/person/admin add/admin change. Все HTTP200, без overflow страницы. Admin AZ/EN — missing fields, на16 сочетаниях.
- Current admin navigation:12 ссылок во всех языках. Enter прокручивает, но фокус остаётся на ссылке. Внутренняя таблица мест шире мобильного контейнера.
- Current mobile directions: поиск/выбор и Space работают,29/29 без дублей. Первая draft-кнопка видима.
- Current restoration: новая анкета восстанавливается; существующий профиль не восстанавливает unsaved name; новый автор в другом аккаунте получает предыдущий локальный текст. После теста удалены только два probe-key.
- Current public RU: пустой стаж скрыт;0 лет показаны. Приватные страницы документов читались только своим синтетическим аккаунтом; список файлов пуст, download ACL по браузерным ролям не проверен.
- Prototype: **96 сочетаний** =8 состояний ×3 языка ×4 ширины. Без horizontal overflow, duplicate IDs или pageerror. Проверены keyboard checkbox/Enter, поиск с сохранением выбора, переход к полю ошибки с aria-describedby, фокус нового места, сохранение введённой цены и нового места при навигации. В proposal нет document-nav; admin не получает checkbox согласия за специалиста.

Артефакты: `specialist-design-2026-10-06/verification.json`, `current-browser-matrix.json`, `source-coverage.json`. Graph coverage best effort; отмеченные template parse ranges проверены напрямую в исходниках. Неиндексированный или отсутствующий путь не трактовался как отсутствие бизнес-правила.

### Не проверено

Реализованного нового UI/черновика ещё нет. Не выполнена сквозная browser-приёмка Save→refresh→claim→moderation→public, одобрение/отказ приглашения через браузер и браузерная загрузка/скачивание файлов всеми ролями. Эти границы покрыты частично серверными HTTP/domain тестами, что не заменяет browser E2E. Не выполнены full-suite, production, реальный мобильный аппарат, screen reader, HEIC/real-file processing, file-signature аудит, внешние хранилища/почта и полная проверка видимости Place selector.

## 8. Предлагаемый интерфейс и scope

**Admin:** сохранить12 групп, использовать стабильные идентификаторы. PC — боковое содержание; mobile — select «Раздел формы» вместо необходимости прокручивать длинный nav-strip. В рабочей реализации все группы остаются в одном form; навигация прокручивает и переносит фокус. Макет показывает разделы по одному для компактного просмотра. Сводка ошибок содержит ссылку на конкретный control/inline row; сохранение и статус видимы снизу, поля не перекрываются.

**Кабинет:** сохранить5 этапов заполнения. Дополнительные разделы «Документы», «Сотрудничество», «Проверка» — отдельные задачи кабинета, не новые этапы и не прогресс «9 шагов». Сохранение на первом шаге остаётся. Состояния: новая анкета, серверный черновик, unsaved changes, сохранение, сохранено, ошибка сохранения, конфликт версии; «на проверке», «опубликовано», «отказ» берутся с сервера.

**Места приёма:** строки с независимыми ценой и телефоном. Добавление нескольких без пересоздания старых; primary, active и история видимы. Общие price/phone не заменяют локальные. Сотрудничество с сетью оформляется на отдельной странице с явными согласиями.

**Черновик предложения:** рекомендуемый новый механизм — приватная working copy автора до отправки. Кнопка на первом шаге сохраняет её на сервере. Сохранение и продолжение доступно только этому автору; отправка материализует канонический Specialist один раз и делает рабочую копию readonly. Автор не получает прав на Specialist или private документы. Старые сохранённые proposal-профили не перераспределяются. Новый механизм требует отдельной модели/сервиса/version/idempotency и локальной миграции после согласования.

**Восстановление:** честная локальная копия текста, привязанная к аккаунту и анкете, с base version; явный выбор восстановления вместо тихой перезаписи новой серверной версии. Нет фонового сохранения на сервере. Не сохранять input file, document data, CSRF/version tokens или private documents в browser storage. Для фото — повторный выбор до успешного серверного сохранения; сохранённое фото должно отображаться при продолжении server draft.

**Подписи:** «Автор предложения», «Подтверждённый специалист», «Место приёма», «Телефон записи в это место», «Цена приёма здесь», «Общие контакты». В employment поле «Роль» заменить локально на «Должность / вид сотрудничества», не менять коды access roles и общие переводы других сущностей. Админское legacy owner поле readonly и с объяснением, что оно не подтверждает личность.

Макеты:

- [Интерактивный PC/mobile](http://localhost:8782/docs/qa/specialist-design-2026-10-06/prototype.html?view=admin&lang=ru) — переключатели8 сценариев и RU/AZ/EN, без server writes.
- [PC admin](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/mock-admin-pc.png), [mobile admin](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/mock-admin-mobile-viewport.png).
- [PC места приёма](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/mock-locations-pc.png), [mobile места приёма](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/mock-locations-mobile-viewport.png).
- [Направления mobile](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/mock-directions-mobile-viewport.png), [ошибки](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/mock-review-pc.png), [документы](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/mock-documents-pc.png), [предложение](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/mock-proposal-pc.png).
- До изменений: [PC admin](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/current-admin-pc.png), [EN mobile admin](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/current-admin-en-mobile.png), [mobile кабинет](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/current-person-mobile.png).

Все изображения — скриншоты localhost с синтетическими данными. Макет не подтверждает работу будущих backend действий. Примеры saved/status/privacy в макете — состояния для согласования, не реальные серверные ответы.

## 9. Приоритеты и следующий шаг

1. Стабильные admin-разделы AZ/EN, корректное active правило и безопасное восстановление по аккаунтам.
2. Несколько мест приёма без перезаписи локальных данных; понятные навигация/фокус/ошибки.
3. Возобновляемая приватная working copy предложения, optional публичные сведения об образовании и честная индикация сохранения/публикации.
4. RU/AZ/EN ×360/390/768/1440, клавиатура, свежая server/browser приёмка всех согласованных изменений.

Конкретные файлы, этапы и приёмка: [план реализации](/home/ramin/kidsmap/docs/superpowers/plans/2026-10-06-specialist-profile-entry.md). Остановиться здесь до согласования пользователем выбранного scope. Правила идентичности, employment, документов, публикации и доступа не менять ради UI.
