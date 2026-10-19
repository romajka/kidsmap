# SITE-QA-06/P2 — CONFIRMED OPEN / PLAN READY

2026-10-18, LOCAL C:/kidsmap, /root sequential execution; django/security/integration/browser responsibilities inline, no independent agent claim. User «дальше» after SITE15 closure authorizes this bounded recheck/plan, not implementation of a newly proposed scope.

**Seven-file candidate is unapplied; application changes0, GREEN NOT RUN.** [Implementation plan and proposed policy](IMPLEMENTATION_PLAN.md), [reviewable diff](proposed.diff), [hashes](candidate-manifest.json), [impact map](IMPACT_MAP.md), [verification](verification.json).

## Snapshot and current behavior

LOCAL HEAD `852938d96764ae315b92859e3651e5ea62054a36`, branch `codex/module09-transfer-2026-10-16-r1`; existing dirty WORKTREE is the source baseline. All1029current-source entries match SITE15's final snapshot and remain unchanged. Previous SITE01/SITE15/module09 scoped LOCAL closures are retained; production UNKNOWN/NOT RUN.

Source `src/catalog/domain_admin/site.py:1067` accepts FILES image and assigns/saves it without decoding. `SiteSettings.logo` and `SiteGalleryImage.image` are FileFields; ordinary settings/direct analytics/gallery forms also allow corrupt bytes. Gallery save triggers responsive derivative work in signals; a failed derivative does not reject the original stored image. Existing photo normalization is a separate service that re-encodes rasters/loses SVG support; no change proposed to that service.

Native proof: correct PNG starts decoded; real upload of a corrupt `.png` receives200/success, changes owned row/file state and gives public naturalWidth0. Correct retry restores a decoded logo. Both content-manager and superuser reproduce it on RU/AZ/EN at390/1440. Ordinary branding form accepts the same corrupt upload with302 and success message. Gallery AJAX creates corrupt records. Existing benign static SVG works for logo/partners and is a positive control, not a new passing claim for the candidate.

## Fresh server RED

[Final RED](evidence/red-backend.json):84methods,21failed candidate methods/106failure observations,0errors, exit1,21.679s. Candidate29methods:8PASS/21FAIL; existing55 SITE01/SITE15/media/sidebar/public-section controls PASS unchanged. Includes real PostgreSQL concurrency control. Full method IDs/runtime are in [static-result.json](evidence/static-result.json).

First82method run had94FAIL/3errors: three new tests dereferenced response.context after the application unexpectedly redirected302. Retained [initial result](evidence/red-initial-backend.json) and [initial candidate](test-initial-candidate.py). Added explicit assertIsNotNone so this is a contract failure, not a test exception; added real truncated raster coverage. Fresh83method run:103FAIL/0errors, retained [v2](evidence/red-v2-backend.json). Static-raster animation coverage then produced the final29-method candidate/fresh84method RED above. Expectations were not weakened. Each RED used a new owned testDB to avoid TransactionTestCase-flushed migration fixtures; no application/assertion repair for old tests. Raw Django test HTML/logs remain ignored scratch only.

These RED observations include both the confirmed corrupt-file defect and deliberately proposed format/cap/static/SVG rules; acceptance of every previously allowed format is not independently called a production exploit. Unsafe SVG fixtures were stored/tested only in owned backend media and never opened in a browser. No production attack or live compromise claim.

## Native evidence

[Main browser recheck](evidence/browser-red.json):30rows/138checks —69controlPASS,69expectedRED. Twelve role/language/width cells each cover real main upload/public decode/retry and gallery upload; three extra native SVG-positive rows and three ordinary branding-form negative rows. Pageerrors0, unexpected local HTTP0;42blocked external requests and42console diagnostics retained, not called console-clean.

[Generic error baseline](evidence/browser-generic-error.json):6cells,18checks —12controlPASS/6heading-layoutFAIL. Existing ordinary validation puts the heading into the30px icon grid column. This is a pre-existing supporting error-state observation, not a new SVG/content exploit. The seventh-file template proposal wraps generic errors using the same icon/content classes already used by SITE15, while preserving its conflict branch/plural body. It does not fix all existing SITE08 overflow/desktop submit positioning or unrelated translations.

