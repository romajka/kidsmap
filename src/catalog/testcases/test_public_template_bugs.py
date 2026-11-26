"""Public regressions for locale fallback, place type and free guide selection."""
import json
import re

from django.test import TestCase, override_settings
from django.utils.translation import override

from catalog.models import Place, PricingPlan
from catalog.testcases.utils import create_quality_place


@override_settings(PUBLIC_BASE_URL='', LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class PublicTemplateBugTests(TestCase):
    def test_moderation_time_uses_the_page_language(self):
        for prefix, value in (('/ru', '24 часа'), ('/en', '24 hours'), ('', '24 saat')):
            with self.subTest(prefix=prefix):
                response = self.client.get(prefix + '/add-place/')
                self.assertContains(response, f'<span class="add-place-stat-value">{value}</span>', html=True)

    def test_russian_about_does_not_fall_back_to_az_favorites(self):
        response = self.client.get('/ru/about/')
        chip = re.search(r'<span class="about-feature-chip"><span class="material-symbols-rounded">favorite</span>\s*([^<]+)</span>', response.content.decode())
        self.assertIsNotNone(chip)
        self.assertEqual(chip.group(1), 'Избранное')

    def test_empty_review_heading_is_translated(self):
        for prefix, heading in (('/en', 'No reviews with text yet.'), ('', 'Hələ mətnli rəy yoxdur.')):
            with self.subTest(prefix=prefix):
                response = self.client.get(prefix + '/reviews/')
                self.assertContains(response, heading)
                self.assertNotContains(response, 'Пока нет отзывов с текстом')

    def test_place_type_is_visible_beside_name_and_absent_from_facts(self):
        place = create_quality_place(name='Synthetic athletics', name_az='Atletika', name_ru='Атлетика',
                                     name_en='Athletics', lesson_format='individual', lesson_duration_minutes=60)
        for lang, kind, label in (
            ('az', 'Daimi məkan', 'Məkan növü'),
            ('ru', 'Постоянное место', 'Тип места'),
            ('en', 'Permanent place', 'Place type'),
        ):
            with self.subTest(lang=lang), override(lang):
                response = self.client.get(place.get_absolute_url())
                html = response.content.decode()
                intro = html.split('class="place-poster__intro"', 1)[1].split('</h1>', 1)[0] + '</h1>'
                facts = html.split('class="detail-facts"', 1)[1].split('</section>', 1)[0]
                self.assertInHTML(f'<span class="place-poster__kind">{kind}</span>', '<div' + intro + '</div>')
                self.assertIn(place.name_i18n(lang), intro.split('<h1', 1)[1])
                self.assertNotIn(kind, facts)
                self.assertNotIn(label, facts)
                for section in (intro, facts):
                    self.assertNotIn('Individual', section)
                if lang == 'en':
                    self.assertContains(response, '60 min')
                    self.assertNotContains(response, '60 мин')

    def test_weekday_abbreviation_has_a_localized_screen_reader_name(self):
        place = create_quality_place(with_schedule_days=True)
        for lang, short, full in (('ru', 'Сб', 'Суббота'), ('az', 'Şən', 'Şənbə'), ('en', 'Sat', 'Saturday')):
            with self.subTest(lang=lang), override(lang):
                response = self.client.get(place.get_absolute_url())
                self.assertContains(response, f'<abbr title="{full}"><span aria-hidden="true">{short}</span>'
                                    f'<span class="visually-hidden">{full}</span></abbr>', html=True, count=1)
                self.assertContains(response, '10:00–16:00')

    def test_english_detail_duration_does_not_fall_back_to_russian(self):
        place = create_quality_place(name='Synthetic duration', lesson_duration_minutes=60)
        with override('en'):
            response = self.client.get(place.get_absolute_url())
        self.assertContains(response, '60 min')
        self.assertNotContains(response, '60 мин')

    def test_english_tariff_format_badges_are_translated(self):
        for lesson_format, label in (('group', 'Group'), ('individual', 'Individual'), ('open_visit', 'Open visit')):
            with self.subTest(lesson_format=lesson_format):
                place = create_quality_place(name='Synthetic tariff format')
                PricingPlan.objects.create(place=place, product_type='lesson', lesson_format=lesson_format, price_kind='exact', price=80)
                with override('en'):
                    response = self.client.get(place.get_absolute_url())
                badges = re.findall(r'<span class="detail-plans__badge">(.*?)</span>', response.content.decode(), re.S)
                self.assertEqual([badge.strip() for badge in badges], [label])

    def test_free_guide_includes_all_four_legacy_zero_price_venues(self):
        places = [create_quality_place(name=f'Zero price venue {i}', category='parks-playgrounds',
                  price_from=0, price_to=0) for i in range(4)]
        eligible = {p.pk for p in places}
        for prefix in ('/ru', '/en', ''):
            response = self.client.get(prefix + '/parents/baku-with-kids/')
            answer = next(item for item in response.context['guide_faq'] if item.get('key') == 'free')
            shown = {p['id'] for p in answer['places']}
            self.assertEqual(len(shown), 3)
            self.assertTrue(shown <= eligible)
            self.assertEqual({p['id'] for p in response.context['guide_places']}, eligible)

    def test_free_guide_uses_active_primary_tariffs_and_never_missing_prices(self):
        free = create_quality_place(name='Free primary museum', category='museums-culture')
        PricingPlan.objects.create(place=free, product_type='admission', price_kind='free')
        trial = create_quality_place(name='Trial only museum', category='museums-culture')
        PricingPlan.objects.create(place=trial, product_type='lesson', price_kind='free', is_trial=True)
        unknown = create_quality_place(name='Unknown price museum', category='museums-culture', price_from=None, price_to=None)
        inactive = create_quality_place(name='Inactive free price', category='museums-culture')
        PricingPlan.objects.create(place=inactive, product_type='admission', price_kind='free', is_active=False)
        mixed = create_quality_place(name='Mixed prices', category='museums-culture')
        PricingPlan.objects.create(place=mixed, product_type='admission', price_kind='free')
        PricingPlan.objects.create(place=mixed, product_type='admission', price_kind='exact', price=10)
        self.assert_free_places({free.pk})

    def test_free_guide_preserves_visibility_location_and_category(self):
        eligible = create_quality_place(name='Eligible free park', category='parks-playgrounds', price_mode='free')
        create_quality_place(name='Private free park', category='parks-playgrounds', price_mode='free', status=Place.STATUS_DRAFT)
        other_town = create_quality_place(name='Other town free park', category='parks-playgrounds', price_mode='free')
        # Historical stored location; this test exercises filtering, not coordinate assignment.
        Place.objects.filter(pk=other_town.pk).update(district='sumgait')
        create_quality_place(name='Free sport', category='SPRT', price_mode='free')
        create_quality_place(name='Paid services park', category='parks-playgrounds', price_mode='free_entry_paid_services')
        self.assert_free_places({eligible.pk})

    def assert_free_places(self, expected):
        for prefix in ('/ru', '/en', ''):
            with self.subTest(prefix=prefix):
                response = self.client.get(prefix + '/parents/baku-with-kids/')
                answer = next(item for item in response.context['guide_faq'] if item.get('key') == 'free')
                self.assertEqual({p['id'] for p in answer['places']}, expected)
                if expected:
                    self.assertNotContains(response, answer['empty_text'])

    def test_server_carousel_contains_each_card_once(self):
        places = [create_quality_place(name=f'Rail fixture {i}', is_home_recommended=True) for i in range(4)]
        response = self.client.get('/ru/')
        rail = response.content.decode().split('data-rail-track', 1)[1].split('</ul>', 1)[0]
        ids = re.findall(r'data-place-id="(\d+)"', rail)
        self.assertEqual(len(ids), 4)
        self.assertEqual(set(ids), {str(p.pk) for p in places})
        self.assertNotIn('data-rail-copy', rail)


class PlaceDetailCleanupTests(TestCase):
    def test_manat_has_a_screen_reader_code_and_keeps_the_offer_currency(self):
        place = create_quality_place(with_pricing_plan=True)
        for lang in ('az', 'ru', 'en'):
            with self.subTest(lang=lang), override(lang):
                response = self.client.get(place.get_absolute_url())
                offer = json.loads(response.context['place_schema_json'])['offers']
                self.assertEqual(offer['priceCurrency'], 'AZN')
                html = response.content.decode()
                for prefix in ('detail-decision__price-value', 'detail-plans__price'):
                    field = html.split(f'class="{prefix}">', 1)[1]
                    self.assertRegex(field, r'^80 <span aria-hidden="true">₼</span><span class="visually-hidden">AZN</span>')

    def test_uniform_week_collapses_only_identical_open_days(self):
        from catalog.templatetags.place_detail_extras import uniform_week
        same = [{'lines': ['10:00–22:30'], 'is_closed': False} for _ in range(7)]
        self.assertEqual(uniform_week(same), '10:00–22:30')
        self.assertEqual(uniform_week(same[:6] + [{'lines': ['10:00–18:00'], 'is_closed': False}]), '')
        self.assertEqual(uniform_week(same[:6] + [{'lines': [], 'is_closed': True}]), '')
        self.assertEqual(uniform_week([]), '')
