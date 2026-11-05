# Specialist subjects — local implementation, 2026-11-05

User scope: subject-aware specialist entry/filtering and clearer visual priority with icons and motion. Implemented by the primary agent, no independent subagents. LOCAL HEAD at start: `7b9ea9803adb1cc83738a6bb1686908541f3d0c2`, branch `redesign/map-and-polish`, no upstream. Existing dirty work and the ongoing split of `views.py` were preserved. Production was not accessed; no commit/push/deploy.

## Behavior

- Shared taxonomy in `src/catalog/services/specialist_subjects.py` reuses the existing specialization relation. English, mathematics, Azerbaijani and Russian keep their existing codes and existing profile assignments.
- Generic tutor and exam-preparation submissions require a subject. Incomplete drafts remain saveable. Pending/published admin forms enforce the same requirement. Other categories retain their existing requirements.
- Owner editor separates category choices from subject choices. Teaching categories come first; the subject panel appears for tutoring/exam preparation or an existing precise-subject profile. Multiple selections retain native checkbox/keyboard behavior. Completeness reflects missing subjects using server-supplied IDs.
- Directory `specialization=tutor` includes legacy subject-only profiles. `subject` is independent of the language of lessons and combines with age, price, sort and other filters. Counts use distinct public active profiles. Unknown subject returns no results.
- English/mathematics shortcuts are near the search box; subject filter is directly below category. Subject badges with consistent icons sit above card descriptions and near the name in the profile. Selected/focus/hover/press states and reduced-motion CSS guard added.
- Additive data migration `0153_specialist_school_subjects` creates physics, chemistry, biology, history, geography, computer science, French and German choices. It does not overwrite existing names/activation or edit profile relations. Reverse deliberately preserves potentially referenced choices. No schema changes.
- Query sanitization now retains `subject`, `age_from`, `age_to`; middleware previously removed these parameters. Subject selection is retained by search, sort and pagination through the existing selected/query contract.

## Verification

All execution used `DJANGO_TESTING=1`, isolated media/private storage, LocMem cache and email, empty inherited service environment and synthetic accounts. The QA profile and logs are under `.tmp/specialist-subjects/`.

- RED: new tests reproduced missing subject validation, the incomplete generic tutor filter and incorrect counters. A subsequent integration test reproduced the canonical-query redirect that stripped the filter. New JS regression reproduced irrelevant subject-panel visibility.
- PostgreSQL 17: **199 specialist tests PASS**, 118.656s, exit 0; all 21 specialist test modules. A disposable loopback-only container named `specialist-subjects-pg` was used, independently of existing database containers.
- Final targeted PostgreSQL rerun after the last presentation/test-fixture adjustments: **43 PASS**, 9.053s, exit 0 (subjects, specialist flows, public presentation, proposal drafts).
- Final Node suite: **25 PASS**, 0 failures/skips, exit 0; owner form, catalog drawer, profile detail and documents. Isolated jsdom 22.1.0. An initial run with the latest jsdom had a legacy HTML-pattern compatibility failure; the existing detail test also needed NODE_PATH for its dependency.
- SQLite exploratory full run: 199 tests, 9 failures/5 errors. Six assertions required PostgreSQL; five concurrency errors were SQLite database locks. Three older success-path fixtures selected a generic tutor without a subject; their already-mathematics profile payload was updated to select mathematics, without changing assertions. These cases passed in PostgreSQL.
- `makemigrations --check --dry-run --settings=qa_settings`: no changes detected. New data migration applied successfully to the disposable databases. Seed idempotency and preservation of an existing inactive/renamed subject are tested.
- JS syntax, Python compilation and changed-file whitespace checks passed. Whitespace check used `core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol` to respect existing CRLF files.

Exact full-suite command and output: `.tmp/specialist-subjects/postgres-suite.log`; final rerun: `final-targeted.log`; JS: `node-final.log`. Reproducible launchers: `run_pg_suite.py`, `pg_settings.py` and `qa_settings.py` in the same local scratch directory. Test credentials are synthetic and are not release configuration.

## Rendered browser evidence

Codex browser, isolated server `http://127.0.0.1:8876`, synthetic data only:

- **63 responsive states**: catalog, owner form, public profile × RU/AZ/EN × 320/360/390/768/1024/1280/1440px. No horizontal page overflow; expected subjects retained. Key states visually inspected with screenshots. No captured browser error logs during these checks.
- English shortcut returned the two English tutors and excluded the English-speaking mathematics tutor.
- Mobile drawer: mathematics + English working language applied successfully and returned only the mathematics tutor; resulting URL retained both filters.
- Native subject checkboxes worked by click and Space, with visible selection/focus styling.
- Login → category tutor → English + mathematics → save draft → reload: both subjects retained.
- Complete online form without a subject: one visible subject validation error, no submission. Selecting both subjects and resubmitting: account showed the profile pending moderation. Synthetic DB verification confirmed `pending` and the three relation codes `tutor`, `english_teacher`, `math_tutor`.
- Motion guard verified in source; reduced-motion browser emulation was not available through the current browser API. Physical devices/Safari, full application acceptance, external services and production deployment were not run.

Local preview remains available on port 8876. The separate disposable PostgreSQL test container is cleaned up after verification. Release must apply data migration 0153 and include the new CSS asset; no normal-development or production database migration was performed here.

