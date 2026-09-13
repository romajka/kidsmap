# Staff Role Change and Superadmin Approval Implementation Plan

> **For agentic workers:** Implement task-by-task with a failing regression test before every production change. Do not commit, push, deploy, migrate production data or contact production under the current audit contract.

**Goal:** Permit safe changes between existing staff roles without deleting users, while making a Superadmin promotion a two-person, auditable workflow that cannot remove the final active Superadmin.

**Architecture:** Centralize role resolution and role assignment in a service instead of modifying `is_superuser`, groups and permissions independently from Django admin. Non-Superadmin staff roles are applied atomically by an existing Superadmin. A Superadmin promotion creates a pending `SuperadminPromotionRequest`; a different active Superadmin must approve it in a locked transaction before the service sets `is_superuser=True`. Role history is append-only in application flows and displayed read-only in the staff admin.

**Tech Stack:** Django 6, Django auth `User`, groups and permissions, Django admin, PostgreSQL constraints/row locks, Django email backend for notification.

**Spec:** User report dated 2026-09-13: correct mistaken `Admin → Volunteer` without deleting the account; Superadmin request, second-person approval/rejection, notification, audit trail and last-Superadmin protection.

## Global Constraints

- A current Superadmin is the only actor permitted to change ordinary staff roles or initiate a Superadmin promotion. A different current, active Superadmin must approve a promotion; the initiator cannot approve their own request.
- An ordinary Admin, Moderator, Content Manager or Volunteer cannot grant, request, approve or directly set Superadmin status.
- The standard staff change form must not expose writable raw `is_superuser`, `is_staff`, `groups` or `user_permissions` controls; all role writes go through the service.
- A user account and all its places remain intact through every role change.
- Never demote, deactivate or delete the last active Superadmin. The service must enforce this under database locks; a disabled button alone is insufficient.
- Notifications are an in-admin pending-request list plus best-effort email to active Superadmins. Email failure must not activate a role or roll back the security record.
- All automated tests use `DJANGO_TESTING=1` and a disposable database. PostgreSQL-only lock/constraint tests are marked as such and do not run against production.

---

### Task 1: Record the existing unsafe behavior in regression tests

**Files:**

- Modify: `src/catalog/testcases/admin.py`
- Create: `src/catalog/testcases/test_staff_role_workflow.py`

**Interfaces:**

- Consumes: `admin:catalog_staffaccessuser_add`, `admin:catalog_staffaccessuser_change`, Django `User` flags/groups/permissions.
- Produces: tests that distinguish direct legacy escalation from the requested workflow.

- [ ] **Step 1: Add a failing existing-user role-change test.**

  Create a staff user with the moderator permission preset, created places and an active session history. As a Superadmin, submit the future role-change control with `volunteer`. Assert the same user primary key, created-place foreign keys and profile remain, `is_staff` stays true, the volunteer group is assigned, and direct permissions are cleared.

- [ ] **Step 2: Run the test and observe the absent role selector.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_staff_role_workflow.StaffRoleWorkflowTests.test_superadmin_changes_existing_admin_to_volunteer_without_deleting_user --noinput`

  Expected before implementation: FAIL because `admin_role` exists only on `StaffAccessUserCreationForm`; `save_related` returns immediately for edits.

- [ ] **Step 3: Add failing Superadmin workflow tests.**

  Assert that a Superadmin's request leaves the target non-superuser, creates one pending request and one history entry. Assert the initiator cannot approve it, a different Superadmin can approve it once, and the target only then gains `is_superuser=True`.

- [ ] **Step 4: Add failing negative-path tests.**

  Assert that every non-Superadmin receives `403` for role change, promotion request, approval and rejection endpoints. Assert direct change-form POST fields for `is_superuser`, groups and permissions do not elevate a user. Assert duplicate pending requests, a disabled target, an inactive confirmer and a stale/rejected request cannot promote anyone.

- [ ] **Step 5: Add failing last-Superadmin tests.**

  With exactly one active Superadmin, attempt role demotion, deactivation and deletion through all staff management endpoints. Assert each action is refused and leaves the account privileged and active. With two active Superadmins, assert one may be demoted only by the other.

### Task 2: Create one canonical staff-role service and immutable history

**Files:**

- Modify: `src/catalog/services/staff_roles.py`
- Create: `src/catalog/services/staff_role_workflow.py`
- Create: `src/catalog/models/staff_role.py`
- Modify: `src/catalog/models/__init__.py`
- Create: `src/catalog/migrations/0104_staff_role_audit_and_superadmin_promotion.py`
- Modify: `src/catalog/testcases/test_staff_role_workflow.py`

**Interfaces:**

- Consumes: Django `User`, `Group`, permission presets and the `KidsMap Volunteers` group.
- Produces: `current_staff_role(user)`, `assign_staff_role(actor, target_id, role)`, `request_superadmin_promotion(actor, target_id)`, `resolve_superadmin_promotion(actor, request_id, approve)`.

- [ ] **Step 1: Write failing pure-service tests for role resolution and assignment.**

  Test `current_staff_role` for Superadmin, Volunteer, Moderator and Content Manager. Test `assign_staff_role` uses exactly one role representation: Volunteer has its group and no direct permissions; Moderator and Content Manager have their exact permission preset and no volunteer group; Superadmin is rejected by this direct-assignment operation.

- [ ] **Step 2: Run the service tests and observe the missing API.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_staff_role_workflow.StaffRoleWorkflowTests.test_assign_staff_role_replaces_the_previous_role_atomically --noinput`

  Expected before implementation: FAIL because role constants and mutations are embedded in `domain_admin.user` and only support new users.

