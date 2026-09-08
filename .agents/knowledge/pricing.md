# Pricing — verified LOCAL source, 2026-09-08

[Current snapshot](current-snapshot.md); [source map](source-of-truth.md). Owner: django-reviewer; schema/legacy: database-reviewer.

- `models/pricing_plan.py:PricingPlan` owns enums, fields, constraints, clean/save and post-save/delete scalar-sync signals.
- `services/pricing_plans.py`: PRICING_STORAGE_FIELDS, serialize_pricing_plan(s), normalize_pricing_plans, replace_place_pricing_plans, sync_legacy_price_fields, public summary functions. Trace exact symbols before adding a field.
- Replacement is atomic, retains IDs using ID/fingerprint, preserves staff verification omitted by owner, removes stale rows and updates scalar projections. Model-only edits miss normalizer/storage/export/fingerprint consumers.
- `models/place.py` keeps relational serialization, legacy JSON fallback and public badge properties. Scalar-only legacy is in use as a compatibility contract; no deletion based on graph.
- `Place.PRICE_MODE_CHOICES` and readiness define non-tariff modes. Owner helper presently differs: do not teach owner/admin parity as AS-IS.
- JSON UI importer → admin validate_pricing_import_view → PlaceAdminForm/save; export_place_json_view uses serializer. CSV import_places updates scalar fields separately.
- `migrate_legacy_prices` can trigger scalar rewrites through signals; dry-run/docstring alone does not prove preservation. Ambiguous product/range → manual_review.

Required impact: owner/admin/volunteer forms and revisions, import/export, filters/API, catalog/map/detail/recommendations, SEO Offer, signals/constraints and migration compatibility.
Validation A traced an important consumer distinction: catalog price filtering uses positive active-primary AZN exact/from/range relational plans; shared cards and home recommendations use backend display properties; home map displays its price badge, while catalog-map payload carries price but its current renderMapCard does not display it. Do not infer identical presentation from shared data. Exact references: [validation A](../../docs/agent-audits/validation-A.md).
Targeted labels: catalog.testcases.pricing_plans_relational, catalog.testcases.pricing_plans, catalog.testcases.place_readiness, catalog.testcases.legacy_migrations, catalog.testcases.test_json_roundtrip_audit, catalog.testcases.test_place_json_and_pricing_modes.
Checks: stable IDs, round-trip precision, owner cannot clear verification, free mode, scalar fallback, second migration run, concurrency when touched. These labels were inspected, not executed in the team-authoring task.
