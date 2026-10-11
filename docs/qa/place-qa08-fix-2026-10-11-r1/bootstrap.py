"""Own QA setup and foreign-file hash inventory, without application edits."""
import hashlib
import json
import secrets
import socket
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STATE = ROOT / '.tmp/place-qa08-fix-20261011-r1'
assert not STATE.exists()
for port in (8842, 55447):
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', port))
STATE.mkdir()
(HERE / 'screenshots').mkdir()
for name in ('media', 'private-media', 'assets', 'unit-media', 'unit-private-media'):
    (STATE / name).mkdir()
(STATE / 'credential').write_text(secrets.token_urlsafe(32), encoding='utf-8')
(STATE / 'locale-profile').write_text('baseline-locales', encoding='utf-8')
paths = subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard', '-z'], cwd=ROOT).decode('utf-8').split('\0')
own = HERE.relative_to(ROOT).as_posix() + '/'
foreign = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths)) if p and not p.startswith(own) and (ROOT/p).is_file()}
(HERE / 'foreign-entry.json').write_text(json.dumps(foreign, indent=2), encoding='utf-8')
(STATE / 'ru-po-before.bin').write_bytes((ROOT/'locale/ru/LC_MESSAGES/django.po').read_bytes())
(STATE / 'journal-before.bin').write_bytes((ROOT/'docs/qa/module-acceptance-prompts.md').read_bytes())
source = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','static','config','locale','templates') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
containers = subprocess.check_output(['wsl.exe','--','docker','ps','--format','{{.ID}} {{.Names}} {{.Ports}}'], text=True).splitlines()
listeners = json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',"Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess | ConvertTo-Json -Compress"], text=True))
entry = {'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), 'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(), 'worktree':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines(), 'active_run':next(x.split(':',1)[1].strip() for x in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:')), 'source_files':source, 'containers':containers, 'listeners':listeners, 'scope':'APPROVED PLACE-QA-08 only; user: Выполняй PLACE-QA-08 по плану'}
(HERE/'entry.json').write_text(json.dumps(entry,indent=2),encoding='utf-8')
config={'browser':{'browserName':'chromium','launchOptions':{'channel':'chrome','headless':True}},'outputDir':str(STATE/'playwright')}
(STATE/'playwright.json').write_text(json.dumps(config),encoding='utf-8')
print('Initialized own isolated harness; foreign files:',len(foreign),'source files:',len(source),'ports free: 8842, 55447')
