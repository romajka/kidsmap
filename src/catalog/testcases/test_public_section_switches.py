from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Organization, SiteSettings
from catalog.models.site import SiteVisibilitySettings
from catalog.services.organization_ownership import request_join
from catalog.testcases.utils import create_quality_place


class PublicSectionSwitchTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('switch_owner')
        self.org = Organization.objects.create(owner=self.owner, name_az='Switch Network', status='published', approved_at=timezone.now(), phone='+994501234567')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner)
        request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        self.settings = SiteSettings.get_solo()

    def toggle(self, enabled):
        obj = SiteVisibilitySettings.objects.get(pk=self.settings.pk)
        obj.organizations_section_enabled = enabled
        obj.save()

    def test_off_hides_public_routes_and_navigation_without_deleting_data(self):
        self.toggle(False)
        self.assertEqual(self.client.get('/organizations/').status_code, 404)
        self.assertEqual(self.client.get(f'/organizations/{self.org.public_id}/').status_code, 404)
        for lang in ['', 'ru/', 'en/']:
            response = self.client.get('/' + lang)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, f'href="/{lang}organizations/"')
        self.assertEqual(Organization.objects.filter(pk=self.org.pk).count(), 1)
        self.toggle(True)
        self.assertEqual(self.client.get('/organizations/').status_code, 200)
        self.assertContains(self.client.get('/'), 'href="/organizations/"')

    def test_off_hides_search_and_card_links_but_preserves_place_content(self):
        from catalog.services.public_presentation import organization_matches, present
        self.toggle(False)
        self.assertEqual(organization_matches('Switch'), [])
        self.assertIsNone(present(self.place)['organization'])
        response = self.client.get('/catalog/', {'q': 'Switch'})
        self.assertNotContains(response, f'/organizations/{self.org.public_id}/')
        self.toggle(True)
        self.assertEqual(len(organization_matches('Switch')), 1)
        self.assertIsNotNone(present(self.place)['organization'])

    def test_sitemaps_follow_switch_and_flags_are_independent(self):
        from catalog.sitemaps import OrganizationSitemap, StaticViewSitemap
        from catalog.services.features import is_events_section_enabled, is_specialists_section_enabled
        before = (is_events_section_enabled(), is_specialists_section_enabled())
        self.toggle(False)
        self.assertNotIn('organization_list', StaticViewSitemap().items())
        self.assertEqual(list(OrganizationSitemap().items()), [])
        self.assertEqual((is_events_section_enabled(), is_specialists_section_enabled()), before)
        self.toggle(True)
        self.assertIn('organization_list', StaticViewSitemap().items())
        self.assertIn(self.org, OrganizationSitemap().items())

    def test_admin_form_has_three_controls_and_proxy_save_invalidates_cache(self):
        from catalog.services.features import is_organizations_section_enabled
        fields = [field for _, options in admin.site._registry[SiteVisibilitySettings].fieldsets for field in options['fields']]
        for field in ['organizations_section_enabled', 'events_section_enabled', 'specialists_section_enabled']:
            self.assertIn(field, fields)
        self.toggle(True)
        self.assertTrue(is_organizations_section_enabled())
        self.toggle(False)
        self.assertFalse(is_organizations_section_enabled())
        staff = get_user_model().objects.create_superuser('switch_admin', email='switch@example.invalid', password='test')
        self.client.force_login(staff)
        response = self.client.get(reverse('admin:catalog_sitevisibilitysettings_change', args=[self.settings.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="organizations_section_enabled"')
        self.assertContains(response, 'name="events_section_enabled"')
        self.assertContains(response, 'name="specialists_section_enabled"')

    def test_admin_section_controls_follow_selected_language(self):
        staff = get_user_model().objects.create_superuser('sections_i18n', email='sections@example.invalid', password='test')
        self.client.force_login(staff)
        url = reverse('admin:catalog_sitevisibilitysettings_change', args=[self.settings.pk])
        expected = {
            'ru': ['Показывать «Афишу»', 'Показывать «Педагогов и специалистов»',
                   'Показывать «Организации»', 'Публичное избранное', 'В настройки сайта'],
            'en': ['Show “Events”', 'Show “Educators and specialists”', 'Show “Organizations”',
                   'Public favorites', 'Back to site settings'],
            'az': ['“Tədbirlər” bölməsini göstər', '“Pedaqoqlar və mütəxəssislər” bölməsini göstər',
                   '“Təşkilatlar” bölməsini göstər', 'İctimai seçilmişlər', 'Sayt parametrlərinə qayıt'],
        }
        for language, labels in expected.items():
            with self.subTest(language=language):
                self.client.cookies['django_language'] = language
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                for label in labels:
                    self.assertContains(response, label)
                if language == 'ru':
                    self.assertContains(response, 'Галочка включена')
                    continue
                for fallback in ['Показывать «', 'Галочка включена', 'Скрывает афишу',
                                 'Скрывает каталог специалистов', 'Скрывает каталог организаций',
                                 'Публичное избранное', 'В настройки сайта']:
                    self.assertNotContains(response, fallback)
