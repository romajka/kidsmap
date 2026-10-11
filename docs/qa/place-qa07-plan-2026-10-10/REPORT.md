# PLACE-QA-07 — Nature choice source gap, fresh baseline and proposed scope

2026-10-10, Asia/Baku. AUDIT / PLAN. One executor `/root`, sequential canonical orchestrator/frontend-reviewer/browser-qa responsibilities; no independent role execution claimed. Scope: this finding's source/rendered baseline and approval-ready plan.

## Snapshot and isolation

Actual `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, `active_run: NONE`. Incoming modified QA register, module evidence and earlier plans preserved. [Snapshot](snapshot.json). PRODUCTION: UNKNOWN, not accessed.

Fresh own container `kidsmap-placeqa07-plan-20261010`, local PostgreSQL 17 image `--pull=never`, DB `placeqa07_plan` and test DB `test_placeqa07_plan`, loopback DB 55444 / HTTP 8823. Ordinary synthetic owner (not staff), directly owned draft place. Dedicated LocMem cache/email, media/private-media; allowlisted process environment, `DJANGO_TESTING=1`, no `.env` or production credentials. Backend transport restricted to own PostgreSQL; browser external requests blocked. [Isolation](isolation.json), [settings](qa07_settings.py), [runtime](runtime.py).

Current RU/AZ/EN PO/MO pairs copied byte-for-byte into ignored own scratch, `LOCALE_PATHS` points only to those frozen copies. [Hash manifest](frozen-catalog-manifest.json). No PO or shared MO modification; no compilation.

## Source and impact

`src/catalog/forms.py:1042–1044` declares `nature` choices with lazy gettext and values `business` / `public_space`. `src/catalog/models/catalog_structure.py:19–21` declares the same `PlaceNature` values/labels. Owner view/controller constructs the form; `owner_place_edit.html` extends `permanent_place_form.html`, includes continuous form and generic `permanent_place_field.html` for the rendered select.

Exact singular non-context msgid `Бизнес` and `Общественное место` are absent from all three project PO/MO pairs. RU identity fallback is correct. **AZ/EN source gap: 4 missing translations**, distinct from stale generated assets in PLACE-QA-06. [Read-only diagnostic](inspect_catalogs.py), [exact presence/lookup/hash results](catalog-comparison.json): six lookups, 2 PASS / 4 FAIL, native exit 1. The proposed labels are AZ `Biznes` / `İctimai məkan`, EN `Business` / `Public space`.

The form initially prefers revision `payload['nature']`; cleaned nature remains an enum string. Live Place nature has approval-pair constraints. Translation-only correction requires no migration or business-rule change. The exact `Бизнес` key is also used for organization relationship labels in model source, so its general translation is shared there; no separate screen rewrite is proposed.

Codebase Memory root/status checked first: project `C-kidsmap`, root `C:/kidsmap`, ready. Graph found OwnerPlaceEditForm and its controller consumer. Coverage returned metadata changes/unavailable records and partial PO/template parsing; actual form/model/controller/templates and exact PO text were reviewed. No negative claim rests on graph absence, and no graph cache was copied into evidence.

## Rendered and backend baseline

Playwright Chromium headless shell **153.0.8010.12**, DPR 1. Actual URLs `http://127.0.0.1:8823/{ru,az,en}/account/places/1/edit/`. RU/AZ/EN ×390/768/1024/1280/1440 × initial/reload: **30 states, 60 option-label checks — 20 PASS / 40 FAIL**. Every selected-language HTML check and every enum-value pair passes; all AZ/EN options remain Russian on reload. No horizontal overflow, local resource failures or page errors. [Browser strings/ARIA/network/geometry](browser-baseline.json), [assertions](browser-assertions.json).

The 60 console messages are deliberately blocked external Leaflet CSS/JS requests from `unpkg.com`; no application console error was observed in this matrix. Provider integration is not tested. Native keyboard ArrowDown selects `public_space` in RU/AZ/EN; its visible AZ/EN label remains Russian. [Keyboard capture script](browser-option-evidence.js) and native results in [browser ledger](browser-command-ledger.jsonl). There was no explicit form submission in the browser; draft transport is confined to the synthetic local fixture.

33 screenshots: 30 initial/reload field captures and three keyboard-selected public-space captures. [Image hashes/dimensions](screenshots-manifest.json). Representative [AZ business after reload](screenshots/az-390-reload-nature.png), [EN business after reload](screenshots/en-1280-reload-nature.png), [AZ public space](screenshots/az-390-public-space-keyboard.png), [EN public space](screenshots/en-390-public-space-keyboard.png). Images inspected without style/DOM/text injection.

Two existing tests passed on the dedicated disposable test DB: candidate nature/gallery displayed without changing live, and public-space submission without organization/photo/coordinates/contact. Native exit **0**, 2 tests, no Django system-check issues. [Observed output](backend-baseline.txt); exact labels in runtime `checks` branch. This supports unchanged baseline lifecycle, not correctness of future translations.

## Recommendation and authorization

P3 remains justified: inconsistent choice labels do not block existing machine-value selection or the tested submission path. Correct only the four AZ/EN source entries, compile isolated catalogues, then verify runtime labels and actual owner save/reload with unchanged revision/live and ACL contracts. [Reviewable plan](../../superpowers/plans/2026-10-10-place-qa07-nature-translations.md).

PLACE-QA-06's reusable build helper is separately unapproved. This scope may use installed GNU msgfmt directly in owned scratch; no helper implementation or shared rebuild is included. Application implementation remains **NOT AUTHORIZED**, approval **PENDING**.

## Exact commands and limits

- `.venv/Scripts/python.exe docs/qa/place-qa07-plan-2026-10-10/bootstrap_audit.py` — exit 0, isolated harness and byte-identical baseline copies.
- `.venv/Scripts/python.exe docs/qa/place-qa07-plan-2026-10-10/inspect_catalogs.py` — exit 1, expected RED: 2/6 targeted lookup matches.
- `.venv/Scripts/python.exe docs/qa/place-qa07-plan-2026-10-10/prepare.py` — exit 0, own DB/migrations/synthetic owner/place/session. Browser session remains only in ignored scratch.
- `.venv/Scripts/python.exe docs/qa/place-qa07-plan-2026-10-10/runtime.py checks` — exit 0, 2 baseline lifecycle tests.
- `pw.py run-code --filename` for baseline and keyboard scripts — both native exit 0; exact argv/output in browser ledger.
- `.venv/Scripts/python.exe docs/qa/place-qa07-plan-2026-10-10/collect_browser_results.py` — exit 1, expected RED: 20/60 option matches.
- Owned server stopped using verified PID/script identity; stop command exit 0, server process exit 1 from intentional termination. Browser close exit 0.
- `.venv/Scripts/python.exe docs/qa/place-qa07-plan-2026-10-10/verify_plan.py` — exit 0, evidence/preservation/shutdown checks passed; translation assertions remain RED.
- [Final command ledger](command-ledger.jsonl), [preservation/shutdown verification](plan-verification.json).

Final preservation: all captured input hashes agree, including source PO/shared MO and six earlier plans; tracked application diff is empty. Owned browser/server/container stopped, container retained. Foreign running stand inventory equals the entry snapshot; every initial stand remains running.

NOT RUN: PO edits, corrected catalogue compilation/runtime checks, new regression tests, browser explicit save followed by reload/DB readback, complete backend suite, broader ACL matrix, other browsers/devices, provider integrations, Docker/CI/release and production. Browser reload was executed against baseline assets. Earlier finding approvals remain pending.
