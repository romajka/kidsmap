# Moderation SLA and Deadline Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Place and Review submitters a truthful moderation deadline and give staff one sortable, filterable queue showing healthy, warning, critical and breached cases.

**Architecture:** Add a versioned SLA policy and a durable `ModerationCase` for each moderation attempt instead of treating mutable `created_at` or `updated_at` fields as clocks. Route submissions and decisions through one workflow service that snapshots the approved policy, records transitions and keeps existing domain statuses authoritative. A resolver registry projects Place, volunteer-revision and Review models into one admin queue without copying their content.

**Tech Stack:** Django models and migrations, PostgreSQL-compatible constraints/indexes, Django services/controllers/admin, server-rendered templates, existing KidsMap CSS tokens, Django `TestCase`, Playwright browser verification.

**Spec:** `docs/product/moderation-sla-spec.md`

## Global Constraints

- Do not hardcode production SLA durations, warning/critical percentages, backlog thresholds or public rejection reasons.
- The planned clock implementation is calendar time. If product approval chooses business time, extend this plan with working-week, holiday and timezone rules before implementation.
- SLA measures time to a moderation decision, never time to guaranteed publication.
- Domain models remain the source of content/publication status; `ModerationCase` owns only SLA timing, assignment and outcome history.
- First release content: owner/admin Place submissions, `VolunteerPlaceRevision`, `PlaceReview`, `SiteReview` and `SpecialistReview`.
- Future Event, Specialist profile and Organization-change SLAs require separately approved policies.
- New UI supports AZ/RU/EN and conveys state with text plus color/icon.
- Tests run only with `DJANGO_TESTING=1` and isolated database/cache/media.
- Production remains read-only during this plan; do not deploy, migrate production, configure policies, commit or push.

---

### Task 1: Add versioned SLA policies and durable moderation cases

**Files:**

- Create: `src/catalog/models/moderation.py`
- Modify: `src/catalog/models/__init__.py`
- Create: `src/catalog/migrations/0105_moderation_sla.py` (use the next free migration number if another approved plan lands first)
- Create: `src/catalog/testcases/test_moderation_sla_models.py`

**Interfaces:**

- Produces: `ModerationSlaPolicy`, `ModerationDecisionReason`, `ModerationCase`, `ModerationCaseTransition`.
- Produces: `ModerationPolicyScope.PLACE`, `ModerationPolicyScope.REVIEW`.
- Produces: concrete `ModerationContentKind` values for Place, volunteer Place revision and the three Review models.
- Consumes: `settings.AUTH_USER_MODEL` and existing domain object IDs.

- [ ] **Step 1: Write failing policy validation tests**

```python
def test_active_policy_requires_complete_ordered_thresholds(self):
    policy = ModerationSlaPolicy(
        scope=ModerationPolicyScope.PLACE,
        version=1,
        target_minutes=None,
        warning_percent=80,
        critical_percent=60,
        clock_mode=ModerationClockMode.CALENDAR,
        is_active=True,
    )
    with self.assertRaises(ValidationError):
        policy.full_clean()
```

Cover positive target duration, `0 < warning < critical < 100`, one active policy per scope, supported clock mode, explicit waiting-user behavior and optional ordered backlog thresholds.

- [ ] **Step 2: Run the model test and confirm the missing model failure**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test catalog.testcases.test_moderation_sla_models --noinput
```

Expected: FAIL because the moderation SLA models do not exist.

- [ ] **Step 3: Implement the policy and reason models**

```python
class ModerationSlaPolicy(models.Model):
    scope = models.CharField(max_length=32, choices=ModerationPolicyScope.choices)
    version = models.PositiveIntegerField()
    target_minutes = models.PositiveIntegerField(null=True, blank=True)
    warning_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    critical_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    clock_mode = models.CharField(max_length=24, choices=ModerationClockMode.choices)
    waiting_user_behavior = models.CharField(max_length=24, choices=WaitingUserBehavior.choices)
    backlog_warning_count = models.PositiveIntegerField(null=True, blank=True)
    backlog_critical_count = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

