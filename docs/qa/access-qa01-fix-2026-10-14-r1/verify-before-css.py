import hashlib,importlib.util,json,subprocess,urllib.request
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
entry=json.loads((HERE/'entry.json').read_text());guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md';app='src/catalog/templates/auth/login.html'
before_note=(HERE/'guide-note-before.txt').read_text().rstrip('\n');now_note=next(s for s in(ROOT/guide).read_text().splitlines()if s.startswith('- Module07 ACCESS-QA-01 —'))
changed=[];missing=[];unchanged=0
for path,sha in entry['files'].items():
 p=ROOT/path
 if not p.is_file():missing.append(path);continue
 if digest(p)==sha:unchanged+=1;continue
 if path==app:continue
 if path==guide and hashlib.sha256(p.read_bytes().replace(now_note.encode(),before_note.encode(),1)).hexdigest()==sha:continue
 changed.append(path)
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
new_other=[p for p in paths if p and '.env' not in Path(p).name and p not in entry['files'] and not p.startswith('docs/qa/'+HERE.name+'/')]
spec=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
manifest=builder.verify(SCRATCH/'locales/manifest.json',ROOT/'locale');assert manifest['locales']==['ru','az','en']
server=json.loads((HERE/'server.json').read_text());proc=Path('/proc')/str(server['pid']);argv=[s.decode()for s in(proc/'cmdline').read_bytes().split(b'\0')if s]
runtime=json.load(urllib.request.urlopen(server['url']+'/qa/source/'));(HERE/'runtime-source-final.json').write_text(json.dumps(runtime,indent=2))
expected=json.loads((HERE/'runtime-source-baseline.json').read_text());runtime_match=runtime['pid']==server['pid'] and runtime['source']==expected and runtime['startup_matches_disk'] and runtime['loaded_template_sha256']==digest(ROOT/app) and argv==server['argv'] and str((proc/'cwd').resolve())==str(ROOT)
assert runtime['sole_locale_paths']==[manifest['locale_root']]
observations=json.loads((HERE/'accepted-current-observations.json').read_text());counts=observations['counts'];assert counts=={'PASS':588,'FAIL':18}
failures=[r for r in observations['rows']if r['status']=='FAIL'];assert all(r['name']=='Submit keyboard focus visibly changes indicator'for r in failures)
assert len({(r['lang'],r['width'])for r in failures})==18
png=[]
for p in sorted((HERE/'screenshots').glob('*.png')):
 with Image.open(p)as im:png.append({'path':str(p.relative_to(HERE)),'sha256':digest(p),'width':im.width,'height':im.height})
(HERE/'png-manifest.json').write_text(json.dumps(png,indent=2))
required={f'screenshots/{lang}-{width}-{scene}.png'for lang in ('ru','az','en')for width in (360,390,768,1024,1280,1440)for scene in ('modal','focus-escaped','empty-error','network-error','loading','success','close-focus','submit-visible-focus','success-visible-focus','close-visible-focus')}
required|={f'screenshots/{lang}-{width}-{scene}.png'for lang in ('ru','az','en')for width in (390,1440)for scene in ('reset-confirm','replay-denied')};assert {r['path']for r in png}==required
processes=[]
for p in entry['foreign_processes']:
 proc=Path('/proc')/str(p['pid'])
 try:ok=str((proc/'cwd').resolve())==p['cwd'] and [a.decode(errors='replace')for a in(proc/'cmdline').read_bytes().split(b'\0')if a]==p['args']
 except OSError:ok=False
 processes.append({'pid':p['pid'],'identity_unchanged':ok})
current={c['ID']:c for c in [json.loads(s)for s in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]}
containers=[{'id':c['id'],'name':c['name'],'preserved':c['id']in current and current[c['id']]['Names']==c['name'] and current[c['id']]['Ports']==c['ports'] and current[c['id']]['State']==c['state']}for c in entry['containers']]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip();active=[s for s in(ROOT/'docs/task33/implementation-status.md').read_text().splitlines()if s.startswith('active_run:')]
tests=next(c for c in [json.loads(s)for s in(HERE/'commands.jsonl').read_text().splitlines()]if c['name']=='reset-tests');assert tests['exit']==0 and 'Ran 9 tests' in(HERE/'reset-tests.txt').read_text()
readback=json.loads((HERE/'readback.json').read_text());assert readback['synthetic_users']==6 and readback['all_old_passwords_denied'] and readback['all_new_passwords_accepted'] and readback['read_only_transaction'] and readback['external_connect_denied']
result={'decision':'ACCESS-QA-01 OPEN: functional focus patch verified; submit visible-focus CSS supplement approval required','closed_ids':[],'open_ids':['ACCESS-QA-01'],'approved_plan':'docs/qa/access-qa01-recheck-2026-10-14-r1/IMPLEMENTATION_PLAN.md','supplement_plan':'CSS_SUPPLEMENT_PLAN.md','head':head,'branch':branch,'active_run':active,'application_files':[app],'baseline_files':len(entry['files']),'unchanged_files':unchanged,'missing_files':missing,'unexpected_changes':changed,'other_new_paths':new_other,'old_processes':processes,'old_containers':containers,'runtime_source_match':runtime_match,'sole_fresh_locales':manifest['locales'],'shared_MO_preserved':all(digest(ROOT/p)==sha for p,sha in entry['files'].items()if p.endswith('.mo')),'backend_methods_pass':9,'backend_receipt_before_JS_timing_refinement':True,'observations':counts,'accepted_state_rows_retained_with_provenance':198,'png_count':len(png),'readonly_readback':readback,'module07_acceptance':'NOT RUN','production':'NOT RUN','integrity_gate_exit_scope':'Preservation/source/locale/evidence consistency only; not semantic acceptance of the18FAIL'}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
assert not changed and not missing and not new_other and head==entry['head'] and branch==entry['branch'] and active==entry['active_run'] and runtime_match and all(p['identity_unchanged']for p in processes) and all(c['preserved']for c in containers)
print(json.dumps({k:v for k,v in result.items()if k not in ('old_processes','old_containers')},ensure_ascii=False))
