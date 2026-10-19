import subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
s=(Q/'supplement-ready.js').read_text().replace("const path='/admin/catalog/'+model+'/1/change/';await p.goto", "await p.setViewportSize({width:1440,height:950});const path='/admin/catalog/'+model+'/1/change/';await p.goto")
(Q/'supplement-final.js').write_text(s.replace("'/png/privacy-ru-360-viewport.png'","'/png/privacy-ru-360-viewport-final.png'"))
(Q/'admin-localized-ru-final.js').write_text((Q/'admin-localized-ru.js').read_text().replace("'/png/admin-localized-'","'/png/admin-final-'"))
for name in ['admin-localized-ru-final','supplement-final','last-controls']:
 r=subprocess.run([sys.executable,str(Q/'run-one.py'),name],capture_output=True,text=True)
 print(r.stdout[-2500:],r.stderr[-1200:],flush=True)
 if r.returncode:raise SystemExit(r.returncode)
