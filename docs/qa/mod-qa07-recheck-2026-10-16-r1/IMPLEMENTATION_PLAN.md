# MOD-QA-07 — понятная сводка ошибок специалиста и переход к полю

**PLAN COMPLETE / CONFIRMED OPEN. Application changes:0. Новый scope требует отдельного approval пользователя.**

Goal: после серверного отклонения Save показывать по одному сообщению на настоящую ошибку и переводить keyboard focus к соответствующему полю/первому доступному чекбоксу группы. Валидация, отклонение, stale guard и права сохраняются.

Architecture: только specialist template и его существующий error-link listener; backend model/admin/form/business rules не меняются. В outer loop `field` — AdminField; `field.errors()` возвращает HTML string, а `field.field.errors` — ErrorList underlying BoundField. Inline loop уже использует BoundField, его не переписывать по аналогии. CheckboxSelectMultiple имеет group auto_id при пустом id_for_label; error link нужен group ID, а JS — доступный control внутри него.

## Подтверждённые ID/причина

Только **MOD-QA-07**. Native RU/AZ/EN×390/1440,6cells/36observations: **12source FAIL /24controls PASS**. В каждойcell одна inline required error порождает много summarylinks, `href="#"`, Enter оставляет focus на A. RU:84links; остальные фактическиеcounts в rawJSON. Все6actual Save подтверждены native confirm и получили server invalid response. Rejected/reason/emptyselection сохраняются во вводе, truthful unsaved status есть, persisted Specialist/M2M/locations/documents fingerprint unchanged.

[RU](native-ru.js.result.json), [AZ](native-az.js.result.json), [EN](native-en.js.result.json), [PNG manifest](png-manifest.json). Это current source/baseline, не harness/freshMO проблема. Текущая документация и installed Django6.0.2 source подтверждают типы, но факт установлен настоящим browser, а не docs. Новых ID кроме MOD07 не заведено.

## Точные файлы:3

1. **`src/catalog/templates/admin/catalog/specialist/change_form.html`**, только главный summary loop, текущая строка13:
   - `for error in field.errors` → `for error in field.field.errors`;
   - href `field.field.id_for_label` → `field.field.id_for_label|default:field.field.auto_id`.
   - Отдельный inline loop, inline `.errorlist`, non_field_errors, escaping, validation/status/private sections не менять.
2. **`static/admin/js/specialist_admin.js`**, только `[data-specialist-errors] a` click listener, текущая строка9:
   - найти target по hash, открыть enclosingdetails как сейчас;
   - если target — container группы, выбрать первый enabled visible input/select/textarea/button внутри; перейти и focus на него;
   - если доступных controls нет, сделать сам существующий target focusable `tabindex=-1` и focus его, без новой keyboard tabstop;
   - ordinary input и навигацию разделов/поиск специализаций/photo/status listeners сохранить. Общий `go()` и общие admin scripts не переписывать.
3. **NEW `src/catalog/testcases/test_mod07_specialist_error_summary.py`**:
   - actual authenticated admin changeform POST без специализаций: server required error остаётся, ровно1summarylink с целым локализованным message и `#id_specializations`, snapshot Specialist/M2M unchanged;
   - несколько ошибок (`name`+specializations): ровно2целых сообщения и correct targets, postedreason/status retained;
   - invalid inline value (например practice_locations price) с заполненными основными полями: inline message целиком/validtarget, никаких HTML chars по буквам; no partial parent/inline save;
   - RU/AZ/EN через properprefix/cookie; ErrorList messages, nonfield и escaped text проверять через actual response, не source-textassert. Existing tests/assertions не менять.

[Готовый двухфайловый diff](proposed.diff), [source/candidate hashes](proposal-manifest.json). Candidate только в `candidate/`, не подключён к runtime. Третий файл — новый test с перечисленным контрактом, без изменения production/backend контрактов. PO/MO source/CSS/schema/config/endpoints/dependencies вне scope.

## Реализация после approval

