"""Only a confirmed moderation submission receives Mappy success decoration."""
from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, SimpleTestCase, TestCase
from catalog import views


class MappySubmissionTests(TestCase):
    def request(self):
        request = RequestFactory().post('/owner/places/1/submit-review/')
        request.user = SimpleNamespace(is_authenticated=True, username='qa-preview', first_name='QA', get_full_name='QA Preview', email='')
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_confirmed_submission_gets_structured_tag_and_original_message(self):
        request = self.request()
        with patch.object(type(views.owner_places_controller), 'submit_for_moderation', return_value=SimpleNamespace(ok=True, message='Sent for review')):
            response = views.owner_place_submit_review(request, 1)
        self.assertEqual(response.status_code, 302)
        notification = list(get_messages(request))[0]
        self.assertEqual(str(notification), 'Sent for review')
        self.assertIn('mappy-submitted', notification.tags.split())

    def test_failed_submission_never_gets_success_tag(self):
        request = self.request()
        with patch.object(type(views.owner_places_controller), 'submit_for_moderation', return_value=SimpleNamespace(ok=False, message='Check required fields')):
            views.owner_place_submit_review(request, 1)
        notification = list(get_messages(request))[0]
        self.assertNotIn('mappy-submitted', notification.tags.split())
        self.assertEqual(str(notification), 'Check required fields')

    def test_success_artwork_renders_only_for_confirmed_submission_tag(self):
        from django.contrib.messages import SUCCESS, ERROR
        from django.contrib.messages.storage.base import Message
        from django.template.loader import get_template
        request = self.request()
        request.resolver_match = SimpleNamespace(url_name='owner_places_dashboard')
        request.LANGUAGE_CODE = 'ru'
        for tag, level in [('mappy-submitted', SUCCESS), ('', SUCCESS), ('', ERROR)]:
            with self.subTest(tag=tag, level=level):
                html = get_template('base.html').render({
                    'request': request,
                    'messages': [Message(level, 'Original result', extra_tags=tag)],
                })
                self.assertEqual('mappy-success-image' in html, bool(tag))
                self.assertIn('Original result', html)
                if tag:
                    self.assertIn('flash-success mappy-submission', html)
