# Volunteer Place Duplicate Prevention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent a volunteer from accidentally creating repeated draft cards for the same place, while preserving a deliberate way to add a distinct branch and a recoverable deletion path for duplicate drafts.

**Architecture:** `Place` remains the canonical card and `VolunteerPlaceRevision` remains its private working version. Before the first `Place` row is persisted, the volunteer flow will serialize creation for its author, detect an active same-name card created by that author, and either direct the user to resume it or require an explicit branch override backed by a distinct address or coordinate pair. The check is server-side; the browser only makes the decision understandable.

**Tech Stack:** Django 6, PostgreSQL, Django admin/Jazzmin, server-rendered templates, vanilla JavaScript, Django `TestCase`.

**Spec:** User request 2026-09-28: prevent duplicate places in the volunteer/admin workflow and allow safe removal of duplicates.

## Global Constraints

- Do not add a database-wide unique constraint on a name: branches may share a brand name.
- Apply the hard stop only to a new, non-deleted place created by the same volunteer with the same normalized AZ/RU/EN display name.
- A branch override is allowed only when its normalized address differs or its latitude/longitude pair differs from the existing card.
- Serialize same-volunteer creation by locking that user row in the transaction; client-side debounce is not a correctness mechanism.
- Never physically delete a card from this flow. Volunteer deletion soft-deletes only their own `draft` or `rejected` card; `pending` and published cards stay admin-only.
- Existing global duplicate suggestions in the main admin form remain advisory and are not repurposed as a uniqueness constraint.
- Preserve `PlaceChangeAudit`; a create, explicit branch override and soft deletion must be attributable without exposing data outside the normal admin views.
- Tests run with `DJANGO_TESTING=1`, isolated DB/cache/media and disabled external integrations.

---

## File Structure

- Create `src/catalog/services/place_duplicates.py`: canonical name/address/coordinate normalization plus a same-volunteer duplicate decision object.
- Modify `src/catalog/services/volunteer_places.py`: call the decision service before the first `Place.save()`, lock the creator row and reject/resume or accept a validated branch override.
- Modify `src/catalog/volunteer_forms.py`: add the non-model `create_as_distinct_branch` control and validate that the explicit override is only present for a new card.
- Modify `src/catalog/domain_admin/volunteer.py`: render a duplicate error with a safe link to the existing card and add a POST-only delete action for deletable volunteer cards.
- Modify `src/catalog/templates/admin/volunteer/edit.html`: show the existing-card call to action and a clear branch confirmation only after the server reports a possible duplicate.
- Modify `src/catalog/templates/admin/volunteer/place_card.html`: show `Удалить черновик` only for cards the volunteer may soft-delete, with a confirmation form.
- Modify `src/catalog/services/volunteer_dashboard.py`: expose `can_delete_draft` based on revision/place state rather than duplicating state checks in a template.
- Modify `src/catalog/testcases/test_volunteer_admin.py`: behavior tests for duplicate rejection, legitimate branch override, concurrency serialization, deletion boundaries and audit entries.

## Task 1: Define the duplicate contract and prove the current failure

**Files:**
- Create: `src/catalog/services/place_duplicates.py`
- Test: `src/catalog/testcases/test_volunteer_admin.py`

**Interfaces:**
- Produces: `find_creator_duplicate(*, creator, candidate, exclude_place_id=None) -> DuplicateDecision`.
- `DuplicateDecision` fields: `existing_place`, `normalized_name`, `is_same_location`, `branch_override_allowed`.
- Consumes: `Place` fields `name_az`, `name_ru`, `name_en`, `name`, `address`, `lat`, `lng`, `created_by`, `deleted_at`.

- [ ] **Step 1: Write the failing same-volunteer duplicate test**

