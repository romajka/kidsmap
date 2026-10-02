# Stage 09 — independent security review

2026-09-30, final re-review after stage 09 hardening. Canonical role: `security-reviewer` (`.agents/agents/security-reviewer/agent.md`). Mode: read-only AUDIT within approved stage 09; report only. Local HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty WORKTREE. Production UNKNOWN and not contacted. This review covers the file bytes identified below; concurrent changes require a new review.

## Scope and result

Reviewed `ServerDraft`, migration 0122, draft service/API/routes, stage 09 tests, image upload validator, publication authorization and local media serving configuration. No confirmed P0/P1 vulnerability in this source snapshot. The privacy boundary is source-supported: each draft read/write rechecks the actor and target permission; POST routes use Django CSRF; uploaded images pass existing decode/size/format normalization; draft bytes live in a sibling of `MEDIA_ROOT`, while checked nginx config only aliases `/media/` to `MEDIA_ROOT`. This is LOCAL source evidence, not proof of deployed storage or nginx configuration.

## Findings and remaining risks

- **SEC09-01 · CLOSED in reviewed LOCAL WORKTREE.** `server_draft_api.py` now decorates all four draft endpoints with Django `never_cache`, covering successful GET/POST and error responses; `test_private_responses_forbid_shared_cache` checks successful JSON responses. Source proof covers the photo `FileResponse` through the same view wrapper. Deployed proxy behavior remains UNKNOWN. Owner: django-reviewer; confidence: high in source fix.
- **SEC09-02 · P3 · LOCAL WORKTREE · file/DB atomicity remains a nonblocking risk.** `server_drafts.py:upload_photo` saves a private file inside a DB transaction and deletes it only if `draft.save()` raises locally. A later outer rollback/commit failure can orphan the private file. No public exposure is implied. Consider transaction-aware cleanup or a bounded orphan reconciliation policy in a later scoped task. Owner: django-reviewer/release-reviewer; concurrency/storage failure probe not run.
- **UNKNOWN: deployment storage boundary.** `private_storage()` uses `Path(settings.MEDIA_ROOT).parent / ('private_' + media.name + '_drafts')`. The repository nginx alias is `/opt/kidsmap/media/`; deployment override, symlinks, filesystem ACLs and backup policy were not inspected. Release-reviewer should verify path separation during release review without reading user files.

## Evidence and checks

- `server_draft_api.py`: `@csrf_protect` and `@never_cache` on the four draft routes; `draft_detail` is GET-only. `_error` echoes submitted form fields on save failures; it does not include foreign draft fields. `server_drafts.py:save/read/upload_photo/materialize_place` uses fresh actor, actor ID, `_target` and version checks. The client-supplied first `draft_id` path uses `get_or_create` plus byte-for-byte retry checks; `test_simultaneous_first_retry_one_draft` covers two concurrent calls. `publication.py:authorize` checks target action; `owner_place_use_cases.py:ensure_owner_permission` checks authenticated active non-volunteer create actor.
- `image_uploads.py:_normalize_uploaded_image`: source byte/pixel/dimension constraints, decoded format and MIME check, WebP normalization. `config/urls.py` and `config/views.py` serve only `MEDIA_ROOT`; checked nginx `/media/` alias targets `/opt/kidsmap/media/`. Draft photo storage is outside that root. `materialize_place` passes `files={}` to Place creation, leaving draft photo private. Stage 09 tests cover CSRF, foreign actor, revocation, stale version, invalid upload, private photo GET, duplicate materialization, no public photo attachment and concurrent saves. `permanent_place_workspace.html` supplies `data-account-id` and object/create draft key; `permanent_place_wizard.js` composes both for localStorage, skips file inputs and labels browser-only/offline saves. Model and migration share the explicit index name `catalog_ser_actor_i_76e27e_idx`.
- Executed: Codebase Memory `list_projects`, scoped architecture/search and `check_index_coverage` at generation `2026-09-30T06:41:05Z` (all cited Python files `no_recorded_issue`; `deploy/` excluded, inspected with direct source); local `rg`, `nl`, `git rev-parse HEAD`, `git status --short`, `sha256sum`. Independent isolated QA04: `python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_drafts --output /tmp/task33-09-independent-security-final` exit 0; 17 tests, 0 failures, 0 errors, 0 skipped; PostgreSQL, 156 applied migrations, 0 unapplied, catalog leaf 0122; container/socket cleanup PASS. Browser, external integration and production checks NOT RUN by this reviewer. The stage lead independently ran the full suite; its outcome is not attributed to this review.

## Reviewed SHA-256 (dirty source, not HEAD)

| Path | SHA-256 |
|---|---|
| `src/catalog/models/server_draft.py` | `21fcc22a9dbdcf2d94033bc08284096ce931ef7dc600f8a288a273d41fb3d216` |
| `src/catalog/migrations/0122_task33_server_draft.py` | `aa3c0d0c0ef38aef3d16268a02dc41467d2a7b0c6d2d4ce075db17ea5b8d3dd9` |
| `src/catalog/services/server_drafts.py` | `908fa52c7673ef7b96246eeceaa30a2b8bdf3d9a519bb9625db54f36f59c0fc0` |
| `src/catalog/controllers/server_draft_api.py` | `d618876b052bba7e79945a0bea7e01e4382fa8a25c2e6a8765528e6d9057fab7` |
| `src/catalog/urls.py` | `7c1412705ef87e1163176baa28650985caf1720de90a5d1cec2cf5f03278ed2d` |
| `src/catalog/testcases/test_task33_drafts.py` | `d4201d000b1a42b936dc95070ae8d6d0c74b03899a7a9a5a3796aa0d00e6884d` |
| `static/js/permanent_place_wizard.js` | `db2fa44bbe053c43739522e19a0c16e3b398e2a037ee2a8fb57138198bb3371e` |
| `src/catalog/templates/pages/includes/permanent_place_workspace.html` | `c1dc3ba70d7dcd47c19fc527f0d20ce4f1a8e94b4947a94751e6e48d6be19e6` |
| `src/catalog/services/image_uploads.py` | `d806b8ffd7d2084513a29e4d570d4cc64d28353353b6b9219deaaf762655552d` |
| `src/catalog/services/publication.py` | `8f8a4d172d538edd7b7247a61173b6421d109e046533cef725d6da7564fda6da` |
| `src/config/urls.py` | `c0d4754d62cfcec87d133b5524e4d09e7e1d01fd31606cbd7590ffaf7e411485` |
| `deploy/nginx/kidsmap.az.conf` | `2d7dc21dfbb79e73f753463c03f50978e9b8525d01685559378dccd04a642a89` |

## Handoff

To **django-reviewer**: preserve the closed cache/privacy boundary and confirm isolated QA results against these SHA values. To **release-reviewer** at release scope: verify deployed media path separation and web-server routing. SEC09-02 is a later bounded storage cleanup concern. Re-request independent review after any stage 09 source change; this report does not certify later bytes.