`ModerationDecisionReason` contains a stable code, policy scope, allowed outcome, internal label, public AZ/RU/EN copy and active flag. Activation requires complete public copy for reasons marked public.

- [ ] **Step 4: Implement case snapshots and constraints**

```python
class ModerationCase(models.Model):
    content_kind = models.CharField(max_length=40, choices=ModerationContentKind.choices)
    object_id = models.PositiveBigIntegerField()
    policy_scope = models.CharField(max_length=32, choices=ModerationPolicyScope.choices)
    policy_version = models.PositiveIntegerField(null=True, blank=True)
    target_minutes = models.PositiveIntegerField(null=True, blank=True)
    warning_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    critical_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    clock_mode = models.CharField(max_length=24, choices=ModerationClockMode.choices, blank=True)
    waiting_user_behavior = models.CharField(max_length=24, choices=WaitingUserBehavior.choices, blank=True)
    submitted_at = models.DateTimeField()
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    paused_seconds = models.PositiveBigIntegerField(default=0)
    closed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    outcome = models.CharField(max_length=24, choices=ModerationOutcome.choices, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    submission_source = models.CharField(max_length=24, choices=ModerationSubmissionSource.choices)
    submitted_at_source = models.CharField(max_length=24, choices=SubmittedAtSource.choices)
```

Add a conditional unique constraint allowing only one unclosed case for `(content_kind, object_id)` and indexes for open deadline ordering, content kind, assignee and submitted time.

- [ ] **Step 5: Add immutable transition rows**

`ModerationCaseTransition` stores case, transition type, actor, timestamp, structured reason and bounded internal note. Reject mutation through model/admin permissions after creation.

- [ ] **Step 6: Generate and validate the migration in the isolated test environment**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test catalog.testcases.test_moderation_sla_models --noinput
```

Expected: no model validation failures and all new tests pass.

### Task 2: Implement one SLA clock and transition service

**Files:**

- Create: `src/catalog/services/moderation_sla.py`
- Create: `src/catalog/services/moderation_subjects.py`
- Create: `src/catalog/testcases/test_moderation_sla_service.py`

**Interfaces:**

- Consumes: models from Task 1.
- Produces: `open_moderation_case(*, content_kind: str, object_id: int, submitted_by, source: str, now=None) -> ModerationCase`.
- Produces: `resolve_moderation_case(*, content_kind: str, object_id: int, outcome: str, actor, reason_code: str = '', internal_note: str = '', now=None) -> ModerationCase`.
- Produces: `request_changes(*, content_kind: str, object_id: int, actor, reason_code: str, internal_note: str = '', now=None) -> ModerationCase`.
- Produces: `resubmit_moderation_case(*, content_kind: str, object_id: int, submitted_by, source: str, now=None) -> ModerationCase`.
- Produces: `calculate_sla_state(case: ModerationCase, *, now=None) -> ModerationSlaState`.
- Produces: `ModerationSubjectResolver` registry for titles, workflow status, URLs and permission-safe previews.

- [ ] **Step 1: Write failing clock-boundary tests**

```python
def test_state_changes_at_configured_boundaries(self):
    case = self.case(target_minutes=100, warning_percent=60, critical_percent=85)
    self.assertEqual(calculate_sla_state(case, now=case.submitted_at + timedelta(minutes=59)).code, 'healthy')
    self.assertEqual(calculate_sla_state(case, now=case.submitted_at + timedelta(minutes=60)).code, 'warning')
    self.assertEqual(calculate_sla_state(case, now=case.submitted_at + timedelta(minutes=85)).code, 'critical')
    self.assertEqual(calculate_sla_state(case, now=case.submitted_at + timedelta(minutes=100)).code, 'breached')
