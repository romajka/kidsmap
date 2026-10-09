# Управление организациями: перепроверка и проект решения

Дата: 2026-10-06. Роль: kidsmap-orchestrator, последовательное выполнение одним агентом; независимые специалисты не запускались. Definition: [.agents/agents/kidsmap-orchestrator/agent.md](/home/ramin/kidsmap/.agents/agents/kidsmap-orchestrator/agent.md).

LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`. Проверялся текущий dirty WORKTREE, включая ранее внесённые изменения мероприятий. `active_run: NONE`. PRODUCTION не исследовался и не изменялся. Исходные 4433 файла зафиксированы по SHA256 перед работой.

Статус: **дизайн для согласования, приложение не изменено**. Добавлены только отчёт, план, HTML-макет, скриншоты и результаты проверок. Scratch-пробы находятся в ignored `.tmp/organization-design-20261006/`. Реализация, миграции новой функциональности, commit/push/deploy не выполнялись.

Прочитаны AGENTS.md, canonical registry/role/architecture/source-of-truth/audit-contract и [исходный аудит](/home/ramin/kidsmap/docs/qa/content-entry-audit-2026-10-06.md). Применены kidsmap-ui-design + frontend-design, writing-plans и verification-before-completion. Граф использовался для навигации, затем проверен исходный код; coverage best-effort, template line 89 помечена partial и прочитана непосредственно.

## 1. Состояние области

**Организация** объединяет бренд, общие контакты, программы и сотрудников. Она может существовать без мест; адрес и часы работы ей не приписываем. **Филиал** — конкретная существующая карточка Place, подключённая к организации. Подключение не пересоздаёт карточку, не передаёт её владельца и не публикует её автоматически.

Место, Activity, OfferingGroup, PricingPlan остаются разными объектами. Часы работы Place и расписание OfferingGroup не объединяются. Общая Program принадлежит организации; локальное занятие ссылается на неё только по действующим правилам.

Стенд текущего исходного кода: `http://localhost:8781/qa/`. Изолированный PostgreSQL `qa_stage04`, тесты — `test_qa_stage04`, контейнер `kidsmap-local-20261006`, без сети и опубликованных DB-портов. Launcher очищает окружение, задаёт `DJANGO_TESTING=1`, пустые внешние DATABASE_URL/Redis, изолированные cache/media/email и устанавливает сетевые/SQL guards. Старый стенд 8780 не использован как доказательство текущей версии. HTML-макет обслуживается отдельным локальным сервером 8782.

Браузерное сравнение текущей версии: RU/AZ/EN × 360/390/768/1440 × четыре экрана = **48 открытий HTTP 200, без горизонтального выхода**. Экраны: организация владельца, создание организации, Organization add в админке, список Place в админке. Создание/связи в существующем browser fixture не отправлялись; POST браузера — только локальная смена синтетической роли.

## 2. Сильные стороны

- Создание организации без филиалов уже работает: `create_organization`, workspace create, тест `test_empty_account_creates_organization_without_address_or_branch`.
- Есть отдельный `create_branch`. Новый филиал принадлежит владельцу организации; сотрудник остаётся автором аудита. Selected-places grant автоматически не расширяется.
- Есть текущие `request_join`, `confirm_join`, `approve_informational_join`, `detach`; они проверяют владельцев, версии и родительские связи под блокировками.
- Поиск/пагинация уже подключённых филиалов существует. Admin Place search уже ищет по AZ/RU/EN/legacy-названию и адресу; это можно использовать для массового выбора.
- Pending и informational не дают сетевых бизнес-прав. Публикация, владение и принадлежность организации — разные состояния.
- Подтверждённый повтор и доменный повтор detach уже идемпотентны. Уведомления имеют deduplication по событию/сущности/версии/получателю.

