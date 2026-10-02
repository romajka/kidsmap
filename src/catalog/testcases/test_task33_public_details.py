"""Stage18 public contracts: live visibility, source metadata and subject identity."""
import importlib.util
import json
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override
from catalog.models import Organization, Program, Activity, OfferingGroup, PricingPlan, PlaceReview, FunnelEvent
from catalog.services import organization_ownership
from catalog.testcases.utils import create_quality_place


class PublicDetailsTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('public18_owner', email='owner18@example.invalid')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner, name_az='Yerli məkan', name_ru='', name_en='', with_subcategory=True)
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Açıq təşkilat', description_az='Təsdiqlənmiş məlumat', status='published', approved_at=timezone.now(), phone='+994501234567', website='https://example.invalid')
        organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        self.place.refresh_from_db()
        self.program = Program.objects.create(organization=self.org, name_az='Ümumi proqram', description_az='Ümumi təsdiqlənmiş mətn', status='published', approved_at=timezone.now())
        self.activity = Activity.objects.create(place=self.place, program=self.program, status='published', supplement_az='Yerli əlavə')
        self.group = OfferingGroup.objects.create(activity=self.activity, name_az='Kiçik qrup', age_from=5, age_to=8, language='az', schedule_text='Şənbə 10:00', conditions_az='8 uşağa qədər')
        PricingPlan.objects.create(offering_group=self.group, product_type='lesson', price=Decimal('25'))

    def present(self, obj, lang='az'):
        self.assertIsNotNone(importlib.util.find_spec('catalog.services.public_presentation'), 'shared public presentation resolver is missing')
        from catalog.services.public_presentation import present
        return present(obj, lang)

    def test_az_fallback_is_explicit_and_group_price_schedule_remain_local(self):
        data = self.present(self.activity, 'en')
        self.assertTrue(data['visible'])
        self.assertTrue(data['translation_fallback'])
        self.assertEqual(data['content_language'], 'az')
        self.assertEqual(data['description'], 'Ümumi təsdiqlənmiş mətn')
        self.assertEqual(data['supplement'], 'Yerli əlavə')
        self.assertEqual(data['groups'][0]['schedule'], 'Şənbə 10:00')
        self.assertIn('25', data['groups'][0]['prices'][0]['label'])

    def test_active_contacts_fallback_and_detach_remove_live_org_sources(self):
        from catalog.models import Place
        Place.objects.filter(pk=self.place.pk).update(phone1='', phone2='', phone3='', website='')
        self.place.refresh_from_db()
        before = self.present(self.place)
        self.assertTrue(before['contacts']['has_phone'])
        self.assertEqual(before['contacts']['website_url'], 'https://example.invalid')
        organization_ownership.detach(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk, expected_ownership_version=1)
        self.place.refresh_from_db();self.activity.refresh_from_db()
        after = self.present(self.place)
        self.assertIsNone(after['organization'])
        self.assertFalse(after['contacts']['has_phone'])
        self.assertEqual(after['contacts']['website_url'], '')
        Program.objects.filter(pk=self.program.pk).update(description_az='LATER NETWORK SECRET')
        self.assertNotIn('LATER NETWORK SECRET', self.present(self.activity)['description'])

    def test_draft_organization_contacts_are_not_inherited(self):
        from catalog.models import Place
        Place.objects.filter(pk=self.place.pk).update(phone1='', phone2='', phone3='', website='')
        Organization.objects.filter(pk=self.org.pk).update(status='draft')
        self.place.refresh_from_db()
        self.assertEqual(self.present(self.place)['contacts']['website_url'], '')
        self.assertIsNone(self.present(self.place)['organization'])

    def test_detail_routes_empty_org_and_standalone_place(self):
        empty = Organization.objects.create(name_az='Ünvansız təşkilat', description_az='Faydalı məlumat', status='published', approved_at=timezone.now())
        response = self.client.get(f'/organizations/{empty.public_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Faydalı məlumat')
        self.assertNotContains(response, 'aggregateRating')
        standalone = create_quality_place(name_az='Müstəqil')
        self.assertIsNone(self.present(standalone)['organization'])
        self.assertEqual(reverse('organization_detail', args=[empty.public_id]), f'/organizations/{empty.public_id}/')
        self.assertEqual(reverse('activity_detail', args=[self.activity.pk]), f'/activities/{self.activity.pk}/')

    def test_hidden_parent_or_activity_returns_404_without_public_payload(self):
        Activity.objects.filter(pk=self.activity.pk).update(status='draft')
        self.assertEqual(self.client.get(f'/activities/{self.activity.pk}/').status_code, 404)
        Activity.objects.filter(pk=self.activity.pk).update(status='published')
        from catalog.models import Place
        Place.objects.filter(pk=self.place.pk).update(is_active=False, status='draft')
        self.assertEqual(self.client.get(f'/activities/{self.activity.pk}/').status_code, 404)
        Organization.objects.filter(pk=self.org.pk).update(archived_at=timezone.now())
        self.assertEqual(self.client.get(f'/organizations/{self.org.public_id}/').status_code, 404)
        self.assertFalse(self.present(self.activity)['visible'])

    def test_org_review_feed_links_original_target_and_excludes_pending(self):
        Activity.objects.create(place=self.place, name_az='PRIVATE DRAFT ACTIVITY', status='draft')
        PlaceReview.objects.create(place=self.place, user=self.owner, text='Approved branch experience', rating=4)
        PlaceReview.objects.create(place=self.place, text='PRIVATE PENDING REVIEW', status='pending', rating=1)
        response = self.client.get(f'/organizations/{self.org.public_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approved branch experience')
        self.assertContains(response, f'/activities/{self.activity.pk}/')
        self.assertNotContains(response, 'PRIVATE DRAFT ACTIVITY')
        self.assertContains(response, self.place.get_absolute_url())
        self.assertNotContains(response, 'PRIVATE PENDING REVIEW')
        self.assertNotContains(response, 'aggregateRating')

    def test_activity_detail_has_local_group_parent_and_no_pending_revision(self):
        from catalog.models import VolunteerPlaceRevision
        VolunteerPlaceRevision.objects.create(activity=self.activity, author=self.owner, payload={'description_az':'PRIVATE CANDIDATE'}, status='pending')
        response = self.client.get(f'/activities/{self.activity.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yerli əlavə')
        self.assertContains(response, 'Şənbə 10:00')
        self.assertContains(response, self.place.get_absolute_url())
        self.assertNotContains(response, 'PRIVATE CANDIDATE')
        self.assertContains(response, '25')

    def test_card_map_and_seo_share_price_and_translation(self):
        from catalog.controllers.place_controller import PlaceController
        from catalog.services.seo import build_place_seo_payload
        from django.template.loader import render_to_string
        data = self.present(self.place, 'en')
        with override('en'):
            card = render_to_string('catalog/includes/place_card.html', {'place':self.place})
            mapped = PlaceController.build_default()._serialize_map_places([self.place], language_code='en')[0]
            seo = build_place_seo_payload(self.place, RequestFactory().get('/en/'), 'en')
        self.assertIn(data['prices']['label'], card)
        self.assertEqual(mapped['price'], data['prices']['label'])
        schema = json.loads(seo['schema_json'])
        self.assertEqual(schema['name'], data['name'])
        self.assertEqual(schema.get('offers', []), data['prices']['schema_offers'])
        self.assertEqual(self.place.category.code, 'EDU')
        self.assertEqual(data['placeholder_icon'], 'EDU')

    @override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True, ANALYTICS_IDENTITY_HASH_KEY='stage18-synthetic-key')
    def test_subject_views_do_not_create_place_events_or_invent_history(self):
        first = self.client.get(f'/organizations/{self.org.public_id}/')
        second = self.client.get(f'/activities/{self.activity.pk}/')
        self.assertEqual((first.status_code, second.status_code), (200, 200))
        self.assertEqual(FunnelEvent.objects.filter(event_type='organization_view', subject_type='organization', subject_id=self.org.pk, schema_version=2).count(), 1)
        self.assertEqual(FunnelEvent.objects.filter(event_type='activity_view', subject_type='activity', subject_id=self.activity.pk, schema_version=2).count(), 1)
        self.assertFalse(FunnelEvent.objects.filter(event_type__in=['place_view','place_open']).exists())

    def test_invalid_legacy_contact_does_not_crash_and_uses_valid_active_fallback(self):
        from catalog.models import Place
        Place.objects.filter(pk=self.place.pk).update(website='http://[malformed')
        self.place.refresh_from_db()
        data = self.present(self.place)
        self.assertEqual(data['contacts']['website_url'], 'https://example.invalid')

    def test_local_phone_keeps_whatsapp_local(self):
        from catalog.models import Place
        Place.objects.filter(pk=self.place.pk).update(phone1='+994501111111', phone2='', phone3='')
        Organization.objects.filter(pk=self.org.pk).update(whatsapp='+994502222222')
        self.place.refresh_from_db()
        self.assertEqual(self.present(self.place)['contacts']['whatsapp_url'], 'https://wa.me/994501111111')

    @override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True, ANALYTICS_IDENTITY_HASH_KEY='stage18-synthetic-key')
    def test_repeated_tracking_on_one_request_does_not_duplicate_subject(self):
        from catalog.services.tracking import track_subject_view
        response = self.client.get(f'/organizations/{self.org.public_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(track_subject_view(request=response.wsgi_request, subject=self.org))
        self.assertEqual(FunnelEvent.objects.filter(event_type='organization_view', subject_id=self.org.pk).count(), 1)

    def test_required_trial_terms_and_category_placeholder_are_visible(self):
        PricingPlan.objects.filter(offering_group=self.group).update(is_required=True, is_trial=True)
        activity = self.client.get(f'/en/activities/{self.activity.pk}/')
        self.assertContains(activity, 'Required payment')
        self.assertContains(activity, 'Trial class')
        place = self.client.get(self.place.get_absolute_url())
        self.assertContains(place, 'data-category-placeholder')

    def test_phone_endpoint_rechecks_contact_inheritance_after_detach(self):
        from catalog.models import Place
        from django.core.cache import cache
        cache.clear()
        Place.objects.filter(pk=self.place.pk).update(phone1='', phone2='', phone3='')
        url = reverse('place_phone_reveal', args=[self.place.pk])
        before = self.client.post(url)
        self.assertEqual(before.status_code, 200)
        self.assertEqual(before.json()['phones'][0]['number'], self.org.phone)
        organization_ownership.detach(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk, expected_ownership_version=1)
        self.assertEqual(self.client.post(url).status_code, 404)

    @override_settings(LOCAL_ANALYTICS_STORAGE_ENABLED=True, ANALYTICS_IDENTITY_HASH_KEY='stage18-synthetic-key')
    def test_localized_urls_and_hidden_subject_have_no_events(self):
        from catalog.services.public_presentation import public_url
        for lang in ('az','ru','en'):
            prefix = '' if lang == 'az' else '/' + lang
            for obj, suffix in ((self.org, f'/organizations/{self.org.public_id}/'), (self.activity, f'/activities/{self.activity.pk}/')):
                self.assertEqual(public_url(obj, lang), prefix + suffix)
        Organization.objects.filter(pk=self.org.pk).update(status='draft')
        self.assertEqual(self.client.get(f'/organizations/{self.org.public_id}/').status_code, 404)
        self.assertFalse(FunnelEvent.objects.filter(event_type='organization_view').exists())
