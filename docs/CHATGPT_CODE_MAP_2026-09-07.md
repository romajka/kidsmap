# KidsMap — техническая карта кода

Дата: 2026-09-07. LOCAL HEAD: `dba2225c0e1d5c41a4406cf7cb9f9ce018b2c648` плюс рабочие изменения.

Основной документ: `docs/CHATGPT_PROJECT_CONTEXT_2026-09-07.md`.

Это индекс файлов, классов, функций и полей моделей, а не полный архив кода. Для реализации нужны соответствующие исходники. Номера строк относятся к рабочему дереву при генерации. Значения настроек и данные пользователей не копируются.

## Охват

Исходники приложения, Python-конфигурация, публичные и административные HTML/CSS/JS, переводы, nginx и workflows. Ниже отдельно перечислены scripts. Не включены media, staticfiles, backups, .env, виртуальные окружения и runtime caches.

## Верхний уровень и скрипты

```text
manage.py
requirements.txt
Dockerfile
docker-compose.yml
scripts/backup-db.sh
scripts/build-server.sh
scripts/build_place_form_icons.py
scripts/check_volunteer_admin.py
scripts/ci_seo_check.sh
scripts/deploy-production.sh
scripts/deploy-server.sh
scripts/migrate.sh
scripts/place_wizard_matrix.py
scripts/publish-main.sh
scripts/release-server.sh
scripts/run_kidsmap_tests.sh
scripts/run_seo_cron.sh
scripts/setup-github-ssh.sh
scripts/start-server.sh
scripts/test_footer_overflow.sh
scripts/test_mobile_navigation.sh
scripts/test_phone_reveal.cjs
scripts/test_photo_editor.cjs
scripts/test_review_cooldown.cjs
scripts/test_review_submission.cjs
```

## Файлы по каталогам

### src/catalog

```text
src/catalog/__init__.py
src/catalog/admin.py
src/catalog/apps.py
src/catalog/content_data.py
src/catalog/context_processors.py
src/catalog/controllers/__init__.py
src/catalog/controllers/account_controller.py
src/catalog/controllers/auth_controller.py
src/catalog/controllers/engagement_controller.py
src/catalog/controllers/home_controller.py
src/catalog/controllers/owner_events_controller.py
src/catalog/controllers/owner_places_controller.py
src/catalog/controllers/owner_reviews_controller.py
src/catalog/controllers/owner_team_controller.py
src/catalog/controllers/ownership_controller.py
src/catalog/controllers/place_controller.py
src/catalog/controllers/place_reviews_controller.py
src/catalog/controllers/seo_controller.py
src/catalog/controllers/site_reviews_controller.py
src/catalog/controllers/tracking_controller.py
src/catalog/domain_admin/__init__.py
src/catalog/domain_admin/category.py
src/catalog/domain_admin/owner.py
src/catalog/domain_admin/place.py
src/catalog/domain_admin/review.py
src/catalog/domain_admin/seo.py
src/catalog/domain_admin/site.py
src/catalog/domain_admin/specialist.py
src/catalog/domain_admin/ui_utils.py
src/catalog/domain_admin/user.py
src/catalog/domain_admin/volunteer.py
src/catalog/forms.py
src/catalog/google_auth.py
src/catalog/indexnow_signals.py
src/catalog/interfaces/__init__.py
src/catalog/interfaces/geocoding.py
src/catalog/interfaces/repositories.py
src/catalog/interfaces/tracking.py
src/catalog/legal_content.py
src/catalog/legal_terms_az.py
src/catalog/legal_terms_en.py
src/catalog/legal_terms_ru.py
src/catalog/management/__init__.py
src/catalog/management/commands/__init__.py
src/catalog/management/commands/apply_seo_fixes.py
src/catalog/management/commands/audit_content.py
src/catalog/management/commands/audit_internal_links.py
src/catalog/management/commands/audit_schema.py
src/catalog/management/commands/audit_seo.py
src/catalog/management/commands/audit_sitemap.py
src/catalog/management/commands/cleanup_migration_junk.py
src/catalog/management/commands/database_inventory.py
src/catalog/management/commands/diagnose_place_visibility.py
src/catalog/management/commands/diagnose_reviews.py
src/catalog/management/commands/geocode_places.py
src/catalog/management/commands/import_places.py
src/catalog/management/commands/migrate_legacy_database.py
src/catalog/management/commands/migrate_legacy_prices.py
src/catalog/management/commands/migrate_legacy_schedules.py
src/catalog/management/commands/migrate_pricing_plans.py
src/catalog/management/commands/recalculate_ratings.py
src/catalog/management/commands/report_legacy_team_access.py
src/catalog/management/commands/restore_featured_places.py
src/catalog/management/commands/rollback_seo_change.py
src/catalog/management/commands/seed_catalog_demo_places.py
src/catalog/management/commands/seed_catalog_taxonomy.py
src/catalog/management/commands/send_test_email.py
src/catalog/management/commands/seo_report.py
src/catalog/management/commands/submit_indexnow.py
src/catalog/management/commands/sync_site_defaults.py
src/catalog/management/commands/validate_places.py
src/catalog/management/commands/verify_database_transfer.py
src/catalog/middleware.py
src/catalog/migrations/0001_initial.py
src/catalog/migrations/0002_place_i18n_fields.py
src/catalog/migrations/0003_place_catalog_improvements.py
src/catalog/migrations/0004_place_photo.py
src/catalog/migrations/0005_place_cover_and_gallery.py
src/catalog/migrations/0006_place_slug.py
src/catalog/migrations/0007_place_likes_count.py
src/catalog/migrations/0008_alter_place_options_placelike.py
src/catalog/migrations/0009_sitesettings.py
src/catalog/migrations/0010_sitesettings_footer_contacts.py
src/catalog/migrations/0011_siteaboutsettings_sitebrandingsettings_and_more.py
src/catalog/migrations/0012_alter_sitesettings_empty_results_image_and_more.py
src/catalog/migrations/0013_place_rating_avg_place_rating_count_placereview.py
src/catalog/migrations/0014_remove_placelike_unique_place_like_per_session_and_more.py
src/catalog/migrations/0015_catalogcontentsettings.py
src/catalog/migrations/0016_placereviewsbyclub.py
src/catalog/migrations/0017_alter_placereview_options_and_more.py
src/catalog/migrations/0018_siteanalytics.py
src/catalog/migrations/0019_sitevisit.py
src/catalog/migrations/0020_place_is_temporary_place_temporary_end_and_more.py
src/catalog/migrations/0021_sitesettings_home_cta_text_az_and_more.py
src/catalog/migrations/0022_funnelevent.py
src/catalog/migrations/0023_userprofile.py
src/catalog/migrations/0024_place_owner_placeownershiprequest_and_more.py
src/catalog/migrations/0025_userprofile_owner_permissions_override_and_more.py
src/catalog/migrations/0026_placechangeaudit_ownerteaminvitation_and_more.py
src/catalog/migrations/0027_userprofile_phone.py
src/catalog/migrations/0028_useremailverification.py
src/catalog/migrations/0029_userprofile_gender.py
src/catalog/migrations/0030_update_public_contacts_defaults.py
src/catalog/migrations/0031_siteregistereduser_staffaccessuser.py
src/catalog/migrations/0032_place_additional_info_place_extra_conditions_and_more.py
src/catalog/migrations/0033_update_footer_phone_default.py
src/catalog/migrations/0034_place_soft_delete_fields.py
src/catalog/migrations/0035_sitesettings_add_social_links.py
src/catalog/migrations/0036_sitegalleryimage.py
src/catalog/migrations/0037_seed_home_hero_site_gallery_images.py
src/catalog/migrations/0038_alter_funnelevent_event_type.py
src/catalog/migrations/0039_expand_catalog_to_azerbaijan.py
src/catalog/migrations/0040_content_moderation_statuses.py
src/catalog/migrations/0041_quarantine_low_quality_public_content.py
src/catalog/migrations/0042_event.py
src/catalog/migrations/0043_alter_place_options_alter_placereviewsbyclub_options.py
src/catalog/migrations/0044_category_alter_event_category_alter_place_category_and_more.py
src/catalog/migrations/0045_category_is_active_subcategory_code_and_more.py
src/catalog/migrations/0046_alter_category_options_alter_subcategory_options.py
src/catalog/migrations/0047_sitesettings_about_hero_image_and_more.py
src/catalog/migrations/0048_alter_category_icon.py
src/catalog/migrations/0049_mariadb_compatible_unique_constraints.py
src/catalog/migrations/0050_migrate_to_hierarchical_districts.py
src/catalog/migrations/0051_placescheduleday_placescheduleinterval.py
src/catalog/migrations/0052_category_color_bg_category_color_text.py
src/catalog/migrations/0053_userprofile_avatar.py
src/catalog/migrations/0054_metrostation_region_specialistspecialization_and_more.py
src/catalog/migrations/0055_seed_specialist_locations_and_specializations.py
src/catalog/migrations/0056_specialist_duration_minutes_specialist_education_az_and_more.py
src/catalog/migrations/0057_specialist_phone_specialist_whatsapp.py
src/catalog/migrations/0058_alter_place_options.py
src/catalog/migrations/0059_seed_educator_specializations.py
src/catalog/migrations/0060_sitesettings_specialists_section_enabled.py
src/catalog/migrations/0061_sitevisibilitysettings.py
src/catalog/migrations/0062_place_lesson_details_and_pricing_plans.py
src/catalog/migrations/0063_event_location_contacts.py
src/catalog/migrations/0064_event_location_filters.py
src/catalog/migrations/0065_eventphoto.py
src/catalog/migrations/0066_sitesettings_events_section_enabled.py
src/catalog/migrations/0067_place_offers_adult_classes.py
src/catalog/migrations/0068_place_phone2_place_phone3.py
src/catalog/migrations/0069_place_multilingual_extra_fields.py
src/catalog/migrations/0070_fix_regional_demo_place_coordinates.py
src/catalog/migrations/0071_category_subcategory_audit_softdelete.py
src/catalog/migrations/0072_subcategory_icon.py
src/catalog/migrations/0073_postgresql_native_constraints.py
src/catalog/migrations/0074_ensure_absheron_region.py
src/catalog/migrations/0075_normalize_public_slugs.py
src/catalog/migrations/0076_place_home_recommendations.py
src/catalog/migrations/0077_place_age_open_ended.py
src/catalog/migrations/0078_place_created_by.py
src/catalog/migrations/0079_sync_public_taxonomy.py
src/catalog/migrations/0080_clean_public_taxonomy.py
src/catalog/migrations/0081_add_ai_referral_event.py
src/catalog/migrations/0082_alter_sitegalleryimage_category.py
src/catalog/migrations/0083_alter_sitegalleryimage_category.py
src/catalog/migrations/0084_pricingplan_relational.py
src/catalog/migrations/0085_pricingplan_integrity_constraints.py
src/catalog/migrations/0086_sitesettings_home_categories_image_and_more.py
src/catalog/migrations/0087_sitesettings_footer_background_image_and_more.py
src/catalog/migrations/0088_sitesettings_about_hero_mobile_image_and_more.py
src/catalog/migrations/0089_seoauditrun_seoissue_seochange.py
src/catalog/migrations/0090_seoissue_cascade_delete.py
src/catalog/migrations/0091_place_custom_price_badge_az_and_more.py
src/catalog/migrations/0092_place_scoped_team_access.py
src/catalog/migrations/0093_backfill_place_scoped_team_access.py
src/catalog/migrations/0094_funnelevent_add_place_signup_events.py
src/catalog/migrations/0095_stage4_neutral_labels.py
src/catalog/migrations/0096_place_schedule_modes.py
src/catalog/migrations/0097_drop_legacy_userprofile_roles.py
src/catalog/migrations/0098_replace_legacy_gmail_contact.py
src/catalog/migrations/0099_alter_place_schedule_mode.py
src/catalog/migrations/0100_place_price_mode.py
src/catalog/migrations/0101_unique_user_email.py
src/catalog/migrations/0102_volunteer_place_revision.py
src/catalog/migrations/0103_place_review_cooldown.py
src/catalog/migrations/__init__.py
src/catalog/models/__init__.py
src/catalog/models/category.py
src/catalog/models/owner.py
src/catalog/models/place.py
src/catalog/models/pricing_plan.py
src/catalog/models/review.py
src/catalog/models/seo.py
src/catalog/models/site.py
src/catalog/models/specialist.py
src/catalog/models/user.py
src/catalog/models/volunteer.py
src/catalog/phone_views.py
src/catalog/photo_views.py
src/catalog/proxy_apps/__init__.py
src/catalog/proxy_apps/catalog_content/__init__.py
src/catalog/proxy_apps/catalog_content/admin.py
src/catalog/proxy_apps/catalog_content/apps.py
src/catalog/proxy_apps/catalog_content/models.py
src/catalog/proxy_apps/catalog_moderation/__init__.py
src/catalog/proxy_apps/catalog_moderation/admin.py
src/catalog/proxy_apps/catalog_moderation/apps.py
src/catalog/proxy_apps/catalog_moderation/migrations/0001_initial.py
src/catalog/proxy_apps/catalog_moderation/migrations/__init__.py
src/catalog/proxy_apps/catalog_moderation/models.py
src/catalog/proxy_apps/catalog_system/__init__.py
src/catalog/proxy_apps/catalog_system/admin.py
src/catalog/proxy_apps/catalog_system/apps.py
src/catalog/proxy_apps/catalog_system/models.py
src/catalog/proxy_apps/catalog_users/__init__.py
src/catalog/proxy_apps/catalog_users/admin.py
src/catalog/proxy_apps/catalog_users/apps.py
src/catalog/proxy_apps/catalog_users/models.py
src/catalog/repositories/__init__.py
src/catalog/repositories/django_repositories.py
src/catalog/repositories/geocoding_repositories.py
src/catalog/repositories/tracking_repositories.py
src/catalog/services/__init__.py
src/catalog/services/admin_analytics.py
src/catalog/services/auth_redirects.py
src/catalog/services/content_quality.py
src/catalog/services/district_geometry.py
src/catalog/services/email_verification.py
src/catalog/services/features.py
src/catalog/services/filtering.py
src/catalog/services/geocoding.py
src/catalog/services/google_analytics_reporting.py
src/catalog/services/gsc_api.py
src/catalog/services/image_uploads.py
src/catalog/services/indexnow.py
src/catalog/services/legacy_schedule_parser.py
src/catalog/services/locations.py
src/catalog/services/options.py
src/catalog/services/owner_place_use_cases.py
src/catalog/services/owner_specialist_use_cases.py
src/catalog/services/ownership_use_cases.py
src/catalog/services/permanent_place_rules.py
src/catalog/services/permanent_place_wizard.py
src/catalog/services/photo_gallery.py
src/catalog/services/place_access.py
src/catalog/services/place_card_validation.py
src/catalog/services/place_readiness.py
src/catalog/services/place_review_submission.py
src/catalog/services/place_schedule.py
src/catalog/services/pricing_plans.py
src/catalog/services/public_filter_options.py
src/catalog/services/public_urls.py
src/catalog/services/reactions.py
src/catalog/services/review_moderation.py
src/catalog/services/review_sorting.py
src/catalog/services/review_use_cases.py
src/catalog/services/seo.py
src/catalog/services/seo_audit_engine.py
src/catalog/services/seo_fix_engine.py
src/catalog/services/seo_landing_aggregates.py
src/catalog/services/seo_landing_visibility.py
src/catalog/services/slugs.py
src/catalog/services/staff_activity.py
src/catalog/services/staff_roles.py
src/catalog/services/tracking.py
src/catalog/services/visit_tracking.py
src/catalog/services/volunteer_dashboard.py
src/catalog/services/volunteer_editor.py
src/catalog/services/volunteer_places.py
src/catalog/sitemaps.py
src/catalog/taxonomy_data.py
src/catalog/templates/admin/catalog/category/change_form.html
src/catalog/templates/admin/catalog/category/change_list.html
src/catalog/templates/admin/catalog/event/change_form.html
src/catalog/templates/admin/catalog/event/change_list.html
src/catalog/templates/admin/catalog/event/location_section.html
src/catalog/templates/admin/catalog/event/media_section.html
src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html
src/catalog/templates/admin/catalog/includes/km_icon_sprite.html
src/catalog/templates/admin/catalog/place/change_form.html
src/catalog/templates/admin/catalog/place/change_list.html
src/catalog/templates/admin/catalog/place/form/_field.html
src/catalog/templates/admin/catalog/place/form/_langgroup.html
src/catalog/templates/admin/catalog/place/form/_navitem.html
src/catalog/templates/admin/catalog/place/form/_section_close.html
src/catalog/templates/admin/catalog/place/form/_section_open.html
src/catalog/templates/admin/catalog/place/form/dialogs.html
src/catalog/templates/admin/catalog/place/form/header.html
src/catalog/templates/admin/catalog/place/form/section_basics.html
src/catalog/templates/admin/catalog/place/form/section_location.html
src/catalog/templates/admin/catalog/place/form/section_media.html
src/catalog/templates/admin/catalog/place/form/section_pricing.html
src/catalog/templates/admin/catalog/place/form/section_verification.html
src/catalog/templates/admin/catalog/place/form/sidebar.html
src/catalog/templates/admin/catalog/place/home_recommendation_editor.html
src/catalog/templates/admin/catalog/place/placephoto_inline.html
src/catalog/templates/admin/catalog/place/pricing_editor.html
src/catalog/templates/admin/catalog/place/quality_check.html
src/catalog/templates/admin/catalog/place/quality_report.html
src/catalog/templates/admin/catalog/place_delete_confirmation.html
src/catalog/templates/admin/catalog/place_delete_selected_confirmation.html
src/catalog/templates/admin/catalog/place_restore_confirmation.html
src/catalog/templates/admin/catalog/placeownershiprequest/change_form.html
src/catalog/templates/admin/catalog/placeownershiprequest/change_list.html
src/catalog/templates/admin/catalog/placereview/change_form.html
src/catalog/templates/admin/catalog/placereview/change_list.html
src/catalog/templates/admin/catalog/placereview/moderation_confirm.html
src/catalog/templates/admin/catalog/seoauditrun/change_list.html
src/catalog/templates/admin/catalog/seoissue/change_list.html
src/catalog/templates/admin/catalog/shared_settings_change_form.html
src/catalog/templates/admin/catalog/siteregistereduser/change_list.html
src/catalog/templates/admin/catalog/specialist/change_form.html
src/catalog/templates/admin/catalog/specialist/change_list.html
src/catalog/templates/admin/catalog/staffaccessuser/change_form.html
src/catalog/templates/admin/catalog/staffaccessuser/change_list.html
src/catalog/templates/admin/catalog/user/change_form.html
src/catalog/templates/admin/catalog/user/submit_line_compact.html
src/catalog/templates/admin/volunteer/base.html
src/catalog/templates/admin/volunteer/detail.html
src/catalog/templates/admin/volunteer/edit.html
src/catalog/templates/admin/volunteer/editor_status.html
src/catalog/templates/admin/volunteer/icon.html
src/catalog/templates/admin/volunteer/index.html
src/catalog/templates/admin/volunteer/pagination.html
src/catalog/templates/admin/volunteer/place_card.html
src/catalog/templates/admin/volunteer/place_form.html
src/catalog/templates/admin/volunteer/review.html
src/catalog/templates/admin/volunteer/review_index.html
src/catalog/templates/auth/email_verification_email.html
src/catalog/templates/auth/includes/google_button.html
src/catalog/templates/auth/login.html
src/catalog/templates/auth/password_reset_complete.html
src/catalog/templates/auth/password_reset_confirm.html
src/catalog/templates/auth/password_reset_done.html
src/catalog/templates/auth/password_reset_email.html
src/catalog/templates/auth/password_reset_form.html
src/catalog/templates/auth/register.html
src/catalog/templates/auth/verify_email.html
src/catalog/templates/base.html
src/catalog/templates/catalog/event_detail.html
src/catalog/templates/catalog/events_landing.html
src/catalog/templates/catalog/includes/breadcrumbs.html
src/catalog/templates/catalog/includes/category_icon.html
src/catalog/templates/catalog/includes/category_visual_icon.html
src/catalog/templates/catalog/includes/event_countdown.html
src/catalog/templates/catalog/includes/phone_reveal.html
src/catalog/templates/catalog/includes/place_card.html
src/catalog/templates/catalog/includes/place_more_panel.html
src/catalog/templates/catalog/includes/review_cooldown.html
src/catalog/templates/catalog/includes/review_item.html
src/catalog/templates/catalog/includes/review_submission_notice.html
src/catalog/templates/catalog/includes/temporary_event_badge.html
src/catalog/templates/catalog/place_detail.html
src/catalog/templates/catalog/place_list.html
src/catalog/templates/catalog/seo_landing.html
src/catalog/templates/catalog/specialist_detail.html
src/catalog/templates/catalog/specialist_list.html
src/catalog/templates/includes/header.html
src/catalog/templates/includes/place_schedule_editor.html
src/catalog/templates/pages/about.html
src/catalog/templates/pages/account_dashboard.html
src/catalog/templates/pages/account_favorites.html
src/catalog/templates/pages/account_profile.html
src/catalog/templates/pages/add_place.html
src/catalog/templates/pages/contacts.html
src/catalog/templates/pages/faq.html
src/catalog/templates/pages/home.html
src/catalog/templates/pages/includes/owner_form_field.html
src/catalog/templates/pages/includes/owner_place_location_status.html
src/catalog/templates/pages/includes/owner_place_map_picker.html
src/catalog/templates/pages/includes/owner_place_wizard.html
src/catalog/templates/pages/includes/owner_wizard_completion.html
src/catalog/templates/pages/includes/permanent_place_field.html
src/catalog/templates/pages/includes/permanent_place_icon.html
src/catalog/templates/pages/includes/permanent_place_map.html
src/catalog/templates/pages/includes/permanent_place_photos.html
src/catalog/templates/pages/includes/permanent_place_workspace.html
src/catalog/templates/pages/includes/site_social_links.html
src/catalog/templates/pages/legal.html
src/catalog/templates/pages/listing_rules.html
src/catalog/templates/pages/owner_event_form.html
src/catalog/templates/pages/owner_listing_type_select.html
src/catalog/templates/pages/owner_place_create.html
src/catalog/templates/pages/owner_place_edit.html
src/catalog/templates/pages/owner_places.html
src/catalog/templates/pages/owner_reviews.html
src/catalog/templates/pages/owner_specialist_create.html
src/catalog/templates/pages/owner_team.html
src/catalog/templates/pages/permanent_place_form.html
src/catalog/templates/pages/place_reviews.html
src/catalog/templates/pages/review_rules.html
src/catalog/templates/pages/site_reviews.html
src/catalog/templates/widgets/image_preview_file_input.html
src/catalog/templates/widgets/multiple_file_input.html
src/catalog/templatetags/__init__.py
src/catalog/templatetags/admin_dashboard_tags.py
src/catalog/templatetags/catalog_i18n.py
src/catalog/testcases/__init__.py
src/catalog/testcases/admin.py
src/catalog/testcases/adult_classes.py
src/catalog/testcases/auth_access.py
src/catalog/testcases/auth_flow.py
src/catalog/testcases/catalog.py
src/catalog/testcases/events_feature.py
src/catalog/testcases/image_uploads.py
src/catalog/testcases/legacy_migrations.py
src/catalog/testcases/owner.py
src/catalog/testcases/permanent_place_wizard.py
src/catalog/testcases/phone_reveal.py
src/catalog/testcases/photo_workflow.py
src/catalog/testcases/place_card_validation.py
src/catalog/testcases/place_filepond_admin.py
src/catalog/testcases/place_readiness.py
src/catalog/testcases/place_taxonomy_admin.py
src/catalog/testcases/postgresql_cutover.py
src/catalog/testcases/pricing_plans.py
src/catalog/testcases/pricing_plans_relational.py
src/catalog/testcases/public.py
src/catalog/testcases/specialists.py
src/catalog/testcases/test_ai_referral_tracking.py
src/catalog/testcases/test_google_auth.py
src/catalog/testcases/test_indexnow.py
src/catalog/testcases/test_json_roundtrip_audit.py
src/catalog/testcases/test_judo_seo_landing.py
src/catalog/testcases/test_password_reset.py
src/catalog/testcases/test_place_json_and_pricing_modes.py
src/catalog/testcases/test_place_review_cooldown.py
src/catalog/testcases/test_review_confirmation.py
src/catalog/testcases/test_search_engine_verification.py
src/catalog/testcases/test_seo_audit_system.py
src/catalog/testcases/test_seo_landing_visibility.py
src/catalog/testcases/test_staff_profile.py
src/catalog/testcases/test_volunteer_admin.py
src/catalog/testcases/test_volunteer_dashboard.py
src/catalog/testcases/tracking.py
src/catalog/testcases/utils.py
src/catalog/tests.py
src/catalog/urls.py
src/catalog/views.py
src/catalog/volunteer_forms.py
src/catalog/volunteer_middleware.py
```