```python
def test_volunteer_cannot_create_second_active_draft_with_same_name(self):
    first = self.submit_new_place(name_az="Azərbaycan DəmirYol Muzeyi", action="draft")

    response = self.client.post(
        "/admin/volunteer/add/",
        self.editor_data("/admin/volunteer/add/", name_az="  azərbaycan dəmiryol muzeyi  ", action="draft"),
    )

    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "already exists")
    self.assertEqual(Place.objects.filter(created_by=self.user, deleted_at__isnull=True).count(), 1)
    self.assertContains(response, reverse("admin:volunteer_edit", args=[first.pk]))
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_cannot_create_second_active_draft_with_same_name --noinput --verbosity 1`

Expected: FAIL because the second POST currently creates a second `Place`.

- [ ] **Step 3: Implement pure normalization and decision code**

```python
@dataclass(frozen=True, slots=True)
class DuplicateDecision:
    existing_place: Place | None
    normalized_name: str
    is_same_location: bool
    branch_override_allowed: bool


def find_creator_duplicate(*, creator, candidate, exclude_place_id=None) -> DuplicateDecision:
    normalized_name = normalize_place_name(candidate)
    if not normalized_name:
        return DuplicateDecision(None, "", False, False)
    candidates = Place.objects.filter(created_by=creator, deleted_at__isnull=True)
    if exclude_place_id:
        candidates = candidates.exclude(pk=exclude_place_id)
    existing = next((place for place in candidates if normalize_place_name(place) == normalized_name), None)
    return DuplicateDecision(existing, normalized_name, same_location(existing, candidate), distinct_location(existing, candidate))
```

`normalize_place_name` must Unicode-normalize, trim, collapse internal whitespace and case-fold the first non-empty localized name, falling back to `name`. `same_location` compares normalized non-empty addresses first, then exact non-null coordinate pairs. `distinct_location` is true only with an existing match and an objectively different non-empty address or coordinate pair.

- [ ] **Step 4: Run the targeted test to verify it is still red**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_cannot_create_second_active_draft_with_same_name --noinput --verbosity 1`

Expected: FAIL until Task 2 wires the service into saving; this confirms the test tests the endpoint, not the helper in isolation.

## Task 2: Block duplicate creation server-side and allow only a real branch override

**Files:**
- Modify: `src/catalog/volunteer_forms.py`
- Modify: `src/catalog/services/volunteer_places.py`
- Test: `src/catalog/testcases/test_volunteer_admin.py`

**Interfaces:**
- Consumes: `find_creator_duplicate`, `DuplicateDecision`, `VolunteerPlaceForm.cleaned_data["create_as_distinct_branch"]`.
- Produces: an unbound or bound `VolunteerPlaceForm` with the non-field error code `duplicate_place_exists` and `duplicate_existing_place_id` for rendering.

- [ ] **Step 1: Write failing tests for override and parallel POST behavior**

```python
def test_volunteer_can_add_same_named_branch_only_with_distinct_address_and_confirmation(self):
    self.submit_new_place(name_az="Kids Academy", address="Nizami 10", action="draft")
    response = self.client.post(
        "/admin/volunteer/add/",
        self.editor_data(
            "/admin/volunteer/add/",
            name_az="Kids Academy", address="Nizami 12", action="draft",
            create_as_distinct_branch="on",
        ),
    )
    self.assertEqual(response.status_code, 302)
    self.assertEqual(Place.objects.filter(created_by=self.user, deleted_at__isnull=True).count(), 2)

def test_duplicate_create_race_leaves_one_card(self):
    responses = self.post_same_new_volunteer_draft_concurrently(name_az="Race Museum")
    self.assertEqual(Place.objects.filter(created_by=self.user, deleted_at__isnull=True).count(), 1)
    self.assertIn(200, [response.status_code for response in responses])
```

- [ ] **Step 2: Run the tests to verify they fail for the intended reason**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_can_add_same_named_branch_only_with_distinct_address_and_confirmation catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_duplicate_create_race_leaves_one_card --noinput --verbosity 1`

Expected: the branch test fails because no explicit override exists; the race test fails because two cards can currently be inserted.

- [ ] **Step 3: Add the form control and server-side save gate**

