"""Return/resubmit presentation must agree with actual state and saved readiness."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override
from django.utils import timezone
from catalog.models import VolunteerPlaceRevision
from catalog.services import publication, moderation_hub
from catalog.services.moderation_changes import describe_change
from catalog.services.place_readiness import evaluate_saved_place_readiness, readiness_data_from_form
from catalog.testcases.utils import create_ready_place, build_structured_schedule_payload


class ModerationReturnClarityTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user('clarity_owner')
        self.staff = users.objects.create_superuser('clarity_staff', 'clarity@example.invalid', 'fictional')
        self.place = create_ready_place(owner=self.owner, created_by=self.owner,
            name='Old test legacy name', name_az='Rəsm studiyası', status='draft', is_active=False)
        self.revision = publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={'address': 'Bakı, Nizami küçəsi 14'}, schema_version=1, expected_version=self.place.content_version)

    def test_saved_candidate_ignores_hidden_stale_legacy_name_and_uses_four_sections(self):
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        readiness = evaluate_saved_place_readiness(self.place)
        self.assertTrue(readiness.is_ready, readiness.issues)
        completion = OwnerPlacesController._calculate_place_completion(self.place, readiness=readiness)
        self.assertEqual((completion['percent'], completion['completed_steps'], completion['total_steps']), (100, 4, 4))
        self.assertEqual([s['fragment'] for s in completion['steps']], ['pc-section-1', 'pc-section-2', 'pc-section-3', 'pc-section-4'])
        self.place.refresh_from_db()
        self.assertEqual(self.place.name, 'Old test legacy name')

    def test_visible_bad_translation_is_still_validated(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={'name_en': 'test'})
        self.place.refresh_from_db()
        self.assertFalse(evaluate_saved_place_readiness(self.place).is_ready)

    def test_legacy_name_is_still_used_without_translations(self):
        from types import SimpleNamespace
        self.place.name_az = self.place.name_ru = self.place.name_en = ''
        data = readiness_data_from_form(SimpleNamespace(instance=self.place, cleaned_data={}, cleaned_schedule_days=[]))
        self.assertEqual(data.name_texts, ('Old test legacy name',))

    def test_return_reason_and_resubmit_preserve_user_work(self):
        self.client.force_login(self.staff)
        url = reverse('admin:volunteer_moderation_detail', args=['content', self.revision.pk])
        reason = 'Уточните адрес.\nУкажите возраст. <script>alert(1)</script>'
        self.client.post(url, {'action': 'return', 'version': self.revision.version, 'reason': reason})
        self.revision.refresh_from_db()
        self.assertEqual((self.revision.status, self.revision.review_note), ('rejected', reason))
        _, counts = moderation_hub.query(self.staff, {'status': 'all'})
        self.assertEqual((counts['pending'], counts['rejected'], counts['declined']), (0, 1, 0))
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/places/')
        self.assertContains(response, 'Уточните адрес.<br>')
        self.assertNotContains(response, '<script>alert(1)</script>')
        revised = publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={'address': 'Bakı, Nizami küçəsi 16'}, schema_version=1,
            expected_version=self.place.content_version, revision_version=self.revision.version)
        self.assertEqual(revised.status, 'pending')
        self.assertEqual(revised.payload['address'], 'Bakı, Nizami küçəsi 16')
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_public)

    def test_structured_review_is_readable_and_retains_exact_audit_details(self):
        import json
        days = json.loads(build_structured_schedule_payload())
        for lang in ('ru', 'az', 'en'):
            with override(lang):
                result = describe_change('structured_schedule', [], days)
                self.assertIn('09:00', result['after_text'])
                self.assertNotIn('weekday', result['after_text'])
                self.assertEqual(json.loads(result['after_raw']), days)
                tariff = {'product_type': 'lesson', 'price_kind': 'range', 'price_min': '40.00',
                          'price_max': '80.00', 'currency': 'AZN', 'is_active': False,
                          'valid_from': '2030-01-01', 'conditions_ru': '<b>Условие</b>'}
                result = describe_change('pricing_plans', [], [tariff])
                self.assertIn('40.00', result['after_text'])
                self.assertIn('80.00', result['after_text'])
                self.assertIn('2030-01-01', result['after_text'])
                self.assertNotIn('price_kind', result['after_text'])
                self.assertEqual(json.loads(result['after_raw']), [tariff])

    def test_return_and_decline_have_separate_localized_counters(self):
        self.client.force_login(self.staff)
        publication.review(actor=self.staff, revision_id=self.revision.pk,
                           version=self.revision.version, approve=False, note='Уточните адрес.')
        for prefix, returned, declined in [('ru/', 'На доработке', 'Отклонено'),
                                          ('en/', 'Needs changes', 'Rejected')]:
            response = self.client.get('/' + prefix + 'admin/volunteer/moderation/')
            self.assertContains(response, returned)
            self.assertContains(response, declined)
            self.assertEqual(response.context['counts']['rejected'], 1)
            self.assertEqual(response.context['counts']['declined'], 0)

    def test_affiliation_rejection_does_not_count_as_content_needs_changes(self):
        from catalog.models import Organization, OrganizationPlaceRequest
        org = Organization.objects.create(name_az='Rəsm', created_by=self.staff)
        OrganizationPlaceRequest.objects.create(place=self.place, organization=org,
            requested_by=self.owner, relationship_kind='informational', status='rejected',
            decided_by=self.staff, decided_at=timezone.now())
        rows, counts = moderation_hub.query(self.staff, {'status': 'declined'})
        self.assertEqual((counts['declined'], counts['rejected']), (1, 0))
        self.assertEqual([row['kind'] for row in rows], ['affiliation'])

    def test_additional_group_change_cannot_look_like_unchanged_pricing(self):
        import copy
        before = {'activities': [{'name_az': 'Rəsm', 'groups': [
            {'name_az': 'Qrup', 'age_from': 5, 'pricing_plans': []}]}]}
        after = copy.deepcopy(before)
        after['activities'][0]['groups'][0]['age_from'] = 7
        result = describe_change('nested_pricing', before, after)
        self.assertEqual(result['change_type'], 'changed')
        self.assertTrue(result['details_changed'])
