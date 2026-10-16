"""Owned local evidence only. Never reads a checkout .env or exports secrets."""
import hashlib,json,subprocess,os
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]; SCRATCH=ROOT/'.tmp'/HERE.name
entry=json.loads((HERE/'entry.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source():return {str(p.relative_to(ROOT)):sha(p) for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
current=source();before=entry['source'];changed=[k for k in before if before[k]!=current.get(k)];added=sorted(current.keys()-before.keys())
allowed={'src/catalog/domain_admin/place.py','src/catalog/services/permanent_place_wizard.py','src/catalog/templates/admin/catalog/place/change_form.html','static/admin/js/kidsmap_place_form.js','src/catalog/testcases/test_place_admin_conflict_retention.py'}
assert set(changed+added)<=allowed
historical=all((ROOT/k).is_file() and sha(ROOT/k)==h for k,h in entry['previous_reports'].items())
shared=all(current[k]==h for k,h in before.items() if k.startswith('locale/') and k.endswith('.mo'))
servers=[]
for name in ('start-local-2026-10-12-r1','module01-full-2026-10-12-r1','module01-completion-2026-10-12-r1','module01-full-2026-10-12-r2','place-qa11-fix-2026-10-12-r1'):
 p=ROOT/'docs/qa'/name/'server.json'
 if p.exists():
  info=json.loads(p.read_text());pid=info['pid'];proc=Path(f'/proc/{pid}/cmdline');alive=proc.exists();match=alive and str(ROOT/'docs/qa'/name/'runtime.py').encode() in proc.read_bytes()
  servers.append({'profile':name,'pid':pid,'alive':alive,'runtime_script_matches':match})
foreign=subprocess.check_output(['docker','ps','--format','{{.ID}} {{.Names}} {{.Ports}}'],text=True)
old_containers={line.split()[0] for line in entry['containers'].splitlines()};now_containers={line.split()[0] for line in foreign.splitlines()}
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
preservation={'checkout':str(ROOT),'head':head,'branch':branch,'head_unchanged':head==entry['head'],'branch_unchanged':branch==entry['branch'],'active_run_none': 'active_run: NONE' in (ROOT/'docs/task33/implementation-status.md').read_text(),'prior_report_hashes_preserved':historical,'shared_mo_preserved':shared,'containers_preserved':old_containers<=now_containers,'earlier_stands':servers,'changed_since_entry':changed,'added_source':added,'scoped_changes_only':True,'global_suite_not_repeated':'User requested targeted checks per fix, module acceptance after all module tasks, global corpus after all13 modules. Module acceptance currently blocked by independent QA14.'}
assert historical and shared and old_containers<=now_containers and preservation['head_unchanged'] and preservation['active_run_none'] and all(s['alive'] and s['runtime_script_matches'] for s in servers)
(HERE/'preservation.json').write_text(json.dumps(preservation,indent=2));(HERE/'final-source.json').write_text(json.dumps(current,indent=2))
versions={}
for name,argv in [('python',[str(ROOT/'.venv/bin/python'),'--version']),('node',['node','--version']),('msgfmt',['msgfmt','--version']),('docker',['docker','--version'])]:
 r=subprocess.run(argv,text=True,capture_output=True);versions[name]={'argv':argv,'exit':r.returncode,'version':(r.stdout+r.stderr).splitlines()[0]}
(HERE/'versions.json').write_text(json.dumps(versions,indent=2))
pngs={str(p.relative_to(HERE)):sha(p) for p in (HERE/'screenshots').glob('*.png')};(HERE/'screenshots-manifest.json').write_text(json.dumps(pngs,indent=2))
# Credential literal scan reports booleans/paths only, never matched values.
secret=json.loads((SCRATCH/'credentials.json').read_text());hits=[]
for base in (HERE,ROOT/'docs/qa/place-qa13-fix-2026-10-12-r1',ROOT/'docs/qa/module01-full-2026-10-12-r4'):
 for p in base.rglob('*'):
  if p.is_file() and p.suffix!='.png':
   raw=p.read_bytes()
   if any(str(v).encode() in raw for v in secret.values() if len(str(v))>=12):hits.append(str(p.relative_to(ROOT)))
assert not hits;(HERE/'credential-literal-scan.json').write_text(json.dumps({'matched_files':hits,'scope':'actual own ignored credentials literals only, not a universal secret audit'}))
print(json.dumps({'preserved':True,'approved_changed_source':len(changed),'new_tests':len(added),'pngs':len(pngs),'secret_literal_hits':len(hits)}))
