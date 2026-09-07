# Full local changes release — 2026-09-07

User explicitly authorized commit/push of all current changes, server deployment and verification. This supersedes the earlier audit-only/local-only scope for this release. No user deletion, guessed role escalation or password/email changes are part of deployment.

- [x] Inventory current worktree, origin/main, server checkout and image; preserve server Google OAuth patch/config.
- [x] Validate all changed domains on isolated PostgreSQL; gettext/JS/diff and credential-pattern scan. Record existing unrelated failures honestly.
- [ ] Keep a protected server-only pre-release DB dump, old image tag and server worktree patch; no cleanup of previous backups. Verify dump structure. Account for review migration removing uniqueness before considering rollback.
- [ ] Commit/push exact reviewed worktree, fetch exact release on server; build while old app remains running; migrate, compile/static/check; start new image.
- [ ] Verify image/commit/schema, public/auth/admin/static/media/roles/reviews/UI; production checks use read-only probes or rollback-only synthetic DB fixtures, not real user mutations. Report limits and final Git/server state.

Pre-push: 162/162 targeted PostgreSQL tests passed, 129.845 s; Django check and migration drift passed; gettext AZ/EN/RU, changed JS syntax and diff passed. Credential-pattern scan: 90 changed/new files, no private-key/token patterns. Source server OAuth files match local main; remaining differences are already reviewed incoming owner/phone changes. Full repository suite is not claimed green (previous baseline admin failures documented).

Google OAuth: 27/27 isolated PostgreSQL tests passed, 10.047 s. Protected server dump (custom format) created and pg_restore --list succeeded; previous image retained.
