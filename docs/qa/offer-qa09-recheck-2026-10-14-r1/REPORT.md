# OFFER-QA-09 — CONFIRMED OPEN / PLAN ONLY

2026-10-14, root sequential, bounded Django/browser audit. Один ID OFFER-QA-09, P2, отдельный baseline вне исторических73tasks/76IDs. Application patches не выполнялись. [Конкретный двухфайловый план](IMPLEMENTATION_PLAN.md) ожидает одобрения. Module05 historical01–08 scoped CLOSED LOCAL; full ACCEPT05/global/external/production NOT RUN.

## Snapshot / preservation / authorization

Фактический checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + incoming dirty WORKTREE. `active_run: NONE` до/после. [Snapshot](snapshot.json), [source hashes](incoming-source.json), [final WORKTREE](worktree-final.txt), [verification](verification.json). Existing source/.agents/scripts/locale/common MO hashes сохранены полностью; только собственные QA/plan files и scoped status link. HEAD не доказывает WORKTREE/production состояние. No commit/push/deploy/production, чужие процессы/стенды/fixtures не менялись. Independent agent execution не заявляется.

Canonical instructions/active orchestrator/shared contracts продолжены из текущего контекста; relevant actual source перепроверен. Systematic-debugging/writing-plans/native playwright-cli workflow. Codebase Memory current root verified, ready;4relevant paths metadata_match/no_recorded_issue, generation2026-10-14T07:49:57Z; best-effort, не completeness proof. `review_form` caller admin review подтверждён actual code; graph caches не сохранялись.

## Native fresh reproduction

[Исторический finding](../offer-qa01-fix-2026-10-13-r1/FINDINGS.md) — checklist. Новый own fictional published Place имеет **только групповой primary exact20 тариф**; direct/scalar prices отсутствуют. Owner/admin synthetic. ORM создаёт только prerequisites/media, не candidate/decision transitions.

Настоящий admin export current JSON → import **только name_en** с schema/source/version → validate200 → native continue import → save → `/admin/volunteer/review/<own-place>/`. Complete nested tree в редакторе сохранился; proposed title есть в comparison. Однако false price warning и **no approve button** при390/1440. Public Activity reload всё ещё показывает собственную группу и цену20.

[Native result](recheck.result.json):8checks,6prerequisites PASS/2fresh FAIL. [PNG manifest](png-manifest.json):3PNG. Desktop [review PNG](screenshots/partial-review-price-blocked-1440.png) просмотрен: предупреждение «Перенесите существующую цену в тарифы…» и отсутствующая approve action. Sidebar state частично перекрывает левую область после resize390→1440; это не самостоятельная full layout acceptance и UI здесь не исправлялся. Warning/text/action дополнительно доказаны реальным DOM и READ ONLY state. Public [before PNG](screenshots/public-grouped20-before.png).

## READ ONLY cause / diagnostic separation

[Probe](probe.json), explicit READ ONLY, statement10s/lock2s: candidate pending, payload_fields **только name_en**, old live name unchanged; own active grouped price20.00, direct tariffs0. `review_form.is_valid=True`, cleaned nested_pricing=None, readiness false, единственная issue code=price/field=pricing_plans.

`src/catalog/services/volunteer_places.py:review_form` строит trusted data из content_snapshot (scalar/direct) +partial saved payload; при отсутствии candidate nested tree не добавляет полный действующий live tree. `src/catalog/services/place_readiness.py` считает grouped prices из cleaned_data.nested_pricing, поэтому не видит существующую цену. Backend readiness правила корректно требуют цену; ошибка adapter inputs.

**SIMULATED diagnostic**, не app PASS: в копию form data в памяти добавлен `serialize_nested_pricing(own_place)`; form cache пересоздан, validation/readiness true, issues пусты. Source/DB не изменены. Этот probe локализует причину, но не заменяет будущий regression/browser acceptance. Saved candidate payload и live дерево не дополнены и не опубликованы.

При explicit candidate nested tree требуется обратное: даже пустое дерево не подменять live prices. Existing serializer исключает archived Activity/OfferingGroup; inactive tariff flags сохранены, `_mapping_has_public_price` не считает inactive/optional plans ценой. Эти контракты должны сохранить negative regression tests из плана, а не более слабая price validation.

