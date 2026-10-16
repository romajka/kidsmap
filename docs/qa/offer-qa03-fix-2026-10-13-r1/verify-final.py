import hashlib,json,subprocess,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
entry=json.loads((P/'entry.json').read_text());allowed={'src/catalog/services/pricing_plans.py','src/catalog/photo_views.py','static/js/permanent_place_photos.js','static/js/owner_place_continuous.js','src/catalog/testcases/test_offer_qa03_error_targets.py','docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/qa/module-acceptance-prompts.md','docs/superpowers/plans/2026-10-13-offer-qa03-structured-error-focus.md'};prefix=str(P.relative_to(R))+'/'
changed=[]
for name,digest in entry['hashes'].items():
 if name in allowed or name.startswith(prefix):continue
 f=R/name
 if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:changed.append(name)
assert not changed,changed
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip();active=[s for s in (R/'docs/task33/implementation-status.md').read_text().splitlines() if s.startswith('active_run:')];assert head==entry['head'] and branch==entry['branch'] and active==['active_run: NONE']
source=json.loads((P/'entry-final.json').read_text())['source_files'];assert all(hashlib.sha256((R/name).read_bytes()).hexdigest()==digest for name,digest in source.items())
manifest=json.loads((P/'source-change-manifest.json').read_text());assert len(manifest)==5 and all(hashlib.sha256((R/m['file']).read_bytes()).hexdigest()==m['after'] for m in manifest)
server=json.loads((P/'server.json').read_text());assert server['script'].encode() in Path('/proc/'+str(server['pid'])+'/cmdline').read_bytes();receipt=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=10));assert receipt['testing'] and receipt['pid']==server['pid'] and receipt['entry_matches_startup'] and receipt['startup_matches_disk'];(P/'runtime-version-final.json').write_text(json.dumps(receipt,indent=2))
files=['native-matrix-final.json','billing-keyboard.result.json','admin-browser.result.json','moderation.result.json'];rows=[]
for name in files:
 result=json.loads((P/name).read_text());assert not result.get('error'),result;rows.extend(result['rows'])
assert len({r['id'] for r in rows})==len(rows)==361 and all(r['status']=='PASS' for r in rows)
pngs=[{'file':str(f.relative_to(P)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'kind':'diagnostic' if 'diagnostic-screenshots' in f.parts else 'accepted'} for f in sorted(P.rglob('*.png'))];(P/'png-manifest.json').write_text(json.dumps(pngs,indent=2));assert sum(p['kind']=='accepted' for p in pngs)==96 and len(pngs)==99
assert json.loads((P/'backend-green.command.json').read_text())['exit']==0 and 'Ran 14 tests' in (P/'backend-green.txt').read_text() and '\nOK\n' in (P/'backend-green.txt').read_text()
for name in ['readonly-candidate-readback-corrected','readonly-approved-readback','js-continuous-syntax','js-photo-syntax','locale-final-verify']:assert json.loads((P/(name+'.command.json')).read_text())['exit']==0,name
verification={'checkout':str(R),'head':head,'branch':branch,'active_run':'NONE','allowed_source_files':5,'incoming_unapproved_changes':changed,'runtime_source_match':True,'backend_unique_methods_pass':14,'native_unique_assertions_pass':361,'native_accepted_failures':0,'native_png':96,'diagnostic_png':3,'historical_raw_harness_failures_retained':True,'locale_manifest_verified':True,'no_shared_mo_changes':True,'foreign_stands_controlled':False,'full_module05':'NOT RUN','production':'NOT RUN','git_mutations':False,'closed_ids':['OFFER-QA-03']};(P/'verification.json').write_text(json.dumps(verification,indent=2));print(json.dumps(verification))
with (P/'COMMANDS.md').open('w') as f:
 f.write('# Exact own-profile commands / exits\n\nSee raw logs and explicit RED/harness distinctions in REPORT.md. Browser native CLI0 means harness completed; accepted assertions are separately verified.\n\n')
 for line in (P/'commands.jsonl').read_text().splitlines():
  item=json.loads(line);f.write('```json\n'+json.dumps(item,ensure_ascii=False)+'\n```\n\n')
