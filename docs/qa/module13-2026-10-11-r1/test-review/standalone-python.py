"""Existing no-Django script unit tests; original assertions, owned temporary files."""
import importlib.util,json,os,runpy,sys,tempfile,time,traceback,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;QA=P.parent;ROOT=QA.parents[2]
S=ROOT/'.tmp/module13-20261011-r1/test-review/standalone';S.mkdir(parents=True,exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(S);tempfile.tempdir=str(S)
real_mkdtemp=tempfile.mkdtemp
def own_mkdtemp(*args,**kwargs):
    if Path(kwargs.get('dir') or S).resolve()==(ROOT/'.tmp').resolve():kwargs['dir']=str(S)
    return real_mkdtemp(*args,**kwargs)
tempfile.mkdtemp=own_mkdtemp
sys.argv=[str(QA/'run.py'),'audit-bootstrap'];runpy.run_path(str(QA/'run.py'),run_name='__qa_bootstrap__')
records=[];suite=unittest.TestSuite()
for filename in ['test_local_map_environment.py','test_build_isolated_locales.py','test_backup_db.py']:
    f=ROOT/'scripts/tests'/filename
    name='qa_existing_'+f.stem
    spec=importlib.util.spec_from_file_location(name,f);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(mod))
class Result(unittest.TextTestResult):
    def entry(self,test,status,err=None,reason=None):
        row={'id':test.id(),'status':status}
        if err:row['traceback']=''.join(traceback.format_exception(*err))
        if reason:row['reason']=reason
        records.append(row)
    def addSuccess(self,test):self.entry(test,'PASS');super().addSuccess(test)
    def addFailure(self,test,err):self.entry(test,'FAIL',err);super().addFailure(test,err)
    def addError(self,test,err):self.entry(test,'ERROR',err);super().addError(test,err)
    def addSkip(self,test,reason):self.entry(test,'SKIP',reason=reason);super().addSkip(test,reason)
started=time.monotonic();result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
counts={s:sum(r['status']==s for r in records) for s in sorted({r['status'] for r in records})}
exit_code=0 if result.wasSuccessful() else 1
(P/'standalone-results.json').write_text(json.dumps({'counts':counts,'records':records,'exit_code':exit_code,'duration_seconds':round(time.monotonic()-started,3),'scratch':str(S),'temp_instrumentation':'tempfile allocation rerouted into own ignored scratch; assertions unchanged'},indent=2),encoding='utf-8')
print(json.dumps({'counts':counts,'exit_code':exit_code}),flush=True);sys.exit(exit_code)
