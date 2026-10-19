import json,subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
(Q/'subset.js').write_text((Q/'subset-template.js').read_text().replace('__FIXTURES__',(Q/'subset-fixtures.json').read_text()))
r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),'subset.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1500:]
p=subprocess.run([sys.executable,str(Q/'parse.py'),'subset'],capture_output=True,text=True);print(p.stdout);assert p.returncode==0,p.stderr
