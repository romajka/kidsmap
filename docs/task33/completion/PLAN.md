# KidsMap №33 — завершение реализации 1–5

**Authorization:** user PLEASE IMPLEMENT THIS PLAN, 2026-10-04. APPROVED IMPLEMENT; existing audit-only findings are now authorized only within these five points. Production/real providers/commit/push/deploy excluded.
**Goal:** close taxonomy search, ownership concurrency, confirmed UI defects, email crash semantics and all actual regression failures; prove complete local acceptance.
**Architecture:** existing Django/PostgreSQL publication/ACL/outbox pipelines, additive model fields, shared approved-taxonomy consumers. Preserve current WORKTREE and immutable final-audit evidence.
**Decisions:** standalone Activity has its own category/subcategory (Place may prefill only); linked Activity reads approved Program snapshot; automatic email retry permits a rare duplicate after ambiguous crash.

- [x] Preserve all current dirty files/binary patch, verify final-audit manifest, establish one active_run. Entry710 saved files and164 immutable audit files verified byte-for-byte.
- [x] Add nullable Activity category/subcategory and Program subcategory, additive migrations, validated owner/admin writers, moderation-safe taxonomy, detach preservation, consistent catalog/counts/map matching.
- [x] Preserve lock ordering/ACL rechecks, explicit structure_changed HTTP409/reload UX, deterministic success/conflict/retry concurrency tests including grants/invitations/versions.
- [x] Hide unknown specialist experience (retain zero), translate event toast, fix count clipping, one Program main landmark, scoped navigation_motion opt-out; native400/302/409 and keyboard/responsive browser checks.
- [x] Preserve inbox/outbox uniqueness and sent suppression, retry timing/limits and access revalidation; crash fault injection before send/after SMTP acceptance/before commit/after commit; document accepted at-least-once email policy in decisions/stage17 docs.
- [x] Resolve all120 initial full-suite problem entries individually and subsequent failures; update obsolete protocol fixtures/assertions only against approved contracts, fix real defects, no skips/xfail/guard weakening. Keep legacy map4query budget and bounded scaling. Separate generic/compact JS phone contracts. Exact-image test document supplied as SHA-verified readonly QA input only.
- [x] Full discovered PostgreSQL suite on host and newly frozen image:0F0E. Migrations, checks, complete discovery, guards/cleanup pass. Old artifact retained.
- [x] Browser main families and Program/Activity/Organization AZ/RU/EN×320/360/390/768/1024/1280/1440, real forms/keyboard/source/runtime checks, zero unexpected errors, fresh screenshots.
- [x] Native recovery with new schema and post-change records preserves tables/public/private/history/outbox; external production gates remain separate.
- [x] New report, per-failure ledger, source/evidence hashes and preservation; update journal and close active_run only after completion.

Ownership: root orchestrates and owns broad regression/test infrastructure/final integration/release/native/report. Django owns taxonomy+concurrency domain/model/forms/services and related tests. Security owns notifications/crash tests and later independent ACL/publication crosscheck. Frontend owns templates/assets/localization/JS contracts and later rendered QA. Shared boundaries coordinated before edits; no revert of colleagues' changes; separate Linux mirrors and uniquely named disposable runs.

Tests: DJANGO_TESTING=1; disposable PostgreSQL/cache/media/email, transport/libpq guard, no inherited production credentials. TDD for feature/bug changes and causal source/trace verification before regression edits. Historical final-audit remains byte-identical; new evidence lives only here or ignored local scratch/external raw evidence.

Final: все пункты подтверждены completion/final-verification.json и rendered report-checks/results.json. Root final execution sequential; active_run closed.