### src/config

```text
src/config/__init__.py
src/config/asgi.py
src/config/database_url.py
src/config/middleware.py
src/config/settings.py
src/config/test_runner.py
src/config/urls.py
src/config/views.py
src/config/wsgi.py
```

### config

```text
config/__init__.py
config/asgi.py
config/middleware.py
config/settings.py
config/urls.py
config/views.py
config/wsgi.py
```

### static/css

```text
static/css/bg_admin_background.css
static/css/components/google_auth.css
static/css/components/header.css
static/css/components/kidsmap_schedule_editor.css
static/css/components/kidsmap_taxonomy_picker.css
static/css/components/phone_reveal.css
static/css/events_landing.css
static/css/motion.css
static/css/pages/about.css
static/css/pages/account_profile.css
static/css/pages/add_place.css
static/css/pages/catalog_places.css
static/css/pages/contacts.css
static/css/pages/detail.css
static/css/pages/legal.css
static/css/pages/listing_rules.css
static/css/pages/permanent_place_wizard.css
static/css/pages/review_rules.css
static/css/pages/specialists.css
static/css/site.css
```

### static/js

```text
static/js/account_profile.js
static/js/ai_referral_tracking.js
static/js/bg_scene.js
static/js/catalog_map.js
static/js/components/kidsmap_taxonomy_picker.js
static/js/google_maps_markers.js
static/js/header.js
static/js/home_hero_slider.js
static/js/home_map.js
static/js/kidsmap_datetime_picker.js
static/js/kidsmap_dependent_subcategory.js
static/js/kidsmap_schedule_editor.js
static/js/motion.js
static/js/owner_event_form.js
static/js/owner_place_map_picker.js
static/js/owner_place_wizard.js
static/js/owner_pricing_plans.js
static/js/permanent_place_photos.js
static/js/permanent_place_pricing.js
static/js/permanent_place_wizard.js
static/js/place_gallery.js
static/js/place_phone_reveal.js
static/js/review_submission.js
static/js/scroll_animations.js
static/js/specialists.js
static/js/temporary_event_timer.js
static/js/tests/ai_referral_tracking.test.js
```

### static/admin

```text
static/admin/css/kidsmap_admin.css
static/admin/css/kidsmap_admin_components.css
static/admin/css/kidsmap_admin_forms.css
static/admin/css/kidsmap_admin_header.css
static/admin/css/kidsmap_admin_layout.css
static/admin/css/kidsmap_admin_tables.css
static/admin/css/kidsmap_admin_tokens.css
static/admin/css/kidsmap_notifications.css
static/admin/css/kidsmap_pagination.css
static/admin/css/kidsmap_site_media.css
static/admin/css/kidsmap_statistics.css
static/admin/css/kidsmap_taxonomy.css
static/admin/css/pages/kidsmap_add_choice.css
static/admin/css/pages/kidsmap_admin_form_shell.css
static/admin/css/pages/kidsmap_admin_sidebar.css
static/admin/css/pages/kidsmap_category_form.css
static/admin/css/pages/kidsmap_category_popup.css
static/admin/css/pages/kidsmap_changelist.css
static/admin/css/pages/kidsmap_dashboard.css
static/admin/css/pages/kidsmap_home_recommendations.css
static/admin/css/pages/kidsmap_moderation_changelist.css
static/admin/css/pages/kidsmap_place_form.css
static/admin/css/pages/kidsmap_place_location.css
static/admin/css/pages/kidsmap_site_settings.css
static/admin/css/pages/kidsmap_staff_access_list.css
static/admin/css/pages/kidsmap_user_access_form.css
static/admin/css/pages/kidsmap_users.css
static/admin/css/pages/specialist_form.css
static/admin/css/pages/staff_profile.css
static/admin/css/pages/volunteer.css
static/admin/css/pages/volunteer_place_form.css
static/admin/js/kidsmap_admin_form_shell.js
static/admin/js/kidsmap_admin_sidebar.js
static/admin/js/kidsmap_category_form.js
static/admin/js/kidsmap_category_popup.js
static/admin/js/kidsmap_event_datetime.js
static/admin/js/kidsmap_home_recommendations.js
static/admin/js/kidsmap_notifications.js
static/admin/js/kidsmap_place_changelist.js
static/admin/js/kidsmap_place_duplicates.js
static/admin/js/kidsmap_place_form.js
static/admin/js/kidsmap_place_json_import.js
static/admin/js/kidsmap_place_location.js
static/admin/js/kidsmap_place_media.js
static/admin/js/kidsmap_review_changelist.js
static/admin/js/kidsmap_site_media.js
static/admin/js/kidsmap_taxonomy.js
static/admin/js/kidsmap_users.js
static/admin/js/specialist_admin.js
static/admin/js/volunteer_place_form.js
```

### templates

```text
templates/admin/base.html
templates/admin/base_site.html
templates/admin/catalog/place_ownership_request_moderate_confirm.html
templates/admin/catalog/placechangeaudit/change_list.html
templates/admin/catalog/site_analytics.html
templates/admin/catalog/site_settings_hub.html
templates/admin/catalog/sitegalleryimage/change_list.html
templates/admin/pagination.html
```

### locale

```text
locale/az/LC_MESSAGES/django.po
locale/en/LC_MESSAGES/django.po
locale/ru/LC_MESSAGES/django.po
```

### deploy/nginx

```text
deploy/nginx/kidsmap.az.conf
```

### .github/workflows

```text
.github/workflows/deploy.yml
```

## Поля доменных моделей

Поля извлечены статически. Значения по умолчанию, наследование, properties, связи и фактическую SQL-схему проверять по исходникам, миграциям и соответствующей базе.

### Category

Источник: `src/catalog/models/category.py:86`.

```text
code: CharField
name: CharField
name_az: CharField
name_ru: CharField
name_en: CharField
icon: CharField
color_bg: CharField
color_text: CharField
is_active: BooleanField
order: PositiveIntegerField
deleted_at: DateTimeField
deleted_by: ForeignKey
created_at: DateTimeField
updated_at: DateTimeField
created_by: ForeignKey
updated_by: ForeignKey
objects: Manager
```

### Subcategory

Источник: `src/catalog/models/category.py:208`.

```text
category: ForeignKey
code: CharField
name: CharField
name_az: CharField
name_ru: CharField
name_en: CharField
icon: CharField
is_active: BooleanField
order: PositiveIntegerField
deleted_at: DateTimeField
deleted_by: ForeignKey
created_at: DateTimeField
updated_at: DateTimeField
objects: Manager
```

### PlaceOwnershipRequest

Источник: `src/catalog/models/owner.py:25`.

```text
place: ForeignKey
applicant: ForeignKey
status: CharField
note: TextField
moderation_note: TextField
moderated_by: ForeignKey
moderated_at: DateTimeField
created_at: DateTimeField
updated_at: DateTimeField
```

### PlaceOwnershipRequestAudit

Источник: `src/catalog/models/owner.py:151`.

```text
ownership_request: ForeignKey
actor: ForeignKey
action: CharField
from_status: CharField
to_status: CharField
note: TextField
created_at: DateTimeField
```

### OwnerTeamMembership

Источник: `src/catalog/models/owner.py:210`.

```text
place: ForeignKey
owner: ForeignKey
member: ForeignKey
role: CharField
is_active: BooleanField
invited_by: ForeignKey
created_at: DateTimeField
updated_at: DateTimeField
```

### OwnerTeamInvitation

Источник: `src/catalog/models/owner.py:270`.

```text
place: ForeignKey
owner: ForeignKey
email: EmailField
role: CharField
status: CharField
token: CharField
invited_by: ForeignKey
invited_user: ForeignKey
responded_at: DateTimeField
created_at: DateTimeField
updated_at: DateTimeField
```

### PlaceChangeAudit

Источник: `src/catalog/models/owner.py:359`.

```text
place: ForeignKey
changed_by: ForeignKey
field_name: CharField
old_value: TextField
new_value: TextField
source: CharField
created_at: DateTimeField
```

### Place

Источник: `src/catalog/models/place.py:27`.

```text
name: CharField
slug: SlugField
name_ru: CharField
name_en: CharField
name_az: CharField
description_ru: TextField
description_en: TextField
description_az: TextField
category: ForeignKey
subcategory: ForeignKey
age_from: PositiveSmallIntegerField
age_to: PositiveSmallIntegerField
age_open_ended: BooleanField
offers_adult_classes: BooleanField
district: CharField
metro: CharField
address: CharField
phone1: CharField
phone2: CharField
phone3: CharField
owner: ForeignKey
created_by: ForeignKey
cover_photo: FileField
photo: FileField
instagram: CharField
website: URLField
schedule: TextField
schedule_mode: CharField
schedule_note_az: TextField
schedule_note_ru: TextField
schedule_note_en: TextField
lesson_duration_minutes: PositiveSmallIntegerField
lesson_format: CharField
lessons_per_week: PositiveSmallIntegerField
lessons_per_month: PositiveSmallIntegerField
pricing_plans_legacy: JSONField
is_temporary: BooleanField
temporary_start: DateTimeField
temporary_end: DateTimeField
lat: FloatField
lng: FloatField
price_mode: CharField
price_from: DecimalField
price_to: DecimalField
price_per_lesson: DecimalField
price_per_month: DecimalField
price_per_8_lessons: DecimalField
extra_conditions: TextField
additional_info: TextField
extra_conditions_az: TextField
extra_conditions_ru: TextField
extra_conditions_en: TextField
additional_info_az: TextField
additional_info_ru: TextField
additional_info_en: TextField
custom_price_badge_az: CharField
custom_price_badge_ru: CharField
custom_price_badge_en: CharField
likes_count: PositiveIntegerField
rating_avg: FloatField
rating_count: PositiveIntegerField
is_home_recommended: BooleanField
home_recommended_order: PositiveSmallIntegerField
is_active: BooleanField
is_verified: BooleanField
status: CharField
rejection_reason: TextField
last_verified_at: DateTimeField
published_at: DateTimeField
deleted_at: DateTimeField
deleted_by: ForeignKey
created_at: DateTimeField
updated_at: DateTimeField
```

### PlacePhoto

Источник: `src/catalog/models/place.py:625`.

