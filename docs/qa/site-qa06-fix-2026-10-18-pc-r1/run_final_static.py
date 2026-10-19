import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'.tmp/site06-pc-fix-r1'
commands=[['docker','exec','m10s06-fix-r1-app','python',str(O/'check_final_static.py')],['docker','exec','m10s06-fix-r1-app','python',str(O/'check_validator_edges.py')],['python3',str(R/'scripts/build_isolated_locales.py'),'verify','--manifest',str(Q/'locales-green/manifest.json'),'--source-locale',str(R/'locale')]]
results=[]
for i,command in enumerate(commands):
 r=subprocess.run(command,capture_output=True,text=True);(Q/('static-'+str(i)+'.log')).write_text(r.stdout+r.stderr);results.append({'command':command,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(O/'evidence/final-static-commands.json').write_text(json.dumps(results,indent=2));assert r.returncode==0,results[-1]
for source,dest in [('final-static-result.json','final-static-runtime.json'),('validator-edges.json','final-validator-edges.json')]: (O/'evidence'/dest).write_bytes((Q/source).read_bytes())
(O/'evidence/runtime-locale-manifest.json').write_bytes((Q/'locales-green/manifest.json').read_bytes())
print(json.dumps({'static_commands':3,'all_exit0':True}))
