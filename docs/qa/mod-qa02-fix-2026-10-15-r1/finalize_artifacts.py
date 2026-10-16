import collections,hashlib,json,struct,subprocess,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
read=lambda p:json.loads(p.read_text());accepted=[];sections={}
for script in('native-main.js','native-edges.js','native-decisions.js','native-authors.js','native-owner-recheck.js','native-security.js'):
 d=read(H/(script+'.result.json'));rows=d['rows']
 if script=='native-authors.js':rows=[r for r in rows if r.get('role')=='volunteer']
 sections[script]=dict(collections.Counter(r['status']for r in rows));accepted.extend({'source_script':script,**r}for r in rows)
 assert all(r['status']=='PASS'for r in rows)
(H/'accepted-observations.json').write_text(json.dumps({'mode':'scoped native observations; not independent test methods','sections':sections,'counts':dict(collections.Counter(r['status']for r in accepted)),'rows':accepted,'exclusion':'original owner login/support and hidden mobile select NOT RUN retained; owner-only recheck supplies full coverage'},ensure_ascii=False,indent=2))
rows=read(H/'native-authors.js.result.json')['rows'];(H/'excluded-harness-observations.json').write_text(json.dumps([r for r in rows if r.get('role')=='owner'],indent=2))
images=[]
for p in sorted((H/'screenshots').glob('*.png')):
 b=p.read_bytes();w,h=struct.unpack('>II',b[16:24]);name=p.name
 phase='MAIN'if name.startswith(('admin-','reviewer-'))else'EDGE'if name.startswith('edge-')else'DECISION'if name.startswith('decision-')else'AUTHOR_INITIAL_SUPPORT'if name.endswith('-initial.png')else'AUTHOR_FLOW'if name.startswith('author-')else'SECURITY_SHARED'
 images.append({'path':str(p.relative_to(H)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'width':w,'height':h,'phase':phase})
(H/'png-manifest.json').write_text(json.dumps(images,indent=2));(H/'visual-review.json').write_text(json.dumps({'manually_viewed':['screenshots/reviewer-az-360-focus.png','screenshots/admin-ru-1440-reload.png','screenshots/edge-corrupt-en-390.png','screenshots/author-owner-actual-hub-review.png'],'observations':['Mobile actual AZ current/proposed stacks with gallery order and native focus','Desktop RU shows all eight thumbnails and captions','Corrupt EN mobile explicitly Photo unavailable with broken link hidden','Actual owner native upload/reorder persisted to reviewer gallery1,2,3,4; ordinary text nature/business remains existing text behavior'],'limit':'Four selected full-page PNGs viewed; tall images downscaled by viewer, not a claim all131 manually reviewed or full WCAG/global sidebar layout acceptance'},indent=2))
issues=[];expected=[]
for script in sections:
 for d in read(H/(script+'.result.json')).get('diagnostics',[]):
  if d['kind']=='requestfailed'and not d.get('local'):expected.append({'script':script,'reason':'blocked external request','record':d});continue
  if d['kind']=='console'and not d.get('local')and d['text']=='Failed to load resource: net::ERR_FAILED':expected.append({'script':script,'reason':'blocked external resource console','record':d});continue
  if script=='native-decisions.js'and d['kind']=='console'and d.get('expected409')and d['text'].startswith('Failed to load resource:'):expected.append({'script':script,'reason':'native whitespace reason validation409','record':d});continue
  if script=='native-security.js'and d['kind']=='console'and((d['role'],d['surface'])in{('bare','hub-detail'),('volunteer','hub-detail')}and '403'in d['text']or(d['role'],d['surface'])==('reviewer','private-document')and '404'in d['text']):expected.append({'script':script,'reason':'expected access-denial status','record':d});continue
  issues.append({'script':script,'record':d})
(H/'diagnostics-classification.json').write_text(json.dumps({'unexplained':issues,'expected_counts':dict(collections.Counter(x['reason']for x in expected)),'expected':expected},indent=2));assert not issues
m=read(H/'server.json');src=json.load(urllib.request.urlopen(m['url']+'/qa/source/'));state=json.load(urllib.request.urlopen(m['url']+'/qa/state/'));(H/'runtime-source-final.json').write_text(json.dumps(src,indent=2));(H/'state-final.json').write_text(json.dumps(state,indent=2))
(H/'author-coverage-boundary.json').write_text(json.dumps({'classification':'QA plan assumption corrected by actual rendered controls; no application defect attributed or extra repair','owner_native':'main + two gallery uploads ready, native reorder, draft/reload/submit, actual reviewer preview; owner cover input does not exist','volunteer_native':'main + cover uploads, draft/reload/submit, actual reviewer preview; gallery input does not exist, existing live gallery retained','NOT_RUN':['owner cover upload control (not present)','volunteer gallery upload control (not present)'],'source':['src/catalog/templates/pages/includes/permanent_place_photos.html','src/catalog/templates/admin/volunteer/place_form.html','src/catalog/volunteer_forms.py: wizard_steps/sections'],'source_scope_extended':False,'backend_assertions_weakened':False,'full_photo_contract':'Both different native entrypoints feed the same hub; main/cover/gallery decoding/order separately covered in36maincells and native owner gallery upload. No claim of unsupported UI actions.'},indent=2))
(H/'browser-command-provenance.json').write_text(json.dumps({'driver':'drive.py','session':'mod02fixr1','semantics':'CLI run-code receives exact JS text, ledger <path> denotes content provenance not literal CLI argument; isolated newContext native interactions, local fixtures API only for fictional credentials/read-only oracle, not auth/save APIs','scripts':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in H.glob('*.js')},'prepatch_native_reference':'../mod-qa02-recheck-2026-10-15-r1/native-recheck.js.result.json; current entry verified template/source identity before patch; fresh permanent RED rerun this run'},indent=2))
print(json.dumps({'accepted':len(accepted),'PNG':len(images),'sections':sections,'unexplained_diagnostics':len(issues),'state':state}))
