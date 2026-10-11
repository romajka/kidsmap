# PLACE-QA-03 — Atomic pricing projection rebase implementation plan

> **For agentic workers:** Execute task-by-task only after the user approves this scope. Use the available `test-driven-development`, `systematic-debugging` and `verification-before-completion` skills. One sequential executor; no application changes in this planning phase, no commit/push/deploy. This plan does not authorize PLACE-QA-01/02.

**Goal:** Допустимая immediate-правка тарифа вместе с названием/адресом оставляет candidate пригодным к последующему одобрению, сохраняя реальные optimistic-concurrency конфликты.

**Architecture:** В существующей транзакции `publication.propose` сравнить snapshot до/после своей immediate-операции. При применении `pricing_plans` обновить в candidate base только фактически изменившиеся производные поля из существующего `PRICES`; согласовать старые scalar-значения, повторно присланные формой, с новой проекцией. Не менять `_immediate`, CAS, `revision_base_matches`, lock order, pricing projection algorithm или moderation gates.

**Tech Stack:** Django 6.0.2, Python 3.12.15, PostgreSQL 17 local image, Django tests and real Chromium owner/moderator flows.

**Spec:** [PLACE-QA-03](../../qa/module01-2026-10-09-r2/findings/PLACE-QA-03.md). [Fresh PostgreSQL evidence](../../qa/place-qa03-plan-2026-10-10/REPORT.md).

## Snapshot / authorization

- PLAN / AWAITING USER SCOPE APPROVAL. Current application files match HEAD.
- Checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; shared journal `active_run: NONE`.
- Preserve incoming modified `docs/qa/module-acceptance-prompts.md`, untracked module01-r1/r2, module02-r1, module03-r1, module04-r1 QA directories, both prior finding plans/evidence and all foreign stands.
- Fresh isolated PostgreSQL audit: six tests, three PASS, two FAIL, one ERROR, exit 1. Error is the reproduced business `Publication source conflict`, not environment setup. Actual moderator HTML from Django test client also suppresses approval. Rendered browser remains NOT RUN.

## Global constraints

- Only PLACE-QA-03. No production credentials, external integrations, commit/push/deploy, data repair or cleanup.
- `DJANGO_TESTING=1`, dedicated PostgreSQL DB/test DB, LocMem cache/email, separate media/private-media, synthetic actors and browser profile. Reject inherited service environment and `.env` loading.
- Do not disable `revision_base_matches`, field checks, dependency/author checks, content-version/revision-version CAS, readiness, `_immediate` conditions or `transaction.atomic`.
- Do not replace the entire candidate base with current live state: this can acknowledge unrelated concurrent changes.
- Do not treat `refresh_from_db` as missing: `_apply` already refreshes after pricing replacement. The defect is in the set of fields rebased, not stale ORM state.
- Preserve explicit scalar-price intent and candidate conditions; unchanged scalar echoes are different from user-requested changes. Existing assertions must not be weakened.
- This prevents new instances of the defect. Previously conflicted persisted revisions are not automatically rewritten or approved; a data-repair/migration scope is not authorized.

## Verified two-stage failure

1. Published place starts with canonical tariff and scalar prices at 15.00.
2. Owner submits a full candidate snapshot with changed name/address and tariff amount 18.00, initially saved as draft.
3. `_immediate` allows only the amount-only tariff change. `_apply` updates tariff and `sync_legacy_price_fields` projects 18.00 to live `price_from/price_to`.
4. `propose` rebases `pricing_plans`, but keeps scalar base at 15.00. The first revision contains only name/address, so it can still report no conflict.
5. A fresh editor snapshot/re-submit contains the current scalar values 18.00. Comparing them with the stale base 15.00 adds `price_from/price_to` to `changed_fields`.
6. Reviewer compares live 18.00 to base 15.00 for those fields and blocks. No concurrent editor is needed.

Fresh diagnostic files record both stages. A naive change that updates base without normalizing old scalar echoes is also unsafe: the first form still carries old 15.00 and could queue an unintended price rollback.

## Allowed files / ownership

Sequential django-reviewer scope; no independent execution claimed.

| File | Proposed change |
|---|---|
| `src/catalog/services/publication.py` | Bounded post-immediate projection rebase inside `propose` |
| `src/catalog/testcases/test_place_qa03_pricing_rebase.py` (new) | Projection, save/submit/review, intent, CAS, atomicity and concurrency regressions |
| `docs/qa/place-qa03-fix-2026-10-10/` (new) | Isolated QA harness, report, exact commands/exit codes, screenshots/readback |
| `.tmp/place-qa03-fix-20261010/` (ignored, new) | Synthetic fixture media, private-media, credentials and raw private diagnostics |

Read-only dependencies: `pricing_plans.py:sync_legacy_price_fields/replace_target_pricing_plans`, `volunteer_places.py:revision_base_matches/review_proposal`, `domain_admin/volunteer.py:review`, existing publication/pricing/owner tests. No UI/template/model/schema edit is currently needed.

