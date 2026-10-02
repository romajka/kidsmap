# Stage04: isolated PostgreSQL baseline

Only LOCAL QA FOUNDATION. No application/schema/test assertion changes. No production connection, deployment or dependency installation.

From `/home/ramin/kidsmap`:

```bash
python3 docs/task33/qa04/run.py --mode discovery --output /tmp/task33-04-discovery-new
python3 docs/task33/qa04/run.py --mode probe --output /tmp/task33-04-probe-new
python3 docs/task33/qa04/run.py --mode all --output /tmp/task33-04-baseline-new
```

Use a new empty output directory per run; nonempty paths and symlink outputs are rejected before creating a container. Requirements: existing project `.venv` with dependencies, accessible local Docker and cached `postgres:17-alpine` image. No pull is performed (`--pull=never`). Evidence snapshot uses PostgreSQL17.10, image `sha256:93aa428db0aeeb71d24dcad1491bef6e1396a4255697e4bfc4c725bfeb981b74`, Django6.0.2, Python3.12.3, psycopg3.2.10. Changing these versions requires a new baseline.

The launcher constructs a clean child environment instead of inheriting credentials or reading `.env`. Settings replace DATABASES (one default only), Redis with LocMemCache, SMTP with locmem email, media with a private `/tmp/kidsmap-task33-qa04-*` directory, integration credentials with empty values. Canonical email display senders are preserved; locmem transport and clean environment isolate mail. QA-only MD5 password hasher accelerates synthetic authentication tests; application password configuration stays unchanged. `DJANGO_TESTING=1` is mandatory.

Each run creates a uniquely labelled, exclusively owned PostgreSQL container: network `none`, no ports, PGDATA tmpfs, one bind mount containing only its Unix socket. Docker snap cannot see the host `/tmp`; the socket is therefore in the checkout's ignored `.tmp/kidsmap-task33-qa04-socket-*` directory with a private parent. It does not mount source, working media or any database volume. PostgreSQL also has an internal default socket solely for the official image's bootstrap; readiness waits for the final postgres PID1. Settings guard rejects foreign DB/cache/media/email paths and symlinks. Python socket and psycopg/libpq guards reject foreign connections before connection. These guards supplement explicitly disabled integrations; they are not a general OS sandbox for arbitrary native binaries.

`finally` verifies nonce/mount/network ownership and removes only that container and its scratch roots. `run.json` reports cleanup. An ownership mismatch leaves resources in place rather than deleting an unverified container. A killed launcher cannot guarantee `finally`: inspect that run's nonce/name before any manual cleanup; never clean unrelated containers.

Safety tests run before starting PostgreSQL. Discovery compares the existing wrapper/full IDs with explicit `catalog.testcases.*` module labels. It records missing IDs, duplicates and module counts. The suite uses the existing KidsMapTestRunner state reset, sequentially, in a separate test DB. Probe fixtures reside in the disposable base DB and never affect test fixtures. `utils.py` has helpers rather than TestCase classes and is excluded. Tests are neither edited nor skipped by this helper.

Modes: discovery verifies isolation and discovery; probe additionally runs `check`, `makemigrations --check --dry-run`, all migrations, migration-state and synthetic repeated SQL/HTTP probes; all additionally runs all explicit modules. Fixtures use existing Place/PricingPlan fields: standalone, logical network branches, independent businesses sharing an address, age/tariff variants, missing coords/photo, old repeated and null-user reviews, event and specialist. Future Organization/Activity/OfferingGroup relations are not created by this stage.

Raw logs stay under the requested `/tmp` output. Only aggregates, test IDs/exception classes, version/isolation booleans and hashes are copied to stage reports. Query text, user records, credentials and row payloads are not report artifacts. HTTP probes use Django's test client, not a rendered browser. `query-baseline.json` contains two identical cold-cache measurements per surface; ORM IDs are compared privately then discarded.

Exit0 means the selected mode completed. Existing suite failures return nonzero with `suite-results.json` and BASELINE_FAILURE; bootstrap/import/harness failures without suite evidence are ENVIRONMENT_FAILURE. System/migration check results must also be read from `checks.json`; they are separately recorded, not hidden by the suite exit. Browser, external services and production are NOT_RUN. Do not use this helper as a deployment readiness decision.

For bounded reproduction of the original failing tests, use the saved canonical IDs (subtests share their parent ID):

```bash
python3 - <<'PY'
import json, subprocess
labels = json.load(open('docs/task33/reports/04-failure-labels.json'))
args = ['python3', 'docs/task33/qa04/run.py', '--mode', 'all', '--output', '/tmp/task33-04-failures-new']
for label in labels:
    args += ['--label', label]
raise SystemExit(subprocess.run(args).returncode)
PY
```

`--label` is repeatable, requires all mode and is validated against fresh canonical discovery. Selected reruns are reported separately from full-suite evidence. Subtest failures record the parent ID and exception class, without parameter values or row data.
