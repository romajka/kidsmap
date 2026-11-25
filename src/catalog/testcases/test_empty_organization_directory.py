"""An empty organization directory stays reachable but is not promoted."""
from django.test import TestCase
from django.utils import timezone

from catalog.models import Organization, SiteSettings
from catalog.sitemaps import StaticViewSitemap


class EmptyOrganizationDirectoryTests(TestCase):
    def setUp(self):
        site = SiteSettings.get_solo()
        site.organizations_section_enabled = True
        site.save()

    def publish(self):
        return Organization.objects.create(name_az='Şəbəkə', name_ru='Сеть', name_en='Network',
                                           status='published', approved_at=timezone.now())

    def test_empty_directory_is_noindex_and_hidden_from_navigation_and_sitemap(self):
        Organization.objects.create(name_az='Gizli', status='draft')
        for prefix in ('', '/ru', '/en'):
            with self.subTest(prefix=prefix):
                response = self.client.get(prefix + '/organizations/')
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<meta name="robots" content="noindex,follow"', html=False)
                self.assertFalse(response.context['is_organizations_directory_listed'])
        self.assertNotIn('organization_list', StaticViewSitemap().items())
        home = self.client.get('/ru/')
        self.assertNotContains(home, 'href="/ru/organizations/"', html=False)
        self.assertNotIn('/organizations/', self.client.get('/llms.txt').content.decode())

    def test_directory_with_published_organization_is_promoted_again(self):
        self.publish()
        response = self.client.get('/ru/organizations/')
        self.assertNotContains(response, '<meta name="robots" content="noindex,follow"', html=False)
        self.assertTrue(response.context['is_organizations_directory_listed'])
        self.assertIn('organization_list', StaticViewSitemap().items())
        self.assertContains(self.client.get('/ru/'), 'href="/ru/organizations/"', html=False)
        self.assertIn('/organizations/', self.client.get('/llms.txt').content.decode())
