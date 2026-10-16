import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];assert(H/'auth-recovery-ready.json').exists();done=[]
for script in ['post-org-native.js','deletion-flow.js','cancel-recovery.js']:
 p=subprocess.run([str(R/'.venv/bin/python'),str(H/'browser_run.py'),script],cwd=R);f=H/(script+'.result.json');d=json.loads(f.read_text())if f.exists()else{};rows=d.get('rows',[]);entry={'script':script,'exit':p.returncode,'rows':len(rows),'nonpass':sum(r.get('status')!='PASS'for r in rows),'error':d.get('error')};done.append(entry);(H/'remaining-queue-status.json').write_text(json.dumps(done,indent=2));print(json.dumps(entry),flush=True)
 if p.returncode or not rows or entry['nonpass']or d.get('error'):sys.exit(1)
