# Place Readiness Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `test-driven-development` and `verification-before-completion` task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every card editor, publication gate and readiness counter use the same twelve requirements, and show the exact missing item beside every incomplete section.

**Architecture:** `catalog.services.place_readiness` remains the sole authority. Admin and volunteer UI receive requirement metadata and reasons from it; browser JavaScript only mirrors the supplied metadata for unsaved form feedback. The owner submission flow must replace its independent `permanent_place_rules.publication_errors` gate with the canonical verdict, preserving only non-readiness form validation.

**Tech Stack:** Django, Django templates, vanilla JavaScript, Django `TestCase`.

**Spec:** User request, 2026-09-16: transparent and identical readiness for Basics, Price & age, Location, Photos, Verification and total.

## Global Constraints

- Canonical requirements stay exactly: name, description, category, subcategory, district/region, address, coordinates, age, price, phone, schedule, main photo.
- `district` is the persisted `Place` location field; the UI must call it a district/region, never a misleading “Город / регион” readiness criterion.
- No duplicate business-rule enum or requirement list in JavaScript.
- Existing published legacy cards keep their documented compatibility path; new publication/submission uses canonical readiness.
- Tests run with `DJANGO_TESTING=1`, disposable DB/media, LocMem cache and no external requests.
- No commit, push, deployment or production mutation is part of this approved-implementation scope unless separately authorized.

---

## Files and responsibilities

- Modify `src/catalog/services/place_readiness.py`: canonical labels and structured section-level missing-item data, if a small presentation helper is needed.
- Modify `src/catalog/services/permanent_place_rules.py`, `src/catalog/forms.py`, and `src/catalog/controllers/owner_places_controller.py`: retire the divergent owner publication gate in favor of `evaluate_form_readiness`/`publication_blocked_message`.
- Modify `src/catalog/domain_admin/place.py`: derive section count plus first missing requirement from the canonical checklist.
- Modify `src/catalog/templates/admin/catalog/place/form/_navitem.html` and `src/catalog/templates/admin/catalog/place/form/_section_open.html`: render `4 / 5 — не заполнено: Район / регион` accessibly for partial sections.
- Modify `static/admin/js/kidsmap_place_form.js`: update that same section explanation from the server-provided checklist while editing, with no new rule list.
- Modify `src/catalog/services/volunteer_editor.py`, `src/catalog/services/volunteer_dashboard.py`, and their rendered templates only if their labels/reasons do not consume the shared canonical label after the service change.
- Modify `src/catalog/testcases/place_readiness.py`, `src/catalog/testcases/owner.py`, `src/catalog/testcases/test_volunteer_admin.py`, and `src/catalog/testcases/admin.py`: regression coverage.

### Task 1: Lock the canonical location contract in tests

**Files:**
- Modify: `src/catalog/testcases/place_readiness.py`
- Modify: `src/catalog/testcases/admin.py`

**Produces:** Tests proving Location has exactly five canonical items and that a card with only `district` blank yields `4 / 5`, code `region`, persisted field `district`, label `Район / регион`, and a human-readable reason.

- [ ] Add a readiness service test that creates `create_ready_place(district="")`, asserts `issues == (region,)`, `issues[0].field == "district"`, `issues[0].label == "Район / регион"`, and location items are `("region", "address", "coordinates", "phone", "schedule")` with four complete.
- [ ] Add an admin change-form test for that place. Assert `km_place_form_summary["sections"]["location"]` contains done `4`, total `5`, and a missing summary naming `Район / регион`; assert the rendered nav/section has both the count and reason.
- [ ] Run these two tests through the isolated harness and confirm they fail before implementation because the current label is `Город / регион` and the section has no reason.

### Task 2: Make the canonical source explicit and presentation-safe

**Files:**
- Modify: `src/catalog/services/place_readiness.py`
- Modify: `src/catalog/domain_admin/place.py`
- Modify: `src/catalog/templates/admin/catalog/place/form/_navitem.html`
- Modify: `src/catalog/templates/admin/catalog/place/form/_section_open.html`
- Modify: `static/admin/js/kidsmap_place_form.js`

**Produces:** A section state shape `{done, total, missing_labels, missing_message}` based solely on `ReadinessItem`s, rendered in both initial HTML and live client updates.

