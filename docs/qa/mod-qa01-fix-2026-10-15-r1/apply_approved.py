import hashlib,json,os,signal,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;O=R/'docs/qa/mod-qa01-recheck-2026-10-15-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
red=json.loads((H/'regression-RED.status.json').read_text());text=(H/'regression-RED.output.txt').read_text();native=json.loads((H/'native-RED.js.result.json').read_text());fail=[r for r in native['rows']if r['status']=='FAIL']
assert red['exit']==1 and 'Ran 4 tests'in text and 'FAILED (failures=6)'in text and '\nERROR:'not in text
assert len(fail)==2 and not any(r['status']=='NOT RUN'for r in native['rows'])and {r['id']for r in fail}=={'moderation queue offers next-page link','pagination is reachable by keyboard'}
path=R/'src/catalog/templates/admin/volunteer/hub_index.html';assert path.read_bytes()==(H/'hub-before.html').read_bytes();test=R/'src/catalog/testcases/test_mod_qa01_hub_pagination.py';assert test.read_bytes()==(O/'proposed-test_mod_qa01_hub_pagination.py').read_bytes()
(H/'RED-source-baseline.json').write_bytes((H/'runtime-source-baseline.json').read_bytes());(H/'RED-runtime-source.json').write_bytes((H/'runtime-source.json').read_bytes())
meta=json.loads((H/'server.json').read_text());proc=Path('/proc')/str(meta['pid']);argv=[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x];assert argv==meta['argv']and(proc/'cwd').resolve()==R
(H/'server-before-patch.json').write_text(json.dumps(meta,indent=2));os.kill(meta['pid'],signal.SIGTERM)
for _ in range(100):
 try:
  if(proc/'stat').read_text().split()[2]=='Z':break
 except FileNotFoundError:break
 time.sleep(.05)
else:raise RuntimeError('Own prepatch process did not stop')
patch=O/'proposed-MOD-QA-01.diff';include='--include=src/catalog/templates/admin/volunteer/hub_index.html';subprocess.run(['git','apply','--check',include,str(patch)],cwd=R,check=True);subprocess.run(['git','apply',include,str(patch)],cwd=R,check=True)
assert path.read_bytes()==(O/'proposed-hub_index.html').read_bytes()
lines=path.read_text().splitlines(True);start=next(i for i,x in enumerate(lines)if x=='{% if page.has_other_pages %}\n');inverse=''.join(lines[:start]+lines[start+7:]);assert inverse.encode()==(H/'hub-before.html').read_bytes()
(H/'inverse-proof.json').write_text(json.dumps({'added_template_lines':7,'inverse_exact_entry':True,'before_sha256':sha(H/'hub-before.html'),'after_sha256':sha(path),'test_exact_approved_proposal':True,'approved_diff_sha256':sha(patch),'existing_assertions_changed':False},indent=2))
paths=json.loads((H/'source-paths.json').read_text());(H/'runtime-source-baseline.json').write_text(json.dumps({p:sha(R/p)for p in paths},indent=2))
with(S/'server-GREEN.log').open('wb')as log:p=subprocess.Popen(meta['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta['pid']=p.pid;(H/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(150):
 try:
  source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=1))
  if source['pid']==p.pid:break
 except Exception:pass
 time.sleep(.1)
else:raise RuntimeError('Own GREEN HTTP failed')
assert source['startup_matches_disk']and source['loaded_template_sha256']==sha(path);(H/'source-GREEN.json').write_text(json.dumps(source,ensure_ascii=False,indent=2));print(json.dumps({'applied_id':'MOD-QA-01','template_lines':7,'own_current_PID':p.pid,'foreign_restart':False}))
