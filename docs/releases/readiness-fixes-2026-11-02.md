# Homepage/auth release — 2026-11-02

Scope: honest localized homepage copy, bounded authentication attempts, and a Git-backed release that preserves the already-deployed map/counter behavior. No schema changes. The independent readiness audit report is not part of this release.

## Authentication policy

- Public and admin password login share a budget: 12 POST attempts per identity and 60 per client IP in a fixed 15-minute window.
- Password-reset requests: 3 per identity and 20 per IP in a fixed one-hour window. Rejected attempts send no email.
- Counters are shared Redis keys containing HMAC digests, not raw credentials. Fixed windows expire without extending on blocked requests; adjacent windows may admit two budgets around a boundary. Successful attempts count too.
- 429 responses are localized, include Retry-After and no-store, and disclose no account existence. Storage/configuration failure returns 503 before authentication or mail processing; no process-local production fallback.
- Trust X-Real-IP only from explicit AUTH_THROTTLE_TRUSTED_PROXIES. nginx must overwrite it with its own client address. Ignore X-Forwarded-For. Bind the web container only to host127.0.0.1:8000. This deployment's bridge gateway must be verified, not copied blindly to another host.

## Build and release contract

1. Verify a clean, committed source snapshot. Preserve unrelated dirty work separately. Export with `git archive <revision>`; record archive SHA256 and commit/tree IDs. Build from that archive with the repository Dockerfile, pinned requirements, and `--build-arg PYTHON_BASE=python:3.12-slim@sha256:<verified-digest>`. Record actual base digest, image ID and OCI revision label. This is source/provenance reproducibility, not a claim of bit-identical apt output.
2. Inspect current effective compose configuration, image, mounts, environment, command, network and migration status. Keep environment values and runtime compose files on the server with mode0600; do not add them to Git or reports. Retain the old image and effective compose file.
3. Compare application source hashes, with only the reviewed diff allowed. A migration difference stops this no-migration release. Create a database backup and validate its gzip stream before the six-field editorial update. Snapshot the existing six homepage title/subtitle fields separately for exact rollback.
4. Generate the candidate effective compose file from the active configuration. Change only image, loopback port binding and narrow trusted-proxy setting; remove build instructions. Preserve all public/private storage mounts and other environment values. Do not invoke the generic release script: it also syncs unrelated settings and clears static files.
5. Run candidate checks before activation. Execute `python manage.py update_homepage_copy` once: it changes only blank/known legacy title/subtitle fields and leaves custom editorial copy untouched. New installations get the same defaults from code.
6. Collect static files without `--clear`; retain the old static manifest and old hashed assets. Activate only web with `up -d --no-deps --no-build web`. Keep DB/Redis and all volumes intact.
7. Verify `/healthz`, current image/revision, selected and full deployed source manifest, absence of pending migrations, effective limits/proxy/cache configuration, unchanged environment/mounts except approved fields, localhost-only port binding, localized home titles, catalog neutral counts and fetched hashed Mappy asset. Browse AZ/RU/EN at390/768/1024/1280/1440. Do not guess production passwords or send reset emails as a smoke test.
8. Keep sanitized verification JSON and rollback instructions with the release. Source archive and commit must be retrievable from Git; checkout cleanliness of an old inactive source directory does not prove running-image provenance.

## Rollback

Restore the saved six homepage values only if they still match this release's replacement values (do not overwrite subsequent editorial work). Restore the prior static manifest. Activate the retained previous image with its saved effective compose configuration; recheck health and source. No schema rollback is necessary. Do not remove newer hashed static assets or private/public media during rollback.

## Acceptance boundaries

Targeted Django regression tests, real isolated Redis concurrency/expiry tests, and relevant JavaScript tests are required. SQLite alone is not PostgreSQL constraint/concurrency evidence. Live authentication abuse probes, actual mail/OAuth delivery, full suite, physical devices and a full backup restoration drill are outside this bounded change.

Verified before release:254 Django homepage/catalog/map tests;90 auth/reset/OAuth tests;3 real isolated Redis atomicity/TTL tests;31 JS tests. Two older map payload expectations were extended to assert the exact publication_date now sent by the already-deployed map implementation. No production behavior was removed to make tests pass. Browser previews:30 localized429/503 states, no horizontal overflow. Activation implementation: `scripts/releases/activate-home-auth-20261102.py`.
