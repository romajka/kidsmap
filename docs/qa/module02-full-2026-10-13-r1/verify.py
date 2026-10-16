import hashlib,json,subprocess,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
base=json.loads((R/'docs/qa/module02-remaining-recheck-2026-10-13-r1/entry.json').read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
source={str(f.relative_to(R)):sha(f) for top in ('src','static','config','locale','templates') for f in (R/top).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
changed=sorted(k for k in set(base['source'])|set(source) if base['source'].get(k)!=source.get(k))
assert changed==['locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po','static/admin/css/pages/kidsmap_changelist.css'],changed
assert all(sha(R/k)==v for k,v in base['previous_reports'].items());assert 'active_run: NONE' in (R/'docs/task33/implementation-status.md').read_text()
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==base['head'];subprocess.run(['git','diff','--check'],check=True)
profiles=[]
for name in ['org-qa03-fix-2026-10-13-r1','org-qa04-fix-2026-10-13-r1',P.name]:
 p=R/'docs/qa'/name;server=json.loads((p/'server.json').read_text());d=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=5));assert d['entry_matches_startup'] and d['startup_matches_disk'];assert str(p/'runtime.py').encode() in (Path('/proc')/str(server['pid'])/'cmdline').read_bytes()
 images=[{'path':str(f.relative_to(p)),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted((p/'screenshots').glob('*.png'))];(p/'png-manifest.json').write_text(json.dumps(images,indent=2));profiles.append({'profile':name,'pid':server['pid'],'runtime_matches':True,'png':len(images)})
rows=[]
for name in ['lifecycle','bulk','api-core','published-roundtrip','team','team-api','advanced-connections','recovery-lost','detach-transfer','admin-flow','nojs-security','expiry']:
 f=P/(name+'.result.json')
 if f.exists():
  d=json.loads(f.read_text());rows += [{'script':name,**r} for r in d.get('rows',[])]
for f in P.glob('team-management.result.attempt*.json'):
 d=json.loads(f.read_text())
 if not d.get('error'):rows+=[{'script':'team-management',**r} for r in d['rows']]
(P/'functional-index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
assert all(json.loads((P/'readback.json').read_text())['flags'].values())
a=json.loads((P/'preservation-before.json').read_text())['rows'];b=json.loads((P/'preservation-after.json').read_text())['rows'];assert len(a)==len(b)==10 and all({k:v for k,v in x.items() if k!='organization_id'}=={k:v for k,v in y.items() if k!='organization_id'} for x,y in zip(a,b))
a=json.loads((P/'detach-before.json').read_text());b=json.loads((P/'detach-after.json').read_text());assert a['protected_hash']==b['protected_hash'] and a['snapshot']==b['snapshot'] and b['organization_id'] is None and b['program_id'] is None
out={'changed_application_files':changed,'foreign_source_assertions_and_shared_MO_preserved':True,'previous_report_files_preserved':len(base['previous_reports']),'active_run':'NONE','profiles':profiles,'raw_functional_rows':len(rows),'raw_pass':sum(r['status']=='PASS' for r in rows),'raw_fail':sum(r['status']=='FAIL' for r in rows),'ten_rich_places_preserved':True,'detach_snapshot_pricing_groups_media_preserved':True,'module_test_discovery':248,'module_backend_run':'NOT RUN until locale correction approval','full_ACCEPT02':'INCOMPLETE: RU fallback regression and ORG-QA-05 OPEN; final matrix/tests NOT RUN','commit_push_deploy_production':'NOT RUN','diff_check_exit':0}
(P/'verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
