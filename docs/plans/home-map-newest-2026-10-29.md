# Homepage map newest-first implementation plan

Goal: Newly added public places appear first in the homepage map list and initial map page, including across the 100-record boundary. Search, category, district and age filters keep the same ordering. Drafts stay private.

Authorization: User requested this map/list correction and chose “Новые сверху по умолчанию”. Execute inline within this scope. Existing unrelated changes must be preserved; entry worktree clean at 6ceeea27.

Architecture: Keep legacy numeric ascending map cursors compatible. Add an explicit homepage map_order=newest parameter with descending ID keyset traversal. Preserve that order through serialization. Flatten shared-venue members and sort newest IDs first in the homepage list; preserve shared map identity. No schema or content changes.

Files: public_map_page.py (descending window), public_map_api.py (opt-in), map_payload.py (optional preserved order), home_controller.py (newest initial page), home_map_search.html (persistent hidden parameter), home_map_explorer.html (localized order description), home_map.js (flat list ordering), relevant Python/JS regression tests.

- [x] Write failing regressions for newest first page across >100 records, complete cursor coverage, filtering/private exclusion, initial homepage parity, and interleaved shared-venue list members.
- [x] Run regressions against current source to confirm failure.
- [x] Implement descending keyset and preserve serialization order only for opt-in homepage; keep existing API behavior intact.
- [x] Flatten/sort list members while retaining their actual point, selection and details links. Describe newest ordering in AZ/RU/EN.
- [x] Run affected map/filter/public Python modules and map JS suite in isolated test settings. Inspect rendered browser results at 390/768/1024/1280/1440, languages and filter/empty states.

Map provider: current production page successfully loaded Google Maps, so the screenshot’s unavailable state is not yet a reproduced persistent failure. Do not claim that independent external-provider problem fixed without evidence.

Validation: 59 isolated SQLite tests and 36 JavaScript tests pass; rendered AZ/RU/EN at390 and1440 plus RU768/1024/1280, all checked without horizontal overflow. PostgreSQL 17 repeat: 59 tests passed, no skips/errors. Production activation is recorded separately in the release report.
