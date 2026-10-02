# Isolated stage07 verification

Uses unchanged QA04 runner/settings/guards: DJANGO_TESTING=1, disposable PostgreSQL17, network none/no ports, PGDATA tmpfs, owned Unix socket; clean env excludes project/prod credentials; LocMem cache/email, isolated media; network/libpq guards. Raw logs/rows/SQL stay /tmp.

- Migration: `python3 docs/task33/qa07/generate.py --mode all --output /tmp/task33-07-generate`
- Targeted: `python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_permissions --label catalog.testcases.test_task33_ownership --label catalog.testcases.test_task33_catalog_schema --output /tmp/task33-07-green-final`
- Full: `python3 docs/task33/qa04/run.py --mode all --output /tmp/task33-07-full-final`

Output directories must be fresh. Safety/isolation/cleanup, exact commands and suite/problem IDs are captured by QA04. No production DB, project services, real email or credentials used. Contract assertions of previous suites are not relaxed.
