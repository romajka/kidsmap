from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import SiteSettings, Specialist, SpecialistSpecialization


class SpecialistAdminTariffTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser('tariff-editor')
        cls.specialty = SpecialistSpecialization.objects.create(code='tariff-test')

    def setUp(self):
        self.client.force_login(self.staff)
        self.request = RequestFactory().get('/')
        self.request.user = self.staff
        self.admin = admin.site._registry[Specialist]

    def form(self, **kwargs):
        data = {'name': 'Example', 'status': 'pending', 'session_formats': ['online'],
                'specializations': [self.specialty.pk], **kwargs}
        return self.admin.get_form(self.request)(data=data)

    def test_packages_cannot_replace_required_single_lesson(self):
        missing = self.form(package_period=['month'], package_amount=['160'], package_sessions=['8'])
        self.assertIn('lesson_price', missing.errors)
        self.assertIn('lesson_type', missing.errors)
        paid = self.form(lesson_type='individual', lesson_price='22.50',
                         package_period=['month'], package_amount=['160'], package_sessions=['8'])
        self.assertTrue(paid.is_valid(), paid.errors)
        person = paid.save()
        self.assertEqual(person.pricing_packages[0]['sessions'], 8)
        url = reverse('admin:catalog_specialist_change', args=[person.pk])
        response = self.client.get(url)
        self.assertContains(response, 'name="lesson_price"')
        self.assertContains(response, 'name="package_sessions"')

    def test_quick_approval_cannot_publish_a_profile_with_only_legacy_amount(self):
        legacy = Specialist.objects.create(name='Legacy', consultation_format='online',
                                            status='pending', is_active=False, price_from=35)
        self.client.post(reverse('admin:catalog_specialist_changelist'),
                         {'action': 'mark_published', '_selected_action': [legacy.pk]})
        legacy.refresh_from_db()
        self.assertEqual(legacy.status, 'pending')

    def test_public_profile_shows_approved_session_and_distinct_package_price(self):
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        form = self.form(lesson_type='group', lesson_price='30', package_period=['month'],
                         package_amount=['200'], package_sessions=['8'])
        self.assertTrue(form.is_valid(), form.errors)
        person = form.save()
        with override('ru'):
            url = person.get_absolute_url()
        guest = self.client_class()
        self.assertEqual(guest.get(url).status_code, 404)
        self.client.post(reverse('admin:catalog_specialist_changelist'),
                         {'action': 'mark_published', '_selected_action': [person.pk]})
        response = guest.get(url)
        self.assertContains(response, '30 ₼ за занятие')
        self.assertContains(response, '200 ₼')
        self.assertContains(response, '8 занятий')
        self.assertContains(response, '25 ₼ за занятие')