```

The numbers are test fixtures only. Add timezone-aware exact-boundary, unconfigured, resolved and waiting-user cases.

- [ ] **Step 2: Write failing idempotency and policy-snapshot tests**

Verify that a second open call returns the same active case, a policy edit does not move its deadline, and concurrent opens cannot create two active cases.

- [ ] **Step 3: Implement policy snapshot and calendar clock calculation**

```python
@dataclass(frozen=True, slots=True)
class ModerationSlaState:
    code: str
    submitted_at: datetime
    due_at: datetime | None
    elapsed: timedelta
    remaining: timedelta | None
    elapsed_percent: int | None
```

Calculate against `timezone.now()` by default. `breached` means unresolved, unpaused and `now >= due_at`. An absent approved policy returns `unconfigured` with no fabricated deadline.

- [ ] **Step 4: Implement waiting-user behavior**

For `PAUSE_RESUME`, record pause time and extend the due time by the exact pause duration on resubmission. For `CLOSE_RESTART`, close with `needs_changes` and open a new attempt on resubmission. Each transition is atomic and audited.

- [ ] **Step 5: Implement known-subject resolvers**

Register resolvers for `Place`, `VolunteerPlaceRevision`, `PlaceReview`, `SiteReview` and `SpecialistReview`. A resolver returns a safe title/preview, current workflow status, admin change URL and policy scope. Unknown kinds fail closed and are reported by quality checks.

- [ ] **Step 6: Run service tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test catalog.testcases.test_moderation_sla_service --noinput
```

Expected: all boundary, concurrency, pause/resume, close/restart and resolver tests pass.

### Task 3: Open cases from every Place and Review submission path

**Files:**

- Modify: `src/catalog/controllers/owner_places_controller.py:1042-1106`
- Modify: `src/catalog/domain_admin/place.py:4525-4543`
- Modify: `src/catalog/domain_admin/volunteer.py:76-100`
- Modify: `src/catalog/services/review_use_cases.py:90-187`
- Modify: `src/catalog/services/place_review_submission.py:41-59`
- Modify: `src/catalog/views.py:441-517, 2206-2281`
- Modify: `src/catalog/controllers/engagement_controller.py`
- Test: `src/catalog/testcases/test_moderation_sla_submissions.py`
- Test: `src/catalog/testcases/test_review_confirmation.py`
- Test: `src/catalog/testcases/owner.py`
- Test: `src/catalog/testcases/test_volunteer_dashboard.py`

**Interfaces:**

- Consumes: `open_moderation_case()` and `resubmit_moderation_case()` from Task 2.
- Produces: `ReviewSubmissionResult.moderation_case` and `OwnerPlaceActionResult.moderation_case`.

- [ ] **Step 1: Write a failing matrix test for all submission routes**

```python
SUBMISSION_CASES = (
    ('owner_place', ModerationContentKind.PLACE, ModerationPolicyScope.PLACE),
    ('admin_place', ModerationContentKind.PLACE, ModerationPolicyScope.PLACE),
    ('volunteer_revision', ModerationContentKind.VOLUNTEER_PLACE_REVISION, ModerationPolicyScope.PLACE),
    ('place_review', ModerationContentKind.PLACE_REVIEW, ModerationPolicyScope.REVIEW),
    ('site_review', ModerationContentKind.SITE_REVIEW, ModerationPolicyScope.REVIEW),
    ('specialist_review', ModerationContentKind.SPECIALIST_REVIEW, ModerationPolicyScope.REVIEW),
)
```

For each route, assert one active case, exact source, actual submitter, submission timestamp and policy snapshot. A validation failure or saved draft creates no case.

- [ ] **Step 2: Verify duplicate and rollback behavior fails before implementation**

Submit twice while pending and assert only one active case. Force a domain save failure and assert no case/transition survives the transaction.

- [ ] **Step 3: Integrate owner and admin Place submissions**

Call `open_moderation_case()` in the same transaction that changes `Place.status` to pending. Do not use `Place.updated_at` as the clock. Existing `PlaceOwnershipRequest` remains part of ownership workflow, not the SLA source of truth.

- [ ] **Step 4: Integrate volunteer revisions**