## Follow-up: one discovery block, accurate requirements and complete user flow

User follow-up on 2026-11-05 explicitly authorized local test creation/submission and requested consolidation of the screenshot's two competing quick-link groups.

Implemented:
- One subject-first discovery block: English, mathematics, Azerbaijani, Russian, all tutors, and an anchor to other categories. Tutors lead the category strip, filter list and owner category picker. Other professions remain available.
- Search matches localized subject names and specialization names even when the name/biography does not mention the subject. All-category/all-tutor links clear the previous subject; other filters remain. Changing category clears a stale subject; choosing a subject selects tutoring.
- The owner completion meter counts the subject separately: online tutor 7 mandatory items, offline/mixed tutor 8. Categories have their own count; the selected summary explicitly includes categories and subjects. No duplicate numeric badge, and no misleading hardcoded 0/6 before initialization.
- Reversed age/price ranges no longer produce a ready-to-submit claim. The server still validates all submissions. Subject errors are visible, associated with the controls, and the error-summary link focuses a visible subject choice.
- Admin uses the same subject requirement metadata, updates completion on selection/removal, and refuses missing subjects on pending/published forms and bulk moderation/publication. Failed admin saves display the persisted publication/visibility status, not unsaved POST values.
- Native checkbox keyboard support, focus indication, small selection/hover transitions, and reduced-motion CSS remain in place.

Rendered acceptance, isolated localhost:8876 only:
1. Created a synthetic tutor through the regular account; filled the other requirements but omitted the subject: meter 6/7.
2. Saved and reopened the incomplete draft; inputs retained. Submission returned the subject error and did not publish anything.
3. Added mathematics; reversed age 18–7 prevented readiness. Corrected to 7–17. Switching to offline with no location showed 7/8; back to online showed 7/7.
4. Saved/reopened with mathematics selected; submitted. Account showed profile pending and identity claim pending separately.
5. Opened the actual submitted profile as the local synthetic moderator. Removing the subject changed admin completion to 6/7. Attempted publication was rejected with the subject error; the saved-state header correctly showed pending/hidden.
6. Restored mathematics and saved publication in the isolated fixture site. Admin counts: total 6, public 5, pending 1. Public tutoring count 5; mathematics count/results 3; English count 2. The profile detail showed mathematics, online, ages 7–17 and Russian working language without inventing a price or verification badge.
7. Typed mathematics in search; three matching profiles. Mobile category/subject controls reacted correctly. Catalog and owner form passed 24 width/language checks: RU/AZ/EN × 320/390/768/1280, no horizontal overflow. Subject/category counts remained 2/1 for one selected subject and category.

Evidence (ignored local scratch, synthetic data only):
- `.tmp/specialist-subjects/form-final.jpg`
- `.tmp/specialist-subjects/catalog-final.jpg`
- `.tmp/specialist-subjects/catalog-mobile-final.jpg`
- `.tmp/specialist-subjects/followup-layouts.json`
- `.tmp/specialist-subjects/followup-node-final.log`: 29 JavaScript tests passed.
- `.tmp/specialist-subjects/followup-final-targeted.log`: 37 targeted PostgreSQL tests passed.
- `makemigrations --check --dry-run --settings=qa_settings`: no changes detected.

Test harness observation: the first follow-up full PostgreSQL suite passed 201 tests. A later 204-test run with `--keepdb` had two existing fixture failures because `TransactionTestCase` flushing removed the migration-seeded EDU category, and two unrelated tests create a Place assuming EDU already exists. Assertions/application code were not weakened. The final suite uses a fresh disposable database; see final verification below. All tests use `DJANGO_TESTING=1`, isolated database/cache/media and a clean environment. Local translations were compiled into the isolated preview's locale directory.

Browser console recorded one cross-navigation `ViewTransition opt-in disabled` rejection while moving between pages; no failed user action was observed. Reduced-motion support was inspected in CSS, not emulated in this browser. No production deployment, production migration, real profile publication, commit or push was performed.

### Final verification

- Fresh isolated PostgreSQL suite: **204 tests passed**, 102.127 s, exit 0. Command: `.venv/bin/python .tmp/specialist-subjects/run_pg_suite.py` (all 21 specialist test modules; the script passes `--settings=pg_settings --noinput` with a clean environment and `DJANGO_TESTING=1`). Log: `.tmp/specialist-subjects/followup-fresh-final.log`. Django destroyed its test database after success.
- Final JS command: `NODE_PATH=$PWD/.tmp/specialist-subjects/node/node_modules node --test scripts/tests/specialist_owner_form.test.cjs scripts/tests/specialist_catalog_drawer.test.cjs scripts/tests/specialist_admin_readiness.test.cjs scripts/tests/specialist_detail.test.cjs scripts/tests/specialist_documents.test.cjs` — **29 passed**, exit 0.
- `node --check static/js/specialists.js` and `node --check static/admin/js/specialist_admin.js`: passed. Own tracked diff whitespace check passed with `core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol` for the repository's existing CRLF files.
- Disposable PostgreSQL container removed after verification. SQLite preview on localhost:8876 retained for review; synthetic account/profile data remain there only. All-module acceptance and production release are outside this run.
