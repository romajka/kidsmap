from unittest.mock import patch

from django.test import SimpleTestCase
from catalog.services import district_geometry as geometry


def square(key, left, right, holes=()):
    return {'type': 'Feature', 'properties': {'district': key}, 'geometry': {
        'type': 'Polygon', 'coordinates': [
            [[left, 0], [right, 0], [right, 2], [left, 2], [left, 0]], *holes]}}


class LocationResolutionTests(SimpleTestCase):
    def test_real_baku_interior_has_city_and_district(self):
        self.assertTrue(callable(getattr(geometry, 'resolve_location', None)), 'Missing coordinate resolver')
        result = geometry.resolve_location(40.4093, 49.8671)
        self.assertEqual((result.status, result.city_key, result.district_key),
                         ('resolved', 'baku', 'baku_narimanov'))
        self.assertTrue(result.dataset_version)

    def resolve(self, lat, lng, features):
        self.assertTrue(callable(getattr(geometry, 'resolve_location', None)), 'Missing coordinate resolver')
        with patch.object(geometry, '_features', return_value=features):
            return geometry.resolve_location(lat, lng)

    def test_shared_edge_and_vertex_never_choose_first_feature(self):
        polygons = [square('baku_sabail', 0, 1), square('baku_yasamal', 1, 2)]
        for features in (polygons, polygons[::-1]):
            for point in ((1, 1), (0, 1)):
                result = self.resolve(*point, features)
                self.assertEqual(result.status, 'ambiguous')
                self.assertEqual(result.district_key, '')

    def test_overlap_is_ambiguous(self):
        result = self.resolve(1, 1.5, [square('baku_sabail', 0, 2), square('baku_yasamal', 1, 3)])
        self.assertEqual(result.status, 'ambiguous')

    def test_hole_and_multipolygon_island(self):
        hole = [[.5, .5], [1.5, .5], [1.5, 1.5], [.5, 1.5], [.5, .5]]
        feature = square('baku_sabail', 0, 2, [hole])
        self.assertEqual(self.resolve(1, 1, [feature]).status, 'outside_coverage')
        self.assertEqual(self.resolve(1, .5, [feature]).status, 'ambiguous')
        feature['geometry'] = {'type': 'MultiPolygon', 'coordinates': [feature['geometry']['coordinates'], square('x', 3, 4)['geometry']['coordinates']]}
        self.assertEqual(self.resolve(1, 3.5, [feature]).district_key, 'baku_sabail')

    def test_invalid_and_uncovered_coordinates(self):
        for lat, lng in [(None, None), ('', ''), (float('nan'), 49), (40, float('inf')), (91, 49), (40, 181), ('bad', 49)]:
            self.assertEqual(self.resolve(lat, lng, []).status, 'invalid_coordinates')
        self.assertEqual(self.resolve(0, 0, []).status, 'outside_coverage')

    def test_unavailable_dataset_is_explicit(self):
        self.assertTrue(callable(getattr(geometry, 'resolve_location', None)), 'Missing coordinate resolver')
        with patch.object(geometry, '_features', side_effect=OSError('missing')):
            self.assertEqual(geometry.resolve_location(40, 49).status, 'unavailable')