```python
# VolunteerPlaceForm
create_as_distinct_branch = forms.BooleanField(required=False, widget=forms.CheckboxInput())

# before the initial Place.save() in save_working_revision
locked_creator = get_user_model().objects.select_for_update().get(pk=user.pk)
decision = find_creator_duplicate(creator=locked_creator, candidate=candidate)
if decision.existing_place and not (
    form.cleaned_data["create_as_distinct_branch"] and decision.branch_override_allowed
):
    form.duplicate_existing_place_id = decision.existing_place.pk
    form.add_error(None, _("A card for this place already exists. Open it to continue, or confirm a distinct branch with another address or location."))
    return place, revision, form
```

Lock the `User` row only for a new card (`place.pk is None`). Do not create a blank `Place` before this gate. On a permitted override, write a `PlaceChangeAudit` entry with field name `duplicate_branch_override` and values `"0" → "1"` after the card exists.

- [ ] **Step 4: Run the duplicate behavior tests to verify they pass**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_cannot_create_second_active_draft_with_same_name catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_can_add_same_named_branch_only_with_distinct_address_and_confirmation catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_duplicate_create_race_leaves_one_card --noinput --verbosity 1`

Expected: PASS; an identical repeat is stopped, a confirmed different branch is allowed, and concurrent requests leave one card.

## Task 3: Make the decision clear in the volunteer UI

**Files:**
- Modify: `src/catalog/domain_admin/volunteer.py`
- Modify: `src/catalog/templates/admin/volunteer/edit.html`
- Test: `src/catalog/testcases/test_volunteer_admin.py`

**Interfaces:**
- Consumes: `form.duplicate_existing_place_id`.
- Produces: `duplicate_existing_url` in the edit context and an accessible alert containing a link to the existing card.

- [ ] **Step 1: Write the failing response test**

```python
def test_duplicate_error_links_volunteer_to_existing_card(self):
    place = self.submit_new_place(name_az="Museum", action="draft")
    response = self.client.post("/admin/volunteer/add/", self.editor_data("/admin/volunteer/add/", name_az="Museum", action="draft"))

    self.assertEqual(response.status_code, 200)
    self.assertContains(response, "data-volunteer-duplicate-alert")
    self.assertContains(response, reverse("admin:volunteer_edit", args=[place.pk]))
```

- [ ] **Step 2: Run the response test to verify it fails**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_duplicate_error_links_volunteer_to_existing_card --noinput --verbosity 1`

Expected: FAIL because the current template has no duplicate alert or existing-card URL.

- [ ] **Step 3: Render the alert and constrained override**

```django
{% if duplicate_existing_url %}
  <section data-volunteer-duplicate-alert class="km-volunteer-duplicate" role="alert">
    <strong>{% translate "Похожая карточка уже есть" %}</strong>
    <p>{% translate "Не создавайте копию: откройте существующий черновик и продолжите работу в нём." %}</p>
    <a href="{{ duplicate_existing_url }}">{% translate "Открыть существующую карточку" %}</a>
    {% if form.create_as_distinct_branch %}{{ form.create_as_distinct_branch }}{% endif %}
  </section>
{% endif %}
```

Do not display the override checkbox before a duplicate decision. If a user tries an override without a distinct address or coordinates, keep the same alert and explain the missing distinguishing data.

- [ ] **Step 4: Run the UI response test to verify it passes**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_duplicate_error_links_volunteer_to_existing_card --noinput --verbosity 1`

Expected: PASS.

## Task 4: Give volunteers a recoverable delete action for duplicate drafts

**Files:**
- Modify: `src/catalog/services/volunteer_dashboard.py`
- Modify: `src/catalog/domain_admin/volunteer.py`
- Modify: `src/catalog/templates/admin/volunteer/place_card.html`
- Test: `src/catalog/testcases/test_volunteer_admin.py`

**Interfaces:**
- Produces: `card["can_delete_draft"]` and POST route `admin:volunteer_delete`.
- Consumes: `Place.soft_delete(deleted_by=...)`, `PlaceChangeAudit`, `own_places`.

- [ ] **Step 1: Write failing deletion-boundary tests**

```python
def test_volunteer_can_soft_delete_own_draft_and_audit_it(self):
    place = self.submit_new_place(name_az="Duplicate draft", action="draft")
    response = self.client.post(reverse("admin:volunteer_delete", args=[place.pk]))
    self.assertEqual(response.status_code, 302)
    place.refresh_from_db()
    self.assertTrue(place.is_deleted)
    self.assertTrue(PlaceChangeAudit.objects.filter(place=place, changed_by=self.user, field_name="deleted_at").exists())

