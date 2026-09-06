# Full readiness branch integration ? 2026-09-06

Source: `origin/readiness-legacy-migration` at `df6fef3`. Local `main` was fast-forwarded from `1ccd06a`, including all nine commits (190 changed paths). No remote push or server deployment was performed.

## Preservation

Original local edits and SQLite database: `backups/before-full-sync-20260906-153435/`. The pre-integration Git stash is retained. Local wizard, account notice changes, gallery removal, coordinate validation and manual map-point preservation are retained. The upstream pricing editor stays at `static/js/owner_pricing_plans.js`; the wizard-specific editor is preserved as `static/js/permanent_place_pricing.js`. Upstream readiness checks take precedence; wizard submission now requires an Azerbaijani name and a subcategory. Open-ended age input remains supported.

## Local database and assets

Applied migrations 0098, 0099 and 0100. Migrated legacy prices for 25 places and structured schedule for one place. 24 ambiguous schedules remain unchanged; review list is in the backup directory. Compiled RU/AZ/EN translation catalogs and collected static assets.

## Included commits

```text
df6fef3 Add Antigravity agents, skills and project configuration
496e7a2 Add Antigravity project configuration
86a0b8c Prevent back-to-top hover state from sticking on touch
199b86a Keep back-to-top button above chat
95680b2 Integrate admin workflow and pricing updates
1788437 Prevent legacy subcategory icons from breaking admin
ec7afb9 Добавить миграцию режима расписания
4cf67db Обновить админку и шаблоны писем
17b8783 Единая проверка готовности карточки и перенос legacy-данных
```

## Complete source change inventory

