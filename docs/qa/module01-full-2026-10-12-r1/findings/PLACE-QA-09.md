# PLACE-QA-09 — Tab focus hidden by sticky actions

Status OPEN. P2, LOCAL Chrome153, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51. New finding ID; recent regression attribution UNKNOWN. Existing PLACE-QA-01–08 closures not reopened.

Role owner; endpoint /ru/account/places/2/edit/?fresh=1 on the owned ACCEPT stand (fictional Place2). Native login, valid published Place, viewport768×950, click name AZ then Tab. Expected: focused description and caret visible above actions. Actual: textarea top914.765625/bottom984.765625 at viewport950; fixed actions overlap it. Screenshot shows focused control absent behind footer. Reproduced RU/AZ/EN×768/1024/1280/1440;12 observations of one cause.360/390 specific first-field transition passed. Separate native-click/fresh-context diagnostic confirms initial programmatic focus is not sole cause.

Evidence: ../matrix.result.json (12 FAIL rows), ../diagnostic.result.json, ../screenshots/focused-description-768.png. Full keyboard cycles reached105 applicable tab positions per cell; their1px custom-input geometry oracle cannot by itself establish additional findings.

Source: static/css/pages/owner_place_continuous.css:1 fixed .pc-actions; :14/:21 scroll margins. static/js/owner_place_continuous.js:185–187 centers error-jump targets, but no equivalent general native Tab handling. Sticky occupancy is the likely cause, source-backed; exact minimal repair awaits PLAN. Scope owner continuous focus/scroll only; do not redesign, reorder Tab, change autosave/CAS or publication. No application fix performed.

Acceptance for future plan: fresh native Tab/ShiftTab through currently visible inputs/details/controls on RU/AZ/EN×360/390/768/1024/1280/1440, including dynamic footer/nav heights, error links, long text, reduced motion; bounding rect + occlusion + focused screenshots, no disruptive typing jumps. Custom visually hidden controls must be assessed through their visible focus representation.
