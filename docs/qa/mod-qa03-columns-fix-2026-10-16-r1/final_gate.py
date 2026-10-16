import hashlib,importlib.util,json,subprocess,urllib.request
from pathlib import Path
from PIL import Image
h=Path(__file__).resolve().parent;r=h.parents[2];load=lambda n:json.loads((h/n).read_text());accepted=[];replaced=[];boundaries=[];diagnostics=[]
for lang in('ru','az','en'):
 for width in(360,390,768,1024,1280,1440):
  name='native-ru-390.pilot.json'if lang=='ru'and width==390 else f'native-{lang}-{width}.js.result.json'
  d=load(name);assert d['complete']and len(d['rows'])==(35 if width<768 else 62);assert d['before']==d['after']==load('domain-before.json')
  assert not [x for x in d['diagnostics']if x.get('local')]
  for x in d['rows']:
   if x['status']=='FAIL':
    assert lang=='ru'and width==390 and x['id']=='Tab reaches visible keyboard checkbox';replaced.append(x)
   else:assert x['status']=='PASS';accepted.append(x)
  boundaries+=d['boundary'];diagnostics+=d['diagnostics']
assert len(replaced)==3
supp=load('native-focus-supplement.js.result.json');assert supp['complete']and len(supp['rows'])==3 and all(x['status']=='PASS'for x in supp['rows']);accepted+=supp['rows']
assert len(accepted)==954
edges=load('native-edges.js.result.json');assert edges['complete']and all(x['status']=='PASS'for x in edges['rows']);assert edges['before']==edges['after']==load('domain-before.json');assert not[x for x in edges['diagnostics']if x.get('local')]
red=load('native-red.js.result.json');assert [(x['model'],x['status'])for x in red['rows']]==[('place','PASS'),('event','FAIL'),('specialist','FAIL')]
assert 'Ran 5 tests' in(h/'tests-red.txt').read_text()and 'failures=68'in(h/'tests-red.txt').read_text();assert 'ERROR:'not in(h/'tests-red.txt').read_text();assert 'Ran 9 tests'in(h/'tests-green.txt').read_text()and '\nOK\n'in(h/'tests-green.txt').read_text()
server=load('server-current.json');pid=server['pid'];assert[a.decode()for a in(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0')if a]==server['argv'];assert(Path('/proc')/str(pid)/'cwd').resolve()==r
source=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10));assert source['pid']==pid and source['startup_matches_disk']and source['source']==load('runtime-source-baseline.json')and len(source['source'])==957;(h/'runtime-source-final.json').write_text(json.dumps(source,indent=2))
assert len(source['sole_locale_paths'])==1;assert all(str(Path(source['sole_locale_paths'][0])/lang/'LC_MESSAGES/django.mo')in source['actual_opened_MO']for lang in('ru','az','en'));assert not any(str(r/'locale')+'/'in n for n in source['actual_opened_MO'])
spec=importlib.util.spec_from_file_location('isolated_locales',r/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);builder.verify(r/'.tmp'/h.name/'locales/manifest.json',r/'locale')
domain=json.load(urllib.request.urlopen(server['url']+'/qa/state/',timeout=10));assert domain==load('domain-before.json');(h/'domain-final.json').write_text(json.dumps(domain,indent=2))
allowed={'src/catalog/templatetags/admin_dashboard_tags.py','src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html','static/admin/js/kidsmap_place_changelist.js'}
old=json.loads((r/'docs/qa/mod-qa03-search-fix-2026-10-16-r1/runtime-source-final.json').read_text())['source'];retained=[n for n,v in old.items()if n not in allowed and hashlib.sha256((r/n).read_bytes()).hexdigest()==v];assert len(retained)==len(old)-3
js='static/admin/js/kidsmap_place_changelist.js';before=(h/'entry-source'/js).read_text();after=(r/js).read_text();start='    var columnCheckboxes =';end='    /* --------------------------------------------------------------------------\n       Click outside to close';assert before.split(start)[0]==after.split(start)[0]and before.split(end)[1]==after.split(end)[1]
name='src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html';before=(h/'entry-source'/name).read_text();after=(r/name).read_text();assert before.split('        <details class="km-columns-details"')[0]==after.split('        {% km_column_options')[0];assert before.split('      <!-- Сохранение')[1]==after.split('      <!-- Сохранение')[1]
retention={'prior_search_source_files':len(old),'unchanged_prior_source_files':len(retained),'changed_only_columns_paths':sorted(allowed),'prior_CSS_file_unchanged':True,'prior_row_menu_JS_prefix_suffix_unchanged':True,'prior_search_sort_template_prefix_suffix_unchanged':True,'previous_scoped_reports':['../mod-qa03-fix-2026-10-15-r1/REPORT.md','../mod-qa03-menu-fix-2026-10-15-r1/REPORT.md','../mod-qa03-sort-fix-2026-10-16-r1/REPORT.md','../mod-qa03-search-fix-2026-10-16-r1/REPORT.md'],'full_previous_suites_repeated':False};(h/'retained-evidence.json').write_text(json.dumps(retention,indent=2))
pres=load('preservation.json');entry=load('entry.json');assert set(pres['changed_entry_files'])<=allowed|{'docs/qa/continuation-and-repair-prompts-2026-10-11.md'};assert not pres['missing_entry_files'];assert all(v['current']and v['current']['ID']==v['entry']['ID']and v['current']['Names']==v['entry']['Names']for v in pres['container_drift']);assert all(pres[k]==entry[k]for k in('head','branch','active_run'))
manifest=[]
for p in sorted(h.rglob('*.png')):
 with Image.open(p)as im:size=list(im.size);im.verify()
 manifest.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':size,'phase':'RED'if p.name.startswith('columns-red-')else'GREEN / retained pilot or targeted supplement'})
