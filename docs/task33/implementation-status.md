# KidsMap №33 — журнал состояния

Обновлено 2026-10-02. Working checkout /home/ramin/kidsmap. LOCAL HEAD c52b871ce5c18656a9eaf9854e66255c2629364e; до пакета WORKTREE clean. Пакет docs/task33 untracked/dirty фиксируется отдельно; HEAD не включает его. PRODUCTION UNKNOWN.

## Текущий запуск

active_run: NONE.
current_scope: stage20 DONE locally; see reports/20.md. No active implementation.
source_head: c52b871ce5c18656a9eaf9854e66255c2629364e; dirty WORKTREE stages05–20; stage20 final20-artifact SHA in reports/20-source-manifest.json, snapshot /tmp/kidsmap-task33-stage20-final-20261002. HEAD does not include implementation.
next_stage: stage21 NOT_STARTED; separate request required. Production NOT_RUN.

## Контрольные точки

- Перенос домой 2026-10-02: пользователь отдельно разрешил commit/push ветки `task33-progress`, main/deployment запрещены. Scope — сохранить реализацию 05–20 и docs/task33, подготовить продолжение с21; сам21 не запущен. Инструкция и отдельный QA archive — [home-handoff.md](home-handoff.md). Исторические HEAD/WORKTREE/NOT_RUN формулировки ниже относятся к завершению соответствующих этапов до переноса.

- Общий план: APPROVED пользователем (прямое PLEASE IMPLEMENT THIS PLAN).
- Owner макеты 02: CREATED / ACCEPTED / APPROVED — owner-02-r1; design/acceptance.md.
- Admin/public макеты 03: CREATED / ACCEPTED / APPROVED — admin-public-03-r1; design/acceptance.md.
- Isolated baseline 04: DONE / PostgreSQL17.10;1231 tests,28 failures+4 errors,0 skipped; known baseline recorded, application NOT_GREEN.
- Specialist дополнительные макеты: NOT_CREATED / NOT_APPROVED.
- Production launch: NOT_REQUESTED / NOT_RUN.

## Этапы

| № | Этап | Статус | Evidence / остаток |
|---|---|---|---|
| 01 | Документы и пакет заданий | DONE | reports/01.md: 28 prompts, 40 Markdown files, 37 local links; package validation PASS |
| 02 | Макеты создания и кабинета | DONE | owner-02-r1; 7 HTML входов, 420 browser cases, 28 flows, 46 PNG; независимый review 43/43 PASS; user acceptance owner-02-r1 ACCEPTED2026-09-29 |
| 03 | Макеты админки и публичного сайта | DONE | admin-public-03-r1; 13 HTML, 924 rendered cases, 38 flows, 5 regressions, 62 PNG; independent273/26 PASS; admin-public-03-r1 ACCEPTED2026-09-29 |
| 04 | Изолированная среда и baseline | DONE | reports/04.md; isolated PostgreSQL,1231 tests/28F4E; checks+migration150/unapplied0+SQL repeats+independent review PASS; app baseline failures retained |
| 05 | Совместимая схема каталога | DONE | reports/05.md;31 schema tests + own independent31 PASS; migration151/unapplied0; full1262/28F4E exact baseline04,0 new regressions; SHA/preservation verified |
| 06 | Владение и принадлежность организации | DONE | reports/06.md; parent70 + independent70 PASS,152 migrations/0 unapplied; full1301/32F8E:31 retained baseline records +9 explained contract outcomes; source SHA/preservation verified |
| 07 | Сотрудники и разрешения | DONE | reports/07.md; parent106 + independent106/7negatives/legacy retention PASS; final full1336/34F8E=40retained06+2superseded expectations; source SHA/preservation verified |
| 08 | Публикации и редакции | DONE | reports/08.md; 37 new tests PASS; full1373/101F13E old-suite incompatibilities classified, application NOT_GREEN; Chromium42/6 PASS; independent SHA50 PASS; cleanup PASS |
| 09 | Серверные черновики и автосохранение | DONE | reports/09.md; 17 new tests + independent17 PASS; full1390/101F13E exactly baseline08 problem records, application NOT_GREEN; Chromium42/6 + offline3 PASS; migration156/unapplied0 |
| 10 | Тарифы и совместимость | DONE | reports/10.md; target + independent 15/15 PASS, full1405/101F13E exact114 baseline09, no new problems; Chromium21/3 import/1 draft save PASS; migration157/unapplied0; source SHA25 PASS |
| 11 | Инструмент переноса | DONE | reports/11.md; target+independent12/12 PASS, full1417/101F13E exact114 baseline10, added0; migration158/unapplied0; source SHA6 PASS; production NOT_RUN |
| 12 | Кабинет организаций | DONE | reports/12.md; final domain85/85, full pre-detach1427/exact114 baseline, Chromium126/126 + affiliation POST5/5 + locale6/6; source SHA17, production NOT_RUN |
| 13 | Новая форма места | DONE | reports/13.md; targeted138/138 PASS, independent Chromium42/42 + focused copy/photo/draft/concurrency checks PASS, source SHA12/12; full suite deferred, production NOT_RUN |
| 14 | Программы и группы | DONE | reports/14.md; final domain173/173 PASS, migration159/0, independent Chromium63/63 + focused flows/RU fix PASS, source SHA16/16; full application suite deferred, production NOT_RUN |
| 15 | Административные редакторы | DONE | reports/15.md: hierarchy editors, versioned reviewer-only unpublish, domain143/143 + final admin16/16, independent Chromium 147-cell + final60/60 + unpublish48/48; source SHA16/16 |
| 16 | Модерация и волонтёры | DONE | reports/16.md: core hub+SLA36/36, broad199/0F1 known baseline E, independent security20/20, Chromium84/84+42/42+9/9; SHA31/31 |
| 17 | Служебные уведомления | DONE | reports/17.md: inbox/outbox/runner, targeted11/11, broad112/112, migration161/0, independent security + Chromium42/42+6/6; SHA14/14, residual timing risks documented |
| 18 | Публичные страницы | DONE | reports/18.md: details/resolver,122/122+final15/15, independent browser105/105+21/21+24/24, security; catalog card21/21 with separate B18-04 page overflow; SHA16/16 |
| 19 | Точный поиск и карточки | DONE | reports/19.md; isolated129/129, independent31/31, browser147/147+final42/42; final source SHA |
| 20 | Карта и общие площадки | DONE | reports/20.md; isolated133/133+final18/18, independent46/46, Chromium105 cells+134/31/47 focused; source SHA20/20 |
| 21 | Локализация, URL и SEO | NOT_STARTED | — |
| 22 | Отзывы и версии реакций | NOT_STARTED | — |
| 23 | Репетиция и приёмка R1 | NOT_STARTED | — |
| 24 | Основа специалистов | NOT_STARTED | — |
| 25 | Интерфейсы специалистов | NOT_STARTED | — |
| 26 | Основа событий | NOT_STARTED | — |
| 27 | Афиша и календарь | NOT_STARTED | — |
| 28 | Итоговая приёмка R2 | NOT_STARTED | — |

