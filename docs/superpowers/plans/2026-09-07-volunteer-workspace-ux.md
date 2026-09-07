# Volunteer workspace implementation plan

**Goal:** A private, useful volunteer dashboard and the shared permanent-place wizard.
**Spec:** User attachment pasted-text.txt, 2026-09-07 (24 sections).
**Architecture:** Keep User + KidsMap Volunteers and own_places(created_by=user, owner NULL, permanent, not deleted). No new ownership/status models. Derive dashboard state from current revision then live Place; reuse canonical place_readiness. Extract existing permanent-place wizard template as a shared component, keeping existing moderation form as its restricted adapter. Keep owner photo upload endpoints closed; volunteer uploads retain proposal-only semantics.

- [x] Audit routes/forms/readiness/owner wizard and write security regressions first. Cover A/B isolation, AJAX/POST/bulk/hidden fields, private public APIs and Superadmin access.
- [x] Implement derived dashboard counts/filter/search/pagination, per-object preview and private photo route. Verify security tests before template work.
- [x] Share permanent-place wizard markup/navigation/pricing/schedule/map components. Volunteer mode uses backend readiness and proposal POST, without owner publication rules or owner photo endpoints. Preserve owner defaults.
- [x] Dashboard: profile header, primary CTA, statistics, tabs/search, photo/list cards, status descriptions and moderation comments, readiness with field deep-links, empty/no-results states. Sidebar only own allowed functions.
- [x] Browser QA at 1920/1440/1280/1024/768/390/360 and RU/AZ/EN; draft/submit/reject/resubmit/published edit; owner wizard smoke. Run targeted backend regression suites and document exact remaining limitations. Local only, no deployment, no deletion/role migration.

Verification: final SQLite 94 tests OK (1 PostgreSQL-only skip), 61.553 s; PostgreSQL 17 94/94 OK, 67.940 s. Browser AZ/EN/RU and seven viewport widths pass; owner wizard smoke passes. See docs/VOLUNTEER_WORKSPACE_AUDIT_AND_UX.md for evidence and public-media limitation. Local preview 8766 restarted with persistent fixture; both logins verified.
