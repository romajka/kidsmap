"""One audit-only regression probe; no application source changes."""
import json,unittest
from pathlib import Path
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.runner import DiscoverRunner
from catalog.models import PricingPlan
from catalog.services import publication
from catalog.services.pricing_plans import serialize_nested_pricing,replace_group_pricing_plans,place_pricing_records,build_public_price_summary
from catalog.testcases.test_task33_pricing import GroupPricingTests
HERE=Path(__file__).resolve().parent
class RemovedGroupProbe(TestCase):
    setUp=GroupPricingTests.setUp
    def test_approved_omission_archives_group(self):
        replace_group_pricing_plans(self.group,[{'product_type':'lesson','price':'20'}])
        replace_group_pricing_plans(self.other,[{'product_type':'lesson','price':'80'}])
        removed_plan=PricingPlan.objects.get(offering_group=self.other)
        actor=get_user_model().objects.create_superuser(username='fictional_offerqa01',email='offerqa01@example.invalid',password=None)
        tree=serialize_nested_pricing(self.place)
        tree['activities'][0]['groups']=[g for g in tree['activities'][0]['groups'] if g['id']!=self.other.pk]
        revision=publication.propose(actor=actor,target_type='place',target_id=self.place.pk,patch={'nested_pricing':tree},schema_version=publication.SCHEMA_VERSION,expected_version=self.place.content_version,revision_version=0,submit=True)
        self.other.refresh_from_db()
        self.assertIsNone(self.other.archived_at)
        self.assertIn(removed_plan.pk,list(place_pricing_records(self.place).values_list('pk',flat=True)))
        publication.review(actor=actor,revision_id=revision.pk,version=revision.version,approve=True)
        self.other.refresh_from_db();revision.refresh_from_db();self.place.refresh_from_db()
        state={'revision_status':revision.status,'candidate_omitted_group':all(g['id']!=self.other.pk for g in revision.payload['nested_pricing']['activities'][0]['groups']),'group_archived':self.other.archived_at is not None,'removed_tariff_public':removed_plan.pk in list(place_pricing_records(self.place).values_list('pk',flat=True)),'history_group_retained':type(self.other).objects.filter(pk=self.other.pk).exists(),'history_tariff_retained':PricingPlan.objects.filter(pk=removed_plan.pk).exists(),'public_max_price':str(build_public_price_summary(self.place,'ru')['max_price'])}
        (HERE/'probe-state.json').write_text(json.dumps(state,indent=2))
        self.assertIsNotNone(self.other.archived_at,'OFFER-QA-01: approved omitted group remains active/public')
runner=DiscoverRunner(verbosity=2,interactive=False)
runner.setup_test_environment()
db=runner.setup_databases()
try:
 result=runner.run_suite(unittest.defaultTestLoader.loadTestsFromTestCase(RemovedGroupProbe))
finally:
 runner.teardown_databases(db);runner.teardown_test_environment()
raise SystemExit(0 if result.wasSuccessful() else 1)
