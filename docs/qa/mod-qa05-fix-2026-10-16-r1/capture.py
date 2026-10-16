import hashlib,json,os,secrets,socket,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
assert not (HERE/'entry.json').exists();SCRATCH.mkdir(mode=0o700);os.chmod(SCRATCH,0o700)
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
files={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in paths if p and '.env'not in Path(p).name and (ROOT/p).is_file() and not p.startswith('docs/qa/'+HERE.name+'/')}
for p in ROOT.glob('locale/*/LC_MESSAGES/*.mo'):files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
processes=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  args=[a.decode()for a in(proc/'cmdline').read_bytes().split(b'\0')if a]
  if len(args)==3 and args[-1]=='serve' and args[1].startswith(str(ROOT/'docs/qa')+'/'):
   processes.append({'pid':int(proc.name),'args':args,'cwd':str((proc/'cwd').resolve())})
 except (OSError,UnicodeDecodeError):pass
containers=[{k:c[k]for k in ('ID','Names','Ports','State')}for c in [json.loads(s)for s in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]]
entry={'root':str(ROOT),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'status':subprocess.check_output(['git','status','--short'],text=True),'active_run':[l for l in(ROOT/'docs/task33/implementation-status.md').read_text().splitlines()if l.startswith('active_run:')],'files':files,'foreign_processes':processes,'containers':containers,'mode':'APPROVED IMPLEMENT MOD-QA-05; approved one-line row trigger focus scope'}
(HERE/'entry.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2))
print(json.dumps({'entry_files':len(files),'foreign_processes':len(processes),'foreign_containers':len(containers),'head':entry['head'],'branch':entry['branch'],'active_run':entry['active_run']}))
