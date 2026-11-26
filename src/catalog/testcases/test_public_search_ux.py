from html.parser import HTMLParser
from types import SimpleNamespace

from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import override

from catalog.models import Place
from catalog.services.localized_content import separate_bilingual_note


AZ = 'Fərdi konsultasiyalar uşaqlar, yeniyetmələr və böyüklər üçün keçirilir.'
RU = 'Индивидуальные консультации проводятся для детей, подростков и взрослых.'


class PublicNoteLanguageTests(SimpleTestCase):
    def test_separate_translations_render_in_the_requested_language(self):
        for lang, expected, absent in [('ru', RU, AZ), ('az', AZ, RU)]:
            with self.subTest(lang=lang), override(lang):
                place = Place(**{f'additional_info_{lang}': AZ + '\n' + RU})
                html = render_to_string('catalog/includes/pricing_notes.html', {'place': place})
                self.assertIn(expected, html)
                self.assertNotIn(absent, html)
                self.assertEqual(getattr(place, f'additional_info_{lang}'), AZ + '\n' + RU)

    def test_neutral_lines_stay_with_their_language_block(self):
        note = AZ + '\n60 dəqiqə\n' + RU + '\n80 AZN / 60 мин'
        self.assertEqual(separate_bilingual_note(note, 'ru'), RU + '\n80 AZN / 60 мин')
        self.assertEqual(separate_bilingual_note(note, 'az'), AZ + '\n60 dəqiqə')

    def test_single_language_brands_and_mixed_sentences_are_preserved(self):
        for note in [RU + ' KidsMap və Mappy.', 'KidsMap · 80 AZN', AZ, RU, AZ + ' ' + RU]:
            for lang in ['az', 'ru', 'en']:
                with self.subTest(note=note, lang=lang):
                    self.assertEqual(separate_bilingual_note(note, lang), note)

    def test_localized_fields_still_override_the_legacy_field_and_escape_html(self):
        with override('ru'):
            place = Place(additional_info=AZ + '\n' + RU, additional_info_ru='Русский текст <script>alert(1)</script>')
            html = render_to_string('catalog/includes/pricing_notes.html', {'place': place})
            self.assertIn('Русский текст &lt;script&gt;', html)
            self.assertNotIn(AZ, html)
            self.assertNotIn('<script>', html)


class SearchAndCompanionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'form' and 'data-home-map-filter-form' in attributes:
            self.elements.append('search')
        if 'data-mappy-helper' in attributes:
            self.elements.append('companion')


class PublicSearchMarkupTests(SimpleTestCase):
    def context(self, lang):
        request = RequestFactory().get('/' if lang == 'az' else f'/{lang}/')
        request.LANGUAGE_CODE = lang
        request.user = AnonymousUser()
        request.resolver_match = SimpleNamespace(url_name='home')
        return {'request': request, 'language': lang, 'hero_title': 'Test title', 'hero_subtitle': 'Test subtitle',
                'specialist_price_max': 500, 'hero_search_label': 'Search', 'hero_cta_text': 'Find', 'selected': dict.fromkeys(['q','age','age_from','age_to','price_from','price_to','specialization','subject','format','region','district','metro','sort','language','min_rating'], '')}

    def test_home_has_one_search_before_companion_with_and_without_map(self):
        for lang in ['az', 'ru', 'en']:
            for places in [[], [{'id': 1, 'name': 'QA place', 'lat': 40.4, 'lng': 49.85}]]:
                with self.subTest(lang=lang, populated=bool(places)), override(lang):
                    context = self.context(lang)
                    context['map_places'] = places
                    html = render_to_string('pages/home.html', context)
                    self.assertEqual(html.count('id="home-hero-search-input"'), 1)
                    parser = SearchAndCompanionParser()
                    parser.feed(html)
                    parser.close()
                    self.assertEqual(parser.elements.count('search'), 1)
                    self.assertLess(parser.elements.index('search'), parser.elements.index('companion'))
                    self.assertEqual('id="home-map-section"' in html, bool(places))

    def test_empty_catalog_class_uses_filtered_results(self):
        for count in [0, 1]:
            context = self.context('ru')
            context.update(page_obj=Paginator(list(range(count)), 12).get_page(1), specialists=[])
            html = render_to_string('catalog/specialist_list.html', context)
            self.assertEqual('km-specialists-catalog is-empty' in html, count == 0)
