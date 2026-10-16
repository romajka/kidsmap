# KidsMap: продолжение на другом ПК и готовые промпты

> Git-перенос 2026-10-12: [статус и отчёт](git-transfer-2026-10-12-r1/REPORT.md), рабочая ветка `task33-progress`. Снимок и первоначальная авторизация ниже относятся к подготовке 2026-10-11; фактическое получение исправлений проверяй по текущему Git checkout.

Дата: 2026-10-11, Asia/Baku. Этот файл подготовлен для переноса через Git и последовательной работы в новых чатах. Сегодня разрешена подготовка документов; доступ к Git/серверу и отдельное поручение на push пользователь даст позже. Commit/push/deploy сейчас не выполняются. Сервер для локальной приёмки не требуется.

## Как пользоваться завтра

1. Синхронизируй подготовленную ветку вместе с исходниками исправлений, тестами, helper и QA-документами. Один этот Markdown не переносит dirty WORKTREE. До синхронизации нужен отдельный согласованный Git-пакет из раздела «Что должно попасть в Git».
2. В новом чате вставь целиком **START** ниже. Агент проверит полученный checkout и создаст свой изолированный стенд. Не запускай старые QA launcher с захардкоженными портами/путями без адаптации.
3. Выбери одну задачу из таблицы модулей и скопируй целиком её **PLAN**. Получи свежий recheck и сохранённый конкретный план. Можно согласовать небольшой связанный batch, если в плане перечислены все ID/файлы/acceptance; объём расширяется только явно.
4. Прочитай план и вставь **IMPLEMENT-APPROVAL** в тот же чат. Это явное разрешение на конкретный последний план. В новом чате укажи фактический путь согласованного плана и свои разрешённые ID. Одобрение этого же scope не надо повторять внутри выполнения.
5. После исправлений соответствующего модуля вставь его **ACCEPT**: это полная свежая приёмка AUDIT ONLY. Если аудит обнаружит новые findings, им нужны самостоятельные ID/план; автоматически остальные ошибки не исправляются.
6. Модуль01 прошёл LOCAL ACCEPT-01: [r6](module01-full-2026-10-12-r6/REPORT.md), QA09–14 закрыты в проверенном scope; QA01–08 scoped evidence сохранены. Native943PASS; Backend470PASS сохранены по неизменившимся исходникам. Следующий пользовательский шаг — отдельный PLAN модуля02. Модуль13 — финальная межмодульная приёмка после01–12.
7. После каждого запуска сохраняй уникальный новый отчёт, evidence, команды/exits, ограничения и handoff; обновляй только соответствующий текущий статус. Исторические отчёты сохраняются. Незавершённые проверки не превращаются в PASS.

Один модуль/согласованный scope — один рабочий чат. На одном checkout выполняй задачи последовательно. Этот файл содержит **73 PLAN** для оставшихся общих причин, **13 ACCEPT** и **2 служебных блока** START/IMPLEMENT-APPROVAL: всего **88 копируемых блоков**. Это библиотека заданий, не обязательные 88 отдельных чатов и не оценка количества дней. PLAN+одобрение+реализация+приёмка могут проходить в одном чате. Свежий recheck может уменьшить очередь.

## Что фактически завершено

На момент подготовки: `C:\kidsmap`, branch `task33-progress`, LOCAL HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE, `active_run: NONE`. Это исторический снимок: на другом ПК записывай свой фактический HEAD и хеши. Clean HEAD не включает локальные незакоммиченные исправления. Production не проверялся и не изменялся.

- PLACE-QA-01–07: свежий scoped recheck 2026-10-11, 38 Django +34 Node +9 locale-helper PASS. Browser 252 PASS/6 FAIL одной причины/12 scope NOT RUN, 164 native PNG. Шесть FAIL относились к PLACE-QA-08.
- PLACE-QA-08 = CROSS-QA-03: выполнен одобренный минимальный patch. В RU PO восстановлена active запись «Выберите район», добавлен regression test. Fresh isolated locales: 6 Django PASS, browser 87 PASS/0 FAIL observations, 24 native PNG. Этот ID и его alias — одна причина и одно исправление.
- Полная LOCAL module01 ACCEPT выполнена в [r6](module01-full-2026-10-12-r6/REPORT.md):943 native PASS,470 backend PASS по проверенному source match, JS52PASS/1SKIP и финальный7PASS subset. [QA14 accepted](place-qa14-close-fix-2026-10-12-r1/REPORT.md) устраняет старый close timer и initial-focus cause по одобренному [плану](../superpowers/plans/2026-10-12-place-qa14-close-race.md). [r5 OPEN](module01-full-2026-10-12-r5/REPORT.md) остаётся историей. Targeted после правки; полная module acceptance после всех его исправлений; global corpus после всех13. Исторический/LOCAL PASS не означает production PASS.
- PLACE-QA-06 отличай от других runtime: в свежем изолированном profile новые MO проверены; общие старые MO и чужие процессы не пересобирались. Missing/obsolete RU ключ PLACE-QA-08 одной сборкой прежнего PO не исправлялся.
- Module03 [LOCAL PASS](module03-full-2026-10-13-r1/REPORT.md),2026-10-13: SPEC-QA-01–04 CLOSED LOCAL;154 unique module tests accepted (146 initial PASS +8 approved targeted recheck, no unchanged full rerun); RU/AZ/EN×6widths, native lifecycle/claim/consent/privacy/CAS, rendered loading and local SVG arrows. Approved plans/source/runtime/preservation in final report. Historical module03 r1 FAIL retained; current acceptance has priority. Global/external/production NOT RUN. Next only module04 PLAN selected by user; automatically not started.
- Module04 [LOCAL PASS](module04-full-2026-10-13-r1/REPORT.md),2026-10-13: EVENT-QA-01–06 CLOSED LOCAL;143 unique method IDs accepted with explicit fixture-order supplement, no unchanged full reruns after patches; native primary clear/required photo gate, owner/admin CAS, drafts/moderation/public/cancel/reschedule, RU/AZ/EN×6widths and final Django-native gettext proof. [Verification](module04-full-2026-10-13-r1/verification.json). Shared PUBLIC/SITE locale group, bulk administration/global corpus/external/production remain outside this closure. Historical r1 evidence retained. Next module05 PLAN selected by user, automatically not started.
- Module05 LOCAL PASS — ACCEPT-05,2026-10-14: [new final REPORT](module05-full-2026-10-14-r2/REPORT.md), [verification](module05-full-2026-10-14-r2/verification.json). OFFER01–11 CLOSED LOCAL in recorded scope; [OFFER10](offer-qa10-fix-2026-10-14-r1/REPORT.md), [OFFER11/final source](offer-qa11-fix-2026-10-14-r1/REPORT.md), [505native/36cells/45PNG verification](offer-qa11-fix-2026-10-14-r1/verification.json).334unique backend methods PASS once;6affected projection methods repeated GREEN after exact foreign pure helper extraction, not340unique. Final15READONLY/84locale checks and current runtime/source/sole fresh catalogs MATCH. Foreign dirty WORKTREE/active_run NONE/stands preserved. [Original FAIL](module05-full-2026-10-14-r1/REPORT.md), drift/harness evidence retained. Next module06 PLAN PUBLIC-QA-01 by user; no automatic06/global/production. Historical73tasks/76IDs/88blocks unchanged;09–11additional fresh findings.
- Module02 [LOCAL PASS](module02-full-2026-10-13-r2/REPORT.md),2026-10-13:248 unique module tests PASS один запуск;288 RU/AZ/EN×6widths rendered states PASS (252 initial +36 corrected QA gaps),289PNG. ORG-QA-01–05 закрыты LOCAL; ORG-QA-02=ACCESS-QA-03 одна причина. Source /home/ramin/kidsmap task33-progress HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +approved dirty WORKTREE, active_run NONE. Previous reports preserved; global/external/production NOT RUN. Следующий этап только PLAN SPEC-QA-01 (module03), автоматически не начат.
- Module06 [LOCAL PASS](module06-full-2026-10-14-r1/REPORT.md),2026-10-14: PUBLIC-QA-01–06 CLOSED LOCAL;288 unique backend methods accepted with targeted environment/template/locale rechecks, no unchanged full rerun;1539 accepted native assertions across18 RU/AZ/EN×6width cells, 721 PNG including retained RED/QA attempts,8 READONLY checks. Approved map geometry/SDK retry/filter stacking/marker Escape/action-label scope; runtime/source/sole fresh locales MATCH. [Verification](module06-full-2026-10-14-r1/verification.json). Real SDK/integrations/global13/production NOT RUN; foreign WORKTREE/active_run/stands preserved. Next only module07 PLAN ACCESS-QA-01 by user; automatically not started. Historical76IDs/73tasks/88blocks unchanged.

- Module02 scoped repairs: ORG-QA-03 toolbar accepted по retained84 +fresh final matrix; [ORG-QA-04 final locale/RU fallback](org-qa04-fix-2026-10-13-r2/REPORT.md)72 native PASS; [ORG-QA-05 columns popup](org-qa05-fix-2026-10-13-r1/REPORT.md)66 native PASS. Supplement plans explicitly approved «да делай»; previous OPEN/red/probe errors retained. [Final ACCEPT-02](module02-full-2026-10-13-r2/REPORT.md) имеет приоритет над r1 INCOMPLETE.
- NETWORK-GRANT-UI (ORG-QA-02 = ACCESS-QA-03): [LOCAL SCOPED ACCEPTED](network-grant-ui-fix-2026-10-12-r1/REPORT.md): список/refresh, смена роли, отзыв сетевого доступа и owner pending-cancel.28 targeted tests PASS;217 browser assertions (199 до последней CSS-only правки с source provenance +18 свежих проверок переноса), RU/AZ/EN ×6 widths;106 accepted PNG. [Fresh recheck](network-grant-ui-recheck-2026-10-12-r1/REPORT.md) сохранён как история. Одна причина, не два исправления. Full ACCEPT-02 NOT RUN; далее отдельный PLAN ORG-QA-03. При handoff 2026-10-13 исходники/evidence совпадают, но прежние runtime PID отсутствуют; live runtime recheck BLOCKED.

Приоритет доказательств для module01: текущая [ACCEPT r6](module01-full-2026-10-12-r6/REPORT.md) и scoped QA14 close/focus repair → предыдущие checkpoints/QA09–13 repair с их границами → свежий PLACE-QA-08 repair REPORT → свежий recheck REPORT → исторические r2/r1. Старое OPEN/PLAN ONLY не отменяет последующее одобрение и свежую проверку.
Свежие источники: [PLACE-QA-08 repair](place-qa08-fix-2026-10-11-r1/REPORT.md), [PLACE-QA-01–07 recheck](module01-recheck-2026-10-11-r1/REPORT.md), [историческая общая сверка](module13-2026-10-11-r1/MASTER_AUDIT.md), [канонические промпты/журнал приёмки](module-acceptance-prompts.md).

- Module07 ACCESS-QA-01 — [scoped LOCAL PASS/report](access-qa01-fix-2026-10-14-r1/REPORT.md),2026-10-14: approved HTML focus lifecycle +explicitly approved scoped CSS outline;606observationsPASS (588retained+18fresh replacements),72additional CSS checks/4shared consumersPASS,9backendPASS retained,6real local-mail/new-password/replay flows RU/AZ/EN390/1440. [Verification](access-qa01-fix-2026-10-14-r1/verification.json). Full ACCEPT-07 NOT RUN; ACCESS03=ORG02 prior module02 acceptance retained; ACCESS02/04/05 separate fresh plans/approvals. Historical queue/rechecks/reports preserved, no module08/production.
- Module07 ACCESS-QA-02 — [scoped LOCAL PASS/report](access-qa02-fix-2026-10-15-r1/REPORT.md),2026-10-15: approved native decline for Place/Organization, fresh recipient/currentness under canonical locks;71unique targeted backend methods,953native observationsPASS (18normal +18stale cells,12shared accept flows),48additional alert-recheck support checks. [Verification](access-qa02-fix-2026-10-15-r1/verification.json). Three inherited no-JS transition AbortErrors reproduced on unchanged login/read routes; global motion not repaired. All foreign baseline files/shared MO preserved; container identities/ports checked, seven stopped container states and older process preservation NOT VERIFIED after interruptions; no foreign restarts. ACCESS01 accepted; ACCESS03=ORG02 prior module02 acceptance retained;04/05 still require separate fresh PLAN. Full ACCEPT-07/08/global/production NOT RUN. Historical recheck/RED/harness evidence retained.
- Module07 ACCESS-QA-04 — [scoped LOCAL PASS/report](access-qa04-fix-2026-10-15-r1/REPORT.md),2026-10-15: explicitly approved two owner-team grid/wrap CSS rules only; fresh native RED5FAIL then575observationsPASS (66matrix states +native lifecycle +6focus-hit states),71PNG including2RED. Short card nowx21..339/369 at360/390, full text preserved; RU/AZ/EN×6widths filled/empty/real error, shared reviews, native invite/accept/role/cancel/remove/reload/readback. [Verification](access-qa04-fix-2026-10-15-r1/verification.json). Backend/JS/template/PO/assertions unchanged; foreign baseline files/sharedMO/known stands checked. ACCESS01/02 accepted;03=ORG02 retained;05requires fresh separate PLAN/approval. Full ACCEPT07/global/production/08 NOT RUN.
- Module07 ACCESS-QA-05 — [scoped LOCAL PASS/report](access-qa05-fix-2026-10-15-r1/REPORT.md), 2026-10-15: explicitly approved four AZ/EN PO entries only; exact runtime/MO oracle 8 RED→8 GREEN, 7 targeted tests PASS, 522 native observations PASS across18 RU/AZ/EN×6width cells,60PNG. Native deletion/cancellation/local-mail/code replay/old-session checks; SIMULATED policy only. [Verification](access-qa05-fix-2026-10-15-r1/verification.json). Foreign files/sharedMO/HEAD/active_run checked; four prior HTTP process continuity NOT VERIFIED after interruption, no foreign restarts. ACCESS01/02/04 accepted;03=ORG02 retained. Full ACCEPT07 still pending; no production/module08.
- Module07 полная ACCEPT-07 — **LOCAL FAIL / ACCESS-QA-06 OPEN**, 2026-10-15: [свежий отчёт](module07-full-2026-10-15-r1/REPORT.md), [verification](module07-full-2026-10-15-r1/verification.json). Исторические ACCESS01–05 CLOSED LOCAL;03=ORG02 без повторного patch. 338 existing unique backend methods PASS;2232 native observations PASS/6 source FAIL,624 PNG including retained attempts. Новый06: форма обрезает крайние пробелы точной фразы удаления; [минимальный отдельный PLAN](module07-full-2026-10-15-r1/PLAN-ACCESS-QA-06.md) и готовый diff пока не применены/не одобрены. ACCEPT app0changes, собственные изолированные services/locales, SIMULATED policy/future clock. Entry files/sharedMO/HEAD/active_run/62containers/1known HTTP сверены; прежняя непрерывность четырёх исчезнувших HTTP остаётся NOT VERIFIED. Исторические числа таблицы сохранены; production/module08 NOT RUN.
- Module07 текущая сводная ACCEPT-07 — **LOCAL PASS / ACCESS-QA-01–06 CLOSED LOCAL**, 2026-10-15: [итоговый отчёт](module07-accept-2026-10-15-r2/REPORT.md), [verification](module07-accept-2026-10-15-r2/verification.json). ACCESS06 исправлен по отдельному одобрению: одна строка strip=False в forms.py +новые4regression methods; свежие4RED(24subfailures)→GREEN,7existing target methods PASS,684native observations PASS/18cells,134PNG с RED evidence. Существующий полный корпус338methods/2232nativePASS retained по hashes, повторно целиком не запускался. Исторический full-r1 LOCAL FAIL сохранён: его06закрыт свежим fix-run.03=ORG02 без повторного patch. Сохранность/процессы/изоляция подтверждаются gate; прежняя continuity четырёх старых HTTP остаётся NOT VERIFIED. Production/module08 NOT RUN.
- Module08 PLAN MOD-QA-01 — **CONFIRMED OPEN / implementation approval pending**, 2026-10-15: [fresh recheck/report](mod-qa01-recheck-2026-10-15-r1/REPORT.md), [конкретный план](mod-qa01-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md), [verification](mod-qa01-recheck-2026-10-15-r1/verification.json). Admin/reviewer ×RU/AZ/EN×6widths:32pending=25+7, pager отсутствует;75controlPASS/72sourceFAIL observations,36PNG;4proposed methods/6expected locale subtestFAIL,0ERROR. App0changes, готовый diff только hub template+new4method test, не применён. Другие MOD IDs/full08/production NOT RUN; historical counts сохранены.
- Module08 MOD-QA-01 — **scoped LOCAL PASS**, 2026-10-15: [approved fix/report](mod-qa01-fix-2026-10-15-r1/REPORT.md), [verification](mod-qa01-fix-2026-10-15-r1/verification.json). Только7строк hub template +new4method test. Fresh4methods/6subtestFAIL RED→5target methods GREEN, 618native PASS observations across36main role×lang×width cells; 146PNG including RED. Native filter form→keyboard Next→Previous→reload, edge states/duplicate filters, unchanged candidate/live fingerprint. Другие MOD IDs не закрыты; полный08pending после его задач. Historical counts/old reports preserved; no production/commit/push/deploy.

- Module08 PLAN MOD-QA-02 — **CONFIRMED OPEN / implementation approval pending**, 2026-10-15: [fresh REPORT](mod-qa02-recheck-2026-10-15-r1/REPORT.md), [точный семифайловый план](mod-qa02-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md). Native36cells admin/reviewer×actualRU/AZ/EN×6widths:189controlPASS/72expected sourceFAIL,36PNG; proposed7methods/12expected assertionFAIL after retained QA fixture-normalization correction. Eight valid local image files/canonical draft→pending; hub renders paths/raw gallery without images. Application0changes; author upload/approve/reject/postpatch GREEN/full08/production NOT RUN. Approval MOD01 не переносится.

- Module08 MOD-QA-02 — **scoped LOCAL PASS**, 2026-10-15: [approved fix/report](mod-qa02-fix-2026-10-15-r1/REPORT.md), [verification](mod-qa02-fix-2026-10-15-r1/verification.json). Exact7file approved presenter/template/scopedCSS/JS/test; fresh7methods/12assertionFAIL RED→13target methods GREEN. Native797acceptedPASS/36maincells/24edgecells/12native approve-reject/2actual supported author flows,131PNG. Original owner hidden-mobile-selector NOT RUN retained; corrected only owner subset, assertions unchanged. Owner main+gallery and volunteer main+cover controls tested; unsupported opposite controls NOT RUN, no editor extension. Shared text/private-doc ACL/current-source/locales/foreign67containers+6HTTP checked. MOD01/02 CLOSED LOCAL;03–08/full08 still pending. No commit/push/deploy/production.

- Module08 PLAN MOD-QA-03 — **CONFIRMED OPEN / approval pending**, 2026-10-15: [fresh REPORT](mod-qa03-recheck-2026-10-15-r1/REPORT.md), [однофайловый CSS-план](mod-qa03-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md). 108native base cells/288states, accepted1037controlPASS/84sourceFAIL; toolbar wrap already fixed, residual date compression/local table scroll/mobile sort clipping confirmed. 414PNG including partial and explicitly SIMULATED design trials. App0changes; proposal27line append only kidsmap_changelist.css, not applied. MOD01/02 LOCAL PASS retained; MOD03OPEN,04–08/full08 pending. No production.

- Module08 MOD-QA-03 — **approved CSS applied / ID OPEN**, 2026-10-15: [current REPORT](mod-qa03-fix-2026-10-15-r1/REPORT.md), [JS supplement pending approval](mod-qa03-fix-2026-10-15-r1/MENU_SUPPLEMENT_PLAN.md). Exact approved27line CSS append; fresh140observations/13expectedFAIL RED→1121PASS/288native responsive states GREEN. Separate actual row menus7PASS/5FAIL; exact prepatch CSS replay same5FAIL. Proposed shared JS remains unapplied, browser-only feasibility20PASS. Full ID/ACCEPT08 not closed; MOD01/02 retained. Interruption left8prior HTTP PIDs absent: preservation NOT VERIFIED, no foreign restart;69container identities/state/ports preserved. Only own profile restarted.

- Module08 MOD-QA-03 menu supplement — **scoped LOCAL PASS / whole ID OPEN**, 2026-10-15: [current REPORT](mod-qa03-menu-fix-2026-10-15-r1/REPORT.md), [separate SORT-REQUEST plan pending approval](mod-qa03-menu-fix-2026-10-15-r1/SORT_IMPLEMENTATION_PLAN.md). Approved sole shared JS applied with reproduced Tab/resize lifecycle refinements in same scope.1191actual menu matrixPASS +21edgePASS +140shared controlsPASS, own domain unchanged. Existing CSS1121PASS retained, not rerun. Fresh sorting2sourceFAIL remain; backend0changes and4file plan not applied.31777entry files preserved except approved JS and this note/link;70prior containers preserved. One entry HTTP absent after interruption remains NOT VERIFIED, no foreign restart. Full08/MOD04–08/production not run; no historical ID closed.

- Module08 MOD-QA-03 SEARCH — **scoped LOCAL PASS / whole MOD03 OPEN**, 2026-10-16: [REPORT](mod-qa03-search-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa03-search-fix-2026-10-16-r1/verification.json). Approved three-file hidden-filter fix;6method/19assertionFAIL RED +3nativeFAIL →14target backendGREEN/1053nativePASS (954matrix+96edges+3exact),54model×locale×viewport cells/90reachable sidebar states,232PNG including separately preserved RED/interrupted/columns evidence. Current956source/own freshRU-AZ-ENMO/domain fingerprint MATCH. Six completed mobile batches retained after interruption; only incomplete desktop batches retried; only ownHTTP restarted. Fresh columns recheck:PlacePASS/Event-SpecialistFAIL; [separate four-file PLAN pending approval](mod-qa03-search-fix-2026-10-16-r1/COLUMNS_IMPLEMENTATION_PLAN.md). Foreign32289entry files preserved except approved2app paths and this status note;72foreign containers unchanged; HEAD/branch/active_run NONE unchanged. MOD04–08/full08/global/production NOT RUN; historical reports retained.

- Module08 MOD-QA-03 columns — **CLOSED LOCAL для всех выявленных причин MOD03 / full08 pending**, 2026-10-16: [REPORT](mod-qa03-columns-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa03-columns-fix-2026-10-16-r1/verification.json). Approved4file metadata/template/JS/test; fresh5methods/68assertionFAIL RED +2nativeFAIL →9target/representative methods GREEN,982accepted nativePASS (954matrix incl3target focus replacements +28edges),54base/90reachable sidebar cells,101PNG. Controls map actual permission-filtered cells; identity/private ACL/Place legacy preferences/trash/reload preserved. Previous full CSS/menu/SORT/SEARCH retained by953unchanged source hashes and unchanged code boundaries, not rerun. Source957/own fresh locales/domain MATCH. Environment interruption: only own verified PG/HTTP recovered without reseed;7complete batches+20partialPASS retained. Entry foreign HTTP104840 absent and two prior PG containers running→exited: continuity NOT VERIFIED, no foreign restart; identities/ports/files/HEAD/active_run checked separately. MOD04–08/full08/global/production not accepted.
- Module08 PLAN MOD-QA-04 — **CONFIRMED OPEN / implementation approval pending**, 2026-10-16: [REPORT](mod-qa04-recheck-2026-10-16-r1/REPORT.md), [four-file PLAN](mod-qa04-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), [verification](mod-qa04-recheck-2026-10-16-r1/verification.json). Fresh native RU/AZ/EN×360/390/768×dashboard/Place:18sourceFAIL/38controlPASS,18PNG. Escape leaves navigation open;360/390 opener covered. Reused only owned current isolated profile after source957/isolation/locale verification; domain unchanged,0MOD04app changes. Proposed sidebar adapter/visible mobile close/scoped focusCSS/new regression; no patch or new PO/vendor/layout changes. MOD05–08/full08/global/production NOT RUN.

- Module08 MOD-QA-04 — **CLOSED LOCAL**, 2026-10-16: [REPORT](mod-qa04-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa04-fix-2026-10-16-r1/verification.json). Approved4file sidebar adapter/mobile close/focusCSS/newtest. Fresh2methods/9assertionFAIL +6nativeFAIL RED→4unique accepted backend methods (2new freshGREEN +2sharedPASS retained),191actual nativePASS+1explicit SIMULATED prevented-Escape guard,18corecells,40PNG. First3AZfixture subFAIL corrected only intended language cookie; only2affected methods rerun. RU50PASS retained, only6focus-readiness measurements replaced with6targetPASS. Normal Escape/close/backdrop/focus/reload/aria/private reader/desktop input and row-menu/accordion guards pass. Source958/own freshRU-AZ-ENMO/domain MATCH; previous unchanged full suites not rerun. Entry32898files preserved except approved3app paths+this note,74containers and entryHTTP30142 identity/state/ports maintained; earlier continuity limits retained. Full08/global/production NOT RUN.
- Module08 PLAN MOD-QA-05 — **CONFIRMED OPEN / approval pending**, 2026-10-16: [REPORT](mod-qa05-recheck-2026-10-16-r1/REPORT.md), [one-file/one-line PLAN](mod-qa05-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), [diff](mod-qa05-recheck-2026-10-16-r1/proposed.diff). Fresh RU/AZ/EN×390/1440:20controlPASS/6return-focus sourceFAIL,12PNG. Initial focus and Tab trapping already work in current shared engine; no duplicate SVG/focus-engine patch. BODY after Escape remains; proposed row-handler trigger.focus before confirmation, only kidsmap_place_changelist.js. App0changes, domain/source unchanged; current own profile/locales verified before read-only reuse. Actual data confirmations/full18cellacceptance/full08/MOD06–08/production NOT RUN.

- Module08 MOD-QA-05 **CLOSED LOCAL**, 2026-10-16: [scoped REPORT](mod-qa05-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa05-fix-2026-10-16-r1/verification.json). Approved one-line row-trigger focus fix; fresh native RED BODY →159native GREEN observations, RU/AZ/EN×6widths,45PNG. Initial HTML focus/trap retained; warning/danger Escape+Cancel restore visible same trigger; shared view/menu sample PASS. Domain unchanged;2entry QA HTTP/74containers preserved; HEAD/branch/active_run unchanged. MOD06–08 OPEN; full ACCEPT08 once after tasks, global separately. No production/commit/push/deploy/module09.

- Module08 MOD-QA-06 **CONFIRMED OPEN / PLAN COMPLETE**, 2026-10-16: [fresh REPORT](mod-qa06-recheck-2026-10-16-r1/REPORT.md), [six-file implementation plan](mod-qa06-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), candidate diff unapplied. Native RU/AZ/EN×390/1440:4sourceFAIL AZ/EN,9controlPASS,6PNG; domain unchanged. Separate scope approval pending. MOD05 CLOSED LOCAL; MOD07–08 OPEN; full08 once after tasks.

- Module08 MOD-QA-06 **CLOSED LOCAL (bounded confirmation scope)**, 2026-10-16: [REPORT](mod-qa06-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa06-fix-2026-10-16-r1/verification.json). Approved6files: localized unpublish modal/native fallback,3PO,newregressiontest.4unique backend methods accepted;102actual primary browser observations RU/AZ/EN×6widths,11edge checks (9explicitSIMULATED+2controls),65PNG including retained failures/interrupted evidence. Only15failed browser observations and2failed backend methods repeated; otherPASS retained. Domain/files/HEAD/branch/active_run/74container states preserved. **3entry QA HTTP disappeared during explicit interruption; continuity NOT VERIFIED**, noforeignrestart; onlyownHTTP recovered. Actual action/toasts/full08/global NOT RUN. MOD07–08 await separate PLAN; no09/production/commit/push/deploy.

- Module08 MOD-QA-07 **CONFIRMED OPEN / PLAN COMPLETE**, 2026-10-16: [fresh REPORT](mod-qa07-recheck-2026-10-16-r1/REPORT.md), [three-file implementation plan](mod-qa07-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), candidate unapplied. Native RU/AZ/EN×390/1440:12sourceFAIL/24controlsPASS,6actual confirmed invalidSave;1error→84RU/83AZ/89EN links,href# and focusstaysA. NewownDB, current959source/freshMO, persistedparent/M2M/locations/documents unchanged;1entryHTTP/74containers preserved. Newscopeapproval pending; MOD01–06 CLOSED LOCAL,08pending/full08onceaftertasks. No apppatch/production/commit/push/deploy/module09.

