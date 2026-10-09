from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from catalog.models import Place, Specialist, SiteSettings
from catalog.testcases.utils import create_ready_place


class RetiredVerificationBadgesTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser('badge_admin', email='badge@example.invalid', password='test')
        self.place = create_ready_place(is_verified=True)
        self.specialist = Specialist.objects.create(name='Legacy verified specialist', slug='legacy-badge', status='published', is_active=True, is_verified=True, consultation_format='online')
        site = SiteSettings.get_solo();site.specialists_section_enabled = True;site.save()

    def test_public_legacy_flags_have_no_badges_or_filters(self):
        for path in ['/catalog/', '/specialists/', '/specialists/legacy-badge/']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            if path == '/catalog/':
                self.assertContains(response, self.place.name_az)
            self.assertNotContains(response, 'name="verified"')
            self.assertNotContains(response, 'km-badge-verified')
            self.assertNotContains(response, 'card-trust-icon--verified')
            self.assertNotContains(response, '100% verified')

    def test_admin_forms_and_actions_cannot_assign_badge(self):
        request = RequestFactory().get('/admin/');request.user = self.staff
        for model, obj in [(Place, self.place), (Specialist, self.specialist)]:
            model_admin = admin.site._registry[model]
            self.assertNotIn('is_verified', model_admin.get_form(request, obj).base_fields)
            self.assertNotIn('mark_verified', model_admin.get_actions(request))
            self.assertNotIn('mark_unverified', model_admin.get_actions(request))
            self.assertNotIn('is_verified', model_admin.get_list_filter(request))
            self.assertIn('mark_published', model_admin.get_actions(request))

    def test_old_filter_urls_no_longer_select_verified_only(self):
        other = Specialist.objects.create(name='Ordinary specialist', slug='ordinary-badge', status='published', is_active=True, consultation_format='online')
        response = self.client.get('/specialists/?verified=1', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, other.name)
        self.assertNotContains(response, 'name="verified"')
