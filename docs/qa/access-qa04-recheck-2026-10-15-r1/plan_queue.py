import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];done=[]
for name in sys.argv[1:]:
 (H/'queue.json').write_text(json.dumps({'running':name,'done':done},indent=2))
 p=subprocess.run([str(R/'.venv/bin/python'),str(H/'browser_run.py'),name],cwd=R);d=json.loads((H/(name+'.status.json')).read_text());done.append(d);(H/'queue.json').write_text(json.dumps({'running':None,'done':done},indent=2))
 assert p.returncode==0 and d['native_driver_exit']==0 and not d.get('error'),d
 if name=='setup.js':assert d['fail']==0
 # Matrix geometry FAIL is the required fresh RED, not an execution error.
