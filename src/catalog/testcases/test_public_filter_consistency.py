from types import SimpleNamespace

from django.test import TestCase, SimpleTestCase

from catalog.controllers.home_controller import HomeController
from catalog.models import Category, Place
from catalog.services.filtering import PlaceListFilters


class HomeDistrictFilterTests(SimpleTestCase):
    def test_missing_district_is_not_guessed_from_a_bounding_rectangle_or_address(self):
        for address in ('Baku road', 'Баку', ''):
            with self.subTest(address=address):
                place = SimpleNamespace(district='', lat=40.589, lng=49.668, address=address)
                self.assertEqual(HomeController._resolve_place_district_info(place, 'ru'), ('', ''))

    def test_known_city_takes_priority_over_coordinates_and_address(self):
        place = SimpleNamespace(district='sumgait', lat=40.589, lng=49.668, address='Baku road',
                                district_i18n=lambda lang: 'Сумгаит')
        self.assertEqual(HomeController._resolve_place_district_info(place, 'ru')[0], 'sumgait')


class CatalogAgeFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category, _ = Category.objects.get_or_create(code='TECH', defaults={'name': 'Technology'})
        for name, low, high in [('unknown', None, None), ('six_to_twelve', 6, 12),
                                ('eight_to_twelve', 8, 12), ('up_to_twelve', None, 12),
                                ('from_six', 6, None)]:
            place = Place.objects.create(name=name, category=cls.category, district='baku_yasamal',
                                         age_from=low, age_to=high)
            # Stage19: Place-only suitability is confirmed general admission.
            # Unmapped legacy lessons are covered separately by ExactSearchTests.
            from django.utils import timezone
            Place.objects.filter(pk=place.pk).update(nature='public_space',nature_approved_at=timezone.now())

    def names(self, **filters):
        return set(PlaceListFilters(**filters).apply(Place.objects.all()).values_list('name', flat=True))

    def test_exact_age_excludes_unknown_and_higher_minimum(self):
        self.assertEqual(self.names(age='6'), {'six_to_twelve', 'up_to_twelve', 'from_six'})

    def test_age_range_excludes_unknown_but_accepts_open_bounds(self):
        self.assertEqual(self.names(age_from='8', age_to='12'),
                         {'six_to_twelve', 'eight_to_twelve', 'up_to_twelve', 'from_six'})

    def test_no_age_filter_keeps_unknown(self):
        self.assertIn('unknown', self.names())

    def test_zero_is_a_real_age_and_one_sided_range_excludes_unknown(self):
        self.assertEqual(self.names(age='0'), {'up_to_twelve'})
        self.assertNotIn('unknown', self.names(age_from='6'))
        self.assertNotIn('unknown', self.names(age_to='12'))

    def test_filters_are_combined(self):
        self.assertEqual(self.names(category='TECH', district='baku_yasamal', age='6'),
                         {'six_to_twelve', 'up_to_twelve', 'from_six'})
        self.assertEqual(self.names(district='sumgait', age='6'), set())

    def test_selected_age_keeps_exact_bounds(self):
        selected = PlaceListFilters(age='6').selected()
        self.assertEqual((selected['age_from'], selected['age_to']), ('6', '6'))


class CatalogEventAgeFilterTests(TestCase):
    def test_age_filter_excludes_events_with_unknown_age(self):
        from datetime import timedelta
        from unittest.mock import patch
        from django.utils import timezone
        from catalog.controllers.place_controller import PlaceController
        from catalog.models import Event

        category, _ = Category.objects.get_or_create(code='TECH', defaults={'name': 'Technology'})
        now = timezone.now()
        for name, low, high in [('unknown', None, None), ('suitable', 6, 12), ('open', None, 12)]:
            Event.objects.create(name=name, category=category, age_from=low, age_to=high, status=Event.STATUS_PUBLISHED,
                                 start_datetime=now + timedelta(hours=1), end_datetime=now + timedelta(hours=2))
        controller = PlaceController.build_default()
        with patch('catalog.controllers.place_controller.is_events_section_enabled', return_value=True):
            filtered = controller._filtered_event_queryset(age_from='6', age_to='6')
            self.assertEqual(set(filtered.values_list('name', flat=True)), {'suitable', 'open'})
            unfiltered = controller._filtered_event_queryset()
            self.assertIn('unknown', unfiltered.values_list('name', flat=True))


class DistrictOptionCountsTests(TestCase):
    def test_baku_count_does_not_guess_missing_district_from_coordinates(self):
        from catalog.services.public_filter_options import build_public_place_filter_options
        from catalog.testcases.utils import create_quality_place

        known = create_quality_place(name='Known district')
        unknown = create_quality_place(name='Unknown district')
        other = create_quality_place(name='Other city')
        # Model save resolves coordinates; emulate stored legacy rows explicitly.
        Place.objects.filter(pk=known.pk).update(district='baku_yasamal')
        Place.objects.filter(pk=unknown.pk).update(district='', lat=40.589, lng=49.668, address='Baku road')
        Place.objects.filter(pk=other.pk).update(district='sumgait', lat=40.589, lng=49.668)
        options = build_public_place_filter_options(language_code='ru')
        baku = next(item for item in options.districts if item['value'] == 'baku')
        self.assertEqual(baku['count'], 1)
