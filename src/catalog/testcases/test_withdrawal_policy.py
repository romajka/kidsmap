"""Every Place withdrawal entry point must preserve candidate/version safety."""
import json
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db.models import F
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import translation

from catalog.models import Place, PlaceChangeAudit
from catalog.services import publication
from catalog.testcases.utils import create_ready_place
from catalog.views.owner import owner_places_controller


class WithdrawalPolicyTests(TestCase):
    paths = ('owner', 'toggle', 'quick', 'mark_draft', 'mark_inactive')

    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user('withdraw-owner')
        self.staff = users.objects.create_superuser('withdraw-staff', '', 'synthetic')
        self.client.force_login(self.staff)
        self.editor = admin.site._registry[Place]
        self.factory = RequestFactory()

    def place(self):
        return create_ready_place(owner=self.owner, created_by=self.owner, district='baku_nasimi')

    def request(self, data=None):
        request = self.factory.post('/admin/catalog/place/', data or {})
        request.user = self.staff
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def withdraw(self, path, place):
        if path == 'owner':
            return self.client.post(reverse('owner_place_draft', args=[place.pk]))
        if path == 'toggle':
            return self.client.post(reverse('admin:catalog_place_toggle_publication', args=[place.pk]),
                                    {'intent': 'unpublish'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        if path == 'quick':
            return self.editor.quick_action_view(self.request({'action': 'to_draft'}), place.pk)
        return getattr(self.editor, path)(self.request(), Place.objects.filter(pk=place.pk))

    def test_unresolved_candidates_block_every_withdrawal_path(self):
        # A direct status save would withdraw despite an outstanding candidate.
        for path in self.paths:
            for submit in (False, True):
                with self.subTest(path=path, submit=submit):
                    place = self.place()
                    revision = publication.propose(actor=self.owner, target_type='place', target_id=place.pk,
                        patch={'description_az': 'Pending withdrawal policy change.'}, schema_version=1,
                        expected_version=place.content_version, submit=submit, explicit_save=False)
                    before = place.content_version
                    self.withdraw(path, place)
                    place.refresh_from_db()
                    revision.refresh_from_db()
                    self.assertEqual((place.status, place.is_active, place.content_version),
                                     ('published', True, before))
                    self.assertEqual(revision.status, 'pending' if submit else 'draft')

    def test_successful_withdrawal_bumps_version_on_every_path(self):
        for path in self.paths:
            with self.subTest(path=path):
                place = self.place()
                before = place.content_version
                self.withdraw(path, place)
                place.refresh_from_db()
                self.assertEqual((place.status, place.is_active, place.content_version),
                                 ('draft', False, before + 1))

    def test_owner_route_returns_error_feedback_for_pending_candidate(self):
        place = self.place()
        publication.propose(actor=self.owner, target_type='place', target_id=place.pk,
            patch={'description_az': 'Pending withdrawal policy change.'}, schema_version=1,
            expected_version=place.content_version)
        response = self.withdraw('owner', place)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(any(message.level == 40 for message in get_messages(response.wsgi_request)))
        self.assertFalse(PlaceChangeAudit.objects.filter(place=place, field_name='status').exists())

    def test_owner_withdrawal_rejects_stale_loaded_version(self):
        place = self.place()
        Place.objects.filter(pk=place.pk).update(content_version=F('content_version') + 1)
        # Simulate a concurrent update after repository lookup, keeping real service/DB.
        with patch.object(owner_places_controller.owner_place_repository, 'get_managed_by_pk', return_value=place):
            result = owner_places_controller.set_publication_state(request=self.request(),
                                                                  place_id=place.pk, is_active=False)
        self.assertFalse(result.ok)
        place.refresh_from_db()
        self.assertTrue(place.is_public)

    def test_ordinary_owner_cannot_withdraw(self):
        place = self.place()
        self.client.force_login(self.owner)
        self.withdraw('owner', place)
        place.refresh_from_db()
        self.assertTrue(place.is_public)

    def test_get_cannot_withdraw(self):
        place = self.place()
        response = self.client.get(reverse('owner_place_draft', args=[place.pk]))
        self.assertEqual(response.status_code, 405)
        place.refresh_from_db()
        self.assertTrue(place.is_public)

    def test_bulk_withdrawal_skips_blocked_candidate_but_processes_other_card(self):
        for path in ('mark_draft', 'mark_inactive'):
            with self.subTest(path=path):
                blocked, ready = self.place(), self.place()
                publication.propose(actor=self.owner, target_type='place', target_id=blocked.pk,
                    patch={'description_az': 'Pending withdrawal policy change.'}, schema_version=1,
                    expected_version=blocked.content_version)
                request = self.request()
                getattr(self.editor, path)(request, Place.objects.filter(pk__in=[blocked.pk, ready.pk]))
                blocked.refresh_from_db()
                ready.refresh_from_db()
                self.assertTrue(blocked.is_public)
                self.assertFalse(ready.is_public)
                self.assertTrue(any(message.level == 30 for message in get_messages(request)))

    def test_conflict_feedback_uses_selected_language_instead_of_service_error(self):
        place = self.place()
        publication.propose(actor=self.owner, target_type='place', target_id=place.pk,
            patch={'description_az': 'Pending withdrawal policy change.'}, schema_version=1,
            expected_version=place.content_version)
        expected = {
            'ru': 'Состояние карточки изменилось. Обновите список и повторите действие.',
            'az': 'Kartın vəziyyəti dəyişib. Siyahını yeniləyin və əməliyyatı təkrarlayın.',
            'en': 'The place status changed. Refresh the list and try again.',
        }
        # Current main gives the owner an actionable candidate explanation;
        # legacy admin endpoints use localized conflict feedback. Test both
        # contracts without replacing either with a raw service exception.
        owner_expected = {
            'ru': 'Сначала одобрите или верните на доработку текущую заявку. Затем снимите карточку с публикации.',
            'az': 'Əvvəlcə cari müraciəti təsdiqləyin və ya düzəliş üçün geri qaytarın. Sonra kartı yayımdan çıxarın.',
            'en': 'First approve the current submission or return it for changes. Then unpublish the listing.',
        }
        for language, message in expected.items():
            with self.subTest(language=language), translation.override(language):
                result = owner_places_controller.set_publication_state(request=self.request(),
                                                                      place_id=place.pk, is_active=False)
                self.assertFalse(result.ok)
                self.assertEqual(str(result.message), owner_expected[language])
                for action, method in [('unpublish', self.editor.toggle_publication_view),
                                       ('to_draft', self.editor.quick_action_view)]:
                    request = self.request({'intent': action, 'action': action})
                    request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
                    response = method(request, place.pk)
                    self.assertEqual(response.status_code, 409)
                    self.assertEqual(json.loads(response.content)['message'], message)
