# MOD-QA-08 — фильтры мероприятий и специалистов

**CONFIRMED OPEN / PLAN COMPLETE. Приложение не изменено.** Новый scope требует отдельного одобрения пользователя. Одобрения MOD01–07 его не покрывают.

Цель: показывать применимые фильтры текущей очереди, использовать уже принятые сервером query strings и сохранять поиск, сортировку, выбранные значения, chips, counts и Reset/Apply. Бизнес-фильтрацию и права не менять.

## Свежий факт и причина

RU/AZ/EN × Event/Specialist ×390/1440:12native cells. У Event видна только категория; отсутствуют status/start_datetime/owner. У Specialist нет select, хотя сервер предоставляет status/is_active/consultation_format/specializations. Это12source FAIL;30контрольных наблюдений PASS, включая клавиатурное открытие панели, counts, действующий category selection→Apply→Reset и неизменность данных. [Raw RU](native-ru-first.json), [AZ](native-az.js.result.json), [EN](native-en.js.result.json), [один исправленный QA-count контроль](native-category-correction.js.result.json).

Общий шаблон проверяет whitelist мест и не использует km_primary_filters Event/Specialist. Серверные filter_specs содержат нужные поля и валидные choices/query strings. [Event contract](contract-event.json), [Specialist contract](contract-specialist.json). При разных категориях Event панель уже не полностью пустая — историческую формулировку уточняем по нынешнему воспроизведению.

Счётчик одного контрольного сценария первоначально получил3вместо2 из-за QA endpoint под публичным путём: middleware правильно очищал его query. Временный read-only helper перенесён в собственный /api/qa/...; только этот контроль повторён с теми же assertions и стал PASS. Приложение/middleware не менялись. Это QA-причина, не дополнительный application finding.

## Точный scope:3файла

1. **`src/catalog/templatetags/admin_dashboard_tags.py`**:
   - Новый simple_tag `km_drawer_filters(cl)` получает группы только из actual `cl.filter_specs`, включая стандартные FieldListFilter и SimpleListFilter с field_path/parameter_name. Список/права/choices определяет текущий ModelAdmin.
   - Для Event/Specialist порядок задаёт существующий `km_primary_filters`, остальные доступные поля следуют за ними. Служебные sort и deleted_at__isnull не дублировать в drawer: сортировка и корзина уже имеют свои controls.
   - Для Place и прочих очередей сохранить прежний whitelist/quality layout. Не выводить все произвольные поля модели.
   - Передавать title/field/готовые choices с server query_string. Никакого нового ORM queryset, ручных lookup values или бизнес-фильтрации.
   - В existing `get_active_filter_chips` разрешить status-chip только для Event/Specialist. Для Place прежние исключения сохраняются; снятие chip использует server all-choice URL и сохраняет прочие параметры.
2. **`src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html`**:
   - Использовать новый normalized drawer group list вместо place-only проверки. Существующие data-filter-select/data-field и server query_string остаются.
   - Связать labels с select через уникальные IDs; существующие CSS-классы сохранить.
   - У Event/Specialist скрыть пустой блок «Качество данных» и фразу «Вкладки — единственный фильтр по статусу», когда status доступен и в панели. У Place прежние блоки остаются.
   - Сохранить search hidden params, counts, кнопки Apply/Reset, quick tabs, sorting и column controls.
3. **NEW `src/catalog/testcases/test_mod08_filter_drawer.py`**:
   - Actual authenticated changelist response: Event/Specialist получают4ожидаемых поля и порядок primary config, localized labels/options/selected state в RU/AZ/EN. Служебные навигационные параметры не становятся select.
   - Следовать выбранным URL из настоящего rendered select: сочетания category/date/status/owner и format/status/direction, q+sort; сравнивать ожидаемые fictional IDs/counts, включая пустой результат. Assertions на поведение, не на наличие строки в source.
   - Selected status/other-filter chips: корректное снятие одного фильтра сохраняет остальные; Reset возвращает full fictional queue и прежний reset-контракт.
   - Place: прежние поля/options/quality controls сохраняются; его status-chip поведение не меняется.
   - Existing assertions не изменять. Новая группа сначала RED на нынешнем приложении, затем GREEN.

