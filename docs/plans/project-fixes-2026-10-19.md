# KidsMap — approved implementation plan for all14audit points

> Execution follows canonical `.agents` roles and the applicable TDD/systematic-debugging/verification skills. User explicitly approved this complete local scope in advance; no repeated implementation approval. Production actions remain excluded. Missing external sub-skills are not prerequisites to this repository's canonical workflow.

**Goal:** resolve all14points explained to the user, preserve existing closed module boundaries and provide fresh regression/browser/performance evidence per point.
**Architecture:** retain canonical services and approved-public readers. Add staged proof of a new email without replacing the working address until confirmation; enforce admin action permissions/methods, durable private storage, coherent pricing/schedule and historical projections, honest SEO diagnostics/recovery, batch public readers and a compatible schema transition.
**Tech stack:** Python3.12/Django6/PostgreSQL17, vanilla SSR/JS/CSS, Node24/jsdom, isolated Chromium, Docker/Compose source configuration.
**Spec:** user message authorizing all14points, audit `docs/agent-audits/MASTER_AUDIT.md` at entry, detailed local `docs/qa/project-audit-2026-10-19/{backend,seo,security-runtime-validation}.md`. Audit entry and2679/139baseline are preserved in the new run's entry artifacts.

## Global constraints

- Base HEAD75c6c18beb35f019a76e96543723448d8ed1cb7d, same branch; preserve two pre-existing modified reports and stashes. No reset/clean/revert/commit/push/merge/deploy.
- Source implementation, source configuration, migrations, tests and necessary localized UI are approved LOCAL scope. No production credentials, connection, migration, restart, config/env/data edits, cleanup or backup scripts.
- Preserve old module01–13closure. Old audit evidence remains immutable; new reports/logs/snapshots are separate ignored artifacts.
- Every behavioral correction gets a failing regression before production-code changes, then targeted GREEN. Fixtures may be corrected to express a genuinely changed contract; never weaken assertions for green.
- Tests use fresh disposable PostgreSQL/socket/profile via `scripts/run_isolated_quality.py`, DJANGO_TESTING=1, LocMem cache/mail and disposable media. Reuse cached dependency image only; runtime source is freshly snapshotted and hashed.
- One lead/root; at most3parallel workers with disjoint files. Helpers/probe output never constitute independent review or production proof.

## File ownership

| Owner | Files / responsibility |
|---|---|
| Auth worker, canonical Django | `src/catalog/models/user.py`, `models/__init__.py`, new0143email-change migration, new email-change/identity service and controller modules, `controllers/auth_controller.py`, `views.py`, `urls.py`, profile/email-confirmation templates, corresponding new auth test modules. Do not edit `forms.py`; request root coordination if needed. |
| SEO worker, canonical SEO | `src/catalog/domain_admin/seo.py`, `services/seo_audit_engine.py`, `services/seo_fix_engine.py`, SEO admin templates and focused SEO regression modules. No sitemap/public_presentation edits. |
| Backend worker, canonical Django | `src/catalog/forms.py` schedule sections, `services/publication.py`, `services/pricing_plans.py`, `services/content_quality.py`, `controllers/public_details.py`, `services/public_presentation.py`, necessary public organization template and focused backend regression modules. Preserve auth form sections. |
| Root, release/integration/browser | plan/status/master/reports/runtime helpers; private-root settings/storage/Compose/deployment guides and corresponding tests;0144event-context DB-default migration + model field after0143; sitemap/public_languages batching coordinated with backend reader; full integration, browser, performance and final source preservation. |

## Task1 — point1: verified email change

- [x] RED: authenticated profile change must retain the old working address and invitation visibility/rights until a code sent to the new address is confirmed. Cover place/organization notifications/acceptance and ordinary profile edits.
- [x] Add separate actor-bound pending-email challenge state (0143) with hashed6digit code,10minute expiry,5attempts,60second resend cooldown; safe normalization/uniqueness, POST/CSRF, stale address/CAS/replay handling, mail-failure and cancellation semantics. No registration challenge repurposing.
- [x] Implement profile initiation and accessible AZ/RU/EN verification UI. Preserve password/Google registration, current login and existing legacy account behavior on unchanged addresses. Newly supplied addresses cannot gain trust before proof; any historical verification mismatch must fail closed for email-bound privileges.
- [x] GREEN auth/profile/team/notification regression plus negative concurrency/replay/expired/mail-failure cases. Explicitly document any legacy current-email policy and allauth/current-verification synchronization.

## Task2 — points2/4/10/11/12: trustworthy SEO administration

- [x] RED: GET on mutation URLs405, unauthorized staff POST403, authorized POST requires CSRF; existing report renders escaped dynamic content under Django6.
- [x] Add explicit admin action/model permission checks, POST forms and safe formatting, preserving normal admin reads.
- [x] RED/repair audit retention: subset/failure preserves unrelated open issues; reconcile only successfully scanned scope, preserve old evidence when the scanner raises.
- [x] RED/repair safe-fix verification: check original issue invariant after supported real action;200alone or404 never means fixed. Unsupported issue remains open with truthful result.
- [x] RED/repair rollback: restore recorded supported field values transactionally or honestly mark the change irreversible; no successful rollback label without actual restoration.
- [x] GREEN SEO/admin/escaping/dry-run/rollback suites, scopes/flags and multi-locale browser smoke.

