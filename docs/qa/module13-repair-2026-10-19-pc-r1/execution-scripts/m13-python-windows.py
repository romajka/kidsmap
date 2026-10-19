import os,sys,unittest,json
from pathlib import Path
R=Path('C:/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
os.environ.clear();os.environ.update(DJANGO_TESTING='1',PYTHONDONTWRITEBYTECODE='1',SYSTEMROOT='C:\\Windows',PATH='C:\\Windows\\System32;C:\\Windows',TEMP=str(Q/'tmp'),TMP=str(Q/'tmp'))
sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'scripts/tests'))
suite=unittest.defaultTestLoader.loadTestsFromName('test_build_isolated_locales')
with (Q/'python-windows-locales.log').open('w',encoding='utf-8') as f:result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
d={'command':[sys.executable,'-I',str(Path(__file__))],'tests':result.testsRun,'failures':[t.id() for t,_ in result.failures],'errors':[t.id() for t,_ in result.errors],'skipped':[(t.id(),r) for t,r in result.skipped],'exit':int(not result.wasSuccessful()),'profile':'Original unchanged Windows-specific wsl compiler tests on native Windows Python, cleared environment; own temporary fixtures only.'};(O/'evidence/python-windows-locales.json').write_text(json.dumps(d,indent=2),encoding='utf-8');print(json.dumps(d,indent=2));raise SystemExit(d['exit'])
