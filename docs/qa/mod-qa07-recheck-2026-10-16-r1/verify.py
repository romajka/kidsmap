import json,hashlib,subprocess,urllib.request,importlib.util
from pathlib import Path
from PIL import Image
h=Path(__file__).resolve().parent;r=h.parents[2];load=lambda n:json.loads((h/n).read_text());rows=[]
for lang in('ru','az','en'):
 d=load(f'native-{lang}.js.result.json');assert d['complete']and len(d['rows'])==12;assert d['before']==d['after']==load('domain-before.json');assert not[x for x in d['diagnostics']if x.get('local')];rows+=d['rows']
fail=[x for x in rows if x['status']=='FAIL'];assert len(fail)==12 and len(rows)==36;assert all(x['id']in('one required error produces one readable summary link','summary keyboard link focuses first specialization checkbox')for x in fail);assert sum(x['id']=='actual native Save confirmation accepted'and x['status']=='PASS'for x in rows)==6
server=load('server.json');p=Path('/proc')/str(server['pid']);assert[x.decode()for x in(p/'cmdline').read_bytes().split(b'\0')if x]==server['argv'];source=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10));assert source['startup_matches_disk']and source['source']==load('runtime-source-red.json')['source']and source['pid']==server['pid'];(h/'runtime-source-final.json').write_text(json.dumps(source,indent=2));domain=json.load(urllib.request.urlopen(server['url']+'/qa/state/'));assert domain==load('domain-before.json');(h/'domain-final.json').write_text(json.dumps(domain,indent=2))
spec=importlib.util.spec_from_file_location('isolated_locales',r/'scripts/build_isolated_locales.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);m=b.verify(r/'.tmp'/h.name/'locales/manifest.json',r/'locale');assert source['sole_locale_paths']==[m['locale_root']];assert all(str(Path(m['locale_root'])/l/'LC_MESSAGES/django.mo')in source['actual_opened_MO']for l in('ru','az','en'));assert not any(str(r/'locale')+'/'in n for n in source['actual_opened_MO'])
for x in load('proposal-manifest.json'):
 assert not x['applied']and hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['source_sha256']and hashlib.sha256((h/'candidate'/x['path']).read_bytes()).hexdigest()==x['candidate_sha256']
assert not(r/'src/catalog/testcases/test_mod07_specialist_error_summary.py').exists();pres=load('preservation.json');e=load('entry.json');assert set(pres['changed_entry_files'])<= {'docs/qa/continuation-and-repair-prompts-2026-10-11.md'}and not pres['missing_entry_files']and not pres['container_drift'];assert all(x['present']and x['same_args']and x['same_cwd']for x in pres['foreign_process_checks']);assert all(pres[k]==e[k]for k in('head','branch','active_run'))
manifest=[]
for p in sorted((h/'screenshots').glob('*.png')):
 with Image.open(p)as im:size=list(im.size);im.verify()
 manifest.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':size,'phase':'RED current unpatchedsource'})
assert len(manifest)==6;(h/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
for name,args in [('candidate-js-syntax',['node','--check',str(h/'candidate/static/admin/js/specialist_admin.js')]),('diff-check',['git','diff','--check'])]:
 p=subprocess.run(args,cwd=r,capture_output=True,text=True);(h/(name+'.txt')).write_text(p.stdout+p.stderr)
 with(h/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':name,'argv':args,'exit':p.returncode})+'\n')
 assert p.returncode==0
v={'id':'MOD-QA-07','status':'CONFIRMED OPEN / PLAN COMPLETE','application_changes':0,'source_fail':12,'control_pass':24,'cells':6,'native_confirmed_invalid_save':6,'png':6,'domain_and_relations_unchanged':True,'local_diagnostics':0,'source_files':len(source['source']),'proposed_existing_app_files':2,'proposed_new_test_files':1,'head':pres['head'],'branch':pres['branch'],'active_run':pres['active_run'],'preservation':pres,'not_run':['patch','new backend RED/GREEN','postpatch18cells','multiple/inline dynamiccases','fullmodule08/global/production/commit/push/deploy']};(h/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in v.items()if k!='preservation'}))
