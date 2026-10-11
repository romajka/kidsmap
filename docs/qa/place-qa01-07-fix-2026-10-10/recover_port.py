"""Windows reserves 55446–55545; retain failed own DB and retry on free 55445."""
import json
import shutil
import socket
import subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
snapshot = json.loads((HERE/'snapshot.json').read_text(encoding='utf-8'))
def run(argv):
    result = subprocess.run(argv,capture_output=True,text=True)
    with (HERE/'command-ledger.jsonl').open('a',encoding='utf-8') as file:
        file.write(json.dumps({'argv':argv,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})+'\n')
    assert result.returncode==0
    return result.stdout.strip()
assert run(['wsl.exe','--exec','docker','inspect',snapshot['container_id'],'--format','{{.Name}}']) == '/'+snapshot['owned_container']
run(['wsl.exe','--exec','docker','stop',snapshot['container_id']])
shutil.copyfile(HERE/'snapshot.json',HERE/'initial-snapshot.json')
with socket.socket() as probe: probe.bind(('127.0.0.1',55445))
for name in ('prepare.py','runtime.py','kmfix_settings.py'):
    path = HERE/name
    content = path.read_text(encoding='utf-8').replace('55460','55445').replace('kidsmap-placeqa01-07-fix-20261010','kidsmap-placeqa01-07-fix-20261010-r2')
    path.write_text(content,encoding='utf-8')
print('Retained stopped own failed container; fresh retry uses free/nonreserved port 55445.')
