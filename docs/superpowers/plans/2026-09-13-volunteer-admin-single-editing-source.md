# Volunteer/Admin Shared Editing Source Implementation Plan

> **For agentic workers:** Implement task-by-task with a failing regression test before each production change. Do not commit, push, deploy, migrate production data, or contact production under the current audit contract.

**Goal:** A volunteer draft and the corresponding admin screen always show and edit the same working data, calculate the same twelve-item readiness, and retain an auditable, conflict-safe moderation workflow.

**Architecture:** `VolunteerPlaceRevision` remains the explicit, private working version while it is in `draft`, `pending`, or `rejected`; `Place` remains the approved public projection. The admin change URL must load the active revision's candidate rather than silently loading the older `Place` row. Both volunteer and admin writes pass through one revision-save service, use the same optimistic version check, and record field-level audit entries. On approval, the existing projection step writes the checked working version to `Place`.

**Tech Stack:** Django 6, Django admin, PostgreSQL/SQLite test runner, Django `ModelForm`, `VolunteerPlaceRevision`, `PlaceChangeAudit`.

**Spec:** User report dated 2026-09-13: volunteer → draft save → database → admin → public `Place`, shared readiness, conflict protection and audit trail.

## Global Constraints

- The twelve readiness requirements remain defined only in `catalog.services.place_readiness`; no duplicate browser or form-specific calculation.
- A proposal is explicitly labelled as a private working version; public views continue reading the approved `Place` projection until an administrator approves it.
- All volunteer-editable `Place` fields, pricing plans and structured schedule use one mapping. `region` is a form-only projection of `Place.district`, through `clean_location_fields`; it is not an additional database column.
- Existing version and base-token checks must reject stale volunteer or admin submissions without overwriting a newer revision.
- Tests run with `DJANGO_TESTING=1`, a disposable test database, LocMem cache and temporary test media.

---

### Task 1: Lock in the reported failure and the target contract

**Files:**

- Modify: `src/catalog/testcases/test_volunteer_admin.py`
- Modify: `src/catalog/testcases/test_volunteer_dashboard.py`
- Modify: `src/catalog/testcases/place_readiness.py`

**Interfaces:**

- Consumes: `VolunteerPlaceRevision.payload`, `editor_data`, `display_card`, the standard `admin:catalog_place_change` URL.
- Produces: regression coverage for a shared proposal candidate, a shared readiness result, and optimistic conflict handling.

- [ ] **Step 1: Add a failing admin-read test for the full shared content set.**

  Create a volunteer revision containing a non-default value for every concrete member of `CONTENT_FIELDS`, normalized tariffs, structured schedule, primary and cover photo paths. Request the standard admin change URL as a superuser and assert its form displays the revision values for title, descriptions, category/subcategory, `age_from`, `age_to`, `age_open_ended`, adult classes, duration, location, contacts, coordinates, images, schedule and tariffs. Assert the location form derives `region` from the same `district` key.

- [ ] **Step 2: Run the new test and observe the current failure.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_admin_change_form_reads_active_volunteer_revision --noinput`

  Expected before implementation: FAIL because the standard admin form receives the stored `Place` object and its empty/old values.

- [ ] **Step 3: Add a failing readiness parity test.**

  Build a revision with nine satisfied readiness items, including `age_from=1` and `age_to=6`. Assert the volunteer dashboard card and the standard admin form report identical `completed_count`, `required_count`, issue codes and percentage. Use the canonical service result as the expected value rather than hard-coding `75`.

- [ ] **Step 4: Add failing write and concurrency tests.**

  Post an administrator correction to an active revision, then reopen it as the volunteer and assert the corrected values appear. Re-post the volunteer's earlier form payload and assert it is rejected, while the administrator's newer revision values remain unchanged. Verify the public page still renders the approved `Place` values before approval and renders the shared revision values after approval.

- [ ] **Step 5: Add a failing audit test.**

  Save a volunteer edit, then an admin correction of the active proposal. Assert `PlaceChangeAudit` contains the place, actor, timestamp, source, field name, old and new values for both changes, including a normalized tariff or schedule change.

### Task 2: Complete the shared editable field contract

**Files:**

- Modify: `src/catalog/volunteer_forms.py`
- Modify: `src/catalog/services/volunteer_places.py`
- Modify: `src/catalog/testcases/test_volunteer_admin.py`

**Interfaces:**

- Consumes: `CONTENT_FIELDS`, `Place` model fields, `init_location_fields`, `configure_location_choices`, `clean_location_fields`.
- Produces: `VolunteerPlaceForm` with every volunteer-editable concrete value plus its derived `region` control.

- [ ] **Step 1: Write a failing form test for the location bridge.**

  Instantiate the volunteer form for a Place whose persisted district is `baku_yasamal`. Assert `region == 'baku'` and `district == 'baku_yasamal'`. Submit a valid non-Baku region and assert the stored candidate's `district` becomes that region key. Submit `region='ganja'` with `district='baku_yasamal'` and assert the form rejects it.

- [ ] **Step 2: Run the location test and observe the missing form controls.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_location_uses_admin_region_district_contract --noinput`

  Expected before implementation: FAIL because `VolunteerPlaceForm` only exposes `district` and does not initialize the form-only `region` field.

