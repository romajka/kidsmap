# Module03 acceptance test portability — concrete supplemental plan

Status: AWAITING APPROVAL. No edits to these files have been made.

Scope: repair the test inputs/environment assumptions exposed by the approved SPEC-QA-01–03 acceptance. Application fixes remain exactly those three IDs. No new application defect is accepted into scope.

Checkout /home/ramin/kidsmap, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, task33-progress, dirty WORKTREE, active_run NONE. Original full run: docs/qa/module03-full-2026-10-13-r1/backend-full.txt,154 methods,146 passed/8 failures. Six failures stop in the disposable-PostgreSQL guard before exercising their scenario. Genuine baseline overlay: docs/qa/module03-full-2026-10-13-r1/baseline-source.json and baseline-legacy-retry.txt; fake-PDF upload passed before patch, feature GET expectation already failed before patch.

Allowed source files — exactly two:

1. `src/catalog/testcases/specialists.py`.
   - Import the already-added `pdf_document_bytes` fixture helper.
   - In `test_owner_uploads_documents_as_pending_private_certificates`, replace both `SimpleUploadedFile(..., b"pdf", ...)` fixtures with a genuine fictional PDF. Keep the initial proposer denial checks and all current assertions unchanged. Invalid-file rejection is covered by dedicated negative regression tests; this legacy test covers authorized upload/ACL.
   - In `test_feature_enabled_by_default`, request the legacy owner GET with `follow=True` and also assert the recorded redirect leads to the canonical specialist proposal URL. Retain the existing final200 assertion and disabled-feature assertions. Actual current source redirects legacy GET to the canonical form; the pre-patch overlay confirms302 is baseline. No business behavior changes.

2. `src/catalog/testcases/test_task33_specialist_db_review.py`.
   - Make `require_disposable_postgres` accept a genuinely isolated current LOCAL QA profile as a second verified branch, retaining its original Unix-socket branch for existing callers.
   - New branch verifies: PostgreSQL vendor; DJANGO_TESTING=1 and settings.TESTING; settings.QA_ROOT resolves strictly under this checkout's ignored .tmp; config.json belongs to that same root; database name is exactly `test_` + this profile config.database; connection host is explicit127.0.0.1; port/user match this own profile config; media/private-media resolve under that same root. Query current_database() to verify actual test DB matches configured test DB. No credentials printed.
   - Do not accept a generic TESTING flag or a spoofed historical path alone. No six test bodies, model/data/security expectations or existing business assertions change. The transfer suite already imports this helper, so its environment failure is covered by this exact file.

QA-only allowed files: current own runtime/settings and docs/qa/module03-full-2026-10-13-r1 evidence. Use the existing own loopback PostgreSQL stand, own test DB/cache/media/private-media/email and compiled locale v2. No .env/production credentials or application/schema/PO/MO changes for this supplement.

Validation:
- Run only the8 failing methods: six database/migration/transfer checks + the two legacy methods. Record RED from existing full run and fresh GREEN after these changes, exact command/exits/counts.
- Do not rerun the unchanged146 passing methods or whole module. The full batch and targeted supplement must refer to matching application source; only these test/environment corrections differ.
- Preserve full initial failures, baseline failure and all assertions. Update module03 final verdict only if native full browser acceptance and all154 methods are actually accepted. Otherwise retain OPEN/NOT RUN.
- No commit/push/deploy/production. Preserve foreign WORKTREE/active_run/stands.

## Execution handoff2026-10-13

Approved in this chat; implementation and applicable verification COMPLETE LOCAL. Authoritative report: docs/qa/module03-full-2026-10-13-r1/REPORT.md. Earlier readiness/pending text describes the planning checkpoint; no commit/push/deploy/production.
