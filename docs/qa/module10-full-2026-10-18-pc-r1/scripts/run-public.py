import subprocess,json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
for lang in ['az','ru','en']:
 name='public-'+lang;(Q/(name+'.js')).write_text((Q/'public-template.js').read_text().replace('__LANG__',lang));r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),name+'.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1600:]
 raw=(Q/(name+'-cli.txt')).read_text();assert raw.startswith('### Result\n'),raw[:900];d=json.loads(raw.splitlines()[1]);(Q/(name+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2));bad=[{k:v for k,v in r.items() if k!='state'} for r in d['rows'] if not all(r['checks'].values())];print(json.dumps({'lang':lang,'cells':len(d['rows']),'failed':bad,'pageerrors':len(d['pageerrors']),'httpErrors':len(d['http']),'blocked':len(d['blocked'])}),flush=True)
