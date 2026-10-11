# Модуль 11: SEO, языковые URL и redirects — FAIL

Роль kidsmap-orchestrator; execution /root, 2026-10-11, 2026-10-11T10:12:28.375984+00:00. Definition .agents/agents/kidsmap-orchestrator/agent.md. Native/HTTP/stand evidence выполнены lead; bounded source seo-reviewer (/root/seo_source), existing tests integration-reviewer (/root/seo_tests) — независимые support tasks по фактическим definition files, с раздельным владением. Не выдаём source specialist за браузерного исполнителя.

AUDIT ONLY, только модуль 11. **7 OPEN:6 P2 /1 P3. Приложение не исправлялось.** Индексация поисковиками, production, commit/push/deploy NOT RUN. Новая проверка; старые отчёты — checklist/infra/dedup, не evidence.

## 1. Состояние области

Checkout **C:/kidsmap**, branch **task33-progress**, HEAD **8d188b316f800fbedf0b1e376905dfd4924cb1b6**. Это dirty WORKTREE + существующие .mo, не clean HEAD и не production. Snapshot2788 source files, digest **e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1**; runtime entry/startup/disk совпадают. Source/foreign preservation финально проверяет [verification.json](verification.json). Foreign active_run **NONE** сохранён. Required documents missing **0**, [documents](documents.json). Dirty PO не компилировались; реальные .mo hashes в [snapshot](snapshot.json). Ни чужие source/assertions/QA, ни чужие stands не исправлялись.

Свежий isolated PG17.11 container kidsmap-module11-20261011-r1, own volume e77bec37ee83741b05ff9f14c82631c05c2c428d0a56c88d559465b69511487d; localhost55442, module11/test_module11. DJANGO_TESTING=1, LocMem cache/email, свои media/private/unit-media и cookie names; credentials только ignored scratch, не artifacts. Backend outbound socket guard; browser external routes abort. Main localhost8827 PID18872 DEBUGTrue, затем own restart PID2428 DEBUGFalse для настоящих 404/410/error render, те же исходники и DB. Supplemental localhost8828 DEBUGFalse с тем же WORKTREE; PUBLIC_BASE_URL=localhost8827. Python3.12.15/Django6.0.2/Jazzmin3.0.1; native Chromium153.0.8010.12. [Isolation](isolation.json), [initial runtime](runtime-initial.json), [safe phase](runtime-safe.json), [final runtime](runtime-final.json). Foreign stands at entry:0; контейнеры/PID другого ПК не использовались. Собственные процессы/DB оставлены для review; это не следующий свежий run.

Codebase Memory graph-first C-kidsmap проверен, coverage metadata_changed/partial/gaps; полное соответствие индекса UNKNOWN. Relevant source fallback56files +15 HEAD comparison, no graph caches export. [Current source review](source-review.md), [corrections/HEAD](source-extra.md), [hashes](source-map.json). SEO audit/apply/rollback side effects inspected, ни одна application-fix команда не запускалась. Current dry-run branch returns unsaved object; историческая blanket «dryrunwrites» не перенесена на этот код.

## 2. Сильные стороны

Fresh HTTP/head отдельно от native: Place PK/legacy/wrong slug/query resolve; finite1–2redirect chains безloop. DefaultAZ безprefix, /az301, RU/EN localized paths. Не вводили несуществующее общее правило «всегда 1hop»: AZwrong-language slug/Eventwrong+query могут потребовать 2hops. Program не имеет отдельной публичной detail route. Organizations UUID и Activities PK стабильны. News/Article models/routes отсутствуют в текущих src/catalog+src/config; это bounded source absence.

Место, организация, программа, специалист и Event прошли по 2 ordinary name rename через native формы→save/reload (Place/Org/Program с candidate→approval); старые URL/canonical сохранились. Candidate/live сверены доapproval. Program approved name появился в embedded org content; source inheritance и Activity snapshot подтверждены. Event начальный legacy fixture был incomplete: готовность телефона/организатора/фото обеспечена через native UI перед повторнымsave. Specialist onsite также требовал места/региона: они добавлены native Select2/controls, штатный confirmation accepted. Никаких audited transitions прямым ORM save.

