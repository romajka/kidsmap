# Admin Place map — approved local completion

Authorization: user asks to fix all remaining problems and newly found defects in this flow. Scope CE-C-03/04 plus directly related admin location defects; one root, no subagents. No commit/push/deploy/production.

1. Snapshot HEAD/dirty/source/locale, isolated8790, own active_run. Fresh browser RED for no-key keyboard map/manual input and clipping (not just document overflow).
2. change_form.html: unconditional local location JS, conditional external SDK. section_location.html: localized unavailable and live error status.
3. location JS: local point open/confirm/clear and geolocation independent of SDK; explicit unavailable, prevent dead SDK search, reuse state across SDK callbacks if regression confirms it.
4. place_form.js: manual-input action always reveals fields and focuses latitude, does not hide visible inputs.
5. CSS: wrap button group, auto button height/min-height44, no text clipping at360/390 or focus ring clipping; preserve desktop layout. Update own relevant PO/MO keys only, preserve other entries.
6. Browser local native form: blank/saved coordinates, manual keyboard, draft/reload, submit/review/public, blank/invalid pair/range, denied geolocation, repeat init and unavailable/late simulated SDK, stale tabs, search availability. RU/AZ/EN×360/390/768/1024/1280/1440. Relevant existing server/JS checks, no assertions weakened.
7. Inspect screenshots, fix new confirmed defects in same flow, package diff/hash/proofs/NOT RUN, update journal/MASTER, leave local stand and close own active_run.

No changes to address/coordinates validation, source/CAS, publication, ownership/ACL, events business requirements or geocoding integrations. External real providers NOT RUN; local adapter simulations are separate evidence.
