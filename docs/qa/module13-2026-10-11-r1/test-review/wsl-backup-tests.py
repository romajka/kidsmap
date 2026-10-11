"""Original backup unittest body in Linux; synthetic copied script, mocked Docker."""
import importlib.util,json,os,sys,tempfile,time,traceback,unittest,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
S=ROOT/'.tmp/module13-20261011-r1/test-review/backup-wsl';S.mkdir(parents=True,exist_ok=True)
assert S.resolve().is_relative_to((ROOT/'.tmp/module13-20261011-r1/test-review').resolve())
for key in list(os.environ):
    if key.startswith(('DJANGO_','DATABASE_','LEGACY_','REDIS_','GOOGLE_','EMAIL_','INDEXNOW_','TASK33_','ANALYTICS_','LOCAL_ANALYTICS_','OWNER_ANALYTICS_')):os.environ.pop(key)
os.environ.update(DJANGO_TESTING='1',TEMP=str(S),TMP=str(S),TMPDIR=str(S));tempfile.tempdir=str(S)
real_copy=shutil.copyfile
def posix_fixture_copy(source,target,*args,**kwargs):
    result=real_copy(source,target,*args,**kwargs)
    if Path(source).resolve()==(ROOT/'scripts/backup-db.sh').resolve():
        copied=Path(target).resolve()
        assert copied.is_relative_to(S.resolve())
        copied.write_bytes(copied.read_bytes().replace(b'\r\n',b'\n'))
    return result
shutil.copyfile=posix_fixture_copy
spec=importlib.util.spec_from_file_location('qa_existing_test_backup_db',ROOT/'scripts/tests/test_backup_db.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
records=[]
class Result(unittest.TextTestResult):
    def row(self,test,status,error=None):
        record={'id':test.id(),'status':status}
        if error:record['traceback']=''.join(traceback.format_exception(*error))
        records.append(record)
    def addSuccess(self,test):self.row(test,'PASS');super().addSuccess(test)
    def addFailure(self,test,error):self.row(test,'FAIL',error);super().addFailure(test,error)
    def addError(self,test,error):self.row(test,'ERROR',error);super().addError(test,error)
start=time.monotonic();result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(unittest.defaultTestLoader.loadTestsFromModule(mod))
code=0 if result.wasSuccessful() else 1
(P/'wsl-backup-results.json').write_text(json.dumps({'records':records,'exit_code':code,'elapsed_seconds':round(time.monotonic()-start,3),'runtime':sys.version.split()[0],'scope':'Real /bin/bash, copied synthetic script/backups with owned CRLF-to-LF transport adaptation, exported mocked Docker and compressor; no real Docker backup or production restore'},indent=2))
sys.exit(code)
