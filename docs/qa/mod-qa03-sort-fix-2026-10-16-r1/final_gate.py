"""Semantic acceptance gate; CLI exit alone is insufficient."""
import hashlib,json,subprocess,urllib.request
from pathlib import Path
from PIL import Image
h=Path(__file__).resolve().parent;r=h.parents[2]
load=lambda n:json.loads((h/n).read_text())
matrix=[];replaced=[];boundaries=[];local_errors=[]
for lang in ('ru','az','en'):
 name=f'native-sort-{lang}.js.result.json' if(h/f'native-sort-{lang}.js.result.json').exists()else f'native-sort-{lang}.recovered.json'
 data=load(name);assert data['complete']
 for row in data['rows']:
  if row['status']=='FAIL':
   assert row['id']=='native flow completion' and row['model']=='event' and row['width']==1024 and row['sidebar']in('expanded','collapsed'),row
   replaced.append(row)
  else:
   assert row['status']=='PASS';matrix.append(row)
 boundaries+=data['boundary'];local_errors += [d for d in data['diagnostics']if d.get('local')]
 assert len([v for v in data['rows']if v['id'].startswith('real row order')])==120
 assert len([v for v in data['rows']if v['id'].startswith('active option')])==120
 assert len([v for v in data['rows']if v['id']=='reset clears search sort filters'])==20
assert len(replaced)==6 and not local_errors
supp=load('native-supplement.js.result.json');assert supp['complete']and all(v['status']=='PASS'for v in supp['rows']) and not supp['diagnostics']
assert len([v for v in supp['rows']if v['id']=='published menu Escape returns trigger focus'])==6
red=load('native-red.js.result.json');green=load('native-green-recheck.js.result.json')
assert len(red['rows'])==2 and all(v['status']=='FAIL'for v in red['rows']);assert len(green['rows'])==2 and all(v['status']=='PASS'for v in green['rows'])
assert 'Ran 6 tests' in(h/'tests-red-ready.txt').read_text() and 'failures=41' in(h/'tests-red-ready.txt').read_text()
assert 'Ran 19 tests' in(h/'tests-green.txt').read_text() and '\nOK\n' in(h/'tests-green.txt').read_text()
server=load('server-current.json');current=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10));assert current['pid']==server['pid']and current['startup_matches_disk']and current['source']==load('runtime-source-green.json')['source'];(h/'runtime-source-final.json').write_text(json.dumps(current,indent=2))
assert len(current['source'])==955 and len(current['sole_locale_paths'])==1
assert all(str(Path(current['sole_locale_paths'][0])/lang/'LC_MESSAGES/django.mo') in current['actual_opened_MO']for lang in('ru','az','en'))
assert not any(str(r/'locale')+'/' in p for p in current['actual_opened_MO'])
counters=load('domain-mutation-counters.json');assert len(counters['counters'])==2 and all({k:row[k]for k in('insert','update','delete')}==counters['expected_own_seed_per_table']for row in counters['counters'])
pres=load('preservation.json');allowed={'src/catalog/domain_admin/place.py','src/catalog/domain_admin/specialist.py','docs/qa/continuation-and-repair-prompts-2026-10-11.md'}
assert set(pres['changed_entry_files'])<=allowed and not pres['missing_entry_files'];entry=load('entry.json');assert all(pres[k]==entry[k]for k in('head','branch','active_run'))
manifest=[]
for p in sorted((h/'screenshots').glob('*.png')):
 with Image.open(p)as im:size=list(im.size);im.verify()
 manifest.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':size,'phase':'GREEN'if p.name.startswith('sort-current-recheck-')else'native postpatch'})
(h/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
check=subprocess.run(['git','diff','--check'],cwd=r,capture_output=True,text=True);(h/'diff-check.txt').write_text(check.stdout+check.stderr);assert check.returncode==0
result={'status':'SCOPED LOCAL PASS: SORT only','whole_MOD_QA_03':'OPEN','head':pres['head'],'branch':pres['branch'],'active_run':pres['active_run'],'backend_methods':19,'fresh_red_methods':6,'fresh_red_assertion_failures':41,'native_red_source_fail':2,'native_exact_green':2,'matrix_accepted_pass':len(matrix),'matrix_raw_fixture_smoke_fail_replaced':len(replaced),'supplement_pass':len(supp['rows']),'native_accepted_total':len(matrix)+len(supp['rows'])+2,'sort_model_locale_viewport_base_cells':36,'reachable_sidebar_cells':60,'sort_order_comparisons':360,'translated_label_comparisons':360,'mobile_overlay_boundaries':len(boundaries),'local_diagnostics':0,'png_count':len(manifest),'source_files':955,'preservation':pres,'checkpoint_recovery':load('checkpoint-recovery.json'),'domain_write_counters':counters,'limitations':['RU/AZ long-running CLI controller exits143 retained. Completed per-cell checkpoints recovered separately; lost original epilogue assertions are not invented. Fresh runtime source gate, native supplement domain hash and exact PostgreSQL own-seed write counters provide separate verification.','Fresh own RED PNG unavailable: exact GREEN harness reused two own screenshot paths; semantic RED and unit RED retained.','Six raw smoke failures: initial sorting fixtures had no Event menu on selected first row; corrected published-row six smoke cases PASS without repeating sorting corpus.','Native search-form submission drops status before sorting: separate OPEN cause/approval pending. Combined q+status sort uses explicit initial URL; native search-only exact trigger2PASS.','Event/Specialist unmatched column controls OPEN/NOT RUN.','Existing mixed dashboard translations visible in PNG are outside sort-label checks; no whole-UI localization PASS.','Full module08/global/production/commit/push/deploy NOT RUN.']}
(h/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in('preservation','limitations')},ensure_ascii=False))