## Как обновлять

Статусы NOT_STARTED / IN_PROGRESS / REVIEW_PENDING / BLOCKED / DONE. При запуске запиши active_run, actual HEAD, dirty/untracked файлы и scope; если другой запуск работает, не захватывай lock автоматически.
DONE требует критериев этапа и свежих проверок; прототип создан и макет принят — разные состояния. Не объявлять application tests PASS по документационным проверкам.
Reports/NN.md содержит exact commands, snapshot, changed source artifacts (sha256 при dirty коде, без самохеширования отчёта), результатов reviewers и NOT_RUN. При exit снимай active_run и указывай следующий доступный этап. Сохраняй историю уже законченных этапов.
Внешний blocker, например отсутствие PostgreSQL/browser/независимого reviewer, пишется конкретно; pending dependency не означает разрешение пропустить проверку.

## История запуска 02

2026-09-29, start 07:30Z, lead Codex primary / frontend-reviewer, support реальный runtime `/root/owner_review` / browser-qa. Prerequisite 01 DONE, active_run при старте none. Before snapshot: tracked clean, docs/task33 untracked; исходный пакет и sha256 сохранены в /tmp/kidsmap-task33-stage02-20260929-0730.

Этап выполнен в design/owner и stage документации. Финальные браузерные проверки: 420 AZ/RU/EN responsive/long/state combinations, 28 interactions, 46 screenshots 390/1280; independent review 43/43 PASS. Новые prototype bugs исправлены и перепроверены; environment tooling failures отделены в reports/02.md. Application/DB/external/production NOT_RUN; commit/push/merge не выполнялись.

DONE относится к созданию/проверке прототипов, не принятию пользователем. Owner checkpoint awaiting_user_review. Admin/public и Specialist макеты не созданы; baseline 04 не выполнялся. До 05–28 обязательны принятые owner/admin-public + baseline; до 25 ещё Specialist screens. Следующее поручение — prompts/03.md. Полный report: reports/02.md; hashes/source state: reports/02-manifest.json. После handoff active_run none.

## История запуска 03

2026-09-29, start08:04Z, lead Codex primary `/root` / frontend-admin, independent reviewer `/root/stage03_review` / canonical browser-qa. Prerequisites01/02 DONE, active_run none before start; исходные104 файла/sha256 сохранены в /tmp/kidsmap-task33-stage03-20260929-080408.

Созданы design/admin, design/public и общий shared03 runtime/harness/preview; 13 HTML и62 реальные PNG. Parent924 rendered combinations +38 flows +5 regressions PASS. Independent273 responsive cases +26 flows PASS на final prototype SHA eacda46b9eeaf5454bd081477a5f991cfeb73eb8582a33abc90b3f7a582ae150; console/resource/external errors0. Initial semantic prototype defects исправлены и проверены; harness failures отделены в reports/03.md.

DONE означает создание/проверку прототипов. Owner02 и admin/public03 оба awaiting_user_review, не приняты. Baseline04 не запускался;04 может идти отдельным поручением,05–28 ждут оба принятых набора и baseline; перед25 ещё Specialist acceptance. Application/DB/integrations/production NOT_RUN; никаких commit/push/deploy. Следующий prompt04. Report reports/03.md; dirty artifacts/hashes reports/03-manifest.json. active_run освобождён после review/checks и закрытия собственных preview/browser.

## История запуска 04

2026-09-29, start08:33Z, lead Codex primary `/root` / canonical integration-reviewer; independent `/root/stage04_review` / canonical database-reviewer. Prerequisite01 DONE, active_run был none. Before snapshot:195 docs/task33 files/hash saved `/tmp/kidsmap-task33-stage04-20260929-083308`;194 unchanged, journal only changed. Tracked/index source clean, HEAD c52b871ce5c18656a9eaf9854e66255c2629364e unchanged; new QA04/report files remain untracked as part of docs/task33.

Disposable PostgreSQL17.10/network none/tmpfs/owned Unix socket, clean env, isolated cache/media/locmem email. Discovery1091→explicit1231 unique IDs,140 omitted by original full; full labels corrected only in QA04. First full1231/29F4E exit33, sender override harness false failure corrected; bounded32tests/27F4E exit31. Final full1231/28F4E/0skip exit32;32 complete records. Concurrent create full FAIL twice/bounded PASS; no application fix claimed. System/migration checks PASS,150 applied/unapplied0; repeated synthetic ORM/HTTP queries stable,7HTTP200.

Independent own discovery/probe+safety7/additional negatives/capture+final aggregate/SHA review PASS. Exact commands/versions/failures/manifest in reports/04.md and04-results.json. All owned completed containers/scratch removed, active_run released. Raw logs/env/rows/SQL remain outside repo; browser/external/working services/production NOT_RUN. Application assertions unchanged, no commit/push/merge/deploy; owner/admin-public acceptance still pending,05–28 NOT_STARTED.

## История preflight05

2026-09-29, lead `/root` / canonical database-reviewer. Actual HEAD c52b871ce5c18656a9eaf9854e66255c2629364e, tracked/index clean;213 previous docs/task33 files saved before edits (snapshot path in reports/05.md). Dependencies01/04 DONE, QA04 reviewed source SHA MATCH. Both owner-02-r1/admin-public-03-r1 remain awaiting_user_review/NOT_APPROVED; required checkpoint blocks05 implementation. Explicit acceptance requested; no response recorded and acceptance not inferred.

Stage05 BLOCKED; only preflight/report/evidence/journal. Application schema/migrations/tests/review NOT_RUN, no production/next stages/commit/push/deploy. Previous artifacts retained; active_run released for handoff. Resume the same stage05 when explicit design acceptance arrives; existing stage authorization persists.

2026-09-29: preflight05 blocker resolved by explicit user response «Принимаю оба набора». Acceptance recorded in design/acceptance.md; resumed05 under existing authorization, no repeated permission request.

## Итог запуска05

2026-09-29, primary `/root` / canonical database-reviewer; independent `/root/stage05_review` / canonical django-reviewer. Оба design revisions приняты отдельным ответом пользователя «Принимаю оба набора», исторический preflight blocker разрешён. Реализована только добавочная схема05: семь новых models, nullable Place links/facts/positive versions, archive/PROTECT и locked integrity hooks, migration0117 после actual0116, meaningful PostgreSQL tests. Legacy Place save сохраняет новые readonly columns под прежним lock; reader/UI переключения нет. PricingPlan и все прежние миграции byte-identical.

