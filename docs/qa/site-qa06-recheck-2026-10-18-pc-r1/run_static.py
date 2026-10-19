import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'.tmp/site06-pc-plan-r1'
commands=[['docker','exec','m10s06-plan-r1-app','python',str(O/'check_static.py')],['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(O/'candidate/locale'),'--output',str(Q/'candidate-locales'),'--compiler','native'],['git','-C',str(R),'apply','--check',str(O/'proposed.diff')]]
if (Q/'candidate-locales/manifest.json').exists():commands[1]=['python3',str(R/'scripts/build_isolated_locales.py'),'verify','--manifest',str(Q/'candidate-locales/manifest.json'),'--source-locale',str(O/'candidate/locale')]
results=[]
for command in commands:
 r=subprocess.run(command,capture_output=True,text=True);results.append({'command':command,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(O/'evidence/static-commands.json').write_text(json.dumps(results,indent=2));assert r.returncode==0,results[-1]
(O/'evidence/static-result.json').write_bytes((Q/'static-result.json').read_bytes());(O/'evidence/candidate-locale-manifest.json').write_bytes((Q/'candidate-locales/manifest.json').read_bytes());(O/'evidence/runtime-locale-manifest.json').write_bytes((Q/'locales/manifest.json').read_bytes())
print(json.dumps({'static_commands':3,'all_exit0':True,'candidate_green':'NOT RUN; application unchanged'}))
