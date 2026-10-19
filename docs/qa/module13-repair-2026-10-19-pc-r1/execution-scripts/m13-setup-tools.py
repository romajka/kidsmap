from pathlib import Path
import json
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
def adapt(t):
 for a,b in [('module12-repair-2026-10-18-pc-r1','module13-repair-2026-10-19-pc-r1'),('m12-full-r1','m13-full-r1'),('m12full-r1','m13full-r1'),('m12full_','m13full_'),('m12_guard','m13_guard'),('M12','M13'),('$m12','$m13'),('module12','module13'),('m12-','m13-')]:t=t.replace(a,b)
 return t
for n in ['stage_apply.py','apply-native.ps1']:(Q/n).write_text(adapt((R/'.tmp/m12-full-r1'/n).read_text()))
(R/'.tmp/m13-tests.py').write_text(adapt((R/'.tmp/m12-tests.py').read_text()))
note=json.loads((O/'evidence/entry-index-note.json').read_text());note['note']='Entry source and refs match previous Module12. Current binary index is the Module13 preservation baseline; equality recorded explicitly.';note['index_matches_previous']=note['previous_module_index_sha256']==note['current_entry_index_sha256'];(O/'evidence/entry-index-note.json').write_text(json.dumps(note,indent=2))
auth=json.loads((O/'authorization.json').read_text());auth['limits']=auth['limits'].replace('43prior','44 prior');(O/'authorization.json').write_text(json.dumps(auth,ensure_ascii=False,indent=2))
# Fixtures only in this new Module13 namespace; disabled transport remains explicit.
(Q/'discovery.py').write_text('''import sys,json,importlib,pkgutil,collections
sys.argv=['runtime.py','discover'];from runtime import *
from config.test_runner import KidsMapTestRunner
from catalog import testcases
def flatten(s):
 for t in s:
  if hasattr(t,'_tests'):yield from flatten(t)
  else:yield t.id()
runner=KidsMapTestRunner(verbosity=0,interactive=False)
modules=['catalog.testcases.'+m.name for m in pkgutil.iter_modules(testcases.__path__) if not m.ispkg]
out={}
for key,labels in [('no_label',[]),('catalog',['catalog']),('exhaustive',modules)]:
 ids=list(flatten(runner.build_suite(labels)));counts=collections.Counter(ids);out[key]={'raw':len(ids),'unique':len(counts),'duplicates':{k:v for k,v in counts.items() if v>1},'ids':sorted(counts)}
out['modules']=modules
print('M13_RESULT'+json.dumps(out))
''')
print('Module13 own tools ready')