Open a Place-scope case when `VolunteerPlaceRevision.status` becomes pending. Draft save and restart do not start the SLA.

- [ ] **Step 5: Integrate all Review submissions**

Refactor specialist review submission into the existing Review use-case boundary, then open/resubmit cases for Place, Site and Specialist reviews. `ReviewSubmissionResult` carries the case so HTTP responses do not query a second source.

- [ ] **Step 6: Run focused submission tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test `
  catalog.testcases.test_moderation_sla_submissions `
  catalog.testcases.test_review_confirmation `
  catalog.testcases.owner.TestOwnerPlaceManagementAndPermissions.test_owner_manager_can_create_place_and_send_for_moderation `
  catalog.testcases.test_volunteer_dashboard --noinput
```

Expected: all new submission tests pass. Preserve any independently reproduced localization failure in `test_review_confirmation` as a separately reported baseline issue; do not weaken its assertions to obtain green.

### Task 4: Close, pause or restart cases from every moderation decision path

**Files:**

- Create: `src/catalog/services/moderation_workflow.py`
- Modify: `src/catalog/domain_admin/place.py:4461-4578`
- Modify: `src/catalog/domain_admin/review.py:565-679, 707-718`
- Modify: `src/catalog/domain_admin/specialist.py:889-962`
- Modify: `src/catalog/domain_admin/volunteer.py:128-147`
- Modify: `src/catalog/controllers/owner_reviews_controller.py:77-93`
- Modify: `src/catalog/models/owner.py:96-135`
- Test: `src/catalog/testcases/test_moderation_sla_decisions.py`
- Test: `src/catalog/testcases/admin.py`
- Test: `src/catalog/testcases/owner.py`

**Interfaces:**

- Consumes: case transition functions from Task 2.
- Produces: `ModerationDecisionResult(case: ModerationCase, changed: bool, public_status: str)`.
- Produces: `moderate_place(*, place: Place, decision: str, actor, reason_code: str = '', internal_note: str = '') -> ModerationDecisionResult`.
- Produces: `moderate_review(*, review, decision: str, actor, reason_code: str = '', internal_note: str = '') -> ModerationDecisionResult`.
- Produces: `moderate_volunteer_revision(*, revision: VolunteerPlaceRevision, decision: str, actor, reason_code: str = '', internal_note: str = '') -> ModerationDecisionResult`.

- [ ] **Step 1: Write failing decision-path tests**

Test single-row and bulk admin approval/rejection, owner-authorized PlaceReview moderation, Place ownership approval that publishes a submitted Place, volunteer revision approve/reject and “return for revision”. Assert the domain state and case outcome always agree.

- [ ] **Step 2: Require structured reasons where users receive feedback**

```python
with self.assertRaisesMessage(ValidationError, 'public_reason_required'):
    moderate_place(place=place, decision='needs_changes', actor=moderator, reason_code='')
```

Reject or needs-changes actions require an active reason allowed for the policy scope/outcome. Store free moderator notes only in the transition audit record.

- [ ] **Step 3: Implement atomic workflow functions**

Use `transaction.atomic()` and `select_for_update()` for the content and active case. Approval/rejection closes the case; requested changes follows the case’s snapshotted waiting-user rule. A repeated decision returns an idempotent result and cannot rewrite the original SLA outcome timestamp.

- [ ] **Step 4: Replace direct queryset status updates**

Change bulk actions to iterate in bounded chunks through the workflow service. Preserve rating-stat refresh and Place quality validation. Report processed, skipped and failed counts without leaving open cases for resolved content.

- [ ] **Step 5: Replace immediate reject/return bulk actions with confirmation forms**

The confirmation form selects one structured reason and accepts a separate internal note. It never exposes internal notes as `Place.rejection_reason` or Review public copy.

- [ ] **Step 6: Run decision and regression tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test `
  catalog.testcases.test_moderation_sla_decisions `
  catalog.testcases.admin.TestAdminBulkActions `
  catalog.testcases.admin.TestReviewRatingSyncAndAdminBulkActions `
  catalog.testcases.owner.TestOwnerPlaceManagementAndPermissions --noinput
```

