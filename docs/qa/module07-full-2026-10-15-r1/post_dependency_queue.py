from pathlib import Path
import subprocess,json,sys
H=Path(__file__).resolve().parent;R=H.parents[2];done=[]
for script in ['post-finalization-privacy-after-deps.js','post-media-positive-after-deps.js']:
 p=subprocess.run([str(R/'.venv/bin/python'),str(H/'browser_run.py'),script],cwd=R);f=H/(script+'.result.json');d=json.loads(f.read_text())if f.exists()else{};rows=d.get('rows',[]);record={'script':script,'exit':p.returncode,'rows':len(rows),'nonpass':sum(r.get('status')!='PASS'for r in rows)};done.append(record);(H/'post-dependency-queue-status.json').write_text(json.dumps(done,indent=2));print(json.dumps(record),flush=True)
 if p.returncode or not rows or record['nonpass']:sys.exit(1)
