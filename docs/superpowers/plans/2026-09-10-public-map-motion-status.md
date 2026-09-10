# Public map motion — implementation and verification, 2026-09-10

## Scope and snapshot

LOCAL HEAD `d59bbc1a`, dirty WORKTREE with unrelated pre-existing admin/home changes preserved. User requested implementation and then explicitly confirmed «да разрешаю» when the automatic reviewer incorrectly applied the historical audit-only restriction. That block was resolved. No commit, push, deployment, production access or Google Cloud configuration change.

Changed scope: `static/js/{google_maps_motion,google_maps_markers,home_map,catalog_map}.js`, `static/css/components/google_maps.css`, home/catalog template asset wiring, catalog AJAX map retention/request cancellation, scoped Node/browser checks. No backend visibility/filter/pricing rules, real coordinates or card content changes. Existing Leaflet/iframe fallback retained.

## Causes found and changes

1. Both Google cluster click handlers previously called `fitBounds`, then possibly another `setZoom` in an idle listener. Home additionally reset viewport and cleared/re-added all cluster membership on each filter. These competing/delayed actions are removed.
2. Catalog desktop AJAX replaced the main column, discarded map state and initialized a new Google Map. The current map panel/canvas now survives fragment replacement. Only fresh server JSON and count metadata are replaced. Surviving place markers retain identity; membership changes are batched into one cluster render, without refitting the user's camera. New/changed public records receive new marker objects only where necessary.
3. AJAX already used AbortController, but an old request's `finally` could clear the newer controller. A request sequence and per-request controller now prevent stale rendering, stale navigation fallback and controller cleanup races. Starting a filter cancels map movement immediately.
4. Both Google views artificially moved duplicate coordinates. They now keep exact coordinates. Coincident clusters offer an accessible AZ/RU/EN place chooser, as do coincident individual pins at manual zoom19. Nearly coincident unresolved groups offer the same choice at zoom18.
5. Legacy Marker click listeners produced an invisible native hit target over the new visual. Public legacy clicks are now registered on an MVCObject, with one accessible OverlayView button, a blank native title and proper z-order. Offscreen visual buttons are excluded from Tab order and the accessibility tree. The actual Google Marker remains the clusterer's marker and InfoWindow anchor. Other detail maps retain their existing marker path.
6. The catalog grid could expand a mobile map beyond the viewport. Its track is constrained; the mobile card scrolls within the map, actions wrap into two columns, the selected pin is moved above the card using one camera operation, and zoom controls remain above it. Closing/reopening the panel preserves the viewport. Card hover no longer bounces pins.

## Camera and marker rendering

Runtime observed in real Chromium: **RASTER**, fractional zoom **false**, Advanced Marker capability **false**. Local Map ID is absent; key/ID values were never included in reports.

