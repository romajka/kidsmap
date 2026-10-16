# OFFER-QA-09 Partial Review Pricing Implementation Plan

**Goal:** Частичная правка названия/текста карточки с действующими групповыми тарифами не должна терять цену в проверке готовности модерации.
**Architecture:** `review_form` собирает trusted complete review view: scalar/direct-pricing snapshot + saved candidate payload + текущий serialized nested tree, только если nested tree отсутствует в payload. Explicit candidate tree имеет приоритет, включая намеренно пустой. Readiness/domain/publication/ACL/CAS правила и live данные не меняются.
**Tech Stack:** existing Django/PostgreSQL services, targeted Django regression tests/native browser.
**Spec:** `docs/qa/offer-qa01-fix-2026-10-13-r1/FINDINGS.md`, OFFER-QA-09; fresh [REPORT](REPORT.md).

## Exact authorization / ownership

APPROVED IMPLEMENT executed2026-10-14 after user confirmation; scoped review-pricing cause CLOSED LOCAL. See docs/qa/offer-qa09-fix-2026-10-14-r1/REPORT.md. Один ID OFFER-QA-09, вне исторических73tasks/76IDs. Последовательный root, Django lead responsibility, independent delegation не заявляется. Без commit/push/deploy/production. Preserve incoming dirty WORKTREE/active_run NONE/чужие стенды.

**Ровно два source/test файла:**

1. `src/catalog/services/volunteer_places.py`: только `review_form` — trusted live nested fallback при отсутствии ключа в saved payload. Не менять content_snapshot/editor_form/candidate_from_payload/save/review services.
2. Новый `src/catalog/testcases/test_offer_qa09_partial_review_pricing.py`: regression поведения review readiness/candidate precedence/negative/security-preservation.

QA/docs: новый `docs/qa/offer-qa09-fix-2026-10-14-r1/`, progress этого плана, scoped status links в continuation guide/module-acceptance-prompts, own ignored `.tmp`. No template/CSS/JS/PO/common-MO/publication/place_readiness/pricing_plans/schema/dependency/CI changes. Если обнаружится другая причина, зависимую реализацию остановить и показать конкретное расширение.

## Task 1 — RED / bounded cause

- [x] Refresh checkout HEAD/branch/dirty/active_run and exact incoming source hashes. Сверить fresh native RED из recheck: candidate payload только name_en, form valid, cleaned nested None, price issue, no approve, live group20/direct tariffs0. Не переносить текущие PID/port на новый fix profile.
- [x] Создать `PartialReviewPricingTests(TestCase)` с fictional owner/staff, create_ready_place без direct tariffs/scalar prices, active published Activity +active OfferingGroup +primary exact20 PricingPlan. Photo/structured schedule/taxonomy/location prerequisite — существующие helpers/own fixture media. Candidate через `publication.propose`, а не прямую запись enum.
- [x] Основной failing method `test_name_only_candidate_counts_current_group_tariff`: assert payload keys == ['name_en']; `review_form(...).is_valid()`; `evaluate_form_readiness(...).is_ready`; no price issue; saved payload/versions/live tariff/name остаются прежними. До patch readiness false — сохранить RED.

```python
revision = publication.propose(
    actor=self.owner, target_type='place', target_id=self.place.pk,
    patch={'name_en': 'Proposed title'}, schema_version=publication.SCHEMA_VERSION,
    expected_version=self.place.content_version, revision_version=0, submit=True,
)
self.assertEqual(set(revision.payload), {'name_en'})
form = review_form(revision)
self.assertTrue(form.is_valid(), form.errors)
readiness = evaluate_form_readiness(form, form.instance)
self.assertTrue(readiness.is_ready, readiness.issues)
self.assertFalse(any(issue.code == 'price' for issue in readiness.issues))
```

## Task 2 — Minimal trusted fallback

- [x] В `review_form` сразу после existing trusted data dict добавить local import и условие. Ниже оставить JSONField/location flag/other form behavior без изменений:

```python
from catalog.services.pricing_plans import serialize_nested_pricing
if 'nested_pricing' not in revision.payload:
    data['nested_pricing'] = serialize_nested_pricing(revision.place)
```

- [x] Не использовать `payload.get(...) or live_tree`: пустой candidate tree не должен восстанавливать удалённые группы/цены. Не менять saved payload/base/dependencies/versions и не применять дерево к БД. Serializer excludes archived Activity/OfferingGroup; inactive plan flag остаётся частью canonical serializer, existing readiness filter не считает его публичной ценой.
- [x] Не читать nested tree из review POST. Caller создаёт form из trusted saved revision; actor permission/source conflict guards существующие.

## Task 3 — Targeted regression / shared guards

