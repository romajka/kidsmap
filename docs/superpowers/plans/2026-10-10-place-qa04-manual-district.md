# PLACE-QA-04 — Manual district availability implementation plan

> **For agentic workers:** Execute task-by-task only after user approval of this scope. Use `test-driven-development`, `systematic-debugging` and `verification-before-completion`. One sequential executor; no application edits during planning, no commit/push/deploy. This plan does not authorize PLACE-QA-01/02/03.

**Goal:** После очистки обеих координат владелец может выбрать Baku и район, сохранить их и восстановить после reload; доступность района соответствует текущему режиму ввода.

**Architecture:** Единый пересчёт доступности района в `location_resolution.js`, ограниченный continuous owner form. Ручной режим определяется двумя пустыми координатами; координатный режим сохраняет серверное разрешение географии. Восстановление черновика передаёт resolver начало/конец пакета изменений, чтобы промежуточные значения не стирали восстановленную географию.

**Tech Stack:** Existing vanilla JavaScript, Node 24.14.0 / jsdom, Django 6.0.2, Python 3.12.15, isolated PostgreSQL and real browser.

**Spec:** [PLACE-QA-04](../../qa/module01-2026-10-09-r2/findings/PLACE-QA-04.md). [Fresh evidence and limitations](../../qa/place-qa04-plan-2026-10-10/REPORT.md).

## Snapshot / authorization

- PLAN / AWAITING USER SCOPE APPROVAL. Application files match HEAD.
- Checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, shared journal `active_run: NONE`.
- Preserve incoming modified `docs/qa/module-acceptance-prompts.md`, untracked module01-r1/r2, module02-r1, module03-r1, module04-r1 directories, earlier finding plans/evidence and all foreign stands.
- Fresh DOM baseline: 9 tests, 4 PASS, 5 FAIL; existing resolver suite: 7 PASS. No browser or database save/reload was executed for this finding in planning.

## Global constraints

- Only PLACE-QA-04. No production access/credentials, external integrations, migrations, commit/push/deploy, or unrelated screen changes.
- Runtime tests require `DJANGO_TESTING=1`, separate DB/test DB/cache/media/private-media/email, synthetic actors and a separate browser profile; do not load `.env` or inherit service credentials.
- Preserve `clean_place_location`, `prepare_place_location`, server-owned region/district choices, ACL, revision lifecycle and publication validation. Both-empty coordinates and partial/invalid coordinates are different cases. Never substitute `0/0` for empty values.
- The clear-button defect is PLACE-QA-02, separately awaiting approval. Reproduce QA04 by clearing coordinate fields directly with their normal events; do not edit `owner_place_map_picker.js` under this scope.
- Shared resolver is also used by admin and legacy wizard. New manual-mode behavior and restore signals apply only to a form within `[data-place-mode="continuous"]`; existing consumers keep their behavior.

## Allowed files and responsibilities

| File | Change after approval |
|---|---|
| `static/js/location_resolution.js` | One district-state helper, region binding, bounded restore handling for continuous owner |
| `static/js/owner_place_continuous.js` | Bracket only `apply(saved)` field restoration with location restore events; preserve autosave/version/conflict logic |
| `src/catalog/templates/includes/location_resolution.html` | Update resolver asset version only |
| `src/catalog/templates/pages/permanent_place_form.html` | Update continuous editor asset version only |
| `scripts/test_location_resolution.cjs` | Manual-mode, restore, stale-response and non-continuous regression cases |
| `src/catalog/testcases/test_place_qa04_manual_location.py` (new) | Server validation and persisted manual geography regressions |
| `docs/qa/place-qa04-fix-2026-10-10/` (new) | Isolated harness, commands, report, screenshots and readback |
| `.tmp/place-qa04-fix-20261010/` (ignored, new) | Synthetic media/private-media, browser profile and local fixture credentials |

Read-only dependencies: `location_assignment.py`, `locations.py`, owner forms/views and existing continuous/location tests. No CSS, new interface copy or locale catalogue changes are needed.

## Task 1: Lock the behavior with regression tests

