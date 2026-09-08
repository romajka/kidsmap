# Permissions — verified LOCAL source, 2026-09-08

Owners: django-reviewer + security-reviewer; DB identities: database-reviewer. [Current snapshot](current-snapshot.md).

| Boundary | Source of truth | Consumers / mandatory evidence |
|---|---|---|
| Owner/team | services/place_access.py; models/owner.py | owner_place_use_cases/controllers, per-Place active team permissions |
| Owner handover | place_access.is_direct_place_manager | Creator fallback only when owner is NULL; created_by otherwise audit history |
| Volunteer group | services/staff_roles.py | is_volunteer excludes superuser; workspace requires authenticated active staff |
| Volunteer route gate | volunteer_middleware.VolunteerAccessMiddleware | Blocks ordinary admin/owner/document routes, including localized aliases |
| Volunteer object scope | services/volunteer_places.own_places | created_by=user AND owner NULL AND deleted_at NULL AND not temporary; dashboard counts/search and detail/edit/photo use scope |
| Service boundary | volunteer_places.save_proposal/restart_proposal | Recheck scope, signed base snapshot and revision version; payload distinct from live Place |
| Superadmin review | volunteer_places.require_reviewer/review_proposal | Active staff superuser, locks, pending/version/base checks, owner handover, backend validation/readiness |
| Owner permission denial | place_access.direct_place_permissions/staff_has_place_permission/has_place_permission | Volunteer rejection even with accidental model/team permissions |
| Admin role presets | domain_admin/user.py:ADMIN_ROLE_CHOICES, StaffAccessUserAdmin.save_related | Existing Django groups/permissions; volunteer preset clears individual permissions |

Volunteer A cannot access Place B through workspace routes/services; this does not prohibit viewing an otherwise public Place on the public website. Hidden buttons are not authorization. Direct GET/POST/AJAX/object IDs, counts/search and photo routes require negative fixtures. Public media storage is a separate boundary.

Tests present: catalog.testcases.test_volunteer_admin, catalog.testcases.test_volunteer_dashboard, catalog.testcases.auth_access. Particularly test_all_foreign_object_methods_and_ajax_are_denied and test_counts_search_and_filter_are_scoped_to_current_volunteer. PostgreSQL concurrency case test_two_reviewers_cannot_apply_the_same_revision_twice is not proven by source or SQLite.

Google identity is separate from authorization: google_auth._resolve_google_user and KidsMapSocialAccountAdapter validate provider identity/ambiguity/inactive users; real provider state/config is UNKNOWN here. Do not restore removed UserProfile global owner role.
