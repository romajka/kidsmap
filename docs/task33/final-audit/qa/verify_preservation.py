"""Read-only verification of pre-audit work and report evidence."""
import hashlib,json,subprocess,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'docs/task33/final-audit'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-c','core.safecrlf=false',*args],cwd=ROOT,stderr=subprocess.DEVNULL).decode().strip()
entry=read(OUT/'entry.json');snapshot=Path(entry['snapshot'])
allowed={'docs/task33/README.md','docs/task33/implementation-status.md','docs/agent-audits/MASTER_AUDIT.md'}
errors=[];changed=[]
for item in entry['files']:
    name=item['path'];saved=snapshot/'files'/name;current=ROOT/name
    if not saved.is_file() or sha(saved)!=item['sha256']:errors.append('snapshot:'+name)
    if not current.is_file() or sha(current)!=item['sha256']:
        changed.append(name)
        if name not in allowed:errors.append('unexpected_mutation:'+name)
old=read(ROOT/'docs/task33/reports/28-source-manifest.json')
for item in old['source_artifacts']:
    if sha(ROOT/item['path'])!=item['sha256']:errors.append('source:'+item['path'])
head=git('rev-parse','HEAD');branch=git('branch','--show-current')
if head!=entry['head'] or branch!=entry['branch']:errors.append('git_identity_changed')
dirty=set((git('diff','--name-only','HEAD','-z')+'\0'+git('ls-files','--others','--exclude-standard','-z')).split('\0'))-{''}
prior={x['path']for x in entry['files']}
extra=sorted(p for p in dirty-prior if not p.startswith('docs/task33/final-audit/') and p not in allowed)
errors.extend('unexpected_new_path:'+p for p in extra)
gallery=OUT/'screenshots/index.json';screens=[]
if gallery.exists():
    index=read(gallery);items=index if isinstance(index,list)else index['screenshots']
    for item in items:
        p=OUT/item['path'];actual=sha(p)
        if actual!=item['sha256']:errors.append('screenshot:'+item['path'])
        screens.append({'path':item['path'],'sha256':actual})
additional=OUT/'additional-preservation.json'
if additional.exists():
    for item in read(additional)['files']:
        if sha(Path(item['snapshot']))!=item['sha256']:errors.append('additional_snapshot:'+item['path'])
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if not errors else'FAIL','head':head,'branch':branch,'prior_dirty_files_saved':len(entry['files']),'prior_dirty_files_unchanged':len(entry['files'])-len(changed),'authorized_document_updates':changed,'prior28_source_hashes_matched':len(old['source_artifacts']),'screenshot_hashes_matched':len(screens),'unexpected_new_paths':extra,'errors':errors,'production':'NOT_CONTACTED','application_edits':'NONE_IN_THIS_AUDIT'}
(OUT/'final-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,ensure_ascii=False));raise SystemExit(bool(errors))
