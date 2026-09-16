from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Category, Place
from catalog.services.locations import clean_location_fields, configure_location_choices


class LocationForm(forms.ModelForm):
    region = forms.ChoiceField(required=False)
    district = forms.ChoiceField(required=False)
    class Meta:
        model = Place
        fields = ('region', 'district', 'lat', 'lng')
    def __init__(self, *args, **kwargs):
        self.draft_save_only = kwargs.pop('draft', True)
        super().__init__(*args, **kwargs)
        configure_location_choices(self)
    def clean(self):
        return clean_location_fields(self, super().clean())


class LocationAssignmentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category, _ = Category.objects.get_or_create(code='EDU', defaults={'name': 'Education'})

    def place(self, **kw):
        values = dict(name='Location fixture', category=self.category, status='draft', is_active=False,
                      lat=40.4093, lng=49.8671)
        values.update(kw)
        return Place.objects.create(**values)

    def test_model_autofills_and_partial_coordinate_save_clears_stale_district(self):
        place = self.place()
        self.assertEqual(place.district, 'baku_narimanov')
        self.assertEqual(place.city, 'baku')
        place.lat, place.lng = 0, 0
        place.save(update_fields=['lat', 'lng'])
        place.refresh_from_db()
        self.assertEqual(place.district, '')
        self.assertEqual(place.city, '')
        self.assertEqual(place.location_resolution_status, 'outside_coverage')

    def test_partial_lat_save_uses_persisted_longitude(self):
        place = self.place()
        place.lng = 0  # deliberately not in update_fields
        place.lat = 40.40931
        place.save(update_fields=['lat'])
        place.refresh_from_db()
        self.assertEqual(place.district, 'baku_narimanov')

    def test_form_autofills_without_manual_choices(self):
        form = LocationForm({'lat': 40.4093, 'lng': 49.8671}, instance=Place(category=self.category))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['district'], 'baku_narimanov')

    def test_forged_manual_district_is_field_error(self):
        form = LocationForm({'lat': 40.4093, 'lng': 49.8671, 'region': 'baku', 'district': 'baku_yasamal'}, instance=Place(category=self.category))
        self.assertFalse(form.is_valid())
        self.assertIn('district', form.errors)

    def test_old_district_after_move_is_replaced_without_javascript(self):
        place = self.place()
        # A point in the museum vicinity, well inside Sabail; not the museum record's coordinates.
        form = LocationForm({'lat': 40.360, 'lng': 49.835, 'region': 'baku', 'district': place.district}, instance=place)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['district'], 'baku_sabail')

    def test_uncovered_draft_clears_old_values_and_publication_is_blocked(self):
        place = self.place()
        data = {'lat': 0, 'lng': 0, 'region': 'baku', 'district': place.district}
        form = LocationForm(data, instance=place)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['district'], '')
        place = self.place()
        form = LocationForm(data, instance=place, draft=False)
        self.assertFalse(form.is_valid())

    def test_unrelated_partial_save_keeps_legacy_location(self):
        place = self.place()
        Place.objects.filter(pk=place.pk).update(district='baku_yasamal', location_resolution_status='legacy')
        place.refresh_from_db()
        place.rating_count = 4
        place.save(update_fields=['rating_count'])
        place.refresh_from_db()
        self.assertEqual(place.district, 'baku_yasamal')

    def test_published_move_outside_coverage_is_atomic(self):
        place = self.place(status='published', is_active=True)
        place.lat, place.lng = 0, 0
        with self.assertRaises(ValidationError):
            place.save(update_fields=['lat', 'lng'])
        place.refresh_from_db()
        self.assertEqual(place.lat, 40.4093)

    def test_override_requires_permission_and_reason_and_expires_on_move(self):
        from catalog.services import location_assignment
        self.assertTrue(callable(getattr(location_assignment, 'set_location_override', None)))
        place = self.place()
        user = get_user_model().objects.create_user('location-user')
        with self.assertRaises(ValidationError):
            location_assignment.set_location_override(place, actor=user, city='baku', district='baku_yasamal', reason='Verified boundary issue')
        admin = get_user_model().objects.create_superuser('location-admin', 'fixture@example.invalid', 'password')
        with self.assertRaises(ValidationError):
            location_assignment.set_location_override(place, actor=admin, city='baku', district='baku_yasamal', reason='')
        location_assignment.set_location_override(place, actor=admin, city='baku', district='baku_yasamal', reason='Verified boundary issue')
        place.save()
        place.refresh_from_db()
        self.assertEqual(place.district, 'baku_yasamal')
        self.assertEqual(place.location_overrides.count(), 1)
        place.lat, place.lng = 40.360, 49.835
        place.save(update_fields=['lat', 'lng'])
        place.refresh_from_db()
        self.assertEqual(place.district, 'baku_sabail')
        self.assertFalse(place.location_overrides.filter(is_current=True).exists())

    def test_geocoding_does_not_crash_or_move_published_place_outside_coverage(self):
        from catalog.interfaces.geocoding import GeocodingPoint
        from catalog.services.geocoding import PlaceGeocodingService
        class Provider:
            def is_configured(self): return True
            def geocode(self, **kwargs): return GeocodingPoint(0, 0)
        place = self.place(status='published', is_active=True, address='Fixture address')
        result = PlaceGeocodingService(Provider()).geocode_place(place=place, overwrite=True)
        self.assertFalse(result.updated)
        self.assertEqual(result.reason, 'location_unresolved')
        self.assertEqual((place.lat, place.lng), (40.4093, 49.8671))
        place.refresh_from_db()
        self.assertEqual(place.district, 'baku_narimanov')


