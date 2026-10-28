"""Addition editor contracts: candidate privacy and actionable save errors."""
import json
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import RequestFactory, TestCase

from catalog.controllers.server_draft_api import draft_collection
from catalog.models import Place, VolunteerPlaceRevision
from catalog.testcases.utils import create_ready_place


class AdditionEditorRegressionTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser('addition-editor', 'editor@example.invalid', 'synthetic')
        self.viewer = get_user_model().objects.create_user('addition-viewer', is_staff=True)
        self.viewer.user_permissions.add(Permission.objects.get(codename='view_place', content_type__app_label='catalog'))
        self.place = create_ready_place(name_az='Original candidate parent', address='Original address')
        self.revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.admin,
            status='pending', payload={'name_az':'Distinct candidate title', 'address':'Candidate address 5', 'phone1':'+994501237890'})

    def duplicates(self, user, **params):
        request = RequestFactory().get('/admin/catalog/place/duplicate-candidates/', params)
        request.user = user
        request.LANGUAGE_CODE = 'az'
        return json.loads(admin.site._registry[Place].duplicate_candidates_view(request).content)['results']

    def test_authorized_editor_matches_candidate_only_phone_and_address(self):
        for params in ({'phone':'+994 50 123 78 90'}, {'address':'Candidate address 5'}):
            with self.subTest(params=params):
                rows = self.duplicates(self.admin, **params)
                self.assertEqual([row['id'] for row in rows], [self.place.pk])
                self.assertEqual(rows[0]['address'], 'Candidate address 5')
                self.assertEqual(rows[0]['title'], 'Distinct candidate title')

    def test_read_only_viewer_cannot_discover_private_candidate_contacts(self):
        self.assertEqual(self.duplicates(self.viewer, phone='+994501237890'), [])
        self.assertEqual(self.duplicates(self.viewer, address='Candidate address 5'), [])
        self.assertEqual(len(self.duplicates(self.viewer, address='Original address')), 1)

    def test_approved_or_excluded_candidate_is_not_suggested(self):
        self.assertEqual(self.duplicates(self.admin, phone='+994501237890', exclude=str(self.place.pk)), [])
        self.revision.status='approved'
        self.revision.save(update_fields=['status'])
        self.assertEqual(self.duplicates(self.admin, phone='+994501237890'), [])

    def test_draft_validation_returns_concrete_field_errors(self):
        request = RequestFactory().post('/api/drafts/', data=json.dumps({'fields':{'age_from':'bad'}}), content_type='application/json')
        request.user = self.admin
        request._dont_enforce_csrf_checks = True
        with patch('catalog.controllers.server_draft_api.service.save', side_effect=ValidationError({'age_from':['Enter a whole number.']})):
            response = draft_collection(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content)['errors'], {'age_from':['Enter a whole number.']})

    def test_numeric_draft_validation_retains_field_name(self):
        from catalog.services.server_drafts import _fields
        with self.assertRaises(ValidationError) as caught:
            _fields('place', {'age_from': 'not-an-age'})
        self.assertIn('age_from', caught.exception.message_dict)

    def test_pending_save_receipt_explains_live_version_and_links_to_authorized_review(self):
        request = RequestFactory().post('/admin/catalog/place/1/change/')
        request.user = self.admin
        request.session = {}
        place_admin = admin.site._registry[Place]
        with patch.object(place_admin, 'message_user'), self.captureOnCommitCallbacks(execute=True):
            place_admin._queue_place_save_result(request, self.place)
        result = request.session['_km_place_editor_result']
        self.assertEqual(result['action'], 'moderation')
        self.assertIn(str(self.revision.pk), result['next_url'])
        self.assertTrue(result['next_label'])

    def test_pending_save_never_suggests_review_when_reviewer_acl_denies_it(self):
        request = RequestFactory().post('/admin/catalog/place/1/change/')
        request.user = self.admin
        request.session = {}
        place_admin = admin.site._registry[Place]
        with patch.object(place_admin, 'message_user'), patch('catalog.services.moderation_hub.reviewer_scopes', side_effect=PermissionDenied), self.captureOnCommitCallbacks(execute=True):
            place_admin._queue_place_save_result(request, self.place)
        self.assertEqual(request.session['_km_place_editor_result']['next_url'], place_admin._place_change_url(self.place))
