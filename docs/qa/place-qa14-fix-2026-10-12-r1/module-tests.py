"""One final module01 corpus, not the global project suite."""
import json,sys,time
from pathlib import Path
from config.test_runner import KidsMapTestRunner
from django.conf import settings
HERE=Path(__file__).resolve().parent
names=['test_place_candidate_conflict_recovery','test_place_admin_conflict_retention','test_task33_place_continuous','test_task33_publication','test_task33_drafts','photo_workflow','image_uploads','owner','test_volunteer_admin','test_volunteer_dashboard','test_admin_candidate_cover','test_admin_legacy_price_preservation','test_admin_i18n','pricing_plans','pricing_plans_relational','place_card_validation','permanent_place_wizard','place_taxonomy_admin']
labels=['catalog.testcases.'+n for n in names]
settings.DATABASES['default']['TEST']['NAME']='test_qa14_module01_final_20261012_r1'
extra=HERE.parents[2]/'.tmp/module01-full-2026-10-12-r1/integration/python-deps'
if extra.is_dir():sys.path.insert(0,str(extra))
runner=KidsMapTestRunner(verbosity=1,interactive=False,parallel=4)
start=time.monotonic();count={}
original=runner.run_suite
def run_suite(suite,**kwargs):
 count['discovered']=suite.countTestCases()
 result=original(suite,**kwargs)
 count.update(executed=result.testsRun,failures=[{'id':t.id(),'trace':trace} for t,trace in result.failures],errors=[{'id':t.id(),'trace':trace} for t,trace in result.errors],skipped=[{'id':t.id(),'reason':reason} for t,reason in result.skipped])
 return result
runner.run_suite=run_suite
exit_code=runner.run_tests(labels)
count.update(labels=labels,exit=exit_code,seconds=time.monotonic()-start,database=settings.DATABASES['default']['TEST']['NAME'],global_corpus=False)
(HERE/'module-tests-result.json').write_text(json.dumps(count,indent=2));sys.exit(exit_code)