(h/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
for name,args in [('diff-check',['git','diff','--check']),('js-syntax',['node','--check','static/admin/js/kidsmap_place_changelist.js'])]:
 p=subprocess.run(args,cwd=r,capture_output=True,text=True);(h/(name+'.txt')).write_text(p.stdout+p.stderr);assert p.returncode==0
summary={'status':'SCOPED LOCAL PASS: columns; foreign HTTP continuity NOT VERIFIED','MOD_QA_03':'All identified local causes closed; full module08 acceptance pending','backend_methods':9,'new_regression_methods':5,'representative_existing_methods':4,'red_assertion_failures':68,'native_source_red_fail':2,'native_control_red_pass':1,'matrix_accepted_pass':len(accepted),'raw_focus_oracle_fail_replaced_only':3,'edge_pass':len(edges['rows']),'native_accepted_total':len(accepted)+len(edges['rows']),'model_locale_width_cells':54,'reachable_sidebar_cells':90,'overlay_boundaries':len(boundaries),'local_diagnostics':0,'png_count':len(manifest),'source_files':957,'domain_unchanged':True,'head':pres['head'],'branch':pres['branch'],'active_run':pres['active_run'],'preservation':pres,'retained_evidence':retention,'limitations':['Owned HTTP/controller vanished during QA; cause not established; only own services restarted. Seven complete batches and20partial accepted assertions retained without repetition.','Entry foreign HTTP104840 absent and two foreign container states changed during environment interruption: continuity NOT VERIFIED. No foreign restart; identities/files/HEAD/active_run checked independently.','Only targeted columns checks and4representative existing test methods; previous unchanged full search/sort/CSS/menu suites not repeated. Full module08/global/production NOT RUN.','Malformed/legacy localStorage setup explicitly SIMULATED; native primary keyboard/checkbox/reload/navigation flows unmodified.','Existing untranslated admin/model labels are reused, including Updated at; no full UI localization claim. Physical devices/non-Chromium NOT RUN.']}
(h/'verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in summary.items()if k not in('preservation','retained_evidence','limitations')}))
