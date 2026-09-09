# KidsMap Living Map Background

The user requested a stronger animated map after this initial version. See [the current visible-journeys revision](LIVING_MAP_JOURNEYS.md) for the final visual design, added scene module and current verification. The initial implementation evidence below remains historical.

Implemented locally on September 9, 2026, on HEAD `fa169b3beaf2f187e48d2196cd6a999ef602be07` plus the existing dirty homepage worktree. Production was not accessed. Existing hero, rail, map, typography, spacing, components and interactions were preserved.

## Files and architecture

- `src/catalog/templates/pages/home.html`: only three added lines: stylesheet, decorative canvas and deferred script. Existing content is unchanged by this task.
- `static/css/pages/living_map_background.css`: fixed, click-through canvas below page content in the body's existing isolated stacking context; no layout dimensions are added to document flow.
- `static/js/living_map_background.js`: initialization, seeded geometry generation, layout measurement, pointer handling, route/place drawing, scheduling, adaptive quality and lifecycle cleanup in named functions. No third-party runtime dependencies.
- `scripts/tests/living_map_{background,quality,lifecycle,adaptive}.browser.js`: real Chromium checks using the repository's existing Playwright CLI function-file convention.
- `docs/superpowers/plans/2026-09-09-living-map-background.md`: implementation plan.

One viewport-sized Canvas 2D paints document-space geometry through the footer. Scroll updates coordinates, not a page-height bitmap. Six sparse Bezier routes and occasional custom outline pins provide a map metaphor without a proximity network. Existing hero glows are retained. Colors are read from actual computed `--brand-turf`, `--brand-celadon`, `--brand-spruce` and rare `--brand-brick` accents.

Cached exclusion rectangles clear decoration beneath text, photos, forms, carousel viewport, real map, owner content and footer content. Nested rectangles are removed before rendering. Content remains above the canvas, including dropdowns, header and toasts. Section intensities are feathered over 64px: hero 1, search .55, stats .3, rail .35, categories .5, map .08, steps .35, owner .45, FAQ .15, footer .25 with a final fade.

## Motion and budgets

| Viewport | Dots | Pins | Normal target |
| --- | ---: | ---: | ---: |
| Desktop, >=1024px | 96 | 8 | 60 FPS |
| Tablet, 768–1023px | 64 | 5 | 60 FPS |
| Mobile, <768px | 32 | 3 | 30 FPS |

Positions span the whole page, with 30% of dots allocated to the hero. Offscreen geometry is not drawn. Pointer radius is 190px, repulsion <=10px, depth-dependent pointer parallax <=6px horizontally / 4px vertically, idle drift <=5px. Return uses time-based exponential interpolation. Touch devices have idle motion and no simulated hover.

`requestAnimationFrame` performs no DOM layout measurements. ResizeObserver, font readiness, resize, accordion and transition completion refresh cached geometry. DPR is capped at 2. Sustained frames above 1.45 times the target interval reduce dots by half, cap DPR at 1, and use 12 FPS idle / 30 FPS pointer response. Quality stays reduced for the remainder of that page visit to avoid oscillation.

Hidden documents cancel the loop. Pagehide removes listeners and disconnects the observer; persisted pages suspend and resume via pageshow. Reduced motion resets displacement and renders a static frame, with redraws only for layout/scroll changes. No Canvas, a throwing Canvas implementation and disabled JavaScript leave ordinary content and links usable.

Added assets: JavaScript 12,210 bytes / 4,190 gzip; CSS 456 bytes / 296 gzip. One decorative DOM node, plus the script and stylesheet elements; no new packages, build step or textual SEO content.

## Verification

All tests used `DJANGO_TESTING=1`, a dedicated local SQLite fixture copy, LocMem cache/email, separate media and disabled external integrations. No production credentials were inherited. SQLite verification does not establish PostgreSQL behavior; there are no backend or schema changes in this feature.

Executed:

```sh
.venv/bin/python .tmp/living_map_preview.py check
node --check static/js/living_map_background.js
node static/js/tests/ai_referral_tracking.test.js
git diff --check
.venv/bin/python .tmp/living_map_preview.py test catalog.testcases.public.TestPublicPagesSmoke --noinput
.venv/bin/python .tmp/living-map/compare_tests.py
.venv/bin/python .tmp/living-map/compare_tests.py baseline
```

System check, syntax, existing analytics JS tests and diff checks pass. The Django class runs 86 tests and reports 20 failures plus one error. The same failures/error reproduce with a template copy that removes only this enhancement, using the project's cache/language-reset test result wrapper. They concern existing markup, translations, SEO expectations and the earlier homepage structure. Assertions and unrelated application code were not changed.

Browser invocation used the installed CLI at `/home/ramin/.npm/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js`:

```sh
node <cli-path> -s=living-map run-code --filename scripts/tests/living_map_background.browser.js
node <cli-path> -s=living-map run-code --filename scripts/tests/living_map_quality.browser.js
node <cli-path> -s=living-map run-code --filename scripts/tests/living_map_lifecycle.browser.js
node <cli-path> -s=living-map run-code --filename scripts/tests/living_map_adaptive.browser.js
```

The fixture preview runs at `http://127.0.0.1:8773`. Initial browser test failed because the homepage had no canvas; the implemented version passes its nine idle/reduced-motion/resize/accessibility checks. Adaptive test first failed at 45 visible arc operations before/after sustained 34ms timestamps; after adaptation it passes at 45 → 26. This is controlled browser-boundary testing, not a real slow-device benchmark.

Responsive matrix: AZ/RU/EN × 375/390/768/1024/1280/1440; all seven major sections scrolled into view. No horizontal overflow, page runtime errors or local HTTP errors. Canvas visibility does not change section geometry. Language/region/category dropdowns, age selection/reset, keyboard focus, FAQ, mobile menu, hero slider, map CTA, guest-like toast, add-place link and login navigation were exercised. The existing rail test passes all 12 checks, including pause, hover, keyboard, reduced motion and touch swipe.

Fallback checks pass for absent/throwing Canvas and disabled JS; actual touch context and DPR=3 pass. Hidden-document cancellation is tested by dispatching a controlled visibility signal, rather than claiming an OS-level tab test. Screenshots of hero and each section at 390/768/1280/1440 are in ignored `output/playwright/living-map/`; desktop/mobile screenshots were visually inspected.

## Performance and remaining limits

The final instrumented two-second run recorded 59.5 callbacks/second, p95 3.8ms and maximum 4.3ms per background callback, with no page runtime or local network errors. Earlier paired samples on this Chromium environment were materially slower: initial full animation about 30 FPS; adaptive idle painting 38.8–39.9 FPS, versus 42.4–48.1 FPS without the enhancement. This variability prevents a claim of sustained 60 FPS on physical hardware. A physical desktop/mobile GPU check remains advisable before deployment. Both the slow-run evidence and the final passing frame-budget check are retained here.

The local map displayed its existing unavailable/fallback state because external map services were not available in this isolated setup. Map surface, CTA, filtering controls and decorative exclusion were checked; live Google map tiles/markers and real OAuth login were not verified. No production deployment, commit or push was performed.
