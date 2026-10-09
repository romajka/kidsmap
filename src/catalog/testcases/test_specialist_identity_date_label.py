"""The admin identity confirmation date is localized and remains read-only."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from catalog.models import Specialist


class SpecialistIdentityDateLabelTests(TestCase):
    def test_add_and_change_show_localized_readonly_identity_date(self):
        staff = get_user_model().objects.create_superuser('identity-label-qa', password='synthetic')
        self.client.force_login(staff)
        person = Specialist.objects.create(name='QA Identity label', person_verified_at=timezone.now())
        labels = {
            'ru': 'Дата подтверждения личности',
            'az': 'Şəxsiyyətin təsdiqlənmə tarixi',
            'en': 'Identity verification date',
        }
        for lang, label in labels.items():
            self.client.cookies['django_language'] = lang
            for suffix in ['add/', f'{person.pk}/change/']:
                with self.subTest(language=lang, route=suffix):
                    response = self.client.get('/admin/catalog/specialist/' + suffix)
                    self.assertContains(response, label)
                    self.assertNotContains(response, 'Person verified at:')
                    self.assertNotIn('person_verified_at', response.context['adminform'].form.fields)
                    self.assertNotContains(response, 'name="person_verified_at"')

    def test_identity_date_keeps_original_field_format_and_empty_value(self):
        from django.contrib import admin
        from django.contrib.admin.utils import display_for_field
        editor = admin.site._registry[Specialist]
        field = Specialist._meta.get_field('person_verified_at')
        for value in [timezone.now(), None]:
            with self.subTest(empty=value is None):
                person = Specialist(person_verified_at=value)
                expected = display_for_field(value, field, editor.get_empty_value_display())
                self.assertEqual(editor.identity_verification_date(person), expected)
