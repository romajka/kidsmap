import subprocess,json,hashlib,sys
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'docs/qa/module01-full-2026-10-12-r1/integration'
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
files=git('ls-files','src','static','scripts','locale').splitlines()
mismatch=[];digest=hashlib.sha256()
for p in files:
 b=(ROOT/p).read_bytes();h=hashlib.sha256(b).hexdigest();digest.update((p+'\0'+h+'\n').encode())
 old=subprocess.check_output(['git','show','HEAD:'+p])
 if b!=old:mismatch.append(p)
data={'path':str(ROOT.resolve()),'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'dirty':git('status','--short'),'tracked_application_paths_checked':len(files),'worktree_equals_HEAD':not mismatch,'mismatch':mismatch,'source_digest_sha256':digest.hexdigest(),'active_run':[x for x in (ROOT/'docs/task33/implementation-status.md').read_text().splitlines() if x.startswith('active_run:')],'runtime':{'python':sys.version.split()[0]},'isolation':{'test_database':'test_accept01_integration_20261012_r1','repair_database':'test_accept01_integration_repair_20261012_r1','host':'127.0.0.1','cache':'LocMem unique integration','media':'own integration scratch','email':'LocMem','egress':'only explicit START PostgreSQL loopback port','dotenv_loaded':False}}
(OUT/'snapshot.json').write_text(json.dumps(data,indent=2));print(json.dumps({k:v for k,v in data.items() if k not in {'dirty','active_run'}}))
