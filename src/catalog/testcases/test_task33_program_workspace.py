"""Stage 14 owner Program and linked local offers."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Activity, Organization, OrganizationGrant, Place, Program
from catalog.services import organization_ownership, publication
from catalog.services.pricing_plans import serialize_nested_pricing, validate_nested_pricing, replace_nested_pricing
from catalog.testcases.utils import create_quality_place


class ProgramWorkspaceTests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.owner = user.objects.create_user(username='program_owner')
        self.manager = user.objects.create_user(username='program_manager')
        self.staff = user.objects.create_superuser(username='program_staff', email='program_staff@example.invalid', password='synthetic')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Şəbəkə')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner, name_az='Birinci')
        organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        self.place.refresh_from_db()

    def test_create_and_edit_program_has_separate_right_and_pending_impact(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('organization_program_create', args=[self.org.pk]), {'name_az': 'Rəsm'})
        self.assertEqual(response.status_code, 302)
        program = Program.objects.get(organization=self.org)
        self.assertEqual(program.status, 'draft')
        activity = Activity.objects.create(place=self.place, program=program, supplement_az='Yerli')
        self.client.force_login(self.manager)
        OrganizationGrant.objects.create(organization=self.org, owner=self.owner, member=self.manager,
            base_ownership_version=self.org.ownership_version, actions=['organization.view', 'place.view', 'place.edit'], scope='all_network', role='EDITOR')
        url = reverse('organization_program_detail', args=[self.org.pk, program.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(reverse('organization_program_save', args=[self.org.pk, program.pk]), {'name_az': 'No'}).status_code, 404)
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(url), self.place.name_az)
        save = reverse('organization_program_save', args=[self.org.pk, program.pk])
        payload = {'name_az': 'New', 'description_az': 'General', 'expected_version': program.content_version,
            'revision_version': 0, 'submit': '1'}
        from django.utils.translation import override
        with override('ru'):
            ru_save = reverse('organization_program_save', args=[self.org.pk, program.pk])
            missing_impact = self.client.post(ru_save, payload)
        self.assertEqual(missing_impact.status_code, 400)
        self.assertContains(missing_impact, 'Проверьте затронутые филиалы', status_code=400)
        self.assertEqual(self.client.post(save, {**payload, 'impact_confirmed': '1'}).status_code, 302)
        program.refresh_from_db(); activity.refresh_from_db()
        self.assertEqual(program.name_az, 'Rəsm')
        self.assertEqual(activity.supplement_az, 'Yerli')
        self.assertEqual(program.content_revision.status, 'pending')
        self.assertEqual(self.client.post(save, {**payload, 'impact_confirmed': '1'}).status_code, 409)
        revision = program.content_revision
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        program.refresh_from_db(); activity.refresh_from_db()
        self.assertEqual(program.name_az, 'New')
        self.assertEqual(activity.program_snapshot['description_az'], 'General')
        self.assertEqual(activity.supplement_az, 'Yerli')

    def test_group_conditions_date_changes_only_on_explicit_current_owner_action(self):
        from catalog.models import OfferingGroup
        activity = Activity.objects.create(place=self.place, name_az='Rəsm')
        group = OfferingGroup.objects.create(activity=activity, name_az='7–10', conditions_az='Bring materials')
        action = reverse('owner_group_confirm_conditions', args=[self.place.pk, group.pk])
        self.client.force_login(self.manager)
        self.assertEqual(self.client.post(action, {'expected_version': group.content_version}).status_code, 404)
        group.refresh_from_db()
        self.assertIsNone(group.conditions_verified_at)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(action, {'expected_version': group.content_version + 1}).status_code, 409)
        group.refresh_from_db()
        self.assertIsNone(group.conditions_verified_at)
        self.assertEqual(self.client.post(action, {'expected_version': group.content_version}).status_code, 302)
        group.refresh_from_db()
        self.assertIsNotNone(group.conditions_verified_at)
        confirmed = group.conditions_verified_at
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile
        with patch('catalog.photo_views.normalize_uploaded_image', return_value=SimpleUploadedFile('ok.webp', b'WEBP', content_type='image/webp')):
            photo = self.client.post(reverse('owner_photo_prepare'), {
                'photo': SimpleUploadedFile('portrait.png', b'valid-synthetic', content_type='image/png')})
        self.assertEqual(photo.status_code, 200)
        group.refresh_from_db()
        self.assertEqual(group.conditions_verified_at, confirmed)
        self.assertEqual(self.client.post(action, {'expected_version': group.content_version - 1}).status_code, 409)
        group.refresh_from_db()
        self.assertEqual(group.conditions_verified_at, confirmed)
        group.conditions_az = 'Changed conditions'
        group.save(update_fields=['conditions_az'])
        group.refresh_from_db()
        self.assertIsNone(group.conditions_verified_at)
        self.assertEqual(self.client.post(action, {'expected_version': group.content_version}).status_code, 302)
        group.refresh_from_db()
        self.assertIsNotNone(group.conditions_verified_at)
        from catalog.services.publication import _apply
        _apply(group, 'offering_group', {'conditions_az': 'Approved new conditions'})
        group.refresh_from_db()
        self.assertIsNone(group.conditions_verified_at)

    def test_linked_activity_uses_approved_program_and_keeps_local_group(self):
        program = Program.objects.create(organization=self.org, name_az='Rəsm', description_az='General', status='published')
        Program.objects.filter(pk=program.pk).update(approved_at=timezone.now())
        program.refresh_from_db()
        payload = {'pricing_schema_version': 2, 'activities': [{
            'id': None, 'program_id': program.pk, 'supplement_az': 'Local', 'groups': [{
                'id': None, 'name_az': '7–10', 'age_from': 7, 'age_to': 10, 'language': 'AZ',
                'schedule_text': 'Mon 17:00', 'pricing_plans': [{
                    'product_type': 'lesson', 'price_kind': 'exact', 'price': '20.00', 'currency': 'AZN',
                    'charge_role': 'primary', 'billing_mode': 'one_time', 'age_from': 7, 'age_to': 10,
                }],
            }],
        }]}
        normalized = validate_nested_pricing(self.place, payload)
        replace_nested_pricing(self.place, normalized)
        activity = Activity.objects.get(place=self.place)
        group = activity.offering_groups.get()
        self.assertEqual(activity.program_id, program.pk)
        self.assertEqual(activity.program_snapshot['description_az'], 'General')
        self.assertEqual(activity.supplement_az, 'Local')
        self.assertEqual((group.age_from, group.age_to, group.language, group.schedule_text), (7, 10, 'AZ', 'Mon 17:00'))
        self.assertEqual(group.pricing_plan_records.count(), 1)
        from catalog.services.pricing_plans import build_pricing_summary
        self.assertIn('Rəsm', build_pricing_summary(self.place, 'az')['plans'][0]['title'])
        self.assertEqual(serialize_nested_pricing(self.place)['activities'][0]['program_id'], program.pk)
        other = Program.objects.create(organization=Organization.objects.create(owner=self.manager, name_az='Other'), name_az='Foreign', status='published')
        payload['activities'][0]['program_id'] = other.pk
        with self.assertRaises(Exception):
            validate_nested_pricing(self.place, payload)
