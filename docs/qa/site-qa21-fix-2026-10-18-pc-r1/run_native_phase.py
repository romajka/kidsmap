import json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parent;phase=sys.argv[1];assert phase in ['red','green'];results=[]
for name in ['browser-acceptance-'+phase+'.js','browser-sentinels-'+phase+'.js']:
 cmd=['python3',str(O/'browser_driver.py'),name];r=subprocess.run(cmd,capture_output=True,text=True);results.append({'command':cmd,'exit':r.returncode});(O/'evidence'/('native-'+phase+'-commands.json')).write_text(json.dumps(results,indent=2));print(r.stdout,flush=True);assert r.returncode==0,r.stderr[-700:]
