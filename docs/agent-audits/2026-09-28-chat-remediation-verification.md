# Chat changes — remediation verification, 2026-09-28

## Source and scope

LOCAL HEAD: `ef949ea99a7635076e4477a29d42b0a5d63796d4`, branch `seo-indexability-20260916`. Results describe the dirty WORKTREE, not PRODUCTION. No production writes, deploy, commit, push or deletion of real records. Unrelated concurrent edits were preserved. All browser records were synthetic in a temporary SQLite database; tests used isolated database/cache/media/email with `DJANGO_TESTING=1` and external integrations disabled.

## Fixed

- Guarded volunteer deletion is reachable, CSRF-protected, permission/status checked and transactional, with audit. Pending, published, foreign and owned cards cannot be deleted by a volunteer.
- Duplicate prevention reads current working payloads, checks every same-name candidate, serializes concurrent creation and runs before upload storage writes. A distinct branch needs explicit confirmation and a different address or coordinates. The checkbox and existing-card link are visible.
- Volunteer verification copy is localized RU/AZ/EN; photo inputs have labels and linked errors. Mobile readiness and SLA layouts no longer overflow the whole page.
- Confirmed SLA: places 72 calendar hours, reviews 24; warning 50%, critical 80%, breach 100%; needs-changes pauses, resubmission restarts. Submission/decision timestamps and actors are integrated, with a permission-scoped queue and localized user messages. Approved revisions are not counted twice; paused age retains accrued time.
- PostgreSQL-specific account-deletion failure: nullable user outer joins were incorrectly locked. Request/user rows now lock separately; cancellation, legal hold and finalization pass PostgreSQL tests.
- Editor initialization no longer triggers a false unsaved-changes warning. Actual field editing still marks the form dirty.

## Executed verification

Runner: `/tmp/kidsmap-chat-review-ux0n43/checks.py`. Removes `DATABASE_URL`, `LEGACY_DATABASE_URL`, `REDIS_URL`; overrides databases/media/email/analytics/maps. A fast password hasher is used only for the repeated isolated regression runs, not application settings.

1. PostgreSQL 17, loopback temporary container, `KIDSMAP_REVIEW_POSTGRES=1 KIDSMAP_REVIEW_FAST_HASHER=1`: default labels `test_volunteer_admin`, `test_moderation_sla`, `test_account_deletion`, `test_volunteer_dashboard`, `test_review_confirmation`, `test_place_review_cooldown`, `place_readiness`: **169 tests, OK, no skips**. Includes concurrent duplicate creation and moderation tests. Earlier run reproduced 8 account-deletion failures/errors before the PostgreSQL locking fix.
2. SQLite expanded run with labels `owner admin specialists test_account_deletion test_review_confirmation test_place_review_cooldown test_volunteer_dashboard place_readiness auth_access`: **432 tests, 4 failures + 3 errors**. The remaining seven all reproduce on an isolated `git archive HEAD` checkout, running the exact seven tests: **4 failures + 3 errors**. No assertion weakening. Earlier receipt-message regression is fixed.
3. Isolated `check`, `makemigrations --check --dry-run`, `migrate`: **no system errors, no model drift, migrations applied**. Includes new `0115` / `0116`.
4. `node --check static/admin/js/volunteer_place_form.js`: exit 0. Scoped `git diff --check -- src/catalog static/admin src/config/settings.py`: exit 0. Whole worktree has an unrelated CSS EOF warning; it was not silently modified.
5. Rendered Playwright checks: editor and queue at 375/768/1024/1440px; editor photo label counts `[1,1]`; admin active revision age `[1,6]`, readiness `12/12`; localized RU/AZ/EN verification/queue. Document width equals viewport at all tested queue sizes. Table retains its own horizontal scrolling on mobile. Owner at 375px sees needs-changes status and saved moderator reason, document width 375px. Duplicate blocked; explicitly confirmed branch created; own draft removed after confirmation. Admin/owner console: zero errors/warnings on final checks. Fresh editor navigation succeeds without a beforeunload warning; editing marks unsaved state.

Ignored browser evidence: `output/playwright/chat-fixed-editor-*.png`, `chat-fixed-verification-*.png`, `chat-fixed-sla-*.png`, `chat-fixed-owner-375.png`. Temporary logs remain under the runner directory; they are not committed repository artifacts.

## Pre-existing expanded-suite failures

`admin.TestAdminOwnershipModerationUX`: `test_admin_can_approve_request_with_direct_button_url`, `test_place_admin_bulk_action_regeocodes_selected_places`, `test_place_admin_can_refresh_coordinates_from_address`, `test_failed_publish_keeps_published_card_active_and_shows_all_issues`, `test_place_admin_can_unpublish_place_from_change_form`.

`owner.TestOwnerPlaceManagementAndPermissions.test_owner_place_create_requires_name_in_azerbaijani`; `admin.TestPlaceRatingsAdmin.test_changelist_pagination_preserves_filters_search_and_sorting`.

These involve the existing geographic/publication/form and pagination contracts. They remain unresolved; the full project suite is not green. Geographic publication guards were not disabled just to satisfy old fixtures.

## Not verified / activation still required

Production state, release readiness of unrelated changes, production migration execution, deletion retention-policy activation, scheduler operation and all-destination 15-day backup expiry. Business approval is recorded in `docs/policies/account-data-retention.md`; it does not establish those operational facts. No claim of an entirely bug-free project or production rollout.