```text
place: ForeignKey
image: FileField
caption: CharField
order: PositiveIntegerField
```

### PlaceScheduleDay

Источник: `src/catalog/models/place.py:649`.

```text
place: ForeignKey
weekday: CharField
is_closed: BooleanField
is_24_hours: BooleanField
order: PositiveSmallIntegerField
```

### PlaceScheduleInterval

Источник: `src/catalog/models/place.py:678`.

```text
schedule_day: ForeignKey
start_time: TimeField
end_time: TimeField
order: PositiveSmallIntegerField
```

### Event

Источник: `src/catalog/models/place.py:698`.

```text
owner: ForeignKey
related_place: ForeignKey
name: CharField
slug: SlugField
name_az: CharField
name_ru: CharField
name_en: CharField
description_az: TextField
description_ru: TextField
description_en: TextField
category: ForeignKey
start_datetime: DateTimeField
end_datetime: DateTimeField
age_from: PositiveSmallIntegerField
age_to: PositiveSmallIntegerField
price_text: CharField
district: CharField
metro: CharField
address: CharField
lat: DecimalField
lng: DecimalField
phone: CharField
instagram: CharField
website: URLField
photo: FileField
moderation_note: TextField
rejection_reason: TextField
status: CharField
published_at: DateTimeField
deleted_at: DateTimeField
created_at: DateTimeField
updated_at: DateTimeField
```

### EventPhoto

Источник: `src/catalog/models/place.py:897`.

```text
event: ForeignKey
image: FileField
caption: CharField
order: PositiveIntegerField
```

### PlaceLike

Источник: `src/catalog/models/place.py:912`.

```text
place: ForeignKey
user: ForeignKey
session_key: CharField
created_at: DateTimeField
```

### PricingPlan

Источник: `src/catalog/models/pricing_plan.py:11`.

```text
place: ForeignKey
product_type: CharField
lesson_format: CharField
charge_role: CharField
billing_mode: CharField
billing_interval: CharField
billing_interval_count: PositiveSmallIntegerField
billing_cycles: PositiveSmallIntegerField
price_kind: CharField
price: DecimalField
price_min: DecimalField
price_max: DecimalField
currency: CharField
quantity: PositiveSmallIntegerField
quantity_unit: CharField
sessions_per_week: PositiveSmallIntegerField
sessions_per_month: PositiveSmallIntegerField
is_unlimited: BooleanField
validity_interval: CharField
validity_interval_count: PositiveSmallIntegerField
valid_from: DateField
valid_until: DateField
audience_type: CharField
age_from: PositiveSmallIntegerField
age_to: PositiveSmallIntegerField
min_people: PositiveSmallIntegerField
max_people: PositiveSmallIntegerField
day_type: CharField
title_az: CharField
title_ru: CharField
title_en: CharField
conditions_az: TextField
conditions_ru: TextField
conditions_en: TextField
is_required: BooleanField
is_active: BooleanField
sort_order: PositiveSmallIntegerField
verified_at: DateTimeField
source_url: URLField
created_at: DateTimeField
updated_at: DateTimeField
```

### PlaceReview

Источник: `src/catalog/models/review.py:20`.

```text
place: ForeignKey
user: ForeignKey
author_name: CharField
is_anonymous: BooleanField
rating: PositiveSmallIntegerField
text: TextField
contains_profanity: BooleanField
likes_count: PositiveIntegerField
dislikes_count: PositiveIntegerField
is_approved: BooleanField
status: CharField
rejection_reason: TextField
session_key: CharField
created_at: DateTimeField
updated_at: DateTimeField
```

### PlaceReviewCooldown

Источник: `src/catalog/models/review.py:102`.

```text
user: ForeignKey
place: ForeignKey
next_allowed_at: DateTimeField
```

### PlaceReviewReaction

Источник: `src/catalog/models/review.py:135`.

```text
review: ForeignKey
user: ForeignKey
session_key: CharField
value: SmallIntegerField
created_at: DateTimeField
updated_at: DateTimeField
```

### SiteReview

Источник: `src/catalog/models/review.py:189`.

```text
user: ForeignKey
author_name: CharField
is_anonymous: BooleanField
rating: PositiveSmallIntegerField
text: TextField
contains_profanity: BooleanField
likes_count: PositiveIntegerField
dislikes_count: PositiveIntegerField
is_approved: BooleanField
status: CharField
rejection_reason: TextField
session_key: CharField
created_at: DateTimeField
updated_at: DateTimeField
```

### SiteReviewReaction

Источник: `src/catalog/models/review.py:298`.

```text
review: ForeignKey
user: ForeignKey
session_key: CharField
value: SmallIntegerField
created_at: DateTimeField
updated_at: DateTimeField
```

### SEOAuditRun

Источник: `src/catalog/models/seo.py:5`.

```text
started_at: DateTimeField
finished_at: DateTimeField
audit_type: CharField
total_urls: PositiveIntegerField
error_count: PositiveIntegerField
warning_count: PositiveIntegerField
auto_fix_count: PositiveIntegerField
status: CharField
code_version: CharField
environment: CharField
summary_notes: TextField
```

### SEOIssue

Источник: `src/catalog/models/seo.py:63`.

```text
audit_run: ForeignKey
url: CharField
page_type: CharField
language: CharField
issue_code: CharField
severity: CharField
level: CharField
description: TextField
current_value: TextField
proposed_value: TextField
rationale: TextField
expected_impact: TextField
risk_assessment: TextField
rollback_instructions: TextField
detected_at: DateTimeField
last_checked_at: DateTimeField
status: CharField
is_auto_fixable: BooleanField
requires_approval: BooleanField
place: ForeignKey
```

### SEOChange

Источник: `src/catalog/models/seo.py:157`.

```text
issue: ForeignKey
change_summary: CharField
old_value: TextField
new_value: TextField
reason: TextField
source: CharField
applied_at: DateTimeField
recheck_result: CharField
is_reversible: BooleanField
is_rolled_back: BooleanField
rolled_back_at: DateTimeField
```

### SiteSettings

Источник: `src/catalog/models/site.py:73`.

```text
brand_name: CharField
logo: FileField
site_background_image: FileField
site_background_mobile_image: FileField
header_background_image: FileField
header_background_mobile_image: FileField
footer_background_image: FileField
footer_background_mobile_image: FileField
home_hero_image: FileField
home_hero_mobile_image: FileField
home_map_image: FileField
home_map_mobile_image: FileField
home_recommended_image: FileField
home_recommended_mobile_image: FileField
home_categories_image: FileField
home_categories_mobile_image: FileField
home_steps_image: FileField
home_steps_mobile_image: FileField
home_trust_image: FileField
home_trust_mobile_image: FileField
home_cta_image: FileField
home_cta_mobile_image: FileField
home_hero_show_decor: BooleanField
home_title_ru: CharField
home_title_en: CharField
home_title_az: CharField
home_subtitle_ru: CharField
home_subtitle_en: CharField
home_subtitle_az: CharField
home_search_label_ru: CharField
home_search_label_en: CharField
home_search_label_az: CharField
home_search_placeholder_ru: CharField
home_search_placeholder_en: CharField
home_search_placeholder_az: CharField
home_cta_text_ru: CharField
home_cta_text_en: CharField
home_cta_text_az: CharField
contacts_text_ru: TextField
contacts_text_en: TextField
contacts_text_az: TextField
about_text_ru: TextField
about_text_en: TextField
about_text_az: TextField
empty_results_text_ru: CharField
empty_results_text_en: CharField
empty_results_text_az: CharField
empty_results_image: FileField
catalog_hero_image: FileField
catalog_hero_mobile_image: FileField
about_hero_image: FileField
about_hero_mobile_image: FileField
reviews_hero_image: FileField
reviews_hero_mobile_image: FileField
for_business_hero_image: FileField
for_business_hero_mobile_image: FileField
dashboard_hero_image: FileField
dashboard_hero_mobile_image: FileField
specialists_section_enabled: BooleanField
events_section_enabled: BooleanField
footer_phone: CharField
footer_email: EmailField
footer_instagram: CharField
footer_telegram: URLField
footer_youtube: URLField
footer_tiktok: URLField
footer_facebook: URLField
footer_linkedin: URLField
footer_whatsapp: CharField
updated_at: DateTimeField
```

### SiteGalleryImage

Источник: `src/catalog/models/site.py:435`.

```text
placement: CharField
image: FileField
category: CharField
title_ru: CharField
title_en: CharField
title_az: CharField
order: PositiveIntegerField
is_active: BooleanField
created_at: DateTimeField
updated_at: DateTimeField
```

### SiteVisit

Источник: `src/catalog/models/site.py:543`.

```text
day: DateField
session_key: CharField
hits: PositiveIntegerField
first_path: CharField
created_at: DateTimeField
updated_at: DateTimeField
```

### FunnelEvent

Источник: `src/catalog/models/site.py:570`.

```text
event_type: CharField
day: DateField
path: CharField
place: ForeignKey
user: ForeignKey
session_key: CharField
event_meta: JSONField
created_at: DateTimeField
```

### CatalogContentSettings

Источник: `src/catalog/models/site.py:642`.

```text
districts_json: JSONField
metro_stations_json: JSONField
seo_pages_json: JSONField
updated_at: DateTimeField
```

### Region

Источник: `src/catalog/models/specialist.py:9`.

```text
key: CharField
name_ru: CharField
name_az: CharField
name_en: CharField
```

### District

Источник: `src/catalog/models/specialist.py:29`.

```text
key: CharField
region: ForeignKey
name_ru: CharField
name_az: CharField
name_en: CharField
```

### MetroStation

Источник: `src/catalog/models/specialist.py:50`.

```text
key: CharField
name_ru: CharField
name_az: CharField
name_en: CharField
```

### SpecialistSpecialization

Источник: `src/catalog/models/specialist.py:70`.

```text
code: CharField
name: CharField
name_ru: CharField
name_az: CharField
name_en: CharField
is_active: BooleanField
order: PositiveIntegerField
```

### Specialist

Источник: `src/catalog/models/specialist.py:93`.

```text
owner: ForeignKey
name: CharField
name_alt: CharField
slug: SlugField
photo: FileField
bio_ru: TextField
bio_az: TextField
bio_en: TextField
specializations: ManyToManyField
consultation_format: CharField
experience_years: PositiveSmallIntegerField
age_from: PositiveSmallIntegerField
age_to: PositiveSmallIntegerField
language_az: BooleanField
language_ru: BooleanField
language_en: BooleanField
price_from: PositiveIntegerField
price_to: PositiveIntegerField
duration_minutes: PositiveSmallIntegerField
education_ru: TextField
education_az: TextField
education_en: TextField
experience_info_ru: TextField
experience_info_az: TextField
experience_info_en: TextField
phone: CharField
whatsapp: CharField
instagram: CharField
website: URLField
rating_avg: FloatField
rating_count: PositiveIntegerField
is_active: BooleanField
is_verified: BooleanField
status: CharField
rejection_reason: TextField
created_at: DateTimeField
updated_at: DateTimeField
```

### SpecialistPracticeLocation

Источник: `src/catalog/models/specialist.py:255`.

```text
specialist: ForeignKey
place: ForeignKey
address: CharField
region: ForeignKey
district: ForeignKey
metro: ForeignKey
lat: FloatField
lng: FloatField
schedule: TextField
price_per_session: PositiveIntegerField
phone: CharField
is_primary: BooleanField
is_active: BooleanField
```

### SpecialistScheduleDay

Источник: `src/catalog/models/specialist.py:305`.

```text
practice_location: ForeignKey
weekday: CharField
is_closed: BooleanField
is_24_hours: BooleanField
order: PositiveSmallIntegerField
```

### SpecialistScheduleInterval

Источник: `src/catalog/models/specialist.py:339`.

```text
schedule_day: ForeignKey
start_time: TimeField
end_time: TimeField
order: PositiveSmallIntegerField
```

### SpecialistDocument

Источник: `src/catalog/models/specialist.py:359`.

```text
specialist: ForeignKey
document_type: CharField
name: CharField
file: FileField
status: CharField
is_published: BooleanField
rejection_reason: TextField
created_at: DateTimeField
```

### SpecialistReview

Источник: `src/catalog/models/specialist.py:415`.

```text
specialist: ForeignKey
user: ForeignKey
author_name: CharField
rating: PositiveSmallIntegerField
text: TextField
is_approved: BooleanField
status: CharField
rejection_reason: TextField
created_at: DateTimeField
```

### UserProfile

Источник: `src/catalog/models/user.py:19`.

```text
user: OneToOneField
phone: CharField
avatar: FileField
gender: CharField
created_at: DateTimeField
updated_at: DateTimeField
```

### UserEmailVerification

Источник: `src/catalog/models/user.py:90`.

```text
user: OneToOneField
email: EmailField
code_hash: CharField
expires_at: DateTimeField
resend_available_at: DateTimeField
attempts_left: PositiveSmallIntegerField
is_verified: BooleanField
verified_at: DateTimeField
created_at: DateTimeField
updated_at: DateTimeField
```

### VolunteerPlaceRevision

Источник: `src/catalog/models/volunteer.py:7`.

```text
place: OneToOneField
author: ForeignKey
payload: JSONField
base_snapshot: JSONField
status: CharField
version: PositiveIntegerField
review_note: TextField
reviewed_by: ForeignKey
created_at: DateTimeField
updated_at: DateTimeField
```

## Индекс Python-классов и функций

Определения уровня модуля и непосредственные методы классов. Миграции и тесты перечислены выше только как файлы. Тела функций и сигнатуры здесь не приводятся.

### src/catalog/apps.py

```text
L4: class CatalogConfig
  L8: CatalogConfig.ready
  L13: CatalogConfig._patch_jazzmin_paginator
```

### src/catalog/content_data.py

```text
L286: def base_seo_landing_pages
L290: def district_seo_pages
L327: def seo_landing_pages
```

### src/catalog/context_processors.py

```text
L82: def _build_social_links
L114: def seo_urls
L177: def _google_analytics_context
L187: def site_settings
```

### src/catalog/controllers/account_controller.py

```text
L12: class AccountController
  L17: AccountController.build_default
  L23: AccountController.ensure_profile
  L26: AccountController.build_favorites_context
  L42: AccountController.build_history_context
  L79: AccountController.build_user_reviews_context
  L93: AccountController.build_dashboard_context
```

### src/catalog/controllers/auth_controller.py

```text
L27: class AuthController
  L32: AuthController.build_default
  L38: AuthController.build_registration_form
  L41: AuthController.build_login_form
  L44: AuthController.build_email_verification_form
  L47: AuthController.build_email_verification_resend_form
  L50: AuthController.build_profile_edit_form
  L60: AuthController.build_password_change_form
  L64: AuthController.register_user_from_form
  L72: AuthController.send_registration_verification_code
  L80: AuthController.verify_registration_email_code
  L87: AuthController.resend_registration_verification_code
  L94: AuthController.update_user_profile_from_form
  L102: AuthController.update_password_from_form
  L105: AuthController.ensure_profile
```

### src/catalog/controllers/engagement_controller.py

```text
L24: class ToggleLikeResult
L31: class ToggleReviewReactionResult
L39: class EngagementController
  L43: EngagementController.build_default
  L46: EngagementController.toggle_place_like
  L51: EngagementController.add_place_review
  L56: EngagementController.add_site_review
  L59: EngagementController.toggle_place_review_reaction
  L69: EngagementController.toggle_site_review_reaction
```

### src/catalog/controllers/home_controller.py

```text
L26: class HomeController
  L31: HomeController.build_default
  L37: HomeController.build_context
  L152: HomeController._selected_age
  L157: HomeController._hero_search_placeholder
  L168: HomeController._default_hero_gallery_items
  L217: HomeController._build_hero_gallery_slides
  L245: HomeController._webp_url_for_gallery_image
```

### src/catalog/controllers/owner_events_controller.py

```text
L10: class EventActionResponse
L16: def _event_required_missing
L40: def create_event
L58: def edit_event
L81: def submit_event_for_review
L97: def delete_event
```

### src/catalog/controllers/owner_places_controller.py

```text
L46: class OwnerPlaceActionResult
L55: class OwnerPlacesController
  L62: OwnerPlacesController.build_default
  L70: OwnerPlacesController._sync_place_coordinates
  L89: OwnerPlacesController._resolve_coordinates_before_create
  L111: OwnerPlacesController._has_manual_coordinates
  L115: OwnerPlacesController._draft_fallback_category
  L119: OwnerPlacesController._quality_issue_labels
  L123: OwnerPlacesController._quality_error_message
  L129: OwnerPlacesController._add_quality_errors_to_form
  L161: OwnerPlacesController._coordinates_changed
  L165: OwnerPlacesController._format_coordinate_value
  L169: OwnerPlacesController._schedule_audit_value
  L172: OwnerPlacesController._build_create_geocoding_message
  L185: OwnerPlacesController._build_manual_point_preview_message
  L191: OwnerPlacesController._build_manual_refresh_message
  L206: OwnerPlacesController._build_create_success_message
  L219: OwnerPlacesController._build_soft_delete_changes
  L229: OwnerPlacesController._is_user_editable_place
  L233: OwnerPlacesController._has_permission
  L237: OwnerPlacesController._build_ownership_note
  L242: OwnerPlacesController._has_place_capacity
  L256: OwnerPlacesController.build_dashboard_context
  L312: OwnerPlacesController.build_edit_form_context
  L355: OwnerPlacesController.build_create_form_context
  L383: OwnerPlacesController.preview_create_coordinates
  L433: OwnerPlacesController.create_place
  L606: OwnerPlacesController.save_edit_form
  L792: OwnerPlacesController.set_publication_state
  L853: OwnerPlacesController.submit_for_moderation
  L915: OwnerPlacesController.delete_gallery_photo
  L947: OwnerPlacesController.delete_place
```

