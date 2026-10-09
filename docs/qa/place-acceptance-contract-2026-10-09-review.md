# Backend-контракт приёмки постоянных мест, 2026-10-09

Bounded support django-reviewer; AUDIT ONLY. Изменён только этот новый отчёт. Application/DB/active_run не изменялись. Это source review, runtime-приёмку выполняет root.

LOCAL HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, branch `task33-progress`, dirty WORKTREE; `docs/task33/implementation-status.md:7` active_run NONE при чтении. Runtime UNKNOWN для support, root сообщил отдельный synthetic stand8792. Production NOT CONTACTED. Исторический content-entry отчёт прочитан как checklist, его выводы не использованы как актуальное evidence.

## Контракт lifecycle

| Действие | AS-IS | Source evidence |
|---|---|---|
| Самостоятельное место | Draft/inactive base; данные формы в candidate. Сравнивать Place и VolunteerPlaceRevision.payload, иначе ввод ошибочно выглядит потерянным | src/catalog/services/publication_forms.py:70-101; src/catalog/controllers/owner_places_controller.py:621-678 |
| Филиал | branch.create; владелец филиала — владелец организации, created_by — actor. business link + две ownership versions. Затем заполнить Place editor | src/catalog/services/business_team.py:326-335; src/catalog/controllers/organization_workspace.py:441-451 |
| Форма после сохранения | Подмешивает draft/pending/rejected candidate в editor; gallery/structured_schedule восстанавливаются из candidate | publication_forms.py:104-140; forms.py:1448-1463 |
| Отправка | Candidate pending; старый public content сохраняется. Existing draft submit передаёт payload с explicit_save=False | publication.py:320-360; owner_places_controller.py:819-855 |
| Отказ | Reason обязателен; candidate сохраняется; revision version растёт. Return — rejected, final reject — declined | publication.py:364-411; services/volunteer_proposals.py:43 |
| Одобрение | Повторная ACL автора, dependency/ownership/base-snapshot проверка; новое место проходит candidate readiness. Published legacy compatibility отдельна | publication.py:373-400 |
| Published edit | Разрешён для not deleted, есть candidate/live граница | owner_places_controller.py:411-412; publication.py:350-400 |
| Public detail | Presentation читает approved live, а не revision; каталог/detail имеют отдельный quality queryset | public_presentation.py:1-5,231-255; content_quality.py:241-275 |

Сокращённые имена services относятся к src/catalog/services; forms.py — src/catalog/forms.py; owner_places_controller — src/catalog/controllers. Admin place.py ниже — src/catalog/domain_admin/place.py.

## Что ждёт модерации

Точная граница publication.py:305-316,350-360:

- Immediate при explicit save: Place schedule/schedule_mode/notes/structured_schedule; scalar суммы цены; tariff суммы только при неизменной структуре/условиях и без gated pricing candidate. OfferingGroup.schedule_text также immediate.
- Gated: name/description AZ/RU/EN, category/subcategory, возраст, контакты, адрес/район/координаты, main/cover photo/gallery, nature/operating_state, price_mode, условия/формат/длительность/частота занятий, structural tariffs/nested_pricing и остальные whitelist content fields.
- Если conditions изменены в patch или уже pending, суммы цены также gated (publication.py:309-316,351-353).
- Explicit draft save тоже может обновить immediate часы/суммы. Draft candidate не означает, что всё сохранённое скрыто. Отдельный submit existing draft с explicit_save=False immediate не применяет.

## Локализация и готовность

Public detail использует presentation.name/description с lang источника (`src/catalog/templates/catalog/place_detail.html:36-38,338-359`). public_presentation.translated:21-32 — выбранный язык → AZ → legacy Place text. Показ AZ текста не записывает RU/EN переводы. `Place.name_i18n` имеет другой legacy fallback EN→RU→name (src/catalog/models/place.py:246-252); проверять фактического потребителя.

