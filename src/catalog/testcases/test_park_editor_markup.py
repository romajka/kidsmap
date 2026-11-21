from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Subcategory
from catalog.services.staff_roles import VOLUNTEER_GROUP
from catalog.testcases.utils import create_ready_place


class ParkEditorMarkupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_superuser('park-editor-admin')
        cls.volunteer = get_user_model().objects.create_user('park-editor-volunteer', is_staff=True)
        cls.volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        category, _ = Category.objects.get_or_create(code='parks-playgrounds', defaults={'name': 'Parks'})
        subcategory, _ = Subcategory.objects.get_or_create(category=category, code='parks-boulevards', defaults={'name': 'Parks and boulevards'})
        cls.park = create_ready_place(category=category, subcategory=subcategory, phone1='', created_by=cls.volunteer)

    def assert_administration_inputs(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        inputs = []
        labels = []

        class Controls(HTMLParser):
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'input' and attrs.get('type') != 'hidden':
                    inputs.append(attrs)
                elif tag == 'label':
                    labels.append(attrs.get('for'))

        Controls().feed(response.content.decode())
        for name in ('administration_name', 'administration_phone'):
            matches = [attrs for attrs in inputs if attrs.get('name') == name]
            self.assertEqual(len(matches), 1, (url, name))
            self.assertIn(matches[0]['id'], labels)
            self.assertNotIn('required', matches[0])

    def test_main_admin_can_enter_contact_on_new_and_published_parks(self):
        self.client.force_login(self.staff)
        for route in (reverse('admin:catalog_place_change', args=[self.park.pk]),
                      reverse('admin:catalog_place_add') + '?type=permanent'):
            with self.subTest(route=route):
                self.assert_administration_inputs(route)

    def test_volunteer_can_enter_contact_on_new_and_published_parks(self):
        self.client.force_login(self.volunteer)
        for route in (f'/admin/volunteer/{self.park.pk}/edit/', '/admin/volunteer/add/'):
            with self.subTest(route=route):
                self.assert_administration_inputs(route)
