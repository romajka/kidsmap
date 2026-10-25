# Production release plan — 2026-10-25

Authorization: user explicitly requested Git push and production deployment on 2026-10-25. Prior audit restrictions remain applicable outside this release scope.

Goal: ship the current place editor, drafts/dashboard fixes, JSON instruction and tariff fixes without transferring local QA data.

Architecture: freeze the existing dirty worktree as a release commit; push a dedicated codex release branch to avoid an uncontrolled main auto-deployment; deploy that exact revision after server preflight. Application image rollback preserves the previous image and uses only backwards-compatible additive migrations.

Tech stack: Django, PostgreSQL, Redis, Docker Compose, nginx, GitHub.

Spec: user requests and docs/qa/2026-10-25-admin-json-instructions-release-check.md.

## Constraints

- Preserve local and server working changes; exclude credentials, environment files, local QA databases/media/fixtures and raw logs from Git.
- Tests use DJANGO_TESTING=1 and isolated database/cache/media/email; production credentials are never used for tests.
- No bulk conversion or reinterpretation of ambiguous legacy prices.
- Keep the local server at port 8898 running.

## Steps

- [x] Inspect current server revision, private storage, service health, disk and migration state; record only sanitized facts.
- [x] Review/stage application, templates, assets, tests and documentation; scan staged changes for secrets and check whitespace.
- [x] Run release regression checks on isolated local resources; freeze and push a dedicated release revision.
- [x] Preserve server checkout changes and prior image; create bounded database/runtime/config backups and verify integrity and recoverability.
- [x] Build the exact new revision, inspect migration plan, apply supported additive migrations and collect static files.
- [x] Activate image, verify public/admin health and migration alignment; recover previous image if health checks fail.
- [x] Save exact revisions, results, limitations and recovery instructions in docs/qa.

## Recovery

Retain old image under an immutable release-specific tag plus server checkout snapshot. Additive 0146/0147 fields can remain for an old application rollback after 0148 installs persistent empty-list SQL defaults; do not reverse migrations or overwrite live database after new writes. Regression tests exercise actual INSERTs through the historical 0145 models. Stop the web writer for the migration batch to avoid the intermediate 0146–0147 window. Database restore is an explicit emergency procedure requiring traffic/writers stopped and an assessment of writes since backup. Preserve static files so previous image can be restored consistently.