Parent RED foundation1F, invariants27F, partial-save1F, stale legacy save1F воспроизведены до соответствующих fixes; две new Event fixture errors исправлены по обязательной category без изменения assertions. Final parent31/0F0E/0skip PASS, independent own31/0F0E/0skip +extra negative PASS на совпадающих final source SHA. Fresh empty DB151 applied/unapplied0; populated0116→0117 retains every old concrete value восьми synthetic records семи types и AZ/RU/EN HTTP200 URLs; три real PostgreSQL concurrency cases PASS.

Full canonical1262 unique executed IDs =1231old+31new,28 failures+4 errors/0 skipped,exit32,521.05s. Exact32 problem records/кратность совпадают с04; new/resolved0, новые31 PASS. Application NOT_GREEN due unchanged known baseline. Same-fixture SQL/HTTP counts exact-equal04. Disposable isolated PostgreSQL17.10/clean env/guards/cache/media/email; all owned cleanup PASS. Raw logs/SQL/rows/env /tmp only. Reports05/05-results/05-review/05-source-manifest фиксируют actual HEAD+dirty code, commands, IDs, SHA и execution identity.

Before snapshot213 files:209 byte-identical,0 missing; только README/decisions/acceptance/journal изменены по текущему stage checkpoint/status. Предыдущие reports/prototypes/QA04 не переписаны. Stage05 DONE, active_run none. Browser/external/production/06–28 NOT_RUN; no commit/push/merge/deploy. Следующий prompt06 только отдельным поручением.

## Preflight08 — блокировка

20260929-104233Z, Codex primary `/root` / canonical django-reviewer. Прямое поручение только08; implementation не начиналась: active_run принадлежит stage06 IN_PROGRESS, dependency07 NOT_STARTED, reports/07.md отсутствует. Принятие owner/admin-public сохраняется. Source HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty source05/06 сохранены с SHA/patch в `/tmp/kidsmap-task33-stage08-preflight-20260929-104233Z`; reports/08-preflight-manifest.json.

Только reports/08.md, manifest и эта запись/строка08; чужие active_run/current_scope/source_head/next_stage не менялись и не освобождались. Application/tests/DB/browser/independent review/production/09–28 NOT RUN; no commit/push/merge/deploy. Возобновить08 после завершения06, освобождения lock и DONE07; текущая авторизация08 сохраняется.

## Итог запуска06

2026-09-29 primary `/root` canonical django-reviewer, independent `/root/stage06_security` canonical security-reviewer. Только серверный ownership/create/claim/join/detach/transfer scope: CLAIM/PUBLICATION раздельно; no automatic verified/publication; обе current owner confirmations, informational/no grants, idempotency/ownership counters, approved detach snapshot/IDs/prices/reviews/contacts, transfer team suspension, cap10 removed/explicit duplicate choice. Новая0118 после0117; PricingPlan и прежние migrations/prototypes/QA tools сохранены. Критические reviewer findings воспроизведены RED и исправлены, включая admin stale request и real network edit/Org transfer TOCTOU.

Parent final70=39ownership+31schema0F0E0skip23.239s; independent own70/0F0E0skip22.636s,20 source SHA совпали. Check/makemigrations PASS, empty DB152 applied/0 unapplied; populated legacy retention+8 real PG races PASS. Full final1301 unique IDs/32F8E0skip597.743s exit40:all70 new/schema PASS,31 baseline records unchanged;9 superseded contract/fixture outcomes по ID (8 additional failing IDs и1 changed baseline outcome), unexplained0. Старые assertions не ослаблялись, application NOT_GREEN. Owner queries43→83 due fresh ACL; public/ORM/admin metrics otherwise equal05. Cleanup всех owned QA runs PASS. Production/browser/external/07–28 NOT RUN. reports/06/06-results/06-review/06-source-manifest фиксируют evidence/риски;active_run NONE.

## Preflight09 — блокировка

20260929-104446Z, Codex primary `/root` / canonical django-reviewer; поручение только09. Dependency08 BLOCKED (reports/08.md: implementation NOT RUN), active_run NONE после concurrent handoff06;06 DONE,07 NOT_STARTED. Дизайн checkpoint принят. HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty source snapshot/SHA/patch `/tmp/kidsmap-task33-stage09-preflight-20260929-104446Z`, inventory reports/09-preflight-manifest.json.

Stage09 BLOCKED; только report/manifest/строка09/history. Чужие active_run/current_scope/source_head/next_stage сохранены. Source/tests/DB/browser/external/independent review/production/10–28 NOT RUN; no commit/push/merge/deploy. Возобновить09 после DONE08; предварительно выполнить07 отдельным поручением,06 уже DONE.

## Итог запуска07

2026-09-29, primary `/root` canonical security-reviewer; independent `/root/stage07_review` canonical django-reviewer. Dependency06 SHA MATCH, checkpoints accepted, active_runNONE при старте;252 before artifacts сохранены (reports/07-before.json). Только07: selected/all-network grants, explicit Org/Program/branch actions, owner-only assignment, locked versioned invitations/current resolver and readers, transfer/revoke/leave/confirm, delegated branch owner/author, diagnostic legacy admin readonly. Additive0119, previous migrations/pricing/prototypes/reports сохранены. Старые assertions не менялись.

Final parent106=35new+70schema/ownership+1unchanged provenance0F0E0skip35.703s; independent106/0F0E0skip31.641s+7negative+populated0118→0119 3legacy team records retention PASS,30source SHA MATCH. Check/makemigrationsPASS,153applied/0unapplied;11real PG races covered incl3new. Full final1336/34F8E0skip:40exact06 problem records retained +2old business moderation/delegation expectations, unexplained0; all35new PASS. Transient direct/team metadata regression RED1F исправлена и перепроверена в fresh final/full, historical full source snapshot сохранён. Application NOT_GREEN. Owner queries83→119; остальные public/ORM/admin aggregates equal06. All owned QA cleanupPASS. Reports07/results/review/source manifest содержат команды/срез/риски.

Stage07 DONE; own active_run освобождён после handoff.08/09 реализации не запускались (старые blocker reports исторические); следующий08 только отдельным поручением. Browser/screenshots/external/production NOTRUN; no commit/push/merge/deploy.

## Stage08 implementation start

20260929-112946Z, direct user APPROVED IMPLEMENT only08. Dependency07 DONE/30 SHA MATCH, accepted owner/admin-public checkpoint, active_run NONE before claim. Snapshot /tmp/kidsmap-task33-stage08-20260929-112946Z: 271 artifacts preserved; HEAD c52b871ce5c18656a9eaf9854e66255c2629364e, dirty WORKTREE05–07. Production/09 NOT RUN.


## Повторный preflight08 — занятый active_run (20260929-123515Z)

Новый диалог получил прямое поручение только08 APPROVED IMPLEMENT. Lead canonical django-reviewer; registry/definitions/shared contracts и prompt08/README/decisions/journal/architecture/dependency07 прочитаны. Dependency07 DONE, owner/admin-public checkpoint ACCEPTED. Исторические blockers06/07 в начале этого отчёта больше не описывают текущие prerequisites.

