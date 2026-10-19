"""OFFER-QA-09: trusted partial moderation keeps current nested pricing."""
from copy import deepcopy
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Activity, OfferingGroup, PricingPlan
from catalog.services import publication
from catalog.services.place_readiness import evaluate_form_readiness
from catalog.services.pricing_plans import serialize_nested_pricing
from catalog.services.volunteer_places import review_form
from catalog.testcases.utils import create_ready_place


class PartialReviewPricingTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user('offer09_owner')
        self.staff = users.objects.create_superuser('offer09_staff', 'offer09@example.invalid', 'fictional')
        self.place = create_ready_place(owner=self.owner, created_by=self.owner,
            with_pricing_plan=False, price_from=None, price_to=None, city='baku', district='baku_yasamal')
        self.activity = Activity.objects.create(place=self.place, name_az='Fictional activity',
            category=self.place.category, subcategory=self.place.subcategory, status='published')
        self.group = OfferingGroup.objects.create(activity=self.activity, name_az='Fictional group', age_from=6, age_to=12)
        self.plan = PricingPlan.objects.create(offering_group=self.group, product_type='lesson', price=Decimal('20'))

    def propose(self, patch=None):
        self.place.refresh_from_db()
        revision = getattr(self.place, 'volunteer_revision', None)
        return publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch=patch if patch is not None else {'name_en': 'Proposed title'},
            schema_version=publication.SCHEMA_VERSION, expected_version=self.place.content_version,
            revision_version=revision.version if revision else 0, submit=True)

    def readiness(self, revision):
        form = review_form(revision)
        self.assertTrue(form.is_valid(), form.errors)
        return form, evaluate_form_readiness(form, form.instance)

    def test_name_only_candidate_counts_current_group_tariff(self):
        revision = self.propose()
        self.assertEqual(set(revision.payload), {'name_en'})
        form, readiness = self.readiness(revision)
        self.assertTrue(readiness.is_ready, readiness.issues)
        self.assertFalse(any(issue.code == 'price' for issue in readiness.issues))
        self.assertEqual(form.cleaned_data['nested_pricing']['activities'][0]['groups'][0]['pricing_plans'][0]['price'], '20.00')
        revision.refresh_from_db(); self.place.refresh_from_db(); self.plan.refresh_from_db()
        self.assertEqual(set(revision.payload), {'name_en'})
        self.assertNotEqual(self.place.name_en, 'Proposed title')
        self.assertEqual(self.plan.price, Decimal('20'))

    def test_explicit_candidate_tree_wins_over_live_prices(self):
        tree = serialize_nested_pricing(self.place)
        tree['activities'][0]['groups'][0]['pricing_plans'][0]['price'] = '35.00'
        revision = self.propose({'nested_pricing': tree})
        form, readiness = self.readiness(revision)
        self.assertTrue(readiness.is_ready)
        self.assertEqual(form.cleaned_data['nested_pricing']['activities'][0]['groups'][0]['pricing_plans'][0]['price'], '35.00')
        self.plan.refresh_from_db(); self.assertEqual(self.plan.price, Decimal('20'))

    def test_explicit_empty_candidate_tree_does_not_restore_live_price(self):
        tree = {'pricing_schema_version': 2, 'activities': []}
        form, readiness = self.readiness(self.propose({'nested_pricing': tree}))
        self.assertEqual(form.cleaned_data['nested_pricing'], tree)
        self.assertTrue(any(issue.code == 'price' for issue in readiness.issues))
        self.group.refresh_from_db(); self.assertIsNone(self.group.archived_at)
        self.assertTrue(PricingPlan.objects.filter(pk=self.plan.pk).exists())

    def test_archived_activity_and_group_do_not_satisfy_price(self):
        revision = self.propose()
        OfferingGroup.objects.filter(pk=self.group.pk).update(archived_at=timezone.now())
        form, readiness = self.readiness(revision)
        self.assertTrue(any(issue.code == 'price' for issue in readiness.issues))
        self.assertEqual(form.cleaned_data['nested_pricing']['activities'][0]['groups'], [])
        Activity.objects.filter(pk=self.activity.pk).update(archived_at=timezone.now())
        revision.refresh_from_db()
        form, readiness = self.readiness(revision)
        self.assertEqual(form.cleaned_data['nested_pricing']['activities'], [])
        self.assertTrue(any(issue.code == 'price' for issue in readiness.issues))
        self.assertTrue(PricingPlan.objects.filter(pk=self.plan.pk).exists())

    def test_inactive_or_addon_only_tariff_does_not_satisfy_price(self):
        revision = self.propose()
        for values in [{'is_active': False}, {'is_active': True, 'charge_role': 'addon', 'product_type': 'addon'}]:
            with self.subTest(values=values):
                PricingPlan.objects.filter(pk=self.plan.pk).update(**values)
                revision.refresh_from_db()
                _, readiness = self.readiness(revision)
                self.assertTrue(any(issue.code == 'price' for issue in readiness.issues))

    def test_direct_tariff_and_free_mode_still_pass(self):
        OfferingGroup.objects.filter(pk=self.group.pk).update(archived_at=timezone.now())
        direct = PricingPlan.objects.create(place=self.place, product_type='lesson', price='7')
        _, readiness = self.readiness(self.propose())
        self.assertTrue(readiness.is_ready)
        direct.delete()  # Own fixture only; exercise free mode without any tariff.
        _, readiness = self.readiness(self.propose({'price_mode': 'free'}))
        self.assertTrue(readiness.is_ready)

    def test_partial_review_is_read_only_and_post_cannot_replace_trusted_tree(self):
        revision = self.propose(); old_payload = deepcopy(revision.payload)
        old_versions = (revision.version, self.place.content_version)
        self.client.force_login(self.staff)
        response = self.client.post(reverse('admin:volunteer_review', args=[self.place.pk]),
            {'action': 'approve', 'version': revision.version - 1, 'nested_pricing': '{"activities":[]}'})
        self.assertEqual(response.status_code, 200)  # Existing review re-renders conflict.
        self.assertTrue(response.context['readiness'].is_ready)
        revision.refresh_from_db(); self.place.refresh_from_db(); self.plan.refresh_from_db()
        self.assertEqual(revision.status, 'pending')
        self.assertEqual(revision.payload, old_payload)
        self.assertEqual((revision.version, self.place.content_version), old_versions)
        self.assertEqual(self.plan.price, Decimal('20'))

    def test_stale_and_foreign_review_preserve_candidate_and_live(self):
        revision = self.propose()
        with self.assertRaises(PermissionDenied):
            publication.review(actor=self.owner, revision_id=revision.pk, version=revision.version, approve=True)
        with self.assertRaises(ValidationError):
            publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version - 1, approve=True)
        revision.refresh_from_db(); self.place.refresh_from_db(); self.plan.refresh_from_db()
        self.assertEqual(revision.status, 'pending')
        self.assertNotEqual(self.place.name_en, 'Proposed title')
        self.assertEqual(self.plan.price, Decimal('20'))
