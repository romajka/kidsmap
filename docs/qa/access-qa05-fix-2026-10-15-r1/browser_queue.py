import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];py=str(R/'.venv/bin/python');done=[]
for lang in ['ru','az','en']:
 p=subprocess.run([py,str(H/'browser_run.py'),lang+'.js'],cwd=R)
 result=H/(lang+'.js.result.json');d=json.loads(result.read_text())if result.exists()else{}
 receipt={'lang':lang,'native_exit':p.returncode,'error':d.get('error','MISSING'),'completed':len(d.get('completedCells',[])),'fail':sum(r.get('status')=='FAIL'for r in d.get('rows',[]))};done.append(receipt);(H/'queue-status.json').write_text(json.dumps(done,indent=2));print(json.dumps(receipt),flush=True)
 if p.returncode or receipt['error']or receipt['fail']or receipt['completed']!=6:sys.exit(1)
