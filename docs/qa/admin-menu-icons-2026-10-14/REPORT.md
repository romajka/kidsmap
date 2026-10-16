# Admin navigation icons and grouping — 2026-10-14

Scope: local burger-menu icons, grouping and spacing explicitly requested by the
user. Branch `task33-progress`, LOCAL HEAD
`e4e05cc213b34e2d771ecb854901bfd016d1db51`; results concern the dirty WORKTREE.
Pre-existing ownership previews, layout fixes and unrelated work were preserved.

Both template shells now render one shared navigation include. Existing menu
metadata resolves to inline SVG outlines from the bundled Material Symbols font,
including meaningful icons for email, social accounts, applications and tokens.
Groups have separate headers, spacing, keyboard focus and a current-page marker.
The active group opens even when an older stored preference closed it. Technical
accounts remain available through the existing model-admin permission checks.
The duplicate permanent-Place navigation destination was removed.

## Verification

- PASS: 24 isolated Django tests, including four new navigation tests and the
  existing volunteer-hub suite. Exact command: the isolated stand venv runs
  `docs/qa/ownership-preview-fix-2026-10-14/runtime.py test catalog.testcases.test_admin_sidebar_navigation catalog.testcases.test_task33_volunteer_hub --keepdb`.
  `tests-final.txt` records 24 tests, 30.221 seconds, OK and no system-check issues.
- PASS: real authenticated synthetic admin paths, 15 browser assertions at
  390/900/1440px, organization and email-address navigation, active-group recovery,
  zero page errors and zero local HTTP failures. `real-browser-result.json`.
- PASS: 222/222 fresh browser assertions. Both real template shells were rendered with the actual vendor burger
  assets and fictional RU/AZ/EN navigation. Fresh responsive/keyboard results are
  recorded in `browser-result.json`; screenshots show expanded and collapsed
  states. This fixture verifies presentation, not translated production records.
- PASS: `git diff --check` and JavaScript syntax check.
- Visual inspection: `real-menu-1440.png` and `real-menu-390.png`, clean glyphs,
  readable labels, group separators and highlighted current route.

The fresh real-browser attempt initially hit CONNECTION_REFUSED before the
isolated server was ready; the completed rerun passed all 15 assertions. An
earlier full fixture matrix passed 696 assertions; a later interrupted repeat is
not counted as success. The final fixture result is the fresh smaller matrix.

## Boundaries

Only fictional local data, isolated PostgreSQL/cache/media and `DJANGO_TESTING=1`
were used. No production credentials, production access, commit, push or deploy.
Production behavior, the real user/card in the supplied screenshot, full-project
suite, physical devices, screen readers and Firefox/WebKit were NOT RUN.
Screenshots are from the local synthetic stand. Previous full-card and public
preview implementations were not re-audited in this menu-only task.

Owned fixture/application servers, named browser session and PostgreSQL container
were stopped after verification. Isolated data was preserved. Source hashes match
the verified files.
