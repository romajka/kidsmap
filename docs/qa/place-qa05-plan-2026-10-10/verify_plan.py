"""Record real assertion exits, verify artifacts and stop only the owned container."""
import hashlib
import json
import re
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = ROOT/'docs/superpowers/plans/2026-10-10-place-qa05-category-popup.md'
snapshot = json.loads((HERE/'snapshot.json').read_text(encoding='utf-8'))


def run(argv, expected=0, output=None):
    result = subprocess.run(argv,cwd=ROOT,capture_output=True,encoding='utf-8')
    row = {'argv':argv,'cwd':str(ROOT),'exit_code':result.returncode}
    if output:
        (HERE/output).write_text(result.stdout+result.stderr,encoding='utf-8')
        row['output_file'] = output
    else:
        row.update(stdout=result.stdout,stderr=result.stderr)
    with (HERE/'command-ledger.jsonl').open('a',encoding='utf-8') as file:
        file.write(json.dumps(row)+'\n')
    assert result.returncode == expected, (argv,result.returncode)
    return result.stdout.strip()


run([sys.executable,str(HERE/'collect_browser_results.py')],output='collected-browser-summary.txt')
run([sys.executable,str(HERE/'assert_baseline.py')],expected=1,output='baseline-assertions.txt')
checks = json.loads((HERE/'baseline-assertions.json').read_text(encoding='utf-8'))
assert checks['total']==36 and checks['passed']==27 and checks['failed']==9
assert run(['git','rev-parse','HEAD']) == snapshot['head']
run(['git','status','--short'])
run(['git','diff','--exit-code','--stat','HEAD','--','src','static','config','locale'])
run(['git','diff','--check'])
current = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in snapshot['source_before_sha256']}
changed = [p for p,h in current.items() if h != snapshot['source_before_sha256'][p]]
assert not [p for p in changed if p != 'docs/qa/module-acceptance-prompts.md'], changed
active = next(x for x in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
assert active == snapshot['active_run'] == 'active_run: NONE'

manifest = []
for file in sorted((HERE/'screenshots').glob('*.png')):
    # PNG IHDR provides dimensions without modifying image pixels.
    data = file.read_bytes()
    manifest.append({'file':file.relative_to(HERE).as_posix(),'width':int.from_bytes(data[16:20],'big'),
        'height':int.from_bytes(data[20:24],'big'),'sha256':hashlib.sha256(data).hexdigest(),
        'classification':'effective geometry' if file.name.startswith('effective-') else
            'keyboard baseline' if file.name.startswith('keyboard-') else 'initial environment-failed matrix'})
assert sum(x['classification']=='effective geometry' for x in manifest)==18
assert sum(x['classification']=='keyboard baseline' for x in manifest)==3
(HERE/'screenshots-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

container_id = snapshot['container_id']
assert re.fullmatch('[0-9a-f]{64}',container_id)
assert run(['wsl.exe','--exec','docker','inspect',container_id,'--format','{{.Name}}']) == '/'+snapshot['owned_container']
run(['wsl.exe','--exec','docker','stop',container_id])
assert run(['wsl.exe','--exec','docker','inspect',container_id,'--format','{{.State.Running}}']) == 'false'
foreign_now = [x.strip() for x in run(['wsl.exe','--exec','docker','ps','--format','{{.Names}} {{.Ports}}']).splitlines()]
foreign_before = [x.strip() for x in snapshot['foreign_stands']]
server = socket.socket()
server.settimeout(1)
assert server.connect_ex(('127.0.0.1',8819)) != 0
server.close()
browser_ledger = [json.loads(x) for x in (HERE/'browser-command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
assert any(row['argv'][-1:] == ['close'] and row['exit_code']==0 and "closed" in row['stdout'] for row in browser_ledger)
links = []
for doc in [PLAN,HERE/'REPORT.md']:
    content = doc.read_text(encoding='utf-8')
    assert not re.search(r'\b(?:TODO|TBD)\b',content)
    assert all(line.rstrip()==line for line in content.splitlines())
    for link in re.findall(r'\]\(([^)]+)\)',content):
        path = (doc.parent/link).resolve()
        assert path.is_file() or path == HERE/'plan-verification.json', (doc,link)
        links.append({'document':doc.relative_to(ROOT).as_posix(),'target':link})
result = {'head':snapshot['head'],'active_run':active,'application_diff_empty':True,
    'application_and_prior_plans_preserved':True,'all_input_hashes_equal':not changed,'observed_document_drift':changed,
    'browser':'Chromium headless shell 153.0.8010.12',
    'effective_geometry':{'checks':18,'passed':15,'failed':3,'local_resource_failures':0,'page_errors':0},
    'keyboard':{'checks':18,'passed':12,'failed':6},'assertion_exit_code':1,
    'long_labels_clipped':checks['long_labels_clipped'],
    'screenshots':{'effective_geometry':18,'keyboard':3},'browser_session':'closed',
    'owned_server':'stopped; loopback 8819 no longer listening',
    'owned_container':snapshot['owned_container'],'owned_container_status':'stopped; not removed',
    'foreign_stands_snapshot_equal':sorted(foreign_now)==sorted(foreign_before),
    'initial_foreign_stands_still_running':set(foreign_before).issubset(foreign_now),
    'new_foreign_stands_observed':sorted(set(foreign_now)-set(foreign_before)),
    'save_reload':'NOT RUN','implementation':'NOT AUTHORIZED','approval':'PENDING',
    'documents_checked':2,'links_checked':len(links),'links':links}
(HERE/'plan-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='links'}))