Вход заблокирован другим запуском: `active_run: 20260929-112946Z / Codex primary /root / stage08 / APPROVED IMPLEMENT.`. Журнал содержит stage08 IN_PROGRESS и start112946Z; dirty WORKTREE уже включает publication.py, publication_forms.py,0120_task33_publication.py,test_task33_publication.py и адаптеры. Эта сессия не является владельцем существующего lock и не перехватывает его. Занятый lock не объявляется stale по совпадению `/root`.

HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, production UNKNOWN/NOT CONTACTED. Текущие dirty/untracked source и task33 artifacts сохранены в `/tmp/kidsmap-task33-stage08-parallel-preflight-20260929-123515Z`; inventory/SHA: [08-parallel-preflight-20260929-123515Z.json](08-parallel-preflight-20260929-123515Z.json). HEAD не представляет dirty код; report себя не хеширует как итоговый artifact, snapshot хранит только входное состояние.

Exact checks: `git status --short`, `git rev-parse HEAD`, чтение scoped файлов, Python snapshot/SHA verification — exit0. Первый sandbox вызов завершился exit1 до исполнения (`mountinfo path is not absolute`); approved escalation позволил чтение и запись только локальной документации/snapshot. Application tests/DB/browser/independent review NOT RUN: concurrent implementation prohibited. Source не менялся этой сессией; concurrent changes принадлежат текущему исполнителю.

Изменения этого preflight: отдельный manifest, append-only примечание в reports/08.md и журнале; active_run/current_scope/status08 не менялись. Все criteria08 остаются на проверке текущего исполнителя; DONE не заявляется. Продолжить08 после его handoff и освобождения lock либо в исходном диалоге.09 и production не запускались; commit/push/merge/deploy NOT RUN.

## Handoff08 и повторный preflight09 (2026-09-30)

Пользователь переключил поручение на **только09** до завершения08. Own run112946Z остановлен без удаления dirty source; current50 source/QA08 files и patch сохранены с SHA (reports/08-handoff-manifest.json,09-preflight-20260930-manifest.json). Stage08 REVIEW_PENDING: финальный targeted/full/browser/independent evidence не завершён или raw временные файлы после смены суток отсутствуют. Исполнитель освободил только свой active_run. Stage09 BLOCKED, потому что непосредственная dependency08 не DONE; никаких source09 изменений, production/commit/push/deploy нет. Возобновить08 и его проверки перед09.

## Возобновление08 (20260930-052128Z)

Прямое поручение пользователя завершить только08. Входной active_run NONE, dependency07 DONE, оба design checkpoints ACCEPTED, 50 SHA handoff MATCH, HEAD прежний dirty. Рабочий run снова занят только08;09 остаётся BLOCKED и source09 не начат.

## Итог возобновления08 — 2026-09-30

Run `20260930-052128Z`, primary `/root` canonical django-reviewer; independent `/root/stage07_review` canonical django-reviewer. Dependency07 DONE, both design checkpoints ACCEPTED, input50 SHA matched handoff. Final source50 SHA `83ae7b97a3963fed61b4a410de626a7f200e8fbe059e056fc61f551e87bbf5c0` matches independent reviewer before/after, HEAD unchanged dirty WORKTREE. Only three stage08 files changed after handoff to fix regressions; all previous changes preserved.

QA04 final full1373=1336old+37new/101F13E0skip exit114, all37 new PASS, 39 exact baseline07 problems retained,3 resolved,75 added records in65 old IDs grouped by obsolete token/candidate/readiness contract; application NOT_GREEN. Check/makemigrations PASS,155 applied/0 unapplied leaf0121, cleanup PASS. Independent37/0F0E plus legacy/stale/admin/volunteer ingress probes PASS, cleanup PASS. Real Chromium42 responsive AZ/RU/EN owner/admin cases+6 save flows PASS, screenshots42, bridge cleanup PASS. Source SHA/`git diff --check` PASS. Evidence: reports/08.md,08-results.json,08-review.md,08-review-evidence.json,08-source-manifest.json. Stage08 acceptance met; own active_run released.

Final dirty snapshot `/tmp/kidsmap-task33-stage08-final-20260930-0558Z` preserves 50 SHA-matched source/QA files and 7 handoff documents. Stage09 former dependency blocker resolved; stage09 work NOT_STARTED in this run and requires separate instruction/preflight. Production/external/commit/push/merge/deploy NOT RUN.

## Итог запуска09 — 2026-09-30

Run `20260930-061647Z`, lead `/root` canonical django-reviewer, independent canonical security-reviewer. Dependency08 DONE, checkpoints ACCEPTED, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged dirty. Серверный Draft API, migration0122, private normalized draft media, optimistic versions/current ACL, idempotent create/materialize, account-scoped browser fallback и UI state contract реализованы только в09. Входной snapshot 303 файла был сохранён и проверен до изменений; после прерывания диалога его `/tmp` копия недоступна. Итоговые 314 dirty/untracked файлов повторно сохранены в `/tmp/kidsmap-task33-stage09-final-20260930-075930Z`; SHA stage09 artifacts в reports/09-source-manifest.json.

Final targeted159/0F0E; full1390=1373old+17new/101F13E, все17 новые PASS, exact114 baseline08 records retained, added0/resolved0, application NOT_GREEN. Check/makemigrations PASS,156 migrations/unapplied0, disposable isolated PostgreSQL/cache/media/email/network none/cleanup PASS. Independent17/0F0E and SHA/source security review; SEC09-01 closed, SEC09-02 private orphan risk recorded. Real Chromium42 AZ/RU/EN ×7 widths ×owner/admin,6 saves,3 account/browser-only/offline probes PASS. Report reports/09.md, aggregate09-results.json, independent09-review.md. Active_run released after handoff; stage10/production/external/commit/push/merge/deploy NOT RUN. Next prompt10 only by separate instruction.

## Итог запуска10 — 2026-09-30

Run `20260930-080319Z`, lead `/root` canonical django-reviewer, independent `/root/stage10_db_review` canonical database-reviewer. Dependency09 DONE, design checkpoints ACCEPTED, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged dirty; 314 входных файлов сохранены с SHA до правок. Реализованы только PricingPlan XOR/target scope, canonical reader/writer, group scalar projection, v1 direct compatibility, versioned v2 nested JSON и публикационный кандидат. 25 source/QA SHA зафиксированы в reports/10-source-manifest.json; независимая сверка 10/10 MATCH.

