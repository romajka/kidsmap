# Account Deletion and Retention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an authenticated user request, confirm, cancel during a grace period and complete deletion of their account, while a scheduled process deletes or anonymizes related data according to an approved, versioned retention policy.

**Architecture:** Account deletion is a stateful workflow, not `User.delete()` from a profile view. A request freezes access immediately after double confirmation, records only a pseudonymous deletion reference, and is processed idempotently by a Django management command. The processor removes direct personal data, anonymizes content whose deletion would break public or moderation history, then deletes the Django user only after every relationship has been handled safely.

**Tech Stack:** Django auth `User`, Django ORM transactions and row locks, Django forms/views/templates, email verification service, Django management command scheduled by infrastructure, Django `TestCase`.

**Spec:** User request of 2026-09-13: self-service account deletion with clear consequences, repeated confirmation, account-disabled state, cancellation grace period, automatic retention processing, handling of reviews/favorites/subscriptions/owner content/moderation history, audit trail without unnecessary personal data, and backup-retention disclosure.

## Global Constraints

- Do not call `User.delete()` directly from a request handler. Current `CASCADE` links would silently erase reviews, ownership requests, favorites, reactions and other records before the retention rules are applied.
- Legal retention periods, legal-hold bases and backup obligations must be approved by KidsMap's authorized legal/privacy owner before the feature is enabled. The implementation must expose the approved policy version; it must not present an invented legal deadline to users.
- The current repository has no `Organization` model. Treat Place owner/team records as the implemented ownership model; do not claim separate Organization behavior until such a model exists.
- Do not make retention depend on an in-process thread, request lifecycle, browser timer or a best-effort queue. Use an idempotent command run by the production scheduler, with a dry-run mode.
- Deletion requests must require CSRF-protected POSTs, explicit typed confirmation, a one-time code sent to the account email, attempt limits and expiry; no GET endpoint may change state.
- Preserve no raw email, phone, name, address, review text or password in the deletion audit. Audit only the random subject reference, policy version, lifecycle timestamps, disposition counters and error code.
- Keep all automated tests on an isolated DB using `DJANGO_TESTING=1`. Do not run the destructive processor against production or local non-test data during development.
- Do not deploy, run production retention, alter backups, commit or push as part of this task.

---

## Policy decisions required before activation

