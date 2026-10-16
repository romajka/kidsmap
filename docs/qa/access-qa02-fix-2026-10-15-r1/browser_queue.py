"""One native browser session, strictly sequential batches. Stop on any semantic error."""
import json,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;results=[]
for name in sys.argv[1:]:
 t=time.monotonic();(H/'browser-queue-current.json').write_text(json.dumps({'running':name,'finished':results},indent=2))
 p=subprocess.run([str(R/'.venv/bin/python'),str(H/'browser_run.py'),name],cwd=R)
 status=H/(name+'.status.json');d=json.loads(status.read_text())if status.exists()else{'error':'Missing driver receipt','exit':p.returncode}
 results.append({'script':name,'native_exit':d.get('native_driver_exit'),'rows':d.get('rows'),'fail':d.get('fail'),'error':d.get('error'),'seconds':round(time.monotonic()-t,3)})
 (H/'browser-queue-current.json').write_text(json.dumps({'running':None,'finished':results},indent=2))
 if p.returncode or d.get('native_driver_exit') != 0 or d.get('error')or d.get('fail'):raise SystemExit(1)
