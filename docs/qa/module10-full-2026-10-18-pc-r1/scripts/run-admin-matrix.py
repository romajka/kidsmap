import subprocess,json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
for lang in ['az','ru','en']:
 name='admin-matrix-'+lang;(Q/(name+'.js')).write_text((Q/'admin-matrix-template.js').read_text().replace('__LANG__',lang));r=subprocess.run([sys.executable,str(Q/'run-one.py'),name],capture_output=True,text=True);print(r.stdout,flush=True);assert r.returncode==0,r.stderr
