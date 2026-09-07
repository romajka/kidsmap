# Volunteer admin implementation plan

**Goal:** Volunteers create and edit only their own places; a Superadmin approves publication and every later change. Published content stays unchanged during review.

**Authorization:** User confirmed keeping all four remaining production accounts and both moderation rules. Local implementation of this scope is authorized. Account ownership for the original Superadmin request remains unresolved. No existing account/role is changed by this implementation; no automatic production release.

**Architecture:** Use a standard Django group as the volunteer marker, with no global model permissions. Give that group a small workspace inside Django admin. A separate per-place revision stores proposed content; only explicit Superadmin approval copies it into Place. Existing publication readiness, pricing, schedule and image validation remain authoritative. Guard every admin route and the alternate owner routes against bypass.

**Tech stack:** Django 6, existing SSR/Jazzmin, PostgreSQL production; isolated local test database/cache/media.

**Spec:** User instructions in this thread, confirmed 2026-09-07: own places only; no delete; publish and subsequent edits require approval; keep previous public version.

## Tasks

- [x] Write and run failing HTTP permission tests: volunteer workspace, forbidden direct admin URLs/POSTs, role creation, nonstaff/anonymous exclusion.
- [x] Add `services/staff_roles.py`, a standard group marker and the Volunteer choice in `domain_admin/user.py`. Existing staff presets stay unchanged.
- [x] Add `models/volunteer.py` and a migration for a versioned per-place proposal (payload, base snapshot, review state, author/reviewer). No migration alters existing users.
- [x] Add `volunteer_forms.py` and `services/volunteer_places.py`: explicit editable-field allowlist; draft/submission; validated images, pricing and schedule; atomic approval/rejection; stale-form and concurrent-live-edit rejection; audit entries.
- [x] Add `domain_admin/volunteer.py`, templates and scoped styles. Volunteer list/form and Superadmin review queue live under admin. Reuse existing pricing/schedule editors.
- [x] Add a resolved-route boundary in `volunteer_middleware.py`; place/owner permission services also reject alternate write access for volunteers. Keep normal users/owners/staff unaffected.
- [x] Test published-before/after behavior, malicious payloads, uploads, rejection/resubmission, stale approval/save, reassigned ownership, taxonomy validation, readiness and CSRF.
- [x] Run targeted existing owner/admin/auth/public tests in isolated services, migration drift/system checks, browser layout and interaction checks.
- [x] Record the actual role matrix, commands/results, limitations and release requirements in `docs/ADMIN_ROLES_AND_PERMISSIONS.md`. Review the final diff; no commit/push/deploy in this local task.

## Verification commands

The isolated runner clears inherited environment before loading Django, sets `DJANGO_TESTING=1`, disposable database/media, LocMem cache/email, disables external integrations and runs `check`, `makemigrations --check --dry-run` and selected `test` labels. First target: `catalog.testcases.test_volunteer_admin`; regressions: existing owner, admin and auth suites. Never execute test commands against production.
