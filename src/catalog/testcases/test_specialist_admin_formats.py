from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse

from catalog.models import District, Region, Specialist, SpecialistPracticeLocation, SpecialistSpecialization


class SpecialistAdminFormatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser('format-editor')
        cls.region = Region.objects.create(key='format-city', name_ru='Город')
        cls.district = District.objects.create(key='format-area', region=cls.region, name_ru='Район')
        cls.specialty, _ = SpecialistSpecialization.objects.get_or_create(code='format-specialty')

    def setUp(self):
        self.client.force_login(self.staff)
        self.model_admin = admin.site._registry[Specialist]

    def form(self, **data):
        request = RequestFactory().get('/')
        request.user = self.staff
        cls = self.model_admin.get_form(request)
        return cls(data={'name': 'Format profile', 'status': 'pending',
                         'lesson_type': 'individual', 'lesson_price': '25',
                         'specializations': [self.specialty.pk], **data})

    def test_admin_can_save_and_reopen_online_and_visits_without_an_office(self):
        form = self.form(session_formats=['online', 'visit'], visit_region=self.region.pk,
                         visit_districts=[self.district.pk])
        self.assertIn('session_formats', form.fields)
        self.assertTrue(form.is_valid(), form.errors)
        person = form.save()
        self.assertEqual(list(person.visit_districts.all()), [self.district])
        self.assertEqual((person.offers_online, person.offers_office, person.offers_visits), (True, False, True))
        response = self.client.get(reverse('admin:catalog_specialist_change', args=[person.pk]))
        self.assertEqual(set(response.context['adminform'].form['session_formats'].value()), {'online', 'visit'})
        self.assertContains(response, 'name="session_formats"', count=3)

    def test_publication_requires_a_format_and_visit_area_but_draft_can_be_empty(self):
        self.assertIn('session_formats', self.form().errors)
        self.assertIn('visit_region', self.form(session_formats=['visit']).errors)
        self.assertIn('visit_districts', self.form(session_formats=['visit'], visit_region=self.region.pk).errors)
        self.assertTrue(self.form(status='draft').is_valid())

    def test_pending_and_publish_actions_skip_office_without_active_location(self):
        fees = {'lesson_type': 'individual', 'lesson_price': 25}
        invalid = Specialist.objects.create(name='Missing office', consultation_format='offline', status='draft', is_active=False, **fees)
        valid = Specialist.objects.create(name='Valid office', consultation_format='offline', status='draft', is_active=False, **fees)
        SpecialistPracticeLocation.objects.create(specialist=valid, region=self.region, address='Test office')
        for action, expected in [('mark_pending', 'pending'), ('mark_published', 'published')]:
            with self.subTest(action=action):
                self.client.post(reverse('admin:catalog_specialist_changelist'),
                                 {'action': action, '_selected_action': [invalid.pk, valid.pk]})
                invalid.refresh_from_db()
                valid.refresh_from_db()
                self.assertEqual(invalid.status, 'draft')
                self.assertEqual(valid.status, expected)

    def test_read_only_editor_can_read_the_confirmed_home_visit_area(self):
        reader = get_user_model().objects.create_user('format-reader', is_staff=True)
        reader.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_specialist'))
        person = Specialist.objects.create(name='Travelling specialist', offers_visits=True, visit_region=self.region)
        person.visit_districts.add(self.district)
        self.client.force_login(reader)
        response = self.client.get(reverse('admin:catalog_specialist_change', args=[person.pk]))
        self.assertContains(response, 'data-saved-visit-area')
        self.assertContains(response, self.district.name_ru)
        self.assertNotContains(response, 'name="session_formats"')