## Task3 — points5/6/7/8/9: correct and efficient public business data

- [x] RED then repair Activity approval/unpublish tariff projection and catalog visibility using current canonical nested tariffs, including legitimate legacy/free/on-request/foreign-currency cases.
- [x] RED then reject malformed schedule JSON/schema with field errors in all shared owner/admin adapters; never turn corrupted input into an explicit all-closed save. Preserve valid all-closed, missing-input and draft compatibility.
- [x] RED then read approved Event venue snapshots consistently in Organization blocks.
- [x] RED then show future employment with explicit future start date/state, or use the same current/future classification as the existing public profile. Preserve mutual consent, expiry and revoked visibility.
- [x] RED query budget then batch Organization branch enrichment through existing readers, prefetch activities/pricing/contact/visibility safely without expanding ACL or public eligibility.
- [x] GREEN functional/negative regressions and same synthetic1/5branch query benchmark against30/74baseline; confirm growth no longer+11per branch.

## Task4 — points3/13: persistent private bytes and compatible updates

- [x] Regression for private-root containment/mount coverage and synthetic upload/download/container replacement. Add explicit persistent specialist/proposal and draft storage paths to source Compose/configuration and documented backup/recovery boundary. Do not expose private bytes under public media or change production mounts.
- [x] Provide an approved-release runbook to preserve any existing container-layer bytes before recreation; executable production transfer is excluded. Local synthetic volumes must retain bytes across two containers.
- [x] RED old-worker INSERT omitting0142context; keep0142history immutable and add0144dependent on0143with persistent JSON database default, matching model migration state.
- [x] GREEN populated0141→0142→latest transition, old/new writes, old-image/code rollback compatibility and isolated reverse/forward schema rehearsal. Document the unavoidable0142→compatibility-migration window and block writers for that step in the future release runbook.

## Task5 — point14: sitemap batch enrichment

- [x] RED query budget using the same5/25Activities and15/75localized URLs as audit12/52query baseline.
- [x] Reuse approved-public batch visibility/affiliation data without stale trust caches or changing language eligibility/canonical/hreflang/URLs. Coordinate with backend owner of public_presentation.
- [x] GREEN sitemap/locale/visibility tests; record measured new query counts and timing without promising production speedup.

## Task6 — integration and report

- [x] Freeze final source snapshot and run fresh complete Django/PostgreSQL gate, migration drift/check, all Node units/DOM with real Django photo form and standalone Python checks.
- [x] Real Chromium AZ/RU/EN×390/768/1024/1280/1440: public/account/editor/admin, email change states and keyboard/CSRF/errors, SEO report/forms, Event/employment projections, no unexpected JS/local HTTP/static/overflow errors. Explicitly distinguish unavailable live SMTP/Google/provider/physical-device coverage.
- [x] Re-run organization/sitemap performance on final source. Keep every failing attempt, classification, source hashes, command/count/exit and skipped scope.
- [x] Review source diff, preserve unrelated files/old evidence, update status/master with per-point acceptance and close only own active_run after all workers finish. Stop only own labelled local resources.
- [x] Final user report enumerates14statuses, fresh tests, measured query reductions, new migrations/configuration and any true external release constraints. No production application is claimed.

## Verification commands

Fresh owned QA harness wraps the exact repository launcher:

```bash
DJANGO_TESTING=1 python scripts/run_isolated_quality.py --profile-root "$PROFILE" --socket-dir "$SOCKET" catalog.testcases.test_project_fixes_email
DJANGO_TESTING=1 python scripts/run_isolated_quality.py --profile-root "$PROFILE" --socket-dir "$SOCKET" catalog.testcases.test_project_fixes_seo
DJANGO_TESTING=1 python scripts/run_isolated_quality.py --profile-root "$PROFILE" --socket-dir "$SOCKET" catalog.testcases.test_project_fixes_backend
DJANGO_TESTING=1 python scripts/run_isolated_quality.py --profile-root "$PROFILE" --socket-dir "$SOCKET"
```

Each invocation has a fresh isolated profile/instance and immutable source manifest. Final labels are those created by their owner and recorded in each evidence file. Node/browser workflow reuses the audit's accepted command families against the new exact source; no historical PASS is promoted to fresh evidence.


Acceptance2026-10-19:14LOCAL implemented; full03=2759PASS, final UI04=154PASS+90browser after one conditional error-marker fix. No second full gate is claimed for that markup-only delta. Full evidence: docs/reports/project-fixes-2026-10-19.md. Production excluded; release runbook prepared, not applied.


Git publication2026-10-19: user explicitly authorized commit/push after LOCAL acceptance. The unchanged application snapshot is being published on codex/module09-transfer-2026-10-16-r1, based on75c6c18beb35f019a76e96543723448d8ed1cb7d. Runtime evidence, screenshots, databases and credentials remain local/ignored. This publication does not apply changes to production. Historical acceptance statements above describe the implementation boundary before this Git-only follow-up.
