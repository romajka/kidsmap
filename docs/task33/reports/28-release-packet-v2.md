# KidsMap Task33 R2 LOCAL release packet

Status: LOCAL CANDIDATE FROZEN. Overall28 acceptance belongs to [reports/28.md](reports/28.md). Production NOT_CONTACTED, exact LOCAL image BUILT; registry publish NOT_RUN, activation NOT_RUN; production readiness is not certified.

## Exact revision

Checkout C:\kidsmap, branch task33-progress, HEAD015d031d8eb17114bd860159dde805b38df3c13c; current dirty application21–27 is R2, HEAD alone is not its version. Exact artifact `r2-local-sha256-2682889e43734eece5b8f0cbc4930e46cc4f75a0f6a5e7c70880cf0bbfde898e`,2793 allowlisted regular files, own standby `/root/km28-release2`.

Archive `/root/task33-evidence/stage28-artifact-20261003/r2-local-sha256-2682889e43734eece5b8f0cbc4930e46cc4f75a0f6a5e7c70880cf0bbfde898e/runtime.tar.gz`; archiveSHA256 `3c705b37c5351fb44e697e308ac73bc51813c64d065eb0d8d1ac3d842b45c26b`, manifestSHA256 `8cc5151a3beb45da606b88a57f54ef62f0d108e3f97d251ed241922b98605e23`. Current source/templates/static/migrations, compiled locales, selected QA and exact recovery reader/override included. No env/Git/venv/user media/database/logs/dumps; shell modes0755. Python3.12.3 and installed dependencies inventoried, no offline wheels bundled.

[28-artifact.json](reports/28-artifact.json) captures every sourceSHA and three explicit AZ/RU/EN MO deltas freshly compiled from identical PO; Windows bytes preserved. All other captured workspace files matched at freeze. [28-artifact-identity.json](reports/28-artifact-identity.json) verifies archive/manifest/standby/current source and records interpreter/dependency/static-source/migration-source identities. Static source identity does not certify a collectstatic volume.

## Schema, media, cohort

Catalog source leaf0133_task33_event_foundation. Fresh actual schema/migrations/conversion/reconciliation is attributed to root/database28 evidence, not inferred from source. Production schema UNKNOWN. Preserve source IDs/legacy values; ambiguous conversion remains manual_review, isolated-only current command never ran in production.

Mandatory future package [release-R2-compose.override.yml](qa28/release-R2-compose.override.yml), alongside reviewed base Compose: required verified allowlisted build context, required reviewed immutable image, explicit TASK33_R1_WRITE_MODE defaultoff/IDs defaultempty, persistent private host bind to exact `/kidsmap-private-media`. Actual settings SRC_DIR=/app/src → BASE_DIR=/app → private root outside /app. Base Compose only mounts public media/static and omits cohort env; raw workspace COPY . can package user data. Base/deployment/application unchanged; override never activated here.

Future image MUST be an actually built verified `@sha256` reference. Synthetic all-zero digest used in config check is not an image. Verify full artifact manifest before build and active image/settings/schema/static/mounts/health before enabling real approved participants. Private host path must be absolute/reviewed/persistent outside public media, restrictive permissions, separate backup and byte reconciliation. Legacy public-path private files require a separately approved transition. deploy-server pulls branch code rather than this dirty artifact; its restart-only failure trap is not compatible recovery and must not be invoked as preflight.

## Validation and recovery

[28-release-review.md](reports/28-release-review.md): artifact safety2/2; official standaloneComposev5.5.0 publishedSHA verified, clean synthetic env/empty external envfile config merge exit0, requiredprivatepath/context/image3/3 negatives exit1; no stack up. Owned networknone/noports cachedpostgres shell container recreated twice retained synthetic private bind bytes, cleanupPASS. This checks bind mechanics, not a Django image. Fresh current nginx1.24 loopback6/6 public200/private404 incl encoded/traversal, cleanupPASS; deployed nginx/TLS UNKNOWN. Evidence: [Compose](reports/28-release-compose.json), [persistence](reports/28-release-validation.json), [nginx](reports/28-release-nginx.json).

