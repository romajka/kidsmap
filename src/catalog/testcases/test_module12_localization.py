from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone,translation
from django.utils.translation import gettext
from catalog.models import FunnelEvent
from catalog.testcases.utils import create_ready_place

AZ_LABELS={
 'дней':'gün',
 'Посещаемость':'Ziyarətlər',
 'Пока нет данных по посещаемости.':'Hələ ziyarət məlumatları yoxdur.',
 'События GA4':'GA4 hadisələri',
 'Активные пользователи':'Aktiv istifadəçilər',
 'Сессии':'Sessiyalar',
 'Просмотры страниц':'Səhifə baxışları',
 'GA4, последние 30 дней':'GA4, son 30 gün',
 'Обзор Google Analytics 4':'Google Analytics 4 icmalı',
 'Выбор периода':'Dövrün seçimi',
 'Топ событий за последние 30 дней':'Son 30 günün ən çox qeydə alınan hadisələri',
 'GA4 пока не вернул событийные данные.':'GA4 hələ hadisə məlumatlarını qaytarmayıb.',
 'Популярные страницы GA4':'GA4 üzrə populyar səhifələr',
 'Топ страниц за последние 30 дней':'Son 30 günün ən çox baxılan səhifələri',
 'GA4 пока не вернул данные по страницам.':'GA4 hələ səhifə məlumatlarını qaytarmayıb.',
}
class LocalizationTests(TestCase):
    def test_az_analytics_labels_have_specific_translations(self):
        with translation.override('az'):
            for source,want in AZ_LABELS.items():
                with self.subTest(source=source):self.assertEqual(gettext(source),want)
    @override_settings(OWNER_ANALYTICS_ENABLED=True,LOCAL_ANALYTICS_STORAGE_ENABLED=True)
    def test_owner_az_comparison_is_az_and_matches_real_delta(self):
        owner=get_user_model().objects.create_user('m12-locale-owner');place=create_ready_place(owner=owner,created_by=owner);now=timezone.now()
        for kind in ['place_view','phone_click']:
            for days in [40,2,1]:FunnelEvent.objects.create(place=place,subject_type='place',subject_id=place.pk,event_type=kind,schema_version=2,occurred_at=now-timedelta(days=days),visitor_key_hash='v1:fictional',session_key_hash='v1:fictional')
        self.client.force_login(owner);self.client.cookies['django_language']='az'
        with translation.override('az'):url=reverse('owner_place_analytics',args=[place.pk])
        result=self.client.get(url);self.assertEqual(result.status_code,200);self.assertEqual(result.context['metrics'].views_change_percent,100.0);self.assertContains(result,'əvvəlki dövrlə müqayisədə',count=2);self.assertNotContains(result,'к прошлому периоду');self.assertNotContains(result,'vs previous period')
