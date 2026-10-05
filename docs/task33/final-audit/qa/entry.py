import datetime,hashlib,json,shutil,subprocess
from pathlib import Path
root=Path('C:/kidsmap');out=root/'docs/task33/final-audit'
def git(*args):return subprocess.check_output(['git','-c','core.safecrlf=false',*args],cwd=root,stderr=subprocess.DEVNULL)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
status=root/'docs/task33/implementation-status.md'
assert 'active_run: NONE' in status.read_text(encoding='utf8')
old=json.loads((root/'docs/task33/reports/28-source-manifest.json').read_text(encoding='utf8'))
for item in old['source_artifacts']:assert sha(root/item['path'])==item['sha256'],item['path']
paths=set((git('diff','--name-only','HEAD','-z')+git('ls-files','--others','--exclude-standard','-z')).decode().split('\0'))-{''}
paths={p for p in paths if not p.startswith('docs/task33/final-audit/')}
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%SZ')
snapshot=root/'scratch'/('task33-final-audit-entry-'+stamp);snapshot.mkdir()
files=[]
for name in sorted(paths):
    src=root/name; assert src.is_file() and not src.is_symlink(),name
    dst=snapshot/'files'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    digest=sha(src);assert sha(dst)==digest
    files.append({'path':name,'sha256':digest})
(snapshot/'tracked.patch').write_bytes(git('diff','--binary','HEAD'))
data={'run':'final-audit-'+stamp,'head':git('rev-parse','HEAD').decode().strip(),'branch':git('branch','--show-current').decode().strip(),'snapshot':str(snapshot),'files':files,'prior28_source_matched':len(old['source_artifacts']),'production':'NOT_CONTACTED'}
(out/'entry.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
lines=status.read_text(encoding='utf8').splitlines()
for i,line in enumerate(lines):
    if line.startswith('active_run:'):lines[i]=f'active_run: {data["run"]} — /root kidsmap-orchestrator; independent comprehensive AUDIT, application read-only.'
    if line.startswith('current_scope:'):lines[i]='current_scope: all28 cross-stage audit requested2026-10-04; fresh isolated tests/browser, detailed report/screenshots/roadmap; previous stage28 results retained.'
status.write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in data.items()if k!='files'}|{'preserved':len(files)}))
