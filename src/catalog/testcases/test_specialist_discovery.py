from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from catalog.models import SiteSettings, Specialist, SpecialistSpecialization

class DiscoveryParser(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.details = []; self.other = None; self.chips = []; self.subjects = []
        self.quick = []
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'details':
            self.details.append(attrs.get('id'))
            if attrs.get('id') == 'specialist-categories': self.other = attrs
        if tag == 'a':
            if 'km-subject-quick-link' in attrs.get('class', '').split():
                self.quick.append(attrs['href'])
            if attrs.get('data-spec-chip'): self.chips.append((attrs, list(self.details)))
            if 'subject=' in attrs.get('href', ''): self.subjects.append((attrs, list(self.details)))
    def handle_endtag(self, tag):
        if tag == 'details': self.details.pop()

class SpecialistDiscoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = SiteSettings.get_solo(); site.specialists_section_enabled = True; site.save()
        for code in ('tutor', 'math_tutor', 'psychologist', 'exam_prep_tutor', 'english_teacher'):
            SpecialistSpecialization.objects.get_or_create(code=code, defaults={'name': code, 'name_ru': code})

        cls.person('Visible mathematician', 'math_tutor')
        cls.person('Visible counsellor', 'psychologist')

    @classmethod
    def person(cls, name, *codes, **attributes):
        attributes.setdefault('status', Specialist.STATUS_PUBLISHED)
        profile = Specialist.objects.create(name=name, consultation_format='online', **attributes)
        profile.specializations.set(SpecialistSpecialization.objects.filter(code__in=codes))
        return profile

    def test_empty_catalog_keeps_filters_but_has_no_quick_navigation(self):
        Specialist.objects.update(status='draft')
        for path in ('/specialists/', '/ru/specialists/', '/en/specialists/'):
            with self.subTest(path=path):
                page = self.client.get(path)
                self.assertFalse(DiscoveryParser(page.content.decode()).quick)
                self.assertNotContains(page, 'class="km-subject-discovery"')
                self.assertContains(page, 'name="specialization"')
                self.assertContains(page, 'name="subject"')
        response = self.client.get('/specialists/', {'specialization': 'tutor', 'subject': 'math_tutor'})
        self.assertEqual(response.context['selected']['subject'], 'math_tutor')
        self.assertTrue(response.context['active_filter_chips'])
        self.assertContains(response, 'class="km-filter-head-reset"')

    def test_discovery_respects_context_and_the_filter_each_link_will_apply(self):
        math = SpecialistSpecialization.objects.get(code='math_tutor')
        math.name_en = 'SearchNeedle'
        math.save()
        self.person('Example coach', 'psychologist', 'math_tutor', language_en=True)
        self.person('SearchNeedle exam', 'exam_prep_tutor', 'english_teacher', language_en=True)
        self.person('SearchNeedle inactive', 'exam_prep_tutor', 'math_tutor', is_active=False, language_en=True)
        self.person('SearchNeedle draft', 'exam_prep_tutor', 'math_tutor', status='draft', language_en=True)
        path = '/en/specialists/'
        params = {'specialization': 'tutor', 'subject': 'math_tutor', 'language': 'en', 'q': 'SearchNeedle'}
        page = self.client.get(path, params)
        links = DiscoveryParser(page.content.decode()).quick
        queries = [parse_qs(urlsplit(href).query) for href in links]
        targets = {(q.get('specialization', [''])[0], q.get('subject', [''])[0]) for q in queries}
        self.assertIn(('tutor', 'english_teacher'), targets)
        self.assertIn(('tutor', 'math_tutor'), targets)
        self.assertIn(('tutor', ''), targets)
        self.assertIn(('psychologist', ''), targets)
        self.assertNotIn(('exam_prep_tutor', 'math_tutor'), targets)
        for href, query in zip(links, queries):
            with self.subTest(href=href):
                self.assertEqual(query['q'], ['SearchNeedle'])
                self.assertEqual(query['language'], ['en'])
                self.assertGreater(self.client.get(path + href).context['page_obj'].paginator.count, 0)

        self.person('Matching exam tutor', 'exam_prep_tutor', 'math_tutor', language_en=True)
        available = DiscoveryParser(self.client.get(path, params).content.decode())
        exam = next(attrs for attrs, _ in available.chips if attrs['data-spec-chip'] == 'exam_prep_tutor')
        self.assertEqual(parse_qs(urlsplit(exam['href']).query)['subject'], ['math_tutor'])
        self.assertEqual(self.client.get(path + exam['href']).context['page_obj'].paginator.count, 1)

    def test_other_directions_are_collapsed_but_subjects_remain_visible(self):
        for path in ('/specialists/', '/ru/specialists/', '/en/specialists/'):
            for query in ({}, {'specialization':'tutor', 'subject':'math_tutor'}):
                with self.subTest(path=path, query=query):
                    response = self.client.get(path, query)
                    self.assertEqual(response.status_code, 200)
                    dom = DiscoveryParser(response.content.decode())
                    self.assertIsNotNone(dom.other)
                    self.assertNotIn('open', dom.other)
                    self.assertTrue(dom.chips)
                    self.assertTrue(all('specialist-categories' in ancestors for _, ancestors in dom.chips))
                    self.assertTrue(any('subject=math_tutor' in a['href'] and not ancestors for a, ancestors in dom.subjects))

    def test_more_nonempty_directions_do_not_issue_more_queries(self):
        path = '/ru/specialists/'
        profile = Specialist.objects.get(name='Visible counsellor')
        self.client.get(path)
        with CaptureQueriesContext(connection) as baseline:
            before = DiscoveryParser(self.client.get(path).content.decode())
        profile.specializations.add(*SpecialistSpecialization.objects.filter(is_active=True))
        with CaptureQueriesContext(connection) as expanded:
            after = DiscoveryParser(self.client.get(path).content.decode())
        self.assertGreater(len(after.chips), len(before.chips))
        self.assertLessEqual(len(expanded), len(baseline))

    def test_selected_other_direction_is_expanded_and_keeps_filter(self):
        response = self.client.get('/ru/specialists/', {'specialization':'psychologist', 'format':'online'})
        dom = DiscoveryParser(response.content.decode())
        self.assertIsNotNone(dom.other)
        self.assertIn('open', dom.other)
        active = next(a for a, _ in dom.chips if a['data-spec-chip'] == 'psychologist')
        self.assertEqual(active.get('aria-current'), 'true')
        self.assertIn('format=online', active['href'])
