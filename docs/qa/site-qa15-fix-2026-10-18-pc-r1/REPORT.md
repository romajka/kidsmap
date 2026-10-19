# SITE-QA-15/P2 — CLOSED LOCAL

Approved implementation of the whole-row settings concurrency policy. Two tabs can no longer silently overwrite each other: the second stale submission receives HTTP409, retains its text/checkbox draft and old token, and offers an explicit link to the current version in a new tab. Selected files must be selected again. No automatic merge, replay or draft persistence after closing/reloading the old tab is claimed.

## Snapshot and scope

LOCAL HEAD `852938d96764ae315b92859e3651e5ea62054a36`, branch `codex/module09-transfer-2026-10-16-r1`; dirty WORKTREE was the implementation base. User «дальше» approved the [six-file plan](../site-qa15-recheck-2026-10-18-pc-r1/IMPLEMENTATION_PLAN.md). [authorization.json](authorization.json), [source-entry.json](source-entry.json), [final implementation diff](implemented.diff).

Exactly six application files: backend `src/catalog/domain_admin/site.py`, shared settings template, new22-method regression module, RU/AZ/EN root PO appendices. No model/schema/routes/presets/CSS/JS file changes in this scope. Three PO files match the original candidate exactly. The template has a conflict-only [layout correction](template-refinement.json); backend/test have the documented [preview refinement](preview-refinement.json), with one added regression and the existing21methods unchanged. Source cohort1029:1023 existing unchanged,2 existing code/template edits,3 existing PO appendices,1 new test. Three PO files retain their original bytes as prefixes and add three messages each.

The backend signs a full-row digest bound to row/section/actor. Admin POST locks the current row before form validation. Missing/tampered/wrong-actor/wrong-section/stale tokens cannot save. Existing permission/CSRF gates remain authoritative. Six proxy editors plus the direct analytics editor participate; statistics changelist and Gallery shared-template consumer retain existing behavior. The hidden CatalogContentSettings direct editor has a pre-existing500 before template rendering, now tracked as [SITE19/P2](findings/SITE-QA-19.md); its controls beyond that exception are NOT RUN. Main-image AJAX takes the same row lock and updates only its field plus updated_at; a gallery write does not invalidate a settings token.

## Server evidence

Fresh RED on owned isolated PostgreSQL:54 methods,16 failed candidate methods/36 failed observations,0 errors;5 candidate and33 existing controls PASS. [RED](evidence/red-backend.json).

Final current-source fresh GREEN testDB:55/55 PASS (22 new+33 existing),0 failures/errors, exit0,21.516s. [Final GREEN](evidence/preview-final-backend.json). Earlier candidate GREEN:54/54 PASS,0 failures/errors, exit0,18.081s. Includes real concurrent PostgreSQL clients requiring exactly one302 and one409, permission/CSRF/escaping/no-orphan tests,22 SITE01 tests and11 existing media/sidebar/public-section controls. [GREEN](evidence/green-final-backend.json). After the final template correction, all21 affected methods reran PASS,0 failures/errors, exit0,5.463s. [Final template tests](evidence/render-final-backend.json). A new preview regression failed against the first backend (1method,1failure,0errors), then all55 methods reran on the final backend/template in a fresh testDB. No full project test claim.

The first GREEN reused RED's keepdb and had2 failures/11 errors in shared tests: RED's TransactionTestCase flush removed migration-seeded taxonomy. Evidence is retained in [first GREEN](evidence/green-backend.json). A new owned GREEN testDB restored migration fixtures; application and test assertions were unchanged. This is not omitted or counted as passing.

## Native Chromium evidence

|Suite|Rows|Checks|PASS|FAIL|
|---|---:|---:|---:|---:|
|browser-preview-final-matrix|72|1224|1224|0|
|browser-preview-recovery|6|60|60|0|
|browser-preview-file-media|12|51|51|0|
|browser-preview-editors|28|147|147|0|
|browser-preview-permissions|11|22|22|0|

The final72-case matrix covers content-manager/superuser ×AZ/RU/EN ×360/390/768/1024/1280/1440 ×same/disjoint fields. It asserts302/409, stored A, retained B and old token, no row/file/admin-log changes on rejection, language, no false success, autofocus, native Tab, visible focus, safe recovery link, and three layout measurements. Current fixture readbacks are synthetic; helper login simulates fixture authentication rather than testing passwords.

