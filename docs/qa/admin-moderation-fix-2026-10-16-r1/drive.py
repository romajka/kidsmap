import json,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;name=sys.argv[1]
t=time.monotonic();argv=['/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh','-s=adminmoderationfix','run-code',(H/(name+'.js')).read_text()]
p=subprocess.run(argv,capture_output=True,text=True,cwd=R);raw=p.stdout+p.stderr
for secret in json.loads((S/'secrets.json').read_text()).values():raw=raw.replace(secret,'[REDACTED]')
(S/(name+'.raw.txt')).write_text(raw)
(H/(name+'-command.json')).write_text(json.dumps({'script':name+'.js','session':'adminmoderationfix','exit':p.returncode,'seconds':round(time.monotonic()-t,3)},indent=2))
if '### Result' not in raw:print(raw[-1200:]);raise SystemExit(1)
data=json.loads(raw.split('### Result',1)[1].split('###',1)[0].strip())
if isinstance(data,str):data=json.loads(data)
(H/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({'script':name,'complete':data.get('complete'),'rows':len(data.get('rows',[])),'fail':sum(x.get('status')=='FAIL'for x in data.get('rows',[])),'error':data.get('error')},ensure_ascii=False))
raise SystemExit(0 if data.get('complete')else 1)
