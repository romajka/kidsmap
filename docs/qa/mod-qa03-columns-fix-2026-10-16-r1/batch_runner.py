import concurrent.futures,json,subprocess,sys,time
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name
cli='/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh'
def worker(lang):
 state={'lang':lang,'completed':[],'failed':[],'running':True}
 def save():(h/f'runner-{lang}.json').write_text(json.dumps(state,indent=2))
 p=subprocess.run([cli,'-s=mod03columns'+lang,'open','about:blank'],cwd=r,capture_output=True,text=True,timeout=90);(s/f'browser-open-{lang}.txt').write_text(p.stdout+p.stderr)
 if p.returncode:state.update(running=False,error='own browser open failed');save();return
 for width in(360,390,768,1024,1280,1440):
  if lang=='ru'and width==390:
   d=json.loads((h/'native-ru-390.pilot.json').read_text());assert d['complete']and len([v for v in d['rows']if v['status']=='FAIL'])==3
   state['completed'].append(width);state['retained_pilot_focus_replaced']=3;save();continue
  name=f'native-{lang}-{width}.js';dest=h/(name+'.result.json')
  if dest.exists():
   d=json.loads(dest.read_text());assert d['complete']and all(v['status']=='PASS'for v in d['rows']);state['completed'].append(width);save();continue
  state['width']=width;save();t=time.monotonic()
  try:
   p=subprocess.run([sys.executable,str(h/'drive_lang.py'),name,lang],cwd=r,capture_output=True,text=True,timeout=180);(s/(name+'.driver.txt')).write_text(p.stdout+p.stderr)
   if not dest.exists():raise RuntimeError('No semantic result')
   d=json.loads(dest.read_text());fail=[v for v in d.get('rows',[])if v['status']!='PASS'];assert p.returncode==0 and d.get('complete')and not fail,(p.returncode,fail[:1]);state['completed'].append(width)
  except Exception as e:state['failed'].append({'width':width,'error':str(e)[:220]});state['running']=False;save();return
  state['last_seconds']=round(time.monotonic()-t,3);save()
 state['running']=False;state['done']=True;save()
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:list(pool.map(worker,('ru','az','en')))
