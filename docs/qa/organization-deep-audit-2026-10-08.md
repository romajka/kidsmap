# Организации KidsMap — функциональная, визуальная и негативная приёмка 2026-10-08

Роль: kidsmap-orchestrator. Execution identity: Codex /root, один исполнитель; Django, security, database, frontend и browser-QA рассмотрены последовательно, независимый аудит других агентов не заявляется. Канонические определения: .agents/registry.json и .agents/agents/kidsmap-orchestrator/agent.md. Scope: локальные текущие организация/место/запрос/связь/программа/сотрудник, кабинет и админка; аудит и отчёт, **без исправлений приложения**.

**Вердикт: основа связей и прав сделана правильно, завершённой приёмку считать нельзя. Подтверждены 13 отдельных проблем: 3 P1, 9 P2, 1 P3.** Два бага теряют ещё не отправленный ввод; один P1 раскрывает название чужой приватной карточки через старый транспорт. Захват владения и скрытый перенос в проверенных сценариях не получились. Это граница доказательства, а не гарантия отсутствия других уязвимостей.

Общая оценка по этому прогону: функциональность **6/10** (основные happy paths есть, восстановление ненадёжно), границы доступа **6/10** (канонические согласия/версии сильные, legacy metadata gate неполный), визуал **6/10** (новые create/connect страницы аккуратные; старые вторичные формы остаются сырыми). Оценки экспертные, не формальная security/WCAG сертификация.

## Snapshot и среда

- LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`.
- Dirty WORKTREE: исходно180 записей porcelain. Зафиксированы5239 SHA файлов до работы; application source/static/locale/config2756 файлов, итоговый digest `c0acc75bdb30a2fd13d87d41f6038e877f6b299d1c3e23b94bf6380b78b10c9c`.
- Стенд: http://localhost:8788/qa/; `/qa/acceptance-version/` подтверждает тот же HEAD/source digest; запуск `2026-10-08T05:58:59.031300+00:00`, начало этого аудита `2026-10-08T06:08:39.936364+00:00`.
- DJANGO_TESTING=true, изолированная синтетическая PostgreSQL, socket без DB ports, network-none DB; отдельная test DB для suites. Раздельные cache/media/private-media, LocMem email/cache, внешние credentials отсутствуют, browser блокирует другие origins. Роли demo_owner/outsider/manager/person/parent/moderator/volunteer исключительно вымышленные.
- Тестовые действия владельца/администратора меняли только собственные ORGQA fixtures. Исходные чужие файлы не переписывались; единственная запись из baseline — журнал implementation-status.md (собственный active_run и запись о приёмке). Новые отчёт/доказательства отдельные.
- PRODUCTION: NOT RUN. Не подключался, не определял production SHA и не переносил локальные результаты на production. Commit/push/deploy не выполнялись.
- Исторические1819 тестов и прежние скриншоты не использованы как свежая приёмка. Новые результаты ниже воспроизведены08Oct на замороженном source.

## 1. Состояние области и карта реализации

```text
Кабинет/create → create_organization → draft Organization (без филиалов)
Редактор → ServerDraft (рабочая копия) / publication.propose (candidate)
Модерация → publication.review → approved/live → public organization
Найти/выбрать места → preview_connections → operation snapshot10min
confirm → actor/key/action/version recheck → per-row canonical request_join/confirm_join
Админ: signed selection → тот же preview/execute; informational требует reviewer
detach-preview → impacts + consent → canonical detach → local program snapshots
Перенос → отдельная отвязка → новый выбор организации → новые согласия
```

Организация — бренд/общие программы/команда, филиал — существующая карточка Place с собственным адресом и контентом. Подключение сохраняет тот же Place ID и владельца. Филиал может быть создан отдельно после сети. Business и informational различаются: вторая не даёт сотрудникам сети бизнес-доступ. Актуальность связи зависит от ownership versions обеих сторон и архива; значение FK само по себе права не даёт.

Source подтверждён прямыми чтениями. Graph `home-ramin-kidsmap` generation2026-10-08T06:05:21Z использован для поиска, затем сверены свежие файлы; truncated graph search не считается исчерпывающим. Проверены organization_connections, organization_ownership, organization_workspace/API, admin transport/business editor, business_team, drafts/publication, directory/public presentation, JS/CSS/templates и целевые tests. Прямое присваивание FK вместо canonical операции не внедрялось.

## 2. Сильные стороны: что реально получилось

Создана новая сеть11 без филиалов, частичный ввод восстановился в той же вкладке, обычный ServerDraft пережил reload, отправка прошла review и публичная карточка200. Изменения опубликованной сети остались candidate; live EN остался `ORGQA Browser network`, candidate `ORGQA Tab A submitted`, published status сохранился. Отдельно администратор создал сеть12, сохранил draft, открыл повторно, отправил, одобрил и сохранил изменение опубликованной сети как draft.

Владелец подключил **10 готовых карточек32–41**, не пересоздавая их: completed receipt `3393a59d-5217-448e-8791-1e84fb0c56ad`, все10 DB business links. Проверены прежние IDs/slug/owner/status,30 реальных image SHA, порядок gallery,10 занятий/групп/тарифов и поля расписания: сравнение до/после равно. Проверка относится к этим10 карточкам, не к произвольным медиа всей базы.

Partial batch корректно различил уже подключённую карточку, другую сеть и запрос другому владельцу. Второй владелец подтвердил место64; owner остался прежним. Администратор получил10 `no_rights` для business без side ownership, а10 informational мест42–51 подключил только после явного review/consent. Сотрудник сети мог смотреть business32, не мог informational42; прямой владелец42 сохранил свои права независимо от информационной связи.

Новая отвязка показала1 общую программу,2 активных сетевых grant и1 прямое разрешение; без consent409. После неё Activity26 стал локальным утверждённым снимком, Group27/Price32/расписание сохранились; manager лишился place.edit, direct parent сохранил. Сетевые контакты перестали наследоваться без копирования. Место66 затем подключил к сети6 только фактический владелец места и этой сети; старый владелец сети5 получил PermissionDenied. Public-detail после отвязки был200: исчезновение страницы не заявляется. До-state отдельного runtime JSON не записался из-за ошибки harness, поэтому непрерывность этого public URL подтверждается лишь текущим GET и целевыми server tests, не выдуманной парой before/after скриншотов.

Срок preview, изменившаяся карточка (`changed`), CSRF, чужая receipt, stale ownership, информационный доступ, повтор/конкурирующие сети/возобновление после прерывания отработали в указанном уровне теста. Две реальные вкладки дали409 и сохранили текстB; сообщение конфликта не локализовано — это отдельный FAIL, а не отказ защиты версий.

## 3. Подтверждённые проблемы

Каждая ниже имеет отдельный scope и готовый промпт. Environment у всех LOCAL synthetic/current WORKTREE, confidence высокая для описанного воспроизведения; production exploit не заявляется.

### ORG-01 · P1 · Запрос по ID чужого приватного места раскрывает его название

**Роль:** Владелец организации demo_owner. **URL:** `/ru/account/organizations/5/join/; /api/ownership/join/place/65/`.

**Шаги:** Взять ID65 вымышленного чужого draft/is_active=False. С действительным CSRF отправить place_id65 в старый join своей организации5, затем открыть её кабинет. Отдельно отправить JSON organization_id5 в ownership API.

**Ожидание:** Недоступная карточка не принимает запрос по угаданному ID и не раскрывает метаданные.

**Факт:** Legacy POST302 создаёт pending; API200 возвращает request_id29. Кабинет показывает название чужого черновика. Новый массовый preview запрещает тот же ID. Владелец и organization_id места не изменились.

**Первопричина:** Проверка участия одной стороны заменяет проверку видимости чужой карточки; список pending не применяет ACL карточки. Source: `src/catalog/services/organization_ownership.py:235; src/catalog/controllers/organization_workspace.py:256; src/catalog/controllers/organization_workspace.py:335`.

**Доказательство:** server-probes.json; api-probes.json. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Security + Django: единый visibility gate для всех транспорта/канонического запроса и безопасное чтение pending. Сохранять исключения для законного прямого владельца и актуальные согласия; не выдавать права по запросу. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-01.md).

### ORG-02 · P1 · Запоздалое автосохранение уничтожает более свежий ввод

**Роль:** Владелец организации. **URL:** `/ru/account/organizations/8/`.

**Шаги:** Сохранить исходный ServerDraft. Начать вводA; задержать доставку его настоящего успешного HTTP-ответа на1800ms. После записиA в сервер ввестиB. Дождаться второго debounce и ответаA; обновить страницу.

**Ожидание:** Состояние «Сохранено» относится к текущему текстуB; локальная копияB сохраняется до его подтверждённой записи.

**Факт:** До обновления полеB, надпись «Сохранено на сервере», local=null, два POST. После обновления восстановлен A=ORGQA First in flight вместо B=ORGQA Latest typed value.

**Первопричина:** Нет очереди запросов/проверки свежести ответа. Успешный старый ответ безусловно очищает sessionStorage и переопределяет состояние после409 нового запроса. Source: `static/js/organization_workspace.js:129`.

**Доказательство:** browser-recovery.json; screenshots/draft-race-390.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Frontend + Django drafts: сохранить version/CAS, сериализовать или объединять очередь, учитывать текущую редакцию текста, не очищать новую локальную копию старым ответом. Отдельно покрыть межвкладочный409. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-02.md).

### ORG-03 · P1 · Неудачное создание стирает локальный черновик

**Роль:** Владелец. **URL:** `/ru/account/organizations/create/`.

**Шаги:** Ввести ORGQA Network loss latest. Убедиться, что sessionStorage содержит данные. Прервать только настоящий POST создания. После завершения страницы сетевой ошибки снова открыть создание в той же вкладке.

**Ожидание:** До подтверждения создания сервером локальная копия сохраняется и восстановится.

**Факт:** Локальная копия была. После проваленного POST и повторного открытия поле пустое. Новая организация не создана.

**Первопричина:** Ключ локального восстановления удаляется в событии submit до ответа сервера. Source: `static/js/organization_workspace.js:100`.

**Доказательство:** browser-edge.json; screenshots/create-network-loss-390.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Frontend: очищать копию только после подтверждённого успешного создания; сохранить данные при network/400/409. Не расширять обещание восстановления за пределы реально используемого sessionStorage. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-03.md).

### ORG-04 · P2 · Старый detach обходит обзор последствий

**Роль:** Владелец организации. **URL:** `/ru/account/organizations/9/branches/52/detach/`.

**Шаги:** Связать собственное вымышленное место52 с организацией9. POST старого маршрута с действительным CSRF и актуальным expected_ownership_version, без preview_id/consent.

**Ожидание:** В веб-сценарии необратимые последствия для сетевого доступа и программ показаны до подтверждения.

**Факт:** POST302 отвязывает место без нового обзора. Новый detach-preview требует consent и возвращает409 без него. Право владельца не обойдено.

**Первопричина:** Старый транспорт всё ещё напрямую вызывает canonical detach, его контракт не содержит snapshot последствий и явного подтверждения UI. Source: `src/catalog/controllers/organization_workspace.py:368; src/catalog/controllers/organization_ownership_api.py:35`.

**Доказательство:** server-probes.json; browser-detach.json. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Django/UX: согласовать совместимость старого HTTP/API-контракта, провести веб-вызов через обзор/receipt либо явно закрыть устаревший путь. Не менять права и canonical detach; перед изменением API представить план совместимости. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-04.md).

### ORG-05 · P2 · Часть ошибок редактора возвращается без объяснения

**Роль:** Владелец. **URL:** `/ru/account/organizations/10/save/`.

**Шаги:** Отправить name_ru длиной256, phone/whatsapp длиной51 с текущими версиями. Это негативный серверный POST, native maxlength намеренно обойдён в тесте.

**Ожидание:** 400 показывает каждую ошибку, сохраняет ввод и даёт понятный переход к полю.

**Факт:** Сервер правильно отклоняет данные; name_ru/phone/whatsapp ошибок в HTML нет, errorlist0. Поля могут иметь aria-invalid без связанного текста.

**Первопричина:** Для перечисленных полей шаблон выводит только widget, errors пропущены; общей сводки в edit нет. Source: `src/catalog/templates/pages/organization_workspace.html:553; src/catalog/controllers/organization_workspace.py:327`.

**Доказательство:** extra-probes.json; browser-errors.json; screenshots/edit-400-no-error-390.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Frontend/accessibility: вывести все серверные field/nonfield errors, привязать aria-describedby, добавить сводку с фокусом/переходом. Серверные ограничения сохранить. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-05.md).

### ORG-06 · P2 · Ошибки показывают технические английские подписи

**Роль:** Владелец. **URL:** `/ru/account/organizations/create/; /ru/account/organizations/11/save/`.

**Шаги:** Отправить создание без названия в RU/AZ/EN. В двух вкладках открыть организацию11 и последовательно отправить разные изменения с одинаковой исходной candidate-version.

**Ожидание:** Локализованные подписи «Название организации (AZ)» и понятное объяснение конфликта с безопасным восстановлением ввода.

**Факт:** Сводка создания показывает Name az во всех трёх языках. Конфликт двух вкладок409 сохраняет B, но показывает Candidate version conflict.

**Первопричина:** У Form нет локализованных labels; ValidationError сервиса выводится пользователю напрямую. Source: `src/catalog/controllers/organization_workspace.py:153; src/catalog/templates/includes/form_error_summary.html:52; src/catalog/controllers/organization_workspace.py:326`.

**Доказательство:** locale-observe.json; extra-probes.json; browser-tabs.json; screenshots/create-error-390.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Django + frontend: локализовать labels и отображение кодов конфликтов RU/AZ/EN; не ослаблять version conflict и не менять утверждения тестов ради зелёного результата. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-06.md).

### ORG-07 · P2 · Без JavaScript приглашение передаёт email и CSRF в URL

**Роль:** Владелец. **URL:** `/ru/account/organizations/5/#org-team`.

