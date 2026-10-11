"""CLI browser driver with isolated environment and exact command ledger."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
scratch = ROOT / '.tmp/place-qa01-07-fix-20261010'
scratch.mkdir(parents=True, exist_ok=True)
env = {k:v for k,v in os.environ.items() if k.upper() in {
    'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','PATHEXT','COMSPEC','USERPROFILE','LOCALAPPDATA','APPDATA'}}
env['DJANGO_TESTING'] = '1'
arguments = sys.argv[1:]
redactions=[]
if arguments and arguments[0] == 'code-file':
    arguments = ['run-code', (ROOT / arguments[1]).read_text(encoding='utf-8').replace('\n',' ')]
elif arguments and arguments[0] in ('login','owner-login'):
    credential=json.loads((scratch/'credentials.json').read_text(encoding='utf-8'))['owner']
    login_file='browser-login.js' if arguments[0]=='login' else 'browser-login-session.js'
    code=(HERE/login_file).read_text(encoding='utf-8').replace('\n',' ')
    code=code.replace('__QA_USER__',json.dumps(credential['username'])).replace('__QA_PASSWORD__',json.dumps(credential['password']))
    arguments=['run-code',code];redactions=[credential['password']]
argv = [r'C:\Program Files\nodejs\node.exe',r'C:\Users\Ramin\AppData\Local\npm-cache\_npx\31e32ef8478fbf80\node_modules\@playwright\cli\playwright-cli.js','-s=placekmfix-plan'] + arguments
result = subprocess.run(argv, cwd=scratch, env=env, capture_output=True, encoding='utf-8')
for private in redactions:
    result.stdout=result.stdout.replace(private,'[REDACTED synthetic password]')
    result.stderr=result.stderr.replace(private,'[REDACTED synthetic password]')
    argv=[value.replace(private,'[REDACTED synthetic password]') for value in argv]
if sys.argv[1]=='code-file' and '### Result' in result.stdout:
    payload=result.stdout.split('### Result',1)[1].lstrip()
    try:
        parsed,_=json.JSONDecoder().raw_decode(payload)
        (HERE/(Path(sys.argv[2]).stem+'.result.json')).write_text(json.dumps(parsed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    except json.JSONDecodeError: pass
with (HERE/'browser-command-ledger.jsonl').open('a', encoding='utf-8') as file:
    file.write(json.dumps({'argv':argv,'cwd':str(scratch),'exit_code':result.returncode,
        'stdout':result.stdout,'stderr':result.stderr})+'\n')
print(result.stdout)
print(result.stderr, file=sys.stderr)
raise SystemExit(result.returncode)
