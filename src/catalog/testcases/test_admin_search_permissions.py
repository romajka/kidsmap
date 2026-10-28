"""Custom suggestion views respect the same model access as their lists."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from catalog.models import Event, Organization, Place, Specialist


class TestAdminSearchPermissions(TestCase):
    models = (Place, Event, Organization, Specialist)

    def request(self, user, term='private-marker'):
        request = RequestFactory().get('/admin/search-suggestions/', {'q': term})
        request.user = user
        request.LANGUAGE_CODE = 'ru'
        return request

    def test_staff_without_model_access_cannot_search_even_with_a_short_query(self):
        staff = get_user_model().objects.create_user('restricted-search', is_staff=True)
        for model in self.models:
            for term in ('private-marker', ''):
                with self.subTest(model=model._meta.label, term=term):
                    with self.assertRaises(PermissionDenied):
                        admin.site._registry[model].search_suggestions_view(self.request(staff, term))

    def test_view_permission_allows_search_only_for_that_model(self):
        for model in self.models:
            with self.subTest(model=model._meta.label):
                staff = get_user_model().objects.create_user('viewer-' + model._meta.model_name, is_staff=True)
                staff.user_permissions.add(Permission.objects.get(
                    content_type__app_label=model._meta.app_label,
                    codename='view_' + model._meta.model_name))
                self.assertEqual(admin.site._registry[model].search_suggestions_view(self.request(staff)).status_code, 200)
                for other in self.models:
                    if other is not model:
                        with self.assertRaises(PermissionDenied):
                            admin.site._registry[other].search_suggestions_view(self.request(staff))

    def test_superuser_keeps_access_to_all_suggestion_views(self):
        staff = get_user_model().objects.create_superuser('search-admin', 'admin@example.invalid', 'synthetic-only')
        for model in self.models:
            with self.subTest(model=model._meta.label):
                self.assertEqual(admin.site._registry[model].search_suggestions_view(self.request(staff)).status_code, 200)
