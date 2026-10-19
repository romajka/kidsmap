import subprocess,json,re
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
cmd=['python3','-m','unittest','discover','-s',str(R/'scripts/tests'),'-p','test_*.py','-v'];p=subprocess.run(cmd,cwd=R,capture_output=True,text=True);raw=p.stdout+p.stderr;(Q/'python-final.log').write_text(raw);d={'command':cmd,'exit':p.returncode,'summary':[l for l in raw.splitlines() if l.startswith(('Ran ','OK','FAILED','FAIL:','ERROR:'))],'skipped':[l for l in raw.splitlines() if ' ... skipped ' in l]};(O/'evidence/python-final.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
