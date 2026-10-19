"""Structured validation targets reach the owner without changing pricing rules."""
import json
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.forms import OwnerPlaceEditForm
from catalog.models import Activity, OfferingGroup, PricingPlan, VolunteerPlaceRevision
from catalog.services.pricing_plans import normalize_pricing_plans, serialize_nested_pricing, validate_nested_pricing
from catalog.testcases.utils import create_ready_place


class OfferingErrorTargetTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='offer03_error_owner')
        self.place = create_ready_place(owner=self.owner, created_by=self.owner, price_mode='tariffs')
        PricingPlan.objects.filter(place=self.place).delete()
        for ai in range(2):
            activity = Activity.objects.create(place=self.place, name_az=f'Activity {ai}', status='published')
            for gi in range(2):
                group = OfferingGroup.objects.create(activity=activity, name_az=f'Group {gi}', age_from=6, age_to=12)
                for pi in range(2):
                    self.target = PricingPlan.objects.create(offering_group=group, product_type='lesson', price='20')
        self.client.force_login(self.owner)

    def payload(self):
        return serialize_nested_pricing(self.place)

    def assert_target(self, payload, expected):
        with self.assertRaises(ValidationError) as raised:
            validate_nested_pricing(self.place, payload)
        error = raised.exception.error_list[0]
        self.assertEqual((error.params or {}).get('field_path'), expected)
        self.target.refresh_from_db()
        self.assertEqual(self.target.price, Decimal('20'))
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
        return raised.exception.messages

    def data(self, payload):
        page = self.client.get(reverse('owner_place_edit', args=[self.place.pk]))
        return {
            'form_action': 'save_draft', 'photo_request_id': str(uuid4()),
            'publication_token': page.context['form']['publication_token'].value(),
            'name_az': self.place.name_az, 'description_az': self.place.description_az,
            'category': self.place.category_id, 'subcategory': self.place.subcategory_id,
            'nature': 'business', 'schedule_mode': 'by_appointment', 'price_mode': 'tariffs',
            'pricing_plans': '[]', 'nested_pricing': json.dumps(payload),
        }

    def test_price_range_billing_age_and_number_format_target_actual_second_plan(self):
        cases = [
            ({'price': '0'}, 'price'),
            ({'price_kind': 'range', 'price_min': '', 'price_max': '30'}, 'price_min'),
            ({'price_kind': 'range', 'price_min': '10', 'price_max': ''}, 'price_max'),
            ({'billing_mode': 'recurring', 'billing_interval': 'month', 'billing_interval_count': 0}, 'billing_interval_count'),
            ({'billing_mode': 'installment', 'billing_cycles': 0}, 'billing_cycles'),
            ({'age_from': 10, 'age_to': 9}, 'age_to'),
            ({'price': 'invalid'}, 'price'),
            ({'billing_mode': 'recurring', 'billing_interval': 'month', 'billing_interval_count': 'invalid'}, 'billing_interval_count'),
        ]
        for changes, key in cases:
            with self.subTest(changes=changes):
                payload = self.payload()
                payload['activities'][1]['groups'][1]['pricing_plans'][1].update(changes)
                self.assert_target(payload, ['activities', 1, 'groups', 1, 'pricing_plans', 1, key])

    def test_group_age_bounds_and_field_validator_have_group_targets(self):
        for changes, key in [({'age_from': 13, 'age_to': 12}, 'age_to'), ({'age_from': -1}, 'age_from')]:
            with self.subTest(changes=changes):
                payload = self.payload()
                payload['activities'][1]['groups'][1].update(changes)
                self.assert_target(payload, ['activities', 1, 'groups', 1, key])

    def test_disjoint_plan_age_targets_the_bound_outside_group(self):
        for changes, key in [({'age_from': 13, 'age_to': 14}, 'age_from'), ({'age_from': 3, 'age_to': 5}, 'age_to')]:
            with self.subTest(changes=changes):
                payload = self.payload()
                payload['activities'][1]['groups'][1]['pricing_plans'][1].update(changes)
                self.assert_target(payload, ['activities', 1, 'groups', 1, 'pricing_plans', 1, key])

    def test_foreign_group_id_stays_rejected_and_targets_local_block(self):
        payload = self.payload()
        payload['activities'][1]['groups'][1]['id'] = 999999
        self.assert_target(payload, ['activities', 1, 'groups', 1])

    def test_machine_address_does_not_depend_on_translated_message(self):
        messages = []
        for lang in ('ru', 'az', 'en'):
            with override(lang):
                payload = self.payload()
                payload['activities'][1]['groups'][1]['pricing_plans'][1]['price'] = '0'
                messages.append(self.assert_target(payload, ['activities', 1, 'groups', 1, 'pricing_plans', 1, 'price'])[0])
        self.assertEqual(len(set(messages)), 3)

    def test_form_preserves_target_params_alongside_legacy_error_text(self):
        payload = self.payload()
        payload['activities'][1]['groups'][1]['pricing_plans'][1]['price'] = '0'
        form = OwnerPlaceEditForm(data=self.data(payload), instance=self.place, draft_save_only=True)
        self.assertFalse(form.is_valid())
        error = form.errors.as_data()['nested_pricing'][0]
        self.assertEqual((error.params or {}).get('field_path'), ['activities', 1, 'groups', 1, 'pricing_plans', 1, 'price'])
        self.assertTrue(form.errors['nested_pricing'][0])

    def test_http_rejection_keeps_messages_adds_targets_and_never_writes_candidate(self):
        payload = self.payload()
        payload['activities'][1]['groups'][1]['pricing_plans'][1]['price'] = '0'
        response = self.client.post(reverse('owner_photo_edit_save', args=[self.place.pk]), self.data(payload))
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertFalse(body['ok'])
        self.assertIsInstance(body['errors']['nested_pricing'][0], str)
        self.assertEqual(body.get('error_targets', {}).get('nested_pricing'), [['activities', 1, 'groups', 1, 'pricing_plans', 1, 'price']])
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
        self.target.refresh_from_db()
        self.assertEqual(self.target.price, Decimal('20'))

    def test_valid_http_save_stays_candidate_and_preserves_live_price(self):
        payload = self.payload()
        payload['activities'][1]['groups'][1]['pricing_plans'][1]['price'] = '30'
        response = self.client.post(reverse('owner_photo_edit_save', args=[self.place.pk]), self.data(payload))
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()['ok'])
        self.target.refresh_from_db()
        self.assertEqual(self.target.price, Decimal('20'))
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.payload['nested_pricing']['activities'][1]['groups'][1]['pricing_plans'][1]['price'], '30.00')

    def test_direct_normalization_keeps_localized_tariff_message(self):
        with override('ru'), self.assertRaises(ValidationError) as raised:
            normalize_pricing_plans([{'product_type': 'lesson', 'price_kind': 'exact', 'price': '0'}])
        self.assertEqual(raised.exception.messages, ['Тариф 1: поле price: Для точной цены укажите сумму больше нуля.'])
