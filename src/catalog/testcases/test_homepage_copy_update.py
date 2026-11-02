from django.core.management import call_command
from django.test import TestCase
from catalog.models import SiteSettings


class HomepageCopyUpdateTests(TestCase):
    def test_replaces_known_legacy_copy_and_is_idempotent(self):
        site = SiteSettings.get_solo()
        site.home_title_ru = 'Найдите кружок для ребёнка в Азербайджане'
        site.home_subtitle_en = 'Sports, creativity, music, and education across all regions in one place.'
        site.save()
        call_command('update_homepage_copy', verbosity=0)
        site.refresh_from_db()
        self.assertEqual(site.home_title_ru, 'Места и занятия для детей в Азербайджане')
        self.assertEqual(site.home_subtitle_en, 'Clubs, classes, parks and entertainment — choose by age and area.')
        updated = site.updated_at
        call_command('update_homepage_copy', verbosity=0)
        site.refresh_from_db()
        self.assertEqual(site.updated_at, updated)

    def test_preserves_custom_copy_and_unrelated_settings(self):
        site = SiteSettings.get_solo()
        site.home_title_ru = 'Авторский заголовок редакции'
        site.home_subtitle_az = 'Redaktorun mətni'
        site.brand_name = 'Custom brand'
        site.save()
        call_command('update_homepage_copy', verbosity=0)
        site.refresh_from_db()
        self.assertEqual(site.home_title_ru, 'Авторский заголовок редакции')
        self.assertEqual(site.home_subtitle_az, 'Redaktorun mətni')
        self.assertEqual(site.brand_name, 'Custom brand')

    def test_fills_blank_locales_without_changing_custom_translation(self):
        site = SiteSettings.get_solo()
        site.home_title_ru = 'Custom'
        site.home_title_az = ''
        site.home_title_en = '  '
        site.save()
        call_command('update_homepage_copy', verbosity=0)
        site.refresh_from_db()
        self.assertEqual(site.home_title_ru, 'Custom')
        self.assertEqual(site.home_title_az, 'Azərbaycanda uşaqlar üçün məkanlar və məşğələlər')
        self.assertEqual(site.home_title_en, 'Places and activities for children in Azerbaijan')

    def test_empty_install_is_not_populated_by_update_command(self):
        SiteSettings.objects.all().delete()
        call_command('update_homepage_copy', verbosity=0)
        self.assertFalse(SiteSettings.objects.exists())
