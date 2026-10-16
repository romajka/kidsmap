# Admin moderation: independent security review

Date: 2026-10-16. Role: `security-reviewer`, execution identity `/root/security_finish`; definition `.agents/agents/security-reviewer/agent.md`.

Mode: READ-ONLY REVIEW of the locally approved eight-fix plan `docs/superpowers/plans/2026-10-16-admin-moderation-eight-fixes.md`. Application and test sources belong to other workers; this reviewer changed only scratch verification files and this evidence report. No production connection or mutation, commit, push or deployment.

Snapshot: LOCAL HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` plus existing dirty WORKTREE. Actual comparison baseline: `.tmp/admin-moderation-audit-2026-10-16-r1/source`, not clean HEAD. Reviewed-file hashes are in `security-source-hashes.json`; they were rechecked after the security suite with no drift.

**Decision: no remaining confirmed security blocker in the bounded moderation fix scope.** This is local acceptance of the reviewed trust boundaries, not production acceptance or a site-wide security audit.

## Evidence

| Boundary | Current evidence and conclusion |
|---|---|
| Protected review workflow | `src/catalog/domain_admin/review_versions.py:40` checks the concrete registered admin object's change permission. Routes at `:49` use `admin_site.admin_view`; no dependency on a public-host staff session. Responses/forms use reversed relative admin URLs. Guest and unprivileged routes are not public previews. |
| Exact decision and revision | `_apply_review_action` validates a positive ASCII numeric revision; `services/review_versions.py:192` locks target/head, reloads the active staff actor, checks concrete review permission, current head and exact pending candidate. A revision from another review receives 409 and changes neither head. |
| Bulk authenticity and atomicity | `domain_admin/review_versions.py:123` binds the signed visible-row snapshot to actor and concrete model, with one-hour expiry. `:134` verifies signature and selected IDs, then wraps all decisions in one outer transaction and checks each object's concrete permission. A second-head conflict rolls back an already processed first-head decision. Tampering returns 400; wrong actor/model returns 403; heads stay pending. |
| Hide/restore | `services/review_versions.py:227` locks target/head and verifies current approved revision and expected visibility. It updates only the approved projection and rating readback; it preserves a pending candidate and immutable history. Repeated/stale decisions fail closed. |
| Shared consumers | The final `SpecialistReviewAdmin` inherits version-aware actions after removal of legacy raw queryset overrides. `domain_admin/review.py:43` makes the Place review inline read-only, disallows add/delete and links to the protected workflow. These two bypasses were raised by the lead and corrected by the owning worker; this reviewer verified their final source. Bounded source search found no other review inline in `src/catalog/domain_admin` or review proxy. |
| CSRF / request methods | All four actual review decision route wrappers, concrete review list and moderation proxy list reject POST without CSRF (403), verified independently with SQL forbidden. Full `Client(enforce_csrf_checks=True)` test confirms missing token is rejected and a valid token permits the legitimate decision. Workflow GET only renders; decision GET renders the confirmation/workflow. Place preview uses `require_GET`; POST cannot publish a preview. |
| Place preview | `domain_admin/place.py:4241` resolves through the admin queryset and checks the concrete Place view/change permission before building the preview. `services/admin_site_preview.py:135` copies the request and uses `AnonymousUser` for guest rendering while retaining the actual administrative session. The preview changes only an in-memory model instance, disables tracking, and returns noindex headers. `admin_view` supplies no-store. Back/locale URLs are constructed locally; untrusted `next` is not used. |
| Escaping | Workflow candidate/current/history/rejection text uses Django autoescaping and autoescaped `linebreaks`; version history and list summaries use `format_html`/`format_html_join` with text arguments. New untrusted values are not interpolated as raw HTML. Existing public preview rendering remains shared. No independent browser XSS payload run was performed. |
| Host-session separation | Fixes use the existing admin origin. No cookie domain/session/CSRF settings were broadened. This review did not change host routing or production configuration. |
| Database schema | All 25 Python files in `src/catalog/models` and all 142 Python files in `src/catalog/migrations` are byte-identical to the pre-fix copied baseline. The reviewed fix adds no fields, constraints or schema migration requirement. |

## Checks executed

1. Read actual source and bounded baseline unified diffs for review actions/services, place preview, proxy moderation and typed review controller; inspected relevant templates, tracking guard, middleware settings and permission wiring.
2. Codebase Memory list/status/architecture/search/trace/coverage were called first. Project root matched `/home/ramin/kidsmap`; generation `2026-10-16T11:58:41Z`. Coverage was unavailable/stale for the newly changed paths and untracked templates, so actual source was used. Trace results were truncated and are navigation only, not exhaustive caller evidence.
3. Python AST parsing passed for eight relevant application modules. SHA-256 snapshot and post-test drift check passed.
4. DB-free RequestFactory route-wrapper probe: six POST routes without CSRF -> 403; SQL execution forbidden by `connection.execute_wrapper`; exit 0. Bootstrapped the existing isolated fix profile but imported current WORKTREE source.
5. Independent PostgreSQL negative suite:

```bash
.venv/bin/python .tmp/admin-moderation-security-fix/run.py
```

Result: **5 tests passed**, 8.609 seconds test execution; command exit 0; system check no issues. Tests:

- actual action rejects missing CSRF, valid CSRF allows the intended decision;
- tampered bulk snapshot rejected without changing candidate;
- bulk snapshot bound to actor and concrete model;
- another review's revision cannot approve the selected head;
- conflict on the second selected head rolls back the first selected head's decision.

Isolation: `DJANGO_TESTING=1`; local audit-owned PostgreSQL `127.0.0.1:33881`; uniquely created/destroyed `test_admin_security_fix`; LocMem cache/email; scratch media/private-media/static paths; external connection guard allows only that PostgreSQL port. Fictional accounts and places only. Root's fixture/audit DB was not modified. Runner and negative suite are scratch files in `.tmp/admin-moderation-security-fix/`; complete local log `test.log`. A missing collected static directory generated a warning; no assertion failed, and this suite does not certify rendered assets.

## Limits and handoff

- No production testing, traffic, deployment, cookie inspection on deployed hosts, data repair or private record access.
- No independent simultaneous-transaction stress test, permission revocation race, cross-device/browser test, live OAuth, storage/nginx audit or full suite. Lock order/race protections were source-reviewed; deterministic conflicts were tested.
- Signed snapshot covers the displayed page. Selecting unseen rows across pages fails closed with 409; this limits bulk UX and does not grant unseen decisions.
- Site-wide historical security findings are outside this bounded fix review. No assertion here closes those findings.
- **Named handoff: `kidsmap-orchestrator`** — integrate the five negative checks with worker regressions and final browser evidence, retain the source hash linkage, and clearly state local fixes versus production-not-deployed status in the user report. No additional security code change requested in this scope.