- [ ] Recheck HEAD/WORKTREE/active_run and source hashes. Record approved scope in the new evidence directory. Check stand ownership and available ports before creating anything.
- [ ] Extend the existing resolver suite using the synthetic fixture and explicit behavioral assertions from [audit baseline](../../qa/place-qa04-plan-2026-10-10/baseline-district.cjs). Keep the baseline evidence unchanged. Example acceptance sequence:

```javascript
point(f, '40.4093', '49.8671');
point(f, '', '');
region(f, 'baku');
assert.equal(f.form.elements.district.disabled, false);
f.form.elements.district.value = 'baku_yasamal';
assert.equal(new f.dom.window.FormData(f.form).get('district'), 'baku_yasamal');
region(f, 'sumgait');
assert.equal(f.form.elements.district.disabled, true);
assert.equal(f.form.elements.district.value, '');
region(f, 'baku');
assert.equal(f.form.elements.district.disabled, false);
```

`point`, `region` and `fixture` are defined in the linked audit fixture. Expand the fixture to include continuous restore events and a non-continuous variant; do not manufacture a browser PASS from jsdom.

- [ ] Add cases for initial saved Baku district, no region, whitespace-only coordinate values, latitude-only/longitude-only, invalid numbers/ranges, genuine numeric zero, resolved Baku/non-Baku and pending/unavailable responses. Validate actual `FormData` and unrelated address values, not just CSS/classes.
- [ ] Cover both restore field orders (coordinates before/after region and district), restore on top of a form with a different saved point, old response arriving during/after restore, and repeated boot. The three manual transitions and two restoration cases must be RED before changes; report each failed assertion.
- [ ] Run Node under an allowlisted environment with `DJANGO_TESTING=1` and `KIDSMAP_JSDOM=C:\kidsmap\.tmp\phone-dom\node_modules\jsdom`, using the audit recorder pattern. Native command: `C:\Program Files\nodejs\node.exe --test scripts/test_location_resolution.cjs`. Keep its actual exit code.
- [ ] Before Task 2, prepare the isolated stand described in Task 3 and capture browser RED: as a synthetic owner, enter a point, clear both coordinate inputs, select Baku and observe the disabled district. Save the fresh screenshot and control state before application edits. Do not reuse the historical module01 stand.

## Task 2: Implement one continuous-form state recalculation

- [ ] Detect the continuous form once at resolver initialization. Keep the existing `values()` behavior for all other consumers. Introduce one helper responsible for continuous `district.disabled`; avoid another competing writer in the editor script.
- [ ] Read raw coordinate strings before numeric conversion. The manual-mode predicate is exactly:

```javascript
const manualMode = lat.value.trim() === '' && lng.value.trim() === '';
```

- [ ] Apply the following contract on initial boot, manual region change, coordinate change, accepted resolver result and completed restore:

| Current state | District behavior |
|---|---|
| Both coordinates empty, region Baku | Enable; preserve a valid existing/restored district option |
| Both empty, other/empty region | Disable; clear a stale Baku district |
| One coordinate present or invalid pair | Do not unlock via manual region change; preserve existing server error/draft policy |
| Complete point awaiting resolution | Disable until current-point result is applied |
| Current-point result or valid existing override | Preserve existing server-driven geography/availability; manual region alone cannot authorize an unresolved point |
| Old response after clear or restore | Ignore; never overwrite the current manual region/district |

- [ ] Bind region changes directly to the helper, independently of `update()`'s unchanged-point early return. Keep `applying`, request serial, abort and point-equality guards. Programmatic changes must not create an event loop; dispatch a district change only when its value actually changes.
- [ ] Keep available options server-supplied. Do not add a client geographic map, trust new client metadata, change override permissions or invent a new publication-ready status. Existing translated labels, native disabled state and status live region remain in use.
- [ ] Bracket the existing assignment loop in `owner_place_continuous.js:apply(saved)` with form events `km:location-restore-start` and `km:location-restore-end`; the end event must run in `finally`. Preserve its existing field-change events for other components and the local `restoring` guard. Event dispatch shape:

```javascript
form.dispatchEvent(new CustomEvent('km:location-restore-start', {bubbles: true}));
try {
  // Existing apply(saved) field assignment/change loop, unchanged.
} finally {
  form.dispatchEvent(new CustomEvent('km:location-restore-end', {bubbles: true}));
}
```