Recovery uses a real new tab and keyboard Enter, verifies current A values, explicitly copies B's chosen field, saves with a fresh token, then rejects the old form again. File cases cover stale upload/no orphan, localized reselection, fresh retry, native main-image upload/delete invalidating an open form. Editor smoke covers all seven real fresh saves in three languages, both Save actions, retained checkbox draft, statistics, Gallery, and gallery independence. CatalogContentSettings direct control initially yielded500/2failed checks; unchanged model __str__/unchanged admin class prove this existing separate SITE19 issue. Original failures are retained, not converted into PASS; final editor suite has28rows/147checks and no claim beyond that baseline exception. Permission probes preserve proxy-only legitimate saves and viewer/denied/volunteer403, SITE01 main-media403 and CSRF403.

Prepatch baseline36 GETcells/72 checks PASS records existing mobile overflow and hidden sidebar submit controls. Mobile submissions use actual Enter from a text input; no hidden-button forcing. Existing overflow is bounded against that baseline, not claimed fixed (separate SITE08).

Initial candidate:72 cases/1008 functional checks PASS, but an inspected mobile PNG showed unreadable alert grid placement. Those results and PNGs remain preserved; they are not final visual proof. The correction uses the existing30px-icon/content grid classes only. Final smoke17 checks and final72-case1224 checks PASS with readable message width, link below message, and content containment. See [initial defect](png/smoke-content-ru-390-disjoint-conflict.png), [corrected mobile](png/final-smoke-content-ru-390-disjoint-conflict.png), [AZ360](png/final-content-az-360-same-conflict.png), [EN1440](png/final-content-en-1440-disjoint-conflict.png), [visual review](visual-review.json).

254 new PNGs are hashed with dimensions in [png-manifest.json](png-manifest.json), including baseline, initial candidate, corrected final matrix and edge cases. [matrix.csv](matrix.csv) enumerates accepted checks. No pageerrors or unexpected local HTTP errors in the final matrix/edge suites that collected those diagnostics. Expected403/409 and blocked external requests are retained/classified; this is not an overall console-clean claim. Console diagnostics were collected for matrices, not every edge probe. Initial file cases had48functionalPASS but3unexpected404 for uncommitted preview URLs. The22nd regression failed against that backend; conflict-only _post_clean now avoids constructing the rejected upload on the instance. Current12file cases51checks include preview decode and have0unexpectedHTTP. Earlier matrices retain their original backend snapshot; current final matrix PNGs use preview-final names.

## Isolation, preservation and limits

Owned app `m10s15-fix-r1-app`, normalDB `m10s15_fix_r1`, RED testDB `test_m10s15_fix_r1`, first GREEN testDB `test_m10s15_fix_r1_green`, final fresh testDB `test_m10s15_fix_r1_preview`, loopback33500; read-only repo mount, RW own scratch, internal QA network. DJANGO_TESTING=1; cleared environment; own cache/media/private-media/locmem email and freshly compiled current RU/AZ/EN MO selected before django.setup. Shared MO files untouched. [Runtime assertions and exact55 IDs](evidence/static-runtime-preview.json), [commands](commands.md).

All26 prior QA packages, out-of-scope source cohort, sharedMO/.cbmignore, HEAD/branch/task33 ref/index bytes/empty staging, active_run NONE and entry container identities/states are checked in [verification.json](verification.json) and [source-final.json](source-final.json). Guide/MASTER append-only proof is [document-preservation.json](document-preservation.json). Inline execution; no independent specialist claim. No commit/push/deploy/reset/clean/stash/branch switch or production operation.

Known boundary: conservative whole-row conflict also rejects disjoint section edits. Arbitrary non-admin writers are not converted to a global CAS service; later external full-row writes and filesystem failures remain outside this contract. Physical devices, screenreader, other browsers, real external services, global suite, release and production NOT RUN.

**Only SITE15/P2 closes locally. Module10 remains15 OPEN (12P2/3P3):14original remaining findings plus new SITE19; full acceptance is pending. SITE01 closure and module09 composite LOCAL closure are retained. Next: separate PLAN SITE06 upload validation; no implementation authorization for it is inferred.**
