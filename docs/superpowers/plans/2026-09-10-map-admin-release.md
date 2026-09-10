# Map and admin release — 2026-09-10

Authorization: the user explicitly requested pushing all accumulated changes and applying them to the KidsMap server. This supersedes historical audit-only and no-deployment instructions for this release. Credentials must not be included in files, commits or reports.

Initial local HEAD, origin/main and clean production checkout all match `d59bbc1a37bda44e1d91e1375a85c820b4a6151e`. Production checkout: `/opt/kidsmap`, branch main; existing web image `sha256:cda46e27fc4289da4d7f4e72699c70904c081bb330d43a80f4329b7f5749d0fd`. PostgreSQL and Redis healthy. No pending production migrations and no new migration/model files in the release. Existing production Google key is configured; Map ID is absent (values not recorded).

Scope: current public map motion/marker updates, local runserver configuration fix, homepage decorative/background changes and all accumulated admin list/profile/region improvements, with their tests and documentation. A release check found RegionAdmin stale metrics and search discarding active filters; confirmed regressions are being corrected with focused tests before publication.

Plan:
- Review exact diff; run isolated admin/permission/region tests, map unit/browser checks, syntax and whitespace checks, and secret-pattern scan.
- Retain previous image and protected server-only database/static/config recovery files; validate archive structure. No deletion of prior backups.
- Commit all reviewed source/tests/docs, push main, then use the established build/release/recreate-web workflow. Avoid simultaneous CI and manual deployments.
- Check deployed revision/image, migrations/Django checks, public/localized/admin entry points and static assets, then verify map interactions in a live browser.

Recovery: no schema change is expected. Restore the retained old web image tag and previous static archive, recreate only web, verify health. Database restore is not automatic and must not overwrite newer user activity. A database archive TOC check is not a restore drill.

Pre-release evidence:
- Recovery files completed under `/opt/kidsmap/backups/releases/20260910-map-admin-113802`: custom PostgreSQL archive (TOC readable), static archive (tar listing readable), protected environment copy; previous image additionally tagged `kidsmap-web:rollback-20260910-map-admin`. An earlier partial archive from the stdin interruption was retained, not used as the completed backup.
- `node static/js/tests/google_maps_motion.test.js`:6/6 passed. `DJANGO_TESTING=1 .venv/bin/python scripts/tests/test_local_map_environment.py`:4/4 passed. Changed/new JavaScript syntax:11 files passed. Credential-pattern scan:47 files, no matches. `git diff --check`:passed after whitespace cleanup.
- `node /tmp/run_map_browser.cjs scripts/tests/public_map_motion.browser.js`:all13 scenarios passed at360/390/768/1024/1280/1440,62 local public places plus620 browser-only fixture. Zero JS exceptions; nine known isolated-media hero image404s. Runtime RASTER, no Advanced Markers capability.
- Local Chromium admin render smoke:7 modified lists × widths390/1440, all HTTP200, no JS exceptions/static failures. Initial mobile overflow in region/staff tables and user toolbar was corrected by scoped horizontal table scrolling and toolbar wrapping; final document overflow0 for all14 page/width pairs. No private user rows or screenshots were exported in reports.
- Isolated public Django smoke:86 tests,8 failures+1 error. All failing labels and outcomes reproduced on pristine initial HEAD (8 test methods, one method has multiple subtest failures); no assertions changed. Full suite is not claimed green. Initial runner invocation failed from compatibility-package path precedence, corrected by allowing manage.py to prepend src.
- Admin/region/ownership checks and exact baseline classification are recorded in `2026-09-10-release-admin-checks.md`. Region stale worker-lifetime cache and search/filter composition regressions corrected. A pre-existing ownership endpoint permission gap was reproduced and closed before deployment; no production exploitation assessment was performed.
