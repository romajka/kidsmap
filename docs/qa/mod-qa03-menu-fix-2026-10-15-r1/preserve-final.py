from pathlib import Path
import json,hashlib,subprocess
H=Path(__file__).resolve().parent;R=H.parents[2];E=json.loads((H/'entry.json').read_text());changed=[];missing=[]
for p,digest in E['files'].items():
 f=R/p
 if not f.is_file():missing.append(p)
 elif hashlib.sha256(f.read_bytes()).hexdigest()!=digest:changed.append(p)
containers=[json.loads(x)for x in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()];by={x['ID']:x for x in containers}
container_checks=[{'name':x['Names'],'same':all(by.get(x['ID'],{}).get(k)==x[k]for k in('ID','Names','Ports','State'))}for x in E['containers']]
process_checks=[]
for x in E['foreign_processes']:
 p=Path('/proc',str(x['pid']))
 try:same=[a.decode()for a in(p/'cmdline').read_bytes().split(b'\0')if a]==x['args']and str((p/'cwd').resolve())==x['cwd']
 except OSError:same=False
 process_checks.append({'pid':x['pid'],'status':'PASS'if same else'NOT VERIFIED','reason':None if same else'PID absent after turn interruption; no foreign restart issued, preservation not claimed'})
result={'baseline_files':len(E['files']),'unchanged':len(E['files'])-len(changed)-len(missing),'changed':changed,'missing':missing,'foreign_containers':container_checks,'foreign_HTTP':process_checks,'historical_four_before_module07_continuity':'NOT VERIFIED retained','head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'active_run':[l for l in(R/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')]}
(H/'preservation-final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'baseline':len(E['files']),'changed':changed,'missing':missing,'containers_same':sum(x['same']for x in container_checks),'foreign_HTTP_unverified':sum(x['status']=='NOT VERIFIED'for x in process_checks)}))
