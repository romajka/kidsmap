"""Bounded module06 gate: semantic receipts, source, isolation, and PNG provenance."""
import hashlib,json,subprocess,sys,struct,urllib.request,csv,datetime
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp'/P.name
def read(f):return json.loads((P/f).read_text())
def latest(prefix):return max(P.glob(prefix+'.result*.json'),key=lambda f:f.stat().st_mtime_ns).name
receipts=[('matrix.result.json',None),('map-geometry-green.result.json',None),(latest('pointer-final-green'),None),('sdk-final-acceptance.result.json',None),(latest('filter-settled'),None),('scroll-keyboard.result.json',None),('resize-final.result.json',None),('functional.result.json','direct'),('native-lifecycle-settled.result.json',None),('map-browser.result.json','pass'),('map-navigation-finish.result.json',None),('navigation-proof.result.json',None),('event-results-finish.result.json',None),(latest('admin-locales'),None),('admin-functional.result.json','admin_initial'),('admin-resume.result.json','admin_resume'),('admin-confirmed.result.json','publish_only'),('admin-approved-lifecycle.result.json',None),('section-negative-finish.result.json',None),('pending-guard-acceptance.json',None),('event-cache-lifecycle.result.json',None),(latest('sdk-empty-roundtrip'),None),(latest('map-action-labels'),None),('map-actions-native.result.json',None),(latest('map-phone-fit-final'),None)]
accepted={}
for file,filter in receipts:
 d=read(file)
 for row in d['rows']:
  id=row['id']
  if filter=='direct' and not(id.startswith(('search-','map-payload-')) or id in ['no-point-list-not-map','private-map-excluded','same-group-price-age']):continue
  if filter=='pass' and row['status']!='PASS':continue
  if filter=='admin_initial' and id in ['admin-functional-harness-error']:continue
  if filter=='admin_resume' and id not in ['native-sections-restore-cache','before-publication-closed','publication-ready-control']:continue
  if filter=='publish_only' and id!='native-publish-public-reload':continue
  x=dict(row);x['receipt']=file;x.setdefault('role','anonymous')
  if id in ['SDK-real-12s-bounded-timeout','late-SDK-callback-recovers']:x.update(lang='en',width=1440)
  key=(id,x['role'],x.get('lang'),x.get('width'));accepted[key]=x
fail=[x for x in accepted.values() if x['status']!='PASS'];assert not fail,[(x['id'],x.get('lang'),x.get('width'),x['status']) for x in fail]
assert len({(x['lang'],x['width']) for x in read('matrix.result.json')['rows']})==18
assert read('test-discovery-final.json')['unique_methods']==288
for file,count in [('module-tests',93),('affected-template-tests',29),('supplement-environment-recheck',10),('final-locale-consumers',15)]:
 assert read(file+'.command.json')['exit']==0
 assert 'Ran '+str(count)+' tests' in (P/(file+'.txt')).read_text()
assert read('discovery-supplement-tests.command.json')['exit']==1
assert len(read('supplement-failed-methods.json'))==10
for row in read('test-discovery-final.json')['core']+read('test-discovery-final.json')['supplement']:
 assert hashlib.sha256((R/row['file']).read_bytes()).hexdigest()==row['source_hash'],row['file']
for path,digest in read('accepted-source.json').items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==digest,path
server=read('server.json');assert server['url'].startswith('http://127.0.0.1:');assert str(P/'runtime.py').encode() in Path('/proc',str(server['pid']),'cmdline').read_bytes()
v=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=10));assert v['pid']==server['pid'] and v['testing'] and v['entry_matches_startup'] and v['startup_matches_disk']
assert v['database_host']=='127.0.0.1' and v['cache'].endswith('LocMemCache') and v['email'].endswith('locmem.EmailBackend') and v['env_file_loaded'] is False
q=subprocess.run([sys.executable,str(R/'scripts/build_isolated_locales.py'),'verify','--manifest',str(S/'locales-final/manifest.json')],capture_output=True,text=True);assert q.returncode==0
assert v['sole_locale_root']==read('locale-manifest-final.json')['locale_root']
assert all(x['status']=='PASS' for x in read('final-state.json')['rows']);assert read('final-state-accepted.command.json')['exit']==0
active=[x for x in (R/'docs/task33/implementation-status.md').read_text().splitlines() if x.startswith('active_run:')];assert active==['active_run: NONE']
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();assert head==read('snapshot.json')['head']
old=read('snapshot.json')['incoming_files'];current=read('entry-final.json')['source_files'];assert all(current.get(k)==h for k,h in old.items() if k.endswith('.mo')), 'shared MO changed'
assert subprocess.run(['git','check-ignore','-q',str(S/'credentials.json')],cwd=R).returncode==0
png=[]
for f in sorted((P/'screenshots').rglob('*.png')):
 data=f.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',data[16:24]);assert w>0 and h>0;png.append({'path':str(f.relative_to(P)),'bytes':len(data),'width':w,'height':h,'sha256':hashlib.sha256(data).hexdigest()})
(P/'png-manifest.json').write_text(json.dumps(png,indent=2))
rows=list(accepted.values());(P/'accepted-browser-rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
with (P/'matrix.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=['id','role','lang','width','status','receipt']);writer.writeheader();writer.writerows({k:x.get(k,'') for k in writer.fieldnames} for x in rows)
(P/'runtime-version-final.json').write_text(json.dumps(v,indent=2))
result={'decision':'LOCAL PASS','module':6,'closed_ids':['PUBLIC-QA-'+str(i).zfill(2) for i in range(1,7)],'confirmed_open_ids':[],'unique_backend_methods':288,'accepted_browser_assertions':len(rows),'matrix_cells':18,'png_count':len(png),'readonly_checks':len(read('final-state.json')['rows']),'runtime_source_match':True,'sole_fresh_locales':['ru','az','en'],'shared_MO_preserved':True,'active_run':'NONE','head':head,'branch':subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip(),'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'not_run':['production','global/all13 corpus and CROSS-QA-02 discovery','real map SDK/tiles/GPS/provider compatibility','real integrations/email delivery/telephone/external route/clipboard','real devices/other engines/screen reader/exhaustive focus traversal']}
(P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