Источники: [ownership](/home/ramin/kidsmap/src/catalog/services/organization_ownership.py:220), [business_team](/home/ramin/kidsmap/src/catalog/services/business_team.py:326), [workspace](/home/ramin/kidsmap/src/catalog/controllers/organization_workspace.py:105), [Place admin search](/home/ramin/kidsmap/src/catalog/domain_admin/place.py:1797).

## 3. Реальные проблемы текущего интерфейса

| ID | Приоритет / эффект | Перепроверка и первопричина | Исправление в предложенном scope |
|---|---|---|---|
| ORG-UX-01 | P2, подключение десятка карточек неудобно | RU live owner form: 100 option, одно место, только название. `_detail_context.owned_places` ограничен собственными standalone, template обычный select. Адреса и состояния недоступны | Отдельный поиск готовых карточек, несколько выбранных ID, состояние каждой строки, серверная пагинация |
| ORG-UX-02 | P2, можно неверно оценить состояние связи | `branches` выбираются по FK; `affiliation_current` нужен отдельно. Template отображает type/contacts, но не объясняет устаревшую связь и её влияние на права | Показывать актуальность и тип связи отдельно от статуса публикации; pending — кто должен подтвердить |
| ORG-UX-03 | P2, последствия отвязки не видны до записи | Live формы detach — непосредственный POST, нет onsubmit-confirm; JS не обрабатывает detach. Последствия находятся только в сервисе | Отдельный серверный preview последствий, явное подтверждение, проверка версий |
| ORG-UX-04 | P2, нет безопасной массовой административной операции | В PlaceAdmin.actions нет операции организации. Organization editor.actions=None. Обычное изменение FK обошло бы consent/ACL/versioning | Добавить отдельную action → target → preview → confirm → per-row result, использующую только канонические переходы |
| ORG-UX-05 | P2, повтор UI не равен повтору сервиса | Доменный `detach` повторяемый; workspace route сначала ищет Place с текущим FK, поэтому повтор после успешной отвязки даст 404. Generic connection errors не объясняют строку | Журнал операции и конечный результат, повтор того же ключа без повторного перехода; понятные коды строки |
| ORG-UX-06 | P3, непонятные поля/роли | Live Organization add показывает Name az / Name ru / Name en и одновременно стандартные Save×3 + draft/submit. Owner team содержит Editor/Manager, grant scope Selected places. Общий legacy MODERATOR preset — только view/stats | Локализовать конкретные поля организации; organization-specific действия сохранения; role/scope и список фактических прав |
| ORG-UX-07 | P3, риск лишней карточки | Новый филиал сразу показывает «Создать отдельно при похожем названии». Для организации эта галочка уже появляется после duplicate_detected | Для филиала сначала показать найденные совпадения и кнопку подключения; отдельное создание — после подтверждённого предупреждения о дубле |

Все findings: LOCAL WORKTREE, confidence high для DOM/source; owner — организация/workspace/admin. Ссылки: [template connection](/home/ramin/kidsmap/src/catalog/templates/pages/organization_workspace.html:360), [detach route](/home/ramin/kidsmap/src/catalog/controllers/organization_workspace.py:222), [OrganizationForm](/home/ramin/kidsmap/src/catalog/domain_admin/business.py:47), [roles](/home/ramin/kidsmap/src/catalog/services/place_access.py:13), [scope labels](/home/ramin/kidsmap/src/catalog/models/business_team.py:21). Реальная эксплуатация или production-потеря данных не установлены.

## 4. Технический долг и предлагаемый механизм

Новые UI не должны вычислять право подключения по роли, FK или доступу `place.edit`. Источником решения остаётся свежий серверный resolver и канонические переходы. Нужен небольшой coordinator `organization_connections`, общий для кабинета и админки, без переписывания ownership/business_team.

Предлагаемый контракт:

