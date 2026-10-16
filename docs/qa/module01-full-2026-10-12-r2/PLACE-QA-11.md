# PLACE-QA-11 — admin keyboard focus covered by bottom Save panel

P2 OPEN, LOCAL Chrome153, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 plus approved PLACE-QA09/10 diff. Attribution to a recent regression UNKNOWN; admin source untouched by the repairs. Different source/role from owner-only PLACE-QA09; old scoped PLACE-QA05 dropdown closure not reopened.

Native reproduction: admin login → `/ru/admin/catalog/place/2/change/` on owned repair profile → click AZ name → Tab to description → Tab to category picker. At390×950 the focused `.km-pf-picker-btn` has top907.65625/bottom949.65625/height42. Its centre hit-tests to bottom Save button `.km-pf-btn--primary`, not to focused category. Actual PNG manually inspected: category selector is behind the bottom panel. Full native admin cycles RU/AZ/EN×360/390/768/1024/1280/1440 all found obscured applicable form controls; individual styled inputs/raw fraction geometry are not separate findings.

Evidence: `../module01-completion-2026-10-12-r1/admin-focus-diagnostic.result.json`, `admin-keyboard.result.json`, `screenshots/admin-confirmed-hidden-focus-390.png`. Source: `static/admin/css/pages/kidsmap_place_form.css:3319` bottom sticky panel, admin template `change_form.html:236`. Controller `static/admin/js/kidsmap_place_form.js` has no general form native-focus visibility handling. This finding blocks full local module01 acceptance. No repair performed for this ID.

Future bounded repair: admin focus/scroll only, measured actual sticky occupancy and minimal immediate correction after native focus; preserve dropdown, modal, validation, readiness, publication/CAS and save actions. New plan is `docs/superpowers/plans/2026-10-12-place-qa11-admin-focus.md` and needs separate scope approval.