**Шаги:** Отключить JS в изолированном Chromium, авторизоваться через локальный QA POST, ввести вымышленный email и нажать «Пригласить».

**Ожидание:** POST на сервер приглашений либо явно недоступная функция с объяснением. Данные и CSRF не попадают в GET.

**Факт:** Форма отправляет GET текущего кабинета с email, role, scope и csrfmiddlewaretoken в query. Приглашений0. Токен в доказательствах заменён REDACTED.

**Первопричина:** У form нет method/action; правильный POST существует только в обработчике JS. Source: `src/catalog/templates/pages/organization_workspace.html:448`.

**Доказательство:** browser-nojs-confirmed.json; team-observe.json; screenshots/team-nojs-390.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Security/frontend/backend: безопасный POST fallback с той же авторизацией/CSRF либо явное отключение отправки без JS. Исключить секреты/query email из URL и отчётов. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-07.md).

### ORG-08 · P2 · После приглашения роль и список не соответствуют результату

**Роль:** Владелец. **URL:** `/ru/account/organizations/5/#org-team`.

**Шаги:** Выбрать MANAGER и пригласить orgqa-new-employee@example.invalid. Дождаться настоящего POST200.

**Ожидание:** Выбранная роль, её пояснение и список ожидающих приглашений согласованы; можно проверить результат без догадки и повторного нажатия.

