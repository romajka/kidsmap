"""Localized sitemap readers must batch fresh visibility/language enrichment."""
from types import SimpleNamespace
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from catalog.models import Activity, Place, Program, Organization
from catalog.sitemaps import ActivitySitemap
from catalog.testcases.utils import create_ready_place


class ActivitySitemapBatchTests(TestCase):
    def setUp(self):
        self.place=create_ready_place()

    def add_activities(self,start,stop):
        for index in range(start,stop):
            Activity.objects.create(place=self.place,status='published',
                name_az=f'Synthetic activity {index}',name_ru=f'Вымышленное занятие {index}',name_en=f'Synthetic activity {index}',
                description_az='Yalnız sintetik yoxlama məlumatları.',description_ru='Только вымышленные данные проверки.',description_en='Synthetic audit fixture only.')

    def urls(self,sitemap=None):
        return (sitemap or ActivitySitemap()).get_urls(site=SimpleNamespace(domain='testserver'),protocol='http')

    def test_query_budget_is_constant_as_localized_activities_grow(self):
        self.add_activities(0,5)
        self.urls()
        with CaptureQueriesContext(connection) as first:
            first_urls=self.urls()
        self.add_activities(5,25)
        self.urls()
        with CaptureQueriesContext(connection) as last:
            last_urls=self.urls()
        self.assertEqual(len(first_urls),15)
        self.assertEqual(len(last_urls),75)
        print(f'SITEMAP_QUERY_BUDGET first={len(first)} last={len(last)}')
        self.assertLessEqual(len(last),len(first)+2)

    def test_reusing_a_generator_does_not_retain_revoked_visibility(self):
        self.add_activities(0,1)
        sitemap=ActivitySitemap()
        self.assertEqual(len(self.urls(sitemap)),3)
        Place.objects.filter(pk=self.place.pk).update(status='draft')
        self.assertEqual(self.urls(sitemap),[])


class ActivityLanguageBatchContractTests(TestCase):
    def setUp(self):
        from catalog.testcases.test_task33_localization import LocalizationContractsTests
        LocalizationContractsTests.setUp(self)

    def assert_matches_canonical_reader(self):
        from catalog.services.public_languages import available_languages, public_activities_with_languages
        rows,languages = public_activities_with_languages()
        for row in rows:
            for obj in (row,row.place,row.program):
                if obj:
                    self.assertFalse(hasattr(obj,'_public_batch'))
            self.assertEqual(languages[row.pk],available_languages(Activity.objects.select_related('place','program').get(pk=row.pk)))
        return languages.get(self.activity.pk,[])

    def test_live_hidden_snapshot_and_stale_affiliation_use_the_canonical_language_rules(self):
        Program.objects.filter(pk=self.program.pk).update(name_ru='Музыка',description_ru='Музыкальные занятия')
        Activity.objects.filter(pk=self.activity.pk).update(supplement_ru='Местное дополнение',
            program_snapshot={'name_az':'Approved snapshot','description_az':'Approved historical description'})
        self.assertEqual(self.assert_matches_canonical_reader(),['az','ru'])
        Program.objects.filter(pk=self.program.pk).update(status='draft')
        self.assertEqual(self.assert_matches_canonical_reader(),['az'])
        Program.objects.filter(pk=self.program.pk).update(status='published')
        Organization.objects.filter(pk=self.org.pk).update(ownership_version=self.org.ownership_version+1)
        self.assertEqual(self.assert_matches_canonical_reader(),[])
        Activity.objects.filter(pk=self.activity.pk).update(program=None)
        self.assertEqual(self.assert_matches_canonical_reader(),['az'])
        Organization.objects.filter(pk=self.org.pk).update(status='draft')
        self.assertEqual(self.assert_matches_canonical_reader(),['az'])
