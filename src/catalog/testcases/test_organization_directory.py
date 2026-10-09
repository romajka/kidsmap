"""Directory visibility follows approved organizations and confirmed live branches."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from catalog.models import Organization, Place
from catalog.services.organization_ownership import request_join
from catalog.testcases.utils import create_quality_place


class OrganizationDirectoryTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('directory_owner')
        self.org = Organization.objects.create(owner=self.owner, name_az='Şəbəkə', name_ru='Сеть музыки', name_en='Music network', description_az='Uşaqlar üçün', status='published', approved_at=timezone.now())
        self.place = create_quality_place(owner=self.owner, created_by=self.owner, district='baku_yasamal')
        # Establish the persisted district explicitly: shared-location assignment
        # may copy canonical address fields during model creation.
        Place.objects.filter(pk=self.place.pk).update(district='baku_yasamal')
        request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)

    def test_localized_routes_and_navigation(self):
        for path, name in [('/organizations/', 'Şəbəkə'), ('/ru/organizations/', 'Сеть музыки'), ('/en/organizations/', 'Music network')]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, name)
            self.assertEqual(response.context['cards'][0]['branch_count'], 1)

    def test_private_organizations_never_appear(self):
        for change in [{'status': 'draft'}, {'approved_at': None}, {'archived_at': timezone.now()}]:
            Organization.objects.filter(pk=self.org.pk).update(**change)
            response = self.client.get('/organizations/', {'q': 'Şəbəkə'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page_obj'].paginator.count, 0)
            Organization.objects.filter(pk=self.org.pk).update(status='published', approved_at=timezone.now(), archived_at=None)

    def test_stale_or_private_branch_does_not_count_or_match_district(self):
        for change in [{'status': 'draft'}, {'is_active': False}, {'deleted_at': timezone.now()}, {'organization_join_org_ownership_version': 999}, {'organization_join_place_ownership_version': 999}]:
            self.place.refresh_from_db()
            baseline = {key: getattr(self.place, key) for key in change}
            Place.objects.filter(pk=self.place.pk).update(**change)
            response = self.client.get('/organizations/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['cards'][0]['branch_count'], 0)
            self.assertEqual(self.client.get('/organizations/?district=baku_yasamal').context['page_obj'].paginator.count, 0)
            Place.objects.filter(pk=self.place.pk).update(**baseline)

    def test_search_district_and_empty_state(self):
        response = self.client.get('/ru/organizations/', {'q': 'музыки', 'district': 'baku_yasamal'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        self.assertEqual(self.client.get('/organizations/?q=missing').context['page_obj'].paginator.count, 0)
        response = self.client.get('/organizations/?district=unknown')
        self.assertEqual(response.context['page_obj'].paginator.count, 0)
        self.assertContains(response, 'noindex,follow')

    def test_pagination_and_detail_backlink(self):
        Organization.objects.bulk_create([Organization(name_az=f'Org {i:02}', status='published', approved_at=timezone.now()) for i in range(13)])
        response = self.client.get('/organizations/?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cards']), 2)
        self.assertContains(self.client.get(f'/organizations/{self.org.public_id}/'), 'href="/organizations/"')

    def test_directory_seo_and_language_links_preserve_only_public_filters(self):
        from catalog.services.public_urls import filtered_query_string_for_path
        from catalog.sitemaps import StaticViewSitemap
        from django.http import QueryDict
        query = QueryDict('q=Music&district=baku_yasamal&page=2&next=private')
        from django.utils.translation import override
        with override('ru'):
            self.assertEqual(filtered_query_string_for_path('/ru/organizations/', query), 'q=Music&district=baku_yasamal&page=2')
        self.assertIn('organization_list', StaticViewSitemap().items())
        self.assertContains(self.client.get('/organizations/'), 'index,follow')
        response = self.client.get('/ru/organizations/', {'q': 'Music'})
        self.assertContains(response, 'noindex,follow')
        self.assertContains(response, '/en/organizations/?q=Music')

    def test_hidden_branch_photo_is_never_used(self):
        from django.core.files.base import ContentFile
        self.place.refresh_from_db()
        self.place.photo.save('directory-test-public.jpg', ContentFile(b'synthetic-photo'), save=True)
        self.addCleanup(self.place.photo.delete, save=False)
        response = self.client.get('/organizations/')
        self.assertEqual(len(response.context['cards'][0]['photos']), 1)
        Place.objects.filter(pk=self.place.pk).update(organization_join_org_ownership_version=999)
        response = self.client.get('/organizations/')
        self.assertEqual(response.context['cards'][0]['photos'], [])
        self.assertNotContains(response, 'directory-test-public')
