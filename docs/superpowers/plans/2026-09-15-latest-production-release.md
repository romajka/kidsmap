# Latest production changes deployment plan

**Goal:** Deploy all currently committed changes through e0759f1f plus required, verified release corrections in80d1df89 and3aec046c, including bfc2c28 admin localization, lists, header and place/pricing/schedule editor changes, while preserving active localized URLs and production data.

**Authorization:** User explicitly requested «примени все последние правки» on2026-09-15. Existing production/push authorization persists. This is approved deployment, not the historical September6 audit.

**Architecture:** Build an immutable candidate image from git archive of the exact committed HEAD. Validate it using a disposable isolated PostgreSQL17 environment with synthetic fixtures. Preserve the existing image/static data and a verified server-only database backup. Fast-forward the clean production checkout and replace only web, retaining existing environment and LOCALIZED_PLACE_URLS_ENABLED=1.

**Tech stack:** Existing Docker Compose, Python3.12/Django, PostgreSQL17, Redis, server nginx, compiled gettext and collected static assets.

**Source:** User request and git diff47859f54..e0759f1f; deployed feature image7328e063 and already active URL backfill.

- [x] Confirm local/GitHub exact HEAD and clean production baseline; review changed code and schema requirements.
- [x] Build named candidate from git archive; run Django checks, migration drift and affected tests in an isolated DB/cache/media environment with DJANGO_TESTING=1 and no production credentials.
- [x] Render new admin/public UI and exercise import/save/pricing/schedule flows in isolated staging; resolve confirmed blockers and repeat affected checks if code changes.
- [x] Back up production database and static files without deleting any existing backups; restore DB in a disposable no-network PostgreSQL17 container to prove recoverability. Retain URL-compatible previous image and active environment privately on server.
- [x] Fast-forward production checkout to the exact tested revision. Apply only required pending migrations, collect static, recreate only web, preserve localized URLs flag and all data.
- [x] Verify live runtime revision/source hashes, Django health/migration state, representative changed UI/static assets and all225 public language URLs/legacy redirects/sitemap. Record exact results and limits.
- [x] Commit/push deployment evidence only, without triggering another application deployment; report actual deployed revision and remaining issues if any.

Recovery: previous image7328e063 supports localized URLs. Keep flag1 and localized slug data during rollback, restore previous static archive if needed, recreate only web. Do not reverse0113 or restore the whole DB over subsequent editorial changes for a UI issue.

Execution evidence: [latest production release](../../agent-audits/latest-production-release-2026-09-15.md). Final application revision3aec046c;753 exact-image tests pass. The evidence-only publication preserves this application revision.
