# KidsMap Living Map Background Implementation Plan

**Goal:** Add a subtle, brand-native animated map behind the existing homepage, through the footer.
**Architecture:** One viewport-sized Canvas 2D, mounted directly under body content. Document-space dots and six curved routes scroll naturally. Cached section bounds control intensity; cached exclusion rectangles protect readable content. No dependencies or application/data changes.
**Tech Stack:** Existing Django SSR, vanilla JavaScript, CSS tokens, Node tests and Chromium browser checks.
**Spec:** User attachment `pasted-text-1.txt`, supplied September 9, 2026.

## Scope and source

LOCAL HEAD `fa169b3beaf2f187e48d2196cd6a999ef602be07`; preserve the six existing dirty homepage/rail/map files. Current user request explicitly authorizes implementation and local verification. No commit, push or production operation. Execute inline under that authorization.

Actual tokens: `--brand-turf: #136f38`, `--brand-celadon: #a8d59b`, `--brand-spruce: #0d4924`, `--brand-brick: #c94a4a`. Homepage paper is `#f7f9f5`. Body already isolates stacking; main is layer 0 and header layer 30. Keep these unchanged. Hero, rail, categories, map, steps, owner, FAQ and footer are existing sections; search and stats are inside hero. Existing home CSS breakpoints include 767, 1023, 1100.

## Tasks

- [x] Add real Chromium regression tests in `scripts/tests/living_map_{background,quality,lifecycle,adaptive}.browser.js`: test Canvas output, reduced-motion scheduling, controlled hidden-tab signal, resize/DPR cap, touch and Canvas fallback. Initial enhancement and adaptive-density tests were observed failing before implementation. Browser tests replace the initially considered mocked Node boundary.
- [x] Add `static/js/living_map_background.js`: named initialization, generation, layout, pointer, rendering, scheduling and cleanup functions. Use 96/64/32 dots, 8/5/3 pins; six sparse routes, 190px pointer radius, <=12px parallax, <=10px repulsion. Low opacity scaled by section. Cache layout on resize/content resize, never measure every animation frame. Stop hidden/reduced loops and restore on pageshow. Lower density after sustained slow frames.
- [x] Add `static/css/pages/living_map_background.css`: decorative fixed layer, pointer-events none, no layout effect; CSS reduced-motion contract. Only link assets and add one aria-hidden canvas from `pages/home.html`; never modify component layout or colors.
- [x] Run Node checks and targeted isolated Django homepage tests. Capture baseline and changed browser evidence at 375/390/768/1024/1280/1440 and AZ/RU/EN. Verify controls, map fallback, FAQ/footer, pointer, scroll, resize, reduced motion, hidden tab, no canvas and JS-disabled fallback. Inspect screenshots and animation frame timings; tune density/opacity if necessary. Existing Django failures were reproduced without the new enhancement; live map provider and physical-device performance remain verification limits.
- [x] Save implementation and verification evidence in `docs/LIVING_MAP_BACKGROUND.md`, including frame-rate variability and external-service limits.
