import json,re,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name
sec=json.loads((S/'credentials.json').read_text());server=json.loads((P/'server.json').read_text())
name=sys.argv[1]
code=(P/name).read_text().replace('__BASE__',server['url']).replace('__PASSWORD__',sec['owner_password']).replace('__FIXTURES__',(P/'fixtures.json').read_text()).replace('__HERE__',str(P))
q=subprocess.run(['playwright-cli','-s=offerqa08recheck-20261014-r1','run-code',code],capture_output=True,text=True)
m=re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)',q.stdout,re.S)
out=m.group(1) if m else re.sub(r'```js.*?```','[executed code omitted]',q.stdout,flags=re.S)+q.stderr
for value in sec.values():out=out.replace(value,'[REDACTED]')
f=P/(Path(name).stem+'.result.json')
if f.exists():f=f.with_name(f.stem+'.attempt'+str(int(time.time()))+'.json')
f.write_text(out)
try:
 d=json.loads(out);print(json.dumps({'result':f.name,'rows':len(d.get('rows',[])),'failures':[x for x in d.get('rows',[]) if x.get('status')=='FAIL'],'error':d.get('error'),'phase':d.get('phase'),'snapshot':d.get('snapshot')},ensure_ascii=False)[:5000])
except Exception:print(out[:1000])
with (P/'commands.jsonl').open('a') as fp:fp.write(json.dumps({'argv':['.venv/bin/python',str(P/'drive.py'),name],'native_cli_exit':q.returncode,'result':f.name})+'\n')
