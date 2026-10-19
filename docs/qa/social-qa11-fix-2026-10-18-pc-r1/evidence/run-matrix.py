import subprocess,json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
for role in ['guest','author','moderator']:
 name='matrix-'+role;(Q/(name+'.js')).write_text((Q/'matrix-template.js').read_text().replace('__ROLE__',role))
 r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),name+'.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1200:]
 p=subprocess.run([sys.executable,str(Q/'parse.py'),name],capture_output=True,text=True);print(p.stdout,flush=True);assert p.returncode==0,p.stderr
