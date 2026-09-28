# Release all current KidsMap changes

Authorization: user explicitly requested push and application of **all changes** on production on 2026-09-28. This supersedes the earlier read-only deployment boundary for this release. No repeated approval required. Work inline; no independent subagents.

Scope: all tracked modifications and nonignored untracked source/tests/static/docs currently in the worktree; moderation SLA queue and lifecycle migrations 0115/0116, volunteer editor/duplicate checks/deletion, catalog/contacts UI and WhatsApp defaults, account-deletion locking remediation, staff creation email validation. Include the minimal PostgreSQL superadmin promotion locking correction, already reproduced failing in existing tests, to complete staff administration checks before release. Exclude secrets, temporary data, test media, backups and caches.

Release source: `seo-indexability-20260916`, initial HEAD `ef949ea99a7635076e4477a29d42b0a5d63796d4`, both local and production. Push the current branch, then deploy the exact reviewed commit. Do not merge to main or trigger a separate main deployment.

- [x] Verify all affected backend flows on a disposable PostgreSQL 17 database, DJANGO_TESTING=1, isolated cache/media/email and no production credentials. Verify drift/system checks, syntax and scoped whitespace. Record baseline failures explicitly; do not weaken assertions.
- [ ] Review staged file inventory and scan added content for credential patterns without outputting values. Commit and push all intended changes on the current branch.
- [ ] Preserve the current production image under a rollback tag and write a production-only rollback manifest. Build the new image while the current container serves traffic.
- [ ] Create a private pre-release DB backup without invoking retention cleanup, verify archive readability, record only aggregate metadata. Verify production migration plan contains only 0115/0116 and system check passes on the new image.
- [ ] Apply release tasks with statement/lock timeouts; compile translations, synchronize blank defaults and collect static. Activate the new web image.
- [ ] Verify exact image/source revision, migration state, checks, health and public/admin smoke paths. Verify staff add form under read-only transactions using synthetic requests; no actual staff account creation in production for QA.
- [ ] Save sanitized release evidence and finish with the deployed commit and remaining baseline limits.

Recovery: new schema additions are nullable and compatible with the old image; `needs_changes` is a new status choice, not a destructive database constraint. If activation/smoke fails, restore web from the preserved old image and restore old static assets; keep additive migrations rather than dropping columns/data. A full database restore is reserved for confirmed corruption and requires a deliberate recovery decision, not an automatic deletion of newer writes. If migration fails, leave the current application online and inspect the failure before further mutation.

Account deletion: deploy its current code/documentation; do not invent or activate pending retention policy settings, scheduler or operational prerequisites. No real user data deletion is part of release.
