import json,hashlib,subprocess,sys
from pathlib import Path
root=Path.cwd();out=root/'docs/qa/module01-completion-2026-10-12-r1/integration'
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
paths=git('ls-files','src','static','locale','scripts').splitlines()
paths+=['src/catalog/testcases/test_place_candidate_conflict_recovery.py']
rows={};changed=[];digest=hashlib.sha256()
for p in sorted(set(paths)):
 h=hashlib.sha256((root/p).read_bytes()).hexdigest();rows[p]=h;digest.update((p+'\0'+h+'\n').encode())
 old=subprocess.run(['git','show','HEAD:'+p],capture_output=True)
 if old.returncode!=0 or hashlib.sha256(old.stdout).hexdigest()!=h:changed.append(p)
x={'root':str(root),'HEAD':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'source_count':len(rows),'source_digest':digest.hexdigest(),'hashes':rows,'changed_application_paths':changed,'dirty':git('status','--short'),'active_run':[s for s in (root/'docs/task33/implementation-status.md').read_text().splitlines() if s.startswith('active_run:')]}
(out/(sys.argv[1]+'.json')).write_text(json.dumps(x,indent=2));print(json.dumps({k:v for k,v in x.items() if k not in {'hashes','dirty'}}))
