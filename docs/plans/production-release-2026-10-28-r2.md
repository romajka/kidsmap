# Production release 2026-10-28, second batch

The user explicitly authorized publishing all pending changes to Git and applying them to production. Entry HEAD: a5262e13b71eac7121cc55eab712f21cbd4bf1ec. Entry worktree/index and source files are preserved in /tmp/kidsmap-release2-20261028. Verification runs from an immutable source copy at /home/ramin/km-rel2-1028.

Scope: pending admin search, navigation, moderation, ratings and owner-team interfaces; optional programme-dependent age across editors, public cards, filtering and maps; locales; isolated test-runner optimization and accompanying checks. Include only reviewed source and documentation; no credentials, QA data, media or runtime evidence.

Release corrections: suggestion endpoints enforce model view/change access, and organization search is registered only on OrganizationAdmin. Preserve the existing mobile pricing acceptance contract (16px inset, 20px gap, 10px chevron). Migration 0151 adds one BooleanField with Python and database defaults False; the database default lets the previous image continue inserting rows during activation or rollback. No backfill changes catalogue content.

1. Run the complete isolated split Django gate on fresh owned PostgreSQL, plus standalone Python/JavaScript, rendered photo and browser full/roles/refinement/feedback checks. Preserve assertions and record any failure.
2. Commit the exact verified snapshot, push the current branch and fast-forward main without force. Use [skip ci] to prevent a second automatic deployment through the old image override. Preserve any later shared worktree edits and report the release boundary.
3. Preserve the currently active image, compose override, storage mapping, database dump and static archive. Verify a restore in a network-disabled disposable PostgreSQL. Keep production records on the server.
4. Build a unique image from the exact Git archive. Preserve the active compose environment and storage settings. Verify candidate source hashes, exclusions, checks, migration drift and SQL; only catalog0151 may be pending.
5. Take a fresh pre-migration dump, migrate with lock/statement timeouts, collect static without clearing old hashed assets, replace only web and check health. Do not run the generic release script or synchronize site defaults.
6. Fast-forward the server checkout to the same commit. Verify Git/image SHA, storage parity, applied migration/default, public/localized/admin HTTP, rendered affected pages and actual hashed asset bytes.

Rollback: reactivate the saved image/override and previous static manifest. Keep the additive column and its False database default; do not restore a database over newer live writes or automatically unapply migration 0151. Recovery directory: /opt/kidsmap-releases/20261028-release2.
