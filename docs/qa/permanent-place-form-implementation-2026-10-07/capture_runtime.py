from pathlib import Path
import json, hashlib, subprocess, datetime
root=Path('/home/ramin/kidsmap'); scratch=Path(__file__).parent
baseline=json.loads((scratch/'baseline.json').read_text())
allowed=set(json.loads((scratch/'allowed-files.json').read_text()))
changes=[p for p,h in baseline.items() if not (root/p).exists() or hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
assert not set(changes)-allowed, set(changes)-allowed
sources={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in baseline if p.startswith(('src/','static/','locale/','config/'))}
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert head==json.loads((scratch/'snapshot.json').read_text())['head']
runtime=dict(head=head,source_files=sources,source_digest=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest(),
             worktree_status=subprocess.check_output(['git','status','--porcelain'],text=True).splitlines(),captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(scratch/'runtime-source.json').write_text(json.dumps(runtime,indent=2)+'\n')
print('Runtime digest:',runtime['source_digest'],'changed allowed files:',len(changes))
