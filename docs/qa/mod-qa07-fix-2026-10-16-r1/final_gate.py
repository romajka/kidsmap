import json,hashlib,subprocess,urllib.request,importlib.util,difflib,time
from pathlib import Path
from PIL import Image
h=Path(__file__).resolve().parent;r=h.parents[2];load=lambda n:json.loads((h/n).read_text());production={'src/catalog/templates/admin/catalog/specialist/change_form.html','static/admin/js/specialist_admin.js'};test='src/catalog/testcases/test_mod07_specialist_error_summary.py';guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md'
red=(h/'tests-red.txt').read_text();assert 'Ran 3 tests'in red and 'FAILED (failures=6)'in red and 'ERROR:'not in red;green=(h/'tests-green.txt').read_text();assert 'Ran 5 tests'in green and '\nOK\n'in green and 'FAIL:'not in green;assert hashlib.sha256((r/test).read_bytes()).hexdigest()==load('test-source-manifest.json')['sha256']
d=load('native-red.js.result.json');assert d['complete']and sum(x['status']=='FAIL'for x in d['rows'])==2;assert not[x for x in d['diagnostics']if x.get('local')];allrows=[]
for lang in('ru','az','en'):
 d=load(f'native-{lang}.js.result.json');assert d['complete']and len(d['rows'])==42 and all(x['status']=='PASS'for x in d['rows']);assert d['before']==d['after']==load('domain-before.json');assert not[x for x in d['diagnostics']if x.get('local')];allrows+=d['rows']
assert len(allrows)==126 and len([x for x in allrows if x['id']=='one required error produces one readable summary link'])==18
edge=load('native-edges.js.result.json');assert edge['complete']and len(edge['rows'])==58 and all(x['status']=='PASS'for x in edge['rows']);assert edge['before']==edge['after']==load('domain-before.json');assert not[x for x in edge['diagnostics']if x.get('local')];assert sum(x['id'].startswith('SIMULATED')for x in edge['rows'])==2
layout=load('native-layout-plan.js.result.json');assert layout['complete']and len(layout['rows'])==12;assert layout['before']==layout['after']==load('domain-before.json');assert not[x for x in layout['diagnostics']if x.get('local')];lf=[x for x in layout['rows']if x['status']=='FAIL'];assert len(lf)==3 and all(x['width']==390 and x['id']=='current error heading fits at most two readable lines'for x in lf);assert sum(x['id'].startswith('SIMULATED')and x['status']=='PASS'for x in layout['rows'])==6
server=load('server-current.json');proc=Path('/proc')/str(server['pid']);assert[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x]==server['argv'];assert(proc/'cwd').resolve()==r;source=json.load(urllib.request.urlopen(server['url']+'/qa/source/'));assert source['pid']==server['pid']and source['startup_matches_disk']and source['source']==load('runtime-source-baseline.json')and len(source['source'])==960;(h/'runtime-source-final.json').write_text(json.dumps(source,indent=2))
spec=importlib.util.spec_from_file_location('isolated_locales',r/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);locale=builder.verify(r/'.tmp'/h.name/'locales/manifest.json',r/'locale');assert source['sole_locale_paths']==[locale['locale_root']];assert all(str(Path(locale['locale_root'])/lang/'LC_MESSAGES/django.mo')in source['actual_opened_MO']for lang in('ru','az','en'));assert not any(str(r/'locale')+'/'in n for n in source['actual_opened_MO'])
domain=json.load(urllib.request.urlopen(server['url']+'/qa/state/'));assert domain==load('domain-before.json');(h/'domain-final.json').write_text(json.dumps(domain,indent=2))
pres=load('preservation.json');entry=load('entry.json');assert set(pres['changed_entry_files'])<=production|{guide}and not pres['missing_entry_files']and not pres['container_drift'];assert all(pres[k]==entry[k]for k in('head','branch','active_run'))
# Refresh process/container identities without repeating complete file hashing or any suites.
for item,check in zip(entry['foreign_processes'],pres['foreign_process_checks']):
 p=Path('/proc')/str(item['pid']);assert p.exists();assert[x.decode()for x in(p/'cmdline').read_bytes().split(b'\0')if x]==item['args'];assert str((p/'cwd').resolve())==item['cwd'];check.update(present=True,same_args=True,same_cwd=True)
containers=[{k:c[k]for k in('ID','Names','Ports','State')}for c in[json.loads(s)for s in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]];byid={c['ID']:c for c in containers};assert all(byid.get(c['ID'])==c for c in entry['containers']);(h/'preservation.json').write_text(json.dumps(pres,indent=2))
css=load('css-supplement-manifest.json');assert not css['applied']and hashlib.sha256((r/css['path']).read_bytes()).hexdigest()==css['source_sha256']and css['source_sha256']==entry['files'][css['path']];assert hashlib.sha256((h/'candidate-css.css').read_bytes()).hexdigest()==css['candidate_sha256']
patch=''
for name in sorted(production):patch+=''.join(difflib.unified_diff((h/'entry-source'/name).read_text().splitlines(True),(r/name).read_text().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
patch+=''.join(difflib.unified_diff([],(r/test).read_text().splitlines(True),fromfile='/dev/null',tofile='b/'+test));(h/'implementation.patch').write_text(patch)
manifest=[]
for p in sorted((h/'screenshots').glob('*.png')):
 with Image.open(p)as im:size=list(im.size);im.verify()
 phase='approved scope GREEN'
 if p.name.startswith('red-'):phase='RED before approved patch'
 elif p.name.startswith('layout-before-'):phase='new CSS cause actual source, OPEN'
 elif p.name.startswith('layout-candidate-'):phase='SIMULATED CSS feasibility, unapplied'
 elif p.name.startswith('sim-'):phase='SIMULATED unavailable controls'
 manifest.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':size,'phase':phase})
assert len(manifest)==62;(h/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
for name,args in [('diff-check',['git','diff','--check']),('js-syntax',['node','--check','static/admin/js/specialist_admin.js'])]:
 p=subprocess.run(args,cwd=r,capture_output=True,text=True);(h/(name+'.txt')).write_text(p.stdout+p.stderr)
 with(h/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':name,'argv':args,'exit':p.returncode})+'\n')
 assert p.returncode==0
v={'id':'MOD-QA-07','status':'APPROVED CORE LOCAL PASS / ID OPEN: CSS supplement approval pending','backend_methods_pass':5,'new_methods':3,'shared_methods':2,'red_new_methods_failed':2,'red_subtest_assertion_failures':6,'red_inline_control_pass':1,'native_primary_pass':126,'primary_cells':18,'native_edges_pass':58,'native_edges_explicit_simulated':2,'actual_ui_and_controls_pass':182,'approved_browser_checks_including_simulation':184,'native_red_source_fail':2,'layout_new_source_fail':3,'layout_baseline_controls_pass':3,'layout_explicit_simulated_candidate_pass':6,'png_count':62,'local_diagnostics':0,'source_files':960,'domain_and_relations_unchanged':True,'head':pres['head'],'branch':pres['branch'],'active_run':pres['active_run'],'preservation':pres,'application_files_changed_existing':2,'new_test_file':test,'unapplied_supplement':css['path'],'not_run':['CSS source patch and postpatch GREEN; whole MOD07 closure','full module08/global','actual successful mutation/delete/private document submission','MOD08 patch/module09/production/commit/push/deploy/non-Chromium/physical devices']};(h/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in v.items()if k!='preservation'}))