### src/catalog/controllers/owner_reviews_controller.py

```text
L21: class OwnerReviewsActionResult
L27: class OwnerReviewsController
  L32: OwnerReviewsController.build_default
  L38: OwnerReviewsController._moderation_scopes
  L45: OwnerReviewsController.build_context
  L77: OwnerReviewsController.set_review_approval
```

### src/catalog/controllers/owner_team_controller.py

```text
L26: class OwnerTeamActionResult
L33: class OwnerTeamController
  L37: OwnerTeamController.build_default
  L42: OwnerTeamController._manageable_place_ids
  L46: OwnerTeamController._manageable_places
  L49: OwnerTeamController.build_manager_context
  L79: OwnerTeamController.build_user_pending_invitations_context
  L85: OwnerTeamController.submit_invitation
  L106: OwnerTeamController._managed_invitation
  L114: OwnerTeamController.cancel_invitation
  L124: OwnerTeamController._managed_membership
  L128: OwnerTeamController.update_member_role
  L141: OwnerTeamController.remove_member
  L150: OwnerTeamController.accept_invitation_for_user
  L159: OwnerTeamController.reject_invitation_for_user
L169: def _form_error_message
```

### src/catalog/controllers/ownership_controller.py

```text
L20: class OwnershipController
  L25: OwnershipController.build_default
  L31: OwnershipController.build_place_claim_context
  L56: OwnershipController.submit_claim_request
```

### src/catalog/controllers/place_controller.py

```text
L37: def _public_request_language
L46: class PlaceController
  L52: PlaceController.build_default
  L59: PlaceController.build_list_context
  L248: PlaceController.build_events_landing_context
  L361: PlaceController._filtered_event_queryset
  L446: PlaceController._base_list_url
  L449: PlaceController.build_normalized_list_query
  L457: PlaceController._build_normalized_query_params
  L504: PlaceController._build_active_filter_chips
  L662: PlaceController._build_event_type_url
  L673: PlaceController._build_popular_options
  L681: PlaceController._build_list_analytics_events
  L728: PlaceController._serialize_map_places
  L783: PlaceController.get_active_place_for_legacy_redirect
  L786: PlaceController.get_active_place_with_gallery
  L798: PlaceController._review_prompt_chips
  L827: PlaceController._build_review_histogram
  L844: PlaceController.build_detail_context
```

### src/catalog/controllers/place_reviews_controller.py

```text
L22: class PlaceReviewsController
  L25: PlaceReviewsController.build_context
```

### src/catalog/controllers/seo_controller.py

```text
L19: class SeoController
  L23: SeoController.build_default
  L26: SeoController.build_landing_context
  L61: SeoController._matching_count_label
```

### src/catalog/controllers/site_reviews_controller.py

```text
L22: class SiteReviewsController
  L26: SiteReviewsController.build_default
  L29: SiteReviewsController._visible_reviews_queryset
  L37: SiteReviewsController.build_context
```

### src/catalog/controllers/tracking_controller.py

```text
L11: class TrackEventResult
  L16: TrackEventResult.as_payload
L23: class TrackingController
  L27: TrackingController.build_default
  L30: TrackingController.track_event_from_json
  L75: TrackingController.track_cta_event_from_json
```

### src/catalog/domain_admin/__init__.py

```text
L38: def _get_sidebar_metrics
L137: def _build_admin_language_switch_items
L164: def _kidsmap_get_app_list
L242: def _admin_role_label
L248: def _normalize_admin_path
L253: def _path_matches_any_prefix
L258: def _build_sidebar_item
L347: def _build_sidebar_sections
L565: def _kidsmap_each_context
```

### src/catalog/domain_admin/category.py

```text
L27: def _normalized_taxonomy_name
L33: def _unique_taxonomy_code
L45: def _duplicate_taxonomy_name
L59: def validate_icon_upload
L99: def save_uploaded_category_icon
L111: class CategoryAdminForm
  L139: CategoryAdminForm.clean
  L164: CategoryAdminForm.clean_icon_upload
  L170: CategoryAdminForm.__init__
  L179: CategoryAdminForm.save
L190: class SubcategoryAdminForm
  L213: SubcategoryAdminForm.__init__
  L219: SubcategoryAdminForm.clean_icon_upload
  L223: SubcategoryAdminForm.clean
  L250: SubcategoryAdminForm.save
L265: class SubcategoryInline
L273: class CategoryAdmin
  L294: CategoryAdmin.get_inlines
  L299: CategoryAdmin.delete_model
  L303: CategoryAdmin.delete_queryset
  L307: CategoryAdmin.get_urls
  L316: CategoryAdmin.toggle_active_view
  L346: CategoryAdmin.changelist_view
  L401: CategoryAdmin.upload_icon_view
L421: class SubcategoryAdmin
  L435: SubcategoryAdmin.delete_model
  L438: SubcategoryAdmin.delete_queryset
  L442: SubcategoryAdmin.has_module_permission
```

### src/catalog/domain_admin/owner.py

```text
L28: class OwnerTeamMembershipAdmin
L37: class OwnerTeamInvitationAdmin
L45: class PlaceChangeTypeFilter
  L87: PlaceChangeTypeFilter.lookups
  L90: PlaceChangeTypeFilter.queryset
L102: class PlaceChangeAuditAdmin
  L123: PlaceChangeAuditAdmin.has_add_permission
  L126: PlaceChangeAuditAdmin.has_change_permission
  L129: PlaceChangeAuditAdmin.has_delete_permission
  L133: PlaceChangeAuditAdmin._truthy_audit_value
  L137: PlaceChangeAuditAdmin._audit_display_value
  L153: PlaceChangeAuditAdmin._audit_user_value
  L169: PlaceChangeAuditAdmin._audit_field_label
  L213: PlaceChangeAuditAdmin._audit_event_metadata
  L283: PlaceChangeAuditAdmin._audit_value_pair
  L309: PlaceChangeAuditAdmin.place_summary
  L329: PlaceChangeAuditAdmin.change_type_badge
  L340: PlaceChangeAuditAdmin.field_changes_summary
  L351: PlaceChangeAuditAdmin.changed_by_summary
  L365: PlaceChangeAuditAdmin.source_badge
  L379: PlaceChangeAuditAdmin.created_at_display
  L383: PlaceChangeAuditAdmin.row_actions
L401: class PlaceOwnershipRequestAuditInline
  L409: PlaceOwnershipRequestAuditInline.has_add_permission
L414: class PlaceOwnershipRequestAdmin
  L488: PlaceOwnershipRequestAdmin.get_queryset
  L491: PlaceOwnershipRequestAdmin.get_deleted_objects
  L502: PlaceOwnershipRequestAdmin.get_urls
  L518: PlaceOwnershipRequestAdmin.status_badge
  L531: PlaceOwnershipRequestAdmin._build_request_form_summary
  L551: PlaceOwnershipRequestAdmin.render_change_form
  L559: PlaceOwnershipRequestAdmin.moderated_at_display
  L563: PlaceOwnershipRequestAdmin.moderated_by_display
  L567: PlaceOwnershipRequestAdmin._place_text_value
  L571: PlaceOwnershipRequestAdmin._format_place_number_pair
  L580: PlaceOwnershipRequestAdmin._render_place_completion_badge
  L587: PlaceOwnershipRequestAdmin._place_completion_rows
  L631: PlaceOwnershipRequestAdmin.place_completion_summary
  L670: PlaceOwnershipRequestAdmin.row_actions
  L690: PlaceOwnershipRequestAdmin._build_request_changelist_query_string
  L702: PlaceOwnershipRequestAdmin._request_quick_filters
  L720: PlaceOwnershipRequestAdmin._request_bulk_actions
  L726: PlaceOwnershipRequestAdmin.changelist_view
  L743: PlaceOwnershipRequestAdmin.has_add_permission
  L746: PlaceOwnershipRequestAdmin._moderate_single
  L795: PlaceOwnershipRequestAdmin.approve_request_view
  L802: PlaceOwnershipRequestAdmin.reject_request_view
  L810: PlaceOwnershipRequestAdmin.approve_requests
  L838: PlaceOwnershipRequestAdmin.reject_requests
L867: class PlaceOwnershipRequestAuditAdmin
  L882: PlaceOwnershipRequestAuditAdmin.has_add_permission
  L885: PlaceOwnershipRequestAuditAdmin.has_change_permission
  L888: PlaceOwnershipRequestAuditAdmin.has_delete_permission
```

### src/catalog/domain_admin/place.py

```text
L69: def _normalized_phone
L73: def _normalized_url
L83: def _normalized_text
L87: def place_quality_error_labels
L91: class PlacePhotoInline
L100: class EventPhotoInline
L109: class PlaceChangeAuditInline
  L117: PlaceChangeAuditInline.has_add_permission
L121: class PlaceAdminForm
  L206: PlaceAdminForm.clean_price_mode
  L212: PlaceAdminForm.clean
  L314: PlaceAdminForm.__init__
  L404: PlaceAdminForm.save
  L418: PlaceAdminForm.clean_phone1
  L424: PlaceAdminForm.clean_phone2
  L428: PlaceAdminForm.clean_phone3
  L432: PlaceAdminForm._configure_metro_choices
L459: class EventAdminForm
  L520: EventAdminForm.clean
  L564: EventAdminForm.__init__
L599: class PlaceCoordinatesFilter
  L603: PlaceCoordinatesFilter.lookups
  L609: PlaceCoordinatesFilter.queryset
L618: class PlaceMapReadyFilter
  L622: PlaceMapReadyFilter.lookups
  L628: PlaceMapReadyFilter.queryset
L637: class PlacePublicationFilter
  L641: PlacePublicationFilter.lookups
  L647: PlacePublicationFilter.queryset
L656: class PlaceDeletedFilter
  L660: PlaceDeletedFilter.lookups
  L666: PlaceDeletedFilter.queryset
L676: class PlaceCreatedByFilter
  L681: PlaceCreatedByFilter.lookups
  L697: PlaceCreatedByFilter.queryset
L706: class EventDeletedFilter
  L710: EventDeletedFilter.lookups
  L716: EventDeletedFilter.queryset
L727: class EventAdmin
  L916: EventAdmin.get_fieldsets
  L921: EventAdmin.get_changeform_initial_data
  L926: EventAdmin.render_change_form
  L948: EventAdmin._fieldset_list
  L951: EventAdmin._build_event_form_sections
  L973: EventAdmin._build_event_secondary_sections
  L994: EventAdmin._field_has_value
  L1025: EventAdmin._event_visibility_state
  L1082: EventAdmin._event_publish_missing_fields
  L1096: EventAdmin._build_event_form_summary
  L1200: EventAdmin.display_name
  L1218: EventAdmin.lifecycle_status_display
  L1240: EventAdmin.row_actions
  L1252: EventAdmin.save_model
  L1266: EventAdmin.response_add
  L1279: EventAdmin.response_change
  L1292: EventAdmin._event_change_url
  L1299: EventAdmin._handle_event_save_draft_submit
  L1303: EventAdmin._handle_publish_event_submit
  L1345: EventAdmin._handle_unpublish_event_submit
  L1359: EventAdmin._event_dashboard_counts
  L1368: EventAdmin._event_dashboard_stats
  L1402: EventAdmin._event_quick_filters
  L1437: EventAdmin._event_bulk_actions
  L1460: EventAdmin.mark_published
  L1484: EventAdmin.mark_draft
  L1501: EventAdmin.mark_pending
  L1519: EventAdmin.mark_rejected
  L1532: EventAdmin.changelist_view
L1546: class PlaceAdmin
  L1839: PlaceAdmin.render_change_form
  L1921: PlaceAdmin.add_view
  L1928: PlaceAdmin._fieldset_list
  L1931: PlaceAdmin._build_place_form_errors
  L2014: PlaceAdmin._build_taxonomy_picker_config
  L2084: PlaceAdmin._build_place_form_sections
  L2087: PlaceAdmin._build_place_carryover_fields
  L2105: PlaceAdmin._build_place_secondary_sections
  L2126: PlaceAdmin._build_place_inline_sections
  L2161: PlaceAdmin._field_has_value
  L2179: PlaceAdmin._place_visibility_state
  L2255: PlaceAdmin._build_place_map_alert
  L2288: PlaceAdmin._resolve_public_site_host
  L2299: PlaceAdmin._build_public_place_link
  L2326: PlaceAdmin._build_place_language_tabs
  L2346: PlaceAdmin._build_place_text_tabs
  L2365: PlaceAdmin._build_place_section_states
  L2422: PlaceAdmin._build_place_form_summary
  L2664: PlaceAdmin.get_fieldsets
  L2669: PlaceAdmin.get_changeform_initial_data
  L2675: PlaceAdmin.get_queryset
  L2694: PlaceAdmin._is_trash_changelist
  L2697: PlaceAdmin.get_list_display
  L2702: PlaceAdmin.get_inline_instances
  L2709: PlaceAdmin._state_visual
  L2726: PlaceAdmin.col_place
  L2788: PlaceAdmin.col_location
  L2811: PlaceAdmin.col_state
  L2874: PlaceAdmin.col_marks
  L2923: PlaceAdmin.col_updated
  L2947: PlaceAdmin.col_actions
  L2983: PlaceAdmin.display_name
  L3014: PlaceAdmin._render_place_state_badge
  L3022: PlaceAdmin.lifecycle_status
  L3031: PlaceAdmin.lifecycle_status_display
  L3035: PlaceAdmin.coordinates_status
  L3042: PlaceAdmin.coordinates_status_display
  L3046: PlaceAdmin.map_ready_status
  L3053: PlaceAdmin.map_ready_status_display
  L3057: PlaceAdmin.quality_status_display
  L3071: PlaceAdmin.last_verified_at_display
  L3077: PlaceAdmin.published_at_display
  L3082: PlaceAdmin._user_label
  L3087: PlaceAdmin._latest_place_audit
  L3093: PlaceAdmin._creation_place_audit
  L3104: PlaceAdmin._first_ownership_request
  L3111: PlaceAdmin.category_summary
  L3129: PlaceAdmin.location_summary
  L3146: PlaceAdmin.publication_status
  L3189: PlaceAdmin.publication_readiness
  L3234: PlaceAdmin.home_recommendation_status
  L3238: PlaceAdmin.map_status_summary
  L3250: PlaceAdmin.owner_display
  L3275: PlaceAdmin.created_summary
  L3284: PlaceAdmin.engagement_summary
  L3304: PlaceAdmin.updated_summary
  L3323: PlaceAdmin.deleted_at_display
  L3333: PlaceAdmin.deleted_by_display
  L3339: PlaceAdmin.get_actions
  L3344: PlaceAdmin.place_state_rules
  L3372: PlaceAdmin.get_deleted_objects
  L3382: PlaceAdmin._build_soft_delete_changes
  L3391: PlaceAdmin._soft_delete_place
  L3407: PlaceAdmin._restore_place
  L3423: PlaceAdmin._response_after_place_soft_delete
  L3431: PlaceAdmin._build_coordinate_changes
  L3440: PlaceAdmin._refresh_place_coordinates_with_audit
  L3453: PlaceAdmin._place_change_url
  L3460: PlaceAdmin._place_delete_url
  L3467: PlaceAdmin._place_restore_url
  L3474: PlaceAdmin._build_changelist_query_string
  L3486: PlaceAdmin._place_quick_filters
  L3584: PlaceAdmin._place_dashboard_counts
  L3610: PlaceAdmin._place_dashboard_stats
  L3650: PlaceAdmin._place_bulk_actions
  L3705: PlaceAdmin._place_trash_bulk_actions
  L3717: PlaceAdmin._build_admin_coordinate_refresh_feedback
  L3745: PlaceAdmin._handle_refresh_coordinates_submit
  L3757: PlaceAdmin._handle_publish_submit
  L3796: PlaceAdmin._handle_unpublish_submit
  L3810: PlaceAdmin.get_urls
  L3862: PlaceAdmin.place_quality_check_view
  L3879: PlaceAdmin.place_quality_report_view
  L3935: PlaceAdmin.validate_pricing_import_view
  L3967: PlaceAdmin.export_place_json_view
  L4006: PlaceAdmin.duplicate_candidates_view
  L4053: PlaceAdmin._home_recommendation_queryset
  L4058: PlaceAdmin._serialize_home_recommendation
  L4081: PlaceAdmin.home_recommendation_candidates_view
  L4107: PlaceAdmin.save_home_recommendations_view
  L4167: PlaceAdmin.toggle_publication_view
  L4235: PlaceAdmin.quick_action_view
  L4307: PlaceAdmin.search_suggestions_view
  L4359: PlaceAdmin.changelist_view
  L4411: PlaceAdmin.mark_active
  L4430: PlaceAdmin.mark_inactive
  L4448: PlaceAdmin.mark_home_recommended
  L4465: PlaceAdmin.unmark_home_recommended
  L4482: PlaceAdmin.mark_draft
  L4496: PlaceAdmin.mark_verified
  L4532: PlaceAdmin.mark_unverified
  L4546: PlaceAdmin.mark_pending
  L4566: PlaceAdmin.mark_published
  L4589: PlaceAdmin.mark_rejected
  L4606: PlaceAdmin.move_selected_to_deleted
  L4640: PlaceAdmin.restore_selected
  L4662: PlaceAdmin.refresh_coordinates
  L4704: PlaceAdmin.delete_view
  L4751: PlaceAdmin.restore_view
  L4794: PlaceAdmin.delete_model
  L4797: PlaceAdmin.delete_queryset
  L4801: PlaceAdmin._stringify_audit_value
  L4808: PlaceAdmin.save_model
  L4918: PlaceAdmin.save_related
  L4922: PlaceAdmin._save_filepond_gallery_uploads
  L4987: PlaceAdmin.response_add
  L5012: PlaceAdmin.response_change
  L5037: PlaceAdmin._handle_save_draft_submit
  L5042: PlaceAdmin.row_actions
L5098: class PlaceReviewsByClubAdmin
  L5105: PlaceReviewsByClubAdmin.get_queryset
  L5126: PlaceReviewsByClubAdmin.display_name
  L5130: PlaceReviewsByClubAdmin.visible_review_count
  L5134: PlaceReviewsByClubAdmin.visible_rating_avg
  L5138: PlaceReviewsByClubAdmin.reviews_link
```

