"""Preserve approved implementation entry without rewriting prior audit evidence."""
import datetime,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path('C:/kidsmap');OUT=ROOT/'docs/task33/completion'
def git(*args):return subprocess.check_output(['git','-c','core.safecrlf=false',*args],cwd=ROOT,stderr=subprocess.DEVNULL)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
status=ROOT/'docs/task33/implementation-status.md';assert 'active_run: NONE'in status.read_text(encoding='utf8')
audit=ROOT/'docs/task33/final-audit';manifest=json.loads((audit/'artifact-manifest.json').read_text())
for row in manifest['files']:assert sha(audit/row['path'])==row['sha256'],row['path']
paths=set((git('diff','--name-only','HEAD','-z')+git('ls-files','--others','--exclude-standard','-z')).decode().split('\0'))-{''}
paths={p for p in paths if not p.startswith('docs/task33/completion/')}
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%SZ')
saved=ROOT/'scratch'/('task33-completion-entry-'+stamp);saved.mkdir()
rows=[]
for name in sorted(paths):
    src=ROOT/name;assert src.is_file()and not src.is_symlink(),name
    dst=saved/'files'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    digest=sha(src);assert sha(dst)==digest;rows.append({'path':name,'sha256':digest})
(saved/'tracked.patch').write_bytes(git('diff','--binary','HEAD'))
audit_rows=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in sorted(audit.rglob('*'))if p.is_file()and'__pycache__'not in p.parts]
data={'run':'completion-'+stamp,'head':git('rev-parse','HEAD').decode().strip(),'branch':git('branch','--show-current').decode().strip(),'snapshot':str(saved),'files':rows,'immutable_audit':audit_rows,'mode':'APPROVED_IMPLEMENT_POINTS_1_TO_5','production':'NOT_CONTACTED','authorization':'User PLEASE IMPLEMENT THIS PLAN; own Activity taxonomy; at-least-once email with rare crash duplicate accepted; no production/commit/push/deploy'}
(OUT/'entry.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
lines=status.read_text(encoding='utf8').splitlines()
for i,line in enumerate(lines):
    if line.startswith('active_run:'):lines[i]='active_run: '+data['run']+' — /root kidsmap-orchestrator; APPROVED IMPLEMENT points1–5.'
    if line.startswith('current_scope:'):lines[i]='current_scope: taxonomy + ownership concurrency + UI fixes + email crash policy + full regression; explicit user plan approved; production/commit/push/deploy excluded.'
status.write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({k:data[k]for k in('run','head','branch','snapshot','mode')}|{'preserved_files':len(rows),'immutable_audit_files':len(audit_rows)}))
