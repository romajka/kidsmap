import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from catalog.testcases.utils import create_ready_place
from catalog.services.staff_roles import VOLUNTEER_GROUP


class VolunteerJsonIdentityScopeTests(TestCase):
    def test_existing_own_card_can_validate_json_without_foreign_access(self):
        user=get_user_model().objects.create_user('json-scope-volunteer',is_staff=True)
        user.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        own=create_ready_place(created_by=user)
        foreign=create_ready_place()
        self.client.force_login(user)
        for place,status in ((own,200),(foreign,403)):
            response=self.client.post(reverse('admin:catalog_place_pricing_import_validate'),data=json.dumps({'place_id':place.pk,'base_content_version':place.content_version,'website':'https://example.com'}),content_type='application/json')
            self.assertEqual(response.status_code,status)
        response=self.client.get(reverse('admin:volunteer_edit',args=[own.pk]))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,f'data-place-id="{own.pk}"')
        self.assertEqual(self.client.get(reverse('admin:catalog_place_change',args=[own.pk])).status_code,403)


class CandidateJsonExportTests(TestCase):
    def test_export_contains_saved_candidate_and_rejects_stale_candidate_version(self):
        from catalog.services import publication
        from catalog.services.place_schedule import serialize_place_schedule
        user=get_user_model().objects.create_superuser('json-candidate','json-candidate@example.invalid','synthetic-test-only')
        place=create_ready_place()
        days=serialize_place_schedule(place)
        days[0]['intervals'][0]['start']='10:00'
        revision=publication.propose(actor=user,target_type='place',target_id=place.pk,
            patch={'name_az':'Saved JSON candidate','structured_schedule':days,
                   'pricing_plans':[{'id':place.pricing_plan_records.first().pk,'product_type':'lesson','price':33}]},
            schema_version=1,expected_version=place.content_version,submit=False,explicit_save=False)
        self.client.force_login(user)
        response=self.client.get(reverse('admin:catalog_place_export_json',args=[place.pk]))
        self.assertEqual(response.status_code,200)
        data=json.loads(response.content)
        self.assertEqual(data['name_az'],'Saved JSON candidate')
        self.assertEqual(data['schedule_days'],days)
        self.assertEqual(data['pricing_plans'][0]['price'],'33.00')
        self.assertEqual(data['candidate_version'],revision.version)
        fresh=self.client.post(reverse('admin:catalog_place_pricing_import_validate'),data=json.dumps(data),content_type='application/json')
        self.assertEqual(fresh.status_code,200)
        data['candidate_version']-=1
        stale=self.client.post(reverse('admin:catalog_place_pricing_import_validate'),data=json.dumps(data),content_type='application/json')
        self.assertEqual(stale.status_code,409)
        place.refresh_from_db()
        self.assertNotEqual(place.name_az,'Saved JSON candidate')