### src/catalog/domain_admin/review.py

```text
L18: def _localized_admin_url
L41: class PlaceReviewInline
  L53: PlaceReviewInline.review_author_display
  L79: PlaceReviewInline.created_at_display
L83: class ReviewModerationStatusFilter
  L87: ReviewModerationStatusFilter.lookups
  L95: ReviewModerationStatusFilter.queryset
L108: class ReviewTextPresenceFilter
  L112: ReviewTextPresenceFilter.lookups
  L118: ReviewTextPresenceFilter.queryset
L127: class ReviewRiskFilter
  L131: ReviewRiskFilter.lookups
  L138: ReviewRiskFilter.queryset
L150: class PlaceReviewAdmin
  L225: PlaceReviewAdmin.get_queryset
  L228: PlaceReviewAdmin._review_has_text
  L231: PlaceReviewAdmin._render_review_badge
  L238: PlaceReviewAdmin._place_admin_change_url
  L241: PlaceReviewAdmin._review_change_url
  L250: PlaceReviewAdmin._review_delete_url
  L259: PlaceReviewAdmin._review_action_url
  L268: PlaceReviewAdmin._review_preview_text
  L276: PlaceReviewAdmin._place_public_link
  L284: PlaceReviewAdmin._review_status
  L296: PlaceReviewAdmin.review_summary
  L320: PlaceReviewAdmin.display_author
  L324: PlaceReviewAdmin.author_summary
  L348: PlaceReviewAdmin.rating_summary
  L363: PlaceReviewAdmin.moderation_status_summary
  L379: PlaceReviewAdmin.risk_flags_summary
  L397: PlaceReviewAdmin.engagement_summary
  L409: PlaceReviewAdmin.created_at_display
  L413: PlaceReviewAdmin.popularity_score_display
  L416: PlaceReviewAdmin._build_review_form_summary
  L443: PlaceReviewAdmin.render_change_form
  L452: PlaceReviewAdmin._build_review_changelist_query_string
  L464: PlaceReviewAdmin._review_quick_filters
  L479: PlaceReviewAdmin._review_bulk_actions
  L487: PlaceReviewAdmin.get_urls
  L496: PlaceReviewAdmin._review_changelist_url
  L502: PlaceReviewAdmin.changelist_view
  L511: PlaceReviewAdmin._message_for_single_review_action
  L519: PlaceReviewAdmin._toggle_review_visibility
  L528: PlaceReviewAdmin.approve_view
  L549: PlaceReviewAdmin.hide_view
  L570: PlaceReviewAdmin.reject_view
  L592: PlaceReviewAdmin.approve_selected
  L604: PlaceReviewAdmin.hide_selected
  L616: PlaceReviewAdmin.reject_selected
  L628: PlaceReviewAdmin.row_actions
L654: class SiteReviewAdmin
  L667: SiteReviewAdmin.display_author
```

### src/catalog/domain_admin/seo.py

```text
L10: class SEOAuditRunAdmin
  L39: SEOAuditRunAdmin.get_urls
  L61: SEOAuditRunAdmin.run_audit_now_view
  L77: SEOAuditRunAdmin.apply_fixes_now_view
  L92: SEOAuditRunAdmin.clear_history_now_view
  L108: SEOAuditRunAdmin.status_badge
  L117: SEOAuditRunAdmin.view_report_button
  L130: SEOAuditRunAdmin.formatted_report_html
  L209: SEOAuditRunAdmin.has_add_permission
  L212: SEOAuditRunAdmin.has_delete_permission
L217: class SEOIssueAdmin
  L247: SEOIssueAdmin.level_badge
  L256: SEOIssueAdmin.severity_badge
  L267: SEOIssueAdmin.status_badge
  L276: SEOIssueAdmin.url_link
  L286: SEOIssueAdmin.edit_object_button
  L305: SEOIssueAdmin.approve_selected_proposals
  L314: SEOIssueAdmin.reject_selected_proposals
  L323: SEOIssueAdmin.recheck_selected_issues
L334: class SEOChangeAdmin
  L361: SEOChangeAdmin.rollback_badge
  L368: SEOChangeAdmin.rollback_selected_changes
  L380: SEOChangeAdmin.has_add_permission
```

### src/catalog/domain_admin/site.py

```text
L25: class _BaseSiteSettingsSectionAdmin
  L64: _BaseSiteSettingsSectionAdmin.get_model_perms
  L68: _BaseSiteSettingsSectionAdmin.has_add_permission
  L71: _BaseSiteSettingsSectionAdmin.has_delete_permission
  L74: _BaseSiteSettingsSectionAdmin.changelist_view
  L80: _BaseSiteSettingsSectionAdmin.render_change_form
  L86: _BaseSiteSettingsSectionAdmin._render_image_preview
  L110: _BaseSiteSettingsSectionAdmin.logo_preview
  L114: _BaseSiteSettingsSectionAdmin.header_background_image_preview
  L118: _BaseSiteSettingsSectionAdmin.header_background_mobile_image_preview
  L122: _BaseSiteSettingsSectionAdmin.footer_background_image_preview
  L126: _BaseSiteSettingsSectionAdmin.footer_background_mobile_image_preview
  L130: _BaseSiteSettingsSectionAdmin.site_background_image_preview
  L134: _BaseSiteSettingsSectionAdmin.site_background_mobile_image_preview
  L138: _BaseSiteSettingsSectionAdmin.home_hero_image_preview
  L142: _BaseSiteSettingsSectionAdmin.home_hero_mobile_image_preview
  L146: _BaseSiteSettingsSectionAdmin.home_map_image_preview
  L150: _BaseSiteSettingsSectionAdmin.home_map_mobile_image_preview
  L154: _BaseSiteSettingsSectionAdmin.home_recommended_image_preview
  L158: _BaseSiteSettingsSectionAdmin.home_recommended_mobile_image_preview
  L162: _BaseSiteSettingsSectionAdmin.home_categories_image_preview
  L166: _BaseSiteSettingsSectionAdmin.home_categories_mobile_image_preview
  L170: _BaseSiteSettingsSectionAdmin.home_steps_image_preview
  L174: _BaseSiteSettingsSectionAdmin.home_steps_mobile_image_preview
  L178: _BaseSiteSettingsSectionAdmin.home_trust_image_preview
  L182: _BaseSiteSettingsSectionAdmin.home_trust_mobile_image_preview
  L186: _BaseSiteSettingsSectionAdmin.home_cta_image_preview
  L190: _BaseSiteSettingsSectionAdmin.home_cta_mobile_image_preview
  L194: _BaseSiteSettingsSectionAdmin.empty_results_image_preview
  L198: _BaseSiteSettingsSectionAdmin.catalog_hero_mobile_image_preview
  L202: _BaseSiteSettingsSectionAdmin.about_hero_mobile_image_preview
  L206: _BaseSiteSettingsSectionAdmin.reviews_hero_mobile_image_preview
  L210: _BaseSiteSettingsSectionAdmin.for_business_hero_mobile_image_preview
  L214: _BaseSiteSettingsSectionAdmin.dashboard_hero_mobile_image_preview
  L218: _BaseSiteSettingsSectionAdmin.catalog_hero_image_preview
  L222: _BaseSiteSettingsSectionAdmin.about_hero_image_preview
  L226: _BaseSiteSettingsSectionAdmin.reviews_hero_image_preview
  L230: _BaseSiteSettingsSectionAdmin.for_business_hero_image_preview
  L234: _BaseSiteSettingsSectionAdmin.dashboard_hero_image_preview
L239: class SiteSettingsCompatAdmin
  L240: SiteSettingsCompatAdmin.has_add_permission
  L243: SiteSettingsCompatAdmin.has_delete_permission
  L246: SiteSettingsCompatAdmin._is_section_complete
  L253: SiteSettingsCompatAdmin._sections
  L319: SiteSettingsCompatAdmin.changelist_view
  L328: SiteSettingsCompatAdmin.change_view
L333: class SiteBrandingSettingsAdmin
L383: class SiteAboutSettingsAdmin
L392: class SiteContactsSettingsAdmin
L400: class SiteFooterSettingsAdmin
L423: class SiteEmptyStateSettingsAdmin
L442: class SiteVisibilitySettingsAdmin
L463: class SiteAnalyticsAdmin
  L464: SiteAnalyticsAdmin.has_add_permission
  L467: SiteAnalyticsAdmin.has_delete_permission
  L470: SiteAnalyticsAdmin.changelist_view
L486: class SiteGalleryImageAdmin
  L570: SiteGalleryImageAdmin.changelist_view
  L942: SiteGalleryImageAdmin.get_changeform_initial_data
  L950: SiteGalleryImageAdmin.image_preview
  L964: SiteGalleryImageAdmin.render_change_form
  L970: SiteGalleryImageAdmin.get_urls
  L986: SiteGalleryImageAdmin.ajax_upload
  L1065: SiteGalleryImageAdmin.ajax_delete_main_image
L1092: class CatalogContentSettingsAdmin
  L1116: CatalogContentSettingsAdmin.has_add_permission
  L1119: CatalogContentSettingsAdmin.has_delete_permission
  L1122: CatalogContentSettingsAdmin.render_change_form
```

### src/catalog/domain_admin/specialist.py

```text
L22: class SpecialistAdminForm
  L27: SpecialistAdminForm.clean
L71: class RegionAdmin
L77: class DistrictAdmin
L84: class MetroStationAdmin
L90: class SpecialistSpecializationAdmin
L96: class SpecialistPracticeLocationInline
L105: class SpecialistDocumentInline
  L114: SpecialistDocumentInline.download_link
L122: class SpecialistAdmin
  L140: SpecialistAdmin.get_queryset
  L146: SpecialistAdmin._build_changelist_query_string
  L158: SpecialistAdmin._dashboard_counts
  L173: SpecialistAdmin._dashboard_stats
  L225: SpecialistAdmin._quick_filters
  L307: SpecialistAdmin._bulk_actions
  L315: SpecialistAdmin.changelist_view
  L332: SpecialistAdmin.mark_published
  L346: SpecialistAdmin.mark_draft
  L359: SpecialistAdmin.mark_pending
  L373: SpecialistAdmin.mark_rejected
  L388: SpecialistAdmin.mark_verified
  L397: SpecialistAdmin.profile_column
  L413: SpecialistAdmin.directions_column
  L423: SpecialistAdmin.format_badge
  L430: SpecialistAdmin.status_badge
  L434: SpecialistAdmin.verification_badge
  L440: SpecialistAdmin.documents_count
  L445: SpecialistAdmin.rating_column
L561: class SpecialistReviewAdmin
  L594: SpecialistReviewAdmin.approve_selected
  L608: SpecialistReviewAdmin.hide_selected
  L622: SpecialistReviewAdmin.reject_selected
```

### src/catalog/domain_admin/ui_utils.py

```text
L5: def render_primary_action
L13: def render_inline_action
L25: def render_action_menu
L50: def render_row_actions_container
L58: def build_admin_query_string
```

### src/catalog/domain_admin/user.py

```text
L92: class StaffAccessUserCreationForm
L111: class _HiddenFromAdminIndexMixin
  L112: _HiddenFromAdminIndexMixin.get_model_perms
L116: class UserProfileInline
  L132: UserProfileInline.get_extra
  L138: UserProfileInline.avatar_preview
L156: class _BaseKidsMapUserAdmin
  L163: _BaseKidsMapUserAdmin.get_queryset
  L166: _BaseKidsMapUserAdmin.get_deleted_objects
  L177: _BaseKidsMapUserAdmin.has_add_permission
  L180: _BaseKidsMapUserAdmin.save_related
  L184: _BaseKidsMapUserAdmin.get_urls
  L197: _BaseKidsMapUserAdmin.site_phone
  L202: _BaseKidsMapUserAdmin.site_gender
  L207: _BaseKidsMapUserAdmin.identity_summary
  L249: _BaseKidsMapUserAdmin._avatar_html
  L267: _BaseKidsMapUserAdmin.password_summary
  L286: _BaseKidsMapUserAdmin.render_change_form
L327: class HiddenBaseUserAdmin
L352: class UserPhoneFilter
  L356: UserPhoneFilter.lookups
  L362: UserPhoneFilter.queryset
L370: class UserPlacesFilter
  L374: UserPlacesFilter.lookups
  L380: UserPlacesFilter.queryset
L388: class UserLastLoginFilter
  L392: UserLastLoginFilter.lookups
  L398: UserLastLoginFilter.queryset
L407: class SiteRegisteredUserAdmin
  L445: SiteRegisteredUserAdmin.get_queryset
  L458: SiteRegisteredUserAdmin.get_urls
  L469: SiteRegisteredUserAdmin.user_toggle_active
  L494: SiteRegisteredUserAdmin.activate_users
  L503: SiteRegisteredUserAdmin.deactivate_users
  L512: SiteRegisteredUserAdmin.user_profile_card
  L597: SiteRegisteredUserAdmin.user_phone
  L614: SiteRegisteredUserAdmin.user_gender
  L628: SiteRegisteredUserAdmin.user_status
  L646: SiteRegisteredUserAdmin.user_date_joined
  L661: SiteRegisteredUserAdmin.user_last_login
  L676: SiteRegisteredUserAdmin.user_activity
  L721: SiteRegisteredUserAdmin.user_actions
  L830: SiteRegisteredUserAdmin._build_user_changelist_query_string
  L833: SiteRegisteredUserAdmin._user_quick_filters
  L862: SiteRegisteredUserAdmin.changelist_view
L939: class StaffAccessRoleFilter
  L943: StaffAccessRoleFilter.lookups
  L950: StaffAccessRoleFilter.queryset
L961: class StaffAccessUserAdmin
  L987: StaffAccessUserAdmin.get_queryset
  L996: StaffAccessUserAdmin.get_readonly_fields
  L1002: StaffAccessUserAdmin.has_change_permission
  L1007: StaffAccessUserAdmin.render_change_form
  L1014: StaffAccessUserAdmin.staff_role
  L1022: StaffAccessUserAdmin.places_count
  L1026: StaffAccessUserAdmin.activity_status
  L1030: StaffAccessUserAdmin.row_actions
  L1038: StaffAccessUserAdmin._is_protected_from_deletion
  L1043: StaffAccessUserAdmin.has_delete_permission
  L1050: StaffAccessUserAdmin.delete_view
  L1066: StaffAccessUserAdmin.get_changeform_initial_data
  L1072: StaffAccessUserAdmin.save_model
  L1081: StaffAccessUserAdmin.save_related
  L1100: StaffAccessUserAdmin.changelist_view
L1121: class UserProfileAccessLevelFilter
  L1125: UserProfileAccessLevelFilter.lookups
  L1132: UserProfileAccessLevelFilter.queryset
L1144: class UserProfileAdmin
  L1162: UserProfileAdmin.access_level
L1171: class UserEmailVerificationAdmin
```

### src/catalog/domain_admin/volunteer.py

```text
L26: def render
L33: def index
L37: def detail
L46: def photo
L70: def edit
L104: def review_index
L110: def display_value
L128: def review
L166: def get_urls
```

### src/catalog/forms.py