Targeted15/0F0E и independent15/0F0E на isolated PostgreSQL PASS. Full final1405=1390old+15new/101F13E0skip exit114: все15 новые PASS, 114 exact baseline09 problem records retained, added0/resolved0; application NOT_GREEN. Check/makemigrations PASS,157 applied/0 unapplied leaf0123, cleanup PASS. Real Chromium21 AZ/RU/EN×7 widths +3 v2 UI imports +1 imported nested draft save with unchanged public content PASS,21 screenshots, loopback bridge cleanup PASS. `git diff --check` PASS. Reports: reports/10.md,10-results.json,10-db-review.md,10-source-manifest.json. Active_run released after handoff.

Migration rollback, production, external integrations, stage11+, commit/push/merge/deploy NOT RUN. Следующий этап 11 только по отдельному поручению.

## Stage11 run — 20260930-100400Z (in progress)

Dependency10 DONE; owner/admin-public accepted; active_run was NONE. Input 339 dirty/untracked files copied and SHA-manifested at `/tmp/kidsmap-task33-stage11-20260930-100400Z`; LOCAL HEAD c52b871ce5c18656a9eaf9854e66255c2629364e unchanged. Conversion code, migration0124, tests and operational migration-map are in progress. Production/12+ NOT RUN.

## Итог запуска11 — 2026-09-30

Run `20260930-100400Z`, lead `/root` canonical database-reviewer, independent `/root/stage11_review` canonical integration-reviewer. Dependency10 DONE, owner/admin-public checkpoints ACCEPTED, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged dirty; входные339 файлов сохранены с SHA,336 byte-identical после работ, изменены только journal/map/models init, missing0. Введены versioned mapping/run ledger, PostgreSQL read-only planner, private plan file, atomic small-batch apply с source lock/fingerprint/checkpoint, ручная очередь без угадывания, aggregate reconciliation, migration0124. Промежуточный P1 inherited DATABASE_URL найден независимым reviewer, исправлен fail-closed guard в обеих операциях и негативными тестами.

Targeted12/0F0E0skip и independent12/0F0E0skip на disposable QA04 PostgreSQL PASS; forced in-batch rollback, concurrent apply, повтор/продолжение, stale source, retained IDs/URL/media/favorites/reviews/reactions и dry-run DB counters включены. Final full1417=1405old+12new/101F13E0skip exit114: все12 новых PASS, exact114/114 baseline10 records retained, added0/resolved0; application NOT_GREEN. `check`/`makemigrations --check --dry-run` PASS, 158 applied/0 unapplied leaf0124; cleanup PASS. Evidence reports/11.md,11-results.json,11-review.md,11-source-manifest.json. Final dirty snapshot `/tmp/kidsmap-task33-stage11-final-20260930`. Stage11 DONE, own active_run released. UI не менялся; browser/external/production/12+/commit/push/merge/deploy NOT RUN. Следующий prompt12 только отдельным поручением.

## Итог запуска12 — 2026-09-30

Run `20260930-115638Z`, lead `/root` canonical frontend-reviewer, independent browser-qa review `reports/12-review.md`. Dependency11 DONE, accepted owner/admin-public designs, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged; dirty WORKTREE 05–12, source stage12 SHA17/17 в `reports/12-source-manifest.json`, stage11 conversion SHA6/6 retained. Initial 344-file /tmp snapshot was lost after turn interruption; auto-review later rejected broad resnapshot due possible sensitive artifacts. Safe scoped 17-source snapshot completed; no previous changes reverted.

Organization workspace: zero Org/branches/standalone states, create without address/branch, overview/branches/programs/team/about, common account navigation, direct Add Place for signed-in users, service-backed two-owner join/detach, manager selected-scope URL protection, draft/candidate/publication statuses and inherited contact source. Targeted11/11 PASS, final ownership+permissions+workspace85/85 PASS on isolated QA04 PostgreSQL; check/makemigrations PASS, 158 applied/0 unapplied, cleanup PASS. Last completed full pre-detach1427/101F13E exact114 stage11 baseline records, 10 new PASS; post-detach full run interrupted before result and not asserted. Application NOT_GREEN. Independent real Chromium126/126 AZ/RU/EN ×7 widths, interaction PASS, real join302/stale409/detach302 POST5/5, follow-up locales6/6, QA cleanup PASS; accepted prototype structural comparison recorded, pixel match NOT_MEASURED. Full evidence reports/12.md,12-results.json,12-review.md.

Stage12 DONE against requested criteria; active_run released after independent handoff. Successful rendered server-draft save, pixel-level match, external fonts and production remain NOT_RUN/UNKNOWN; source changes stage13+/commit/push/merge/deploy NOT_RUN. Следующий prompt13 только отдельным поручением.

## Handoff этапа 13 — 2026-09-30

Run `20260930-142327Z`, lead `/root` canonical frontend-reviewer, independent browser-qa. Dependency12 DONE, accepted designs; LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged, dirty WORKTREE 05–13. Entry scoped snapshot and final 10-source SHA manifest `reports/13-source-manifest.json` preserved; 10/10 SHA match. Continuous owner Place page, server/browser draft persistence, explicit save, public_space/business contact rules, candidate/live presentation implemented. Targeted isolated QA04 87/87 PASS, checks/migrations PASS, cleanup PASS. Independent Chromium preliminary 42/42 responsive and final focused draft/reload/concurrent conflict PASS; 63-cell final matrix not completed. Full suite deferred per user's test cadence; production/external/stage14/commit/push/merge/deploy NOT RUN.

Stage13 **REVIEW_PENDING**: Activity/OfferingGroup authoring with one simple activity block and expandable group plans/translations is absent, so three group tariffs and related publication/browser scenarios remain unverified. Follow-up also needs final browser matrix and server upload error. Reports: `reports/13.md`, `reports/13-review.md`. Own active_run released on handoff; stage14 cannot be treated as unblocked or started.

## Preflight14 — блокировка 2026-09-30

Прямое поручение только14. На входе active_run NONE, dependency13 REVIEW_PENDING с отсутствующим Activity/OfferingGroup editor и групповыми тарифами; owner/admin-public designs приняты. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged, dirty WORKTREE 05–13, 393 changed/untracked entries before this report. Scoped four-source snapshot `/tmp/kidsmap-task33-stage14-preflight-20260930-152904Z`, SHA и полный inventory `reports/14-preflight-manifest.json`. Только report/manifest/journal изменены, source14 не тронут. Stage14 BLOCKED; active_run не захватывался и остаётся NONE. Tests/DB/browser/review/external/production/15+/commit/push/merge/deploy NOT RUN. Завершить13 и получить DONE перед новым preflight14.

## Preflight15 — блокировка 2026-09-30

Прямое поручение только15. На входе active_run NONE, dependency14 BLOCKED (13 REVIEW_PENDING с отсутствующим Activity/OfferingGroup editor); owner/admin-public designs приняты. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged, dirty WORKTREE05–14, 395 changed/untracked entries before this report. Scoped six-source snapshot `/tmp/kidsmap-task33-stage15-preflight-20260930-153155Z`, SHA и inventory `reports/15-preflight-manifest.json`. Изменены только report/manifest/journal; source15 не тронут. Stage15 BLOCKED; active_run не захватывался и остаётся NONE. Tests/DB/browser/review/external/production/16+/commit/push/merge/deploy NOT RUN. Завершить13→14 до повторного preflight15.

