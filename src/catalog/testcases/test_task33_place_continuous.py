"""Stage 13 owner form contracts, separate from the volunteer wizard."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place, VolunteerPlaceRevision
from catalog.testcases.utils import create_quality_place


class ContinuousPlaceFormTests(TestCase):
    def setUp(self):
        from catalog.testcases.utils import ensure_quality_subcategory
        ensure_quality_subcategory('EDU')
        self.owner = get_user_model().objects.create_user(username="continuous_owner")
        self.place = create_quality_place(owner=self.owner, created_by=self.owner)
        self.client.force_login(self.owner)

    def test_create_uses_four_visible_sections_and_server_draft_transport(self):
        response = self.client.get(reverse("owner_place_create") + "?type=permanent")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-place-mode="continuous"')
        self.assertEqual(response.content.count(b'data-place-section='), 4)
        self.assertContains(response, reverse("server_draft_collection"))
        self.assertNotContains(response, "data-pw-next")
        self.assertNotContains(response, "data-pw-prev")
        self.assertContains(response, 'name="pricing_plans"')
        self.assertContains(response, 'name="nested_pricing"')
        self.assertContains(response, 'data-pc-add-activity')
        self.assertContains(response, 'name="publication_token"')

    def test_submission_summary_does_not_make_map_and_photos_mandatory(self):
        response = self.client.get(reverse('owner_place_create') + '?type=permanent')
        summary = response.context['form'].submission_readiness
        self.assertEqual(summary['required_count'], 10)
        self.assertNotIn('photo', [item['code'] for item in summary['items']])
        self.assertNotIn('coordinates', [item['code'] for item in summary['items']])
        self.assertTrue(summary['issues'])

    def test_submission_summary_counts_group_tariff_without_general_ticket(self):
        import json
        from catalog.forms import OwnerPlaceCreateForm
        from catalog.testcases.utils import ensure_quality_subcategory
        subcategory = ensure_quality_subcategory('EDU')
        form = OwnerPlaceCreateForm(data={
            'name_az': 'Rəsm mərkəzi', 'description_az': 'Uşaqlar üçün rəsm dərsləri.',
            'category': 'EDU', 'subcategory': str(subcategory.pk), 'nature': 'business',
            'age_from': '0', 'age_to': '12', 'region': 'baku', 'district': 'baku_yasamal',
            'address': 'QA küçəsi 1', 'schedule_mode': 'always_open',
            'website': 'https://example.invalid', 'pricing_plans': '[]',
            'nested_pricing': json.dumps({'pricing_schema_version': 2, 'activities': [{
                'name_az': 'Rəsm', 'description_az': 'Rəsm dərsləri', 'groups': [{
                    'name_az': 'Uşaqlar', 'age_from': 0, 'age_to': 12,
                    'schedule_text': 'Çərşənbə 15:00',
                    'pricing_plans': [{'product_type': 'lesson', 'price': '15'}],
                }],
            }]}),
        })
        self.assertTrue(form.is_valid(), form.errors)
        summary = form.submission_readiness
        self.assertTrue(next(item for item in summary['items'] if item['code'] == 'price')['complete'])
        self.assertTrue(summary['is_ready'])

    def test_submission_contact_marker_is_a_choice_and_public_space_is_exempt(self):
        from catalog.forms import OwnerPlaceEditForm
        form = OwnerPlaceEditForm(instance=Place(nature='public_space'))
        summary = form.submission_readiness
        contact = next(item for item in summary['items'] if item['code'] == 'phone')
        self.assertTrue(contact['complete'])
        self.assertTrue(contact['config']['optional'])
        self.assertEqual(contact['config']['fields'], ['phone1', 'phone2', 'phone3', 'website'])

    def test_admin_displayed_readiness_counts_saved_group_prices(self):
        from django.contrib import admin
        from catalog.domain_admin.place import PlaceAdmin, PlaceAdminForm
        from catalog.models import Activity, OfferingGroup, PricingPlan
        activity = Activity.objects.create(place=self.place, name_az='Rəsm', status='published')
        group = OfferingGroup.objects.create(activity=activity, name_az='Kiçik', age_from=5, age_to=8)
        PricingPlan.objects.create(offering_group=group, product_type='lesson', price='20')
        summary = PlaceAdmin(Place, admin.site)._build_place_form_summary(
            form=PlaceAdminForm(instance=self.place), obj=self.place)
        price = next(item for item in summary['checklist_items'] if item['code'] == 'price')
        self.assertTrue(price['initial'])
        import json
        staff = get_user_model().objects.create_superuser(username='continuous_summary_staff', email='summary@example.invalid')
        self.client.force_login(staff)
        response = self.client.get(reverse('admin:catalog_place_change', args=[self.place.pk]))
        nested = json.loads(response.context['adminform'].form['nested_pricing'].value())
        self.assertEqual(nested['activities'][0]['groups'][0]['id'], group.pk)

    def test_edit_shows_live_and_candidate_separately(self):
        response = self.client.get(reverse("owner_place_edit", args=[self.place.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-place-live')
        self.assertContains(response, 'data-place-candidate')
        self.assertContains(response, 'data-source-version=')
        self.assertContains(response, 'data-target-id=')
        self.assertEqual(response.content.count(b'data-place-section='), 4)

    def test_edit_displays_candidate_nature_and_saved_gallery_without_changing_live(self):
        from catalog.forms import OwnerPlaceEditForm
        from catalog.testcases.utils import ensure_quality_subcategory
        ensure_quality_subcategory('EDU')
        original_nature = self.place.nature
        VolunteerPlaceRevision.objects.create(place=self.place, author=self.owner,
            payload={'nature': 'public_space', 'gallery': [
                {'id': None, 'image': 'places/qa-candidate.webp', 'caption': '', 'order': 0},
            ]})
        form = OwnerPlaceEditForm(instance=self.place)
        self.assertEqual(form['nature'].value(), 'public_space')
        self.assertEqual(form.saved_gallery_preview[0]['image'], 'places/qa-candidate.webp')
        self.place.refresh_from_db()
        self.assertEqual(self.place.nature, original_nature)

    def test_public_space_can_submit_without_organization_photo_coordinates_or_contact(self):
        import json
        from catalog.testcases.utils import ensure_quality_subcategory
        subcategory = ensure_quality_subcategory('EDU')
        response = self.client.post(reverse('owner_place_create'), {
            'form_action': 'save_and_publish',
            'name_az': 'Yeni ictimai park',
            'description_az': 'Uşaqlar üçün açıq oyun sahəsi və ailələrin rahat gəzintisi üçün park.',
            'category': 'EDU', 'subcategory': str(subcategory.pk),
            'nature': 'public_space', 'age_from': '0', 'age_to': '18',
            'region': 'baku', 'district': 'baku_yasamal', 'address': 'Bakı, park girişi',
            'schedule_mode': 'always_open',
            'pricing_plans': json.dumps([{'product_type': 'admission', 'price_kind': 'free', 'is_active': True}]),
            'phone1': '', 'phone2': '', 'phone3': '', 'website': '',
        })
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.context else response.content[:100])
        created = Place.objects.exclude(pk=self.place.pk).get()
        candidate = VolunteerPlaceRevision.objects.get(place=created).payload
        self.assertEqual(candidate['name_az'], 'Yeni ictimai park')
        self.assertEqual(candidate['nature'], 'public_space')
        self.assertFalse(candidate.get('photo'))
        self.assertIsNone(candidate.get('lat'))
        self.assertIsNone(created.organization_id)

    def test_business_needs_one_allowed_contact_and_does_not_need_translation(self):
        import json
        from catalog.testcases.utils import ensure_quality_subcategory
        subcategory = ensure_quality_subcategory('EDU')
        payload = {
            'form_action': 'save_and_publish', 'name_az': 'Yeni mərkəz',
            'description_az': 'Uşaqlar üçün maraqlı dərslər və rahat mühit təqdim edən mərkəz.',
            'category': 'EDU', 'subcategory': str(subcategory.pk), 'nature': 'business',
            'age_from': '5', 'age_to': '12', 'region': 'baku', 'district': 'baku_yasamal',
            'address': 'Bakı, mərkəz küçəsi 1', 'schedule_mode': 'always_open',
            'pricing_plans': json.dumps([{'product_type':'lesson','price_kind':'exact','price':'20','is_active':True}]),
        }
        missing = self.client.post(reverse('owner_place_create'), payload)
        self.assertEqual(missing.status_code, 200)
        self.assertIn('phone1', missing.context['form'].errors)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(payload__name_az='Yeni mərkəz').exists())
        allowed = self.client.post(reverse('owner_place_create'), {**payload, 'website':'https://example.org'})
        self.assertEqual(allowed.status_code, 302, allowed.context['form'].errors if allowed.context else allowed.content[:100])
        candidate = VolunteerPlaceRevision.objects.get(payload__name_az='Yeni mərkəz').payload
        self.assertEqual(candidate['website'], 'https://example.org')
        self.assertFalse(candidate.get('name_ru'))
        self.assertFalse(candidate.get('name_en'))

    def test_three_direct_plans_keep_distinct_price_rows_without_activity(self):
        import json
        from catalog.testcases.utils import ensure_quality_subcategory
        subcategory = ensure_quality_subcategory('EDU')
        plans = [{'product_type':'admission','price_kind':'exact','price':str(amount),'is_active':True,
                  'title_az':title} for amount,title in ((5,'Uşaq'),(10,'Ailə'),(15,'Qrup'))]
        response = self.client.post(reverse('owner_place_create'), {
            'form_action':'save_and_publish','name_az':'Ümumi biletli park',
            'description_az':'Uşaqlar üçün böyük açıq park və ümumi giriş biletləri.',
            'nature':'public_space','category':'EDU','subcategory':str(subcategory.pk),
            'age_from':'0','age_to':'18','region':'baku','district':'baku_yasamal',
            'address':'Bakı, park yolu 1','schedule_mode':'always_open','pricing_plans':json.dumps(plans),
        })
        self.assertEqual(response.status_code,302,response.context['form'].errors if response.context else response.content[:100])
        candidate = VolunteerPlaceRevision.objects.get(payload__name_az='Ümumi biletli park').payload
        self.assertEqual(len(candidate['pricing_plans']),3)
        self.assertEqual(tuple(float(row['price']) for row in candidate['pricing_plans']), (5,10,15))
        self.assertFalse(candidate.get('nested_pricing',{}).get('activities'))

    def test_new_group_with_three_tariffs_stays_candidate_until_place_approval(self):
        import json
        from catalog.models import Activity, OfferingGroup, PricingPlan
        from catalog.services.publication import review
        from catalog.testcases.utils import ensure_quality_subcategory
        subcategory = ensure_quality_subcategory('EDU')
        nested = {'pricing_schema_version': 2, 'activities': [{
            'id': None, 'name_az': 'Rəsm dərsi', 'description_az': 'Uşaqlar üçün rəsm məşğələsi.',
            'groups': [{'id': None, 'name_az': 'Kiçik qrup', 'age_from': 5, 'age_to': 8,
                        'language': 'az', 'schedule_text': 'Çərşənbə 15:00', 'pricing_plans': [
                            {'product_type': 'membership', 'price': '90', 'age_from': 5, 'age_to': 8},
                            {'product_type': 'lesson', 'price_kind': 'free', 'price': '0', 'is_trial': True},
                            {'product_type': 'registration_fee', 'charge_role': 'registration_fee',
                             'price': '15', 'is_required': True},
                        ]}],
        }]}
        response = self.client.post(reverse('owner_place_create'), {
            'form_action': 'save_and_publish', 'name_az': 'Rəsm mərkəzi',
            'description_az': 'Uşaqlar üçün rəsm dərsləri və yaradıcılıq mərkəzi.',
            'category': 'EDU', 'subcategory': str(subcategory.pk), 'nature': 'business',
            'age_from': '5', 'age_to': '8', 'region': 'baku', 'district': 'baku_yasamal',
            'address': 'Bakı, rəsm küçəsi 1', 'schedule_mode': 'always_open',
            'website': 'https://example.org', 'pricing_plans': '[]',
            'nested_pricing': json.dumps(nested),
        })
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.context else response.content[:100])
        candidate = VolunteerPlaceRevision.objects.get(payload__name_az='Rəsm mərkəzi')
        self.assertEqual(candidate.payload['nested_pricing']['activities'][0]['groups'][0]['pricing_plans'].__len__(), 3)
        self.assertFalse(Activity.objects.filter(place=candidate.place).exists())
        staff = get_user_model().objects.create_superuser(username='continuous_staff', email='staff@example.invalid', password='synthetic')
        review(actor=staff, revision_id=candidate.pk, version=candidate.version, approve=True)
        activity = Activity.objects.get(place=candidate.place)
        group = OfferingGroup.objects.get(activity=activity)
        self.assertEqual(group.schedule_text, 'Çərşənbə 15:00')
        self.assertEqual((group.age_from, group.age_to), (5, 8))
        plans = list(PricingPlan.objects.filter(offering_group=group))
        self.assertEqual(len(plans), 3)
        self.assertEqual(sum(bool(plan.is_trial) for plan in plans), 1)
        self.assertEqual(sum(bool(plan.is_required) for plan in plans), 1)
        candidate.place.refresh_from_db()
        self.assertTrue(candidate.place.is_public)

    def test_published_group_price_edit_is_candidate_until_approval(self):
        import json
        from catalog.models import Activity, OfferingGroup, PricingPlan
        from catalog.services.pricing_plans import serialize_nested_pricing
        from catalog.services.publication import review
        from catalog.testcases.utils import ensure_quality_subcategory
        self.place.subcategory = ensure_quality_subcategory(self.place.category_id)
        self.place.save(update_fields=['subcategory'])
        activity = Activity.objects.create(place=self.place, name_az='Rəsm', status='published')
        group = OfferingGroup.objects.create(activity=activity, name_az='Kiçik', age_from=5, age_to=8)
        plan = PricingPlan.objects.create(offering_group=group, product_type='lesson', price='20')
        self.place.status = Place.STATUS_PUBLISHED
        self.place.is_active = True
        self.place.save(update_fields=['status', 'is_active'])
        nested = serialize_nested_pricing(self.place)
        nested['activities'][0]['groups'][0]['pricing_plans'][0]['price'] = '30.00'
        page = self.client.get(reverse('owner_place_edit', args=[self.place.pk]))
        response = self.client.post(reverse('owner_place_edit', args=[self.place.pk]), {
            'form_action': 'save_and_publish',
            'publication_token': page.context['form']['publication_token'].value(),
            'name_az': self.place.name_az, 'description_az': self.place.description_az,
            'category': self.place.category_id, 'subcategory': self.place.subcategory_id,
            'nature': 'business', 'schedule_mode': 'by_appointment', 'nested_pricing': json.dumps(nested),
            'pricing_plans': json.dumps(self.place.pricing_plans),
        })
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.context else response.content[:100])
        plan.refresh_from_db()
        self.assertEqual(str(plan.price), '20.00')
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.status, 'pending')
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)
        staff = get_user_model().objects.create_superuser(username='continuous_group_staff', email='group-staff@example.invalid', password='synthetic')
        review(actor=staff, revision_id=revision.pk, version=revision.version, approve=True)
        plan.refresh_from_db()
        self.assertEqual(str(plan.price), '30.00')

    def test_photo_prepare_failure_returns_retryable_error(self):
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile
        url = reverse('owner_photo_prepare')
        with patch('catalog.photo_views.normalize_uploaded_image', side_effect=OSError('synthetic storage failure')):
            failed = self.client.post(url, {'photo': SimpleUploadedFile('portrait.png', b'valid-synthetic', content_type='image/png')})
        self.assertEqual(failed.status_code, 503)
        self.assertIn('error', failed.json())
        with patch('catalog.photo_views.normalize_uploaded_image', return_value=SimpleUploadedFile('ok.webp', b'WEBP', content_type='image/webp')):
            retried = self.client.post(url, {'photo': SimpleUploadedFile('portrait.png', b'valid-synthetic', content_type='image/png')})
        self.assertEqual(retried.status_code, 200)

    def test_group_age_conflict_and_foreign_group_id_are_rejected(self):
        from django.core.exceptions import ValidationError
        from catalog.services.pricing_plans import validate_nested_pricing
        base = {'pricing_schema_version': 2, 'activities': [{
            'id': None, 'name_az': 'Rəsm', 'groups': [{
                'id': None, 'name_az': 'Kiçik', 'age_from': 5, 'age_to': 8,
                'pricing_plans': [{'product_type': 'lesson', 'price': '20', 'age_from': 10, 'age_to': 12}],
            }],
        }]}
        with self.assertRaises(ValidationError):
            validate_nested_pricing(self.place, base)
        base['activities'][0]['groups'][0]['pricing_plans'][0].update(age_from=5, age_to=8)
        base['activities'][0]['groups'][0]['id'] = 999999
        with self.assertRaises(ValidationError):
            validate_nested_pricing(self.place, base)

    def test_incomplete_group_data_roundtrips_in_private_server_draft(self):
        from catalog.services import publication, server_drafts
        unfinished = {'pricing_schema_version': 2, 'activities': [{'name_az': 'Rəsm'}]}
        draft = server_drafts.save(user=self.owner, data={
            'target_type': 'place', 'target_id': None,
            'schema_version': publication.SCHEMA_VERSION, 'expected_version': 0,
            'fields': {'nested_pricing': unfinished},
        })
        self.assertEqual(server_drafts.read(user=self.owner, draft_id=draft.pk).fields['nested_pricing'], unfinished)

    def test_server_draft_roundtrip_keeps_region_and_editor_note(self):
        from catalog.services import publication, server_drafts
        draft = server_drafts.save(user=self.owner, data={
            'target_type':'place','target_id':None,
            'schema_version':publication.SCHEMA_VERSION,'expected_version':0,
            'fields':{'region':'baku','district':'baku_yasamal','moderation_note':'Gate on entry'},
        })
        resumed = server_drafts.read(user=self.owner,draft_id=draft.pk)
        self.assertEqual(resumed.fields['region'],'baku')
        self.assertEqual(resumed.fields['moderation_note'],'Gate on entry')

    def test_explicit_place_save_consumes_matching_server_draft(self):
        from catalog.models import ServerDraft
        from catalog.services import publication, server_drafts
        draft = server_drafts.save(user=self.owner, data={
            'target_type':'place','target_id':self.place.pk,
            'schema_version':publication.SCHEMA_VERSION,'source_version':self.place.content_version,
            'expected_version':0,'fields':{'description_az':'New copy'},
        })
        page = self.client.get(reverse('owner_place_edit', args=[self.place.pk]))
        self.assertEqual(page.status_code, 200)
        data = {'form_action':'save_draft','server_draft_id':str(draft.pk),
                'publication_token':page.context['form']['publication_token'].value(),
                'name_az':self.place.name_az, 'description_az':self.place.description_az,
                'category':self.place.category_id, 'nature':'business'}
        response = self.client.post(reverse('owner_place_edit', args=[self.place.pk]), data)
        self.assertEqual(response.status_code,302,response.context['form'].errors if response.context else response.content[:100])
        draft = ServerDraft.objects.get(pk=draft.pk)
        self.assertEqual(draft.materialized_place_id,self.place.pk)
        from catalog.services.server_drafts import DraftConflict
        with self.assertRaises(DraftConflict):
            server_drafts.save(user=self.owner, data={
                'draft_id':str(draft.pk),'target_type':'place','target_id':self.place.pk,
                'schema_version':publication.SCHEMA_VERSION,'source_version':draft.source_version,
                'expected_version':draft.version,'fields':{'description_az':'stale overwrite'},
            })

    def test_public_live_place_is_not_hidden_by_incomplete_server_draft(self):
        self.place.status = Place.STATUS_PUBLISHED
        self.place.is_active = True
        self.place.save(update_fields=["status", "is_active"])
        from catalog.services import publication, server_drafts
        server_drafts.save(user=self.owner, data={
            "target_type": "place", "target_id": self.place.pk,
            "schema_version": publication.SCHEMA_VERSION,
            "source_version": self.place.content_version,
            "expected_version": 0, "fields": {"description_az": "Incomplete edit"},
        })
        response = self.client.get(reverse("owner_place_edit", args=[self.place.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-place-live')
        self.assertContains(response, 'data-place-candidate')
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)