1. **Поиск.** AZ/RU/EN/legacy-названия + адрес; ID, название, адрес, опубликованный статус и допустимые сведения о текущей организации. Авторизованные собственные карточки и публичные карточки других владельцев. Чужие закрытые черновики, владельцы, email и сотрудники не выдаются. Поиск и счётчики выполняются после ограничения видимости. Размер страницы 20, batch до 100 явно выбранных уникальных карточек. Выбор сохраняется при поиске и пагинации; «выбрать на странице» не выбирает всю базу.
2. **Цель.** Одна организация и один явно выбранный тип связи. После смены цели/типа требуется новый preview. Архивная организация недоступна для новых связей.
3. **Просмотр.** Серверный снимок с actor, ID цели, mode, выбранными ID, ownership/content versions и состояниями FK/type/current requests/program dependencies. Срок действия preview 10 минут; просроченный preview требует просмотра заново. Не доверять expected versions и reason codes из браузера.
4. **Подтверждение.** CSRF/POST; журнал операции с уникальным `(actor, idempotency_key)` и fingerprint payload/preview. Тот же ключ с другим payload отвергается. Проверяется текущая видимость и права; результат не раскрывает скрытые данные после отзыва доступа.
5. **По строкам.** Одна атомарная транзакция на карточку, итог строки фиксируется в той же транзакции, что и переход. Независимые строки могут завершиться с разными результатами. Блокировки доменных объектов: Organization → Place → Program → Activity → request, PK order. Ошибка одной строки не откатывает остальные. Preview не держит блокировки до нажатия подтверждения.
6. **Изменение редактором.** Любое значимое расхождение ownership/content/FK/type/request/program snapshot даёт `changed` без записи этой строки. Ownership сменился и вернулся — всё равно отказ по ownership_version. Не обновлять preview и не повторять переход автоматически.
7. **Повтор и разрыв связи.** Два одновременных submit с одним ключом получают одну операцию. При обрыве ответа пользователь запрашивает её результат. После перезапуска продолжаются только незавершённые строки, с проверкой прежнего снимка; завершённые не выполняются снова. Ошибочные строки получают новый просмотр/подтверждение и новый ключ.

Для этого предлагаются две небольшие новые таблицы журнала (операция/строка) и additive migration. Они хранят ID, числовые версии, fingerprint и codes, без копирования email/приватных полей. Административный CRUD журнала не открывается. Receipt не является источником текущего права или текущей принадлежности: эти сведения всегда перечитываются. Пока это **предложение**, таблиц/миграции в приложении нет.

## 5. Затрагиваемые правила и последствия

### Матрица прав: сохраняем действующее поведение

| Ситуация | Канонический переход / результат | UI |
|---|---|---|
| Один активный владелец места и организации | `request_join(business)` подтверждает обе стороны и подключает | «Подключить»; предварительно показать открывающийся сетевой доступ |
| Инициатор владеет одной стороной, другая имеет другого владельца | request pending → `confirm_join` другим владельцем | «Отправить запрос» → «Ждёт владельца места/организации»; до подтверждения сетевых прав нет |
| Сотрудник сети имеет `place.edit` или `branch.create`, но не владеет стороной | `_side_owner` не разрешает бизнес-подключение | Не показывать возможность подключения только по этому grant; отдельное создание филиала остаётся по `branch.create` |
| Администратор/superuser не владеет ни одной стороной | Нет blanket business-join bypass | «Нет права на бизнес-связь». Не подставлять владельца вместо request.user |
| Уполномоченный KidsMap reviewer, явно выбран informational | `request_join(informational)` → `approve_informational_join` после явного review | «Информационная связь»; не открывает доступ сотрудников сети. Reviewer: active staff + superuser или `catalog.change_placeownershiprequest` |
| У места/организации нет владельца | Business требует обоих владельцев | «Сначала подтвердите право управления»; не захватывать и не назначать владельца массовой операцией |
| Уже текущая связь с этой целью и тем же типом | Идемпотентный already_connected | Без записи/уведомления от coordinator |
| Связь с другой организацией, включая устаревший FK | request_join отклоняет до detach | Конфликт; исходная связь не меняется. Нет автоматического переноса |
| Текущий тип связи отличается | Отдельное осознанное действие, вне bulk | Не превращать business в informational и обратно без отдельного просмотра последствий; не исправлять конфликт сменой mode |
| Program принадлежит другой сети | `_apply_link` отклоняет несовместимость | «Программы другой организации»; manual review, без перепривязки Program/Activity |
| Pending ownership snapshot устарел | `request_join` умеет отменить устаревший pending и создать новый | Новый просмотр и актуальные подтверждения, только через сервис |
| Pending content snapshot устарел | `confirm_join` отклоняет stale; автоматической отмены/пересоздания такого запроса сейчас нет | «Карточка изменилась; требуется проверка». Не обещать работающую кнопку отмены/повторной отправки; resolution отдельного неподдерживаемого перехода не входит в scope |

