from urllib.parse import parse_qs, urlsplit

from django.test import TestCase

from catalog.models import District, Region, SiteSettings, Specialist, SpecialistPracticeLocation


class SpecialistFormatDiscoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        cls.city = Region.objects.create(key="format-city", name_ru="Город")
        cls.north = District.objects.create(key="format-north", name_ru="Север", region=cls.city)
        cls.south = District.objects.create(key="format-south", name_ru="Юг", region=cls.city)

    def test_catalog_offers_three_independent_formats(self):
        page = self.client.get('/ru/specialists/')
        for code in ('online', 'office', 'visit'):
            self.assertContains(page, f'type="checkbox" name="format" value="{code}"')

    def specialist(self, name, **fields):
        return Specialist.objects.create(name=name, status='published', is_active=True, **fields)

    def test_office_and_visit_have_independent_districts_and_citywide_counts_once(self):
        mixed = self.specialist('Mixed', offers_office=True, offers_visits=True, visit_region=self.city)
        mixed.visit_districts.add(self.south)
        SpecialistPracticeLocation.objects.create(specialist=mixed, region=self.city, district=self.north, address='Office')
        citywide = self.specialist('Citywide', offers_visits=True, visit_region=self.city, visit_citywide=True)
        online = self.specialist('Remote', offers_online=True)
        path = '/ru/specialists/'

        def ids(page):
            return {item.pk for item in page.context['page_obj']}

        params = {'format': 'visit', 'district': self.north.pk}
        self.assertEqual(ids(self.client.get(path, params)), {citywide.pk})
        params['district'] = self.south.pk
        page = self.client.get(path, params)
        self.assertEqual(ids(page), {citywide.pk, mixed.pk})
        counts = {item['value']: item['count'] for item in page.context['filter_options'].districts}
        self.assertEqual((counts[self.north.pk], counts[self.south.pk]), (1, 2))
        params.update(format='office', district=self.north.pk)
        self.assertEqual(ids(self.client.get(path, params)), {mixed.pk})
        params.update(format=['online','visit'], district=self.north.pk)
        page = self.client.get(path, params)
        self.assertEqual(ids(page), {citywide.pk, online.pk})
        self.assertContains(page, 'По вашему запросу подходит онлайн')
        chips = {chip['label']: parse_qs(urlsplit(chip['remove_url']).query)
                 for chip in page.context['active_filter_chips']}
        self.assertEqual(chips['Онлайн']['format'], ['visit'])
        self.assertEqual(chips['Выезд к семье']['format'], ['online'])
        self.assertEqual(ids(self.client.get(path, {'format':'offline'})), {citywide.pk, mixed.pk})

    def test_visit_only_hides_stale_office_data_including_map_payload(self):
        person = self.specialist('Visiting specialist', offers_visits=True, visit_region=self.city)
        person.visit_districts.add(self.south)
        SpecialistPracticeLocation.objects.create(specialist=person, region=self.city, address='StalePrivateAddress',
                                                  lat=40.3, lng=49.4, is_active=True)
        for prefix, label in (('/ru', 'Выезд к семье'), ('/en', 'Home visits'), ('', 'Ailənin ünvanında')):
            page = self.client.get(prefix + '/specialists/' + person.slug + '/')
            self.assertContains(page, label)
            self.assertContains(page, 'Юг')
            self.assertNotContains(page, 'StalePrivateAddress')
            self.assertEqual(page.context['specialist_map_locations'], [])

    def test_full_format_labels_match_home_catalog_and_profile_in_all_locales(self):
        from catalog.controllers.home_controller import HomeController

        person = self.specialist('Three formats', offers_online=True, offers_office=True, offers_visits=True,
                                 visit_citywide=True, visit_region=self.city, photo='public/example.jpg')
        SpecialistPracticeLocation.objects.create(specialist=person, region=self.city, district=self.south, address='Venue')
        cases = [
            ('ru', '/ru', 'Онлайн · У специалиста · Выезд к семье'),
            ('az', '', 'Onlayn · Mütəxəssisin qəbul yerində · Ailənin ünvanında'),
            ('en', '/en', 'Online · At the specialist’s location · Home visits'),
        ]
        for language, prefix, label in cases:
            with self.subTest(language=language):
                self.assertEqual(HomeController._specialists_block(language)['people'][0]['format_label'], label)
                self.assertContains(self.client.get(prefix + '/specialists/'), label)
                self.assertContains(self.client.get(prefix + '/specialists/' + person.slug + '/'), label)

    def test_legacy_in_person_stays_in_broad_filter_only_until_an_office_is_known(self):
        person = self.specialist('Original profile', consultation_format='both')
        for code, appears in (('offline', True), ('online', True), ('office', False), ('visit', False)):
            page = self.client.get('/ru/specialists/', {'format': code})
            self.assertEqual(person.pk in {item.pk for item in page.context['page_obj']}, appears)
        page = self.client.get('/ru/specialists/' + person.slug + '/')
        self.assertContains(page, 'Очно, место уточняется')
        self.assertNotContains(page, 'id="practice-locations"')