## Preflight16 — блокировка 2026-09-30

Прямое поручение только16. На входе active_run NONE; dependency15 BLOCKED, поскольку14 BLOCKED и13 REVIEW_PENDING. Owner/admin-public designs приняты. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged, dirty WORKTREE05–15, 397 changed/untracked entries before this report. Scoped five-source snapshot `/tmp/kidsmap-task33-stage16-preflight-20260930-153427Z`, SHA и inventory `reports/16-preflight-manifest.json`. Изменены только report/manifest/journal; source16 не тронут. Stage16 BLOCKED; active_run не захватывался и остаётся NONE. Tests/DB/browser/review/external/production/17+/commit/push/merge/deploy NOT RUN. Завершить13→14→15 до повторного preflight16.

## Повторный preflight14 — 2026-10-02

Повторное прямое поручение только14. Входной active_run NONE;13 всё ещё REVIEW_PENDING (Activity/OfferingGroup editor и групповые тарифы не готовы), поэтому14 остаётся BLOCKED. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty WORKTREE с399 changed/untracked entries на входе. Четыре scoped source SHA совпали с предыдущим preflight; новый snapshot `/tmp/kidsmap-task33-stage14-recheck-20261002-051237Z`, inventory `reports/14-recheck-20261002-manifest.json`. Изменены только отчёт14, новый manifest и журнал. Active_run не захватывался. Application tests/DB/browser/review/external/production/15+/commit/push/merge/deploy NOT RUN. Следующий доступный шаг — закончить13; после DONE заново проверить14.

## Итог продолжения этапа 13 — 2026-10-02

Run `20261002-051702Z`, lead `/root` canonical frontend-reviewer, независимый browser-qa `/root/stage13_resume_browser`. Dependency12 DONE, owner/admin-public макеты приняты, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` не менялся; исходные 400 dirty/untracked путей inventory `reports/13-resume-entry.json`, итоговый scoped 12-source snapshot `/tmp/kidsmap-task33-stage13-resume-final-20261002-060244Z`, SHA12/12 совпадают по `reports/13-resume-final-manifest.json`. Предыдущие изменения сохранены.

Добавлены progressive Activity/OfferingGroup/групповые тарифы и серверный candidate→approval contract, draft restore, readiness и отрицательная валидация. Targeted isolated QA04 **138/138** PASS, PostgreSQL17, check/makemigrations PASS, 158 applied/0 unapplied, cleanup PASS. Независимый Chromium owner AZ/RU/EN ×7 widths 42/42 PASS; клавиатура, три групповых тарифа, server draft, второй контекст, конфликт409, live/candidate, ошибки формы, injected photo503→retry200 PASS. После последней текстовой правки отдельный RU Chromium probe PASS. Ограничения и точные команды — `reports/13.md`, `reports/13-resume-review.md`. Полный suite отложен по пожеланию пользователя до общей финальной проверки; baseline application NOT_GREEN не переоценивался.

Stage13 DONE; active_run освобождён. Stage14 NOT_STARTED и доступен только по отдельному поручению с новым preflight; предыдущие blocked preflights14–16 остаются историей. Production/external/commit/push/merge/deploy и этапы14+ NOT RUN.

## Итог запуска14 — 2026-10-02

Run `20261002-stage14`, lead `/root` canonical frontend-reviewer, independent `/root/stage14_browser_review` canonical browser-qa. Dependency13 DONE, owner/admin-public designs ACCEPTED, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged dirty; входные405 путей не сброшены. Финальный scoped16 source/QA SHA16/16 и полный dirty inventory412 записаны в reports/14-source-manifest.json; snapshot `/tmp/kidsmap-task33-stage14-final-20261002`.

Общая Program AZ/RU/EN/category и impact филиалов, отдельный `program.manage`, linked Activity с approved common snapshot и местным supplement, одна Group с возрастом/языком/расписанием и несколькими локальными тарифами, явное подтверждение `conditions_verified_at` реализованы. Pending редакции и local conditions сохраняются; stale date сбрасывается при правке условий. Migration0125 переименовывает поле без потери существующей даты. Targeted isolated QA04 173/173 PASS, check/makemigrations PASS,159 applied/0 unapplied, cleanup PASS; syntax/diff PASS. Независимый Chromium63/63 AZ/RU/EN×7 widths и focused access/impact/three-tariff/confirm PASS. RU localization finding закрыт отдельным browser recheck. Полный старый suite отложен по ранее согласованному ритму, application baseline NOT_GREEN не переоценивался. Evidence reports/14.md и14-review.md.

Stage14 DONE; own active_run released. Production/external/15+/commit/push/merge/deploy NOT RUN. Следующий prompt15 только по отдельному поручению.

## Итог запуска15 — 2026-10-02

Run `20261002-stage15`, lead `/root` canonical frontend-admin scope, independent `/root/stage15_browser_review` canonical browser-qa. Dependency14 DONE, accepted owner/admin-public designs, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged dirty; 412 entry paths preserved under `/tmp/kidsmap-task33-stage15-entry-20261002`. Stage15 source SHA16/16 and full final dirty inventory in `reports/15-source-manifest.json`; snapshot `/tmp/kidsmap-task33-stage15-final-20261002`.

Organization/Program/Activity/OfferingGroup editors use candidate service for draft/submit, reviewer service for approve, separate badges and current/candidate diff; staff invitation uses owner-authorized team service. `publication.unpublish` uses existing reviewer ACL, locked target, optimistic version and pending-candidate check; direct Place ModelAdmin save removed. Activity becomes published only on approval, Group inherits Activity publication and separately reports conditions verification. Place hidden carryover/explicit preview language/import target ID/hour-vs-condition UI and RU mobile overflow corrected. Broad ACL proposal was rejected by auto-review and not applied; narrower existing-ACL service was accepted and verified.

Isolated QA04 domain **143/143** PASS, final admin **16/16** PASS, check/makemigrations/cleanup PASS. Independent real Chromium intermediate147/147 HTTP/lang, final-source focused60/60 and unpublish48/48 HTTP/lang/overflow0; Place/Organization/Activity real synthetic POST, keyboard/confirm, diff escape, links7/7, static404/page exceptions0. BQA15-01/02 closed. Independent importer probe AZ/RU/EN: v2 export/own target3/3 PASS, foreign Group ID3/3 rejected, foreign Place ID3/3 blocked before apply; successful browser apply/save NOT RUN, server tests cover schema/target. Full old application suite deferred; baseline application NOT_GREEN not reevaluated. Evidence `reports/15.md`, `reports/15-review.md`.

Stage15 **DONE**; active_run released. Stage16 NOT_STARTED and requires separate prompt. Production/external/commit/push/merge/deploy NOT RUN.

## Handoff этапа 16 и preflight17 — 2026-10-02

Пользователь переключил прямое поручение с16 на **только17** до закрытия последней integration находки. Own run16 `20261002-083809Z` освобождён, исходный восьмифайловый snapshot сохранён, 29 текущих source/QA/localization/plan файлов скопированы в `/tmp/kidsmap-task33-stage16-handoff-20261002-093545Z` с SHA `reports/16-handoff-manifest.json`; LOCAL HEAD неизменён, dirty WORKTREE сохранён. Volunteer proposals, informational links, hub и localized UI реализованы. QA04 targeted20/20 PASS, broader199/0F1E (один ранее известный old assertion `name_az`), check/makemigrations/cleanup PASS. Независимый browser final84/84 AZ/RU/EN×7 и security20/20 на своём snapshot; после security review обнаружена ACL несогласованность общей SLA очереди для affiliation-only reviewer. Negative assertion добавлен, но исправление и корректный RED/GREEN запуск не выполнены до переключения; stage16 **REVIEW_PENDING**, не DONE. Evidence `reports/16.md`, `16-review.md`, `16-security-review.md`.

Preflight17: direct user request, dependency16 REVIEW_PENDING, accepted owner/admin-public designs, active_run после handoff NONE. `prompts/17.md`, README/decisions/status, architecture notifications, canonical django-reviewer проверены. 448 dirty/untracked путей на входе, read-only SHA входных source в `reports/17-preflight-manifest.json`. Stage17 **BLOCKED**; его application source, tests, browser, SMTP/runner, external и production NOT RUN. Нового active_run17 не было. Следующее действие — завершение16 по отдельному поручению, затем повторный preflight17. Commit/push/merge/deploy/18+ NOT RUN.

## Возобновление этапа16 — 2026-10-02

Прямое повторное поручение только16; dependency15 DONE, owner/admin-public accepted, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged, 451 dirty/untracked entries at entry; 29/29 SHA handoff source matched `reports/16-handoff-manifest.json`, сохранённая scoped копия `/tmp/kidsmap-task33-stage16-handoff-20261002-093545Z` не сбрасывалась. Own run `20261002-stage16-resume` занят только16; остаток SEC16-04 queue ACL и финальные проверки. Stage17/production NOT RUN.

## Итог возобновления этапа16 — 2026-10-02

Run `20261002-stage16-resume`, lead `/root` canonical frontend-admin scope, independent `/root/stage16_security_review` (security-reviewer) and `/root/stage16_browser_review` (browser-qa). Dependency15 DONE, owner/admin-public designs ACCEPTED, входной active_run NONE, handoff SHA29/29 MATCH. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` не менялся; все source stage16 в dirty WORKTREE. Финальный snapshot `/tmp/kidsmap-task33-stage16-final-20261002-102208Z`, SHA31/31 и полный inventory453 в `reports/16-source-manifest.json`; чужие изменения не сбрасывались.

