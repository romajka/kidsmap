# Source of truth map

Срез: 2026-09-06. **LOCAL** `main`, `df6fef3` + dirty/untracked; **PRODUCTION** clean `86a0b8c`, ветка `readiness-legacy-migration`, catalog0100 по read-only проверке оркестратора. Это разные версии. Строки ниже указывают LOCAL; при сдвиге строк искать указанный символ. Production агрегаты и точное соответствие отдельных файлов — в deployment/database audit, иначе **UNKNOWN**.

Порядок доказательств для AS-IS: исполняемый код конкретной версии + миграции + read-only DB schema/data aggregates + наблюдаемое public/admin поведение. Документация и Codebase Memory помогают найти реализацию, но не заменяют её. TO-BE/PLANNED не становятся AS-IS от наличия файла плана.

| Domain | Основной источник | Смежные источники / граница |
|---|---|---|
| Django apps/settings | `src/config/settings.py:180` INSTALLED_APPS, `:305` MIDDLEWARE | `config/settings.py:3` — wrapper; `src/catalog/apps.py` выполняет signals/Jazzmin patch. |
| Routes / API | `src/config/urls.py:34`, `src/catalog/urls.py:82` urlpatterns | API Django views, не предполагать DRF: `views.py:47` pricing; LOCAL `phone_views.py:20`, `photo_views.py:74`. |
| Architecture layers | `src/catalog/interfaces/repositories.py`, `repositories/django_repositories.py` | Controllers + services; `views.py`, models и domain_admin также содержат ORM/правила. |
| Place model | `src/catalog/models/place.py:27` Place | FK Category.code, owner, created_by, scalar/JSON compatibility, relations; не только docs matrix. |
| Publication readiness | `src/catalog/services/place_readiness.py:466/:568/:680` | `content_quality.py:416` adapter, admin `domain_admin/place.py:268`. |
| Admin publication / existing-live compatibility | `src/catalog/domain_admin/place.py:269` | Новая/повторная публикация требует readiness; ordinary save live legacy имеет исключение. |
| Owner submission | `src/catalog/controllers/owner_places_controller.py:432/:605/:852` | LOCAL `forms.py:1469` → untracked permanent_place_rules.py; рассинхронизация с readiness. |
| Draft semantics | `src/catalog/forms.py:888/:1538` OwnerPlace forms | Controller defaults/statuses; освобождение required не отменяет типы/отношения/файлы. |
| Public visibility | `src/catalog/services/content_quality.py:236` public_place_queryset | `:355` published_place_queryset мягче; repository55/59 использует public queryset. |
| Verified badge | `src/catalog/services/place_card_validation.py:87` validate_place_card | Отдельный контракт от публикации, public SQL и completeness UI. |
| Pricing | `src/catalog/models/pricing_plan.py:11`, `services/pricing_plans.py:182/:295/:461` | `Place.pricing_plans` property360; scalar sync345; migration0084/0085/0100. |
| Schedule | `src/catalog/models/place.py:28/:649/:678`, `services/place_schedule.py:300/:415` | Public rows514/open status616; legacy parser и migration command отдельно. |
| Taxonomy | `src/catalog/models/category.py` Category/Subcategory | `src/catalog/taxonomy_data.py`, `src/catalog/domain_admin/category.py`, `src/catalog/management/commands/seed_catalog_taxonomy.py`; FK vs static seed различать. |
| Location / maps | `src/catalog/services/locations.py:515/:551`, `services/geocoding.py` | Place district/metro strings; Specialist Region/District/MetroStation FK в models/specialist.py; maps static/js отдельно. |
| Authentication | `src/catalog/controllers/auth_controller.py:74`, `forms.py:395/:566/:807`, `views.py:1643/:1707` | OTP services/email_verification.py + repository; LOCAL Google google_auth.py, settings allauth, migration0101. |
| Email identity | `src/catalog/models/user.py:90` UserEmailVerification | Profile email update != verified claim; LOCAL0101 unique lower(trim(email)) не считать применённой на prod. |
| Permissions | `src/catalog/services/place_access.py:54/:78/:88` | owner_place_use_cases.py25/37; UserProfile role удалена0097; Django staff/model perms отдельно. |
| Ownership / teams | `src/catalog/models/owner.py:25/:94/:210/:270` | ownership_use_cases.py24; owner_team_controller.py; scopes per Place, legacy null не выдаёт права. |
| Moderation | `src/catalog/controllers/owner_reviews_controller.py`, `models/owner.py:94`, `domain_admin/` | Статусы Place/Event/reviews различны; audit PlaceChangeAudit/OwnershipRequestAudit. |
| Reviews / ratings | `src/catalog/models/review.py`, `services/review_use_cases.py:89/:132` | content_quality.py365 public rating filter, review_moderation.py40; SpecialistReview отдельно. |
| Events | `src/catalog/models/place.py:698` Event; `controllers/owner_events_controller.py:40/:58/:81` | Legacy temporary Place существует одновременно; features.py и public expiry. |
| Specialists | `src/catalog/models/specialist.py:93/:255/:359/:415` | services/owner_specialist_use_cases.py; views.py1814 documents,1837 list,2084 detail. |
| Media | `src/catalog/services/image_uploads.py`, `models/place.py:625` PlacePhoto | LOCAL photo_views.py/photo_gallery.py; owner controller680+ on_commit deletion; nginx/direct media access отдельно. |
| Admin composition | `src/catalog/admin.py:4` → domain_admin package | domain_admin/__init__.py163/562 sidebar/context; place.py, user.py, specialist.py; proxy_apps + admin templates. |
| Public UI | `src/catalog/templates/base.html`, `templates/pages/home.html`, `templates/catalog/place_list.html`, `place_detail.html` | static/css/site.css и imports, static/js/catalog_map.js/home_map.js; templates + CSS + JS проверять вместе. |
| Owner UI | `src/catalog/templates/pages/owner_place_*.html`, LOCAL `permanent_place_form.html` | LOCAL permanent_place_wizard/photos/pricing assets и forms/controllers gates. |
| Localization | `src/config/settings.py` LANGUAGES, `src/config/urls.py` i18n_patterns | locale/*/LC_MESSAGES, *_az/ru/en model fields, services/locations.py, inline translation dictionaries. |
| SEO title/meta/schema | `src/catalog/services/seo.py:59/:193/:359` | templates/base.html, context_processors.py, services/public_urls.py; LocalBusiness/Event payload проверять по конкретному builder. |
| Canonical / hreflang / slugs | `src/catalog/services/public_urls.py`, `services/slugs.py`, `middleware.py` | models get_absolute_url, context_processors.py, config urls default-language redirects. |
| Sitemap / robots | `src/catalog/sitemaps.py:14/:56/:66/:89`; `src/config/views.py:22/:76` | SEO landing visibility services/seo_landing_visibility.py109; actual public visibility queryset. |
| SEO audit/fixes | `src/catalog/services/seo_audit_engine.py:28`, seo_fix_engine.py | models/seo.py; audit_* commands vs apply_seo_fixes/rollback_seo_change; audit results may themselves write DB. |
| Product analytics | `src/catalog/services/tracking.py:144/:335`, visit_tracking.py:14 | models/site.py SiteVisit/FunnelEvent; views.py545 origin/rate checks; client tracking assets. |
| GA4 / admin analytics | `src/catalog/services/google_analytics_reporting.py:60/:241`, admin_analytics.py:60 | Settings/DB toggles separate from evidence of external GA ingestion; не раскрывать credentials. |
| Background processing | `src/catalog/services/indexnow.py:29/:192`, indexnow_signals.py | ThreadPoolExecutor + on_commit, не durable Celery queue; cron подтверждать на сервере. |
| DB schema / integrity | `src/catalog/models/`, `src/catalog/migrations/` | Реальная PostgreSQL introspection + django_migrations; model state не доказывает deployed schema. |
| Migration tools | `src/catalog/management/commands/database_inventory.py`, migrate_legacy_database.py, verify_database_transfer.py | Legacy pricing/schedule/team команды; проверять запись/флаги перед запуском. |
| Tests | `src/catalog/tests.py`, `src/catalog/testcases/`, `scripts/run_kidsmap_tests.sh` | Discovery patterns и CI labels проверять; local/prod DB isolation обязательна. |
| Browser QA | `scripts/test_mobile_navigation.sh`, `scripts/test_footer_overflow.sh` | LOCAL test_photo_editor.cjs/test_phone_reveal.cjs; реальные снимки/console, а не только наличие теста. |
| Runtime / dependencies | `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `scripts/start-server.sh` | Серверные image/process/versions проверять read-only, не выводить .env. |
| Deployment / release | `scripts/deploy-server.sh`, `release-server.sh`, `deploy-production.sh`, `.github/workflows/deploy.yml` | Scripts описывают механизм; deployed HEAD/container image доказываются отдельно. |
| Nginx / static / media | `deploy/nginx/kidsmap.az.conf`, Docker volumes, settings STATIC/MEDIA | Репозиторный nginx template не доказывает активный server config. |
| Backups / operations | `scripts/backup-db.sh`, `scripts/run_seo_cron.sh` | Наличие backup script != работающий schedule/проверенный restore; cron/timers/dumps только read-only audit. |
| Existing agent system | `.agents/agents/`, `.agents/rules/agent-orchestration.md`, `.agents/skills/` | Актуальный registry/orchestrator; не создавать параллельную папку agents по примеру из prompt. |

## Источники, требующие критического чтения

- `AI_HANDOFF.md`: история проекта и навигация; global owner-role текст и старый local path устарели.
- `docs/PERMANENT_PLACE_FIELD_MATRIX.md`: untracked документ со спорными ручными выводами. Текущий код содержит `price_mode`, `place_readiness.py`, пять schedule modes; 120 символов не блокируют canonical readiness.
- `docs/FULL_READINESS_SYNC_REPORT.md` и implementation reports — заявления о проделанной работе, которые надо сверять с dirty diff; LOCAL owner path уже показывает иной gate.
- Новые Google/photo/phone/wizard файлы — LOCAL AS-IS рабочего дерева, но не автоматически committed или production AS-IS.
- Для неподтверждённого server DB usage писать UNKNOWN. Не переносить приватные строки, credentials, dumps или logs в knowledge.
