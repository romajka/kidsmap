import json,re,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name
sec=json.loads((S/'credentials.json').read_text());server=json.loads((P/'server.json').read_text())
s=(P/sys.argv[1]).read_text().replace('__BASE__',server['url']).replace('__HERE__',str(P)).replace('__PASSWORD__',sec['admin_password']).replace('__FIXTURES__',(P/'fixtures.json').read_text())
q=subprocess.run(['playwright-cli','-s=org-qa03-fix-2026-10-13-r1','run-code',s],capture_output=True,text=True)
m=re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)',q.stdout,re.S)
out=m.group(1) if m else re.sub(r'```js.*?```','[executed code omitted]',q.stdout,flags=re.S)+q.stderr
for v in sec.values():out=out.replace(v,'[REDACTED]')
result_file=P/(Path(sys.argv[1]).stem+'.result.json')
if result_file.exists():result_file=result_file.with_name(result_file.stem+'.attempt'+str(int(time.time()))+'.json')
result_file.write_text(out)
print(out[:2500])
with (P/'commands.jsonl').open('a') as f:f.write(json.dumps({'command':'.venv/bin/python '+str(P.relative_to(P.parents[2])/'drive.py')+' '+sys.argv[1],'cli_exit':q.returncode})+'\n')
