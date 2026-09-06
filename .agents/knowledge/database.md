# PostgreSQL and migration knowledge

AS-IS:2026-09-06. [Production evidence](../../docs/agent-audits/PRODUCTION_READ_ONLY.md) E2/E3 is authoritative for the inspected server; model/migration files explain semantics. LOCAL SQLite/test fixtures do not establish production usage.

## Schema and source

- PostgreSQL17.10,50 public tables,23MB, catalog migrations through0100; LOCAL adds untracked0101 unique normalized User email plus allauth migrations. Do not fake-apply it.
- `models/place.py` groups Place/Event/schedules/photos/likes; `models/pricing_plan.py` provides relational pricing constraints and projection signals; `models/owner.py`, `review.py`, `specialist.py`, `site.py`, `seo.py` define other domains.
- Place.category FK uses string Category.code, physical column category. Pricing legacy JSON field is named pricing_plans_legacy in Python but physical column pricing_plans. See0084 SeparateDatabaseAndState before interpreting schema drift.
- Day uniqueness `(place_id,weekday)`, pricing amount/currency/role checks and lookup/order indexes protect important invariants.72FK/67CHECK/24UNIQUE/50PK observed, all validated; declared-FK orphan checks0.
- App DB role is superuser: security/release must plan a least-privilege application/migration split before changing privileges.

## Data evidence and legacy

| Fact | Agent implication |
|---|---|
|321Place,78plans across25Place|Do not assume all prices have migrated|
|266Place scalar price present/no plans|LEGACY-IN-USE; no destructive cleanup|
|2nonempty legacy JSON;230scalar ranges;228monthly|Classify source + fallback/projection + DB usage per record|
|300structured schedules,3text schedules|Overlap possible; text is still used|
|83published status/237draft/1rejected|Visibility SQL is a separate contract|
|202missing coordinate,256photo refs|Do not treat every draft gap as public defect|
|2duplicate email groups/6accounts|Identity decisions required before local0101|
|0Event,0temporary Place,0SpecialistDocument|Unused in current data is not dead code|
|0team memberships/invitations|Retained compatibility still requires impact analysis|

See [legacy](legacy.md) for statuses ACTIVE/LEGACY-IN-USE/MIGRATED-BUT-RETAINED/DEPRECATED/CANDIDATE-FOR-REMOVAL/UNKNOWN. Scalars may be both legacy inputs and current projections.

## Safe inspection

Use provided connection mechanisms without logging credentials. Start a transaction with `SET TRANSACTION READ ONLY`, statement_timeout15s and lock_timeout2s. Inspect catalogs, aggregates and bounded joins. Do not invoke arbitrary management commands on the assumption that their name implies read-only; SEO audit writes, and several dry-run paths persist audit metadata.

FK index heuristic found no missing candidate; a321-row seq scan is not evidence for adding an index. Use query source + representative non-executing EXPLAIN; EXPLAIN ANALYZE only in an explicitly authorized isolated environment. Never print full user/session/event payloads.

## Migration contract

AUDIT → PLAN → DRY RUN → BACKUP → USER APPROVAL → APPLY → VERIFY for destructive production changes. Current task stops at audit. Dry-run must produce deterministic counts, ambiguity/manual_review and checkpoint/rollback plan; it must not silently infer pricing product type. Test idempotency and round trips on disposable copies, not production. Migration history alone does not establish complete semantic migration.

Management commands to inspect (not blindly run): `src/catalog/management/commands/` pricing/schedule import, ownership reporting, PostgreSQL cutover and SEO commands. Backend owns pricing/readiness meaning; database-reviewer owns integrity/data transition evidence. Security owns identity and privilege boundaries; release-reviewer owns actual activation and recovery.
