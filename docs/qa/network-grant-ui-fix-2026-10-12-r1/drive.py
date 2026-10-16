import json,re,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
secret=json.loads((SCRATCH/'credentials.json').read_text());server=json.loads((HERE/'server.json').read_text())
name=sys.argv[1];s=(HERE/name).read_text()
if '__ACL_FIXTURES__' in s:s=s.replace('__ACL_FIXTURES__',(HERE/'acl-fixture-ids.json').read_text())
s=s.replace('__BRANCH_ID__',str(json.loads((HERE/'entities.json').read_text()).get('branch_ids',[3])[0]))
s=s.replace('__COMMON__',(HERE/'common.js').read_text()) if '__COMMON__' in s else s
s=s.replace('__PLACE_ID__',str(json.loads((HERE/'entities.json').read_text())['id']))
s=s.replace('__FIXTURES__',(HERE/'fixtures.json').read_text()).replace('__BASE__',server['url']).replace('__HERE__',str(HERE)).replace('__SCRATCH__',str(SCRATCH))
if '__CARD_URLS__' in s:s=s.replace('__CARD_URLS__',(HERE/'card-urls.json').read_text())
if '__CASES__' in s:s=s.replace('__CASES__',(HERE/'case-fixtures.json').read_text())
if '__ENTITIES__' in s:s=s.replace('__ENTITIES__',(HERE/'entities.json').read_text())
for key in ('owner_password','admin_password'):s=s.replace('__'+key.upper()+'__',secret[key])
if 'consoleEvents=[]' in s:s=re.sub(r'errors,network(?=[},])','errors,network,consoleEvents',s)
start=time.monotonic();p=subprocess.run(['playwright-cli','-s='+ (sys.argv[2] if len(sys.argv)>2 else 'networkuifix-20261012-r1'),'run-code',s],capture_output=True,text=True)
m=re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)',p.stdout,re.S)
result=m.group(1) if m else re.sub(r'```js.*?```','[executed code omitted]',p.stdout,flags=re.S)+p.stderr
for v in secret.values():result=result.replace(v,'[REDACTED]')
file=HERE/(Path(name).stem+'.result.json')
if file.exists():file=file.with_name(file.stem+'.attempt'+str(int(time.time()))+'.json')
try:
 parsed=json.loads(result)
 if 'html' in parsed:
  (SCRATCH/'captured-html.html').write_text(parsed.pop('html'))
  result=json.dumps(parsed)
except ValueError: pass
file.write_text(result)
try:
 data=json.loads(result)
 if data.get('entities'):(HERE/'entities.json').write_text(json.dumps(data['entities']))
 print(json.dumps({'script':name,'rows':len(data.get('rows',[])),'failures':[x for x in data.get('rows',[]) if x.get('status')=='FAIL'],'error':data.get('error'),'keys':list(data)},ensure_ascii=False)[:2500])
except ValueError:print(result[:1800])
with (HERE/'commands.jsonl').open('a') as f:f.write(json.dumps({'command':f'.venv/bin/python {HERE.relative_to(ROOT)}/drive.py {name}','cli_exit':p.returncode,'seconds':round(time.monotonic()-start,2),'result':file.name})+'\n')
sys.exit(p.returncode)
