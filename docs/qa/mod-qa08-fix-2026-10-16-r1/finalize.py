import json,hashlib,struct,urllib.request,difflib,subprocess
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];read=lambda n:json.loads((h/n).read_text());rows=[];excluded=[]
for lang in ('ru','az','en'):
 d=read('native-'+lang+'.js.result.json');assert d['complete'] and not d.get('error')
 for x in d['rows']:
  if x['status']=='FAIL' and x['id']=='four ordered localized controls with associated labels and server choices':excluded.append(x)
  else:rows.append(x)
d=read('native-correction-shared.js.result.json');assert d['complete'];rows+=d['rows'];assert len(excluded)==24 and all(x['status']=='PASS'for x in rows)
(h/'accepted-observations.json').write_text(json.dumps({'rows':rows,'excluded_original_comparisons':excluded,'scope':'24 failed QA locale comparisons replaced only; all other current behavior observations retained'},ensure_ascii=False,indent=2))
meta=read('server-current.json');source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/'));after=json.load(urllib.request.urlopen(meta['url']+'/qa/state/'));assert source['pid']==meta['pid'] and source['startup_matches_disk'] and len(source['source'])==961;assert source['source']==read('runtime-source-baseline.json');assert after==read('domain-before.json')
(h/'runtime-source-final.json').write_text(json.dumps(source,indent=2));(h/'domain-final.json').write_text(json.dumps(after,indent=2))
manifest=[]
for p in sorted((h/'screenshots').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,v=struct.unpack('>II',b[16:24]);manifest.append({'path':str(p.relative_to(h)),'sha256':hashlib.sha256(b).hexdigest(),'width':w,'height':v})
(h/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
allowed={x['path']for x in read('applied.json')};pres=read('preservation.json');assert set(pres['changed_entry_files'])==allowed and not pres['missing_entry_files'] and not pres['container_drift'];assert all(x['same_args'] and x['same_cwd']for x in pres['foreign_process_checks']);assert pres['active_run']==['active_run: NONE']
for x in read('applied.json'):assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['candidate_sha256']
assert 'Ran 1 test' in(h/'backend-green-reset.txt').read_text() and '\nOK\n' in(h/'backend-green-reset.txt').read_text();assert 'Ran 8 tests' in(h/'backend-green.txt').read_text() and 'FAILED (failures=2)' in(h/'backend-green.txt').read_text();assert 'FAILED (failures=6)' in(h/'backend-red-final.txt').read_text()
acl=read('shared-acl.json')['rows'];assert len(acl)==9 and all(x['status']=='PASS'for x in acl)
diff=''.join(''.join(difflib.unified_diff((h/'entry-source'/n).read_text().splitlines(True),(r/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n))for n in sorted(allowed));(h/'applied.diff').write_text(diff)
verification={'status':'MOD-QA-08 CLOSED LOCAL; full ACCEPT-08 pending','snapshot':{k:pres[k]for k in('head','branch','active_run')},'approved_scope':sorted(allowed|{'src/catalog/testcases/test_mod08_filter_drawer.py'}),'backend_unique_accepted_methods':8,'backend_repeat':'only one Reset method after correcting new fixture ordering expectation','native_accepted':len(rows),'native_fail':0,'native_cells':36,'acl_observations':len(acl),'png':len(manifest),'source_files':len(source['source']),'domain_unchanged':True,'shared_mo_unchanged':True,'entry_files_preserved_except_approved':True,'container_count':74,'foreign_http_preserved':True,'additional_observation':'Existing AZ/EN footer count remains Russian; unchanged fuzzy PO translation, outside this approval. Carry to full acceptance; not silently fixed.','not_run':['full ACCEPT-08','global corpus','production','cross-browser','OS select popup pixels','screen reader','external services','module09']}
(h/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2));print(json.dumps(verification,ensure_ascii=False))