Expected: decisions close/pause cases consistently and existing moderation permissions/quality checks still pass.

### Task 5: Build the unified staff SLA queue

**Files:**

- Modify: `src/catalog/proxy_apps/catalog_moderation/models.py`
- Modify: `src/catalog/proxy_apps/catalog_moderation/admin.py`
- Create: `src/catalog/domain_admin/moderation_sla.py`
- Create: `src/templates/admin/catalog/moderation/sla_queue.html`
- Create: `static/admin/css/pages/kidsmap_moderation_sla.css`
- Modify: `src/templates/admin/index.html:22-145`
- Modify: `src/catalog/templatetags/admin_dashboard_tags.py:24-78`
- Test: `src/catalog/testcases/test_moderation_sla_admin.py`
- Test: `src/catalog/testcases/admin.py`

**Interfaces:**

- Consumes: `calculate_sla_state()` and subject resolvers from Task 2.
- Produces: `ModerationSlaQueue` proxy admin and `build_moderation_queue_summary(*, user, now=None) -> ModerationQueueSummary`.

- [ ] **Step 1: Write failing queue permission and ordering tests**

Create mixed Place/Review cases with different deadlines. Assert the default open queue orders by `due_at`, then `submitted_at`, and hides kinds for which the staff user lacks source-model view permission.

- [ ] **Step 2: Write failing filter/sort tests**

Test content family, concrete kind, workflow status, submitted-date range, SLA state and assignee filters. Assert received time and elapsed age can be explicitly sorted oldest/newest.

- [ ] **Step 3: Implement an annotated queue queryset**

Fetch cases in one query plus bounded resolver batches by content kind. Avoid one query per row. Orphaned subjects are excluded from actions and flagged for the quality command.

- [ ] **Step 4: Render the operational table**

Columns: type/source, material, workflow status, received, elapsed, remaining/overdue, SLA state, assignee and action. Use existing admin tokens; healthy is green, warning yellow, critical red and breached stronger red. Each cell includes text, and the table remains usable without color.

- [ ] **Step 5: Add assignment actions**

Add “Assign to me” and “Release” actions guarded by source-model change permission. Record `assigned`, `reassigned` or `released` transitions.

- [ ] **Step 6: Connect dashboard cards to filtered unified queue URLs**

Show total open, Place, Review, warning, critical and breached counts. Backlog warning appears only when the active policy contains an approved threshold. Existing specialized moderation pages remain available.

- [ ] **Step 7: Run admin tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test `
  catalog.testcases.test_moderation_sla_admin `
  catalog.testcases.admin.TestAdminSidebarStructure `
  catalog.testcases.admin.TestKidsMapAdminDashboard --noinput
```

Expected: queue permissions, ordering, filters, assignment and dashboard counts pass.

### Task 6: Show truthful SLA status to Place and Review submitters

**Files:**

- Create: `src/catalog/services/moderation_presenters.py`
- Modify: `src/catalog/controllers/owner_places_controller.py:429-484`
- Modify: `src/catalog/controllers/account_controller.py:80-105`
- Modify: `src/catalog/controllers/owner_reviews_controller.py:45-75`
- Modify: `src/catalog/views.py:441-517, 1300-1310, 2206-2281`
- Create: `src/catalog/templates/includes/moderation_status.html`
- Modify: `src/catalog/templates/pages/owner_places.html:315-446`
- Modify: `src/catalog/templates/pages/account_dashboard.html:237-270`
- Modify: `src/catalog/templates/pages/owner_reviews.html`
- Modify: `src/catalog/templates/pages/owner_listing_type_select.html:280-288`
- Modify: `static/css/pages/account_profile.css`
- Modify: `static/js/review_submission.js`
- Test: `src/catalog/testcases/test_moderation_sla_user_ui.py`
- Test: `src/catalog/testcases/test_review_confirmation.py`
- Test: `src/catalog/testcases/owner.py`

