"""The visible column controls must address the rendered, authorized cells."""
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from catalog.models import Event, Place, Specialist


class ColumnMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.menu = False
        self.label = None
        self.controls = []
        self.storage_key = None
        self.table = False
        self.section = None
        self.cell = None
        self.row = None
        self.headers = []
        self.body = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'details' and attrs.get('id') == 'km-columns-menu':
            self.menu = True
            self.storage_key = attrs.get('data-storage-key')
        if self.menu and tag == 'label':
            self.label = None
        if self.menu and tag == 'input' and 'data-toggle-col' in attrs:
            self.label = {'target': attrs['data-toggle-col'],
                          'index': int(attrs.get('data-column-index', '-1')),
                          'disabled': 'disabled' in attrs, 'label': ''}
            self.controls.append(self.label)
        if tag == 'table' and attrs.get('id') == 'result_list':
            self.table = True
        if self.table and tag in ('thead', 'tbody'):
            self.section = tag
        if self.table and tag == 'tr':
            self.row = []
            if self.section == 'tbody':
                self.body.append(self.row)
        if self.table and tag in ('th', 'td'):
            self.cell = {'classes': attrs.get('class', '').split(), 'text': ''}
            if self.section == 'thead':
                self.headers.append(self.cell)
            elif self.row is not None:
                self.row.append(self.cell)

    def handle_data(self, data):
        if self.label is not None:
            self.label['label'] += data
        if self.cell is not None:
            self.cell['text'] += data

    def handle_endtag(self, tag):
        if tag == 'label':
            self.label = None
        if tag == 'details':
            self.menu = False
        if tag in ('th', 'td'):
            self.cell = None
        if tag == 'table':
            self.table = False


class AdminQueueColumnTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser('columns-admin', 'columns@example.invalid', 'synthetic')
        cls.reader = get_user_model().objects.create_user('columns-reader', is_staff=True)
        cls.reader.user_permissions.add(Permission.objects.get(codename='view_specialist', content_type__app_label='catalog'))
        Place.objects.create(name='Columns Place', name_ru='Columns Place', name_az='Columns Place', name_en='Columns Place', category_id='EDU', status='draft')
        Place.objects.create(name='Columns Deleted', category_id='EDU', status='draft', deleted_at=timezone.now(), deleted_by=cls.admin)
        Event.objects.create(name='Columns Event', category_id='EDU', status='draft')
        Specialist.objects.create(name='Columns Specialist', status='draft')

    def setUp(self):
        self.client.force_login(self.admin)

    def page(self, model, lang='ru', params=None):
        prefix = '' if lang == 'az' else '/' + lang
        response = self.client.get(prefix + '/admin/catalog/' + model._meta.model_name + '/', params or {})
        self.assertEqual(response.status_code, 200)
        return ColumnMarkup(response.content.decode())

    def assert_controls_match_real_cells(self, markup):
        self.assertTrue(markup.controls)
        self.assertTrue(markup.body)
        self.assertTrue(markup.controls[0]['disabled'])
        self.assertEqual(sum(c['disabled'] for c in markup.controls), 1)
        targets = [c['target'] for c in markup.controls]
        self.assertEqual(len(targets), len(set(targets)))
        for excluded in ('column-action_checkbox', 'column-row_actions', 'column-col_actions'):
            self.assertNotIn(excluded, targets)
        for control in markup.controls:
            with self.subTest(target=control['target']):
                index = control['index']
                self.assertGreaterEqual(index, 0)
                self.assertLess(index, len(markup.headers))
                label = ' '.join(control['label'].split()).casefold()
                header = ' '.join(markup.headers[index]['text'].split()).casefold()
                self.assertTrue(label)
                self.assertIn(label, header)
                for row in markup.body:
                    self.assertIn(control['target'].replace('column-', 'field-', 1), row[index]['classes'])

    def test_every_control_addresses_actual_header_and_cells_in_all_locales(self):
        for model in (Place, Event, Specialist):
            for lang in ('ru', 'az', 'en'):
                with self.subTest(model=model.__name__, lang=lang):
                    self.assert_controls_match_real_cells(self.page(model, lang))

    def test_trash_controls_address_deleted_date_instead_of_missing_updated_column(self):
        for lang in ('ru', 'az', 'en'):
            with self.subTest(lang=lang):
                markup = self.page(Place, lang, {'deleted_state': 'deleted'})
                self.assert_controls_match_real_cells(markup)
                targets = [c['target'] for c in markup.controls]
                self.assertIn('column-deleted_at_display', targets)
                self.assertNotIn('column-col_updated', targets)

    def test_ordinary_specialist_reader_never_gets_private_column_control(self):
        self.assertIn('column-documents_count', [c['target'] for c in self.page(Specialist).controls])
        self.client.force_login(self.reader)
        for lang in ('ru', 'az', 'en'):
            with self.subTest(lang=lang):
                markup = self.page(Specialist, lang)
                self.assert_controls_match_real_cells(markup)
                self.assertNotIn('column-documents_count', [c['target'] for c in markup.controls])

    def test_storage_does_not_transfer_choices_between_queues_and_retains_place_key(self):
        self.assertEqual(self.page(Place).storage_key, 'km_hidden_columns')
        self.assertEqual(self.page(Event).storage_key, 'km_hidden_columns:catalog.event')
        self.assertEqual(self.page(Specialist).storage_key, 'km_hidden_columns:catalog.specialist')

    def test_empty_results_keep_permitted_options_and_anonymous_stays_out(self):
        for model in (Place, Event, Specialist):
            with self.subTest(model=model.__name__):
                markup = self.page(model, params={'q': 'no-synthetic-match-7654321'})
                self.assertFalse(markup.body)
                self.assertTrue(markup.controls[0]['disabled'])
                self.assertTrue(all(c['index'] >= 0 for c in markup.controls))
        self.client.logout()
        response = self.client.get('/ru/admin/catalog/specialist/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
