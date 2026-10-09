"""ORG-03: only a successful native create can acknowledge local recovery."""
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Organization


class OrganizationCreationConfirmationTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='org03_owner')
        self.stranger = get_user_model().objects.create_user(username='org03_stranger')
        self.client.force_login(self.owner)
        self.url = reverse('organization_workspace_create')
        self.fields = dict(name_az='  ORG03 Fictional network  ', name_ru='Синтетическая сеть',
            name_en='', description_az='  Original input  ', phone='', whatsapp='', website='')

    def create(self):
        response = self.client.post(self.url, self.fields)
        self.assertEqual(response.status_code, 302)
        return response['Location']

    def test_success_acknowledges_exact_submitted_fields_once(self):
        location = self.create()
        self.assertEqual(Organization.objects.filter(owner=self.owner).count(), 1)
        self.assertNotIn('Original', location)
        response = self.client.get(location)
        self.assertEqual(response.context.get('organization_create_confirmation'), self.fields)
        self.assertContains(response, 'id="org-create-confirmation"')
        self.assertFalse(response.context['organization'].places.exists())
        repeated = self.client.get(location)
        self.assertIsNone(repeated.context.get('organization_create_confirmation'))
        self.assertNotContains(repeated, 'id="org-create-confirmation"')

    def test_invalid_input_does_not_confirm_or_create(self):
        response = self.client.post(self.url, {**self.fields, 'website':'not a URL'})
        self.assertEqual(response.status_code, 400)
        self.assertNotContains(response, 'id="org-create-confirmation"', status_code=400)
        self.assertFalse(Organization.objects.filter(owner=self.owner).exists())
        self.assertNotIn('organization_create_confirmation', self.client.session)

    def test_duplicate_conflict_never_confirms_a_second_creation(self):
        self.create()
        response = self.client.post(self.url, self.fields)
        self.assertEqual(response.status_code, 409)
        self.assertNotContains(response, 'id="org-create-confirmation"', status_code=409)
        self.assertEqual(Organization.objects.filter(owner=self.owner).count(), 1)

    def test_forged_or_missing_nonce_cannot_confirm_and_does_not_consume_receipt(self):
        location = self.create()
        path = urlsplit(location).path
        for url in [path, path+'?created=forged']:
            response = self.client.get(url)
            self.assertIsNone(response.context.get('organization_create_confirmation'))
        self.assertEqual(self.client.get(location).context.get('organization_create_confirmation'), self.fields)

    def test_receipt_is_bound_to_the_created_organization(self):
        other = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Other network')
        location = self.create()
        query = parse_qs(urlsplit(location).query)
        self.assertIn('created', query)
        token = query['created'][0]
        wrong = self.client.get(reverse('organization_workspace_detail',args=[other.pk])+'?created='+token)
        self.assertIsNone(wrong.context.get('organization_create_confirmation'))
        self.assertEqual(self.client.get(location).context.get('organization_create_confirmation'), self.fields)

    def test_other_user_cannot_read_creation_confirmation_or_organization(self):
        location = self.create()
        stranger_client = Client()
        stranger_client.force_login(self.stranger)
        self.assertEqual(stranger_client.get(location).status_code, 404)
        self.assertEqual(self.client.get(location).context.get('organization_create_confirmation'), self.fields)
