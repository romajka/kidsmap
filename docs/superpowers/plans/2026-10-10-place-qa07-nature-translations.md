# PLACE-QA-07 — Nature choice translations implementation plan

> Awaiting explicit user approval for this scope. One sequential executor. Apply systematic-debugging, writing-plans, test-driven-development, playwright and verification-before-completion. No commit/push/deploy. Other finding plans remain separate and unapproved.

**Goal:** Владелец видит правильные варианты типа места на RU/AZ/EN; отправленные и сохранённые значения остаются `business` и `public_space`.

**Architecture:** Добавить два отсутствующих gettext msgid в AZ/EN PO. Собрать текущие RU/AZ/EN каталоги установленным GNU msgfmt в новый изолированный каталог, подключить его через настройки собственного QA-стенда и запустить свежий Django-процесс. Проверить реальные form choices и сохранённый revision payload. Формы, модели, enum, ACL и publication service не требуют изменений.

**Spec:** [PLACE-QA-07](../../qa/module01-2026-10-09-r2/findings/PLACE-QA-07.md). [Fresh evidence](../../qa/place-qa07-plan-2026-10-10/REPORT.md).

## Snapshot and verified baseline

Actual checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, `active_run: NONE`. Incoming QA register/module directories, earlier plans and foreign stands must be preserved. PRODUCTION: UNKNOWN, not accessed.

`src/catalog/forms.py:OwnerPlaceEditForm.nature` declares lazy gettext choices. `src/catalog/models/catalog_structure.py:PlaceNature` uses the same two msgid and enum values. `owner_place_edit` → `OwnerPlacesController.build_edit_form_context` → form → permanent-place template → generic field include renders the actual select. `OwnerPlaceEditForm.__init__` prefers candidate nature from revision; `clean()` keeps the machine value. `Place.nature` and its approval pair have DB constraints.

All six exact source keys are absent from current RU/AZ/EN PO and MO. RU fallback is correct; four AZ/EN translations are missing in source. Rebuilding unchanged PO cannot provide them. Fresh baseline browser: 3 locales × 5 widths × initial/reload, 60 option-label checks: 20 PASS / 40 FAIL; enum values correct in every state. Keyboard selection of `public_space` works and displays Russian text in AZ/EN. Two existing lifecycle tests pass.

## Exact translations and scope

| msgid | RU (unchanged fallback) | AZ new msgstr | EN new msgstr |
|---|---|---|---|
| `Бизнес` | `Бизнес` | `Biznes` | `Business` |
| `Общественное место` | `Общественное место` | `İctimai məkan` | `Public space` |

| Allowed file/path | Change |
|---|---|
| `locale/az/LC_MESSAGES/django.po` | Two non-fuzzy singular entries with accurate source references |
| `locale/en/LC_MESSAGES/django.po` | Same two entries in English |
| `src/catalog/testcases/test_task33_place_nature_localization.py` (new) | Runtime labels, unchanged enum values and owner revision save/reload contracts |
| `docs/qa/place-qa07-fix-2026-10-10/` (new) | Isolated settings/launcher, commands, hashes, browser evidence and report |
| `.tmp/place-qa07-fix-20261010/` (ignored, new) | PO snapshots/MO outputs, media/private-media and synthetic browser session |

No RU PO, form/model/template/JS/CSS, migration, shared MO, Docker/CI/release changes. Do not run broad `makemessages` or change unrelated PO entries/headers. Gettext keys are shared: `Бизнес` also labels organization relationship choices in model source. Its translation is the same general concept; the catalogue change naturally applies wherever that exact msgid is used. Do not introduce a new context or rewrite another screen under this scope.

## Task 1: Preserve snapshot and add meaningful RED regression

- [ ] Recheck HEAD/WORKTREE/active_run, source hashes, prior plans and foreign resources. Record scope approval and create fresh fix evidence/scratch. Keep planning evidence immutable.
- [ ] Add tests before PO edits. In `translation.override('ru'/'az'/'en')`, materialize the actual lazy form choices and `PlaceNature` labels; assert the table above and exact ordered values `business`, `public_space`.
- [ ] Prove both machine values pass the actual ChoiceField validation in all locales, while translated display strings (`Biznes`, `İctimai məkan`, `Business`, `Public space`) are rejected as submitted values. Do not derive server values from translated labels.
- [ ] Add owner endpoint tests using ordinary synthetic users, editable draft fixtures and normal tokens/source versions: save each nature through the actual form; assert candidate revision payload contains the enum string, live nature/approval facts stay unchanged, then GET reload shows the candidate selected. Preserve unrelated name/address/schedule/price fields. Cover one non-owner request to prove unchanged object ACL without broadening access.
- [ ] Run the new tests against byte-identical copies of current MO on the dedicated test DB; retain native exit and expected four missing-label failures. Do not stub gettext or modify expected labels to obtain green.