Classification: fresh current-WORKTREE source baseline, independent of completed08. Historical originalQA01 также воспроизводил09; текущий source проверен заново. Regression относительно неизвестного release/production NOT RUN. Business impact P2 — действующая карточка не проходит UI approval небольшой правки. Live privacy/price preservation prerequisites PASS; full security/ACL/concurrency acceptance NOT RUN.

## Own isolation / runtime / locales

Новый own profile `.tmp/offer-qa09-recheck-2026-10-14-r1`, PostgreSQL17.10 на `127.0.0.1:38995`, DB `offerqa09recheck_20261014_r1`, container `offer-qa09-recheck-2026-10-14-r1-pg`, unique volume `offer-qa09-recheck-2026-10-14-r1-pg-data`; HTTP `http://127.0.0.1:43061`, ownPID1586308. Значения относятся только к этому run.

[Runtime receipt](runtime-final.json): DJANGO_TESTING=true, entry=startup=disk,2806source files; exact own runtime cmdline проверен. Own DB/cache/media/private-media/cookies/LocMem email. Runtime внешние socket connections разрешает только own PostgreSQL; browser outside-base blocked. Fresh fictional data, no production credentials, checkout .env не загружался; credentials только own ignored0600 scratch. Все accepted01–08 и предыдущие QA DB/fixtures не тронуты; active_run не присвоен.

[Fresh locale manifest](locale-manifest.json): current RU/AZ/EN собраны helper `scripts/build_isolated_locales.py` через native GNU msgfmt, build/verify exits0. Sole LOCALE_PATHS `.tmp/offer-qa09-recheck-2026-10-14-r1/locales/locale`, manifest verified до django.setup. Common MO не переписывались. Own venv использует существующие пакеты; dependencies не менялись, старые .env/данные не копировались.

Primary native page errors0/unexpected local HTTP failures0; outside resources BLOCKED. Полный console/keyboard/responsive/locale acceptance на PLAN этапе NOT RUN. Backend regression tests НЕ запускались/новый test file НЕ создан; это этап repro+plan, не implementation. Setup system check exit0 не является module acceptance.

## Plan / handoff

[План](IMPLEMENTATION_PLAN.md): только `src/catalog/services/volunteer_places.py:review_form` и новый `src/catalog/testcases/test_offer_qa09_partial_review_pricing.py`. Minimal trusted live-tree fallback только если saved payload не содержит nested_pricing. Не менять readiness/domain/ACL/CAS/legacy/publication/schema/PO/templates/CSS/JS/CI/dependencies. Meaningful RED/GREEN для partial candidate, explicit empty/changed tree precedence, archived/inactive negative sources, direct/free modes, read-only preservation, stale/foreign review.4affected existing named guards проверены по actual AST, но не выполнялись этим PLAN.

09 **OPEN**, требуется concrete plan approval перед patch. [Approval prompt](next-prompt.txt). После scoped repair09 — ACCEPT-05 один раз на готовом модуле; module06 автоматически не начинать. Historical73groups/76IDs/88guideblocks не расширены новым09. Full ACCEPT05/global/external/production NOT RUN.

## Exact commands / exits

[commands.jsonl](commands.jsonl) — exact setup/browser sequence; `.command.json` — exact argv/exits/durations; `.txt` sanitized stdout/stderr. CLI run-code exit0 не является application PASS:2actualFAIL assertions сохранены. In-memory simulation явно отличается от native/source acceptance.

- `read-only-probe.command.json` exit0 — `.tmp/offer-qa09-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa09-recheck-2026-10-14-r1/runtime.py script probe.py`.
- `server.command.json` exit0 — `.tmp/offer-qa09-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa09-recheck-2026-10-14-r1/start-server.py`.
- `verification.command.json` exit0 — `.tmp/offer-qa09-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa09-recheck-2026-10-14-r1/verify.py`.

- `verification-handoff.command.json` exit0 — `.tmp/offer-qa09-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa09-recheck-2026-10-14-r1/verify.py`. Final source/runtime/snapshot/active_run preservation confirmed.
