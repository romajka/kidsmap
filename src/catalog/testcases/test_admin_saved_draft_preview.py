"""The saved-card preview must show the same working copy as its editor."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place, PlaceChangeAudit, VolunteerPlaceRevision
from catalog.services import publication
from catalog.testcases.utils import create_ready_place


class AdminSavedDraftPreviewTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser(
            'saved-preview-staff', 'saved-preview@example.invalid', 'fictional')
        self.place = create_ready_place(
            name_ru='Базовое название', description_ru='Базовое описание',
            extra_conditions_ru='Базовые условия', additional_info_ru='Базовая информация',
            status='draft', is_active=False)
        self.url = reverse('admin:catalog_place_site_preview', args=[self.place.pk])
        self.client.force_login(self.staff)
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'ru'

    def propose(self, **patch):
        return publication.propose(
            actor=self.staff, target_type='place', target_id=self.place.pk,
            patch=patch, schema_version=1, expected_version=self.place.content_version,
            submit=False, explicit_save=False)

    def test_saved_draft_and_rejected_copy_are_visible_in_every_language(self):
        revision = self.propose(**{
            **{f'name_{lang}': f'Saved {lang} name' for lang in ('az', 'ru', 'en')},
            **{f'extra_conditions_{lang}': f'Saved {lang} conditions' for lang in ('az', 'ru', 'en')},
        })
        for status in ('draft', 'rejected', 'pending'):
            VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status=status)
            for lang in ('az', 'ru', 'en'):
                with self.subTest(status=status, language=lang):
                    response = self.client.get(self.url, {'lang': lang})
                    self.assertContains(response, f'Saved {lang} name')
                    self.assertContains(response, f'Saved {lang} conditions')
                    self.assertTrue(response.context['site_preview_saved_candidate'])
        self.place.refresh_from_db()
        self.assertEqual(self.place.name_ru, 'Базовое название')
        self.assertFalse(self.place.is_active)

    def test_saved_prices_schedule_and_explicit_clear_replace_base_values(self):
        self.propose(
            extra_conditions_ru='', additional_info_ru='Новая информация черновика',
            pricing_plans=[{'product_type': 'visit', 'price': 47, 'quantity': 30,
                            'quantity_unit': 'minute', 'title_ru': 'Новый сеанс'}],
            structured_schedule=[{'weekday': 'mon', 'is_closed': False,
                                  'intervals': [{'start': '11:15', 'end': '19:45'}]}])
        response = self.client.get(self.url, {'lang': 'ru'})
        self.assertContains(response, 'Новая информация черновика')
        self.assertContains(response, 'Новый сеанс')
        self.assertContains(response, '11:15–19:45')
        self.assertNotContains(response, 'Базовые условия')
        self.assertNotContains(response, 'Базовая информация')
        self.assertEqual(response.context['place'].pricing_plans[0]['price'], '47.00')

    def test_preview_remains_read_only_and_private_with_saved_candidate(self):
        revision = self.propose(extra_conditions_ru='Сохранённые условия')
        before = (PlaceChangeAudit.objects.count(), revision.version,
                  self.place.content_version, self.place.status, self.place.is_active)
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
            response = self.client.get(self.url, {'lang': 'ru'})
        self.assertContains(response, 'Сохранённые условия')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('noindex', response['X-Robots-Tag'])
        self.assertFalse(response.context['request'].user.is_authenticated)
        self.place.refresh_from_db(); revision.refresh_from_db()
        self.assertEqual(before, (PlaceChangeAudit.objects.count(), revision.version,
                                 self.place.content_version, self.place.status, self.place.is_active))
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_approved_revision_does_not_override_current_card(self):
        revision = self.propose(name_ru='Старый кандидат')
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status='approved')
        response = self.client.get(self.url, {'lang': 'ru'})
        self.assertContains(response, 'Базовое название')
        self.assertNotContains(response, 'Старый кандидат')
        self.assertFalse(response.context.get('site_preview_saved_candidate', False))

    def test_saved_candidate_does_not_widen_object_permission(self):
        self.propose(name_ru='Приватный черновик')
        limited = get_user_model().objects.create_user('preview-limited', is_staff=True)
        self.client.force_login(limited)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, 'Приватный черновик', status_code=403)
