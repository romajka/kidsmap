# SITE-QA-19: CatalogContentSettings string representation — Implementation Plan

> For agentic workers: execute inline, task by task, after explicit approval of this two-file scope. Current project authorization overrides generic skill commit/delegation suggestions. No subagent, commit, push or deployment is authorized.

**Goal:** Restore the existing hidden catalog-content editor by returning a real localized Python string from its model's `__str__`.

**Architecture:** Evaluate the existing lazy gettext value inside each `__str__` call. Keep the message identifier, current translations, admin registration, JSON fields and existing permission behavior. Add one focused regression module; no field/options/schema changes.

**Tech Stack:** Current isolated runtime Python3.12.15 / Django6.0.2, PostgreSQL17 QA fixture, current root RU/AZ/EN PO compiled to owned scratch, native Chromium through playwright-cli.

**Spec:** [Finding](../site-qa15-fix-2026-10-18-pc-r1/findings/SITE-QA-19.md), [fresh evidence](REPORT.md), [candidate hashes](candidate-manifest.json).

## Global constraints

- PLAN only until user approves this exact scope. Application files are unchanged in this package.
- Preserve all1031 source hashes,29prior packages/5861files, shared MO/.cbmignore, HEAD/branch/task33/index bytes/empty staging/active_run NONE and all entry foreign runtime identities/states.
- Preserve approved SITE01/SITE15/SITE06 behavior and module09 LOCAL closure. Module10 remains14OPEN; this plan does not close SITE19.
- All runtime work must use DJANGO_TESTING=1, environment cleared before Django import, separate owned normal/testDB/cache/media/private/email/locales and disabled external integrations. Production is not used.
- Do not normalize line endings, alter existing tests/assertions, change PO/JS/CSS/templates/routes/presets/fields/migrations, activate historical proxy apps, or repair other findings.
- Existing AZ/EN translations of the message are “Kataloqda yenilər” / “New in catalog”; preserve them. Their editorial quality is outside this crash fix.

## Task1: Establish an independent fix profile and reproduce RED

**Files:** create an independent fix evidence directory `docs/qa/site-qa19-fix-2026-10-18-pc-r1` and ignored scratch `.tmp/site19-pc-fix-r1`. Read this sealed PLAN; never rewrite it or relaunch its bootstrap.

**Interfaces:** consumes `source-entry.json`, `candidate-manifest.json`, `test_site19_candidate.py`, `bootstrap.py` and `runtime.py` as reference; produces a fresh source/preservation snapshot and exact RED command/result before application changes.

- [ ] Verify the PLAN artifact manifest and all source hashes; capture current document hashes after the PLAN appendices. Preserve this package in addition to its29 predecessors.
- [ ] Create a new owned profile only after absence checks: app `m10s19-fix-r1-app`, normalDB `m10s19_fix_r1`, RED testDB `test_m10s19_fix_r1_red`, GREEN testDB `test_m10s19_fix_r1_green`, loopback33540, cache `m10s19-fix-r1`, RAM media `/tmp/site19-pc-fix-r1-media` inside the new app's own tmpfs. Use existing verified QA PG/internal network, read-only repo bind and RW own scratch; never restart/reuse a previous app or its DB/media.
- [ ] Clear inherited environment before `django.setup`, assert all source/current-locale manifests and isolated settings as in this package. Compile current3PO to fresh owned locales. Precreate the exact absent RED testDB to avoid creation timeout; migrate through Django's test runner.
- [ ] Copy the exact candidate test bytes only into owned scratch, retaining module name `test_site19_candidate`. Execute against unchanged application:

```bash
docker exec m10s19-fix-r1-app python /mnt/c/kidsmap/.tmp/site19-pc-fix-r1/runtime.py test test_site19_candidate catalog.testcases.public.TestCatalogContentSettingsWiring
```

Expected current baseline:20methods,7failed candidate methods/28failure observations,0errors;13methods pass. Source remains1031. A different result requires investigation before apply, without weakened assertions.

## Task2: Apply the exact two-file candidate

**Files:** modify `src/catalog/models/site.py:784`; create `src/catalog/testcases/test_site_qa19_catalog_content.py` from the full candidate in this package.

**Interfaces:** `CatalogContentSettings.__str__(self)` returns `str`, with current language chosen at each call; no queries, writes, JSON normalization or state mutation. Existing proxy subclasses inherit this behavior without changing their Meta labels or registration.

- [ ] Recheck both candidate before hashes and empty staging. Check then apply the byte-preserving patch:

```bash
git apply --check docs/qa/site-qa19-recheck-2026-10-18-pc-r1/proposed.diff
git apply docs/qa/site-qa19-recheck-2026-10-18-pc-r1/proposed.diff
```

