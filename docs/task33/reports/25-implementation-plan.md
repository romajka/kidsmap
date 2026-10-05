# Specialist Screens Implementation Plan

**Goal:** integrate accepted specialist-25-r1 with real stage24 services, preserving person privacy, bilateral consent, historical practice and legacy URLs.

**Architecture:** server-rendered Django workspace modes call existing specialist_domain/specialist_documents services. Business grants never grant person/document access. Public profile consumes server-filtered current/past employment and approved opted-in qualifications. No new framework, schema or production transfer is planned.

**Tech Stack:** Django6, PostgreSQL17 disposable QA04, existing templates/CSS, AZ/RU/EN gettext, local Chromium.

**Spec:** prompts/25.md; decisions.md D08; architecture.md Specialists/Screens; specialist-25-r1 accepted2026-10-03 by «принимаю продолдавй».

## Constraints and preservation

Only25; no26+, production, commit/push/deployment. HEAD015d031d on task33-progress; all220 incoming dirty/untracked files and binary patch saved before edits (25-implementation-entry-manifest.json). Owner/admin-public acceptance persists. Person/Org/dedicated review permissions remain backend-derived; POST+CSRF and bound nested IDs. Data/URLs/history cannot be inferred from names. Test DJANGO_TESTING=1, disposable PostgreSQL/cache/media/email, no external credentials/integrations. Keep assertions strong; label historical failures separately.

## Task1 — backend workspace (stage25_backend)

Files: new controllers/specialist_workspace.py, specialist_forms.py, testcases/test_task33_specialist_workspace.py; urls.py; bounded owner_specialist_use_cases.py and specialist_domain.py only as needed.

- [x] Write meaningful tests for anonymous/foreign/person/org/ordinary-staff/dedicated reviewer, CSRF, nested claim/employment/document IDs, stale version, one-sided consent, opt-in vs approval, denied person fields through business scope.
- [x] Run isolated RED before implementation; root coordinates shared Linux mirror.
- [x] Add person workspace, org proposals/links, claim submit/withdraw, document upload/opt-in, dedicated review forms using existing service APIs. Explicit action+version; successful POST redirects; invalid form preserves input. Fresh ACL at service boundary.
- [x] Person editor retains online/private office; optimistic stale save uses existing version/timestamp without unnecessary schema changes.
- [x] Execute targeted GREEN and adjacent stage24 services/security tests; report exact counts/snapshot.

## Task2 — accepted UI (stage25_ui)

Files: pages/specialist_workspace.html, pages/owner_specialist_create.html, catalog/specialist_detail.html, static/css/pages/specialist_workspace.css; bounded UI JS only if needed.

- [x] Agree route/form/context contract with backend; real Django forms and CSRF replace all design simulation.
- [x] Render person/org/claim/doc/review states, label pending confirmation and role/period/current vs past; business cannot see biography/contacts/docs editor.
- [x] Reuse accepted hierarchy/tokens, native labels/buttons, visible focus and linked errors. Upload identity always private; qualification choice separate from moderation.
- [x] Add public current/past employment and practice history from root-provided server context; approved-only documents; management/claim links route by stable ID.
- [x] Verify browser AZ/RU/EN all seven widths and meaningful interaction/error states through independent QA.

## Task3 — public contracts and fixture transfer (root)

Files: services/specialist_presentation.py (new), views.py:specialist_detail, testcases/test_task33_specialist_screens.py (new); locale/az|ru|en django.po; bounded owner dashboard/org navigation templates if needed after ownership agreement.

- [x] Test that past/future/cancelled/ownership-stale participation never appears as current employment; direct published old slug URLs retain RU/EN200 and AZ canonical301→200; no private pending document metadata.
- [x] Test additive0130→0132 transfer with duplicate-name profiles, legacy Place link, independent office/online practice, documents/reviews/IDs/URLs preserved. No claims/consents inferred; rerun conversion deterministic.
- [x] Introduce server presentation classifier from actual dates/consent epochs and safe historical context; connect public view.
- [x] Extract only stage25 labels, provide AZ/RU/EN translations, compile catalogs in isolated mirror.

## Task4 — independent checks and final handoff

Ownership: stage25_browser owns new qa25 application harness/evidence and application browser report. After implementation, independent security-reviewer gets bounded frozen source+own negatives; implementation executor review is not independent.

- [x] Actual local Chromium profiles/workspaces/org invitations/claims/docs/reviewer across AZ/RU/EN×320/360/390/768/1024/1280/1440, keyboard/errors/console/static/private endpoints.
- [x] Isolated nested-ID/role/URL/fixture transfer and adjacent Task33 tests; Django checks/migration consistency. Full suite only if needed to assess new failures; historical NOT_GREEN remains explicit.
- [x] Preserve220 entry files, enumerate authorized deltas, SHA source/QA/locale artifacts without final report self-hash. Update25.md/results/source manifest/journal/acceptance; DONE only if all acceptance and independent checks passed, else concrete REVIEW_PENDING/BLOCKED.
- [x] Release own active_run after real executors finish; stop before26/production. No new user approval required within accepted25 scope.

## Execution result — 2026-10-03

Completed in scope25: root479/479 Task33; independent security17/17 plus late static-template delta; browser168/380 plus corrective42/84; migration/fixture transfer and cleanup PASS. Exact commands/snapshots/limits in25.md and reviewer reports. Historical full application NOT_GREEN and fresh full1716 NOT_RUN. No26+/production/commit/push/deploy. Source/preservation final manifest excludes report self-hashes.
