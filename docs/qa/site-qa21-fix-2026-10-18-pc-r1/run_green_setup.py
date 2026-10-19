import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site21-pc-fix-r1';results=[]
commands=[['python3',str(O/'start_server.py'),'green'],['python3',str(O/'prepare_browser_phase.py'),'green'],['python3',str(O/'run_native_phase.py'),'green']]
for i,cmd in enumerate(commands):
 r=subprocess.run(cmd,capture_output=True,text=True);(Q/('green-setup-'+str(i)+'.log')).write_text(r.stdout+r.stderr);results.append({'command':cmd,'exit':r.returncode});(O/'evidence/green-setup-commands.json').write_text(json.dumps(results,indent=2));print(r.stdout,flush=True);assert r.returncode==0,r.stderr[-700:]
