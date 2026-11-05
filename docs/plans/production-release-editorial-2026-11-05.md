# Editorial illustration release — 2026-11-05

The user authorized applying the previously generated KidsMap illustrations, pushing Git, and updating the supplied production server. This release merges the existing editorial branch with production revision cdfcdbe7d6a432299187e8e6b19cb6d932dcf088, preserving the current map, warm palette and specialist subject changes.

Scope: 22 transparent WebP assets, illustrated choice cards in the five parent guides, shared decorative art on home/contact/FAQ/about/add-place/directory and empty-result pages. Keep the user-requested homepage interest/category section removed. Animations respect reduced-motion. No model or database migration changes relative to the current production revision.

1. Preserve the original worktree as a private source archive and patch. Resolve the homepage merge explicitly; retain the current homepage route with adapted artwork sizing.
2. Run the complete isolated PostgreSQL quality gate, the CI JavaScript unit/DOM selection and standalone Python checks. Check desktop/mobile rendering and localized pages.
3. Preserve the active production image, effective compose, static files and database in a private server-side release directory; verify database restoration in an isolated disposable container. Prepare an executable web/static rollback.
4. Push the release branch and fast-forward main only. Use `[skip ci]` to avoid a concurrent legacy deployment. Build an image from the exact Git archive with the revision label.
5. Require no pending migrations. Collect static without clearing, then replace only web with the existing environment, mounts, ports and networks. Verify PostgreSQL and Redis container identity remains unchanged.
6. Verify the live revision, health, source/static hashes and rendered images. Keep production credentials and backup contents out of Git and reports.

Private execution evidence: `/home/ramin/kidsmap/.tmp/illustrations-release/`. Server recovery files: `/opt/kidsmap-releases/20261105-editorial-illustrations/`. Build and tests may run concurrently; activation requires passing checks.
