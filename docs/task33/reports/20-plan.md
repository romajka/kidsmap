# Stage20 Implementation Plan

Scope authorized by prompts/20.md only; no production/commit/push/later stages.

- [x] Establish failing real integration tests: shared verified venue vs coordinate overlap, filtered members/prices, missing/invalid coordinates, address edit and Event preservation.
- [x] Shared map_payload serializer consumes PlaceListFilters and prepare_cards, groups only active confirmed Location links, returns numeric coordinate points with independent members; include venue-only coords and per-card missing marker.
- [x] Catalog popup renders independent members, maps all member URLs to one marker, retains visual clusters; catalog counts businesses and actual missing coordinates.
- [x] Home consumes same serializer and server filter endpoint, refreshes membership/popups with cancellation guards; no duplicated business matching rules.
- [x] Detach only edited Place venue link on ordinary address/coord updates and approved publication updates. Never mutate shared Location/Event history.
- [x] Run isolated QA04 targeted/adjacent suites, checks/migration state/cleanup, JS syntax/diff. Real independent browser AZ/RU/EN x 320/360/390/768/1024/1280/1440 with map transport doubles and unavailable transport, popup keyboard/resize.
- [x] Independent integration review, final source SHA/preservation manifest/report/journal; release only own active_run.

Files: services/map_payload.py, catalog_structure.py, publication.py, public_presentation.py, repositories/django_repositories.py; controllers/place_controller.py/home_controller.py/public_map_api.py; urls.py; catalog_map.js/home_map.js; place_card.html/place_list.html/home.html; scoped CSS if needed; test_task33_map.py/test_task33_home_map.py. Roles: primary frontend-reviewer; bounded home worker; independent browser/integration.
