"""Server-backed editor field validation; no external profile lookup."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.translation import override

from catalog.models import Place, VolunteerPlaceRevision
from catalog.services.phone_forms import ContactPhoneFormMixin
from catalog.testcases.utils import ensure_quality_subcategory


class SocialEditor(ContactPhoneFormMixin, forms.ModelForm):
    class Meta:
        model = Place
        fields = ('instagram',)


class InstagramFieldTests(SimpleTestCase):
    def test_accepted_uppercase_url_prefixes_render_as_working_profile_links(self):
        for value in ('HTTPS://WWW.INSTAGRAM.COM/KidsMap.AZ/?utm_source=QR',
                      'INSTAGRAM.COM/KidsMap.AZ/?utm_source=QR',
                      'WWW.INSTAGRAM.COM/KidsMap.AZ/?utm_source=QR'):
            with self.subTest(value=value):
                form = SocialEditor(data={'instagram': value})
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data['instagram'], value)
                host = 'www.instagram.com' if 'WWW.' in value else 'instagram.com'
                self.assertEqual(Place(instagram=value).instagram_url(),
                                 f'https://{host}/KidsMap.AZ/?utm_source=QR')

    def test_profile_render_preserves_handle_case_and_existing_legacy_fallback(self):
        cases = {
            '': '',
            '@KidsMap.AZ': 'https://instagram.com/KidsMap.AZ',
            'KidsMap.AZ': 'https://instagram.com/KidsMap.AZ',
            'https://instagram.com/KidsMap.AZ/?utm_source=QR': 'https://instagram.com/KidsMap.AZ/?utm_source=QR',
            'old / profile at desk': 'https://instagram.com/old / profile at desk',
            'https://example.invalid/old-profile': 'https://example.invalid/old-profile',
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(Place(instagram=value).instagram_url(), expected)

    def test_profile_formats_are_preserved_without_lookup_or_rewriting(self):
        for value in ('', 'kidsmap', '@kidsmap.az', 'kids_map.1',
                      'instagram.com/kidsmap', 'www.instagram.com/kidsmap/',
                      'https://instagram.com/kidsmap/?utm_source=qr',
                      'https://www.instagram.com/kidsmap', 'http://instagram.com/kidsmap'):
            with self.subTest(value=value):
                form = SocialEditor(data={'instagram': value})
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data['instagram'], value)

    def test_obviously_invalid_profile_values_are_field_errors(self):
        for value in ('https://example.com/kidsmap', 'https://instagram.com.evil.invalid/kidsmap',
                      'https://user:pass@instagram.com/kidsmap', 'javascript:alert(1)',
                      'https://instagram.com/', 'https://instagram.com/p/abc',
                      'https://instagram.com/stories/kidsmap/123', '@@kidsmap',
                      'kid map', ' kidsmap', 'kidsmap\n', 'kid\x00map',
                      'https://instagram.com/kid%2Fmap', 'https://instagram.com:8443/kidsmap'):
            with self.subTest(value=value):
                form = SocialEditor(data={'instagram': value})
                self.assertFalse(form.is_valid())
                self.assertIn('instagram', form.errors)
                expected = 'null_characters_not_allowed' if '\x00' in value else 'invalid_instagram'
                self.assertEqual(form.errors.as_data()['instagram'][0].code, expected)

    def test_untouched_legacy_is_preserved_but_changed_invalid_value_is_rejected(self):
        for persisted in (True, False):
            place = Place(pk=42 if persisted else None, instagram='old profile / ask desk')
            options = {} if persisted else {'preserve_existing_contacts': True}
            form = SocialEditor(data={'instagram': place.instagram}, instance=place, **options)
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data['instagram'], 'old profile / ask desk')
            changed = SocialEditor(data={'instagram': 'new profile / ask desk'}, instance=place, **options)
            self.assertFalse(changed.is_valid())
            self.assertIn('instagram', changed.errors)

    def test_changed_valid_profile_and_explicit_clear_are_allowed_for_legacy(self):
        for value in ('', '@new.profile'):
            form = SocialEditor(data={'instagram': value}, instance=Place(pk=42, instagram='old / profile'))
            self.assertTrue(form.is_valid(), form.errors)
            self.assertEqual(form.cleaned_data['instagram'], value)

    def test_profile_error_is_localized(self):
        messages = []
        for language in ('az', 'ru', 'en'):
            with override(language):
                form = SocialEditor(data={'instagram': 'https://example.com/kidsmap'})
                self.assertFalse(form.is_valid())
                messages.append(str(form.errors['instagram'][0]))
        self.assertEqual(len(set(messages)), 3)


class PlaceLiveValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.subcategory = ensure_quality_subcategory('EDU')
        user = get_user_model()
        cls.owner = user.objects.create_user('live_validation_owner')
        cls.staff = user.objects.create_superuser('live_validation_staff', 'validation@example.invalid', 'synthetic')
        cls.volunteer = user.objects.create_user('live_validation_volunteer', is_staff=True)
        cls.volunteer.groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])

    def payload(self, **changes):
        return dict(name_az='Uşaqların yaradıcılıq məkanı', description_az='Uşaqlar üçün yaradıcılıq və təhsil.',
                    category='EDU', subcategory=str(self.subcategory.pk), age_from='3', age_to='12',
                    region='baku', district='baku_yasamal', address='Yaradıcılıq küçəsi 1',
                    schedule_mode='always_open', price_mode='free', pricing_plans='[]',
                    phone1='+994504274393', phone_country='AZ', whatsapp_mode='none',
                    revision_version='0', base_token='new-place', action='draft',
                    **changes)

    def test_all_three_editor_forms_validate_instagram(self):
        from catalog.forms import OwnerPlaceCreateForm
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.volunteer_forms import VolunteerPlaceForm
        for form_class in (OwnerPlaceCreateForm, PlaceAdminForm, VolunteerPlaceForm):
            for value, valid in [('https://evil.invalid/kidsmap', False), ('@kidsmap.az', True)]:
                with self.subTest(form=form_class.__name__, value=value):
                    form = form_class(data=self.payload(instagram=value))
                    form.is_valid()
                    self.assertEqual('instagram' not in form.errors, valid, form.errors)

    def test_all_three_forms_preserve_untouched_saved_profile(self):
        from catalog.forms import OwnerPlaceEditForm
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.volunteer_forms import VolunteerPlaceForm
        from catalog.testcases.utils import create_ready_place
        place = create_ready_place(category=self.subcategory.category, subcategory=self.subcategory,
                                   instagram='old / profile at desk')
        for form_class in (OwnerPlaceEditForm, PlaceAdminForm, VolunteerPlaceForm):
            for value, valid in [('old / profile at desk', True), ('changed / wrong profile', False), ('@new.profile', True)]:
                with self.subTest(form=form_class.__name__, value=value):
                    form = form_class(data=self.payload(instagram=value), instance=Place.objects.get(pk=place.pk))
                    form.is_valid()
                    self.assertEqual('instagram' not in form.errors, valid, form.errors)
                    if valid:
                        self.assertEqual(form.cleaned_data['instagram'], value)

    def test_check_only_reports_bad_contacts_and_clears_corrected_errors_without_writes(self):
        for user, suffix in ((self.owner, ''), (self.staff, '?surface=admin'), (self.volunteer, '?surface=volunteer')):
            with self.subTest(surface=suffix):
                self.client.force_login(user)
                url = reverse('place_editor_preview_new') + suffix
                before = (Place.objects.count(), VolunteerPlaceRevision.objects.count())
                bad = self.payload(instagram='https://evil.invalid/kidsmap', website='http://')
                bad.update(phone1='546435643', _km_check_required='1')
                good = self.payload(instagram='https://www.instagram.com/kidsmap/?utm_source=qr', website='https://example.com')
                good['_km_check_required'] = '1'
                with CaptureQueriesContext(connection) as queries:
                    invalid = self.client.post(url, bad)
                    corrected = self.client.post(url, good)
                self.assertEqual(invalid.status_code, 422)
                for field in ('phone1', 'website', 'instagram'):
                    self.assertIn(field, invalid.json()['errors'])
                self.assertEqual(corrected.status_code, 200, corrected.content)
                self.assertTrue(corrected.json()['ok'])
                self.assertEqual(corrected.json()['errors'], {})
                writes = [q['sql'] for q in queries if q['sql'].lstrip().upper().startswith(('INSERT', 'UPDATE', 'DELETE'))]
                self.assertEqual(writes, [])
                self.assertEqual(before, (Place.objects.count(), VolunteerPlaceRevision.objects.count()))
                self.assertIn('no-store', corrected.headers['Cache-Control'])
