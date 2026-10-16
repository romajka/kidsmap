import hashlib,json,subprocess,urllib.request,importlib.util,difflib,time,re
from pathlib import Path
from PIL import Image
h=Path(__file__).resolve().parent;r=h.parents[2];load=lambda n:json.loads((h/n).read_text());allowed={'static/admin/js/kidsmap_place_changelist.js','src/catalog/templates/admin/catalog/place/change_list.html','locale/ru/LC_MESSAGES/django.po','locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po'};guide='docs/qa/continuation-and-repair-prompts-2026-10-11.md';test='src/catalog/testcases/test_mod06_unpublish_localization.py'
red=(h/'tests-red.txt').read_text();assert 'Ran 3 tests'in red and 'FAILED (failures=3)'in red and 'ERROR:'not in red
first=(h/'tests-green.txt').read_text();assert 'Ran 4 tests'in first and 'FAILED (failures=2)'in first and 'ERROR:'not in first;corr=(h/'tests-green-correction.txt').read_text();assert 'Ran 2 tests'in corr and '\nOK\n'in corr and 'FAIL:'not in corr;assert hashlib.sha256((r/test).read_bytes()).hexdigest()==load('test-source-manifest.json')['sha256']
red=load('native-red.js.result.json');assert red['complete']and sum(x['status']=='FAIL'for x in red['rows'])==1;assert not[x for x in red['diagnostics']if x.get('local')]
rows=[];failed=[]
for lang in('ru','az','en'):
 d=load(f'native-{lang}-first.json'if lang!='en'else'native-en.js.result.json');assert d['complete']and len(d['rows'])==34;assert d['before']==d['after']==load('domain-before.json');assert not[x for x in d['diagnostics']if x.get('local')]
 for x in d['rows']:
  if x['status']=='FAIL':failed.append(x)
  else:assert x['status']=='PASS';rows.append(x)
supp=load('native-correction.js.result.json');assert supp['complete']and len(supp['rows'])==len(failed)==15 and all(x['status']=='PASS'for x in supp['rows']);key=lambda x:(x['id'],x['lang'],x['width']);assert{key(x)for x in failed}=={key(x)for x in supp['rows']};assert supp['before']==supp['after']==load('domain-before.json');assert not[x for x in supp['diagnostics']if x.get('local')];rows+=supp['rows'];assert len(rows)==102
assert len([x for x in rows if x['id']=='exact localized title body cancel confirm'])==18;assert len([x for x in rows if x['id']=='dialog and both controls fit viewport'])==18
edge=load('native-edges.js.result.json');assert edge['complete']and len(edge['rows'])==11 and all(x['status']=='PASS'for x in edge['rows']);assert edge['before']==edge['after']==load('domain-before.json');assert not[x for x in edge['diagnostics']if x.get('local')];sim=[x for x in edge['rows']if x['id'].startswith('SIMULATED')];assert len(sim)==9
server=load('server-current.json');proc=Path('/proc')/str(server['pid']);assert[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x]==server['argv'];assert(proc/'cwd').resolve()==r
source=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10));assert source['pid']==server['pid']and source['startup_matches_disk']and source['source']==load('runtime-source-baseline.json')and len(source['source'])==959;(h/'runtime-source-final.json').write_text(json.dumps(source,indent=2))
spec=importlib.util.spec_from_file_location('isolated_locales',r/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);locale=builder.verify(r/'.tmp'/h.name/'locales-green/manifest.json',r/'locale');assert source['sole_locale_paths']==[locale['locale_root']];assert all(str(Path(locale['locale_root'])/lang/'LC_MESSAGES/django.mo')in source['actual_opened_MO']for lang in('ru','az','en'));assert not any(str(r/'locale')+'/'in n for n in source['actual_opened_MO'])
domain=json.load(urllib.request.urlopen(server['url']+'/qa/state/',timeout=10));assert domain==load('domain-before.json');(h/'domain-final.json').write_text(json.dumps(domain,indent=2))
pres=load('preservation.json');entry=load('entry.json');assert set(pres['changed_entry_files'])<=allowed|{guide}and not pres['missing_entry_files'];assert all(pres[k]==entry[k]for k in('head','branch','active_run'));interrupt=load('interruption.json');assert not interrupt['foreign_restart_performed'];assert all(not x['present']for x in interrupt['foreign_http']);assert not pres['container_drift']
# Interruption killed earlier QA HTTP. Never convert this limitation to a preservation PASS.
assert all(not x['present']for x in pres['foreign_process_checks']);pres['process_continuity']='NOT VERIFIED:3entry QA HTTP disappeared during explicit interruption; no foreign restart; own HTTP recovered only'
(h/'preservation.json').write_text(json.dumps(pres,indent=2))
patch=''
for name in sorted(allowed):
 before=(h/'entry-source'/name).read_text();after=(r/name).read_text();patch+=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