SEC16-04 affiliation-only SLA queue ACL закрыт; расширены permission-scoped type filters/counters, RU/AZ/EN sidebar label и имя Organization в link rows. Значимые RED до исправлений и GREEN после них в `reports/16.md`. Финальный targeted isolated QA04 hub+SLA **36/36** PASS, check/makemigrations PASS, PostgreSQL17 applied160/unapplied0, cleanup PASS. Финальный смежный199/0F1E — тот же известный old `KeyError('name_az')` из stage08 baseline, без новых failures/errors, application baseline NOT_GREEN; полный suite не запускался. Независимый security20/20 PASS и SEC16-02/03/04 closed. Реальный Chromium первоначальный294/294, final hub84/84 и resumed affiliation-only42/42 AZ/RU/EN×7, filter3/3, label9/9, mobile submenu PASS; browser report `reports/16-review.md`. Python/JS syntax, msgfmt AZ/RU/EN, `git diff --check` PASS.

Stage16 **DONE** по его локальным критериям, own active_run освобождён. Исторический blocked preflight17 остаётся историей;17 теперь NOT_STARTED и требует отдельного поручения. Production/external/commit/push/merge/deploy/17+ NOT RUN.

## Запуск этапа17 — 2026-10-02

Прямое поручение только17; dependency16 DONE, owner/admin-public accepted, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged, 453 dirty/untracked paths на входе; 10 относящихся source SHA и scoped copy `/tmp/kidsmap-task33-stage17-entry-20261002-103001Z` в `reports/17-entry-manifest.json`. Исторический blocked preflight17 не менял application source. Own run `20261002-103001Z` занят только17. Production/18+/commit/push/merge/deploy NOT RUN.

## Завершение этапа17 — 2026-10-02

Run `20261002-103001Z`, lead `/root` canonical django-reviewer, independent `/root/stage17_security` security-reviewer and `/root/stage17_browser` browser-qa. Dependency16 DONE, accepted owner/admin-public designs, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged; все stage17 source остались в dirty WORKTREE. 14 source SHA и полный inventory в `reports/17-source-manifest.json`, scoped snapshot `/tmp/kidsmap-task33-stage17-final-20261002-1115Z`; чужие изменения не сбрасывались.

Inbox, durable transactional email outbox, dedupe, bounded SMTP retry, stale suppression, POST/CSRF invitation and join actions, локальный preview/`--send` runner выполнены. Final isolated QA04 targeted **11/11 PASS**, adjacent regression **112/112 PASS**, check/makemigrations PASS, PostgreSQL17 **161 applied/0 unapplied**, cleanup PASS. Первый смежный прогон дал один переменный старый ownership race (104/105), диагностический/финальный повторы прошли; details и риск в `reports/17.md`. Независимый security review без ACL bypass, остаточный P2 timing risk generic mail при cancel/SMTP; Chromium inbox42/42 AZ/RU/EN×7, join6/6, old-email focused PASS. Full suite, real SMTP/external, production NOT_RUN. `reports/17.md`, `17-security-review.md`, `17-browser-review.md` содержат точное evidence. Stage17 **DONE локально**, own active_run освобождён; stage18 только отдельным поручением. No commit/push/merge/deploy.

## Запуск этапа18 — 20261002-112210Z

Прямое поручение только18; dependency17 DONE, design checkpoints accepted, входной active_run NONE. Сохранены 465 файлов dirty WORKTREE и binary diff в `/tmp/kidsmap-task33-stage18-entry-20261002-112210Z`; entry SHA/inventory в `reports/18-entry-manifest.json`. LOCAL HEAD unchanged. Production/19+/commit/push/deploy NOT_RUN.

## Завершение этапа18 — 2026-10-02

