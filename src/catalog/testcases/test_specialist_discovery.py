from html.parser import HTMLParser
from django.test import TestCase
from catalog.models import SiteSettings, SpecialistSpecialization

class DiscoveryParser(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.details = []; self.other = None; self.chips = []; self.subjects = []
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'details':
            self.details.append(attrs.get('id'))
            if attrs.get('id') == 'specialist-categories': self.other = attrs
        if tag == 'a':
            if attrs.get('data-spec-chip'): self.chips.append((attrs, list(self.details)))
            if 'subject=' in attrs.get('href', ''): self.subjects.append((attrs, list(self.details)))
    def handle_endtag(self, tag):
        if tag == 'details': self.details.pop()

class SpecialistDiscoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = SiteSettings.get_solo(); site.specialists_section_enabled = True; site.save()
        for code in ('tutor', 'math_tutor', 'psychologist'):
            SpecialistSpecialization.objects.get_or_create(code=code, defaults={'name': code, 'name_ru': code})

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

    def test_selected_other_direction_is_expanded_and_keeps_filter(self):
        response = self.client.get('/ru/specialists/', {'specialization':'psychologist', 'format':'online'})
        dom = DiscoveryParser(response.content.decode())
        self.assertIsNotNone(dom.other)
        self.assertIn('open', dom.other)
        active = next(a for a, _ in dom.chips if a['data-spec-chip'] == 'psychologist')
        self.assertEqual(active.get('aria-current'), 'true')
        self.assertIn('format=online', active['href'])
