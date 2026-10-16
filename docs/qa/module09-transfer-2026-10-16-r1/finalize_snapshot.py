import ast,hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;v=json.loads((H/'verification.json').read_text());assert not v['forbidden_paths']and not v['secret_findings']and not v['large_files_over_90MiB'];entry=json.loads((H/'entry.json').read_text());env=dict(os.environ,GIT_INDEX_FILE=str(S/'full.index'))
def git(*a,input=None):return subprocess.run(['git','-c','gc.auto=0',*a],cwd=R,env=env,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
state=json.loads((S/'snapshot-index-state.json').read_text());proc=subprocess.Popen(['git','cat-file','--batch'],cwd=R,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
def blob(oid):
 proc.stdin.write((oid+'\n').encode());proc.stdin.flush();head=proc.stdout.readline().split();assert head[1]==b'blob';size=int(head[2]);b=proc.stdout.read(size);assert proc.stdout.read(1)==b'\n';return b
sources={};late=[];js=[]
for n,m in state['entries'].items():
 if not n.startswith(('src/','static/','locale/','config/','templates/','scripts/'))or Path(n).suffix not in {'.py','.html','.js','.css','.po','.cjs'}:continue
 b=blob(m['oid']);sources[n]=hashlib.sha256(b).hexdigest()
 p=R/n
 if not p.exists()or hashlib.sha256(p.read_bytes()).hexdigest()!=sources[n]:late.append(n)
 if n in state['changed_paths']and Path(n).suffix in{'.js','.cjs'}:
  c=subprocess.run(['node','--check','--input-type='+('commonjs'if n.endswith('.cjs')else'module')],input=b,capture_output=True);js.append({'path':n,'exit':c.returncode})
proc.stdin.close();proc.wait();assert proc.returncode==0
(H/'transferred-source-manifest.json').write_text(json.dumps(sources,indent=2));v['source_manifest']={'files':len(sources),'scope':'Full staged application/scripts py/html/js/css/po/cjs sources','current_disk_drift_after_freeze':late};v['application_javascript_syntax']={'files':len(js),'failures':[x for x in js if x['exit']]};v['known_exclusions']=['new ignored .tmp runtime profiles/credentials','checkout .env and local databases/private-media','venv/node_modules/compiledMO/pyc','production backups/data/logs'];v['publication']='READY, NOT YET PUSHED';v['acceptance']='NOT RUN: this is WIP transfer, not module09 acceptance';(H/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2))
if late:raise SystemExit('Application changed after freeze; inspect metadata, do not publish outdated source')
git('add','--',str(H.relative_to(R)))
fulltree=git('write-tree').decode().strip();(S/'full-tree.json').write_text(json.dumps({'tree':fulltree,'base':entry['head'],'branch':entry['target_branch']},indent=2));print(json.dumps({'tree':fulltree,'source_files':len(sources),'python_ast':v['application_python_ast'],'javascript_syntax':v['application_javascript_syntax'],'disk_drift':late,'shared_index_match':hashlib.sha256((R/'.git/index').read_bytes()).hexdigest()==entry['index_sha256']},ensure_ascii=False))
