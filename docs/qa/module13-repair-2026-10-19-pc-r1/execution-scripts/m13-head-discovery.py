from pathlib import Path
import subprocess,tarfile,json,hashlib
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';D=Q/'head-donor';assert not D.exists();D.mkdir();P=Q/'head-profile';P.mkdir()
git=['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap'];paths=['src','config','catalog','test_catalog.py','manage.py','scripts','static','templates','locale','requirements.txt'];tracked=set(subprocess.check_output(git+['ls-tree','--name-only','HEAD'],text=True).splitlines());paths=[p for p in paths if p in tracked]
with (Q/'head-source.tar').open('wb') as f:subprocess.run(git+['archive','HEAD','--',*paths],stdout=f,check=True)
with tarfile.open(Q/'head-source.tar') as archive:
 assert all((D/m.name).resolve().is_relative_to(D.resolve()) and Path(m.name).name!='.env' for m in archive.getmembers())
 archive.extractall(D,filter='data')
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(D/'locale'),'--output',str(Q/'head-locales'),'--compiler','native'];p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
(P/'settings.py').write_text("from config.settings import *\nSECRET_KEY='fictional-head-discovery'\nDATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}\nCACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'m13-head-discovery'}}\nEMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'\nLOCALE_PATHS=["+repr(str(Q/'head-locales/locale'))+"]\nGOOGLE_APPLICATION_CREDENTIALS=GOOGLE_OAUTH_CLIENT_ID=GOOGLE_OAUTH_CLIENT_SECRET=GOOGLE_ANALYTICS_MEASUREMENT_ID=GOOGLE_ANALYTICS_PROPERTY_ID=INDEXNOW_KEY=''\n")
(P/'discover.py').write_text('''import sys,os,json,pkgutil
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/m13-full-r1');D=Q/'head-donor';P=Q/'head-profile'
os.environ.clear();os.environ.update(DJANGO_TESTING='1',DJANGO_SETTINGS_MODULE='settings',PATH='/usr/local/bin:/usr/bin:/bin',HOME='/tmp',LANG='C.UTF-8',PYTHONDONTWRITEBYTECODE='1');sys.dont_write_bytecode=True
sys.path[:0]=[str(P),str(D/'src'),str(D)];os.chdir(D)
from scripts.build_isolated_locales import verify
verify(Q/'head-locales/manifest.json',D/'locale')
import django;django.setup()
from config.test_runner import KidsMapTestRunner
from catalog import testcases
def flatten(s):
 for t in s:
  if hasattr(t,'_tests'):yield from flatten(t)
  else:yield t.id()
out={}
for key,labels in [('no_label',[]),('catalog',['catalog']),('exhaustive',['catalog.testcases.'+m.name for m in pkgutil.iter_modules(testcases.__path__) if not m.ispkg])]:
 ids=list(flatten(KidsMapTestRunner(verbosity=0,interactive=False).build_suite(labels)));out[key]={'raw':len(ids),'unique':len(set(ids)),'ids':sorted(set(ids))}
(Q/'head-discovery.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:{a:b for a,b in v.items() if a!='ids'} for k,v in out.items()},indent=2))
''')
p=subprocess.run(['docker','exec','m13qa04-r4-app','python',str(P/'discover.py')],capture_output=True,text=True);(Q/'head-discovery.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
d=json.loads((Q/'head-discovery.json').read_text());d['snapshot']={'head':subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip(),'archive_source_only':True,'no_database_opened_or_tests_executed':True,'real_GitHub':'NOT RUN'};(O/'evidence/head-discovery.json').write_text(json.dumps(d,indent=2));print(p.stdout)