Run `20261002-112210Z`, lead `/root` canonical frontend-reviewer, UI `/root/stage18_ui`, independent `/root/stage17_security` security-reviewer и `/root/stage17_browser` browser-qa. Dependency17 DONE, owner/admin-public designs ACCEPTED, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged; исходные465 файлов сохранены,460 неизменны,5 изменены в scope18, удалённых0.16 source/QA SHA и полный dirty inventory — `reports/18-source-manifest.json`, snapshot `/tmp/kidsmap-task33-stage18-final-snapshot-20261002`.

Organization/Place/Activity details, общие visibility/translations/contacts/prices/schema offers, current approved affiliation fallback, canonical category SVG, branch activity links, existing subject analytics/dedupe реализованы. Pending content скрыт, standalone не получает Org, detached approved local snapshot отделён от live Program. Final isolated QA04122/122 PASS; после последних branch/icon исправлений targeted15/15 PASS, check/makemigrations/cleanup PASS, PostgreSQL17 applied161/unapplied0. Независимый security SEC18-01 closed; Chromium detail105/105, final Org metadata21/21, canonical EDU icon24/24 PASS. Catalog card data/keyboard21/21 PASS, но whole-catalog9/21 cells имеют35px overflow (B18-04), остающийся после удаления карточек; точный источник UNKNOWN, вне изменённых cards, передан как ограничение для отдельно запускаемого19. Полный suite/реальные внешние интеграции/production NOT_RUN; весь каталог и сайт не объявлены зелёными.

Stage18 **DONE локально**; own active_run освобождён. Evidence `reports/18.md`, `18-results.json`, `18-browser-review.md`, `18-security-review.md`. Следующий prompt19 только отдельным поручением. Commit/push/merge/deploy и19+ NOT_RUN.

## Запуск этапа19 — 20261002-120112Z

Прямое поручение только19; dependency18 DONE, owner/admin-public designs ACCEPTED, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged; 484 dirty/untracked файлов и binary diff сохранены в `/tmp/kidsmap-task33-stage19-entry-20261002-120112Z`, SHA/inventory `reports/19-entry-manifest.json`. Own run занят только19. Production/20+/commit/push/merge/deploy NOT_RUN.

## Завершение этапа19 — 2026-10-02

Run `20261002-120112Z`, lead `/root` canonical django-reviewer; UI `/root/stage19_ui`, independent integration `/root/stage19_review` и browser `/root/stage19_browser`. Dependency18 DONE, accepted owner/admin-public designs, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged; all484 entry dirty/untracked files + binary diff сохранены. Final scoped20 source/QA/contract SHA и inventory/preservation — `reports/19-source-manifest.json`, snapshot `/tmp/kidsmap-task33-stage19-final-20261002`; deleted entry0, чужие изменения не сбрасывались.

Same Activity/group conjunction, one Place/dedupe, conservative unknown legacy, confirmed admission, mixed taxonomy counts, current Org-name discovery/page links, matched card groups/prices, batch catalog/new/home/favorites/suggestions реализованы. Budget controls/sorting/metadata promises удалены; old query parameters совместимы без ценового обещания. Independent price/age/timeline/query whitelist findings закрыты meaningful RED/GREEN. Age bounds/legacy age сохраняются через /new redirect/pagination/locale; no unknown Place→Activity category inference. B18-04 и B19-01/02/03 closed.

Final isolated QA04 **129/129 PASS**, check/makemigrations/cleanup PASS, PostgreSQL17 **161 applied/0 pending**. Independent final **31/31 PASS**, rendered-card SQL1/four=9/9; entry reader1/eight=6/41 versus batch8/8, timing synthetic/no load claim. Real Chromium primary **147/147**, final new+matched **42/42**, **275/275 focused assertions**, AZ/RU/EN×7 widths; resize/back/locale/keyboard/mobile and suggestions exact age/price/URLs PASS; JS/static4040, external Fonts/Maps blocked. Final AST14/14 and diff check PASS; independent snapshot SHA16/16 and12/12 match. Reports `19.md`, `19-review.md`, `19-browser-review.md`, `19-ui.md`, `19-results.json`.

Stage19 **DONE локально**, own active_run released. Unknown Activity/subcategory authoring remains conservative exclusion, large-catalog taxonomy memory/load NOT_MEASURED, historic full-suite/application NOT_GREEN not re-evaluated. Production/external/commit/push/merge/deploy/20+ NOT_RUN. Prompt20 only separate user instruction.


## Завершение этапа20 — 2026-10-02

Run `20261002-123827Z`, lead `/root` canonical frontend-reviewer; bounded home implementation `/root/stage20_home`, independent `/root/stage20_integration` integration-reviewer и `/root/stage20_browser` browser-qa. Dependency19 DONE, owner/admin-public ACCEPTED, входной active_run NONE. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` unchanged, входные503 dirty/untracked файла + binary diff сохранены. Финальный scoped20 source/QA/contract SHA20/20 и полный inventory/preservation — `reports/20-source-manifest.json`, snapshot `/tmp/kidsmap-task33-stage20-final-20261002`;491 entry files unchanged,12 changed in scope,deleted0.

Confirmed shared active Location даёт одну numeric точку со списком независимых Place; near/same coords остаются visual cluster без business/Org merge. Same PlaceListFilters/presentation18–19 применяется к list/catalog map/home GET API; filtered popup members/offers/prices, inherited contact presence, locale fallback mark и координатный route. No/invalid coords остаются в list с пометкой; missing counts считают businesses отдельно от venue pins. Ordinary/approved address/coordinate edit отсоединяет только target Place, shared Location/other businesses/historic Event fields preserved. Home async cancellation/clear-stale membership/zero/reset реализованы.

Final isolated QA04 **133/133 PASS**, final payload18/18 PASS, check/makemigrations PASS, PostgreSQL161 applied/0 pending, cleanup PASS. Independent **46/46 PASS**,14-source review и whole Event/stale/partial-save negatives; late glyph-only delta verified by browser. Real Chromium AZ/RU/EN×7 widths matrix105/105 +550 assertions; latest catalog21 cells +134 keyboard/resize/unavailable assertions, home31 filter/age6/zero/reset/API assertions, final home9 cases +47 console/focus assertions PASS. B20-01 malformed schedule SVG CLOSED, JS/application console0; source11/11 browser SHA MATCH. Node renderer/race/route/lang, AST11/11/diff PASS. Initial-home-query hypothesis rejected by actual canonical301 routing/browser; home URL policy unchanged. Exact commands and intermediate fixture/harness failures in reports/20.md,20-review.md,20-browser-review.md,20-home.md,20-results.json.

Stage20 **DONE locally**, own active_run released. Historical full-suite/application NOT_GREEN not reevaluated; large-catalog load and real Maps/clustering/CDNs/physical devices NOT_RUN. Production/external writes/commit/push/merge/deploy/21+ NOT_RUN. Next prompt21 only separate user instruction.