**Факт:** Сервер создал ровно одно MANAGER/PENDING приглашение. После reset селект EDITOR, пояснение всё ещё «Просмотр, редактирование и статистика»; нового приглашения в списке нет до обновления.

**Первопричина:** После team.reset не вызывается updateRole и не обновляется список. Source: `static/js/organization_workspace.js:194`.

**Доказательство:** browser-team.json; team-observe.json; screenshots/team-reset-390.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Frontend: согласовать состояние после reset, показать созданное приглашение/обновить список, loading и защиту повторной отправки; серверную защиту duplicate pending сохранить. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-08.md).

### ORG-09 · P2 · Старые маленькие поля портят новые формы управления

**Роль:** Владелец/сотрудник. **URL:** `/ru/account/organizations/5/; /ru/account/organizations/10/`.

**Шаги:** Открыть кабинет и пустую сеть на PC/mobile; проверить новый филиал, новую программу и приглашение.

**Ожидание:** Единые читабельные поля с нормальной зоной нажатия, явной структурой и понятными обязательными значениями.

**Факт:** Категория/роль/область20px, email и название программы22px; часть полей нативные, часть оформленные. На мобильном подпись роли переносится отдельно от Email. Кабинет — длинная лента около4500px на PC, вкладки служат якорями, а не скрывают разделы.

**Первопричина:** CSS покрывает .org-fields input/textarea, но не select; программа и team используют другую разметку без общих классов. Source: `static/css/pages/organization_workspace.css:303; src/catalog/templates/pages/organization_workspace.html:327; src/catalog/templates/pages/organization_workspace.html:432`.

**Доказательство:** browser-matrix.json; screenshots/clipped-team-390.png; screenshots/matrix-workspace-1440.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Frontend/design: ограниченная унификация этих трёх форм, минимум44px по правилам проекта, responsive/layout/focus. Улучшение длинной навигации сначала показать макетом; не переделывать доменную модель. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-09.md).

### ORG-10 · P2 · Подписи админки зафиксированы на AZ даже в RU/EN

**Роль:** Администратор. **URL:** `/admin/catalog/organization/add/; /admin/catalog/organization/12/change/`.

**Шаги:** В одном серверном процессе переключить RU/AZ/EN и открыть редактор. Дополнительно сравнить OrganizationForm.base_fields[name_az].label с gettext под каждым override.

**Ожидание:** Язык названий и описаний совпадает с текущим интерфейсом; маркеры AZ/RU/EN обозначают язык данных.

**Факт:** Поле всегда Təşkilatın adı (AZ), type=str. Под RU ожидается «Название организации (AZ)», под EN Organization name (AZ). Азербайджанский вариант корректен только для AZ.

**Первопричина:** Форматирование lazy-перевода через % в Meta выполняется при импорте и превращает label в обычную строку. Source: `src/catalog/domain_admin/business.py:51`.

**Доказательство:** locale-observe.json; browser-extra-matrix-confirmed.json; screenshots/admin-editor-1440.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Django/i18n: сохранить ленивое форматирование либо вычислять label в __init__ в активном языке. Проверить в одном процессе последовательные запросы всех языков и другие страницы с такими же строками. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-10.md).

### ORG-11 · P3 · Пагинация кабинета говорит с диктором по-русски в AZ/EN

**Роль:** Владелец/сотрудник. **URL:** `/en/account/organizations/5/; /account/organizations/5/`.

**Шаги:** Открыть сеть с более6 филиалами в EN/AZ и проверить aria-label блока пагинации.

**Ожидание:** Доступное имя навигации соответствует языку интерфейса.

**Факт:** aria-label всегда «Пагинация филиалов»; визуальные кнопки могут быть переведены. Имя пользователя на русском не считается ошибкой перевода.

**Первопричина:** Доступное имя задано literal RU. Source: `src/catalog/templates/pages/organization_workspace.html:321`.

