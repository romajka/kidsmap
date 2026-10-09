"""ORG-01: guessed IDs never disclose a foreign private Place or grant access."""
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone, translation
from catalog.models import Organization, OrganizationPlaceRequest, Place
from catalog.services import organization_ownership as ownership, organization_connections as connections
from catalog.services.business_team import has_action
from catalog.testcases.utils import create_quality_place


class OrganizationJoinVisibilityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='org01_network_owner')
        self.other = User.objects.create_user(username='org01_place_owner')
        self.stranger = User.objects.create_user(username='org01_stranger')
        self.org = Organization.objects.create(owner=self.owner, name_az='ORG01 Uydurma şəbəkə')
        self.secret = 'ORG01 PRIVATE CARD NEVER DISCLOSE'
        self.place = create_quality_place(owner=self.other, created_by=self.other,
            name=self.secret, name_az=self.secret, name_ru=self.secret, name_en=self.secret,
            status='draft', is_active=False)

    def join(self, actor=None):
        return ownership.request_join(actor=actor or self.owner, place_id=self.place.pk, organization_id=self.org.pk)

    def old_request(self):
        # A historical unauthorized request, created before the visibility gate.
        return OrganizationPlaceRequest.objects.create(place=self.place, organization=self.org,
            requested_by=self.owner, relationship_kind='business',
            base_place_owner_id=self.other.pk, base_organization_owner_id=self.owner.pk,
            base_place_ownership_version=self.place.ownership_version,
            base_organization_ownership_version=self.org.ownership_version,
            base_place_content_version=self.place.content_version,
            organization_owner_confirmed_at=timezone.now())

    def csrf_client(self, actor=None):
        client = Client(enforce_csrf_checks=True)
        client.force_login(actor or self.owner)
        client.get(reverse('organization_workspace_detail', args=[self.org.pk]))
        token = client.cookies[settings.CSRF_COOKIE_NAME].value
        return client, token

    def assert_unchanged(self):
        self.place.refresh_from_db()
        self.assertEqual(self.place.owner_id, self.other.pk)
        self.assertIsNone(self.place.organization_id)
        self.assertEqual((self.place.status, self.place.is_active), ('draft', False))
        self.assertFalse(has_action(user=self.owner, target=self.place, action='place.view'))

    def test_canonical_guessed_private_id_denied_without_request_or_rights(self):
        with self.assertRaises(PermissionDenied): self.join()
        self.assertFalse(OrganizationPlaceRequest.objects.exists())
        self.assert_unchanged()

    def test_legacy_valid_csrf_denies_private_id_and_repeated_post_without_name(self):
        client, token = self.csrf_client()
        for _ in range(2):
            response = client.post(reverse('organization_workspace_join', args=[self.org.pk]),
                {'place_id': self.place.pk, 'csrfmiddlewaretoken': token})
            self.assertEqual(response.status_code, 409)
            self.assertNotContains(response, self.secret, status_code=409)
        self.assertFalse(OrganizationPlaceRequest.objects.exists())
        self.assert_unchanged()

    def test_api_valid_csrf_denies_private_id_without_receipt(self):
        client, token = self.csrf_client()
        for _ in range(2):
            response = client.post(f'/api/ownership/join/place/{self.place.pk}/',
                json.dumps({'organization_id': self.org.pk}), content_type='application/json', HTTP_X_CSRFTOKEN=token)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json(), {'error': 'forbidden'})
        self.assertFalse(OrganizationPlaceRequest.objects.exists())
        self.assert_unchanged()

    def test_workspace_redacts_historical_private_pending_in_all_languages(self):
        item = self.old_request()
        self.client.force_login(self.owner)
        for language in ('az', 'ru', 'en'):
            with translation.override(language):
                response = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, self.secret)
            self.assertNotIn(item, response.context['pending_requests'])
        self.assertTrue(OrganizationPlaceRequest.objects.filter(pk=item.pk, status='pending').exists())
        self.assert_unchanged()

    def test_historical_private_pending_cannot_be_confirmed_or_reused(self):
        item = self.old_request()
        with self.assertRaises(PermissionDenied): ownership.confirm_join(actor=self.owner, request_id=item.pk)
        with self.assertRaises(PermissionDenied): self.join()
        item.refresh_from_db()
        self.assertEqual(item.status, 'pending')
        self.assertIsNone(item.place_owner_confirmed_at)
        self.assert_unchanged()

    def test_api_cannot_confirm_historical_private_pending(self):
        item = self.old_request()
        client, token = self.csrf_client()
        response = client.post(f'/api/ownership/confirm-join/place/{item.pk}/', '{}',
            content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'error': 'forbidden'})
        self.assert_unchanged()

    def test_bulk_preview_also_rejects_guessed_private_id(self):
        with self.assertRaises(PermissionDenied):
            connections.preview_connections(actor=self.owner, organization_id=self.org.pk,
                relationship_kind='business', place_ids=[self.place.pk])
        self.assertFalse(OrganizationPlaceRequest.objects.exists())

    def test_direct_owner_can_share_private_place_by_current_consent(self):
        item = self.join(self.other)
        self.assertEqual(item.status, 'pending')
        self.assertFalse(has_action(user=self.owner, target=self.place, action='place.view'))
        self.client.force_login(self.owner)
        response = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]))
        self.assertContains(response, self.secret)
        self.assertIn(item, response.context['pending_requests'])
        approved = ownership.confirm_join(actor=self.owner, request_id=item.pk)
        self.assertEqual(approved.status, 'approved')
        self.place.refresh_from_db()
        self.assertTrue(ownership.affiliation_current(self.place, self.org))
        before = self.place.content_version
        self.assertEqual(self.join().pk, item.pk)
        self.assertEqual(ownership.confirm_join(actor=self.owner, request_id=item.pk).pk, item.pk)
        self.place.refresh_from_db()
        self.assertEqual(self.place.content_version, before)
        self.assertEqual(self.place.owner_id, self.other.pk)

    def test_same_owner_can_connect_own_private_draft(self):
        own_org = Organization.objects.create(owner=self.other, name_az='ORG01 Own network')
        item = ownership.request_join(actor=self.other, place_id=self.place.pk, organization_id=own_org.pk)
        self.assertEqual(item.status, 'approved')
        self.place.refresh_from_db()
        self.assertEqual((self.place.owner_id, self.place.status, self.place.is_active), (self.other.pk, 'draft', False))
        self.assertTrue(ownership.affiliation_current(self.place, own_org))

    def test_public_place_dual_consent_and_replay_preserve_content(self):
        Place.objects.filter(pk=self.place.pk).update(status='published', is_active=True)
        self.place.refresh_from_db()
        before = (self.place.name_az, self.place.photo.name, self.place.owner_id)
        item = self.join()
        self.assertEqual(item.status, 'pending')
        self.assertFalse(has_action(user=self.owner, target=self.place, action='place.edit'))
        self.assertEqual(self.join().pk, item.pk)
        approved = ownership.confirm_join(actor=self.other, request_id=item.pk)
        self.assertEqual(approved.status, 'approved')
        self.place.refresh_from_db()
        self.assertEqual((self.place.name_az, self.place.photo.name, self.place.owner_id), before)
        self.assertEqual(self.join().pk, item.pk)

    def test_visibility_withdrawn_after_public_request_blocks_old_organization_consent(self):
        Place.objects.filter(pk=self.place.pk).update(status='published', is_active=True)
        item = self.join()
        Place.objects.filter(pk=self.place.pk).update(status='draft', is_active=False, content_version=F('content_version')+1)
        with self.assertRaises((PermissionDenied, ValidationError)): ownership.confirm_join(actor=self.owner, request_id=item.pk)
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(reverse('organization_workspace_detail', args=[self.org.pk])), self.secret)
        self.assert_unchanged()

    def test_stale_private_owner_consent_is_not_visibility(self):
        item = self.join(self.other)
        Place.objects.filter(pk=self.place.pk).update(content_version=F('content_version')+1)
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(reverse('organization_workspace_detail', args=[self.org.pk])), self.secret)
        with self.assertRaises(PermissionDenied): self.join()
        with self.assertRaises(PermissionDenied): ownership.confirm_join(actor=self.owner, request_id=item.pk)
        self.assert_unchanged()

    def test_owner_change_invalidates_private_consent(self):
        item = self.join(self.other)
        ownership.transfer_owner(actor=self.other, target_type='place', target_id=self.place.pk,
            new_owner_id=self.stranger.pk, expected_ownership_version=self.place.ownership_version)
        with self.assertRaises(PermissionDenied): self.join()
        with self.assertRaises((PermissionDenied, ValidationError)):
            ownership.confirm_join(actor=self.owner, request_id=item.pk)
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(reverse('organization_workspace_detail', args=[self.org.pk])), self.secret)

    def test_unrelated_actor_cannot_use_private_owner_consent(self):
        item = self.join(self.other)
        with self.assertRaises(PermissionDenied): ownership.confirm_join(actor=self.stranger, request_id=item.pk)
        other_org = Organization.objects.create(owner=self.stranger, name_az='ORG01 Unrelated network')
        with self.assertRaises(PermissionDenied):
            ownership.request_join(actor=self.stranger, place_id=self.place.pk, organization_id=other_org.pk)
        self.assert_unchanged()

    def test_private_consent_is_scoped_to_the_invited_organization(self):
        item = self.join(self.other)
        second = Organization.objects.create(owner=self.owner, name_az='ORG01 Second network')
        with self.assertRaises(PermissionDenied):
            ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=second.pk)
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(reverse('organization_workspace_detail', args=[second.pk])), self.secret)
        self.assertEqual(OrganizationPlaceRequest.objects.filter(place=self.place).count(), 1)
        self.assertEqual(item.status, 'pending')
