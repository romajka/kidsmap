"""Owned short native batches with durable results; no long exec-owned controller."""
import concurrent.futures,json,subprocess,sys,time
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name
cli='/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh'
def worker(lang):
 state={'lang':lang,'completed':[],'failed':[],'running':True}
 def save(): (h/f'runner-{lang}.json').write_text(json.dumps(state,indent=2))
 if True:
  t=time.monotonic();p=subprocess.run([cli,'-s=mod03search'+lang,'open','about:blank'],cwd=r,capture_output=True,text=True,timeout=90)
  (s/f'browser-open-{lang}.txt').write_text(p.stdout+p.stderr)
  if p.returncode:state.update(running=False,error='own browser open failed');save();return
 for width in(360,390,768,1024,1280,1440):
  name=f'native-{lang}-{width}.js';dest=h/(name+'.result.json')
  if dest.exists():data=json.loads(dest.read_text());assert data['complete'] and all(row['status']=='PASS' for row in data['rows']);state['completed'].append(width);save();continue
  state['width']=width;save();t=time.monotonic()
  try:
   p=subprocess.run([sys.executable,str(h/'drive_lang.py'),name,lang],cwd=r,capture_output=True,text=True,timeout=260)
   (s/(name+'.driver.txt')).write_text(p.stdout+p.stderr)
   if not dest.exists():raise RuntimeError('no semantic result')
   data=json.loads(dest.read_text());fail=[v for v in data.get('rows',[])if v['status']!='PASS']
   assert p.returncode==0 and data.get('complete') and not fail,(p.returncode,fail[:1])
   state['completed'].append(width)
  except Exception as e:state['failed'].append({'width':width,'error':str(e)[:220]});state['running']=False;save();return
  state['last_seconds']=round(time.monotonic()-t,3);save()
 state['running']=False;state['done']=True;save()
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(worker,('ru','az','en')))
