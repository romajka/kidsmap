import json,hashlib,subprocess,urllib.request,importlib.util,time
from pathlib import Path
from PIL import Image
h=Path(__file__).resolve().parent;r=h.parents[2];load=lambda n:json.loads((h/n).read_text());d=load('native-recheck.js.result.json');assert d['complete']and len(d['rows'])==13;fail=[x for x in d['rows']if x['status']=='FAIL'];assert len(fail)==4 and all(x['id']=='unpublish confirmation uses selected language'and x['lang']in('az','en')for x in fail);assert not[x for x in d['diagnostics']if x.get('local')];assert d['before']==d['after']
server=load('snapshot.json')['server'];source=json.load(urllib.request.urlopen(server['url']+'/qa/source/'));assert source['startup_matches_disk']and source['source']==load('runtime-source-entry.json')['source'];(h/'runtime-source-final.json').write_text(json.dumps(source,indent=2))
spec=importlib.util.spec_from_file_location('isolated_locales',r/'scripts/build_isolated_locales.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b);m=b.verify(r/'.tmp/mod-qa05-fix-2026-10-16-r1/locales/manifest.json',r/'locale');assert source['sole_locale_paths']==[m['locale_root']]
assert not(r/'src/catalog/testcases/test_mod06_unpublish_localization.py').exists()
for x in load('proposal-manifest.json'):
 assert not x['applied']and hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['source_sha256'];assert hashlib.sha256((h/'candidate'/x['path']).read_bytes()).hexdigest()==x['candidate_sha256']
commands=[['node','--check',str(h/'candidate/static/admin/js/kidsmap_place_changelist.js')]]
for lang in('ru','az','en'):commands.append(['msgfmt','--check-format','-o',str(r/'.tmp/mod-qa05-fix-2026-10-16-r1'/f'candidate-mod06-{lang}.mo'),str(h/'candidate/locale'/lang/'LC_MESSAGES/django.po')])
for args in commands:
 t=time.monotonic();p=subprocess.run(args,capture_output=True,text=True)
 with(h/'commands.jsonl').open('a')as f:f.write(json.dumps({'argv':args,'exit':p.returncode,'seconds':round(time.monotonic()-t,3)})+'\n')
 assert p.returncode==0,p.stderr
manifest=[]
for p in sorted((h/'screenshots').glob('*.png')):
 with Image.open(p)as im:size=list(im.size);im.verify()
 manifest.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':size})
assert len(manifest)==6;(h/'png-manifest.json').write_text(json.dumps(manifest,indent=2));result={'id':'MOD-QA-06','status':'PLAN COMPLETE / CONFIRMED OPEN','source_fail':4,'control_pass':9,'cells':6,'png':6,'application_changes':0,'planned_files':6,'candidate_files':5,'local_diagnostics':0,'domain_unchanged':True,'source_matches':True,'candidate_syntax_catalog_checks':4,'not_run':['application patch','new backend regression RED/GREEN','postpatch18cell GREEN','actual unpublish/delete and postsubmit notifications','full08/global/production']};(h/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
