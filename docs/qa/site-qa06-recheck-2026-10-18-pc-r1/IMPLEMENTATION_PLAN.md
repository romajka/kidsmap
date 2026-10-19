# SITE-QA-06: validate site media before storage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Repository override:** those optional execution packages are not available in this session. Follow canonical KidsMap routing; execute inline with the available TDD/debugging/verification skills. Do not install skills, spawn agents, commit or push by following boilerplate. No application implementation is authorized yet.

**Goal:** reject corrupt, oversized or disallowed new site-media uploads before changing storage/rows/logs, preserve existing valid media, and keep supported static SVG artwork.

**Architecture:** one dedicated byte-preserving validator for site media, used by main/gallery AJAX and the existing settings/gallery ModelForms. Keep SITE01 permission gates and SITE15 revision/locking semantics. Reuse the existing alert icon/content grid for ordinary validation errors; no CSS/JS/model/schema changes.

**Tech Stack:** locally verified Python3.12.15/Django6.0.2/Pillow11.3.0, stdlib ElementTree, PostgreSQL QA fixture runtime and native Chromium. No dependency/version change.

**Spec:** [current finding](../module10-full-2026-10-18-pc-r1/findings/SITE-QA-06.md), [fresh REPORT](REPORT.md), [impact map](IMPACT_MAP.md). [Reviewable seven-file patch](proposed.diff), [hashes](candidate-manifest.json).

## Global constraints

- PLAN only until this exact scope/policy is approved; source1029 unchanged. Existing SITE01/SITE15 and module09 closures remain historical scoped LOCAL evidence.
- Fresh owned fix profile before implementation: proposed namespace `.tmp/site06-pc-fix-r1`, app `m10s06-fix-r1-app`, normal/test DB `m10s06_fix_r1`/`test_m10s06_fix_r1`, loopback33520. Verify names/port absent; choose a new unique suffix if occupied. Do not reuse this plan's mutated fixture DB or old test DBs.
- DJANGO_TESTING=1, environment cleared before settings import, own DB/cache/media/private-media/locmem email and freshly compiled **current** root RU/AZ/EN MO selected before django.setup. Disable external integrations. Production NOT RUN/read-only boundary retained.
- Preserve dirty WORKTREE, source/ref/index bytes, shared MO/.cbmignore, active_run NONE and all prior packages/foreign runtimes. No reset/clean/stash/branch switch/commit/push/deploy, model/schema cleanup or old-data rewrite.
- Approval changes only the seven files below; it does not authorize SITE19, SITE11, SITE08 or a broad media-system refactor.

## Scope and proposed policy to approve

|File|Change|
|---|---|
|`src/catalog/services/site_media_validation.py`|New byte-preserving site-media validator; full [candidate](candidate/src/catalog/services/site_media_validation.py)|
|`src/catalog/domain_admin/site.py`|Validate AJAX before writes; settings form uploads after revision check; gallery form uploads; full [candidate](candidate/src/catalog/domain_admin/site.py)|
|`src/catalog/testcases/test_site_qa06_media_validation.py`|New29-method real-ingress regression module, already RED; full [candidate](candidate/src/catalog/testcases/test_site_qa06_media_validation.py)|
|`src/catalog/templates/admin/catalog/shared_settings_change_form.html`|Use existing icon/content grid for generic errors and alert focus; preserve existing plural message body and SITE15 conflict branch; [candidate](candidate/src/catalog/templates/admin/catalog/shared_settings_change_form.html)|
|`locale/ru/LC_MESSAGES/django.po`|Append5 localized messages, preserve original bytes|
|`locale/az/LC_MESSAGES/django.po`|Append corresponding5messages|
|`locale/en/LC_MESSAGES/django.po`|Append corresponding5messages|

1. **Rasters:** static JPEG/PNG/WebP only. Check the decoded format, truthful filename extension and declared MIME (empty/octet-stream allowed only when actual content and extension are valid). Verify container and reopen/load pixels. Reject animated PNG/WebP and GIF/HEIF for this site-media boundary; owner/place photo normalization remains unchanged. Preserve accepted bytes/extension/transparency: no recompression, flattening, resize or silent conversion.
2. **Limits:** logo and HOME_PARTNERS at most500KiB (512000bytes), other site fields/HOME_HERO at most2MiB (2097152bytes); exactly-at-limit remains valid. At most12000pixels per side and50000000pixels. Existing preferred dimensions/aspect/minimum-logo-quality hints remain advisory. Some panel hints recommend lower sizes; these hard upper bounds are the explicit new policy, not a claim that all existing recommendations are already quotas.
3. **SVG:** keep only for logo and HOME_PARTNERS, at most500KiB. Restrictive UTF-8 static drawing profile: SVG namespace/root; simple geometry/groups/defs/gradients/stops/clip paths/title/description; presentation attributes in the candidate allowlist; fragment-only `url(#id)`. No script/events/style/style-element/foreignObject/image/use/link/animation/filter/mask/pattern/foreign namespaces; no DTD/entity declarations or extra processing instructions. Parse the original document, including its XML declaration, without fetching resources. At most20000nodes, depth64, attribute length65536; finite positive dimensions/viewBox limits. Reject the whole unsupported file rather than stripping content or claiming arbitrary SVG compatibility. Complex legitimate exports may need re-export as plain SVG/PNG. This is a proposed restrictive profile, not a security certification or current agreed sanitizer.
4. **Destinations:** main-field allowlist remains server-owned; unknown gallery placement400 before any save. When both field and placement are sent, main-field authority/policy wins; placement must not grant SVG allowance or weaken the field's permission requirement.
5. **Failure:** AJAX400 `{success:false,error:<localized text>}`; normal ModelForm200 with field error, old stored media and submitted other fields retained. No new stored file, gallery/settings mutation or admin log on invalid input. Rewind uploads in all validator outcomes. Existing client error handling can restore preview/loader/button; its hardcoded Russian wrapper/loading/delete text remains SITE11, not new JS scope.
6. **Ordering/compatibility:** normal permissions/CSRF/volunteer gates precede byte inspection. SITE15 stale/missing/wrong token remains409 before file validation, preserving old token/draft/no-write semantics. Fresh valid forms and valid AJAX retain existing302/200 behavior, row locks, partial main-image writes/cache clearing. Validate only NEW UploadedFile values; old references/no-upload edits and deletion remain possible, including removal of legacy invalid files. No retrospective asset audit/cleanup or global CAS/storage-transaction guarantee.

