"""Public discovery keeps exact suitability while accepting language variants."""
from django.test import TestCase
from django.utils import timezone

from catalog.models import Activity, Category, OfferingGroup, Organization, Place, PricingPlan
from catalog.services.filtering import PlaceListFilters
from catalog.testcases.utils import create_quality_place


class SearchQueryVariantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.swim = create_quality_place(name='Swim fixture', name_ru='плавание для детей',
            name_az='Su dərsləri', category='SPRT', district='baku_yasamal')
        cls.pool = create_quality_place(name='Pool fixture', name_ru='бассейн для отдыха',
            name_az='İstirahət', category='SPRT', district='baku_yasamal')
        cls.hidden = create_quality_place(name='Hidden fixture', name_ru='плавание скрытое',
            status='draft', category='SPRT')
        cls.school = create_quality_place(name='School fixture', name_ru='школа плавания',
            name_az='Məktəb', category='SPRT')
        # Stored regional legacy data; do not invoke the unrelated new-location
        # boundary resolver (this fixture has no imported regional polygons).
        Place.objects.filter(pk=cls.school.pk).update(district='sumgait',
            address='Sumqayıt şəhəri', lat=40.589, lng=49.668)
        cls.brand = create_quality_place(name='Indigo Brand', name_az='Indigo Brand', category='EDU')

    def ids(self, query, **kwargs):
        return set(PlaceListFilters(query=query, **kwargs).apply(Place.objects.all()).values_list('pk', flat=True))

    def test_latin_transliteration_finds_cyrillic_name(self):
        self.assertIn(self.swim.pk, self.ids('plavanie'))
        self.assertIn(self.school.pk, self.ids('shkola plavaniya'))

    def test_reviewed_equivalents_work_across_three_languages(self):
        for query in ('swimming', 'üzgüçülük', 'uzguculuk', 'PLAVANIE'):
            with self.subTest(query=query):
                self.assertIn(self.swim.pk, self.ids(query))
                self.assertNotIn(self.pool.pk, self.ids(query))

    def test_literal_brand_and_unknown_queries_do_not_become_generic_results(self):
        self.assertIn(self.brand.pk, self.ids('Indigo'))
        self.assertEqual(self.ids('utterlyunknownxyz'), set())
        self.assertEqual(self.ids('plavanie indigo'), set())

    def test_transliteration_keeps_geography_and_category_constraints(self):
        self.assertEqual(self.ids('shkola plavaniya', district='baku'), set())
        self.assertEqual(self.ids('plavanie', category='ART'), set())
        self.assertIn(self.swim.pk, self.ids('plavanie', district='baku', category='SPRT'))

    def test_empty_query_still_returns_unfiltered_catalog(self):
        self.assertIn(self.pool.pk, self.ids(''))
        self.assertIn(self.brand.pk, self.ids(''))

    def test_autocomplete_and_catalog_keep_private_cards_hidden(self):
        for lang, prefix in [('az', ''), ('ru', '/ru'), ('en', '/en')]:
            with self.subTest(lang=lang):
                response = self.client.get('/api/catalog/suggestions/', {'q':'plavanie', 'lang':lang})
                self.assertEqual(response.status_code, 200)
                ids = {p['id'] for p in response.json()['places']}
                self.assertIn(self.swim.pk, ids)
                self.assertNotIn(self.hidden.pk, ids)
                self.assertNotIn(self.pool.pk, ids)
                response = self.client.get(prefix + '/catalog/', {'q':'plavanie'})
                self.assertContains(response, f'data-place-id="{self.swim.pk}"')
                self.assertNotContains(response, f'data-place-id="{self.hidden.pk}"')
                self.assertNotContains(response, f'data-place-id="{self.pool.pk}"')

    def test_category_autocomplete_accepts_transliteration(self):
        Category.objects.filter(code='SPRT').update(name='Climbing', name_ru='Скалолазание',
            name_en='Climbing', name_az='Dırmanma')
        data = self.client.get('/api/catalog/suggestions/', {'q':'skalolazanie', 'lang':'ru'}).json()
        self.assertIn('SPRT', {cat['code'] for cat in data['categories']})

    def test_organization_discovery_uses_same_name_variants_and_visibility(self):
        from catalog.services.public_presentation import organization_matches
        Organization.objects.create(name_az='Məktəb', name_ru='шахматная школа',
            status='published', approved_at=timezone.now())
        Organization.objects.create(name_az='Hidden', name_ru='шахматная школа скрыта', status='draft')
        matches = organization_matches('shakhmatnaya shkola', 'ru')
        self.assertEqual([row['name'] for row in matches], ['шахматная школа'])

    def test_activity_alias_does_not_combine_age_or_price_from_other_lesson(self):
        place = create_quality_place(name='Mixed activities', name_az='Dərslər', category='SPRT')
        swimming = Activity.objects.create(place=place, status='published', name_ru='плавание',
            program_snapshot={'category_id':'SPRT'})
        group = OfferingGroup.objects.create(activity=swimming, name_ru='старшая группа', age_from=8, age_to=12)
        PricingPlan.objects.create(offering_group=group, product_type='lesson', price=100)
        chess = Activity.objects.create(place=place, status='published', name_az='Chess',
            program_snapshot={'category_id':'SPRT'})
        other = OfferingGroup.objects.create(activity=chess, name_az='Younger', age_from=4, age_to=6)
        PricingPlan.objects.create(offering_group=other, product_type='lesson', price=20)
        self.assertIn(place.pk, self.ids('plavanie', age='9', price_to='120'))
        self.assertNotIn(place.pk, self.ids('plavanie', age='5'))
        self.assertNotIn(place.pk, self.ids('plavanie', age='9', price_to='30'))
        group.archived_at = timezone.now()
        group.save(update_fields=['archived_at'])
        self.assertNotIn(place.pk, self.ids('plavanie', age='9'))

    def test_approved_snapshot_text_can_be_found_by_transliteration(self):
        place = create_quality_place(name='Snapshot fixture', name_az='Mərkəz', category='SPRT')
        activity = Activity.objects.create(place=place, status='published', name_az='Dərs',
            program_snapshot={'name_ru':'шахматы', 'category_id':'SPRT'})
        OfferingGroup.objects.create(activity=activity, name_az='Qrup', age_from=5, age_to=10)
        self.assertIn(place.pk, self.ids('shakhmaty', age='7'))


