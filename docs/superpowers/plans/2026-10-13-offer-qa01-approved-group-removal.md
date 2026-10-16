# OFFER-QA-01: approved group removal — Implementation Plan

> Execution: sequential in this chat, after explicit approval of this document. User instructions override skill defaults about subagents and commits. No commit/push/deploy/production.

**Status:** COMPLETE LOCAL for OFFER-QA-01, explicitly approved by user «да». Separate partial-review baseline OFFER-QA-09 remains OPEN; no expansion implemented.

**Goal:** A group removed from the complete owner offer tree disappears from public offers only after moderation approval, while its database history remains.

**Architecture:** Retain the existing candidate/live publication boundary. Add explicit complete-tree semantics to the pricing writer, with a non-destructive default for partial callers. Publication applies the complete `nested_pricing` snapshot inside its existing atomic, locked and CAS-checked transaction. Archive omitted groups/activities through their canonical archive method and refresh scalar price projections.

**Tech Stack:** Current checkout Django/Python/PostgreSQL; existing native owner and moderator interfaces. No dependencies/schema changes.

**Spec:** `docs/qa/continuation-and-repair-prompts-2026-10-11.md`, PLAN OFFER-QA-01; `docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-01.md`.

## Constraints and exact scope

Only OFFER-QA-01. OFFER-QA-02–08 are outside scope. Preserve ACL, source/candidate versions, program provenance, candidate/live separation, rejected candidates and historical rows. Do not delete business Activity/OfferingGroup records, infer removals from CSV or partial writer calls, alter constraints, loosen assertions, clear drafts or change UI/translations incidentally.

Application files to change:

1. `src/catalog/services/pricing_plans.py` — `replace_nested_pricing` only: explicit keyword-only `complete_tree=False`, omitted row archival after whole-payload validation, existing writes unchanged, final projection refresh.
2. `src/catalog/services/publication.py` — `_apply` nested pricing call only: pass `complete_tree=True` because the approved nested payload is the complete editor snapshot.
3. NEW `src/catalog/testcases/test_offer_qa01_group_removal.py` — focused regression tests for publication removal and safe partial calls.

Evidence/document ownership: new `docs/qa/offer-qa01-fix-2026-10-13-r1/` (choose a fresh suffix if it exists), this plan status, corresponding current module05 status references in the two QA guides. Historical reports remain unchanged. No module05 PASS until its full final acceptance.

## Task 1: prove and protect the deletion contract

- [x] Port the audit reproduction from `docs/qa/offer-qa01-recheck-2026-10-13-r1/probe.py` into the new regression file; use `GroupPricingTests.setUp` as fixture setup without inheriting its test methods.
- [x] Record native RED on the unchanged source, with exact test labels/exits. Expected failure is missing `archived_at` after approval, not environment or fixture failure.

Core behavior assertions:

```python
nested = serialize_nested_pricing(self.place)
nested['activities'][0]['groups'] = [
    row for row in nested['activities'][0]['groups']
    if row['id'] != self.other.pk
]
revision = publication.propose(
    actor=staff, target_type='place', target_id=self.place.pk,
    patch={'nested_pricing': nested}, schema_version=publication.SCHEMA_VERSION,
    expected_version=self.place.content_version, revision_version=0, submit=True,
)
self.other.refresh_from_db()
self.assertIsNone(self.other.archived_at)  # live remains before approval
publication.review(actor=staff, revision_id=revision.pk,
                   version=revision.version, approve=True)
self.other.refresh_from_db()
self.assertIsNotNone(self.other.archived_at)
self.assertTrue(OfferingGroup.objects.filter(pk=self.other.pk).exists())
self.assertTrue(PricingPlan.objects.filter(pk=removed_plan.pk).exists())
self.assertNotIn(removed_plan.pk,
                place_pricing_records(self.place).values_list('pk', flat=True))
self.place.refresh_from_db()
self.assertEqual(self.place.price_to, Decimal('20'))
```

Additional focused cases in this same file:

- [x] Removing an entire activity archives the activity and its active groups, retains tariffs/history and excludes them publicly.
- [x] Approving an explicit empty activities tree archives all active activities/groups, preserves direct Place pricing and refreshes projections.
- [x] Rejection leaves live rows and public prices unchanged.
- [x] Default partial `replace_nested_pricing(place, partial)` retains omitted activities/groups; explicit complete mode archives them.
- [x] Foreign activity/group/plan IDs fail before any row is archived; snapshot rows, versions and scalar prices remain unchanged.
- [x] Inject a failure after an archive/write inside complete mode and assert the transaction restores all rows/versions/prices.
- [x] Removing a tariff from a retained group follows existing `replace_group_pricing_plans` behavior; unchanged IDs remain stable.
- [x] Second approval of the same completed revision and stale source/candidate requests are rejected without further changes; a new proposal uses current versions.

