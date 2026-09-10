# Public map motion implementation plan

Goal: preserve Google Maps, filters, public payloads, category pins and cards while making cluster → places → one selected card predictable.
Authorization: user explicitly requested implementation and browser recording. LOCAL HEAD d59bbc1a with pre-existing dirty worktree; no production actions, DB changes, commit or push.

Architecture: shared camera/selection controller for home and catalog; current MarkerClusterer remains the only clustering engine. Exact coordinates, stable home marker instances and delta membership updates. Native raster camera movement; bounded 520ms moveCamera easing only with vector/fractional capability. Advanced markers require configured Map ID and runtime capability; otherwise a Google OverlayView visual attached to the existing legacy Marker lifecycle, never decorative coordinate offsets.
Tech: vanilla JS, Google Maps API, existing MarkerClusterer, scoped map CSS, Node tests and Playwright.
Spec: user brief in this session (all six sections).

- [x] Add behavioral regression tests for cancellation, reduced motion, duplicate-coordinate choice, bounds, delta updates and exact positions.
- [x] Add static/js/google_maps_motion.js: one camera owner, projected padded bounds, interruption handling, accessible coincident-place chooser and selected marker state.
- [x] Update static/js/google_maps_markers.js with opt-in public visuals, real Advanced capability gating, preserved SVG anchors and accessible legacy overlay buttons. No bounce for public maps.
- [x] Update static/js/home_map.js and static/js/catalog_map.js: remove Google-coordinate jitter and competing idle zoom, use shared cluster handler, update home cluster membership only when changed, preserve viewport and one card. Preserve Leaflet/iframe fallback behavior.
- [x] Load shared controller in home.html and place_list.html; add scoped motion/chooser styles to static/css/components/google_maps.css. Preserve all existing dirty edits.
- [x] Verify Node behavior and real browser at 360/390/1440 plus 768/1024/1280 where practical, AZ/RU/EN, empty/single/many/duplicates, rapid click/drag/filter, keyboard and reduced motion. Current local public data + expanded in-browser fixtures; production DB untouched.
- [x] Record working Google Maps interaction to output/playwright; report genuine runtime capability and remaining limitations. Do not claim smoothness from tests/CSS alone.

Verification and limits: [implementation report](2026-09-10-public-map-motion-status.md). The raster native duration and vector/Advanced browser limitation are explicitly recorded.
