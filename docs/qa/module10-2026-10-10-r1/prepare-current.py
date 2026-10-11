"""Own supplemental fresh runtime after foreign WORKTREE drift; never overwrite entry."""
from pathlib import Path
import json,hashlib,datetime,subprocess
P=Path(__file__).resolve().parent;R=P.parents[2]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source={p.relative_to(R).as_posix():h(p) for top in ['src','static','config','locale','templates'] for p in (R/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
old=json.loads((P/'snapshot.json').read_text());changed=[{'path':f,'entry_sha256':sha,'current_sha256':source.get(f),'mtime_utc':datetime.datetime.fromtimestamp((R/f).stat().st_mtime,datetime.timezone.utc).isoformat()} for f,sha in old['source_files'].items() if source.get(f)!=sha];added=[f for f in source if f not in old['source_files']]
x={'checkout':str(R),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files':source,'source_digest':hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),'entry_changed':changed,'entry_added':added,'worktree':subprocess.check_output(['git','status','--short'],cwd=R,text=True).splitlines()}
assert not (P/'current-snapshot.json').exists();(P/'current-snapshot.json').write_text(json.dumps(x,indent=2),encoding='utf-8')
for oldname,newname in [('run.py','run-current.py'),('qa_settings.py','qa_settings_current.py'),('qa_urls.py','qa_urls_current.py'),('drive.py','drive-current.py'),('common.js','common-current.js'),('matrix-filled.js','current-matrix.js'),('focus-proof.js','current-focus.js'),('network-proof.js','current-network.js')]:
 s=(P/oldname).read_text(encoding='utf-8')
 if oldname=='run.py':s=s.replace("DJANGO_SETTINGS_MODULE='qa_settings'","DJANGO_SETTINGS_MODULE='qa_settings_current'").replace("'snapshot.json'","'current-snapshot.json'").replace('127.0.0.1:8823','127.0.0.1:8825').replace('127.0.0.1:8824','127.0.0.1:8826')
 if oldname=='qa_settings.py':s=s.replace("ROOT_URLCONF = 'qa_urls'","ROOT_URLCONF = 'qa_urls_current'").replace('localhost:8823','localhost:8825').replace("'LOCATION': 'module10-r1'","'LOCATION': 'module10-r1-current'")
 if oldname=='qa_urls.py':s=s.replace("'snapshot.json'","'current-snapshot.json'")
 if oldname=='drive.py':s=s.replace("here/'common.js'","here/'common-current.js'")
 if oldname=='common.js':s=s.replace('localhost:8823','localhost:8825').replace("file='screenshots/'+name","file='screenshots/current-'+name")
 if oldname in ['focus-proof.js','network-proof.js']:s=s.replace('screenshots/','screenshots/current-')
 (P/newname).write_text(s,encoding='utf-8')
print('Current source files',len(source),'changed',len(changed),'added',len(added),'digest',x['source_digest'])
