import json,hashlib,subprocess,urllib.request,difflib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
rows={}
for name in ['matrix','lifecycle','keyboard','shared-final']:
 d=json.loads((P/(name+'.result.json')).read_text());assert not d.get('error'),d
 for i,row in enumerate(d['rows']):
  key=f"geometry:{row['kind']}:{row['lang']}:{row['width']}" if name=='matrix' else row['id'];rows[key]=row
 assert not d.get('errors'),d.get('errors')
failures=[{'id':k,**v} for k,v in rows.items() if v['status']!='PASS'];assert not failures,failures
assert len(rows)==88
assert not json.loads((P/'shared-final.result.json').read_text())['network']
assert json.loads((P/'readback.command.json').read_text())['exit']==0
source=json.loads((P/'incoming-source.json').read_text());changed=[f for f,h in source.items() if not (R/f).exists() or hashlib.sha256((R/f).read_bytes()).hexdigest()!=h]
assert changed==['static/admin/css/kidsmap_admin_components.css'],changed
snap=json.loads((P/'snapshot.json').read_text());assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==snap['HEAD'];assert subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip()==snap['branch']
server=json.loads((P/'server.json').read_text());assert str(P/'runtime.py').encode() in (Path('/proc')/str(server['pid'])/'cmdline').read_bytes()
receipt=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=10));assert receipt['testing'] and receipt['entry_matches_startup'] and receipt['startup_matches_disk'];(P/'runtime-final.json').write_text(json.dumps(receipt,indent=2))
(P/'application.diff').write_text(''.join(difflib.unified_diff((P/'incoming.css').read_text().splitlines(True),(R/'static/admin/css/kidsmap_admin_components.css').read_text().splitlines(True),fromfile='incoming-WORKTREE/static/admin/css/kidsmap_admin_components.css',tofile='approved-WORKTREE/static/admin/css/kidsmap_admin_components.css')))
png=[]
for f in sorted((P/'screenshots').glob('*.png')):
 diagnostic=f.name in ['list-390.png','list-1440.png','place-390.png','place-1440.png']
 png.append({'file':'screenshots/'+f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'role':'initial shared fixture diagnostic' if diagnostic else 'accepted'})
(P/'png-manifest.json').write_text(json.dumps(png,indent=2));assert sum(x['role']=='accepted' for x in png)==76
q=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert q.returncode==0,q.stdout
v={'status':'CLOSED LOCAL','id':'OFFER-QA-05','unique_native_assertions':len(rows),'failures':failures,'matrix_cells':54,'long_status_cells':12,'source_changes':changed,'incoming_source_files_preserved':len(source)-1,'accepted_png':76,'diagnostic_png':4,'runtime_source_match':True,'locale_manifest_verified_before_setup':True,'read_only_candidate_live_invariants':'PASS','git_diff_check_exit':q.returncode,'full_ACCEPT05':'NOT RUN','backend_tests':'NOT RUN','global':'NOT RUN','production':'NOT RUN'}
(P/'verification.json').write_text(json.dumps(v,indent=2));print(json.dumps(v))
