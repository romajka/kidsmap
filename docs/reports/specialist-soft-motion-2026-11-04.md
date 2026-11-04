# Specialist soft motion — 2026-11-04

User-authorized local polish of the public specialist card. Existing dirty work preserved. No backend, API, business JS, data or permission changes; no deploy.

Changes limited to `static/css/pages/specialist_detail.css` and its versioned stylesheet reference in `specialist_detail.html`:
- One-time380ms header entry,420ms photo, lightly staggered facts (maximum475ms including delay),380ms secondary blocks.
-150–180ms button/document hover and press feedback; back-arrow response; review rating/focus/feedback states.
- Native details remain keyboard-operable; chevron rotates and revealed content fades/slides4px over220ms. Native close remains immediate; no artificial height animation.
- No looping animation. No new JS/dependency. Contact bar itself never moves. `prefers-reduced-motion: reduce` disables component animations/transitions, including pseudos.

Verification: browser normal motion320/390/768/1440 PASS, reduced motion320/390/1440 PASS. No overflow/pageerrors, fixed CTA bottom preserved, native disclosure click/Enter works. Reduced-motion computed animated-elements list empty; content opacity1. Mobile and expanded disclosure screenshots visually inspected. Existing map/review JS regressions11PASS; scoped diffcheck PASS. No new tests added for this reversible CSS polish; browser evidence verifies actual computed motion.

Evidence `.tmp/specialist-motion-20261104/`: before.css/html, plan.md, browser.js/log, js-tests.log. Screenshots `output/playwright/specialist-soft-motion-mobile.png` and `specialist-soft-motion-details.png`. Existing preview8894 restarted with isolated public_preview_settings and left running. The earlier mobile report's source hashes predate this intentional follow-up; new hashes in this scratch directory supersede only the two touched files.

Limits: desktop Chromium with mobile viewport, no physical device/Safari performance claim. Default/native page remains readable without JS. Live production not changed.
