# OFFER-QA-03: точный переход к ошибке тарифа — Implementation Plan

> **For agentic workers:** implement this plan task-by-task in the current chat. User instructions take precedence over skill defaults: no commits, no extra agents, targeted verification only; application changes require this concrete scope approval.

**Goal:** Ссылка в сводке ошибок раскрывает нужные занятие/группу/тариф и фокусирует конкретное ошибочное поле независимо от языка сообщения.

**Architecture:** Сохранить существующие локализованные `errors` и дополнить ответ параллельным машинным `error_targets`. Адрес поля переносить из `ValidationError.params` через форму и photo transport до owner UI. Адрес не извлекать из текста сообщения. Без изменений правил цены, возраста, биллинга или публикации.

**Tech Stack:** Existing Django/Python/PostgreSQL, plain JavaScript, native Chromium QA.

**Spec:** `docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-03.md`; fresh evidence `docs/qa/offer-qa03-recheck-2026-10-13-r1/REPORT.md`.

## Snapshot / authorization

- Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty incoming WORKTREE, `active_run: NONE`.
- PLAN / fresh recheck only at creation. Approval of OFFER-QA-01/02 does not authorize this new scope.
- Fresh native RU/AZ/EN at390px: bad price in activities[1].groups[1].pricing_plans[1], POST422, value0 retained; clicking error selects `program_id` in activity0. Three focus assertions FAIL as expected before patch. Separate second pass records viewport PNGs.
- Owned isolated process348816, `http://127.0.0.1:34529`, PostgreSQL17.10 DB `offerqa02fix_20261013_r1`, loopback60693. These are freshly verified recheck values, not portable commands.
- Runtime source/startup/disk match; DJANGO_TESTING=1, LocMem cache/email, one current RU/AZ/EN isolated locale root, no .env load, external browser requests BLOCKED, backend egress only own PG.
- Fictional fixture2activities/4groups/8plans, all live prices20; explicit READ ONLY readback: zero revisions, unchanged prices after three rejected saves.

## Global constraints

- Only OFFER-QA-03. OFFER-QA-04–09 and other enum caption localization are outside scope.
- Preserve incoming fixes in pricing_plans.py, publication invariants, ACL/CAS, existing tests and assertions, foreign WORKTREE/active_run/stands. No model/schema migration or additional dependencies.
- No commit/push/deploy/production, .env copying, old credentials/data, shared MO rewriting.
- Preserve message text/order and API `errors` shape for existing clients. Add metadata only; invalid/missing paths use a safe block fallback.
- No parsing localized messages. Selectors constructed only from validated path segments and safe indices/keys; never interpolate arbitrary server strings into selectors.
- Targeted tests per repair; full ACCEPT-05 after remaining module tasks, global suite later.

## Exact application scope

Modify:
1. `src/catalog/services/pricing_plans.py` — attach structured paths while preserving canonical validators and messages; nested activity/group/plan prefix and field metadata.
2. `src/catalog/photo_views.py` — expose parallel targets from form errors.as_data() on existing invalid-save response, preserving conflict metadata.
3. `static/js/permanent_place_photos.js` — retain `error_targets` through XHR rejection and save() result.
4. `static/js/owner_place_continuous.js` — use structured target for each summary link, open all ancestors and focus corresponding field; safe compatibility fallback.

Create:
5. `src/catalog/testcases/test_offer_qa03_error_targets.py` — behavioral service/form/HTTP regression tests and no-write checks.

Documentation/evidence only:
- this plan;
- new unique `docs/qa/offer-qa03-fix-2026-10-13-r1/` with runtime, commands, results, screenshots/PNG manifest, REPORT/FINDINGS/next-prompt;
- scoped status links in `docs/qa/continuation-and-repair-prompts-2026-10-11.md` and `docs/qa/module-acceptance-prompts.md`.

`src/catalog/forms.py` is an inspected consumer, not a planned mutation: `add_error('nested_pricing', exc)` already preserves ValidationError objects/params in as_data(). Prove this with a form regression. If that assumption fails, leave finding OPEN and present the actual required extension before modifying that file.

