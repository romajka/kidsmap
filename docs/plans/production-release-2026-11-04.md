# Combined release — 2026-11-04

The user explicitly authorized pushing all accumulated changes and deploying them to production. Scope: specialists onboarding/moderation/public presentation, public mobile repairs, parent guides and assets, homepage slider/motion, image SEO. Preserve the deployed image-SEO overlay behavior and all live content/storage/configuration.

1. Capture all publishable working-tree files and hashes in a private local snapshot; exclude ignored runtime databases, media, credentials and browser artifacts. Verify the exact frozen source with the full isolated quality runner, standalone Python and JS suites and relevant browser checks.
2. Inspect production revision/image/effective compose/migrations read-only. Retain the running image, compose and static manifest server-side; create and validate a database backup. No schema or business-record edits are intended.
3. Commit the verified source, push working branch and fast-forward main without force. Use `[skip ci]` to avoid the legacy deployment workflow competing with this controlled release.
4. Build the exact Git archive, preserve mounts/env/network/ports, check application and pending migrations. Compile locales in the image, collect static without clearing, activate only web. Unexpected pending migrations or configuration drift stop activation.
5. Verify deployed commit/image/source hashes, health, migrations, public/admin endpoints, localized rendered pages and static assets. Restore the previous image/manifest on activation failure. Preserve any subsequent parallel local edits separately from the tested snapshot.

Evidence: `.tmp/release-all-20261104/`; server recovery material: `/opt/kidsmap-releases/20261104-all-changes/` (private, never committed).