```text
A	.agents/agents/analytics-reviewer/agent.md
A	.agents/agents/browser-qa/agent.md
A	.agents/agents/code-reviewer/agent.md
A	.agents/agents/data-quality-reviewer/agent.md
A	.agents/agents/database-reviewer/agent.md
A	.agents/agents/django-reviewer/agent.md
A	.agents/agents/frontend-reviewer/agent.md
A	.agents/agents/integration-reviewer/agent.md
A	.agents/agents/localization-reviewer/agent.md
A	.agents/agents/performance-reviewer/agent.md
A	.agents/agents/release-reviewer/agent.md
A	.agents/agents/security-reviewer/agent.md
A	.agents/agents/seo-reviewer/agent.md
A	.agents/mcp_config.json
A	.agents/rules/agent-orchestration.md
A	.agents/skills/baseline-ui/SKILL.md
A	.agents/skills/fixing-accessibility/SKILL.md
A	.agents/skills/frontend-design/SKILL.md
A	.agents/skills/kidsmap-ui-design/SKILL.md
A	.agents/skills/systematic-debugging/CREATION-LOG.md
A	.agents/skills/systematic-debugging/SKILL.md
A	.agents/skills/systematic-debugging/condition-based-waiting-example.ts
A	.agents/skills/systematic-debugging/condition-based-waiting.md
A	.agents/skills/systematic-debugging/defense-in-depth.md
A	.agents/skills/systematic-debugging/find-polluter.sh
A	.agents/skills/systematic-debugging/root-cause-tracing.md
A	.agents/skills/systematic-debugging/test-academic.md
A	.agents/skills/systematic-debugging/test-pressure-1.md
A	.agents/skills/systematic-debugging/test-pressure-2.md
A	.agents/skills/systematic-debugging/test-pressure-3.md
A	.agents/skills/test-driven-development/SKILL.md
A	.agents/skills/test-driven-development/writing-good-tests.md
A	.agents/skills/verification-before-completion/SKILL.md
A	.agents/skills/writing-plans/SKILL.md
A	.agents/skills/writing-plans/plan-document-reviewer-prompt.md
M	.env.example
M	docker-compose.yml
A	docs/superpowers/plans/2026-09-04-admin-notifications-modals-revamp.md
A	kidsmap_extra_agents/.agents/agents/analytics-reviewer/agent.md
A	kidsmap_extra_agents/.agents/agents/database-reviewer/agent.md
A	kidsmap_extra_agents/.agents/agents/integration-reviewer/agent.md
A	kidsmap_extra_agents/.agents/agents/localization-reviewer/agent.md
A	kidsmap_extra_agents/.agents/agents/performance-reviewer/agent.md
A	kidsmap_extra_agents/.agents/agents/release-reviewer/agent.md
A	kidsmap_extra_agents/.agents/agents/seo-reviewer/agent.md
M	locale/ru/LC_MESSAGES/django.po
A	scripts/build_place_form_icons.py
M	src/catalog/context_processors.py
M	src/catalog/controllers/owner_places_controller.py
M	src/catalog/controllers/owner_reviews_controller.py
M	src/catalog/domain_admin/place.py
M	src/catalog/domain_admin/user.py
M	src/catalog/forms.py
M	src/catalog/legal_content.py
A	src/catalog/management/commands/migrate_legacy_prices.py
A	src/catalog/management/commands/migrate_legacy_schedules.py
M	src/catalog/management/commands/sync_site_defaults.py
A	src/catalog/migrations/0098_replace_legacy_gmail_contact.py
A	src/catalog/migrations/0099_alter_place_schedule_mode.py
A	src/catalog/migrations/0100_place_price_mode.py
M	src/catalog/models/category.py
M	src/catalog/models/place.py
M	src/catalog/models/site.py
M	src/catalog/services/content_quality.py
M	src/catalog/services/email_verification.py
A	src/catalog/services/legacy_schedule_parser.py
A	src/catalog/services/place_readiness.py
M	src/catalog/services/place_schedule.py
M	src/catalog/services/pricing_plans.py
M	src/catalog/services/seo.py
M	src/catalog/templates/admin/catalog/event/change_form.html
M	src/catalog/templates/admin/catalog/event/change_list.html
M	src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html
A	src/catalog/templates/admin/catalog/includes/km_icon_sprite.html
M	src/catalog/templates/admin/catalog/place/change_form.html
M	src/catalog/templates/admin/catalog/place/change_list.html
A	src/catalog/templates/admin/catalog/place/form/_field.html
A	src/catalog/templates/admin/catalog/place/form/_langgroup.html
A	src/catalog/templates/admin/catalog/place/form/_navitem.html
A	src/catalog/templates/admin/catalog/place/form/_section_close.html
A	src/catalog/templates/admin/catalog/place/form/_section_open.html
A	src/catalog/templates/admin/catalog/place/form/dialogs.html
A	src/catalog/templates/admin/catalog/place/form/header.html
A	src/catalog/templates/admin/catalog/place/form/section_basics.html
A	src/catalog/templates/admin/catalog/place/form/section_location.html
A	src/catalog/templates/admin/catalog/place/form/section_media.html
A	src/catalog/templates/admin/catalog/place/form/section_pricing.html
A	src/catalog/templates/admin/catalog/place/form/section_verification.html
A	src/catalog/templates/admin/catalog/place/form/sidebar.html
M	src/catalog/templates/admin/catalog/place/home_recommendation_editor.html
D	src/catalog/templates/admin/catalog/place/location_section.html
D	src/catalog/templates/admin/catalog/place/media_section.html
M	src/catalog/templates/admin/catalog/place/placephoto_inline.html
M	src/catalog/templates/admin/catalog/place/pricing_editor.html
M	src/catalog/templates/admin/catalog/place_delete_confirmation.html
M	src/catalog/templates/admin/catalog/place_delete_selected_confirmation.html
M	src/catalog/templates/admin/catalog/place_restore_confirmation.html
M	src/catalog/templates/admin/catalog/placeownershiprequest/change_form.html
M	src/catalog/templates/admin/catalog/placereview/change_form.html
M	src/catalog/templates/admin/catalog/placereview/moderation_confirm.html
M	src/catalog/templates/admin/catalog/shared_settings_change_form.html
M	src/catalog/templates/admin/catalog/siteregistereduser/change_list.html
M	src/catalog/templates/admin/catalog/user/change_form.html
A	src/catalog/templates/auth/email_verification_email.html
M	src/catalog/templates/auth/login.html
M	src/catalog/templates/auth/password_reset_complete.html
M	src/catalog/templates/auth/password_reset_confirm.html
M	src/catalog/templates/auth/password_reset_done.html
A	src/catalog/templates/auth/password_reset_email.html
M	src/catalog/templates/auth/password_reset_email.txt
M	src/catalog/templates/auth/password_reset_form.html
M	src/catalog/templates/auth/password_reset_subject.txt
M	src/catalog/templates/base.html
M	src/catalog/templates/includes/place_schedule_editor.html
M	src/catalog/templates/pages/contacts.html
M	src/catalog/templates/pages/faq.html
M	src/catalog/templates/pages/includes/site_social_links.html
M	src/catalog/templates/pages/legal.html
A	src/catalog/templates/pages/listing_rules.html
M	src/catalog/templates/pages/owner_listing_type_select.html
M	src/catalog/templates/pages/owner_places.html
M	src/catalog/templates/pages/owner_reviews.html
A	src/catalog/templates/pages/review_rules.html
M	src/catalog/templatetags/admin_dashboard_tags.py
M	src/catalog/testcases/admin.py
M	src/catalog/testcases/auth_flow.py
M	src/catalog/testcases/catalog.py
A	src/catalog/testcases/legacy_migrations.py
M	src/catalog/testcases/owner.py
M	src/catalog/testcases/place_card_validation.py
A	src/catalog/testcases/place_readiness.py
M	src/catalog/testcases/place_taxonomy_admin.py
M	src/catalog/testcases/public.py
A	src/catalog/testcases/test_json_roundtrip_audit.py
A	src/catalog/testcases/test_password_reset.py
A	src/catalog/testcases/test_place_json_and_pricing_modes.py
M	src/catalog/testcases/utils.py
M	src/catalog/urls.py
M	src/catalog/views.py
M	src/config/settings.py
M	src/config/urls.py
M	src/templates/admin/index.html
M	static/admin/css/kidsmap_admin.css
A	static/admin/css/kidsmap_admin_header.css
A	static/admin/css/kidsmap_notifications.css
A	static/admin/css/pages/kidsmap_admin_form_shell.css
M	static/admin/css/pages/kidsmap_admin_sidebar.css
M	static/admin/css/pages/kidsmap_changelist.css
M	static/admin/css/pages/kidsmap_dashboard.css
M	static/admin/css/pages/kidsmap_place_form.css
D	static/admin/css/pages/kidsmap_place_pricing.css
A	static/admin/css/pages/kidsmap_users.css
A	static/admin/js/kidsmap_admin_form_shell.js
M	static/admin/js/kidsmap_category_popup.js
M	static/admin/js/kidsmap_home_recommendations.js
A	static/admin/js/kidsmap_notifications.js
M	static/admin/js/kidsmap_place_changelist.js
M	static/admin/js/kidsmap_place_form.js
M	static/admin/js/kidsmap_place_json_import.js
M	static/admin/js/kidsmap_place_location.js
A	static/admin/js/kidsmap_place_media.js
M	static/admin/js/kidsmap_review_changelist.js
M	static/admin/js/kidsmap_site_media.js
M	static/admin/js/kidsmap_taxonomy.js
A	static/admin/js/kidsmap_users.js
M	static/css/components/kidsmap_schedule_editor.css
M	static/css/motion.css
M	static/css/pages/account_profile.css
M	static/css/pages/contacts.css
A	static/css/pages/legal.css
A	static/css/pages/listing_rules.css
A	static/css/pages/review_rules.css
M	static/css/site.css
M	static/img/icon/social/facebook.svg
M	static/img/icon/social/linkedin.svg
M	static/img/icon/social/telegram.svg
M	static/img/icon/social/tiktok.svg
A	static/img/kidsmap-brand-logo.png
A	static/img/kidsmap-email-logo.png
M	static/img/kidsmap-logo.svg
A	static/img/logo-mark.svg
M	static/img/logo.svg
M	static/js/kidsmap_schedule_editor.js
M	static/js/owner_pricing_plans.js
D	stitch (4).zip
D	stitch (5).zip
D	stitch_desktop.zip
M	templates/admin/base.html
M	templates/admin/base_site.html
D	"\320\243\320\273\321\203\321\207\321\210\320\265\320\275\320\270\321\217 \320\264\320\273\321\217 Kidsmap.az.zip"
```