**Доказательство:** browser-matrix.json. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Frontend/accessibility: локализовать доступное имя и проверить аналогичные общие aria-строки на других organization страницах. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-11.md).

### ORG-12 · P2 · Устаревший pending запрос не имеет безопасного пути продолжения

**Роль:** Оба владельца. **URL:** `/ru/account/organizations/5/connections/?place_ids=68`.

**Шаги:** Создать запрос сети5 к вымышленному месту68 другого владельца. Увеличить content_version места, имитируя сохранение редактором. Проверить confirm обеих сторон и повторный request_join инициатора; открыть новый preview.

**Ожидание:** Старое согласие блокируется, но пользователю доступна явная отмена/новый запрос с новой версией и повторным согласием обеих сторон.

**Факт:** Три действия ValidationError Request is stale; запрос52 остаётся pending, место не связано, новый preview manual_review и0 исполняемых строк. В HTTP/API нет cancel/reject для join; описанного владельцам способа восстановления не нашёл.

**Первопричина:** Pending заменяется при смене ownership, но не при смене content; confirm правильно запрещает устаревшую версию. UI не даёт перехода восстановления. Source: `src/catalog/services/organization_ownership.py:257; src/catalog/services/organization_ownership.py:276; src/catalog/services/organization_connections.py:115`.

**Доказательство:** stale-join.json; browser-stale.json; screenshots/stale-request-390.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Django/UX: сначала согласовать явный lifecycle cancel/re-request и миграционную совместимость; сохранять fail-closed, CAS и повторные согласия, не автоматически одобрять/переносить сеть. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-12.md).

### ORG-13 · P2 · Редактор нового сеанса показывает старый ServerDraft поверх отправленной заявки

**Роль:** Владелец, новое устройство/сеанс. **URL:** `/ru/account/organizations/13/`.

**Шаги:** Создать организацию13. Через настоящий drafts API сохранить name_en Older server working copy. Через HTML save отправить Explicit latest submitted на модерацию. Открыть кабинет из чистого сеанса без sessionStorage.

**Ожидание:** Редактор различает отправленную заявку и старую рабочую копию; старый черновик не подменяет успешно отправленные данные молча.

**Факт:** Draft201, submit302, свежий GET200. Candidate pending содержит Explicit latest submitted; поле редактора Older server working copy. В том же старом браузере local recovery может скрыть дефект.

**Первопричина:** Сначала payload candidate накладывается на live, затем ServerDraft с совпадающим source_version безусловно перекрывает его; версия candidate/явная отправка не учитываются. Source: `src/catalog/controllers/organization_workspace.py:268`.

**Доказательство:** candidate-overlay.json; browser-candidate-overlay.json; screenshots/candidate-overlay-390.png. Все JSON в [evidence](organization-deep-audit-2026-10-08/evidence), изображения в [screenshots](organization-deep-audit-2026-10-08/screenshots).

**Область исправления / следующий шаг:** Django drafts + frontend: определить порядок live/candidate/working draft, связать рабочую копию с версией candidate или потреблять только действительно отправленный draft с CAS. Показать выбор восстановления, если данные различаются; сохранить более новый параллельный черновик. [Готовый промпт](organization-deep-audit-2026-10-08/prompts/org-13.md).

## 4. Tech debt

Два поколения транспорта живут одновременно: операция с preview/receipt и старые join/confirm/detach/API. Новые экраны проверяют больше контекста, старые опираются на canonical ownership, где нет того же visibility gate. Удаление старых маршрутов здесь не проводилось: нужна оценка совместимости клиентов и регрессий.

Live/candidate/ServerDraft/sessionStorage имеют разные версии, но UX показывает их как один редактор. ORG-02 и ORG-13 — разные проявления отсутствия согласованного порядка версий и подтверждённого сохранения. Лучше сначала исправить сохранность, затем косметику.

Workspace содержит формы разной эпохи, часть labels разметкой вручную, часть Form-generated, часть переводов вычислена при импорте. Это объясняет несовпадение UI/error/ARIA языка и размеров. Сохранять постоянное место, программу, занятие, группу и тариф отдельными сущностями; расписание места не объединять с schedule_text группы.

## 5. Risks и пределы

- Receipt после detach может скрыть строку как unavailable, когда инициатор лишается сетевого доступа и карточка не входит в quality-visible search. В базе операция66 действительно `detached`; первый browser assertion по видимому tr получилFAIL. Это нужно отдельно уточнить продуктово: сохранить безопасную историческую квитанцию об успехе без раскрытия текущего приватного контента. Не классифицировано как утечка/неуспешная отвязка.
- Утрата inherited контактов реальна; direct-detail после detach200 не означает попадание во все quality catalog/map queries. Перед изменениями отдельно согласовать серверно вычисляемое предупреждение о публичной доступности. Требования каталога не смягчать.
-7 ViewTransition InvalidStateError в раннем browser-main2 (при screenshot animations=disabled/navigation); последующие108 layout loads —0. Причина noise/реальный shared motion дефект не классифицирована. Не заявляю, что весь прогон имел0 JS errors.
- Стенд — текущий локальный dirty code. Не проверялись production threat model, эксплуатация без локального session, нагрузка1000+ филиалов, реальные внешние письма/доставка, Redis/shared worker lifecycle, другие браузеры и физические телефоны.
- Новая branch67 создана, но её полное заполнение/публикацию через редактор места в этом прогоне не довёл. Управление специалистом/документы требуют своей отдельной свежей приёмки; снимки других сущностей не подменяют её.

