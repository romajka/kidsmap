# Living Map: visible journeys

The subsequent public-site extension is documented in [LIVING_MAP_PUBLIC.md](LIVING_MAP_PUBLIC.md). The hero treatment below is preserved.

September 9, 2026. User feedback explicitly requested a more visible, interesting map animation instead of barely moving dots. This revision supersedes the visual treatment in `LIVING_MAP_BACKGROUND.md`; the existing page design and unrelated worktree changes remain intact.

## Result

- Larger vector landmarks: folded map, park, art palette, book and trophy. Category geometry follows the existing SVG assets, with the same green/mint tokens.
- Routes progressively draw across open spaces; a continuously interpolated beacon travels along each route. Landmarks grow on arrival, float gently and respond to pointer proximity.
- Twelve-second staggered stories: route drawing, arrival, hold, smooth fade and repeat. Reduced motion shows complete, static routes.
- Desktop side streets connect the upper and lower hero routes. Mobile uses two smaller landmarks and omits side streets. Later scenes occupy actual gaps before the rail, categories, steps, owner, FAQ and footer.
- Existing particles are secondary. No extra libraries, raster artwork, map API or framework changes.

Visual reference: the progressive-route and moving-marker technique illustrated in [Tom Miller's animated map tutorial](https://tympanus.net/codrops/2026/05/21/creating-scroll-driven-svg-map-animations-with-gsap/). This implementation uses the existing Canvas lifecycle, without GSAP or copied tutorial code.

## Changed files in this revision

- `static/js/living_map_scene.js`: safe placement, route geometry, timeline, vector landmarks and Canvas drawing.
- `static/js/living_map_background.js`: scene integration, cached palette, gallery clipping exclusions, real elapsed timeline time and corrected high-refresh frame budget.
- `src/catalog/templates/pages/home.html`: one additional deferred scene script before the existing background script.
- `static/js/tests/living_map_scene.test.js`: five behavior tests for placement, connected hero routes, growing paths, stable reduced motion, continuous beacon interpolation and mobile fit.
- `scripts/tests/living_map_scene.browser.js`: verifies module wiring and that clipped slideshow images do not erase outside decoration.
- `scripts/tests/living_map_cadence.browser.js`: controlled 90Hz scheduling test.
- Existing background/adaptive browser tests now observe an active hero scene and count small particles separately from landmark rings.
- This report and `docs/superpowers/plans/2026-09-09-living-map-scenes.md`.

The old mask included offscreen slideshow image rectangles beyond their clipping viewport. The new larger scenes made that defect visible. A browser regression test failed before the fix and passed afterwards. The rendering scheduler also discarded fractional frame budgets: a controlled 90Hz test initially produced 22 paints per half-second and now produces 30. Timeline time now follows elapsed time even in the adaptive low-frequency idle mode.

## Verification

Local isolated preview: `http://127.0.0.1:8773`, `DJANGO_TESTING=1`, separate SQLite fixture/media, LocMem cache/email, no production credentials or operations.

Executed successfully:

```sh
node static/js/tests/living_map_scene.test.js
node --check static/js/living_map_scene.js
node --check static/js/living_map_background.js
.venv/bin/python .tmp/living_map_preview.py check
git diff --check
```

Playwright CLI `run-code --filename` checks:

- `living_map_scene.browser.js`: 2 checks pass, including actual clipping regression.
- `living_map_background.browser.js`: 9 checks pass, including idle, static reduced motion, resize and resumed motion.
- `living_map_adaptive.browser.js`: visible small-circle operations reduce from 46 to 28 under controlled sustained slow timestamps.
- `living_map_cadence.browser.js`: 30 actual paints over a simulated half-second on a 90Hz screen. This is a scheduler contract test, not a physical-display benchmark.
- `living_map_quality.browser.js`: all 18 combinations of AZ/RU/EN and widths 375/390/768/1024/1280/1440 pass. No overflow, runtime errors or local HTTP errors; dropdowns, age control, FAQ, mobile menu and keyboard focus work. Instrumented callback p95 was 3.1ms, maximum 4.4ms in that run. RAF callback frequency includes skipped paints and is not presented as display FPS.

Desktop early/later frames, the categories section and mobile hero were visually inspected. A video and animated GIF were captured in ignored `output/playwright/living-map/`: `journey-desktop.webm`, `journey-preview.gif`, `journey-final-1440.png`.

The previous revision's Django smoke baseline had 20 failures and one error across 86 tests, reproduced without the enhancement. That unrelated suite was not repeated for this visual revision. Live external map tiles/OAuth and sustained physical-device GPU performance remain outside verified scope. No deployment, commit or push.