def test_volunteer_cannot_delete_pending_or_published_card(self):
    place = self.submit_new_place(name_az="Pending draft", action="submit")
    self.assertEqual(self.client.post(reverse("admin:volunteer_delete", args=[place.pk])).status_code, 403)
```

- [ ] **Step 2: Run the deletion tests to verify they fail**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_can_soft_delete_own_draft_and_audit_it catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_cannot_delete_pending_or_published_card --noinput --verbosity 1`

Expected: FAIL because no volunteer delete route exists.

- [ ] **Step 3: Add the POST-only soft-delete route and card action**

```python
@require_http_methods(["POST"])
def delete(request, place_id):
    place = get_object_or_404(own_places(request.user).select_for_update(), pk=place_id)
    revision = getattr(place, "volunteer_revision", None)
    if place.status != Place.STATUS_DRAFT or (revision and revision.status == VolunteerPlaceRevision.Status.PENDING):
        raise PermissionDenied
    previous = {"is_active": place.is_active, "deleted_at": place.deleted_at, "deleted_by_id": place.deleted_by_id}
    place.soft_delete(deleted_by=request.user)
    DjangoPlaceChangeAuditRepository().create_entries(...)
    return redirect("admin:volunteer_index")
```

The card form must include CSRF protection and a native confirmation message. The action label must say `Удалить черновик`; it must never appear for `pending`, approved/published or already deleted cards. Superadmins continue to use the existing main-admin soft-delete and restore flows.

- [ ] **Step 4: Run the deletion tests to verify they pass**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_can_soft_delete_own_draft_and_audit_it catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_volunteer_cannot_delete_pending_or_published_card --noinput --verbosity 1`

Expected: PASS.

## Task 5: Regression and rendered-browser verification

**Files:**
- Test: `src/catalog/testcases/test_volunteer_admin.py`
- Test: `src/catalog/testcases/test_volunteer_dashboard.py`

- [ ] **Step 1: Run the focused server suite**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin catalog.testcases.test_volunteer_dashboard --noinput --verbosity 1`

Expected: PASS with no database writes outside the disposable test database.

- [ ] **Step 2: Run the admin duplicate regression suite**

Run: `DJANGO_TESTING=1 .venv/bin/python manage.py test catalog.testcases.admin --noinput --verbosity 1`

Expected: PASS; the pre-existing main-admin contact/address suggestions still work.

- [ ] **Step 3: Perform rendered admin QA using isolated fixtures**

Check: create first draft → try same name → alert/link → resume existing; create same-name distinct-address branch with explicit confirmation; delete a draft; verify no delete action for pending card. Verify 390, 768, 1024, 1280 and 1440 px; keyboard focus, form error, confirmation and no console/static errors.

- [ ] **Step 4: Record the exact command outputs and snapshot in the implementation handoff**

Include the tested commit, PASS/FAIL counts, browser widths and any untested production scope. Do not deploy, purge existing duplicate records or commit/push without separate authorization.

## Plan Review

- Spec coverage: prevents repeated volunteer drafts; differentiates real branches; keeps global duplicate hints; provides soft deletion rather than destructive deletion; records auditable changes; preserves main-admin and published-content safety.
- Deliberate boundary: existing duplicates are not bulk-deleted. They remain recoverable and require a reviewed selection; the new volunteer action applies only to the author’s draft/rejected work.
- Type consistency: the save gate produces `duplicate_existing_place_id`; the view derives `duplicate_existing_url`; the template consumes only the URL. Dashboard deletion permission is computed in Python and consumed by the card template.
