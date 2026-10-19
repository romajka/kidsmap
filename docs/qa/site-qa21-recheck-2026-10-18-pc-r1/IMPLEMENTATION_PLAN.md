# SITE-QA-21 catalog editor column width — Implementation Plan

> For agentic workers: execute inline only after user approval of this one-file scope. No subagent/commit/push/deploy authorization. Preserve the sealed PLAN and all previous work.

**Goal:** Let the existing catalog JSON editor use its available Bootstrap column and keep its cards clear of the actions panel.

**Architecture:** Restore the `col-12` root class used by the installed Jazzmin change-form template, conditionally for `opts.model_name == 'catalogcontentsettings'` in the existing shared override. This uses existing Bootstrap flex/gutters and current KidsMap grid/tokens/max-width; it changes no CSS, fields, behavior or copy. Other model-name branches render the same root class as before.

**Tech Stack:** Existing Django6.0.2/Jazzmin/Bootstrap templates and native cached Chromium via playwright-cli; disposable PostgreSQL17 QA fixtures/current root3PO.

**Spec:** [SITE21 finding](../site-qa19-fix-2026-10-18-pc-r1/findings/SITE-QA-21.md), [fresh source proof](evidence/source-probe.json), [baseline/prototype measurements](evidence/prototype-assessment.json), [exact candidate](candidate-manifest.json).

## Global constraints

- Current mode PLAN; this candidate is NOT applied. Source1032 is unchanged. Actual-source GREEN is NOT RUN.
- Preserve31previous packages/6166files plus this completed PLAN, source hashes, shared MO/.cbmignore, HEAD/branch/task33/index bytes/empty staging/active_run NONE and foreign runtime identities/states. New fix profile must have its own normal/test DB/cache/media/private/email/compiled locales, environment cleared before Django import and DJANGO_TESTING=1; integrations disabled.
- Only one application file: `src/catalog/templates/admin/catalog/shared_settings_change_form.html`. Keep raw line endings outside the exact replacement. No CSS/JS/backend/model/migration/locale/permission/route/preset edits or proxy activation.
- SITE19/SITE01/SITE15/SITE06 and module09 LOCAL closures remain. SITE08 mobile hidden Save, SITE20 readonly Save, SITE11 translations and all other findings stay separate; no overflow hiding or forced hidden clicks.
- Current module10 stays15OPEN (11P2/4P3) until an applied-source verified fix; no prototype-based closure, module11/global/release/production claim.

## Task1: Independent fix profile and fresh native RED

**Files:** create new `docs/qa/site-qa21-fix-2026-10-18-pc-r1` / ignored `.tmp/site21-pc-fix-r1`; read the sealed PLAN only.

**Interfaces:** consumes this PLAN's hashes, source/native evidence and ready [actual-source browser script](browser-acceptance.js); produces fresh snapshot/current failing geometry without injected DOM changes.

- [ ] Verify this artifact manifest and all1032current source hashes. Record fresh guide/MASTER hashes after PLAN appendices; include this package with its31predecessors. Check runtime namespace absence before creation; preserve all foreign apps.
- [ ] Create independent app `m10s21-fix-r1-app`, normalDB `m10s21_fix_r1`, testDB `test_m10s21_fix_r1`, cache `m10s21-fix-r1`, loopback33560, new own tmpfs media `/tmp/site21-pc-fix-r1-media`, own private media/locmem email and separately compiled current3PO. Use verified existing owned QA PG/internal network, read-only repo/RW own scratch. Use this package's bootstrap/runtime as source reference; never rerun the sealed PLAN bootstrap or reuse its normal DB.
- [ ] Seed the same four fictional actors/short JSON through the new fixture scripts. Keep `/qa/site21/login/` and readonly `/qa/site21/state/` helpers. Copy browser-acceptance.js unmodified into the new fix package and create its owned `png` folder. Configure a new named playwright session `site21-pc-fix-r1` on33560.
- [ ] Execute the script against unchanged source with the new profile's copied browser driver:

```bash
python3 /mnt/c/kidsmap/docs/qa/site-qa21-fix-2026-10-18-pc-r1/browser_driver.py browser-acceptance.js
```

There is no class injection in this script. Expected RED:36cells,12desktop card-overlap failures and root-width failures; all permitted GET/language/no-write/focus controls pass. Current PLAN measurements establish56failed visible-geometry checks of180, with prototype separately recorded. The fresh script also respects the existing1200px maximum; exact fresh counts must be recorded rather than invented. Investigate any differing behavior before apply; do not weaken geometric assertions.

## Task2: Apply the exact conditional class

**Modify:** `src/catalog/templates/admin/catalog/shared_settings_change_form.html:15` only.

**Interfaces:** ModelAdmin provides `opts.model_name`; the page already uses it for the form ID. Bootstrap owns `col-12` (`flex:0 0 100%`, existing15px gutters); KidsMap's grid and max-width retain their rules. Other10compiled branch examples are unchanged, including inactive proxy `contentcatalogsettings`.