- [ ] **Step 3: Add the virtual location controls to `VolunteerPlaceForm`.**

  Declare `region` as a non-model `ChoiceField`, initialize `region` and `district` with `init_location_fields`, configure both choice lists with `configure_location_choices`, and call `clean_location_fields` during `clean`. Keep `CONTENT_FIELDS` restricted to actual persisted `Place` fields; `content_snapshot` continues storing the canonical `district` key only.

- [ ] **Step 4: Make the field inventory executable.**

  Add a test that compares `CONTENT_FIELDS` with the concrete fields that the proposal service snapshots and projects, and separately asserts inclusion of `pricing_plans` and `structured_schedule`. This protects every field named in the spec from a silent divergence.

- [ ] **Step 5: Run the Task 2 tests.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_volunteer_admin --noinput`

  Expected after implementation: the new field-contract tests pass; unrelated existing failures, if any, are reported separately.

### Task 3: Centralize proposal reads, writes and audit records

**Files:**

- Modify: `src/catalog/services/volunteer_places.py`
- Modify: `src/catalog/models/owner.py`
- Create: `src/catalog/migrations/0103_placechangeaudit_volunteer_source.py`
- Modify: `src/catalog/testcases/test_volunteer_admin.py`

**Interfaces:**

- Consumes: `Place`, `VolunteerPlaceRevision`, `CONTENT_FIELDS`, normalized pricing plans, validated schedule days and `PlaceChangeAudit`.
- Produces: a single service that saves an active working revision for either actor and records the delta.

- [ ] **Step 1: Write failing service tests for revision persistence.**

  Exercise a new `save_working_revision(user, place_id, data, files, source)` entry point. Assert it locks `Place` then its revision, validates `revision_version` and `base_token`, increments `revision.version`, preserves the base snapshot, stores the complete normalized payload, and does not update `Place` or its public schedule/pricing records.

- [ ] **Step 2: Run the service tests and observe the absent shared entry point.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_working_revision_save_records_all_changed_fields --noinput`

  Expected before implementation: FAIL because only `save_proposal` exists and it records no draft field audit entries.

- [ ] **Step 3: Implement `save_working_revision` and route `save_proposal` through it.**

  Move the existing validation, storage-safe photo persistence, payload construction, revision/version update and pending/draft transition into the shared service. Accept an explicit audit source. Compute old and new working snapshots before save, then bulk-create one `PlaceChangeAudit` entry per changed content, tariff or structured-schedule value.

- [ ] **Step 4: Add an explicit volunteer audit source.**

  Add `SOURCE_VOLUNTEER = 'VOLUNTEER'` to `PlaceChangeAudit.SOURCE_CHOICES`, create the state migration, and use it for volunteer saves. Continue using `SOURCE_ADMIN` for administrator changes and approval projection. Do not serialize secrets or user records into audit values.

- [ ] **Step 5: Preserve current approval semantics.**

  Keep `review_proposal` as the sole path that projects a pending revision into `Place`, writes pricing/schedule relations and makes a card public. Its existing base-snapshot conflict test remains mandatory.

- [ ] **Step 6: Run service and approval regression tests.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_working_revision_save_records_all_changed_fields catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_superadmin_approval_publishes_valid_proposal_and_audits_changes catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_concurrent_admin_edit_requires_explicit_restart --noinput`

  Expected after implementation: PASS.

### Task 4: Make the primary admin route edit the active working version

**Files:**

- Modify: `src/catalog/domain_admin/place.py`
- Create: `src/catalog/templates/admin/catalog/place/volunteer_revision_change_form.html`
- Modify: `src/catalog/templates/admin/catalog/place/change_form.html`
- Modify: `src/catalog/testcases/test_volunteer_admin.py`

**Interfaces:**

- Consumes: `active VolunteerPlaceRevision`, `VolunteerPlaceForm`, `save_working_revision`, `evaluate_form_readiness`.
- Produces: a standard place-admin change URL that displays the proposal candidate and writes corrections to that same revision.

- [ ] **Step 1: Write the failing GET/POST route tests.**

  For a draft, pending and rejected revision, GET `admin:catalog_place_change` as a superuser. Assert the response identifies the working state and renders form values from `revision.payload`. POST an edit with the current revision version and assert `Place` stays unchanged, `revision.payload` contains the correction, `revision.version` increments and a volunteer GET sees it. Test that an outdated administrator POST is rejected.

- [ ] **Step 2: Run the route tests and observe the old `Place` form.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_admin_change_form_reads_active_volunteer_revision catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_admin_edit_updates_active_revision_without_public_projection --noinput`

  Expected before implementation: FAIL because `PlaceAdmin` builds `PlaceAdminForm(instance=Place)` and `save_model` writes the live projection.

