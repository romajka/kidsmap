# Admin draft recovery — 26 October 2026

Status: **LOCAL PASS**. User authorized three reported fixes. Branch `codex/admin-draft-recovery-2026-10-26`, based on `1b0acf8c`. No commit, push, deployment or production data changes. No migration.

## Result

1. **Conflict recovery.** Admin and volunteer editors show a separate explicit **«Начать с текущей версии»** action when their working revision conflicts with current content. The action starts a draft from current data, retains the original author and stores the complete former revision in `PlaceChangeAudit` under `working_revision_restart`. Current user permissions, signed source token and revision version are checked again inside the atomic operation. A stale tab cannot reset a newer revision; failed audit storage rolls the operation back. The live card is unchanged.
2. **Unknown schedule.** An empty structured week stays `[]` through form, JS, save and JSON export. The editor displays **«Расписание пока неизвестно»** and Unknown day labels. Clear and empty import retain this state. Explicit closed days remain stored closed days; seven closed days display Closed. Unknown hours remain incomplete for publication and do not manufacture public opening-hours claims. Existing legacy text fallback is preserved.
3. **Saved preview.** The private saved-card preview now selects an active draft, rejected or pending revision. It displays saved texts, prices, schedule, explicit empty values and related candidate data using the existing renderer. Drafts are labelled **«Сохранённый черновик»**. Approved/no-revision cards retain the current-content fallback. Request inspection remains separate. Preview is read-only, permission-protected, noindex and no-store.

The shared schedule script references were cache-busted in admin, volunteer and owner forms. New recovery/preview text is translated for AZ/RU/EN.

## Causes

- Admin used the volunteer working-copy form but omitted the old volunteer-only restart action; its handler accepted only normal saves. The previous restart also discarded the candidate without archiving it.
- Parser/validator/serializer/JS normalized missing hours into a seven-day closed default. The schedule writer and public row formatter also discarded explicitly closed weeks. Editable placeholder rows are now separate from actual data.
- `build_place_preview` always built from the base Place; only request/revision previews selected candidates. It now explicitly selects eligible saved revisions while retaining the existing guest-looking public renderer.

## Verification

All application tests used cleared environment, `DJANGO_TESTING=1`, dedicated PostgreSQL test databases, isolated LocMem caches/media/private storage/email and current isolated locales. PostgreSQL ran in a task-owned Docker container with networking disabled and a dedicated Unix socket. No production credentials or production data were used.

**TDD:** Each fix had an observed failing regression before implementation. Logs retained under `/tmp/kidsmap-admin-fixes-20261026/`. Initial PostgreSQL provisioning and synthetic-fixture failures were corrected before green acceptance; they are not presented as product regressions.

**Django/PostgreSQL:158 PASS** in the joint run (48.507 seconds):

```sh
.venv/bin/python /tmp/kidsmap-admin-fixes-20261026/run-tests.py integrated \
 catalog.testcases.test_admin_saved_draft_preview \
 catalog.testcases.test_admin_revision_recovery \
 catalog.testcases.test_admin_unknown_schedule \
 catalog.testcases.test_admin_place_moderation_fix \
 catalog.testcases.test_ownership_site_preview \
 catalog.testcases.test_place_editor_preview \
 catalog.testcases.test_place_json_scope \
 catalog.testcases.test_volunteer_admin \
 catalog.testcases.pricing_plans
```

Additional targeted acceptance: schedule/backend corruption-preservation checks16 PASS; conflict plus existing volunteer workflow70 PASS. These overlap the joint run; do not add them to158.

**Node:80 unique checks PASS.** The joint run passed79, with one Select2 test skipped for missing vendor paths. That specific test then passed with the real Django admin jQuery/Select2 assets. Eight other tests were intentionally filtered out in that focused rerun.

```sh
KIDSMAP_JSDOM=/home/ramin/kidsmap/.tmp/phone-dom/node_modules/jsdom \
 node --test scripts/tests/schedule_unknown.test.cjs scripts/tests/schedule_confirm.test.cjs \
 scripts/tests/place_json_patch.test.cjs scripts/tests/place_json_prompts.test.cjs \
 scripts/tests/editor_preview_return.test.cjs scripts/tests/editor_feedback.test.cjs \
 scripts/tests/owner_workflow.test.cjs

KIDSMAP_JSDOM=/home/ramin/kidsmap/.tmp/phone-dom/node_modules/jsdom \
KIDSMAP_JQUERY=/home/ramin/kidsmap/.venv/lib/python3.12/site-packages/django/contrib/admin/static/admin/js/vendor/jquery/jquery.js \
KIDSMAP_SELECT2=/home/ramin/kidsmap/.venv/lib/python3.12/site-packages/django/contrib/admin/static/admin/js/vendor/select2/select2.full.js \
 node --test --test-name-pattern='Select2 options stay' scripts/tests/place_json_prompts.test.cjs
```

**Rendered CUA browser:**45 verified states: unknown-hours editor, visible conflict/recovery form and saved preview; AZ/RU/EN; actual widths390/768/1024/1280/1440. Required content was present and no horizontal overflow occurred. Screenshots reviewed at desktop and mobile. A fixture that no longer conflicted after recovery was replaced by a genuinely conflicting legacy revision before the final responsive matrix. Early attempts to resize an inactive tab are excluded from acceptance.

Functional browser checks: recovery warning/button visible; recovery loads current values and enables save; subsequent draft save succeeds; schedule preset→Clear→confirm→keyboard save→JSON export preserves `schedule_days:[]`; explicitly closed week remains Closed; saved preview displays new conditions and a47AZN synthetic tariff. Recovery form console: no errors. Synthetic users/data only; separate local session/CSRF cookie names avoided collisions with another local app.

Browser evidence: `/tmp/kidsmap-admin-fixes-20261026/browser-responsive.json`, `browser-unknown-export.json`, `browser-console.json`; screenshots in `.tmp/admin-draft-fixes-20261026/screenshots/`.

**Other checks:** Django `check` PASS; `makemigrations --check --dry-run` reports no changes; Python compilation PASS; three gettext catalogues compile with format checks; `git -c core.whitespace=cr-at-eol diff --check` PASS. Existing CRLF is preserved. A plain whitespace check reports those CR line endings, not introduced spaces.

Source manifest: `/tmp/kidsmap-admin-fixes-20261026/source-manifest.json`. A concurrent unrelated favorites-rating fix in `account_dashboard.html` and `test_account_dashboard_favorites.py` was preserved and excluded from this scope.

## Release and data follow-up

Not deployed. Production bug338 and stored schedules353–358 are not claimed fixed by local acceptance.

After an approved release:

1. Verify admin static asset version and the new recovery/preview UI on the deployed build.
2. For Sky Park338, use the explicit recovery action. Its former candidate is archived. Then obtain a fresh export and enter the confirmed branch data/tariffs; do not reuse stale import versions.
3. For drafts353–358 with previously fabricated closed weeks and genuinely unknown hours, use Clear and save each draft. Do not clear359 with confirmed hours or309 with pre-existing hours. No heuristic bulk rewrite is included.
4. Reopen those drafts, export JSON and verify unknown hours are `[]`; check saved-candidate preview. Publication remains a separate user review.

Not run: full application suite, physical devices/Safari, live production rollout and production data cleanup. Browser tool timeouts were handled by inspecting actual state before retry; no security policy bypass was used.