class LocationPreviewTests(TestCase):
    def test_requires_login_and_returns_server_result_without_writes(self):
        from django.urls import reverse
        endpoint = reverse('location_resolve')
        url = endpoint + '?lat=40.4093&lng=49.8671'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.create_user('preview-user')
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['district_key'], 'baku_narimanov')
        self.assertEqual(response.json()['city_key'], 'baku')
        self.assertEqual(response.json()['status'], 'resolved')
        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(self.client.post(endpoint).status_code, 405)
        self.assertEqual(self.client.get(endpoint + '?lat=NaN&lng=49').status_code, 400)


class AdminLocationControlsTests(TestCase):
    def test_only_authorized_admin_sees_single_override_control(self):
        from django.contrib.auth.models import Permission
        from django.urls import reverse
        user = get_user_model().objects.create_user('geo-staff', is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename='add_place', content_type__app_label='catalog'))
        self.client.force_login(user)
        response = self.client.get(reverse('admin:catalog_place_add'), {'type': 'permanent'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="location_override_reason"')
        user.user_permissions.add(Permission.objects.get(codename='override_place_location'))
        response = self.client.get(reverse('admin:catalog_place_add'), {'type': 'permanent'})
        self.assertContains(response, 'name="location_override_reason"', count=1)
        url = reverse('admin:catalog_place_location_resolve')
        self.assertTrue(url.startswith('/admin/catalog/place/'))
        response = self.client.get(url, {'lat': 40.4093, 'lng': 49.8671})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['district_key'], 'baku_narimanov')

    def test_admin_preview_uses_requested_editor_language(self):
        from django.urls import reverse
        user = get_user_model().objects.create_superuser('preview-language', 'lang@example.invalid', 'pass')
        self.client.force_login(user)
        response = self.client.get(reverse('admin:catalog_place_location_resolve'),
                                   {'lat': 40.36, 'lng': 49.835, 'language': 'en'})
        self.assertEqual(response.json()['district_label'], 'Sabail')
        self.assertEqual(response.json()['language'], 'en')

    def test_admin_can_save_an_exception_and_moving_the_pin_cancels_it(self):
        from django.urls import reverse
        from catalog.testcases.utils import create_ready_place
        user = get_user_model().objects.create_superuser('override-http', 'override@example.invalid', 'pass')
        self.client.force_login(user)
        place = create_ready_place()
        url = reverse('admin:catalog_place_change', args=[place.pk])
        page = self.client.get(url)
        form = page.context['adminform'].form
        data = {name: form[name].value() if form[name].value() is not None else ''
                for name, field in form.fields.items() if not isinstance(field, forms.FileField)}
        for inline in page.context['inline_admin_formsets']:
            management = inline.formset.management_form
            data.update({management[name].html_name: management[name].value() for name in management.fields})
        data.update(region='baku', district='baku_sabail', location_override_reason='Checked exception for test', _continue='1')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.context['adminform'].form.errors if response.status_code == 200 else '')
        place.refresh_from_db()
        self.assertEqual(place.location_resolution_status, 'overridden')
        self.assertEqual(place.district, 'baku_sabail')
        self.assertEqual(place.location_overrides.get(is_current=True).reason, 'Checked exception for test')
        data.update(lat='40.39', lng='49.81', location_override_reason='')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.context['adminform'].form.errors if response.status_code == 200 else '')
        place.refresh_from_db()
        self.assertEqual(place.district, 'baku_yasamal')
        self.assertFalse(place.location_overrides.filter(is_current=True).exists())
