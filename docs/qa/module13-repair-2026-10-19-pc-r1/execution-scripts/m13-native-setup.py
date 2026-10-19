from pathlib import Path
import subprocess,json
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
t=(Q/'qa_urls.py').read_text().replace('qa/m12/','qa/m13/');(Q/'qa_urls.py').write_text(t)
for name in ['seed-extra.py']:
 t=(R/'.tmp/m12-full-r1'/name).read_text()
 for a,b in [('m12-full-r1','m13-full-r1'),('m12full_r1','m13full_r1'),('m12_','m13_'),('M12','M13')]:t=t.replace(a,b)
 (Q/name).write_text(t)
for name in ['seed.py','seed-extra.py']:
 p=subprocess.run(['docker','exec','m13full-r1-app','python',str(Q/name)],capture_output=True,text=True);(Q/(name+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,name
p=subprocess.run(['docker','exec','-d','m13full-r1-app','python',str(Q/'runtime.py'),'serve'],capture_output=True,text=True);assert p.returncode==0
print('New Module13 fixtures seeded and own server started; own proxy is next.')
