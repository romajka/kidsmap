"""A public detail page recommends places using the same points as the map."""
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import override

from catalog.controllers.place_controller import PlaceController
from catalog.models import Location, Place
from catalog.services.catalog_structure import bind_confirmed_location
from catalog.testcases.utils import create_quality_place


class NearbyPlacesTests(TestCase):
    def place(self, name, lat=40.41, lng=49.87, **fields):
        return create_quality_place(name=name, name_az=name, lat=lat, lng=lng, **fields)

    def confirm_venue(self, place, lat=None, lng=None):
        venue = Location.objects.create(address='Campus entrance', lat=lat, lng=lng, confirmed_at=timezone.now())
        bind_confirmed_location(place.pk, venue.pk, expected_content_version=place.content_version)
        place.refresh_from_db()
        return venue

    def nearby(self, origin):
        response = self.client.get(origin.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        return [(place.pk, place.nearby_km) for place in response.context['nearby_places']]

    def test_neighbour_beyond_first_two_thousand_public_records(self):
        origin = self.place('Library')
        closest = self.place('Play room', lat=40.4105)
        # These newer cards have identical scores and are hundreds of km away.
        remote = Place.objects.bulk_create([
            Place(slug=f'western-hall-{i}', name='Western hall', name_az='Western hall',
                  description_az='Ailə dərnəyi', category_id='EDU', website='https://example.invalid',
                  address='Gəncə', lat=40.68, lng=46.36, schedule='Saturday', price_from=20,
                  status='published', is_active=True)
            for i in range(2000)
        ], batch_size=50)
        picked = PlaceController._nearby_places(origin, 'en', {closest.pk})
        self.assertEqual([place.pk for place in picked], [closest.pk, *(other.pk for other in remote[:5])])
        self.assertEqual(picked[0].nearby_km, 0.1)
        self.assertTrue(picked[0].is_liked)

    def test_distance_uses_confirmed_origin(self):
        origin = self.place('Shared campus')
        old_neighbour = self.place('Old neighbour', lat=40.4101)
        new_neighbour = self.place('New neighbour', lat=40.42001, lng=49.88)
        self.confirm_venue(origin, 40.42, 49.88)
        self.assertEqual(self.nearby(origin), [(new_neighbour.pk, 0.0), (old_neighbour.pk, 1.4)])

    def test_confirmed_candidates_replace_missing_or_stale_place_points(self):
        origin = self.place('Library')
        by_venue = self.place('Court', lat=None, lng=None)
        self.confirm_venue(by_venue, 40.4101, 49.87)
        address_only = self.place('Sports hall')
        self.confirm_venue(address_only)
        self.assertEqual(self.nearby(origin), [(by_venue.pk, 0.0)])

    def test_address_only_origin_falls_back_to_category_without_distances(self):
        origin = self.place('Shared campus')
        self.confirm_venue(origin)
        earlier = self.place('Community room', lat=None, lng=None)
        later = self.place('Children’s centre')
        self.place('Concert hall', category='ART')
        self.assertEqual(self.nearby(origin), [(later.pk, None), (earlier.pk, None)])
        for language, title in (('az', 'Eyni kateqoriyadan digər məkanlar'),
                                ('ru', 'Другие места той же категории'),
                                ('en', 'Other places in this category')):
            with self.subTest(language=language), override(language):
                response = self.client.get(origin.get_absolute_url())
                self.assertContains(response, title)
                self.assertNotContains(response, 'class="detail-nearby__distance"')

    def test_archived_venue_falls_back_to_place_coordinates(self):
        origin = self.place('Library')
        neighbour = self.place('Dance hall', lat=40.4101)
        venue = self.confirm_venue(neighbour, 40.42, 49.88)
        Location.objects.filter(pk=venue.pk).update(archived_at=timezone.now())
        self.assertEqual(self.nearby(origin), [(neighbour.pk, 0.0)])

    def test_only_public_places_with_map_points_get_a_distance(self):
        origin = self.place('Local centre')
        same_category = self.place('Community centre', lat=40.419)
        other_category = self.place('Studio', lat=40.411, category='ART')
        self.place('Archived listing', deleted_at=timezone.now())
        self.place('Pending listing', status='pending', is_active=False)
        self.place('Unknown location', lat=None, lng=None)
        invalid = self.place('Unmapped site')
        Place.objects.filter(pk=invalid.pk).update(lat=0, lng=0)
        response = self.client.get(origin.get_absolute_url())
        picked = response.context['nearby_places']
        self.assertEqual([(place.pk, place.nearby_km) for place in picked],
                         [(same_category.pk, 1.0), (other_category.pk, 0.1)])
        for place in picked:
            self.assertContains(response, f'href="{place.get_absolute_url()}"')
            self.assertEqual(self.client.get(place.get_absolute_url()).status_code, 200)
