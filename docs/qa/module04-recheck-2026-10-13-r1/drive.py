import base64,json,re,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name
sec=json.loads((S/'credentials.json').read_text());server=json.loads((P/'server.json').read_text());name=sys.argv[1]
s=(P/name).read_text().replace('__BASE__',server['url']).replace('__HERE__',str(P)).replace('__LOCAL_PASSWORD__',sec['owner_password']).replace('__ASSETS__',str(S/'assets')).replace('__FIXTURE__',(P/'fixtures.json').read_text()).replace('__COMMON__',(P/'common.js').read_text() if (P/'common.js').exists() else '')
for token,file in [('__FIXTURES__','fixture-ids.json'),('__ENTITIES__','entities.json')]:
 if token in s:s=s.replace(token,(P/file).read_text())
s=s.replace('__BASE__',server['url']).replace('__LOCAL_PASSWORD__',sec['owner_password']).replace('__ASSETS__',str(S/'assets')).replace('__FIXTURE__',(P/'fixtures.json').read_text()).replace('__FULLFIXTURE__',(P.parent/'module04-full-2026-10-13-r1/fixtures.json').read_text())
q=subprocess.run(['playwright-cli','-s=module04event-20261013-r1','run-code',s],capture_output=True,text=True)
m=re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)',q.stdout,re.S);out=m.group(1) if m else re.sub(r'```js.*?```','[executed code omitted]',q.stdout,flags=re.S)+q.stderr
for v in sec.values():out=out.replace(v,'[REDACTED]')
f=P/(Path(name).stem+'.result.json')
if f.exists():f=f.with_name(f.stem+'.attempt'+str(int(time.time()))+'.json')
try:
 d=json.loads(out)
 for shot in d.get("shots",[]):
  (P.parent/"module04-full-2026-10-13-r1/screenshots"/shot["file"]).write_bytes(base64.b64decode(shot.pop("png")))
 out=json.dumps(d,ensure_ascii=False);f.write_text(out)
 if d.get('entities'):
  previous=json.loads((P/'entities.json').read_text()) if (P/'entities.json').exists() else {}
  previous.update(d['entities']);(P/'entities.json').write_text(json.dumps(previous))
 print(json.dumps({'rows':len(d.get('rows',[])),'FAIL':[r for r in d.get('rows',[]) if r.get('status')=='FAIL'],'error':d.get('error'),'phase':d.get('phase'),'result':f.name},ensure_ascii=False)[:1500])
except ValueError:
 f.write_text(out);print(out[:400])
with (P/'commands.jsonl').open('a') as f:f.write(json.dumps({'command':'.venv/bin/python '+str(P.relative_to(P.parents[2])/'drive.py')+' '+name,'cli_exit':q.returncode,'result':f.name})+'\n')
