import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;results=[]
for name in ['browser-json-flows.js','browser-long-json.js','browser-mobile-errors.js']:
 cmd=['python3',str(O/'browser_driver.py'),name];r=subprocess.run(cmd,capture_output=True,text=True);results.append({'command':cmd,'exit':r.returncode});(O/'evidence/extended-native-commands.json').write_text(json.dumps(results,indent=2));print(r.stdout,flush=True);assert r.returncode==0,r.stderr[-700:]