On start, the continuous resolver invalidates pending work and suspends its own per-field reactions. On end, it reads the complete DOM tuple exactly once: preserve valid manual geography when both coordinates are empty; otherwise resolve the restored point under the existing coordinate policy. Other consumers do not listen to these events. Initial boot after an already-finished restore also reads the final tuple correctly.

- [ ] Bump both changed script asset versions at their existing template includes (suggested `20261010_place_qa04`) so a stale editor cannot omit events required by a fresh resolver. No template layout or copy changes.
- [ ] Run the expanded Node suite; require all new expectations plus the original 7 tests to pass. Keep non-continuous fixtures and existing override/network cases green without changing their assertions to mask failures.

## Task 3: Verify server contracts and real save/reload

- [ ] Create a dedicated local PostgreSQL stand using the already available `postgres:17-alpine`, never an implicit pull. Suggested container `kidsmap-placeqa04-fix-20261010`, DB `placeqa04_fix`, test DB `test_placeqa04_fix`, loopback port 55439 and HTTP 8818; recheck availability and choose another unused suffix if needed.
- [ ] Adapt the reviewed isolated settings/runner from `docs/qa/place-qa03-plan-2026-10-10/qa03_settings.py` and `run_tests.py` into this finding's new evidence directory. Use separate LocMem cache/email, media/private-media, allowlisted environment, no `.env`, external socket/browser-route blocking and synthetic records. Start background helpers hidden; track only owned PIDs/container IDs.
- [ ] In the new Django suite, use the existing `LocationForm` fixture contract and real database writes. Core persisted expectation:

```python
form = LocationForm(
    {'lat': '', 'lng': '', 'region': 'baku', 'district': 'baku_yasamal'},
    instance=Place(name='QA04 synthetic place', category=self.category,
                   status='draft', is_active=False),
)
self.assertTrue(form.is_valid(), form.errors)
place = form.save()
place.refresh_from_db()
self.assertIsNone(place.lat)
self.assertIsNone(place.lng)
self.assertEqual((place.city, place.district), ('baku', 'baku_yasamal'))
self.assertEqual(place.location_resolution_status, 'missing_coordinates')
```

Import `LocationForm` from `catalog.testcases.test_location_assignment`, `Place/Category` from `catalog.models`; create the synthetic EDU category in `setUpTestData`. Also test non-Baku canonical storage, incompatible district rejection, existing forged-district checks for a complete point, and partial/invalid coordinates with `draft=False`. Do not impose a new draft/publication policy through test expectations.

- [ ] Run through the isolated runner: `catalog.testcases.test_place_qa04_manual_location`, `catalog.testcases.test_location_assignment`, `catalog.testcases.test_location_resolution`, `catalog.testcases.test_task33_place_continuous`. Record the actual command, database identity without credentials, exit code and failures.
- [ ] Compare with Task 1's browser baseline. After changes, repeat as synthetic owner: input a point, clear both inputs, choose Baku and Yasamal, edit a title/address sentinel, save draft, wait for server acknowledgement, reload, logout/login and reopen. Check selected/enabled district, both coordinates empty, sent draft fields, persisted server state and unrelated fields.
- [ ] Repeat Baku → another region → Baku, empty/partial/invalid point and a pending resolver response delivered after clear. Exercise actual local and server draft restoration, including an existing place whose persisted point differs from the restored draft. Confirm invalid publication attempts receive existing server validation.
- [ ] Check RU/AZ/EN, keyboard access/focus and native disabled behavior. Render the affected form at 390/768/1024/1280/1440 widths; capture the target control and a saved/reloaded state. Smoke-check legacy wizard/admin on the isolated stand because the resolver file is shared.

## Task 4: Evidence and completion gate

- [ ] Save exact commands/native exit codes, versions, snapshot/source hashes, RED/GREEN logs, synthetic DB readback and screenshots in the new fix report. Record each omitted check as NOT RUN with its reason. A screenshot alone does not prove persistence; a Django client/jsdom result does not prove browser rendering.
- [ ] Review the final diff against this file allowlist, preserve foreign changes/stands and stop only helpers created by this run. No blanket cleanup, commits or deployment.
- [ ] Mark PLACE-QA-04 fixed only after state transitions, draft persistence/reload, server geography, original regressions and rendered browser gates pass. Other findings remain independently awaiting approval.
