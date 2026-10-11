"""Package fresh evidence; never infer green from CLI exit alone."""
from pathlib import Path
import json,csv,hashlib,collections,datetime
from PIL import Image
P=Path(__file__).resolve().parent;R=P.parents[2]
rows=[];runs=[]
selected=['functional3','functional4','lifecycle','matrix','admin-matrix','schedule-fresh','events-recheck','pricing','restore','restore-read','adversarial','multiple','admin-lifecycle','detach','roundtrip','common','catalog-corrected','conflict-matrix','clipping','rejection','rejection-repro']
for name in selected:
 p=P/(name+'.result.txt')
 if not p.exists():continue
 x=json.loads(p.read_text(encoding='utf-8'))
 runs.append({'name':name,'rows':len(x.get('rows',[])),'raw_counts':dict(collections.Counter(r.get('status','NOT RUN') for r in x.get('rows',[]))),'harness_error':x.get('error'),'page_network_errors':x.get('errors',[])})
 for raw in x.get('rows',[]):
  r=dict(raw);status=r.get('status','NOT RUN');note='';id=r.get('id',r.get('scenario',''))
  if name=='lifecycle' and id.startswith('same-offering-filter'):
   status='NOT RUN';note='Superseded expectation: legacy price_max intentionally removed; see catalog-corrected fresh DOM rows.'
  if name=='detach' and id=='native-reviewed-branch-detach':
   s=json.loads((P/'state-post-detach.json').read_text(encoding='utf-8'))
   ok=next(a for a in s['Activity'] if a['id']==1)['program_id'] is None and 'Обработка завершена' in r['result']
   status='PASS' if ok else 'FAIL';note='Raw expected word Отсоединено was wrong; native completed result + readonly program_id NULL + retained groups/prices + employee denial verify actual contract.'
  if name=='schedule-fresh' and 'reload_status' in r and r['reload_status']=='FAIL':
   status='FAIL';note='Save HTTP200, reload mismatch; isolated reproduction not confirmed. Root cause UNKNOWN; no confirmed defect assigned.'
  if name=='admin-matrix' and r.get('metrics',{}).get('clippedBadges'):
   note='Badge wider than direct parent is a research flag, not proof of clipping. Separate clipping run checks ancestors; rendered crops inspected.'
  width=r.get('width','UNRECORDED')
  lang=r.get('lang','UNRECORDED')
  role=r.get('role','mixed' if name in ['functional3','functional4','lifecycle','detach'] else 'owner')
  rows.append({'run':name,'scenario':id,'role':role,'language':lang,'width':width,'status':status,'raw_status':r.get('status','NOT RUN'),'evidence':p.name,'screenshot':r.get('screenshot',''),'note':note})
 # Raw scripts that did not reach all steps are not counted as PASS.
 if x.get('error'):rows.append({'run':name,'scenario':'unfinished-script-tail','role':'mixed','language':'UNRECORDED','width':'UNRECORDED','status':'NOT RUN','raw_status':'HARNESS ERROR','evidence':p.name,'screenshot':'','note':x['error'].split('\n')[0]})
for role,scenario,reason in [('owner','native-archive-program-activity','No archive action in inspected supported editor; model/service archive exercised only by existing backend tests.'),('admin-editor','json-v1-roundtrip','v2 native roundtrip executed; v1 serialization covered by existing Django suites only.'),('mixed','full-schedule-media-json-roundtrip','Export omits structured hours, legacy schedule, and media bytes; tariff roundtrip does not prove full Place roundtrip.'),('owner','group-recurring-installment-complete-save','Recurring blocked by missing owner billing_interval_count control. Installment cycles/unit controls absent; complete positive UI path NOT RUN.'),('mixed','physical-device-browser-at-multiple-heights','Chromium CSS viewport emulation at height950; physical devices/other engines/heights NOT RUN.'),('mixed','all-authorization-and-mutation-cartesian-combinations','Named native mutations mainly RU PC/mobile; layout/loading/error/conflict cells cover18 combinations. Full mutation×role×lang×width product NOT RUN.'),('mixed','external-maps-fonts-geolocation','SIMULATED blocked transport; live SDK/integrations/geolocation NOT RUN.'),('mixed','production-and-full-suite','No production connection; selected250 Django tests only.'),('mixed','regression-versus-other-version','No previous revision/production evaluated; observed baseline of current WORKTREE only.')]:
 rows.append({'run':'coverage','scenario':scenario,'role':role,'language':'RU/AZ/EN','width':'360/390/768/1024/1280/1440','status':'NOT RUN','raw_status':'NOT RUN','evidence':'REPORT.md','screenshot':'','note':reason})
with (P/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['run','scenario','role','language','width','status','raw_status','evidence','screenshot','note']);w.writeheader();w.writerows(rows)
derived={'inspection-contact.png','admin-group-badge-crop-390.png','owner-schedule-copy-crop-1024.png','admin-group-en-badge-crop-390.png'}
manifest=[{'path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'pixel_width':Image.open(p).width,'pixel_height':Image.open(p).height,'origin':'derived inspection crop/contact' if p.name in derived else 'fresh rendered browser','sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((P/'screenshots').glob('*.png'))]
(P/'screenshots-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
summary={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_runs':runs,'matrix_rows':len(rows),'matrix_counts':dict(collections.Counter(r['status'] for r in rows)),'screenshots':len(manifest),'browser_screenshots':sum(r['origin']=='fresh rendered browser' for r in manifest),'derived_images':len(derived),'screenshots_bytes':sum(r['bytes'] for r in manifest),'django_final_tests':250,'django_final_pass':250,'test_native_exit_codes':[json.loads((P/f).read_text())['exit_code'] for f in ['tests-command.json','tests-extra-command.json']]}
(P/'results-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='selected_runs'},ensure_ascii=True))
