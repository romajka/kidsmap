from pathlib import Path
import json,csv,hashlib,collections
from PIL import Image
P=Path(__file__).resolve().parent;rows=[];excluded=[]
selected=['flows','matrix','decisions','edits','favorites-notifications','favorites-finish','site-finish','acl','proof','supplement','final-proof','readback-final','event-final','pagination-matrix','event-positive','cards-sort']
for name in selected:
 f=P/(name+'.result.txt')
 if not f.exists():continue
 try:x=json.loads(f.read_text(encoding='utf-8'))
 except ValueError:continue
 for r in x.get('rows',[]):
  reason=None
  if name=='flows' and r['id'].startswith('harness-'):reason='Own duplicate main selector; decisions completed real native moderation separately.'
  if name=='decisions' and r['id'] in ['owner-reply-available-specialist','employee-reply-scope-activity']:reason='Incorrect own fixture entitlement expectation: unverified business owner is not specialist person; default EDITOR lacks reviews.reply. Positive explicit grant/person cases independently passed.'
  if name=='decisions' and r['id']=='site-decision-harness':reason='Own guessed unsupported SiteReview custom URL; actual standard admin change-form path completed in site-finish.'
  if name=='favorites-notifications' and r['id'].startswith('favorites-'):reason='Own wrong catalog URL /places/. Valid native /catalog/ flow completed in favorites-finish.'
  if name=='acl' and r['id']=='negative-react-4-8' and r['role']=='author':reason='Own expected400 wrong: self-reaction permission returns403 first. Fresh readback-final confirms403.'
  if name=='acl' and r['id']=='positive-acl-harness-place':reason='Own mouse stability/timing; native keyboard report persisted, readback-final confirms exact private response.'
  if name=='supplement' and r['id']=='employee-report-keyboard-saved':reason='Premature read after Enter before async POST committed; retained final state and fresh readback-final prove saved/private report.'
  if name=='proof' and r['id']=='place-index-pagination':reason='Initial matcher insufficient; real page2 redirect cause reproduced in pagination-matrix18cells, SOCIAL-QA-09.'
  if name=='final-proof' and r['id']=='pagination-retry-harness':reason='Wait timeout diagnosed as real301 to page1, independently reproduced18cells in pagination-matrix. Not counted as an unavailable scenario.'
  if reason:excluded.append({'run':name,**r,'exclusion':reason});continue
  if name=='matrix' and r['id']=='admin-place-overflow' and r['status']=='FAIL':r['classification']='SHARED pre-existing MOD-QA-03; fresh3cells; no duplicate SOCIAL cause'
  rows.append({'run':name,**r})
for f in P.glob('*.result.attempt*.txt'):
 excluded.append({'artifact':f.name,'exclusion':'Retained superseded own harness attempt; current selected results are named above.'})
gaps=[
 ('smtp-actual','Real SMTP/Google/SDK/CDN integrations NOT RUN; LocMem only, external transport blocked; network delay/abort explicitly SIMULATED.'),
 ('crash-tests-environment','10/77 selected Django methods stop in setUp: missing guard, required Unix PostgreSQL socket and TASK33_QA_ROOT. Bodies NOT RUN on Windows/TCP stand; no permissive guard shim/assertion change.'),
 ('full-suite','Only unchanged targeted77 methods; full application suite NOT RUN.'),
 ('mutation-full-matrix','Core native lifecycle/ACL mostly RU1440, positive event reply RU390. Every operation×all roles×18cells NOT RUN; per-row matrix is authoritative.'),
 ('public-card-all-widths','Fresh actual4 public cards RU/AZ/EN at390/1440; remaining4 widths for these embedded card sections NOT RUN. Review pages/full editor matrix covers all18cells.'),
 ('screen-reader-devices','Real screen reader, Safari/Firefox, physical touch devices NOT RUN; programmatic semantics and native keyboard tested.'),
 ('notification-badge-menu','Dedicated notification popup/unread badge not implemented in inspected controller/template/header; existing account menu and inbox tested. Feature requirement absent, no defect inferred.'),
 ('typed-hide-author-site-edit','Typed legacy admin hide/approve routes deliberately forbidden by VersionedReviewAdminMixin; standalone author SiteReview edit not exposed. No unsupported feature defect; site approve/hide/reject and typed edit/reject/approve tested.'),
 ('invite-expiry-high-volume','Real clock expiry,100+ inbox pagination, every invite entity kind/organization-join action NOT RUN. Existing tests cover dedupe/recipient/staleness; native place invite/revoke/2tabs done.'),
 ('large-typed-pagination','Typed target renders all27 current approved reviews and has no paginator; supported site/place global feed pagination tested. Requirement for target pagination not established.'),
 ('production-release','Production/build image/source-PC DB/PIDs/volumes/external sessions NOT RUN/UNKNOWN. New local source/runtime only.'),
 ('favorite-dynamic-hide','Initial hidden/inactive/archived/deleted saved-like visibility proven; changing a favorited public card through each hide/delete lifecycle NOT RUN.'),
 ('role-specific-mouse-report','Employee report Enter/save/private readback PASS; reliable mouse submission after auto-scroll not established, no product finding inferred from own selector timeout.'),
]
gaprows=[{'run':'scope','id':k,'status':'NOT RUN','role':'scope','lang':'all','width':'all','reason':v} for k,v in gaps]
(P/'coverage-gaps.json').write_text(json.dumps(gaprows,indent=2,ensure_ascii=False),encoding='utf-8')
(P/'excluded-observations.json').write_text(json.dumps(excluded,indent=2,ensure_ascii=False),encoding='utf-8')
(P/'matrix.json').write_text(json.dumps(rows+gaprows,indent=2,ensure_ascii=False),encoding='utf-8')
with(P/'matrix.csv').open('w',newline='',encoding='utf-8-sig')as out:
 w=csv.DictWriter(out,fieldnames=['run','id','status','role','lang','width','url','http','screenshot','reason','classification'],extrasaction='ignore');w.writeheader();w.writerows(rows+gaprows)
shots=[]
for f in sorted((P/'screenshots').glob('*.png')):
 with Image.open(f)as im:dims=list(im.size)
 shots.append({'path':f.relative_to(P).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'dimensions':dims,'classification':'NATIVE rendered Chromium; retained diagnostic attempts included'})
(P/'screenshots-manifest.json').write_text(json.dumps(shots,indent=2),encoding='utf-8')
summary={'observations':dict(collections.Counter(r['status']for r in rows)),'observation_count':len(rows),'by_run':{n:dict(collections.Counter(r['status']for r in rows if r['run']==n))for n in selected},'native_png':len(shots),'explicit_scope_gaps':len(gaps),'excluded_rows':len(excluded)}
(P/'results-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