## 6. Dead/legacy candidates

| Кандидат | Состояние | Следующее действие |
|---|---|---|
| organization_workspace_join/confirm/detach | Живые маршруты, exercised; не dead | Согласовать единые guards/совместимость |
| ownership API join/detach | Живой API, private join200 | Тот же gate; совместимость API отдельно |
| data-join-form JS | Историческая ветка handler; rendered use полностью не доказан | Найти все consumers перед удалением; не удалял |
| Новые operations/receipts | Рабочие, не замена владению | Сохранить actors, CAS/idempotency/per-row results |

Ни один кандидат не удалён.

## 7. Выполненные проверки и пробелы

**Fresh server:**138 tests/OK за46.515s; дополнительно4 switches/OK за4.514s — всего142. Это не полный серверный набор.

```bash
.venv/bin/python .tmp/content-entry-final-20261007/run_unit.py \
 catalog.testcases.test_organization_connections \
 catalog.testcases.test_organization_connections_concurrency \
 catalog.testcases.test_task33_organization_workspace \
 catalog.testcases.test_task33_ownership \
 catalog.testcases.test_task33_permissions \
 catalog.testcases.test_task33_program_workspace \
 catalog.testcases.test_organization_directory \
 catalog.testcases.test_task33_drafts
.venv/bin/python .tmp/content-entry-final-20261007/run_unit.py catalog.testcases.test_public_section_switches
```

Helper очищает environment, выставляет DJANGO_TESTING=1 и проверяет изоляцию до Django setup. Unit runs используют отдельную disposable testDB, не browser fixture DB. Логи сохранены в evidence/server-scope.log и section-switch-tests.log.

**Browser:** Chromium/Playwright CLI, отдельные context и только localhost8788.72 owner/public layout cases =6 экранов ×3 языка ×4 ширины;36 admin cases =3 экрана ×3 реально переключённых языка ×4 ширины. Итог108 HTTP200/layout checks,0 matrix pageerror. Они доказывают загрузку/границы формы, **не полную отправку каждого сценария в каждой комбинации**. Реальные create/save/review/confirm/detach действия отдельно выполнены преимущественно в RU. ПК/mobile screenshot предоставлены; физические устройства не использованы.

```bash
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh \
 --session organization-audit-20261008 run-code \
 --filename .tmp/organization-audit-20261008/browser_matrix.js
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh \
 --session organization-audit-20261008 run-code \
 --filename .tmp/organization-audit-20261008/browser_extra_matrix.js
```

Остальные scripts/result JSON именованы по scenario в .tmp/organization-audit-20261008 и evidence.5 keyboard assertions: Enter details, Tab exit, Space selection, Enter preview, Space consent. Дополнительный контроль visible input/select/button bounding boxes360/390/768/1440: clip0. Подозрение из раннего full-page screenshot о постоянном горизонтальном обрезании **не подтвердилось** при отдельном измерении; оформлено как false alarm, не задача исправления. Маленькие controls20–22px подтверждены независимо.

Harness-ошибки не выданы за appbugs: двойной /ru prefix, IDs вне первой страницы20, неверный CSS numeric attribute selector, закрытый translation disclosure, hidden Jazzmin tab, native URL invalid безPOST, несуществующий role button QA безJS, late chrome-error navigation. Все соответствующие проверки повторены корректно. Admin selection выполнен поддерживаемой кнопкой connection_selection; скрытый native action select не использован как доказательство поломки массового пути. Ранний exact-label check «Изменения на модерации» былFAIL из-за icon ligature; модель/pending chip и дальнейшая moderation подтвердилиPASS. Ненайденный place старымjoin отвечает контролируемым409 — не проблема404/400. HTTP200/409, ошибочно записанные в поле status первых scripts, разобраны по условию и последующим DB assertions. Нельзя механически складывать все raw FAIL как баги.

Таблица — 48 самостоятельных сценариев: **PASS 30 / FAIL 11 / NOT RUN 7**. Один сценарий может покрывать несколько asserts; это не число всех тестов.

