import ast, csv, hashlib, json, os, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path('C:/kidsmap');OUT=Path(__file__).resolve().parent
log=OUT/'command-results.json'
ledger={'scope':'Reconciliation QA commands only; no backend/browser/app transitions executed by this role','commands':[]}
log.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
env=dict(os.environ);env['PYTHONIOENCODING']='utf-8';env['PYTHONDONTWRITEBYTECODE']='1'
for name in ['inventory.py','asset_readback.py','import_root_evidence.py','assemble.py']:
    cmd=[sys.executable,str(OUT/name)];start=time.monotonic()
    completed=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
    first=completed.stdout.splitlines()[0] if completed.stdout else ''
    try:summary=json.loads(first)
    except ValueError:summary=first
    ledger['commands'].append({'utc':datetime.now(timezone.utc).isoformat(),'argv':cmd,'exit_code':completed.returncode,
        'seconds':round(time.monotonic()-start,3),'summary':summary,'stderr':completed.stderr})
    log.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if completed.returncode:print(json.dumps({'failed':name,'exit_code':completed.returncode}));sys.exit(completed.returncode)
data=json.loads((OUT/'historical-findings.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok,detail=None):checks.append({'check':name,'status':'PASS' if ok else 'FAIL','detail':detail})
check('81 unique historical IDs',len(data['findings'])==81 and len({f['id'] for f in data['findings']})==81)
check('Historical severity distribution',data['severity']=={'P2':67,'P1':2,'P3':12},data['severity'])
check('77 historical deduplicated buckets',data['historical_root_cause_bucket_count']==77)
check('Seven later PLACE repair claims explicitly retained',len(data['later_repair_claim_ids'])==7)
check('Required nine report sections',all(('## '+str(n)+'. ') in (OUT/'REPORT.md').read_text(encoding='utf-8') for n in range(1,10)))
fresh_ids={'SITE-QA-01','ANALYTICS-QA-01','ORG-QA-02','ACCESS-QA-03'}
check('Only parent-explicit historical IDs receive fresh FAIL',all(f['fresh_module13_status']==('FAIL' if f['id'] in fresh_ids else 'NOT RUN') for f in data['findings']))
fresh_changes=[]
for r in data['fresh_parent_handoff']['files']:
    p=ROOT/r['evidence']
    if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:fresh_changes.append(r['evidence'])
check('Fresh parent artifacts retained and linked',not fresh_changes,fresh_changes)
bad_links=[]
for p in OUT.glob('*.md'):
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if target.startswith(('http:','https:','mailto:','#')):continue
        path=target.split('#',1)[0];path=re.sub(r':\d+$','',path)
        q=(p.parent/path).resolve()
        if not q.exists():bad_links.append({'file':p.name,'target':target})
check('Local Markdown links exist',not bad_links,bad_links)
stale=[]
for r in data['reports']:
    p=ROOT/r['report']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=r['report_sha256']:stale.append(r['report'])
for f in data['findings']:
    for old in f['historical_occurrences']:
        p=ROOT/old['finding'].split('#',1)[0]
        if hashlib.sha256(p.read_bytes()).hexdigest()!=old['finding_sha256']:stale.append(old['finding'])
check('All historical documents unchanged during reconciliation',not stale,stale)
snapshot=json.loads((ROOT/'docs/qa/module12-2026-10-11-r1/snapshot.json').read_text(encoding='utf-8'))
changed=[]
for p,expected in snapshot['source_files'].items():
    q=ROOT/p
    if not q.exists() or hashlib.sha256(q.read_bytes()).hexdigest()!=expected:changed.append(p)
check('Current source matches parent inherited module12 application manifest',not changed,{'recorded_files':len(snapshot['source_files']),'changed':changed,'note':'Source preservation only; not fresh runtime attestation.'})
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
check('Parent HEAD and branch retained',head==data['head'] and branch==data['branch'],{'head':head,'branch':branch})
active=(ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8')
check('Parent active_run NONE retained',re.search(r'active_run:\s*NONE',active) is not None)
for name in ['coverage.csv','source-coverage.csv','mandatory-gaps.csv']:
    with (OUT/name).open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    check(name+' preserves historical vs explicit parent freshness',all(r['fresh_module13_status'] in ['FAIL','NOT RUN'] if r.get('record_kind')=='FRESH_PARENT_HANDOFF' else r['fresh_module13_status']=='NOT RUN' for r in rows),{'rows':len(rows)})
for p in OUT.glob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
check('Own Python syntax valid',True,{'files':len(list(OUT.glob('*.py')))})
whitespace=[]
for p in OUT.glob('*.md'):
    for n,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
        if line.rstrip()!=line:whitespace.append({'file':p.name,'line':n})
check('Own Markdown no trailing whitespace',not whitespace,whitespace)
jsonfiles=list(OUT.glob('*.json'))
for p in jsonfiles:json.loads(p.read_text(encoding='utf-8'))
check('Own JSON valid',True,{'files':len(jsonfiles)})
artifact_manifest=[]
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name not in ['verification.json','artifact-manifest.json','command-results.json']:
        artifact_manifest.append({'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'artifact-manifest.json').write_text(json.dumps(artifact_manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
result={'utc':datetime.now(timezone.utc).isoformat(),'exit_code':0 if all(c['status']=='PASS' for c in checks) else 1,
    'checks':checks,'counts':dict(__import__('collections').Counter(c['status'] for c in checks)),
    'scope_note':'Artifact/source/document validation only. Root owns fresh native runtime/test acceptance and foreign-stand preservation.'}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ledger['verification_exit_code']=result['exit_code'];ledger['verification_counts']=result['counts']
log.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'native_commands':[(Path(c['argv'][-1]).name,c['exit_code']) for c in ledger['commands']],
    'verification_exit_code':result['exit_code'],'checks':result['counts'],'findings':81,'buckets':77,
    'coverage_rows':data['coverage_rows'],'source_declarations':data['source_inventory_counts']},ensure_ascii=False))
sys.exit(result['exit_code'])
