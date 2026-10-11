# PLACE-QA-02 — Provider-independent owner map controls implementation plan

> **For agentic workers:** Execute task-by-task only after user approval of this scope. Use available `test-driven-development`, `fixing-accessibility` and `verification-before-completion` skills. One sequential executor; no commit/push/deploy. This does not authorize PLACE-QA-01 or any other finding.

**Goal:** Очистка ручных координат и обратная связь geolocation работают в continuous-редакторе места независимо от загрузки SDK карты.

**Architecture:** Инициализировать контроллер полей/кнопок для `[data-permanent-map]` до выбора провайдера. Google/Leaflet подключаются к уже работающим контролам без повторного назначения обработчиков; placeholder не считается готовым SDK. Сохранить существующий `km:map-change` → location resolution → server draft/save contract.

**Tech Stack:** Existing vanilla JS, Django templates and localized `ui_copy`, node:test/jsdom, isolated PostgreSQL QA and Chromium.

**Spec:** [PLACE-QA-02](../../qa/module01-2026-10-09-r2/findings/PLACE-QA-02.md). [Fresh planning evidence](../../qa/place-qa02-plan-2026-10-10/REPORT.md).

## Authorization and snapshot

- PLAN / AWAITING USER SCOPE APPROVAL. Application code is unchanged.
- Checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, journal `active_run: NONE`.
- Preserve modified `docs/qa/module-acceptance-prompts.md` and incoming untracked module01-r1/r2, module02-r1, module03-r1, module04-r1 QA directories. Preserve PLACE-QA-01 plan/evidence and all running stands.
- A fresh isolated DOM probe against current JS produced 5 expected failures, exit 1: clear with unavailable provider, clear with configured-but-missing Google, unsupported geolocation, denied geolocation, late Leaflet attachment after placeholder. This is not browser or save/reload evidence.

## Global constraints

- Only PLACE-QA-02. No production credentials, external integrations, commit/push/deploy, cleanup or changes to unrelated screens.
- New local stand: `DJANGO_TESTING=1`, separate DB/test DB, LocMem cache/mail, media/private-media roots and browser profile; synthetic records only. Do not import checkout `.env` or reuse historical QA DBs.
- Frontend never substitutes blank/missing/invalid coordinates with `0/0` or the map's default center. A real supplied zero is not a missing-value sentinel: server geography rules still decide acceptance.
- Preserve server validation, geographic coverage, ACL, revision/publication and draft contracts. Do not change `location_assignment.py`, `location_resolution.js`, models or migrations.
- The JS is also used by legacy owner/event forms. Activate the new control orchestration only for `[data-permanent-map]`; retain legacy initialization/binding behavior and smoke-test it.
- Do not add a dependency or fetch an external map SDK for QA. Local provider doubles and browser geolocation overrides must be labeled as simulations, never live-provider success.

## Verified source and dependencies

| Source | Finding / constraint |
|---|---|
| `static/js/owner_place_map_picker.js:228` | `bindLocateButton` handles unsupported/error only after a provider initializer calls it; no in-progress status |
| Same file, `initLeafletMapPicker` / `initGoogleMapPicker` | Clear, locate and manual input bindings live inside provider setup |
| Same file, `initMapPicker:455` | Unavailable branch disables search, sets `mapInitialized=1`, and binds neither action |
| `src/catalog/templates/pages/includes/permanent_place_map.html` | Manual inputs, clear/locate controls and labels; status lacks a live region; failure copy assumes a working map |
| `src/catalog/templates/pages/permanent_place_form.html:21` | Owns script loading/cache version and Google callback; Leaflet script tag can be identified explicitly for load retry |
| `static/js/location_resolution.js:113` | Consumes `km:map-change`; clears stale derived geography and rejects stale lookup responses |
| `static/js/owner_place_continuous.js:262` | Same event participates in dirty state, local draft and server autosave |
| `src/catalog/services/location_assignment.py:101` | Server owns empty/partial/outside-coverage and region/district validation; frontend must not bypass it |