| Сценарий | Статус | Доказательство / граница |
|---|---|---|
| Создание сети без филиалов — кабинет | PASS | Org11: HTML create, zero branches, draft |
| Частичный ввод создания → refresh той же вкладки | PASS | browser-main2; sessionStorage |
| Создание → сбой сети → восстановление | FAIL | ORG-03 |
| Обычное server autosave → reload | PASS | browser-main2 |
| Перекрывающиеся autosave ответы | FAIL | ORG-02 |
| Отправка → модерация → публичная сеть без филиалов | PASS | browser-finish; final-domain-state: Org11 published, public200 |
| Изменение опубликованной сети сохраняет старый public до review | PASS | live/candidate divergent; final-domain-state |
| Новый сеанс после explicit submit | FAIL | ORG-13: pending верный, редактор показывает старый рабочий draft |
| Дубликат организации: предупреждение, явное отдельное создание | PASS | browser duplicate409; create separate — fresh server tests |
| Поиск готового места по имени/адресу | PASS | browser selection/search; search-observe: адрес25→ID56 |
| Выбор сохраняется при смене поиска | PASS | browser-main2:10 carried IDs |
| Подключение10 готовых мест собственнику сети | PASS | receipt3393a59d…;10 DB business links |
| Галерея/основное фото/порядок/занятия/группы/цены/часы | PASS | 10 cards,30 real files SHA+IDs+fields; preservation-result |
| Частичный результат: existing + другая сеть + чужой owner | PASS | already_connected/other_network/requested; pending64 then second consent |
| Чужой владелец: два согласия | PASS | browser-finish; owner remains outsider |
| Новый отдельный филиал в сети | PASS | browser-finish: Place67 draft, separate branch workspace |
| Полное заполнение и публикация этого нового филиала | NOT RUN | Организационный быстрый create прошёл; редактор места67 целиком не проходил |
| Повторное подтверждение того же receipt | PASS | owner connect replay; detach replay; real concurrency tests |
| Другой редактор изменил место после preview | PASS | extra-probes:changed, place53 standalone |
| Expired preview, >100, bool, пустой/повторяющийся ID | PASS | extra-probes/server-probes; controlled errors |
| CSRF, GET-mutation, foreign receipt/workspace | PASS | 403/405/404; browser/server probes |
| Угадывание ID чужого приватного draft | FAIL | ORG-01: legacy/API leak, bulk blocks |
| Админ: выбор10 → organization → business без согласий | PASS | browser-admin-supported:10 no_rights, no implicit owner authority |
| Админ: informational explicit review →10 links | PASS | browser-admin-supported; member view32true/view42false |
| Админ: создание → draft → reload → submit → approve → published edit draft | PASS | Org12 browser-admin-editor/final finish; source canonical create/propose |
| Новая отвязка: обзор программ/доступов/контактов и consent | PASS | impact:program1,network grants2,direct1; missing consent409 |
| Отвязка: программный snapshot, группы/тарифы/direct grant | PASS | Activity26 local approved snapshot; Group27/Price32 retained; managerfalse,parenttrue |
| Legacy отвязка без обзора | FAIL | ORG-04: authenticated owner POST succeeds without preview |
| Перенос в другую сеть | PASS | Separate detach; old network owner PermissionDenied; actual place+target owner links toOrg6 |
| Устаревший pending запрос после content edit | FAIL | ORG-12: manual_review, both confirms +retry rejected; recovery path absent |
| Две вкладки: version conflict и сохранение вводаB | PASS | browser-tabs:409,B retained; raw English message ORG-06 |
| Ошибки всех полей редактора/сводка создания | FAIL | ORG-05/06:400 no field errors; technical Name az |
| Обычное приглашение MANAGER | PASS | POST200; one PENDING/MANAGER DB invitation |
| Приглашение: итоговый список/описание после reset | FAIL | ORG-08 |
| Приглашение без JS | FAIL | ORG-07: GET email+CSRF;0 invitations |
| Принятие/истечение/повтор приглашения, отзыв, transfer race | PASS | Server test level only: GrantTests/TeamConcurrencyTests |
| Принятие/отклонение/отзыв приглашений через browser UI | NOT RUN | Не подменять backend tests доказательством UI |
| Общие программы: locked revisions, branch override, access | PASS | Fresh test_task33_program_workspace + ownership snapshot tests; local detach snapshot observed |
| Полный UI create/review групп, тарифов и программ из сети | NOT RUN | Здесь проверены сохранность и серверный contract, не все их editors |
| Public-section switches | PASS | 4 fresh test_public_section_switches, server/HTTP level |
| Выключение/включение флага через rendered admin UI | NOT RUN | В браузере переключатель в этом прогоне не менялся |
| RU/AZ/EN ×360/390/768/1440: owner6 views +admin3 views | PASS | 108 successful layout loads, actual language checked in final admin matrix;0 matrix pageerror |
| Визуальная согласованность и размер secondary controls | FAIL | ORG-09:20–22px; форма визуально неоднородна |
| Язык labels/errors/ARIA | FAIL | ORG-06/10/11; корректная загрузка страницы ≠ локализация всего UI |
| Клавиатура: disclosure,Tab,Space selection/consent,Enter preview | PASS | 5 browser_keyboard assertions; no trap in tested segment |
| NVDA/VoiceOver, все controls/зум/контраст | NOT RUN | Native screen readers и полный WCAG audit не запускались |
| Приватные документы специалиста после изменения сети | NOT RUN | В этой организации документацию личности не создавал/не открывал |
| Реальная почта/SMS/внешние карты/production | NOT RUN | External origins blocked; LocMem email/cache, no production credentials |

