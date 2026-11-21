from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.test import TestCase
from django.utils import timezone

from catalog.testcases.specialist_document_fixtures import portrait_upload
from catalog.forms import OwnerSpecialistForm
from catalog.models import Specialist
from catalog.services.owner_specialist_use_cases import save_owner_specialist_profile
from catalog.services.specialist_proposal_drafts import (
    _revision_payload, proposal_forms, save_proposal,
)


class SpecialistTariffFormsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_user('tariff-author')

    def profile_data(self, **extra):
        data = QueryDict('', mutable=True)
        data.update({
            'name': 'Tariff example', 'bio_ru': 'Example', 'language_ru': 'on',
            'requested_specialization': 'Example area', 'session_formats': 'online',
            'phone': '+994501234567', 'locations-TOTAL_FORMS': '0',
            'locations-INITIAL_FORMS': '0', **extra,
        })
        return data

    def test_complete_package_cannot_replace_base_price_or_type(self):
        data = self.profile_data(package_period='month', package_amount='160', package_sessions='8')
        form = OwnerSpecialistForm(data, files={'photo': portrait_upload()}, actor=self.actor)
        self.assertEqual(set(form.errors), {'lesson_type', 'lesson_price'})

    def test_missing_duration_and_explicit_zero_are_valid_on_send(self):
        data = self.profile_data(lesson_type='individual', lesson_price='0')
        sent = save_proposal(actor=self.actor, draft_id=uuid4(), expected_version=0,
                             data=data, files={'photo': portrait_upload()}, submit=True)
        person = sent.submitted_specialist
        person.refresh_from_db()
        self.assertEqual(getattr(person, 'lesson_price', None), Decimal('0.00'))
        self.assertIsNone(person.duration_minutes)
        self.assertEqual(person.status, 'pending')

    def test_ordered_packages_survive_moderator_revision_snapshot(self):
        data = self.profile_data(lesson_type='pair', lesson_price='12.50')
        for name, values in {
            'package_period': ['month', '', 'package'],
            'package_amount': ['89.90', '', '51'],
            'package_sessions': ['8', '', '4'],
        }.items():
            data.setlist(name, values)
        sent = save_proposal(actor=self.actor, draft_id=uuid4(), expected_version=0,
                             data=data, files={'photo': portrait_upload()}, submit=True)
        person = sent.submitted_specialist
        expected = [{'period': 'month', 'amount': '89.90', 'sessions': 8},
                    {'period': 'package', 'amount': '51.00', 'sessions': 4}]
        self.assertEqual(getattr(person, 'pricing_packages', None), expected)
        form, _ = proposal_forms(actor=self.actor, payload=_revision_payload(person, 'other'))
        self.assertEqual([row['sessions'] for row in form.pricing_package_rows], ['8', '4'])
        self.assertEqual(form['lesson_price'].value(), '12.50')

    def test_unfinished_packages_reopen_in_draft_and_block_send(self):
        data = self.profile_data(lesson_type='group', lesson_price='20',
                                 package_period='month', package_amount='80', package_sessions='')
        key = uuid4()
        draft = save_proposal(actor=self.actor, draft_id=key, expected_version=0, data=data, files={})
        form, _ = proposal_forms(actor=self.actor, payload=draft.payload)
        self.assertEqual(getattr(form, 'pricing_package_rows', []),
                         [{'period': 'month', 'amount': '80', 'sessions': ''}])
        with self.assertRaises(ValidationError) as error:
            save_proposal(actor=self.actor, draft_id=key, expected_version=1, data=data, files={}, submit=True)
        self.assertIn('pricing_packages', error.exception.form.errors)

    def test_invalid_tariffs_are_rejected_and_preserved_for_correction(self):
        for period, amount, sessions in [('year', '10', '1'), ('month', '-1', '8'),
                                         ('month', '0.123', '1'), ('package', '10', '0'),
                                         ('package', '10', '1.5'), ('month', '80', '2147483648')]:
            with self.subTest(period=period, amount=amount, sessions=sessions):
                form = OwnerSpecialistForm(self.profile_data(
                    lesson_type='consultation', lesson_price='9', package_period=period,
                    package_amount=amount, package_sessions=sessions), actor=self.actor)
                self.assertIn('pricing_packages', form.errors)
                self.assertEqual(form.pricing_package_rows, [
                    {'period': period, 'amount': amount, 'sessions': sessions}])

    def test_model_draft_preserves_legacy_prices_and_partial_rows_then_clears_packages(self):
        person = Specialist.objects.create(name='Legacy example', verified_person_user=self.actor,
                                           person_verified_at=timezone.now(),
                                           price_from=0, price_to=75)
        data = self.profile_data(package_period='month', package_amount='12,50')
        draft = OwnerSpecialistForm(data, actor=self.actor, instance=person, draft_save_only=True)
        result = save_owner_specialist_profile(user=self.actor, form=draft, draft_save_only=True)
        self.assertTrue(result.ok)
        person.refresh_from_db()
        self.assertEqual((person.price_from, person.price_to), (0, 75))
        self.assertEqual(person.pricing_packages, [{'period': 'month', 'amount': '12,50', 'sessions': ''}])
        self.assertIsNone(person.lesson_price)
        form = OwnerSpecialistForm(self.profile_data(lesson_type='group', lesson_price='15,50'),
                                   actor=self.actor, instance=person, files={'photo': portrait_upload()})
        result = save_owner_specialist_profile(user=self.actor, form=form, draft_save_only=False)
        self.assertTrue(result.ok, result.form.errors)
        person.refresh_from_db()
        self.assertEqual(person.pricing_packages, [])
        self.assertEqual(person.lesson_price, Decimal('15.50'))
        self.assertEqual(person.status, Specialist.STATUS_PENDING)

    def test_typo_in_lesson_type_or_amount_blocks_sending(self):
        for kind, price, field in [('seminar', '20', 'lesson_type'), ('group', '-1', 'lesson_price'),
                                   ('pair', '2.123', 'lesson_price'), ('pair', 'NaN', 'lesson_price')]:
            with self.subTest(kind=kind, price=price):
                form = OwnerSpecialistForm(self.profile_data(lesson_type=kind, lesson_price=price))
                self.assertIn(field, form.errors)

    def test_package_total_must_be_above_zero(self):
        for amount in ('0', '0.00'):
            with self.subTest(amount=amount):
                form = OwnerSpecialistForm(self.profile_data(
                    lesson_type='group', lesson_price='10', package_period='package',
                    package_amount=amount, package_sessions='4'), actor=self.actor)
                self.assertIn('pricing_packages', form.errors)

    def test_package_count_is_limited(self):
        data = self.profile_data(lesson_type='group', lesson_price='10')
        data.setlist('package_period', ['package'] * 11)
        data.setlist('package_amount', ['40'] * 11)
        data.setlist('package_sessions', ['4'] * 11)
        self.assertIn('pricing_packages', OwnerSpecialistForm(data, actor=self.actor).errors)
        for name in ('package_period', 'package_amount', 'package_sessions'):
            data.setlist(name, data.getlist(name)[:10])
        self.assertNotIn('pricing_packages', OwnerSpecialistForm(data, actor=self.actor).errors)
