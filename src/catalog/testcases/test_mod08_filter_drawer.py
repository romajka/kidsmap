"""Exercise actual rendered filter choices and their resulting admin queues."""
from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import urlsplit

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, Event, Place, Specialist, SpecialistSpecialization
from catalog.templatetags.admin_dashboard_tags import get_active_filter_chips


class DrawerControls(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.selects = {}
        self.labels = {}
        self.current = self.option = self.label = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'label' and attrs.get('for', '').startswith('km-drawer-select-'):
            self.label = attrs['for']
            self.labels[self.label] = ''
        if tag == 'select' and 'data-filter-select' in attrs:
            self.current = {'id': attrs.get('id'), 'options': []}
            self.selects[attrs['data-field']] = self.current
        if tag == 'option' and self.current is not None:
            self.option = {'url': attrs['value'], 'selected': 'selected' in attrs, 'text': ''}
            self.current['options'].append(self.option)

    def handle_data(self, data):
        if self.label is not None:
            self.labels[self.label] += data
        if self.option is not None:
            self.option['text'] += data

    def handle_endtag(self, tag):
        if tag == 'label':
            self.label = None
        if tag == 'option':
            self.option = None
        if tag == 'select':
            self.current = None


class FilterDrawerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_superuser('drawer-admin', 'drawer@example.invalid', 'synthetic')
        cls.other = get_user_model().objects.create_user('drawer-owner')
        cls.categories = [Category.objects.create(code='DRAW' + str(i), name='Drawer ' + str(i),
            name_ru='Категория ' + str(i), name_az='Kateqoriya ' + str(i), name_en='Category ' + str(i)) for i in range(2)]
        cls.directions = [SpecialistSpecialization.objects.create(code='drawer-' + str(i), name='Drawer ' + str(i),
            name_ru='Направление ' + str(i), name_az='İstiqamət ' + str(i), name_en='Direction ' + str(i)) for i in range(2)]
        cls.events, cls.specialists = [], []
        for i, status in enumerate(('published', 'pending', 'draft')):
            name = 'DRAWERQA ' + str(i)
            event = Event.objects.create(name=name, name_ru=name, name_az=name, name_en=name,
                category=cls.categories[i % 2], status=status, owner=cls.actor if i != 1 else cls.other,
                start_datetime=timezone.now() + timedelta(days=(0, 3, 35)[i]))
            specialist = Specialist.objects.create(name=name, status=status, is_active=i != 1,
                consultation_format=('online', 'offline', 'both')[i])
            specialist.specializations.add(cls.directions[i % 2])
            cls.events.append(event.pk)
            cls.specialists.append(specialist.pk)
        Place.objects.create(name='DRAWERQA Place', name_ru='DRAWERQA Place', name_az='DRAWERQA Place',
            name_en='DRAWERQA Place', category=cls.categories[0], created_by=cls.actor, status='published')

    def setUp(self):
        self.client.force_login(self.actor)

    def page(self, model, query='q=DRAWERQA&sort=name_asc', lang='ru'):
        self.client.cookies['django_language'] = lang
        path = ('' if lang == 'az' else '/' + lang) + '/admin/catalog/' + model._meta.model_name + '/'
        response = self.client.get(path + '?' + query)
        self.assertEqual(response.status_code, 200, getattr(response, 'url', ''))
        return response

    def choose(self, response, field, parameter, value):
        controls = DrawerControls(response.content.decode()).selects
        self.assertIn(field, controls, 'Applicable filter missing from rendered drawer')
        option = next(o for o in controls[field]['options']
            if QueryDict(urlsplit(o['url']).query).get(parameter) == str(value))
        return self.page(response.context['cl'].model, urlsplit(option['url']).query)

    def assert_ids(self, response, expected):
        self.assertEqual(list(response.context['cl'].result_list.values_list('pk', flat=True)), expected)
        self.assertEqual(response.context['cl'].result_count, len(expected))

    def test_applicable_controls_order_labels_and_options_all_locales(self):
        for model in (Event, Specialist):
            for lang in ('ru', 'az', 'en'):
                with self.subTest(model=model.__name__, lang=lang):
                    response = self.page(model, lang=lang)
                    parsed = DrawerControls(response.content.decode())
                    expected = (['category', 'status', 'start_datetime', 'owner'] if model is Event
                        else ['status', 'is_active', 'consultation_format', 'specializations'])
                    self.assertEqual(list(parsed.selects), expected)
                    self.assertEqual(len(set(c['id'] for c in parsed.selects.values())), 4)
                    for spec in response.context['cl'].filter_specs:
                        field = getattr(spec, 'field_path', None) or getattr(spec, 'parameter_name', None)
                        if field not in expected:
                            continue
                        control = parsed.selects[field]
                        self.assertEqual(parsed.labels[control['id']], str(spec.title))
                        self.assertEqual(control['options'], [{'url': o['query_string'], 'selected': bool(o['selected']),
                            'text': str(o['display'])} for o in spec.choices(response.context['cl'])])
                    status = parsed.selects['status']['options']
                    self.assertIn({'ru': 'Опубликовано', 'az': 'Dərc olunub', 'en': 'Published'}[lang], [o['text'] for o in status])
                    self.assertNotContains(response, 'km-filter-chips-section')

    def test_event_multiple_rendered_choices_preserve_search_sort_and_zero_results(self):
        response = self.choose(self.page(Event), 'category', 'category__code__exact', self.categories[0].pk)
        self.assert_ids(response, [self.events[0], self.events[2]])
        response = self.choose(response, 'status', 'status__exact', 'published')
        self.assert_ids(response, self.events[:1])
        response = self.choose(response, 'owner', 'owner__id__exact', self.actor.pk)
        self.assert_ids(response, self.events[:1])
        date = DrawerControls(response.content.decode()).selects['start_datetime']['options'][1]
        query = urlsplit(date['url']).query
        self.assertIn('start_datetime__gte', QueryDict(query))
        self.assertIn('start_datetime__lt', QueryDict(query))
        response = self.page(Event, query)
        self.assert_ids(response, self.events[:1])
        self.assertEqual(response.context['cl'].params['q'], 'DRAWERQA')
        self.assertEqual(response.context['cl'].params['sort'], 'name_asc')
        response = self.choose(response, 'owner', 'owner__id__exact', self.other.pk)
        self.assert_ids(response, [])

    def test_specialist_choices_selected_state_and_zero_results(self):
        response = self.choose(self.page(Specialist), 'consultation_format', 'consultation_format__exact', 'online')
        response = self.choose(response, 'status', 'status__exact', 'published')
        response = self.choose(response, 'specializations', 'specializations__id__exact', self.directions[0].pk)
        response = self.choose(response, 'is_active', 'is_active__exact', '1')
        self.assert_ids(response, self.specialists[:1])
        for control in DrawerControls(response.content.decode()).selects.values():
            self.assertEqual(sum(o['selected'] for o in control['options']), 1)
            selected = next(o for o in control['options'] if o['selected'])
            self.assert_ids(self.page(Specialist, urlsplit(selected['url']).query), self.specialists[:1])
        response = self.choose(response, 'consultation_format', 'consultation_format__exact', 'offline')
        self.assert_ids(response, [])

    def test_status_chip_removes_only_status_and_reset_clears_query(self):
        for model, expected in ((Event, self.events), (Specialist, self.specialists)):
            with self.subTest(model=model.__name__):
                response = self.page(model, 'q=DRAWERQA&sort=name_asc&status__exact=published')
                chips = get_active_filter_chips(response.context['cl'])
                status = next((c for c in chips if c['param'] == 'status'), None)
                self.assertIsNotNone(status, 'Selected status must have an independently removable chip')
                query = urlsplit(status['remove_url']).query
                self.assertEqual(QueryDict(query)['q'], 'DRAWERQA')
                self.assertEqual(QueryDict(query)['sort'], 'name_asc')
                self.assert_ids(self.page(model, query), expected)
                reset = response.context['km_changelist_reset_url']
                self.assertFalse({'q', 'sort', 'status__exact'} & set(QueryDict(urlsplit(reset).query)))
                self.assert_ids(self.page(model, urlsplit(reset).query), list(reversed(expected)))

    def test_removing_category_chip_keeps_status_and_search(self):
        response = self.choose(self.page(Event, 'q=DRAWERQA&sort=name_asc&status__exact=published'),
            'category', 'category__code__exact', self.categories[0].pk)
        chip = next(c for c in get_active_filter_chips(response.context['cl']) if c['param'] == 'category')
        query = urlsplit(chip['remove_url']).query
        self.assertNotIn('category__code__exact', QueryDict(query))
        self.assertEqual(QueryDict(query)['status__exact'], 'published')
        self.assertEqual(QueryDict(query)['q'], 'DRAWERQA')
        self.assert_ids(self.page(Event, query), self.events[:1])

    def test_place_keeps_legacy_controls_quality_and_no_status_chip(self):
        response = self.page(Place, 'q=DRAWERQA&sort=name_asc&status__exact=published')
        cl = response.context['cl']
        legacy = [getattr(s, 'field_path', None) for s in cl.filter_specs
            if getattr(s, 'field_path', None) in {'created_by', 'created_date', 'category', 'district', 'is_verified'}]
        self.assertEqual(list(DrawerControls(response.content.decode()).selects), legacy)
        self.assertContains(response, 'km-filter-chips-section')
        self.assertNotIn('status', [c['param'] for c in get_active_filter_chips(cl)])
