# KidsMap production release — 2026-11-06

User authorization: push the current new changes to GitHub and apply them to the supplied KidsMap production server. Application snapshot: 64ace560f51d7ce917a1b42e6fc5bae827dd125d, nine commits after the previously deployed 36f2df595b253055f04848dce7dab27837826498. Original primary checkout clean. Use the existing isolated worktree for release metadata.

Scope: specialist moderation feedback and resubmission, readable notification email templates, admin login return destination, catalogue/map filtering and list ordering, shared visual foundation, compact homepage assets, place/add-place/unavailable page refinements. No migration files changed.

1. Freeze an exact source archive. Run the complete isolated PostgreSQL gate, CI JavaScript unit/DOM selection and standalone Python checks. Preserve current dirty work if it appears later.
2. Read production revision, effective compose and service identities. Keep private backups of database/static/compose and previous image; verify database restoration in an isolated disposable container. Prepare executable rollback.
3. Push release branch and fast-forward main only. Add [skip ci] to the release metadata commit to avoid the legacy deployment racing the controlled update. Build the exact Git archive with an OCI revision label.
4. Require zero pending migrations, collect static without clearing, and replace only web. Preserve env, mounts, ports, networks, PostgreSQL and Redis identities.
5. Verify health, exact source/static hashes, localized public/admin-login routes and desktop/mobile rendering. Keep credentials, private records and server recovery artifacts outside Git.

The outbox delivery script is included. Enabling a new schedule and sending the existing queue requires the user's separate answer; do not trigger email delivery during release verification. Existing schedules are preserved.

Execution evidence: `/home/ramin/kidsmap/.tmp/release-20261106/`. Private server recovery directory: `/opt/kidsmap-releases/20261106-site-improvements/`.
