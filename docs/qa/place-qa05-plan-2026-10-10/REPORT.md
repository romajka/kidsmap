# PLACE-QA-05 — fresh rendered baseline and proposed scope

Date: 2026-10-10, Asia/Baku. AUDIT / PLAN, approval pending. One sequential executor `/root` under canonical orchestrator/frontend-admin/browser-qa responsibilities; no independent specialist execution claimed. Application source was not changed.

## Snapshot and isolated stand

Checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, `active_run: NONE`. [Snapshot](snapshot.json) records incoming worktree and source/prior-plan hashes. PRODUCTION was not accessed and its current state is UNKNOWN.

Created only `kidsmap-placeqa05-plan-20261010`, using local `postgres:17-alpine --pull=never`, DB `placeqa05_plan` on loopback 55440. Actual tested page: `http://127.0.0.1:8819/admin/catalog/place/1/change/`. A generated synthetic superuser and synthetic draft place were used. The long translated category is also synthetic; default categories come from local migrations. Restricted moderator permissions were not tested.

`DJANGO_TESTING=1`, allowlisted process environments, no `.env`, dedicated media/private-media, LocMem cache/email, empty integration settings and blocked external sockets/browser requests. Generated session state is kept only in ignored `.tmp` scratch, not in reports. [Isolation metadata](isolation.json), [runtime](runtime.py), [settings](qa05_settings.py).

Browser: installed Playwright Chromium headless shell **153.0.8010.12**, desktop viewport emulation, height 900. The local Chrome attempt first failed to locate its executable under the restricted environment and then reported remote debugging prohibited by system policy. The audit did not change that policy or install a browser; it used the existing dedicated test browser.

## Fresh effective results

The effective matrix contains **18 rendered checks**. Local resource failures: **0**; page errors: **0**. External Google font requests were deliberately blocked; fallback fonts were used. [Effective geometry/network evidence](browser-matrix-2.json).

| Viewport | RU document scrollWidth | AZ | EN | Horizontal overflow |
|---|---:|---:|---:|---|
| 360 | 373 | 373 | 373 | FAIL in all three languages |
| 390 | 390 | 390 | 390 | PASS |
| 768 | 768 | 768 | 768 | PASS |
| 1024 | 1024 | 1024 | 1024 | PASS |
| 1280 | 1280 | 1280 | 1280 | PASS |
| 1440 | 1440 | 1440 | 1440 | PASS |

At 360: closed document width = 360; trigger left = 53 and width = 254; open popup minimum/computed width = 320, right edge = 373. The failure is a custom DOM popup, not an operating-system native select. Long fixture labels use nowrap/ellipsis and are not shown in full.

Representative screenshots: [RU/360](screenshots/effective-ru-360.png), [AZ/360](screenshots/effective-az-360.png), [EN/360](screenshots/effective-en-360.png), [RU/390](screenshots/effective-ru-390.png), [RU/1440](screenshots/effective-ru-1440.png). All eighteen effective images are listed with hashes in [screenshot manifest](screenshots-manifest.json).

Keyboard results at 360 were identical across RU/AZ/EN. [Raw focus/value readback](browser-keyboard-2.json):

| Sequence | Observed result |
|---|---|
| Enter on trigger | Opens; search input receives focus |
| Tab from search | Focus moves to an option button |
| Shift+Tab | Focus returns to search |
| Escape from search with results | Closes; focus returns to trigger |
| ArrowDown + Enter on the filtered synthetic option | Correct native category value; closes, but focus falls to BODY |
| Escape with zero matches | FAIL: remains expanded, focus stays in search |

The latter two behaviors are documented bounded additions to the proposed popup scope, not fixes already performed. Keyboard selection was not saved to DB. Existing Russian search/count/footer helper strings on AZ/EN were observed and left outside this implementation proposal.

## Cause, dependency and impact

`static/admin/css/pages/kidsmap_place_form.css` sets `.km-pf-picker-dropdown` to absolute `left:0`, width 100%, **min-width 320px**. The field is narrower and inset by 53 px at 360; its minimum width causes the measured 13 px overflow. Search flex sizing and nowrap/ellipsis option text must be considered when shrinking the popup.

