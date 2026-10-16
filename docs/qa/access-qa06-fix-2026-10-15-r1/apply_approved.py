"""Apply exactly approved field diff only after fresh expected test/browser RED."""
import hashlib,json,os,signal,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;O=R/'docs/qa/module07-full-2026-10-15-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
red=json.loads((H/'regression-RED.status.json').read_text());output=(H/'regression-RED.output.txt').read_text();native=json.loads((H/'native-RED.js.result.json').read_text());fails=[r for r in native['rows']if r['status']=='FAIL']
assert red['exit']==1 and 'Ran 4 tests'in output and 'FAILED (failures=24)'in output and '\nERROR:'not in output
assert len(fails)==1 and fails[0]['detail']=={'http':302,'active':False,'state':'SCHEDULED'}and not any(r['status']=='NOT RUN'for r in native['rows'])
assert sha(R/'src/catalog/forms.py')==sha(H/'forms-before.py')and(R/'src/catalog/testcases/test_access_qa06_deletion_phrase.py').read_bytes()==(O/'proposed-test_access_qa06_deletion_phrase.py').read_bytes()
meta=json.loads((H/'server.json').read_text());proc=Path('/proc')/str(meta['pid']);args=[a.decode()for a in(proc/'cmdline').read_bytes().split(b'\0')if a]
assert args==meta['argv']and(proc/'cwd').resolve()==R
(H/'server-before-patch.json').write_text(json.dumps(meta,indent=2));os.kill(meta['pid'],signal.SIGTERM)
for _ in range(100):
 try:
  if(proc/'stat').read_text().split()[2]=='Z':break
 except FileNotFoundError:break
 time.sleep(.05)
else:raise RuntimeError('Own prepatch HTTP did not stop')
patch=O/'proposed-ACCESS-QA-06.diff'
subprocess.run(['git','apply','--check','--include=src/catalog/forms.py',str(patch)],cwd=R,check=True)
subprocess.run(['git','apply','--include=src/catalog/forms.py',str(patch)],cwd=R,check=True)
new=(R/'src/catalog/forms.py').read_text();before=(H/'forms-before.py').read_text();needle='        max_length=80,\n        strip=False,\n'
assert new.count(needle)==1 and new.replace(needle,'        max_length=80,\n',1)==before
(H/'inverse-proof.json').write_text(json.dumps({'only_one_added_keyword_line':True,'inverse_equals_entry_forms_sha256':sha(H/'forms-before.py'),'current_forms_sha256':sha(R/'src/catalog/forms.py'),'test_exact_proposal':True,'approved_diff_sha256':sha(patch),'existing_assertions_changed':False},indent=2))
paths=json.loads((H/'source-paths.json').read_text());(H/'runtime-source-baseline.json').write_text(json.dumps({p:sha(R/p)for p in paths},indent=2))
argv=[str(S/'venv/bin/python'),str(H/'runtime.py'),'serve']
with(S/'server-GREEN.log').open('wb')as log:p=subprocess.Popen(argv,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta={**meta,'pid':p.pid,'argv':argv};(H/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(200):
 try:
  source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=1))
  if source['pid']==p.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise RuntimeError('Own GREEN HTTP not ready')
assert source['startup_matches_disk']and source['typed_confirmation_strip']is False
(H/'source-GREEN.json').write_text(json.dumps(source,ensure_ascii=False,indent=2));print(json.dumps({'approved_id':'ACCESS-QA-06','single_field_patch_applied':True,'only_own_HTTP_restarted':True,'current_pid':p.pid,'strip':source['typed_confirmation_strip']}))
