# Homepage map and mobile hero release

User explicitly authorized pushing and applying all current changes on the server. Existing authorization covers commit/push/activation; no repeated approval request. Execution is inline, without subagents.

Source: branch `seo-indexability-20260916`, initial HEAD/origin `07abeae33ae1deadf8d77dcfd854c54f9566980f`. Scope: all current tracked modifications and the homepage UI plan/regression tests; exclude ignored temporary previews, fixtures, media, keys and backups. Includes homepage composition/hero/mobile map, autocomplete/live-count/provider fallback, district aliases and age consistency in catalog. No schema migrations, environment changes, seeding, user-data edits or main-branch merge.

Preflight:
- Reviewed changed backend boundaries, template/map configuration and source inventory. Preserve unrelated existing worktree work.
- `.venv/bin/python .tmp/home-map-ui/run-filter-tests.py catalog.testcases.test_public_filter_consistency catalog.testcases.events_feature catalog.testcases.test_home_public_metrics catalog.testcases.test_responsive_images.ResponsiveImageTests`:24 passed. Environment cleared, DJANGO_TESTING=1, disposable SQLite test DB, isolated LocMem cache/media/email, no production credentials.
- `.venv/bin/python .tmp/home-map-ui/release-checks.py`:check, makemigrations --check --dry-run and migrate --check passed against isolated migrated preview DB under query_only; no new migrations.
- `node --test scripts/tests/home_map_filters.test.cjs`:9 passed, including canonical district/AND/age and script-to-Leaflet-provider asset URL/integrity regression.
- `node --check static/js/home_map.js`, Python AST parse of5changed source/test modules, `git diff --check`:passed.
- `playwright_cli.sh --session home-map-ui run-code --filename=.tmp/home-map-ui/hero-check.js`:18 locale/width layouts (RU/AZ/EN ×320/360/390/430/768/1440), images/text/touch targets, click/Enter slider navigation, reduced motion and primary CTA passed.
- Existing27combination browser checks and broader129test/2baseline failures recorded in `2026-09-28-home-map-ui.md`; full suite is not green. No weakened assertions.

Release blocker corrected during source review: fallback loader read Leaflet asset metadata from map div while actual template declares it on script. Failing clean-browser fixture timed out before correction; loader now captures URLs/SRI in SCRIPT_CONFIG just as it does Google metadata, retaining div fallback compatibility. Browser `.tmp/home-map-ui/fallback-clean-check.js` uses a fresh context with no init scripts or HTML rewrite, exact-byte local provider assets only, and confirms actual Leaflet map initialization. JS cache query updated to map_release4.

Production access: documented root@157.173.119.227 rejected the current agent/default identity with `Permission denied (publickey,password)`. Current production revision/image/checkout cleanliness cannot be verified. User asked asynchronously for a working SSH alias/key path or authorization of their current local public key; no password/private key requested. Do not claim activation before actual access and post-release health/source/static checks.

Activation when access is restored: verify clean checkout, exact branch/revision and healthy current image; preserve current image and static snapshot privately for rollback. Fast-forward to the exact pushed revision, build web while old app serves traffic; run Django check/migrate --check/drift checks on new image and collectstatic --noinput without clear. Recreate only web. Verify health/home/catalog RU/AZ/EN, source/static hashes and mobile rendered UI. Do not apply migrations or modify environment/data. On activation failure restore retained image/static; do not roll back database data.