- Проверить entry HEAD/branch/dirty/active_run, app sourcehash, actual PID/source и принадлежность своего QA профиля. При drift отразить его; новая причина/расширение отдельно, тот же approvedscope не переспрашивать.
- Использовать собственную изолированную DB/cache/media/private-media/email, fictional data, DJANGO_TESTING=1, backend egress только ownPG/browser ownorigin. Новый fixrun. Текущий ownPG server/ownPLAN DB разрешены к reuse только после ownership/isolation/source verification; не трогать чужие процессы и DB. Вся первая проверка выполнялась в новой собственной `mod07_plan_r1`, старые fixtureDB не использовались для POST.
- Написать3новых regression methods, получить meaningful RED на actual server responses до productionpatch. Повторить browser только конкретный failing subset (oneerror+focus), не весь старый модуль03/08.
- Применить только согласованные2productionfiles. Сохранить прежний source, actualdiff и hashes.
- Собрать текущие RU/AZ/EN PO через scripts/build_isolated_locales.py в fresh ownpath, verify manifest **до django.setup**, единственный LOCALE_PATHS; sharedMO не перезаписывать. Проверить actual opened projectMO/template/module/source текущего процесса.
- Targeted backend GREEN: новая группа; representative shared subset существующих `SpecialistEntryAdminTests.test_stale_admin_form_rejects_parent_and_location_overwrite` и `test_plain_editor_has_no_private_document_inline_or_count`. Это guards неизменной валидации/приватности, не повтор полной module03 acceptance. Изменять assertions для GREEN запрещено.
- Actual native UI: single required error RU/AZ/EN×360/390/768/1024/1280/1440 (18targetedcells): снять все специализации, выбрать rejected/длинную причину, Save→nativeconfirm→servererror. Проверить ровно1читаемую ссылку, inline error, unsavedstatus, postedinput retained, Enter наsummary→visiblecheckboxfocus/hit, reachablecontrols/безviewportoverflow. 18cells относятся только к этой ошибке, не к полному модулю.
- Representative additional cases RU/AZ/EN×390/1440: multipleerrors+invalidinline, long reason/escaped fictionaltext; ordinaryinputlink, noHTMLinjection, empty/invisiblegroup fallback явно SIMULATED если потребуется. Если inline productioncause отдельно подтвердится и понадобится дополнительный файл — не включать молча, отдельныйscopeapproval. Без ошибок/безspecialistform listener не ломает другие страницы; representative normalGET/reload достаточно.
- Все PLAN/targetedinvalidPOST должны оставлять persisted parent/M2M/locations/documents unchanged, username/session/lang изменения отделять. Реальный успешный save не нужен для исправления сводки; если для acceptance потребуется, только отдельная ownfixture и точный diff, без чужихданных.
- Console/network/PNGmanifest, commands/exits/counts, before/after source/locale/domain, preservation. Закрыть MOD07 только поGREEN. Не повторять MOD01–06 suites; полный module08 один раз после08, global отдельно. MOD08 отдельныйplan, module09 не начинать. Без commit/push/deploy/production.

## Риски, роли и границы

Основной риск — перепутать AdminField и BoundField и оставить пустой target у checkboxgroup; regression фиксирует оба контракта. Listener меняется только для errorlinks, чтобы sectionnavigation не получила побочный focus. Fallbackcontainer безcontrols остаётся доступной точкой с programmaticfocus. Валидация required/atomic/stale/privateACL остаётся серверной. Owner: frontend-admin + Django, область module03; lead выполняет роли последовательно, independent review не заявляется.

Свежий graph project `home-ramin-kidsmap` rootverified; relevant template/adminfile metadata_match/no_recorded_issue, generation2026-10-16T06:57:54Z. Для динамического template/AdminField source прочитан напрямую; graph completeness не доказана, cache вrepo не сохранялся. Угаданного `kidsmap_admin_changeform.js` нет; фактический script определён из template — `specialist_admin.js`.

**NOT RUN доapproval:** application patch/newbackendRED/postpatchGREEN, multiple/inline dynamiccases, full18cellpostpatch, full08/global/production. Исторические MOD07 evidence сохранены; текущий report не превращает старуюmodule03приёмку в полный новыйPASS.