Native отвязка Place1 через preview→consent→confirm→receipt→reload: organization_id и Activity.program_id сталиNULL; публичные URL сохраняются, Course provider удалён, локальный snapshot данных сохраняется. Прямое Event→Org и Specialist practice→Place независимо разрешаются; [relations](relations.result.txt), [read-only DB readback](readback.json). Readback — explicit READ ONLY transaction/timeouts, не переход.

Все 3section flags OFF→ON через native admin save/reload:18lang/width combinations, visible200, скрытыеOrg/Spec404/Event410, metadata/HTML без карточечных данных, sitemap visibility. Event sitemap omission отдельно FAIL, даже ON. Private initial states all applicable models GET404 и exact exclusion XML, [HTTP final](http-final.json). States fixtures не доказательство native moderation lifecycle.

Place emptyEN translations canonicalAZ и no ENalternate; отображённый fallback не объявляется сохранённым переводом. Catalog page2 self-canonical/index; filters/empty noindex, strong>=5 landing index; backend boundary0/4/5 passed. Existing serializer protects script termination and preserves parsed text; native XSS sentinel0, JSON-LD parse/escaping PASS. Historical XSS/Event-schema-absence findings не воспроизведены.

Native RU/AZ/EN×360/390/768/1024/1280/1440: actual filled/empty/long/escaped/filter/pagination/redirect pages and final mutated entities. Tested geometry no horizontal overflow in these samples; native keyboard Tab/ShiftTab/Space/Enter/Escape, menu/language navigation→reload, focus style before/after and return focus. Footer verified after actual scroll, not initial observer-hidden fullpage bottom. Instrumented initial public matrix: no JS page exception/local asset failures; external blocked CDN/maps labelled SIMULATED/NOT RUN. Full contrast/each control/browser variants NOT RUN.

Native ownerRU1440 two-tab409 shows error summary and retains stale input; public live/canonical unchanged. SIMULATED local POST abort before server, input survives Back (autosave separately available), live unchanged; no claim for real provider/server/network outage. Local image delay1400ms/503 preserves head identity (RU/AZ/EN360/1440).30 own social preview captures, explicitly SIMULATED external-platform behavior; no external bots.

## 3. Реальные проблемы

[7 отдельные findings + самостоятельные repair prompts](FINDINGS.md). Generic social descriptions5entity; Specialist generic social title; Event logo instead uploaded photo; Event absent sitemap; editable specialist slug old404; SEO config editor500; Org/Activity HEAD405. Repro steps, role/endpoint, expected/fact, source/root cause, priority/dependencies and current evidence in each finding. Ни один дефект не исправлялся.

## 4. Tech debt

Изолированные SEO head blocks нуждаются в согласованном public payload. Specialist slug-only identity требует явной стабильности/alias policy; raw SEO JSON editor landing rename blocked500. Event/Specialist generic all-language hreflang differs from real-translation policy Place/Org/Activity: это source+runtime observation, **manual_review**, не отдельный подтверждённый дефект без общего product contract. Soft legacy Place detail visibility versus stricter list/sitemap quality — реальный текущий контракт, не автоматическая утечка.

## 5. Risks

7local findings source paths unchanged vs HEAD in scoped15file comparison: **pre-existing baseline source**, fresh WORKTREE reproduction. Audit не установил NEW REGRESSION. Всё checkout dirty; pristine-HEAD runtime/production/масштаб/search-engine effect UNKNOWN. Не переносим общую sitemap gap на утверждение «Google не индексирует»; HEAD405 также не доказывает этого. Multiworker invalidation и real integrations NOT RUN. Отдельный own DEBUGFalse process не использовался как доказательство shared-cache invalidation: flag checks выполнялись на одном PID2428.

## 6. Dead/legacy candidates

