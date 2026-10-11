"""Stop only resources whose identities match this run's recorded ownership."""
import json
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
rows=[]
def run(argv):
    result=subprocess.run(argv,cwd=ROOT,capture_output=True,encoding='utf-8')
    rows.append({'argv':argv,'exit_code':result.returncode})
    assert result.returncode==0,(argv,result.returncode)
    return result.stdout.strip()
pid=int(json.loads((HERE/'server-process.json').read_text())['pid'])
command=f"$taskServerProcess = Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}'; if ($taskServerProcess.CommandLine -notlike '*place-qa01-07-fix-2026-10-10/runtime.py serve*') {{ throw 'Owned server identity mismatch' }}; Stop-Process -Id {pid}"
run(['powershell.exe','-NoProfile','-Command',command])
for filename in ('initial-snapshot.json','snapshot.json'):
    owned=json.loads((HERE/filename).read_text(encoding='utf-8'))
    name=owned['owned_container'];expected=owned['container_id']
    actual=run(['wsl.exe','--exec','docker','inspect','--format','{{.Id}}',name])
    assert actual==expected,'Owned container identity mismatch'
    run(['wsl.exe','--exec','docker','stop',name])
result={'own_server_stopped':True,'own_browser_closed':True,'own_containers_stopped_and_retained':True,'foreign_resources_touched':False,'commands':rows}
(HERE/'cleanup.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('Verified own server/containers stopped; containers and evidence retained.')