patch+=''.join(difflib.unified_diff([], (r/test).read_text().splitlines(True),fromfile='/dev/null',tofile='b/'+test));(h/'implementation.patch').write_text(patch)
manifest=[]
for f in sorted(h.rglob('*.png')):
 with Image.open(f)as im:size=list(im.size);im.verify()
 relative=str(f.relative_to(h));phase='GREEN'
 if relative.startswith('interrupted-evidence/'):phase='INTERRUPTED partial; not accepted'
 elif relative.startswith('first-screenshots/')or f.name.startswith('modal-az-'):phase='initial failed run retained'
 elif f.name.startswith('red-'):phase='RED'
 elif f.name.startswith('sim-'):phase='explicit SIMULATED edge'
 manifest.append({'path':relative,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'size':size,'phase':phase})
primary=[]
for lang in('ru','az','en'):
 for width in(360,390,768,1024,1280,1440):
  prefix='corrected-modal-'if lang=='az'or(lang=='ru'and width==360)else'modal-';path=f'screenshots/{prefix}{lang}-{width}.png';assert(h/path).exists();primary.append(path)
assert len(primary)==18;(h/'png-manifest.json').write_text(json.dumps({'all_png':manifest,'accepted_primary_cells':primary,'all_count':len(manifest)},indent=2))
for name,args in [('diff-check',['git','diff','--check']),('js-syntax',['node','--check','static/admin/js/kidsmap_place_changelist.js'])]:
 t=time.monotonic();p=subprocess.run(args,cwd=r,capture_output=True,text=True);(h/(name+'.txt')).write_text(p.stdout+p.stderr)
 with(h/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':name,'argv':args,'exit':p.returncode,'seconds':round(time.monotonic()-t,3)})+'\n')
 assert p.returncode==0
result={'status':'SCOPED LOCAL PASS; process continuity NOT VERIFIED','id':'MOD-QA-06','backend_unique_methods_accepted':4,'new_methods_accepted':3,'shared_methods_retained_pass':1,'backend_initial_red':3,'backend_first_green_fail_retained':2,'backend_affected_recheck_pass':2,'native_main_accepted':102,'native_original_failed_observations_replaced':15,'native_main_retained_pass':87,'native_primary_cells':18,'native_edge_checks':11,'native_explicit_simulated_checks':9,'native_edge_real_controls':2,'accepted_total_browser_checks':113,'native_fresh_red_source_fail':1,'png_total':len(manifest),'png_primary_cells':18,'local_diagnostics':0,'domain_unchanged':True,'source_files':959,'approved_existing_app_files':5,'new_regression_file':test,'head':pres['head'],'branch':pres['branch'],'active_run':pres['active_run'],'preservation':pres,'not_run':['full module08 until all tasks completed; global acceptance','actual unpublish/delete submissions, loading/error/success toasts','MOD07–08 new scopes; module09','production/commit/push/deploy/physical devices/non-Chromium'],'limitations':['3entry QA HTTP disappeared across explicit interruption; no foreign restart; continuity NOT VERIFIED. OwnPG same ID/volume/domain preserved.','Initial candidate used translate tag for percent placeholder; within approved template scope changed2tags to blocktranslate. Test assertions unchanged.','First RU1/AZ2 geometry sampled modal animation; harness now awaits existing animations, no CSS change. Only15failed browser observations rechecked;87PASS retained.','9explicit SIMULATED browser checks, separate from102primary actual UI checks and2edge controls.','Fingerprint covers Place/Event/Specialist full fields, not all tables. Local sessions/language changed through fictional login. External font requests blocked.']};(h/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in('preservation','not_run','limitations')}))