- [x] `test_explicit_candidate_tree_wins_over_live_prices`: valid candidate changes own group tariff20→35; cleaned tree price35, live20 до approval, никаких fallback merged rows.
- [x] `test_explicit_empty_candidate_tree_does_not_restore_live_price`: candidate `{pricing_schema_version:2,activities:[]}`, нет direct tariffs/free mode; price readiness остаётся false, live row/history не меняются.
- [x] `test_archived_activity_and_group_do_not_satisfy_price`: отдельные fictional archived Activity/group sources исключены fallback; negative price stays blocked, archived rows/history preserved.
- [x] `test_inactive_or_optional_only_tariff_does_not_satisfy_price`: inactive flag/optional role из существующей mapping semantics не обойти новым fallback. Positive on_request/free/exact primary fixtures сохраняют existing price-kind rules; не придумывать новые enums.
- [x] `test_direct_tariff_and_free_mode_still_pass`: отсутствие grouped tree не ломает direct tariff и existing price_mode=free behavior.
- [x] `test_partial_review_is_read_only_and_post_cannot_replace_trusted_tree`: form evaluation не меняет name/live tree/plan IDs/history/version/payload; native/admin review request с чужим nested body не становится источником form readiness. UI/public approval gate/ACL/CAS остаются existing domain authorities.
- [x] `test_stale_and_foreign_review_preserve_candidate_and_live`: named caller/controller check чужой actor denied; stale version fails; no tariff/history writes. Не ослаблять assertions/требование реальной цены.
- [x] GREEN только новый class +selected affected existing:
  - `catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_admin_and_volunteer_use_identical_revision_readiness`
  - `catalog.testcases.test_task33_pricing.GroupPricingTests.test_nested_import_waits_for_publication_approval`
  - `catalog.testcases.test_offer_qa01_group_removal.ApprovedGroupRemovalTests.test_empty_complete_tree_preserves_direct_tariff_and_history`
  - `catalog.testcases.place_readiness.PlaceReadinessRulesTests.test_legacy_scalar_price_does_not_satisfy_the_price_item`

Проверить discovery exact method names; записать manifest/counts/commands/exits. Test DB только собственная, DJANGO_TESTING=1/LocMem cache/email/media/private-media/disabled integrations; environment/baseline failures отделить. Не запускать полный модуль на каждом patch.

## Task 4 — Native acceptance / handoff

- [x] Fresh own fix stand/profile и unique loopback PostgreSQL/DB/cache/media/private-media/email, fictional actors; без checkout .env/production credentials. Fresh helper RU/AZ/EN build/manifest verify/sole LOCALE_PATHS до django.setup; entry/startup/disk source match.
- [ ] Additional owner-only name native transition remains NOT RUN (hidden language tab in harness; current locale compiler then blocked). Admin partial-name and explicit empty/valid trees accepted below.
- [x] Admin настоящим partial JSON import меняет только name_en → save → review → approve → reload. Own public grouped20 остаётся, proposed title приходит в live только после approval. Owner partial name/text submit также проходит тот же review adapter; READ ONLY payload_fields проверяет отсутствие nested tree в candidate. Не заменять эти transitions ORM.
- [x] Negative candidate явно удаляет дерево/группу с единственной ценой: review требует цену, не получает скрытый fallback на старый тариф. Archived/inactive sources тоже не дают false PASS. Не пытаться опубликовать заведомо invalid candidate в production; все negative fixtures собственные.
- [x] Review price/warning/approve states RU/AZ/EN ×360/390/768/1024/1280/1440, native admin language menu, keyboard/focus/400/409 where applicable, console/network/PNG manifest. UI не переделывать этим scope. Shared owner/admin/current public price consumers — targeted smoke; full other modules не заявлять.
- [x] Reviewable two-file diff, fresh snapshot/runtime/locales/RED→GREEN/method counts, lifecycle/pricing/history readback, exact commands/exits/native assertions/PNG/NOT RUN. Closed только09 при фактическом scoped acceptance; full ACCEPT05/global/external/production NOT RUN до отдельной модульной проверки.

## Next

После accepted09 все выбранные ремонты module05 готовы для ACCEPT-05. Подготовить exact ACCEPT prompt из guide с текущими evidence links и user preference: module-level corpus один раз в конце; no full repeated checks unchanged source. Не начинать module06 автоматически.

Completion:12targeted methods and10native scoped checks PASS, module334methods PASS;36review gate matrix cells accepted. Only OFFER09 scoped cause closed. Full ACCEPT05 FAIL due separate OFFER10 enum captions and concurrent foreign RU duplicate. Owner-only native supplement not counted; see repair/full reports. No module06 started.