## Task 2: minimal writer repair

- [x] Add the explicit flag without changing existing callers by default:

```python
@transaction.atomic
def replace_nested_pricing(place, payload, *, allow_verified=False,
                           complete_tree=False):
    from catalog.models import Activity, OfferingGroup
    normalized = validate_nested_pricing(place, payload,
                                         allow_verified=allow_verified)
    kept_activity_ids = set()
    # Existing activity/group write loop stays in place.
```

- [x] In the existing loop, collect saved activity/group PKs including newly created rows. After writing each retained activity's groups, when `complete_tree` is true, archive its omitted active groups through `group.archive()`:

```python
if complete_tree:
    for omitted in activity.offering_groups.filter(
            archived_at__isnull=True).exclude(pk__in=kept_group_ids).order_by('pk'):
        omitted.archive()
```

- [x] After all retained activities are written, in complete mode archive groups under omitted active activities and then archive those activities; never touch another Place or previously archived rows:

```python
if complete_tree:
    for omitted_activity in Activity.objects.filter(
            place=place, archived_at__isnull=True).exclude(
                pk__in=kept_activity_ids).order_by('pk'):
        for group in omitted_activity.offering_groups.filter(
                archived_at__isnull=True).order_by('pk'):
            group.archive()
        omitted_activity.archive()
    sync_legacy_price_fields(place.pk)
return normalized
```

- [x] Publication `_apply` changes only its nested writer call:

```python
replace_nested_pricing(target, patch['nested_pricing'], complete_tree=True)
```

Validation of the entire payload precedes all mutations; archival occurs only during approved application, never propose/draft/save. Existing locked target and atomic review remain the boundary; do not introduce a competing publication mechanism. Canonical `archive()` increments content versions and updates timestamps. Final scalar synchronization handles the empty tree and any order-dependent signals. Default partial writer behavior remains the previous behavior.

## Task 3: targeted verification and handoff

- [x] Run the new regression file RED→GREEN through the isolated profile runtime. Run affected existing suites `catalog.testcases.test_task33_pricing.GroupPricingTests`, `catalog.testcases.test_task33_completion_taxonomy`, `catalog.testcases.test_task33_program_workspace`; record discovery IDs and native exits. Run once, repeat only failed or source-affected checks.
- [x] Use a new own browser/runtime profile and current PO RU/AZ/EN compilation verified before `django.setup`; one `LOCALE_PATHS`. Do not use common MO, old profiles, `.env` or another stand. Confirm running source hash equals current checkout.
- [x] With fictional fixtures, use actual owner UI: open two priced groups, remove one, submit; public reload before review retains it. Use actual moderator approval; owner and public reload afterwards omit it and use the remaining price. READ ONLY DB snapshots confirm archived rows, retained history, stable retained IDs and updated projections. ORM only sets up fixtures.
- [x] Repeat the affected native removal/save/reload path RU/AZ/EN ×360/390/768/1024/1280/1440; inspect keyboard controls, errors/conflicts, console/network and save screenshots with PNG hashes. No full unrelated UI matrix.
- [x] Confirm unchanged shared consumers: owner candidate reopening and admin nested import/approval; public activity/Place detail and pricing headline agree with active archive filters. Partial service/CSV tests must not infer removals.
- [x] Preserve all prior file hashes, HEAD/branch/active_run/shared MO and foreign stands. Record exact commands/exits/counts, snapshots, source/runtime provenance, cause, scoped diff, browser evidence and NOT RUN.
- [x] Close only OFFER-QA-01 when actual post-patch acceptance is demonstrated; module05 remains IN PROGRESS. Full module05 acceptance once after its selected repairs; global project suite later, as requested by the user.

NOT RUN at planning stage: patch/GREEN, native owner→moderator→public acceptance, full module05/global corpus, physical devices, real integrations and production. New findings outside these three source files require a separate concrete scope; do not silently expand.

## Execution handoff

[REPORT](../../qa/offer-qa01-fix-2026-10-13-r1/REPORT.md), [verification](../../qa/offer-qa01-fix-2026-10-13-r1/verification.json), [new OPEN baseline](../../qa/offer-qa01-fix-2026-10-13-r1/FINDINGS.md).38 unique targeted methods PASS, native owner/moderator/public18 cells; admin nested approval PASS. Partial name-only import retains tree/live but approval is blocked by pre-existing09; that wider workflow is not accepted. Native stale payload rejected422 by archived relation validator; typed409 UI not claimed. No unrelated implementation, no module05 full PASS.
