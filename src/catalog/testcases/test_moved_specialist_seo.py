"""Localized public metadata for a former place that is now a person."""
from html import escape
from xml.etree import ElementTree

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from catalog.models import PlaceSpecialistMove, Specialist
from catalog.models.site import SiteSettings
from catalog.testcases.utils import create_quality_place
from catalog.testcases.test_parent_guide_images import ImageMarkup


@override_settings(PUBLIC_BASE_URL='https://kidsmap.az', LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class MovedSpecialistSeoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = Specialist.objects.create(
            name='Stored name', slug='person-qa', bio_ru='Биография',
            status='published', is_active=True, photo='specialists/photo-qa.webp',
            instagram='profile.qa', phone='+994501112233',
        )
        cls.copy = {
            'az': {'name': 'Ad', 'title': 'Azərbaycanca başlıq', 'description': 'Azərbaycanca mətn'},
            'ru': {'name': 'Имя', 'title': 'Заголовок', 'description': 'Описание'},
            'en': {'name': 'Name', 'title': 'English title', 'description': 'Quoted <tag> & </script> text'},
        }

        config = SiteSettings.get_solo()
        config.specialists_section_enabled = True
        config.save()

    def record_move(self):
        return PlaceSpecialistMove.objects.create(
            place=create_quality_place(status='draft', is_active=False),
            specialist=self.person, localized_seo=self.copy,
        )

    def page(self, language):
        with override(language):
            path = reverse('specialist_detail', args=[self.person.slug])
        return path, self.client.get(path)

    def test_moved_profile_has_one_localized_identity_across_html_social_and_schema(self):
        self.record_move()
        for lang, copy in self.copy.items():
            with self.subTest(lang=lang):
                path, response = self.page(lang)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertInHTML(f'<h1>{escape(copy["name"])}</h1>', html)
                self.assertInHTML(f'<title>{escape(copy["title"])}</title>', html)
                parsed = ImageMarkup(html)
                for key in ('og:title', 'twitter:title'):
                    self.assertEqual(parsed.meta[key], copy['title'])
                for key in ('description', 'og:description', 'twitter:description'):
                    self.assertEqual(parsed.meta[key], copy['description'])
                image = next(im for im in parsed.images if im.get('class') == 'sp-photo')
                self.assertEqual(image['alt'], copy['name'])
                for key in ('og:image', 'twitter:image'):
                    self.assertEqual(parsed.meta[key], 'https://kidsmap.az' + image['src'])
                    self.assertEqual(parsed.meta[key + ':alt'], copy['name'])
                canonical = 'https://kidsmap.az' + path
                self.assertEqual(parsed.meta['og:url'], canonical)
                self.assertInHTML(f'<link rel="canonical" href="{canonical}">', html)
                self.assertNotIn('noindex', parsed.meta['robots'])
                for altlang in (*self.copy, 'x-default'):
                    with override('az' if altlang == 'x-default' else altlang):
                        target = 'https://kidsmap.az' + reverse('specialist_detail', args=[self.person.slug])
                    self.assertInHTML(f'<link rel="alternate" hreflang="{altlang}" href="{target}">', html)
                profile, = [s for s in parsed.schemas if s.get('@type') == 'ProfilePage']
                self.assertEqual((profile['url'], profile['inLanguage']), (canonical, lang))
                self.assertEqual([s for s in parsed.schemas if s.get('@id') == canonical], [profile])
                person = profile['mainEntity']
                self.assertEqual((person['@type'], person['name']), ('Person', copy['name']))
                self.assertEqual(person['image'], parsed.meta['og:image'])
                self.assertTrue({'telephone', 'sameAs', 'email', 'review', 'aggregateRating'}.isdisjoint(person))
                trail, = [s for s in parsed.schemas if s.get('@type') == 'BreadcrumbList']
                urls = [item['item'] for item in trail['itemListElement']]
                with override(lang):
                    expected = ['https://kidsmap.az' + reverse(route) for route in ('home', 'specialist_list')]
                self.assertEqual(urls, expected + [canonical])
                self.assertEqual(trail['itemListElement'][-1]['name'], copy['name'])
                self.assertIn('aria-current="page"', html)

    def test_moved_office_uses_localized_structured_hours_and_falls_back_to_text(self):
        self.record_move()
        self.person.offers_office = True
        self.person.save(update_fields=['offers_office'])
        office = self.person.practice_locations.create(address='QA office', schedule='Obsolete hours')
        day = office.schedule_days.create(weekday='mon', is_closed=False)
        day.intervals.create(start_time='09:00', end_time='18:00')
        self.person.practice_locations.create(address='Second office', schedule='Legacy hours')
        for lang, monday in {'az': 'Bazar ertəsi', 'ru': 'Понедельник', 'en': 'Monday'}.items():
            with self.subTest(lang=lang):
                _, response = self.page(lang)
                self.assertContains(response, f'{monday}  09:00–18:00')
                self.assertNotContains(response, 'Obsolete hours')
                self.assertContains(response, 'Legacy hours')

    def test_sitemap_tracks_published_state_in_all_three_languages(self):
        self.record_move()
        destinations = set()
        for lang in self.copy:
            with override(lang):
                destinations.add('https://kidsmap.az' + reverse('specialist_detail', args=[self.person.slug]))

        def sitemap_targets():
            response = self.client.get('/sitemap.xml')
            self.assertEqual(response.status_code, 200)
            sitemap = ElementTree.fromstring(response.content)
            return {element.text for element in sitemap.findall('{*}url/{*}loc')}

        self.assertTrue(destinations.issubset(sitemap_targets()))
        self.person.is_active = False
        self.person.save(update_fields=['is_active'])
        self.assertTrue(destinations.isdisjoint(sitemap_targets()))
        for lang in self.copy:
            with self.subTest(lang=lang):
                self.assertEqual(self.page(lang)[1].status_code, 404)

    def test_regular_profile_is_unchanged(self):
        _, response = self.page('ru')
        self.assertContains(response, '<h1>Stored name</h1>', html=True)
        parsed = ImageMarkup(response.content.decode())
        self.assertFalse(any(s.get('@type') in {'ProfilePage', 'BreadcrumbList'} for s in parsed.schemas))