- [ ] Change the `region` requirement label to the accurate user-facing text `Район / регион`; retain code `region` for compatibility and retain `field="district"` so its anchor and error focus resolve to the actual control.
- [ ] In `_build_place_section_states`, collect incomplete checklist items per section and add `missing_labels` plus `missing_message`, where `missing_message` is `Не заполнено: <labels joined by comma>`; do not count optional `region`, `metro`, gallery, Instagram, website, or advice.
- [ ] Render `{{ state.label }} — {{ state.missing_message }}` in the nav and accordion header only when `state.missing_message` is non-empty; expose it as normal text, not `title`-only content.
- [ ] Include each checklist item’s server label in the existing JSON configuration. In `paintSection`, build the same Russian/localized `Не заполнено: …` string from incomplete items in that section and set the nav and header text; do not introduce a manual list of field names.
- [ ] Run Task 1 tests and the existing admin layout test; both must pass.

### Task 3: Remove the owner publication-rule fork

**Files:**
- Modify: `src/catalog/forms.py`
- Modify: `src/catalog/services/permanent_place_rules.py`
- Modify: `src/catalog/controllers/owner_places_controller.py`
- Modify: `src/catalog/testcases/owner.py`
- Modify: `src/catalog/testcases/place_readiness.py`

**Produces:** Owner submission, admin publication and volunteer approval return the same completed count and issue codes for identical submitted data.

- [ ] Add a parameterized test that builds one valid submitted payload and then independently removes `district`, uses a short but non-empty description, selects `price_mode="free"`, and supplies a non-Baku district. Assert owner submission, `evaluate_form_readiness`, and admin publication agree on `is_ready` and issue codes for each case.
- [ ] Replace the `publication_errors(...)` call in `PermanentPlaceForm.clean()` with a call to `evaluate_form_readiness(self, self.instance)` after schedule and pricing normalization. Attach every returned issue to `issue.field` and add `publication_blocked_message(readiness)` as the non-field explanation when submission is blocked.
- [ ] Keep file-size, date-range, taxonomy relationship, phone format and image validation in the form: they are validation, not readiness requirements.
- [ ] Delete `permanent_place_rules.REQUIRED`, `publication_errors`, `client_rules`, and all now-dead imports/callers only after `rg` proves no consumer remains. Do not remove generic `copy()` if the volunteer UI still consumes it.
- [ ] Run the new parity test plus focused owner, readiness and volunteer approval tests; all must pass.

### Task 4: Verify save/reload and all UI surfaces

**Files:**
- Modify: `src/catalog/testcases/test_volunteer_admin.py`
- Modify: `src/catalog/testcases/admin.py`
- Modify: `src/catalog/testcases/owner.py`

**Produces:** Regression protection for recalculation after save and for the admin/volunteer/publication invariant.

- [ ] Add an admin POST test: save a draft with empty `district`, reload, assert Location says `4 / 5` and explicitly names `Район / регион`; POST a district, reload, assert `5 / 5` and no location missing reason.
- [ ] Extend `test_admin_and_volunteer_use_identical_revision_readiness` with the partial-location payload and assert equal total, done count, issue codes, issue labels and section counts.
- [ ] Add a volunteer approval test that rejects the same partial payload using `publication_blocked_message`, then accepts it after the district is supplied.
- [ ] Run `scripts/check_volunteer_admin.py catalog.testcases.place_readiness catalog.testcases.owner catalog.testcases.test_volunteer_admin catalog.testcases.admin` and record exact pass/failure counts. Then run rendered browser QA at 390, 768, 1024, 1280 and 1440px on an isolated fixture: verify no overflow, keyboard activation of the missing-item link, focus landing on district, live 4/5→5/5 update, and save/reload persistence.

## Acceptance checks

- Location with address, coordinates, phone and schedule but no district reads `4 / 5 — не заполнено: Район / регион`.
- Every incomplete section names its missing canonical items; Verification lists the same items with actionable anchors.
- Admin, volunteer draft/review, owner submission and publication gate agree on canonical readiness for the same payload.
- Saving then reloading does not change the verdict without a data change.
- The total stays `12 / 12` only when publication readiness is true.
