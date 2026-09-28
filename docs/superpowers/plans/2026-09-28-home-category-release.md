# Home category release plan

Scope authorized by the user's instruction to push and deploy all remaining changes. Execute inline; no delegation. Files: home.html and home_redesign.css, plus this release record. Preserve the responsive photo implementation.

- [x] Review all worktree changes; connect the existing keyboard pause state and preserve native category link semantics.
- [x] Run isolated home/template tests and rendered mobile/desktop checks, including keyboard focus and reduced motion.
- [x] Commit the verified snapshot and push seo-indexability-20260916.
- [x] Production: confirm clean checkout, retain old image and static files, fast-forward, build, run checks/collectstatic without migrations or seeding, restart only web.
- [x] Verify HTTP200, running source/CSS match, AZ/RU/EN category links, mobile bounds, responsive photo URLs and zero console errors. Record release result and leave local/Git/production synchronized.

## Release result

- Runtime commit: `57a2c032e34631dbebf3826ec86a0c54b7465c56` (all remaining application changes).
- Web image: `sha256:880492f61046962bcd13d6a6a85d45da2451247c74cc6fa633925860d73b39a6`, started 2026-09-28 09:32:44 UTC.
- Tests: `DJANGO_TESTING=1 DJANGO_DEBUG=1` with DATABASE_URL/REDIS_URL unset; isolated source runner `/tmp/kidsmap-staff-test-runner.py`, temp media/LocMem cache/email, integrations disabled. `catalog.testcases.test_home_public_metrics` plus `catalog.testcases.test_responsive_images.ResponsiveImageTests`: 12 passed, no skips. No DB was used by these SimpleTestCases. Full suite not rerun for this template/CSS release.
- Browser preflight: actual templates/static assets served by an isolated loopback fixture preview, widths375/1280, RU/EN/AZ labels. This was not production data or a full browser integration test.
- Production: clean checkout fast-forwarded, web built; Django check and migrate --check passed. collectstatic --noinput ran without clear. No migrations, seeding, env/config edits or media generation were run. Only web was recreated.
- Recovery: retained prior image `kidsmap-web:rollback-home-cloud-20260928`, private static snapshot `/opt/kidsmap-releases/20260928-home-cloud/static-before.tar.gz`. gzip integrity verified; restore not executed.
- Both changed runtime files SHA256-match server checkout. Collected `css/pages/home_redesign.7cc8e4102408.css` matches CSS source byte-for-byte and browser loads it with `v=20260928_cloud2`.
- Public health/home/catalog/RU/EN HTTP200. Production displays10 category links. Clicking first AZ category opened `/catalog/?category=SPRT`, returned12 cards. Mobile375px: all category bounds within viewport; focus outline3px, all category animations paused during keyboard focus. Reduced-motion animations are none. RU/EN mobile categories fit too; console errors0 (existing Maps warning remains).
- Responsive hero images still load derivative URLs; checked home has0 broken images. Mobile screenshot visually inspected; screenshots are ignored QA artifacts under output/playwright.
- Root executed directly, no independent/subagent reviews. Remaining repository worktree changes were included in this release; no application changes intentionally left pending.
