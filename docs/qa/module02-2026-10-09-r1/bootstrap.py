"""Create only this run's QA scaffold; never modify application/previous audit."""
import json, hashlib, subprocess
from pathlib import Path
here=Path(__file__).resolve().parent
root=here.parents[2]
old=here.with_name('module01-2026-10-09-r1')
for name in ['qa_settings.py','qa_urls.py','browser.config.json','drive.py','test_driver.py']:
    s=(old/name).read_text(encoding='utf-8')
    for a,b in [('module01-20261009-r1','module02-20261009-r1'),('module01-2026-10-09-r1','module02-2026-10-09-r1'),('module01_r1','module02_r1'),('module01-r1','module02-r1'),('module01','module02'),('8811','8812'),('55431','55432')]:s=s.replace(a,b)
    if name=='drive.py':
        start=s.index("if sys.argv[1]=='branch-lifecycle.js':")
        end=s.index("(here/(Path(sys.argv[1]).stem+'.effective.js'))")
        s=s[:start]+s[end:]
    if name=='test_driver.py':continue
    (here/name).write_text(s,encoding='utf-8')
state=root/'.tmp/module02-20261009-r1'
state.mkdir(parents=True,exist_ok=True)
for n in ['media','private-media','assets','unit-media','unit-private-media']:(state/n).mkdir(exist_ok=True)
(here/'screenshots').mkdir(exist_ok=True)
source={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for top in ['src','static','config','locale'] for p in (root/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
preserved={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in old.rglob('*') if p.is_file()}
snapshot={'checkout':str(root),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip(),'entry_worktree':subprocess.check_output(['git','status','--short'],cwd=root,text=True).splitlines(),'active_run':'NONE','source_files':source,'source_digest':hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),'preserved_module01':preserved,'entry_journal_sha256':hashlib.sha256((here.parent/'module-acceptance-prompts.md').read_bytes()).hexdigest(),'entry_active_marker_sha256':hashlib.sha256((root/'docs/task33/implementation-status.md').read_bytes()).hexdigest()}
(here/'snapshot.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
print('Source hashes',len(source),'prior artifacts',len(preserved))
