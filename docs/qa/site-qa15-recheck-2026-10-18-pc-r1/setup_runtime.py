import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-plan-r1'
(Q/'qa_urls.py').write_bytes((O/'qa_urls.py').read_bytes())
commands=[['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales'),'--compiler','native'],['docker','exec','m10s15-plan-r1-app','python',str(Q/'runtime.py'),'migrate']]
if (Q/'locales/manifest.json').exists():commands[0]=['python3',str(R/'scripts/build_isolated_locales.py'),'verify','--manifest',str(Q/'locales/manifest.json'),'--source-locale',str(R/'locale')]
results=[]
for n,cmd in enumerate(commands):
 r=subprocess.run(cmd,capture_output=True,text=True);(Q/('setup-'+str(n)+'.log')).write_text(r.stdout+r.stderr);results.append({'command':cmd,'exit':r.returncode});assert r.returncode==0,(n,(r.stdout+r.stderr)[-800:])
(O/'evidence/setup-commands.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
