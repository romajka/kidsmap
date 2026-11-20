from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils.translation import override


class EventEditorialPresentationTests(SimpleTestCase):
    def test_photo_credit_and_schedule_are_linked_without_absorbing_other_paragraphs(self):
        from catalog.templatetags.event_editorial import event_story

        narrative = 'Сюжет с упоминанием https://commons.wikimedia.org/ и <img>.'
        source = 'Источник расписания — Театр, https://example.org/afisha. Билеты — iTicket.az.'
        credit = ('На обложке здание. Фото — Автор · CC BY 4.0 · '
                  'https://commons.wikimedia.org/wiki/File:Hall_(2013).jpg · '
                  'https://creativecommons.org/licenses/by/4.0/')
        story = event_story('\r\n\r\n'.join([narrative, source, credit]))
        self.assertEqual(story['paragraphs'], [narrative])
        self.assertEqual([p['url'] for p in story['sources'][0] if 'url' in p], ['https://example.org/afisha'])
        self.assertEqual([p['url'] for p in story['sources'][1] if 'url' in p], [
            'https://commons.wikimedia.org/wiki/File:Hall_(2013).jpg',
            'https://creativecommons.org/licenses/by/4.0/',
        ])

    def test_unrecognized_or_malformed_source_remains_plain_text(self):
        from catalog.templatetags.event_editorial import event_story

        for text in ['Источник расписания — подробности в зале.',
                     'Источник расписания — https://theatre.az@evil.example/path.',
                     'Some unrelated text and https://creativecommons.org/licenses/by/4.0/']:
            with self.subTest(text=text):
                self.assertEqual(event_story(text), {'paragraphs': [text], 'sources': []})

    def test_all_site_languages_and_fallback_keep_original_attribution(self):
        template = 'catalog/includes/event_story.html'
        for language, prefix in [('en', 'Programme and times from'), ('az', 'Tamaşa haqqında məlumat və cədvəl —')]:
            with self.subTest(language=language), override('ru'):
                story = f'Story <em>text</em>.\n\n{prefix} Theatre, https://example.org/show.'
                html = render_to_string(template, {'event': SimpleNamespace(**{'description_' + language: story}), 'language': 'ru'})
                self.assertIn(f'data-source-language="{language}"', html)
                self.assertIn('Story &lt;em&gt;text&lt;/em&gt;.', html)
                self.assertIn('href="https://example.org/show"', html)
                self.assertIn(prefix, html)

    def test_gallery_credits_keep_author_and_license_separate_from_image_alt(self):
        cap = ('Auditorium, 2013 — Author · retouch: Editor · CC BY-SA 4.0 · '
               'https://commons.wikimedia.org/wiki/File:Hall.jpg · https://creativecommons.org/licenses/by-sa/4.0/')
        event = SimpleNamespace(gallery=SimpleNamespace(all=[SimpleNamespace(image=SimpleNamespace(url='/media/hall.jpg'), caption=cap)]))
        html = render_to_string('catalog/includes/event_gallery.html', {'event': event, 'language': 'en'})
        self.assertIn('Auditorium, 2013', html)
        self.assertIn('retouch: Editor', html)
        self.assertIn('href="https://creativecommons.org/licenses/by-sa/4.0/"', html)
        self.assertNotIn('alt="Auditorium, 2013 — Author', html)

    def test_detail_ticket_action_is_limited_to_the_ticket_seller(self):
        template = 'catalog/includes/event_registration.html'
        for url, expected in [('https://iticket.az/events/kids/show', True),
                              ('https://iticket.az.other.example/show', False),
                              ('https://other.example/?redirect=https://iticket.az', False)]:
            event = SimpleNamespace(occurrence_state='scheduled', has_ended=False, registration={
                'url': url, 'kind': 'link', 'label': 'Записаться'})
            for detail in (True, False):
                rendered = render_to_string(template, {'event': event, 'event_detail_cta': detail, 'language': 'ru'})
                self.assertIn('data-event-registration-kind="link"', rendered)
                self.assertEqual('Билеты на iTicket' in rendered, expected and detail)
