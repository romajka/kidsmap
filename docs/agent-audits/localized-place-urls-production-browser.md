# Live public rendered URL verification

2026-09-15, browser-qa. Parent reports deployed source47859f54 with localized URLs enabled; this role independently inspected live HTTP-rendered pages, not deployment files. No login, application POST, production fixture mutation or source modification.

Selected translated public Place4 from supplied `public-url-map.json`:
- AZ `/place/4-baki-cudo-telim-merkezi/`
- RU `/ru/place/4-bakinskii-centr-obucheniya-dzyudo/`
- EN `/en/place/4-baku-judo-training-center/`

Command: `node /tmp/kidsmap-url-ops/live-browser.cjs`, exit0. Real headless Chromium1228 / installed Playwright, fresh anonymous context. GET requests allowed only kidsmap.az and font assets fonts.googleapis.com/fonts.gstatic.com. All non-GET, tracking/analytics and other hosts aborted (18 blocked requests). No production credentials used.

PASS: each language URL final200 with expected localized path and canonical. Desktop and mobile language-link hrefs exactly match supplied map. Actual desktop dropdown click navigation AZ→RU→EN arrives at each matching URL with visible heading and no redirect loop. Public heading/content visible at390 and1280 for all3 languages;6 viewport cases, no horizontal overflow. Zero pageerrors, zero observed HTTP400+ responses.

Screenshots: `/tmp/kidsmap-url-ops/live-place-{az,ru,en}-{390,1280}.png`. Visually inspected RU390 and EN1280: translated headings, image and card content rendered, no clipped horizontal layout. Raw structured result: `live-browser-result.json`.

Boundaries: one public place sample, not all225 language URLs (parent owns comprehensive HTTP checks). Mobile switch hrefs checked but mobile drawer clicks not exercised. External analytics/maps intentionally blocked; this is URL/navigation/render proof, not external integration verification. No confirmed blocker in this bounded check.
