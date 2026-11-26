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
                story = event_story(text)
                self.assertEqual((story['paragraphs'], story['sources'], story['links']), ([text], [], []))

    def test_all_site_languages_and_fallback_keep_original_attribution(self):
        template = 'catalog/includes/event_story.html'
        for language, prefix in [('en', 'Programme and times from'), ('az', 'Tamaşa haqqında məlumat və cədvəl —')]:
            with self.subTest(language=language), override('ru'):
                story = f'Story <em>text</em>.\n\n{prefix} Theatre, https://example.org/show.'
                html = render_to_string(template, {'event': SimpleNamespace(**{'description_' + language: story}), 'language': 'ru'})
                self.assertIn(f'data-source-language="{language}"', html)
                self.assertIn('Story &lt;em&gt;text&lt;/em&gt;.', html)
                self.assertIn('href="https://example.org/show"', html)
                # the source is shown as a tidy link, not as a paragraph of raw text
                self.assertNotIn(prefix, html)
                self.assertNotIn('>https://example.org/show<', html)

    def test_gallery_credits_keep_author_and_license_separate_from_image_alt(self):
        cap = ('Auditorium, 2013 — Author · retouch: Editor · CC BY-SA 4.0 · '
               'https://commons.wikimedia.org/wiki/File:Hall.jpg · https://creativecommons.org/licenses/by-sa/4.0/')
        event = SimpleNamespace(gallery=SimpleNamespace(all=[SimpleNamespace(image=SimpleNamespace(url='/media/hall.jpg'), caption=cap)]))
        html = render_to_string('catalog/includes/event_gallery.html', {'event': event, 'language': 'en'})
        self.assertIn('Auditorium, 2013', html)
        self.assertIn('retouch: Editor', html)
        self.assertIn('href="https://creativecommons.org/licenses/by-sa/4.0/"', html)
        self.assertNotIn('alt="Auditorium, 2013 — Author', html)

    def test_reference_lines_become_one_link_per_site_and_captions_use_the_page_language(self):
        from catalog.templatetags.event_editorial import caption_for, event_caption, event_story

        story = event_story('Hekayə.\n\nTamaşa və cədvəl — Teatr — https://www.teatr.az/a · https://www.teatr.az/b\n\n'
                            'Afişa — Teatr. https://www.teatr.az/a')
        self.assertEqual(story['paragraphs'], ['Hekayə.'])
        self.assertEqual(story['links'], [{'url': 'https://www.teatr.az/a', 'label': 'teatr.az'}])
        cap = event_caption('Kukla Teatrı / Театр кукол / Puppet Theatre (2015) · Interfase · CC BY-SA 4.0 · '
                            'https://commons.wikimedia.org/wiki/File:P.JPG · https://creativecommons.org/licenses/by-sa/4.0/')
        self.assertEqual((cap['credit']['author'], cap['credit']['license']), ('Interfase', 'CC BY-SA 4.0'))
        self.assertEqual([caption_for(cap['title'], lang) for lang in ('az', 'ru', 'en')],
                         ['Kukla Teatrı', 'Театр кукол', 'Puppet Theatre'])

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

    def test_language_line_repeating_the_badge_is_dropped_and_duration_is_readable(self):
        import datetime
        from types import SimpleNamespace
        from catalog.templatetags.event_editorial import event_duration, event_story

        story = event_story('Tamaşanın dili — Azərbaycan dili.\n\nHekayə.')
        self.assertEqual(story['paragraphs'], ['Hekayə.'])
        start = datetime.datetime(2026, 11, 29, 12, 0, tzinfo=datetime.timezone.utc)
        event = SimpleNamespace(start_datetime=start, end_datetime=start + datetime.timedelta(minutes=90))
        self.assertEqual(event_duration(event, 'az'), '1 saat 30 dəq')
        self.assertEqual(event_duration(event, 'ru'), '1 ч 30 мин')
        event.end_datetime = start + datetime.timedelta(days=2)
        self.assertEqual(event_duration(event, 'az'), '')

    def test_event_reviews_cover_empty_long_anonymous_and_many(self):
        import datetime
        from types import SimpleNamespace as N

        def review(i, rating, text, anon=False):
            rev = N(rating=rating, text=text, is_anonymous=anon, contains_profanity=False,
                    created_at=datetime.datetime(2026, 11, 20, tzinfo=datetime.timezone.utc))
            return N(pk=i, author_name_i18n='Anonim' if anon else f'User {i}', current_revision=rev)

        event = N(pk=7, has_ended=False)
        empty = render_to_string('catalog/includes/event_reviews.html', {
            'event': event, 'language': 'az', 'event_reviews': [], 'event_rating': {'count': 0, 'average': 0}})
        self.assertIn('Hələ rəy yoxdur', empty)
        self.assertIn('#write-review', empty)

        reviews = [review(1, 5, 'Uzun ' * 100), review(2, 4, 'Qısa', anon=True)] + [review(i, 3, 'ok') for i in range(3, 7)]
        html = render_to_string('catalog/includes/event_reviews.html', {
            'event': event, 'language': 'az', 'event_reviews': reviews, 'event_rating': {'count': 6, 'average': 3.5}})
        self.assertEqual(html.count('class="km-rv"'), 4)          # four here, the rest on the reviews page
        self.assertIn('Bütün 6 rəy', html)
        self.assertIn('Davamını oxu', html)                       # long text folds
        self.assertIn('km-rv__avatar--anon', html)
        self.assertIn('Qiymət: 5 / 5', html)                      # the number is visible, not only stars
