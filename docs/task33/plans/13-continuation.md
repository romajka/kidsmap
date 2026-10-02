# Stage 13 Activity and Group Form Implementation Plan

> **For agentic workers:** Execute these checked steps inline in this session; user authorization for stage 13 already exists. No commit or stage 14 work.

**Goal:** Complete the owner Place continuous form with optional local activities, groups and group tariffs while keeping Park/direct admission independent.

**Architecture:** Extend the existing `nested_pricing` Place candidate field to carry new Activity/OfferingGroup metadata with group plans. Validation stays in Python; the owner browser editor serializes the same versioned tree for explicit submit and autosave. Place approval creates children atomically, so pending edits do not change live pages.

**Tech Stack:** Django forms/publication service, PostgreSQL QA04, vanilla JavaScript, existing pricing records.

**Spec:** `docs/task33/prompts/13.md`, `docs/task33/architecture.md`, accepted owner design.

## Global constraints

- Only stage 13; no Program editor or shared Program publication (stage 14).
- Keep volunteer wizard and direct Place tariffs compatible.
- No production, commit, push, or deploy.
- Targeted isolated QA and real browser AZ/RU/EN widths; no full suite until later milestone per user preference.

### Task 1: server candidate contract

**Files:** `src/catalog/services/pricing_plans.py`, `src/catalog/services/publication_forms.py`, `src/catalog/forms.py`, `src/catalog/services/server_drafts.py`; test `src/catalog/testcases/test_task33_place_continuous.py`.

- [ ] Write a failing request test: create Place with one activity/group and three plan rows, including age/trial/fee; assert candidate only, no live Activity before approval.
- [ ] Run the one test; confirm the expected missing-field failure.
- [ ] Accept a versioned `nested_pricing` JSON field in owner form and private server draft.
- [ ] Validate new IDs as null, reject foreign IDs, unknown keys and age conflicts; preserve old v2 existing-ID payloads.
- [ ] On staff approval create Activity/OfferingGroup/three plans atomically. Assert IDs and local conditions survive; published Place remains visible during pending edit.
- [ ] Run targeted tests and confirm green.

### Task 2: progressive owner editor

**Files:** `src/catalog/templates/pages/includes/owner_place_continuous.html`, `static/js/owner_place_offerings.js`, `static/js/owner_place_continuous.js`, `static/css/pages/owner_place_continuous.css`, `src/catalog/templates/pages/permanent_place_form.html`.

- [ ] Add browser fixture assertion: untouched park has no Activity controls; Add activity opens one block; Add group/plan/translation are explicit actions.
- [ ] Confirm the browser assertion fails on current template.
- [ ] Render controls and sync the hidden `nested_pricing` input with versioned data; restore draft without user-triggered autosave.
- [ ] Ensure preview/errors/keyboard and photo status still work; run real browser AZ/RU/EN responsive matrix.

### Task 3: close stage

**Files:** `docs/task33/reports/13.md`, `docs/task33/implementation-status.md`, stage13 source manifest.

- [ ] Run focused Django tests incl draft, pricing, publication, volunteer and owner organization regression; inspect exact results.
- [ ] Obtain independent bounded review on final source; verify its evidence and source SHA.
- [ ] Check remaining acceptance, final SHA, diff; mark DONE only if every requirement is met, otherwise leave REVIEW_PENDING with precise gaps.
