"""Sequential native browser scripts; summarize actual structured outputs."""
from pathlib import Path
import subprocess,json,sys,collections,datetime
P=Path(__file__).resolve().parent;R=P.parents[2];sys.stdout.reconfigure(encoding='utf-8')
out=[]
for name in ['tail.js','public-native.js','map-geometry.js','admin-functional.js','event-native.js']:
 r=subprocess.run([str(R/'.venv/Scripts/python.exe'),str(P/'drive.py'),name],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
 try:d=json.loads((P/(Path(name).stem+'.result.txt')).read_text(encoding='utf-8'));rows=d.get('rows',[]);summary={'script':name,'native_exit':r.returncode,'rows':len(rows),'statuses':dict(collections.Counter(x['status'] for x in rows))}
 except Exception as e:summary={'script':name,'native_exit':r.returncode,'harness_result_error':str(e)}
 out.append(summary);(P/'pipeline-summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(summary),flush=True)
