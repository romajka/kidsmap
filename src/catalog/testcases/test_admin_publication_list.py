"""Publication in the list is visibility, separate from saved edit readiness."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place, VolunteerPlaceRevision
from catalog.services import publication
from catalog.testcases.utils import create_ready_place


class AdminPublicationListTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser('list-publisher', '', 'fictional')
        self.viewer = get_user_model().objects.create_user('list-viewer', is_staff=True)
        self.viewer.user_permissions.add(Permission.objects.get(codename='view_place'))
        self.place = create_ready_place(district='baku_nasimi')
        self.client.force_login(self.staff)
        self.model_admin = admin.site._registry[Place]

    def listing(self, **params):
        response = self.client.get(reverse('admin:catalog_place_changelist'), params)
        self.assertEqual(response.status_code, 200)
        return response

    def row(self, response):
        return next(obj for obj in response.context['cl'].result_list if obj.pk == self.place.pk)

    def test_ready_draft_is_explicitly_unpublished_with_publish_action(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft', is_active=False)
        html = self.model_admin.col_state(self.row(self.listing()))
        self.assertIn('Не опубликовано', html)
        self.assertIn('Готово к публикации', html)
        self.assertIn('data-publication-action', html)
        self.assertIn('>Опубликовать</button>', html)
        self.assertNotIn('>Снять с публикации</button>', html)

    def test_published_place_has_explicit_visibility_and_unpublish_action(self):
        html = self.model_admin.col_state(self.row(self.listing()))
        self.assertIn('Видно на сайте', html)
        self.assertIn('>Снять с публикации</button>', html)
        self.assertNotIn('>Опубликовать</button>', html)

    def test_pending_edits_do_not_erase_existing_publication(self):
        publication.propose(actor=self.staff,target_type='place',target_id=self.place.pk,
            patch={'address':'Saved pending address'},schema_version=1,
            expected_version=self.place.content_version,submit=True,explicit_save=True)
        obj=self.row(self.listing())
        html=self.model_admin.col_state(obj)
        self.assertIn('>Опубликовано</span>',html)
        self.assertIn('Правки на модерации',html)
        self.assertIn('>Снять с публикации</button>',html)
        self.assertEqual(Place.objects.get(pk=self.place.pk).address,self.place.address)

    def test_incomplete_draft_explains_next_step_instead_of_fake_publish_button(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft',is_active=False,lat=None,lng=None)
        obj=self.row(self.listing())
        html=self.model_admin.col_state(obj)
        self.assertIn('Не опубликовано',html)
        self.assertIn('Исправить',html)
        self.assertNotIn('data-publication-action',html)
        self.assertIn('data-can-toggle-publication="0"',self.model_admin.col_actions(obj))

    def test_quality_hidden_place_is_not_labelled_published_or_counted_as_visible(self):
        Place.objects.filter(pk=self.place.pk).update(lat=None,lng=None,address='')
        response=self.listing()
        html=self.model_admin.col_state(self.row(response))
        self.assertIn('Скрыто с сайта',html)
        self.assertNotIn('>Опубликовано</span>',html)
        counts=self.model_admin._place_dashboard_counts(response.wsgi_request)
        self.assertEqual(counts['quick_published'],0)
        self.assertEqual(counts['quick_unpublished'],1)
        self.assertNotIn(self.place.pk,[p.pk for p in self.listing(publication_state='published').context['cl'].result_list])
        self.assertIn(self.place.pk,[p.pk for p in self.listing(publication_state='unpublished').context['cl'].result_list])

    def test_view_only_user_does_not_receive_publication_controls(self):
        self.client.force_login(self.viewer)
        obj=self.row(self.listing())
        self.assertNotIn('data-publication-action',self.model_admin.col_state(obj))
        self.assertIn('data-can-toggle-publication="0"',self.model_admin.col_actions(obj))

    def test_successful_publish_and_unpublish_change_actual_visibility(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft',is_active=False)
        url=reverse('admin:catalog_place_toggle_publication',args=[self.place.pk])
        for expected in (True,False):
            response=self.client.post(url,HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.json()['ok'])
            obj=self.row(self.listing())
            self.assertEqual(obj.km_in_public_catalog,expected)

    def test_pending_saved_revision_is_in_moderation_filter_and_count(self):
        publication.propose(actor=self.staff,target_type='place',target_id=self.place.pk,
            patch={'address':'Saved pending address'},schema_version=1,
            expected_version=self.place.content_version,submit=True,explicit_save=True)
        response=self.listing(publication_state='review')
        self.assertEqual(self.row(response).pk,self.place.pk)
        counts=self.model_admin._place_dashboard_counts(response.wsgi_request)
        self.assertEqual(counts['quick_pending'],1)
        self.assertEqual(counts['stat_pending'],1)

    def test_stale_publish_action_cannot_unpublish_an_already_public_place(self):
        response=self.client.post(reverse('admin:catalog_place_toggle_publication',args=[self.place.pk]),
            {'intent':'publish'},HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code,409)
        self.place.refresh_from_db()
        self.assertEqual((self.place.status,self.place.is_active),('published',True))

    def test_stale_unpublish_action_cannot_publish_a_draft(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft',is_active=False)
        response=self.client.post(reverse('admin:catalog_place_toggle_publication',args=[self.place.pk]),
            {'intent':'unpublish'},HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code,409)
        self.place.refresh_from_db()
        self.assertEqual((self.place.status,self.place.is_active),('draft',False))

    def test_another_request_cannot_grant_publication_controls_to_viewer_rows(self):
        self.client.force_login(self.viewer)
        viewer_row=self.row(self.listing())
        self.client.force_login(self.staff)
        self.listing()
        self.assertNotIn('data-publication-action',self.model_admin.col_state(viewer_row))

    def test_ready_working_copy_cannot_offer_publish_when_stored_point_is_missing(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft', is_active=False, lat=None, lng=None)
        self.place.refresh_from_db()
        publication.propose(actor=self.staff, target_type='place', target_id=self.place.pk,
            patch={'lat': 40.4, 'lng': 49.8}, schema_version=1,
            expected_version=self.place.content_version, submit=False, explicit_save=False)
        response = self.listing()
        obj = self.row(response)
        card = next(c for c in response.context['cl'].place_cards if c['pk'] == self.place.pk)
        self.assertEqual(card['readiness_score'], 100)
        self.assertTrue(card['has_coordinates'])
        self.assertFalse(card['is_ready'])
        self.assertTrue(card['publication_blockers'])
        self.assertNotIn('>Опубликовать</button>', self.model_admin.col_state(obj))
        self.assertIn('data-can-toggle-publication="0"', self.model_admin.col_actions(obj))
        self.assertNotIn(self.place.pk, [p.pk for p in self.listing(publication_state='ready').context['cl'].result_list])

    def test_pending_source_conflict_is_not_offered_as_ready(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft', is_active=False)
        self.place.refresh_from_db()
        publication.propose(actor=self.staff, target_type='place', target_id=self.place.pk,
            patch={'address': 'Pending address'}, schema_version=1,
            expected_version=self.place.content_version, submit=True, explicit_save=False)
        Place.objects.filter(pk=self.place.pk).update(address='Concurrent address')
        response = self.listing()
        obj = self.row(response)
        card = next(c for c in response.context['cl'].place_cards if c['pk'] == self.place.pk)
        self.assertEqual(card['readiness_score'], 100)
        self.assertFalse(card['is_ready'])
        self.assertTrue(card['publication_blockers'])
        self.assertNotIn('>Опубликовать</button>', self.model_admin.col_state(obj))
        self.assertNotIn(self.place.pk, [p.pk for p in self.listing(publication_state='ready').context['cl'].result_list])

    def test_pending_valid_point_is_ready_and_can_really_be_published(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft', is_active=False, lat=None, lng=None)
        self.place.refresh_from_db()
        publication.propose(actor=self.staff, target_type='place', target_id=self.place.pk,
            patch={'lat': 40.4, 'lng': 49.8}, schema_version=1,
            expected_version=self.place.content_version, submit=True, explicit_save=False)
        response = self.listing(publication_state='ready')
        card = next(c for c in response.context['cl'].place_cards if c['pk'] == self.place.pk)
        self.assertTrue(card['is_ready'])
        self.assertTrue(card['has_coordinates'])
        result = self.client.post(reverse('admin:catalog_place_toggle_publication', args=[self.place.pk]),
            {'intent': 'publish'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(result.status_code, 200, result.content)
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)