```text
L52: class LocalizedModelChoiceField
  L53: LocalizedModelChoiceField.label_from_instance
L59: class SubcategorySelect
  L60: SubcategorySelect.create_option
L72: class MultipleFileInput
L76: class MultipleFileField
  L77: MultipleFileField.clean
L84: class PlaceScheduleEditorFormMixin
  L85: PlaceScheduleEditorFormMixin._init_schedule_editor
  L149: PlaceScheduleEditorFormMixin._clean_schedule_editor
  L174: PlaceScheduleEditorFormMixin.save_schedule
L181: def _normalize_whitespace
L185: def _validate_person_name
L215: def _validate_phone
L234: def _normalize_azerbaijan_phone_candidate
L241: def _azerbaijan_phone_error
L250: def _format_azerbaijan_phone_for_input
L283: def _validate_azerbaijan_phone
L320: def _build_registration_username
L347: def _validate_uploaded_image
L353: class MultipleFileInput
L358: class ImagePreviewFileInput
L362: class MultipleFileField
  L363: MultipleFileField.__init__
  L377: MultipleFileField.clean
L395: class RegistrationForm
  L441: RegistrationForm.__init__
  L469: RegistrationForm._apply_registration_copy
  L536: RegistrationForm.clean_email
  L546: RegistrationForm.clean_first_name
  L549: RegistrationForm.clean_last_name
  L552: RegistrationForm.clean_phone
  L555: RegistrationForm.save
L566: class LoginForm
  L594: LoginForm.__init__
  L612: LoginForm._apply_login_copy
  L649: LoginForm.clean
L686: class EmailVerificationForm
  L717: EmailVerificationForm.clean_email
  L720: EmailVerificationForm.clean_code
L727: class EmailVerificationResendForm
  L738: EmailVerificationResendForm.clean_email
L742: class UserProfileEditForm
  L771: UserProfileEditForm.__init__
  L775: UserProfileEditForm.clean_email
  L786: UserProfileEditForm.clean_first_name
  L789: UserProfileEditForm.clean_last_name
  L792: UserProfileEditForm.clean_phone
L796: class UserPasswordChangeForm
  L797: UserPasswordChangeForm.__init__
L807: class UserPasswordResetForm
  L808: UserPasswordResetForm.get_users
  L842: UserPasswordResetForm.__init__
  L852: UserPasswordResetForm.clean_email
L871: class UserSetPasswordForm
  L872: UserSetPasswordForm.__init__
L884: class PlainMultipleImageInput
L888: class OwnerPlaceEditForm
  L1093: OwnerPlaceEditForm.__init__
  L1305: OwnerPlaceEditForm._configure_location_choices
  L1341: OwnerPlaceEditForm._build_location_choices
  L1357: OwnerPlaceEditForm._coerce_bound_subcategory_value
  L1386: OwnerPlaceEditForm.clean
  L1514: OwnerPlaceEditForm.clean_phone1
  L1521: OwnerPlaceEditForm.clean_phone2
  L1524: OwnerPlaceEditForm.clean_phone3
  L1528: OwnerPlaceEditForm.wizard_steps
  L1533: OwnerPlaceEditForm.wizard_copy
L1538: class OwnerPlaceCreateForm
  L1552: OwnerPlaceCreateForm.__init__
  L1581: OwnerPlaceCreateForm.clean
  L1588: OwnerPlaceCreateForm.clean_phone1
  L1597: OwnerPlaceCreateForm.save
L1611: class OwnerEventForm
  L1739: OwnerEventForm.__init__
  L1783: OwnerEventForm.clean_name_az
  L1786: OwnerEventForm.clean_phone
  L1792: OwnerEventForm.clean
  L1871: OwnerEventForm.save
L1887: class OwnerTeamInvitationForm
  L1913: OwnerTeamInvitationForm.__init__
L1918: class OwnerTeamRoleUpdateForm
L1930: class OwnerSpecialistForm
  L2018: OwnerSpecialistForm.__init__
  L2044: OwnerSpecialistForm.clean
  L2115: OwnerSpecialistForm.save
```

### src/catalog/google_auth.py

```text
L63: def _language
L68: def _safe_target
L76: def _error_response
L90: def google_login
L109: def google_callback
L121: class IdentityRejected
  L122: IdentityRejected.__init__
L126: def _normalized_users
L131: def _resolve_google_user
L194: class KidsMapSocialAccountAdapter
  L195: KidsMapSocialAccountAdapter.populate_user
  L205: KidsMapSocialAccountAdapter.pre_social_login
  L220: KidsMapSocialAccountAdapter.on_authentication_error
```

### src/catalog/indexnow_signals.py

```text
L97: def _place_is_indexable
L101: def _field_value
L106: def _significant_snapshot
L113: def _indexable_seo_landing_urls
L121: def _safely_run
L128: def _notify_indexable_seo_landings
L132: def _notify_place_change
L160: def capture_place_indexnow_state
L181: def notify_indexnow_after_place_save
L212: def _notify_related_place_change
L229: def notify_indexnow_after_direct_place_relation_change
L241: def notify_indexnow_after_schedule_interval_change
L258: def notify_indexnow_after_catalog_content_save
```

### src/catalog/interfaces/geocoding.py

```text
L8: class GeocodingPoint
L14: class IGeocodingRepository
  L16: IGeocodingRepository.is_configured
  L20: IGeocodingRepository.geocode
```

### src/catalog/interfaces/repositories.py

```text
L26: class IPlaceRepository
  L28: IPlaceRepository.active_queryset
  L32: IPlaceRepository.active_queryset_with_gallery
  L36: IPlaceRepository.top_popular
  L40: IPlaceRepository.map_ready_queryset
  L44: IPlaceRepository.upcoming_temporary
  L48: IPlaceRepository.filtered_active_queryset
  L52: IPlaceRepository.claim_candidates_for_user
L56: class ISiteReviewRepository
  L58: ISiteReviewRepository.approved_queryset
L62: class ISettingsRepository
  L64: ISettingsRepository.get_catalog_settings
  L68: ISettingsRepository.get_site_settings
  L72: ISettingsRepository.list_site_gallery_images
L76: class IUserProfileRepository
  L78: IUserProfileRepository.get_or_create_for_user
  L82: IUserProfileRepository.set_phone
  L86: IUserProfileRepository.set_gender
L90: class IEmailVerificationRepository
  L92: IEmailVerificationRepository.get_by_user
  L96: IEmailVerificationRepository.get_by_email
  L100: IEmailVerificationRepository.get_pending_user_by_email
  L104: IEmailVerificationRepository.save_challenge
  L117: IEmailVerificationRepository.mark_verified
  L121: IEmailVerificationRepository.decrement_attempts
L125: class IAccountRepository
  L127: IAccountRepository.list_user_favorite_likes
  L131: IAccountRepository.list_recent_place_open_events
L135: class IPlaceOwnershipRequestRepository
  L137: IPlaceOwnershipRequestRepository.list_for_user
  L141: IPlaceOwnershipRequestRepository.latest_for_user_and_place
  L145: IPlaceOwnershipRequestRepository.create_pending
L149: class IOwnerPlaceRepository
  L151: IOwnerPlaceRepository.managed_queryset
  L155: IOwnerPlaceRepository.get_managed_by_pk
  L159: IOwnerPlaceRepository.add_gallery_images
L163: class IOwnerTeamRepository
  L165: IOwnerTeamRepository.list_members
  L169: IOwnerTeamRepository.list_invitations
  L173: IOwnerTeamRepository.list_pending_invitations_for_user
  L177: IOwnerTeamRepository.create_invitation
  L181: IOwnerTeamRepository.get_pending_owner_invitation
  L185: IOwnerTeamRepository.get_pending_invitation_for_user
  L189: IOwnerTeamRepository.accept_invitation
  L193: IOwnerTeamRepository.reject_invitation
  L197: IOwnerTeamRepository.cancel_invitation
  L201: IOwnerTeamRepository.update_membership_role
  L205: IOwnerTeamRepository.remove_membership
  L209: IOwnerTeamRepository.list_active_memberships_for_user
L213: class IPlaceReviewRepository
  L215: IPlaceReviewRepository.list_for_place_scope
  L219: IPlaceReviewRepository.get_for_place_scope
L223: class IPlaceChangeAuditRepository
  L225: IPlaceChangeAuditRepository.create_entries
```

### src/catalog/interfaces/tracking.py

```text
L10: class IEventPlaceRepository
  L12: IEventPlaceRepository.find_active_for_event
L16: class IFunnelEventRepository
  L18: IFunnelEventRepository.create_event
L31: class ISiteVisitRepository
  L33: ISiteVisitRepository.increment_or_create_hit
```

### src/catalog/legal_content.py

```text
L14: def paragraph
L18: def bullets
L22: def email_block
L26: def _current_legal_contact_email
L34: def section
L43: def sub_section
L51: def _privacy_sections_ru
L453: def _privacy_sections_az
L855: def _privacy_sections_en
L1310: def get_legal_page_content
```

### src/catalog/legal_terms_az.py

```text
L3: def _terms_sections_az
```

### src/catalog/legal_terms_en.py

```text
L3: def _terms_sections_en
```

### src/catalog/legal_terms_ru.py

```text
L3: def _terms_sections_ru
```

### src/catalog/management/commands/apply_seo_fixes.py

```text
L14: class Command
  L17: Command.add_arguments
  L36: Command.handle
```

### src/catalog/management/commands/audit_content.py

```text
L7: class Command
  L10: Command.handle
```

### src/catalog/management/commands/audit_internal_links.py

```text
L23: class Command
  L26: Command.add_arguments
  L29: Command.handle
```

### src/catalog/management/commands/audit_schema.py

```text
L23: class Command
  L26: Command.handle
```

### src/catalog/management/commands/audit_seo.py

```text
L20: class Command
  L23: Command.add_arguments
  L34: Command.handle
```

### src/catalog/management/commands/audit_sitemap.py

```text
L21: class Command
  L24: Command.add_arguments
  L31: Command.handle
  L200: Command._check_live
```

### src/catalog/management/commands/cleanup_migration_junk.py

```text
L7: class Command
  L10: Command.add_arguments
  L15: Command.handle
```

### src/catalog/management/commands/database_inventory.py

```text
L9: class Command
  L12: Command.add_arguments
  L26: Command.handle
```

### src/catalog/management/commands/diagnose_place_visibility.py

```text
L20: class Command
  L23: Command.add_arguments
  L26: Command.handle
```

### src/catalog/management/commands/diagnose_reviews.py

```text
L18: class Command
  L21: Command.add_arguments
  L29: Command.handle
  L79: Command._diagnose_place_reviews
  L138: Command._diagnose_site_reviews
```

### src/catalog/management/commands/geocode_places.py

```text
L8: class Command
  L11: Command.add_arguments
  L20: Command.handle
```

### src/catalog/management/commands/import_places.py

```text
L9: class Command
  L12: Command.add_arguments
  L15: Command.handle
  L74: Command._normalize_row
```

### src/catalog/management/commands/migrate_legacy_database.py

```text
L25: def managed_models_by_table
L34: def ordered_models
L61: def table_columns
L69: class Command
  L72: Command.add_arguments
  L82: Command.handle
  L174: Command._copy_table
  L295: Command._normalize_value
  L305: Command._prune_table
  L334: Command._build_generated_id_maps
  L388: Command._reset_sequences
  L394: Command._write_report
```

### src/catalog/management/commands/migrate_legacy_prices.py

```text
L58: class PlanDraft
  L62: PlanDraft.describe
L76: class PlaceOutcome
L83: def _decimal
L89: def build_plan_drafts
L158: class Command
  L161: Command.add_arguments
  L183: Command.handle
  L211: Command._plan_for_place
  L222: Command._apply
  L240: Command._report
```

### src/catalog/management/commands/migrate_legacy_schedules.py

```text
L21: class ScheduleOutcome
L29: class Command
  L32: Command.add_arguments
  L51: Command.handle
  L70: Command._plan_for_place
  L88: Command._apply
  L103: Command._report
L139: def _serialize
```

### src/catalog/management/commands/migrate_pricing_plans.py

```text
L11: class Command
  L14: Command.add_arguments
  L20: Command.handle
```

### src/catalog/management/commands/recalculate_ratings.py

```text
L15: class Command
  L18: Command.handle
```

### src/catalog/management/commands/report_legacy_team_access.py

```text
L14: class Command
  L17: Command.add_arguments
  L24: Command.handle
  L76: Command._label
  L82: Command._reason
```

### src/catalog/management/commands/restore_featured_places.py

```text
L87: class Command
  L90: Command.add_arguments
  L93: Command.handle
```

### src/catalog/management/commands/rollback_seo_change.py

```text
L12: class Command
  L15: Command.add_arguments
  L18: Command.handle
```

### src/catalog/management/commands/seed_catalog_demo_places.py

```text
L15: class DemoPlaceTemplate
L53: class DemoReviewTemplate
L63: class DemoEventTemplate
L77: class Command
  L85: Command.add_arguments
  L98: Command.handle
  L136: Command._apply_defaults
  L199: Command._sync_file_field
  L216: Command._sync_instance_file_field
  L232: Command._ensure_public_description
  L240: Command._sync_gallery
  L268: Command._sync_reviews
  L292: Command._sync_events
  L330: Command._build_review_templates
  L367: Command._build_event_templates
  L417: Command._repo_root
  L420: Command._build_templates
```

### src/catalog/management/commands/seed_catalog_taxonomy.py

```text
L7: class Command
  L14: Command.add_arguments
  L29: Command.handle
```

### src/catalog/management/commands/send_test_email.py

```text
L6: class Command
  L9: Command.add_arguments
  L22: Command.handle
```

### src/catalog/management/commands/seo_report.py

```text
L17: class Command
  L20: Command.add_arguments
  L23: Command.handle
```

### src/catalog/management/commands/submit_indexnow.py

```text
L15: class Command
  L18: Command.add_arguments
  L36: Command.handle
  L68: Command._current_urls
```

### src/catalog/management/commands/sync_site_defaults.py

```text
L43: class Command
  L46: Command.handle
```

### src/catalog/management/commands/validate_places.py

```text
L9: class Command
  L12: Command.add_arguments
  L17: Command.handle
```

### src/catalog/management/commands/verify_database_transfer.py

```text
L18: class Command
  L21: Command.add_arguments
  L27: Command.handle
  L96: Command._stats
  L112: Command._id_set
  L126: Command._check_relations
  L165: Command._check_duplicates
  L200: Command._check_translations
  L217: Command._check_images
  L238: Command._check_sequence
```

### src/catalog/middleware.py

```text
L15: class CanonicalPublicHostMiddleware
  L18: CanonicalPublicHostMiddleware.__init__
  L21: CanonicalPublicHostMiddleware.__call__
L29: class AdminHostRedirectMiddleware
  L37: AdminHostRedirectMiddleware.__init__
  L40: AdminHostRedirectMiddleware.__call__
L51: class CleanPublicQueryMiddleware
  L54: CleanPublicQueryMiddleware.__init__
  L57: CleanPublicQueryMiddleware.__call__
```

### src/catalog/models/category.py

```text
L17: def _read_local_svg_icon
L76: def _normalize_hex
L80: class ActiveCategoryManager
  L82: ActiveCategoryManager.get_queryset
L86: class Category
  L125: Category.name_i18n
  L138: Category.icon_name
  L142: Category.icon_file_url
  L156: Category.icon_is_svg
  L160: Category.icon_is_font_class
  L164: Category.icon_svg_source
  L168: Category.color_preset
  L172: Category.resolved_color_bg
  L178: Category.resolved_color_text
  L183: Category.archive
  L190: Category.restore
  L198: Category.__str__
L202: class ActiveSubcategoryManager
  L204: ActiveSubcategoryManager.get_queryset
L208: class Subcategory
  L242: Subcategory.archive
  L249: Subcategory.restore
  L256: Subcategory.name_i18n
  L269: Subcategory.icon_file_url
  L285: Subcategory.__str__
```

### src/catalog/models/owner.py

```text
L25: class PlaceOwnershipRequest
  L88: PlaceOwnershipRequest.__str__
  L92: PlaceOwnershipRequest.is_pending
  L96: PlaceOwnershipRequest.apply_moderation
  L137: PlaceOwnershipRequest.save
L151: class PlaceOwnershipRequestAudit
  L186: PlaceOwnershipRequestAudit.__str__
  L190: PlaceOwnershipRequestAudit.log_event
L210: class OwnerTeamMembership
  L263: OwnerTeamMembership.__str__
  L266: OwnerTeamMembership.get_permissions
L270: class OwnerTeamInvitation
  L345: OwnerTeamInvitation.__str__
  L349: OwnerTeamInvitation.is_pending
  L352: OwnerTeamInvitation.save
L359: class PlaceChangeAudit
  L400: PlaceChangeAudit.__str__
```

### src/catalog/models/place.py

```text
L18: def _localized_free_label
L27: class Place
  L204: Place._normalize_lang
  L209: Place.__init__
  L220: Place.name_i18n
  L228: Place.description_i18n
  L232: Place.address_i18n
  L237: Place.district_i18n
  L244: Place.metro_i18n
  L252: Place.safe_photo_size
  L260: Place.instagram_url
  L272: Place.website_url
  L280: Place.gallery_files
  L298: Place._public_file_exists
  L314: Place.public_image_file
  L322: Place.public_image_url
  L327: Place.has_public_image
  L331: Place.age_display
  L340: Place.clean
  L360: Place.pricing_plans
  L371: Place.pricing_plans
  L375: Place.price_range_display
  L380: Place.lesson_duration_display
  L386: Place.card_price_badge
  L390: Place.card_price_badge_label
  L394: Place.card_price_badge_value
  L398: Place.card_price_badge_currency
  L402: Place.pricing_options
  L416: Place.phone_numbers
  L425: Place._localized_text
  L432: Place.extra_conditions_i18n
  L435: Place.additional_info_i18n
  L439: Place.has_more_details
  L471: Place.has_structured_schedule
  L477: Place.has_schedule_content
  L484: Place.schedule_note_i18n
  L488: Place.schedule_rows
  L494: Place.schedule_summary
  L500: Place.has_coordinates
  L504: Place.is_deleted
  L508: Place.is_public
  L519: Place.publication_state
  L533: Place.is_map_ready
  L537: Place.map_readiness_reason
  L546: Place.soft_delete
  L556: Place.restore_from_deleted
  L566: Place.__str__
  L569: Place.get_category_display
  L575: Place.category_code
  L578: Place.get_absolute_url
  L581: Place._build_unique_slug
  L592: Place.save
  L612: Place.refresh_rating_stats
L625: class PlacePhoto
  L637: PlacePhoto.safe_image_size
  L645: PlacePhoto.__str__
L649: class PlaceScheduleDay
  L674: PlaceScheduleDay.__str__
L678: class PlaceScheduleInterval
  L694: PlaceScheduleInterval.__str__
L698: class Event
  L767: Event._normalize_lang
  L772: Event.__init__
  L779: Event.name_i18n
  L787: Event.description_i18n
  L791: Event.address_i18n
  L797: Event.has_coordinates
  L801: Event.age_display
  L811: Event.price_display
  L815: Event.has_ended
  L819: Event.is_running_now
  L826: Event.effective_status
  L832: Event.is_public
  L841: Event.instagram_url
  L853: Event.get_absolute_url
  L856: Event._build_unique_slug
  L867: Event.save
  L874: Event.__str__
  L877: Event.get_category_display
  L883: Event.category_code
L897: class EventPhoto
  L908: EventPhoto.__str__
L912: class PlaceLike
  L940: PlaceLike.save
  L944: PlaceLike.__str__
L948: class PlaceReviewsByClub
```

