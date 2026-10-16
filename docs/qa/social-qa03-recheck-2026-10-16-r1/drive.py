import json,re,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
code=(HERE/sys.argv[1]).read_text()
argv=['/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh','-s=social03recheckr1','run-code',code]
t=time.monotonic();p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
raw=(p.stdout+p.stderr)
for value in json.loads((ROOT/'.tmp'/HERE.name/'credentials.json').read_text()).values():
 if isinstance(value,str):raw=raw.replace(value,'[REDACTED]')
raw=re.sub(r'[0-9a-f]{8}-[0-9a-f-]{27,}','[OWN-ID]',raw,flags=re.I)
raw=re.sub(r'([?&]token=)[^\s\"<>]+',r'\1[OWN-TOKEN]',raw)
raw=re.sub(r'(https?://[^\s"<>]+/reset/)[^\s"<>]+',r'\1[REDACTED]',raw)
(ROOT/'.tmp'/HERE.name/(sys.argv[1]+'.raw.txt')).write_text(raw)
with (HERE/'commands.jsonl').open('a') as f:f.write(json.dumps({'name':sys.argv[1],'argv':[argv[0],argv[1],'run-code','<'+str(HERE/sys.argv[1])+'>'],'exit':p.returncode,'seconds':round(time.monotonic()-t,3)})+'\n')
if '### Result' in raw:
 text=raw.split('### Result',1)[1].split('###',1)[0].strip()
 try:
  data=json.loads(text)
  if isinstance(data,str):data=json.loads(data)
  (HERE/(sys.argv[1]+'.result.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
  print(json.dumps({'rows':len(data.get('rows',[])),'fail':sum(r.get('status')=='FAIL' for r in data.get('rows',[])),'exit':p.returncode,'error':data.get('error')},ensure_ascii=False))
 except ValueError:print('Result parsing failed; inspect sanitized output')
else:print('No semantic result; raw restricted to ignored scratch')
sys.exit(p.returncode)
