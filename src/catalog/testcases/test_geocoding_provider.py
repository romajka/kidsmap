import json
from io import BytesIO
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.test import SimpleTestCase, override_settings

from catalog.services.geocoding import PlaceGeocodingService


OLD_CITY = (40.366667, 49.833333)
CITY_CENTER = (40.409264, 49.867092)


def candidate(point=OLD_CITY, types=('street_address',), precision='ROOFTOP', **fields):
    return {
        'formatted_address': 'İçərişəhər, Bakı',
        'types': list(types),
        'geometry': {'location': dict(zip(('lat', 'lng'), point)), 'location_type': precision},
        **fields,
    }


@override_settings(GOOGLE_MAPS_API_KEY='offline-test')
class GoogleGeocodingTests(SimpleTestCase):
    def lookup(self, response, **fields):
        urlopen = 'catalog.repositories.geocoding_repositories.urlopen'
        if isinstance(response, Exception):
            transport = patch(urlopen, side_effect=response)
        else:
            data = response if isinstance(response, bytes) else json.dumps(response).encode()
            transport = patch(urlopen, return_value=BytesIO(data))
        with transport as request:
            result = PlaceGeocodingService.build_default().geocode_location(
                address='ичери шяхяр', **fields)
            params = parse_qs(urlsplit(request.call_args.args[0]).query)
            self.assertEqual(params['components'], ['country:AZ'])
        return result

    def matches(self, *results, **fields):
        return self.lookup({'status': 'OK', 'results': results}, **fields)

    def test_selects_only_precise_result_in_either_order(self):
        broad = candidate(CITY_CENTER, ('locality', 'political'), 'APPROXIMATE', partial_match=True)
        for results in ((broad, candidate()), (candidate(), broad)):
            with self.subTest(results=results):
                result = self.matches(*results)
                self.assertEqual(result.reason, 'resolved')
                self.assertEqual((result.point.lat, result.point.lng), OLD_CITY)

    def test_partial_area_route_station_or_interpolated_house_require_confirmation(self):
        for item in (
            candidate(partial_match=True),
            candidate(types=('neighborhood', 'political'), precision='GEOMETRIC_CENTER'),
            candidate(types=('route',), precision='GEOMETRIC_CENTER'),
            candidate(types=('subway_station', 'establishment', 'point_of_interest')),
            candidate(precision='RANGE_INTERPOLATED'),
            candidate(types=('locality', 'political')),
            candidate(precision='APPROXIMATE'),
        ):
            with self.subTest(item=item):
                self.assertEqual(self.matches(item).reason, 'ambiguous')

    def test_distinct_precise_points_are_ambiguous_but_same_point_is_unique(self):
        self.assertEqual(self.matches(candidate(), candidate(CITY_CENTER)).reason, 'ambiguous')
        same = candidate(types=('establishment', 'point_of_interest'), precision='GEOMETRIC_CENTER')
        self.assertEqual(self.matches(candidate(), same).reason, 'resolved')

    def test_malformed_candidates_cannot_hide_a_later_valid_point(self):
        for item in (None, [], {'geometry': {}}, candidate(('bad', 49)), candidate((91, 181)),
                     candidate((float('nan'), 49)), candidate((True, 49))):
            with self.subTest(item=item):
                self.assertEqual(self.matches(item).reason, 'provider_error')
                result = self.matches(item, candidate())
                self.assertEqual(result.reason, 'resolved')
                self.assertEqual((result.point.lat, result.point.lng), OLD_CITY)

    def test_swapped_or_foreign_points_do_not_resolve(self):
        foreign = candidate(address_components=[{'types': ['country'], 'short_name': 'US'}])
        for item in (candidate(OLD_CITY[::-1]), foreign):
            with self.subTest(item=item):
                self.assertEqual(self.matches(item).reason, 'location_unresolved')
                self.assertEqual(self.matches(item, candidate()).reason, 'resolved')

    def test_empty_response_and_provider_problems_have_distinct_reasons(self):
        self.assertEqual(self.lookup({'status': 'ZERO_RESULTS'}).reason, 'not_found')
        self.assertEqual(self.matches().reason, 'not_found')
        for response in (TimeoutError(), b'{', None, [], {'status': 'REQUEST_DENIED'},
                         {'status': 'OVER_QUERY_LIMIT'}, {'status': 'OK', 'results': {}}):
            with self.subTest(response=response):
                self.assertEqual(self.lookup(response).reason, 'provider_error')

    def test_query_uses_current_address_with_city_context_only(self):
        query = self.matches(candidate(), district='baku_narimanov', metro='narimanov').query
        self.assertEqual(query, 'ичери шяхяр, Баку, Азербайджан')
        service = PlaceGeocodingService.build_default()
        self.assertEqual(service.build_query_from_location(address='ул. 1', district='ganja'),
                         'ул. 1, Гянджа, Азербайджан')