`static/admin/js/kidsmap_place_form.js:initTaxonomyDropdownPickers/buildDropdown` generates both category and subcategory controls. The Escape branch is below an early return for an empty item list; successful selection closes without restoring trigger focus. The active `change_form.html` loads these assets. `section_basics.html` supplies category/subcategory fields, and `place_taxonomy_config.py` derives labels/IDs from server form querysets. Proposed changes preserve the hidden native select and its change event.

Codebase Memory root/status and coverage were checked before source investigation. Index was ready, but cited paths returned `metadata_changed` / `coverage_unavailable`; a guessed `section_category.html` path was missing, and source discovery identified the actual `section_basics.html`. Graph search was narrowed to the picker and callers, then confirmed directly. No graph cache was exported.

P2 remains confirmed on LOCAL HEAD in a real browser. No server business-rule/schema/ACL change is needed. Shared picker behavior requires subcategory regression coverage.

## Harness limitations and exact execution

The first matrix run used a single-threaded Django development server and recorded **276 local request failures / 13 page errors**. It is an environment failure and is excluded from acceptance. [Initial measurements](browser-matrix-1.json) and `screenshots/open-*` remain as diagnostics. Only the owned server was restarted with threading enabled; the effective run has a separate filename set, verified CSS and zero local failures. No application CSS/JS was injected or patched for either run.

The first keyboard CLI call returned early on an unsaved-change dialog, so no returned result was accepted. The repeated check used a new owned tab per locale and discarded its unsaved synthetic choice on close; it produced complete focus results. CLI may exit 0 while reporting a tool error/modal, so evidence parsing and behavioral assertions are separate.

- Preparation: `.venv/Scripts/python.exe docs/qa/place-qa05-plan-2026-10-10/prepare.py` — exit 0, including isolated migrations/seed.
- Browser matrix/keyboard: `pw.py run-code --filename` with the absolute [matrix script](browser-matrix.js) and [keyboard script](browser-keyboard.js) — native exit 0; raw argv/results in the ledger. Effective assertions are RED because the application is unchanged.
- Exact native Docker/Git/Python commands: [command ledger](command-ledger.jsonl). Exact Playwright commands and setup failures: [browser ledger](browser-command-ledger.jsonl).
- Own server start: `.venv/Scripts/python.exe docs/qa/place-qa05-plan-2026-10-10/runtime.py serve`; final threaded run redirected only to `.tmp/place-qa05-plan-20261010/server.log`. Both owned instances were stopped by verified PID/script identity; the first process returned exit 1 after intentional termination. This is not an application test failure.
- [Assertions](assert_baseline.py), [assertion results](baseline-assertions.json) and [final verification](plan-verification.json) distinguish behavioral RED from successful evidence recording. Assertion command `.venv/Scripts/python.exe docs/qa/place-qa05-plan-2026-10-10/assert_baseline.py` returned exit 1: 36 checks, 27 PASS, 9 FAIL (3 geometry and 6 keyboard). Long-label clipping was separately observed in all eighteen geometry cases.
- Final command `.venv/Scripts/python.exe docs/qa/place-qa05-plan-2026-10-10/verify_plan.py` returned exit 0: documents/evidence verified, application and all recorded input hashes unchanged, own browser/server closed and own PostgreSQL stopped without removal. Both intentionally stopped server processes returned exit 1. The final running-container list additionally contains `kidsmap-module05-20261010-r1` on 55436; this task did not create or change it. Initial foreign stands remain running.

## Plan and NOT RUN

[Implementation plan awaiting approval](../../superpowers/plans/2026-10-10-place-qa05-category-popup.md): mobile popup sizing, full label wrapping, input shrink, two bounded keyboard repairs and asset version updates; fresh save/reload and targeted existing regressions after approval. No overall admin redesign or changes to other findings.

NOT RUN: application implementation, post-fix checks, admin save/reload and DB persistence of a changed category, restricted moderator ACL, subcategory browser matrix, resize while open, keyboard focus-on-option Escape, real mobile device/virtual keyboard, other browsers, complete backend suite, external integrations and production. The fixture migration/seed is not a save/reload regression result.
