# OPEN functional follow-up, separate from applied CSS and pending menu JS

Event/Specialist shared sort links use `?q=QA+Queue+2&sort=created_desc`; native selection redirects to `?e=1`, loses q, reload retains incorrect state. Current actual-source run:3locales×2widths×2queues,24FAIL for sort/reload +12dependent NOT RUN. Exact prepatch stylesheet replay reproduced both queues atRU1024 with1matching record before sort and identical e=1 after. CSS SHA in replay equals approved prepatch SHA; shared JS/backend source unchanged in this run. This is not attributed to the CSS fix.

Evidence: native-flows-r2.js.result.json, accepted-functional.json, native-sort-prepatch-replay.js.result.json,2prepatch-sort-replay PNG. No automatic new historical ID mapping, no fix/closed ID. Need separate source cause and concrete approved plan before change. Pending MENU_SUPPLEMENT_PLAN covers row popover placement/lifecycle only and will not fix sorting.

Shared Event/Specialist column menu checkboxes reference Place-only `column-col_*` headers, absent in their own tables. Dropdown geometry was checked; real column toggling there is NOT RUN, not PASS. Treat source support/other historical task mapping separately; do not silently extend menu-placement proposal to columns/backend.
