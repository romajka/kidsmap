"""Current semantic gate for approved search scope, not whole MOD03/08 acceptance."""
import hashlib,importlib.util,json,subprocess,urllib.request
from pathlib import Path
from PIL import Image
h=Path(__file__).resolve().parent;r=h.parents[2];load=lambda n:json.loads((h/n).read_text())
main=[];edges=[];boundaries=[];external=[]
for lang in ('ru','az','en'):
 for width in (360,390,768,1024,1280,1440):
  d=load(f'native-{lang}-{width}.js.result.json');assert d['complete'];assert all(v['status']=='PASS' for v in d['rows']);assert not [x for x in d['diagnostics']if x.get('local')]
  assert d['before']==d['after']==load('domain-before.json')
  assert len(d['rows'])==(35 if width<768 else 62)
  for model in ('place','event','specialist'):
   for sidebar in ('expanded','collapsed'):
    cell=[v for v in d['rows']if v.get('model')==model and v.get('sidebar')==sidebar and v['id']not in('domain unchanged in batch','current runtime source matches disk')]
    assert len(cell)==(1 if width<768 and sidebar=='expanded'else 10),(lang,width,model,sidebar,len(cell))
  main+=d['rows'];boundaries+=d['boundary'];external+=d['diagnostics']
 d=load(f'native-edge-{lang}.js.result.json');assert d['complete']and len(d['rows'])==32 and all(v['status']=='PASS'for v in d['rows']);assert d['before']==d['after']==load('domain-before.json');assert not[x for x in d['diagnostics']if x.get('local')];edges+=d['rows'];external+=d['diagnostics']
red=load('native-red.js.result.json');green=load('native-exact-green.js.result.json');assert len(red['rows'])==len(green['rows'])==3 and all(v['status']=='FAIL'for v in red['rows'])and all(v['status']=='PASS'for v in green['rows'])
assert 'Ran 6 tests' in(h/'tests-red.txt').read_text()and 'failures=19' in(h/'tests-red.txt').read_text()
assert 'Ran 14 tests' in(h/'tests-green-corrected.txt').read_text()and '\nOK\n' in(h/'tests-green-corrected.txt').read_text()
server=load('server-current.json');pid=server['pid'];assert [x.decode()for x in(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')if x]==server['argv'];assert (Path('/proc')/str(pid)/'cwd').resolve()==r
current=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10));assert current['pid']==pid and current['startup_matches_disk']and current['source']==load('runtime-source-baseline.json')and len(current['source'])==956
(h/'runtime-source-final.json').write_text(json.dumps(current,indent=2));assert len(current['sole_locale_paths'])==1
assert all(str(Path(current['sole_locale_paths'][0])/lang/'LC_MESSAGES/django.mo')in current['actual_opened_MO']for lang in('ru','az','en'));assert not any(str(r/'locale')+'/'in x for x in current['actual_opened_MO'])
spec=importlib.util.spec_from_file_location('isolated_locales',r/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);builder.verify(r/'.tmp'/h.name/'locales/manifest.json',r/'locale')
domain=json.load(urllib.request.urlopen(server['url']+'/qa/state/',timeout=10));assert domain==load('domain-before.json');(h/'domain-final.json').write_text(json.dumps(domain,indent=2))
columns=load('native-columns-recheck.js.result.json');assert columns['complete']and columns['domain_unchanged']and columns['before']==domain;assert [(x['model'],x['status'])for x in columns['rows']]==[('place','PASS'),('event','FAIL'),('specialist','FAIL')]
pres=load('preservation.json');entry=load('entry.json');allowed={'src/catalog/templatetags/admin_dashboard_tags.py','src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html','docs/qa/continuation-and-repair-prompts-2026-10-11.md'};assert set(pres['changed_entry_files'])<=allowed and not pres['missing_entry_files']and not pres['container_drift'];assert all(pres[k]==entry[k]for k in('head','branch','active_run'))
manifest=[]
for p in sorted(h.rglob('*.png')):
 with Image.open(p)as im:size=list(im.size);im.verify()
 phase='interrupted attempt'if 'interruption-01'in p.parts else 'columns RED (separate OPEN cause)'if p.name.startswith('columns-red-')else'SEARCH RED'if p.name.startswith('red-')else'SEARCH GREEN'
 manifest.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':size,'phase':phase})
(h/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
check=subprocess.run(['git','diff','--check'],cwd=r,capture_output=True,text=True);(h/'diff-check.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
commands=[json.loads(x)for x in(h/'commands.jsonl').read_text().splitlines()];required=[f'native-{lang}-{width}.js'for lang in('ru','az','en')for width in(360,390,768,1024,1280,1440)]+[f'native-edge-{lang}.js'for lang in('ru','az','en')]+['native-columns-recheck.js','tests-green-corrected']
assert all(any(c['name']==name and c['exit']==0 for c in commands)for name in required)
result={'status':'SCOPED LOCAL PASS: SEARCH FILTER preservation','whole_MOD_QA_03':'OPEN: columns','head':pres['head'],'branch':pres['branch'],'active_run':pres['active_run'],'backend_methods':14,'fresh_red_methods':6,'fresh_red_assertion_failures':19,'native_red_fail':3,'native_exact_green':3,'matrix_pass':len(main),'edge_pass':len(edges),'native_accepted_total':len(main)+len(edges)+3,'model_locale_width_cells':54,'reachable_sidebar_cells':90,'overlay_boundaries':len(boundaries),'local_diagnostics':0,'expected_external_blocked_diagnostics':len(external),'png_count':len(manifest),'source_files':956,'domain_unchanged':True,'preservation':pres,'limitations':['Six complete mobile batches retained; interrupted RU768 checkpoint and PNG preserved; only incomplete desktop batches rerun. Owned HTTP restarted after turn interruption, no continuity claim for the stopped process.','First GREEN fixture-order mistakes corrected with explicit sort setup; assertions unchanged; all raw outputs retained.','External fonts/resources blocked. Physical devices and non-Chromium browsers NOT RUN. Existing mixed dashboard translations are outside search scope.','Columns fresh native Event/Specialist FAIL; separate next four-file PLAN awaiting approval.','MOD04–08/full module08/global/production/commit/push/deploy NOT RUN.']}
(h/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in('preservation','limitations')}))
