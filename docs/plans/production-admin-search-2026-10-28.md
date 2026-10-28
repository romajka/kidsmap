# Production admin draft search release — 2026-10-28

User explicitly authorized committing/pushing all pending changes and applying them to the supplied server. Scope: the diagnosed admin draft search fix, tests and reports. Entry local/remote/server revision: e7bd719f. Server checkout clean; two changed runtime files match the active image. No schema/static/dependency changes.

1. Preserve local patch/source snapshot and previous server image/compose override.
2. Verify 63 targeted/regression tests on isolated PostgreSQL17 with canonical safety guards; result PASS. SQLite full-migration run also PASS, 63 tests.
3. Commit all five pending source/test/report/plan paths. Push current branch and fast-forward main atomically, without force. Use [skip ci] to avoid a second deployment by the generic workflow.
4. Fast-forward the clean server checkout to the exact commit. Build a small overlay image from the verified active e7bd719f image, copying the two runtime files and the new regression test. Clone the active compose override and preserve all settings/mounts; update only image/build/revision metadata.
5. Run candidate Django checks and migration-plan verification. No migrate, sync_site_defaults, collectstatic or catalog writes are required.
6. Replace only web. Verify running revision/source hashes, unchanged mounts, health/public/admin HTTP, and read-only search for the existing draft347 through available authenticated evidence.
7. Preserve rollback image/configuration and release evidence privately on the server. Remove only the disposable QA container owned by this release.

Rollback: reactivate the saved image with the saved override. No database rollback is required or authorized for this code-only release. On unrelated worktree/remote drift, preserve it and reconcile before activation. Content-automation state is outside this release.
