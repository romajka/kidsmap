"""Stage20 real shared venue/filter/edit contracts on disposable fixtures."""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.utils import timezone
from catalog.models import Place, Location, Event
from catalog.controllers.place_controller import PlaceController
from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services.filtering import PlaceListFilters
from catalog.services.catalog_structure import bind_confirmed_location
from catalog.testcases import test_task33_search
from catalog.testcases.utils import create_quality_place


class MapContractsTests(TestCase):
    def setUp(self):
        self.a=create_quality_place(name_az='Independent A',lat=40.41,lng=49.87)
        self.b=create_quality_place(name_az='Independent B',lat=40.410001,lng=49.870001)
        self.venue=Location.objects.create(address='Verified shared address',lat=Decimal('40.42'),lng=Decimal('49.88'),confirmed_at=timezone.now())
        for p in (self.a,self.b):
            bind_confirmed_location(p.pk,self.venue.pk,expected_content_version=p.content_version)
            p.refresh_from_db()

    def payload(self,**params):
        filters=PlaceListFilters.from_request(RequestFactory().get('/places/',params))
        qs=filters.apply(DjangoPlaceRepository().active_queryset())
        return PlaceController.build_default()._serialize_map_places(DjangoPlaceRepository().map_ready_queryset(qs),language_code='en',filters=filters)

    def test_verified_venue_one_point_two_independent_cards(self):
        data=self.payload()
        self.assertEqual(len(data),1)
        self.assertEqual({m['id'] for m in data[0]['members']},{self.a.pk,self.b.pk})
        self.assertEqual((data[0]['lat'],data[0]['lng']),(40.42,49.88))
        self.assertEqual(len({m['url'] for m in data[0]['members']}),2)

    def test_nearby_or_identical_coordinates_do_not_assert_shared_identity(self):
        Place.objects.filter(pk__in=[self.a.pk,self.b.pk]).update(confirmed_location=None,venue_confirmed_at=None,lat=40.41,lng=49.87)
        self.assertEqual(len(self.payload()),2)

    def test_venue_only_coordinates_and_no_fake_missing_points(self):
        Place.objects.filter(pk=self.a.pk).update(lat=None,lng=None)
        missing=create_quality_place(name_az='No map',lat=None,lng=None)
        self.assertEqual({m['id'] for p in self.payload() for m in p['members']},{self.a.pk,self.b.pk})
        self.assertIn(missing.pk,DjangoPlaceRepository().active_queryset().values_list('pk',flat=True))

    def test_invalid_coordinates_rejected(self):
        Place.objects.filter(pk__in=[self.a.pk,self.b.pk]).update(confirmed_location=None,venue_confirmed_at=None,lat=0,lng=0)
        self.assertEqual(self.payload(),[])
        Place.objects.filter(pk=self.a.pk).update(lat=91,lng=49)
        self.assertEqual(self.payload(),[])

    def test_filtered_members_and_matched_prices(self):
        fixture=test_task33_search.ExactSearchTests();fixture.offer(self.a,'Younger',self.a.category_id,4,6,'25');fixture.offer(self.a,'Older',self.a.category_id,8,12,'120');fixture.offer(self.b,'Other business older',self.b.category_id,8,12,'90')
        data=self.payload(age='5')
        self.assertEqual(len(data),1)
        member=data[0]['members'][0]
        self.assertEqual(member['id'],self.a.pk)
        self.assertEqual(len(data[0]['members']),1)
        self.assertNotIn('120',member['price'])
        self.assertIn('25',member['price'])
        self.assertEqual(len(member['matched_offers']),1)

    def test_archived_venue_not_used(self):
        Location.objects.filter(pk=self.venue.pk).update(archived_at=timezone.now())
        self.assertEqual(len(self.payload()),2)
        self.assertEqual({p['key'] for p in self.payload()},{f'place:{self.a.pk}',f'place:{self.b.pk}'})

    def test_address_edit_detaches_only_changed_place_and_preserves_event(self):
        event=Event.objects.create(name_az='Historical snapshot',name='Historical snapshot',category=self.a.category,related_place=self.a,address='Past address',start_datetime=timezone.now())
        self.a.address='Different address';self.a.save(update_fields=['address']);self.a.refresh_from_db();self.b.refresh_from_db();self.venue.refresh_from_db();event.refresh_from_db()
        self.assertIsNone(self.a.confirmed_location_id)
        self.assertEqual(self.b.confirmed_location_id,self.venue.pk)
        self.assertEqual(self.venue.address,'Verified shared address')
        self.assertEqual(event.address,'Past address')

    def test_map_missing_count_counts_members_not_venues(self):
        create_quality_place(name_az='No coordinates',lat=None,lng=None)
        request=RequestFactory().get('/places/')
        from django.contrib.auth.models import AnonymousUser
        request.user=AnonymousUser()
        request.session={}
        context=PlaceController.build_default().build_list_context(request)
        self.assertEqual(context['catalog_map_missing_count'],1)
        self.assertEqual(context['catalog_map_places_count'],2)

    def test_route_transport_contains_no_private_contact(self):
        Place.objects.filter(pk=self.a.pk).update(phone1='+994500001234')
        import json
        self.assertNotIn('+994500001234',json.dumps(self.payload()))

    def test_address_only_confirmed_venue_does_not_borrow_business_coordinates(self):
        Location.objects.filter(pk=self.venue.pk).update(lat=None,lng=None)
        self.assertEqual(self.payload(),[])

    def test_unchanged_address_partial_content_edit_keeps_shared_venue(self):
        self.a.description_az='Updated text';self.a.save(update_fields=['description_az']);self.a.refresh_from_db()
        self.assertEqual(self.a.confirmed_location_id,self.venue.pk)
        self.a.address=self.a.address;self.a.save(update_fields=['address']);self.a.refresh_from_db()
        self.assertEqual(self.a.confirmed_location_id,self.venue.pk)

    def test_coordinate_edit_detaches_only_edited_place(self):
        self.a.lat=40.4093;self.a.save(update_fields=['lat']);self.a.refresh_from_db();self.b.refresh_from_db()
        self.assertIsNone(self.a.confirmed_location_id)
        self.assertEqual(self.b.confirmed_location_id,self.venue.pk)

    def test_pending_address_keeps_venue_approved_address_detaches_only_target(self):
        from django.contrib.auth import get_user_model
        from catalog.services import publication
        owner=get_user_model().objects.create_user(username='map_owner')
        staff=get_user_model().objects.create_superuser(username='map_staff',email='map@example.invalid')
        Place.objects.filter(pk=self.a.pk).update(owner=owner,created_by=owner)
        self.a.refresh_from_db()
        revision=publication.propose(actor=owner,target_type='place',target_id=self.a.pk,
            patch={'address':'New approved address'},schema_version=1,expected_version=self.a.content_version,
            revision_version=0,submit=True,explicit_save=True)
        self.a.refresh_from_db();self.assertEqual(self.a.confirmed_location_id,self.venue.pk)
        publication.review(actor=staff,revision_id=revision.pk,version=revision.version,approve=True)
        self.a.refresh_from_db();self.b.refresh_from_db()
        self.assertIsNone(self.a.confirmed_location_id)
        self.assertEqual(self.b.confirmed_location_id,self.venue.pk)

    def test_no_coordinates_remains_visible_with_clear_card_marker(self):
        missing=create_quality_place(name_az='Visible missing marker',lat=None,lng=None)
        response=self.client.get('/en/catalog/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Visible missing marker')
        self.assertContains(response,'Location not marked on map')
