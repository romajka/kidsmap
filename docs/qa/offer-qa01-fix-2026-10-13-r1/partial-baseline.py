"""Separate pre-patch source probe; writes only disposable fictional test DB."""
import hashlib,json,subprocess,sys,types,unittest
from pathlib import Path
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.runner import DiscoverRunner
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp'/P.name;e=json.loads((P/'entry.json').read_text())
from catalog import services
provenance={}
for name in ['pricing_plans','publication']:
 file=f'src/catalog/services/{name}.py';raw=subprocess.check_output(['git','show',e['HEAD']+':'+file],cwd=R)
 assert hashlib.sha256(raw).hexdigest()==e['files'][file]
 path=S/('baseline-'+name+'.py');path.write_bytes(raw);mod=types.ModuleType('catalog.services.'+name);mod.__file__=str(path);mod.__package__='catalog.services';sys.modules[mod.__name__]=mod;setattr(services,name,mod);exec(compile(raw,str(path),'exec'),mod.__dict__);provenance[file]=hashlib.sha256(raw).hexdigest()
from catalog.models import Activity,OfferingGroup,PricingPlan
from catalog.testcases.utils import create_ready_place
from catalog.services.volunteer_places import review_form
from catalog.services.place_readiness import evaluate_form_readiness
class PartialBaseline(TestCase):
 def test_prepatch_partial_review_loses_existing_group_pricing(self):
  place=create_ready_place(with_pricing_plan=False,district='baku_yasamal',city='baku',schedule_mode='always_open')
  activity=Activity.objects.create(place=place,name_az='Fictional baseline activity',status='published')
  group=OfferingGroup.objects.create(activity=activity,name_az='Fictional baseline group')
  PricingPlan.objects.create(offering_group=group,product_type='lesson',price='20')
  actor=get_user_model().objects.create_superuser(username='fictional_partial_baseline',email='baseline@example.invalid',password=None)
  revision=services.publication.propose(actor=actor,target_type='place',target_id=place.pk,patch={'name_en':'Fictional partial name'},schema_version=services.publication.SCHEMA_VERSION,expected_version=place.content_version,revision_version=0,submit=True)
  form=review_form(revision);valid=form.is_valid();ready=evaluate_form_readiness(form,form.instance)
  price_missing=any(issue.code=='price' for issue in ready.issues)
  proof={'source':'both changed services loaded from exact pre-patch HEAD matching entry hashes','hashes':provenance,'partial_payload_fields':revision.changed_fields,'form_valid':valid,'price_missing':price_missing,'issues':[{'code':i.code,'field':i.field,'message':str(i.message)} for i in ready.issues],'is_ready':ready.is_ready,'group_active':OfferingGroup.objects.filter(pk=group.pk,archived_at__isnull=True).exists(),'actual_price':'20','ui_baseline_finding':'OFFER-QA-09, independent of group-removal repair'}
  (P/'partial-baseline.json').write_text(json.dumps(proof,indent=2))
  self.assertTrue(price_missing)
  self.assertFalse(ready.is_ready)
runner=DiscoverRunner(verbosity=1,interactive=False);runner.setup_test_environment();db=runner.setup_databases()
try:result=runner.run_suite(unittest.defaultTestLoader.loadTestsFromTestCase(PartialBaseline))
finally:runner.teardown_databases(db);runner.teardown_test_environment()
raise SystemExit(0 if result.wasSuccessful() else 1)
