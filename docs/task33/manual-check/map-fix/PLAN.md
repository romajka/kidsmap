# Home map tile failure implementation plan

Scope authorized by the user's screenshot request: fix the homepage OpenStreetMap tile requests and failure presentation, update the running local preview. No production, credentials, provider rotation, commit or push. Preserve completed audit evidence.

Cause: Django sends Referrer-Policy: same-origin; Leaflet tile images inherit it and omit Referer to OSM. The current layer renders upstream image bodies without checking HTTP status. OSM requires a Referer and the canonical tile.openstreetmap.org URL.

- [x] Preserve the current home_map.js, home.html and preview launcher; record the entry hashes.
- [x] Reproduce a valid image body with HTTP 403 in real Chromium; require no rejected tile image to be displayed and a readable localized status.
- [x] Add behavioral JS tests for successful load, rejected HTTP response, network error and unload cancellation/resource cleanup.
- [x] In static/js/home_map.js introduce a Leaflet tile loader that fetches each visible tile with origin-only cross-origin referrer, default browser caching and omitted credentials. Only successful responses become object URLs. Cancel/revoke on unload. On failure remove the basemap layer, retain marker/filter interactions, and show a localized status outside the map.
- [x] In src/catalog/templates/pages/home.html supply AZ/RU/EN background-error copy and update the asset version. Keep the global referrer policy unchanged.
- [x] Run new JS tests and existing home-map filter tests. Verify actual Leaflet rendering with controlled 403/network/success responses, localization, mobile layout and surviving markers; one bounded live provider check, no automated panning or bulk tile downloads.
- [x] Create a versioned preview source manifest overlay for the changed files; copy only verified files into the preview mirror, preserve the synthetic DB, restart, and verify HTTP access. Historical completion manifests stay immutable.
- [x] Save results/screenshots and append the task journal. This run does not repeat the full backend regression or establish provider uptime.

References: https://operations.osmfoundation.org/policies/tiles/ and https://leafletjs.com/reference.html#tilelayer.
