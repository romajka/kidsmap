# Home category release plan

Scope authorized by the user's instruction to push and deploy all remaining changes. Execute inline; no delegation. Files: home.html and home_redesign.css, plus this release record. Preserve the responsive photo implementation.

- [x] Review all worktree changes; connect the existing keyboard pause state and preserve native category link semantics.
- [x] Run isolated home/template tests and rendered mobile/desktop checks, including keyboard focus and reduced motion.
- [ ] Commit the verified snapshot and push seo-indexability-20260916.
- [ ] Production: confirm clean checkout, retain old image and static files, fast-forward, build, run checks/collectstatic without migrations or seeding, restart only web.
- [ ] Verify HTTP200, running source/CSS match, AZ/RU/EN category links, mobile bounds, responsive photo URLs and zero console errors. Record release result and leave local/Git/production synchronized.
