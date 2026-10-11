"""Sequential native CLI operations on the supplemental current WORKTREE stand."""
from pathlib import Path
import subprocess,sys,json,os,datetime
P=Path(__file__).resolve().parent;R=P.parents[2];sys.stdout.reconfigure(encoding='utf-8');env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
(P/'current-settings.js').write_text((P/'settings.js').read_text(encoding='utf-8'),encoding='utf-8')
results=[]
for name in ['current-settings','current-focus','current-boundary','current-pages','current-network']:
 r=subprocess.run([str(R/'.venv/Scripts/python.exe'),str(P/'drive-current.py'),name+'.js'],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
 with (P/'current-checks.log').open('a',encoding='utf-8') as f:f.write(name+'\n'+r.stdout+'\n'+r.stderr+'\n')
 try:d=json.loads((P/(name+'.result.txt')).read_text(encoding='utf-8'));rows=d.get('rows',[]);counts={s:sum(x.get('status')==s for x in rows) for s in ['PASS','FAIL','NOT RUN']}
 except ValueError:counts={'HARNESS_ERROR':True}
 x={'name':name,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cli_exit':r.returncode,'counts':counts};results.append(x);print(json.dumps(x),flush=True)
 (P/'current-checks.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
 if r.returncode:sys.exit(r.returncode)
print('Supplemental current WORKTREE native checks complete',flush=True)