Owner/admin теперь используют evaluate_form_readiness: forms.py:1665-1675; admin place.py:347-369; permanent_place_rules.py:15-19. Старое divergence не актуальный finding.

Обязательны AZ name/description, согласованные category/subcategory, адрес/locality, возраст, business контакт, цена, часы. Short description — advice; photo и coordinates НЕ обязательны (place_readiness.py:158-294,426-440,462-492). RU/EN можно оставить пустыми. Test/lorem в имени/описании блокируется: fixtures — нормальные вымышленные названия.

Modes: tariffs/free/free_entry_paid_services/events (models/place.py:41-49). Tariffs требует active priced tariff; остальные три не требуют tariff (place_readiness.py:241-268). Общий/платный билет следует проверить как тариф, отдельного fifth price_mode нет.

Regular часы требуют meaningful structured days; legacy schedule text недостаточен для republish. always_open/by_appointment/variable/events самодостаточны, ближайшее Event не обязательно (place_readiness.py:278-294). OfferingGroup.schedule_text отдельно от Place.schedule_days; detail отдельно показывает занятия и часы (`place_detail.html:351-353,420-452`).

## Координаты и медиа

No pin допускается с выбранной locality/address (location_assignment.py:116-128). Парность, finite, lat±90/lng±180 validated (forms.py:1598-1610; models/place.py:366-375). Resolver проверяет совпадение города/района с точкой; stale прежний район может автообновиться (location_assignment.py:165-185).

0/0 исключено из map transport (map_payload.py:6-18); модель has_coordinates означает только non-null, не valid map point (models/place.py:532-534). Не принимать badge за доказательство пригодной точки.

Фото raw15MB/50MP/12000px; normalized2MB, batch22MB, gallery10; ошибки файла/порядка validate (forms.py:1473-1475,1677-1711). Foreign gallery ID отвергается (publication.py:184-219). Candidate gallery хранится отдельно (publication_forms.py:112-140). Bound admin сохраняет saved candidate photo/cover, включая clear (admin place.py:378-388,5292-5316).

## ACL, CAS и повтор

Owner editor требует managed place + place.edit (owner_places_controller.py:517-533). Direct owner не имеет place.publish; business org grants требуют current business affiliation, informational link не выдаёт ownership (place_access.py:68-94).

Подписанный token содержит ID/schema/content_version/live snapshot/dependencies/candidate version (publication_forms.py:10-34). propose row locks и оба versions (publication.py:320-339). Stale save не должен затереть свежую вкладку; ValidationError сохраняет bound form (views.py:1394-1431). ServerDraft actor/schema/source/version ACL и CAS (server_drafts.py:71-122); materialize idempotent при materialized_place_id (161-189).

**Runtime-гипотеза, не подтверждённый дефект:** explicit create form POST replay. views.py:1067-1076 каждый раз вызывает create_place до mark_explicit_save; publication_forms.py:78-86 token проверяет id/schema, затем создаёт новый base. Duplicate warning может скрыть повтор; create_separate позволяет одинаковое имя. Проверить response loss/retry и две create-вкладки. API materialize idempotency не доказывает form POST idempotency.

## UI wiring для root

Branch POST `/account/organizations/<org_id>/branches/create/` (src/catalog/urls.py:119); form name_az/category_id/allow_separate (organization_workspace.py:178-181). Moderation hub: textarea reason, hidden version, action=return для доработки, action=reject для окончательного отказа (`src/catalog/domain_admin/volunteer.py:299-310`, template admin/volunteer/hub_detail.html:13). Old volunteer review route uses note — distinct implementation.

Targeted labels (NOT RUN support): catalog.testcases.test_task33_publication; catalog.testcases.place_readiness; catalog.testcases.test_place_json_and_pricing_modes; catalog.testcases.test_task33_place_continuous; catalog.testcases.test_location_assignment; catalog.testcases.test_admin_candidate_cover; catalog.testcases.photo_workflow; catalog.testcases.image_uploads; catalog.testcases.test_task33_r1_owner_safety. Optional structural pricing test_task33_pricing; server drafts test_task33_drafts.

