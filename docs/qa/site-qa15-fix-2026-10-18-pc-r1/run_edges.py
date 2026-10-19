import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent
for name in ['browser-recovery.js','browser-file-media.js','browser-editors.js','browser-permissions.js']:
 r=subprocess.run(['python3',str(O/'browser_driver.py'),name],capture_output=True,text=True)
 print(r.stdout+r.stderr,flush=True)
 assert r.returncode==0,name
 data=json.loads((O/'evidence'/(name.removesuffix('.js')+'.json')).read_text())
 if data.get('error') or any(False in row.get('checks',{}).values() for row in data.get('rows',[])):print('EDGE FAILURE retained: '+name,flush=True)
