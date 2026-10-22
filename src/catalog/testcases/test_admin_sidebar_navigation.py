"""Daily navigation stays compact without losing authorized destinations."""
from pathlib import Path
import re

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from django.utils.translation import override

from catalog.domain_admin import _build_sidebar_sections


class AdminSidebarNavigationTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser(
            'sidebar_fixture', 'sidebar@example.invalid', 'fictional'
        )
        self.request = RequestFactory().get('/admin/account/emailaddress/')
        self.request.user = self.staff
        self.request.resolver_match = resolve(self.request.path)
        self.metrics = {key: 0 for key in (
            'places_total', 'events_total', 'specialists_total', 'places_deleted',
            'places_pending', 'events_pending', 'specialists_pending',
            'place_reviews_total', 'place_reviews_pending', 'ownership_pending',
        )}

    def test_technical_settings_replace_account_group_and_stay_active_on_classic_url(self):
        groups = _build_sidebar_sections(self.request, metrics=self.metrics)
        self.assertNotIn('accounts', [group['key'] for group in groups])
        settings_group = next(group for group in groups if group['key'] == 'settings')
        self.assertTrue(settings_group['active'])
        technical = next(item for item in settings_group['items']
                         if item['url'] == reverse('admin:kidsmap_navigation_technical'))
        self.assertTrue(technical['active'])
        self.client.force_login(self.staff)
        response = self.client.get(technical['url'])
        self.assertEqual(response.status_code, 200)
        for name in ('account_emailaddress', 'socialaccount_socialaccount',
                     'socialaccount_socialapp', 'socialaccount_socialtoken'):
            self.assertContains(response, reverse('admin:%s_changelist' % name))

    def test_catalog_contains_five_daily_destinations(self):
        groups = _build_sidebar_sections(self.request, metrics=self.metrics)
        catalog = next(group for group in groups if group['key'] == 'catalog')
        self.assertEqual(len(catalog['items']), 5)
        expected = {
            reverse('admin:catalog_place_changelist') + '?is_temporary__exact=0',
            reverse('admin:catalog_event_changelist'),
            reverse('admin:catalog_specialist_changelist'),
            reverse('admin:catalog_organization_changelist'),
            reverse('admin:catalog_placereview_changelist'),
        }
        self.assertEqual({item['url'] for item in catalog['items']}, expected)

    def test_final_context_merges_moderation_without_losing_existing_queues(self):
        groups = admin.site.each_context(self.request)['kidsmap_sidebar_sections']
        self.assertEqual([group['key'] for group in groups],
                         ['catalog', 'moderation', 'users', 'analytics', 'seo_monitoring', 'settings'])
        moderation = next(group for group in groups if group['key'] == 'moderation')
        urls = [item['url'] for item in moderation['items']]
        self.assertIn(reverse('admin:volunteer_moderation_hub'), urls)
        self.assertIn(reverse('admin:moderation_sla'), urls)
        self.assertEqual(len(urls), len(set(urls)))

    def test_moderation_attention_uses_pending_accessible_queues(self):
        self.metrics['places_pending'] = 3
        sections = _build_sidebar_sections(self.request, metrics=self.metrics)
        moderation = next(section for section in sections if section['key'] == 'moderation')
        self.assertTrue(moderation.get('has_pending', False))
        self.metrics['places_pending'] = 0
        sections = _build_sidebar_sections(self.request, metrics=self.metrics)
        moderation = next(section for section in sections if section['key'] == 'moderation')
        self.assertFalse(moderation.get('has_pending', False))

    def test_trash_count_does_not_mark_settings_as_pending_moderation(self):
        from catalog.domain_admin.navigation import merge_moderation_sections
        self.metrics['places_deleted'] = 4
        sections = _build_sidebar_sections(self.request, metrics=self.metrics)
        settings_group = next(section for section in sections if section['key'] == 'settings')
        trash = next(item for item in settings_group['items'] if 'deleted_state=deleted' in item['url'])
        self.assertEqual(trash['badge_count'], 4)
        self.assertFalse(settings_group.get('has_pending', False))
        final_sections = merge_moderation_sections(sections)
        final_settings = next(section for section in final_sections if section['key'] == 'settings')
        self.assertFalse(final_settings.get('has_pending', False))

    def test_localized_event_editor_marks_catalog_event_as_active(self):
        self.request = RequestFactory().get('/ru/admin/catalog/event/123/change/')
        self.request.user = self.staff
        with override('ru'):
            sections = _build_sidebar_sections(self.request, metrics=self.metrics)
        catalog = next(section for section in sections if section['key'] == 'catalog')
        event_item = next(item for item in catalog['items'] if '/catalog/event/' in item['url'])
        self.assertTrue(event_item['active'])
        self.assertTrue(catalog['active'])

    def test_localized_volunteer_moderation_keeps_merged_section_active(self):
        hub_url = reverse('admin:volunteer_moderation_hub')
        self.request = RequestFactory().get('/ru' + hub_url)
        self.request.user = self.staff
        with override('ru'):
            sections = admin.site.each_context(self.request)['kidsmap_sidebar_sections']
        moderation = next(section for section in sections if section['key'] == 'moderation')
        volunteer_item = next(item for item in moderation['items'] if item['url'] == hub_url)
        self.assertTrue(volunteer_item['active'])
        self.assertTrue(moderation['active'])

    def test_place_moderator_keeps_only_authorized_merged_queues(self):
        moderator = get_user_model().objects.create_user('place_only_moderator', is_staff=True)
        moderator.user_permissions.add(Permission.objects.get(
            content_type__app_label='catalog', codename='change_place',
        ))
        self.request = RequestFactory().get(reverse('admin:index'))
        self.request.user = moderator
        sections = admin.site.each_context(self.request)['kidsmap_sidebar_sections']
        moderation = next(section for section in sections if section['key'] == 'moderation')
        urls = {item['url'] for item in moderation['items']}
        allowed = {
            reverse('admin:catalog_moderation_moderationplace_changelist'),
            reverse('admin:volunteer_moderation_hub'),
            reverse('admin:moderation_sla'),
        }
        self.assertEqual(urls, allowed)
        for url_name in (
            'catalog_moderation_moderationevent_changelist',
            'catalog_moderation_moderationspecialist_changelist',
            'catalog_moderation_moderationreview_changelist',
            'catalog_placeownershiprequest_changelist',
        ):
            self.assertNotIn(reverse('admin:' + url_name), urls)
        self.client.force_login(moderator)
        for name in ('volunteer_moderation_hub', 'moderation_sla'):
            response = self.client.get(reverse('admin:' + name))
            self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:catalog_event_changelist'))
        self.assertEqual(response.status_code, 403)

    def test_no_duplicate_catalog_place_destination(self):
        groups = _build_sidebar_sections(self.request, metrics=self.metrics)
        catalog = next(group for group in groups if group['key'] == 'catalog')
        urls = [item['url'] for item in catalog['items']]
        self.assertEqual(len(urls), len(set(urls)))

    def test_technical_hub_is_hidden_and_denied_to_staff_without_permissions(self):
        user = get_user_model().objects.create_user('limited_sidebar', is_staff=True)
        self.request.user = user
        groups = _build_sidebar_sections(self.request, metrics=self.metrics)
        urls = [item['url'] for group in groups for item in group['items']]
        self.assertNotIn(reverse('admin:kidsmap_navigation_technical'), urls)
        self.client.force_login(user)
        for name in ('technical', 'directories'):
            response = self.client.get(reverse('admin:kidsmap_navigation_%s' % name))
            self.assertEqual(response.status_code, 403)
            self.assertNotContains(response, '/admin/socialaccount/socialtoken/', status_code=403)

    def test_technical_hub_respects_individual_account_model_permission(self):
        user = get_user_model().objects.create_user('email_only_sidebar', is_staff=True)
        model = apps.get_model('account', 'EmailAddress')
        user.user_permissions.add(Permission.objects.get(
            content_type__app_label='account', content_type__model=model._meta.model_name,
            codename='view_emailaddress',
        ))
        self.request.user = user
        groups = _build_sidebar_sections(self.request, metrics=self.metrics)
        urls = [item['url'] for group in groups for item in group['items']]
        self.assertIn(reverse('admin:kidsmap_navigation_technical'), urls)
        self.client.force_login(user)
        response = self.client.get(reverse('admin:kidsmap_navigation_technical'))
        self.assertContains(response, reverse('admin:account_emailaddress_changelist'))
        for name in ('socialaccount', 'socialapp', 'socialtoken'):
            self.assertNotContains(response, reverse('admin:socialaccount_%s_changelist' % name))

    def test_volunteer_keeps_specialized_menu_and_cannot_enter_settings_hubs(self):
        volunteer = get_user_model().objects.create_user('nav_volunteer', is_staff=True)
        group, _ = Group.objects.get_or_create(name='KidsMap Volunteers')
        volunteer.groups.add(group)
        self.request.user = volunteer
        groups = admin.site.each_context(self.request)['kidsmap_sidebar_sections']
        self.assertEqual([group['key'] for group in groups], ['volunteer'])
        self.client.force_login(volunteer)
        for name in ('directories', 'technical'):
            response = self.client.get(reverse('admin:kidsmap_navigation_%s' % name))
            self.assertEqual(response.status_code, 403)

    def test_every_menu_icon_references_an_existing_vector_symbol(self):
        from catalog.templatetags.kidsmap_navigation import navigation_icon
        symbols = set(re.findall(
            r'id="kmi-([^"]+)"',
            (Path(settings.BASE_DIR) / 'src/catalog/templates/admin/catalog/includes/km_icon_sprite.html').read_text(),
        ))
        for group in _build_sidebar_sections(self.request, metrics=self.metrics):
            for item in [group, *group['items']]:
                symbol = navigation_icon(item['icon'])
                self.assertIn(symbol, symbols)
                self.assertNotIn(symbol, {'radio_button_checked', 'radio_button_unchecked'})
        for source in ('templates/admin/base.html', 'src/templates/admin/base.html'):
            self.assertIn('admin/catalog/includes/sidebar_navigation.html',
                          (Path(settings.BASE_DIR) / source).read_text())
