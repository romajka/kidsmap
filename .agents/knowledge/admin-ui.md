# Admin UI KidsMap

Срез: 2026-09-06; AS-IS устанавливается по коду, не по design handoff или плану.
Production baseline `86a0b8c` и локальное dirty дерево рассматриваются отдельно: [deployment.md](deployment.md).
Общие контракты: [architecture.md](architecture.md), [source-of-truth.md](source-of-truth.md).

## Реальная структура

- Django Admin с Jazzmin: `src/config/settings.py:181`.
- Template lookup сначала `BASE_DIR/templates`, затем `src/templates`, затем app templates: settings `:325–332`.
- Общий admin shell: `templates/admin/base.html`.
- Дополнительный общий слой: `templates/admin/base_site.html`; CSS `:6`, notifications JS `:11`.
- Предметные admin templates находятся и в `templates/admin/catalog/`, и в `src/catalog/templates/admin/catalog/`.
- Не считать два корня дубликатами: Django loader precedence определяет активный override.
- Backend registration: `src/catalog/admin.py`, `src/catalog/domain_admin/`, `src/catalog/proxy_apps/*/admin.py`.
- Frontend-admin отвечает за отображение и взаимодействие; permissions, form validation и save actions — Django/security.

## Карта поверхностей

| Поверхность | Источники |
| --- | --- |
| Общие стили/навигация | `static/admin/css/kidsmap_admin.css`; `static/admin/js/kidsmap_admin_sidebar.js` |
| Toast/modal | `static/admin/js/kidsmap_notifications.js`; `templates/admin/base_site.html:11` |
| Place form/list | `src/catalog/domain_admin/place.py:1546`; templates `admin/catalog/place/change_form.html`, `change_list.html` |
| Place sections | `src/catalog/templates/admin/catalog/place/form/` |
| Place JS | `static/admin/js/kidsmap_place_form.js`, `_location.js`, `_media.js`, `_duplicates.js`, `_json_import.js` |
| Event form/list | `src/catalog/domain_admin/place.py:727`; `src/catalog/templates/admin/catalog/event/` |
| Users/staff | `src/catalog/domain_admin/user.py`; templates `user/`, `staffaccessuser/`, `siteregistereduser/` |
| Moderation/ownership | `domain_admin/review.py`, `owner.py`; placeownershiprequest/placereview templates |
| Taxonomy | `domain_admin/category.py`; `static/admin/js/kidsmap_taxonomy.js`, category JS |
| SEO audit UI | `domain_admin/seo.py`; `templates/admin/catalog/seoauditrun/`, `seoissue/` |
| Statistics | `domain_admin/site.py:480`; `templates/admin/catalog/site_analytics.html`; analytics.md |

Неполные domain_admin/template пути в таблице разрешаются относительно `src/catalog/`.

## Place и Event контракты

- `PlaceAdminForm` находится в `domain_admin/place.py:121`, EventAdminForm `:459`.
- Place templates назначаются `:1603–1607`; отдельно change/delete/selected-delete поверхности.
- Place form рендерит поля вручную: комментарии `:1679`, список `:1722`.
- `_build_place_carryover_fields` `:2087` сохраняет поля, которые новая форма не отображает явно.
- При редизайне нельзя выбросить carryover/management fields: это может обнулить данные при save.
- Admin completeness indicator не заменяет publication readiness/backend validation.
- Pricing editor и schedule editor должны сохранить сериализацию payload и form errors.
- JSON importer заполняет форму; это не свободная API-запись модели.
- Export не является полным backup/round-trip: см. `docs/PERMANENT_PLACE_FIELD_MATRIX.md:285` и реальный export view.
- Для удаления/восстановления использовать существующие admin workflows; аудит не нажимает destructive actions.

## AS-IS и планы

- `docs/superpowers/plans/2026-09-04-admin-notifications-modals-revamp.md` — план, не доказательство всех реализованных пунктов.
- `kidsmap_notifications.js` действительно подключён через base_site; это проверено по source.
- Design handoff HTML в `docs/design_handoff_zip5/` — визуальные исходники/референсы, не runtime templates.
- Локальные изменения owner wizard не означают, что admin перешёл на ту же структуру.
- `docs/PERMANENT_PLACE_FIELD_MATRIX.md` полезен для связей и скрытых полей, но описывает dirty local snapshot.

## Риски

| Приоритет | Факт/риск | Уверенность |
| --- | --- | --- |
| P2 | Statistics selector90 использует GA year KPI; `admin_analytics.py:37–42`, selector template `:21` | Высокая, source |
| P2 | GA reporting синхронно делает до7 report calls без собственного cache/explicit timeout | Высокая по вызовам; latency не измерена |
| P2 | SEO audit/actions пишут audit rows, включая часть dry-run; не запускать на prod в read-only режиме | Высокая |
| P3 | Большой Place JS (~74KB) и ручной form/carryover contract повышают стоимость регрессии | Source; не доказанная runtime ошибка |

Проблемы analytics подробно описаны в [analytics.md](analytics.md); SEO/XSS — [seo.md](seo.md).
Не создавать копии одного finding с разными приоритетами: владелец и общий ID определяются master audit.

## Проверки перед handoff

- Django admin permission matrix: staff без model permission, moderator, owner, superuser — согласно текущему backend.
- Render add/change с ошибками; inline management forms; hidden/carryover values; save/reload на изолированных данных.
- Place prices/schedule/location/media; Event даты; moderation reason; duplicate handling.
- Клавиатура/focus/escape/return-focus для modal; toast aria-live и error persistence.
- Mobile/tablet и длинные AZ/RU/EN строки; плотность admin не должна ломать controls.
- Проверить Console, Network, static404 и фактически активный template override.
- Relevant suites: `src/catalog/testcases/admin.py`, `place_taxonomy_admin.py`, `place_filepond_admin.py`, `events_feature.py`.
- Source-level discovery не проверял авторизованные browser flows. Не выдавать его за UI PASS.
- Production audit: не сохранять формы, не применять JSON import, не запускать audit/fix actions; role-authenticated просмотры только при доступе.
