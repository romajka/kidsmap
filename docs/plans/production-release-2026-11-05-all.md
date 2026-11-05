# Combined release — 2026-11-05

The user explicitly authorized pushing all current changes and applying them to the KidsMap production server, then confirmed the existing server address. Scope: accumulated map/design and place-moderation commits, current module split and safe runtime defaults, and specialist subject selection, discovery, validation and counters.

1. Preserve a private source snapshot, patch and hashes. Exclude ignored credentials, runtime databases, media and QA evidence. Freeze the release and run the complete isolated quality gate plus standalone Python and JavaScript suites.
2. Preserve the running production image, effective compose configuration, static tree and database in a private server-side release directory. Verify a restore into an isolated server-side database. Preserve existing env/mounts/networks and unrelated containers.
3. Commit the verified snapshot, push the working branch and fast-forward remote main without force. Use `[skip ci]` to avoid the legacy deploy script racing the controlled deployment; run the quality gates locally.
4. Build the exact revision. Inspect migration plan; the expected addition is 0153, an idempotent subject seed that preserves existing rows and can remain after an image rollback. Apply only the reviewed migration, collect static without clearing, and replace only web using the existing effective compose configuration.
5. Verify active revision/image/source/static hashes, migration state, health, localized rendered catalog/form and representative existing pages. Retain an executable rollback procedure to the previous image/static configuration. Document any later local changes separately.

The release also fixes the build-time translation command so it does not load production settings or require runtime credentials after DEBUG becomes false by default. Public asset versions are refreshed for changed CSS/JS.