- [ ] Reverify approved before SHA and candidate/diff hashes, then check/apply:

```bash
git apply --check docs/qa/site-qa21-recheck-2026-10-18-pc-r1/proposed.diff
git apply docs/qa/site-qa21-recheck-2026-10-18-pc-r1/proposed.diff
```

The complete existing-code change is:

```django
  <div id="content-main" class="km-place-form-page{% if opts.model_name == 'catalogcontentsettings' %} col-12{% endif %}">
```

- [ ] Verify exact candidate SHA and1031other source hashes unchanged; update only new own source guard. Current PO files/shared MO and source cohort count1032 remain. Compile the actual candidate in the real Django template engine and verify active template origin. Do not add a parallel CSS rule or broaden the condition to other models to make unrelated failures green.

## Task3: Actual-source GREEN and bounded regressions

**Files:** new fix evidence only; no new application test file for a class-presence mirror test. Geometry/keyboard/native persistence are the meaningful UI regression.

**Interfaces:** same browser acceptance from RED, fresh source-loaded own server and normal fixture; no in-memory injection or alternate template loader.

- [ ] Restart only the verified owned new server after source guard update, preserving its proxy/normal fixtures and all old apps. Repeat exact browser-acceptance.js: all36cells/five geometry criteria must pass, source-loaded full-width roots/cards fit main/no action overlap/no document overflow; readonly/super fields, language, keyboard, JSON/timestamp/log no-write remain correct. Inspect real screenshots at1440/390 in each language. Compare actual textarea widths with measured baseline74–94px and prototype600px at1440.
- [ ] Test actual source persistence after reload. For the editor role in RU/AZ/EN at1440, use real textareas and visible `_continue`/`_save`: valid nested/Unicode JSON save/readback; malformed values in each field retain bad/other drafts and unchanged DB/log; native valid retry. Inspect resulting error layout at360/390 by resizing the actual returned page. Native mobile submit remains blocked by SITE08: record it; no forced click.
- [ ] Use one valid long JSON fixture with a1024character unbroken value and nested objects; verify editor and view-only value wrapping/bounds at390/1280/1440, then restore original short synthetic JSON through native save and keep QA logs. Do not mutate real/user data or add validation policy.
- [ ] Capture before/after sentinel GETs for branding, direct analytics and gallery add at390/1440 in each language; root class and expected controls/geometry must match their own prepatch baselines because the new condition is false. Known SITE08 errors remain classified; no broad layout or readonly-action closure. Verify other model-name render branches with current template engine.
- [ ] Run the existing105method suite on a fresh isolated migration-backed testDB, unchanged assertions:

```bash
docker exec m10s21-fix-r1-app python /mnt/c/kidsmap/.tmp/site21-pc-fix-r1/runtime.py test catalog.testcases.test_site_qa19_catalog_content catalog.testcases.public.TestCatalogContentSettingsWiring catalog.testcases.test_site_qa06_media_validation catalog.testcases.test_site_qa01_media_permissions catalog.testcases.test_site_qa15_settings_concurrency catalog.testcases.admin.TestSiteGalleryImageAdminMedia catalog.testcases.admin.TestAdminSidebarStructure catalog.testcases.test_public_section_switches
```

Expected105PASS/0failures/0errors, exit0. This includes current SITE19 form/save/readonly semantics and prior approved media/permission/concurrency regressions. No production credentials or RED DB reuse/flush workaround. A separate fresh testDB name may be added only within this new owned namespace after absence checks if isolation requires it; record exact argv.

## Task4: Seal and hand off

**Files:** fix report/verification/manifest and append-only guide/MASTER.

- [ ] Verify one exact application path,1031others preserved, all previous artifacts/refs/index/MO/.cbmignore/activeNONE/foreign runtimes and own fixture final state. Run native Windows `git diff --check`, WSL reverse patch check, template/current3PO/source guards. Collect actual DOM/pageerror/console/network/static404 and PNG evidence; classify blocked externals instead of claiming console clean.
- [ ] Only after actual-source acceptance, close SITE21/P2 LOCAL and reconcile module10 from15 to14OPEN (10P2/4P3), absent another independently proved finding. Keep SITE20/SITE08/SITE11 open and prior closures intact. If a new independent issue appears, record it separately without applying other fixes.
- [ ] Seal evidence/hashes and exact command/snapshot/counts/not-run limits. No commit/push/deploy/cleanup or production/global/release/module11 action. Next work needs its own concrete scope and approval.

## Self-review

Root cause is source-backed: current base flex row257, shared override15 missing Jazzmin's root col-12 at installed change_form47. Reversible native prototype changes flex basis auto→100%, improves geometry in all36cells, returns to baseline on removal and writes no fixture data. Its source remains unapplied. Current candidate compiles, one-file patch checks and scoped10negative branches pass; none substitutes for post-approval actual-source error/long-value/sentinel/functional tests listed above. Prepared future acceptance script is NOT RUN in this PLAN. No independent-agent claim.
