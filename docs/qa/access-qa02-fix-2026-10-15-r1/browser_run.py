import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;script=sys.argv[1]
with(S/(script+'.driver.log')).open('w')as out:p=subprocess.run([str(R/'.venv/bin/python'),str(H/'drive.py'),script],stdout=out,stderr=subprocess.STDOUT,timeout=600)
receipt={'script':script,'native_driver_exit':p.returncode}
result=H/(script+'.result.json')
if result.exists():
 d=json.loads(result.read_text());receipt.update(rows=len(d.get('rows',[])),fail=sum(r.get('status')=='FAIL'for r in d.get('rows',[])),error=d.get('error'),completedCells=d.get('completedCells'))
(H/(script+'.status.json')).write_text(json.dumps(receipt,indent=2))

sys.exit(p.returncode)
