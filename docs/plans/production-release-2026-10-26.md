# Production release — 2026-10-26

Authorization: user explicitly requested publishing all accumulated changes to GitHub and applying them on the supplied production server. This supersedes the earlier read-only audit scope for this release only. No additional approval is required for the approved rollout.

Entry: local HEAD `1b0acf8c6d03e71d8516cfb92c19018db1426ebf`, branch `codex/admin-draft-recovery-2026-10-26`, 98 modified/untracked source/test/plan/report files. Entry patch/archive/manifest in `/tmp/kidsmap-release-20261026/`. Production checkout clean at `4a255ebf6a4e0df79e4c60e175bcaea5552b9080`; running image `kidsmap:admin-editor-parity-20261025-4a255ebf6a4e`. Remote main equals local entry HEAD. Previous commit delta is documentation only. Production catalog migrations through 0148 already applied.

Scope: all current source changes for admin draft recovery/preview/schedules, publication request completion and readiness, organization workflows, account/settings/reviews, parent guides/home placement, homepage controls and stable map selection, translations and their tests/reports. Preserve existing media, private mounts, environment, custom SiteSettings and unrelated applications. Do not guess or bulk-rewrite historical card data.

- [ ] Review the exact diff; scan publishable paths for credentials; preserve entry work.
- [ ] Full isolated Django/PostgreSQL gate, JS corpus, standalone Python checks, real rendered current photo integration. Prior bounded browser reports remain evidence for their exact source snapshots; verify representative combined local journeys if needed.
- [ ] Commit the reviewed snapshot and publish the current branch plus fast-forward main. Use `[skip ci]` to prevent the main workflow from launching a second uncontrolled deployment with the old build-context override; record the complete local quality results instead.
- [ ] Record server recovery metadata, create a dedicated verified database dump and static archive without invoking backup retention cleanup. Keep credentials/private files on server only.
- [ ] Create an immutable release source from the exact Git SHA and build a uniquely tagged image. Preserve the current compose private-media override while replacing its stale build context and image/revision label.
- [ ] Candidate image: migrations check, drift check, Django check and translation/static generation. Retain old hashed static files; no forced data seeding or overwrite of SiteSettings.
- [ ] Activate only the web service with the reviewed override; health/HTTP/assets/actual image source hashes and locale/browser map selection acceptance. Retain rollback image/override/static/database backup.
- [ ] Record GitHub versus production SHA and test evidence, clean up owned QA runtime, leave the application running.

Rollback: compose the saved old image/override, restore saved static files only if needed. No schema change is expected; database restore is reserved for confirmed data loss, never applied over newer live data automatically. Stop release on unexpected schema or storage differences.

## Findings from the complete gate

The first 3167-test run found two application regressions: a typed list/dict JSON value crashed the read-only readiness projection before validation, and an unsaved candidate gallery row without a database id crashed moderation preview. Existing security/location tests reproduced both; the narrow rerun now passes both without weakening their assertions. The projection retains disabled-field handling and does not validate/save the form; gallery rows receive their normal optional id without changing stored data.

Other failures: the local venv lacked the already pinned `pypdf==6.20.1`; an old phone-migration fixture restored only migration0145, leaving later tests without0146–0148; one SimpleTestCase called a view that now correctly registers an on-commit callback; an HTML regex counted a data attribute as a form input; two old expectations still described the previous home title and immediate organization confirmation action. The fixture now restores graph leaves, the transaction-using test uses TestCase, the attribute matcher excludes data-name suffixes, and the expectations retain the approved new title/preview GET plus acceptance POST checks. No application validation/assertions were relaxed merely to obtain green.

A reuse of the flushed test DB caused missing taxonomy fixture failures in the broad targeted rerun; that run is not acceptance. A completely fresh socket-only PostgreSQL instance is used for the final full rerun.