class ExtendedActivityEquivalentTests(TestCase):
    """Common activities are found whichever language or keyboard a parent uses."""

    @classmethod
    def setUpTestData(cls):
        cls.dance = create_quality_place(name='Dance fixture', name_ru='Танцевальная студия',
            name_az='Rəqs studiyası', name_en='Dance studio', category='SPRT')
        cls.football = create_quality_place(name='Ball fixture', name_ru='Детская футбольная школа',
            name_az='Uşaq futbol məktəbi', name_en='Kids football school', category='SPRT')
        cls.chess = create_quality_place(name='Chess fixture', name_ru='Шахматная школа',
            name_az='Məktəb', category='EDU')
        cls.official = create_quality_place(name='Official fixture', name_az='Rəsmi mərkəz',
            name_ru='Центр', category='EDU')

    def ids(self, query):
        return set(PlaceListFilters(query=query).apply(Place.objects.all()).values_list('pk', flat=True))

    def test_dance_is_found_from_every_language_and_latin_keyboard(self):
        for query in ('танцы', 'tancy', 'dance', 'rəqs', 'reqs'):
            with self.subTest(query=query):
                self.assertIn(self.dance.pk, self.ids(query))
                self.assertNotIn(self.football.pk, self.ids(query))

    def test_football_is_found_from_every_language(self):
        for query in ('футбол', 'futbol', 'football', 'soccer'):
            with self.subTest(query=query):
                self.assertIn(self.football.pk, self.ids(query))
                self.assertNotIn(self.dance.pk, self.ids(query))

    def test_stems_match_inflected_names(self):
        self.assertIn(self.chess.pk, self.ids('шахматы'))
        self.assertIn(self.chess.pk, self.ids('chess'))

    def test_unlisted_words_are_not_expanded(self):
        # "rəsm" is deliberately not a reviewed term: it would reach "Rəsmi".
        self.assertEqual(self.ids('рисование'), set())
        self.assertEqual(self.ids('бассейн'), set())