Legacy PK/root/default-language routes retained compatibility and tested redirect; не удалять. Retained incomplete published fixtures допускаются soft detail predicate, не evidence unauthorized publication. Source/graph не дают разрешения удалять модели/DB/roles. News/articles отсутствуют в bounded current source, никаких объектов не удалено. Старые reports и foreign run сохранены.

## 7. Tests gaps

Existing assertions unchanged. Primary110 methods: **106 PASS /3 FAIL /1 ERROR**, exit1;6native failure/error entries include subtests, это 4methods. Их неизменённый legacy flag-off repeat **4/4PASS**, exit0: configuration compatibility mismatch (stand explicitly flagTrue, normal TESTING defaultFalse), application regression не подтверждён. Additional JSON-LD/public_details/directory **25PASS**,9Linux guardFAIL before business assertions=**9 ENVIRONMENT /NOT RUN**, exit1. Event public **8/8PASS**, exit0. Across runs156method executions=143PASS/12FAIL/1ERROR; это repetitions/guard attempts, не 156unique passing product scenarios. [Main handoff](tests-review.md), [extra handoff](extra-tests-review.md), sanitized native logs and exact argv in [COMMANDS](COMMANDS.md).

Acceptance observations **2753 PASS /153 FAIL /175 NOT RUN**, total3081; это observations, не unique scenarios. [CSV](matrix.csv), [JSON](matrix.json), [role/lang/width summary](coverage-by-role-language-width.md), [counts](counts.json). 28rows excluded with reason: own incorrect one-hop/uppercase/private Program expectations, status collision, pre-click validation; fresh focused reruns supersede, original raw preserved. Incomplete own specialist fixtures, Select2/dialog/nav harness failures также отдельно, не product findings. [Exclusions](excluded-observations.json).

Явные [NOT RUN limits](coverage-gaps.json): landing native rename blocked500; Activity own name rename native not established; hidden lifecycle transitions initial-fixture only; native mutations/conflict/network outsideRU1440; other-model full private native error matrix; simulated loading/error/preview at360/1440only; real4-card native boundary; cooperation consent lifecycle; nine Linux donor DB invariant tests; full suite/CI/pristine-HEAD/production/indexing/bots/otherbrowsers/contrast/sharedRedis/realexternal integrations. Возможные privacy/SEO contracts за пределами фактически выполненного не объявлены PASS.

Fresh screenshots **724 PNG**, originals native, включая пустые/filled/long/error404/500/410, openmenu/select, focus, saved/reloaded/candidate/live/rename/detach/conflict/simulated network/image and30preview. [Hash/dimension manifest](screenshots-manifest.json). Manual rendered inspection: PC Place/focus, mobile long/Organization, Event360, native conflict1440, config500, oldslug404, Specialist360preview; automation checked geometry/DOM/metadata across18cells. Screenshot fullpage observer/footer not-yet-visible не объявлялся visual defect; footer actualscroll validated separately.

## 8. Recommendations

Передать 7 repair prompts отдельно на согласованное исправление; в текущем run не применять. Сначала SEO-QA-06 восстановление конфигурационного editor, затем native landing rename. SEO-QA-05 URL policy/aliases и 01–03 social blocks; SEO-QA-04 sitemap integration с privacy;07HEAD interoperability. Каждый будущий fix требует fresh isolated checks and regression evidence, сохранения чужих изменений и текущего canonical scope.

Журнал обновлён только row11; module12/13 untouched и NOT RUN. [Текст следующего чата](next-chat.txt) продолжает 12.13 после остальных. Следующий run создаёт собственный fresh стенд; текущие localhost8827/8828/55442 и PID — review state, не новое доказательство. В рамках этого run выполнен только 11.

## 9. P0/P1/P2/P3

P0=0,P1=0; P2=SEO-QA-01…06, P3=SEO-QA-07. Все OPEN. Overall **FAIL**, ограничения **NOT RUN**; нет утверждения «всё работает». [Final preservation/runtime/artifact checks](verification.json) и [exact commands/exit codes](COMMANDS.md).