**Interfaces:**

- Consumes: case/state from Tasks 2 and 3.
- Produces: `build_submitter_status(case, *, language: str, now=None) -> SubmitterModerationStatus`.

- [ ] **Step 1: Write failing localized presentation tests**

```python
def test_place_pending_copy_promises_a_decision_not_publication(self):
    status = build_submitter_status(self.case, language='ru', now=self.now)
    self.assertEqual(status.title, 'На модерации')
    self.assertIn(status.deadline_text, status.body)
    self.assertNotIn('будет опубликовано через', status.body.lower())
```

Cover AZ/RU/EN, long text wrapping, unconfigured policy, waiting user, breach, approval, rejection and needs changes.

- [ ] **Step 2: Add a presenter DTO and localized duration/deadline formatting**

```python
@dataclass(frozen=True, slots=True)
class SubmitterModerationStatus:
    code: str
    title: str
    body: str
    deadline_text: str
    public_reason: str
    rules_url: str
```

Use Django localization and the configured KidsMap timezone. Do not expose internal notes, moderator identity, queue priority or internal SLA colors.

- [ ] **Step 3: Update Place submission and dashboard UI**

After successful submission show “On moderation”, the configured maximum decision time/deadline and the publication caveat. On the owner card, keep the latest status visible across visits. Replace the hardcoded “within a few hours” marketing sentence with policy-driven copy or neutral text when unconfigured.

- [ ] **Step 4: Update Review confirmation and persistent status UI**

AJAX and redirect responses include the deadline plus links to review rules and privacy policy. Extend the user’s review context to cover Place, Site and Specialist reviews with safe target labels. An unconfigured case says that the review was accepted without inventing a duration.

- [ ] **Step 5: Show only approved public decision reasons**

Rejected/needs-changes content displays localized `ModerationDecisionReason` copy. A missing public reason falls back to a neutral result and rules link; raw internal notes never render.

- [ ] **Step 6: Run user-facing tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test `
  catalog.testcases.test_moderation_sla_user_ui `
  catalog.testcases.test_review_confirmation `
  catalog.testcases.owner.TestOwnerPlaceManagementAndPermissions.test_owner_dashboard_shows_clear_moderation_statuses_on_cards --noinput
```

Expected: truthful localized copy and persistent statuses pass. Keep the pre-existing AZ/EN confirmation mismatch visible until fixed by an approved implementation task.

### Task 7: Add backfill, consistency audit and internal alerts

**Files:**

- Create: `src/catalog/management/commands/backfill_moderation_cases.py`
- Create: `src/catalog/management/commands/audit_moderation_sla.py`
- Create: `src/catalog/testcases/test_moderation_sla_commands.py`
- Create: `docs/operations/moderation-sla.md`

**Interfaces:**

- Consumes: models/services from Tasks 1-4.
- Produces: dry-run-safe backfill and aggregate-only consistency audit commands.

- [ ] **Step 1: Write failing backfill-source tests**

For legacy pending data, verify source priority:

1. pending Place ownership request submission time when it is the matching submission;
2. volunteer revision `updated_at` for a pending volunteer revision;
3. Review `created_at`, except updated Site/Specialist records whose exact resubmission time is unavailable;
4. general `updated_at` only as an explicitly marked estimate.

- [ ] **Step 2: Implement dry-run backfill**

Default output contains aggregate counts by content kind and timestamp-source quality. `--apply` creates idempotent cases. Applying an active policy to old open cases requires a separate explicit flag and prints how many would immediately be breached.

- [ ] **Step 3: Write and implement consistency checks**

Detect pending content without a case, open cases for resolved/missing content, duplicate active cases, invalid deadlines, cases without an approved policy snapshot, and domain/case outcome disagreement. Output counts and object kinds only, never review text or user-level data.

- [ ] **Step 4: Document internal notification semantics**

