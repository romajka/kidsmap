# PLACE-QA-12 admin CAS retention Implementation Plan

> APPROVED 2026-10-12: user explicitly approved QA12 and QA13 together. Execution evidence: docs/qa/place-qa12-fix-2026-10-12-r1/REPORT.md. Preserve existing QA09/10/11 diffs and all stands. No commit/push/deploy/production.

**Goal:** keep the submitted admin text/nested form after typed candidate conflict, while protecting the newer canonical version and live Place.

**Architecture:** the existing transactional save remains authoritative. Its typed CAS rejection is re-rendered as an invalid bound form using request-local error state; it must never replay a valid write. Existing request-specific `LocationActorForm` carries the error without mutating shared ModelAdmin/Form classes. Current-version comparison opens a separate authorized GET view.

**Tech stack:** existing Django6 ModelAdmin, PostgreSQL, existing JS/CSS and request-language copy.

**Spec:** `docs/qa/module01-full-2026-10-12-r2/PLACE-QA-12.md`; current module01 acceptance guide.

## Exact boundaries

- Modify `src/catalog/domain_admin/place.py`: PlaceAdmin.get_form/changeform_view/render_change_form only.
- Modify `src/catalog/templates/admin/catalog/place/change_form.html`: typed-conflict banner/current-view link only.
- Modify `static/admin/js/kidsmap_place_form.js`: honest halted/error state for that banner; no stale retries or token rewrite.
- Create `src/catalog/testcases/test_place_admin_conflict_retention.py` and own `docs/qa/place-qa12-fix-2026-10-12-r1/` scripts/evidence/report.
- Existing `ui_copy().server_conflict/open_current_draft` translations can be reused; no new copy/PO patch planned here. No pricing/readiness/ACL/CAS/media storage/model/schema changes. Uploaded-file reselection must be handled honestly: invalid server form cannot claim that a browser FileList survived a document replacement. This plan's proven defect is scalar/nested input loss; report exact file behavior and do not add a staging subsystem silently.
- DJANGO_TESTING=1; fresh own profile/DB/cache/media/private-media/email/locales, fictional data, blocked/SIMULATED external requests, no .env or production credentials. Readback READ ONLY/timeouts, secrets ignored scratch only.

## Task 1 — RED then request-local invalid redisplay

- [ ] New meaningful test: actual admin A/B GETs and publication tokens, native-equivalent POSTs. A commits newer name; stale B posts another valid name plus nested fields. Before patch B redirects and loses its form. Assert that newer candidate/live are protected and bound B remains visible after rejection; assertions must not be weakened.
- [ ] Catch only the actual `candidate_version_conflict` error code from save. Preserve existing handling for unrelated ValidationErrors and volunteer/event paths. The first atomic save must roll back normally.
- [ ] Set a request-local conflict attribute and render the normal admin POST as **invalid**. Extend the already request-bound `LocationActorForm.clean()` to add that non-field error. Existing LocationActorForm permissions and formset validation remain active.

Core pattern:

```python
def clean(self):
    cleaned = super().clean()
    error = getattr(request, '_km_candidate_conflict', None)
    if error is not None:
        self.add_error(None, error)
    return cleaned
```

After rollback, the exception branch can call the normal superclass changeform renderer with that request-local flag, inside a new atomic block. Because the form is invalid, `save_model`/`save_related` must not run again. Do not recursively call the same exception-handling method, temporarily monkeypatch the singleton ModelAdmin, replace POST with GET, replace submitted fields with canonical data, or refresh the stale publication token.

- [ ] Render translated conflict/current-view banner using existing copy and same-object authorized `request.path` GET in a new noopener tab. Stop stale-save actions while retaining editable input; no forced merge/retry. Normal validation errors and valid saves keep their existing behavior.

## Task 2 — acceptance and handoff

- [ ] New tests cover real stale/current tokens, no second write on invalid redisplay, scalar/nested values, foreign/revoked actor, ordinary validation and publication/live protection. Include post-validation race after form.clean, not only an upfront token check.
- [ ] Native A/B matrix all18cells, retained B and untouched A/live, comparison tab, deliberate manual current-view correction/save/reload, honest error status, file widget behavior recorded. No ORM for audited transitions.
- [ ] Run new tests plus affected existing admin/publication/media/ACL suites and configured discovery/corpus as required by changed backend scope. Preserve historical guard/baseline failures and assertions. Check RU/AZ/EN fresh locale/runtime source gate and PNG hashes.
- [ ] Own report records RED/GREEN, exact diff/commands/exits/counts, preservation and limits. Close only QA12 if accepted. Then repeat module01 ACCEPT; new defects stay OPEN with separate approval.

## Testing cadence — user override in this chat

Targeted checks and affected consumers after each repair; module acceptance once all module findings are addressed; global configured corpus only after all13 modules. The older full-corpus-per-repair instruction above is superseded. Current new QA14 is outside this approved scope and prevents module01 closure.
