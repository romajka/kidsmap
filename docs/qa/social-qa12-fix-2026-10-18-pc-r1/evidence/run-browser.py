import subprocess,json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
for kind in ['place','activity','specialist','event']:
 name='native-'+kind;t=(Q/'browser-template.js').read_text().replace('__FIXTURES__',(Q/'fixtures.json').read_text()).replace('__KIND__',kind);(Q/(name+'.js')).write_text(t)
 r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),name+'.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1800:]
 raw=(Q/(name+'-cli.txt')).read_text();assert raw.startswith('### Result\n'),raw[:900];d=json.loads(raw.splitlines()[1]);(Q/(name+'.json')).write_text(json.dumps(d,indent=2));bad=[r for r in d['rows'] if not all(r['checks'].values())];print(json.dumps({'kind':kind,'rows':len(d['rows']),'checks':sum(len(r['checks']) for r in d['rows']),'failed':bad,'console':len(d['consoleErrors']),'pageerrors':len(d['pageerrors']),'http':len(d['http']),'requestfailed':len(d['failed']),'blocked':len(d['blocked'])}),flush=True);assert not bad
