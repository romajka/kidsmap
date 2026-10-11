# Module12 — Просмотры, счётчики и аналитика

**DONE—FAIL;8 OPEN findings (6P2/2P3).** Date2026-10-11, AUDIT ONLY. Lead `/root` kidsmap-orchestrator and browser-qa sequentially; delegated support `/root/analytics_source` and `/root/analytics_tests`, actual canonical definitions read. Independent source/tests; browser evidence produced by lead. Application/rules/migrations/existing assertions untouched.

## 1. Состояние области

Checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE. `active_run: NONE` preserved. [Snapshot](snapshot.json), [foreign entry manifest](preservation-entry.json), [foreign stands](stands-entry.json), [required documents](documents.json): missing0. Historical content-entry and source-map used for checklist only. Production UNKNOWN/NOT RUN.

Fresh owned stand: localhost8829 enabled local analytics/owner flag;8830 deliberately disabled collection error-state profile (E103 silenced only there, not tests), same owned DB for no-write comparison. PostgreSQL17.11 container `kidsmap-module12-20261011-r1`/port55443; separate test_module12. Python3.12.15/Django6.0.2/Chromium153.0.8010.12. [Isolation](isolation.json): LocMem cache/email, own media/private-media,175 migrations; fictional actors/data only. [Runtime source attestation](stand-final.json) binds PID/startup/current hashes to2788 WORKTREE source files; digest `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`. Foreign module11 HTTP8827/8828+DB55442 and container unchanged, checked finally.

Browser uses normal Chrome UA because headless UA is excluded as bot; mobile UA separately emulated. External socket guard and browser route abort, both GA identifiers empty, no real Google requests. Filling/error GA graphs and selective repository failure are SIMULATED. Positive click/private-ID cases after port rejection use narrowly scoped SIMULATED route.fetch Origin/Referer proxy; raw unadapted403 retained. Config defaults disable local/owner analytics; explicit enabled profile tests conditional implementation, not deployment state.

Actual contract ([source-map](source-review/source-map.md)): canonical view per successful server Place render, no view dedupe; repeats add views. Subject key `(schema2,subject_type=place,subject_id=PK)`, legacy by place FK, not URL/slug. Visitor HMAC userPK or anonymous session, session HMAC separately; hashes not exported. Distinct identities include all eligible events, including contact-only. Metric aggregation excludes bots/staff/current explicit actor exclusions; owner is included. No automatic inactive-user exclusion assertion. Owner rolling `[now-30days,now)` and equally long previous window. Half-open Baku midnight/month boundary checks executed. SiteVisit currently unwired, raw0 consistent. GA KPI/chart data separate from local Place metrics; owner has five cards/no chart/filter/API, admin reports GA. No fabricated DB↔GA equivalence.

## 2. Сильные стороны

Native role views/exclusions, reload/back/forward/two-tabs, language/query/redirect visits and same-user mobile identity matched actual delta rules. Two admin edits→candidate→approve→public reload persisted all translations and stable localized slugs; old canonical URLs200 and obsolete slug redirects→canonical added exactly one entity view. Hide→404→republish retained history. Candidate/live readback, names normalized by backend whitespace stripping. Canonical functional/lifecycle actions include fresh aggregate before/after in result files; probes read-only with timeouts. Earlier aborted functional/lifecycle harness attempts retain traces/frames but their in-memory partial action arrays were lost; only later fully captured repetitions support canonical delta conclusions. Pure render/oracle checks refer to those recorded snapshots rather than claiming an additional transition.

Owner values matched DB summary; empty metrics and deliberate unavailable state rendered. Long published names tested18cells after native saves. Period links7/30/90/365 and invalid fallback30 tested; actual keyboard Enter navigation18PASS after correcting harness wait race. No horizontal document overflow found in applicable tested frames; layouts, long admin table paths, chart canvas, PC/mobile contact dialogs inspected in native PNG/contact sheets.

## 3. Реальные проблемы

