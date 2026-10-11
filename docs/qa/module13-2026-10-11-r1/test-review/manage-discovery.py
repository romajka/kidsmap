"""Actual manage.main argument wiring; DISCOVERY ONLY, no test execution/DB create."""
import importlib.util,json,os,runpy,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;QA=P.parent;ROOT=P.parents[3]
sys.stdout.reconfigure(encoding='utf-8')
sys.argv=[str(QA/'run.py'),'audit-bootstrap'];runpy.run_path(str(QA/'run.py'),run_name='__qa_bootstrap__')
from django.conf import settings
from config.test_runner import KidsMapTestRunner
def flat(suite):
    for case in suite:
        if isinstance(case,unittest.TestSuite):yield from flat(case)
        else:yield case.id()
class DiscoveryRelay(KidsMapTestRunner):
    def run_tests(self,test_labels,**kwargs):
        import catalog
        ids=list(flat(super().build_suite(test_labels)))
        result={'purpose':'DISCOVERY ONLY; not a test PASS result','argv':sys.argv,'cwd':os.getcwd(),'forwarded_labels':list(test_labels),'parallel':self.parallel,'base_runner':'config.test_runner.KidsMapTestRunner','source_runner':str(Path(__import__('config.test_runner',fromlist=['x']).__file__).resolve()),'catalog_file':catalog.__file__,'catalog_path':list(catalog.__path__),'count':len(ids),'ids':ids,'database_created':False,'tests_executed':0}
        (P/'manage-discovery.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k!='ids'},indent=2))
        return 0
settings.TEST_RUNNER='__main__.DiscoveryRelay'
spec=importlib.util.spec_from_file_location('qa_actual_manage',ROOT/'manage.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
sys.argv=[str(ROOT/'manage.py'),'test','--parallel','1'];mod.main()
