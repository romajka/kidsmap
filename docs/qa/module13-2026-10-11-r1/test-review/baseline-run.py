"""Single isolated HEAD donor backend process after full WORKTREE suite completes."""
from pathlib import Path
import hashlib,json,os,socket,sys,time,traceback,unittest
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8',errors='backslashreplace')
compiled='--compiled-head' in sys.argv
prefix='baseline-compiled' if compiled else 'baseline'
D=ROOT/'.tmp/module13-20261011-r1/test-review/head-donor'
for key in list(os.environ):
    if key.startswith(('DJANGO_','DATABASE_','LEGACY_','REDIS_','GOOGLE_','EMAIL_','INDEXNOW_','TASK33_','ANALYTICS_','LOCAL_ANALYTICS_','OWNER_ANALYTICS_')):os.environ.pop(key)
os.environ.update(DJANGO_TESTING='1',DJANGO_DEBUG='1',DJANGO_SETTINGS_MODULE='baseline_settings',PYTHONDONTWRITEBYTECODE='1')
os.environ['KIDSMAP_QA_COMPILED_HEAD']='1' if compiled else '0'
sys.path[:0]=[str(P),str(D/'src'),str(D)]
real=socket.socket.connect
def guarded(sock,address):
    if isinstance(address,tuple) and address[0] not in ('127.0.0.1','localhost','::1'):raise RuntimeError('External network blocked by baseline QA')
    return real(sock,address)
socket.socket.connect=guarded
import django;django.setup()
import config.settings
assert Path(config.settings.__file__).resolve().is_relative_to(D.resolve())
from django.conf import settings
assert settings.TESTING and settings.DATABASES['default']['TEST']['NAME']==('test_module13_head_compiled' if compiled else 'test_module13_head')
if compiled:assert list(settings.LOCALE_PATHS)==[ROOT/'.tmp/module13-20261011-r1/test-review/head-gettext/locale']
from django.test.utils import get_runner
if '--discovery' in sys.argv:
    import ast,collections
    os.chdir(D)
    base=get_runner(settings)(verbosity=0,interactive=False,parallel=1)
    def flat(suite):
        for test in suite:
            if isinstance(test,unittest.TestSuite):yield from flat(test)
            else:yield test.id()
    imported={n.module for n in ast.walk(ast.parse((D/'src/catalog/tests.py').read_text())) if isinstance(n,ast.ImportFrom)}
    extras=['catalog.testcases.'+p.stem for p in sorted((D/'src/catalog/testcases').glob('*.py')) if not p.name.startswith('test_') and p.stem not in ('__init__','utils') and 'catalog.testcases.'+p.stem not in imported]
    no_label=list(flat(base.build_suite([])))
    catalog=list(flat(base.build_suite(['catalog'])))
    full=list(flat(base.build_suite(['catalog']+extras)))
    result={'purpose':'HEAD tracked donor DISCOVERY ONLY','cwd':str(D),'head_no_label_count':len(set(no_label)),'head_catalog_count':len(set(catalog)),'head_explicit_full_count':len(set(full)),'head_ci_missing_count':len(set(full)-set(no_label)),'head_wrapper_missing_count':len(set(full)-set(catalog)),'head_no_label_ids':no_label,'head_catalog_ids':catalog,'head_full_ids':full,'extra_labels':extras,'tests_executed':0,'database_created':False}
    (P/'head-discovery.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('_ids')},indent=2));sys.exit(0)
labels=json.loads((P/'baseline-labels.json').read_text())
records=[];base=get_runner(settings)
class Runner(base):
    def get_resultclass(self):
        parent=super().get_resultclass() or unittest.TextTestResult
        class Result(parent):
            def item(self,test,status,error=None,subtest=None):
                row={'id':test.id(),'status':status}
                if error:row['traceback']=''.join(traceback.format_exception(*error))
                if subtest:row['subtest_id']=subtest.id()
                records.append(row)
                with (P/(prefix+'-observations.jsonl')).open('a',encoding='utf-8') as h:h.write(json.dumps(row)+'\n')
            def addSuccess(self,test):self.item(test,'PASS');super().addSuccess(test)
            def addFailure(self,test,error):self.item(test,'FAIL',error);super().addFailure(test,error)
            def addError(self,test,error):self.item(test,'ERROR',error);super().addError(test,error)
            def addSkip(self,test,reason):self.item(test,'SKIP');super().addSkip(test,reason)
            def addSubTest(self,test,subtest,error):
                if error:self.item(test,'SUBTEST_FAIL',error,subtest)
                super().addSubTest(test,subtest,error)
        return Result
start=time.monotonic();code=2
try:code=1 if Runner(verbosity=1,interactive=False,parallel=1).run_tests(labels) else 0
finally:
    (P/(prefix+'-results.json')).write_text(json.dumps({'labels':labels,'exit_code':code,'duration_seconds':round(time.monotonic()-start,3),'records':records,'profile':'HEAD tracked app with '+('fresh HEAD GNU gettext output' if compiled else 'frozen actual WORKTREE runtime .mo')+', same test profile, separate test DB'},indent=2),encoding='utf-8')
sys.exit(code)