Document that the first release uses admin dashboard counts only. Warning, critical, breached and backlog states are recalculated at request time; no email, worker or scheduled sender is introduced.

- [ ] **Step 5: Run command tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test catalog.testcases.test_moderation_sla_commands --noinput
```

Expected: dry run is non-mutating, apply is idempotent and audit output contains no content/identity values.

### Task 8: Verify the full workflow and rendered UI

**Files:**

- Modify: `docs/operations/moderation-sla.md`
- Test: all files introduced or named above.

**Interfaces:**

- Consumes: complete feature from Tasks 1-7.
- Produces: reproducible verification ledger and rollout checklist.

- [ ] **Step 1: Run the complete focused suite**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test `
  catalog.testcases.test_moderation_sla_models `
  catalog.testcases.test_moderation_sla_service `
  catalog.testcases.test_moderation_sla_submissions `
  catalog.testcases.test_moderation_sla_decisions `
  catalog.testcases.test_moderation_sla_admin `
  catalog.testcases.test_moderation_sla_user_ui `
  catalog.testcases.test_moderation_sla_commands --noinput
```

- [ ] **Step 2: Run affected regressions**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test `
  catalog.testcases.owner `
  catalog.testcases.admin `
  catalog.testcases.test_review_confirmation `
  catalog.testcases.test_volunteer_dashboard `
  catalog.testcases.auth_access `
  catalog.testcases.specialists --noinput
```

Do not change assertions solely to make the suite green. Record the existing AZ/EN review-confirmation failure separately if it remains reproducible.

- [ ] **Step 3: Check migrations and Django configuration**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py check
```

Expected: no migration drift and no system-check errors.

- [ ] **Step 4: Verify browser behavior with isolated test data**

Use Playwright against a local `DJANGO_TESTING=1` server. Check user notices, owner cards and the admin queue at 375, 768, 1024 and 1440 CSS pixels. Verify keyboard filters/actions, visible focus, no horizontal overflow, text-plus-color states, AZ/RU/EN copy and zero console errors.

- [ ] **Step 5: Verify time transitions deterministically**

Use frozen server times in tests for healthy → warning → critical → breached, pause/resume and resolution. Do not rely on real sleeps or client clocks.

- [ ] **Step 6: Record rollout gates**

The implementation report must identify approved Place/Review durations, clock start, waiting-user behavior, thresholds, calendar mode, reason catalogue, policy version, backfill dry-run counts and the exact first activation timestamp. Keep all production actions pending separate authorization.

## Rollout sequence

1. Product owner approves all eight policy decisions in the spec.
2. Deploy schema/code with policies inactive and run isolated verification.
3. Run production backfill and consistency commands in read-only dry-run mode after separate authorization.
4. Create and approve policy versions and structured public reasons.
5. Apply reviewed backfill, then activate policies.
6. Enable user deadline copy and the unified staff queue together so external promises have internal visibility.
7. Observe breached/backlog counts before considering email or other external notifications.

## Acceptance criteria

- Every successful supported submission opens exactly one case at the real transition into moderation.
- Draft saves and failed submissions do not start SLA time.
- Place and Review policies can have different approved durations and thresholds.
- Existing cases retain their original deadline when policies change.
- Staff see one permission-safe queue ordered by deadline/submission age with required filters and assignment.
- Healthy, warning, critical, breached, waiting-user and unconfigured states are textually distinguishable without relying on color.
- Decisions and requested changes atomically update domain state and SLA history.
- Users see a maximum decision time and publication caveat; they never receive a publication guarantee.
- Volunteer revisions and all three existing Review models cannot bypass the SLA pipeline.
- Internal notes and moderator identities never appear in user-facing output.
- No production duration, threshold or reason is invented by application code.

Plan complete and saved to `docs/superpowers/plans/2026-09-13-moderation-sla-and-deadline-control.md`. Implementation requires approval under the repository rule in `AGENTS.md`: “Future implementation requires a concrete plan and user approval for its scope.”
