# Admin moderation fixes Implementation Plan

> **For agentic workers:** implement task by task with TDD and review checkpoints. User directly authorized all eight findings on 2026-10-16. Canonical project roles provide disjoint parallel support; no further local implementation approval is needed.

**Goal:** Fix AM-01 through AM-08 from the completed moderation audit.

**Architecture:** Administrative review decisions stay on the admin origin and use atomic, revision-aware services. Existing public rendering/visibility remains shared; admin-only preview must never publish records. Status changes redirect to concrete objects, not filtered proxy objects.

**Tech Stack:** Existing Django, PostgreSQL, vanilla templates/JS, gettext.

**Spec:** `docs/qa/admin-moderation-audit-2026-10-16-r1/BUG_REPORT.md`.

## Global Constraints

- Preserve dirty/untracked work; no application-wide revert, commit/push or production mutation.
- Test with DJANGO_TESTING=1, disposable DB/cache/media/email, external integrations disabled.
- Keep host-session separation and permission checks; do not broaden cookies.
- Existing stale ownership request remains protected; no bypass, automatic ownership grant or data repair.
- Independent reviewers own separate files; root owns integration/browser/report.

## Task 1: Reviews (django-reviewer)

Files: `services/review_versions.py`, `domain_admin/review.py`, `domain_admin/review_versions.py`, `proxy_apps/catalog_moderation/admin.py` (review-specific sections only), review templates/static as needed; new `test_admin_review_workflow_fix.py`.

- [x] Write failing tests for admin-origin workflow, object ACL, pending edits in queue, atomic bulk decisions/repeated decisions, hiding a published review while preserving its candidate and rating/public readback.
- [x] Run RED in owned isolated profile.
- [x] Add protected admin target review route. Use shared typed review controller/template with an admin return path and admin-bound form actions. All visible review links resolve to admin origin.
- [x] Replace legacy field updates with version-aware moderation and explicit visibility operations; verify concrete and proxy actions, single and bulk. Preserve revision history and pending candidate when hiding; do not bypass conflicts.
- [x] Run GREEN plus representative existing typed-review/public-rating/permission tests; write handoff and exact commands.

## Task 2: Places, stale requests and translations (django-reviewer support)

Files: `domain_admin/place.py`, `domain_admin/owner.py`, `services/admin_place_preview.py`, preview services/templates, `locale/*/LC_MESSAGES/django.po`, new `test_admin_place_moderation_fix.py`.

- [x] Write failing tests for pending-place preview without public exposure, concrete redirect after publishing, stale request list/confirmation state, and rendered RU action labels.
- [x] Run RED in separate isolated DB.
- [x] Expose permission-checked admin site-preview for Place, reusing existing preview rendering without depending on an ownership request; replace pending-public link with this route.
- [x] Redirect proxy publication to the concrete Place admin. Show stale block reason before allowing confirmation; preserve actual moderation validation.
- [x] Correct only audited erroneous translations (Открыть, Низкая оценка, Риски and tightly related misleading actions). Build isolated MOs.
- [x] Run GREEN and affected shared place/ownership preview/publication tests; write handoff.

## Task 3: Integration and rendered acceptance (root)

- [x] Capture source manifest and keep both workers disjoint; review security boundaries and diff.
- [x] Build a fresh owned runtime from the final WORKTREE with isolated DB/media/cache/email/locales.
- [x] Run review creation/edit → admin queue → approve/reject/hide/repeat → public text/rating checks. Run pending place → preview → publish → concrete admin/public checks. Use fictional accounts only.
- [x] RU/AZ/EN × 390/768/1024/1280/1440 affected pages; screenshot review, keyboard/modals, console/network, no accidental public-origin jumps.
- [x] Verify source hashes, report every AM item with current evidence, residual limits and production-not-deployed boundary. No claim of production acceptance from local QA.

No commits are planned; user requested fixes and report, not a Git or deployment operation.
