import subprocess,sys,json,time
from pathlib import Path
h=Path(__file__).resolve().parent
for token in sys.argv[1:]:
 phase,case,lang=token.split(':');start=time.monotonic();p=subprocess.run(['python3',str(h/'run_browser.py'),phase,case,lang]);print(json.dumps({'phase':phase,'case':int(case),'language':lang,'exit':p.returncode,'seconds':round(time.monotonic()-start,3)}),flush=True)
 if p.returncode:raise SystemExit(p.returncode)
