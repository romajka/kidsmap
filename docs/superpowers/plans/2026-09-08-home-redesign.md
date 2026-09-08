# Home redesign implementation plan

**Goal:** Adapt the supplied Kidsmap.az redesign project.zip to the actual home page, with responsive layout, animation and an isolated rollback.
**Authorization:** User approved adaptation on 2026-09-08 and requested the ability to revert if dissatisfied.
**Architecture:** Retain the Django home context, shared card include, map, filter handlers and existing gallery. Load one home-only stylesheet; add localized presentation and category links to the home template. No backend, production or shared navigation changes.
**Stack:** Existing Django templates, CSS, existing JS.
**Reference:** /home/ramin/Downloads/Kidsmap.az redesign project.zip

- [x] Inspect template/CSS/script dependencies and archive. Baseline HEAD d75b34f4; unrelated dirty work is preserved.
- [x] Save exact original template at output/home-redesign/before/home.html (ignored local artifact).
- [x] Add hero eyebrow, primary map/catalog CTA, category discovery links using actual home_categories, and recommended section anchor. Preserve actual counters and data attributes.
- [x] Add static/css/pages/home_redesign.css: green/cream surfaces, editorial hero, photo collage, search panel, category grid, map, cards, steps, owner section, FAQ. Scope all rules to page-home; 320–1440 responsive widths; keyboard focus; reduced motion.
- [x] Render using isolated existing audit fixture settings/database; inspect real screenshots, test AZ/RU/EN widths, dropdowns, gallery and links. External integrations blocked during browser checks; record map limitation.
- [x] Verify git diff --check, template rendering and no unrelated modifications. Save screenshots and verification JSON under output/home-redesign.

Rollback: restore only src/catalog/templates/pages/home.html from output/home-redesign/before/home.html and remove the new home_redesign.css file after checking that no later edits would be overwritten. Do not reset the worktree. No commit/push/deploy in this task.

## Verification, 2026-09-08

- Local isolated preview: `DJANGO_TESTING=1`, `home_preview_settings`, disposable SQLite copy `/tmp/kidsmap-home-preview/fixture.sqlite3`, local cache/email, no inherited credentials; runserver 127.0.0.1:8772.
- `playwright-cli -s=home-redesign run-code` checks saved under `output/home-redesign/`: responsive-check.txt, interaction-check.txt, link-check.txt, desktop.png, mobile.png, full-desktop.png.
- Responsive matrix AZ/RU/EN × 320/360/390/768/1024/1280/1440: 21/21 without horizontal overflow, one h1, no pageerror events. Initial 768–1280 overflow traced to rotated decorative pseudo-element; corrected geometry and reran entire matrix.
- Category and district menus open; category selection EDU changes existing hidden select; gallery next activates slide 1; keyboard Tab/Shift+Tab gives solid visible outline; reduced motion sets photo animation to none. Programmatic focus after pointer input correctly does not force focus-visible.
- Fixture has four places and one populated category; counts/text in screenshots are fixture content.
- Google map and dependent age interaction NOT VERIFIED: isolated preview intentionally has no Google Maps key. Existing home_map.js only binds age handlers after successful map initialization; age input stays empty here. No map JS was changed.
- Existing fixture content includes some AZ strings on RU page; new copy is localized explicitly.
- Full backend suite not run: presentation-only change. Production not changed.
- Rollback original and SHA256 manifest in output/home-redesign; reverse template patch checked with git apply --reverse --check. Check manifest before reverting to avoid overwriting later work.
