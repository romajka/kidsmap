"""Offline handoff verification; does not claim live runtime or repeat acceptance."""
import hashlib,json,subprocess
from pathlib import Path
p=Path(__file__).resolve().parent
root=p.parents[2]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
entry=json.loads((p/'entry.json').read_text())
final=json.loads((p/'entry-final.json').read_text())['source_files']
assert all((root/k).is_file() and sha(root/k)==v for k,v in final.items())
assert all((root/k).is_file() and sha(root/k)==v for k,v in entry['previous_reports'].items())
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=root).strip()==entry['head']
assert subprocess.check_output(['git','branch','--show-current'],text=True,cwd=root).strip()==entry['branch']
assert 'active_run: NONE' in (root/'docs/task33/implementation-status.md').read_text()
assert (root/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text().count('```text')==88
rows=json.loads((p/'browser-evidence-index.json').read_text())['rows']
assert len(rows)==217 and all(r['status']=='PASS' for r in rows)
png=json.loads((p/'png-manifest.json').read_text())
assert all(sha(p/r['path'])==r['sha256'] for r in png)
assert 'Ran 28 tests' in (p/'targeted-green.txt').read_text() and '\nOK\n' in (p/'targeted-green.txt').read_text()
for args in (['git','diff','--check'],['node','--check','static/js/organization_workspace.js']):
 subprocess.run(args,cwd=root,check=True)
stands=[]
for f in (root/'docs/qa').glob('*/server.json'):
 d=json.loads(f.read_text()); q=Path('/proc')/str(d['pid'])/'cmdline'
 stands.append({'profile':f.parent.name,'recorded_pid':d['pid'],'recorded_process_exists':q.exists()})
out={'date':'2026-10-13','source_matches_accepted_snapshot':True,'previous_evidence_files_unchanged':len(entry['previous_reports']),'saved_backend_pass':28,'saved_browser_pass':217,'accepted_png':len({r['screenshot'] for r in rows if 'screenshot' in r}),'all_png_hashes_match':len(png),'diff_check_exit':0,'node_check_exit':0,'live_verification':'BLOCKED: connection refused; recorded processes absent','stands':stands,'restarted_or_stopped_processes_this_handoff':False,'full_module02':'NOT RUN'}
(p/'handoff-verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
