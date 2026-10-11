import subprocess, sys, json, re, os, time, datetime, shutil
os.environ['PYTHONIOENCODING']='utf-8'
os.environ['PYTHONUTF8']='1'
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
here=Path(__file__).resolve().parent
credential=(here.parents[2]/'.tmp/module01-recheck-20261011-r1/credential').read_text()
source=(here/sys.argv[1]).read_text(encoding='utf-8')
if '__QA01R_COMMON__' in source:source=source.replace('__QA01R_COMMON__',(here/'common.js').read_text(encoding='utf-8'))
if '__LAWFUL_JSON__' in source:source=source.replace('__LAWFUL_JSON__',(here/'lawful-fixtures.json').read_text(encoding='utf-8'))
source=source.replace('__FIXTURES_JSON__',(here/'fixtures.json').read_text(encoding='utf-8'))
source=source.replace('__EXTRA_JSON__',(here/'extra-fixtures.json').read_text(encoding='utf-8')) if '__EXTRA_JSON__' in source else source
source=source.replace('__CARD_URLS__',(here/'card-urls.json').read_text(encoding='utf-8')) if '__CARD_URLS__' in source else source
if '__MAP_ADAPTER_JSON__' in source:source=source.replace('__MAP_ADAPTER_JSON__',json.dumps((here/'map-adapter.js').read_text(encoding='utf-8')))
(here/(Path(sys.argv[1]).stem+'.effective.js')).write_text(source,encoding='utf-8')
source=source.replace('__LOCAL_PASSWORD__',credential)

cli=Path.home()/'AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js'
started=time.monotonic()
session=sys.argv[2] if len(sys.argv)>2 else 'place-recheck-r1'
assert session in ['place-recheck-r1']
result=subprocess.run(['C:/Program Files/nodejs/node.exe',str(cli),'-s='+session,'run-code',source],capture_output=True,text=True,encoding='utf-8',errors='replace')
out=result.stdout
# Keep results only; never persist echoed executed code or credentials.
match=re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)',out,re.S)
clean=match.group(1) if match else re.sub(r'```js.*?```','[executed code omitted]',out,flags=re.S)
clean=clean.replace(credential,'[redacted]')
mailfile=here.parents[2]/'.tmp/module01-recheck-20261011-r1/mail.json'
if mailfile.exists():
 for m in json.loads(mailfile.read_text(encoding='utf-8')):
  for value in re.findall(r'\b\d{6}\b|https?://[^\s<>]+/auth/reset/[^\s<>]+',m['body']):clean=clean.replace(value,'[LOCAL-MAIL-SECRET-REDACTED]')
clean=re.sub(r'(/auth/reset/)[^/\s"<>]+/[^/\s"<>]+/',r'\1[UID]/[TOKEN]/',clean)
clean=re.sub(r'([?&]token=)[^&\s"<>]+',r'\1[REDACTED]',clean)
target=here/(Path(sys.argv[1]).stem+'.result.txt')
if target.exists():
    index=1
    while target.with_name(target.stem+f'.attempt{index}.txt').exists():index+=1
    shutil.copyfile(target,target.with_name(target.stem+f'.attempt{index}.txt'))
target.write_text(clean,encoding='utf-8')
with (here/'command-ledger.jsonl').open('a',encoding='utf-8') as out:
    out.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':f'.venv/Scripts/python.exe docs/qa/module01-recheck-2026-10-11-r1/drive.py {sys.argv[1]}'+(' '+session if len(sys.argv)>2 else ''),'cli_exit_code':result.returncode,'duration_seconds':round(time.monotonic()-started,2),'result':target.name,'browser_session':session})+'\n')
try:
 data=json.loads(clean);print(json.dumps({'rows':len(data.get('rows',[])),'counts':{status:sum(x.get('status')==status for x in data.get('rows',[])) for status in ['PASS','FAIL','NOT RUN']},'keys':list(data),'failures':[x for x in data.get('rows',[]) if x.get('status')=='FAIL'][:6]},ensure_ascii=False)[:5500])
except (ValueError,AttributeError):print(clean[:3500])
print('CLI exit',result.returncode)
sys.exit(result.returncode)
if result.stderr:print(result.stderr[:500])
