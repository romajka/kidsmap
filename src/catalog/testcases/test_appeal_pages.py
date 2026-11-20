"""A user and two moderators follow the authenticated appeal routes."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone, translation

from catalog.models import SiteReview


class AppealPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.author = users.create_user('appeal-page-author')
        cls.stranger = users.create_user('appeal-page-other')
        cls.first = users.create_user('original-moderator', is_staff=True)
        cls.second = users.create_user('next-moderator', is_staff=True)
        permission = Permission.objects.get(content_type__app_label='catalog', codename='change_sitereview')
        for user in (cls.first, cls.second):
            user.user_permissions.add(permission)
        cls.review = SiteReview.objects.create(
            user=cls.author, status='rejected', is_approved=False, text='First-hand experience',
            moderated_by=cls.first, moderated_at=timezone.now(), rejection_reason='Missing visit date',
        )

    def setUp(self):
        self.locale = translation.override('en')
        self.locale.__enter__()
        self.addCleanup(self.locale.__exit__, None, None, None)

    def submission_url(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('appeal_inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Missing visit date')
        return response.context['decisions'][0]['submit_url']

    def test_full_lifecycle_retains_source_and_delivers_result(self):
        from moderation_appeals.models import Appeal
        url = self.submission_url()
        data = {'explanation': 'I visited on Friday', 'evidence_url': 'https://example.org/ticket'}
        for _ in range(2):
            self.assertEqual(self.client.post(url, data).status_code, 302)
        appeal = Appeal.objects.get()
        self.assertNotContains(self.client.get(reverse('appeal_inbox')), 'original-moderator')
        self.client.force_login(self.second)
        detail = reverse('appeal_review', args=[appeal.pk])
        self.assertContains(self.client.get(reverse('appeal_queue')), 'First-hand experience')
        review = self.client.get(detail)
        self.assertContains(review, 'original-moderator')
        self.assertContains(review, data['explanation'])
        self.assertEqual(self.client.post(detail, {'action': 'claim'}).status_code, 302)
        self.assertEqual(self.client.post(detail, {'action': 'approve', 'reason': 'Visit date confirmed.'}).status_code, 302)
        self.client.force_login(self.author)
        self.assertContains(self.client.get(reverse('appeal_inbox')), 'Visit date confirmed.')
        self.assertContains(self.client.get(reverse('account_notifications')), reverse('appeal_inbox'))
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, 'rejected')
        self.assertFalse(self.review.is_approved)

    def test_forms_retain_input_validate_evidence_and_scope(self):
        url = self.submission_url()
        invalid = self.client.post(url, {'explanation': '   ', 'evidence_url': 'ftp://example.org/file'})
        self.assertEqual(invalid.status_code, 400)
        errors = invalid.context['decisions'][0]['form'].errors
        self.assertEqual(set(errors), {'explanation', 'evidence_url'})
        self.assertEqual(self.client.get(url).status_code, 405)
        denied = Client(enforce_csrf_checks=True)
        denied.force_login(self.author)
        self.assertEqual(denied.post(url, {'explanation': 'Details'}).status_code, 403)
        self.client.force_login(self.stranger)
        self.assertNotContains(self.client.get(reverse('appeal_inbox')), 'Missing visit date')
        self.assertEqual(self.client.post(url, {'explanation': 'Other'}).status_code, 404)

    def test_localized_private_routes_and_auth(self):
        for locale in ('az', 'ru', 'en'):
            with self.subTest(locale=locale), translation.override(locale):
                self.client.logout()
                path = reverse('appeal_inbox')
                self.assertEqual(self.client.get(path).status_code, 302)
                self.client.force_login(self.author)
                response = self.client.get(path)
                self.assertContains(response, 'Missing visit date')
                self.assertIn('no-store', response.headers['Cache-Control'])
                self.client.force_login(self.second)
                self.assertContains(self.client.get(reverse('appeal_queue')), 'class=')

    def test_staff_actions_are_scoped_and_require_a_written_decision(self):
        from moderation_appeals.models import Appeal
        self.client.post(self.submission_url(), {'explanation': 'My visit date is on the ticket.'})
        appeal = Appeal.objects.get()
        detail = reverse('appeal_review', args=[appeal.pk])
        self.client.force_login(self.first)
        self.assertEqual(self.client.post(detail, {'action': 'claim'}).status_code, 403)
        self.client.force_login(self.second)
        self.client.post(detail, {'action': 'claim'})
        invalid = self.client.post(detail, {'action': 'reject', 'reason': '   '})
        self.assertEqual(invalid.status_code, 400)
        self.assertContains(invalid, 'autofocus', status_code=400)
        appeal.refresh_from_db()
        self.assertEqual(appeal.status, 'second_review')
        self.assertEqual(self.client.post(detail, {'action': 'reject', 'reason': 'Date is unclear.'}).status_code, 302)
        self.assertNotContains(self.client.get(reverse('appeal_queue')), reverse('appeal_review', args=[appeal.pk]))
        self.assertContains(self.client.get(reverse('appeal_queue'), {'status': 'rejected'}), reverse('appeal_review', args=[appeal.pk]))

    def test_staff_routes_use_the_admin_host(self):
        self.client.force_login(self.second)
        with self.settings(ADMIN_HOST='admin.kidsmap.test', ALLOWED_HOSTS=['testserver', 'admin.kidsmap.test']):
            response = self.client.get(reverse('appeal_queue'))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, 'http://admin.kidsmap.test' + reverse('appeal_queue'))
            inbox = self.client.get(reverse('appeal_inbox'))
            self.assertEqual(inbox.status_code, 200)

    def test_two_recipients_share_status_but_only_appellant_sees_private_material(self):
        from catalog.models import Specialist
        from catalog.services import specialist_moderation
        from moderation_appeals.models import Appeal
        person = Specialist.objects.create(name='Shared profile', created_by=self.author,
                                           verified_person_user=self.stranger, status='rejected')
        specialist_moderation.notify_decision(person, 'rejected', 'Missing information', actor=self.first)
        self.client.force_login(self.author)
        response = self.client.get(reverse('appeal_inbox'))
        row = next(row for row in response.context['decisions'] if row['decision'].kind == 'specialist')
        url = row['submit_url']
        self.client.post(url, {'explanation': 'Private note', 'evidence_url': 'https://example.org/private'})
        self.client.force_login(self.stranger)
        response = self.client.get(reverse('appeal_inbox'))
        self.assertContains(response, 'Shared profile')
        self.assertNotContains(response, 'Private note')
        self.assertNotContains(response, 'https://example.org/private')
        self.assertNotContains(response, f'action="{url}"')
        self.assertEqual(self.client.post(url, {'explanation': 'A second appeal'}).status_code, 302)
        self.assertEqual(Appeal.objects.count(), 1)