|ID|Priority|Problem|Copyable prompt|
|---|---|---|---|
|[ANALYTICS-QA-01](findings/ANALYTICS-QA-01.md)|P2|Staff без model permission читает общую статистику|[prompt](findings/ANALYTICS-QA-01-repair.txt)|
|[ANALYTICS-QA-02](findings/ANALYTICS-QA-02.md)|P2|Событие принимается для активной приватной карточки|[prompt](findings/ANALYTICS-QA-02-repair.txt)|
|[ANALYTICS-QA-03](findings/ANALYTICS-QA-03.md)|P2|Легитимный Origin с портом отклонён|[prompt](findings/ANALYTICS-QA-03-repair.txt)|
|[ANALYTICS-QA-04](findings/ANALYTICS-QA-04.md)|P2|Период90 использует годовые GA KPI|[prompt](findings/ANALYTICS-QA-04-repair.txt)|
|[ANALYTICS-QA-05](findings/ANALYTICS-QA-05.md)|P2|GA unavailable/error показаны как нулевая аудитория|[prompt](findings/ANALYTICS-QA-05-repair.txt)|
|[ANALYTICS-QA-06](findings/ANALYTICS-QA-06.md)|P3|AZ дельта содержит русский текст|[prompt](findings/ANALYTICS-QA-06-repair.txt)|
|[ANALYTICS-QA-07](findings/ANALYTICS-QA-07.md)|P2|Отказ analytics write ломает публичную карточку|[prompt](findings/ANALYTICS-QA-07-repair.txt)|
|[ANALYTICS-QA-08](findings/ANALYTICS-QA-08.md)|P3|AZ административная аналитика имеет русские labels|[prompt](findings/ANALYTICS-QA-08-repair.txt)|

[Individual findings and prompts](FINDINGS.md) contain role/URL, exact steps, expected/actual delta, evidence, source cause, priority justification and dependencies. No fixes performed. Eight implementation/content failures exist in examined HEAD source or PO entries; completely clean checkout process not run. New regression not established. Simulated fault is conditional failure evidence, not production incident. AZ admin label failure08 confirmed by native18cells and15PO/MO key checks; PO global dirty preserved, specific entries matchHEAD. It shares locale build dependency SITE-QA-07, but wrong fuzzy drafts are a separate cause.

## 4. Tech debt

Legacy SiteVisit is defined but currently unwired; raw v1/v2 identity aggregation has distinct rules. Source comments/history do not define current deployment. Owner metric consumer supports Place, while raw Organization/Activity views have no equivalent owner statistics contract. Admin computes local metrics without rendering them; charts/tables fixed30days distinct from selected KPI window. Missing historical test name `test_public_favorites` replaced by actual existing `test_public_favorite_count`; dated app-template path absent, actual dashboard template in root templates. These are explicit scope facts, not missing mandatory document claims.

## 5. Risks

All conclusions LOCAL enabled QA profile. No production requests/credentials/config changes, commit/push/deploy. Real GA delivery, consent, property timezone, Google quota/latency remain NOT RUN. Current actor exclusions affect historical reports dynamically; no policy change inferred. UI errors do not reveal backend credentials (DEBUGFalse). External map/font/CDN transport blocked and classified SIMULATED, not local app failure. 31 relevant source/test files matchHEAD per [source snapshot](test-review/source-snapshot.json).

## 6. Dead/legacy candidates

SiteVisit lack of current caller is a research candidate only; service tests/history exist. No file, DB table, raw history or record was deleted. No orphan/dead-code conclusion from graph used to remove anything.

## 7. Tests gaps и coverage

Existing Django60/60 PASS exit0 (81.489s); own9 assertions4PASS/5FAIL exit1 (39.419s), canonical69methods64PASS/5FAIL. JS AI assertion scriptPASS exit0, phone DOM4/4PASS exit0 (DOM SIMULATED, not native). [Test report](test-review/REPORT.md), [exact commands/attempt exits](COMMANDS.md), [browser ledger](command-ledger.jsonl). Earlier unit/mock/harness attempts retained;79 raw completed Django method executions are not69unique methods. No existing assertion weakened.