- Current raster path uses Google's native padded `fitBounds`; one action advances at most two zoom levels. Expanded *camera bounds*, not changed point coordinates, cap near-point zoom without temporary `maxZoom` or competing idle callbacks. Same-zoom card positioning uses `panTo`.
- Vector + fractional-zoom path uses one cancellable 520ms requestAnimationFrame loop, updating center/zoom through `moveCamera`, following the [official Move Camera Easing pattern](https://developers.google.com/maps/documentation/javascript/examples/move-camera-ease) without Tween/GSAP dependencies. It does not alter tilt/heading. This path is logic-tested, **not rendered-browser verified** with the current configuration.
- New clicks, pointer/touch, wheel, keyboard, drag, filters, hidden document and reduced-motion preference changes cancel owned transitions. The vector loop ends when complete. Reduced motion uses an immediate camera update and disables entrance/hover transitions.
- Existing MarkerClusterer/SuperClusterAlgorithm remains the only cluster engine (`maxZoom:18`, `radius:100`). Cluster calculation runs on its normal update/idle lifecycle, never per camera frame. No second clustering library added.
- Category SVG pins and green count circles retain their content. Only the inner visual animates: opacity0→1, scale.94→1, 190ms; short hover/focus feedback, stronger selected outline/scale. Unchanged single markers stay attached, and cluster membership signatures suppress repeated entrance effects for unchanged groups.
- Advanced Markers are used on public maps only with a supplied Map ID and positive runtime `getMapCapabilities().isAdvancedMarkersAvailable`, per [Google's capability guidance](https://developers.google.com/maps/documentation/javascript/advanced-markers/start). No demo Map ID used.

## Executed checks

Local browser server: `python3 /tmp/kidsmap_motion_serve.py` at `127.0.0.1:8773`, `DJANGO_TESTING=1`, separate `/tmp/kidsmap-motion.sqlite3` copied read-only from local SQLite, locmem cache/email, isolated media. Production database untouched. Current local public map payload: **62 places**. Expanded browser-only fixture: **620 places**, plus empty/single/coincident/near-coincident fixtures.

- `node static/js/tests/google_maps_motion.test.js`: **6/6 passed**. Initial five tests first failed with the controller absent; then passed. Cancellation, bounded completion, reduced motion, coincident choice, marker membership delta, bounded native near-point fitting. `node --test` child-process isolation was unavailable in the sandbox; direct Node's test runner executed successfully.
- `node --check` for all four changed map scripts and all three browser scenario files: passed.
- `git diff --check -- static/js/home_map.js static/js/catalog_map.js static/js/google_maps_markers.js src/catalog/templates/catalog/place_list.html src/catalog/templates/pages/home.html`: passed.
- `node /tmp/run_map_browser.cjs scripts/tests/public_map_motion.browser.js`: **passed** after fixing real hit-target and mobile-overflow failures. Home card checked at **360/390/768/1024/1280/1440**. Catalog cards/reopen at **360/390/1440**. AZ/RU/EN home. Real mouse cluster→pin→one card→Escape; repeated cluster clicks during motion; drag interruption; real category filtering during motion; viewport/marker identity retention; one Maps API load; initial empty iframe fallback, single result, filtering to empty; coincident chooser; 620-place interaction; keyboard/reduced motion; catalog AJAX preserves map, surviving markers and camera. Zero `pageerror` events.
- `node /tmp/run_map_browser.cjs scripts/tests/public_map_motion_edges.browser.js`: **passed**. Exact-coordinate chooser at manual zoom19; near-coordinate zoom sequence **13→15→17→18→choice**; two rapid AJAX requests with delayed first response leave the second category active and retain the same map. Zero `pageerror` events.
- `node /tmp/run_map_browser.cjs /tmp/map_catalog_probe.js`: final 360px rendered check. Map width318 at x21, card width316 at x22, horizontal scroll0, viewport overflow0. Screenshot visually inspected after the final mobile height adjustment.
- `node /tmp/run_map_browser.cjs scripts/tests/public_map_motion_recording.browser.js`: actual Chromium screen recordings at 1440 and390, cluster/pin/card/close/zoom-out. Zero `pageerror` events. Capture observations (not an FPS guarantee): maximum sampled rAF gaps67ms desktop/17ms mobile; no frame in the sampled interval had zero marker DOM nodes. Recordings were inspected through extracted successive frames; DOM counts alone are not evidence of smoothness or loaded map tiles.
- `ffprobe` verified final MP4 files: desktop7.48s, mobile6.96s. Initial page loading was trimmed, interaction frames unchanged.

Browser MCP transport closed midway through work; remaining checks used installed local Chromium through Playwright. The final working browser checks above are real browser runs, not DOM mocks.

## Artifacts

- `output/playwright/map-motion-1440.mp4` — desktop demonstration.
- `output/playwright/map-motion-390.mp4` — mobile demonstration.
- `output/playwright/map-motion-{1440,390}.png` — card snapshots.
- `output/playwright/catalog-probe.png` — final catalog mobile card.
- `output/playwright/public_map_motion.browser-results.json` — full matrix.
- `output/playwright/public_map_motion_edges.browser-results.json` — edge cases.
- `output/playwright/public_map_motion_recording.browser-results.json` — capture observations.

## Remaining limitations

- Native raster camera timing is Google's decision; **450–600ms is not guaranteed**. Raster temporarily scales existing tiles while new ones load; a two-level step reduces but does not eliminate that effect. Do not describe this as guaranteed60fps or vector-quality motion. Actual vector/Advanced animation needs a properly configured real Map ID and separate browser verification; no Cloud change is included.
- Browser console contains Google's existing legacy Marker deprecation warning. The isolated home environment has **nine unrelated hero-photo HTTP404s**; no map/static resource failure or JavaScript exception was observed in the final scenario run. Therefore “zero console/network errors across the whole site” is not claimed.
- Full backend/Django regression suite, live production, real mobile hardware and cross-browser engines were not tested. Browser fixtures do not modify production data. The isolated preview was restarted after the user reported the unavailable-map fallback and is left running at http://127.0.0.1:8773/ru/#home-map (temporary SQLite copy, not deployment configuration). A fresh Chromium check confirmed that port8000 renders no Google API key and no markers; port8773 receives the existing local key, loads Google Maps and renders16 marker/cluster buttons with zero JavaScript exceptions. Evidence: output/playwright/map_preview_probe-results.json and local-preview-restored.png. No key value was recorded.

## Local port8000 follow-up

The user's regular `manage.py runserver 127.0.0.1:8000` process had no Google Maps key in its environment; `manage.py` did not read `.env`. The separate port8773 preview did not fix that process. `manage.py` now reads only `GOOGLE_MAPS_API_KEY` and `GOOGLE_MAPS_MAP_ID` from the existing local `.env` for the `runserver` command, respecting explicitly supplied environment values (including empty values). No database/service credentials are loaded; other management commands and production WSGI/ASGI entry points are unchanged. No cloud or key changes were made.

`DJANGO_TESTING=1 .venv/bin/python scripts/tests/test_local_map_environment.py`: four tests failed before implementation, then four passed. Tests use temporary fake configuration without Django or a database. `git diff --check -- manage.py scripts/tests/test_local_map_environment.py`: passed. Fresh Chromium on port8000 returned HTTP200, Google Maps loaded,16 marker/cluster buttons and zero JavaScript exceptions. The local auto-reloader picked up the fix; ordinary future runserver launches also receive the map settings.