Волонтёрский informational workflow сохраняется с его отдельными ограничениями. Массовая админ-операция не расширяет волонтёрские права и не делает автора владельцем.

`affiliation_current`: совпадение organization_id, org не архивна, известный kind и совпадающие ownership_version обеих сторон с сохранёнными join versions. Существующий FK или approved старого запроса сами по себе не дают актуальной связи. Бизнес-доступ дополнительно требует kind=`business` и действующего grant/owner. `content_version` не участвует в долговременной актуальности уже подтверждённой связи, но участвует в согласовании pending и в новом preview.

### Отвязка и перенос

- `detach` разрешён владельцу Place **или** организации; не заменяем это правилом «оба согласия» и не выдаём staff override. Допускается отвязка от архивной организации. Expected ownership version проверяется.
- Уполномоченный reviewer informational не получает автоматического права detach. Если у обеих сторон нет владельца, этот переход недоступен по действующему `_side_owner`; массовая операция не обещает отмену по административной кнопке.
- Владелец, slug, publication/is_active и карточка не изменяются. Фото, собственные контакты, отзывы, группы, тарифы и расписание остаются. Отдельные часы работы Place не превращаются в расписание занятий.
- У Activity с Program прекращается live связь `program_id`. Сохраняется последняя утверждённая версия текста/таксономии и source ID/version; локальные дополнения сохраняются. Если безопасного утверждённого snapshot/version нет, операция останавливается для ручной проверки. Нельзя безусловно обещать отвязку любой карточки.
- Владелец старой сети и её сотрудники теряют доступ, полученный именно через эту связь. Прямые grants Place остаются. Записи сетевых назначений не удаляются: после повторного подключения к той же сети доступ может вернуться, если grant всё ещё актуален.
- Selected-places scope ограничивает права на Place; отдельно выданные organization.view/edit и program.manage относятся к организации, а не только к выбранному филиалу. Название роли не заменяет список этих прав.
- Унаследованные телефон/сайт/WhatsApp сети перестают действовать; собственные контакты не заменяем и не копируем автоматически. Публичная карточка не удаляется, но набор отображаемых сетевых контактов/ссылок может измениться.
- **Перенос — два явно подтверждаемых шага.** Сначала preview → detach. Затем отдельный выбор новой сети → preview → request_join/confirm_join. Между шагами и до нового подтверждения место самостоятельное. Если новое подключение не получилось, результат прямо говорит «Место отсоединено; новая сеть не подключена», с переходом к повторному просмотру. Автоматического rollback старых программ/прав или обещания атомарного переноса нет.

### Слова и роли

| Сейчас | Предлагаемый текст | Что сохраняем |
|---|---|---|
| Name az/ru/en в Organization admin | Название организации (AZ/RU/EN), полная локализация | Те же поля/required/publication validation |
| «Место подтвердило» | «Владелец места подтвердил» / «Ждёт владельца места» | Значения confirmed_at и owner IDs |
| «Связать своё место» | «Подключить существующие места» | Consent и actual permissions |
| Editor / Manager | Редактор / Менеджер; рядом перечислены фактические права | EDITOR/MANAGER codes и actions без изменения |
| Legacy MODERATOR бизнес-команды | Наблюдатель — стандартно просмотр/статистика | MODERATOR code и preset, не роль модератора KidsMap |
| Selected places / All network / «Область» | Выбранные филиалы / Вся сеть / Область доступа | selected_places/all_network; будущие филиалы входят только в all_network |
| Непонятные стандартные Save действия Organization | Сохранить черновик / Отправить на проверку; переходы отдельно | Текущий candidate/live и review контракт, без автопубликации |