[Двухфайловый candidate diff](proposed.diff), [SHA256 и applied:false](proposal-manifest.json). Третий файл — только перечисленная новая тестовая группа. Candidate хранится в QA bundle и не подключён к приложению.

**JS/CSS/PO/ModelAdmin/list_filter/schema/permissions вне scope.** Существующий переход по choice.query_string при изменении select и действия Apply/Reset сохраняются; их настоящий UI-контроль проверен до patch и будет проверен после. Для нового deferred/batch Apply или иной причины нужен отдельный план, если она фактически обнаружится.

## Реализация после approval

- Проверить root/HEAD/branch/dirty/active_run, source hashes и ownership/isolation/runtime. Новый fix-run, DJANGO_TESTING=1, собственные DB/testDB/cache/media/private-media/email и fictional data. Известный own PG/DB можно повторно использовать только после проверки. Не загружать checkout.env/production credentials, внешние обращения blocked либо явно SIMULATED. Старые отсутствующие HTTP не перезапускать.
- Сохранить исходники и новую regression группу; выполнить только её meaningful RED и один failing browser subset до patch. Не повторять неизменённые suites MOD01–07.
- Применить только3перечисленных файла, сверив candidate hashes и scope. Общая причина принадлежит frontend-admin/Django; lead работает последовательно, независимый агент не заявляется.
- Собрать текущие RU/AZ/EN PO через scripts/build_isolated_locales.py в новый own каталог, verify manifest **до django.setup**, единственный LOCALE_PATHS; shared MO не менять. Проверить actual opened project MO и source/template/module origins работающего процесса.
- Targeted backend GREEN: новая группа. Representative shared — existing `AdminQueueSearchStateTests.test_repeated_supported_status_filter_values_survive_the_form` и `test_search_does_not_expand_permissions_or_mutate_domain_records`. Только эти guards, не вся search/sort/columns библиотека.
- **Actual rendered native GREEN** RU/AZ/EN × Event/Specialist ×360/390/768/1024/1280/1440:36targeted cells. Keyboard open, native select→существующая навигация→Apply→reload→Reset; правильные выбранные значения/labels/IDs/counts/chips, zero-results, доступность labels, без обрезанных controls/overflow. Сочетания проверять так, чтобы второй фильтр сохранял первый, q и sort; дата может менять несколько query parameters одновременно.
- Representative Place/shared scenarios только390/1440: его старые фильтры/quality/search/sort не ломаются; removing one chip сохраняет другие условия. Роль с доступом только к Specialist не получает Event доступ. Use GET-only flows и исключить domain mutations; до/после snapshot parent/M2M/locations/documents/Place/Event должен совпасть.
- Сохранить console/network, PNG manifest, exactcommands/exits/counts, source/locale/live readback, preservation и NOT RUN. На новом расхождении assertions не ослаблять и не добавлять молча новые файлы.
- Закрыть только MOD08 по фактическому GREEN. После завершения последней задачи выполнить **полный ACCEPT-08 один раз** по guide; global acceptance отдельно. Module09 автоматически не начинать. Без commit/push/deploy/production.

## Риски и ограничения

Общий renderer затрагивает Place, поэтому его legacy branch сохраняется и проверяется целевым guard. Choices остаются opaque server URLs: это поддерживает boolean/null/date/multi-parameter filters без ручной JS-пересборки и сохраняет backend validation/ACL. Удаление chip использует существующий all-choice URL, а не общий reset. Переводы берутся из действующих field titles/choices; новых PO-ключей нет.

Graph-first: actual project `home-ramin-kidsmap`, root verified, initial generation2026-10-16T07:47:10Z; дополнительные tag/test paths проверены generation2026-10-16T08:20:58Z; relevant template/admin/JS metadata_match, no recorded issue. Динамические связи filter_specs/ModelAdmin/choices проверены непосредственно source и runtime. Graph не доказательство полноты и не сохранялся в repo. Candidate Python/JS backend контракты не проверены postpatch, потому что approval пока отсутствует.

**NOT RUN:** application patch/newbackend RED/GREEN, postpatch36cells, candidate browser, full08/global/production. Четыре entry HTTP исчезли при прерывании подготовки; continuity NOT VERIFIED, чужого restart не было. Восстановлен только own PG с тем же ID и новая own DB, затем собственный HTTP. Это ограничение среды не превращается в PASS.