### src/catalog/models/pricing_plan.py

```text
L11: class PricingPlan
  L152: PricingPlan.clean
  L232: PricingPlan.save
  L236: PricingPlan.title_i18n
  L240: PricingPlan.conditions_i18n
L247: def _sync_pricing_plan_legacy_fields
```

### src/catalog/models/review.py

```text
L20: class PlaceReview
  L59: PlaceReview.__str__
  L63: PlaceReview.popularity_score
  L66: PlaceReview.refresh_reaction_stats
  L75: PlaceReview.save
  L85: PlaceReview.delete
  L92: PlaceReview.author_name_i18n
  L98: PlaceReview.text_i18n
L102: class PlaceReviewCooldown
L113: def sync_place_rating_stats
L123: def _on_place_review_saved
L129: def _on_place_review_deleted
L135: class PlaceReviewReaction
  L177: PlaceReviewReaction.save
  L183: PlaceReviewReaction.delete
L189: class SiteReview
  L232: SiteReview.__str__
  L259: SiteReview._localized_demo_value
  L266: SiteReview.author_name_i18n
  L271: SiteReview.text_i18n
  L276: SiteReview.popularity_score
  L279: SiteReview.refresh_reaction_stats
  L288: SiteReview.save
L298: class SiteReviewReaction
  L340: SiteReviewReaction.save
  L346: SiteReviewReaction.delete
```

### src/catalog/models/seo.py

```text
L5: class SEOAuditRun
  L59: SEOAuditRun.__str__
L63: class SEOIssue
  L153: SEOIssue.__str__
L157: class SEOChange
  L182: SEOChange.__str__
```

### src/catalog/models/site.py

```text
L18: def _get_solo_site_settings
L59: def _get_solo_catalog_content_settings
L66: def clear_singleton_caches
L73: class SiteSettings
  L347: SiteSettings._normalize_lang
  L352: SiteSettings._i18n_text
  L356: SiteSettings.contacts_text_i18n
  L359: SiteSettings.about_text_i18n
  L362: SiteSettings.empty_results_text_i18n
  L365: SiteSettings.home_title_i18n
  L368: SiteSettings.home_subtitle_i18n
  L371: SiteSettings.home_search_label_i18n
  L374: SiteSettings.home_search_placeholder_i18n
  L377: SiteSettings.home_cta_text_i18n
  L380: SiteSettings.footer_instagram_url
  L393: SiteSettings._footer_external_url
  L396: SiteSettings.footer_telegram_url
  L399: SiteSettings.footer_youtube_url
  L402: SiteSettings.footer_tiktok_url
  L405: SiteSettings.footer_facebook_url
  L408: SiteSettings.footer_linkedin_url
  L412: SiteSettings.get_solo
  L415: SiteSettings.save
  L422: SiteSettings.delete
  L431: SiteSettings.__str__
L435: class SiteGalleryImage
  L472: SiteGalleryImage._normalize_lang
  L477: SiteGalleryImage.title_i18n
  L490: SiteGalleryImage.__str__
L494: class SiteBrandingSettings
L501: class SiteAboutSettings
L508: class SiteContactsSettings
L515: class SiteFooterSettings
L522: class SiteEmptyStateSettings
L529: class SiteVisibilitySettings
L536: class SiteAnalytics
L543: class SiteVisit
  L562: SiteVisit.__str__
  L566: SiteVisit.today
L570: class FunnelEvent
  L638: FunnelEvent.__str__
L642: class CatalogContentSettings
  L649: CatalogContentSettings.get_solo
  L652: CatalogContentSettings.districts
  L675: CatalogContentSettings.metro_stations
  L682: CatalogContentSettings.seo_pages
  L701: CatalogContentSettings.__str__
L707: def _clear_site_settings_cache
L713: def _clear_catalog_content_settings_cache
```

### src/catalog/models/specialist.py

```text
L9: class Region
  L21: Region.name_i18n
  L25: Region.__str__
L29: class District
  L42: District.name_i18n
  L46: District.__str__
L50: class MetroStation
  L62: MetroStation.name_i18n
  L66: MetroStation.__str__
L70: class SpecialistSpecialization
  L85: SpecialistSpecialization.name_i18n
  L89: SpecialistSpecialization.__str__
L93: class Specialist
  L201: Specialist.refresh_rating_stats
  L213: Specialist.bio_i18n
  L217: Specialist.education_i18n
  L221: Specialist.experience_info_i18n
  L225: Specialist.get_absolute_url
  L229: Specialist.save
  L241: Specialist.__str__
  L245: Specialist.age_display
L255: class SpecialistPracticeLocation
  L291: SpecialistPracticeLocation.clean
  L299: SpecialistPracticeLocation.__str__
L305: class SpecialistScheduleDay
  L335: SpecialistScheduleDay.__str__
L339: class SpecialistScheduleInterval
  L355: SpecialistScheduleInterval.__str__
L359: class SpecialistDocument
  L403: SpecialistDocument.__str__
  L407: SpecialistDocument.is_verified
  L411: SpecialistDocument.is_public
L415: class SpecialistReview
  L460: SpecialistReview.__str__
  L463: SpecialistReview.save
  L468: SpecialistReview.delete
L474: def sync_specialist_rating_stats
L484: def _on_specialist_review_saved
L490: def _on_specialist_review_deleted
```

### src/catalog/models/user.py

```text
L19: class UserProfile
  L67: UserProfile.__str__
  L71: UserProfile.get_or_create_for_user
L76: class SiteRegisteredUser
L83: class StaffAccessUser
L90: class UserEmailVerification
  L112: UserEmailVerification.__str__
```

### src/catalog/models/volunteer.py

```text
L7: class VolunteerPlaceRevision
  L29: VolunteerPlaceRevision.__str__
```

### src/catalog/phone_views.py

```text
L20: def reveal_place_phones
```

### src/catalog/photo_views.py

```text
L26: def owner_photo_thumbnail
L51: def prepare_owner_photo
L74: def save_owner_photos
```

### src/catalog/proxy_apps/catalog_content/apps.py

```text
L3: class CatalogContentConfig
```

### src/catalog/proxy_apps/catalog_content/models.py

```text
L4: class ContentCatalogSettings
L11: class ContentSiteGallery
L18: class ContentSiteReview
```

### src/catalog/proxy_apps/catalog_moderation/admin.py

```text
L21: class PendingModerationAdminMixin
  L31: PendingModerationAdminMixin._source_admin
  L34: PendingModerationAdminMixin.has_module_permission
  L37: PendingModerationAdminMixin.has_view_permission
  L40: PendingModerationAdminMixin.has_change_permission
  L43: PendingModerationAdminMixin.has_add_permission
  L46: PendingModerationAdminMixin.has_delete_permission
  L49: PendingModerationAdminMixin.get_actions
  L58: PendingModerationAdminMixin.return_for_revision
  L61: PendingModerationAdminMixin.changelist_view
L84: class ModerationPlaceAdmin
  L91: ModerationPlaceAdmin.get_list_display
  L109: ModerationPlaceAdmin.get_queryset
L119: class ModerationEventAdmin
  L126: ModerationEventAdmin.get_queryset
L132: class ModerationSpecialistAdmin
  L139: ModerationSpecialistAdmin.get_queryset
L144: class ModerationReviewAdmin
  L151: ModerationReviewAdmin.get_queryset
```

### src/catalog/proxy_apps/catalog_moderation/apps.py

```text
L3: class CatalogModerationConfig
```

### src/catalog/proxy_apps/catalog_moderation/models.py

```text
L6: class ModerationPlace
L13: class ModerationEvent
L20: class ModerationReview
L28: class ModerationSpecialist
L35: class ModerationPlaceOwnershipRequest
```

### src/catalog/proxy_apps/catalog_system/apps.py

```text
L3: class CatalogSystemConfig
```

### src/catalog/proxy_apps/catalog_system/models.py

```text
L8: class SystemSiteSettings
L15: class SystemSiteBranding
L22: class SystemSiteAbout
L29: class SystemSiteContacts
L36: class SystemSiteFooter
L43: class SystemSiteEmptyState
L50: class SystemSiteAnalytics
L57: class SystemPlaceChangeAudit
L64: class SystemPlaceOwnershipRequestAudit
```

### src/catalog/proxy_apps/catalog_users/apps.py

```text
L3: class CatalogUsersConfig
```

### src/catalog/proxy_apps/catalog_users/models.py

```text
L4: class UsersSiteRegisteredUser
L11: class UsersStaffAccessUser
L18: class UsersEmailVerification
L25: class UsersOwnerTeamMembership
```

### src/catalog/repositories/django_repositories.py

```text
L54: class DjangoPlaceRepository
  L55: DjangoPlaceRepository.active_queryset
  L58: DjangoPlaceRepository.active_queryset_with_gallery
  L61: DjangoPlaceRepository.top_popular
  L68: DjangoPlaceRepository.map_ready_queryset
  L78: DjangoPlaceRepository.upcoming_temporary
  L89: DjangoPlaceRepository.filtered_active_queryset
  L95: DjangoPlaceRepository.claim_candidates_for_user
L117: class DjangoSiteReviewRepository
  L118: DjangoSiteReviewRepository.approved_queryset
L122: class DjangoSettingsRepository
  L123: DjangoSettingsRepository.get_catalog_settings
  L126: DjangoSettingsRepository.get_site_settings
  L129: DjangoSettingsRepository.list_site_gallery_images
L136: class DjangoUserProfileRepository
  L137: DjangoUserProfileRepository.get_or_create_for_user
  L140: DjangoUserProfileRepository.set_phone
  L148: DjangoUserProfileRepository.set_gender
L160: class DjangoEmailVerificationRepository
  L161: DjangoEmailVerificationRepository.get_by_user
  L164: DjangoEmailVerificationRepository.get_by_email
  L174: DjangoEmailVerificationRepository.get_pending_user_by_email
  L180: DjangoEmailVerificationRepository.save_challenge
  L205: DjangoEmailVerificationRepository.mark_verified
  L223: DjangoEmailVerificationRepository.decrement_attempts
L229: class DjangoAccountRepository
  L230: DjangoAccountRepository.list_user_favorite_likes
  L237: DjangoAccountRepository.list_recent_place_open_events
L251: class DjangoPlaceOwnershipRequestRepository
  L252: DjangoPlaceOwnershipRequestRepository.list_for_user
  L259: DjangoPlaceOwnershipRequestRepository.latest_for_user_and_place
  L266: DjangoPlaceOwnershipRequestRepository.create_pending
L275: class DjangoOwnerPlaceRepository
  L276: DjangoOwnerPlaceRepository.managed_queryset
  L289: DjangoOwnerPlaceRepository.get_managed_by_pk
  L292: DjangoOwnerPlaceRepository.add_gallery_images
L331: class DjangoOwnerTeamRepository
  L332: DjangoOwnerTeamRepository.list_members
  L339: DjangoOwnerTeamRepository.list_invitations
  L346: DjangoOwnerTeamRepository.list_pending_invitations_for_user
  L356: DjangoOwnerTeamRepository.create_invitation
  L374: DjangoOwnerTeamRepository.get_pending_owner_invitation
  L384: DjangoOwnerTeamRepository.get_pending_invitation_for_user
  L399: DjangoOwnerTeamRepository.accept_invitation
  L416: DjangoOwnerTeamRepository.reject_invitation
  L422: DjangoOwnerTeamRepository.cancel_invitation
  L428: DjangoOwnerTeamRepository.update_membership_role
  L441: DjangoOwnerTeamRepository.remove_membership
  L449: DjangoOwnerTeamRepository.list_active_memberships_for_user
L457: class DjangoPlaceReviewRepository
  L458: DjangoPlaceReviewRepository.list_for_place_scope
  L464: DjangoPlaceReviewRepository.get_for_place_scope
L472: class DjangoPlaceChangeAuditRepository
  L473: DjangoPlaceChangeAuditRepository.create_entries
  L492: DjangoPlaceChangeAuditRepository._stringify
```

### src/catalog/repositories/geocoding_repositories.py

```text
L13: class GoogleMapsGeocodingRepository
  L16: GoogleMapsGeocodingRepository.is_configured
  L19: GoogleMapsGeocodingRepository.geocode
```

### src/catalog/repositories/tracking_repositories.py

```text
L12: class DjangoEventPlaceRepository
  L13: DjangoEventPlaceRepository.find_active_for_event
L17: class DjangoFunnelEventRepository
  L18: DjangoFunnelEventRepository.create_event
L38: class DjangoSiteVisitRepository
  L39: DjangoSiteVisitRepository.increment_or_create_hit
```

### src/catalog/services/admin_analytics.py

```text
L16: def _delta_none
L25: def _build_kpi_card
L37: def _ga_period_key
L45: def _bar_items
L60: def build_statistics_context
L119: def build_site_analytics_context
```

### src/catalog/services/auth_redirects.py

```text
L26: def _is_auth_url
L38: def resolve_safe_next_url
L51: def build_header_login_url
```

### src/catalog/services/content_quality.py

```text
L48: def place_quality_error_label
L54: def place_quality_error_labels
L58: def format_place_quality_errors
L82: def contains_test_content
L92: def _normalized_junk_expression
L106: def normalized_junk_q
L122: def place_junk_q
L132: def _pricing_plan_price_q
L144: def _plan_has_public_price
L159: def _mapping_has_public_price
L174: def _place_has_pricing_plan_price
L192: def _has_price_q
L214: def _has_description_q
L226: def _has_pricing_plan_q
L236: def public_place_queryset
L283: def place_catalog_visibility_reasons
L355: def published_place_queryset
L365: def public_review_filter
L389: def public_review_queryset
L395: def approved_review_queryset
L407: class QualityCheck
  L412: QualityCheck.is_ready
L416: def place_quality_check
L432: def review_quality_check
```

### src/catalog/services/district_geometry.py

```text
L16: def _features
L21: def _point_in_ring
L35: def _polygon_contains
L39: def district_for_coordinates
```

### src/catalog/services/email_verification.py

```text
L19: class EmailVerificationResult
L26: def _ttl_minutes
L31: def _cooldown_seconds
L36: def _max_attempts
L41: def _normalize_email
L45: def _generate_code
L49: def _send_code
L80: def send_registration_code
L132: def verify_registration_code
L186: def resend_registration_code
```

### src/catalog/services/features.py

```text
L4: def is_specialists_section_enabled
L12: def require_specialists_section_enabled
L17: def is_events_section_enabled
L25: def require_events_section_enabled
```

### src/catalog/services/filtering.py

```text
L9: class PlaceListFilters
  L31: PlaceListFilters.from_request
  L69: PlaceListFilters._normalize_subcategory
  L98: PlaceListFilters._events_section_enabled
  L103: PlaceListFilters._int_or_none
  L106: PlaceListFilters._normalized_age_bounds
  L122: PlaceListFilters._normalized_price_bounds
  L134: PlaceListFilters.apply
  L238: PlaceListFilters.selected
L262: def build_new_page_stats
```

### src/catalog/services/geocoding.py

```text
L12: class PlaceGeocodingLookupResult
L20: class PlaceGeocodingResult
L27: class PlaceGeocodingService
  L31: PlaceGeocodingService.build_default
  L35: PlaceGeocodingService.build_query_from_location
  L62: PlaceGeocodingService.build_query
  L69: PlaceGeocodingService.geocode_location
  L89: PlaceGeocodingService.geocode_place
L112: def place_location_fields_changed
```

### src/catalog/services/google_analytics_reporting.py

```text
L12: def _empty_period_stats
L22: def _empty_daily_chart
L31: class GoogleAnalyticsAdminSnapshot
  L44: GoogleAnalyticsAdminSnapshot.as_context
L60: class GoogleAnalyticsAdminReportingService
  L68: GoogleAnalyticsAdminReportingService.build_snapshot
  L118: GoogleAnalyticsAdminReportingService._property_name
  L121: GoogleAnalyticsAdminReportingService._run_report
  L153: GoogleAnalyticsAdminReportingService._build_period_stats
  L173: GoogleAnalyticsAdminReportingService._build_daily_chart
  L190: GoogleAnalyticsAdminReportingService._build_top_pages
  L210: GoogleAnalyticsAdminReportingService._build_top_events
L241: def build_google_analytics_context
```

### src/catalog/services/gsc_api.py

```text
L17: class GoogleSearchConsoleService
  L20: GoogleSearchConsoleService.__init__
  L24: GoogleSearchConsoleService.is_configured
  L28: GoogleSearchConsoleService.get_search_analytics
  L54: GoogleSearchConsoleService.get_sitemap_status
```

### src/catalog/services/image_uploads.py

```text
L42: def image_upload_config
L51: def _safe_output_name
L56: def _flatten_to_rgb
L67: def _encode_webp
L92: def _normalize_uploaded_image
L184: def normalize_uploaded_image
```

### src/catalog/services/indexnow.py

```text
L33: class IndexNowSubmissionResult
L39: def indexnow_enabled
L43: def key_location
L48: def canonical_indexnow_url
L85: def localized_canonical_urls
L97: def place_canonical_urls
L104: def seo_landing_canonical_urls
L108: def _dedupe_cache_key
L113: def _eligible_urls
L127: def submit_indexnow_urls
L178: def enqueue_indexnow_urls
```

### src/catalog/services/legacy_schedule_parser.py

