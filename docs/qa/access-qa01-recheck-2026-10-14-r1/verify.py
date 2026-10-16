import hashlib,json,os,subprocess,sys,time,urllib.request,importlib.util
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entry=json.loads((HERE/'entry.json').read_text());changed=[];missing=[];unchanged=0
guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md'
note=next(s+'\n\n' for s in (ROOT/guide).read_text().splitlines() if s.startswith('- Module07 PLAN ACCESS-QA-01 —'))
for p,h in entry['files'].items():
 file=ROOT/p
 if not file.is_file():missing.append(p);continue
 if digest(file)==h:unchanged+=1;continue
 if p==guide and hashlib.sha256(file.read_bytes().replace(note.encode(),b'',1)).hexdigest()==h:continue
 changed.append(p)
spec=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
manifest=builder.verify(SCRATCH/'locales/manifest.json',ROOT/'locale');assert manifest['locales']==['ru','az','en']
server=json.loads((HERE/'server.json').read_text());pid=server['pid'];proc=Path('/proc')/str(pid)
args=[s.decode() for s in (proc/'cmdline').read_bytes().split(b'\0') if s]
runtime=json.load(urllib.request.urlopen(server['url']+'/qa/source/'));(HERE/'runtime-source-final.json').write_text(json.dumps(runtime,indent=2))
runtime_match=runtime['pid']==pid and runtime['startup_matches_disk'] and runtime['loaded_template_sha256']==digest(ROOT/'src/catalog/templates/auth/login.html') and str((proc/'cwd').resolve())==str(ROOT) and args==server['argv']
focus=json.loads((HERE/'focus-matrix.js.result.json').read_text());reset=json.loads((HERE/'reset-flow.js.result.json').read_text());resume=json.loads((HERE/'reset-flow-resume.js.result.json').read_text())
rows=focus['rows']+reset['rows']+resume['rows'];counts={s:sum(r['status']==s for r in rows)for s in ('PASS','FAIL')};assert len(focus['rows'])==162 and len(reset['rows'])+len(resume['rows'])==45 and not resume.get('error')
assert len({(r['lang'],r['width'])for r in focus['rows']})==18
assert not focus['diagnostics']['pageerrors'] and not resume['diagnostics']['pageerrors'] and not reset['diagnostics']['pageerrors']
png=[]
for p in sorted((HERE/'screenshots').glob('*.png')):
 with Image.open(p)as im:png.append({'path':str(p.relative_to(HERE)),'sha256':digest(p),'width':im.width,'height':im.height})
(HERE/'png-manifest.json').write_text(json.dumps(png,indent=2));assert {item['path'] for item in png} == {f'screenshots/{lang}-{width}-{state}.png' for lang in ('ru','az','en') for width in (360,390,768,1024,1280,1440) for state in ('modal','focus-escaped')} | {f'screenshots/{lang}-390-{state}.png' for lang in ('ru','az','en') for state in ('network-error','loading','success','replay-denied')}
processes=[]
for item in entry['foreign_processes']:
 if item['args'][:2]==['/bin/bash','-c'] and any("name='access-qa01-recheck-2026-10-14-r1'" in a and 'paths=subprocess.check_output' in a for a in item['args'][2:]):continue  # exact own snapshot shell, not an app server
 p=Path('/proc')/str(item['pid'])
 try:ok=str((p/'cwd').resolve())==item['cwd'] and [a.decode(errors='replace')for a in(p/'cmdline').read_bytes().split(b'\0')if a]==item['args']
 except OSError:ok=False
 processes.append({'pid':item['pid'],'identity_unchanged':ok})
containers={c['ID']:c for c in [json.loads(line)for line in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]}
container_rows=[{'id':c['id'],'name':c['name'],'preserved':c['id']in containers and containers[c['id']]['Names']==c['name'] and containers[c['id']]['Ports']==c['ports'] and containers[c['id']]['State']==c['state']}for c in entry['containers']]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip();active=[s for s in(ROOT/'docs/task33/implementation-status.md').read_text().splitlines()if s.startswith('active_run:')]
result={'decision':'RECHECK COMPLETE; ACCESS-QA-01 CONFIRMED OPEN; PLAN AWAITING USER APPROVAL','head':head,'branch':branch,'active_run':active,'application_patch':False,'baseline_files':len(entry['files']),'unchanged_files':unchanged,'allowed_prior_file_change':guide,'unexpected_changed_files':changed,'missing_files':missing,'old_processes':processes,'old_containers':container_rows,'runtime_source_match':runtime_match,'sole_fresh_locale_manifest':True,'locales':manifest['locales'],'browser_counts':counts,'matrix_observations':len(focus['rows']),'reset_observations':len(reset['rows'])+len(resume['rows']),'png_count':len(png),'module_acceptance':'NOT RUN','production':'NOT RUN','setup_attempts_retained':True}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
assert not changed and not missing and head==entry['head'] and branch==entry['branch'] and active==entry['active_run'] and runtime_match and all(r['identity_unchanged']for r in processes) and all(r['preserved']for r in container_rows)
print(json.dumps({k:v for k,v in result.items()if k not in('old_processes','old_containers')},ensure_ascii=False))
