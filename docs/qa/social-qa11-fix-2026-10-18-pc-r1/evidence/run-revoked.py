import subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
(Q/'revoked-retry.js').write_text((Q/'revoked-retry-template.js').read_text().replace('__FIXTURES__',(Q/'subset-fixtures.json').read_text()))
r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),'revoked-retry.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1500:]
p=subprocess.run([sys.executable,str(Q/'parse.py'),'revoked-retry'],capture_output=True,text=True);print(p.stdout,flush=True);assert p.returncode==0,p.stderr