```text
L108: def _normalize
L116: def _fold
L120: def _parse_day_spec
L165: def _single_day
L183: def parse_legacy_schedule
L230: def describe_payload
```

### src/catalog/services/locations.py

```text
L267: def get_metro_translation
L291: def normalize_to_key
L306: def get_location_translation
L344: def _normalize_location_segment
L379: def _deduplicate_location_segments
L398: def localize_address_text
L479: def get_regions_choices
L499: def get_baku_districts_choices
L506: def get_all_districts_flat_choices
L515: def init_location_fields
L534: def configure_location_choices
L551: def clean_location_fields
```

### src/catalog/services/options.py

```text
L13: def _normalize_language
L18: def _translate_for_language
L23: def _extract_option_payload
L61: def build_localized_option
L100: def build_localized_options
L115: def find_localized_label
L128: def sort_translated_values
L142: def sort_choice_tuples
L232: def _sortable_label
```

### src/catalog/services/owner_place_use_cases.py

```text
L17: class OwnerAccessResult
L26: def ensure_owner_permission
L40: def resolve_owner_permission_scopes
L83: def place_ids_for_permission
L91: def build_owner_places_stats
```

### src/catalog/services/owner_specialist_use_cases.py

```text
L13: class OwnerSpecialistResult
L20: def _sync_primary_location
L41: def _create_pending_documents
L53: def save_owner_specialist_profile
```

### src/catalog/services/ownership_use_cases.py

```text
L12: class OwnershipRequestResult
L19: def submit_place_ownership_request
```

### src/catalog/services/permanent_place_rules.py

```text
L6: def copy
L15: def publication_errors
L46: def client_rules
```

### src/catalog/services/permanent_place_wizard.py

```text
L5: def localize_fields
L58: def ui_copy
L119: def build_steps
```

### src/catalog/services/photo_gallery.py

```text
L5: def validate_gallery_order
L14: def apply_gallery_order
```

### src/catalog/services/place_access.py

```text
L51: def permissions_for_role
L55: def is_direct_place_manager
L71: def direct_place_permissions
L81: def staff_has_place_permission
L93: def has_place_permission
L107: class PlacePermissionScope
```

### src/catalog/services/place_card_validation.py

```text
L15: class PlaceCardIssue
L22: class PlaceCardValidationResult
  L27: PlaceCardValidationResult.is_valid
L31: def _decimal
L40: def _plan_minimum
L52: def _active_primary_prices
L65: def _has_photo
L71: def _language_warning
L87: def validate_place_card
```

### src/catalog/services/place_readiness.py

```text
L36: class PlaceReadinessData
L69: class ReadinessRequirement
L84: class ReadinessIssue
L96: class ReadinessItem
  L101: ReadinessItem.code
  L105: ReadinessItem.label
  L109: ReadinessItem.is_complete
L114: class PlaceReadiness
  L120: PlaceReadiness.issues
  L124: PlaceReadiness.required_count
  L128: PlaceReadiness.completed_count
  L132: PlaceReadiness.percentage
  L138: PlaceReadiness.is_ready
  L142: PlaceReadiness.quality_codes
L146: def _text
L150: def _contains_test_content
L156: def _check_name
L164: def _check_description
L179: def _check_category
L185: def _check_subcategory
L200: def _check_region
L206: def _check_address
L215: def _check_coordinates
L226: def _check_age
L252: def _check_price
L270: def _check_phone
L276: def _check_schedule
L295: def _check_photo
L424: def _advice_short_description
L443: def _advice_cover_photo_as_main
L466: def evaluate_readiness
L498: def _has_legacy_price
L512: def _place_schedule_is_structured
L520: def readiness_data_from_place
L568: def evaluate_place_readiness
L574: def _form_value
L584: def readiness_data_from_form
L662: def _coerce_coordinate
L671: def _coerce_int
L680: def evaluate_form_readiness
L686: def format_readiness_issues
L692: def publication_blocked_message
```

### src/catalog/services/place_review_submission.py

```text
L12: def cooldown_seconds
L16: def cooldown_payload
L29: def _latest_allowed_at
L34: def get_place_review_cooldown
L41: def create_pending_place_review
```

### src/catalog/services/place_schedule.py

```text
L127: def _schedule_lang
L132: def schedule_mode_label
L138: def schedule_mode_note
L153: def _format_event_date
L161: def _upcoming_place_events
L190: def build_default_schedule_payload
L202: def parse_schedule_payload
L224: def dump_schedule_payload
L228: def is_meaningful_schedule
L237: def weekday_full_label
L242: def weekday_short_label
L247: def _coerce_bool
L253: def _parse_time
L268: def _format_time
L272: def _localized_closed_label
L281: def _localized_around_clock_label
L291: class ScheduleValidationResult
  L296: ScheduleValidationResult.is_valid
L300: def validate_schedule_payload
L392: def serialize_place_schedule
L415: def sync_place_schedule
L453: def schedule_signature
L458: def build_schedule_rows
L507: def build_schedule_summary
L514: def build_public_schedule_rows
L565: def build_public_schedule_summary
L574: def _today_weekday_key
L578: def _day_display_lines
L587: def build_public_schedule_week
L616: def build_open_status
```

### src/catalog/services/pricing_plans.py

```text
L28: def _as_int
L44: def _as_price
L56: def _legacy_plan
L74: def _compat_to_canonical
L113: def _model_to_compat
L138: def serialize_pricing_plan
L158: def serialize_pricing_plans
L162: def pricing_audit_summary
L182: def normalize_pricing_plans
L295: def replace_place_pricing_plans
L335: def _plan_bounds
L345: def sync_legacy_price_fields
L369: def public_pricing_plans
L410: def active_pricing_plan_range
L442: def has_azn_pricing_plans
L454: def format_price_amount
L461: def build_public_price_summary
L662: def build_compact_schedule_rows
L668: def _format_starting_price
L681: def format_price_range
L694: def get_starting_price
L795: def build_pricing_summary
```

### src/catalog/services/public_filter_options.py

```text
L13: class PublicPlaceFilterOptions
L20: def _with_selected_option
L36: def _move_baku_first
L48: def _build_category_option
L66: def _build_subcategory_option
L85: def build_public_place_filter_options
L227: class PublicSpecialistFilterOptions
L234: def build_public_specialist_filter_options
```

### src/catalog/services/public_urls.py

```text
L28: def public_origin
L33: def public_hostname
L38: def build_public_absolute_uri
L52: def resolve_url_name
L59: def canonical_public_path
L70: def allowed_query_params_for_path
L74: def filtered_query_string_for_path
L87: def filtered_query_string
```

### src/catalog/services/reactions.py

```text
L13: def ensure_session_key
L19: def identity_filter_for_request
L25: def likes_filter_for_request
L31: def liked_place_ids
L35: def mark_liked_flags
L40: def toggle_place_like
L73: def create_or_update_review
L111: def _reaction_actor_defaults
L117: def _toggle_review_reaction
L163: def toggle_place_review_reaction
L172: def toggle_site_review_reaction
L181: def _mark_review_reactions
L203: def mark_place_review_reactions
L207: def mark_site_review_reactions
```

### src/catalog/services/review_moderation.py

```text
L15: class ModeratedReviewText
L21: def _mask_match
L28: def _sanitize_value
L40: def moderate_review_content
```

### src/catalog/services/review_sorting.py

```text
L18: def normalize_review_sort
L24: def apply_review_sorting
```

### src/catalog/services/review_use_cases.py

```text
L13: class ReviewSubmissionResult
L21: class ReviewPayload
L28: def _author_name_from_account
L44: def _build_review_payload
L90: def submit_place_review
L140: def submit_site_review
```

### src/catalog/services/seo.py

```text
L16: def _normalize_text
L20: def _truncate_text
L27: def _catalog_cards_count
L46: def _catalog_cards_found
L59: def build_branded_seo_title
L66: def _absolute_uri
L74: def _build_breadcrumb_schema
L93: def _build_item_list_schema
L113: def _catalog_category_label
L121: def _catalog_title_base
L154: def _catalog_filter_summary
L193: def build_sitewide_schema_payload
L226: def build_home_seo_payload
L252: def build_catalog_seo_payload
L335: def _place_description
L359: def build_place_seo_payload
L545: def build_site_reviews_seo_payload
L569: def build_seo_landing_schema_payload
```

### src/catalog/services/seo_audit_engine.py

```text
L28: class SEOAuditEngine
  L29: SEOAuditEngine.__init__
  L37: SEOAuditEngine.run_audit
  L111: SEOAuditEngine._get_page
  L117: SEOAuditEngine._audit_single_url
  L152: SEOAuditEngine._audit_sitemap_and_robots
  L292: SEOAuditEngine._audit_static_routes
  L335: SEOAuditEngine._audit_seo_landings
  L380: SEOAuditEngine._audit_places_all
  L394: SEOAuditEngine._audit_place
  L501: SEOAuditEngine._check_html_meta
```

### src/catalog/services/seo_fix_engine.py

```text
L19: class SEOFixEngine
  L20: SEOFixEngine.__init__
  L26: SEOFixEngine.apply_safe_fixes
  L43: SEOFixEngine._fix_single_issue
  L131: SEOFixEngine._recheck_issue_url
  L140: SEOFixEngine.rollback_change
```

### src/catalog/services/seo_landing_aggregates.py

```text
L102: def is_judo_landing
L112: def _age_label
L122: def _price_bounds
L127: def _price_text
L132: def build_judo_landing_aggregates
```

### src/catalog/services/seo_landing_visibility.py

```text
L20: class SeoLandingVisibility
  L24: SeoLandingVisibility.pages
L32: def _query_params
L37: def _place_list_filters
L41: def seo_landing_place_queryset
L49: def _batchable_filter_q
L65: def _matching_counts
L109: def build_seo_landing_visibility
```

### src/catalog/services/slugs.py

```text
L9: def build_ascii_slug
L15: def build_unique_ascii_slug
```

### src/catalog/services/staff_activity.py

```text
L9: def staff_activity_context
```

### src/catalog/services/staff_roles.py

```text
L6: def is_volunteer
L15: def can_use_volunteer_workspace
```

### src/catalog/services/tracking.py

```text
L99: def _normalize_meta
L116: def build_google_analytics_event
L123: def queue_google_analytics_event
L136: def pop_queued_google_analytics_events
L144: class TrackingService
  L149: TrackingService.build_default
  L155: TrackingService.track_event
  L184: TrackingService.track_catalog_funnel_events
  L226: TrackingService.track_place_open_event
  L234: TrackingService.track_click_event
  L258: TrackingService.track_ai_referral_visit
  L312: TrackingService.track_cta_click_event
L335: def track_event
L352: def track_catalog_funnel_events
L361: def track_place_open_event
L365: def track_cta_click_event
L375: def track_click_event
```

### src/catalog/services/visit_tracking.py

```text
L14: class SiteVisitTracker
  L21: SiteVisitTracker.build_default
  L24: SiteVisitTracker._strip_language_prefix
  L33: SiteVisitTracker.track_request
```

### src/catalog/services/volunteer_dashboard.py

```text
L13: def _
L26: def workspace_places
L37: def display_card
L63: def dashboard_context
```

### src/catalog/services/volunteer_editor.py

```text
L8: def editor_context
```

### src/catalog/services/volunteer_places.py

```text
L21: def json_value
L25: def content_snapshot
L36: def live_snapshot
L43: def base_token
L48: def token_matches
L55: def own_places
L62: def candidate_from_payload
L73: def editor_form
L87: def _check_version
L93: def save_proposal
L140: def restart_proposal
L153: def require_reviewer
L158: def review_form
L169: def review_proposal
```

### src/catalog/sitemaps.py

```text
L14: class LocalizedSitemap
  L21: LocalizedSitemap.get_urls
L30: class StaticViewSitemap
  L33: StaticViewSitemap.items
  L52: StaticViewSitemap.location
L56: class PlaceSitemap
  L59: PlaceSitemap.items
  L62: PlaceSitemap.lastmod
L66: class SeoLandingSitemap
  L69: SeoLandingSitemap.items
  L79: SeoLandingSitemap.location
  L82: SeoLandingSitemap.lastmod
L89: class SpecialistSitemap
  L92: SpecialistSitemap.items
  L97: SpecialistSitemap.lastmod
```

### src/catalog/taxonomy_data.py

```text
L149: def category_seed_rows
L167: def subcategory_seed_rows
```

### src/catalog/templatetags/admin_dashboard_tags.py

```text
L19: def admin_filter_choices
L24: def get_dashboard_stats
L125: def get_plural_form
L144: def paginator_count_label
L164: def paginator_page_range
L169: def paginator_page_url
L174: def paginator_range_label
L184: def get_active_filter_chips
L218: def get_recent_admin_actions
L305: def get_dashboard_workspace_hubs
```

### src/catalog/templatetags/catalog_i18n.py

```text
L8: def _plural_form
L21: def review_count
L40: def tariff_count
```

### src/catalog/views.py

```text
L47: def place_pricing_api
L93: def _resolve_safe_next_url
L98: def _is_ajax_request
L102: def _build_login_redirect_url
L108: def _build_owner_create_draft_key
L137: def _engagement_login_required_response
L154: def _allowed_tracking_hosts
L165: def _has_allowed_tracking_origin
L188: def _tracking_rate_limit_exceeded
L207: def _redirect_to_login
L212: def _build_managed_places_summary
L257: def _resolve_auth_intent
L264: def home
L277: def place_list
L281: def place_new
L285: def events_landing
L296: def _render_place_list
L317: def place_detail_legacy
L322: def place_detail
L342: def toggle_place_like
L386: def _review_submission_response
L405: def add_place_review
L438: def add_site_review
L465: def site_reviews
L470: def place_reviews
L476: def vote_place_review
L519: def vote_site_review
L563: def track_event
L572: def seo_landing
L577: def about
L606: def faq_page
L634: def contacts
L732: def add_place
L747: def _permanent_redirect_with_query
L754: def legacy_for_business_redirect
L759: def place_root_redirect
L769: def legacy_owner_section_redirect
L776: def legal_page
L822: def owner_places_dashboard
L864: def _build_owner_taxonomy_picker_config
L911: def owner_place_create
L1019: def owner_event_create
L1061: def owner_event_edit
L1107: def owner_event_submit_review
L1124: def owner_event_delete
L1137: def event_detail
L1164: def owner_place_edit
L1220: def owner_place_publish
L1233: def owner_place_draft
L1246: def owner_place_submit_review
L1259: def owner_place_delete
L1272: def owner_place_gallery_photo_delete
L1288: def owner_team_dashboard
L1306: def owner_team_invite
L1328: def owner_team_cancel_invitation
L1341: def owner_team_update_member_role
L1354: def owner_team_remove_member
L1367: def owner_team_accept_invitation
L1380: def owner_team_reject_invitation
L1392: def owner_reviews_dashboard
L1410: def owner_review_approve
L1427: def owner_review_reject
L1444: def request_place_ownership
L1467: def account_verify_email
L1536: class AccountDashboardView
  L1541: AccountDashboardView.get_context_data
L1554: class AccountFavoritesView
  L1559: AccountFavoritesView.get_context_data
L1574: class AccountProfileView
  L1579: AccountProfileView._build_context
  L1594: AccountProfileView.get
  L1604: AccountProfileView.post
L1644: def account_dashboard
L1648: def account_favorites
L1652: def account_profile
L1656: def account_settings
L1660: def account_register
L1724: def account_login
L1765: def account_logout
L1771: class UserPasswordResetView
  L1779: UserPasswordResetView.form_valid
  L1807: UserPasswordResetView.form_invalid
L1831: def serve_specialist_document
L1854: def specialist_list
L2101: def specialist_detail
L2152: def add_specialist_review
L2229: def owner_specialist_create
L2260: def owner_specialist_edit
L2302: def admin_add_choice
```

### src/catalog/volunteer_forms.py

```text
L32: class VolunteerPlaceForm
  L41: VolunteerPlaceForm.__init__
  L79: VolunteerPlaceForm.clean
  L106: VolunteerPlaceForm.clean_photo
  L110: VolunteerPlaceForm.clean_cover_photo
  L114: VolunteerPlaceForm.clean_phone1
  L118: VolunteerPlaceForm.clean_phone2
  L122: VolunteerPlaceForm.clean_phone3
  L127: VolunteerPlaceForm.publication_rules
  L133: VolunteerPlaceForm.wizard_steps
  L142: VolunteerPlaceForm.wizard_copy
  L151: VolunteerPlaceForm.sections
```

### src/catalog/volunteer_middleware.py

```text
L8: class VolunteerAccessMiddleware
  L15: VolunteerAccessMiddleware.process_view
```

### src/config/database_url.py

```text
L17: def parse_database_url
```

### src/config/middleware.py

```text
L5: class AdminLocaleMiddleware
  L10: AdminLocaleMiddleware.__init__
  L13: AdminLocaleMiddleware._resolve_admin_language
  L29: AdminLocaleMiddleware.__call__
```

### src/config/settings.py

```text
L16: def _env_bool
L23: def _env_list
L27: def _is_placeholder_secret
L38: def _has_default_db_credentials
```

### src/config/views.py

```text
L17: def sitemap_xsl
L22: def public_sitemap
L66: def indexnow_key_file
L76: def robots_txt
L124: def healthz
L128: def redirect_legacy_default_language_prefix
L136: def serve_media_file
```

## Пределы проверки

Исходных файлов: 558. Python-файлов разобрано: 325. Определений в индексе: 1944.

Приложение не импортировалось и не исполнялось. База, production, браузер и внешние сервисы не опрашивались. Это документация, а не результат тестирования.
