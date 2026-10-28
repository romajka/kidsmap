"""Consolidated notices keep human text and distinguish a moderation receipt."""
from django.contrib.messages import constants
from django.contrib.messages.storage.base import Message
from django.test import SimpleTestCase
from django.utils.html import format_html

from catalog.templatetags.admin_dashboard_tags import km_consolidated_admin_messages


class ConsolidatedAdminNoticeTests(SimpleTestCase):
    def message(self, text, level=constants.SUCCESS):
        return Message(level, text)

    def test_standalone_django_link_is_plain_readable_text(self):
        message = self.message(format_html('Место «<a href="{}">{}</a>» был успешно изменен.', '/admin/catalog/place/1/change/', 'A&B'))
        text = km_consolidated_admin_messages([message])[0]['text']
        self.assertEqual(text, 'Место «A&B» был успешно изменен.')

    def test_specific_pending_receipt_replaces_redundant_boilerplate(self):
        receipt = {'message': 'Изменения ожидают модерации.', 'next_url': '/admin/review/1/', 'next_label': 'Проверить'}
        messages = [self.message('Место был успешно изменен.'), self.message(receipt['message'])]
        rows = km_consolidated_admin_messages(messages, receipt)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['next_url'], receipt['next_url'])

    def test_warning_is_retained_beside_pending_receipt(self):
        receipt = {'message': 'Saved for review'}
        rows = km_consolidated_admin_messages([self.message('Missing photo', constants.WARNING)], receipt)
        self.assertEqual([row['tag'] for row in rows], ['success', 'warning'])

    def test_plain_text_is_escaped_when_template_renders_it(self):
        from django.template import Context, Template
        row = km_consolidated_admin_messages([self.message('&lt;script&gt;unsafe&lt;/script&gt;')])[0]
        html = Template('{{ text }}').render(Context(row))
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
