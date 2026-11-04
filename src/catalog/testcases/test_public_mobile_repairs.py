"""Public navigation and presentation regressions from the mobile audit."""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import Activity, Category, Place, Specialist, SpecialistReview
from catalog.services.place_schedule import build_open_status
from catalog.forms import LoginForm


class PublicLoginLocaleTests(SimpleTestCase):
    def test_language_changes_do_not_mutate_other_login_forms(self):
        # Requests in different languages share a worker, but not their copy.
        with patch.object(LoginForm, 'error_messages', LoginForm.error_messages.copy()):
            with override('ru'):
                russian = LoginForm()
                russian_error = str(russian.error_messages['invalid_login'])
            with override('en'):
                english = LoginForm()
            with override('az'):
                azerbaijani = LoginForm()
            with override('ru'):
                self.assertEqual(str(russian.error_messages['invalid_login']), russian_error)
                self.assertEqual(str(LoginForm().error_messages['invalid_login']), russian_error)
            self.assertEqual(english.error_messages['invalid_login'], 'Incorrect email or password.')
            self.assertEqual(azerbaijani.error_messages['invalid_login'], 'E-poçt və ya şifrə yanlışdır.')


class PublicMobilePresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(code='mobile-repairs', name_az='Art')
        cls.place = Place.objects.create(name='Place', name_az='Place', category=cls.category, status='published', is_active=True)
        cls.activity = Activity.objects.create(place=cls.place, name_az='Class', status='published')
        cls.specialist = Specialist.objects.create(name='Specialist', status='published', is_active=True)
        cls.review = SpecialistReview.objects.create(specialist=cls.specialist, author_name='Public Parent', text='A useful review', rating=4, status='approved', is_approved=True)

    def test_faq_offers_real_contact_instead_of_fake_receipt(self):
        response = self.client.get('/ru/faq/')
        self.assertContains(response, 'mailto:')
        self.assertNotContains(response, 'handleFaqFormSubmit')
        self.assertNotContains(response, 'id="faq-form-success"')

    def test_specialist_review_author_is_visible(self):
        response = self.client.get(f'/ru/reviews/specialist/target/{self.specialist.pk}/')
        self.assertContains(response, '>Public Parent</h3>', html=False)

    def test_anonymous_specialist_review_does_not_expose_stored_name(self):
        SpecialistReview.objects.filter(pk=self.review.pk).update(is_anonymous=True, author_name='Private retained name')
        response = self.client.get(f'/ru/reviews/specialist/target/{self.specialist.pk}/')
        self.assertNotContains(response, 'Private retained name')
        self.assertContains(response, '>Аноним</h3>', html=False)

    def test_fractional_rating_has_proportional_fill(self):
        SpecialistReview.objects.create(specialist=self.specialist, author_name='Other Parent', text='Another useful review', rating=5, status='approved', is_approved=True)
        response = self.client.get(f'/ru/reviews/specialist/target/{self.specialist.pk}/')
        self.assertContains(response, '--rating-percent: 90%')

    def test_summary_stars_represent_the_numeric_score(self):
        response = self.client.get(f'/ru/reviews/specialist/target/{self.specialist.pk}/')
        self.assertContains(response, '--rating-percent: 80%')

    def test_guest_can_return_to_activity_and_sign_in_to_review(self):
        with override('ru'):
            url = reverse('typed_reviews', args=['activity', self.activity.pk])
            back = reverse('activity_detail', args=[self.activity.pk])
        response = self.client.get(url)
        self.assertContains(response, f'href="{back}"')
        self.assertContains(response, f'/ru/auth/login/?next={url}')
        self.assertNotContains(response, 'data-review-edit')

    def test_authenticated_activity_guest_prompt_is_replaced_by_composer(self):
        user = get_user_model().objects.create_user(username='review-parent')
        self.client.force_login(user)
        response = self.client.get(f'/ru/reviews/activity/target/{self.activity.pk}/')
        self.assertContains(response, 'data-review-edit')
        self.assertNotContains(response, 'data-review-guest')


class PublicScheduleMomentTests(SimpleTestCase):
    def status(self, hour, language='ru', closed=False):
        place = SimpleNamespace(schedule_mode='regular', has_structured_schedule=True)
        day = {'weekday': 'wed', 'is_closed': closed, 'is_24_hours': False,
               'intervals': [] if closed else [{'start': '15:00', 'end': '18:00'}]}
        with patch('catalog.services.place_schedule.serialize_place_schedule', return_value=[day]), \
             patch('catalog.services.place_schedule._today_weekday_key', return_value='wed'), \
             patch('catalog.services.place_schedule.timezone.localtime', return_value=datetime(2026, 11, 4, hour, tzinfo=ZoneInfo('Asia/Baku'))):
            return build_open_status(place, language)

    def test_before_and_after_hours_do_not_claim_closed_for_whole_day(self):
        for hour in (14, 19):
            self.assertEqual(self.status(hour)['label'], 'Сейчас закрыто')
        self.assertEqual(self.status(16)['label'], 'Сейчас открыто')

    def test_day_off_still_says_closed_today(self):
        self.assertEqual(self.status(16, closed=True)['label'], 'Сегодня закрыто')

    def test_current_time_labels_in_all_languages(self):
        self.assertEqual(self.status(14, 'en')['label'], 'Closed now')
        self.assertEqual(self.status(16, 'az')['label'], 'Hazırda açıqdır')