- Module08 MOD-QA-07 **approved core LOCAL PASS / whole ID OPEN**, 2026-10-16: [REPORT](mod-qa07-fix-2026-10-16-r1/REPORT.md), [CSS supplement PLAN pending approval](mod-qa07-fix-2026-10-16-r1/CSS_SUPPLEMENT_PLAN.md). Approved2appfiles+NEWtest:2methods/6languageassertionFAIL RED→5target/sharedmethodsGREEN;126primarynativePASS/18cells+58edgesPASS(2explicitSIMULATED), persistedparent/M2M/locations/documentsunchanged. Newheadinglayout3mobileFAIL,6SIMULATEDCSSfeasibilityPASS; CSS unapplied.62PNG,current960source/ownfreshMO,2entryHTTP+74containers preserved;HEAD/branch/active_runNONE unchanged. No full08/global/09/production/commit/push/deploy.

- Module08 MOD-QA-07 **CLOSED LOCAL**, 2026-10-16: [итоговый REPORT](mod-qa07-css-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa07-css-fix-2026-10-16-r1/verification.json). Одобренное CSS-дополнение: один файл, две scoped rules. Fresh RED1 →128actual native PASS (108 по18RU/AZ/EN×width cells +20representative checks RU390/EN1440),23PNG; ошибок console/network local0. Предыдущие5backend methods/184browser checks (2SIMULATED) сохранены по959unchanged source hashes и неизменным evidence; полный корпус не повторялся. Domain/M2M/locations/documents unchanged;3entry HTTP/74containers, чужие файлы/HEAD/branch/active_runNONE сохранены. MOD01–07 CLOSED LOCAL, остался отдельный PLAN MOD08; full08 один раз после последней задачи, global отдельно. Без09/production/commit/push/deploy.

- Module08 MOD-QA-08 **CONFIRMED OPEN / PLAN COMPLETE**, 2026-10-16: [REPORT](mod-qa08-recheck-2026-10-16-r1/REPORT.md), [план на3файла](mod-qa08-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), candidate unapplied. Native RU/AZ/EN×Event/Specialist×390/1440:12sourceFAIL/30controlsPASS,13PNG; Event показывает только category, Specialist не показывает select при наличии server filter_specs. Контроль category selection/Apply/Reset PASS; одна QA-count ошибка исправлена только в helper и перепроверена отдельно. Application changes0,960current source/freshownMO, новаяfictionalDB/domain unchanged. После tool interruption4entryHTTP отсутствуют, continuity NOT VERIFIED; foreignrestart0, восстановлен только ownPGsameID/port и свойHTTP. Scopeapproval pending; MOD01–07 CLOSED LOCAL; full08одинразпослеMOD08, globalотдельно. Без09/production/commit/push/deploy.

- Module08 MOD-QA-08 **CLOSED LOCAL**, 2026-10-16: [REPORT](mod-qa08-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa08-fix-2026-10-16-r1/verification.json). Approved3files: normalized actual filter_specs renderer/status chips +template +new regression. Fresh meaningful RED→8unique targeted/shared backend methods accepted,470nativePASS/36cells+Place representative,9ACL PASS,76PNG. Only24false QA locale comparisons andoneReset test expectation repeated; other accepted checks retained. Source961/ownfreshMO/domain unchanged;33670otherentryfiles/74containers/entryHTTP preserved, active_runNONE. MOD01–08 CLOSED LOCAL scoped; full ACCEPT-08 next once, whole module not yet accepted. Separate unchanged AZ/EN footer-count translation observed outside approval; carry to full audit. No09/production/commit/push/deploy.

- Module08 **полный ACCEPT-08 выполнен один раз / LOCAL FAIL**, 2026-10-16: [REPORT](module08-full-2026-10-16-r1/REPORT.md), [verification](module08-full-2026-10-16-r1/verification.json), [новые findings и3плана](module08-full-2026-10-16-r1/FINDINGS.md).261/261backendPASS,1272native observations:1213PASS/59sourceFAIL по3новым причинам;18corecells/4queues,18invalid-Save и18explicitSIMULATEDtransport cells,304PNG. MOD01–08 scopedCLOSED LOCAL; новые MOD09(P3fuzzy count/created),MOD10(P3toast literals),MOD11(P2terminal decision reason) OPEN, candidate patches unapplied, approval pending. One ownAZrenderer incident UNKNOWN; freshAZ390/remainder controls complete, foreignHTTP2/containers74/source961/WORKTREE/active_runNONE сохранены. Adjacent editor/home-recommendations locale observations transferred, not fixed. Не повторять неизменённый full corpus; после approval толькоtargeted/affected checks. Модуль09 не запускать; безproduction/commit/push/deploy.

- Module08 MOD-QA-09–11 **CLOSED LOCAL / модуль остаётся LOCAL FAIL**, 2026-10-16: [новый REPORT](mod-qa09-11-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa09-11-fix-2026-10-16-r1/verification.json). Одобренные9app/testfiles; meaningfulRED→13targeted/sharedbackendPASS,433acceptedbrowserPASS,18primary+18reviewer cells RU/AZ/EN×6widths,294PNG включая RED/candidate/history. Полный261backendcorpus не повторён. Новые [MOD12/13 OPEN и точные планы](mod-qa09-11-fix-2026-10-16-r1/FINDINGS.md): конфликт legacyCSS и блокировка очереди уведомлений; candidates не применены, требуется отдельное одобрение3unique files. Пользователь разрешил push/сервер **после готовности модуля**; условие ещё не выполнено, production/commit/push/deploy NOT RUN. Не начинать09; active_runNONE/foreignwork сохранены.

- Module08 **LOCAL PASS — итог ACCEPT-08**, 2026-10-16: [финальный REPORT](module08-accept-2026-10-16-r2/REPORT.md), [verification](module08-accept-2026-10-16-r2/verification.json), [последние MOD12/13](mod-qa12-13-fix-2026-10-16-r1/REPORT.md). MOD01–13 CLOSED LOCAL в записанном scope. Полный261backendPASS выполнен один раз; после новых причин сохранён и дополнен13targetedDjangoPASS,4NodeGREEN,433nativePASS для09–11 и341nativePASS для12/13 (18cells,74actualPOST,безручногоочищенияочереди). Source965,956unchanged common source+5covered changes+4newtests;3PO отдельно проверены. ЧужиеWORKTREE/4QAHTTP/74containers/active_runNONE сохранены. Global/physical/cross-browser/production не приняты этимLOCALPASS. Пользователь разрешилGitpush/сервер после готовности модуля: теперь отдельная release phase, безавтоматическогоmodule09.

- Module08 **выкладка выполнена**, 2026-10-16: [release REPORT](module08-release-2026-10-16-r1/REPORT.md), [verification](module08-release-2026-10-16-r1/verification.json). После LOCAL PASS пользователь отдельно разрешил Git push и сервер. Код cfef63e3, release-ветка codex/module08-release-2026-10-16; весь безопасный пакет QA в Git,5историческихCSRF-логов сохранены только локально. Production image1f2d56ca,968source/PO+3MO MATCH,30readonly nativePASS RU/AZ/EN×390/1440,10originHTTP200. БД/schema/env/mounts/PG/Redis сохранены, backup/rollback подготовлены. Исходный локальный HEAD/index/dirtyWORKTREE/active_runNONE сохранены. Это ограниченный production smoke, не полная production-приёмка всех модулей; внешние интеграции/реальные email/admin mutations NOT RUN. До выкладки отмечен отсутствующий настроенный GA ADC файл. Модуль09 автоматически не начинать.

- Module09 SOCIAL-QA-01 **CONFIRMED OPEN / PLAN COMPLETE**, 2026-10-16: [fresh REPORT](social-qa01-recheck-2026-10-16-r1/REPORT.md), [two-file implementation plan](social-qa01-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), candidate diff unapplied. Native four typed reviews create→reload→approve→reload RU390:20controlPASS/8sourceFAIL,8PNG. Rating4 saved; editor empty. New ownPG/DB/cache/media/private-media/email/freshRU-AZ-ENMO,967current source; application changes0. User interruption removed5entryQAHTTP; continuity NOT VERIFIED, foreignrestart0; ownHTTP alone resumed after source check. Scopeapproval pending; SOCIAL02–09 historical queue awaiting separate fresh PLAN, fullACCEPT09 once after tasks. No commit/push/deploy/production.

- Module09 SOCIAL-QA-01 **CLOSED LOCAL**, 2026-10-16: [REPORT](social-qa01-fix-2026-10-16-r1/REPORT.md), [verification](social-qa01-fix-2026-10-16-r1/verification.json). Approved template +new7method regression only; RED6methods/61assertionfailures→11unique targeted/shared GREEN. Native4types×6states×RU/AZ/EN×6widths:432state cells/1728primary checks;6native390/1440 cases, keyboard/ACL, real409 and2SIMULATEDtransport checks. Completed CAS/Back3checks retained from partial attempt; shared view-transition error separately recorded, not fixed. Full ACCEPT09/global/production NOT RUN. SOCIAL02 next separate PLAN;03–09 still require fresh scope. Foreign WORKTREE/index/sharedMO/HEAD/active_run/75containers/current entryHTTP checked; earlier5HTTP continuity remains NOT VERIFIED. No commit/push/deploy.

- Module09 SOCIAL-QA-02 **CONFIRMED OPEN / PLAN COMPLETE**, 2026-10-16: [fresh REPORT](social-qa02-recheck-2026-10-16-r1/REPORT.md), [three-file implementation plan](social-qa02-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), candidates unapplied. Native reload16states/4types:40PASS/24sourceFAIL,16PNG;8readonly rejected records have saved reason, author feedback absent. Existing own current968source/freshsoleMO profile ownership/isolation verified before reuse; application changes0. SOCIAL01 CLOSED LOCAL; scope02 approval pending,03–09 await separate fresh PLAN. Full ACCEPT09 once after tasks; no production/commit/push/deploy.

- Module09 SOCIAL-QA-02 **CLOSED LOCAL**, 2026-10-16: [REPORT](social-qa02-fix-2026-10-16-r1/REPORT.md), [verification](social-qa02-fix-2026-10-16-r1/verification.json). Approved controller/template +new4method regression; RED4methods/26assertionFAIL →8targeted/shared GREEN. Native4types×2rejected states×RU/AZ/EN×6widths:144cells/864primary checks;1420acceptedPASS,198nativePNG including retained partial captures. Author-only reason/text, current projection, real-cooldown correction/resubmit/approve, escaping/focus/overflow/privacy checked. Source969/index/sharedMO/HEAD/active_run/76entrycontainers preserved;2entryHTTP disappeared during environment discontinuity, continuity NOT VERIFIED, foreignrestart0; own HTTP alone resumed. Batch143 between completed cases recorded, only remaining cases continued. SOCIAL01–02 closed; next separate PLAN SOCIAL03. Full ACCEPT09 once after tasks, global/production/commit/push/deploy NOT RUN.

- Module09 SOCIAL-QA-03 **OPEN / REVIEWABLE PLAN READY — SOURCE REFRESH REQUIRED**, 2026-10-16: [REPORT](social-qa03-recheck-2026-10-16-r1/REPORT.md), [verification](social-qa03-recheck-2026-10-16-r1/verification.json), [three-file scope](social-qa03-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md). Captured969snapshot:18Specialist native409 cells RU/AZ/EN×6widths,36controlPASS/36sourceFAIL/18PNG; editor/B/navigation absent, latestA/public preserved;18known sharedViewTransition errors recorded. After capture, outside-scope review service/admin/PO changes and5newsource files invalidate whole-current-source/locale parity; failed gates retained, no currentPASS. Controller/template proposal baselines still match, app patch0; six candidate tests NOT RUN. After scope approval: fresh isolatedsource/MO and targeted native409+RED before patch; changed cause/extra file needs new approval. SOCIAL01–02 scoped historicalLOCAL results retained; transfer to changedWORKTREE requires affected rechecks, fullACCEPT09 once after tasks. Foreign changes preserved, no commit/push/deploy/production.

## Сколько задач осталось и как идти

Историческая сверка: 81 ID /77 групп причин. Module13 добавил 3 новых CROSS ID: всего 84 уникальных ID. PLACE-QA-08 — alias CROSS-QA-03, не 85-й дефект. Из очереди исключены PLACE-QA-01–07 и CROSS-QA-03: **76 оставшихся ID /73 группы**. Это очередь для свежего recheck, а не подтверждение 76 текущих неисправностей или полного покрытия продукта.

Два объединения предотвращают повторное исправление: NETWORK-GRANT-UI = ORG-QA-02 +ACCESS-QA-03; COMPILED-LOCALE-FRESHNESS = оставшиеся EVENT-QA-01 +PUBLIC-QA-03 +SITE-QA-07. PLACE-QA-06 из исторической locale-группы уже scoped PASS. Новые дефекты, новые NOT RUN и другие причины переводов учитываются отдельно.

Рекомендуемый порядок после START: проверить получение PLACE fixes и fresh locale profile; выполнить недостающую ACCEPT-01; начать отдельные исправления с SITE-QA-01 (P1 ACL), ANALYTICS-QA-01 (чтение без permission) и CROSS-QA-02 (discovery тестов), затем общий NETWORK-GRANT-UI, общий locale recheck и функциональные задачи по модулям. Для каждого batch сначала PLAN. Приоритет может измениться после свежего воспроизведения. Связанные SITE/ANALYTICS permission задачи не объединять в patch без конкретного согласованного общего плана.

