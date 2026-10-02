# Stage04 LOCAL QA FOUNDATION plan

Goal: reproducible PostgreSQL baseline of existing HEAD, no application fixes.
Scope: qa04 local runner/settings/guard/synthetic probes and reports04; existing application/test assertions unchanged. Stage05–28 and production excluded.

- [x] Clean child env, explicit settings, fail-closed connection/media/email/cache guards; negative safety tests before DB commands.
- [x] New exclusively-owned PostgreSQL17 container: cached image, network none, no ports, tmpfs data, unique private ignored .tmp socket parent (Docker snap cannot see host /tmp), with Unix socket bind only. Assert ownership/isolation before use; finally cleanup only own container.
- [x] Test discovery compare wrapper/full vs explicit actual modules; preserve labels, deduplicate only identical unittest IDs when Django does so.
- [x] PostgreSQL system/migration-state checks, existing owner/admin/public/volunteer/pricing/reviews/specialists/events + readiness/legacy suites. No assertion changes; failures stored as baseline IDs with sanitized class, full logs local scratch only.
- [x] Synthetic fixed fixtures: standalone, logical network (AS-IS no Organization/Activity/group yet), independent shared address, multi tariff/age cases, missing coords/photo, repeated/null-user old reviews; repeated same-fixture HTTP output/SQL counts and aggregates, no row dumps.
- [x] Independent canonical database-reviewer checks guard/discovery/evidence; report hashes/preservation/status, release active_run. User design acceptance stays pending.

Files: qa04/{run.py,settings.py,guard.py,commands.py,fixtures.py,test_safety.py,README.md,plan.md}, reports/04*. Reproduction requires installed .venv/Docker/cached postgres17 image; no dependency install or existing container reuse.
