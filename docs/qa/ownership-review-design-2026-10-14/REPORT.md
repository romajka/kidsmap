# Ownership inspection design — 2026-10-14

Explicit user authorization: improve the full-card inspection page visually and
functionally, including lightweight statistics and animation. LOCAL HEAD
`e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`; all results
below concern the dirty WORKTREE. Pre-existing changes were preserved.

## Result

Compact identity header with photo, title, publication state and prominent actual
website preview. Four linked metrics use the displayed snapshot: required-field
completion, stored/available photos, languages with both name and description,
and activities/groups. Completeness explicitly does not imply moderator approval.

The changes disclosure compares the displayed submitted snapshot with live data.
Scalar values appear side-by-side, cleared values are marked, and large text stays
fully available in native disclosures. Structured blocks link to the full section.
Equivalent numeric representations are normalized through model fields before
comparison; foreign-key differences use related names and stable field ordering.
The current-version view has no submitted-diff block.

Section navigation highlights the current section, moves keyboard focus to the
chosen section, and sticks below the admin header on larger screens. Mobile
navigation stays in normal flow. Photo zoom, language selection, publication,
ownership, rejection and stale-request permission gates were preserved. Small
hover/section transitions respect reduced motion. No extra packages or fonts.
Exact RU/AZ/EN messages were appended without replacing existing locale entries.

## Evidence

- `tests-before.txt`: expected failure for the absent review-summary helper.
- `normalization-before.txt`: expected failure proving equivalent serialized
  prices/ages were initially treated as changes. Regression test added before fix.
- `tests-final.txt`: fresh isolated Django run of review-summary, existing full
  admin-preview and existing website-preview suites; includes permissions,
  unpublished visibility, PostgreSQL read-only transaction and no tracking writes.
  Exact invocation: isolated stand venv runs
  `docs/qa/ownership-preview-fix-2026-10-14/runtime.py test catalog.testcases.test_ownership_review_summary catalog.testcases.test_ownership_admin_preview catalog.testcases.test_ownership_site_preview --keepdb`.
- `browser-result.json`: fresh actual authenticated Chromium flow, RU/AZ/EN at
  390/768/1024/1440px. Metrics, resolved icons, translation, overflow, navigation
  focus/clearance, language filters, expand/collapse, gallery arrows/Escape/focus
  return, current/submitted versions, genuine website preview, reduced motion,
  long title and no review writes. No external service dependencies.
- Visual inspection of desktop, mobile and changes screenshots. Source/screenshot
  hashes identify the verified snapshot. `git diff --check` and JS syntax passed.

An intermediate browser attempt asserted a version switch before navigation had
completed; final harness waits for the URL and page content. The final expanded-sidebar matrix also exposed an actual tablet-header overflow;
this was fixed in the page stylesheet and retested. Intermediate results
are not used as acceptance. The final result replaces them.

## Limits and manual review

Fictional local data only. Isolated DB/cache/media, `DJANGO_TESTING=1`, allowlisted
environment and blocked external transport. No production access, schema changes,
commit, push or deployment. Production records, full-project suite, screen
readers, physical devices and Firefox/WebKit were NOT RUN. Missing photos and
incomplete languages are covered by summary tests; the visual fixture is complete.
A scoped tablet-header correction keeps all actions reachable with the expanded
sidebar at 768–991px; only redundant text labels are hidden, accessible names and
buttons remain. The task-owned browser session is closed after QA. The user's local application
and its isolated PostgreSQL remain running for manual review at:

http://127.0.0.1:55069/admin/catalog/placeownershiprequest/1/preview/

Use the synthetic credentials already supplied in this chat. Credentials are not
included in repository artifacts.

Final evidence: 35/35 tests PASS (42.067 seconds); 111/111 browser assertions
PASS, zero page errors/local HTTP failures/review writes. JS syntax and diff
whitespace checks PASS. Final source and screenshot hashes saved.