## Evidence/checks

| Check | Support result |
|---|---|
| Current snapshot, canonical role/contracts, graph/source mapping | PASS source |
| Candidate/live, moderation, localization, field gates/readiness | PASS source contract; runtime NOT RUN |
| Browser lifecycle, DB/public round-trip, width/language/files/network/focus | NOT RUN support; root responsibility |
| Isolated Django tests | NOT RUN support; no isolated settings passed |
| Production/integrations/commit/push/deploy | NOT RUN |

Commands executed in /home/ramin/kidsmap: `git rev-parse HEAD`, `git branch --show-current`, `git status --short`, `rg -n 'active_run' docs/task33/implementation-status.md`; bounded rg/sed/nl source reads of all referenced files. All actual source reads succeeded. Exploratory rg on assumed controllers/place_detail_controller.py, controllers/catalog_controller.py, controllers/publication_api.py, domain_admin/moderation.py, use_cases/* and *schedule* test glob exited2 because paths absent; actual views/presentation/volunteer wiring subsequently inspected. Python report write first attempted `python`, exit127 command not found; repeated with python3, no app effects.

Codebase Memory list_projects → current root; index_status ready; get_architecture discovery; search_graph OwnerPlacesController 63–968; check_index_coverage publication/publication_forms/forms/localized_content/place_readiness/admin place: metadata_match/no_recorded_issue. Full index generation2026-10-09T11:10:16Z; ignored inventory truncated2000/3435; templates parse_partial. Critical evidence checked actual source; graph absence not used for negative proof.

No confirmed runtime finding assigned in source-only scope. Source invariants cannot replace UI execution.

Handoff: kidsmap-orchestrator/root, verify stand source hashes, native no-pin/AZ-only/gallery candidate lifecycle, immediate hours/amounts vs gated identity/mode, stale-tabs and create replay. Register PLACE-QA defects only with observed reproducibility. DB/security impact reviewed by source; DB not contacted. UNKNOWN actual runtime/build until root manifest validation, real SDK/GPS, browser and persistence outcomes.

## WORKTREE hashes

```text
7766db2be4bddb69dbfa4f538013b09331b2e7dcda32514e52b7994647450ef6  src/catalog/services/publication.py
332c31ec37307148069c0c68eab6b212814935cbe9d2d37ba2a471a844ae1cdd  src/catalog/services/publication_forms.py
15ceea48730eb16dc6beb013170ffd589f6d31f41cdcf471c3182bbfd2f73b1b  src/catalog/forms.py
dd2a7e17c551d09e9d40ab7f1e711c87877625fddf3f39a1cdc2e3ff733eec28  src/catalog/services/place_readiness.py
458e998f12abfc9f738245a1d5d7b586ae9f316454f9c940347d6460b9bada06  src/catalog/services/public_presentation.py
fdf557b7017792519194d37f782cdbfb7f8e5988280599631ce21ba9a2de9152  src/catalog/services/location_assignment.py
67d0c2e3b93111eb34da02df2f6352a8fe691d79b14a5cdddc0bab6d0e942038  src/catalog/services/map_payload.py
94ee7e8d69f9e37e9ab046531c5912aaa3430ccfd477f018c06c8e9b76477817  src/catalog/services/server_drafts.py
eed12d2db2f21c3622078f0e1af8a8828c2900c1fa45cc2f85ca908861aa18ee  src/catalog/services/place_access.py
dddf6d9922ef7e62443b8e3d0530b4a47e4be24d03245d3403b6f3a011f227fb  src/catalog/controllers/owner_places_controller.py
54bb619399bd95fde672380f261b370d94db2d84a0c46240e045fa8441f211c3  src/catalog/domain_admin/place.py
164aca1ef1b1679caeaeda69b5b24aa942678bb1ad90614e3b5d1c7f845a9665  src/catalog/views.py
8358fe7a86e331fbd85cb1f7d4f9e637e45ced0059ac335150fa71d637902a3c  src/catalog/models/place.py
3da595ee0310bbd9a79da9cedcf1f3c0dba33cffc37e0ed9d9d406291e718343  src/catalog/services/business_team.py
ff23914a026154fa1bbda9678cd1c7a48015d07917e504f3ea8bd71ccff010cc  src/catalog/controllers/organization_workspace.py
```

## Дополнительная сверка root runtime: immediate tariff projection и отказ

Root сообщил свежие synthetic UI наблюдения на stand8792, Place158: name_ru/address gated, schedule_mode by_appointment и tariff15→18 immediate; после save_draft→submit reviewer `/admin/volunteer/review/158/` показывает конфликт, только отказ. Это runtime evidence root, не отдельный прогон support.

**Причина для проверки scalar diff:**

1. publication.snapshot включает PRICES price_from/price_to, независимо от наличия UI inputs (publication.py:19,24-27,35-63). save_form строит полный snapshot candidate (publication_forms.py:46).
2. Immediate pricing_plans применяет _apply→replace_place_pricing_plans (publication.py:283-285); replacement синхронизирует scalar projections (pricing_plans.py:349-350,603-627), например15→18.
3. propose обновляет live после _apply (publication.py:355), но base обновляет **только immediate keys** (356), обычно pricing_plans/schedule_mode. Derived price_from/price_to не входили changed до apply и поэтому их base может остаться15.
4. Следующий полный snapshot формы уже содержит scalar18; incoming18 попадает в pending против старого base15 (357). Changed_fields теперь содержит price_from/price_to, хотя это projection собственного explicit save.
5. revision_base_matches требует live==base для changed_fields (volunteer_places.py:61-67) и запрещает approval. publication.review имеет такое же условие (publication.py:382-383). Это объясняет видимый false conflict без конкурирующего редактора. Для окончательной привязки root должен вывести только synthetic conflicting field names + base/live/payload values.

Рекомендация отдельного scoped fix: в publication pipeline синхронизировать base/pending с серверными projections, возникшими в том же immediate apply, сохранив защиту от настоящего stale editor. Не обходить conflict gate. Regression: published exact tariff15→18 + gated name/address, save_draft→save_and_publish→approve; старый текст до approval, новая сумма сразу, approved тексты после; stale second tab по-прежнему rejected. Цена из unrelated чужой/устаревшей записи не должна скрываться как projection.

**Причина отсутствующей причины отказа в owner editor:** views.py:1384-1387 передаёт place_revision; publication.review:408 сохраняет note в revision.review_note. `src/catalog/templates/pages/includes/owner_place_continuous.html:7` рендерит lifecycle rejected/needs_changes, но весь template не выводит review_note/rejection_reason; `owner_place_edit.html` только наследует permanent_place_form. Следовательно retained refusal note не доступен в редакторе. `owner_places.html:401-406` использует Place.rejection_reason для другого lifecycle и не заменяет revision.review_note.

Рекомендация отдельного UI scoped fix: показать сохранённый revision.review_note в editor rejected/declined рядом с состоянием и действиями; RU/AZ/EN, безопасный escaped текст, public content не меняется. Runtime check: refusal с уникальной synthetic причиной→owner editor→reload→logout/login→причина видима, исправление→resubmit, reviewer latest reason/history не теряются.

Final IDs/severity и screenshots назначает root в основном отчёте. Support app/DB не менял, тесты не запускал.

## Независимая сверка final evidence и severity

Повторно прочитаны `.tmp/place-acceptance-20261009-8792/matrix.json` и `state-conflict.json` без DB/app writes. Matrix:198 rows,195PASS/3FAIL. Три FAIL — одна проблема `/admin/catalog/place/160/change/`, category dropdown open, RU/AZ/EN360:scrollWidth373. Source причина — custom taxonomy picker, **не Select2**: `static/admin/css/pages/kidsmap_place_form.css:1104-1110` absolute left0,width100%,min-width320px,max-width520px. `static/admin/js/kidsmap_place_form.js:1153-1155,1285-1311` создаёт dropdown внутри формы, открывает и фокусирует без viewport clamp. При content inset53px fixed minimum320px даёт правую границу373px, согласуется с наблюдением. Исправляющий scope: custom picker responsive width/position, длинные option names/search, category/subcategory, keyboard/open/close; не маскировать overflow clipping всей страницы.

Owner unavailable map source подтверждён: `static/js/owner_place_map_picker.js:474-480` ставит initialized и unavailable сообщение, отключает только searchBtn. Clear handler подключён лишь в Leaflet/Google init (319/435), locate также внутри этих init через общий helper. `src/catalog/templates/pages/includes/owner_place_map_picker.html:43-44` рендерит active locate/clear. Поэтому при provider=unavailable clear/locate активны без action. Scope: общий independent clear/manual координат, truthful state locate в unavailable/noSDK/GPS-denied, повторная и поздняя SDK инициализация; no external integrations для regression.

state-conflict.json независимо подтверждает base price_from/to15.00 и payload18.00 для revision pending version7. Scalar live18 в этом artifact не выведен, его подтверждение относится к root readback, а не к независимому чтению support. Причина baseline/projection в разделе выше согласуется со свежим evidence.

Рекомендуемая severity всех четырёх findings **P2**:

| Finding | Impact / граница |
|---|---|
| False conflict после immediate tariff projection | Блокирует normal approval собственного обновления без конкурентной вкладки; old public version и candidate сохранены |
| Причина отказа не показана в owner editor | Владелец не может понять требуемое исправление из формы; note не потерян в DB |
| Owner map unavailable active no-op clear/locate | Обещанная функция не выполняется при отсутствие provider; ручные координаты и сохранение доступны |
| Admin custom category dropdown360 overflow | Основной taxonomy control выходит за viewport RU/AZ/EN; 13px, mobile360 scope, page-wide full sign-off не выдаётся |

P1 не обоснован: не показаны потеря данных, публикация unapproved content, захват прав или полный отказ всех вариантов. Full UI sign-off не следует из195matrix PASS либо226targeted server PASS (server count сообщён root, support сам tests не запускал). Root присваивает PLACE-QA IDs/URLs/steps/screenshots и финальные самостоятельные prompts.

Named handoff: kidsmap-orchestrator/root — основной `docs/qa/place-acceptance-2026-10-09-8792.md`. Scope audit завершён по проверенным evidence, приложение не изменено.

## Пятый подтверждённый дефект: keyboard focus перекрыт sticky footer

Независимо прочитан root `focus-probe.json`. Owner768×950: после Tab с name_az activeElement=description_az; rect top882.59375/bottom952.59375,height70. elementFromPoint(384,912.59375) возвращает `footer.pc-actions`, uncovered=false. Контроль owner390 PASS, moderator768 PASS; не расширять finding на все ширины. Screenshot: `docs/qa/place-acceptance-2026-10-09-8792/screenshots/owner-focus-probe-768.png` (наличие файла проверено, visual capture выполнен root).

Source: `static/css/pages/owner_place_continuous.css:13` устанавливает `.pc-actions{position:sticky;bottom:0;z-index:7}`; line14 scroll-margin-bottom110px, line21 на <=900px верхний scroll-margin230px. `src/catalog/templates/pages/includes/owner_place_continuous.html:39` выводит footer внутри .pc-content. `static/js/owner_place_continuous.js:177-181` центрирует поле только через явный goTo (section/error navigation); line254 обработчик обычного keydown лишь отмечает userInteracted, не обеспечивает видимость focused field. Focusin unobscured handler в этом owner controller отсутствует. Поэтому native Tab scroll может оставить textarea под sticky footer; CSS scroll-margin alone не доказал достаточной защиты — свежий geometry probe показывает перекрытие.

Severity **P2**: клавиатурное заполнение основного поля описания на tablet768 затруднено, пользователь фокусирует скрытый control. Данных не потеряно, нарушения прав нет; P1 не обоснован. Scope frontend owner long-form keyboard/sticky/layout, без backend/publication/DB изменений. Отдельный finding от admin category360 overflow.

Самостоятельный prompt: «Исправь только перекрытие клавиатурного фокуса в continuous owner Place form. После Tab/ShiftTab focused control должен оставаться внутри реально свободной области между sticky header/savebar и bottom actions, в том числе768×950. Учти динамическую высоту footer, длинные RU/AZ/EN подписи, textarea, открытые details и reduced-motion; избежать скачков при вводе/потери фокуса, не заменять native Tab order. Не менять бизнес-правила, autosave/CAS или public card. Fresh rendered regression: owner RU/AZ/EN×360/390/768/1024/1280/1440, forward/back Tab, section/error navigation; bounding rect и elementFromPoint подтверждают видимость focused control. Приложи tablet screenshot до/после и isolated existing form checks.»

Support source audit/report only; application не редактировал. Named handoff root: включить пятый PLACE-QA P2 с указанными raw evidence и источниками, сохранив195/3 основную геометрическую матрицу и отдельную focus-probe строку.

## Шестой кандидат P2: admin mobile section-navigation

Source mechanism подтверждён. Fresh root nav-probe.json independently3FAIL:360 top-716.859375,height2547.75;390 top-684.234375,height2482.953125;768 top-323,height≈1998. focus-final.json108 rows9FAIL — moderator RU/AZ/EN×360/390/768 section navigation. Probe использует change section picker; root дополнительно проверяет native Select2 option click, чтобы исключить harness-only path. До получения native результата источник и probe подтверждены, окончательный runtime статус отдельной native проверки PENDING.

`static/admin/js/kidsmap_place_form.js:76-77` change `[data-pf-section-select]` вызывает focusTarget('#'+value). focusTarget:268-274 разрешает **весь section**, а не heading/первое поле;290-293 scrollIntoView(block:center) центрирует section высотой значительно больше viewport. Начало location с heading/region оказывается выше окна.299-301 пытается focus на section с preventScroll:true; `src/catalog/templates/admin/catalog/place/form/_section_open.html:6-12` section без tabindex, поэтому фокус не переносится. Desktop `[data-pf-nav-for]` использует другой handler155-178 и scrollTo, его нельзя объявлять неисправным по mobile case.

Реальное последствие: пользователь выбирает «Локация», но попадает в середину длинной секции, не видит heading/город/район, клавиатурный фокус остаётся body. Это дефект ориентации и navigation, самостоятельный от textarea sticky overlap и category dropdown width. Рекомендуемый P2 при подтверждённом native выборе; нет доказанного DB/data-loss impact.

Самостоятельный repair prompt: «Исправь только mobile section picker административного постоянного Place. При native выборе раздела в RU/AZ/EN на360/390/768 показывай начало раздела ниже sticky bars и переносись на семантически подходящий focusable heading/control. Не центрируй большой section целиком; сохраняй open state/scrollspy/Select2 keyboard behavior и desktop navigation. Проверить native click и keyboard option select, forward Tab, collapsed/expanded long location/media sections, reduced-motion и все widths. Ожидание: heading и первое соответствующее поле доступны в viewport, focus не body, нет ухода в середину section; приложение/модерация/DB contracts неизменны.»

Support ничего не исправлял. Handoff root: подтвердить native путь и обновить sixth finding статус с его evidence.

### Sixth native UI verification supersedes PENDING

Root затем выполнил настоящий click видимого Select2 option «Локация». Independently read nav-ui.json:3/3FAIL360/390/768, scrollY0, selector вновь basics, location top5880/5587/3325, active Select2 combobox. Следовательно основное поведение — **видимый mobile picker не выполняет navigation**, а неправильное центрирование из предыдущего probe — вторичная проблема того же компонента.

Source integration цепочка: `static/admin/js/kidsmap_place_form.js:16-22` ready на DOMContentLoaded; helper on:29 использует native addEventListener; selector:76-77 подписан только на native change. Установленный и используемый Jazzmin `.venv/lib/python3.12/site-packages/jazzmin/static/jazzmin/js/change_form.js:113-117` applySelect2 оборачивает все select, кроме явно listed исключений; mobile section selector из `src/catalog/templates/admin/catalog/place/change_form.html:95` не входит в исключения. Jazzmin вызов applySelect2:137 внутри jQuery document.ready:120. Actual installed Select2 `.../jazzmin/static/vendor/select2/js/select2.min.js:1` selection adapter вызывает `$element.val(...).trigger("input").trigger("change")` — jQuery synthetic события, а owner local native listener не получает этот маршрут.

Возврат focus на combo вызывает root focusin → markCurrentSection (`kidsmap_place_form.js:246-248`) → sectionSelect.value=current.id:229. Без navigation текущий раздел basics, что согласуется с raw scrollY0/resetbasics. Это не проблема текста option и не отсутствующая секция.

Статус sixth **CONFIRMED P2**. Scoped repair prompt уточнение: корректно согласовать native/Select2 change и scrollspy, исключить двойное срабатывание, показать начало section с правильным focus; проверить actual visible UI pointer+keyboard и native fallback. Не полагаться на программное selectOption как доказательство Select2 path. Ни application, ни third-party dependencies support не изменял.

## Седьмой подтверждённый P2: часы Place названы расписанием занятий

Root native branch159 approval прошёл; отдельные сохранённые values Place будни09–18 и OfferingGroup суббота14–15 сохранены/публичны. Independently read branch-public-languages.json:3public-language PASS,3semantic-label FAIL. RU public #schedule показывает «Расписание занятий» над09:00–18:00; AZ «Dərs cədvəli», EN «Class schedule». Это реальные открытые public translations, не source-only гипотеза.

Причина: `src/catalog/services/pricing_plans.py:1157` классифицирует ownership расписания по category whitelist PARK/BEACH/FUN/CAMP/WATERPARK/ZOO. Для ART/EDU regular вместо schedule_working_hours выбирает schedule_label:1161-1164. Localized schedule_label:860/892/924 — текст о занятиях. Между тем rows/week/open_status:1166-1168 строятся всегда из Place; `src/catalog/services/place_schedule.py:587-590` читает Place.schedule_days, не OfferingGroup.schedule_text. `src/catalog/templates/catalog/place_detail.html:420-435` отображает эту неверную badge над Place-week. У занятий отдельно корректное поле (`public_presentation.py:141`; `templates/catalog/includes/public_offerings.html:10`).

Severity **P2**, semantic contract error: родитель может принять время открытия места09–18 за время занятий, хотя группа только суббота14–15. Ошибка на трёх языках, затрагивает центральную информацию planning посещения; данные/время не потеряны. P1 отсутствует. Это самостоятельный дефект public presentation, не смешивание persisted schedule relations.

Самостоятельный prompt: «Исправь только семантическую подпись регулярных часов постоянного Place на публичной карточке. Place.schedule_days всегда означает часы работы места, включая ART/EDU; расписание OfferingGroup остаётся расписанием занятий. Убери вывод типа по whitelist категории, сохрани корректные подписи nonregular/by-appointment/events и существующие localized тексты, цены и hours значения. Не перемещай/копируй расписания, не меняй readiness/moderation/schema. Regression: ART/EDU и PARK с Place будни09–18 + группа суббота14–15; RU/AZ/EN public badge явно говорит о часах работы, группа о занятиях, оба values прежние; без группы, free/event price modes, nonregular hours сохраняются. Проверка public SSR/screenshots и targeted presentation suites.»

Support только дополнил свой отчёт; root назначает PLACE-QA ID, publicURL и screenshots, общий module sign-off по отдельным PASS не выдаётся.
