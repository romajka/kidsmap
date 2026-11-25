"""List location and thumbnail must reflect the revision an editor can open."""
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

from catalog.models import Category, Organization, Place, VolunteerPlaceRevision


class AdminSavedLocationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser('location-editor', '', 'fictional')
        cls.viewer = get_user_model().objects.create_user('location-viewer', is_staff=True)
        cls.viewer.user_permissions.add(Permission.objects.get(codename='view_place'))
        category = Category.objects.create(code='QA_LOCATION', name_az='Location fixture')
        cls.place = Place(name='Coordinate fixture', name_az='Coordinate fixture',
                          category=category, status='draft', is_active=False)
        Place.objects.bulk_create([cls.place])
        cls.revision = VolunteerPlaceRevision.objects.create(place=cls.place, author=cls.staff,
            status='draft', payload={'lat': '40.4', 'lng': '49.8', 'address': 'Saved Avenue 123'})

    def listing(self, value=None, *, user=None):
        self.client.force_login(user or self.staff)
        return self.client.get(reverse('admin:catalog_place_changelist'),
                               {'coordinates_status': value} if value else {})

    def row(self, response):
        return next(obj for obj in response.context['cl'].result_list if obj.pk == self.place.pk)

    def test_saved_coordinates_excluded_from_missing_tab_and_count(self):
        response = self.listing('no')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.place.pk, [p.pk for p in response.context['cl'].result_list])
        self.assertContains(response, 'Coordinate fixture', count=0)
        counts = admin.site._registry[Place]._place_dashboard_counts(response.wsgi_request)
        self.assertEqual(counts['quick_without_coordinates'], 0)
        self.assertEqual(counts['stat_without_coordinates'], 0)

    def test_row_displays_saved_address_and_coordinate_status(self):
        response = self.listing('yes')
        obj = self.row(response)
        model_admin = admin.site._registry[Place]
        self.assertIn('Saved Avenue 123', model_admin.col_location(obj))
        self.assertNotIn('нет координат', model_admin.col_location(obj))
        self.assertIn('Есть координаты', str(model_admin.coordinates_status(obj)))

    def test_each_active_revision_status_uses_saved_location(self):
        for status in ('draft', 'pending', 'rejected'):
            VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(status=status)
            with self.subTest(status=status):
                self.assertEqual(self.row(self.listing('yes')).pk, self.place.pk)

    def test_approved_revision_no_longer_overlays_live_location(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(status='approved')
        self.assertEqual(self.row(self.listing('no')).pk, self.place.pk)
        self.assertNotContains(self.listing(), 'Saved Avenue 123')

    def test_explicit_clear_and_partial_coordinate_do_not_fall_back(self):
        Place.objects.filter(pk=self.place.pk).update(lat=40, lng=49, address='Live address')
        for value in (None, ''):
            VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(
                payload={'lat': value, 'address': ''})
            with self.subTest(value=value):
                request = RequestFactory().get('/admin/catalog/place/')
                request.user = self.staff
                model_admin = admin.site._registry[Place]
                obj = model_admin.get_queryset(request).get(pk=self.place.pk)
                self.assertFalse(obj.km_saved_has_coordinates)
                self.assertNotIn('Live address', model_admin.col_location(obj))

    def test_absent_key_falls_back_and_zero_is_a_coordinate(self):
        Place.objects.filter(pk=self.place.pk).update(lng=0)
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={'lat': 0})
        self.assertEqual(self.row(self.listing('yes')).pk, self.place.pk)

    def test_viewer_and_revoked_actor_cannot_read_saved_fields(self):
        response = self.listing('no', user=self.viewer)
        self.assertEqual(self.row(response).pk, self.place.pk)
        self.assertNotContains(response, 'Saved Avenue 123')
        request = RequestFactory().get('/admin/catalog/place/')
        request.user = self.staff
        get_user_model().objects.filter(pk=self.staff.pk).update(is_active=False)
        obj = admin.site._registry[Place].get_queryset(request).get(pk=self.place.pk)
        self.assertNotIn('Saved Avenue 123', admin.site._registry[Place].col_location(obj))

    def test_object_permission_denial_does_not_reveal_candidate(self):
        model_admin = admin.site._registry[Place]
        original = model_admin.has_change_permission
        def permission(request, obj=None):
            return False if obj is not None else original(request)
        with patch.object(model_admin, 'has_change_permission', side_effect=permission):
            response = self.listing('no')
        self.assertEqual(self.row(response).pk, self.place.pk)
        self.assertNotContains(response, 'Saved Avenue 123')

    def test_saved_photo_is_used_without_publication_or_live_mutation(self):
        field = Place._meta.get_field('photo')
        name = field.storage.save('qa-location/candidate.gif', ContentFile(
            b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'))
        self.addCleanup(field.storage.delete, name)
        payload = dict(self.revision.payload, photo=name)
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload=payload)
        response = self.listing()
        self.assertIn(field.storage.url(name), admin.site._registry[Place].col_place(self.row(response)))
        self.assertNotContains(self.listing(user=self.viewer), field.storage.url(name))
        live = Place.objects.get(pk=self.place.pk)
        self.assertEqual((live.lat, live.lng, live.address, bool(live.photo), live.status, live.is_active),
                         (None, None, '', False, 'draft', False))
        self.assertEqual(VolunteerPlaceRevision.objects.get(pk=self.revision.pk).version, 1)

    def test_saved_gallery_can_supply_thumbnail_when_no_main_photo(self):
        field = Place._meta.get_field('photo')
        name = field.storage.save('qa-location/gallery.gif', ContentFile(b'GIF89a'))
        self.addCleanup(field.storage.delete, name)
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={
            **self.revision.payload, 'gallery': [{'id': None, 'image': name, 'order': 0, 'caption': ''}]})
        response = self.listing()
        self.assertIn(field.storage.url(name), admin.site._registry[Place].col_place(self.row(response)))

    def test_draft_coordinates_do_not_make_place_publicly_map_ready(self):
        response = self.listing('yes')
        self.assertFalse(self.row(response).is_map_ready)

    def test_map_mark_and_publish_menu_use_saved_coordinate_presence(self):
        obj = self.row(self.listing())
        model_admin = admin.site._registry[Place]
        self.assertIn('Точка на карте есть', model_admin.col_marks(obj))
        self.assertIn('data-has-coords="1"', model_admin.col_actions(obj))

    def test_cleared_candidate_photos_do_not_resurrect_live_cover(self):
        field = Place._meta.get_field('photo')
        name = field.storage.save('qa-location/obsolete.gif', ContentFile(b'GIF89a'))
        self.addCleanup(field.storage.delete, name)
        Place.objects.filter(pk=self.place.pk).update(photo=name, cover_photo=name)
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={
            **self.revision.payload, 'photo': '', 'cover_photo': '', 'gallery': []})
        response = self.listing()
        self.assertNotIn(field.storage.url(name), admin.site._registry[Place].col_place(self.row(response)))

    def test_missing_candidate_image_uses_existing_saved_cover(self):
        field = Place._meta.get_field('photo')
        name = field.storage.save('qa-location/fallback.gif', ContentFile(b'GIF89a'))
        self.addCleanup(field.storage.delete, name)
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={
            **self.revision.payload, 'photo': 'qa-location/missing-file.gif', 'cover_photo': name})
        response = self.listing()
        self.assertIn(field.storage.url(name), admin.site._registry[Place].col_place(self.row(response)))

    def test_viewer_counts_and_filters_use_only_visible_live_values(self):
        response = self.listing('no', user=self.viewer)
        counts = admin.site._registry[Place]._place_dashboard_counts(response.wsgi_request)
        self.assertEqual(counts['quick_without_coordinates'], 1)
        self.assertEqual(counts['stat_without_coordinates'], 1)
        self.assertEqual(self.row(response).pk, self.place.pk)

    def test_other_entity_revision_does_not_break_the_admin_list(self):
        organization = Organization.objects.create(name_az='Private organization', owner=self.staff)
        VolunteerPlaceRevision.objects.create(organization=organization, author=self.staff,
            status='draft', payload={'address': 'Detached private address', 'lat': 40, 'lng': 49})
        response = self.listing()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Detached private address')

    def test_control_card_coordinate_badge_uses_saved_point(self):
        response = self.listing('yes')
        card = next(c for c in response.context['cl'].place_cards if c['pk'] == self.place.pk)
        self.assertTrue(card['has_coordinates'])
        self.assertEqual(card['has_coords_num'], 1)
        self.assertNotContains(response, 'km-card-coords-warn')

    def test_control_card_coordinate_badge_respects_explicit_clear(self):
        Place.objects.filter(pk=self.place.pk).update(lat=40, lng=49)
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={'lat': None})
        response = self.listing()
        card = next(c for c in response.context['cl'].place_cards if c['pk'] == self.place.pk)
        self.assertFalse(card['has_coordinates'])
        self.assertEqual(card['has_coords_num'], 0)
        self.assertContains(response, 'km-card-coords-warn')

    def test_explicit_null_point_is_in_missing_filter_and_not_present_filter(self):
        Place.objects.filter(pk=self.place.pk).update(lat=40, lng=49)
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={'lat': None})
        missing = self.listing('no')
        present = self.listing('yes')
        self.assertIn(self.place.pk, [p.pk for p in missing.context['cl'].result_list])
        self.assertNotIn(self.place.pk, [p.pk for p in present.context['cl'].result_list])