Clearing coordinates may invalidate derived city/district via the existing resolver. “Preserve other fields” means title, description, address, contacts, pricing, schedule and media; do not freeze stale derived geography against the current contract.

## Allowed files

| File | Change |
|---|---|
| `static/js/owner_place_map_picker.js` | Permanent-map control initialization, renderer attachment/retry, async request invalidation; preserve legacy branch |
| `src/catalog/templates/pages/includes/permanent_place_map.html` | Localized geolocation messages and accessible status |
| `src/catalog/services/permanent_place_wizard.py` | New RU/AZ/EN status-copy keys only |
| `src/catalog/templates/pages/permanent_place_form.html` | Map script cache version and a marker on the Leaflet SDK script |
| `scripts/test_owner_place_map_picker.cjs` (new) | Focused JS regression/adapter tests, extending the audit fixture |
| `src/catalog/testcases/test_task33_place_continuous.py` | Localized fallback/status markup checks only |
| `docs/qa/place-qa02-fix-2026-10-10/` (new) | QA harness, exact command/exit ledger, report, screenshots, sanitized evidence |
| `.tmp/place-qa02-fix-20261010/` (ignored, new) | Disposable fixture media/private-media, passwords/cookies/raw diagnostics |

No CSS or application backend mutations are currently needed. If fresh UI save/reload reveals a separate backend failure, retain evidence and request an explicit scope change rather than fold it into this fix.

## Task 1: Fresh baseline and regression tests

- [ ] Recheck HEAD, worktree, active_run and free ports. Record hash manifests for incoming work and affected application files. Claim only a new run; leave previous stands and plans intact.
- [ ] Create a new PostgreSQL instance on loopback 55436 and HTTP 8816 if still free. Existing Docker is accessible through WSL. Use this command only after approval, with a new unique suffix if the name/port is occupied:

```powershell
wsl.exe --exec docker run -d --name placeqa02-20261010-pg --publish 127.0.0.1:55436:5432 --env POSTGRES_DB=placeqa02 --env POSTGRES_USER=placeqa02 --env POSTGRES_HOST_AUTH_METHOD=trust postgres:17
```

- [ ] Create reviewed `run.py` / `qa_settings.py` in the new evidence directory using the established isolation pattern from module01-r2, with DB `placeqa02` / test DB `test_placeqa02`. Clear inherited service environment before Django loads, assert testing/cache/mail/media/DB isolation, and block external socket/browser transport. Do not run the historical launcher. Log actual settings as booleans/QA resource names, never credential values.
- [ ] With a fresh synthetic owner, create a place through UI. Enter 40.4093 / 49.8671 with SDK blocked; perform clear and locate. Capture current failure and saved values. This is the required rendered baseline and does not replace the existing DOM probe.
- [ ] Add `scripts/test_owner_place_map_picker.cjs`, reusing the source-evaluating fixture from `docs/qa/place-qa02-plan-2026-10-10/baseline-map-controls.cjs`. Put localization strings in fixture data attributes and assert externally observable outcomes, not private helper names. Retain the two clear failures, unsupported/denied failures and late-attachment failure as RED tests.
- [ ] Extend regression coverage with the cases below, including the shared resolver integration. Existing resolver tests remain unchanged.

| Scenario | Required assertion |
|---|---|
| Missing Google/Leaflet and explicit unavailable | Clear sets both values to `''`, clears badge, shows empty status and emits exactly one `km:map-change` |
| Initial empty fields | No default-center or zero coordinates written; no initial dirty notification |
| No geolocation API | Localized unsupported status; original point and other fields unchanged |
| Permission denied / unavailable / timeout / synchronous throw | Loading then applicable failure text; original coordinates unchanged; control recovers |
| Successful geolocation, no SDK | Finite supplied point fills inputs, status changes and one change event reaches resolver |
| Nonfinite/out-of-range geolocation payload | No point replacement, no fallback 0/0, visible error |
| Locate pending → clear / manual edit / second locate | Old success/error callbacks cannot undo the newer action |
| Manual edits with and without SDK | Current inputs remain authoritative; marker sync and notification do not overwrite unrelated fields |
| Repeated init/refresh callbacks | One action → one request/event; no duplicate handlers or map instances |
| Late Google / late Leaflet / Google-after-Leaflet fallback | At most one renderer attaches; it reads current fields; cleared point is not resurrected |
| Clear while server location lookup pending | Existing resolver cancels/ignores old response; stale district does not reappear |
| Legacy event/owner roots | Existing provider-backed clear/locate and optional-map behavior retained |

