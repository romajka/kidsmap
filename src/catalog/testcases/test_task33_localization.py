"""Stage21: approved content languages, stable URLs and factual public SEO."""
import json
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Activity, Organization, Program, OfferingGroup, PricingPlan, Place
from catalog.services import organization_ownership, publication
from catalog.testcases.utils import create_quality_place, create_ready_place


@override_settings(PUBLIC_BASE_URL='https://kidsmap.az', LOCALIZED_PLACE_URLS_ENABLED=True)
class LocalizationContractsTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('locale21_owner', email='locale21@example.invalid')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner,
            name_az='Yerli məkan', name_ru='', name_en='', description_ru='', description_en='')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner,
            name_az='Açıq təşkilat', description_az='Təsdiqlənmiş məlumat',
            status='published', approved_at=timezone.now())
        organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        self.place.refresh_from_db()
        self.program = Program.objects.create(organization=self.org, name_az='Musiqi proqramı',
            description_az='Uşaqlar üçün musiqi məşğələləri', status='published', approved_at=timezone.now())
        self.activity = Activity.objects.create(place=self.place, program=self.program, status='published', supplement_az='Yerli əlavə')
        self.group = OfferingGroup.objects.create(activity=self.activity, name_az='Kiçik qrup',
            language='en', age_from=5, age_to=8, schedule_text='Şənbə 10:00')
        PricingPlan.objects.create(offering_group=self.group, product_type='lesson', price='25')

    def place_path(self, language):
        with override(language):
            return self.place.get_absolute_url()

    def entity_path(self, entity, language):
        prefix = '' if language == 'az' else '/' + language
        if isinstance(entity, Organization):
            return f'{prefix}/organizations/{entity.public_id}/'
        return f'{prefix}/activities/{entity.pk}/'

    def test_az_only_place_is_canonical_az_and_has_only_az_alternate(self):
        response = self.client.get(self.place_path('ru'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + self.place_path('az'))
        self.assertEqual(set(response.context['alternate_urls']), {'az'})
        self.assertContains(response, 'data-translation-fallback')
        self.assertEqual(json.loads(response.context['place_schema_json'])['url'], response.context['canonical_url'])

    def test_locale_switch_keeps_untranslated_page_accessible(self):
        response = self.client.get(self.place_path('az'))
        self.assertContains(response, 'href="https://kidsmap.az' + self.place_path('ru') + '"')
        self.assertNotContains(response, '<link rel="alternate" hreflang="ru"')
        self.assertEqual(self.client.get(self.place_path('en')).status_code, 200)

    def test_name_only_is_not_a_substantive_translation(self):
        Place.objects.filter(pk=self.place.pk).update(name_ru='Местный центр')
        self.place.refresh_from_db()
        response = self.client.get(self.place_path('ru'))
        self.assertEqual(set(response.context['alternate_urls']), {'az'})
        self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + self.place_path('az'))

    def test_mixed_translation_labels_each_field_with_its_actual_language(self):
        Place.objects.filter(pk=self.place.pk).update(name_ru='Местный центр')
        self.place.refresh_from_db()
        response = self.client.get(self.place_path('ru'))
        data = response.context['presentation']
        self.assertEqual(data['name_language'], 'ru')
        self.assertEqual(data['description_language'], 'az')
        self.assertContains(response, 'lang="ru">Местный центр</h1>')
        self.assertContains(response, 'class="detail-prose" lang="az"')

    def test_complete_ru_translation_is_reciprocal_without_en(self):
        Place.objects.filter(pk=self.place.pk).update(name_ru='Местный центр', description_ru='Занятия музыкой для детей')
        self.place.refresh_from_db()
        for language in ('az', 'ru'):
            response = self.client.get(self.place_path(language))
            self.assertEqual(set(response.context['alternate_urls']), {'az', 'ru'})
            self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + self.place_path(language))
            for alternate in ('az', 'ru'):
                self.assertEqual(response.context['alternate_urls'][alternate], 'https://kidsmap.az' + self.place_path(alternate))

    def test_sitemap_excludes_incomplete_translations(self):
        from catalog.sitemaps import PlaceSitemap
        Place.objects.filter(pk=self.place.pk).update(name_ru='Местный центр')
        locations = {item['location'] for item in PlaceSitemap().get_urls(site=SimpleNamespace(domain='kidsmap.az'))}
        self.assertEqual(locations, {'https://kidsmap.az' + self.place_path('az')})
        Place.objects.filter(pk=self.place.pk).update(description_ru='Занятия музыкой для детей')
        self.place.refresh_from_db()
        locations = {item['location'] for item in PlaceSitemap().get_urls(site=SimpleNamespace(domain='kidsmap.az'))}
        self.assertEqual(locations, {'https://kidsmap.az' + self.place_path('az'), 'https://kidsmap.az' + self.place_path('ru')})

    def test_organization_has_factual_schema_and_az_fallback(self):
        response = self.client.get(self.entity_path(self.org, 'en'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + self.entity_path(self.org, 'az'))
        self.assertIn('entity_schema_json', response.context)
        schema = json.loads(response.context['entity_schema_json'])
        self.assertEqual(schema['@type'], 'Organization')
        self.assertEqual(schema['name'], 'Açıq təşkilat')
        for field in ('aggregateRating', 'address', 'geo', 'startDate'):
            self.assertNotIn(field, schema)

    def test_activity_partial_program_translation_keeps_az_canonical(self):
        Program.objects.filter(pk=self.program.pk).update(name_ru='Музыка', description_ru='Музыкальные занятия')
        response = self.client.get(self.entity_path(self.activity, 'ru'))
        self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + self.entity_path(self.activity, 'az'))
        self.assertEqual(set(response.context['alternate_urls']), {'az'})

    def test_complete_activity_translation_has_own_canonical_and_course_facts(self):
        Program.objects.filter(pk=self.program.pk).update(name_ru='Музыка', description_ru='Музыкальные занятия')
        Activity.objects.filter(pk=self.activity.pk).update(supplement_ru='Местное дополнение')
        response = self.client.get(self.entity_path(self.activity, 'ru'))
        self.assertEqual(set(response.context['alternate_urls']), {'az', 'ru'})
        self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + self.entity_path(self.activity, 'ru'))
        self.assertIn('entity_schema_json', response.context)
        schema = json.loads(response.context['entity_schema_json'])
        self.assertEqual(schema['@type'], 'Course')
        self.assertEqual(schema['name'], 'Музыка')
        for field in ('aggregateRating', 'startDate', 'endDate', 'geo'):
            self.assertNotIn(field, schema)

    def test_entity_sitemaps_only_offer_substantive_approved_languages(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://kidsmap.az' + self.entity_path(self.org, 'az'))
        self.assertNotContains(response, 'https://kidsmap.az' + self.entity_path(self.org, 'ru'))
        self.assertContains(response, 'https://kidsmap.az' + self.entity_path(self.activity, 'az'))
        Organization.objects.filter(pk=self.org.pk).update(status='draft')
        response = self.client.get('/sitemap.xml')
        self.assertNotContains(response, 'https://kidsmap.az' + self.entity_path(self.org, 'az'))

    def test_activity_sitemap_language_checks_do_not_load_full_price_presentations(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from catalog.sitemaps import ActivitySitemap
        Activity.objects.bulk_create([Activity(place=self.place, program=self.program,
            status='published') for _ in range(4)])
        with CaptureQueriesContext(connection) as queries:
            urls = ActivitySitemap().get_urls(site=SimpleNamespace(domain='kidsmap.az'))
        self.assertEqual(len(urls), 5)
        self.assertLessEqual(len(queries), 80,
            'Language eligibility must not resolve groups, tariff offers and contacts repeatedly')

    def test_hidden_program_with_empty_legacy_activity_is_not_a_sitemap_entry(self):
        from catalog.sitemaps import ActivitySitemap
        Program.objects.filter(pk=self.program.pk).update(status='draft')
        Activity.objects.filter(pk=self.activity.pk).update(program_snapshot={},
            name_az='', name_ru='', name_en='', description_az='', description_ru='', description_en='')
        response = self.client.get(self.entity_path(self.activity, 'az'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['presentation']['name'], '')
        self.assertEqual(response.context['presentation']['description'], '')
        self.assertEqual(ActivitySitemap().get_urls(site=SimpleNamespace(domain='kidsmap.az')), [])

    def test_related_group_and_tariff_fallback_text_has_actual_language(self):
        OfferingGroup.objects.filter(pk=self.group.pk).update(conditions_az='8 uşağa qədər')
        PricingPlan.objects.filter(offering_group=self.group).update(title_az='Əsas dərs', conditions_az='Ayda dörd dərs')
        response = self.client.get(self.entity_path(self.activity, 'ru'))
        group = response.context['presentation']['groups'][0]
        self.assertEqual(group['name_language'], 'az')
        self.assertEqual(group['conditions_language'], 'az')
        self.assertEqual(group['prices'][0]['title_language'], 'az')
        self.assertEqual(group['prices'][0]['conditions_language'], 'az')
        self.assertContains(response, '<h3 lang="az">Kiçik qrup</h3>')
        self.assertContains(response, '<span lang="az">Əsas dərs</span>')
        self.assertContains(response, '<p lang="az">Ayda dörd dərs</p>')
        self.assertContains(response, 'href="' + self.entity_path(self.org, 'ru') + '" lang="az"')
        self.assertContains(response, 'href="' + self.place_path('ru') + '" lang="az"')

    def test_fallback_metadata_does_not_translate_navigation_or_class_title_to_az(self):
        response = self.client.get(self.place_path('en'))
        crumbs = response.context['place_breadcrumb_items']
        self.assertEqual([item['name'] for item in crumbs[:2]], ['Home', 'Catalog'])
        self.assertEqual([item['url'] for item in crumbs[:2]], ['/en/', '/en/catalog/'])
        self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + self.place_path('az'))
        response = self.client.get(self.entity_path(self.activity, 'en'))
        self.assertEqual(response.context['presentation']['groups'][0]['prices'][0]['title'], 'Lesson')

    def test_script_termination_text_remains_data_in_entity_schema(self):
        hostile = 'Musiqi </script><script>alert(1)</script> & dərslər'
        Organization.objects.filter(pk=self.org.pk).update(description_az=hostile)
        response = self.client.get(self.entity_path(self.org, 'az'))
        self.assertIn('entity_schema_json', response.context)
        encoded = response.context['entity_schema_json']
        self.assertNotIn('<', encoded)
        self.assertNotIn('>', encoded)
        self.assertEqual(json.loads(encoded)['description'], hostile)

    def test_closed_historical_place_has_200_notice_and_no_current_offers(self):
        Place.objects.filter(pk=self.place.pk).update(operating_state='closed', operating_state_approved_at=timezone.now())
        response = self.client.get(self.place_path('az'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-operating-state="closed"')
        self.assertNotIn('noindex', response.context['robots_content'])
        schema = json.loads(response.context['place_schema_json'])
        self.assertNotIn('offers', schema)
        self.assertNotIn('openingHoursSpecification', schema)
        self.assertNotContains(self.client.get('/catalog/'), self.place_path('az'))
        payload = self.client.get('/api/catalog/map/').json()
        self.assertEqual(payload['count'], 0)

    def test_unpublished_place_does_not_become_a_historical_public_page(self):
        Place.objects.filter(pk=self.place.pk).update(is_active=False)
        self.assertEqual(self.client.get(self.place_path('az')).status_code, 404)

    def test_old_identifier_and_wrong_slug_redirect_to_same_language_without_chain(self):
        prefix = '/ru'
        for path in (f'{prefix}/place/{self.place.pk}/', f'{prefix}/place/{self.place.pk}-wrong/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response['Location'], self.place_path('ru'))
            self.assertEqual(self.client.get(response['Location']).status_code, 200)

    def test_locale_does_not_change_currency_country_or_class_language(self):
        from catalog.services.public_presentation import present
        for language in ('az', 'ru', 'en'):
            data = present(self.activity, language)
            self.assertEqual(data['groups'][0]['language'], 'en')
            self.assertEqual(data['groups'][0]['schedule'], 'Şənbə 10:00')
            offers = data['prices']['schema_offers']
            if isinstance(offers, dict): offers = [offers]
            self.assertEqual({offer['priceCurrency'] for offer in offers}, {'AZN'})
            response = self.client.get(self.place_path(language))
            self.assertEqual(json.loads(response.context['place_schema_json'])['address']['addressCountry'], 'AZ')

    def test_explicit_offer_locale_does_not_depend_on_ambient_translation(self):
        from catalog.services.public_presentation import present
        with override('az'):
            data = present(self.activity, 'en')
        self.assertEqual(data['groups'][0]['prices'][0]['title'], 'Lesson')
        self.assertEqual(data['prices']['schema_offers']['name'], 'Lesson')
        self.assertEqual(data['prices']['schema_offers']['priceCurrency'], 'AZN')

    def test_new_publication_requires_az_and_does_not_require_ru_en(self):
        reviewer = get_user_model().objects.create_superuser('locale21_reviewer', 'review21@example.invalid', 'synthetic-only')
        place = create_ready_place(status='draft', name_az='', name_ru='Музыка', name_en='',
            description_ru='Занятия музыкой для детей', description_en='')
        with self.assertRaises(ValidationError):
            publication.publish(actor=reviewer, place_id=place.pk, expected_version=place.content_version)
        Place.objects.filter(pk=place.pk).update(name_az='Musiqi mərkəzi', name_ru='', description_ru='')
        place.refresh_from_db()
        approved = publication.publish(actor=reviewer, place_id=place.pk, expected_version=place.content_version)
        self.assertTrue(approved.is_public)