## Task 1: Fresh runtime and RED regression

- [ ] Recheck HEAD/WORKTREE/active_run, source hashes and running stands. Record the approved scope and new run owner only in the new evidence directory; preserve previous reports.
- [ ] Use a new dedicated PostgreSQL container and new synthetic browser data. The locally available image is `postgres:17-alpine`; plain `postgres:17` was absent during planning. Prevent an implicit pull:

```powershell
wsl.exe --exec docker run --pull=never --detach --name kidsmap-placeqa03-fix-20261010 --publish 127.0.0.1:55438:5432 --env POSTGRES_DB=placeqa03_fix --env POSTGRES_USER=placeqa03_fix --env POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
```

Check port/name availability first; use a new suffix if occupied. HTTP suggestion is loopback 8817. Record actual endpoints and image identity. Do not reuse a foreign stand.

- [ ] Adapt the reviewed audit `qa03_settings.py` / `run_tests.py` into the new QA harness with `placeqa03_fix` and `test_placeqa03_fix`, separate media/private-media/cache/email/cookies and allowlisted environment. Add loopback-only serving for browser QA; block external sockets and browser routes. Capture commands through a native subprocess ledger; private synthetic credentials remain in ignored scratch.
- [ ] Repeat the actual UI baseline: create/submit/approve place, set a 15.00 tariff, edit name/address and price to 18.00 together, explicitly save draft, reload, submit, open reviewer. Record price already 18.00, identity still approved-old, candidate conflict and missing approval control. Browser evidence is required even though the PostgreSQL service/test-client baseline is already reproduced.
- [ ] Add `test_place_qa03_pricing_rebase.py`. Reuse the fixture pattern in `docs/qa/place-qa03-plan-2026-10-10/audit_projection_tests.py`, importing `PublicationFixture` and using real `publication.propose/review` and DB writes. The first three audited cases must fail before implementation. Preserve the historical RED files unchanged.

Core test sequence, using the existing fixture helper:

```python
patch = self.s.snapshot(self.place, 'place')
old_identity = (self.place.name_ru, self.place.address)
patch['name_ru'] = 'QA candidate identity'
patch['address'] = 'QA candidate address'
patch['pricing_plans'][0]['price'] = '18.00'
revision = self.propose(patch, submit=False)
self.place.refresh_from_db()
live = self.s.snapshot(self.place, 'place')
for field in self.s.PRICES:
    self.assertEqual(revision.base_snapshot[field], live[field])
self.assertFalse(self.s.PRICES.intersection(revision.changed_fields))
self.assertEqual((self.place.name_ru, self.place.address), old_identity)
patch = self.s.snapshot(self.place, 'place')
patch.update(revision.payload)
revision = self.propose(patch, revision_version=revision.version, submit=True)
self.assertTrue(revision_base_matches(revision, self.place))
self.approve(revision)
self.place.refresh_from_db()
self.assertEqual(self.place.name_ru, 'QA candidate identity')
self.assertEqual(self.place.address, 'QA candidate address')
self.assertEqual(self.place.price_from, Decimal('18.00'))
```

Import `Decimal` and `revision_base_matches`; fixture creates a published place with a canonical direct tariff at 15.00. Refresh after each write. Explicitly assert that scalar echo 15.00 is never left as a pending price rollback.

```powershell
.venv/Scripts/python.exe docs/qa/place-qa03-fix-2026-10-10/run.py test catalog.testcases.test_place_qa03_pricing_rebase
```

## Task 2: Bounded atomic rebase

- [ ] Keep every existing pre-write CAS/authorization/dependency/conflict check in its current order. Save `before_immediate = dict(live)` immediately before `_apply`.
- [ ] After `_apply` and fresh `snapshot`, derive a rebase set from the existing `immediate` keys plus only changed scalar projections when the immediate write contained `pricing_plans` on a Place. Use existing `PRICES`, whose five members match `sync_legacy_price_fields` outputs; do not add new immediate permissions.
- [ ] Before the existing pending update/filter, normalize only incoming projection echoes that equal the pre-immediate live value. This removes the old-form echo rather than proposing a rollback. Preserve explicitly different incoming values and existing intentional pending values; values already equal to the new base naturally disappear through the existing filter.

Proposed replacement for the current immediate block (inside the existing transaction):

```python
if immediate:
    before_immediate = dict(live)
    _apply(target, target_type, {k: patch[k] for k in immediate})
    live = snapshot(target, target_type)
    rebase_fields = set(immediate)
    if target_type == 'place' and 'pricing_plans' in immediate:
        projections = {k for k in PRICES if before_immediate[k] != live[k]}
        for k in projections:
            if k in incoming and incoming[k] == before_immediate[k]:
                incoming[k] = live[k]
        rebase_fields.update(projections)
    for k in rebase_fields:
        base[k] = live[k]
    for k in immediate:
        pending.pop(k, None)
```

Leave the existing `pending.update(...)`, equality filtering, revision-version increment and save logic after this block. The regression matrix below is the gate for this candidate implementation; refine only within this scope if an intent-preservation test disproves it.