- [ ] **Step 3: Add `StaffRoleAudit`.**

  Store `actor`, `target`, stable actor/target display snapshots, `old_role`, `new_role`, `action`, timestamp and an optional request reference. Supported actions are `ROLE_CHANGED`, `SUPERADMIN_REQUESTED`, `SUPERADMIN_APPROVED`, `SUPERADMIN_REJECTED`, `SUPERADMIN_DEMOTION_BLOCKED` and `LAST_SUPERADMIN_BLOCKED`. Register a read-only admin view; prohibit add, edit and delete through the application admin.

- [ ] **Step 4: Add `SuperadminPromotionRequest`.**

  Store `target`, `initiated_by`, `decided_by`, status (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`), creation/decision timestamps and optional rejection note. Add a PostgreSQL partial unique constraint allowing at most one pending request per target. Keep the target non-superuser until the approval transaction succeeds.

- [ ] **Step 5: Implement the locked workflow service.**

  Use `transaction.atomic` and `select_for_update` on target users, the promotion request and the active Superadmin set before a privilege-changing write. `assign_staff_role` checks actor authority, rejects Superadmin role input, replaces the target's group/permission representation atomically, writes `StaffRoleAudit`, and blocks operations that would remove the final active Superadmin. `request_superadmin_promotion` requires an active Superadmin actor and a non-superuser active target. `resolve_superadmin_promotion` requires a distinct active Superadmin, locks the request, validates its pending state and target, sets `is_staff=True` and `is_superuser=True` only on approval, then records the decision.

- [ ] **Step 6: Run Task 2 tests.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_staff_role_workflow --noinput`

  Expected after implementation: service and audit tests pass.

### Task 3: Replace raw staff-role editing in the primary admin UI

**Files:**

- Modify: `src/catalog/domain_admin/user.py`
- Modify: `src/catalog/templates/admin/catalog/staffaccessuser/change_form.html`
- Modify: `src/catalog/templates/admin/catalog/staffaccessuser/change_list.html`
- Modify: `static/admin/css/pages/kidsmap_staff_access_list.css`
- Modify: `src/catalog/testcases/admin.py`

**Interfaces:**

- Consumes: canonical role service, promotion request status and read-only audit records.
- Produces: a role selector for ordinary changes and explicit request/approve/reject controls for Superadmin promotions.

- [ ] **Step 1: Write failing admin-render tests.**

  As a Superadmin, GET an existing staff user form and assert it contains the current role, an ordinary-role selector and a role history block, but no writable raw `is_superuser`, `groups` or `user_permissions` inputs. Assert an active promotion request shows its target, initiator, created time and status. As a non-Superadmin, assert the controls and all management URLs are unavailable.

- [ ] **Step 2: Run the admin-render tests and observe the raw Django permissions fieldset.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_staff_role_workflow.StaffRoleWorkflowTests.test_staff_change_form_uses_role_workflow_not_raw_permission_fields --noinput`

  Expected before implementation: FAIL because the form renders writable `is_superuser`, `groups` and `user_permissions` for a Superadmin.

- [ ] **Step 3: Add an edit form with `admin_role` for ordinary roles.**

  Use the same canonical choices as creation, excluding Superadmin from the direct selector. On a valid ordinary-role POST, call `assign_staff_role`; preserve the account, profile and created places. Update `staff_role` and filters to distinguish Moderator and Content Manager rather than rendering both merely as `Admin`.

- [ ] **Step 4: Make Superadmin a separate request action.**

  Replace direct Superadmin creation/selection with a request action visible only to active Superadmins. The action creates `SuperadminPromotionRequest`, renders an unambiguous pending status and never calls `obj.is_superuser = True` directly.

- [ ] **Step 5: Add approval and rejection endpoints.**

  Register admin-site protected POST-only URLs for request approval and rejection. Confirm identity of the target, initiator and second approver in the confirmation page. Reject self-approval and stale/duplicate requests through the service. Show success or refusal messages without disclosing sensitive audit data to unauthorized users.

- [ ] **Step 6: Preserve last-Superadmin protection across the UI.**

  Route role demotion and active-status changes through the service. Continue blocking deletion of the self account and last Superadmin, and additionally prevent status deactivation of the final active Superadmin.

- [ ] **Step 7: Run focused UI tests.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_staff_role_workflow catalog.testcases.admin.UserAdminUXTests --noinput`

### Task 4: Deliver notifications and a reviewer work queue

**Files:**

- Modify: `src/catalog/domain_admin/user.py`
- Create: `src/catalog/templates/admin/catalog/staffaccessuser/superadmin_promotion_request_list.html`
- Create: `src/catalog/templates/admin/catalog/staffaccessuser/superadmin_promotion_request_confirm.html`
- Modify: `src/catalog/services/staff_role_workflow.py`
- Modify: `src/catalog/testcases/test_staff_role_workflow.py`

**Interfaces:**

- Consumes: pending promotion request, current active Superadmin query and Django mail connection.
- Produces: an internal review queue and notification that identify target, initiator, request time and approve/reject actions.

- [ ] **Step 1: Write failing queue and notification tests.**

  Create a pending request and assert a second Superadmin sees it in the protected queue with the target, initiator, created timestamp and both decision actions. Use Django's test email outbox to assert an email is addressed only to active Superadmins other than the initiator, contains no password or token, and links to the protected confirmation page.

- [ ] **Step 2: Run the notification test and observe the missing queue.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_staff_role_workflow.StaffRoleWorkflowTests.test_pending_superadmin_request_notifies_other_active_superadmins --noinput`

  Expected before implementation: FAIL because no promotion request model, queue or notification exists.

- [ ] **Step 3: Send notifications only after the database commit.**

  In `request_superadmin_promotion`, schedule the mail send with `transaction.on_commit`. Catch and log delivery failures without changing request status. The in-admin queue remains the authoritative notification, so email configuration cannot become a privilege escalation dependency.

- [ ] **Step 4: Render the protected queue and confirmation screen.**

  List only pending requests to active Superadmins. The confirmation screen presents the target, initiator, creation time and audit history, requires an explicit POST action, and offers rejection with an optional reason. No GET request changes a role or request state.

- [ ] **Step 5: Run Task 4 tests.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_staff_role_workflow --noinput`

### Task 5: Validate migrations, concurrency and the real Admin-to-Volunteer correction

**Files:**

- Modify: `src/catalog/testcases/test_staff_role_workflow.py`
- Modify: `src/catalog/testcases/admin.py`

**Interfaces:**

- Consumes: role service, new models, staff change admin and notification queue.
- Produces: evidence that ordinary role corrections and Superadmin safety controls work together.

- [ ] **Step 1: Add a PostgreSQL concurrency test.**

  Start two independent transactions that approve the same pending request. Assert exactly one approval succeeds, exactly one audit entry records `SUPERADMIN_APPROVED`, and the second call receives a stale-request error. Mark this test with `skipUnless(connection.vendor == 'postgresql', ...)`.

- [ ] **Step 2: Add direct-bypass regression tests.**

  Submit crafted posts to the normal staff admin change and add URLs with `is_superuser=on`, arbitrary groups and direct permissions. Assert the values are ignored or rejected unless they are supplied through the audited role service. Include an attempt by a target user to approve their own request.

- [ ] **Step 3: Run focused tests and structural checks.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_staff_role_workflow catalog.testcases.admin.UserAdminUXTests --noinput`

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py check`

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py makemigrations --check --dry-run`

- [ ] **Step 4: Perform isolated rendered-browser acceptance.**

  At 390, 768, 1024, 1280 and 1440 pixels, verify staff list role labels, Admin-to-Volunteer correction, pending Superadmin status, second-superadmin approve/reject controls, self-approval refusal, last-Superadmin refusal, audit history and keyboard focus. Use only isolated fixture data.

- [ ] **Step 5: Apply the requested real role correction after implementation.**

  Identify the intended account by an exact username or email supplied by the requester, display the resolved account identity and current role for review, then use the same audited Admin-to-Volunteer action. Verify the account ID, profile and created-place counts are unchanged and report the resulting role-audit record. Never guess a user from a partial name.

## Plan self-review

- Existing source has no role-change workflow or generic notification model; the plan creates narrow, reviewable models rather than coupling permission elevation to an unrelated notification system.
- The current direct Superadmin creation flow is intentionally replaced, not wrapped: the new UI contains no direct Superadmin selector and the service rejects it as an ordinary role assignment.
- The plan covers account preservation, all configured ordinary roles, two-person promotion approval, notifications, audit history, raw-field bypasses, stale decisions, and the last active Superadmin invariant.
- The exact account for the requested `Admin → Volunteer` correction is unknown and remains untouched until the requester supplies a username or email after the feature is implemented.
