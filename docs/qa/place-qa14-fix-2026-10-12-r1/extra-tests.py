import json,time,sys
from pathlib import Path
from config.test_runner import KidsMapTestRunner
HERE=Path(__file__).resolve().parent
labels=['acl_probes','gap_probes']+['catalog.testcases.'+m for m in ['test_place_rejection_feedback','test_place_qa03_pricing_rebase','test_place_qa04_manual_location','test_task33_place_nature_localization','test_place_qa08_district_localization']]
runner=KidsMapTestRunner(verbosity=1,interactive=False);old=runner.run_suite;counts={};start=time.monotonic()
def run(suite,**kw):
 counts['discovered']=suite.countTestCases();result=old(suite,**kw);counts.update(executed=result.testsRun,failures=[{'id':t.id(),'trace':s} for t,s in result.failures],errors=[{'id':t.id(),'trace':s} for t,s in result.errors],skipped=[{'id':t.id(),'reason':s} for t,s in result.skipped]);return result
runner.run_suite=run;status=runner.run_tests(labels);counts.update(labels=labels,exit=status,seconds=time.monotonic()-start);(HERE/'extra-tests-result.json').write_text(json.dumps(counts,indent=2));sys.exit(status)