Example observable assertions, inside the new fixture-based tests:

```javascript
f.click('clear');
assert.equal(f.input('lat').value, '');
assert.equal(f.input('lng').value, '');
assert.equal(f.changes(), 1);
assert.equal(f.root.closest('form').elements.address.value, 'Synthetic address');
```

The fixture APIs are defined in the saved audit script; extend that fixture to return captured geolocation callbacks and renderer counters for race/idempotence cases.

```powershell
$env:DJANGO_TESTING = '1'
$env:KIDSMAP_JSDOM = 'C:\kidsmap\.tmp\phone-dom\node_modules\jsdom'
node --test scripts/test_owner_place_map_picker.cjs
```

Expected RED: intended behavior assertions fail against current app source; do not reinterpret environment exceptions as a successful reproduction.

## Task 2: Bind permanent-map controls before SDK initialization

- [ ] Add an idempotent `ensurePermanentControls(root)` before provider dispatch. It uses `buildSharedState(root)` once per permanent root and owns clear/locate/manual-change listeners. Keep provider initialization state separate from control initialization.
- [ ] Use a small renderer adapter with signatures `setPoint(lat, lng, options)` and `clearPoint()`. Before attachment, controls update inputs/status/badge and emit the existing event. After attachment, controls delegate to the renderer's existing methods, so each action still emits only one event. Existing provider listeners are installed only for non-permanent roots.
- [ ] Clear must increment the current location-request generation before clearing. A geolocation callback applies only when both its generation and the input snapshot are still current; manual editing/clear/another locate invalidates it. Successful SDK attachment alone must not invalidate or replay user data.

Required value guard before accepting a browser geolocation result:

```javascript
const valid = typeof lat === 'number' && typeof lng === 'number'
  && Number.isFinite(lat) && Number.isFinite(lng)
  && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
```

This is numeric validity only. Keep geographic coverage checks on the server.

- [ ] Set visible in-progress text before `getCurrentPosition`. Preserve coordinates on unsupported/denied/timeout/error, including synchronous exceptions. Keep the current 10-second request timeout. Avoid stealing focus; use status text and `aria-busy` for progress.
- [ ] For permanent roots, render unavailable placeholder without setting `mapInitialized=1`. Disable only provider search, not clear/locate. Use `textContent` when creating placeholder text. Missing Google with no Leaflet after the current fallback wait must show the same explanation.
- [ ] Google callback, known Leaflet script load/error, and `kidsMapRefreshOwnerMapPickers` retry attachment. Mark the template's Leaflet script with `data-owner-map-sdk="leaflet"` so retry is bounded to that loader. No unbounded polling or new provider requests.
- [ ] When a provider attaches, remove placeholder, restore search only if supported, and initialize the renderer from the current input values silently. Keep first successful renderer; later callbacks do not create another map or duplicate clear/locate handlers. A failed constructor leaves the independent controls usable.

## Task 3: Copy, accessibility and GREEN checks

- [ ] Add exact strings to `permanent_place_wizard.ui_copy()` and expose them as data attributes only in the permanent map include:

| Key | RU | AZ | EN |
|---|---|---|---|
| `map_locating` | Определяем геопозицию… | Məkanınız müəyyən edilir… | Detecting your location… |
| `map_locate_error` | Не удалось определить геопозицию. Введите координаты вручную. | Məkanınızı müəyyən etmək olmadı. Koordinatları əl ilə daxil edin. | Could not detect your location. Enter coordinates manually. |
| `map_locate_unsupported` | Геолокация недоступна в этом браузере. Введите координаты вручную. | Bu brauzerdə geolokasiya əlçatan deyil. Koordinatları əl ilə daxil edin. | Geolocation is unavailable in this browser. Enter coordinates manually. |
| `map_locate_denied` | Доступ к геолокации запрещён. Разрешите доступ или введите координаты вручную. | Geolokasiyaya girişə icazə verilmir. İcazə verin və ya koordinatları əl ilə daxil edin. | Location access was denied. Allow access or enter coordinates manually. |
| `map_locate_timeout` | Время ожидания геопозиции истекло. Повторите попытку или введите координаты вручную. | Məkanın müəyyən edilməsi üçün gözləmə vaxtı bitdi. Yenidən cəhd edin və ya koordinatları əl ilə daxil edin. | Location request timed out. Try again or enter coordinates manually. |

