# Home places rail implementation plan

**Goal:** Real place cards in a slow continuous desktop rail after the hero, replacing the lower recommendations grid; touch scrolling on mobile, accessible pause and reduced motion.
**Authorization:** User approved “делаем” after the proposed design. Preserve separate rollback to the first redesign.
**Architecture:** Filter existing public popular_places into home_rail_places with photos in HomeController; compact server-rendered include with existing age/price properties. New dedicated vanilla JS enhances native horizontal scrolling; desktop visual copies excluded from tab order and accessibility tree. Existing map/card business logic unchanged.
**Files:** src/catalog/controllers/home_controller.py; src/catalog/templates/pages/home.html; src/catalog/templates/catalog/includes/home_places_rail.html; static/css/pages/home_redesign.css; static/js/home_places_rail.js; scripts/tests/home_places_rail.browser.js.
**Reference:** User-approved conversation design and supplied redesign archive.

- [x] Record a failing real-browser behavior check: moving desktop rail, pause, hover, focus, reduced motion and mobile manual scrolling.
- [x] Add photo-filtered context and compact localized card rail before categories; remove lower recommendations grid.
- [x] Add scoped CSS and vanilla JS: seamless loop at 22px/s, offscreen/tab-hidden suspension, responsive cleanup, visual copies with no duplicate IDs or keyboard stops.
- [x] Browser verification on local isolated fixture: three languages, 320–1440 widths, links, pauses, no-JS fallback, one-item state and wrap. No production access.
- [x] Save screenshots/results and rollback manifest. Original files at output/home-redesign/before-rail. Revert only these three modified files plus remove new include/JS; do not reset unrelated work.

## Verification

Local only; isolated home_preview_settings with DJANGO_TESTING=1 and disposable SQLite fixture.

- RED: `playwright-cli -s=home-redesign run-code "$(cat scripts/tests/home_places_rail.browser.js)"` failed with Expected the places rail on the home page.
- GREEN: same command, 11 checks passed (output/home-redesign/rail-green.txt). The preview uses --noreload; local preview process restarted to load the new controller context.
- Browser AZ/RU/EN × 320,360,390,768,1024,1280,1440: 21 widths match document scroll widths; no pageerror events. Loop crosses 1232px period and continues at 5px; real place link opens successfully. rail-matrix.txt.
- No-JS browser: four original fixture cards, zero copies, pause hidden, place link works. rail-nojs.txt.
- Single-item DOM fixture with actual production initializer: no copies and pause hidden. rail-single.txt.
- Real screenshots inspected: rail-desktop.png and rail-mobile.png. Test photos repeat because fixture uses the same image for four places.
- `node --check static/js/home_places_rail.js`, `git diff --check`, isolated `manage.py check`: pass; Django reports no issues.
- Whole backend suite not run. Existing map/age limitation in isolated preview remains (no Google key); those files unchanged. No production deployment, commit or push.
- Stage rollback inputs and SHA256 guard manifest: output/home-redesign/before-rail/. Original pre-redesign home is still output/home-redesign/before/home.html.
