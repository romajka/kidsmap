import csv,hashlib,json,struct,urllib.request
from collections import Counter
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];read=lambda name:json.loads((h/name).read_text());rows=[];excluded=[]
def include(name, predicate=lambda x:True, note=''):
 d=read(name)
 for index,x in enumerate(d.get('rows',[])):
  item={**x,'run':name,'row_index':index}
  if predicate(x):
   if name=='transport.js.result.json':item['model']='place';item['transport']='SIMULATED' if x['id']!='simulated transports preserve domain'else'actual read-only fingerprint'
   rows.append(item)
  else:excluded.append({**item,'exclusion':note})
for lang in ('ru','az','en'):
 include('matrix-'+lang+'.js.result.json',lambda x:x['id'] not in ['hub first page lists 25 candidates with keyboard next','column restored and Escape closes menu'],'360 hub first-page control repeated in corrected resume; boolean open check invalid')
 include('matrix-final-resume-'+lang+'.js.result.json',lambda x:x['id']!='column restored and Escape closes menu','incorrect falsy boolean open check, replaced with supported native close')
 for prefix in ['matrix-resume-','matrix-continue-']:
  excluded += [{**x,'run':prefix+lang+'.js.result.json','exclusion':'resume viewport incorrectly remained1280 at tagged360; raw retained, corrected targeted resume replaces'}for x in read(prefix+lang+'.js.result.json').get('rows',[])]
include('columns-native-close.js.result.json')
excluded += [{**x,'run':'columns-close-check.js.result.json','exclusion':'unsupported Escape expectation for native details; W3C APG Enter/Space contract; retained actual observation, no app finding'}for x in read('columns-close-check.js.result.json')['rows']]
for name in ['native-errors.js.result.json','acl.js.result.json','flows-native.js.result.json','role-delete.js.result.json','transport.js.result.json','audit-history.js.result.json','event-current-save.js.result.json','native-publication.js.result.json','az-publication-repro.js.result.json','native-publication-missing.js.result.json','created-label-recheck.js.result.json']:include(name)
include('flows2-native-corrected.js.result.json',lambda x:x['status']!='NOT RUN','obsolete visible bulk-reject selector; actual form rejection replaces')
include('positive-editors.js.result.json',lambda x:x['status']!='NOT RUN','Event current Save is _continue, actual path repeated separately; Specialist4PASS retained')
assert all(x['status']in('PASS','FAIL')for x in rows)
counts=dict(Counter(x['status']for x in rows));failids=Counter(x['id']for x in rows if x['status']=='FAIL');assert set(failids)=={'drawer count translated into selected language','loading toast uses selected language','success toast uses selected language','processed moderation displays saved refusal and no decision form','created metadata uses selected language'},failids
(h/'matrix.json').write_text(json.dumps({'rows':rows,'counts':counts},ensure_ascii=False,indent=2));(h/'excluded-observations.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2))
with(h/'matrix.csv').open('w',newline='')as f:
 writer=csv.DictWriter(f,fieldnames=['run','row_index','id','status','role','lang','width','model','transport','detail'],extrasaction='ignore');writer.writeheader();writer.writerows({**x,'detail':json.dumps(x.get('detail',{}),ensure_ascii=False)}for x in rows)
meta=read('server.json');source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/'));state=json.load(urllib.request.urlopen(meta['url']+'/qa/state/'));assert source['pid']==meta['pid'] and source['startup_matches_disk'];assert source['source']==read('runtime-source-baseline.json');assert len(source['source'])==961
(h/'runtime-source-final.json').write_text(json.dumps(source,indent=2));(h/'state-final.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
manifest=[]
for p in sorted((h/'screenshots').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,v=struct.unpack('>II',b[16:24]);manifest.append({'path':str(p.relative_to(h)),'width':w,'height':v,'sha256':hashlib.sha256(b).hexdigest()})
(h/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
log=(h/'full-backend.txt').read_text();assert 'Ran 261 tests' in log and '\nOK\n' in log
pres=read('preservation.json');assert not pres['missing_entry_files'] and not pres['container_drift'];assert set(pres['changed_entry_files'])<= {'docs/qa/continuation-and-repair-prompts-2026-10-11.md'};assert all(x['same_args'] and x['same_cwd']for x in pres['foreign_process_checks']);assert pres['active_run']==['active_run: NONE'];assert pres['head']=='e4e05cc213b34e2d771ecb854901bfd016d1db51'
verification={'verdict':'LOCAL FAIL','legacy_ids':{'MOD-QA-'+str(i).zfill(2):'CLOSED LOCAL, fresh bounded recheck'for i in range(1,9)},'new_open':{'MOD-QA-09':'P3 count/created fuzzy PO','MOD-QA-10':'P3 publication toast literals','MOD-QA-11':'P2 saved reason absent in terminal detail'},'snapshot':{k:pres[k]for k in('head','branch','active_run')},'application_changes_during_accept':0,'backend':{'tests':261,'failures':0,'errors':0,'skips':0,'seconds':183.790,'full_corpus_runs':1},'native':{'counts':counts,'total_observations':len(rows),'failure_controls':dict(failids),'excluded_or_replaced':len(excluded),'core_locale_width_cells':18,'core_queues':4,'invalid_specialist_save_cells':18,'simulated_transport_cells':18,'actual_ajax_complete_pairs':6,'png':len(manifest)},'source_files':len(source['source']),'current_source_matches':True,'locale_build_verify':True,'sole_locale_paths':source['sole_locale_paths'],'preservation':{'entry_files':pres['entry_files'],'entry_changes':pres['changed_entry_files'],'missing':0,'foreign_http':len(pres['foreign_process_checks']),'container_count':pres['current_container_count'],'container_drift':0,'shared_MO_unchanged':True},'renderer_incident':'One owned AZ renderer stalled95percentCPU and was stopped after verified ownership. Cause UNKNOWN; no stack obtained. Fresh AZ390 minimal6controls and remaining AZ1440/EN390/1440 completed; incident not declared application defect or continuity PASS.','not_run':['global corpus and other modules','production/deploy/commit/push','physical devices, cross-browser, screen reader, OS native select popup pixels','full9roles x18viewport mutation cross-product','audit retention/LogEntry exhaustiveness and concurrent batch stress','affiliation full decision lifecycle beyond existing backend guards','home-recommendations configuration locale and full Specialist editor label locale; adjacent transfer only','new09/10/11 fixes pending approval']}
(h/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2));print(json.dumps({'counts':counts,'total':len(rows),'excluded':len(excluded),'png':len(manifest),'fail_ids':dict(failids),'source':len(source['source'])},ensure_ascii=False))