## Task 1: Revalidate snapshot and failing behavior in a fresh fix profile

**Consumes:** this package's before/candidate/diff hashes, source-entry/source-final, current application, existing55site regression methods.

**Produces:** fresh fix-package source/safety entry, owned red locales/runtime/testDB, RED29candidate+55existing methods.

- [x] Current plan RED is complete:84methods,21failed candidate methods/106failure observations,0errors;8candidate+55existing PASS, exit1. Original82method94FAIL/3context errors and83method103FAIL/0errors are retained and classified in REPORT.
- [ ] Revalidate all1029current-source hashes, every existing-file before-hash and absence of both new root files before editing. Revalidate root/index/ref/sharedMO/activeNONE/prior packages. `git apply --check` must pass against this exact WORKTREE. Do not bypass a mismatch or patch failure with whitespace flags.
- [ ] Provision the fresh owned fix profile described above. Run the same29-method candidate module from its own scratch against unchanged application plus the55existing labels, using the isolated runtime/runner. Exact labels/argv are in [red-backend.json](evidence/red-backend.json). Real PostgreSQL is required for SITE15 concurrency. Preserve original failed results and use a fresh migration-backed testDB for subsequent GREEN rather than a flushed keepdb.

The regression contract is concrete, for example:

```python
before = self.snapshot()  # settings/gallery rows, media hashes, admin-log count
response = self.client.post(self.ajax, {
    'field': 'logo', 'image': self.upload('broken.png', b'not a png')})
self.assertEqual(response.status_code, 400)
self.assertEqual(self.snapshot(), before)
```

Use the complete supplied29-method module unchanged; it also exercises real form routes, valid byte preservation, both SVG positive controls, unsafe XML/SVG inputs (never loaded in browser), boundaries, MIME/extension, pixels, truncated containers, animation,403/CSRF and stale409. Do not weaken assertions to make the candidate pass.

## Task 2: Apply the exact validator and ingress integration

**Consumes:** a new Django UploadedFile plus trusted destination after existing access gates.

**Produces:** `validate_site_media_upload(uploaded_file, *, field=None, placement=None)` returning the same rewound file or raising controlled ValidationError; no DB/storage operations in the validator.

- [ ] Apply only [proposed.diff](proposed.diff), after Task1 and explicit approval. Full code lives in the seven supplied candidate files, not an abbreviated sketch. Exact guarded application mechanism:

```python
from pathlib import Path
import hashlib, json, subprocess
root = Path('/mnt/c/kidsmap')
plan = root / 'docs/qa/site-qa06-recheck-2026-10-18-pc-r1'
manifest = json.loads((plan/'candidate-manifest.json').read_text())
for rel, item in manifest['files'].items():
    path = root/rel
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    assert actual == item['before_sha256'], rel
assert hashlib.sha256((plan/'proposed.diff').read_bytes()).hexdigest() == manifest['diff_sha256']
subprocess.run(['git', '-C', str(root), 'apply', '--check', str(plan/'proposed.diff')], check=True)
subprocess.run(['git', '-C', str(root), 'apply', str(plan/'proposed.diff')], check=True)
for rel, item in manifest['files'].items():
    assert hashlib.sha256((root/rel).read_bytes()).hexdigest() == item['candidate_sha256'], rel
```