Database-reviewer owns native separate recovery with post-switch R1+R2 records, public/private media and durable notification queue, using this exact frozen reader, writesoff and read-only restored DB. Require executed28 recovery evidence of exact identity/all table digests/media bytes/Specialist documents/Event history/outbox/typed reviews/URLs. Root owns final suites/browser/security acceptance. Never overwrite source/new rows with a pre-switch dump or reverse schema as recovery.

## Built LOCAL image and static closure

Refreshed artifact preserves prior V1 and changes only QA recovery_reader lifecycle SHA83513bde82b1211adbd170aeec95187154a7d9df328c175ab7bbd9dfcc389d21; application untouched. [28-artifact-refresh.json](reports/28-artifact-refresh.json). Original standby contains two generated QA-helper pyc caches after metadata reads; failed exhaustive2795 inventory preserved. Fresh verified archive extracted to `/root/km28-image-context`: exactly2793 actual regular files, no extras/symlinks/env/media/DB/venv, verified before AND after final image build. No shared standby/cache deletion. [28-release-context.json](reports/28-release-context.json).

Final LOCAL image ID `sha256:e9ba5fb1303f1309a5627c2f7c78fecdc29b5544acccb283e5639be2c756c5a8`, tag `kidsmap-task33-r2-local:2682889e43734eece5b8f0cbc4930e46cc4f75a0f6a5e7c70880cf0bbfde898e`. Actual local daemon RepoDigests recorded in [28-release-image.json](reports/28-release-image.json); registry publish/accessibility NOT_RUN, no registry digest assumed from configID. `docker build --iidfile ... -t ... /root/km28-image-context` exit0; image metadata-only stopped/source probe confirms all2793 members match and no data paths, owned networknone/noports container cleanupPASS. [28-release-image-verification.json](reports/28-release-image-verification.json).

Image Python3.12.15/39 installed packages differs from host tested Python3.12.3/39; [runtime delta](reports/28-release-runtime-delta.json) inventories exact dependency differences. Full suites were not executed inside this image. Host artifact identity/interpreter remain unchanged. Final image WhiteNoise production static backend executed only with DJANGO_TESTING1/network+libpq guards, noports/networknone/read-only helper plus owned temporary root.9305 collected files, manifestSHA7da4de86a4cb148aa783c824d8a31bd0d9748941e24e5c2bcb2f9c2f3fa08ae2/inventorySHAb408557f6ec81d5d9f46e44625a4b32bcc3777c7d4096bc4d39df8348656cb09 **identical to root host collection**; ownedcontainer cleanupPASS, output retained outsideGit. [28-release-image-static.json](reports/28-release-image-static.json), [28-static.json](reports/28-static.json). Initial static launcher failed before Python because clean PATH omitted /usr/local/bin; evidence retained, explicit executable fixed harness only. No web/Gunicorn/deployment started.

Compose merge/required-variable three negatives repeated for final `/root/km28-image-context`; PASS. Its synthetic image input remains explicitly synthetic and does not substitute for the actual built image ID. Future production runtime checks and activation still require separate instruction.

## Stop criteria and external gates

Stop activation/expansion on lost IDs/media/private bytes/revisions, cross-owner/document access, wrong typed review target, false search identity, contradictory tariff, broken old URL, unexpected500, schema or reconciliation mismatch, queue loss. Disable HTTP writes, quiesce offline commands/queue/cron separately, preserve new data/evidence and reconcile before resuming. HTTP gating is not schema rollback.

Before separately authorized production: exact real image/provenance, effective mounts/private denials, schema/reconciliation/recoverable backup/off-host restore, real approved cohort, queue schedule/locking and SMTP result, real OAuth/Maps, numeric error/latency/query baseline and monitoring owner. Isolated stubs do not establish live integrations. No production deploy/migrate/restart/backup/cleanup or commit/push/merge ran. No next numbered stage remains; production requires separate explicit scoped instruction.