Normalized scenario observations: **{'PASS': 542, 'FAIL': 79, 'NOT RUN': 25}**; [matrix CSV](matrix.csv), [matrix JSON](matrix.json), [counts](counts.json). Counts are observations including repeats, not unique tests; scenario/role/lang/width all recorded. [Reconciliation](reconciliation.json) explains initial port-blocked downstream NOT RUN, stale-navigation false FAIL, trailing-space normalization and login `next` query false FAIL. Raw evidence never overwritten; attempts copied by drive.py.

|Language|360|390|768|1024|1280|1440|
|---|---|---|---|---|---|---|
|ru|PASS:27, FAIL:3, NOT RUN:0|PASS:30, FAIL:5, NOT RUN:0|PASS:27, FAIL:3, NOT RUN:0|PASS:27, FAIL:3, NOT RUN:0|PASS:27, FAIL:3, NOT RUN:0|PASS:82, FAIL:14, NOT RUN:11|
|az|PASS:26, FAIL:5, NOT RUN:0|PASS:27, FAIL:5, NOT RUN:0|PASS:26, FAIL:5, NOT RUN:0|PASS:26, FAIL:5, NOT RUN:0|PASS:26, FAIL:5, NOT RUN:0|PASS:27, FAIL:5, NOT RUN:0|
|en|PASS:27, FAIL:3, NOT RUN:0|PASS:28, FAIL:3, NOT RUN:0|PASS:27, FAIL:3, NOT RUN:0|PASS:27, FAIL:3, NOT RUN:0|PASS:27, FAIL:3, NOT RUN:0|PASS:28, FAIL:3, NOT RUN:0|

Fresh native PNG **200**, [manifest/dimensions/SHA](screenshots-manifest.json); derived contact sheets are visual indexes, not counted as native frames. Sample [PC staff access](screenshots/admin-analytics-staff-1440.png), [mobile90](screenshots/admin-filled-ru-390.png), [error](screenshots/admin-error-ru-390.png), [AZ delta](screenshots/owner-filled-az-390.png), [public500](screenshots/public-analytics-backend-failure-ru-390.png), [long title](screenshots/owner-long-en-390.png). Additional zero-data/native dialogs/ACL/loading/focus frames included. Console/network per54 public/owner/admin frames in [telemetry](telemetry.result.txt); external aborted resource messages separately retained. Native CPU/browser screenshot loading capture is SSR pending navigation; no invented client loading/conflict form.

NOT RUN: Real GA ingestion/Realtime/property/Google timezone and report data disabled, credentials never used; Production not contacted; Chromium153 only; responsive viewport and mobile UA emulation, physical devices/Safari/Firefox NOT RUN; SiteVisit service has no current caller; native0 rows, direct service contract only; UI has five cards and fixed rolling30days; no chart/date filter/API implemented; Raw subject views exist, local metrics supports Place only; no equivalent owner graphs/API; No equivalent implemented Event/Specialist analytics history consumer, native cancellation metric check NOT RUN; Place has hide/draft/delete actions; no native archive action, exact archive history transition NOT RUN; Source sums distinct v1/v2 independently; cross-version identity migration not executed; Existing unit filters exercised; native toggle exclusion/inactive account history semantics NOT RUN; No retention purge/archive run; history checked hide/restore only; External seven-call latency/quotas not measured; Read-only cards have no editing/conflict form; two-tab public views exercised; Main port normal contact FAIL; positive transport recovery SIMULATED; contact endpoint injection panel RU1440 only. Scope gaps remain in matrix; audit completion means report completed, not full product PASS.

## 8. Recommendations

Resolve01ACL,03Origin and02subject eligibility; then07analytics failure isolation,04period/05state presentation,06/08localization. Respect current business source-of-truth, test expected deltas and privacy boundaries. Re-run relevant backend plus native cells after individually approved repairs; real GA later requires separate explicit authorized integration task. No auto repair or deployment.

## 9. P0/P1/P2/P3 и handoff

P0=0/P1=0/P2=6/P3=2 confirmed within local/SIMULATED scope. Final preservation/source/runtime/PNG/link/secret/oracle counts verification: [verification](verification.json), command `.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/verify.py`. Journal row12 only updated;13 remains NOT RUN. [Next chat text](next-chat.txt) starts13 final cross-module audit, with fresh evidence required and foreign stands preserved.
