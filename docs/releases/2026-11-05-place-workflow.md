# Place addition workflow release — 2026-11-05

Authorized scope: fixes for the ten findings in the place-addition audit, followed by the user's explicit Git push and production release request. Base revision: 8b6a523ff38db335bd5e86ac888cfaaac6e6077f.

Changes: unchanged published saves no longer reopen moderation; exact PUBLICATION decisions and revisions stay synchronized; owner cards expose saved-candidate status, note and completion; admin counters/list/SLA share one pending selection; pending previews show the candidate; photo counts and main-image readiness agree; checklist links and price summaries use the current editor. A snapshot-bound reconciliation command classifies redundant legacy claims without granting rights or publishing data. Its apply path is a separate, explicit operator action.

Validation before commit: 607 PostgreSQL17 tests passed (0 failures/errors/skips), including concurrency; 84 JavaScript tests passed. Fresh canonical isolated-quality profile verified source_unchanged=true, migrations and model drift. Earlier browser acceptance verified draft submit, return/reason, resubmit, approval, public visibility and notifications; RU/AZ/EN owner screens passed. Mobile viewport override was ineffective and is not claimed verified.

Production preflight: clean checkout at the base revision; existing immutable image matched it; catalog migrations through0152 applied. No model/migration/dependency/runtime configuration delta. Database backup was restored successfully in a network-isolated disposable PostgreSQL; static snapshot and old image retained privately on the server.

Deployment plan: push the current codex branch; archive the exact committed revision, build a labeled immutable image; retain the effective compose configuration/mounts and change only web image plus revision label. Run check and migrate --check; collect static without --clear; replace only web. No generic deploy script, sync_site_defaults or blanket migration. Rollback uses the previous immutable image/configuration/static snapshot and does not overwrite newer database writes.

Post-release: verify deployed revision, health, source/static parity and authenticated admin state. Resolve only an inspected empty candidate or a classifier-confirmed already-fulfilled legacy claim. Genuine district changes remain pending factual moderation. Never treat published status alone as an ownership approval.
