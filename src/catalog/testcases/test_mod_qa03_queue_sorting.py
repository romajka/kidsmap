"""Queue sorting must retain search, filters, pagination and read permissions."""
from datetime import timedelta
from urllib.parse import parse_qs

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone, translation

from catalog.models import Event, Specialist
from catalog.templatetags.admin_dashboard_tags import cl_sort_url


class QueueSortingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_superuser('sort-admin', 'sort@example.invalid', 'synthetic')
        cls.records = {}
        now = timezone.now()
        for model in (Event, Specialist):
            records = []
            for i, name in enumerate(('SORTQA Zebra', 'SORTQA Alpha', 'SORTQA Alpha', 'Outside')):
                values = {'name': name, 'status': 'published' if i < 3 else 'draft'}
                if model is Event:
                    values.update(category_id='EDU', start_datetime=now + timedelta(days=3))
                else:
                    values.update(consultation_format='online')
                obj = model.objects.create(**values)
                created = now + timedelta(days=(2, 1, 1, 4)[i])
                updated = now + timedelta(days=(1, 3, 3, 2)[i])
                model.objects.filter(pk=obj.pk).update(created_at=created, updated_at=updated)
                records.append({'pk': obj.pk, 'name': name, 'created': created, 'updated': updated})
            cls.records[model] = records

    def setUp(self):
        self.client.force_login(self.actor)

    def page(self, model, params=None, lang='ru'):
        prefix = '' if lang == 'az' else '/' + lang
        response = self.client.get(f'{prefix}/admin/catalog/{model._meta.model_name}/', params or {})
        self.assertEqual(response.status_code, 200, getattr(response, 'url', ''))
        return response

    def expected(self, model, key, records=None):
        field, direction = key.rsplit('_', 1)
        return [r['pk'] for r in sorted(records or self.records[model], key=lambda r: (r[field], r['pk']), reverse=direction == 'desc')]

    def test_six_orders_use_independent_dates_names_and_stable_ties(self):
        for model in self.records:
            for key in ('created_desc', 'created_asc', 'updated_desc', 'updated_asc', 'name_asc', 'name_desc'):
                with self.subTest(model=model.__name__, key=key):
                    response = self.page(model, {'sort': key})
                    self.assertEqual([o.pk for o in response.context['cl'].result_list], self.expected(model, key))

    def test_search_and_status_survive_sorting(self):
        for model in self.records:
            with self.subTest(model=model.__name__):
                response = self.page(model, {'sort': 'name_asc', 'q': 'SORTQA', 'status__exact': 'published'})
                cl = response.context['cl']
                self.assertEqual(cl.query, 'SORTQA')
                self.assertEqual([o.pk for o in cl.result_list], self.expected(model, 'name_asc', self.records[model][:3]))
                self.assertEqual(cl.params['status__exact'], 'published')

    def test_current_label_and_active_option_in_all_locales(self):
        labels = {'created_asc': 'Создано (старые)', 'name_desc': 'По названию (Я → А)', 'updated_desc': 'Обновлено (новые)'}
        for model in self.records:
            for lang in ('ru', 'az', 'en'):
                for key, message in labels.items():
                    with self.subTest(model=model.__name__, lang=lang, key=key):
                        response = self.page(model, {'sort': key}, lang)
                        self.assertEqual(response.context['km_current_sort'], key)
                        with translation.override(lang):
                            self.assertEqual(str(response.context['km_current_sort_label']), translation.gettext(message))
                        self.assertContains(response, 'km-sort-option is-active', count=1)

    def test_default_and_invalid_sort_fall_back_to_updated_desc(self):
        for model in self.records:
            for params in ({}, {'sort': 'not_a_field'}, {'sort': '-owner__password'}):
                with self.subTest(model=model.__name__, params=params):
                    response = self.page(model, params)
                    self.assertEqual([o.pk for o in response.context['cl'].result_list], self.expected(model, 'updated_desc'))
                    self.assertEqual(response.context['km_current_sort'], 'updated_desc')

    def test_pagination_preserves_sort_search_filter_and_new_sort_resets_page(self):
        for model in self.records:
            configured = admin.site._registry[model]
            original = configured.list_per_page
            configured.list_per_page = 2
            self.addCleanup(setattr, configured, 'list_per_page', original)
            with self.subTest(model=model.__name__):
                params = {'sort': 'created_asc', 'q': 'SORTQA', 'status__exact': 'published'}
                first = self.page(model, params)
                cl = first.context['cl']
                page_link = cl.get_query_string({'p': 2})
                query = parse_qs(page_link.lstrip('?'))
                self.assertEqual(query['sort'], ['created_asc'])
                self.assertEqual(query['q'], ['SORTQA'])
                second = self.page(model, {**params, 'p': 2})
                self.assertEqual([o.pk for o in second.context['cl'].result_list], self.expected(model, 'created_asc', self.records[model][:3])[2:])
                sort_query = parse_qs(cl_sort_url(second.context['cl'], 'name_asc').lstrip('?'))
                self.assertNotIn('p', sort_query)
                self.assertEqual(sort_query['q'], ['SORTQA'])
                self.assertEqual(sort_query['status__exact'], ['published'])

    def test_view_permissions_private_columns_and_domain_data_unchanged(self):
        before = {model: list(model.objects.order_by('pk').values()) for model in self.records}
        viewer = get_user_model().objects.create_user('sort-viewer', is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_event'))
        self.client.force_login(viewer)
        self.page(Event, {'sort': 'created_asc'})
        self.assertEqual(self.client.get('/ru/admin/catalog/specialist/', {'sort': 'created_asc'}).status_code, 403)
        viewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='view_specialist'))
        self.assertNotContains(self.page(Specialist, {'sort': 'name_asc'}), 'column-documents_count')
        self.assertEqual(before, {model: list(model.objects.order_by('pk').values()) for model in self.records})
