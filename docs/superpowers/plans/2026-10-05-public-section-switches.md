# Public section switches

User authorizes local admin control of Events, Educators and Organizations. Preserve preceding directory WORKTREE and synthetic preview data. No production/commit/push. active_run NONE.

1. Add regression tests for Organization off/on, public links/search/cards/sitemap, proxy-admin persistence/cache invalidation and independent switches; demonstrate RED.
2. Add SiteSettings.organizations_section_enabled default True and additive migration0135; use existing cached singleton and fail-closed features pattern. Hide org directory/detail (404), main/mobile/footer links, catalog org discovery and Place/Activity organization link blocks and sitemap when off. Keep Places, inherited approved contact/program data and organization admin/workspace available.
3. Consolidate three existing/new checkboxes in admin SiteVisibilitySettings (Settings → Sections), clarify labels and explanations, show hidden org status in admin sidebar. Existing Events/Specialists behavior retained.
4. Verify isolated PostgreSQL targeted regressions and migration state. Apply migration only to owned synthetic preview DB, restart owned HTTP preserving data. In browser save all OFF then individual ON; check public links, direct routes and retained admin data; restore previous flags. Save verification/manual instructions.

Execution completed locally. Added responsive, visibility-only admin renderer/styles after rendered QA found the previous single-switch CSS caused overlap. Final isolated44/44 PASS, admin save/off/on browser12 checks PASS, four admin viewport checks PASS. Migration state clean, synthetic data preserved, original flags restoredTrue. Visual acceptance awaiting_user_review. Evidence: docs/qa/public-section-switches-2026-10-05.md.