Use the existing `t(ru, az, en)` helper; no global `.po/.mo` rebuild. Existing `map_unavailable` already explains manual entry.

- [ ] On `[data-map-status]`, add `role="status" aria-live="polite" aria-atomic="true"`. Preserve native buttons, keyboard operation and focus styles. Replace map-only recovery instructions with the above manual-entry copy.
- [ ] Bump only `owner_place_map_picker.js` query version in `permanent_place_form.html` to `20261010_place_qa02`. Do not overwrite a CSS-version change from an independently approved PLACE-QA-01.
- [ ] Add a locale-loop test to `ContinuousPlaceFormTests` using `translation.override(locale)` and the owner edit GET: verify exact status data text, available clear/locate buttons and the live-region attributes in RU/AZ/EN. No backend rule/assertion weakening.
- [ ] Run the following through the isolated environment and capture native exit codes:

```powershell
node --check static/js/owner_place_map_picker.js
node --test scripts/test_owner_place_map_picker.cjs scripts/test_location_resolution.cjs
.venv/Scripts/python.exe docs/qa/place-qa02-fix-2026-10-10/run.py test catalog.testcases.test_task33_place_continuous catalog.testcases.test_location_resolution catalog.testcases.test_location_assignment
.venv/Scripts/python.exe docs/qa/place-qa02-fix-2026-10-10/run.py check
git diff --check
```

Retain initial RED and final GREEN evidence. Classify any other failure using a fresh baseline; do not fix adjacent findings automatically.

## Task 4: Real browser persistence and handoff

- [ ] On the new isolated Django stand, with SDK transport blocked, test manual point → explicit save → reload → clear → explicit save → reload/new login. Assert both coordinate inputs remain empty, never `0` or center defaults. Inspect the effective stored candidate/live state according to the existing publication lifecycle, not only DOM or localStorage.
- [ ] Keep distinguishable title/address/description/contact/pricing/schedule values and fixture media; compare them before/after. Record any expected resolver-derived city/district changes separately.
- [ ] Verify geolocation unsupported, denied, timeout and successful response with explicit browser fixtures; verify no old geolocation callback restores a cleared/manual-edited point. No real OS location or live provider integration is claimed.
- [ ] Delay synthetic SDK attachment after initial manual edits/clear; verify single initialization, correct current coordinates and stable buttons. Cover both Google and Leaflet adapter contracts, plus missing configured SDK and total unavailability.
- [ ] Test server geography with partial coordinates, invalid numbers and an outside-coverage fixture. Assert existing draft/submission verdicts and ACL stay intact; never bypass validation to make browser checks pass.
- [ ] Matrix: RU/AZ/EN × 390/768/1024/1280/1440 for unavailable state and visible geolocation feedback. Full save/reload and late-SDK flows at 390 and 1440; inspect keyboard/focus, overflow, console and network. Include legacy event-map smoke without changing that screen.
- [ ] Save `REPORT.md`, command ledger, source/stand snapshots, isolation booleans, DOM/backend/browser results, sanitized stored-coordinate readback, screenshot manifest and preservation verification under the new evidence directory. Keep failed attempts and precise limitations.

Acceptance: clear and feedback work without SDK, late SDK does not regress controls, saved empty coordinates survive reload, other user fields remain intact, scoped regression checks pass. NOT RUN must explicitly include production, real external integrations and the full unrelated application suite, plus any incomplete acceptance cell. PLACE-QA-02 remains OPEN until these gates pass.
