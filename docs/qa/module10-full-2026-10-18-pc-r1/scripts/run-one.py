import subprocess,json,sys
from pathlib import Path
Q=Path(__file__).resolve().parent;name=sys.argv[1]
if name=='flags':(Q/'flags.js').write_text((Q/'flags-template.js').read_text().replace('__FIXTURES__',(Q/'fixtures.json').read_text()))
if name=='media':(Q/'media.js').write_text((Q/'media-template.js').read_text().replace('__ASSETS__',json.dumps({'staff':json.loads((Q/'assets.json').read_text())['staff']})))
r=subprocess.run([sys.executable,str(Q/'browser_driver.py'),name+'.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout[-1800:]
raw=(Q/(name+'-cli.txt')).read_text();assert raw.startswith('### Result\n'),raw[:1000];d=json.loads(raw.splitlines()[1]);(Q/(name+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2));bad=[{k:v for k,v in r.items() if k not in ['state','observedExcerpt','focus']} for r in d.get('rows',[]) if 'checks' in r and not all(r['checks'].values())];print(json.dumps({'name':name,'rows':len(d.get('rows',[])),'failed':bad,'pageerrors':len(d.get('pageerrors',[])),'httpErrors':len(d.get('http',[])),'blocked':len(d.get('blocked',[]))},ensure_ascii=False))
