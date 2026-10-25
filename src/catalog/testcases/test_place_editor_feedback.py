"""A success receipt must come from a committed action and be consumed once."""
from types import SimpleNamespace
from unittest.mock import patch

from django.template import Context, Engine
from django.test import RequestFactory, SimpleTestCase

from catalog.services.place_editor_feedback import editor_result_context, queue_editor_result


class PlaceEditorFeedbackTests(SimpleTestCase):
    def request(self, method='get', path='/ru/account/places/'):
        request = getattr(RequestFactory(), method)(path)
        request.user = SimpleNamespace(is_authenticated=True, is_active=True)
        request.session = {}
        request.resolver_match = SimpleNamespace(url_name='owner_places_dashboard')
        return request

    def test_success_waits_for_commit_and_destination_consumes_it_once(self):
        request = self.request()
        callbacks = []
        with patch('catalog.services.place_editor_feedback.transaction.on_commit', side_effect=callbacks.append):
            queue_editor_result(request, action='moderation', message='Sent for review')
        self.assertEqual(request.session, {})
        self.assertEqual(len(callbacks), 1)
        callbacks[0]()
        self.assertEqual(editor_result_context(request)['place_editor_result'], {
            'action': 'moderation', 'outcome': 'success', 'message': 'Sent for review',
        })
        self.assertEqual(editor_result_context(request), {})

    def test_post_preview_and_anonymous_requests_do_not_consume_receipt(self):
        request = self.request()
        with patch('catalog.services.place_editor_feedback.transaction.on_commit', side_effect=lambda callback: callback()):
            queue_editor_result(request, action='draft', message='Draft saved')
        for method, preview, authenticated in [('POST', True, True), ('GET', True, True), ('GET', False, False)]:
            request.method = method
            request.site_preview = preview
            request.user.is_authenticated = authenticated
            self.assertEqual(editor_result_context(request), {})
        request.method = 'GET'
        request.site_preview = False
        request.user.is_authenticated = True
        self.assertEqual(editor_result_context(request)['place_editor_result']['action'], 'draft')

    def test_unrelated_public_pages_do_not_consume_and_admin_destination_does(self):
        request = self.request(path='/ru/catalog/')
        request.resolver_match.url_name = 'catalog'
        with patch('catalog.services.place_editor_feedback.transaction.on_commit', side_effect=lambda callback: callback()):
            queue_editor_result(request, action='save', message='Saved')
        self.assertEqual(editor_result_context(request), {})
        request.path = '/admin/catalog/place/'
        request.resolver_match.url_name = 'catalog_place_changelist'
        self.assertEqual(editor_result_context(request)['place_editor_result']['action'], 'save')

    def test_unconfirmed_or_invalid_actions_cannot_create_success_receipt(self):
        request = self.request()
        with self.assertRaises(ValueError):
            queue_editor_result(request, action='anything', message='Saved')
        self.assertEqual(request.session, {})

    def test_failed_native_post_discards_an_older_success_receipt(self):
        request = self.request()
        with patch('catalog.services.place_editor_feedback.transaction.on_commit', side_effect=lambda callback: callback()):
            queue_editor_result(request, action='draft', message='Earlier draft saved')
        request.method = 'POST'
        self.assertEqual(editor_result_context(request), {})
        request.method = 'GET'
        self.assertEqual(editor_result_context(request), {})

    def test_rendered_receipt_escapes_message_and_is_not_derived_from_query_string(self):
        from django.conf import settings
        engine = Engine(dirs=[str(settings.BASE_DIR / 'src/catalog/templates')])
        template = engine.get_template('catalog/includes/place_editor_result.html')
        request = self.request(path='/ru/account/places/?success=1')
        self.assertNotIn('data-km-editor-result', template.render(Context({'request': request})))
        html = template.render(Context({'place_editor_result': {
            'action': 'draft', 'outcome': 'success', 'message': '<script>bad()</script>',
        }}))
        self.assertIn('data-action="draft"', html)
        self.assertIn('data-outcome="success"', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>bad()', html)
