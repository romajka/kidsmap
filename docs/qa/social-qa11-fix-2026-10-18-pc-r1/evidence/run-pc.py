import subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
for role in ['guest','author','moderator']:
 name='pc-'+role;t=(Q/'matrix-template.js').read_text().replace('__ROLE__',role).replace('[360,390,768,1024,1280,1440]','[1440]').replace('if(width===390)','if(width===1440)').replace("'/png/matrix-'","'/png/pc-'")
 (Q/(name+'.js')).write_text(t)
 r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),name+'.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1200:]
 p=subprocess.run([sys.executable,str(Q/'parse.py'),name],capture_output=True,text=True);print(p.stdout,flush=True);assert p.returncode==0,p.stderr
