# Living Map: animated journeys revision

User feedback authorizes a stronger, visibly animated map background, preserving existing KidsMap layout and controls. The earlier tiny-particle treatment was insufficient.

- [x] Add a small scene module and real behavior tests for safe landmark placement, visibly growing routes, smooth cycle reset and reduced motion.
- [x] Integrate into the existing Canvas lifecycle. Reuse brand colors and existing category icon geometry. Use larger map/park/art/book/trophy landmarks, route tracing, traveling beacons and arrival growth. Keep content masks, hidden-tab cancellation and adaptive quality.
- [x] Place scenes deliberately in open horizontal bands between sections, with smaller mobile landmarks. Keep scattered dots secondary. Connect the hero bands with rounded side streets on desktop.
- [x] Inspect actual animated desktop/mobile frames, capture a motion preview, run scene tests plus existing background and interaction checks. Record current limits without re-running unrelated baseline failures. See `docs/LIVING_MAP_JOURNEYS.md`.

Files: new `static/js/living_map_scene.js`, `static/js/tests/living_map_scene.test.js`; modify only `static/js/living_map_background.js`, homepage asset wiring and living-map documentation. No backend, deployment, commit or push.
