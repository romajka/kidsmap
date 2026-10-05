"""Hash application and executed browser harness separately; exclude collectors."""
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
APP=('src','templates','static','locale','config','scripts')
def hashes(root, harness=False):
    result={}
    for domain in APP if not harness else ('docs/task33/qa04','docs/task33/qa28'):
        for p in sorted((root/domain).rglob('*')):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix=='.pyc':continue
            if not harness and p.suffix=='.mo':continue
            if harness and domain.endswith('qa28') and not p.relative_to(root/domain).parts[0].startswith('browser'):continue
            result[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    if not harness:result['manage.py']=hashlib.sha256((root/'manage.py').read_bytes()).hexdigest()
    return result

if sys.argv[1]=='freeze':
    app=hashes(ROOT);artifact=hashes(Path('/root/km28-release3'))
    assert app==artifact,'Application mismatch from exact R2 artifact'
    harness=hashes(ROOT,True)
    for name in harness:
        if name.endswith('.py'):ast.parse((ROOT/name).read_text())
    data={'artifact':'r2-local-sha256-65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2',
          'application':app,'executed_harness':harness,'compiled_mo':'from identical PO only'}
    (ROOT/'browser-source.json').write_text(json.dumps(data,indent=2))
    print(json.dumps({'application_files':len(app),'harness_files':len(harness),'artifact_match':True,'AST':'PASS'}))
else:
    frozen=json.loads((ROOT/'browser-source.json').read_text())
    current=hashes(Path('/mnt/c/kidsmap'))
    changed=[name for name,value in frozen['application'].items() if current.get(name)!=value]
    new=sorted(set(current)-set(frozen['application']))
    result={'application_files':len(current),'mismatches':changed,'new_application_files':new,
            'executed_harness_unchanged':hashes(ROOT,True)==frozen['executed_harness']}
    print(json.dumps(result))
    assert not changed and not new and result['executed_harness_unchanged']
