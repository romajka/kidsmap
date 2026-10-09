# Organization directory

Authorized by user 2026-10-05: design and create a separate public organizations page locally. Baseline HEAD 2da9d33, clean WORKTREE, active_run NONE. No production actions, commit or push.

Goal: organizations must be discoverable through desktop/mobile navigation and a dedicated localized directory, with truthful branch counts and links to existing detail pages.

1. Add regression tests in catalog/testcases/test_organization_directory.py; run isolated PostgreSQL QA to demonstrate missing-route failure.
2. Create controllers/organization_directory.py: published/approved/nonarchived organization queryset, search localized names/descriptions, canonical district filter, pagination. Count and display only published active nondeleted branches with current confirmed ownership versions. Keep zero-branch organizations visible. Fetch page branch data in bounded queries; use public branch photos, never invent organization logos.
3. Create catalog/organization_list.html and css/pages/organization_directory.css: localized hero, labelled GET search and district controls, organization cards, explicit branch-photo captions, empty state, pagination, responsive focus-visible styles. Translation fallback remains explicit.
4. Integrate urls.py, desktop/mobile header, footer and detail backlink. Update public query whitelist and static sitemap; filtered pages noindex, clean canonical directory.
5. Run new tests and impacted public-details/public URL/SEO checks. Restart only owned preview HTTP server, preserving synthetic DB. Render RU/AZ/EN and mobile, inspect overflow, images, navigation/filter/empty-state and local errors. Save aggregate evidence; report targeted checks separately from full-suite status.

Acceptance: /organizations/, /ru/organizations/, /en/organizations/ return 200; private organizations/branches cannot leak through search, counts, districts or photos; existing demo networks show 10 branches each; no horizontal overflow at 320px; keyboard usable controls; org detail returns to listing; filter state survives language switch. Existing specialist map JS failure remains outside this scope.

Execution: implementation and targeted verification complete locally; visual design awaiting_user_review. Evidence and manual acceptance checklist: docs/qa/organization-directory-2026-10-05.md. Final targeted PostgreSQL run43/43 PASS; directory browser24 contexts PASS. No production/commit/push.
