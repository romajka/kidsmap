"""Merge only fresh selected observations; keep raw QA mistakes separately."""
from pathlib import Path
import json,csv,hashlib
from collections import Counter,defaultdict
from PIL import Image
P=Path(__file__).resolve().parent
selected=['acl','acl-boundaries','matrix','modal-proof','auth-flow','auth-resume','auth-negative','team-flow','team-resume','privacy-flow','deletion-flow','cancel-recovery','supplement-matrix','access-transitions','deletion-relations','person-deletion','org-conflict-proof','final-browser-proof','api-contracts']
rows=[];removed=[];runs={}
for name in selected:
 data=json.loads((P/(name+'.result.txt')).read_text(encoding='utf-8'))
 runs[name]=dict(Counter(x['status'] for x in data['rows']))
 for x in data['rows']:
  reason=None
  if x.get('role')=='QA':reason='Own harness interruption; recovered with focused fresh scripts.'
  if name=='acl' and x['role'] in ['admin','volunteer']:reason='Superseded by acl-boundaries; business roles and volunteer middleware corrected against source.'
  if name=='matrix' and x['id'] in ['settings-images','settings-long-filled-images','reset-modal-Escape']:reason='Hidden empty-src avatar image or unsettled modal geometry; superseded by supplement-matrix/modal-proof.'
  if name=='supplement-matrix' and x['id']=='organization-409-preserves-input':reason='350ms observation before asynchronous list refresh completed; superseded by org-conflict-proof.'
  if reason:removed.append({'run':name,'id':x['id'],'status':x['status'],'role':x['role'],'lang':x['lang'],'width':x['width'],'reason':reason});continue
  rows.append({'run':name,**x})
rows.extend({'run':'finalize-owned',**x} for x in json.loads((P/'finalize-owned.result.json').read_text())['rows'])
for lang in ['az','en']:
 for width in [390,1440]:
  for state in ['deletion-code-error','deletion-phrase-error']:
   rows.append({'run':'locale-rendered-review','id':state+'-language','status':'FAIL','role':'own-deletion-fixture','lang':lang,'width':width,'finding':'ACCESS-QA-05','screenshot':f'{state}-{lang}-{width}.png','classification':'Actual rendered error plus locale-runtime.json; SIMULATED test retention policy'})
findings={'reset-modal-focus-trap':'ACCESS-QA-01','reset-modal-focus-return':'ACCESS-QA-01','recipient-inbox-no-reject-control':'ACCESS-QA-02','organization-management-controls-missing':'ACCESS-QA-03','place-team-items-contained':'ACCESS-QA-04'}
for x in rows:
 if x['status']=='FAIL':x.setdefault('finding',findings.get(x['id']))
gaps=[]
for lang in ['ru','az','en']:
 for width in [360,768,1024,1280]:
  for scenario in ['complete-registration-verification-reset-profile-path','complete-account-deletion-confirm-cancel-path']:
   gaps.append({'id':scenario,'status':'NOT RUN','role':'registered-user','lang':lang,'width':width,'reason':'Complete native transition path ran at 390/1440; base rendered states covered all six widths.'})
 for width in [360,390,768,1024,1280,1440]:
  for scenario in ['organization-member-role-remove-native-control','organization-invitation-cancel-native-control','recipient-decline-native-control']:
   gaps.append({'id':scenario,'status':'NOT RUN','role':'network' if scenario.startswith('organization') else 'recipient','lang':lang,'width':width,'reason':'Required rendered control is missing. Findings ACCESS-QA-02/03; implemented HTTP transitions partly covered.'})
gaps.extend({'id':id,'status':'NOT RUN','role':role,'lang':'N/A','width':'N/A','reason':reason} for id,role,reason in [
 ('real-google-oauth','anonymous','No approved external test credentials; external network blocked. Local disabled branch and unchanged adapter tests covered.'),
 ('real-email-delivery','all','Mail captured only inside own ignored scratch/test backend; no external SMTP.'),
 ('production','all','No production access authorized or performed.'),
 ('natural-30-day-deletion-and-backup-expiry','own-deletion-fixture','Canonical processor exercised with explicit future now; natural waiting, scheduled deployment and backup deletion not performed.'),
 ('browser-safari-firefox-and-real-touch-device','all','Actual Chromium headless browser only; viewport is not physical device evidence.'),
 ('screen-reader','all','Keyboard and rendered focus covered; real assistive technology not run.'),
 ('specialist-transfer-reconciliation-body','admin','282-test run has one Windows disposable-path preflight FAIL before scenario body; no guard/assertion bypass.'),
 ('native-ownership-transfer-ui','owner','Implemented CSRF JSON transfer tested; user-facing native transfer screen absent.'),
 ('default-inactive-retention-policy-native-ui','user','Initial default active boolean false; tested stand deliberately uses existing synthetic TEST_POLICY for deletion paths.'),
 ('natural-password-reset-token-expiry','anonymous','Replay/malformed/registration-expired challenge covered; no wall-clock wait for reset-link TTL.'),
 ('organization-invitation-reject-cancel-HTTP','recipient/network','Place reject/cancel HTTP/native covered; organization accept/role/remove/conflict covered; org reject/cancel endpoints not executed.'),
 ('every-role-every-native-transition-every-width','all','No claim of full cross product: detailed matrix identifies executed roles/widths; remaining combinations not run.')])
(P/'coverage-gaps.json').write_text(json.dumps(gaps,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'matrix.json').write_text(json.dumps({'observations':rows,'not_run':gaps},ensure_ascii=False,indent=2),encoding='utf-8')
with (P/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
 fields=['run','id','status','finding','role','lang','width','http','url','screenshot','classification','reason'];w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(rows);w.writerows(gaps)
(P/'excluded-observations.json').write_text(json.dumps(removed,ensure_ascii=False,indent=2),encoding='utf-8')
shots=[]
for f in sorted((P/'screenshots').glob('*.png')):
 with Image.open(f) as im:size=list(im.size)
 shots.append({'file':'screenshots/'+f.name,'pixels':size,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'type':'NATIVE browser PNG; includes retained own diagnostic attempts'})
derived=[{'file':f.relative_to(P).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'type':'DERIVED contact sheet/crop, originals unchanged'} for f in sorted((P/'visual-review').glob('*')) if f.is_file()]
(P/'screenshots-manifest.json').write_text(json.dumps({'native':shots,'derived':derived},indent=2),encoding='utf-8')
bywidth=defaultdict(Counter)
for x in rows:bywidth[str(x['lang'])+'/'+str(x['width'])][x['status']]+=1
summary={'decision':'FAIL; audit complete with explicit NOT RUN limits','selected_runs':selected,'raw_run_counts':runs,'observations':dict(Counter(x['status'] for x in rows)),'not_run_scope_rows':len(gaps),'excluded_own_qa_observations':len(removed),'fail_rows_by_finding':dict(Counter(x.get('finding') for x in rows if x['status']=='FAIL')),'unclassified_fail_rows':[x for x in rows if x['status']=='FAIL' and not x.get('finding')],'by_language_width':{k:dict(v) for k,v in bywidth.items()},'native_png':len(shots),'derived_images':len(derived),'tests':{'methods':282,'pass':281,'native_preflight_fail':1,'error':0,'application_failures_confirmed':0,'exit_code':1,'scenario_body_NOT_RUN':1},'findings':{'P0':0,'P1':0,'P2':5,'P3':0}}
(P/'results-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['raw_run_counts','selected_runs','by_language_width']},ensure_ascii=False))