| Модуль | Исторические ID, оставшиеся для recheck | PLAN блоков здесь | Переход |
|---|---|---:|---|
| 01 Постоянные места | 0 исторических; QA09–14 LOCAL CLOSED, module01 ACCEPT r6 PASS | 0 | [Задачи](#m01) · [ACCEPT-01](#accept01) · [текущий r6](module01-full-2026-10-12-r6/REPORT.md) |
| 02 Организации, готовые места и сотрудники | 4 | 4 | [Задачи](#m02) · [ACCEPT-02](#accept02) |
| 03 Специалисты и приватные документы | 3 | 3 | [Задачи](#m03) · [ACCEPT-03](#accept03) |
| 04 Мероприятия | 3 | 3 | [Задачи](#m04) · [ACCEPT-04](#accept04) |
| 05 Программы, занятия, группы, тарифы и расписание | 8 | 8 | [Задачи](#m05) · [ACCEPT-05](#accept05) |
| 06 Публичный каталог, поиск, фильтры и карта | 4 | 3 | [Задачи](#m06) · [ACCEPT-06](#accept06) |
| 07 Аккаунты, команда, права и приватность | 5 | 4 | [Задачи](#m07) · [ACCEPT-07](#accept07) · [LOCAL PASS:01–06](module07-accept-2026-10-15-r2/REPORT.md) · [исторический full-r1](module07-full-2026-10-15-r1/REPORT.md) |
| 08 Админка, модерация и волонтёрский кабинет | 0 OPEN в проверенном scope;MOD01–13 CLOSED LOCAL | 0 | [ACCEPT-08 LOCAL PASS](module08-accept-2026-10-16-r2/REPORT.md) · [verification](module08-accept-2026-10-16-r2/verification.json) · full261 once +targeted supplements |
| 09 Отзывы, избранное и уведомления | 9 | 9 | [Задачи](#m09) · [ACCEPT-09](#accept09) |
| 10 Настройки, разделы и общие страницы | 15 | 14 | [Задачи](#m10) · [ACCEPT-10](#accept10) |
| 11 SEO, языковые URL и redirects | 7 | 7 | [Задачи](#m11) · [ACCEPT-11](#accept11) |
| 12 Просмотры, счётчики и аналитика | 8 | 8 | [Задачи](#m12) · [ACCEPT-12](#accept12) |
| 13 Финальная межмодульная приёмка и сводка | 2 | 2 | [Задачи](#m13) · [ACCEPT-13](#accept13) |

Общий NETWORK prompt находится в модуле 02, общий locale prompt — в 04. Поэтому 07, 06 и 10 имеют меньше собственных PLAN, чем своих исторических ID. CROSS-QA-01/02 находятся в 13; повторные свежие module13 findings SITE/ANALYTICS/ORG/ACCESS/SOCIAL учитываются в исходных модулях.

## START — первый запуск на другом компьютере

```text
Продолжаем KidsMap на другом ПК по docs/qa/continuation-and-repair-prompts-2026-10-11.md. Прочитай вступление, текущий статус, таблицу модулей и раздел переноса; все 73 задания целиком заранее не загружай.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.

Режим: проверка полученного checkout и подготовка собственного LOCAL QA стенда, без исправлений приложения. Свежие источники: docs/qa/module01-recheck-2026-10-11-r1/REPORT.md, docs/qa/place-qa08-fix-2026-10-11-r1/REPORT.md, docs/qa/module13-2026-10-11-r1/MASTER_AUDIT.md. PLACE-QA-01–08 не переисправляй по старому r2; full module01 ещё NOT RUN.

Проверь наличие исходников существующих PLACE fixes, scripts/build_isolated_locales.py, новых regression tests и связанных QA документов по docs/qa/continuation-2026-10-11/transfer-inputs.json. Если bundle неполный, перечисли конкретные отсутствующие/неполученные материалы. Не объявляй Windows SHA/порты актуальными. Проверь доступные Python/Node/PostgreSQL/Docker/browser/msgfmt по lock/config репозитория. Используй существующий runtime или настрой свой по инструкциям проекта; не скачивай данные/credentials со старого стенда. PostgreSQL запуск только собственный с явным loopback и уникальными DB/container/cache/media. Не останавливай чужие процессы; active_run не присваивай автоматически.

Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Прочитай docs/qa/isolated-locale-build.md и действующие тестовые настройки перед запуском. Старые .venv, .tmp, compiled MO, browser profiles и контейнеры через Git не переносятся. Исторические launcher — примеры архитектуры изоляции, а не portable команды. Создай свои уникальные настройки без загрузки checkout .env; секреты остаются вне Git. Для readback используй READ ONLY транзакции с таймаутами.

Сохрани docs/qa/<свой-уникальный-start-run>/REPORT.md: path/HEAD/branch/dirty WORKTREE/active_run, доставленные fixes и недостающие документы, версии инструментов, isolation/locale manifest, runtime source match, точные команды/exits, NOT RUN. Сравнение helper/test/source hashes — provenance, не PASS полного module01. На выходе дай следующий конкретный prompt ACCEPT-01 либо выбранный пользователем PLAN из guide. Остальные задачи автоматически не начинай.
```

## IMPLEMENT-APPROVAL — после просмотра конкретного плана

Копируй в **тот же чат**, в котором агент только что сохранил и показал конкретный план. Этот блок является твоим разрешением на реализацию этого плана. Если продолжение в новом чате, сначала добавь путь плана и разрешённые ID своими словами.

```text
Одобряю реализацию последнего конкретного implementation plan, который ты сохранил и показал в этой переписке. Выполни только перечисленные в нём ID и файлы, включая связанные целевые тесты, локализацию и QA evidence. Если одобрение относится к одному ID/общей причине, остальные findings не входят в scope. Это разрешение на локальную реализацию и проверку плана, без commit/push/deploy/production.

Перед изменениями назови фактический путь одобренного плана и его ID, сверяй текущий checkout/source. Если в переписке нет конкретного доступного плана или его scope неоднозначен, реализацию не начинай: сначала предъяви конкретный документ и границы. Уже одобренный scope повторно не переспрашивай. Существенное расширение согласуй отдельно, продолжая независимую разрешённую работу.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Исправь первопричину минимально, сохраняя бизнес-контракт, ACL, CAS и candidate/live invariants. Meaningful regression tests для поведения/data/security: сначала воспроизведение до patch, затем GREEN; не меняй существующие assertions ради green. Для простых обратимых визуальных изменений докажи поведение браузером без тестов, повторяющих код. Запусти обязательные целевые проверки и affected shared consumers; no-label Django test/full wrapper не считать полным корпусом без discovery доказательства CROSS-QA-02. Отдели baseline и environment failures от регрессий.

Для UI выполни реальные native transitions, сохранение/reload/readback, RU/AZ/EN ×360/390/768/1024/1280/1440 в применимом scope, keyboard/focus, error/conflict и console/network; source inspection/jsdom/HTTP200 не заменяют rendered browser. ORM допустим для fictional fixture setup, не для проверяемого пользовательского перехода. Внешние интеграции только явно SIMULATED/NOT RUN. Новую locale сборку делай только для своего profile.

Доведи одобренный scope до reviewable diff и свежего отчёта: snapshot/runtime, причина, точные изменения, команды/exits/counts, tests/browser evidence и PNG manifest, NOT RUN, preservation чужого WORKTREE/active_run/стендов. Закрой только ID с фактическим acceptance, явно укажи пределы; не приписывай общий module PASS по целевому repair. Обнови соответствующий статус со ссылками, сохрани исторические отчёты. Дай handoff и подходящий ACCEPT prompt; недопроверенный/неисправленный finding оставь OPEN.
```

## PLAN — отдельные задачи по модулям

Каждый блок целиком задаёт свежую проверку и план одной причины. Выполнение PLAN не разрешает автоматически реализацию. Технические задания перенесены из прежних standalone prompts; новые ограничения этапа и свежий статус в этом guide имеют приоритет над историческим «исправь». Репозиторные пути переносимы, localhost/fixture IDs в описаниях только иллюстрируют старое воспроизведение.

<a id="m01"></a>

### 01. Постоянные места

PLACE-QA-01–08 исключены из повторного repair. Выполни [ACCEPT-01](#accept01) для полной приёмки. Новый независимо подтверждённый дефект получит новый ID либо обоснованный reopen с новым evidence.

<a id="m02"></a>

### 02. Организации, готовые места и сотрудники

<a id="repair-ORG-QA-01"></a>

#### PLAN ORG-QA-01 · P2

ORG-QA-01 — опубликованная организация получает устаревшую базу автосохранения. ID: ORG-QA-01.

Источники: [docs/qa/module02-2026-10-09-r1/findings/ORG-QA-01.md](module02-2026-10-09-r1/findings/ORG-QA-01.md), [docs/qa/module02-2026-10-09-r1/repair-prompts.md](module02-2026-10-09-r1/repair-prompts.md).

```text
KidsMap: PLAN ORG-QA-01. ID scope: ORG-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module02-2026-10-09-r1/findings/ORG-QA-01.md, docs/qa/module02-2026-10-09-r1/repair-prompts.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Продолжаем KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module02-2026-10-09-r1/findings/ORG-QA-01.md. Проверь текущие checkout/HEAD/WORKTREE/active_run и сохрани чужие изменения. Scope: исправить привязку ServerDraft к форме опубликованной организации после одобрения.
Воспроизведи на новых вымышленных изолированных данных: автосохранение draft → submit → review approve → редактирование опубликованного → серверное autosave → новая browser context. Сейчас форма source_version=2 получает draft source_version=1 и HTTP409, same-tab recovery скрывает проблему. Исследуй _detail_context, organization_workspace.html и существующий draft/publication контракт. Используй актуальный draft на текущей базе либо предусмотренное безопасное восстановление устаревшего; не ослабляй CAS и проверки владельца, не стирай локальные данные и не перекрывай более новый submitted candidate старым working draft.
Добавь содержательную regression проверку перехода approve→fresh autosave и conflict при настоящей конкуренции. Докажи сохранение/reload в независимой сессии, сохранность публичной версии до review, RU/AZ/EN и mobile/desktop error states. DJANGO_TESTING=1, отдельные DB/cache/media/email, без production/commit/push/deploy. Сначала представь конкретный план исправления в этом scope согласно AGENTS, затем реализуй после согласования scope. Итог: diff, команды/exit codes, свежие evidence/screenshots и оставшиеся ограничения.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-NETWORK-GRANT-UI"></a>

#### PLAN NETWORK-GRANT-UI · P2

Список сотрудников сети и штатный отзыв доступа. ID: ORG-QA-02, ACCESS-QA-03.

Источники: [docs/qa/module02-2026-10-09-r1/findings/ORG-QA-02.md](module02-2026-10-09-r1/findings/ORG-QA-02.md), [docs/qa/module07-2026-10-10-r1/FINDINGS.md](module07-2026-10-10-r1/FINDINGS.md), [docs/qa/module13-2026-10-11-r1/findings/ORG-QA-02.md](module13-2026-10-11-r1/findings/ORG-QA-02.md), [docs/qa/module13-2026-10-11-r1/findings/ACCESS-QA-03.md](module13-2026-10-11-r1/findings/ACCESS-QA-03.md).

```text
KidsMap: PLAN NETWORK-GRANT-UI. ID scope: ORG-QA-02, ACCESS-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module02-2026-10-09-r1/findings/ORG-QA-02.md, docs/qa/module07-2026-10-10-r1/FINDINGS.md, docs/qa/module13-2026-10-11-r1/findings/ORG-QA-02.md, docs/qa/module13-2026-10-11-r1/findings/ACCESS-QA-03.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Одна общая причина: ORG-QA-02 и ACCESS-QA-03. Прочитай оба исходных findings и свежие module13/findings/ORG-QA-02.md, ACCESS-QA-03.md. Владелец приглашает fictional сотрудника EDITOR/all_network, получатель принимает через inbox; текущий кабинет не показывает действующих сотрудников и управление/revoke. Проверь organization_workspace markup/JS и канонические business_team actions/CAS/ACL по source. План должен дать владельцу список действующих сотрудников и native revoke, сохраняя веточные grants, ownership и права. Участник без полномочий не получает управление. ACCEPTANCE будущего patch: invite→accept→список→revoke через настоящий UI→reload; фактический запрет бывшему сотруднику по applicable endpoints, direct guessed IDs и stale/two-tab attempts; RU/AZ/EN PC/mobile, клавиатура и public/private invariants. ACCESS-QA-02 (decline приглашения) — отдельный scope, автоматически не добавляй. Не делай два разных patch для одинаковой причины.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ORG-QA-03"></a>

#### PLAN ORG-QA-03 · P2

ORG-QA-03 — административный выбор карточек выходит за экран на 1024px. ID: ORG-QA-03.

Источники: [docs/qa/module02-2026-10-09-r1/findings/ORG-QA-03.md](module02-2026-10-09-r1/findings/ORG-QA-03.md), [docs/qa/module02-2026-10-09-r1/repair-prompts.md](module02-2026-10-09-r1/repair-prompts.md).

```text
KidsMap: PLAN ORG-QA-03. ID scope: ORG-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module02-2026-10-09-r1/findings/ORG-QA-03.md, docs/qa/module02-2026-10-09-r1/repair-prompts.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Прочитай AGENTS.md и docs/qa/module02-2026-10-09-r1/findings/ORG-QA-03.md. Scope: исправить responsive toolbar административного выбора мест перед подключением к организации. На1024px с sidebar доступно660px, а nowrap форма требует803–893px; document overflow126–216px наEN/AZ/RU. Исследуй kidsmap_changelist.css и существующий search panel. Согласуй конкретный план scope; используй доступную ширину контента/перенос controls, сохрани локальный scroll таблицы. Не скрывай переполнение всего документа и не меняй ownership/connections logic. Докажи поиском/выбором/переходом к preview на360/390/768/1024/1280/1440, RU/AZ/EN, с sidebar и без, клавиатурой и fresh screenshots/geometry. Новые fictional isolated данные; без production/commit/push/deploy, сохранить чужой WORKTREE.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ORG-QA-04"></a>

#### PLAN ORG-QA-04 · P3

ORG-QA-04 — административный редактор организации частично остаётся русским. ID: ORG-QA-04.

Источники: [docs/qa/module02-2026-10-09-r1/findings/ORG-QA-04.md](module02-2026-10-09-r1/findings/ORG-QA-04.md), [docs/qa/module02-2026-10-09-r1/repair-prompts.md](module02-2026-10-09-r1/repair-prompts.md).

```text
KidsMap: PLAN ORG-QA-04. ID scope: ORG-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module02-2026-10-09-r1/findings/ORG-QA-04.md, docs/qa/module02-2026-10-09-r1/repair-prompts.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Прочитай AGENTS.md и docs/qa/module02-2026-10-09-r1/findings/ORG-QA-04.md. Scope: устранить остаточные русские заголовки административного редактора организации наAZ/EN. Свежие browser proofs показывают корректные поля, но вкладку «Названия», заголовок «Организации» и служебные секции по-русски. Текущий gettext для первых двух строк возвращаетRU наAZ/EN. Сначала проверь все фактические источники и текущие PO/MO; не смешивай missing translations с frozen import-time labels. Представь точечный план и согласуй scope; добавь недостающие переводы/исправь привязку языка существующих строк без нового workflow. Проверь сменуRU→AZ→EN в одном процессе и браузере, create/edit/draft/pending/published, mobile/desktop screenshots и labels. Обновляй только согласованные application/locale файлы. Без production/commit/push/deploy; чужие изменения сохранить.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m03"></a>

### 03. Специалисты и приватные документы

<a id="repair-SPEC-QA-01"></a>

#### PLAN SPEC-QA-01 · P2

SPEC-QA-01 — повреждённый файл принимается как документ. ID: SPEC-QA-01.

Источники: [docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-01.md](module03-2026-10-10-r1/findings/SPEC-QA-01.md).

```text
KidsMap: PLAN SPEC-QA-01. ID scope: SPEC-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-01.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap, прочитай AGENTS.md и канонические .agents. Исправь только SPEC-QA-01 из docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-01.md. Перед реализацией подготовь конкретный план; следуй имеющейся авторизации пользователя, при её отсутствии запроси согласование плана.
Причина: upload_document в src/catalog/services/specialist_documents.py принимает расширение PNG/PDF/JPEG без проверки содержимого. Свежий UI-upload файла corrupt.png с 9 байтами «not a PNG» создал документ7 и вернул его после reload/download200. Нужно отвергать неподдерживаемые и повреждённые файлы до записи документа/файла, ограничить ресурсы разбора и дать понятную ошибку, сохранив ввод. Не ослабляй приватное хранение, identity-always-private, отдельное согласие person и одобрение сертификатов, свежие role checks и защищённые download headers. Добавь meaningful негативные и позитивные проверки настоящих файлов; не меняй существующие assertions ради зелёного результата. DJANGO_TESTING=1, новая изолированная DB/cache/media/private-media/email, только вымышленные данные. Перепроверь загрузку, reload и скачивание через rendered UI на RU/AZ/EN PC/mobile. Сохрани diff, точные команды/exit codes/новые доказательства. Сохрани чужие изменения и стенды. Без commit/push/deploy/production и расширения scope.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SPEC-QA-02"></a>

#### PLAN SPEC-QA-02 · P2

SPEC-QA-02 — после 409 сломано превью сохранённого фото. ID: SPEC-QA-02.

Источники: [docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-02.md](module03-2026-10-10-r1/findings/SPEC-QA-02.md).

```text
KidsMap: PLAN SPEC-QA-02. ID scope: SPEC-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-02.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap, прочитай AGENTS.md/.agents и docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-02.md. Исправь только сломанное превью существующего фото при stale-version409. Перед реализацией подготовь конкретный план; следуй имеющейся авторизации, иначе согласуй scope.
В двух вкладках person-профиля сохранение NEWER, затем STALE даёт правильный409 и защищает NEWER, но HTML основного превью получает /media/proposal_…webp без specialists/photos/ и image404. Исследуй связку save_owner_specialist_profile stale check → controller form.add_error → OwnerSpecialistForm.clean/нормализация существующего FieldFile → template specialist.photo.url. Нужно показывать действующее persisted фото и сохранять пользовательский ввод при конфликте без повторной записи/копирования существующего файла. Не ослабляй CAS, проверку person и публикационную модерацию. Meaningful regression test должен проверять реальный URL, файл и состояние БД на409, плюс контроль400 и новый upload. Затем свежий rendered UI двух вкладок/reload на RU/AZ/EN PC/mobile, screenshot ошибок и network. Только DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Не меняй assertions ради зелёного. Сохрани чужие изменения/active_run/стенды; без commit/push/deploy/production и других исправлений.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SPEC-QA-03"></a>

#### PLAN SPEC-QA-03 · P3

SPEC-QA-03 — мобильная навигация формы обрезана. ID: SPEC-QA-03.

Источники: [docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-03.md](module03-2026-10-10-r1/findings/SPEC-QA-03.md).

```text
KidsMap: PLAN SPEC-QA-03. ID scope: SPEC-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-03.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Прочитай AGENTS.md, .agents и docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-03.md в фактическом корне KidsMap. Исправь только внутреннюю обрезку мобильной навигации формы специалистов. Сначала дай конкретный план; используй существующее согласование scope или согласуй его до реализации.
В author proposal и person editor RU/AZ/EN при360/390/768 header/nav имеют height8 и overflow:hidden, хотя текст20px и стрелки32px. Причина source-backed: старое правило .km-owner-mobile-progress div в static/css/pages/specialists.css:917 применяется к новым div header/nav. Сделай размеры заголовка и nav по содержимому, ограничь оформление8px полосой прогресса, сохрани кликабельность и видимый keyboard focus. Не расширяй изменение на редизайн всей формы. Перепроверь RU/AZ/EN ×360/390/768/1024/1280/1440: все5 этапов, длинный label, пустые/ошибочные состояния, Tab/Shift+Tab/Enter/Space, внутреннюю обрезку и реальные screenshots. Нужен rendered browser; scrollWidth<=viewport недостаточно. Сохрани нижние действия и desktop stepper. Только изолированный DJANGO_TESTING=1 и вымышленные данные; сохрани чужие изменения/стенды, без commit/push/deploy/production. Дай diff и свежую проверку, не правь existing assertions ради зелёного.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m04"></a>

### 04. Мероприятия

<a id="repair-COMPILED-LOCALE-FRESHNESS"></a>

#### PLAN COMPILED-LOCALE-FRESHNESS · P2/P3

Свежие compiled locales для Events, публичного каталога и общих страниц. ID: EVENT-QA-01, PUBLIC-QA-03, SITE-QA-07.

Источники: [docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-01.md](module04-2026-10-10-r1/findings/EVENT-QA-01.md), [docs/qa/module06-2026-10-10-r1/FINDINGS.md](module06-2026-10-10-r1/FINDINGS.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-07.md](module10-2026-10-10-r1/findings/SITE-QA-07.md), [docs/qa/module01-recheck-2026-10-11-r1/REPORT.md](module01-recheck-2026-10-11-r1/REPORT.md), [docs/qa/isolated-locale-build.md](isolated-locale-build.md).

```text
KidsMap: PLAN COMPILED-LOCALE-FRESHNESS. ID scope: EVENT-QA-01, PUBLIC-QA-03, SITE-QA-07. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-01.md, docs/qa/module06-2026-10-10-r1/FINDINGS.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-07.md, docs/qa/module01-recheck-2026-10-11-r1/REPORT.md, docs/qa/isolated-locale-build.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Общий исторический runtime/build дефект: EVENT-QA-01, PUBLIC-QA-03, SITE-QA-07. PLACE-QA-06 относится к той же исторической группе, но уже имеет scoped PASS в свежем isolated profile и НЕ входит в открытую очередь. Прочитай docs/qa/isolated-locale-build.md, scripts/build_isolated_locales.py, эти три findings и свежий module01-recheck REPORT. Сначала собери новые MO из текущих PO для своего runtime, проверь manifest/hashes/эффективный LOCALE_PATHS до django.setup. Recheck нужных строк EventAdmin, каталога и общих страниц RU→AZ→EN в одном процессе, отдельные новые browser contexts, PC/mobile. Сравни active/fuzzy/obsolete ключи PO с runtime gettext и реальными DOM labels; не смешивай stale MO, missing/wrong/fuzzy PO и frozen import-time labels. Свежая сборка может закрыть environment finding без app patch. В плане укажи минимальную portable build/launch/quality-gate меру только если её отсутствие свежо подтверждено; существующий helper повторно не реализуй. Не объявляй все старые runtime исправленными и не обновляй shared MO/чужие процессы. PLACE-QA-08 уже исправлен отдельно: RU ключ «Выберите район» активен; одна пересборка obsolete PO до его исправления не помогала. Отдельные source translation findings остаются в своих scopes.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-EVENT-QA-02"></a>

#### PLAN EVENT-QA-02 · P2

EVENT-QA-02 — кнопка удаления главного фото ничего не удаляет. ID: EVENT-QA-02.

Источники: [docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-02.md](module04-2026-10-10-r1/findings/EVENT-QA-02.md).

```text
KidsMap: PLAN EVENT-QA-02. ID scope: EVENT-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-02.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь EVENT-QA-02 по docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-02.md в KidsMap. Прочитай AGENTS.md/.agents, сохрани чужие изменения/active_run/стенды. Scope: штатная кнопка удаления главного фото EventAdmin и её shared handler, честное preview/readiness и серверное сохранение; не менять правила публикации или schema. Сначала составь конкретный implementation-план по каноническим правилам.
Свежая причина: JS ищет id_photo-clear, а реальный checkbox name=photo-clear имеет id photo-clear_id. Проверь все соответствующие lookup, стандартные widgets и shared consumers. Привяжи handler к действительному контролу без хрупкой догадки об id. Черновик должен после клика/сохранения/reload действительно иметь пустое фото; отмена выбора/замена должны работать. Для опубликованного события отдельно проверь настоящий серверный контракт удаления обязательного фото и честную ошибку/готовность; прежний audit не доказал gate bypass.
Добавь содержательную регрессионную проверку roundtrip, не меняй существующие assertions ради green. На новом изолированном DJANGO_TESTING=1 стенде с вымышленными данными пройди UI upload→save→reload→delete→save→reload и replace, проверь публичную карточку, RU/AZ/EN и mobile/PC, shared consumers по impact analysis. Сохрани свежие доказательства и точные counts/exits. Без production, commit/push/deploy. При обязательном отдельном согласовании плана предъяви его до implementation.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-EVENT-QA-03"></a>

#### PLAN EVENT-QA-03 · P2

EVENT-QA-03 — инструкции восстановления/готовности остаются русскими в AZ/EN. ID: EVENT-QA-03.

Источники: [docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-03.md](module04-2026-10-10-r1/findings/EVENT-QA-03.md).

```text
KidsMap: PLAN EVENT-QA-03. ID scope: EVENT-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-03.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
В KidsMap исправь EVENT-QA-03 по docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-03.md. Прочитай AGENTS.md и .agents, сохрани чужие изменения, active_run и стенды. Scope: AZ/EN инструкции текущей трёхшаговой формы Event, readiness/recovery/conflict copy и воспроизводимая поставка locale. Сначала конкретный план согласно правилам репозитория; не меняй workflow, права, требования отправки или сохранённые переводы Event.
Свежий симптом: на английском и азербайджанском интерфейсе часть требований и кнопок восстановления остаётся RU. Сверь trans msgid в owner_event_form/recovery, существующие .po/.mo и реально загружаемые пути. Добавь отсутствующие корректные переводы новых сообщений и синхронизируй compiled catalogs; учти общую зависимость EVENT-QA-01. Не подменяй AZ контент настоящим переводом и не убирай предупреждения о локальной копии/версии.
На отдельном DJANGO_TESTING=1 стенде пройди реальный draft→reload, две вкладки→conflict, выбор восстановления, ошибка отправки и network abort→restore. Проверь RU/AZ/EN × 360/390/768/1024/1280/1440, accessible names, видимый focus и отсутствие RU copy в AZ/EN именно для UI-инструкций. Сохрани свежие screenshots, native commands/counts/exits; не меняй существующие assertions. Без production, commit/push/deploy; при обязательном согласовании implementation-плана предъяви его до правок.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m05"></a>

### 05. Программы, занятия, группы, тарифы и расписание

<a id="repair-OFFER-QA-01"></a>

#### PLAN OFFER-QA-01 · P2

OFFER-QA-01 — Удалённая группа остаётся публичной после одобрения. ID: OFFER-QA-01.

Источники: [docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-01.md](module05-2026-10-10-r1/findings/OFFER-QA-01.md).

```text
KidsMap: PLAN OFFER-QA-01. ID scope: OFFER-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-01.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: OFFER-QA-01, Удалённая группа остаётся публичной после одобрения. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-01.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Nested replacement/publication, archive/visibility semantics, owner editor. Зависимости: PricingPlan history, candidate/live и транзакция одобрения. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Обеспечь предусмотренное контрактом удаление/архивирование отсутствующей группы при одобрении полного nested payload. Не интерпретируй частичный import как очистку. Проверь также пропуск занятия, удаление тарифа, foreign IDs, атомарность, историю и повторное одобрение. Воспроизведи полный UI путь и reload публичной карточки.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-OFFER-QA-02"></a>

#### PLAN OFFER-QA-02 · P2

OFFER-QA-02 — В редакторе групп нет обязательных полей регулярного абонемента. ID: OFFER-QA-02.

Источники: [docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-02.md](module05-2026-10-10-r1/findings/OFFER-QA-02.md).

```text
KidsMap: PLAN OFFER-QA-02. ID scope: OFFER-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-02.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: OFFER-QA-02, В редакторе групп нет обязательных полей регулярного абонемента. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-02.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Owner group pricing editor/choices/copy; согласование с canonical PricingPlan validation. Не ослаблять DB constraints и существующие assertions. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Добавь согласованные с canonical pricing поля count/cycles/quantity/unit, условную видимость и сохранение значений. Обеспечь recurring и installment без фиктивных defaults. Проверь membership/month/count, installment/cycles, quantity/unit, переключение one_time, invalid0, RU/AZ/EN mobile/PC, native save и reload.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-OFFER-QA-03"></a>

#### PLAN OFFER-QA-03 · P2

OFFER-QA-03 — Сводка ошибки цены фокусирует выбор программы. ID: OFFER-QA-03.

Источники: [docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-03.md](module05-2026-10-10-r1/findings/OFFER-QA-03.md).

```text
KidsMap: PLAN OFFER-QA-03. ID scope: OFFER-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-03.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: OFFER-QA-03, Сводка ошибки цены фокусирует выбор программы. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-03.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Структурированная адресация ошибок backend→owner form, сохранение localized текста, focus/details. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Согласуй машинный путь ошибки и UI-target без парсинга переведённого текста. При нескольких занятиях/группах/тарифах раскрой и сфокусируй конкретный erroneous input. Проверь Tab/Shift+Tab, mobile, hidden blocks, price/age/billing ошибки и сохранность ввода. Не меняй существующие assertions для зелёного результата.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-OFFER-QA-04"></a>

#### PLAN OFFER-QA-04 · P2

OFFER-QA-04 — Кнопки расписания выходят за границы формы при1024px. ID: OFFER-QA-04.

Источники: [docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-04.md](module05-2026-10-10-r1/findings/OFFER-QA-04.md).

```text
KidsMap: PLAN OFFER-QA-04. ID scope: OFFER-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-04.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: OFFER-QA-04, Кнопки расписания выходят за границы формы при1024px. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-04.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Owner schedule responsive CSS с учётом actual content width; shared component/admin consumers. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Исправь responsive композицию schedule controls в continuous owner form при1024 и соседних размерах. Проверь regular, несколько интервалов, длинные AZ/RU labels, open copy popup, keyboard, sticky sidebar и widths360/390/768/1024/1280/1440. Не меняй schedule/business rules.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-OFFER-QA-05"></a>

#### PLAN OFFER-QA-05 · P3

OFFER-QA-05 — Мобильный статус группы требует горизонтального скролла внутри вкладки. ID: OFFER-QA-05.

Источники: [docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-05.md](module05-2026-10-10-r1/findings/OFFER-QA-05.md).

```text
KidsMap: PLAN OFFER-QA-05. ID scope: OFFER-QA-05. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-05.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: OFFER-QA-05, Мобильный статус группы требует горизонтального скролла внутри вкладки. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-05.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Admin status badges/BusinessEditor responsive layout; остальные entity forms. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Обеспечь чтение полного статуса без внутренней горизонтальной прокрутки. Сохрани статусную семантику, focus и размер контролов. Проверь Program/Activity/Group, длинные RU/AZ/EN подписи и все6 ширин, включая open tabs. Учитывай что root overflow detector не ловит этот случай.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-OFFER-QA-06"></a>

#### PLAN OFFER-QA-06 · P3

OFFER-QA-06 — AZ/EN административные статусы частично остаются русскими. ID: OFFER-QA-06.

Источники: [docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-06.md](module05-2026-10-10-r1/findings/OFFER-QA-06.md).

```text
KidsMap: PLAN OFFER-QA-06. ID scope: OFFER-QA-06. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-06.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: OFFER-QA-06, AZ/EN административные статусы частично остаются русскими. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-06.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Translations/build packaging; definitions BusinessEditor; зависит от согласованного набора переводов и выпуска compiled catalogs. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Отдели недостающие msgid/msgstr от устаревших .mo. Подготовь AZ/EN status translations и воспроизводимую сборку locale artifacts, затем повтори fresh browser проверку фактически поставляемых файлов. Не называй recompilation приложения исправлением безопасности и не меняй бизнес-статусы.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-OFFER-QA-07"></a>

#### PLAN OFFER-QA-07 · P2

OFFER-QA-07 — Обычный адрес редактора молча восстанавливает устаревшую рабочую копию. ID: OFFER-QA-07.

Источники: [docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-07.md](module05-2026-10-10-r1/findings/OFFER-QA-07.md).

```text
KidsMap: PLAN OFFER-QA-07. ID scope: OFFER-QA-07. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-07.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: OFFER-QA-07, Обычный адрес редактора молча восстанавливает устаревшую рабочую копию. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-07.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области ServerDraft lifecycle/version checks, owner restoration UX, candidate/live и multiple sessions. Не очищать все черновики вслепую. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Устрани молчаливое применение устаревшей server copy: версия карточки/кандидата, явный выбор восстановления, scope actor+target, завершение старых copies при explicit save с сохранением нужного ввода. Проверь два разных browser contexts, обычный /edit/, fresh=1, logout/login, reload после draft/save/approval, server/local conflicts и отсутствие потери новых B данных.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-OFFER-QA-08"></a>

#### PLAN OFFER-QA-08 · P2

OFFER-QA-08 — Причина окончательного отказа программы не видна владельцу. ID: OFFER-QA-08.

Источники: [docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-08.md](module05-2026-10-10-r1/findings/OFFER-QA-08.md).

```text
KidsMap: PLAN OFFER-QA-08. ID scope: OFFER-QA-08. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-08.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: OFFER-QA-08, Причина окончательного отказа программы не видна владельцу. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-08.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Program owner candidate lifecycle/status rendering/forms; moderation decision contract. Зависимости: различие return/rejected и final reject/declined. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Согласуй отображение declined/rejected с canonical review semantics: причина, текущие и предложенные тексты, доступное дальнейшее действие. Не переименовывай бизнес-статусы только ради UI. Проверь approve/return/final reject, owner reload, correction/resubmit, AZ/RU/EN, mobile/PC и неизменность live до одобрения.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m06"></a>

### 06. Публичный каталог, поиск, фильтры и карта

PUBLIC-QA-03 выполняется в [COMPILED-LOCALE-FRESHNESS](#repair-COMPILED-LOCALE-FRESHNESS), модуль 04.

<a id="repair-PUBLIC-QA-01"></a>

#### PLAN PUBLIC-QA-01 · P2

PUBLIC-QA-01 — desktop popup общей площадки обрезан, внутреннее закрытие недоступно. ID: PUBLIC-QA-01.

Источники: [docs/qa/module06-2026-10-10-r1/FINDINGS.md](module06-2026-10-10-r1/FINDINGS.md).

```text
KidsMap: PLAN PUBLIC-QA-01. ID scope: PUBLIC-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module06-2026-10-10-r1/FINDINGS.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только PUBLIC-QA-01 из docs/qa/module06-2026-10-10-r1/FINDINGS.md в текущем KidsMap checkout. Сначала прочитай AGENTS.md и канонические .agents, определи HEAD/WORKTREE/active_run и сохрани чужие изменения. Scope: desktop popup общей площадки в публичном каталоге; static/js/catalog_map.js positionDesktopCard и связанные стили static/css/site.css, static/css/pages/catalog_places.css. Fresh evidence: map-geometry.result.txt, map-browser.result.txt, screenshots/map-geometry-ru-768.png. Карта 400px, popup 560px, top отрицательный, overflow:hidden обрезает верх и кнопку ×. Ограничь размер/размещение popup видимой областью, сохрани прокрутку, доступное закрытие и возврат фокуса. Согласуй конкретный план до реализации, затем проверь native clicks и геометрию RU/AZ/EN × 360/390/768/1024/1280/1440, длинный контент, resize и marker motion. Локальный adapter используй только как SIMULATED interface; реальный SDK укажи отдельно. DJANGO_TESTING=1, отдельные DB/cache/media/email, вымышленные данные. Не менять assertions ради зелёного результата. Без production, commit/push/deploy. Отчёт и fresh PNG; остальные findings не исправлять в этом scope.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-PUBLIC-QA-02"></a>

#### PLAN PUBLIC-QA-02 · P2

PUBLIC-QA-02 — отказ загрузки настроенного SDK оставляет вечный loading. ID: PUBLIC-QA-02.

Источники: [docs/qa/module06-2026-10-10-r1/FINDINGS.md](module06-2026-10-10-r1/FINDINGS.md).

```text
KidsMap: PLAN PUBLIC-QA-02. ID scope: PUBLIC-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module06-2026-10-10-r1/FINDINGS.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только PUBLIC-QA-02 из docs/qa/module06-2026-10-10-r1/FINDINGS.md. Прочитай AGENTS.md/.agents, зафиксируй checkout/HEAD/WORKTREE/active_run, сохрани чужую работу. Scope: configured Google SDK failure handling публичного каталога, script tag в src/catalog/templates/catalog/place_list.html и bootstrap static/js/catalog_map.js. Native evidence sdk-failure.result.txt и error-evidence.result.txt: SDK request aborted, через 15s карта всё ещё Loading map/Загружаем карту без terminal error или retry. Подготовь конкретный план, согласуй его и реализуй обработку отказа/ограниченное ожидание/повтор с понятным RU/AZ/EN состоянием. Сохрани доступность списка, Escape, фокус и корректный поздний callback; не создавай дубликаты markers/listeners при retry. Проверь настоящий rendered browser RU/AZ/EN × 360/390/768/1024/1280/1440 с локальным transport abort и delayed callback. Dummy/local adapter — SIMULATED; реальные SDK/credentials без разрешённого тестового окружения NOT RUN. Только DJANGO_TESTING=1 и изолированные вымышленные данные, без production/commit/push/deploy. Сохрани fresh screenshots, команды и exit codes; не исправляй другие findings.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-PUBLIC-QA-04"></a>

#### PLAN PUBLIC-QA-04 · P2

PUBLIC-QA-04 — hero перекрывает фильтры и перехватывает клик по категории. ID: PUBLIC-QA-04.

Источники: [docs/qa/module06-2026-10-10-r1/FINDINGS.md](module06-2026-10-10-r1/FINDINGS.md).

```text
KidsMap: PLAN PUBLIC-QA-04. ID scope: PUBLIC-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module06-2026-10-10-r1/FINDINGS.md. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только PUBLIC-QA-04 из docs/qa/module06-2026-10-10-r1/FINDINGS.md. Прочитай AGENTS.md/.agents и kidsmap-ui-design, зафиксируй HEAD/WORKTREE/active_run, сохрани чужие изменения. Scope: stacking contexts responsive фильтров каталога в static/css/pages/catalog_places.css и static/css/site.css. Fresh native evidence pointer-final.result.txt, screenshots/pointer-final-ru-390.png; pointer-final-ru-768.png — проверенная PASS граница. Catalog layout z-index1!important держит drawer ниже hero z-index100!important; настоящий клик по категории перехватывает hero. Подготовь и согласуй конкретный план, затем обеспечь видимость и pointer доступность drawer/sidebar с правильным backdrop и фокусом. Проверь RU/AZ/EN × 360/390/768/1024/1280/1440, длинные hero headings, открытие/закрытие/Escape/Tab/Shift+Tab, scroll и hit-test controls, а также map popup и sticky header. Не использовать force click как acceptance proof. Только изолированный DJANGO_TESTING=1 стенд с вымышленными данными. Без production/commit/push/deploy; fresh screenshots и отдельный отчёт. Другие PUBLIC-QA не входят в scope.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m07"></a>

### 07. Аккаунты, команда, права и приватность

ACCESS-QA-03 выполняется вместе с ORG-QA-02 в [NETWORK-GRANT-UI](#repair-NETWORK-GRANT-UI), модуль 02.

<a id="repair-ACCESS-QA-01"></a>

#### PLAN ACCESS-QA-01 · P2

ACCESS-QA-01 — фокус выходит из модального окна восстановления пароля. ID: ACCESS-QA-01.

Источники: [docs/qa/module07-2026-10-10-r1/FINDINGS.md](module07-2026-10-10-r1/FINDINGS.md), [docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-01.txt](module07-2026-10-10-r1/repair-ACCESS-QA-01.txt).

```text
KidsMap: PLAN ACCESS-QA-01. ID scope: ACCESS-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module07-2026-10-10-r1/FINDINGS.md, docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-01.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и свежий docs/qa/module07-2026-10-10-r1/REPORT.md вместе с FINDINGS.md. Сверь текущие HEAD/branch/WORKTREE/active_run и воспроизведи дефект заново: старый evidence не доказывает состояние нового snapshot. Сохрани чужие изменения, active_run и стенды. Для широкого поиска сначала codebase-memory-mcp C-kidsmap, затем проверка нужных source.

Сначала составь конкретный план указанного ниже ремонта и согласуй scope по AGENTS.md, если он ещё не разрешён пользователем. Существующее разрешение повторно не запрашивай. Без production, commit/push/deploy. Проверки только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email и вымышленные данные. Не менять assertions или бизнес-правила ради green. После разрешённого ремонта сохрани новые результаты, native exit codes и реальные browser screenshots; чётко перечисли NOT RUN.

Цель: ACCESS-QA-01, P2 — доступность модального окна восстановления пароля. Scope: src/catalog/templates/auth/login.html и необходимые относящиеся к нему CSS/тесты. Сейчас после открытия и двух Tab фокус уходит на BODY/фон; closeModal не возвращает его opener.

Сделай полноценное управление фокусом: сохранить фактический opener, корректно установить начальный focus, циклические Tab/Shift+Tab только по доступным controls диалога, исключить интерактивный фон на время открытия, вернуть фокус после Escape/крестика/закрытия. Сохрани существующие AJAX reset, локализованные empty/network errors, сохранность email, disabled/loading и CSS transitions. Не блокируй успешное восстановление пароля.

Acceptance: реальный Chromium RU/AZ/EN ×360/390/768/1024/1280/1440; Enter/Space на opener, Tab/Shift+Tab через полный цикл, Escape и close button, видимый focus и восстановление opener. Проверить повторное открытие, пустой/заполненный email, loading/success/error и сетевой отказ. Свежие PC/mobile PNG и actual activeElement trail. Отдельно функциональное reset → локальное письмо → новый пароль → replay denial.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ACCESS-QA-02"></a>

#### PLAN ACCESS-QA-02 · P2

ACCESS-QA-02 — получатель не может отклонить приглашение через UI. ID: ACCESS-QA-02.

Источники: [docs/qa/module07-2026-10-10-r1/FINDINGS.md](module07-2026-10-10-r1/FINDINGS.md), [docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-02.txt](module07-2026-10-10-r1/repair-ACCESS-QA-02.txt).

```text
KidsMap: PLAN ACCESS-QA-02. ID scope: ACCESS-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module07-2026-10-10-r1/FINDINGS.md, docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-02.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и свежий docs/qa/module07-2026-10-10-r1/REPORT.md вместе с FINDINGS.md. Сверь текущие HEAD/branch/WORKTREE/active_run и воспроизведи дефект заново: старый evidence не доказывает состояние нового snapshot. Сохрани чужие изменения, active_run и стенды. Для широкого поиска сначала codebase-memory-mcp C-kidsmap, затем проверка нужных source.

Сначала составь конкретный план указанного ниже ремонта и согласуй scope по AGENTS.md, если он ещё не разрешён пользователем. Существующее разрешение повторно не запрашивай. Без production, commit/push/deploy. Проверки только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email и вымышленные данные. Не менять assertions или бизнес-правила ради green. После разрешённого ремонта сохрани новые результаты, native exit codes и реальные browser screenshots; чётко перечисли NOT RUN.

Цель: ACCESS-QA-02, P2 — получатель должен иметь доступный отказ от актуального приглашения места и организации. Scope: account_notifications template/controller, необходимый POST adapter и тесты; использовать существующие services/business_team.decide_invitation и их ACL. Сейчас inbox даёт только Accept/Mark read, хотя place reject endpoint возвращает200 и REJECTED.

Добавь локализованный native control отказа для актуального приглашения. Не доверяй произвольным entity_type/entity_id из браузера: извлекай разрешённую notification через текущий recipient scope, свежо проверяй email/user/owner/version/expiry и target. CSRF, POST-only, honest success/error, отсутствие побочных изменений при чужом ID, отменённом/истёкшем/уже принятом приглашении. Не расширять права автора, сотрудника, волонтёра или администратора.

Acceptance: владелец приглашает через UI, получатель отклоняет через UI, reload подтверждает REJECTED и отсутствие гранта; повтор, две вкладки, отмена владельцем перед отказом, изменившийся владелец, чужая notification/target и network failure. RU/AZ/EN ×6 widths; клавиатура/видимый focus/длинные данные/PC-mobile PNG. Принимающий путь и локальные письма не должны регрессировать.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ACCESS-QA-04"></a>

#### PLAN ACCESS-QA-04 · P2

ACCESS-QA-04 — карточки приглашений места обрезаются на 360px. ID: ACCESS-QA-04.

Источники: [docs/qa/module07-2026-10-10-r1/FINDINGS.md](module07-2026-10-10-r1/FINDINGS.md), [docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-04.txt](module07-2026-10-10-r1/repair-ACCESS-QA-04.txt).

```text
KidsMap: PLAN ACCESS-QA-04. ID scope: ACCESS-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module07-2026-10-10-r1/FINDINGS.md, docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-04.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и свежий docs/qa/module07-2026-10-10-r1/REPORT.md вместе с FINDINGS.md. Сверь текущие HEAD/branch/WORKTREE/active_run и воспроизведи дефект заново: старый evidence не доказывает состояние нового snapshot. Сохрани чужие изменения, active_run и стенды. Для широкого поиска сначала codebase-memory-mcp C-kidsmap, затем проверка нужных source.

Сначала составь конкретный план указанного ниже ремонта и согласуй scope по AGENTS.md, если он ещё не разрешён пользователем. Существующее разрешение повторно не запрашивай. Без production, commit/push/deploy. Проверки только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email и вымышленные данные. Не менять assertions или бизнес-правила ради green. После разрешённого ремонта сохрани новые результаты, native exit codes и реальные browser screenshots; чётко перечисли NOT RUN.

Цель: ACCESS-QA-04, P2 — убрать обрезку карточок приглашений команды места при360px. Scope: соответствующие responsive selectors static/css/site.css и при необходимости семантическая разметка owner_team.html. Shared owner-review selectors учитывать отдельно. Бизнес-правила/данные/миграции не трогать.

Свежий trigger: cancelled07@example.invalid в h3 карточки; bounds x21..380.1875 при viewport360, body scrollWidth360 маскирует clipping. Ограничь grid min-content/ширины доступной областью и обеспечь перенос email/длинных имён. Не скрывай проблему overflow:hidden и не урезай идентификатор получателя без способа прочитать его полностью.

Acceptance: filled/empty/error team lists с вымышленными длинными email и именами, RU/AZ/EN ×6 widths. Проверяй не только root scrollWidth, но bounds карточек/текста и rendered clipping, role forms/buttons/selects/keyboard focus. PC/mobile PNG; краткая проверка owner reviews как shared CSS regression. Для малой CSS-правки не создавать зеркальные unit tests; реальное browser evidence обязательно.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ACCESS-QA-05"></a>

#### PLAN ACCESS-QA-05 · P2

ACCESS-QA-05 — ошибки удаления аккаунта на AZ/EN остаются русскими. ID: ACCESS-QA-05.

Источники: [docs/qa/module07-2026-10-10-r1/FINDINGS.md](module07-2026-10-10-r1/FINDINGS.md), [docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-05.txt](module07-2026-10-10-r1/repair-ACCESS-QA-05.txt).

```text
KidsMap: PLAN ACCESS-QA-05. ID scope: ACCESS-QA-05. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module07-2026-10-10-r1/FINDINGS.md, docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-05.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и свежий docs/qa/module07-2026-10-10-r1/REPORT.md вместе с FINDINGS.md. Сверь текущие HEAD/branch/WORKTREE/active_run и воспроизведи дефект заново: старый evidence не доказывает состояние нового snapshot. Сохрани чужие изменения, active_run и стенды. Для широкого поиска сначала codebase-memory-mcp C-kidsmap, затем проверка нужных source.

Сначала составь конкретный план указанного ниже ремонта и согласуй scope по AGENTS.md, если он ещё не разрешён пользователем. Существующее разрешение повторно не запрашивай. Без production, commit/push/deploy. Проверки только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email и вымышленные данные. Не менять assertions или бизнес-правила ради green. После разрешённого ремонта сохрани новые результаты, native exit codes и реальные browser screenshots; чётко перечисли NOT RUN.

Цель: ACCESS-QA-05, P2 — корректный AZ/EN язык ошибок подтверждения удаления аккаунта. Scope: точные связанные auth/deletion msgids в locale/az и locale/en и воспроизводимая сборка catalogs; не менять логику кода/точной фразы/сессий/retention policy.

Свежий trigger: неверный код и неверная фраза при native deletion confirmation. В AZ/EN UI остаются русские ошибки. Runtime gettext возвращает русский msgid; code-error записи .po fuzzy и имеют неправильный смысл «ввести код». Не удаляй fuzzy массово и не делай строковые overrides вместо корректных переводов. Проверь точные тексты, наличие в итоговом .mo и реальные loaded catalog paths. Existing чужие .mo/локальные стенды не перезаписывать; первоначальная верификация с собственными catalogs/stand.

Acceptance: RU/AZ/EN ×360/390/768/1024/1280/1440; own fixture request→wrong code→wrong phrase→correction→confirm/cancel, отображение полевых ошибок и сохранность ввода. Локальные письма/tokens не сохранять в артефактах. Используй изолированную явно SIMULATED TEST_POLICY для недоступной default inactive policy; не утверждай production readiness. Свежие mobile/PC PNG ошибок, runtime gettext evidence, exact compile/test commands/exits и source/runtime identity. Значение ошибочного кода/фразы должно быть объяснено верно на активном языке.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m08"></a>

### 08. Админка, модерация и волонтёрский кабинет

<a id="repair-MOD-QA-01"></a>

#### PLAN MOD-QA-01 · P2

MOD-QA-01 — В центре модерации нет перехода к следующим страницам. ID: MOD-QA-01.

Источники: [docs/qa/module08-2026-10-10-r1/findings/MOD-QA-01.md](module08-2026-10-10-r1/findings/MOD-QA-01.md), [docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-01.txt](module08-2026-10-10-r1/repair-prompts/MOD-QA-01.txt).

```text
KidsMap: PLAN MOD-QA-01. ID scope: MOD-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module08-2026-10-10-r1/findings/MOD-QA-01.md, docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-01.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: исправь только MOD-QA-01 — В центре модерации нет перехода к следующим страницам.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/MOD-QA-01.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: admin / content reviewer; /ru/admin/volunteer/moderation/?status=pending. Открыть очередь с более чем 25 предложениями. Прокрутить таблицу и найти переход на страницу 2. Затем сравнить с реально отрисованной страницей ?page=2.
Факт: На первой странице 25 строк, ссылок page=2 нет. Pending counter показывает 32. Страница 2 существует и содержит другие предложения, но попасть на неё из очереди нельзя.
Source: src/catalog/domain_admin/volunteer.py:282–296; src/catalog/templates/admin/volunteer/hub_index.html:19–23. Причина: View передаёт Paginator(rows,25).get_page(...), а hub_index.html завершает таблицу без pagination controls. Подтверждено source и 18 rendered cells.

Разрешённая область исправления: hub_index.html / moderation_hub_index; сохранить ACL, counts, GET-фильтры и порядок.
Зависимости: Django moderation hub; общая доступная навигация страниц.
Целевое поведение: Доступные с клавиатуры предыдущая/следующая страница, номер страницы и сохранение выбранных фильтров.
Приёмка: Создать 26+ вымышленных предложений; пройти UI page1→page2→page1 клавиатурой, с entity/status/date filters. Проверить RU/AZ/EN и шесть ширин; empty и out-of-range page.

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-MOD-QA-02"></a>

#### PLAN MOD-QA-02 · P2

MOD-QA-02 — Фото и галерея в централизованной модерации отображаются путями. ID: MOD-QA-02.

Источники: [docs/qa/module08-2026-10-10-r1/findings/MOD-QA-02.md](module08-2026-10-10-r1/findings/MOD-QA-02.md), [docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-02.txt](module08-2026-10-10-r1/repair-prompts/MOD-QA-02.txt).

```text
KidsMap: PLAN MOD-QA-02. ID scope: MOD-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module08-2026-10-10-r1/findings/MOD-QA-02.md, docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-02.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: исправь только MOD-QA-02 — Фото и галерея в централизованной модерации отображаются путями.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/MOD-QA-02.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: admin / content reviewer; /ru/admin/volunteer/moderation/content/39/. В кабинете владельца выбрать главное фото и два фото галереи, дождаться ready, сохранить черновик, reload и отправить. Открыть реальную pending-заявку в moderation hub.
Факт: В .km-volunteer нет ни одного img. Главное фото — places/gallery.webp, галерея — строковое представление массива словарей. При этом native approve применяет фотографии; публичная карточка после reload реально загружает все три фото.
Source: src/catalog/templates/admin/volunteer/hub_detail.html:9–11; src/catalog/services/moderation_hub.py:reviewer_scopes / changes. Причина: hub_detail.html выводит before/after как обычные строки. Native valid payload и публичный readback подтверждают, что дело не в повреждённой фикстуре. Отдельная legacy review имеет preview, но она superadmin-only; штатный content reviewer получает там 403.

Разрешённая область исправления: Typed presentation of media changes in moderation hub; безопасная выдача preview по существующим правам.
Зависимости: publication payload/gallery order; privacy/storage; модуль01. Не расширять права на приватные документы.
Целевое поведение: Просмотр текущего и предложенного главного фото и галереи с порядком, пригодный для визуального решения.
Приёмка: Native owner/volunteer photo+gallery draft→reload→submit→review; видимые current/candidate previews и порядок, corrupt/missing media state. Approve/reject не меняют прежний контракт live; reviewer без прав private docs не получает их.

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-MOD-QA-03"></a>

#### PLAN MOD-QA-03 · P2

MOD-QA-03 — Панель очередей выходит за экран при ширине 1024. ID: MOD-QA-03.

Источники: [docs/qa/module08-2026-10-10-r1/findings/MOD-QA-03.md](module08-2026-10-10-r1/findings/MOD-QA-03.md), [docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-03.txt](module08-2026-10-10-r1/repair-prompts/MOD-QA-03.txt).

```text
KidsMap: PLAN MOD-QA-03. ID scope: MOD-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module08-2026-10-10-r1/findings/MOD-QA-03.md, docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-03.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: исправь только MOD-QA-03 — Панель очередей выходит за экран при ширине 1024.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/MOD-QA-03.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: admin; /ru/admin/catalog/place/; /ru/admin/catalog/event/; /ru/admin/catalog/specialist/. Открыть очередь на 1024px с обычным sidebar. Дождаться settled layout. Сравнить viewport и правый край toolbar, раскрыть сортировку/колонки. Посмотреть строки мест.
Факт: Root scrollWidth=1162 в RU/AZ и 1099 в EN при viewport=1024. .km-toolbar-right выходит до x=1162.31/1099.09. Кнопки справа обрезаны; у мест первые строки достигают 548px, колонка обновления сжимается до почти нулевой ширины.
Source: static/admin/css/pages/kidsmap_changelist.css:445–491,731,989–998,2862; src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html:95. Причина: Подтверждён источник общего overflow: nowrap в search form, min-width:280px у поиска и toolbar-right при sidebar; wrapping breakpoint только max-width:900. Причина сжатия отдельных table columns/548px row требует дополнительного CSS разбора — гипотеза, не доказанная общая первопричина.

Разрешённая область исправления: Shared changelist toolbar responsive layout и scoped table column rules. Не менять данные/фильтрацию.
Зависимости: sidebar available content width; Place/Event/Specialist shared template; модули01/03/04.
Целевое поведение: Панель поиска/сортировки/колонок помещается в доступную ширину; таблица прокручивается в своём контейнере и остаётся читаемой.
Приёмка: RU/AZ/EN × 360/390/768/1024/1280/1440, sidebar open/closed, dropdowns open. Root overflow ≤1px, все управляющие элементы доступны; таблица имеет локальный scroll, строки обновления не превращаются в вертикальный текст.

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-MOD-QA-04"></a>

#### PLAN MOD-QA-04 · P2

MOD-QA-04 — Escape не закрывает мобильную административную навигацию. ID: MOD-QA-04.

Источники: [docs/qa/module08-2026-10-10-r1/findings/MOD-QA-04.md](module08-2026-10-10-r1/findings/MOD-QA-04.md), [docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-04.txt](module08-2026-10-10-r1/repair-prompts/MOD-QA-04.txt).

```text
KidsMap: PLAN MOD-QA-04. ID scope: MOD-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module08-2026-10-10-r1/findings/MOD-QA-04.md, docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-04.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: исправь только MOD-QA-04 — Escape не закрывает мобильную административную навигацию.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/MOD-QA-04.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: admin; /ru/admin/; /ru/admin/catalog/place/. Фокусировать кнопку навигации, открыть Enter, нажать Escape. Проверить видимость sidebar и body.sidebar-open. Затем активировать оставшуюся сфокусированной кнопку Enter.
Факт: После Escape sidebar остаётся видимым и sidebar-open сохраняется во всех 9 cells. Enter на прежней кнопке закрывает его. При pointer попытке нажать эту кнопку открытый sidebar/logo перекрывает её.
Source: static/admin/js/kidsmap_admin_sidebar.js:1–82; административный header data-widget=pushmenu / Jazzmin PushMenu. Причина: Обёртка использует data-widget=pushmenu; локальный kidsmap_admin_sidebar.js обрабатывает клавиши accordion-пунктов, но не обеспечивает Escape для внешнего sidebar. Runtime подтверждает отсутствие closure. Точная ответственность vendor pushmenu/местного adapter требует решения при исправлении.

Разрешённая область исправления: Интеграция header/sidebar PushMenu: Escape, видимый close/toggle и возврат фокуса.
Зависимости: Vendor Jazzmin/AdminLTE; accordion semantics не ломать; не приписывать sidebar role=dialog без решения по контракту.
Целевое поведение: Escape закрывает открытое перекрывающее меню и сохраняет понятный видимый фокус.
Приёмка: Native Tab/Shift+Tab/Enter/Space/Escape на 360/390/768 во всех языках. Видимый opener/close, меню закрывается Escape и overlay, после закрытия виден правильный фокус.

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-MOD-QA-05"></a>

#### PLAN MOD-QA-05 · P2

MOD-QA-05 — В подтверждении снятия с публикации фокус остаётся на BODY. ID: MOD-QA-05.

Источники: [docs/qa/module08-2026-10-10-r1/findings/MOD-QA-05.md](module08-2026-10-10-r1/findings/MOD-QA-05.md), [docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-05.txt](module08-2026-10-10-r1/repair-prompts/MOD-QA-05.txt).

```text
KidsMap: PLAN MOD-QA-05. ID scope: MOD-QA-05. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module08-2026-10-10-r1/findings/MOD-QA-05.md, docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-05.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: исправь только MOD-QA-05 — В подтверждении снятия с публикации фокус остаётся на BODY.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/MOD-QA-05.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: admin; /ru/admin/catalog/place/ → row menu → toggle-publication confirmation. Фокусировать row more-actions, Enter, выбрать снятие с публикации. Нажимать Tab и Shift+Tab, затем Escape.
Факт: Начальный фокус BODY, последовательные Tab остаются BODY. Escape закрывает modal, но фокус не возвращается opener. В списке focusables первый элемент — SVG use href=#kmi-warning с tabIndex=-1 и aria-hidden=true.
Source: static/admin/js/kidsmap_notifications.js:64–75,90–138,157–177,319–327; static/admin/js/kidsmap_place_changelist.js:row action handler. Причина: getFocusableElements включает любой [href], в том числе SVG use. Warning confirm не соответствует primary/danger selector, поэтому autofocus и trapping используют нефокусируемый use. lastFocusedElement записывается после закрытия row menu, без явного видимого opener; native readback возвращает BODY.

Разрешённая область исправления: Общий kmModal focus engine + передача/восстановление row trigger. Только реально focusable HTML controls; warning tone учитывать.
Зависимости: Общий компонент влияет на confirmations в других модулях; отдельно MOD-QA-06 i18n.
Целевое поведение: Начальный фокус внутри alertdialog, кнопки доступны Tab/Shift+Tab, после Escape фокус возвращается на видимый row opener.
Приёмка: Реальный browser, sprite и fallback icons, primary/danger/warning, первый/последний Tab/Shift+Tab, Enter/Space/Escape, close/cancel, видимый focus return. Все 18 cells; не ограничиваться jsdom.

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-MOD-QA-06"></a>

#### PLAN MOD-QA-06 · P2

MOD-QA-06 — AZ/EN подтверждение снятия с публикации написано по-русски. ID: MOD-QA-06.

Источники: [docs/qa/module08-2026-10-10-r1/findings/MOD-QA-06.md](module08-2026-10-10-r1/findings/MOD-QA-06.md), [docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-06.txt](module08-2026-10-10-r1/repair-prompts/MOD-QA-06.txt).

```text
KidsMap: PLAN MOD-QA-06. ID scope: MOD-QA-06. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module08-2026-10-10-r1/findings/MOD-QA-06.md, docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-06.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: исправь только MOD-QA-06 — AZ/EN подтверждение снятия с публикации написано по-русски.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/MOD-QA-06.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: admin; /admin/catalog/place/ и /en/admin/catalog/place/ → row unpublish. Перейти в AZ или EN очередь и открыть подтверждение снятия опубликованного места.
Факт: «Снять с публикации?», русское объяснение, «Да, снять», «Отмена» в AZ и EN. На EN окружающая основная административная UI переведена. Подтверждено 12 captured texts и 4 повторных browser cells.
Source: static/admin/js/kidsmap_place_changelist.js:647–654,575–579; shared notifications defaults. Причина: Строки захардкожены в kidsmap_place_changelist.js:647–654 и не получают i18n/data labels. Source не зависит от версии .mo. Собственный первоначальный matcher содержал mojibake; статус исправлен по сохранённому rendered text и независимо повторён final-proof.

Разрешённая область исправления: Локализованные labels для row unpublish confirmation; связанные hardcoded success text проверить отдельно, они пока source-only.
Зависимости: Django gettext/data attributes; MOD-QA-05 для общей modal проверки; не переводить пользовательские сохранённые названия.
Целевое поведение: Заголовок, объяснение и кнопки на выбранном языке; пользовательское название места может сохранять свой язык.
Приёмка: AZ/RU/EN: native modal title/body/cancel/confirm и фактически выполненные уведомления, все 6 ширин. Проверить source↔compiled catalogs; отдельно указать fallback, не записывать перевод в модель.

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-MOD-QA-07"></a>

#### PLAN MOD-QA-07 · P2

MOD-QA-07 — Сводка ошибки специалиста разбивает HTML на отдельные символы. ID: MOD-QA-07.

Источники: [docs/qa/module08-2026-10-10-r1/findings/MOD-QA-07.md](module08-2026-10-10-r1/findings/MOD-QA-07.md), [docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-07.txt](module08-2026-10-10-r1/repair-prompts/MOD-QA-07.txt).

```text
KidsMap: PLAN MOD-QA-07. ID scope: MOD-QA-07. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module08-2026-10-10-r1/findings/MOD-QA-07.md, docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-07.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: исправь только MOD-QA-07 — Сводка ошибки специалиста разбивает HTML на отдельные символы.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/MOD-QA-07.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: admin; передать владельцу модуля03; /ru/admin/catalog/specialist/1/change/. В admin снять все специализации, выбрать rejected, указать причину, нажать Save и принять нативное подтверждение. Сервер отклоняет форму. Посмотреть верхнюю error summary.
Факт: Одна .errorlist превращается в 84 error-summary links: «Специализации: <», затем «u», «l», символы class/errorlist markup и далее. Красный блок занимает большую часть экрана. Allowlisted persisted state остаётся прежним, что является правильной валидацией.
Source: src/catalog/templates/admin/catalog/specialist/change_form.html:12–14; Django admin.helpers.AdminField.errors. Причина: В specialist/change_form.html цикл for error in field.errors перебирает AdminField.errors() как HTML string; нужен список ошибок underlying bound field. Подтверждены rendered links и source; это ошибка отображения, а не отсутствие required validation.

Разрешённая область исправления: Specialist server error summary и переход к underlying field/checkbox group; application validation не ослаблять.
Зависимости: Модуль03; Django AdminField vs BoundField; inline error summaries проверить на тот же тип.
Целевое поведение: Одна понятная ошибка «Обязательное поле» с переходом к специализациям, честное состояние несохранённого ввода.
Приёмка: Одна и несколько серверных ошибок, inline errors, длинные тексты и native Save confirmation; понятные сообщения без HTML chars, правильные focus targets, сохранность ввода. RU/AZ/EN × 390/1440 минимум; existing assertions не менять ради зелёного.

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-MOD-QA-08"></a>

#### PLAN MOD-QA-08 · P2

MOD-QA-08 — Панели фильтров мероприятий и специалистов открываются пустыми. ID: MOD-QA-08.

Источники: [docs/qa/module08-2026-10-10-r1/findings/MOD-QA-08.md](module08-2026-10-10-r1/findings/MOD-QA-08.md), [docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-08.txt](module08-2026-10-10-r1/repair-prompts/MOD-QA-08.txt).

```text
KidsMap: PLAN MOD-QA-08. ID scope: MOD-QA-08. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module08-2026-10-10-r1/findings/MOD-QA-08.md, docs/qa/module08-2026-10-10-r1/repair-prompts/MOD-QA-08.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
KidsMap: исправь только MOD-QA-08 — Панели фильтров мероприятий и специалистов открываются пустыми.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/MOD-QA-08.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: admin; /ru/admin/catalog/event/; /ru/admin/catalog/specialist/. Открыть очередь, кнопкой Filter/Enter раскрыть панель. Попытаться выбрать статус, дату события или формат консультации. Сравнить с конфигурацией admin и настоящими filter_specs.
Факт: Панель содержит пустую область, заголовок качества данных, Reset/Apply и счётчик, но не содержит native select. Для специалиста доступны в server filter_specs status/is_active/consultation_format/specializations; для события status/start_datetime/owner, но UI их не выводит.
Source: src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html:280–315; src/catalog/domain_admin/place.py:938,1549; src/catalog/domain_admin/specialist.py:451–455. Причина: Общий search_panel фильтрует spec.field_path по фиксированному whitelist мест created_by/created_date/category/district/is_verified и place quality fields. km_primary_filters Event и Specialist не используется в этом rendering. В фикстуре Event единственная категория поэтому Django законно не выводит category; остальные доступные specs также проигнорированы.

Разрешённая область исправления: Shared filter renderer по entity-specific config/filter_specs; preserve query, chips, counts и reset/apply behavior.
Зависимости: SimpleListFilter и стандартные FieldListFilter; связанные очереди других сущностей; не менять бизнес-фильтрацию и права.
Целевое поведение: Поля применимых фильтров, определённых для данной сущности; выбор и применение меняют GET и список.
Приёмка: Вымышленные Event с разными датами/категориями/status и Specialist с разными format/status/directions. Реальный UI selection→Apply→reload→reset; правильные counts/chips, пустой результат; RU/AZ/EN × все 6 ширин.

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m09"></a>

### 09. Отзывы, избранное и уведомления

<a id="repair-SOCIAL-QA-01"></a>

#### PLAN SOCIAL-QA-01 · P2

SOCIAL-QA-01 — Сохранённая оценка не восстанавливается в редакторе. ID: SOCIAL-QA-01.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-01.md](module09-2026-10-10-r1/findings/SOCIAL-QA-01.md), [docs/qa/module13-2026-10-11-r1/findings/SOCIAL-QA-01-repair.txt](module13-2026-10-11-r1/findings/SOCIAL-QA-01-repair.txt).

```text
KidsMap: PLAN SOCIAL-QA-01. ID scope: SOCIAL-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-01.md, docs/qa/module13-2026-10-11-r1/findings/SOCIAL-QA-01-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в C:/kidsmap (на другом ПК сначала найди checkout). Прочитай AGENTS.md, канонические .agents, docs/qa/module13-2026-10-11-r1/REPORT.md и findings/SOCIAL-QA-01.md в том же run. Задача: SOCIAL-QA-01, SOCIAL-QA-01 — Сохранённая оценка не восстанавливается в редакторе, P2. Сохрани чужие изменения, active_run и стенды. Без commit/push/deploy/production.

Подтверждённый trigger: Choose rating4 and fictional literal HTML text, submit pending review, reload editor.
Ожидание: Saved rating4 selected while content remains escaped.
Факт: Persisted candidate content survives but all four editor rating controls reopen empty. Public approved text escapes correctly.
Свежие доказательства: docs/qa/module13-2026-10-11-r1/social-private.result.txt; matrix.json; screenshots-manifest.json. Source refs: src/catalog/templates/catalog/typed_reviews.html.
Группа причины: REVIEW-RATING-READBACK. 

Сначала проверь текущий source и составь конкретный план исправления с файлами, зависимостями и meaningful regression проверками. Согласно audit scope реализацию выполняй только после согласования этого плана. Не меняй существующие assertions ради green. Применимые проверки: DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, внешние интеграции выключены. После согласованного исправления повтори реальный UI trigger, сохранение/reload и PC/mobile RU/AZ/EN; сохраняй candidate/live и ACL. Отдельно классифицируй source translation, generated assets, baseline и environment failures. Сохрани свежий отчёт, точные команды/counts/exit codes/screenshots и NOT RUN ограничения.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SOCIAL-QA-02"></a>

#### PLAN SOCIAL-QA-02 · P2

SOCIAL-QA-02 — Автор не видит сохранённую причину отказа. ID: SOCIAL-QA-02.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-02.md](module09-2026-10-10-r1/findings/SOCIAL-QA-02.md), [docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-02.txt](module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-02.txt).

```text
KidsMap: PLAN SOCIAL-QA-02. ID scope: SOCIAL-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-02.md, docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-02.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-02.md. Проверь текущие HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Старый QA09 — checklist, не свежий PASS.

Задача: исправить только SOCIAL-QA-02 «Автор не видит сохранённую причину отказа» (P2). Роль/URL: автор; /ru/reviews/event/target/1/ и /reviews/specialist/target/2/.
Воспроизведение: Автор отправляет; модератор отклоняет с QA09 reason. Для live отзыва отправить новую редакцию и отклонить. Автор делает reload.
Ожидание: Автор видит отказ, причину и отклонённый текст, может исправить; approved live остаётся прежним.
Подтверждённый факт: Причины сохранены в revisions; после отказа candidate pointer очищен. Редактор показывает прежний live либо только rejected head text, без причины/понятного статуса.18cells воспроизведены для отклонённого edit.
Проверенный источник/причина: src/catalog/services/review_versions.py:215; src/catalog/controllers/typed_reviews.py:86; src/catalog/templates/catalog/typed_reviews.html:22; moderate_candidate очищает candidate_revision_id; own view/template не выбирают последнее отклонённое решение и не выводят reason.
Конкретная область: Показать автору последнее релевантное решение и reason без раскрытия приватных жалоб. Сохранить live/candidate invariant, обеспечить исправление и resubmit с reload.
Ответственные границы/зависимости: django-reviewer + frontend-reviewer + security-reviewer; причина/жалоба остаются доступны только соответствующему автору/платформе.

Сначала воспроизведи на новом DJANGO_TESTING=1 изолированном DB/cache/media/private-media/email стенде с вымышленными данными и подготовь конкретный план. Реализацию выполняй только в согласованном scope, используя уже данную в новом чате авторизацию; не проси её повторно. Не меняй существующие assertions ради зелёного результата. После scoped исправления выполни meaningful regression checks и настоящий browser/reload RU/AZ/EN×360/390/768/1024/1280/1440; сохрани новый отчёт, exact commands/counts/exit codes, screenshots, candidate/live/ACL readback и NOT RUN. Не расширяй задачу на остальные findings. Без production credentials, внешних интеграций, commit/push/deploy.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SOCIAL-QA-03"></a>

#### PLAN SOCIAL-QA-03 · P2

SOCIAL-QA-03 — 409 убирает редактор и встроенное восстановление ввода. ID: SOCIAL-QA-03.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-03.md](module09-2026-10-10-r1/findings/SOCIAL-QA-03.md), [docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-03.txt](module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-03.txt).

```text
KidsMap: PLAN SOCIAL-QA-03. ID scope: SOCIAL-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-03.md, docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-03.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-03.md. Проверь текущие HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Старый QA09 — checklist, не свежий PASS.

Задача: исправить только SOCIAL-QA-03 «409 убирает редактор и встроенное восстановление ввода» (P2). Роль/URL: автор; /ru/reviews/specialist/target/1/.
Воспроизведение: Открыть отзыв в2вкладках, отправить редакцию A, затем устаревшую B.
Ожидание: 409 объясняет конфликт внутри интерфейса; несохранённый ввод B доступен для сравнения/повтора после обновления версии.
Подтверждённый факт: Сервер защищает данные, но отдаёт отдельную страницу «Отзыв изменился. Обновите страницу.» без редактора, навигации и B.18cells. Back в отдельной проверке возвращал ввод — постоянная потеря данных не заявляется.
Проверенный источник/причина: src/catalog/controllers/typed_reviews.py:65; ReviewConflict обработан сырой HttpResponse409, а не формой/сохранением submitted payload.
Конкретная область: Добавить локализованную обработку409 с сохранением B и явным восстановлением/обновлением. Не превращать конфликт в успешное сохранение и не делать слепой повтор POST.
Ответственные границы/зависимости: django-reviewer + frontend-reviewer; CAS, текущие права, candidate/live и cooldown обязательны.

Сначала воспроизведи на новом DJANGO_TESTING=1 изолированном DB/cache/media/private-media/email стенде с вымышленными данными и подготовь конкретный план. Реализацию выполняй только в согласованном scope, используя уже данную в новом чате авторизацию; не проси её повторно. Не меняй существующие assertions ради зелёного результата. После scoped исправления выполни meaningful regression checks и настоящий browser/reload RU/AZ/EN×360/390/768/1024/1280/1440; сохрани новый отчёт, exact commands/counts/exit codes, screenshots, candidate/live/ACL readback и NOT RUN. Не расширяй задачу на остальные findings. Без production credentials, внешних интеграций, commit/push/deploy.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SOCIAL-QA-04"></a>

#### PLAN SOCIAL-QA-04 · P2

SOCIAL-QA-04 — Страница уведомлений не подключает оформление кабинета. ID: SOCIAL-QA-04.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-04.md](module09-2026-10-10-r1/findings/SOCIAL-QA-04.md), [docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-04.txt](module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-04.txt).

```text
KidsMap: PLAN SOCIAL-QA-04. ID scope: SOCIAL-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-04.md, docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-04.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-04.md. Проверь текущие HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Старый QA09 — checklist, не свежий PASS.

Задача: исправить только SOCIAL-QA-04 «Страница уведомлений не подключает оформление кабинета» (P2). Роль/URL: получатель уведомлений, все роли; /ru/account/notifications/, /account/notifications/, /en/account/notifications/.
Воспроизведение: Войти, открыть пустой/заполненный inbox на360/390 и PC.
Ожидание: Навигация кабинета и строки/кнопки уведомлений имеют существующее оформление, понятные состояния и фокус.
Подтверждённый факт: Синие browser-default ссылки, стандартные кнопки, маркеры списка; account-main-layout display:block во всех18cells. Соседнее избранное с тем же navigation оформлено.
Проверенный источник/причина: src/catalog/templates/pages/account_notifications.html:1; static/css/pages/account_profile.css:811; static/css/pages/organization_workspace.css:823; Template использует account/org классы, но не определяет extra_head для соответствующих CSS; runtime stylesheet list это подтверждает. Внешние fonts blocked не объясняют отсутствие локальных правил.
Конкретная область: Подключить правильные существующие стили кабинета и аккуратно определить необходимые inbox rows/buttons. Проверить empty/read/unread/invite/revoked состояния, keyboard и18cells.
Ответственные границы/зависимости: frontend-reviewer; общая навигация и scoped inbox styles, без прав/данных/глобального редизайна.

Сначала воспроизведи на новом DJANGO_TESTING=1 изолированном DB/cache/media/private-media/email стенде с вымышленными данными и подготовь конкретный план. Реализацию выполняй только в согласованном scope, используя уже данную в новом чате авторизацию; не проси её повторно. Не меняй существующие assertions ради зелёного результата. После scoped исправления выполни meaningful regression checks и настоящий browser/reload RU/AZ/EN×360/390/768/1024/1280/1440; сохрани новый отчёт, exact commands/counts/exit codes, screenshots, candidate/live/ACL readback и NOT RUN. Не расширяй задачу на остальные findings. Без production credentials, внешних интеграций, commit/push/deploy.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SOCIAL-QA-05"></a>

#### PLAN SOCIAL-QA-05 · P2

SOCIAL-QA-05 — Страница отзывов о сайте переполняется на768px. ID: SOCIAL-QA-05.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-05.md](module09-2026-10-10-r1/findings/SOCIAL-QA-05.md), [docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-05.txt](module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-05.txt).

```text
KidsMap: PLAN SOCIAL-QA-05. ID scope: SOCIAL-QA-05. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-05.md, docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-05.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-05.md. Проверь текущие HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Старый QA09 — checklist, не свежий PASS.

Задача: исправить только SOCIAL-QA-05 «Страница отзывов о сайте переполняется на768px» (P2). Роль/URL: вошедший пользователь; /ru/reviews/, /reviews/, /en/reviews/.
Воспроизведение: Открыть страницу с доступной формой автора при768px; посмотреть hero, sorting и реакции.
Ожидание: Контент/кнопки помещаются в viewport без горизонтального scroll и обрезки.
Подтверждённый факт: Document822px при viewport768; сортировка справа805px, реакции791px. Computed review-form-grid tracks220/260/200px, width708/right784.59; форма содержит только2label. Guest без формы помещается.12matrix cells FAIL + отдельная geometry proof.
Проверенный источник/причина: static/css/site.css:6160; src/catalog/templates/pages/site_reviews.html:155; Три минимальные grid tracks220/260/200 с gap28 дают intrinsic min-width708 вложенной форме и растягивают внешние блоки; responsive collapse наступает ниже проверенной ширины.
Конкретная область: Устранить лишнюю/жёсткую колонку и min-content overflow в реальной2полной форме. Не маскировать обрезку overflow-x:hidden; сверить остальные формы и18cells, особенно768.
Ответственные границы/зависимости: frontend-reviewer; scoped .review-form-grid для site form, сохранение остальных consumers.

Сначала воспроизведи на новом DJANGO_TESTING=1 изолированном DB/cache/media/private-media/email стенде с вымышленными данными и подготовь конкретный план. Реализацию выполняй только в согласованном scope, используя уже данную в новом чате авторизацию; не проси её повторно. Не меняй существующие assertions ради зелёного результата. После scoped исправления выполни meaningful regression checks и настоящий browser/reload RU/AZ/EN×360/390/768/1024/1280/1440; сохрани новый отчёт, exact commands/counts/exit codes, screenshots, candidate/live/ACL readback и NOT RUN. Не расширяй задачу на остальные findings. Без production credentials, внешних интеграций, commit/push/deploy.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SOCIAL-QA-06"></a>

#### PLAN SOCIAL-QA-06 · P2

SOCIAL-QA-06 — Выбор звёзд не имеет программного состояния. ID: SOCIAL-QA-06.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-06.md](module09-2026-10-10-r1/findings/SOCIAL-QA-06.md), [docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-06.txt](module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-06.txt).

```text
KidsMap: PLAN SOCIAL-QA-06. ID scope: SOCIAL-QA-06. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-06.md, docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-06.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-06.md. Проверь текущие HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Старый QA09 — checklist, не свежий PASS.

Задача: исправить только SOCIAL-QA-06 «Выбор звёзд не имеет программного состояния» (P2). Роль/URL: автор отзыва о сайте; /ru/reviews/ и языковые варианты.
Воспроизведение: Tab к звезде, выбрать3 с Space/Enter, проверить rendered attributes и hidden rating.
Ожидание: Доступное название оценки и программное состояние выбранного значения позволяют понять текущую оценку.
Подтверждённый факт: Keyboard меняет hidden rating=3, active CSS красит звёзды, но aria-pressed/aria-checked/role radio отсутствуют; label — только цифра.72matrix проверки selected state FAIL. Реальный screen reader NOT RUN.
Проверенный источник/причина: src/catalog/templates/pages/site_reviews.html:158,196; paint() меняет только CSS.active; кнопки с numeric aria-label не сообщают выбор через семантику или live status.
Конкретная область: Обеспечить доступную группу оценки и объявляемое выбранное значение; согласовать keyboard, фокус, тексты AZ/RU/EN. Проверить mouse/Tab/ShiftTab/Space/Enter и native POST/reload.
Ответственные границы/зависимости: frontend-reviewer + accessibility; server payload/range и default rating сохранить.

Сначала воспроизведи на новом DJANGO_TESTING=1 изолированном DB/cache/media/private-media/email стенде с вымышленными данными и подготовь конкретный план. Реализацию выполняй только в согласованном scope, используя уже данную в новом чате авторизацию; не проси её повторно. Не меняй существующие assertions ради зелёного результата. После scoped исправления выполни meaningful regression checks и настоящий browser/reload RU/AZ/EN×360/390/768/1024/1280/1440; сохрани новый отчёт, exact commands/counts/exit codes, screenshots, candidate/live/ACL readback и NOT RUN. Не расширяй задачу на остальные findings. Без production credentials, внешних интеграций, commit/push/deploy.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SOCIAL-QA-07"></a>

#### PLAN SOCIAL-QA-07 · P3

SOCIAL-QA-07 — Название занятия заменено техническим Activity object. ID: SOCIAL-QA-07.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-07.md](module09-2026-10-10-r1/findings/SOCIAL-QA-07.md), [docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-07.txt](module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-07.txt).

```text
KidsMap: PLAN SOCIAL-QA-07. ID scope: SOCIAL-QA-07. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-07.md, docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-07.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-07.md. Проверь текущие HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Старый QA09 — checklist, не свежий PASS.

Задача: исправить только SOCIAL-QA-07 «Название занятия заменено техническим Activity object» (P3). Роль/URL: гость/автор; /ru/reviews/activity/target/1/ и языковые варианты.
Воспроизведение: Открыть настоящую карточку занятия Uydurma QA09 fəaliyyət, затем его страницу отзывов.
Ожидание: Заголовок явно называет занятие с языковым fallback.
Подтверждённый факт: На review page заголовок «Отзывы: Activity object (1)» во всех18cells, хотя name_az сохранено и настоящая карточка отображает название.
Проверенный источник/причина: src/catalog/controllers/typed_reviews.py:90; src/catalog/models/catalog_structure.py:71; target_name использует name_i18n либо str(target); Activity не имеет нужного name_i18n/__str__, унаследованные name_* не выбраны.
Конкретная область: Использовать действительное публичное имя Activity и существующий языковой fallback; сверить место/специалиста/мероприятие и отсутствие technical object IDs в пользовательском заголовке.
Ответственные границы/зависимости: django-reviewer + frontend-reviewer; canonical public presentation/fallback, не добавлять независимую локализацию.

Сначала воспроизведи на новом DJANGO_TESTING=1 изолированном DB/cache/media/private-media/email стенде с вымышленными данными и подготовь конкретный план. Реализацию выполняй только в согласованном scope, используя уже данную в новом чате авторизацию; не проси её повторно. Не меняй существующие assertions ради зелёного результата. После scoped исправления выполни meaningful regression checks и настоящий browser/reload RU/AZ/EN×360/390/768/1024/1280/1440; сохрани новый отчёт, exact commands/counts/exit codes, screenshots, candidate/live/ACL readback и NOT RUN. Не расширяй задачу на остальные findings. Без production credentials, внешних интеграций, commit/push/deploy.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SOCIAL-QA-08"></a>

#### PLAN SOCIAL-QA-08 · P2

SOCIAL-QA-08 — Отозванное приглашение оставляет пустую403страницу. ID: SOCIAL-QA-08.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-08.md](module09-2026-10-10-r1/findings/SOCIAL-QA-08.md), [docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-08.txt](module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-08.txt).

```text
KidsMap: PLAN SOCIAL-QA-08. ID scope: SOCIAL-QA-08. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-08.md, docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-08.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-08.md. Проверь текущие HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Старый QA09 — checklist, не свежий PASS.

Задача: исправить только SOCIAL-QA-08 «Отозванное приглашение оставляет пустую403страницу» (P2). Роль/URL: получатель приглашения; /ru/account/notifications/<id>/accept/.
Воспроизведение: Владелец отправляет приглашение через UI. Получатель оставляет inbox открытым; владелец отменяет приглашение. Получатель нажимает старую Accept.
Ожидание: Доступ не выдан; интерфейс объясняет устаревшее/отозванное приглашение и предлагает вернуться/обновить inbox.
Подтверждённый факт: 403 корректно запрещает выдачу прав, но body пустой, ссылок0; пользователь видит белую страницу. Native empty recipient case и БД CANCELLED/no grant подтверждены.
Проверенный источник/причина: src/catalog/controllers/workflow_notifications.py:63; Исключение stale/ValidationError преобразовано в HttpResponseForbidden() без content/template/messages.
Конкретная область: Обработать собственное stale/cancelled приглашение понятным AZ/RU/EN состоянием с возвратом в inbox, сохранив403/guard и отсутствие повторного grant. Чужой ID остаётся без информационной утечки.
Ответственные границы/зависимости: django-reviewer + frontend-reviewer + security-reviewer; не раскрывать чужое приглашение, не ослаблять проверки версии/владельца/email/expiry.

Сначала воспроизведи на новом DJANGO_TESTING=1 изолированном DB/cache/media/private-media/email стенде с вымышленными данными и подготовь конкретный план. Реализацию выполняй только в согласованном scope, используя уже данную в новом чате авторизацию; не проси её повторно. Не меняй существующие assertions ради зелёного результата. После scoped исправления выполни meaningful regression checks и настоящий browser/reload RU/AZ/EN×360/390/768/1024/1280/1440; сохрани новый отчёт, exact commands/counts/exit codes, screenshots, candidate/live/ACL readback и NOT RUN. Не расширяй задачу на остальные findings. Без production credentials, внешних интеграций, commit/push/deploy.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SOCIAL-QA-09"></a>

#### PLAN SOCIAL-QA-09 · P2

SOCIAL-QA-09 — Пагинация и сортировка ленты отзывов сбрасываются301. ID: SOCIAL-QA-09.

Источники: [docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-09.md](module09-2026-10-10-r1/findings/SOCIAL-QA-09.md), [docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-09.txt](module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-09.txt).

```text
KidsMap: PLAN SOCIAL-QA-09. ID scope: SOCIAL-QA-09. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-09.md, docs/qa/module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-09.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module09-2026-10-10-r1/findings/SOCIAL-QA-09.md. Проверь текущие HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Старый QA09 — checklist, не свежий PASS.

Задача: исправить только SOCIAL-QA-09 «Пагинация и сортировка ленты отзывов сбрасываются301» (P2). Роль/URL: гость/автор; /ru/place-reviews/?page=2 и ?sort=likes; AZ/EN variants.
Воспроизведение: Иметь29 approved reviews; нажать страницу2 либо выбрать «likes» в реальном select и применить.
Ожидание: Показана2страница с другими отзывами; выбранный sort сохраняется.
Подтверждённый факт: GET?page=2 получает301 Location на URL без query; browser возвращается к active page1 во всех18cells. Sort likes также301→popular во всех3языках. Site reviews control?page=2=200 и native pagination PASS.
Проверенный источник/причина: src/catalog/services/public_urls.py:12,28,81; src/catalog/middleware.py:84; src/catalog/controllers/place_reviews_controller.py:34; Allowlist содержит site_reviews:{sort,page}, но не place_reviews. PublicQueryParameterCanonicalMiddleware удаляет законные параметры до Paginator/sorting.
Конкретная область: Разрешить только реальные параметры sort/page для place_reviews в canonical query contract, сохранив удаление посторонних параметров. Native page1/2/3, сортировка, RU/AZ/EN, language switching/canonical/redirect и другие URL должны пройти свежую проверку.
Ответственные границы/зависимости: django-reviewer + seo-reviewer + frontend-reviewer; module11 query/canonical/language regressions.

Сначала воспроизведи на новом DJANGO_TESTING=1 изолированном DB/cache/media/private-media/email стенде с вымышленными данными и подготовь конкретный план. Реализацию выполняй только в согласованном scope, используя уже данную в новом чате авторизацию; не проси её повторно. Не меняй существующие assertions ради зелёного результата. После scoped исправления выполни meaningful regression checks и настоящий browser/reload RU/AZ/EN×360/390/768/1024/1280/1440; сохрани новый отчёт, exact commands/counts/exit codes, screenshots, candidate/live/ACL readback и NOT RUN. Не расширяй задачу на остальные findings. Без production credentials, внешних интеграций, commit/push/deploy.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m10"></a>

### 10. Настройки, разделы и общие страницы

SITE-QA-07 выполняется в [COMPILED-LOCALE-FRESHNESS](#repair-COMPILED-LOCALE-FRESHNESS), модуль 04.

<a id="repair-SITE-QA-01"></a>

#### PLAN SITE-QA-01 · P1

SITE-QA-01 — Staff без model permissions меняет глобальный логотип. ID: SITE-QA-01.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-01.md](module10-2026-10-10-r1/findings/SITE-QA-01.md), [docs/qa/module13-2026-10-11-r1/findings/SITE-QA-01-repair.txt](module13-2026-10-11-r1/findings/SITE-QA-01-repair.txt).

```text
KidsMap: PLAN SITE-QA-01. ID scope: SITE-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-01.md, docs/qa/module13-2026-10-11-r1/findings/SITE-QA-01-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в C:/kidsmap (на другом ПК сначала найди checkout). Прочитай AGENTS.md, канонические .agents, docs/qa/module13-2026-10-11-r1/REPORT.md и findings/SITE-QA-01.md в том же run. Задача: SITE-QA-01, SITE-QA-01 — Staff без model permissions меняет глобальный логотип, P1. Сохрани чужие изменения, active_run и стенды. Без commit/push/deploy/production.

Подтверждённый trigger: Staff actor has0 model permissions. Open global media editor, upload fictional PNG through its native chooser, reload and visit home.
Ожидание: 403 and no global media write.
Факт: Page200, upload200 and public logo changes; current synthetic stand only.
Свежие доказательства: docs/qa/module13-2026-10-11-r1/acl-native.result.txt; matrix.json; screenshots-manifest.json. Source refs: templates/MO, src/catalog/domain_admin/site.py.
Группа причины: GLOBAL-MEDIA-ACL. 

Сначала проверь текущий source и составь конкретный план исправления с файлами, зависимостями и meaningful regression проверками. Согласно audit scope реализацию выполняй только после согласования этого плана. Не меняй существующие assertions ради green. Применимые проверки: DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, внешние интеграции выключены. После согласованного исправления повтори реальный UI trigger, сохранение/reload и PC/mobile RU/AZ/EN; сохраняй candidate/live и ACL. Отдельно классифицируй source translation, generated assets, baseline и environment failures. Сохрани свежий отчёт, точные команды/counts/exit codes/screenshots и NOT RUN ограничения.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-02"></a>

#### PLAN SITE-QA-02 · P2

SITE-QA-02 — AZ-тексты «О проекте» и пустого каталога сохраняются, но не отображаются. ID: SITE-QA-02.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-02.md](module10-2026-10-10-r1/findings/SITE-QA-02.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-02-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-02-repair.txt).

```text
KidsMap: PLAN SITE-QA-02. ID scope: SITE-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-02.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-02-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-02.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-02 «AZ-тексты «О проекте» и пустого каталога сохраняются, но не отображаются», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Через админку сохранить разные QA10-маркеры RU/AZ/EN для about_text и empty_results_text. Reload показывает сохранённые AZ-значения. Открыть AZ about и каталог без совпадений на всех шести ширинах.
Ожидание: Вывод сохранённого AZ-текста; default только при пустом поле.
Аудит наблюдал: Во всех 6 AZ cells обе публичные страницы показывают захардкоженный default. RU/EN тексты выводятся. AZ перевод действительно сохранён, это не fallback.
Первопричина/гипотеза: Подтверждено: AZ-ветка шаблона стоит перед проверкой site_about_text/site_empty_results_text.
Область: Приоритет сохранённого локализованного значения над default для обоих шаблонов; сохранить языковые fallback правила.
Зависимости: SiteSettings i18n helpers/context; отдельные пустое/заполненное AZ и RU/EN regressions.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-03"></a>

#### PLAN SITE-QA-03 · P2

SITE-QA-03 — Редактируемый текст контактов не используется публичной страницей. ID: SITE-QA-03.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-03.md](module10-2026-10-10-r1/findings/SITE-QA-03.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-03-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-03-repair.txt).

```text
KidsMap: PLAN SITE-QA-03. ID scope: SITE-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-03.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-03-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-03.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-03 «Редактируемый текст контактов не используется публичной страницей», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Сохранить contacts_text_ru/az/en через админку, reload и затем публичные contacts в 18 cells.
Ожидание: Публичная страница выводит сохранённый текст соответствующего языка.
Аудит наблюдал: Ни один из 18 contacts display checks не находит сохранённый QA10-текст. Footer phone/email при этом обновляются и видны.
Первопричина/гипотеза: Подтверждено: context processor отдаёт site_contacts_text, но contacts.html не потребляет его.
Область: Связать текст настройки с публичным содержимым контактов; оставить phone/email/social отдельными полями.
Зависимости: Единый публичный text rendering и i18n contract; проверить HTML escaping и длинный текст.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-04"></a>

#### PLAN SITE-QA-04 · P2

SITE-QA-04 — Настройки CTA и placeholder главной игнорируются. ID: SITE-QA-04.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-04.md](module10-2026-10-10-r1/findings/SITE-QA-04.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-04-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-04-repair.txt).

```text
KidsMap: PLAN SITE-QA-04. ID scope: SITE-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-04.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-04-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-04.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-04 «Настройки CTA и placeholder главной игнорируются», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Сохранить разные home_cta_text_* и home_search_placeholder_* через UI. Reload админки, затем главная во всех 18 cells.
Ожидание: Сохранённые локализованные CTA и placeholder выводятся на главной.
Аудит наблюдал: По 18 FAIL на CTA и placeholder; вместо QA10-маркеров hardcoded тексты. Title/subtitle/search-label и декор реагируют на настройки.
Первопричина/гипотеза: Подтверждено: HomeController формирует hero_cta_text/hero_search_placeholder, шаблон использует literals вместо этих context values.
Область: Связать CTA/placeholder с context, сохранить defaults и выбранный язык без копирования fallback в сохранённый перевод.
Зависимости: HomeController trimming/default policy; 18 native cells после save/reload.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-05"></a>

#### PLAN SITE-QA-05 · P2

SITE-QA-05 — Загруженные hero PC/mobile главной не выводятся. ID: SITE-QA-05.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-05.md](module10-2026-10-10-r1/findings/SITE-QA-05.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-05-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-05-repair.txt).

```text
KidsMap: PLAN SITE-QA-05. ID scope: SITE-QA-05. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-05.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-05-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-05.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-05 «Загруженные hero PC/mobile главной не выводятся», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Загрузить вымышленные разные home_hero_image/home_hero_mobile_image через native file chooser. Reload подтверждает файлы. Открыть главную на mobile/PC; проверить DOM src/background и rendered screenshot.
Ожидание: Обозначенные в медиаредакторе PC/mobile изображения используются соответствующим публичным hero.
Аудит наблюдал: Оба файла сохраняются, но ни одна из 18 публичных cells не использует их. Главная остаётся со статическими фото.
Первопричина/гипотеза: Подтверждено для home hero: обновлённый шаблон не потребляет эти SiteSettings fields, несмотря на действующий редактор. Не утверждается, что все остальные image fields также не работают.
Область: Согласовать конкретно home hero image PC/mobile с текущей композицией и редактором. Перед изменением UI предложить точный план; не удалять поля или DB структуры по отсутствию references.
Зависимости: KidsMap UI design и product contract; no-image fallback, mobile/PC, reload/cache.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-06"></a>

#### PLAN SITE-QA-06 · P2

SITE-QA-06 — Файл PNG с неверным содержимым сохраняется и ломает публичный логотип. ID: SITE-QA-06.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-06.md](module10-2026-10-10-r1/findings/SITE-QA-06.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-06-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-06-repair.txt).

```text
KidsMap: PLAN SITE-QA-06. ID scope: SITE-QA-06. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-06.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-06-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-06.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-06 «Файл PNG с неверным содержимым сохраняется и ломает публичный логотип», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Через native file chooser отправить qa10-bad.png (MIME image/png, содержимое Synthetic invalid PNG). Reload медиахаба и главной.
Ожидание: Ошибка валидации и сохранность прежнего валидного изображения.
Аудит наблюдал: Ответ 200 success=true, FileField заменён. После reload admin/public img.complete=true и naturalWidth=0. После фиксации доказательства валидный logo восстановлен через UI.
Первопричина/гипотеза: Подтверждено: FileField и custom AJAX save не декодируют/не валидируют содержимое изображения до замены.
Область: Проверять содержимое/разрешённые форматы до сохранения, лимиты и безопасное замещение. Ошибка должна сохранять старый файл и честный UI.
Зависимости: Storage/file lifecycle, validation, SITE-QA-01 authorization; реальные HTTP/native chooser tests.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-08"></a>

#### PLAN SITE-QA-08 · P2

SITE-QA-08 — Мобильные формы общих настроек переполняют viewport. ID: SITE-QA-08.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-08.md](module10-2026-10-10-r1/findings/SITE-QA-08.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-08-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-08-repair.txt).

```text
KidsMap: PLAN SITE-QA-08. ID scope: SITE-QA-08. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-08.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-08-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-08.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-08 «Мобильные формы общих настроек переполняют viewport», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Открыть заполненные формы в RU/AZ/EN на 360/390. Проверить document.scrollWidth, bounding rects inputs/file-upload, screenshot.
Ожидание: Форма и поля помещаются в viewport без горизонтального скролла.
Аудит наблюдал: 26 FAIL cells. Пример RU 360: document/body width=611, input vTextField width=362, file-upload width≈543.7, right≈610.7.
Первопричина/гипотеза: Подтверждён DOM trigger: generic text/file controls шире доступного поля. Полный CSS cascade root ещё требует bounded inspection при repair; не доказана одна универсальная CSS строка.
Область: Responsive bounds для generic settings fieldsets/inputs/file controls и перенос длинных путей; не скрывать проблему overflow-x:hidden.
Зависимости: Frontend-admin/KidsMap UI rules; native filled/errors RU/AZ/EN 360/390 и desktop regression.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-09"></a>

#### PLAN SITE-QA-09 · P2

SITE-QA-09 — OFF мероприятий оставляет публичный direct URL legacy temporary Place. ID: SITE-QA-09.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-09.md](module10-2026-10-10-r1/findings/SITE-QA-09.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-09-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-09-repair.txt).

```text
KidsMap: PLAN SITE-QA-09. ID scope: SITE-QA-09. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-09.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-09-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-09.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-09 «OFF мероприятий оставляет публичный direct URL legacy temporary Place», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: На начальной вымышленной опубликованной temporary Place включить events OFF через settings UI. Каталог/map скрывают Place6; открыть его canonical URL RU/AZ/EN во всех ширинах. Вернуть ON.
Ожидание: Публичный direct URL также скрыт при OFF, как каталог и map.
Аудит наблюдал: Все 18 OFF direct checks получают 200; каталог/map корректно исключают ID6. ON снова показывает карточку. Данные объектов сохраняются.
Первопричина/гипотеза: Подтверждено: public detail использует published_place_queryset без events flag; strict catalog/map queryset исключает is_temporary при OFF.
Область: Единый flag/availability contract для legacy temporary detail без смешения OFF с unpublish/archive/delete. Не менять данные карточки для имитации скрытия.
Зависимости: Features/public queryset/canonical URL; map/catalog/direct + ON roundtrip, исторические legacy правила.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-10"></a>

#### PLAN SITE-QA-10 · P2

SITE-QA-10 — OFF мероприятий возвращает пустую 410 страницу. ID: SITE-QA-10.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-10.md](module10-2026-10-10-r1/findings/SITE-QA-10.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-10-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-10-repair.txt).

```text
KidsMap: PLAN SITE-QA-10. ID scope: SITE-QA-10. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-10.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-10-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-10.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-10 «OFF мероприятий возвращает пустую 410 страницу», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Выключить events section через native settings. Открыть list и event detail во всех 18 cells.
Ожидание: Читаемое локализованное сообщение с выходом к доступным разделам при корректном HTTP статусе.
Аудит наблюдал: 36 checks list/detail: HTTP410, bodyLength=0; rendered browser полностью пустой.
Первопричина/гипотеза: Подтверждено: early guards возвращают HttpResponseGone() без body/template.
Область: Локализованный rendered 410 response с навигацией, сохранить семантику disabled feature и отсутствие скрытых данных.
Зависимости: Shared error template/header/footer, three languages/mobile/PC; SITE-QA-09 separately.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-11"></a>

#### PLAN SITE-QA-11 · P3

SITE-QA-11 — Loading и удаление медиа захардкожены на русском. ID: SITE-QA-11.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-11.md](module10-2026-10-10-r1/findings/SITE-QA-11.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-11-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-11-repair.txt).

```text
KidsMap: PLAN SITE-QA-11. ID scope: SITE-QA-11. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-11.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-11-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-11.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-11 «Loading и удаление медиа захардкожены на русском», приоритет P3. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: EN/AZ: задержать/оборвать own upload через browser route, открыть delete confirmation. Проверить visible loading/title/buttons.
Ожидание: Состояния и действия на выбранном языке.
Аудит наблюдал: По 12 FAIL на loading и deletion title (AZ/EN ×6 widths): «Загрузка…», «Удалить изображение?» и русские actions. Нативный транспорт при этих проверках SIMULATED; текст реально rendered.
Первопричина/гипотеза: Подтверждено: literals в kidsmap_site_media.js передаются kmModal; это отдельная причина от SITE-QA-07 compiled gettext.
Область: Использовать существующий JS translation mechanism для этих состояний и ошибок, сохранить loading/disabled behaviour.
Зависимости: Admin frontend/localization; runtime .mo build отдельно по SITE-QA-07; loading/error/delete native checks.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-12"></a>

#### PLAN SITE-QA-12 · P3

SITE-QA-12 — DEBUG=False 404 не локализован и не содержит пути восстановления. ID: SITE-QA-12.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-12.md](module10-2026-10-10-r1/findings/SITE-QA-12.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-12-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-12-repair.txt).

```text
KidsMap: PLAN SITE-QA-12. ID scope: SITE-QA-12. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-12.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-12-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-12.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-12 «DEBUG=False 404 не локализован и не содержит пути восстановления», приоритет P3. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Открыть заведомо неизвестный URL на отдельном own DEBUG=False stand во всех 18 cells.
Ожидание: Читаемая общая ошибка на выбранном языке и ссылка домой/в каталог.
Аудит наблюдал: Дефолтный английский Not Found/Page not found для всех языков, 0 anchors. HTTP404 и отсутствие overflow корректны. DEBUG=True диагностические страницы исключены из findings.
Первопричина/гипотеза: Подтверждено на локальном DEBUG=False: используется default Django 404; проектный общий error rendering не применяется. Production reverse-proxy error page не исследован.
Область: Общий localized 404 для Django route miss с доступной навигацией, корректным статусом и без деталей внутренних URL.
Зависимости: URL/error handler + templates/locales, DEBUG=False tests; не менять proxy/production в этом repair.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-13"></a>

#### PLAN SITE-QA-13 · P2

SITE-QA-13 — Фокус диалога удаления медиа выходит за modal. ID: SITE-QA-13.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-13.md](module10-2026-10-10-r1/findings/SITE-QA-13.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-13-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-13-repair.txt).

```text
KidsMap: PLAN SITE-QA-13. ID scope: SITE-QA-13. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-13.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-13-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-13.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-13 «Фокус диалога удаления медиа выходит за modal», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Открыть удаление logo. Дождаться анимации. Tab несколько раз, Shift+Tab. Сверить activeElement и aria-modal dialog. Escape, проверить сохранность файла.
Ожидание: Начальный фокус внутри диалога, Tab/Shift+Tab циклически остаются в нём.
Аудит наблюдал: Фокус остаётся/возвращается на background delete button; forward Tab не находится внутри modal. Escape после завершения анимации корректно закрывает и не удаляет файл.
Первопричина/гипотеза: Гипотеза, не подтверждённая первопричина: взаимодействие initial focus/focus trap/других loaded admin handlers. Сам эффект фиксируется activeElement trace и native UI; требуется отдельное событие-by-событие исследование перед исправлением.
Область: Воспроизвести после bringToFront/ожидания, установить точную причину focus ownership. Исправить начальный фокус/trap/restore без изменения разрешений или удаления данных.
Зависимости: Unified notifications modal + loaded admin JS; Enter/Space/Tab/ShiftTab/Escape, all18 cells and other dialogs regression.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-14"></a>

#### PLAN SITE-QA-14 · P2

SITE-QA-14 — Несохранённый ввод settings теряется при обрыве POST. ID: SITE-QA-14.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-14.md](module10-2026-10-10-r1/findings/SITE-QA-14.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-14-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-14-repair.txt).

```text
KidsMap: PLAN SITE-QA-14. ID scope: SITE-QA-14. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-14.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-14-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-14.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-14 «Несохранённый ввод settings теряется при обрыве POST», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Заполнить footer_email новым вымышленным значением. Через browser route.abort оборвать native form POST до сервера. После browser error нажать Back. Сверить history и DB.
Ожидание: Старое значение DB сохраняется; введённое значение можно восстановить и повторить сохранение без ложного успеха.
Аудит наблюдал: DB сохраняет старый edited10@example.invalid, ложного save нет. Chromium показывает chrome-error, Back ведёт на account/profile (admin form GET заменён в history), введённый текст отсутствует. Повторный независимый контекст подтверждает результат.
Первопричина/гипотеза: Подтверждён механизм history на simulated transport; SSR form navigation без draft persistence/recovery. Реальный сетевой разрыв/серверный отказ не выполнялся, другие браузеры не проверены.
Область: Предложить минимальный план восстановления ввода/повторной отправки для settings SSR form. Не обещать save до ответа сервера; исключить secret fields из возможного локального draft.
Зависимости: Frontend-admin form lifecycle/cache/history; injected abort + reload/Back and successful-save cleanup; реальный disconnect отдельная проверка.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SITE-QA-15"></a>

#### PLAN SITE-QA-15 · P2

SITE-QA-15 — Две вкладки настроек молча теряют сохранённое изменение. ID: SITE-QA-15.

Источники: [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-15.md](module10-2026-10-10-r1/findings/SITE-QA-15.md), [docs/qa/module10-2026-10-10-r1/findings/SITE-QA-15-repair.txt](module10-2026-10-10-r1/findings/SITE-QA-15-repair.txt).

```text
KidsMap: PLAN SITE-QA-15. ID scope: SITE-QA-15. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module10-2026-10-10-r1/findings/SITE-QA-15.md, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-15-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/SITE-QA-15.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: SITE-QA-15 «Две вкладки настроек молча теряют сохранённое изменение», приоритет P2. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: Открыть footer form одновременно в A/B. В A изменить только телефон на +994000000013 и сохранить. Не перезагружая B, изменить только email на tabB10@example.invalid и сохранить. Reload обеих вкладок и read-only DB check.
Ожидание: Изменение email не стирает уже сохранённый другой телефон; stale form получает понятный conflict/reload или сохраняет только собственный intent.
Аудит наблюдал: A сохраняет новый телефон. После B email обновлён, телефон возвращается к +994000000011 из старой формы. Errors отсутствуют, reload обеих вкладок подтверждает потерю A. После evidence прежние вымышленные контакты восстановлены native POST; отдельно native dblclick сохраняет ожидаемое значение.
Первопричина/гипотеза: Подтверждён механизм: обычный полный ModelForm POST stale fields; updated_at readonly и не используется для version/conflict check. Сервер видит старое значение телефона как новое намерение B и сохраняет его. Product choice merge vs conflict требует плана, сам silent lost update воспроизведён.
Область: Установить intent/version policy для SiteSettings section forms: явный conflict с сохранением ввода либо корректное слияние непересекающихся изменений. Не реализовывать blind last-write merge по всей singleton модели.
Зависимости: Django model/admin/forms + shared error UX; separate fields and same-field conflict, double submit, reload/cache; no assertion rewrites.

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m11"></a>

### 11. SEO, языковые URL и redirects

<a id="repair-SEO-QA-01"></a>

#### PLAN SEO-QA-01 · P2

SEO-QA-01 · P2 · Карточки используют общее описание каталога в OG/Twitter. ID: SEO-QA-01.

Источники: [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-01.md](module11-2026-10-11-r1/findings/SEO-QA-01.md), [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-01-repair.txt](module11-2026-10-11-r1/findings/SEO-QA-01-repair.txt).

```text
KidsMap: PLAN SEO-QA-01. ID scope: SEO-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-01.md, docs/qa/module11-2026-10-11-r1/findings/SEO-QA-01-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md и каноническую .agents. Исправь только SEO-QA-01: Карточки используют общее описание каталога в OG/Twitter.

Исходное подтверждение: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-01.md, source-extra.md и свежие evidence. Это dirty WORKTREE на HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6; сначала зафиксируй текущий checkout/HEAD/branch/active_run и проверь drift. Сохрани чужие изменения, active_run и стенды. Исторический отчёт — repro/checklist, не новая проверка.

Repro: Открыть любую seeded опубликованную карточку; сравнить meta description и OG/Twitter description; выполнить reload и собственный локальный preview.
Ожидание: Social descriptions описывают именно текущую карточку и соответствуют её approved описанию.
Подтверждённый факт: meta description индивидуальный; og:description и twitter:description — общий текст каталога.90 native failures включают это на 5entity×18cells.
Область согласованного исправления: Публичные detail templates/shared SEO context; только approved public descriptions, fallback/escaping и privacy.
Причина/source: base.html:30/35 содержит отдельные блоки meta_description_og/twitter_description; detail templates переопределяют только meta_description. Причина подтверждена source-extra.md; файлы совпадают с HEAD.
Зависимости: seo-reviewer, frontend-reviewer; зависимости SEO-QA-02/03 имеют смежные template blocks.

Сначала представь конкретный bounded план согласно текущим AGENTS; при реализации сохраняй публичные/приватные границы и остальные контракты. Не исправляй остальные findings в этом scope, не ослабляй существующие assertions. Проверки только DJANGO_TESTING=1, новый изолированный DB/cache/media/private-media/email, вымышленные данные, без внешних интеграций/production credentials. Без commit/push/deploy/production.

Свежая проверка после изменения: существующие релевантные тесты, негативные private/disabled состояния, настоящий native UI→save→reload для применимой мутации, RU/AZ/EN desktop/mobile, HTTP/head отдельно от rendered browser. Для social preview используй собственный локальный preview без внешних ботов; indexing/Search Console/IndexNow не вызывай. Сохрани новый отчёт/evidence/screenshots, counts/exit codes, WORKTREE/runtime соответствие и NOT RUN ограничения. Не утверждай production эффект без его проверки.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SEO-QA-02"></a>

#### PLAN SEO-QA-02 · P2

SEO-QA-02 · P2 · Social title специалиста остаётся KidsMap. ID: SEO-QA-02.

Источники: [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-02.md](module11-2026-10-11-r1/findings/SEO-QA-02.md), [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-02-repair.txt](module11-2026-10-11-r1/findings/SEO-QA-02-repair.txt).

```text
KidsMap: PLAN SEO-QA-02. ID scope: SEO-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-02.md, docs/qa/module11-2026-10-11-r1/findings/SEO-QA-02-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md и каноническую .agents. Исправь только SEO-QA-02: Social title специалиста остаётся KidsMap.

Исходное подтверждение: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-02.md, source-extra.md и свежие evidence. Это dirty WORKTREE на HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6; сначала зафиксируй текущий checkout/HEAD/branch/active_run и проверь drift. Сохрани чужие изменения, active_run и стенды. Исторический отчёт — repro/checklist, не новая проверка.

Repro: Переименовать специалиста через админку, подтвердить dialog, reload; открыть карточку и локальный preview.
Ожидание: og:title/twitter:title содержат идентичность опубликованного специалиста.
Подтверждённый факт: title/H1 — Uydurma QA11 specialist verified rename2; og:title и twitter:title — KidsMap.
Область согласованного исправления: Specialist detail social title blocks, общий формат title и approved публичный текст.
Причина/source: specialist_detail.html override title/meta_description, но не og_title/twitter_title; base.html defaults.15 relevant source files совпадают с HEAD.
Зависимости: seo-reviewer/frontend-reviewer; согласовать с SEO-QA-01.

Сначала представь конкретный bounded план согласно текущим AGENTS; при реализации сохраняй публичные/приватные границы и остальные контракты. Не исправляй остальные findings в этом scope, не ослабляй существующие assertions. Проверки только DJANGO_TESTING=1, новый изолированный DB/cache/media/private-media/email, вымышленные данные, без внешних интеграций/production credentials. Без commit/push/deploy/production.

Свежая проверка после изменения: существующие релевантные тесты, негативные private/disabled состояния, настоящий native UI→save→reload для применимой мутации, RU/AZ/EN desktop/mobile, HTTP/head отдельно от rendered browser. Для social preview используй собственный локальный preview без внешних ботов; indexing/Search Console/IndexNow не вызывай. Сохрани новый отчёт/evidence/screenshots, counts/exit codes, WORKTREE/runtime соответствие и NOT RUN ограничения. Не утверждай production эффект без его проверки.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SEO-QA-03"></a>

#### PLAN SEO-QA-03 · P2

SEO-QA-03 · P2 · Фото мероприятия отсутствует в social image metadata. ID: SEO-QA-03.

Источники: [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-03.md](module11-2026-10-11-r1/findings/SEO-QA-03.md), [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-03-repair.txt](module11-2026-10-11-r1/findings/SEO-QA-03-repair.txt).

```text
KidsMap: PLAN SEO-QA-03. ID scope: SEO-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-03.md, docs/qa/module11-2026-10-11-r1/findings/SEO-QA-03-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md и каноническую .agents. Исправь только SEO-QA-03: Фото мероприятия отсутствует в social image metadata.

Исходное подтверждение: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-03.md, source-extra.md и свежие evidence. Это dirty WORKTREE на HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6; сначала зафиксируй текущий checkout/HEAD/branch/active_run и проверь drift. Сохрани чужие изменения, active_run и стенды. Исторический отчёт — repro/checklist, не новая проверка.

Repro: Через admin Event1 загрузить собственный fixture.png, заполнить телефон/организатора; Save→reload; открыть публичную карточку и её head.
Ожидание: При наличии опубликованного главного фото OG/Twitter используют его абсолютный public URL.
Подтверждённый факт: Карточка показывает /media/events/fixture.png, изображение loaded=true; OG/Twitter image остаётся /static/img/logo.svg.18 native cells подтверждены.
Область согласованного исправления: Event template/head context, валидное public photo и fallback при отсутствии фото.
Причина/source: event_detail.html не override og_image/twitter_image; base.html:31/36 берёт site logo. Place уже override оба фото-блока: ранняя гипотеза про Place Twitterlogo исключена.
Зависимости: seo-reviewer/frontend-reviewer; SEO-QA-01 смежный template.

Сначала представь конкретный bounded план согласно текущим AGENTS; при реализации сохраняй публичные/приватные границы и остальные контракты. Не исправляй остальные findings в этом scope, не ослабляй существующие assertions. Проверки только DJANGO_TESTING=1, новый изолированный DB/cache/media/private-media/email, вымышленные данные, без внешних интеграций/production credentials. Без commit/push/deploy/production.

Свежая проверка после изменения: существующие релевантные тесты, негативные private/disabled состояния, настоящий native UI→save→reload для применимой мутации, RU/AZ/EN desktop/mobile, HTTP/head отдельно от rendered browser. Для social preview используй собственный локальный preview без внешних ботов; indexing/Search Console/IndexNow не вызывай. Сохрани новый отчёт/evidence/screenshots, counts/exit codes, WORKTREE/runtime соответствие и NOT RUN ограничения. Не утверждай production эффект без его проверки.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SEO-QA-04"></a>

#### PLAN SEO-QA-04 · P2

SEO-QA-04 · P2 · Публичное мероприятие не включается в sitemap. ID: SEO-QA-04.

Источники: [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-04.md](module11-2026-10-11-r1/findings/SEO-QA-04.md), [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-04-repair.txt](module11-2026-10-11-r1/findings/SEO-QA-04-repair.txt).

```text
KidsMap: PLAN SEO-QA-04. ID scope: SEO-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-04.md, docs/qa/module11-2026-10-11-r1/findings/SEO-QA-04-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md и каноническую .agents. Исправь только SEO-QA-04: Публичное мероприятие не включается в sitemap.

Исходное подтверждение: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-04.md, source-extra.md и свежие evidence. Это dirty WORKTREE на HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6; сначала зафиксируй текущий checkout/HEAD/branch/active_run и проверь drift. Сохрани чужие изменения, active_run и стенды. Исторический отчёт — repro/checklist, не новая проверка.

Repro: Включить события через admin; сохранить полноценное fictional Event через UI; GET AZ/RU/EN детали и sitemap; повторить после OFF→ON.
Ожидание: Публичное индексируемое Event получает sitemap entry по согласованному visibility/language contract.
Подтверждённый факт: Опубликованный Event GET200/index, JSON-LD Event присутствует; все 3 EventURL отсутствуют в свежих initial/final XML. Hidden/disabled entries не попадают.
Область согласованного исправления: Event sitemap + регистрация; public predicate, approved даты/языки, flags.
Причина/source: src/config/urls.py:21 sitemap registry не содержит EventSitemap; current sitemaps.py Event класс не подключён.
Зависимости: seo-reviewer/django-reviewer; интеграционные тесты visibility.

Сначала представь конкретный bounded план согласно текущим AGENTS; при реализации сохраняй публичные/приватные границы и остальные контракты. Не исправляй остальные findings в этом scope, не ослабляй существующие assertions. Проверки только DJANGO_TESTING=1, новый изолированный DB/cache/media/private-media/email, вымышленные данные, без внешних интеграций/production credentials. Без commit/push/deploy/production.

Свежая проверка после изменения: существующие релевантные тесты, негативные private/disabled состояния, настоящий native UI→save→reload для применимой мутации, RU/AZ/EN desktop/mobile, HTTP/head отдельно от rendered browser. Для social preview используй собственный локальный preview без внешних ботов; indexing/Search Console/IndexNow не вызывай. Сохрани новый отчёт/evidence/screenshots, counts/exit codes, WORKTREE/runtime соответствие и NOT RUN ограничения. Не утверждай production эффект без его проверки.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SEO-QA-05"></a>

#### PLAN SEO-QA-05 · P2

SEO-QA-05 · P2 · Редактирование slug специалиста превращает старый URL в 404. ID: SEO-QA-05.

Источники: [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-05.md](module11-2026-10-11-r1/findings/SEO-QA-05.md), [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-05-repair.txt](module11-2026-10-11-r1/findings/SEO-QA-05-repair.txt).

```text
KidsMap: PLAN SEO-QA-05. ID scope: SEO-QA-05. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-05.md, docs/qa/module11-2026-10-11-r1/findings/SEO-QA-05-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md и каноническую .agents. Исправь только SEO-QA-05: Редактирование slug специалиста превращает старый URL в 404.

Исходное подтверждение: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-05.md, source-extra.md и свежие evidence. Это dirty WORKTREE на HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6; сначала зафиксируй текущий checkout/HEAD/branch/active_run и проверь drift. Сохрани чужие изменения, active_run и стенды. Исторический отчёт — repro/checklist, не новая проверка.

Repro: В admin Specialist1 изменить exposed slug; подтвердить штатный dialog; save→reload; открыть новый и предыдущий URL во всех 3 языках.
Ожидание: Существующая публичная ссылка сохраняется либо получает permanent redirect к текущей идентичности без loop и приватного раскрытия.
Подтверждённый факт: Новый URL200 и canonical новый; старый 404, Location отсутствует во всех 3 языках. Обычные 2 name rename до slug edit сохраняли старый URL.
Область согласованного исправления: Политика стабильного specialist URL: immutable slug либо alias/history с 301 и public visibility guard; минимальные изменения, migrations только если необходимы согласованному дизайну.
Причина/source: admin.py exposed slug; Specialist slug-only lookup views.py:2881 точный и alias resolver отсутствует. Модель генерирует slug только при пустом значении. Source соответствует HEAD.
Зависимости: seo-reviewer/django-reviewer/database-reviewer; URL policy, uniqueness, hidden states.

Сначала представь конкретный bounded план согласно текущим AGENTS; при реализации сохраняй публичные/приватные границы и остальные контракты. Не исправляй остальные findings в этом scope, не ослабляй существующие assertions. Проверки только DJANGO_TESTING=1, новый изолированный DB/cache/media/private-media/email, вымышленные данные, без внешних интеграций/production credentials. Без commit/push/deploy/production.

Свежая проверка после изменения: существующие релевантные тесты, негативные private/disabled состояния, настоящий native UI→save→reload для применимой мутации, RU/AZ/EN desktop/mobile, HTTP/head отдельно от rendered browser. Для social preview используй собственный локальный preview без внешних ботов; indexing/Search Console/IndexNow не вызывай. Сохрани новый отчёт/evidence/screenshots, counts/exit codes, WORKTREE/runtime соответствие и NOT RUN ограничения. Не утверждай production эффект без его проверки.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SEO-QA-06"></a>

#### PLAN SEO-QA-06 · P2

SEO-QA-06 · P2 · Редактор «Контент и SEO» возвращает 500. ID: SEO-QA-06.

Источники: [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-06.md](module11-2026-10-11-r1/findings/SEO-QA-06.md), [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-06-repair.txt](module11-2026-10-11-r1/findings/SEO-QA-06-repair.txt).

```text
KidsMap: PLAN SEO-QA-06. ID scope: SEO-QA-06. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-06.md, docs/qa/module11-2026-10-11-r1/findings/SEO-QA-06-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md и каноническую .agents. Исправь только SEO-QA-06: Редактор «Контент и SEO» возвращает 500.

Исходное подтверждение: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-06.md, source-extra.md и свежие evidence. Это dirty WORKTREE на HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6; сначала зафиксируй текущий checkout/HEAD/branch/active_run и проверь drift. Сохрани чужие изменения, active_run и стенды. Исторический отчёт — repro/checklist, не новая проверка.

Repro: Войти synthetic superuser; открыть singleton editor в трёх языках; повторить DEBUGFalse в 6 ширинах.
Ожидание: Редактор открывается и позволяет native save/reload SEO landing config.
Подтверждённый факт: HTTP500; DEBUGTrue диагностика __str__ returned non-string (type __proxy__); DEBUGFalse native error18cells. Landing rename/repeated rename зависимо NOT RUN.
Область согласованного исправления: CatalogContentSettings.__str__ Python string contract и bounded native/admin regression.
Причина/source: models/site.py:10 gettext_lazy; CatalogContentSettings.__str__ :784–785 возвращает proxy; Django6.0.2 options.py:1911 вызывает str(obj). HEAD+WORKTREE source одинаковы.
Зависимости: django-reviewer/frontend-admin; дальше native landing edit/rename audit.

Сначала представь конкретный bounded план согласно текущим AGENTS; при реализации сохраняй публичные/приватные границы и остальные контракты. Не исправляй остальные findings в этом scope, не ослабляй существующие assertions. Проверки только DJANGO_TESTING=1, новый изолированный DB/cache/media/private-media/email, вымышленные данные, без внешних интеграций/production credentials. Без commit/push/deploy/production.

Свежая проверка после изменения: существующие релевантные тесты, негативные private/disabled состояния, настоящий native UI→save→reload для применимой мутации, RU/AZ/EN desktop/mobile, HTTP/head отдельно от rendered browser. Для social preview используй собственный локальный preview без внешних ботов; indexing/Search Console/IndexNow не вызывай. Сохрани новый отчёт/evidence/screenshots, counts/exit codes, WORKTREE/runtime соответствие и NOT RUN ограничения. Не утверждай production эффект без его проверки.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-SEO-QA-07"></a>

#### PLAN SEO-QA-07 · P3

SEO-QA-07 · P3 · HEAD организаций и занятий возвращает 405 при GET200. ID: SEO-QA-07.

Источники: [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-07.md](module11-2026-10-11-r1/findings/SEO-QA-07.md), [docs/qa/module11-2026-10-11-r1/findings/SEO-QA-07-repair.txt](module11-2026-10-11-r1/findings/SEO-QA-07-repair.txt).

```text
KidsMap: PLAN SEO-QA-07. ID scope: SEO-QA-07. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-07.md, docs/qa/module11-2026-10-11-r1/findings/SEO-QA-07-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом корне KidsMap. Прочитай AGENTS.md и каноническую .agents. Исправь только SEO-QA-07: HEAD организаций и занятий возвращает 405 при GET200.

Исходное подтверждение: docs/qa/module11-2026-10-11-r1/findings/SEO-QA-07.md, source-extra.md и свежие evidence. Это dirty WORKTREE на HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6; сначала зафиксируй текущий checkout/HEAD/branch/active_run и проверь drift. Сохрани чужие изменения, active_run и стенды. Исторический отчёт — repro/checklist, не новая проверка.

Repro: GET текущий public URL; HEAD тот же URL без params; повторить после rename/detach.
Ожидание: HEAD публичного GET ресурса поддерживается, сохраняет status/SEO headers и не возвращает тело.
Подтверждённый факт: GET200; HEAD405, Allow GET, во всех 3 языках для 2 типов. Свежий final повтор 6FAIL.
Область согласованного исправления: Public Organization/Activity HTTP method decorators/headers; existing visibility/privacy guards.
Причина/source: controllers/public_details.py:17/179 @require_GET допускает GET и отклоняет HEAD. HEAD check unchanged; privacy guard GET работает.
Зависимости: django-reviewer/seo-reviewer; no DB migration needed.

Сначала представь конкретный bounded план согласно текущим AGENTS; при реализации сохраняй публичные/приватные границы и остальные контракты. Не исправляй остальные findings в этом scope, не ослабляй существующие assertions. Проверки только DJANGO_TESTING=1, новый изолированный DB/cache/media/private-media/email, вымышленные данные, без внешних интеграций/production credentials. Без commit/push/deploy/production.

Свежая проверка после изменения: существующие релевантные тесты, негативные private/disabled состояния, настоящий native UI→save→reload для применимой мутации, RU/AZ/EN desktop/mobile, HTTP/head отдельно от rendered browser. Для social preview используй собственный локальный preview без внешних ботов; indexing/Search Console/IndexNow не вызывай. Сохрани новый отчёт/evidence/screenshots, counts/exit codes, WORKTREE/runtime соответствие и NOT RUN ограничения. Не утверждай production эффект без его проверки.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m12"></a>

### 12. Просмотры, счётчики и аналитика

<a id="repair-ANALYTICS-QA-01"></a>

#### PLAN ANALYTICS-QA-01 · P2

ANALYTICS-QA-01 — Staff без model permission читает общую статистику. ID: ANALYTICS-QA-01.

Источники: [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-01.md](module12-2026-10-11-r1/findings/ANALYTICS-QA-01.md), [docs/qa/module13-2026-10-11-r1/findings/ANALYTICS-QA-01-repair.txt](module13-2026-10-11-r1/findings/ANALYTICS-QA-01-repair.txt).

```text
KidsMap: PLAN ANALYTICS-QA-01. ID scope: ANALYTICS-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-01.md, docs/qa/module13-2026-10-11-r1/findings/ANALYTICS-QA-01-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в C:/kidsmap (на другом ПК сначала найди checkout). Прочитай AGENTS.md, канонические .agents, docs/qa/module13-2026-10-11-r1/REPORT.md и findings/ANALYTICS-QA-01.md в том же run. Задача: ANALYTICS-QA-01, ANALYTICS-QA-01 — Staff без model permission читает общую статистику, P2. Сохрани чужие изменения, active_run и стенды. Без commit/push/deploy/production.

Подтверждённый trigger: Same permissionless staff opens site analytics.
Ожидание: Model-authorized access only;403.
Факт: 200 with global analytics surface.
Свежие доказательства: docs/qa/module13-2026-10-11-r1/acl-native.result.txt; matrix.json; screenshots-manifest.json. Source refs: src/catalog/domain_admin/site.py.
Группа причины: GLOBAL-ANALYTICS-ACL. 

Сначала проверь текущий source и составь конкретный план исправления с файлами, зависимостями и meaningful regression проверками. Согласно audit scope реализацию выполняй только после согласования этого плана. Не меняй существующие assertions ради green. Применимые проверки: DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, внешние интеграции выключены. После согласованного исправления повтори реальный UI trigger, сохранение/reload и PC/mobile RU/AZ/EN; сохраняй candidate/live и ACL. Отдельно классифицируй source translation, generated assets, baseline и environment failures. Сохрани свежий отчёт, точные команды/counts/exit codes/screenshots и NOT RUN ограничения.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ANALYTICS-QA-02"></a>

#### PLAN ANALYTICS-QA-02 · P2

ANALYTICS-QA-02 — Событие принимается для активной приватной карточки. ID: ANALYTICS-QA-02.

Источники: [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-02.md](module12-2026-10-11-r1/findings/ANALYTICS-QA-02.md), [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-02-repair.txt](module12-2026-10-11-r1/findings/ANALYTICS-QA-02-repair.txt).

```text
KidsMap: PLAN ANALYTICS-QA-02. ID scope: ANALYTICS-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-02.md, docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-02-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только ANALYTICS-QA-02: Событие принимается для активной приватной карточки в KidsMap. Работай в фактическом корне checkout; прочитай AGENTS.md, .agents/README.md, registry, canonical role, source-of-truth и engineering/audit contracts. Сохрани чужой dirty WORKTREE, active_run и стенды; зафиксируй HEAD/branch и actual runtime. Отчёт: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-02.md.

Воспроизведение: POST phone_click с place_id активного draft2 или archived4. Нативный same-origin порт сначала блокируется; независимый тест и узкий SIMULATED port-header proxy доходят до business validator.
Ожидание: Отказ, delta событий0 для непубличной карточки.
Факт: 200 {ok:true}, delta+1; contact_actions приватного объекта увеличивается. Ни контакт, ни private content в ответе не раскрываются.
Источник: src/catalog/repositories/tracking_repositories.py:12; первопричина: find_active_for_event ограничивает active/deleted, не publication/public visibility.

Конкретная область исправления: Используй существующий shared public-visibility contract при разрешении analytics subject IDs. Проверь published/draft/pending/rejected/archived/inactive/deleted/foreign known IDs, delta0 при отказе; публичный чужой объект может легитимно получать гостевое событие.
Зависимости и владелец: django-reviewer + analytics-reviewer; shared public visibility policy, dependency03 for native port stand.

Сначала подготовь конкретный план и regression evidence, затем действуй в пределах явно разрешённой пользователем области. Соблюдай канонические инструкции о согласовании implementation scope. Тесты только DJANGO_TESTING=1, свежие отдельные DB/cache/media/private-media/email, вымышленные данные; внешние GA/Google/OAuth/Maps выключить. Не менять существующие assertions радиgreen, не использовать ORM для проверяемых UI-переходов. Не commit/push/deploy и не обращаться к production.

Приёмка: функциональный before/after по серверному контракту, настоящий UI/save/reload где применимо, RU/AZ/EN×360/390/768/1024/1280/1440, доступный focus/keyboard/empty/error. Сохрани новый отчёт/скриншоты/commands/counts/exit, различи реальные проверки и SIMULATED adapters/NOT RUN. Объясни пределы исправления и чужие неизменённые файлы.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ANALYTICS-QA-03"></a>

#### PLAN ANALYTICS-QA-03 · P2

ANALYTICS-QA-03 — Легитимный Origin с портом отклонён. ID: ANALYTICS-QA-03.

Источники: [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-03.md](module12-2026-10-11-r1/findings/ANALYTICS-QA-03.md), [docs/qa/module13-2026-10-11-r1/findings/ANALYTICS-QA-03-repair.txt](module13-2026-10-11-r1/findings/ANALYTICS-QA-03-repair.txt).

```text
KidsMap: PLAN ANALYTICS-QA-03. ID scope: ANALYTICS-QA-03. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-03.md, docs/qa/module13-2026-10-11-r1/findings/ANALYTICS-QA-03-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в C:/kidsmap (на другом ПК сначала найди checkout). Прочитай AGENTS.md, канонические .agents, docs/qa/module13-2026-10-11-r1/REPORT.md и findings/ANALYTICS-QA-03.md в том же run. Задача: ANALYTICS-QA-03, ANALYTICS-QA-03 — Легитимный Origin с портом отклонён, P2. Сохрани чужие изменения, active_run и стенды. Без commit/push/deploy/production.

Подтверждённый trigger: Open fictional ready Place1 on localhost:8831, reveal phone and invoke native tracked phone action.
Ожидание: Accepted legitimate same-origin event;200 with documented delta.
Факт: Native request returns403. No Origin proxy/adapter applied; rejected delta cannot establish a recorded click.
Свежие доказательства: docs/qa/module13-2026-10-11-r1/redirect-counters.result.txt; matrix.json; screenshots-manifest.json. Source refs: src/catalog/views.py.
Группа причины: ANALYTICS-ORIGIN-PORT. 

Сначала проверь текущий source и составь конкретный план исправления с файлами, зависимостями и meaningful regression проверками. Согласно audit scope реализацию выполняй только после согласования этого плана. Не меняй существующие assertions ради green. Применимые проверки: DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, внешние интеграции выключены. После согласованного исправления повтори реальный UI trigger, сохранение/reload и PC/mobile RU/AZ/EN; сохраняй candidate/live и ACL. Отдельно классифицируй source translation, generated assets, baseline и environment failures. Сохрани свежий отчёт, точные команды/counts/exit codes/screenshots и NOT RUN ограничения.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ANALYTICS-QA-04"></a>

#### PLAN ANALYTICS-QA-04 · P2

ANALYTICS-QA-04 — Период90 использует годовые GA KPI. ID: ANALYTICS-QA-04.

Источники: [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-04.md](module12-2026-10-11-r1/findings/ANALYTICS-QA-04.md), [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-04-repair.txt](module12-2026-10-11-r1/findings/ANALYTICS-QA-04-repair.txt).

```text
KidsMap: PLAN ANALYTICS-QA-04. ID scope: ANALYTICS-QA-04. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-04.md, docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-04-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только ANALYTICS-QA-04: Период90 использует годовые GA KPI в KidsMap. Работай в фактическом корне checkout; прочитай AGENTS.md, .agents/README.md, registry, canonical role, source-of-truth и engineering/audit contracts. Сохрани чужой dirty WORKTREE, active_run и стенды; зафиксируй HEAD/branch и actual runtime. Отчёт: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-04.md.

Воспроизведение: Выбрать90дней. В SIMULATED GA snapshot задать отличающиеся month/year/quarter числа; читать native KPI.
Ожидание: KPI относятся к выбранным90дням.
Факт: На кнопке90; KPI3650/3651/3652 из year. Own assertion quarter92 vs year367 FAIL. Chart/table отдельно честно подписаны30дней.
Источник: src/catalog/services/admin_analytics.py:37; первопричина: _ga_period_key(90)→year; Reporting PERIODS.year=364daysAgo.

Конкретная область исправления: Согласуй диапазон KPI с90дней selector; сохрани явный фиксированный30дней contract chart/tables либо отдельно согласуй его изменение. Проверь7/30/90/365, invalid fallback, inclusive calendar endpoints/timezone, partial GA failure; только mocked reports без реальных запросов.
Зависимости и владелец: analytics-reviewer + django-reviewer; GA report range contract, timezone property UNKNOWN.

Сначала подготовь конкретный план и regression evidence, затем действуй в пределах явно разрешённой пользователем области. Соблюдай канонические инструкции о согласовании implementation scope. Тесты только DJANGO_TESTING=1, свежие отдельные DB/cache/media/private-media/email, вымышленные данные; внешние GA/Google/OAuth/Maps выключить. Не менять существующие assertions радиgreen, не использовать ORM для проверяемых UI-переходов. Не commit/push/deploy и не обращаться к production.

Приёмка: функциональный before/after по серверному контракту, настоящий UI/save/reload где применимо, RU/AZ/EN×360/390/768/1024/1280/1440, доступный focus/keyboard/empty/error. Сохрани новый отчёт/скриншоты/commands/counts/exit, различи реальные проверки и SIMULATED adapters/NOT RUN. Объясни пределы исправления и чужие неизменённые файлы.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ANALYTICS-QA-05"></a>

#### PLAN ANALYTICS-QA-05 · P2

ANALYTICS-QA-05 — GA unavailable/error показаны как нулевая аудитория. ID: ANALYTICS-QA-05.

Источники: [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-05.md](module12-2026-10-11-r1/findings/ANALYTICS-QA-05.md), [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-05-repair.txt](module12-2026-10-11-r1/findings/ANALYTICS-QA-05-repair.txt).

```text
KidsMap: PLAN ANALYTICS-QA-05. ID scope: ANALYTICS-QA-05. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-05.md, docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-05-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только ANALYTICS-QA-05: GA unavailable/error показаны как нулевая аудитория в KidsMap. Работай в фактическом корне checkout; прочитай AGENTS.md, .agents/README.md, registry, canonical role, source-of-truth и engineering/audit contracts. Сохрани чужой dirty WORKTREE, active_run и стенды; зафиксируй HEAD/branch и actual runtime. Отчёт: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-05.md.

Воспроизведение: Открыть реальный локальный dashboard с обоими GA identifiers пустыми; затем SIMULATED report backend error.
Ожидание: Явное unavailable/error состояние; не подменять его аудиторией0 и успешным updated timestamp.
Факт: Три KPI0 и «Обновлено сегодня»; ga4.error не показан. Повторено18cells, error adapter явно SIMULATED.
Источник: templates/admin/catalog/site_analytics.html:24; первопричина: Snapshot хранит enabled/connected/error, template их не использует; kpi default0.

Конкретная область исправления: Покажи disabled/error/partial/empty/loaded состояния по GA snapshot contract. Нули только при подтверждённом успешном пустом отчёте, updated timestamp отражает успешную загрузку. Дай доступную ошибку и повтор; RU/AZ/EN и шесть widths, без credentials details.
Зависимости и владелец: analytics-reviewer/frontend-admin; dependency04 period semantics.

Сначала подготовь конкретный план и regression evidence, затем действуй в пределах явно разрешённой пользователем области. Соблюдай канонические инструкции о согласовании implementation scope. Тесты только DJANGO_TESTING=1, свежие отдельные DB/cache/media/private-media/email, вымышленные данные; внешние GA/Google/OAuth/Maps выключить. Не менять существующие assertions радиgreen, не использовать ORM для проверяемых UI-переходов. Не commit/push/deploy и не обращаться к production.

Приёмка: функциональный before/after по серверному контракту, настоящий UI/save/reload где применимо, RU/AZ/EN×360/390/768/1024/1280/1440, доступный focus/keyboard/empty/error. Сохрани новый отчёт/скриншоты/commands/counts/exit, различи реальные проверки и SIMULATED adapters/NOT RUN. Объясни пределы исправления и чужие неизменённые файлы.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ANALYTICS-QA-06"></a>

#### PLAN ANALYTICS-QA-06 · P3

ANALYTICS-QA-06 — AZ дельта содержит русский текст. ID: ANALYTICS-QA-06.

Источники: [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-06.md](module12-2026-10-11-r1/findings/ANALYTICS-QA-06.md), [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-06-repair.txt](module12-2026-10-11-r1/findings/ANALYTICS-QA-06-repair.txt).

```text
KidsMap: PLAN ANALYTICS-QA-06. ID scope: ANALYTICS-QA-06. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-06.md, docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-06-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только ANALYTICS-QA-06: AZ дельта содержит русский текст в KidsMap. Работай в фактическом корне checkout; прочитай AGENTS.md, .agents/README.md, registry, canonical role, source-of-truth и engineering/audit contracts. Сохрани чужой dirty WORKTREE, active_run и стенды; зафиксируй HEAD/branch и actual runtime. Отчёт: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-06.md.

Воспроизведение: С вымышленными previous/current rows открыть AZ owner analytics; previous_views>0.
Ожидание: Дельта и пояснение на AZ.
Факт: «…% к прошлому периоду» в AZ; native screenshot6 widths.
Источник: src/catalog/templates/pages/owner_analytics.html:32/44; первопричина: Для percentage small template разделяет только EN и else(RU); AZ попадает в RU.

Конкретная область исправления: Локализуй пояснения дельты просмотров и контактных действий дляAZ/RU/EN существующей системой. Проверь previous0 (без процента), положительную/отрицательную/нулевую дельту и длинные значения на360/390/768/1024/1280/1440.
Зависимости и владелец: frontend-reviewer/analytics-reviewer; перевод обоих delta labels.

Сначала подготовь конкретный план и regression evidence, затем действуй в пределах явно разрешённой пользователем области. Соблюдай канонические инструкции о согласовании implementation scope. Тесты только DJANGO_TESTING=1, свежие отдельные DB/cache/media/private-media/email, вымышленные данные; внешние GA/Google/OAuth/Maps выключить. Не менять существующие assertions радиgreen, не использовать ORM для проверяемых UI-переходов. Не commit/push/deploy и не обращаться к production.

Приёмка: функциональный before/after по серверному контракту, настоящий UI/save/reload где применимо, RU/AZ/EN×360/390/768/1024/1280/1440, доступный focus/keyboard/empty/error. Сохрани новый отчёт/скриншоты/commands/counts/exit, различи реальные проверки и SIMULATED adapters/NOT RUN. Объясни пределы исправления и чужие неизменённые файлы.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ANALYTICS-QA-07"></a>

#### PLAN ANALYTICS-QA-07 · P2

ANALYTICS-QA-07 — Отказ analytics write ломает публичную карточку. ID: ANALYTICS-QA-07.

Источники: [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-07.md](module12-2026-10-11-r1/findings/ANALYTICS-QA-07.md), [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-07-repair.txt](module12-2026-10-11-r1/findings/ANALYTICS-QA-07-repair.txt).

```text
KidsMap: PLAN ANALYTICS-QA-07. ID scope: ANALYTICS-QA-07. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-07.md, docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-07-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только ANALYTICS-QA-07: Отказ analytics write ломает публичную карточку в KidsMap. Работай в фактическом корне checkout; прочитай AGENTS.md, .agents/README.md, registry, canonical role, source-of-truth и engineering/audit contracts. Сохрани чужой dirty WORKTREE, active_run и стенды; зафиксируй HEAD/branch и actual runtime. Отчёт: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-07.md.

Воспроизведение: При здоровых catalog reads через собственный QA adapter вызвать DatabaseError actual DjangoFunnelEventRepository.create_event; открыть карточку.
Ожидание: Карточка200, аналитика честно недоступна; без фиктивного записанного события.
Факт: Native500 на390/1440, event delta0. Own corrected injection confirmed=true; исходный неверно подключённый mock исключён. SIMULATED fault.
Источник: src/catalog/controllers/place_controller.py:735; первопричина: Tracking write выполняется синхронно в build_detail_context без обработки отказа независимого analytics storage.

Конкретная область исправления: Изолируй отказ analytics persistence от публичного SSR при исправной основной БД; проверь реальный вызванный repository mock и transaction recovery, logs только безопасные агрегаты, не скрывай основную catalog/ACL ошибку. Native200/reload, event delta0, disabled flag и штатный delta+1 обязательны.
Зависимости и владелец: analytics-reviewer/django-reviewer; transaction handling, telemetry errors без payload leakage.

Сначала подготовь конкретный план и regression evidence, затем действуй в пределах явно разрешённой пользователем области. Соблюдай канонические инструкции о согласовании implementation scope. Тесты только DJANGO_TESTING=1, свежие отдельные DB/cache/media/private-media/email, вымышленные данные; внешние GA/Google/OAuth/Maps выключить. Не менять существующие assertions радиgreen, не использовать ORM для проверяемых UI-переходов. Не commit/push/deploy и не обращаться к production.

Приёмка: функциональный before/after по серверному контракту, настоящий UI/save/reload где применимо, RU/AZ/EN×360/390/768/1024/1280/1440, доступный focus/keyboard/empty/error. Сохрани новый отчёт/скриншоты/commands/counts/exit, различи реальные проверки и SIMULATED adapters/NOT RUN. Объясни пределы исправления и чужие неизменённые файлы.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-ANALYTICS-QA-08"></a>

#### PLAN ANALYTICS-QA-08 · P3

ANALYTICS-QA-08 — AZ административная аналитика имеет русские labels. ID: ANALYTICS-QA-08.

Источники: [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-08.md](module12-2026-10-11-r1/findings/ANALYTICS-QA-08.md), [docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-08-repair.txt](module12-2026-10-11-r1/findings/ANALYTICS-QA-08-repair.txt).

```text
KidsMap: PLAN ANALYTICS-QA-08. ID scope: ANALYTICS-QA-08. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-08.md, docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-08-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Исправь только ANALYTICS-QA-08: AZ административная аналитика имеет русские labels в KidsMap. Работай в фактическом корне checkout; прочитай AGENTS.md, .agents/README.md, registry, canonical role, source-of-truth и engineering/audit contracts. Сохрани чужой dirty WORKTREE, active_run и стенды; зафиксируй HEAD/branch и actual runtime. Отчёт: docs/qa/module12-2026-10-11-r1/findings/ANALYTICS-QA-08.md.

Воспроизведение: ВыбратьAZ в admin, открыть KPI/график/таблицы с отключённымGA либо SIMULATED filled report.
Ожидание: Названия метрик и подписей наAZ, без неверных переводов.
Факт: KPI/подписи наRU при Statistika/Unikal/Baxışlar наAZ;11 fuzzy PO ключей отсутствуют вMO,15проверенныхentries совпадаютHEAD.
Источник: locale/az/LC_MESSAGES/django.po:11260; первопричина: gettext вызван корректно; fuzzy drafts неверны и не попали вMO. Компиляция без проверки переводов недостаточна.

Конкретная область исправления: Согласуй и исправь только11 неверных fuzzy AZ analytics переводов, затем обнови соответствующийMO существующим locale workflow. Не снимай fuzzy со всего файла и не меняй чужие pendingPO строки. Проверь placeholders, native AZ KPI/chart/tables/empty/error и RU/EN smoke; сохранность иных locale edits обязательна.
Зависимости и владелец: frontend-admin; locale build dependency SITE-QA-07, отдельный content cause; not duplicate owner06.

Сначала подготовь конкретный план и regression evidence, затем действуй в пределах явно разрешённой пользователем области. Соблюдай канонические инструкции о согласовании implementation scope. Тесты только DJANGO_TESTING=1, свежие отдельные DB/cache/media/private-media/email, вымышленные данные; внешние GA/Google/OAuth/Maps выключить. Не менять существующие assertions радиgreen, не использовать ORM для проверяемых UI-переходов. Не commit/push/deploy и не обращаться к production.

Приёмка: функциональный before/after по серверному контракту, настоящий UI/save/reload где применимо, RU/AZ/EN×360/390/768/1024/1280/1440, доступный focus/keyboard/empty/error. Сохрани новый отчёт/скриншоты/commands/counts/exit, различи реальные проверки и SIMULATED adapters/NOT RUN. Объясни пределы исправления и чужие неизменённые файлы.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="m13"></a>

### 13. Финальная межмодульная приёмка и сводка

<a id="repair-CROSS-QA-01"></a>

#### PLAN CROSS-QA-01 · P2

CROSS-QA-01 — Перенесённое будущее событие исчезает из организации. ID: CROSS-QA-01.

Источники: [docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-01.md](module13-2026-10-11-r1/findings/CROSS-QA-01.md), [docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-01-repair.txt](module13-2026-10-11-r1/findings/CROSS-QA-01-repair.txt).

```text
KidsMap: PLAN CROSS-QA-01. ID scope: CROSS-QA-01. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-01.md, docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-01-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-01.md. Зафиксируй HEAD/dirty WORKTREE/active_run; сохрани чужие изменения и стенды. Этот промпт задаёт подготовку конкретного плана исправления, не разрешает автоматически приложение/commit/push/deploy/production.

Разбери CROSS-QA-01: опубликованное будущее Event после native reschedule остаётся в общей афише/карточке, но пропадает из страницы организации. Проверь src/catalog/controllers/public_details.py:135, lifecycle и все потребители публичного upcoming queryset. Определи единый контракт scheduled/rescheduled/cancelled/past/deleted/private и влияние section toggles; не расширяй видимость частных событий. Дай минимальный reviewable план с файлами/зависимостями и acceptance.

После отдельного согласования scope реализуй regression test на PostgreSQL и native UI проверку: организация→филиал→physical+online Event→publish→reschedule на будущую дату→все публичные читатели→cancel→переключение раздела. RU/AZ/EN, PC/mobile, reload, новая дата и прежний URL, консоль/network. Только DJANGO_TESTING=1, отдельные DB/cache/media/private/email, fictional fixtures; реальные интеграции NOT RUN. Не ослабляй существующие assertions. Сохрани свежие evidence/отчёт, явно отдели clean HEAD/baseline/environment и ограничения.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```

<a id="repair-CROSS-QA-02"></a>

#### PLAN CROSS-QA-02 · P2

CROSS-QA-02 — Команда CI не обнаруживает значительную часть тестов. ID: CROSS-QA-02.

Источники: [docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-02.md](module13-2026-10-11-r1/findings/CROSS-QA-02.md), [docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-02-repair.txt](module13-2026-10-11-r1/findings/CROSS-QA-02-repair.txt).

```text
KidsMap: PLAN CROSS-QA-02. ID scope: CROSS-QA-02. Прочитай статус и правила docs/qa/continuation-and-repair-prompts-2026-10-11.md; не загружай остальные задачи без необходимости.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Определи фактический checkout на этом ПК, текущие HEAD/branch/dirty WORKTREE/active_run. Сохрани чужие изменения, active_run и стенды. Старые SHA, localhost, PID, DB/container/browser session — исторические ссылки, а не параметры нового стенда. Без commit/push/deploy/production.
ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план. Приложение, конфигурацию CI, schema и existing assertions сейчас не изменяй. Формулировки «исправь/добавь» в техническом задании ниже описывают цель будущей реализации, не дают разрешения выполнить её этим запуском. Если текущий источник уже исправлен или проблема исчезла на свежих MO, сохрани доказательства и не делай повторный patch. Исторический FAIL не доказывает текущий FAIL.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Обязательные входные материалы: docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-02.md, docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-02-repair.txt. Для источников module13 свежий повтор имеет приоритет по evidence, но его исторические runtime параметры не используй на другом ПК.

Техническое задание для плана и будущего согласованного исправления:
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, .agents и docs/qa/module13-2026-10-11-r1/findings/CROSS-QA-02.md вместе с test-review/discovery-audit.json/manage-discovery.json. Сохрани dirty WORKTREE, active_run, чужие стенды. Сначала представь конкретный минимальный план discovery/CI; изменения приложения, assertions, commit/push/deploy/production не разрешены этим промптом без согласования scope.

Устрани после согласования молчаливое выпадение tests из no-label python manage.py test --parallel 1 и wrapper full. Зафиксируй текущий tracked корпус отдельно от локальных untracked тестов. Сверь no-label, wrapper, явно полный набор и clean HEAD; выбери устойчивую единую точку discovery, которая включает catalog.testcases.test_* и нужные non-test-prefixed домены без дублирования. Сохрани KidsMapTestRunner resets cache/language и реальные assertions; не отключай падающие tests ради зелёного CI.

Acceptance: списки уникальных IDs согласованы между локальным full и quality gate; новые тестовые модули включаются по документированному правилу; нет дубликатов/тихих пропусков. Полный применимый Django+JS набор выполняется на DJANGO_TESTING=1 с отдельными PostgreSQL/cache/media/private-media/email, blocked/stubbed external transport. Environment failures и baseline failures остаются отдельными, точные counts/exits/commands приложены. Приватные данные/credentials не сохранять. Реальный GitHub запуск и production не объявлять проверенными без выполнения.

На выходе сохрани новый REPORT и конкретный implementation plan в docs/qa/<свой-уникальный-run>/: подтверждённые ID/общую причину, точные файлы, минимальный diff, зависимости/риски, regression acceptance, команды и NOT RUN. Для broad exploration сначала codebase-memory-mcp проекта C-kidsmap: freshness/coverage, затем нужный source и динамические Django/ORM связи через текстовый поиск; graph — подсказка, не доказательство удаления. Установи source/baseline/environment/QA-harness классификацию. Не смягчай assertions ради green. Перед реализацией нужен этот reviewable план и одобрение конкретного scope; готовый блок одобрения есть в guide. Уже выданное одобрение того же плана повторно не запрашивай. Дай текст для следующего чата с фактическими путями, snapshot и ограничениями; не сохраняй credentials/реальные записи/production logs или graph caches.
```


## ACCEPT — полная свежая приёмка каждого модуля

Ниже 13 самостоятельных блоков исходной module acceptance спецификации с актуальным вступлением. Они выполняются после выбранных ремонтов либо как AUDIT ONLY по ещё не проверенному полному scope. Старые DONE/FAIL/scoped PASS не освобождают от сценариев новой полной приёмки. Production, реальные внешние сервисы и физические устройства не входят в эти локальные запуски и отмечаются NOT RUN.

<a id="accept01"></a>

### ACCEPT-01. Постоянные места

```text
KidsMap: ACCEPT-01, полная свежая приёмка модуля «Постоянные места». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 01.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Особый текущий статус: PLACE-QA-01–07 свежо подтверждены в module01-recheck-2026-10-11-r1; PLACE-QA-08 alias CROSS-QA-03 закрыт в place-qa08-fix-2026-10-11-r1. Текущий module01-full-2026-10-12-r6/REPORT.md: LOCAL PASS, QA09–14 closed within actual scope; QA14 close()/show()/shared focus extension одобрено и принято.943 native assertions PASS,470 backend tests PASS сохранены при source match; JS52PASS/1SKIP и финальный7PASS subset. Читай свежий r6 и scoped QA14 close report; старый r5 OPEN — история. Это не разрешение нового patch, global run или production. По правилу пользователя targeted после repair, full module после его всех исправлений, global corpus после всех13; старое full-corpus-per-repair требование ниже не применять. Прочитай оба REPORT и limits/NOT RUN, не переисправляй старый r2. На своём fresh locale profile проверь доставку текущих fixes как regressions, затем закрой недостающие категории/филиалы, все pricing modes и concurrency, координатный corpus включая 0/0 отдельно от geographic gates, gallery file/order/delete corpus, opening hours отдельно от lesson timetable, ACL endpoints, double-submit/two-tabs/lost-response/recovery и полный applicable keyboard. Расширенная states×roles×18 cells matrix обязана иметь явные PASS/FAIL/NOT RUN, не blanket PASS. Full configured Django/JS corpus/discovery и clean HEAD comparison фиксируй отдельно; реальные provider/GPS/screenreader/production остаются NOT RUN без отдельного фактического выполнения/авторизации. Новый defect ID только по fresh evidence, alias не дублировать.

Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку постоянных мест: кабинет владельца, административный редактор и публичная карточка.

Проверь:
1. Создание самостоятельного места и филиала, разные категории и подкатегории.
2. Названия AZ/RU/EN, пустые переводы и языковой fallback. Раздели отображение другого языка и реально сохранённый перевод.
3. Описание, возраст, контакты, адрес, регион/район, карту и ручные координаты. Отсутствие точки, 0/0, неверную/неполную пару, отказ геолокации и отсутствие SDK. Перепроверь docs/qa/admin-place-map-fix-2026-10-09.md, если файл доступен.
4. Бесплатный/платный вход, общий билет, цену по мероприятию. Повторное переключение режимов и повторное редактирование не должны вызывать зависание.
5. Часы работы места отдельно от расписания занятий.
6. Главное фото, галерею, порядок, замену/удаление и ошибку файла. Сверь данные после reload и на публичной карточке.
7. Навигацию по длинной форме, готовность по серверным требованиям, сводку/переход к ошибке и честное состояние сохранения.

Выполни настоящий путь через UI: создание → частичное заполнение → черновик → reload → выход/вход → продолжение → ошибка → исправление → отправка → отказ с причиной → повторная отправка → одобрение → публичная карточка → изменение опубликованного. По коду установи, какие изменения ждут модерации; сверяй candidate и live.

Негативно проверь чужой ID, недостаточные права, повторное нажатие, две вкладки, сетевую ошибку и сохранность ввода. Проверяемые переходы не выполняй прямым ORM-сохранением. Префикс дефектов PLACE-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module01-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept02"></a>

### ACCEPT-02. Организации, готовые места и сотрудники

```text
KidsMap: ACCEPT-02, полная свежая приёмка модуля «Организации, готовые места и сотрудники». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 02.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи полную функциональную и визуальную приёмку управления организациями. Дополнительно прочитай docs/qa/organization-deep-audit-2026-10-08.md, если доступен, и перепроверь исторические ORG findings.

Изучи canonical request_join, confirm_join, detach, affiliation_current и версии владения. Проверяемые связи выполняй через реальные UI/API, не присваиванием organization_id.

Позитивные сценарии:
1. Создать организацию без филиалов, сохранить, reload, отредактировать. Проверить доступные процессы модерации/публичного отображения по текущему контракту.
2. Найти готовые места по названию/адресу; увидеть текущую сеть, доступность и состояние запроса.
3. Подключить 10 существующих мест без пересоздания. Сверить ID, владельца, фото, занятия, группы, цены и расписание до/после.
4. Пройти необходимые согласия сторон, отмену/отказ/повтор запроса.
5. Создать новый филиал отдельно от подключения готовой карточки.
6. Массовая операция: выбор → организация → preview/conflicts → подтверждение → результат по каждой карточке.
7. Отвязать место и выполнить разрешённый перенос в другую сеть с объяснением последствий.
8. Приглашение сотрудника, понятность ролей, принятие/отказ/отзыв и удаление доступа.

Негативно: другая сеть; чужой приватный draft по угаданному ID; недостаточные права; старое согласие после смены владельца; изменение между preview и confirm; mixed batch с частичным отказом; двойное подтверждение; lost response/retry; истёкшее приглашение. Проверь legacy endpoints и API, не только новый интерфейс.

Запрос не должен выдавать права или раскрывать приватные метаданные. Отвязка должна учитывать общие программы и доступ сотрудников по действующему контракту. Префикс ORG-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module02-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept03"></a>

### ACCEPT-03. Специалисты и приватные документы

```text
KidsMap: ACCEPT-03, полная свежая приёмка модуля «Специалисты и приватные документы». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 03.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку специалистов: предложение профиля, личный кабинет, административный редактор и публичная карточка.

Проверь:
1. Имя, фото, направления, возраст детей, языки, формат, описание, образование, стоимость.
2. Пустой стаж и 0 лет, отрицательные/чрезмерные значения.
3. Поиск направлений на телефоне, отсутствие дублей, удаление выбранного.
4. Несколько мест приёма: адрес/филиал, отдельная цена и телефон каждого; онлайн/смешанный формат.
5. Разделение автора предложения, специалиста, сотрудничества с сетью и места приёма.
6. Приглашение сетью, принятие/отказ/отзыв/повтор и изменение полномочий.
7. Подтверждение личности и claim существующего профиля по предусмотренному процессу.
8. Приватность документов личности; публикацию сертификатов с необходимыми согласиями.

Пройди реальный UI: частичное предложение → черновик с первого и остальных доступных этапов → reload → продолжение → ошибки → отправка → модерация/отказ → исправление → публикация → редактирование опубликованного. Сверь места приёма, файлы и публичную версию.

Проверь две вкладки, повтор отправки, ошибку файла/сети, чужой draft/profile/document ID. Матрица доступа: гость, автор предложения, специалист, сотрудник сети, владелец сети, модератор, администратор. Прямое скачивание документа, доступ после отзыва роли, безопасное публичное media. Автор предложения не получает личные права. Префикс SPEC-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module03-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept04"></a>

### ACCEPT-04. Мероприятия

```text
KidsMap: ACCEPT-04, полная свежая приёмка модуля «Мероприятия». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 04.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку мероприятий: кабинет владельца, административный редактор, управление событием и публичная карточка.

Изучи существующие 3 этапа; не придумывай второй процесс.
1. Организация/специалист как организатор; ровно один организатор; отсутствие доступного организатора и отзыв права во время ввода.
2. Площадка отдельно от организатора: собственный адрес, разрешённая площадка KidsMap, недоступная/скрытая площадка.
3. Очно/онлайн, переключение туда/обратно, обязательность полей и сохранность скрытых значений по контракту.
4. Asia/Baku: дата, начало/окончание, полночь, одинаковое время, окончание раньше начала, истёкшее событие.
5. Возраст, цена, контакты, описание и переводы.
6. Фото/порядок галереи/ошибки файла/предпросмотр.
7. Черновик с каждого этапа, reload, повторное открытие.
8. Отправка, отказ/исправление, одобрение и изменение опубликованного.
9. Отмена/перенос: причина, новая дата, публичный статус, список/поиск и старая ссылка.

Негативно: чужие права/ID, двойная отправка, две вкладки, изменение организатора/площадки другим редактором, сбой сети/карты, ошибки публикации. Административные подписи и состояния новая/draft/pending/published/rejected должны соответствовать серверу.

Выбор формата проверь клавиатурой и по доступному имени/состоянию. Обещания о проверенных профилях, записи участников и рассылке сопоставь с реально реализованным процессом. Сохранение/публикацию докажи round-trip, не одним preview. Префикс EVENT-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module04-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept05"></a>

### ACCEPT-05. Программы, занятия, группы, тарифы и расписание

```text
KidsMap: ACCEPT-05, полная свежая приёмка модуля «Программы, занятия, группы, тарифы и расписание». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 05.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи отдельную функциональную и визуальную приёмку программ, занятий, групп, тарифов и расписания.

Установи действующий контракт Program, Activity, OfferingGroup, PricingPlan и расписаний. Не смешивай сеть, место, занятие, группу и тариф.

Проверь:
1. Общую программу организации и самостоятельное занятие места; создание/редактирование/архив и поддержанные состояния публикации.
2. Несколько занятий/групп одного места: названия, классификацию, возраст, формат и условия.
3. Подтверждение условий группы и изменение подтверждённых данных.
4. Бесплатно, общий билет, разовое посещение, абонемент и другие реально поддержанные тарифы; цена 0/пусто, валюта, единица оплаты, несколько тарифов.
5. Принадлежность тарифа группе; цена одной группы не должна смешиваться с возрастом другой.
6. Все поддержанные режимы часов работы места отдельно от расписания занятий. Несколько интервалов, выходные, пересечения, неверные интервалы, смену режима.
7. Структурированные данные и legacy fallback: редактирование не стирает старые цены/расписание без предусмотренного действия.
8. Отвязку филиала: общие программы, локальные группы, доступ сотрудников.
9. Public card/catalog/search/filter: цена/возраст/расписание относятся к одному подходящему предложению.

Сохранение/reload, ошибки, повтор, две вкладки, чужие ID, атомарность неудачной операции. Сверь связанные записи до/после. Если импорт/экспорт существует, проверь round-trip на своих локальных фикстурах. Отдельно мобильное добавление/удаление строк и ошибки внутри скрытых блоков. Префикс OFFER-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module05-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept06"></a>

### ACCEPT-06. Публичный каталог, поиск, фильтры и карта

```text
KidsMap: ACCEPT-06, полная свежая приёмка модуля «Публичный каталог, поиск, фильтры и карта». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 06.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку главной, списков мест/организаций/специалистов/мероприятий, публичных карточек, поиска и карты.

Контролируемый набор: published/draft/pending/rejected/inactive/archived; разные районы, категории, возрасты, цены и группы.

Проверь:
1. Главную, меню, навигацию, карточки и переходы между сущностями.
2. Поиск по названию/адресу/реально поддержанным полям; AZ/RU/EN, частичный запрос, пустой результат. Опечатки проверяй как обязательную функцию только при подтверждённой поддержке.
3. Фильтры отдельно/совместно, сброс, сортировку, pagination, URL params, Back/Forward, reload, прямую ссылку.
4. Согласованность списка, количества и карты.
5. Совпадение возраста/цены/направления с одной подходящей группой.
6. Группировку площадок, одинаковые координаты разных мест, карточки без точки, popup и правильную карточку.
7. Отсутствие приватных/неодобренных данных в HTML/API/search suggestions/map.
8. Актуальность после публикации, изменения, отмены события и скрытия раздела; действующую инвалидацию локального cache.
9. Контакты, раскрытие телефона, внешние ссылки, фото/галерею и пустые состояния.

Отказ карты/сети проверяй локально. Раздели adapter simulation и реально проверенный SDK. Не используй production-карточки или внешние production-ключи. Проверь реальные клики и геометрию, а не только screenshot. Префикс PUBLIC-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module06-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept07"></a>

### ACCEPT-07. Аккаунты, команда, права и приватность

```text
KidsMap: ACCEPT-07, полная свежая приёмка модуля «Аккаунты, команда, права и приватность». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 07.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную, визуальную и негативную приёмку аккаунтов, команд и прав доступа.

Проверь:
1. Регистрацию, email confirmation, login/logout, восстановление пароля, профиль по реализованным процессам.
2. Неверные данные, email normalization, дубли, истёкшие/повторные токены, повтор запросов. Email перехватывай локально.
3. next/redirect, CSRF, создание/завершение сессии.
4. Google OAuth: локальные ошибки/adapters отдельно; внешнюю авторизацию без разрешённых тестовых credentials отметь NOT RUN.
5. Команду места/организации: приглашение, принятие/отказ/отзыв, смену роли, удаление сотрудника и потерю доступа в открытой вкладке.
6. Удаление аккаунта: связанные владение, связи, приглашения и приватные данные, только на своих фикстурах.
7. Прямые URL/API/download, подмену ID и доступ после изменения роли/владельца.
8. Автор предложения, специалист, владелец места/сети, сотрудник, волонтёр, модератор, администратор: точные границы.
9. Приватные документы в HTML/API/media/download/cache; сертификаты по предусмотренным согласиям.

Матрица роль × действие × сущность. Докажи отказ реальным HTTP и отсутствием побочных изменений: скрытая кнопка не является ACL. Негативные запросы только localhost/synthetic objects. Не сохраняй пароли, токены или env values в отчёте.

Подтверждённую утечку сообщи сразу, но автоматически не исправляй. Префикс ACCESS-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module07-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept08"></a>

### ACCEPT-08. Админка, модерация и волонтёрский кабинет

```text
KidsMap: ACCEPT-08, полная свежая приёмка модуля «Админка, модерация и волонтёрский кабинет». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 08.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку общих административных и модерационных процессов.

Установи реально существующие admin/volunteer поверхности и права.

Проверь:
1. Очереди мест/организаций/мероприятий/специалистов: поиск, фильтры, pagination, счётчики, переходы.
2. Одобрение, отказ с причиной, повторную отправку, отзыв заявки, действие над обработанной заявкой.
3. Candidate/live до решения/после одобрения/после отказа, включая фото и связанные данные.
4. Readiness: new/draft/pending/published/rejected по серверным требованиям.
5. Два модератора/две вкладки, stale version, повтор, частичный отказ batch.
6. Волонтёра: назначенные объекты, ограничения полей, отправку на проверку, отзыв назначения.
7. Прямые admin URL/API и действие без роли.
8. Журнал действий и причины решений без доступа к документам лишним ролям.
9. Mass actions: preview/confirmation/results и сохранность данных. Удаление только если предусмотрено и только своих фикстур.

Не дублируй полный обход каждого редактора: scope — очереди, решения, версии, массовые действия, admin navigation. Смежный finding передавай владельцу модуля со ссылкой на evidence.

Отдельно таблицы/sidebar/открытые фильтры/модалки/ошибки на телефоне и клавиатуру. Префикс MOD-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module08-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept09"></a>

### ACCEPT-09. Отзывы, избранное и уведомления

```text
KidsMap: ACCEPT-09, полная свежая приёмка модуля «Отзывы, избранное и уведомления». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 09.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку отзывов, избранного и внутренних уведомлений.

Проверь реально поддержанные процессы:
1. Отзывы о сайте и типах карточек: создание, оценку, required fields, редактирование, модерацию, отказ, public display.
2. Ответ/решение владельца: только разрешённые объекты и действия.
3. Голоса/полезность, повтор нажатия, корректность счётчиков.
4. Рейтинг/количество после одобрения, скрытия и изменения.
5. Длинный текст, спецсимволы, безопасное HTML display, pagination, empty state.
6. Favorite add/remove, double click, reload, login/logout, сохранность списка.
7. Favorite скрытой/архивной/недоступной карточки без утечки приватных данных.
8. Read/unread уведомления, счётчик, переход к объекту, принятие приглашения.
9. Повторное/stale уведомление, удалённый объект, отозванное приглашение, чужой notification ID.

Гость/автор/владелец/сотрудник/модератор/admin по действующим правилам. Сверь сохранённые записи и счётчики; анимация UI не доказывает сохранение. Негативные HTTP/API только локально.

Отдельно accessible rating controls, меню уведомлений и формы на телефоне. Отсутствующую функцию не называй дефектом без подтверждённого требования. Префикс SOCIAL-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module09-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept10"></a>

### ACCEPT-10. Настройки, разделы и общие страницы

```text
KidsMap: ACCEPT-10, полная свежая приёмка модуля «Настройки, разделы и общие страницы». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 10.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку настроек сайта, переключателей разделов и общих страниц.

Разрешено менять настройки только собственной изолированной тестовой DB.

Проверь:
1. Реальные branding/contacts/footer/hero PC/mobile/empty states/public text settings.
2. Главную, о проекте, FAQ, контакты, правила/privacy/terms и страницу бизнеса, если существует.
3. Save через админку, reload, public display, действующую инвалидацию cache.
4. Поочерёдное OFF/ON организаций/специалистов/мероприятий и других существующих flags.
5. Влияние flag на меню/home/catalog/search/map/direct URL/API/account по фактическому контракту.
6. Сохранность данных и admin editing при скрытом публичном разделе.
7. Language switch: текущую страницу/params, active language, fallback, ошибки и общие переводы.
8. Header/footer/mobile menu/breadcrumbs/shared buttons/forms/toast/modal/404 и поддержанные error pages.
9. Неверные ссылки/контакты, длинные тексты, missing images, save failure.

Раздели скрытие раздела, unpublish карточки, архив и удаление. Проверяй публичный результат, не только flag DB.

Дополнительно контраст/читаемость/200% zoom, открытые меню/модалки и fixed elements. В отчёте перечисли собственные изменения тестовых настроек. Префикс SITE-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module10-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept11"></a>

### ACCEPT-11. SEO, языковые URL и redirects

```text
KidsMap: ACCEPT-11, полная свежая приёмка модуля «SEO, языковые URL и redirects». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 11.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи локальную функциональную и визуальную приёмку URL, redirects и SEO.

Прочитай актуальную SEO source-map. Не отправляй IndexNow/Search Console запросы. SEO-команды сначала проверь на побочные записи.

Проверь:
1. URL мест/организаций/специалистов/мероприятий/занятий/реальных SEO landing pages.
2. Старый URL, неверный slug, rename и несколько rename: конечную сущность, HTTP status, число redirects, отсутствие loop, допустимые params.
3. AZ/RU/EN/default-language redirects, canonical/hreflang/language switch.
4. title/description/headings/Open Graph/images и preview без обращения к внешним ботам.
5. robots/sitemap/structured data по фактической public visibility.
6. Draft/pending/rejected/inactive/archived и disabled sections: отсутствие приватных данных в sitemap/HTML/JSON-LD/metadata.
7. Pagination/filter/empty/direct URL и действующий indexability contract.
8. Ссылки между сетью/филиалом/занятием/специалистом/событием после изменения/отвязки.
9. Escaping пользовательского текста в metadata/JSON-LD.

Не предполага́й наличие новостей/статей: найди реальные routes/models. Если модуль есть, включи его rename/redirect/SEO; иначе явно укажи отсутствие в текущем коде.

HTTP/head/schema проверь отдельно от visual browser: заголовки/breadcrumbs/links/страница после redirect. Локальную корректность не называй подтверждённой индексацией поисковиком. Префикс SEO-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module11-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept12"></a>

### ACCEPT-12. Просмотры, счётчики и аналитика

```text
KidsMap: ACCEPT-12, полная свежая приёмка модуля «Просмотры, счётчики и аналитика». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 12.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.



Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку просмотров и аналитики.

Прочитай analytics source-map. Внешнюю отправку событий и реальные Google Analytics запросы отключи.

Установи определение view/unique visitor/event и ключ агрегирования: object/URL/slug/session/actor или фактический другой ключ. Не выдумывай методику.

Проверь:
1. Карточку гостем/login user/owner/staff: какие просмотры учитываются и исключаются.
2. Reload/Back/Forward/two tabs/repeated event request и текущую дедупликацию.
3. Rename карточки: заход по старой redirect-ссылке и новой. Докажи delta и выясни, суммируются ли просмотры у одной сущности.
4. Несколько rename, языковые URL, query params, устройства.
5. Phone/contact clicks/transitions и реализованные funnel events.
6. Invalid payload, чужой/private object ID, repeat, disabled analytics, локальный backend failure.
7. Owner/admin graphs: dates/periods/Asia/Baku/day-month boundaries/empty/totals.
8. DB aggregates/API/graphs consistency; отсутствие доступа к чужим данным.
9. Cancel/hide/archive и сохранность истории по контракту.

Фиксируй before/after каждого контролируемого действия. Adapter = SIMULATED, внешняя интеграция = NOT RUN, если не выполнена реально.

Отдельно period filters/graphs/tables/empty-error states. В findings укажи ожидаемый/фактический delta. Префикс ANALYTICS-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module12-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```

<a id="accept13"></a>

### ACCEPT-13. Финальная межмодульная приёмка и сводка

```text
KidsMap: ACCEPT-13, полная свежая приёмка модуля «Финальная межмодульная приёмка и сводка». Режим строго AUDIT ONLY, без новых application fixes. Прочитай текущий статус/границы docs/qa/continuation-and-repair-prompts-2026-10-11.md и новые repair REPORT выбранного модуля. Исторический журнал уже содержит завершённые аудиты; не выбирай автоматически «первый незавершённый» из старой серии. Выполни именно модуль 13.

Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, действующее определение .agents/agents/kidsmap-orchestrator/agent.md, .agents/knowledge/architecture.md, .agents/knowledge/source-of-truth.md и .agents/rules/audit-contract.md. Используй только канонические активные роли и применимые skills.
Свежая проверка: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, вымышленные данные, отключённые или явно SIMULATED внешние обращения. Не используй production credentials и не копируй .env. Подтверди исходники работающего процесса. Собери RU/AZ/EN из текущих PO в собственный изолированный каталог через scripts/build_isolated_locales.py; проверь manifest и подключи единственный LOCALE_PATHS до django.setup. Общие старые MO не перезаписывай. Инструменты, пути и свободные порты найди заново.

Финальную сверку делай по новым локальным отчётам модулей 01–12, новым repair plans/results и открытому ledger; прежний module13 MASTER лишь историческая база. PLACE-QA-01–08 имеют scoped результаты, не общий product PASS. CROSS-QA-01 и CROSS-QA-02 учитывай один раз, ORG/ACCESS network и compiled locales дедуплицируй с сохранением исходных ID. Новое состояние репозитория/проверок не наследует прежние counts/HEAD. Если обязательная полная module acceptance отсутствует, итог INCOMPLETE/NOT RUN с причинами; не выдавай общий PASS только по историческим или целевым repair отчётам. Новые P0/P1/непринятые существенные findings сохраняй открытыми. Actual GitHub execution/production/real integrations не заявляй выполненными локальной проверкой.

Полная спецификация этого запуска:
Работай в корне репозитория KidsMap. На этом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Запускай после отдельных модульных аудитов. Проведи финальную межмодульную приёмку и сведи новые результаты.

Прочитай модульные отчёты текущей серии. Сопоставь routes/models/admin surfaces с coverage; найди непроверенные области. Отчёты другого snapshot не считаются автоматически свежими: изменившиеся критичные сценарии перепроверь.

Пройди один реальный путь:
1. Создать организацию без филиалов.
2. Создать/опубликовать места и подключить готовые через canonical request/confirm.
3. Добавить программу/занятия/группы/тарифы/расписания.
4. Предложить специалиста, пройти подтверждения, сотрудничество с сетью и несколько мест приёма.
5. Очное событие на площадке филиала и online event с доступным организатором.
6. Draft/reload/submit/reject/correct/approve/public card.
7. Edit published/two-tab conflict/live preservation.
8. Detach branch/revoke employee/change cooperation/reschedule-cancel event: связанные программы/ACL/public display.
9. Public sections OFF/ON: menu/direct URLs/search/map/data preservation.
10. Фото/галерею/private docs/reviews/favorites/redirects/view counters в местах пересечения модулей.

Позитивные/негативные пути, повторы, partial failure. Полные применимые backend/JS-наборы запускай только подтверждённым изолированным launcher. Ничего не ослабляй/отключай ради green. Недоступный набор = NOT RUN с причиной.

Сведи дубли по первопричине, сохрани исходные IDs/evidence. Итог дополнительно:
— module/scenario/role/snapshot/PASS/FAIL/NOT RUN/evidence;
— открытые P0–P3, coverage gaps, внешние/device/browser ограничения;
— counts/exit codes, screenshots, порядок исправления с зависимостями;
— отдельные repair prompts.
Новый префикс CROSS-QA-xx. Общий PASS проекта не заявляй при невыполненных обязательных сценариях. Локальная приёмка не доказывает production-состояние.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.

Новый run имеет уникальный каталог docs/qa/<module13-full-YYYY-MM-DD-run> с фактическим snapshot, REPORT, matrix, counts, exact commands/exits, failures и limits, свежими browser PNG/manifest. Обнови только статус этого модуля со ссылкой на новую приёмку, сохраняя предыдущие evidence. Целевые repair тесты не заменяют полный module scope; NOT RUN/SIMULATED явно выдели. Дай новый handoff. Без commit/push/deploy/production и без удаления чужих артефактов.
```


## Что должно попасть в Git перед переездом

Это инструкция для будущего отдельно разрешённого Git-запуска. Сейчас ничего не staged/committed/pushed. Доступ к серверу сам по себе не разрешает deployment. Git переносит только закоммиченные и полученные файлы; игнорируемый стенд и незакоммиченные fixes завтра отсутствуют.

1. Зафиксировать фактические HEAD/branch/remote и полный staged/unstaged/untracked inventory. Не считать существующую ветку `task33-progress` или SHA будущей веткой назначения без проверки. Сначала показать reviewable список того, что будет переноситься, сохранить чужие изменения; не использовать слепой `git add .`.
2. Включить нужные изменения существующих PLACE-QA-01–07 и RU PO PLACE-QA-08, связанные templates/services/JS/CSS/locales. Сверить весь dirty diff с отчётами, не уронить прежние поправки. Добавить новые regression tests и isolated locale helper, перечисленные в transfer-inputs.json. Новый тест PLACE-QA-08 и PO должны уехать вместе.
3. Включить этот guide, companion index/verification, AGENTS и канонические .agents, актуальный module acceptance журнал, планы/QA отчёты с referenced findings/standalone prompts. Сверить transitive Markdown links: перенос одного REPORT без его evidence даст неполный пакет.
4. Native PNG/screenshots и result JSON/CSV/commands нужны, если переносится доказательная база целиком. До push проверить объём и Git hosting limits; для крупных файлов согласовать подходящий bundle/LFS/archive с manifest и доступным местом хранения. Не удалять evidence ради успешного push и не помечать отсутствующие PNG как доставленные.
5. Исключить .env/credentials/env values, .tmp runtime state, .venv, production logs/dumps/records, DB volumes, test media/private documents и graph caches. QA fixtures только явно вымышленные; fixture passwords/токены тоже не копировать в Git. Shared ignored MO не отправлять вместо portable PO+build helper. Новому ПК нужны свои tools/builds/DB/cache/media/browser.
6. Перед разрешённым commit/push проверить только относящиеся к пакету необходимые проверки/secret scan и staged diff, затем показать точную ветку/remote/состав и выполнить действие согласно данному разрешению. Не запускать deployment scripts/production migrations/cleanup. Обновить handoff фактическим commit SHA и инструкцией получения ветки.
7. На другом ПК после fetch/pull проверить transfer manifest/наличие обязательных файлов и новый snapshot. Исторические PO hash применимы к истории, текущие source hashes и fresh build manifest — к новой сборке. Если ожидаемые fixes не приехали, сначала восстановить корректный согласованный source bundle; не повторять их реализацию по старому FAIL.

Подробные portable inputs и состояние Git на момент подготовки: [transfer-inputs.json](continuation-2026-10-11/transfer-inputs.json). Это нижняя граница нужных входов и inventory, а не разрешение автоматически добавлять все чужие файлы. [repair-index.json](continuation-2026-10-11/repair-index.json) содержит 73 группы и coverage 76 ID. [verification.json](continuation-2026-10-11/verification.json) проверяет структуру/ссылки/coverage этого guide, а не application PASS.

## Что остаётся только на исходном ПК

Исторические стенды C:\kidsmap: recheck localhost:8841/PID16156, PostgreSQL loopback55446/container kidsmap-module01-recheck-20261011-r1, browser place-recheck-r1; PLACE-QA-08 repair localhost:8842/PID19364, PostgreSQL loopback55447/container kidsmap-place-qa08-fix-20261011-r1, browser place-qa08-fix-r1. Эти значения документируют выполненную проверку. На новом ПК их не запускать/не считать доступными, на исходном не останавливать и не пересобирать в ходе подготовки guide.

## Формат отчёта и закрытия задачи

Отчёт должен связывать фактический checkout/HEAD/dirty WORKTREE, выбранный scope, running source, изоляцию и locale manifest с точными выполненными проверками. Указывать: trigger/ожидание/факт/первопричину, что изменено и почему, команды/exits и итог counts без смешения observations с unique tests, UI save/reload/readback, raw evidence и native PNG/DERIVED различие, открытые ошибки/NOT RUN/SIMULATED, сохранность чужого состояния и следующий шаг. Закрытие действует только в проверенном profile; clean HEAD/production/global module PASS отдельно не выводятся.

Этот guide фиксирует очередь на 2026-10-11. После каждого свежего ремонта/приёмки добавляй ссылку в следующий handoff и актуализируй индекс с проверкой уникальности/aliases. Исторический ledger/module13 MASTER не переписывай так, будто тогдашний аудит был PASS. Новый итоговый MASTER создаётся по новым evidence.

## Current LOCAL module01 acceptance — 2026-10-12 r6

Module01 LOCAL PASS on /home/ramin/kidsmap task33-progress HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +approved dirty WORKTREE; active_run NONE. QA14 remaining modal close/focus cause accepted; QA09–13 retained/rechecked. [Final943 native assertions/470 unchanged-source backend/JS52PASS1SKIP](module01-full-2026-10-12-r6/REPORT.md), [QA14 scoped report](place-qa14-close-fix-2026-10-12-r1/REPORT.md), [next PLAN ORG-QA-01](module01-full-2026-10-12-r6/next-prompt.txt). This newer checkpoint supersedes r5 OPEN for LOCAL module01; historical reports/76 IDs/73 tasks/88 blocks retained. Global corpus/external/production NOT RUN. Other modules not automatically started or accepted.

- Module08 MOD-QA-03 SORT — **scoped LOCAL PASS / whole MOD03 OPEN**, 2026-10-16: [REPORT](mod-qa03-sort-fix-2026-10-16-r1/REPORT.md), [verification](mod-qa03-sort-fix-2026-10-16-r1/verification.json). Approved four-file whitelist/filter/order/context fix for Event/Specialist; fresh6method RED/41assertionFAIL +2nativeFAIL →19target backendGREEN/1511accepted nativePASS,360real-order +360translated-label comparisons across36base/60reachable sidebar cells;92PNG. Six raw fixture-menu FAIL (missing trigger) replaced by55target supplementPASS; RU/AZ CLI143 cell checkpoints recovered, lost final epilogue not invented; own-seed PG write counters exact. RED semantics retained; two own RED PNG paths reused by GREEN and explicitly unavailable. Search-form status loss before sorting remains separate OPEN [3file PLAN](mod-qa03-sort-fix-2026-10-16-r1/SEARCH_FILTER_IMPLEMENTATION_PLAN.md), unmatched columns OPEN/NOT RUN; MOD04–08/full08/production NOT RUN. Foreign32129-entry files preserved except approved2backend files and this status note;71foreign containers unchanged; HEAD/branch/active_run unchanged.