Проверяем все потребители общих role choices: OwnerTeamMembership, OwnerTeamInvitation, OrganizationGrant, OrganizationTeamInvitation, приглашения и admin diagnostics. Платформенную роль «Модератор KidsMap» не переименовываем. Organization field labels задаём в OrganizationForm, не глобальной заменой общего gettext «Название». Все copy RU/AZ/EN; существующие значения enum и права не меняются.

## 6. Legacy / удаление

Удалять ничего не предлагается. Старые API/одиночные POST остаются доступными и используют существующие сервисы. `transfer_owner` меняет **владельца**, это не перенос Place между организациями; не использовать его для переноса филиала. Legacy MODERATOR code не является dead code и не удаляется. Информационные связи не переводятся массово в business.

## 7. Выполненные проверки и пробелы

### Серверные проверки

Первый штатный запуск:

```bash
.venv/bin/python .tmp/event-admin-fix-20261006/run.py catalog.testcases.test_task33_ownership catalog.testcases.test_task33_permissions catalog.testcases.test_task33_organization_workspace catalog.testcases.test_task33_public_details > .tmp/organization-design-20261006/domain-tests.log 2>&1
```

101 tests, exit 1: 12 ошибок FK `category=EDU` в workspace fixture и 1 failure branch-create 400/302 в той же области. После TransactionTestCase flush в независимом workspace setUp не создаётся Category. Это не скрыто и не объявлено штатным зелёным запуском.

Следующий isolated harness наследует 12 штатных WorkspaceTests **без изменения assertions**, явно создавая синтетическую Category/Subcategory перед setUp. Добавлены 7 scratch-проб действующих сервисов. В первой версии scratch-пробы попытка модельного save content_version закономерно отклонялась структурным guard; сама проба исправлена на fixture-имитацию завершённого редактирования content через SQL update, без записи organization_id.

Окончательный запуск:

```bash
.venv/bin/python .tmp/organization-design-20261006/run-probe.py catalog.testcases.test_task33_ownership catalog.testcases.test_task33_permissions catalog.testcases.test_task33_public_details domain_probe > .tmp/organization-design-20261006/probe-tests-final.log 2>&1
```

**108 tests, 24.722s, OK, exit 0** = 89 существующих ownership/permissions/public-details tests + 12 workspace assertions с явной category fixture + 7 новых scratch-проб. PostgreSQL concurrency tests включены. Это проверка действующих контрактов, а не новой массовой операции.

Scratch-пробы подтверждают:

- 10 ready Places, 12/12 publication readiness: request_join → repeat → detach → repeat, без смены PK/slug/owner/publication/photo и без изменений gallery/Activity/OfferingGroup/PricingPlan/PlaceScheduleDay/Interval.
- Superuser без владения стороной не создаёт business-link; informational reviewer workflow не выдаёт ему place.edit.
- Другая сеть блокирует подключение без скрытой отвязки.
- Изменение content_version после первого согласия блокирует confirm_join второй стороной.
- Прямой grant сохраняется, сетевой прекращается; повторная связь может восстановить selected network scope.
- Отвязка общей Program сохраняет утверждённую копию, source ID, группы/цены/часы/фото.
- Смена владельца организации делает связь устаревшей и не даёт новому владельцу автоматического сетевого доступа.

Штатные concurrency tests дополнительно проверяют конкурирующие подтверждения, смену владельца, pending program edit и повтор приглашений. Нового receipt/batch concurrency пока нет. В launcher получено предупреждение о dirty models без соответствующего migration state; существующие модели/миграции не исправлялись в этом scope.