## Task1 — regression and machine path contract

- [x] Record new incoming WORKTREE hashes and current source/active_run; validate owned process identity before any control. Prepare own unique QA profile, unique PG DB/cache/media/private-media/email and browser session, no inherited env or production credentials. Build current RU/AZ/EN using `scripts/build_isolated_locales.py` into that profile, verify manifest before django.setup, sole LOCALE_PATHS.
- [x] Add meaningful tests and run them before patch: service exception params lacks target, form lacks target, HTTP lacks error_targets and native focus remains wrong. Keep exact RED results.

Target contract:

```python
# ValidationError.params carries data without changing its translated message.
field_path = ['activities', 1, 'groups', 1, 'pricing_plans', 1, 'price']
# Existing form error key is still nested_pricing; targets align with each message.
error_targets = {
    'nested_pricing': [field_path],
}
# HTTP remains {ok:False, errors:{nested_pricing:[localized_message]}, ...}
```

Behavioral test core (fixture created with canonical Activity/OfferingGroup/PricingPlan factories):

```python
payload = serialize_nested_pricing(self.place)
payload['activities'][1]['groups'][1]['pricing_plans'][1]['price'] = '0'
with self.assertRaises(ValidationError) as raised:
    validate_nested_pricing(self.place, payload)
self.assertEqual(
    raised.exception.error_list[0].params['field_path'],
    ['activities', 1, 'groups', 1, 'pricing_plans', 1, 'price'],
)
self.assertEqual(PricingPlan.objects.get(pk=self.target_plan.pk).price, Decimal('20'))
```

Test scenarios in the new test class, subtests where appropriate:
- exact0, missing lower/upper range bounds -> price/price_min/price_max; second activity/group/plan index proof;
- reversed plan ages -> age_to; group reversed ages -> group age_to; group/plan disjoint ages -> offending plan age_from/age_to;
- recurring count0 and installment cycles0 -> corresponding billing input; no synthetic valid defaults;
- wrong number format -> active conversion field, retaining current rejection/message;
- form as_data() preserves params, localized messages under RU/AZ/EN have identical machine paths;
- native save endpoint422 returns unchanged legacy errors plus targets, no revision/live pricing writes;
- successful valid save still has existing semantics; foreign group ID remains rejected with safe block path, never misleading foreign-field address.

Explicit commands use own profile runtime with test labels:

```text
<own-venv>/bin/python <own-QA>/runtime.py test catalog.testcases.test_offer_qa03_error_targets --verbosity=2
```

## Task2 — attach metadata at canonical validation boundaries

- [x] Add optional `error_path=()` to normalize_pricing_plans; existing callers keep current signature behavior. Within per-plan ValidationError catch preserve existing first-error message/order, code and params, add field_path consisting of prefix + pricing_plans/index + actual error_dict key. Generic plan errors target plan block, not an invented field. Track active conversion field for numeric-format exceptions.
- [x] Enumerate activities/groups in validate_nested_pricing; pass prefix to normalize_pricing_plans. Attach paths to `_editor_values` per-field failures via optional prefix, preserving default behavior for unrelated callers. For relational age checks select canonical age_from/age_to control; activity/group structure/ID/taxonomy errors target corresponding block. Do not loosen permitted keys, ownership checks or age bounds.

Helper interface:

```python
# local helper in existing pricing service, no new module/refactor
# Returns ValidationError whose original message/code/params remain readable.
def _error_with_path(error, field_path):
    params = dict(error.params or {})
    params['field_path'] = list(field_path)
    return ValidationError(error.message, code=error.code, params=params)
```

Use on scalar error_list members. Do not stringify errors before capturing error_dict field names. Existing translated “Тариф…” wrapper remains the user text; retain number/error formatting params alongside field_path.

- [x] Build error_targets in photo_views from the same form.as_data() order as errors. For each scalar error with no path use null target; emit only additive metadata. Keep existing candidate_version_conflict response untouched.