## Verification

Django system checks, migration consistency and JavaScript syntax checks passed. 116 HTML templates compiled successfully. Public pages returned HTTP 200, including the new footer and floating back-to-top control.

Full discovery ran 807 tests. After compiling translations, using UTF-8 on Windows, and resolving integration differences, 271 targeted tests were rerun: 250 passed, 20 failed and one errored. All 21 remaining failures/errors reproduce in a pristine checkout of the donor branch. No new failures remained in this comparison. Existing failures include admin UI expectations, audience/catalog assertions, email copy, map query counts and unavailable HEIF encoder support. Detailed machine-readable results and pristine-donor comparison are in the backup directory.

### Remaining inherited test failures

- `catalog.testcases.public.TestPublicPagesSmoke.test_en_password_reset_page_uses_english_text`
- `catalog.testcases.admin.TestAdminChangelistUI.test_shared_search_panel_rendered_in_all_models (url='/admin/catalog/siteregistereduser/')`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_admin_index_dashboard_summary_uses_real_database_counts`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_admin_place_changelist_renders_filter_select_options`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_change_form_shows_visibility_controls`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_changelist_searches_by_azerbaijani_name`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_changelist_shows_stats_and_quick_filter_counts`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_changelist_uses_compact_search_panel`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_restore_view_confirms_and_restores_place`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_shows_coordinates_and_map_readiness_statuses`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_review_admin_change_form_shows_full_text_panel`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_site_users_changelist_shows_profile_details`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_user_change_form_has_no_groups_block`
- `catalog.testcases.admin.TestAdminTemporaryEventInputs.test_place_change_page_renders_single_compact_datetime_inputs`
- `catalog.testcases.admin.TestAdminTemporaryEventInputs.test_place_changelist_filters_by_staff_member_who_added_card`
- `catalog.testcases.auth_flow.TestPasswordResetIdentifierSupport.test_password_reset_accepts_username_and_sends_email`
- `catalog.testcases.adult_classes.PlaceAdultClassesPublicTests.test_catalog_has_no_adult_filter_and_renders_compact_audience`
- `catalog.testcases.adult_classes.PlaceAdultClassesPublicTests.test_place_detail_renders_children_only_and_mixed_audience`
- `catalog.testcases.catalog.CatalogMapQueryEfficiencyTests.test_map_serialization_query_count_does_not_grow_with_schedules`
- `catalog.testcases.public.TestCatalogEnhancements.test_public_catalog_accessibility_labels_are_localized`
- `catalog.testcases.image_uploads.TestOwnerImageNormalization.test_heic_is_converted_to_webp`
