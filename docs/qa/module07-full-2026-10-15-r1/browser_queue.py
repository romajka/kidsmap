import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];done=[]
for script in json.loads((H/'browser-queue.json').read_text()):
 p=subprocess.run([str(R/'.venv/bin/python'),str(H/'browser_run.py'),script],cwd=R)
 f=H/(script+'.result.json');d=json.loads(f.read_text())if f.exists()else{};rows=d.get('rows',[])
 receipt={'script':script,'exit':p.returncode,'rows':len(rows),'counts':{s:sum(r.get('status')==s for r in rows)for s in ['PASS','FAIL','NOT RUN']},'error':d.get('error')};done.append(receipt);(H/'queue-status.json').write_text(json.dumps(done,indent=2));print(json.dumps(receipt),flush=True)
 if p.returncode or not rows or d.get('error'):sys.exit(1)
 # Independent audit scripts continue on semantic FAIL/NOT RUN; findings remain explicit.
