# Stage20 — homepage map bounded implementation

Authorization: stage20 APPROVED IMPLEMENT, delegated by lead frontend-reviewer. Scope: homepage controller/template/JS, GET-only public map endpoint, targeted tests. No production, commit, push or later-stage work. Shared dirty WORKTREE preserved; source HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e` is not the version of modified source.

## Behavior / source evidence

- `HomeController.build_context`: server `PlaceListFilters` + public repository queryset + common `serialize_map_places`; initial business count sums members, not physical pins.
- `public_map_api.public_map`: public-only GET endpoint `/api/catalog/map/`, HTTP405 for mutations, no cached private responses; shared catalog filters/grouped serializer; response points/count.
- `home_map.js:serverFilterUpdater`: aborts prior requests, rejects late responses, closes popups and clears stale markers before filtering. Each new server result rebuilds map markers and uses current point members. Google/Leaflet transport and visual clustering retained.
- `renderPopupContent`/`renderMemberPopup`: independent member details/contacts/prices, matching activity/group names, numeric coordinate-only route URL; scrollable shared-point members. No frontend catalog business filter rules.
- `home.html`: map API URL reversed in current locale, count is businesses, map asset initializes even when initial filtered result is empty, enabling filter reset.

Owned source files: `src/catalog/controllers/home_controller.py`, new `src/catalog/controllers/public_map_api.py`, insertion into `src/catalog/urls.py`, `src/catalog/templates/pages/home.html`, `static/js/home_map.js`. Tests: `src/catalog/testcases/test_task33_home_map.py`, `docs/task33/tests/stage20_home_map.test.cjs`.

## Executed verification

- `node --check static/js/home_map.js`: exit0.
- `node docs/task33/tests/stage20_home_map.test.cjs`: exit0, grouped business links, numeric route, server business-filter boundary, popup close, stale markers removed during pending request and stale response rejection PASS. Meaningful popup, numeric route and pending-markers RED assertions observed before corresponding implementation.
- `git diff --check`: exit0.
- `python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_home_map --output /tmp/task33-20-home-red`: exit2 safety environment failure; no DB created.
- `./.venv/bin/python docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_home_map --output /tmp/task33-20-home-red2`: exit3,3/3 failed301 due to noncanonical default-language fixture `/az/`; this is not valid missing-feature RED evidence.
- `./.venv/bin/python docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_home_map --output /tmp/task33-20-home-green`: exit2 sandbox socket safety PermissionError; no DB created.
- Same command with output `/tmp/task33-20-home-green2`, approved sandbox escalation for isolated QA04: exit3,3/3 fixture301 failures; no application conclusion. Corrected fixture to canonical `reverse('public_map')`, retaining HTTP200/405 assertions. Added same-group ART+age endpoint versus catalog integration (age5 excluded / age9 included, matched offers only ART).

Final corrected4-test DB rerun is owned by parent lead; see main `20.md` for final result and browser worker evidence. This bounded report does not claim completion before those checks. External Google/Leaflet integrations and production NOT RUN. Own source review is not independent review.

## Remaining acceptance

Corrected endpoint PostgreSQL tests, locale/responsive rendered-browser matrix, map-popup keyboard/resize and map-unavailable evidence are coordinated by parent. Shared venue/no-coordinates grouping and historic Event snapshot acceptance belongs to the common map/backend scope in main report.
83f13a09649b6abcdb04091afb070f427f457dd3801d38effa353b7523228872  src/catalog/controllers/home_controller.py
fe0bbd838ac87de20229d6a980c9aa24f792384928eaad749b732a1fc610acb3  src/catalog/controllers/public_map_api.py
dc30872d7149d63d6b93e4cfc90542cd0b47181fee498bdd41a4f43d5c43670d  static/js/home_map.js
f0f3c8bc7f22558fede92a8c23f93b6e328a51868536ee7011be8db4d264eb8f  src/catalog/templates/pages/home.html
aa449c1ae4476e8c986799c7fb678147f65452ff12a53d43991007d1c65a1438  src/catalog/testcases/test_task33_home_map.py
4ca40b6286bfc520d301597c4160aacc16d02b4468f9c6d0a88cf0fb0c04d5aa  docs/task33/tests/stage20_home_map.test.cjs
