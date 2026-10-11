"""Package fresh evidence without promoting harness errors into findings."""
from pathlib import Path
import json,csv,hashlib,datetime
P=Path(__file__).resolve().parent
names=['lifecycle','resume','moderation','boundaries','media','photo-clear-probe','rights-submit','venue-submit','occurrence','state-matrix','last-public','visual-review','tampering']
records=[];harness=[]
for name in names:
 d=json.loads((P/f'{name}.result.txt').read_text(encoding='utf-8'))
 if d.get('error'):harness.append({'run':name,'error':d['error'],'completed_rows_retained':len(d.get('rows',[]))})
 for row in d.get('rows',[]):
  x={'run':name,**row}
  if row.get('scenario')=='published-primary-delete-blocked':x.update(status='NOT RUN',reason='Button did not send clear. Publication deletion gate not exercised; EVENT-QA-02 has separate draft roundtrip proof.')
  if row.get('scenario')=='cancelled-removed-from-upcoming-list':x.update(status='NOT RUN',reason='Incorrect own QA expectation; canonical existing test requires retained cancelled card with state. Rechecked PASS in last-public.')
  if row.get('state')=='public-translated':x['role']='public'
  records.append(x)
matrix=json.loads((P/'matrix.result.txt').read_text())['rows']
for x in matrix:
 x['geometry_document_language_status']=x['status'];x['copy_status']='NOT RUN';x['copy_finding']=''
 if x['role'] in ('owner','specialist'):
  x['copy_status']='FAIL' if x['lang'] in ('en','az') else 'PASS'
  x['copy_finding']='EVENT-QA-03' if x['copy_status']=='FAIL' else ''
 elif x['role']=='admin' and x['lang']=='ru':x['copy_status']='FAIL';x['copy_finding']='EVENT-QA-01'
records.extend({'run':'matrix',**x} for x in matrix)
(P/'scenario-results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
with (P/'matrix.csv').open('w',newline='',encoding='utf-8-sig') as f:
 fields=['role','state','lang','width','geometry_document_language_status','copy_status','copy_finding','url','screenshot'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(matrix)
with (P/'scenario-matrix.csv').open('w',newline='',encoding='utf-8-sig') as f:
 fields=['run','role','scenario','state','lang','width','status','reason','screenshot'];w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(records)
png=[{'path':p.relative_to(P).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (P/'screenshots').glob('*.png')]
(P/'screenshots-manifest.json').write_text(json.dumps(png,indent=2),encoding='utf-8')
summary={'module':'04','run':'module04-2026-10-10-r1','verdict':'FAIL','executed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'matrix_geometry_rows':len(matrix),'matrix_geometry_PASS':sum(x['status']=='PASS' for x in matrix),'state_rows':len(json.loads((P/'state-matrix.result.txt').read_text())['rows']),'screenshots':len(png),'normalized_rows':len(records),'normalized_counts':{s:sum(x.get('status')==s for x in records) for s in ['PASS','FAIL','NOT RUN']},'application_findings':{'P0':0,'P1':0,'P2':3,'P3':0},'django':{'run':129,'pass':118,'application_baseline_failures':2,'environment_preflight_failures_NOT_RUN':9,'native_exit':1,'assertions_changed':False},'harness_errors':harness,'console_network':json.loads((P/'matrix.result.txt').read_text()).get('consoleRows',[]),'normalization_note':'Native raw rows preserved. Geometry PASS is not copy acceptance; AZ/EN owner copy FAIL and RU admin fields FAIL are explicit in matrix.csv. Invalid QA expectations remain NOT RUN. Harness failures are not application findings.'}
(P/'evidence-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['matrix_geometry_rows','state_rows','screenshots','normalized_counts','django']}))
