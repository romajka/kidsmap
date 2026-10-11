"""Django test discovery only; no test execution or database creation."""
import collections,json,runpy,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;QA=P.parent;ROOT=P.parents[3]
sys.argv=[str(QA/'run.py'),'audit-bootstrap'];runpy.run_path(str(QA/'run.py'),run_name='__qa_bootstrap__')
from django.conf import settings
from django.test.utils import get_runner
def flat(suite):
    for case in suite:
        if isinstance(case,unittest.TestSuite):yield from flat(case)
        else:yield case.id()
runner=get_runner(settings)(verbosity=0,interactive=False)
normal=list(flat(runner.build_suite(['catalog'])))
ci=list(flat(runner.build_suite([])))
full=json.loads((P/'full-inventory.json').read_text())
missing=sorted(set(full['ids'])-set(normal))
modules=collections.Counter(x.rsplit('.',2)[0] for x in missing)
result={'default_catalog_count':len(normal),'default_no_label_ci_count':len(ci),'ci_ids':ci,'full_explicit_count':full['unique_count'],'missing_count':len(missing),'missing_ids':missing,'missing_modules':dict(modules),'wrapper':'scripts/run_kidsmap_tests.sh full -> catalog only','ci':'.github/workflows/deploy.yml:78 manage.py test --parallel 1','fresh_discovery_only':True}
(P/'discovery-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('missing_ids','ci_ids')},indent=2))
