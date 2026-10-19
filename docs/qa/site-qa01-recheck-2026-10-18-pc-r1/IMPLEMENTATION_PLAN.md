# SITE-QA-01: Media authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> Session override: execute canonical roles sequentially; no new agents or missing skill dependencies are needed for this bounded scope. Existing repository workflow and user authorization take precedence over this skill template.

**Goal:** закрыть подтверждённый SITE-QA-01/P1: прямой staff GET/POST не должен обходить Django model permissions и менять глобальные файлы сайта.

**Architecture:** custom media hub delegates access decisions to existing ModelAdmin permissions. Main fields belong to SiteSettings, gallery creation belongs to SiteGalleryImage. Backend enforces permissions before singleton/storage/query writes; UI uses the same computed capabilities. Existing canonical staff role presets remain unchanged.

**Tech Stack:** Django6.0.2, Python3.12.15, PostgreSQL17, vanillaJS/Django templates, isolated Chromium CLI.

**Spec:** `docs/qa/module10-full-2026-10-18-pc-r1/findings/SITE-QA-01.md` + current [REPORT](REPORT.md), [proposed.diff](proposed.diff), [candidate-manifest](candidate-manifest.json). State PLAN ONLY, approval pending; never treat candidate files as applied sources.

## Global Constraints

- Source1027/HEAD852938d/transfer branch and approved SOCIAL01–12 dirty work remain preserved. No reset/clean/stash/checkout switch/commit/push/deploy/production. active_run NONE.
- Application scope exact4files below; no permission preset/group/migration/model/schema/PO/MO/CSS changes. No correction of SITE02–18 in this scope.
- Tests require DJANGO_TESTING=1, new own normal/testDB/cache/media/private-media/email/current RU/AZ/EN MO and no production credentials.
- CSRF/admin_view/VolunteerAccessMiddleware remain intact. GET wrong-method400, valid authorized invalid-field400, existing payload success format preserved except unauthorized gallery action URLs become null.
- Main-field mutation uses `catalog.change_sitesettings`. Proxy-only grants such as `change_sitebrandingsettings` do not newly confer main media AJAX access. Existing proxy editor authorization remains unchanged. This deliberate policy must be included in scope approval; custom production grants are UNKNOWN.

## Exact files and responsibilities

|File|Action|Responsibility|
|---|---|---|
|`src/catalog/domain_admin/site.py`|Modify|Hub permission guard, main-field change check, gallery-add check, capability context, authorized action URLs|
|`templates/admin/catalog/sitegalleryimage/change_list.html`|Modify|Hide unauthorized upload/delete/add/edit controls, retain read-only previews/public links|
|`static/admin/js/kidsmap_site_media.js`|Modify|Newly uploaded gallery card only renders non-null edit/delete links|
|`src/catalog/testcases/test_site_qa01_media_permissions.py`|Create|22 regression methods, owned temp storage snapshots, role/CSRF/localized/positive controls|

Actual loader uses root `templates/admin/catalog/sitegalleryimage/change_list.html`; do not create an app-template duplicate. New test candidate is formatting-only AST-equivalent to the executed prototype; current fixture-only email correction preserved the intended security assertions.

## Proposed permission policy

|Actor/grant|Hub GET|Main-field upload/delete|Gallery upload/create|
|---|---|---|---|
|Guest/inactive/nonstaff|Existing outer-admin redirect|Existing redirect|Existing redirect|
|Volunteer, even with accidental grants|403 by existing middleware|403|403|
|Active staff without model grants|403|403|403|
|view_sitegalleryimage only|200 read-only|403|403|
|change_sitegalleryimage only|200 gallery-edit authority|403|403 (add is separate)|
|view + add_sitegalleryimage|200, add allowed|403|200; no edit/delete link unless separately granted|
|view_sitesettings only|403 unless gallery-view/change granted|403|403|
|change_sitesettings only|403 unless gallery-view/change granted|200|403 unless gallery-add granted|
|Current content-manager preset / superuser|200|200|200|

Hub visibility and direct action capability follow different model ownership; requiring gallery-view permission for a SiteSettings write would arbitrarily remove an already authorized settings action. Main image removal changes a SiteSettings field, so uses change_sitesettings, not delete_sitesettings. Standard gallery change/delete endpoints retain existing Django object-level behavior.