### Браузер и макет

- Текущая версия: 48 открытий, RU/AZ/EN × 360/390/768/1440, 0 HTTP/overflow failures. [Матрица](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/current-browser-results.json).
- Макет: 9 экранов × 3 языка × 4 ширины = **108 открытий**, без overflow, JS errors и неименованных input/select/textarea. [Матрица](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/prototype-browser-results.json).
- Keyboard/demo flows: 6 сочетаний RU/AZ/EN × 360/1440; Tab → skip-link, Space → выбор 10, поиск адреса с сохранением выбора, focus на пустое AZ-name, блокирование business для staff без владения, явное informational, consent → результат, replay notice, detach consent. **72 булевых assertions true**. [Результаты](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/prototype-flow-results.json).
- Сохранены 4 скриншота текущего UI и 12 скриншотов предложенного дизайна PC1440/mobile390. PC/mobile owner и detach визуально просмотрены; admin mobile и PC owner просмотрены до/после уточнений. Это rendered-browser evidence, не только inspection CSS.

**Не выполнено:** POST новых UI, реальная массовая операция, durable idempotency после перезапуска, новый batch race/partial retry, реальный перенос через новые экраны, screen reader/full WCAG/все браузеры, Google/geocoding, настоящая доставка email, production и full-suite. Фото в domain-пробах — синтетические file references; фактическая загрузка/сравнение байтов медиа в будущем acceptance обязательна. Public-details server tests выполнены; публичная карточка после действий нового UI в браузере не проверена, поскольку UI ещё не реализован.

## 8. Рекомендуемое решение и макеты

Реализовать только [план](/home/ramin/kidsmap/docs/superpowers/plans/2026-10-06-organization-management.md) после согласования. [Открыть интерактивный макет](http://localhost:8782/docs/qa/organization-design-2026-10-06/prototype.html?view=owner&lang=ru). На телефоне выбор экрана — верхний select, на PC — sidebar **только навигации макета**, не предложение новых разделов продукта. В приложении остаётся существующая навигация кабинета/админки.

Макет не отправляет backend-запросы. Preview/results/показанный повтор — демонстрационные состояния; автоматического сохранения или уже реализованного server receipt не обещаем. Информационный mode демонстрирует copy/availability; его отдельный полный bulk result пока не нарисован. Кнопка повторного просмотра в демо открывает пример полного review; в реализации должны попасть только выбранные проблемные строки.

| Экран | PC | Mobile |
|---|---|---|
| Поиск/подключение | [PC](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-owner-pc.png) | [Mobile](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-owner-mobile.png) |
| Массовый просмотр | [PC](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-admin-pc.png) | [Mobile](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-admin-mobile.png) |
| Частичный результат | [PC](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-result-pc.png) | [Mobile](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-result-mobile.png) |
| Отвязка/перенос | [PC](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-detach-pc.png) | [Mobile](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-detach-mobile.png) |
| Организация без мест | [PC](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-empty-pc.png) | [Mobile](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-empty-mobile.png) |
| Роли/область | [PC](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-team-pc.png) | [Mobile](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/proposed-team-mobile.png) |

## 9. Приоритет и решение

P0/P1 авария/эксплуатация не установлены. P2: поиск существующих мест, состояние связи, preview отвязки, безопасная bulk action и журнал результата. P3: подписи, roles/scope, условное предупреждение о дубле.

Решение этого прохода: **готово к рассмотрению пользователем; внедрение не согласовано**. Серверные правила владения, публикации, подтверждения, Program и grant не меняем ради вида. Blanket admin business override, новые правила отмены stale-content pending, автоматический перенос и миграция старых связей не входят в план. [Проверка сохранности](/home/ramin/kidsmap/docs/qa/organization-design-2026-10-06/preservation-results.json) фиксирует сохранность первоначальных файлов и HEAD.
