"""Regression contracts for audit points 5–9; disposable synthetic data only."""
import json
import re
from collections import Counter
from datetime import timedelta
from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from catalog.forms import OwnerPlaceCreateForm, OwnerPlaceEditForm, PlaceScheduleEditorFormMixin
from catalog.domain_admin.place import PlaceAdminForm
from catalog.models import Activity, Event, OfferingGroup, Organization, Place, PricingPlan, SiteSettings, Specialist
from catalog.services import publication, organization_ownership, specialist_domain
from catalog.services.content_quality import public_place_queryset
from catalog.services.place_schedule import serialize_place_schedule, sync_place_schedule
from catalog.services.pricing_plans import build_public_price_summary
from catalog.testcases.utils import create_quality_place


class ScheduleForm(PlaceScheduleEditorFormMixin, forms.Form):
    schedule = forms.CharField(required=False)
    schedule_mode = forms.CharField(required=False)

    def __init__(self, *args, instance, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        self._init_schedule_editor()

    def clean(self):
        return self._clean_schedule_editor(super().clean())


class ProjectBackendFixesTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username='fixes-owner')
        self.staff = get_user_model().objects.create_superuser(
            username='fixes-reviewer', email='reviewer@example.invalid', password='synthetic')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner,
            with_schedule_days=True, with_subcategory=True, price_from=None, price_to=None)

    def tariff(self, *, status='published', **values):
        activity = Activity.objects.create(place=self.place, name_az='Synthetic lesson', status=status)
        group = OfferingGroup.objects.create(activity=activity, name_az='Synthetic group')
        args = {'product_type': 'lesson', 'price': Decimal('137.00'), **values}
        plan = PricingPlan.objects.create(offering_group=group, **args)
        return activity, group, plan

    def organization(self):
        config = SiteSettings.get_solo()
        config.organizations_section_enabled = config.events_section_enabled = True
        config.specialists_section_enabled = True
        config.save()
        return Organization.objects.create(owner=self.owner, created_by=self.owner,
            name_az='Synthetic network', status='published', approved_at=timezone.now())

    def test_approved_activity_updates_scalar_and_catalog(self):
        activity, _, _ = self.tariff(status='draft')
        revision = publication.propose(actor=self.owner, target_type='activity', target_id=activity.pk,
            patch={'name_az': 'Approved lesson'}, schema_version=publication.SCHEMA_VERSION,
            expected_version=activity.content_version, submit=True)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal('137.00'))
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=self.place.pk)).exists())

    def test_unpriced_activity_lifecycle_preserves_legacy_scalar_price(self):
        Place.objects.filter(pk=self.place.pk).update(price_from=Decimal('80.00'), price_to=Decimal('80.00'))
        activity = Activity.objects.create(place=self.place, name_az='Unpriced lesson', status='draft')
        revision = publication.propose(actor=self.owner, target_type='activity', target_id=activity.pk,
            patch={'name_az': 'Approved unpriced lesson'}, schema_version=publication.SCHEMA_VERSION,
            expected_version=activity.content_version, submit=True)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version, approve=True)
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal('80.00'))
        activity.refresh_from_db()
        publication.unpublish(actor=self.staff, target_type='activity', target_id=activity.pk,
                              expected_version=activity.content_version)
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal('80.00'))

    def test_unpublished_activity_removes_hidden_price_but_retains_other_tariffs(self):
        activity, _, _ = self.tariff()
        direct = PricingPlan.objects.create(place=self.place, product_type='lesson', price=Decimal('200.00'))
        publication.unpublish(actor=self.staff, target_type='activity', target_id=activity.pk,
                              expected_version=activity.content_version)
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal('200.00'))
        direct.delete()
        self.place.refresh_from_db()
        self.assertIsNone(self.place.price_from)
        self.assertIsNone(build_public_price_summary(self.place, 'ru')['min_price'])

    def test_nested_non_scalar_prices_are_catalog_visible_and_hidden_drafts_are_not(self):
        activity, _, plan = self.tariff(currency='USD')
        for values in ({'currency': 'USD'}, {'currency': 'AZN', 'price_kind': 'on_request', 'price': None},
                       {'price_kind': 'free', 'price': Decimal('0')}):
            with self.subTest(values=values):
                for key, value in values.items():
                    setattr(plan, key, value)
                plan.save()
                self.place.refresh_from_db()
                self.assertTrue(public_place_queryset(Place.objects.filter(pk=self.place.pk)).exists())
        publication.unpublish(actor=self.staff, target_type='activity', target_id=activity.pk,
                              expected_version=activity.content_version)
        self.assertFalse(public_place_queryset(Place.objects.filter(pk=self.place.pk)).exists())

    def test_malformed_schedule_returns_field_errors_in_owner_and_admin(self):
        for form_class in (OwnerPlaceCreateForm, OwnerPlaceEditForm, PlaceAdminForm):
            for raw in ('[null]', '[{}]', '{broken', '{"days":true}', '[{"weekday":"mon","intervals":3}]'):
                with self.subTest(form=form_class.__name__, raw=raw):
                    form = form_class(data={'structured_schedule': raw}, instance=self.place)
                    self.assertFalse(form.is_valid())
                    self.assertIn('structured_schedule', form.errors)

    def test_invalid_schedule_cannot_save_over_existing_hours(self):
        original = serialize_place_schedule(self.place)
        for raw in ('{broken', '42', '[null]', '{"days":{}}', '[{"weekday":"mon","intervals":[null]}]'):
            with self.subTest(raw=raw):
                form = ScheduleForm(data={'structured_schedule': raw, 'schedule_mode': 'regular'}, instance=self.place)
                self.assertFalse(form.is_valid())
                with self.assertRaises(ValueError):
                    form.save_schedule(self.place)
                self.assertEqual(serialize_place_schedule(self.place), original)

    def test_missing_schedule_preserves_hours_and_explicit_closed_is_valid(self):
        original = serialize_place_schedule(self.place)
        missing = ScheduleForm(data={}, instance=self.place)
        self.assertTrue(missing.is_valid(), missing.errors)
        missing.save_schedule(self.place)
        self.assertEqual(serialize_place_schedule(self.place), original)
        closed = [{'weekday': day['weekday'], 'is_closed': True, 'intervals': []} for day in original]
        form = ScheduleForm(data={'structured_schedule': json.dumps(closed)}, instance=self.place)
        self.assertTrue(form.is_valid(), form.errors)
        form.save_schedule(self.place)
        self.assertTrue(all(day['is_closed'] for day in serialize_place_schedule(self.place)))

    def test_shared_schedule_writer_rejects_corruption_before_deleting_hours(self):
        original = serialize_place_schedule(self.place)
        with self.assertRaises(ValidationError):
            sync_place_schedule(self.place, [None])
        self.assertEqual(serialize_place_schedule(self.place), original)

    def test_owner_draft_post_reports_invalid_schedule_and_preserves_hours(self):
        from catalog.services.publication_forms import version_token
        original = serialize_place_schedule(self.place)
        self.client.force_login(self.owner)
        data = {'action': 'draft', 'publication_token': version_token(self.place),
                'structured_schedule': '{broken', 'name_az': self.place.name_az}
        response = self.client.post(reverse('owner_place_edit', args=[self.place.pk]), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('structured_schedule', response.context['form'].errors)
        self.assertEqual(serialize_place_schedule(self.place), original)

    def test_organization_event_uses_approved_venue_fact(self):
        org = self.organization()
        now = timezone.now()
        Event.objects.create(owner=self.owner, name='Synthetic event', name_az='Synthetic event',
            category=self.place.category, organizer_organization=org, related_place=self.place,
            status='published', start_datetime=now+timedelta(days=1), end_datetime=now+timedelta(days=1,hours=1),
            event_format='physical', venue_snapshot={'label': 'Approved historic venue', 'address': 'Historic address'})
        response = self.client.get(reverse('organization_detail', args=[org.public_id]))
        self.assertEqual(response.context['org_events'][0]['venue_name'], 'Approved historic venue')
        Place.objects.filter(pk=self.place.pk).update(name_az='Later name', status='draft', is_active=False)
        response = self.client.get(reverse('organization_detail', args=[org.public_id]))
        self.assertEqual(response.context['org_events'][0]['venue_name'], 'Approved historic venue')

    def test_future_employment_has_explicit_date_and_state(self):
        org = self.organization()
        person = get_user_model().objects.create_user(username='fixes-person')
        specialist = Specialist.objects.create(name='Synthetic specialist', status='published', is_active=True,
            verified_person_user=person, person_verified_at=timezone.now())
        start = timezone.localdate()+timedelta(days=30)
        employment = specialist_domain.propose_employment(actor=self.owner, specialist_id=specialist.pk,
            organization_id=org.pk, role='Teacher', start_date=start)
        specialist_domain.confirm_employment(actor=self.owner, employment_id=employment.pk,
            side='organization', expected_version=employment.version)
        employment.refresh_from_db()
        specialist_domain.confirm_employment(actor=person, employment_id=employment.pk,
            side='person', expected_version=employment.version)
        for lang, label in (('ru', 'Начнёт работу'), ('en', 'Starts on'), ('az', 'İşə başlayır')):
            with self.subTest(lang=lang):
                from django.utils.translation import override
                with override(lang):
                    response = self.client.get(reverse('organization_detail', args=[org.public_id]))
                row = response.context['org_specialists'][0]
                self.assertEqual(row['temporal_state'], 'future')
                self.assertEqual(row['start_date'], start)
                self.assertContains(response, label)
        Organization.objects.filter(pk=org.pk).update(ownership_version=org.ownership_version+1)
        response = self.client.get(reverse('organization_detail', args=[org.public_id]))
        self.assertEqual(response.context['org_specialists'], [])

    def test_batch_organization_excludes_stale_affiliation_and_draft_activities(self):
        org = self.organization()
        organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=org.pk)
        public, _, _ = self.tariff()
        private, _, _ = self.tariff(status='draft')
        response = self.client.get(reverse('organization_detail', args=[org.public_id]))
        self.assertEqual([a['id'] for a in response.context['branches'][0]['activities']], [public.pk])
        self.assertNotContains(response, '/activities/'+str(private.pk)+'/')
        Organization.objects.filter(pk=org.pk).update(ownership_version=org.ownership_version+1)
        response = self.client.get(reverse('organization_detail', args=[org.public_id]))
        self.assertEqual(response.context['branches'], [])

    def test_organization_branch_query_budget_does_not_grow_per_branch(self):
        org = self.organization()
        organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=org.pk)
        url = reverse('organization_detail', args=[org.public_id])
        self.client.get(url)
        with CaptureQueriesContext(connection) as one:
            response = self.client.get(url)
        self.assertEqual(response.context['branches_count'], 1)
        for _ in range(4):
            branch = create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True)
            organization_ownership.request_join(actor=self.owner, place_id=branch.pk, organization_id=org.pk)
        self.client.get(url)
        with CaptureQueriesContext(connection) as five:
            response = self.client.get(url)
        print('BACKEND_QUERY_BUDGET', {'one': len(one), 'five': len(five)})
        if len(five) > len(one)+2:
            # Synthetic fixture queries only; print table/operation aggregates,
            # never SQL values or application/user records.
            def tables(queries):
                return Counter((q['sql'].split()[0], tuple(re.findall(r'FROM "([^"]+)"', q['sql']))) for q in queries)
            print('BACKEND_QUERY_TABLE_GROWTH', tables(five)-tables(one))
        self.assertEqual(response.context['branches_count'], 5)
        self.assertLessEqual(len(five), len(one)+2)

    def test_organization_activity_prices_keep_constant_query_budget(self):
        org = self.organization()
        organization_ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=org.pk)
        self.tariff()
        url = reverse('organization_detail', args=[org.public_id])
        self.client.get(url)
        with CaptureQueriesContext(connection) as one:
            response = self.client.get(url)
        self.assertEqual(response.context['branches'][0]['activities'][0]['prices']['min_price'], Decimal('137.00'))
        for number in range(4):
            branch = create_quality_place(owner=self.owner, created_by=self.owner, with_subcategory=True)
            organization_ownership.request_join(actor=self.owner, place_id=branch.pk, organization_id=org.pk)
            activity = Activity.objects.create(place=branch, name_az='Lesson '+str(number), status='published')
            group = OfferingGroup.objects.create(activity=activity, name_az='Group')
            PricingPlan.objects.create(offering_group=group, product_type='lesson', price=Decimal('150.00'))
        self.client.get(url)
        with CaptureQueriesContext(connection) as five:
            response = self.client.get(url)
        print('BACKEND_ACTIVITY_QUERY_BUDGET', {'one': len(one), 'five': len(five)})
        self.assertEqual(response.context['branches_count'], 5)
        self.assertEqual(len([a for b in response.context['branches'] for a in b['activities']]), 5)
        self.assertLessEqual(len(five), len(one)+2)
