# MOD-QA-04 — CLOSED LOCAL / scoped LOCAL PASS

2026-10-16, `/root`, canonical kidsmap-orchestrator; frontend-admin/browser-qa/integration-reviewer выполнены последовательно основным исполнителем, независимых агентов не было. Definitions `.agents/agents/<role>/agent.md`. [Approval](APPROVAL.md): пользовательское «обобряю» одобряет показанный four-file PLAN. Применены TDD/debug/verification/KidsMap UI/accessibility skills.

## 1. Состояние и snapshot

`/home/ramin/kidsmap`, `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` +dirty WORKTREE, `active_run: NONE`. [Entry](entry.json), [current runtime/source](runtime-source-final.json), [verification](verification.json). Own current HTTP PID70775 loopback34827. Own previously created/verified fictional PostgreSQL на47955/database mod03_columns_fix_r1 повторно использован без reseed/migrate; новый HTTP/cache/media/private-media/email/locale root и отдельный test_mod04_escape_fix_r1. [Profile ownership/isolation](profile-reuse.json), [runtime info](runtime-info.json). Source958MATCH; HEAD не включает dirty fixes; production NOT RUN.

## 2. Исправление и сильные стороны

В исходном состоянии Escape не закрывал наружный sidebar; на360/390 opener был перекрыт. Добавлен локальный adapter, использующий обычный click существующего PushMenu opener. Mobile close-button внутри панели имеет RU/AZ/EN имя; Escape/close/backdrop возвращают фокус на видимый opener. Aria-controls/expanded синхронизируются с body state. На desktop Escape в контенте не сворачивает persistent sidebar. Existing accordion/search logic сохранены.

Только4согласованных files, [exact own diff](implementation.patch): static/admin/js/kidsmap_admin_sidebar.js; src/catalog/templates/admin/catalog/includes/sidebar_navigation.html; static/admin/css/pages/kidsmap_admin_sidebar.css; NEW src/catalog/testcases/test_admin_sidebar_escape.py. Header/vendor/PO/ACL/models/data contracts не менялись. Existing header CSS использует !important; scoped visibility/focus rules используют соответствующие overrides. Sidebar не объявлялся dialog; новый focus-trap/inert контракт не вводился.

## 3. Реальные проблемы и RED → GREEN

Fresh nativeRED:6original RU width/surface failures,14controlPASS, [JSON](native-red.js.result.json),6отдельных red-escape PNG. Предыдущий planning RED18 сохранён исторически, повторно все18до patch не запускались. New2methods RED:9assertionFAIL/0ERROR, [вывод](tests-red.txt).

Текущий код закрывает original Escape trigger во всех18RU/AZ/EN×360/390/768×dashboard/Place cells; возврат на правильный видимый keyboard opener и aria=false подтверждены. MOD04 CLOSED LOCAL. Следующий [MOD05 read-only recheck](../mod-qa05-recheck-2026-10-16-r1/REPORT.md) подтвердил только оставшийся return-focus дефект; его patch не разрешён и не применён.

## 4. Tech debt и ограничения контракта

Existing body classes остаются источником состояния; код не меняет их вручную. На persistent desktop dismiss ограничен фокусом в sidebar/opener; nested prevented Escape имеет приоритет. На mobile navigation остаётся обычной sidebar-навигацией, полная modal isolation/trap не заявляется. Existing unrelated translations/navigation labels не переписывались.

## 5. Риски и scope preservation

Глобальный sidebar используется несколькими staff поверхностями. Проверены normal toggle, input/row-menu Escape, accordion persistence, restricted reader; modal engine/publication/save/backend не менялись. Scope source preservation:954из957предыдущих source hashes неизменны,3approved paths изменены и новыйtest добавлен. [Retention](retained-evidence.json). Это не новая полная приёмка прежних таблиц/поиска/колонок.

## 6. Legacy/dead candidates

Удалений/cleanup/refactor нет; old accordion/storage/search-clear functions сохранены. Старые reports/raw FAIL/PNG не перезаписывались. New close использует existing перевод «Закрыть» и kmi-close, без новых PO/icons.

## 7. Только целевые проверки

