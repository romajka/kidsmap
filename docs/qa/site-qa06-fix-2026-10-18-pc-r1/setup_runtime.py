import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1'
commands=[['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-red'),'--compiler','native'],['docker','exec','m10s06-fix-r1-app','python',str(Q/'runtime.py'),'migrate'],['docker','exec','m10s06-fix-r1-app','python',str(Q/'seed.py')]]
results=[]
for n,cmd in enumerate(commands):
 r=subprocess.run(cmd,capture_output=True,text=True);(Q/('setup-'+str(n)+'.log')).write_text(r.stdout+r.stderr);results.append({'command':cmd,'exit':r.returncode});(O/'evidence/setup-commands.json').write_text(json.dumps(results,indent=2));assert r.returncode==0,(n,(r.stdout+r.stderr)[-900:])
print(json.dumps(results,indent=2))