- [ ] Do not rebase `name`, `address`, unrelated pricing projections with no observed change, relation dependencies or all live fields. Do not change `base_content_version` assignment independently of the existing pipeline.
- [ ] Do not alter `_immediate` eligibility for conditions/tariff structure, existing pending pricing, autosave or nested pricing. No new automatic repair on reads or moderation GET.

## Task 3: Regression, CAS and rollback gates

| Scenario | Acceptance |
|---|---|
| Mixed identity/address + amount; direct submit | Live price immediate, identity gated, review succeeds, no scalar echo rollback |
| Mixed draft → reload/save → submit | Base projections current; candidate contains intended identity only; review GET offers approval and POST succeeds |
| Price-only then repeated editor save | Stable tariff IDs/projections; no artificial conflict or pending rollback |
| Second mixed edit and subsequent resubmit | Correct revision/content versions and new identity; no duplicate tariff rows |
| All five scalar projections | Exact/from/range and lesson/month/eight-lessons fixtures exercise every changed projection, including transitions to/from null |
| Amount with tariff structure/conditions change | Existing moderation gating retained; no new immediate-field eligibility |
| Nonexplicit save / existing pending tariff or conditions | Existing candidate bundle preserved; no immediate leak |
| Explicit scalar values vs unchanged full-form echoes | Explicit intent follows existing immediate/gated rules; echoed old value cannot undo canonical projection |
| Candidate value deliberately reverted to live | Existing revert-to-live behavior retained; do not replace incoming globally with only changed keys |
| Stale content-version / stale revision-version / replay approval | Rejected before unintended write; state unchanged |
| Real overlapping second-writer identity edit | Review/source conflict retained; other editor's change preserved |
| Unrelated non-overlapping second-writer field | Existing allowed merge behavior remains; no global base reset |
| Failure after immediate pricing write before revision save | Exception rolls back tariffs, scalar projections, versions and revision together |
| Unsupported actor / ownership/dependency change | Existing ACL/dependency checks continue to deny |

- [ ] Use a test-only injected failure at `VolunteerPlaceRevision.save` after `_apply` to verify rollback; never mock `_apply`/CAS/projection functions to manufacture success. Compare serialized tariff rows, scalar values, revision payload/base/version and content version before/after failure.
- [ ] Add PostgreSQL `TransactionTestCase` with two separate connections and deterministic synchronization for stale CAS/overlapping writer. Use supported service paths and bounded waits; do not claim sequential ORM mutation proves lock behavior. Record actual concurrency outcome separately from browser two-tab results.
- [ ] Run the new suite and existing affected suites on the isolated test database:

```powershell
.venv/Scripts/python.exe docs/qa/place-qa03-fix-2026-10-10/run.py test catalog.testcases.test_place_qa03_pricing_rebase catalog.testcases.test_task33_publication catalog.testcases.test_task33_place_continuous catalog.testcases.pricing_plans_relational catalog.testcases.test_place_json_and_pricing_modes catalog.testcases.test_volunteer_admin
.venv/Scripts/python.exe docs/qa/place-qa03-fix-2026-10-10/run.py check
git diff --check
```

Capture exact labels, counts, failures/skips and native exits. No assertion changes to obtain green. New/unrelated failures require fresh baseline classification, not speculative attribution.

## Task 4: Real owner/moderator browser lifecycle

- [ ] On fresh synthetic data, approve the initial place, then perform mixed name/address + 15→18 amount edit through owner UI. Save/reload, submit, open moderator review, approve, reload owner and public detail. Verify intended live identity/address and canonical/scalar price 18.00; DB diagnostic confirms effective stored state.
- [ ] Repeat a price-only edit and a second mixed edit. Check stable tariff IDs and that old approved identity is retained until moderation.
- [ ] Use two owner tabs opened at the same versions: one saves, the stale one attempts save/submit. Verify controlled conflict and no silent overwrite. Use a distinct authorized synthetic second-editor identity to perform a genuine overlapping change; stale approval must remain blocked. Do not emulate that case solely with DOM mutation.
- [ ] Compare one supported non-overlapping second-editor update with existing contract. Keep title/address/pricing/readiness/ACL and publication verdicts separate in readback.
- [ ] Check the affected owner/review flow in RU/AZ/EN, 390 and 1440 for full roundtrip; smoke approval availability/conflict feedback at 768/1024/1280. Inspect DOM, keyboard/focus, console and network; capture screenshots before/after approve, after reload and in real conflict states.
- [ ] Save fresh `REPORT.md`, command ledger, isolation/snapshot manifests, RED/GREEN logs, structured DB readback, concurrency results, browser matrix/screenshots and input-preservation verification in the new evidence directory. Sensitive fixture credentials/cookies stay in ignored scratch.

Completion requires an approvable mixed edit without a competitor, successful persistence after real UI approval, and retained conflict detection with a competitor. Report all incomplete gates as NOT RUN. Production, external integrations, full unrelated suite and retrospective candidate repair remain outside scope.
