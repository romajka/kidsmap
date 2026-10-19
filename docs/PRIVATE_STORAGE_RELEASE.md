# Private storage and workflow-context release

This is a future production procedure for a separately approved release.
No production operation has been performed for the 2026-10-19 local fixes.

## Preserve private bytes before changing containers

The old Compose file did not persist `/kidsmap-private-media` (specialist and
proposal documents) or `/app/private_media_drafts` (draft photos). Do not replace,
remove, prune or recreate the existing web container until preservation is
verified. Public `media` backups do not include these files.

1. Schedule maintenance and stop incoming writes and all background writers.
   Keep the old container and image available. Record the deployed commit,
   database migration state and mount metadata without copying environment
   values, document contents or user records into repository artifacts.
2. Inspect the two actual storage settings and mount destinations in the running
   installation. If customized, use their actual roots throughout this procedure.
   The checked-in preflight covers the standard roots; it cannot certify a
   customized installation or take a backup.
3. An authorized operator must copy both complete private trees to access-limited
   storage **outside the old container**, preserving names, ownership, permissions
   and bytes. Verify aggregate file counts and byte counts and a private checksum
   manifest. Treat that manifest as confidential operational data, not a repo
   report. Test restoring a copy into a disposable container with the same UID.
4. Create the intended Compose `private_documents` and `private_drafts` volumes
   under the same Compose project identity. Restore the preserved trees into
   them before mounting them in the replacement web container. Never mount them
   under nginx's document root or public media. Existing custom bind mounts or
   volumes require an explicit copy/verified reuse; a new empty volume is not a
   migration. Restrict directories to0700 and files to0600, with application
   ownership. Retain the original container until verification is complete.
5. Verify restored aggregate counts/checksums and perform an authenticated
   download and draft-photo round trip using an authorized test account. An
   anonymous request and another account must be denied; no direct public URL
   may serve a private file. Restart/recreate a disposable verification container
   and repeat the reads. Add both private volumes to the real backup/restore
   schedule before ending maintenance.

`scripts/check-private-storage.sh` is read-only and runs before deployment's
failure trap, Git changes, builds or recreation. It refuses deployment when an
unmounted standard root contains entries or cannot be inspected. It neither
copies files nor authorizes deletion. A mounted root is not proof that the new
volume contains its data: the preservation checks above remain mandatory.

## Schema transition and writer boundary

Do not edit migration0142, which has already been exercised in prior environments.
The new0143 creates actor-bound pending email confirmations.0144 leaves a database
default of `{}` on `WorkflowNotification.event_context`. Thus an old worker which
omits that column can still insert a notification after0144.

There is an incompatible interval after0142 and before0144:0142's Python default
alone is not a database INSERT default. **All old and new writers must remain
blocked for the complete migration batch**, including web, jobs, notification
senders and manual tasks. A generic online deployment of0142 is not safe.
For this release, after preservation and maintenance verification, build the
reviewed image, apply the full migration batch with writers stopped, verify0144
and its database default, then start only the new application and resume writes.
Do not use a normal online rollout to skip this boundary. The release script
requires explicit confirmation of this externally verified writer boundary when
0142 or0144 is pending (`KIDSMAP_WRITERS_STOPPED=1`); this flag does not itself
stop any service and must only be supplied to the reviewed release invocation.

Test password/Google registration, profile email initiation/confirmation, current
and newly addressed invitations, private downloads, draft photos, SEO reports and
public catalogs. Verify migration drift and health checks before opening traffic.
Actual SMTP delivery, production volumes and production service topology still
need release-time verification.

## Recovery

Prefer rolling back application code while keeping the additive0142–0144 schema
and both restored private volumes.0144 preserves old notification INSERTs;0143
is unused by old code. An older application also reintroduces the email-change
and SEO-admin defects: keep affected mutations blocked until a reviewed secure
version is running. Schema compatibility alone is not a security sign-off for
the old code. Do not reverse0144 while old workers write notifications.
Do not reverse0143 after real pending confirmations exist without an approved
data-handling decision. Database restore requires a separately approved recovery
plan and coordinated writer shutdown; this document does not authorize one.
Keep the protected original private copy until the release and restore checks
have been accepted. Never run cleanup as part of troubleshooting this release.
