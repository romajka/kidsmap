import os,sys,socket,json,importlib.util,unittest,time,subprocess
from pathlib import Path
ROOT=Path.cwd().resolve();HERE=ROOT/'.tmp/module01-completion-2026-10-12-r1/integration';OUT=ROOT/'docs/qa/module01-completion-2026-10-12-r1/integration'
for k in list(os.environ):
 if k not in {'PATH','LANG','LC_ALL','TZ'}: os.environ.pop(k)
os.environ.update(DJANGO_TESTING='1',DJANGO_SETTINGS_MODULE='settings',PYTHONDONTWRITEBYTECODE='1')
sys.path[:0]=[str(HERE),str(ROOT/'.tmp/module01-full-2026-10-12-r1/integration/python-deps'),str(ROOT/'src')]
cfg=json.loads((ROOT/'.tmp/start-local-2026-10-12-r1/config.json').read_text())
orig=socket.socket.connect
origex=socket.socket.connect_ex
def ok(a): return isinstance(a,tuple) and len(a)>1 and a[0] in ('127.0.0.1','localhost') and a[1]==cfg['pg_port']
def connect(s,a):
 if not ok(a): raise RuntimeError('QA egress denied')
 return orig(s,a)
def connectex(s,a):
 if not ok(a): raise RuntimeError('QA egress denied')
 return origex(s,a)
socket.socket.connect=connect;socket.socket.connect_ex=connectex
sp=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py');b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
m=b.verify(HERE/'locales/manifest.json',ROOT/'locale');assert set(m['locales'])=={'ru','az','en'}
import django;django.setup()
from django.conf import settings
if sys.argv[1]=='full':settings.DATABASES['default']['TEST']['NAME']='test_completion01_integration_full_20261012_r1'
if sys.argv[1] in {'repair','repro'}:settings.DATABASES['default']['TEST']['NAME']='test_completion01_integration_repair_20261012_r1'
assert settings.TESTING and len(settings.LOCALE_PATHS)==1 and settings.DATABASES['default']['TEST']['NAME'] in {'test_completion01_integration_20261012_r1','test_completion01_integration_repair_20261012_r1','test_completion01_integration_full_20261012_r1'}
from config.test_runner import KidsMapTestRunner
runner=KidsMapTestRunner(verbosity=1,interactive=False,parallel=4 if sys.argv[1]=='full' else 1)
def flat(s):
 for t in s:
  if isinstance(t,unittest.TestSuite):yield from flat(t)
  else:yield t
labels=['catalog.testcases.'+p.stem for p in sorted((ROOT/'src/catalog/testcases').glob('*.py')) if p.stem!='__init__']
def suite_for(ls):return {t.id():t for t in flat(runner.build_suite(ls))}
if sys.argv[1]=='discovery':
 no=suite_for([]);wrapper=suite_for(['catalog']);explicit=suite_for(labels)
 chosen=dict(no);chosen.update(explicit)
 data={'no_label_count':len(no),'wrapper_full_count':len(wrapper),'explicit_catalog_count':len(explicit),'unique_full_count':len(chosen),'labels':labels,'missing_no_label':sorted(set(chosen)-set(no)),'missing_wrapper_full':sorted(set(chosen)-set(wrapper)),'all_test_ids':sorted(chosen),'failed_import_ids':[x for x in chosen if '_FailedTest' in x]}
 (OUT/'discovery.json').write_text(json.dumps(data,indent=2));print(json.dumps({k:v for k,v in data.items() if k.endswith('count') or k=='failed_import_ids'}))
else:
 inventory=json.loads((OUT/'discovery.json').read_text());selected=inventory['labels']
 if sys.argv[1]=='place':selected=[l for l in selected if any(x in l for x in ('place','photo','image','pricing','schedule','owner','publication','moderation','volunteer'))]
 if sys.argv[1]=='repair':selected=['catalog.testcases.'+m for m in ['test_place_rejection_feedback','test_place_qa03_pricing_rebase','test_place_qa04_manual_location','test_task33_place_nature_localization','test_task33_place_continuous','test_place_qa08_district_localization']]
 if sys.argv[1]=='target':selected=['catalog.testcases.test_place_candidate_conflict_recovery']
 if sys.argv[1]=='affected':selected=['catalog.testcases.'+m for m in ['test_place_candidate_conflict_recovery','test_task33_place_continuous','test_task33_publication','test_task33_drafts','photo_workflow','image_uploads','owner','test_volunteer_admin','test_volunteer_dashboard']]
 if sys.argv[1]=='repro':
  previous=json.loads((HERE/'full-result.json').read_text());selected=[t['id'] for t in previous['failures']+previous['errors']]
 raw=suite_for(selected)
 if sys.argv[1]=='full':raw.update(suite_for([]))
 from django.test.runner import reorder_tests,partition_suite_by_case
 suite=unittest.TestSuite(reorder_tests(list(raw.values()),(unittest.loader._FailedTest,*runner.reorder_by)))
 if runner.parallel>1:suite=runner.parallel_test_suite(partition_suite_by_case(suite),runner.parallel,runner.failfast,runner.debug_mode,runner.buffer)
 runner.build_suite=lambda *a,**kw:suite
 original_run_suite=runner.run_suite
 def run_suite(suite,**kwargs):
  result=original_run_suite(suite,**kwargs)
  data={'testsRun':result.testsRun,'failures':[{'id':t.id(),'trace':trace} for t,trace in result.failures],'errors':[{'id':t.id(),'trace':trace} for t,trace in result.errors],'skipped':[{'id':t.id(),'reason':why} for t,why in result.skipped],'stopped':result.shouldStop}
  (HERE/(sys.argv[1]+'-result.json')).write_text(json.dumps(data,indent=2))
  return result
 runner.run_suite=run_suite
 start=time.monotonic();exitcode=runner.run_tests(selected)
 print(json.dumps({'mode':sys.argv[1],'exit':exitcode,'discovered':len(raw),'duration_s':time.monotonic()-start,'labels':selected}));sys.exit(exitcode)
