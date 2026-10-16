# Release safety review — AM-02 list links follow-up

Role: `release-reviewer`, `/root/release_safety`, read-only review. User authorization and r1 snapshot supplied by orchestrator. No server connection, production command, application edit or test run by this reviewer.

**PASS for source-level safety; no release blocker found.** Deployment/runtime acceptance remains orchestrator-owned.

## Scope and evidence

- Compared `src/catalog/domain_admin/place.py` and `src/catalog/testcases/test_admin_place_moderation_fix.py` against exact saved r1 bytes under `.tmp/admin-moderation-release-2026-10-16-r2/before/`.
- One `_place_view_url` helper selects the existing protected concrete Place preview for unpublished state and the prior public route for published-active state. Both `col_actions` and `row_actions` consume it; list-menu `data-view-url` also consumes the selected URL. Labels use existing translations. No save/publication/permission contracts were changed.
- Existing `site_preview_view` obtains the object from the admin queryset and checks concrete Place view/change permission; helper routing adds no permission bypass.
- Regression exercises ordinary/proxy admin, both action renderers and pending/draft/inactive-published/active-published states. Parent-provided `red.json` records 12 expected pre-fix failures. The test verifies generated action URLs; rendered navigation remains a separate browser check.
- `prepare.py` requires the 81-test green receipt, validates both before hashes against the r1 manifest, packages exactly two files plus manifest, and carries r1 as the explicit parent patch. It does not package the full dirty worktree.
- `build_remote.py` copies the server-side r1 build context to a new r2 path, overlays the two-file delta, checks all 973 resulting source hashes and absent `.env`/MO before image compilation. No running service changes occur during build.
- Candidate/runtime checks preserve effective environment/mount mapping, verify source and fresh MO, and run migration-plan/system checks in a read-only DB transaction. No migrations/data synchronization are called.
- Activation retains the corrected r1 protection: source/MO/schema verification is inside the rollback boundary. Rollback verifies command exits, bounded readiness, old image, exact environment, `.env` file hash, mounts and protected service IDs. Separate r2 backups and stage preserve r1 rollback image/context.
- `final_remote.py` checks public/admin localized GET health, new static source hash, old image availability, protected service identities and backup metadata. It is bounded evidence; it does not prove moderation POST behavior on real production records.

## Checks executed / not run

Executed: source/diff review of two application/test files; all eight r2 Python scripts parsed with `ast.parse`, including the embedded activation verification program. Reviewed activation SHA256: `bfcfda7c81e7f803ab44e234a908ef42e26e73216d362e30e71e11217a5b61ff`.

Not run by reviewer: Django tests, package preparation/build, server preflight/activation, rollback injection, restore drill, native browser checks. Actual 81-test result and production state were not yet available at review time. Graph coverage for newly generated QA scripts remains UNKNOWN; direct source is the evidence.

Handoff: **kidsmap-orchestrator** — require fresh 81-test green and two-file package hashes, execute guarded r2 candidate/activation/runtime steps, then navigate from the pending list action to protected preview in the authenticated browser. Do not process real moderation records as verification.