[Commands/exits](commands.jsonl), [semantic gate](final_gate.py), [PNG manifest](png-manifest.json).

- **4unique backend methods accepted**:2new GREEN в [tests-green-targeted.txt](tests-green-targeted.txt),2existing shared methods PASS retained из первого4-method запуска. После fixture correction повторены только2affected methods. Первый output [tests-green.txt](tests-green.txt) сохраняет3AZsubtestFAIL: custom AdminLocaleMiddleware по умолчанию используетRU для unprefixed /admin/ без выбранной cookie. В новом test fixture явно задаётся выбранный язык и дополнительно проверяется actual LANGUAGE_CODE; все expected labels/ACL assertions сохранены. [Correction](test-fixture-correction.md). Shared assertions/files не менялись.
- **168accepted main browser PASS**:18primary cells, native Enter/Space/Escape/Tab/ShiftTab, close/button/backdrop, logo hit/geometry, visible focus, aria state, reload/reopen; языки переключались actual menu POST. RU initial50PASS/6immediate readinessFAIL сохранён в native-ru-first.json. Фокус возвращается на requestAnimationFrame; [supplement6PASS](native-focus-supplement.js.result.json) перепроверил только6failed observations с ожиданием active+aria+hit≤1500ms, остальные50не повторялись. [Readiness note](focus-readiness-correction.md). Stuck focus остаётся FAIL; приложение ради этих измерений не менялось.
- **23actual native shared PASS +1explicit SIMULATED guard** в [edges](native-edges.js.result.json): RU1024/AZ1280/EN1440 persistent input Escape/normal toggle/row-menu Escape, accordion Enter/Space/reload, AZ390 ограниченный reader и privacy links. Только один temporary preventDefault listener — SIMULATED, отдельно от настоящих flows.
- Всего **191actual native PASS +1SIMULATED =192accepted checks**,0local console/page/network/HTTP errors. External resources/fonts blocked; внешние интеграции не проверялись.
- **40PNG**, hashes/format/dimensions verified. RED6 и GREEN34 раздельны; AZ390 open sidebar screenshot просмотрен визуально, не заявляется просмотр всех40PNG.
- Before/after full-field fingerprint Place/Event/Specialist (4/3/3fictionalrows) совпал: [before](domain-before.json)/[final](domain-final.json). Это не hash всех таблиц auth/session. Ни одного confirm/save/publication data action эта задача не выполняла.

## 8. Изоляция, сохранность и следующий шаг

DJANGO_TESTING=1, очищенный env, checkout.env/production credentials не загружались; own egress socket только verifiedPG, browser только ownloopback. Unique owncache/media/private-media/file-email; own dependency copies verified, без сетевой установки.

Текущие RU/AZ/EN PO собраны build_isolated_locales.py в новый `.tmp/mod-qa04-fix-2026-10-16-r1/locales`, manifest проверен доsetup и повторно в final gate; единственный собственный LOCALE_PATHS, все3ownMO открыты. Shared MO не перезаписывались. [Manifest](locale-manifest.json).

Entry32898 files: 32894неизменённых, 4допустимых changed existing paths,0missing; новыйtest/ownQAдобавлены. Only3approved existing app paths +appended guide note; [preservation](preservation.json). Все74entry container ID/state/ports и один entry HTTP30142 argv/cwd сохраняются. Состояние этих стендов проверено в текущем run; прежние ограничения continuity из прошлого columns run не отменяются. HEAD/branch/active_run прежние; no reset/clean/stash/foreign restart. Свой новый HTTP перезапускался только для загрузки собственного patch.

Следующий конкретный scope — [MOD05 one-file/one-line PLAN](../mod-qa05-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), approval pending. New-cause patch автоматически не применялся.

## 9. Приоритеты и NOT RUN

MOD-QA-04 P2 CLOSED LOCAL. MOD-QA-05 P2 CONFIRMED OPEN; initial/trap историческая причина уже исправлена, остаётся return-focus. Full module08, MOD06–08, all-modules/global, production/commit/push/deploy, physical devices/non-Chromium NOT RUN. Полный модуль08 — один раз после всех его задач, module09 не начинался.
