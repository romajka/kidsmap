# Living Map on public pages

September 9, 2026. The user approved the hero and requested the same living background throughout the public site, reacting to the mouse and clicks, with vertical animation continuing into the footer. This extends `LIVING_MAP_JOURNEYS.md`.

## Result

- One shared, decorative, viewport-sized Canvas in `base.html`; its stylesheet and two scripts load only on the 19 visitor route names in `LIVING_MAP_URL_NAMES`. Home no longer declares its own instance. Account, owner, authentication, admin, API and unknown routes do not receive this enhancement.
- The existing hero journeys remain. Additional trails run down both gutters, with moving light segments in opposite directions, map/category destinations and rounded ends entering beneath the footer edges. Narrow screens retain thinner side trails without forcing large destinations into the content.
- Pointer proximity brightens trails and enlarges icons. Clicks/taps on free background produce two expanding rings, lasting one second, with at most four active ripples. Listeners are passive and ignore form controls, links, buttons and interactive maps.
- Cached content masks protect text, forms, galleries, cards and footer content. Landmark placement also avoids other journey landmarks. The existing clipped-gallery mask regression stays covered.
- Reduced motion stays static and ignores hover/click effects. Hidden tabs stop animation; existing capped DPR, adaptive quality, frame cadence and cleanup remain. No new packages, external animation service or page-height bitmap allocation.

## Verification

LOCAL dirty WORKTREE only; isolated preview at `http://127.0.0.1:8773`, disposable SQLite/media, `DJANGO_TESTING=1`, LocMem email/cache and external integrations disabled. No production operations, commit or push. Existing unrelated homepage/rail changes are preserved.

Commands executed:

```sh
node --check static/js/living_map_background.js
node --check static/js/living_map_scene.js
node static/js/tests/living_map_scene.test.js
.venv/bin/python .tmp/living_map_preview.py test catalog.testcases.test_living_map --verbosity=1
git diff --check
```

Seven scene tests pass, including long-page/footer geometry and narrow-screen exclusion. Two Django test methods cover shared rendering for all 19 public route names and exclusion of 10 account/auth/API/admin/unknown cases, without database access. New scope/geometry tests failed before implementation and passed afterward.

Browser invocation uses the installed CLI:

```sh
node /home/ramin/.npm/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js -s=living-map run-code --filename scripts/tests/living_map_public.browser.js
```

The same command was run with these function files:

| File | Observed result |
| --- | --- |
| `living_map_public.browser.js` | 48 public page/language renders, 15 responsive cases, single Canvas, routes ending at footer, login exclusion, FAQ and catalog navigation; no runtime errors |
| `living_map_click.browser.js` | Six checks: mouse ripple, four-ripple cap, expiration, touch, reduced-motion suppression and static pixels |
| `living_map_scene.browser.js` | Two hero wiring/clipped-slide checks |
| `living_map_background.browser.js` | Nine idle/static/resize/resumption checks |
| `living_map_cadence.browser.js` | 30 actual paints in 0.5 simulated seconds at 90 Hz |
| `living_map_adaptive.browser.js` | Visible small-circle operations drop from 47 to 28 under controlled slow timestamps |
| `living_map_quality.browser.js` | 18 homepage language/width combinations, navigation controls, keyboard and hidden-tab lifecycle; callback p95 2.8 ms, maximum 3.4 ms in the sampled run |

RAF callback frequency includes callbacks that skip painting; it is not display FPS. These are Chromium checks and controlled scheduler tests, not a sustained physical-device GPU benchmark.

The public responsive comparison exposed pre-existing catalog overflow: document width 803 px at viewport 768, and 1315 px at viewport 1280. Both values were identical after hiding the Canvas. This background change does not add that overflow. Event/specialist detail and SEO route gating have server-rendered coverage; those individual detail templates were not browser-tested with populated records in this fixture. Live map tiles/OAuth and the unrelated full Django suite were not rerun.

Desktop top/middle/footer, mobile about/catalog and the preserved home hero were visually inspected. Final video and GIF are in ignored `output/playwright/living-map/public-journey.webm` and `public-journey.gif`; screenshots use `public-*-final.png`, `public-mobile-*.png` and `public-preserved-hero.png`.

## Footer curve correction

Follow-up user feedback identified an angular footer entry in wide gutters. The original turn compressed its entire horizontal displacement into 100 vertical pixels, sampled every 24px; moving trail strokes also cut across the curve. Replaced that turn with a densely sampled cubic curve whose entry tangent matches the side street and whose exit is horizontal. Turn height now scales with gutter width. The moving light and its tail follow cumulative path distance, keeping speed even through the bend.

Two regression tests failed before the correction; all nine scene tests now pass. `living_map_footer.browser.js` passes at 390/1440/1920/2560px: both footer endpoints, continuous tangent, active motion, static reduced motion, no overflow or runtime errors. The rendered 1920px footer was visually inspected in `output/playwright/living-map/footer-smooth-1920.png`; that screenshot supersedes the older video/GIF for the footer turn.
