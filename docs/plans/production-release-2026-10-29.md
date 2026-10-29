# Production release — 2026-10-29

The user explicitly authorized pushing all accumulated source changes and applying them to the supplied server. This authorizes the reviewed combined release, recovery material, web replacement and verification; earlier audit-only restrictions do not prohibit this deployment.

Entry LOCAL: `codex/admin-draft-recovery-2026-10-26`, HEAD `de51c39eb6e15212bd97d55a33777af965e10e5f`, 50 pending paths. Entry patch/index/hash manifest: `/tmp/kidsmap-release-all-20261029`. Frozen test source: `/home/ramin/km-release-all-20261029`.

Entry PRODUCTION: clean `/opt/kidsmap` main at the same HEAD; image `kidsmap:place-dedup-20261029-de51c39eb6e1`; effective compose override `/opt/kidsmap-releases/20261029-place-dedup/release.override.json`. Preserve media, static, private document bind and private draft volume exactly. No model/schema/configuration/content changes are intended.

Scope: staff editor same-origin transport fix, place list/card and ready-filter presentation, specialist public/admin/owner UI, reviews/contact presentation, maps/paging/category navigation and tariff summary. Correct confirmed combined-release regressions with tests before deployment: preserve price kinds/currencies in the compact editor summary and align ready filtering/counts with authorized saved/live readiness.

1. Preserve entry work, review the complete diff and scan publishable source for secrets. Verify immutable source; preserve subsequent shared edits.
2. Run the complete unmodified isolated quality runner (`--execution split --workers 4`) on fresh owned PostgreSQL, standalone Python and JS checks, and bounded rendered browser acceptance. Do not weaken guards/assertions.
3. Commit exact verified source, push the working branch and fast-forward main without force. Add `[skip ci]` to prevent the legacy main workflow deploying a second mutable build.
4. Preserve production image/override/storage/static manifest and recovery backup on the server. Do not download private records or print credentials. Do not invoke generic release-server (it seeds site defaults and clears static).
5. Build a uniquely tagged image from the exact Git archive. Validate source parity, image exclusions, Django checks, no migration drift and `migrate --check`; unexpected pending migrations stop activation. Reuse actual storage/environment/compose settings.
6. Collect static without clearing previous hashed files; activate only web, with rollback to the saved image and manifest on failure. Leave database/cache/other services intact.
7. Fast-forward server checkout, verify Git/image revision, source and asset hashes, health, localized public/admin endpoints and authenticated staff form routing/checking. No real cards need creating or publishing for deployment checks.

Rollback: reactivate previous compose files/image and previous static manifest; retain old hashed files. No schema downgrade or database restoration over newer live writes.

## Combined verification corrections

The first full parallel lane ran 3286 tests and found 9 failure records plus 3 locale error records. A separate immutable `de51c39e` baseline reproduced eight affected scenarios: expired fixed-date tariff fixture, obsolete mixed-billing price-range assertions, old age-control placement expectation, and duplicate-creation fixture/label assumptions. Fixes preserve all amounts, currencies, billing units, saved-copy versions and duplicate denial; genuine distinct branches have separate addresses. The existing-profile hidden slug input was removed while retaining the original identity assertions. The volunteer preview test now checks the server-selected administrative path. Final acceptance uses a new owned PostgreSQL profile and the complete combined source after these corrections.
