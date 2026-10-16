import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];done=[]
for name in sys.argv[1:]:
 (H/'green-queue.json').write_text(json.dumps({'running':name,'done':done},indent=2));p=subprocess.run([str(R/'.venv/bin/python'),str(H/'browser_run.py'),name],cwd=R);d=json.loads((H/(name+'.status.json')).read_text());done.append(d);(H/'green-queue.json').write_text(json.dumps({'running':None,'done':done},indent=2));assert p.returncode==0 and d['native_driver_exit']==0 and not d.get('error') and d.get('fail')==0,d