45new native PNGs:39core +6generic-error baseline. [Manifest](png-manifest.json). Inspected [broken public logo](png/red-content-ru-390-broken-public-logo.png), [recovered logo](png/red-content-ru-390-restored-public-logo.png), [accepted bad normal form](png/red-super-en-1440-accepted-bad-form.png), [generic error mobile](png/baseline-generic-error-ru-390.png) and [desktop](png/baseline-generic-error-en-1440.png). Immediate screenshots may include existing form-shell positioning/transient layout; no new global-layout finding or closure is inferred. Byte readbacks/HTTP/decode determine the upload finding. [Matrix](matrix.csv) keeps core and adjacent observations separate.

## Proposed repair and policy decision

One dedicated pre-storage validator used by both AJAX branches and NEW-file ModelForm ingress; preserve accepted bytes/alpha and existing references. Proposed static JPEG/PNG/WebP; matching extension/declared MIME, actual verify+decode; max500KiB logo/partners and2MiB other fields/hero;12000side/50MP. Proposed restricted static UTF-8 SVG only logo/partners (simple geometry/gradients/clips, no CSS/use/images/scripts/external content; explicit budgets). This is not arbitrary SVG compatibility or a sanitizer certification. Complex SVG and previously accepted animations/HEIF/GIF may need re-export; those policy restrictions need approval.

Expected rejection: AJAX400 localized JSON, forms200 with field errors, no target row/file/admin-log mutation. SITE01 permissions/CSRF/volunteer gates stay first, SITE15 stale409 stays ahead of validation; valid302/200, locked partial media writes, deletion and no-upload edits remain. Five new messages per RU/AZ/EN PO, existing bytes preserved. No models/schema/dependency/CSS/JS/routes/presets or retroactive cleanup. Full exact interfaces/code/test cases/limits and future native acceptance are in the plan/candidates, not applied source.

## Static checks, isolation, preservation and limits

[Final static commands](evidence/static-commands.json) all exit0: candidate Python AST/code compile, candidate template compile, root current template origin/source1029 guards/runtime safety/84method enumeration, candidate3PO compilation/verification, exact git apply --check. Candidate Python modules were not imported/executed GREEN; rendering behavior remains NOT RUN. Initial normalized-EOL patch check failed against CRLF source, retained [initial result](evidence/static-initial-commands.json) and [old diff](proposed-normalized-eol.diff); final patch preserves original line endings and applies cleanly. No whitespace bypass.

Owned app `m10s06-plan-r1-app`, normalDB `m10s06_plan_r1`, fresh testDBs `test_m10s06_plan_r1`, `_final`, `_static`, loopback33510; read-only repository bind, RW own scratch, internal verified QA PG/network. Environment cleared before Django setup; DJANGO_TESTING1, own cache/media/private-media/locmem email, root current3MO compiled and selected before setup, external integrations off. Python3.12.15/Django6.0.2/Pillow11.3.0 verified. Fixture authentication is simulated; actual UI submits/backend writes/readbacks are real and synthetic. Bad gallery assets intentionally remain in this disposable RED profile; use a fresh profile after approval. A copied launcher initially polled an old helper path404 while root served200; corrected only own helper/readiness/server and retained [classification](evidence/readiness-adjustment.json).

Source/ref/index/activeNONE/sharedMO/.cbmignore,27prior packages and entry container identities/states are checked by [verification](verification.json); guide/MASTER append-only proof in [document-preservation](document-preservation.json). Codebase Memory ready count is not freshness: its snippet lines/edges are stale and File metadata lacks generation; relevant source verified directly, no graph cache copied. No commit/push/deploy/reset/clean/stash/branch switch/production operation.

**SITE06 stays OPEN/P2; module10 stays15canonicalOPEN (12P2/3P3), full acceptance pending.** SITE19 and other scopes remain open; SITE01/SITE15 and module09 closure evidence retained. GREEN/native candidate behavior/full suite/physical devices/screenreader/cross-browser/real external services/release/production NOT RUN. Next action is user decision on the concrete seven-file policy/scope; implementation approval has not been inferred from this planning request.
