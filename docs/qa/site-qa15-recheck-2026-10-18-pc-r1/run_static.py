import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-plan-r1'
(Q/'check_candidate.py').write_bytes((O/'check_candidate.py').read_bytes())
commands=[['docker','exec','m10s15-plan-r1-app','python',str(Q/'check_candidate.py')],
 ['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(O/'candidate/locale'),'--output',str(Q/'candidate-locales'),'--compiler','native'],
 ['git','-C',str(R),'apply','--check',str(O/'proposed.diff')]]
if (Q/'candidate-locales/manifest.json').exists():commands[1]=['python3',str(R/'scripts/build_isolated_locales.py'),'verify','--manifest',str(Q/'candidate-locales/manifest.json'),'--source-locale',str(O/'candidate/locale')]
results=[]
for n,cmd in enumerate(commands):
 r=subprocess.run(cmd,capture_output=True,text=True);result={'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr};results.append(result);assert r.returncode==0,result
(O/'evidence/candidate-static.json').write_text(json.dumps(results,indent=2));print(json.dumps({'static_commands':len(results),'all_exit0':True,'candidate_green':'NOT RUN'}))
