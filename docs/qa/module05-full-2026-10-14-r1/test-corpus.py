import json,unittest
from pathlib import Path
from django.conf import settings
from django.db import connection
from django.test.runner import DiscoverRunner
from catalog.testcases.utils import ensure_quality_subcategory
P=Path(__file__).resolve().parent
labels=['catalog.testcases.'+name for name in [
 'test_task33_program_workspace','test_task33_pricing','test_task33_public_details',
 'test_organization_detach_transport','test_place_json_and_pricing_modes','pricing_plans_relational',
 'pricing_plans','test_legacy_pricing_notes','test_task33_publication','test_task33_permissions',
 'place_readiness','test_public_filter_consistency','test_task33_admin_editors',
 'test_offer_qa01_group_removal','test_offer_qa03_error_targets','test_offer_qa07_stale_draft_restore',
 'test_offer_qa08_program_declined','test_offer_qa09_partial_review_pricing',
 'test_task33_drafts','test_task33_place_continuous']]
labels+=['catalog.testcases.test_volunteer_admin.VolunteerAccessTests.test_admin_and_volunteer_use_identical_revision_readiness']
settings.MEDIA_ROOT=settings.BASE_DIR/'.tmp/module05-full-2026-10-14-r1/unit-media';settings.PRIVATE_MEDIA_ROOT=settings.BASE_DIR/'.tmp/module05-full-2026-10-14-r1/unit-private-media';settings.SESSION_COOKIE_NAME='sessionid';settings.CSRF_COOKIE_NAME='csrftoken'
class Runner(DiscoverRunner):
 def build_suite(self,*args,**kwargs):
  suite=super().build_suite(*args,**kwargs)
  def flat(s):
   for t in s:
    if isinstance(t,unittest.TestSuite):yield from flat(t)
    else:yield t.id()
  ids=list(flat(suite));assert len(ids)==len(set(ids));(P/'test-discovery.json').write_text(json.dumps({'labels':labels,'count':len(ids),'method_ids':ids},indent=2));return suite
 def setup_databases(self,**kwargs):
  result=super().setup_databases(**kwargs)
  assert connection.settings_dict['NAME']=='test_module05full_20261014_r1'
  for code in ['EDU','TECH','MUS','SPRT']:ensure_quality_subcategory(code)
  return result
runner=Runner(verbosity=2,interactive=False,keepdb=True)
result=runner.run_tests(labels);raise SystemExit(bool(result))