- [ ] Preserve `PermissionDenied`/CSRF ordering and SITE15 token clean/_post_clean/get_queryset unchanged. `_SettingsRevisionForm.clean` validates only NEW file fields after a valid revision; `self.add_error(name, exc)` removes invalid file data before instance construction.
- [ ] Use `_SiteGalleryMediaForm.clean` for add/change uploads; keep existing fields/permissions. A placement form error still prevents writes normally.
- [ ] In `ajax_upload`, validate known destination, then call the validator, then enter existing main-image row lock/partial save or gallery create/order computation. Controlled ValidationError becomes400; no storage call is made first. Keep delete handler unchanged.
- [ ] Keep shared photo service `image_uploads.py`, models, signals, schema and dependency files unchanged. Gallery post_save derivative generation is downstream; invalid data must never reach it. Safe SVG can continue bypassing raster derivative generation while retaining its original file.
- [ ] Update source guards from1029to1031 (two new Python files) only for approved bytes. Compile current applied PO into a NEW owned green locale directory and select it before django.setup; retain red/candidate locale snapshots and shared MO.
- [ ] Run all84methods on a newly created GREEN testDB. Require0failures/0errors, including the real concurrent302/409 case. This candidate has **not** been imported/executed GREEN in the plan stage. Investigate actual failures by source/fixture, preserve them and do not edit assertions merely for green.

## Task 3: Render validation and verify the real user paths

**Consumes:** field errors from the validator, existing shared error shell and localized five-message PO appendices.

**Produces:** readable generic error alert and existing per-field error links/focus; conflict branch behavior retained.

- [ ] Apply only the candidate template markup. The existing CSS at `kidsmap_admin_form_shell.css:473` expects `30px minmax(0,1fr)` for icon/content. Generic errors currently put the heading into the icon slot; native6baseline cells confirm this. Reuse `km-place-form-alert__icon`, `__content`, `__heading`, `__description`, and role=alert/tabindex=-1/autofocus. Preserve the original plural block's literal body, existing translations and SITE15 new-tab/file notice branch. No CSS/JS edits.
- [ ] Native Chromium current-source baseline and negative/positive flows for content-manager and superuser ×RU/AZ/EN ×360/390/768/1024/1280/1440. For both main and gallery uploads: valid start; invalid PNG400 + no row/file/admin-log changes + old decoded public/preview image retained + no false success + loader removed/button restored; explicit valid retry works. Use real input events, not transport stubs.
- [ ] Native normal branding file-error POST200 on the same role/language/width grid; verify field error, readable alert, focus/Tab, aria-invalid/describedby, retained other inputs and stored preview, no new overflow against that profile's baseline. Mobile submit can use actual Enter if sidebar buttons remain hidden (existing SITE08); do not force hidden buttons.
- [ ] Direct analytics and gallery add/change form invalid/valid uploads for superuser in three languages at390/1440, plus intermediate-width error-shell checks. Verify both Save actions, no-upload saves, existing invalid-file deletion, exact size boundary, SVG logo/partners positive decode, unknown field/placement and mixed field+placement. Do not load unsafe SVG payloads into a browser; use server-side fixture tests with external integrations off.
- [ ] Recheck SITE01 viewer/add-only/proxy-only/denied/volunteer/CSRF media authority and SITE15 stale form/media interleaves/no token refresh. Shared native Gallery controls remain reachable; CatalogContentSettings direct UI beyond its pre-existing SITE19 __str__500 remains explicit NOT RUN rather than a false PASS.
- [ ] Record expected400/403/409 and blocked requests separately from unexpected HTTP/pageerrors; no broad console-clean claim. Preserve actual images/hashes/dimensions, exact commands and any failed harness results.

## Task 4: Reconcile scope and decision

- [ ] Confirm exact seven-file applied hashes; all out-of-scope cohort entries unchanged; PO append-only with5messages each; previous packages/refs/index/activeNONE/sharedMO/.cbmignore/foreign runtimes retained. Record actual1031source snapshot and any genuinely necessary correction within approved scope.
- [ ] Produce a new unique fix REPORT/verification/PNG/artifact manifest; append guide/MASTER only after completed verification. This plan package and its original RED/native evidence remain immutable.
- [ ] Only then consider SITE06/P2 CLOSED LOCAL. With current canonical counts this would leave14OPEN; SITE19 and full module10 acceptance remain pending. Do not auto-close other IDs, start module11 or claim production/release/global suite coverage.

## Risks and rollback

New caps/formats/static profile are deliberate new policy and require approval. Some complex SVGs/animations/HEIF uploads previously accepted will be rejected; plain supported SVG and transparent rasters preserve bytes. This is not a general SVG sanitizer or a file-storage transaction layer. There is no retroactive removal of previously uploaded bad media, no change to direct model/manual writers, no guarantee for genuine I/O failures after a validated save begins. Existing SITE08 layout, SITE11 untranslated wrappers and SITE19 hidden editor remain open.

Rollback reverses only approved before/candidate byte changes and newly added files after hash review; no Git reset/clean or schema rollback. Restore no old data automatically.

Library rationale: Pillow's [Image reference](https://pillow.readthedocs.io/en/stable/reference/Image.html) distinguishes identification/verification from pixel loading; runtime version here is11.3.0 and candidate syntax is checked locally. Python's [ElementTree documentation](https://docs.python.org/3.12/library/xml.etree.elementtree.html) warns about untrusted XML; the proposed SVG profile adds pre-parser declaration rejection and strict post-parse namespace/element/attribute/budget checks, rather than treating XML parsing alone as validation. Its behavior remains GREEN NOT RUN until implementation approval.