Use an allowlisted runtime like this audit's `runtime.py`, `DJANGO_TESTING=1`, own `qa07_fix_settings` and `LOCALE_PATHS`; no inherited `.env` or service credentials. Concrete test invocation through that wrapper:

```text
.venv/Scripts/python.exe docs/qa/place-qa07-fix-2026-10-10/runtime.py test catalog.testcases.test_task33_place_nature_localization
```

## Task 2: Add only the source entries and compile owned catalogues

- [ ] Add two entries to each AZ/EN PO, non-fuzzy, no duplicate or obsolete msgid; preserve encoding/newlines and all other entries. Verify the exact diff is only four translations plus their references.
- [ ] Recheck installed WSL GNU gettext identity (audit found `msgfmt` 0.21). Freeze current RU/AZ/EN PO bytes and hashes in a new own scratch directory; never copy shared old MO into the corrected build. Source hashes must match before/after capture.
- [ ] Compile each frozen PO with GNU msgfmt `--check-format --statistics --endianness=little`, no `--use-fuzzy`, into the owned locale root. Use subprocess argv and `wslpath -u` for Windows paths. Example for AZ:

```text
wsl.exe --exec msgfmt --check-format --statistics --endianness=little -o /mnt/c/kidsmap/.tmp/place-qa07-fix-20261010/locale/az/LC_MESSAGES/django.mo /mnt/c/kidsmap/.tmp/place-qa07-fix-20261010/source/az/LC_MESSAGES/django.po
```

- [ ] Record original/current PO hashes, frozen PO and generated MO hashes, compiler/version/options/exits; decode outputs with `GNUTranslations` and compare the six targeted lookups. If any project catalogue fails compilation, retain diagnostics and report the blocker; do not edit other translations or suppress errors.
- [ ] The stand uses only the validated own locale directory and starts as a fresh process. Never recompile shared `locale/**/*.mo`, alter another process's translation cache or run release scripts.

The [PLACE-QA-06 plan](2026-10-10-place-qa06-isolated-locales.md) proposes a reusable build/verify helper and remains separately unapproved. PLACE-QA-07 may use that helper if it is subsequently approved and verified. It can also perform the explicit isolated GNU build above within this scope; it does not implement the QA06 helper or claim QA06 resolved.

## Task 3: Isolated backend GREEN and real browser persistence

- [ ] Create a new own PostgreSQL/DB/cache/email/media/private-media/browser namespace, ordinary synthetic owner and editable draft places. Suggested unused-at-implementation-check ports: DB 55445, HTTP 8824; verify availability and container identity first. Use the local PostgreSQL 17 image with `--pull=never` and no foreign DB.
- [ ] Run new tests with corrected catalogue plus the two audited lifecycle checks (`test_edit_displays_candidate_nature_and_saved_gallery_without_changing_live`, `test_public_space_can_submit_without_organization_photo_coordinates_or_contact`). Keep assertion expectations fixed. Run Django system checks and PO format validation; record native command/exit/counts.
- [ ] In real Chromium, RU/AZ/EN ×390/768/1024/1280/1440, inspect both actual options' display text and submitted values, HTML language, focus/keyboard, local network/console and horizontal overflow. Screenshot each choice visibly selected, with no DOM/style/text patches.
- [ ] For each locale and each enum value, save a valid synthetic draft through the owner UI, require a successful normal response, reload and verify the same selected value and translated label. Read back the same place's revision payload and distinguish it from live approved nature. Verify unrelated fields unchanged; do not direct-write DB to manufacture a successful save.
- [ ] Keep blocked external Leaflet/Google transport explicit; these checks establish local owner form behavior, not provider integration. Record any unrelated validation/baseline issue separately. Do not fix PLACE-QA-01–06 or other screens to complete this finding.

## Task 4: Final evidence and handoff

- [ ] Save native commands/exits, RED/GREEN results, PO/MO/runtime-path hashes, screenshots, browser version and explicit NOT RUN scope. Confirm corrected strings actually come from the new catalogue loaded by the fresh process.
- [ ] Recheck exact four-entry PO diff, unchanged enum/form/model/ACL/lifecycle sources, unchanged shared MO hashes, prior plans, active_run and foreign resources. Keep generated binaries and session secrets in ignored scratch.
- [ ] Close only this fix run's browser/server/container using recorded identities; retain evidence. Mark PLACE-QA-07 fixed only after source entries, compiled/runtime label checks and rendered save/reload pass. Production and other finding statuses remain UNKNOWN/pending as applicable.