## Task3 — transport and correct native focus

- [x] Carry body.error_targets through every XHR/save rejection/result branch in permanent_place_photos.js, including preserved conflict handling and retry. Do not drop metadata at the photo adapter boundary.
- [x] Change showErrors(errors, targets={}) to render each message as its own button, aligned with its target. Existing ordinary scalar fields and legacy array/string errors remain supported. Clear prior summary-owned aria-invalid/aria-describedby before rebuilding, retaining unrelated descriptors.
- [x] fieldTarget uses structured segment array; validate nonnegative safe integer indices and whitelist names, locate inside `[data-pc-offerings]`. Accept activity/group/plan block paths and final `[data-offering-key]`. Billing/age/name fields must be included. For missing/invalid path use existing block fallback rather than translated-text regex.

UI interface:

```javascript
function showErrors(errors, targets = {}) { /* one message and matching target per button */ }
function fieldTarget(name, path = null) { /* validated segments, no message parsing */ }
// Save result call site:
showErrors(result.errors || {}, result.error_targets || {});
```

- [x] Keep goTo's native details opening and focus. Open advanced details ancestor for billing fields; scroll/focus target visibly without sticky controls obscuring it. If control is intentionally hidden due inactive billing mode, choose visible safe parent control rather than creating a new business rule.

## Task4 — targeted acceptance / handoff

- [x] GREEN same new regression tests. Run affected existing service/form consumer guards only:

```text
catalog.testcases.test_task33_pricing.GroupPricingTests.test_target_scoped_roundtrip_and_foreign_ids
catalog.testcases.test_task33_pricing.GroupPricingTests.test_group_age_conflict_and_currency_are_not_silently_coerced
catalog.testcases.test_task33_pricing.GroupPricingTests.test_json_ui_validator_distinguishes_v1_from_nested_v2
catalog.testcases.test_task33_place_continuous.ContinuousPlaceFormTests.test_group_age_conflict_and_foreign_group_id_are_rejected
catalog.testcases.test_task33_place_continuous.ContinuousPlaceFormTests.test_published_group_price_edit_is_candidate_until_approval
```

No repeated OFFER01/02 full runs, no no-label test wrapper, no changed existing assertions.

- [x] Native RU/AZ/EN ×360/390/768/1024/1280/1440: 2activities/2groups/2plans, wrong exact price at index1/1/1, close all details, actual save422, click actual error button; expected price focused, correct ancestors open, value0 retained, wrong branches remain closed. Screenshot viewport focus and error summary, geometry/console/network.
- [x] At390 in each language: price range max, reversed group/plan age, recurring count0, installment cycles0; keyboard Tab/ShiftTab around target, advanced disclosure; repeated submit leaves no stale ARIA reference. Correct bad value via UI, save/reload and explicit READ ONLY candidate/live readback. Valid candidate changes only on successful save; prior live price untouched until actual moderation approval.
- [x] Inspect affected shared pricing consumers: existing admin nested editor remains usable and localized error messages not lost. Direct pricing has safe existing fallback if it has no structured metadata. Broader direct-price editor focus improvements are outside this finding.
- [x] Verify process source hashes, current locale manifest, no application changes outside exactly5files, incoming bytes/active_run preserved; record precise command exits/test counts/assertions, screenshots hashes, blocked integrations and NOT RUN.
- [x] Close only OFFER-QA-03 if its executed acceptance passes. Full module05 and production remain NOT RUN. Next task is PLAN OFFER-QA-04, requiring fresh recheck; OFFER09 remains OPEN.

## Execution receipt

Approved by user in this chat and executed2026-10-13. Exact five application/test files,14targeted methods PASS,361native assertions PASS,96accepted PNGs+3diagnostic copies, READ ONLY candidate/approval readback. See `docs/qa/offer-qa03-fix-2026-10-13-r1/REPORT.md` for retained harness/fixture failures and NOT RUN. OFFER-QA-03 CLOSED LOCAL only. No full module/global/production PASS.
