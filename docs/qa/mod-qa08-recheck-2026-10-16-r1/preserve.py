import hashlib,json,subprocess
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];entry=json.loads((h/'entry.json').read_text());changed=[];missing=[]
for name,digest in entry['files'].items():
 p=r/name
 if not p.is_file():missing.append(name)
 elif hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changed.append(name)
containers=[{k:c[k]for k in('ID','Names','Ports','State')}for c in[json.loads(s)for s in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]]
byid={c['ID']:c for c in containers};drift=[{'entry':c,'current':byid.get(c['ID'])}for c in entry['containers']if byid.get(c['ID'])!=c]
active=[l for l in(r/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]
process_checks=[]
for item in entry['foreign_processes']:
 proc=Path('/proc')/str(item['pid'])
 try:
  args=[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x];cwd=str((proc/'cwd').resolve())
  process_checks.append({'pid':item['pid'],'same_args':args==item['args'],'same_cwd':cwd==item['cwd'],'present':True})
 except (OSError,UnicodeDecodeError):process_checks.append({'pid':item['pid'],'present':False})
result={'entry_files':len(entry['files']),'changed_entry_files':changed,'missing_entry_files':missing,'unchanged_files':len(entry['files'])-len(changed)-len(missing),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'active_run':active,'entry_foreign_processes':entry['foreign_processes'],'entry_container_count':len(entry['containers']),'current_container_count':len(containers),'container_drift':drift,'foreign_process_checks':process_checks,'process_continuity':'Fresh entry QA HTTP identity checked by pid,argv,cwd; no blanket claim for unrecorded machine processes'}
(h/'preservation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,ensure_ascii=False))