- [ ] **Step 3: Add the dedicated active-revision admin change path.**

  In `PlaceAdmin`, detect a non-approved `volunteer_revision` before building the normal change form. Render `VolunteerPlaceForm` from `editor_form(place, revision)` in an admin-styled template, including `revision_version`, `base_token`, taxonomy, tariff editor, structured schedule editor and map/location controls. The template must label the screen as the volunteer working version and link to the approved public projection where one exists.

- [ ] **Step 4: Route admin corrections through the shared service.**

  Handle the active-revision POST before normal `ModelAdmin.save_model`. Call `save_working_revision` with `SOURCE_ADMIN`; return form errors for stale versions or changed live base snapshots. Do not call `super().save_model`, save inlines, publish, or alter `Place` on this path.

- [ ] **Step 5: Show one readiness result for the loaded candidate.**

  Build the summary and sidebar from `evaluate_form_readiness(form, form.instance)` for the active revision. Render the same completed count, total and missing codes that `display_card` computes. Retain the normal `PlaceAdminForm` path when no active revision exists.

- [ ] **Step 6: Run the complete admin/volunteer integration group.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_volunteer_admin catalog.testcases.test_volunteer_dashboard catalog.testcases.place_readiness --noinput`

  Expected after implementation: all tests related to this feature pass. Record any unrelated localization baseline separately.

### Task 5: Verify field parity, public projection and user-facing states

**Files:**

- Modify: `src/catalog/testcases/test_volunteer_admin.py`
- Modify: `src/catalog/testcases/test_volunteer_dashboard.py`
- Modify: `docs/LIVING_MAP_PUBLIC.md` only if it contains a conflicting statement about card data sources; otherwise do not edit it.

**Interfaces:**

- Consumes: volunteer route, standard admin route, review approval route and public place route.
- Produces: end-to-end evidence for all fields and workflow states.

- [ ] **Step 1: Add a parameterized field-parity test.**

  Cover: all localized title/description values; category/subcategory; age from/to/open ended; adult flag; duration and lesson metadata; pricing and tariffs; region/district/metro; address; three phones; website; Instagram; coordinates; photo/cover photo; schedule mode, notes and structured days; extra conditions and additional information. For each value, assert volunteer view equals the active admin revision view, then approve and assert the corresponding `Place` and public representation use the projected value where public output exposes it.

- [ ] **Step 2: Add workflow-state tests.**

  Verify draft save is visible in the main admin route; pending save remains visible but public content stays at the approved projection; rejection preserves the same editable revision; approval copies it to `Place`; admin correction is visible on the volunteer's next GET; and stale submissions fail without data loss.

- [ ] **Step 3: Run focused Django tests.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py test catalog.testcases.test_volunteer_admin catalog.testcases.test_volunteer_dashboard catalog.testcases.place_readiness --noinput`

- [ ] **Step 4: Run structural checks.**

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py check`

  Run: `$env:DJANGO_TESTING='1'; .\\.venv\\Scripts\\python.exe manage.py makemigrations --check --dry-run`

  Expected: both commands exit 0 after the state migration is present.

- [ ] **Step 5: Perform rendered-browser acceptance on isolated fixture data.**

  Check volunteer and admin active-revision forms at 390, 768, 1024, 1280 and 1440 pixels: field values, `X / 12`, draft save, admin correction, reload, stale-submission error, photo previews, tariff editor, schedule editor, keyboard focus and no horizontal overflow. Do not use production pages because analytics may write events.

## Plan self-review

- Every field named in the report is covered by Task 2 or Task 5; the only exception is `region`, which is derived from the persisted `district` field and is tested explicitly.
- The plan preserves the required public moderation boundary while removing the silent split between the normal admin form and volunteer working data.
- The plan includes the existing draft, pending, rejected, approved, stale-volunteer and stale-admin paths, and field-level audit records.
- No destructive data migration is planned. Existing revisions become visible to the standard admin route through the same payload already stored for them.