## Task 1: Server permission boundary and regression

**Consumes:** existing admin_view, request.user.has_perm, ModelAdmin.has_view_or_change_permission/has_add_permission/has_change_permission/has_delete_permission. **Produces:** permission-denied403 before data/file changes; context booleans and nullable edit/delete URLs.

- [x] Write22 candidate methods and run against unchanged application. Current RED:14failed methods/31failure observations,8candidatePASS;6sharedPASS;0errors/exit1.
- [ ] Before applying: revalidate all candidate before-hashes and current source/ref/index; if changed, rebase plan and preserve foreign changes. Check local table route aliases/current3MO.
- [ ] Apply only approved `site.py` candidate: import PermissionDenied; check hub access before singleton/query; field uploads require change_sitesettings; placement uploads require has_add_permission; deletion requires change_sitesettings. Put permission checks outside broad exception handlers so denial stays403, not500.
- [ ] Preserve admin_view/CSRF/method/allowed-field/cache invalidation/storage and normal Gallery CRUD code. Add per-item can_change/can_delete and context can_change_main_images/has_add_permission; upload response URLs null if not authorized.
- [ ] Add target22method test file; run it RED before application patch in future fix profile, then GREEN with candidate applied. New method names/path must match this plan, with no test-only DB name tied to this audit.

Future test command inside fresh owned app: `python <own-runtime.py> test catalog.testcases.test_site_qa01_media_permissions catalog.testcases.admin.TestSiteGalleryImageAdminMedia catalog.testcases.admin.TestAdminSidebarStructure`. Exact new own profile name selected at approved execution; do not rerun or mutate this plan's old artifacts.

## Task 2: Capability-consistent controls

**Consumes:** Task1 capability context/nullable URLs. **Produces:** read-only hub without mutation controls, valid add-only card links, unchanged authorized appearance.

- [ ] Apply only candidate template guards: main mutation inputs/buttons/settings link under can_change_main_images; add under has_add_permission; item edit/delete per respective capability. No new labels or layout/CSS changes.
- [ ] Apply two JS nullable-link guards for newly uploaded gallery cards; no unrelated innerHTML cleanup/locale/loading redesign.
- [ ] Python AST, Django template compile and Node `--check`; no missing selectors/pageerrors when upload input/add controls are absent.
- [ ] Native RU/AZ/EN×360/390/768/1024/1280/1440 for denied staff, viewer, view+add, content manager and superuser: directURL statuses, read-only buttons absence, keyboard navigation, no new overflow. Separate pre-existing SITE08 mobile layout remains OPEN; do not repair here.
- [ ] Real authorized upload/delete/readback/public fallback and restricted staff/viewer direct POST with validCSRF; assert no DB/file/cache/public changes on denied requests. Snapshot own storage bytes and gallery counts. No mutation of real users/media.
- [ ] Add-only upload result: no edit/delete links without grants, full-permission user retains links. Recheck guest/nonstaff/inactive and volunteer with accidental grants, localized aliases and missingCSRF403.

## Task 3: Scoped acceptance and handoff

- [ ] Verify all22targeted+6shared methods GREEN/exit0 with actual run logs; compare source diff exact4files and previous1027source preservation outside3existingfiles.
- [ ] New unique fix package: red/green logs, permission matrix, screenshot manifest, mutation/no-mutation readbacks, source/candidate/apply hashes, exact commands/exits, honest NOTRUN.
- [ ] Preserve22prior packages and current plan package, shared MO/.cbmignore/refs/index/activeNONE/foreign runtime identities; append guide/MASTER only after verified result.
- [ ] Close only SITE01/P1 LOCAL if required checks pass. Remaining15module10 findings stay OPEN; no module11/global/release/production sign-off.

## Risks, rollback and approval boundary

Custom production permission assignments are UNKNOWN. The intended model split is explicit above; do not grant new rights automatically. Proxy-only editors retain their own forms but need explicit canonical SiteSettings permission for these AJAX actions. Gallery image validation SITE06, JavaScript localization SITE11 and generic403/404 design are separate findings.

Rollback only the exact approved4file patch against recorded before-hashes, preserving unrelated work; never reset/clean/stash. No DB rollback/migration because schema/presets unchanged. Current proposal is not deployed or applied. Approval means this policy and exact4file scope; any wider change requires its own plan.