The only existing-code change is:

```python
    def __str__(self):
        return str(_("Контент каталога"))
```

Do not translate at import time or replace this expression with `self._meta.verbose_name`: the historical proxy overrides that label. Existing message identifier and per-call lazy translation are deliberately retained.

- [ ] Verify both exact after hashes from `candidate-manifest.json`, full AST diff limited to this return expression,1030other existing sources unchanged, one new regression module. Update only the new fix profile's source guard to1032 sources; rebuild/verify own current locales. No application assertion refinement is planned.

## Task3: Verify fresh GREEN and relevant regressions

**Files:** new fix package evidence only. The complete12-method test code is [candidate regression module](candidate/src/catalog/testcases/test_site_qa19_catalog_content.py); no placeholder implementation is required.

**Interfaces:** consumes exact applied bytes and fresh migration-backed GREEN DB; produces exact test counts/exit and current runtime/source evidence.

- [ ] Select the new fresh GREEN testDB before Django import, without flushing/reusing RED DB. Run:

```bash
docker exec m10s19-fix-r1-app python /mnt/c/kidsmap/.tmp/site19-pc-fix-r1/runtime.py test catalog.testcases.test_site_qa19_catalog_content catalog.testcases.public.TestCatalogContentSettingsWiring catalog.testcases.test_site_qa06_media_validation catalog.testcases.test_site_qa01_media_permissions catalog.testcases.test_site_qa15_settings_concurrency catalog.testcases.admin.TestSiteGalleryImageAdminMedia catalog.testcases.admin.TestAdminSidebarStructure catalog.testcases.test_public_section_switches
```

Expected105methods (12new+8content+85existing),0failures/0errors, exit0. A failure outside the changed representation must be classified and investigated; no unrelated application fix is authorized.

- [ ] Confirm unsaved/persisted real-string labels under AZ/RU/EN, same-instance language switching,0queries and no model writes; super/editor GET200, viewer readonly GET200, successful Unicode/nested JSON roundtrip and localized LogEntry, invalid JSON bound errors/no DB/log write, viewer/denied POST403, denied GET403, anonymous login redirect, hidden index and disabled add/delete, existing content getter semantics.
- [ ] Confirm no field/Meta AST change. No migration is expected or authorized. Verify Python compilation, template origin/current locale manifest, source/preservation manifests, patch reverse-check and native Windows `git diff --check`.

## Task4: Native editor acceptance and handoff

**Files:** new fix package native scripts/results/PNGs and report; append guide/MASTER only after verified outcome.

**Interfaces:** separate fresh BrowserContext per fictional actor; actual existing model admin URLs and local fixture state. No response stubs, model monkeypatches or forced hidden clicks.

- [ ] Repeat this package's36cells: super AZ/RU/EN at360/390/768/1024/1280/1440; editor/viewer/denied AZ/RU/EN at390/1440. Expected permitted GET200/editor visible or actual readonly values; denied403. Collect DOM/console/localHTTP/static404/geometry and PNGs. Verify JSON and admin-log no-write after GET.
- [ ] At desktop1440 for super/editor, use the real three textareas and visible `_continue`/`_save` buttons: valid nested/Unicode JSON edit → reload/readback equal; malformed JSON → visible bound error, unchanged DB/log and retained draft; retry → successful save. Use native Tab focus, actual labels/errors and screenshots in all3languages. Inspect the new accessible UI rather than claiming coverage from the former500 pages.
- [ ] At mobile, inspect textarea geometry, keyboard focus, service section and save-control visibility. If the existing SITE08 hidden sidebar prevents a native submit, record that blocker; do not force click or claim a native mobile save. A browser API POST may separately verify malformed-form server response/error rendering, explicitly marked API-driven, never counted as native submission. SITE08/SITE11 remain open.
- [ ] Reconcile all exact source/previous packages/runtime/refs/index/MO/document checks. Only with original500 resolved and acceptance evidence may SITE19 close LOCAL, reducing module10 from14 to13OPEN. Any newly reachable independent defect gets its own finding and count reconciliation, without automatic fixes.
- [ ] Seal new evidence/hashes, append guide/MASTER, report exact executed/not-run scope and retain owned runtimes. No commit/push/deploy, module11, full project/release or production claim.

## Self-review

Two application paths only; complete candidate code/diff and SHA supplied. RED demonstrates the same model return-type failure in Python, Django GET, validation render and successful-save logging. Existing permission/content controls pass. Candidate AST/apply checks pass but do not establish GREEN. Bound JSON errors, successful saves, keyboard/layout and native controls remain post-approval acceptance work. No independent review/delegation is claimed.
