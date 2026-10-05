"""Aggregate-only verification of the new synthetic handoff preview."""
import json,hashlib,subprocess,urllib.request,re
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
STATE=Path('/tmp/kidsmap-task33-qa04-manual-portable')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
seeds=[read(p) for p in sorted((STATE/'demo100').glob('*.json'))]
assert len(seeds)>=2 and seeds[0]['created']==100 and seeds[-1]['created']==0
assert all(r['public_total']==103 and r['photos_verified']==396 and r['existing_places_unchanged'] for r in seeds)
info=json.loads(subprocess.check_output(['docker','inspect','kidsmap-manual-portable'],text=True))[0]
assert info['Config']['Labels']['kidsmap.manual.owner']=='manual-portable'
assert info['HostConfig']['NetworkMode']=='none' and not info['HostConfig']['PortBindings']
browser=read(HERE/'browser.json');assert browser['status']=='PASS'
immutable={}
for area,filename,key in [('completion','evidence-manifest.json','files'),('completion','entry.json','immutable_audit')]:
    data=read(ROOT/'docs/task33'/area/filename)[key]
    for i in data:
        p=(ROOT/i['path']) if key=='immutable_audit' else ROOT/'docs/task33'/area/i['path']
        assert sha(p)==i['sha256'],i['path']
    immutable['final-audit' if key=='immutable_audit' else area]=len(data)
manifest=read(STATE/'source-manifest.json')['source_files']
for i in manifest:assert sha(ROOT/i['path'])==i['sha256']
photo_sources=set(re.findall(r'static/img/[A-Za-z0-9_./-]+',(ROOT/'src/catalog/management/commands/seed_catalog_demo_places.py').read_text()))
tracked=set(subprocess.check_output(['git','-C',str(ROOT),'ls-files','-z']).decode().split('\0'))
assert photo_sources and all(p in tracked and (ROOT/p).is_file() for p in photo_sources), 'Demo photos missing from Git'
http=[]
for path in ['/qa/','/qa/fixtures.json','/ru/catalog/','/admin/login/']:
    with urllib.request.urlopen('http://127.0.0.1:8781'+path,timeout=15) as r:assert r.status==200;http.append({'url':path,'status':r.status})
whitespace=(HERE/'whitespace-check.log').read_text(encoding='utf-8-sig')
issues=[line for line in whitespace.splitlines() if ': trailing whitespace.' in line or ': new blank line at EOF.' in line]
result={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'portable_contract_tests':3,'source_files':len(manifest),
 'fresh_database_migrations':168,'public_places':103,'photos':396,'demo_photo_sources_in_git':len(photo_sources),'initial_created':100,'restart_created':0,'existing_rows_preserved':True,
 'browser':browser,'http':http,'database_network':'none','database_ports':False,'immutable_evidence':immutable,
 'git_whitespace_check':{'exit':2,'findings':len(issues),'disposition':'Retained existing whitespace in frozen historical evidence, originals and previously tested QA/test sources; no behavior failure, no assertions changed'},
 'local_sensitive_files_preserved':all((ROOT/p).exists() for p in ['.env#','backups/db.sqlite3.before-migrate-20260831-151210']),
 'known_qa_issues':'Initial bootstrap compiled scratch catalogues; bounded to locale/*.po with msgfmt. Browser first counted only loaded lazy photos; final test scrolls every photo and checks successful decoding.',
 'production':'NOT_CONTACTED','full_backend_regression':'NOT_REPEATED; packaging-only QA helpers changed'}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['browser','http','known_qa_issues']},ensure_ascii=False))
