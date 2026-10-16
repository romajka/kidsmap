import json,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2]
import sys
name=sys.argv[1] if len(sys.argv)>1 else 'browser'
argv=['/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh','-s=adminapprovalaudit','run-code',(H/(name+'.js')).read_text()]
t=time.monotonic();p=subprocess.run(argv,capture_output=True,text=True,cwd=R)
raw=p.stdout+p.stderr
secret=json.loads((R/'.tmp'/H.name/'secrets.json').read_text())
for v in secret.values():raw=raw.replace(v,'[REDACTED]')
(R/'.tmp'/H.name/(name+'.raw.txt')).write_text(raw)
(H/(name+'-command.json')).write_text(json.dumps({'tool':argv[0],'session':argv[1],'script':name+'.js','exit':p.returncode,'seconds':time.monotonic()-t},indent=2))
if '### Result' in raw:
 text=raw.split('### Result',1)[1].split('###',1)[0].strip();data=json.loads(text)
 if isinstance(data,str):data=json.loads(data)
 (H/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
 print(json.dumps({'saved':name+'.json','keys':list(data)},ensure_ascii=False))
else:print(raw[-1500:])