## 8. Recommendations и готовые промпты

Начать с ORG-01/02/03, затем ORG-13 и ORG-12. Только после сохранности данных и безопасного восстановления доводить сообщения/приглашения/визуал. Минимальные scope разделены; пользователь ещё не разрешал внедрение findings этого аудита.

[Все13 готовых промптов для копирования](organization-deep-audit-2026-10-08/prompts.md). В каждом есть reproduction, ограниченная область, canonical safeguards, позитивная/негативная регрессия, локальный стенд, RU/AZ/EN/responsive/keyboard и требование точного отчёта. Для ORG-04/12 изменения transport/lifecycle сначала требуют плана совместимости; для новой навигации ORG-09 — согласования макета. Тестами нельзя снять необходимость согласий или переписать expected только ради PASS.

## 9. Приоритеты и решение приёмки

| Приоритет | Количество | Что блокирует |
|---|---:|---|
| P0 |0 подтверждено| Текущая критическая компрометация не подтверждена |
| P1 |3| Privacy gate и два случая потери ввода |
| P2 |9| Ошибки, stale recovery/candidate layer, старый detach, team, layout, admin labels |
| P3 |1| Локализованное доступное имя paginator |

**Приёмка не пройдена.** Базовые операции подключения/согласий/конкуренции можно считать подтверждёнными только в указанных локальных сценариях; редактор и recovery требуют исправлений и повторного прогона. Производственный запуск не рекомендован на основании одних142 зелёных серверных тестов.

## Скриншоты

Все изображения свежие с localhost8788 и вымышленных карточек. Длинные страницы лучше открывать по ссылке в полном размере.

| Экран | PC1440 | Mobile390 |
|---|---|---|
| Кабинет сети | [PC](organization-deep-audit-2026-10-08/screenshots/matrix-workspace-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/matrix-workspace-390.png) |
| Поиск готовых мест | [PC](organization-deep-audit-2026-10-08/screenshots/matrix-search-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/matrix-search-390.png) |
| Подтверждение10 | [PC](organization-deep-audit-2026-10-08/screenshots/connect-review-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/connect-review-390.png) |
| Итог по10 | [PC](organization-deep-audit-2026-10-08/screenshots/connect-result-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/connect-result-390.png) |
| Последствия отвязки | [PC](organization-deep-audit-2026-10-08/screenshots/detach-impact-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/detach-impact-390.png) |
| Админ — массовое подтверждение | [PC](organization-deep-audit-2026-10-08/screenshots/admin-review-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/admin-review-390.png) |
| Административный редактор | [PC](organization-deep-audit-2026-10-08/screenshots/admin-editor-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/admin-editor-390.png) |
| Public организация | [PC](organization-deep-audit-2026-10-08/screenshots/matrix-public-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/matrix-public-390.png) |
| Stale pending recovery | [PC](organization-deep-audit-2026-10-08/screenshots/stale-request-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/stale-request-390.png) |
| Candidate перекрыт старым draft | [PC](organization-deep-audit-2026-10-08/screenshots/candidate-overlay-1440.png) | [Mobile](organization-deep-audit-2026-10-08/screenshots/candidate-overlay-390.png) |

[Подписи админки в RU](organization-deep-audit-2026-10-08/screenshots/admin-labels-390.png), [Потеря при autosave](organization-deep-audit-2026-10-08/screenshots/draft-race-390.png), [маленькие team поля](organization-deep-audit-2026-10-08/screenshots/clipped-team-390.png), [ошибка без объяснения](organization-deep-audit-2026-10-08/screenshots/edit-400-no-error-390.png), [конфликт двух вкладок](organization-deep-audit-2026-10-08/screenshots/two-tabs-conflict-390.png), [Name az](organization-deep-audit-2026-10-08/screenshots/create-error-390.png), [неверная роль после reset](organization-deep-audit-2026-10-08/screenshots/team-reset-390.png).

Исходные runtime/baseline большие манифесты остались в ignored .tmp, секреты и env не копировались. В доставку вошли только source metadata, собственные synthetic results, безопасные логи тестов и скриншоты; token в no-JS URL редактирован. SHA каждого артефакта — evidence-sha256.json.

Завершение: 2026-10-08, финальная сверка source/HEAD/стенда и всех относительных ссылок выполнена. Собственный active_run закрыт в NONE; приложение0 edits, исторические материалы сохранены.
