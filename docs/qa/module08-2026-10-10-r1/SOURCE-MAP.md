# Source → реальный контракт → свежая проверка

| Source | Контракт / связь | Evidence |
|---|---|---|
| catalog/domain_admin/volunteer.py:get_urls/moderation_hub_index/detail | admin.site.admin_view, paginator25, detail errors409 и обязательная причина | matrix/ACL/flows |
| catalog/services/moderation_hub.py:reviewer_scopes/query/detail | content через platform place.publish, affiliation через change_placeownershiprequest; свежий actor | acl195 |
| catalog/services/volunteer_proposals.py:review | ревизии идут через publication.apply/return/reject, не прямой UI ORM | nativeflows |
| catalog/services/publication.py | candidate/base_content_version/dependencies vs live; photos/related apply | flows2/gallery-finish, unchangedtests |
| catalog/services/volunteer_places.py + domain_admin/volunteer.py:delete | created_by actor + owner=NULL scope, fresh role/soft delete | acl/role revoke/delete |
| catalog/services/staff_roles.py | preset роли, activate/revoke path staffaccessuser | flows3-resume |
| catalog/domain_admin/place.py:EventAdmin/EventAdminForm + services/event_domain.py | updated_at/organizer lock, действующий organizer required; Event1 badfixture denied, Event2 valid native flow | editor-validation/editor-finish |
| catalog/domain_admin/specialist.py:SpecialistAdminForm/bulk actions | required fields и expected_updated_at в form; bulk status updates отдельны | specialist-save-proof/specialist-valid-finish, tests |
| templates/admin/volunteer/hub_index/detail | таблица без pager, plain string media | MOD-QA-01/02 |
| static/admin/js/kidsmap_notifications.js | SVG href попадает в focusables, warning fallback | MOD-QA-05 |
| static/admin/js/kidsmap_place_changelist.js | real AJAX guards + hardcoded confirmation | supplement/MOD-QA-06 |
| static/admin/css/pages/kidsmap_changelist.css | nowrap/min width + breakpoint при sidebar | MOD-QA-03 |
| templates/admin/catalog/specialist/change_form.html | AdminField.errors iterated as string | MOD-QA-07 |
| templates/admin/catalog/includes/km_changelist_search_panel.html | place-only filter whitelist; primary configs других моделей игнорируются | drawers/filter-contract/MOD-QA-08 |

Paths здесь относительны src/ либо root для static. Graph-first выполнен до широкого source exploration; dynamic ORM/admin registration проверены чтением source. Production UNKNOWN. Это source map, не rendered-browser доказательство; raw browser files выше являются отдельным подтверждением.