The engineering work may create the workflow and its tests, but the production command must refuse to process a request until the following approved policy document exists and the version is configured. The Azerbaijan personal-data requirements explicitly include anonymization, storage and destruction among operations that need approved instructions/software; they do not provide an application-specific number of days. [Azerbaijan personal-data protection requirements](https://frameworks.e-qanun.az/20/c_f_20046.html)

| Data class | Proposed technical treatment | Duration / owner decision required |
| --- | --- | --- |
| Grace period | Account disabled, no ordinary login, user may cancel through a one-time email confirmation. | Approve exact calendar days; proposed product default: 30 days. |
| Auth/profile PII | Delete profile avatar from storage, `UserProfile`, email-verification record and user identifiers at completion. | Completion date after grace period, unless an explicit legal hold applies. |
| Favorites, reactions, review cooldowns, sessions | Physically delete. Invalidate current and existing auth sessions as soon as deletion is confirmed. | On confirmation for sessions; at completion for database rows. |
| Analytics | Remove user relation or delete direct user events; preserve only non-identifying aggregates. | Existing database audit proposes `FunnelEvent` maximum 180 days; privacy owner must confirm this applies after a deletion request. |
| Published reviews | Keep the public text/rating and moderation state only if approved policy requires preservation; set `user=NULL`, clear author name and remove reactions. | Approve whether content remains, is removed, and its retention period. |
| Ownership requests, team invitations and moderation history | Preserve status/timestamps only where operationally necessary; remove applicant/owner identity, invite email and free-text notes that may contain PII. | Approve retention period and legal basis. |
| Places, Events, specialists and public business content | Unlink the account; do not infer that public business contacts are the user's personal data. Pending/draft content must be explicitly retained, transferred or removed by the approved policy. | Approve owner-content disposition and handover rule. |
| Deletion audit | Retain pseudonymous event record; no foreign key to deleted user and no direct identifiers. | Approve audit duration and legal basis. |
| Backups | Do not rewrite historical backups. Disclose the oldest possible purge date based on the backup schedule and make new backups exclude deleted user data. | Current script removes backups older than 15 days and keeps at most five; confirm with infrastructure/legal owner and document immutable/off-site copies if any. |

## File map

- Create: `docs/policies/account-data-retention.md` — approved user-facing and operational retention matrix, policy version, legal owner, effective date, grace period, holds and backup statement.
- Modify: `src/catalog/models/user.py` — `AccountDeletionRequest` and pseudonymous `AccountDeletionAudit` models.
- Modify: `src/catalog/models/review.py`, `src/catalog/models/owner.py`, `src/catalog/models/place.py`, `src/catalog/models/specialist.py`, `src/catalog/models/site.py` — make required relations nullable/`SET_NULL` so content can be anonymized deliberately rather than deleted by User cascade.
- Create: `src/catalog/services/account_deletion.py` — transaction-safe request, confirmation, cancellation and finalization service with an explicit data-disposition registry.
- Modify: `src/catalog/forms.py`, `src/catalog/controllers/auth_controller.py`, `src/catalog/views.py`, `src/catalog/urls.py` — confirmation forms and authenticated profile endpoints.
- Modify: `src/catalog/templates/pages/account_profile.html`, `static/css/pages/account_profile.css` — settings-page disclosure, danger zone and accessible confirmation views.
- Create: `src/catalog/management/commands/process_account_deletions.py` — idempotent scheduled processor with `--dry-run`, bounded batches and machine-readable aggregate output.
- Create: `src/catalog/migrations/0105_account_deletion_retention.py` — schema and relation migrations; select the next number at execution time if another approved plan has landed first.
- Create: `src/catalog/testcases/test_account_deletion.py` — workflow, data-disposition, authorization, idempotency and command tests.
- Modify: `src/catalog/testcases/auth_flow.py` — profile/settings rendering and existing profile behavior regression coverage.
- Modify after infrastructure approval only: deployment scheduler documentation/configuration — daily command invocation, alerting and backup lifecycle ownership. Do not alter deployment configuration in this application change without that approval.

### Task 1: Approve and publish the retention policy before enabling deletion

**Files:**
- Create: `docs/policies/account-data-retention.md`
- Inspect: `scripts/backup-db.sh`, `docs/postgresql_audit_20260722.md`, `src/catalog/models/*.py`

**Interfaces:**
- Consumes: legal/privacy sign-off, infrastructure backup inventory and the relationship inventory in the models.
- Produces: a versioned policy document whose `policy_version` is stored in every deletion request and displayed in the user confirmation screen.

- [ ] **Step 1: Obtain written approval for every blank duration and exception in the policy table.**

  The approver must set a concrete grace period, completion timing, audit period, review disposition, ownership-content disposition, legal-hold authority and every backup destination's maximum expiry. Do not activate the deletion feature based on the proposed 30-day grace period alone.

- [ ] **Step 2: Create the policy document with immutable operational fields.**

  Include this exact structure, replacing bracketed values only with the approved values:

  ```markdown
  # KidsMap Account Data Retention Policy

  **Policy version:** `ADRP-YYYY-NN`
  **Effective date:** `YYYY-MM-DD`
  **Approved by:** `<role and decision record>`
  **Grace period:** `<N calendar days>`
  **Processor cadence:** `<daily UTC time>`

  | Data category | Disposition | Retention | Legal basis / owner |
  | --- | --- | --- | --- |
  | Account identifiers and profile | delete | `<duration>` | `<approved basis>` |
  | Published place/site/specialist reviews | `<delete or anonymize>` | `<duration>` | `<approved basis>` |
  | Moderation and ownership history | `<redact/anonymize>` | `<duration>` | `<approved basis>` |
  | Security/deletion audit | retain pseudonymously | `<duration>` | `<approved basis>` |
  | Product analytics | remove account link / aggregate only | `<duration>` | `<approved basis>` |
  | Backups | expire, never mutate in place | `<maximum expiry>` | `<backup owner>` |
  ```

- [ ] **Step 3: Define the user-facing promise from the approved policy.**

  Write the exact AZ/RU/EN copy for: data deleted, data anonymized, data retained under a legal hold, cancellation deadline, final deletion date, public-review disposition, owner-content disposition and backup expiry. The UI must render those facts from the policy version, not hard-code a different deadline.

- [ ] **Step 4: Record an activation gate.**

  The service must reject `confirm_deletion()` if no active approved policy record/version is configured. It must return an operator-safe error such as `retention_policy_not_active`, never silently choose a default duration.

### Task 2: Add lifecycle records and remove unsafe cascade assumptions

**Files:**
- Modify: `src/catalog/models/user.py`
- Modify: `src/catalog/models/review.py`, `src/catalog/models/owner.py`, `src/catalog/models/place.py`, `src/catalog/models/specialist.py`, `src/catalog/models/site.py`
- Create: `src/catalog/migrations/0105_account_deletion_retention.py`
- Test: `src/catalog/testcases/test_account_deletion.py`

**Interfaces:**
- Consumes: Django `User`, profile/email-verification records and existing user foreign keys.
- Produces: `AccountDeletionRequest` lifecycle records and user relationships that can be deleted, cleared, retained or anonymized by the processor in a controlled order.

- [ ] **Step 1: Write failing lifecycle and cascade-safety tests.**

  Cover these minimum cases:

  ```python
  def test_confirmed_request_disables_user_without_deleting_related_rows(self): ...
  def test_finalization_anonymizes_published_review_instead_of_cascading_it(self): ...
  def test_finalization_deletes_favorite_reaction_and_profile_pii(self): ...
  def test_finalization_preserves_pseudonymous_deletion_audit_after_user_is_deleted(self): ...
  def test_finalization_unlinks_public_place_and_event_owner_without_deleting_public_content(self): ...
  ```

  Assert `PlaceReview.user_id is None` and `PlaceReview.author_name == ""` after completion when the approved policy says to anonymize. Assert the request/audit stores a random subject reference and does not contain the original username, email, phone or full name.

- [ ] **Step 2: Add `AccountDeletionRequest`.**

  Add a model with a nullable `user` FK (`SET_NULL`), `subject_reference=UUIDField(unique=True)`, lifecycle states `REQUESTED`, `CONFIRMATION_SENT`, `SCHEDULED`, `CANCELED`, `HELD`, `PROCESSING`, `COMPLETED`, `FAILED`, timestamps for request/confirm/cancel/process/complete, `scheduled_for`, `policy_version`, hashed confirmation code, confirmation expiry, remaining attempts, and a non-sensitive `hold_code` / `failure_code`.

  Add partial uniqueness so only one request in `REQUESTED`, `CONFIRMATION_SENT`, `SCHEDULED`, `HELD` or `PROCESSING` exists per user. Index `status, scheduled_for`; validate every transition in a service, not in templates or the management command.

- [ ] **Step 3: Add `AccountDeletionAudit`.**

  Store `subject_reference`, `event_type`, `policy_version`, timestamp and a small JSON `counters` object of category counts. Add a database/model validation that rejects identifier keys such as `email`, `phone`, `name`, `username`, `address`, `text`, `old_value` and `new_value` in `counters`.

- [ ] **Step 4: Migrate content relationships to deliberate anonymization.**

  Change only the user relations that the approved policy needs to preserve into nullable `SET_NULL` relations. At a minimum review `PlaceReview`, `SiteReview`, `SpecialistReview`, ownership-request applicant/history, team owner/member records, invitations and analytics links. Keep reactions, likes, review cooldowns, profile and email verification eligible for physical deletion.

  For each relation, add a migration and a test showing the exact post-finalization state. Do not make every relationship `SET_NULL` by default: direct personal records must be deleted, while integrity-preserving public/moderation records must be redacted explicitly.

- [ ] **Step 5: Run the new model tests.**

  Run:

  ```powershell
  $env:DJANGO_TESTING='1'; .\.venv\Scripts\python.exe manage.py test catalog.testcases.test_account_deletion --noinput
  ```

  Expected: initially fail before the models/migration; pass after the implementation. Also run `makemigrations --check --dry-run` after migration creation; expected: `No changes detected`.

### Task 3: Implement the secure request, confirmation, cancellation and finalization service

**Files:**
- Create: `src/catalog/services/account_deletion.py`
- Modify: `src/catalog/controllers/auth_controller.py`
- Test: `src/catalog/testcases/test_account_deletion.py`

**Interfaces:**
- Consumes: `user`, active policy version, current time and one-time confirmation code.
- Produces: `request_account_deletion(user)`, `confirm_account_deletion(user, code, typed_confirmation)`, `cancel_account_deletion(subject_reference, code)`, and `finalize_account_deletion(request_id, now)`.

- [ ] **Step 1: Write failing workflow and security tests.**

  Include:

  ```python
  def test_request_requires_active_retention_policy(self): ...
  def test_confirmation_requires_exact_typed_phrase_and_valid_email_code(self): ...
  def test_invalid_code_is_rate_limited_and_expired_code_is_rejected(self): ...
  def test_confirmation_sets_is_active_false_sets_unusable_password_and_logs_out_current_session(self): ...
  def test_cancel_before_scheduled_for_restores_access_and_invalidates_code(self): ...
  def test_cancel_after_grace_period_is_rejected(self): ...
  def test_finalization_is_idempotent_when_retried_after_partial_failure(self): ...
  def test_legal_hold_defers_finalization_without_restoring_login(self): ...
  ```

- [ ] **Step 2: Implement request creation under a transaction and row lock.**

  Lock the user row and active deletion request. Reject staff/superuser accounts from self-service deletion with a neutral support route; they require the separate authorized staff-offboarding procedure so the last-superadmin protection is never bypassed. Generate a fresh `subject_reference`, create `CONFIRMATION_SENT`, hash a random one-time code, send it to the verified account email and write a pseudonymous `confirmation_sent` audit event.

- [ ] **Step 3: Implement double confirmation and immediate access freeze.**

  `confirm_account_deletion` must validate the exact localized typed confirmation phrase and hashed code within expiry/attempt limit. In one transaction it sets `scheduled_for = now + policy.grace_period`, changes status to `SCHEDULED`, sets `user.is_active = False`, calls `user.set_unusable_password()`, saves the user, deletes direct password-reset/email-verification challenges that must not survive, calls `logout(request)` for the current session, and writes `deletion_scheduled` audit data.

- [ ] **Step 4: Implement cancellation through an independent confirmation.**

  Cancellation must use a fresh one-time code delivered to the pre-deletion verified email and may only occur before `scheduled_for` and while no legal hold applies. It restores `is_active=True` but does not restore an unusable password; require the user to set a new password via the established recovery flow. Mark the request `CANCELED`, destroy the code and write a pseudonymous `deletion_canceled` audit event.

- [ ] **Step 5: Implement finalization as ordered, idempotent dispositions.**

  Lock the request and user; skip non-due, canceled, completed or held records. Mark `PROCESSING`, execute each disposition in a transaction-safe, retryable order, record only counters, and mark `COMPLETED` only after every category finishes:

  1. delete avatar storage object and `UserProfile`, verification data, likes, reactions, cooldowns and direct sessions/tokens;
  2. delete or unlink user-linked analytics under the approved policy;
  3. anonymize retained reviews and moderation records, clearing author names, applicant/owner identity, invitation emails and free-text PII where the approved policy requires it;
  4. revoke team memberships/invitations and unlink public Place/Event/Specialist ownership under the approved owner-content rule;
  5. clear user references from audit/history models that legitimately retain event metadata;
  6. set `request.user = None`, preserve only its UUID subject reference, then delete the Django user.

  A processor exception records only a stable `failure_code`, leaves the request retryable and must never print user records, emails or payloads to logs.

- [ ] **Step 6: Run the workflow tests.**

  Run the command from Task 2, Step 5. Expected: PASS.

### Task 4: Add the profile UX and self-service endpoints

**Files:**
- Modify: `src/catalog/forms.py`, `src/catalog/controllers/auth_controller.py`, `src/catalog/views.py`, `src/catalog/urls.py`
- Modify: `src/catalog/templates/pages/account_profile.html`, `static/css/pages/account_profile.css`
- Test: `src/catalog/testcases/auth_flow.py`, `src/catalog/testcases/test_account_deletion.py`

**Interfaces:**
- Consumes: account-settings route, active retention policy and account-deletion service results.
- Produces: a settings danger zone, confirmation page, cancellation page and status view for the request owner only.

- [ ] **Step 1: Write failing route and access tests.**

  Test anonymous redirect, CSRF rejection, GET non-mutation, user A cannot see/cancel user B's request, request page shows approved policy facts, invalid typed confirmation/code remains on the page with field errors, and confirmed request redirects to a signed-out status page.

- [ ] **Step 2: Add narrow forms and routes.**

  Add routes named `account_deletion_request`, `account_deletion_confirm`, `account_deletion_cancel` and `account_deletion_status`. Use forms with `typed_confirmation`, `confirmation_code` and `form_action`; do not add a deletion branch to the generic profile-edit form. All state transitions remain in the service from Task 3.

- [ ] **Step 3: Add a settings danger zone with policy-derived disclosure.**

  On `/account/settings/`, render a native `<section>` titled “Удалить аккаунт” with a destructive button leading to the confirmation page. The confirmation page must explicitly list deleted classes, anonymized classes, legal-hold possibility, grace/cancellation date, final processing date, public-review/owner-content outcome, backup expiry statement and irreversibility. Render data from the active policy object/version.

- [ ] **Step 4: Keep controls accessible and non-accidental.**

  Use real `<button>` / `<form>` controls, a visible associated label for the typed confirmation/code fields, field-level errors with `aria-describedby`, `aria-invalid` when invalid, and an `aria-live` status region for code-send errors. Do not use a single-click modal or JavaScript-only confirmation.

- [ ] **Step 5: Render state-specific status and cancellation.**

  `SCHEDULED` shows access disabled, exact cancellation deadline and a cancellation action. `HELD` explains only that processing is delayed under the approved retention policy; it must not disclose legal-case data. `COMPLETED` is reachable only through a short-lived signed status link and contains no identifiers. `CANCELED` confirms how to regain access through password recovery.

- [ ] **Step 6: Run focused web tests.**

  Run:

  ```powershell
  $env:DJANGO_TESTING='1'; .\.venv\Scripts\python.exe manage.py test catalog.testcases.auth_flow.TestAccountProfileUpdates catalog.testcases.test_account_deletion --noinput
  ```

  Expected: PASS.

### Task 5: Implement and operate the retention processor safely

**Files:**
- Create: `src/catalog/management/commands/process_account_deletions.py`
- Modify: `src/catalog/testcases/test_account_deletion.py`
- Modify after infrastructure approval only: scheduler/runbook document

**Interfaces:**
- Consumes: due `AccountDeletionRequest` records and `finalize_account_deletion()`.
- Produces: idempotent aggregate results for scheduler monitoring; no per-user personal data in stdout/stderr.

- [ ] **Step 1: Write failing command tests.**

  Cover `--dry-run` does not mutate, due scheduled requests complete, future/canceled/held requests are skipped, one failed record does not stop another, a second command run is a no-op for completed requests, and command output contains aggregate counts only.

- [ ] **Step 2: Implement the command interface.**

  Provide:

  ```text
  manage.py process_account_deletions --dry-run --limit 100
  manage.py process_account_deletions --limit 100
  ```

  Select due rows ordered by `scheduled_for, id`; use `select_for_update(skip_locked=True)` where supported; call the service once per row; print one aggregate line such as `processed=4 completed=3 held=0 failed=1 skipped=12`. Do not accept an `--all` or `--ignore-grace-period` option.

- [ ] **Step 3: Define scheduler ownership after review.**

  Add the approved daily invocation, timeout, non-zero exit alert and backup-expiry monitoring to the infrastructure runbook. The application processor must remain safe if the scheduler is late: it processes any overdue request once, and never accelerates a request before `scheduled_for`.

- [ ] **Step 4: Run command and regression tests.**

  Run:

  ```powershell
  $env:DJANGO_TESTING='1'; .\.venv\Scripts\python.exe manage.py test catalog.testcases.test_account_deletion catalog.testcases.auth_flow --noinput
  ```

  Expected: PASS. Also run `python scripts/tests/test_backup_db.py`; expected: PASS, confirming the existing backup retention behavior is unchanged by application code.

## Self-review

- The plan includes the user-visible delete button, repeated confirmation, disabled/pending state, cancellation grace period, final processing, audit trail and outcome status.
- It explicitly handles favorites, reactions, reviews, analytics, ownership requests, team invitations, public places/events/specialists, moderation history, profile fields, avatar files, email verification, sessions and backups.
- It prevents the current `CASCADE` relationships from choosing the data disposition by accident and distinguishes deletion from anonymization.
- It states the absence of an Organization model and prevents unsupported promises about it.
- It treats exact legal periods as an approval gate, supported by official Azerbaijani personal-data requirements rather than inventing legal advice.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-13-account-deletion-and-retention.md`. Implementation requires approval under the repository rule in `AGENTS.md`: “Future implementation requires a concrete plan and user approval for its scope.”
